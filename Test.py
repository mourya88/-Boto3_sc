pipeline {
    agent any
    parameters([
        booleanParam(
            name: 'SKIP_SCHEDULED_RUN',
            defaultValue: false,
            description: 'Set true to skip this scheduled run'
        )
    ])

    stages {
        stage('Guard: skip?') {
            when { expression { params.SKIP_SCHEDULED_RUN } }
            steps {
                echo "Run skipped (SKIP_SCHEDULED_RUN=true)"
            }
        }

        stage('Trigger Deployment') {
            when { expression { !params.SKIP_SCHEDULED_RUN } }
            steps {
                script {
                    def envName = "CIT"
                    def slotNo = "1"
                    def podName = "BCARD"
                    def miniappsparam = "uka-channel-app:102.15-SNAPSHOT,uka-client-app:104.5-SNAPSHOT,uka-channel-config-aws-cit:3.5-SNAPSHOT"
                    def targetJobPath = "APIN152377/OLAF/AWS/OLAF_AWS_Deployment/Deployment_job_CIT"

                    echo "Proceeding with scheduled deploy for ${envName} slot ${slotNo}..."

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
