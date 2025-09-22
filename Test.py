pipeline {
    agent any

    parameters {
        // --- CIT slot scheduling ---
        choice(name: 'CIT_SLOT_0', choices: ['OFF', 'ON'], description: 'Terminate CIT Slot 0')
        choice(name: 'CIT_SLOT_1', choices: ['OFF', 'ON'], description: 'Terminate CIT Slot 1')
        choice(name: 'CIT_SLOT_2', choices: ['OFF', 'ON'], description: 'Terminate CIT Slot 2')

        // --- SIT slot scheduling ---
        choice(name: 'SIT_SLOT_0', choices: ['OFF', 'ON'], description: 'Terminate SIT Slot 0')
        choice(name: 'SIT_SLOT_1', choices: ['OFF', 'ON'], description: 'Terminate SIT Slot 1')
        choice(name: 'SIT_SLOT_2', choices: ['OFF', 'ON'], description: 'Terminate SIT Slot 2')
    }

    stages {
        stage('Terminate Selected Slots') {
            steps {
                script {
                    def podName = "BCARD"
                    def targetJob = "APIN152377/OLAF/AWS/OLAF_AWS_Deployment/Terminate_Slot"

                    // --- Iterate over environments and slots ---
                    ['CIT', 'SIT'].each { envName ->
                        [0, 1, 2].each { slotNo ->
                            def choiceVal = params["${envName}_SLOT_${slotNo}"]

                            if (choiceVal == 'ON') {
                                echo "⚠️ Scheduling termination for ${envName} slot ${slotNo}"

                                // Trigger downstream terminate job
                                build job: targetJob, parameters: [
                                    string(name: 'POD_NAME', value: podName),
                                    string(name: 'SLOT_NO', value: "${slotNo}"),
                                    string(name: 'ENV', value: envName)
                                ], wait: false
                            } else {
                                echo "⏭ Skipping ${envName} slot ${slotNo} (set to OFF)"
                            }
                        }
                    }
                }
            }
        }
    }
}
