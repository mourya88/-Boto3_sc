pipeline {
    agent any

    parameters {
        // Slot scheduling with OFF/TRUE/FALSE options
        choice(name: 'RUN_SLOT_0', choices: ['OFF', 'TRUE', 'FALSE'], description: 'CIT Slot 0 schedule (OFF/TRUE=Recreate/ FALSE=No Recreate)')
        choice(name: 'RUN_SLOT_1', choices: ['OFF', 'TRUE', 'FALSE'], description: 'CIT Slot 1 schedule (OFF/TRUE=Recreate/ FALSE=No Recreate)')
        choice(name: 'RUN_SLOT_2', choices: ['OFF', 'TRUE', 'FALSE'], description: 'CIT Slot 2 schedule (OFF/TRUE=Recreate/ FALSE=No Recreate)')
    }

    stages {
        stage('CIT Deployments') {
            steps {
                script {
                    def envName   = "CIT"
                    def podName   = "BCARD"
                    def targetJob = "APIN152377/OLAF/AWS/OLAF_AWS_Deployment/Deployment_job_CIT"

                    [0, 1, 2].each { slotNo ->
                        def slotChoice = params["RUN_SLOT_${slotNo}"]

                        if (slotChoice != 'OFF') {
                            echo "🔄 Running scheduled deploy for ${envName} slot ${slotNo} (Recreate=${slotChoice})"

                            // --- Fetch last successful build for this slot ---
                            def jobUrl = "https://jenkins-oss-congo.barclays.intranet/job/${targetJob}/api/json?tree=builds[number,result,actions[parameters[name,value]]]"
                            def response = ""
                            withCredentials([usernamePassword(credentialsId: 'testjob-cred',
                                                             usernameVariable: 'USERNAME',
                                                             passwordVariable: 'PASSWORD')]) {
                                response = sh(
                                    script: """curl -g -s -u "$USERNAME:$PASSWORD" "${jobUrl}" """,
                                    returnStdout: true
                                ).trim()
                            }

                            def json = readJSON text: response
                            def lastSuccessfulBuild = json.builds.find { build ->
                                build.result == "SUCCESS" &&
                                build.actions.any { action ->
                                    action.parameters?.any { p ->
                                        p.name == "SLOT_NO" && p.value.toString() == "${slotNo}"
                                    }
                                }
                            }

                            if (!lastSuccessfulBuild) {
                                echo "⚠️ No successful build found for slot ${slotNo}, skipping."
                                return
                            }

                            echo "📌 Last successful build for slot ${slotNo}: #${lastSuccessfulBuild.number}"

                            def miniappsParam = ""
                            lastSuccessfulBuild.actions.each { action ->
                                action.parameters?.each { p ->
                                    if (p.name == "MINIAPPS_TO_DEPLOY") {
                                        miniappsParam = p.value
                                    }
                                }
                            }

                            if (!miniappsParam) {
                                echo "⚠️ MINIAPPS_TO_DEPLOY not found for slot ${slotNo}, skipping."
                                return
                            }

                            echo "✅ Resolved MINIAPPS_TO_DEPLOY for slot ${slotNo}: ${miniappsParam}"

                            // --- Trigger downstream deployment job ---
                            build job: targetJob, parameters: [
                                string(name: 'POD_NAME', value: podName),
                                string(name: 'SLOT_NO', value: "${slotNo}"),
                                string(name: 'MINIAPPS_TO_DEPLOY', value: miniappsParam),
                                string(name: 'RECREATE_ENV', value: slotChoice), // "TRUE" or "FALSE"
                                string(name: 'APPD_ENABLE', value: 'true')
                            ], wait: false

                        } else {
                            echo "⏭️ Skipping slot ${slotNo} (set to OFF)"
                        }
                    }
                }
            }
        }
    }
}
