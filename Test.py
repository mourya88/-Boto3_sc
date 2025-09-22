pipeline {
    agent any

    parameters {
        // Slot selection toggles
        booleanParam(name: 'RUN_SLOT_0', defaultValue: false, description: 'Schedule deploy for CIT slot 0')
        booleanParam(name: 'RUN_SLOT_1', defaultValue: false, description: 'Schedule deploy for CIT slot 1')
        booleanParam(name: 'RUN_SLOT_2', defaultValue: false, description: 'Schedule deploy for CIT slot 2')

        // Recreate env flags (per slot)
        booleanParam(name: 'RECREATE_SLOT_0', defaultValue: false, description: 'Recreate env for slot 0')
        booleanParam(name: 'RECREATE_SLOT_1', defaultValue: false, description: 'Recreate env for slot 1')
        booleanParam(name: 'RECREATE_SLOT_2', defaultValue: false, description: 'Recreate env for slot 2')
    }

    triggers {
        // Example: run daily at 2 AM
        cron('H 2 * * *')
    }

    stages {
        stage('CIT Deployments') {
            steps {
                script {
                    def envName = "CIT"
                    def podName = "BCARD"
                    def targetJobPath = "OLAF/AWS/OLAF_AWS_Deployment/Deployment_job_CIT"

                    // Define slot configs
                    def schedules = [
                        [slot: "0", run: params.RUN_SLOT_0, recreate: params.RECREATE_SLOT_0],
                        [slot: "1", run: params.RUN_SLOT_1, recreate: params.RECREATE_SLOT_1],
                        [slot: "2", run: params.RUN_SLOT_2, recreate: params.RECREATE_SLOT_2]
                    ]

                    schedules.each { entry ->
                        if (entry.run) {
                            echo "🚀 Checking last successful build for env=${envName}, slot=${entry.slot}, recreate=${entry.recreate}"

                            def jobUrl = "https://jenkins-oss-congo.barclays.intranet/job/${targetJobPath}/api/json?tree=builds[number,result,actions[parameters[name,value]]]]"

                            withCredentials([usernamePassword(credentialsId: 'testjob-cred',
                                                              usernameVariable: 'USERNAME',
                                                              passwordVariable: 'PASSWORD')]) {
                                def response = sh(
                                    script: """curl -g -s -u $USERNAME:$PASSWORD '${jobUrl}' """,
                                    returnStdout: true
                                ).trim()

                                def json = readJSON text: response

                                // Find last successful build for this slot
                                def lastBuild = json.builds.find { build ->
                                    build.result == "SUCCESS" &&
                                    build.actions.any { it.parameters?.any { p -> p.name == 'SLOT_NO' && p.value == entry.slot } }
                                }

                                if (!lastBuild) {
                                    echo "⚠️ No successful build found for slot ${entry.slot}"
                                    return
                                }

                                def miniappsVersion = lastBuild.actions
                                    .find { it.parameters }
                                    ?.parameters.find { it.name == 'miniappsDeployVersion' }?.value

                                echo "✅ Found build #${lastBuild.number} for slot ${entry.slot}, miniappsDeployVersion=${miniappsVersion}"

                                // Trigger deployment job
                                build job: targetJobPath,
                                      parameters: [
                                          string(name: 'SLOT_NO', value: entry.slot),
                                          string(name: 'ENV_NAME', value: envName),
                                          string(name: 'miniappsDeployVersion', value: miniappsVersion),
                                          booleanParam(name: 'RECREATE_ENV', value: entry.recreate)
                                      ]
                            }
                        } else {
                            echo "⏭️ Skipping slot ${entry.slot}"
                        }
                    }
                }
            }
        }
    }
}
