
properties([
  parameters([
    booleanParam(
      name: 'SKIP_SCHEDULED_RUN',
      defaultValue: false,
      description: 'Set true to skip this scheduled run'
    )
  ])
])

pipeline {
  agent any

  stages {
    stage('Guard: skip?') {
      when { expression { !params.SKIP_SCHEDULED_RUN } }
      steps {
        echo "Proceeding with scheduled recreate..."
      }
    }

    stage('Read last MINIAPPS and trigger deploy') {
      when { expression { !params.SKIP_SCHEDULED_RUN } }
      steps {
        script {
          def jobName = "OLAF_AWS_Deployment/Deployment_job_CIT"
          def job     = Jenkins.instance.getItemByFullName(jobName)
          def lastOK  = job?.getLastSuccessfulBuild()

          if (!lastOK) {
            error "No successful previous build found for ${jobName}"
          }

          def paramsAction = lastOK.getAction(hudson.model.ParametersAction)
          def miniapps     = paramsAction?.getParameter('MINIAPPS_TO_DEPLOY')?.value

          if (!miniapps) {
            error "Previous build missing MINIAPPS_TO_DEPLOY"
          }

          echo "Using MINIAPPS_TO_DEPLOY from last OK run: ${miniapps}"

          build job: jobName, parameters: [
            string(name: 'POD_NAME',            value: 'BCARD'),
            string(name: 'SLOT_NO',             value: '1'),
            string(name: 'MINIAPPS_TO_DEPLOY',  value: miniapps),
            string(name: 'RECREATE_ENV',        value: 'TRUE'),
            string(name: 'APPD_ENABLE',         value: 'true')
          ], wait: false
        }
      }
    }
  }

  post {
    always {
      script {
        if (params.SKIP_SCHEDULED_RUN) {
          echo "Run skipped (SKIP_SCHEDULED_RUN=true)."
        }
      }
    }
  }
}
