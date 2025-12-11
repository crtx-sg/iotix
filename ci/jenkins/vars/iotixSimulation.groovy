/**
 * IoTix Jenkins Shared Library
 *
 * Run IoT device simulations in Jenkins pipelines.
 *
 * Usage in Jenkinsfile:
 *   @Library('iotix') _
 *
 *   pipeline {
 *       agent any
 *       stages {
 *           stage('IoT Simulation') {
 *               steps {
 *                   iotixSimulation(
 *                       deviceEngineUrl: 'http://device-engine:8080',
 *                       deviceModel: 'models/temperature-sensor.json',
 *                       deviceCount: 100,
 *                       duration: 120
 *                   )
 *               }
 *           }
 *       }
 *   }
 */

def call(Map config = [:]) {
    def deviceEngineUrl = config.deviceEngineUrl ?: 'http://localhost:8080'
    def deviceModel = config.deviceModel
    def deviceCount = config.deviceCount ?: 10
    def duration = config.duration ?: 60
    def testSuite = config.testSuite
    def outputDir = config.outputDir ?: 'iotix-results'

    if (!deviceModel) {
        error "deviceModel is required"
    }

    def modelId = ''
    def groupId = ''

    try {
        stage('Register Device Model') {
            def modelJson = readFile(deviceModel)
            def response = httpRequest(
                url: "${deviceEngineUrl}/api/v1/models",
                httpMode: 'POST',
                contentType: 'APPLICATION_JSON',
                requestBody: modelJson
            )
            def result = readJSON(text: response.content)
            modelId = result.id
            echo "Registered model: ${modelId}"
        }

        stage('Create Device Group') {
            def payload = """{"modelId": "${modelId}", "count": ${deviceCount}}"""
            def response = httpRequest(
                url: "${deviceEngineUrl}/api/v1/groups",
                httpMode: 'POST',
                contentType: 'APPLICATION_JSON',
                requestBody: payload
            )
            def result = readJSON(text: response.content)
            groupId = result.groupId
            echo "Created group: ${groupId} with ${deviceCount} devices"
        }

        stage('Start Simulation') {
            httpRequest(
                url: "${deviceEngineUrl}/api/v1/groups/${groupId}/start",
                httpMode: 'POST'
            )
            echo "Started ${deviceCount} devices"
        }

        stage('Run Simulation') {
            echo "Running simulation for ${duration} seconds..."
            sleep(duration)

            def response = httpRequest(
                url: "${deviceEngineUrl}/api/v1/stats",
                httpMode: 'GET'
            )
            def stats = readJSON(text: response.content)
            echo "Simulation Stats:"
            echo "  Active Devices: ${stats.activeDevices}"
            echo "  Total Messages: ${stats.totalMessagesSent}"
            echo "  Bytes Sent: ${stats.totalBytesSent}"

            // Store metrics for downstream stages
            env.IOTIX_DEVICES = stats.activeDevices.toString()
            env.IOTIX_MESSAGES = stats.totalMessagesSent.toString()
        }

        if (testSuite) {
            stage('Run Robot Tests') {
                sh """
                    pip install robotframework robotframework-iotix
                    robot --outputdir ${outputDir} \
                        --variable DEVICE_ENGINE_URL:${deviceEngineUrl} \
                        ${testSuite}
                """

                robot(
                    outputPath: outputDir,
                    passThreshold: 100.0,
                    unstableThreshold: 80.0
                )
            }
        }

    } finally {
        stage('Cleanup') {
            if (groupId) {
                try {
                    httpRequest(
                        url: "${deviceEngineUrl}/api/v1/groups/${groupId}",
                        httpMode: 'DELETE'
                    )
                    echo "Cleaned up device group: ${groupId}"
                } catch (Exception e) {
                    echo "Warning: Failed to cleanup group: ${e.message}"
                }
            }
        }
    }

    return [
        devicesCreated: env.IOTIX_DEVICES?.toInteger() ?: 0,
        messagesSent: env.IOTIX_MESSAGES?.toInteger() ?: 0
    ]
}
