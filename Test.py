     
script {
    // 🔹 Constants
    def envName = "CIT"
    def slotNo  = "1"   // Scheduler is for slot1
    def podName = "BCARD"
    def targetJobPath = "APIN152377/job/OLAF/job/AWS/job/OLAF_AWS_Deployment/job/Deployment_job_CIT"

    // 🔹 Jenkins REST API endpoint for build history
    def jobUrl = "https://jenkins-oss-congo.barclays.intranet/job/${targetJobPath}/api/json?tree=builds[number,result,url,actions[parameters[name,value]]]"

    echo "▶ Scheduler started for env=${envName}, slot=${slotNo}, pod=${podName}"
    echo "Fetching build history from: ${jobUrl}"

    withCredentials([usernamePassword(credentialsId: 'testjob-cred',
                                      usernameVariable: 'USERNAME',
                                      passwordVariable: 'PASSWORD')]) {

        // 🔹 Call Jenkins API with proper quoting
        def response = sh(
            script: """curl -s -u "$USERNAME:$PASSWORD" "${jobUrl}" """,
            returnStdout: true
        ).trim()

        echo "Fetched response (first 200 chars): ${response.take(200)}"

        def data = readJSON text: response

        // 🔹 Find the latest SUCCESS build for the given slot
        def matchingBuild = data.builds.find { b ->
            b.result == 'SUCCESS' && b.actions.any { a ->
                a.parameters?.any { p -> p.name == "SLOT_NO" && p.value == slotNo }
            }
        }

        if (!matchingBuild) {
            error "❌ No successful build found for SLOT_NO=${slotNo}"
        }

        echo "✅ Found last successful build #${matchingBuild.number} for SLOT_NO=${slotNo}"
        echo "Build URL: ${matchingBuild.url}"

        // 🔹 Extract MINIAPPS_TO_DEPLOY from that build
        def miniappsParam = matchingBuild.actions
            .collect { it.parameters }
            .flatten()
            .find { it?.name == "MINIAPPS_TO_DEPLOY" }?.value

        if (!miniappsParam) {
            error "❌ No MINIAPPS_TO_DEPLOY parameter found in build #${matchingBuild.number}"
        }

        echo "📦 Last deployed MINIAPPS_TO_DEPLOY for slot=${slotNo}: ${miniappsParam}"

        // 🔹 Trigger the deployment job with the resolved values
        build job: targetJobPath, parameters: [
            string(name: 'POD_NAME', value: podName),
            string(name: 'SLOT_NO', value: slotNo),
            string(name: 'MINIAPPS_TO_DEPLOY', value: miniappsParam),
            string(name: 'RECREATE_ENV', value: 'TRUE'),
            string(name: 'APPD_ENABLE', value: 'true')
        ], wait: false
    }
}
