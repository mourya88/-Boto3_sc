// ---------- parameters ----------
properties([
  parameters([
    booleanParam(
      name: 'SKIP_SCHEDULED_RUN',
      defaultValue: false,
      description: 'Set true to skip this scheduled run'
    )
  ])
])

// ---------- constants for this schedule (CIT / slot 1 / BCARD) ----------
def envName = "CIT"
def slotNo  = "1"
def podName = "BCARD"

// Full project name (from the job’s page → “Full project name”)
def targetJobPath = "APIN152377/OLAF/AWS/OLAF_AWS_Deployment/Deployment_job_CIT"

pipeline {
  agent any

  stages {
    stage('Guard: skip?') {
      when { expression { !params.SKIP_SCHEDULED_RUN } }
      steps { echo "Proceeding with scheduled deploy for ${envName} slot ${slotNo}..." }
    }

    stage('Find last successful build with same SLOT/ENV') {
      when { expression { !params.SKIP_SCHEDULED_RUN } }
      steps {
        script {
          import jenkins.model.Jenkins
          import hudson.model.ParametersAction
          import hudson.model.StringParameterValue
          import hudson.model.Result

          def job = Jenkins.instance.getItemByFullName(targetJobPath)
          if (!job) {
            error "Target job not found: ${targetJobPath}"
          }

          // Find last SUCCESS build where SLOT_NO == slotNo (ENV is implied by job name: CIT)
          def matchingBuild = job.builds.find { b ->
            b?.result == Result.SUCCESS && b.getAction(ParametersAction)?.parameters?.any { p ->
              p instanceof StringParameterValue && p.name == 'SLOT_NO' && "${p.value}" == slotNo
            }
          }

          if (!matchingBuild) {
            error "No successful previous build found for ${targetJobPath} with SLOT_NO=${slotNo}"
          }

          def paramsAction = matchingBuild.getAction(ParametersAction)
          def miniappsParam = paramsAction?.getParameter('MINIAPPS_TO_DEPLOY')?.value
          if (!miniappsParam) {
            error "Previous matching build (#${matchingBuild.number}) has no MINIAPPS_TO_DEPLOY"
          }

          echo "Using MINIAPPS_TO_DEPLOY from build #${matchingBuild.number}: ${miniappsParam}"

          // Trigger the deployment with values resolved above
          build job: targetJobPath, parameters: [
            string(name: 'POD_NAME',           value: podName),
            string(name: 'SLOT_NO',            value: slotNo),
            string(name: 'MINIAPPS_TO_DEPLOY', value: "${miniappsParam}"),
            string(name: 'RECREATE_ENV',       value: 'FALSE'), // as requested
            string(name: 'APPD_ENABLE',        value: 'true')
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
