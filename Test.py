pipeline {
    agent any

    parameters {
        // Slot 0
        booleanParam(name: 'RUN_SLOT_0', defaultValue: false, description: 'Schedule deploy for CIT slot 0')
        choice(name: 'RECREATE_SLOT_0', choices: ['false', 'true'], description: 'Recreate env for slot 0')

        // Slot 1
        booleanParam(name: 'RUN_SLOT_1', defaultValue: false, description: 'Schedule deploy for CIT slot 1')
        choice(name: 'RECREATE_SLOT_1', choices: ['false', 'true'], description: 'Recreate env for slot 1')

        // Slot 2
        booleanParam(name: 'RUN_SLOT_2', defaultValue: false, description: 'Schedule deploy for CIT slot 2')
        choice(name: 'RECREATE_SLOT_2', choices: ['false', 'true'], description: 'Recreate env for slot 2')
    }

    stages {
        stage('CIT Deployments') {
            steps {
                script {
                    def envName = "CIT"
                    def podName = "BCARD"
                    def targetJobPath = "APIN152377/OLAF/AWS/OLAF_AWS_Deployment/Deployment_job_CIT"

                    [0, 1, 2].each { slot ->
                        if (params["RUN_SLOT_${slot}"]) {
                            def recreateFlag = params["RECREATE_SLOT_${slot}"].toBoolean()
                            echo "🔍 Looking up last successful build for env=${envName}, slot=${slot}"

                            // API URL to fetch previous builds for this job
                            def jobUrl = "https://jenkins-oss-congo.barclays.intranet/job/APIN152377/job/OLAF/job/AWS/job/OLAF_AWS_Deployment/job/Deployment_job_CIT/api/json?tree=builds[number,result,actions[parameters[name,value]]]"

                            withCredentials([usernamePassword(credentialsId: 'test-job-cred',
                                                             usernameVariable: 'USERNAME',
                                                             passwordVariable: 'PASSWORD')]) {
                                def response = sh(
                                    script: """curl -s -u $USERNAME:$PASSWORD "${jobUrl}" """,
                                    returnStdout: true
                                ).trim()

                                def json = readJSON text: response

                                // Find last successful build for this slot
                                def lastBuild = json.builds.find { build ->
                                    build.result == "SUCCESS" &&
                                    build.actions.any { a ->
                                        a.parameters?.any { p ->
                                            p.name == "SLOT_NO" && p.value.toString() == "${slot}"
                                        }
                                    }
                                }

                                if (lastBuild) {
                                    def miniappsParam = lastBuild.actions.collectMany { it.parameters ?: [] }
                                                                  .find { it.name == "MINIAPPS_TO_DEPLOY" }?.value

                                    echo "✅ Last successful build found: #${lastBuild.number}"
                                    echo "✅ Resolved MINIAPPS_TO_DEPLOY = ${miniappsParam}"

                                    // Trigger downstream deployment
                                    build job: targetJobPath,
                                        parameters: [
                                            string(name: 'POD_NAME', value: podName),
                                            string(name: 'SLOT_NO', value: "${slot}"),
                                            string(name: 'MINIAPPS_TO_DEPLOY', value: miniappsParam ?: ""),
                                            booleanParam(name: 'RECREATE_ENV', value: recreateFlag),
                                            string(name: 'APPD_ENABLE', value: 'true')
                                        ],
                                        wait: false
                                } else {
                                    echo "⚠️ No successful build found for slot ${slot}, skipping deployment."
                                }
                            }
                        } else {
                            echo "⏭ Skipping slot ${slot} (RUN flag = false)"
                        }
                    }
                }
            }
        }
    }
}
