/**
 * IoTix Load Test Jenkins Shared Library
 *
 * Run Locust load tests for IoT device simulation.
 *
 * Usage:
 *   iotixLoadTest(
 *       locustFile: 'tests/locust/iot_simulation.py',
 *       users: 1000,
 *       spawnRate: 50,
 *       duration: '5m'
 *   )
 */

def call(Map config = [:]) {
    def deviceEngineUrl = config.deviceEngineUrl ?: 'http://localhost:8080'
    def locustFile = config.locustFile
    def users = config.users ?: 10
    def spawnRate = config.spawnRate ?: 1
    def duration = config.duration ?: '1m'
    def outputDir = config.outputDir ?: 'locust-results'
    def workers = config.workers ?: 0

    if (!locustFile) {
        error "locustFile is required"
    }

    stage('Setup Locust') {
        sh 'pip install locust locust-plugins paho-mqtt'
    }

    stage('Run Load Test') {
        def locustCmd = """
            locust -f ${locustFile} \
                --host ${deviceEngineUrl} \
                --users ${users} \
                --spawn-rate ${spawnRate} \
                --run-time ${duration} \
                --headless \
                --csv ${outputDir}/results \
                --html ${outputDir}/report.html
        """

        if (workers > 0) {
            // Distributed mode
            parallel(
                master: {
                    sh """
                        locust -f ${locustFile} \
                            --master \
                            --expect-workers ${workers} \
                            --host ${deviceEngineUrl} \
                            --users ${users} \
                            --spawn-rate ${spawnRate} \
                            --run-time ${duration} \
                            --headless \
                            --csv ${outputDir}/results \
                            --html ${outputDir}/report.html
                    """
                },
                workers: {
                    for (int i = 0; i < workers; i++) {
                        sh """
                            locust -f ${locustFile} \
                                --worker \
                                --master-host localhost &
                        """
                    }
                    sleep(duration.replaceAll('[^0-9]', '').toInteger() * 60 + 10)
                }
            )
        } else {
            sh locustCmd
        }
    }

    stage('Publish Results') {
        archiveArtifacts artifacts: "${outputDir}/**/*"

        publishHTML(target: [
            allowMissing: true,
            alwaysLinkToLastBuild: true,
            keepAll: true,
            reportDir: outputDir,
            reportFiles: 'report.html',
            reportName: 'Locust Load Test Report'
        ])

        // Parse CSV for metrics
        def statsFile = "${outputDir}/results_stats.csv"
        if (fileExists(statsFile)) {
            def stats = readCSV(file: statsFile)
            if (stats.size() > 1) {
                def aggregated = stats[-1]
                echo "Load Test Results:"
                echo "  Total Requests: ${aggregated[2]}"
                echo "  Failures: ${aggregated[3]}"
                echo "  Median Response Time: ${aggregated[5]}ms"
                echo "  95th Percentile: ${aggregated[8]}ms"
                echo "  Requests/sec: ${aggregated[9]}"
            }
        }
    }
}
