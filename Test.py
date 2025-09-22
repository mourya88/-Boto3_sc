
pipeline {
    agent any
    parameters {
        booleanParam(
            name: 'SKIP_SCHEDULED_RUN',
            defaultValue: false,
            description: 'Set true to skip this scheduled run'
        )
    }

    stages {
        stage('Guard: skip?') {
            when { expression { params.SKIP_SCHEDULED_RUN } }
            steps {
                echo "⚠️ Run skipped (SKIP_SCHEDULED_RUN=true)."
            }
        }

        stage('Fetch last slot build & trigger deployment') {
            when { expression { !params.SKIP_SCHEDULED_RUN } }
            steps {
                script {
                    // Constants
                    def envName = "CIT"
                    def slotNo = "1"          // Scheduler is for slot1
                    def podName = "BCARD"
                    def targetJobPath = "APIN152377/job/OLAF/job/AWS/job/OLAF_AWS_Deployment/job/Deployment_job_CIT"

                    // Build history endpoint (returns list of builds)
                    def jobUrl = "https://jenkins-oss-congo.barclays.intranet/job/${targetJobPath}/api/json?tree=builds[number,result,url,actions[parameters[name,value]]]"

                    echo "🟢 Scheduler started for env=${envName}, slot=${slotNo}, pod=${podName}"
                    echo "Fetching build history from: ${jobUrl}"

                    withCredentials([usernamePassword(
                        credentialsId: 'testjob-cred',
                        usernameVariable: 'USERNAME',
                        passwordVariable: 'PASSWORD'
                    )]) {
                        def response = sh(
                            script: """curl -s -u $USERNAME:$PASSWORD "${jobUrl}" """,
                            returnStdout: true
                        ).trim()

                        echo "✅ Raw response fetched (first 200 chars): ${response.take(200)}"

                        def data = readJSON text: response

                        // Find the latest SUCCESS build for this slot
                        def matchingBuild = data.builds.find { b ->
                            b.result == 'SUCCESS' && 
                            b.actions.any { a -> 
                                a.parameters?.any { p -> p.name == "SLOT_NO" && p.value == slotNo }
                            }
                        }

                        if (!matchingBuild) {
                            error "❌ No successful build found for slot ${slotNo}"
                        }

                        echo "✅ Last successful build number for slot ${slotNo}: ${matchingBuild.number}"
                        echo "🔗 Build URL: ${matchingBuild.url}"

                        // Extract MINIAPPS_TO_DEPLOY
                        def miniappsParam = matchingBuild.actions.collectMany { a -> 
                            a.parameters ?: [] 
                        }.find { p -> p.name == "MINIAPPS_TO_DEPLOY" }?.value

                        if (!miniappsParam) {
                            error "❌ No MINIAPPS_TO_DEPLOY found in last successful slot ${slotNo} build"
                        }

                        echo "✅ Resolved MINIAPPS_TO_DEPLOY for slot ${slotNo}: ${miniappsParam}"

                        // Trigger target job with values
                        build job: targetJobPath, parameters: [
                            string(name: 'POD_NAME', value: podName),
                            string(name: 'SLOT_NO', value: slotNo),
                            string(name: 'MINIAPPS_TO_DEPLOY', value: miniappsParam),
                            string(name: 'RECREATE_ENV', value: 'TRUE'),
                            string(name: 'APPD_ENABLE', value: 'true')
                        ], wait: false
                    }
                }
            }
        }
    }
}
