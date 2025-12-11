# IoTix JMeter Test Plans

JMeter test plans for load testing the IoTix platform.

## Prerequisites

- Apache JMeter 5.5+ installed
- IoTix Device Engine running on localhost:8080

## Test Plans

### iot-device-test.jmx

Basic device lifecycle load test:
- Registers a device model (setup)
- Creates devices
- Starts devices
- Waits for telemetry
- Gets device metrics
- Stops and deletes devices

## Running Tests

### GUI Mode (Development)

```bash
jmeter -t iot-device-test.jmx
```

### CLI Mode (CI/CD)

```bash
jmeter -n -t iot-device-test.jmx \
  -Jbase_url=http://localhost:8080 \
  -Jthreads=100 \
  -Jrampup=30 \
  -l results.jtl \
  -e -o report/
```

### With Docker

```bash
docker run --rm -v $(pwd):/jmeter justb4/jmeter \
  -n -t /jmeter/iot-device-test.jmx \
  -Jbase_url=http://host.docker.internal:8080 \
  -l /jmeter/results.jtl
```

## Configuration

| Property | Default | Description |
|----------|---------|-------------|
| base_url | http://localhost:8080 | Device engine URL |
| threads | 10 | Number of concurrent threads |
| rampup | 10 | Ramp-up period in seconds |

## Distributed Testing

For large-scale tests, run JMeter in distributed mode:

```bash
# On worker nodes
jmeter-server -Djava.rmi.server.hostname=<worker-ip>

# On controller
jmeter -n -t iot-device-test.jmx \
  -R worker1,worker2,worker3 \
  -Jthreads=1000 \
  -l results.jtl
```

## Analyzing Results

Generate HTML report from results:

```bash
jmeter -g results.jtl -o report/
```
