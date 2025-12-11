# Getting Started with IoTix

IoTix is an open-source platform for simulating IoT devices at massive scale. This guide will help you get started quickly.

## Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for development)
- Node.js 18+ (for schema package)
- Kubernetes cluster (optional, for production)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/iotix/iotix.git
cd iotix
```

### 2. Start with Docker Compose

The quickest way to get started is using Docker Compose:

```bash
cd deploy/docker
docker-compose up -d
```

This starts:
- Device Engine API on port 8080
- Test Engine API on port 8081
- Management API on port 8082
- MQTT Broker (Mosquitto) on port 1883
- Kafka on port 9092
- InfluxDB on port 8086
- Grafana on port 3000

### 3. Verify Services

```bash
# Check device engine
curl http://localhost:8080/health

# Check test engine
curl http://localhost:8081/health

# Check management API
curl http://localhost:8082/health
```

### 4. Register a Device Model

Create a device model JSON file:

```json
{
  "id": "temperature-sensor",
  "name": "Temperature Sensor",
  "type": "sensor",
  "protocol": "mqtt",
  "connection": {
    "broker": "mqtt://localhost:1883",
    "topicPattern": "devices/${deviceId}/telemetry"
  },
  "telemetry": [
    {
      "name": "temperature",
      "type": "number",
      "generator": {
        "type": "random",
        "min": 18,
        "max": 28
      },
      "intervalMs": 1000
    }
  ]
}
```

Register it:

```bash
curl -X POST http://localhost:8080/api/v1/models \
  -H "Content-Type: application/json" \
  -d @temperature-sensor.json
```

### 5. Create and Start a Device

```bash
# Create device
curl -X POST http://localhost:8080/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{"modelId": "temperature-sensor"}'

# Start device (replace DEVICE_ID)
curl -X POST http://localhost:8080/api/v1/devices/DEVICE_ID/start
```

### 6. Monitor Telemetry

Subscribe to MQTT to see telemetry:

```bash
mosquitto_sub -h localhost -t 'devices/+/telemetry' -v
```

### 7. View Metrics in Grafana

Open http://localhost:3000 (admin/admin) and explore the IoTix dashboards.

## Creating Device Groups

For large-scale simulations, create device groups:

```bash
# Create 100 devices
curl -X POST http://localhost:8080/api/v1/groups \
  -H "Content-Type: application/json" \
  -d '{"modelId": "temperature-sensor", "count": 100}'

# Start all devices in group
curl -X POST http://localhost:8080/api/v1/groups/GROUP_ID/start
```

## Running Tests

### Robot Framework Tests

```bash
pip install robotframework-iotix
robot --variable DEVICE_ENGINE_URL:http://localhost:8080 examples/tests/
```

### Locust Load Tests

```bash
pip install locust locust-plugins
locust -f examples/locust/iot_device_simulation.py --host mqtt://localhost:1883
```

## Kubernetes Deployment

For production, deploy to Kubernetes using Helm:

```bash
helm repo add iotix https://iotix.github.io/charts
helm install iotix iotix/iotix --namespace iotix --create-namespace
```

See the [Deployment Guide](deployment-guide.md) for detailed instructions.

## Next Steps

- [Device Model Reference](device-model-reference.md) - Complete device model specification
- [API Documentation](api-documentation.md) - REST API reference
- [Deployment Guide](deployment-guide.md) - Production deployment
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
