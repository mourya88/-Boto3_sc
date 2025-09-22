     
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
                echo "Run skipped (SKIP_SCHEDULED_RUN=true)."
            }
        }

        stage('Fetch miniapps via REST API') {
            when { expression { !params.SKIP_SCHEDULED_RUN } }
            steps {
                script {
                    // constants for CIT slot01
                    def envName   = "CIT"
                    def slotNo    = "1"
                    def podName   = "BCARD"
                    def targetJobPath = "APIN152377/OLAF/AWS/OLAF_AWS_Deployment/Deployment_job_CIT"

                    // Jenkins REST API URL for last successful build
                    def jobUrl = "https://jenkins-oss-congo.barclays.intranet/job/${targetJobPath}/lastSuccessfulBuild/api/json"

                    // Call REST API with basic auth (replace with Jenkins credentials later)
                    withCredentials([usernamePassword(credentialsId: 'your-jenkins-creds-id',
                                                      usernameVariable: 'USERNAME',
                                                      passwordVariable: 'PASSWORD')]) {
                        def response = sh(
                            script: """
                                curl -s -u $USERNAME:$PASSWORD "$jobUrl"
                            """,
                            returnStdout: true
                        ).trim()

                        echo "Fetched JSON: ${response.take(200)}..."  // print first 200 chars for debug

                        def json = readJSON text: response
                        def paramsAction = json.actions.find { it._class?.contains("ParametersAction") }
                        def miniappsparam = paramsAction?.parameters.find { it.name == "MINIAPPS_TO_DEPLOY" }?.value

                        if (!miniappsparam) {
                            error "No MINIAPPS_TO_DEPLOY found in last successful build!"
                        }

                        echo "Resolved MINIAPPS_TO_DEPLOY = ${miniappsparam}"

                        // Trigger target job with values
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
