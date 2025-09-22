     
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
                echo "⏭️ Run skipped because SKIP_SCHEDULED_RUN=true"
            }
        }

        stage('Find last successful build for slot and Deploy') {
            when { expression { !params.SKIP_SCHEDULED_RUN } }
            steps {
                script {
                    // constants
                    def envName   = "CIT"
                    def slotNo    = "1"     // Scheduler is for slot1
                    def podName   = "BCARD"
                    def targetJobPath = "APIN152377/OLAF/AWS/OLAF_AWS_Deployment/Deployment_job_CIT"

                    // Jenkins REST API endpoint for job history (not just last build)
                    def jobUrl = "https://jenkins-oss-congo.barclays.intranet/job/${targetJobPath}/api/json?tree=builds[number,result,url,actions[parameters[name,value]]]"

                    echo "🔎 Scheduler started for env=${envName}, slot=${slotNo}, pod=${podName}"
                    echo "Fetching build history from: ${jobUrl}"

                    withCredentials([usernamePassword(credentialsId: 'testjob-cred',
                                                      usernameVariable: 'USERNAME',
                                                      passwordVariable: 'PASSWORD')]) {
                        def response = sh(
                            script: """curl -s -u $USERNAME:$PASSWORD "$jobUrl" """,
                            returnStdout: true
                        ).trim()

                        def data = readJSON text: response

                        // Find the latest SUCCESS build where SLOT_NO == slotNo
                        def matchingBuild = data.builds.find { b ->
                            b.result == 'SUCCESS' && b.actions.any { a ->
                                a.parameters?.any { p -> p.name == 'SLOT_NO' && "${p.value}" == slotNo }
                            }
                        }

                        if (!matchingBuild) {
                            error "❌ No successful build found for slot=${slotNo}"
                        }

                        // Extract MINIAPPS_TO_DEPLOY
                        def miniappsparam = null
                        matchingBuild.actions.each { a ->
                            a.parameters?.each { p ->
                                if (p.name == 'MINIAPPS_TO_DEPLOY') {
                                    miniappsparam = p.value
                                }
                            }
                        }

                        if (!miniappsparam) {
                            error "❌ No MINIAPPS_TO_DEPLOY found in build #${matchingBuild.number}"
                        }

                        echo "📊 Found last successful build for slot=${slotNo}: #${matchingBuild.number}"
                        echo "📊 MINIAPPS_TO_DEPLOY=${miniappsparam}"
                        echo "✅ Proceeding with scheduled deployment for env=${envName}, slot=${slotNo}"
                        echo "🚀 Deploying miniapps version: ${miniappsparam}"

                        // Trigger deployment job
                        build job: targetJobPath, parameters: [
                            string(name: 'POD_NAME', value: podName),
                            string(name: 'SLOT_NO', value: slotNo),
                            string(name: 'MINIAPPS_TO_DEPLOY', value: miniappsparam),
                            string(name: 'RECREATE_ENV', value: 'TRUE'),
                            string(name: 'APPD_ENABLE', value: 'true')
                        ], wait: false
                    }
                }
            }
        }
    }
}
