# IoTix

Open-source IoT device simulation platform for testing at scale. Supports MQTT, CoAP, HTTP, and custom protocols to simulate 1K to 1M+ IoT devices.

## Features

- **Device Virtualization**: JSON-based device models with realistic telemetry generation
- **Multi-Protocol Support**: MQTT, CoAP, HTTP out-of-the-box with extensible adapter pattern
- **Scalable Architecture**: Docker Compose for development, Kubernetes for production
- **Test Automation**: Robot Framework, JMeter, and Locust integration
- **Real-time Monitoring**: Grafana dashboards with InfluxDB metrics storage
- **Multi-tenant Management**: User/tenant management with RBAC and audit logging

## Project Structure

```
iotix/
├── packages/                 # TypeScript/Node.js packages
│   └── device-schema/        # JSON schema definitions and validators
├── services/                 # Python microservices
│   ├── device-engine/        # Core device simulation service (port 8080)
│   ├── test-engine/          # Test execution engine (port 8081)
│   └── management-api/       # REST API for administration (port 8082)
├── examples/                 # Example tests and device models
│   └── device-models/        # Sample device model configurations
├── deploy/                   # Deployment configurations
│   └── docker/               # Docker Compose setup
└── openspec/                 # Project specifications
```

## Quick Start (Docker)

The recommended way to run IoTix is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/iotix/iotix.git
cd iotix

# Start all services
docker compose -f deploy/docker/docker-compose.yml up -d

# View logs
docker compose -f deploy/docker/docker-compose.yml logs -f

# Stop services
docker compose -f deploy/docker/docker-compose.yml down
```

### Service Endpoints

| Service | Port | URL |
|---------|------|-----|
| Device Engine | 8080 | http://localhost:8080 |
| Test Engine | 8081 | http://localhost:8081 |
| Management API | 8082 | http://localhost:8082 |
| MQTT Broker | 1883, 9001 | mqtt://localhost:1883 |
| Kafka | 9092 | localhost:9092 |
| InfluxDB | 8086 | http://localhost:8086 |
| Grafana | 3000 | http://localhost:3000 (admin/admin) |

### Verify Installation

```bash
# Check service health
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8082/health

# List device models
curl http://localhost:8080/api/v1/models

# Access Swagger API documentation
# Device Engine: http://localhost:8080/docs
# Test Engine:   http://localhost:8081/docs
# Management:    http://localhost:8082/docs
```

---

## Device Models

Device models are JSON configurations that define how virtual IoT devices behave. They specify device type, protocol, telemetry attributes, commands, and behaviors.

### Device Model Schema

```json
{
  "id": "string (required)",
  "name": "string (required)",
  "description": "string (optional)",
  "version": "string (optional, semver)",
  "type": "sensor | gateway | actuator | custom (required)",
  "protocol": "mqtt | coap | http (required)",
  "connection": { },
  "telemetry": [ ],
  "commands": [ ],
  "behaviors": [ ],
  "metadata": { }
}
```

### Adding Custom Device Models

1. Create a JSON file in `examples/device-models/` or your custom directory
2. Set the `DEVICE_MODEL_PATH` environment variable to your models directory
3. Restart the Device Engine to load the models

```bash
# Using Docker
docker compose -f deploy/docker/docker-compose.yml up -d

# Using local development
export DEVICE_MODEL_PATH=/path/to/your/device-models
uvicorn src.main:app --reload --port 8080
```

---

## Device Model Examples

### Basic Sensor (Single Parameter)

```json
{
  "id": "simple-temperature",
  "name": "Simple Temperature Sensor",
  "type": "sensor",
  "protocol": "mqtt",
  "connection": {
    "broker": "mqtt-broker",
    "port": 1883,
    "topicPattern": "devices/${deviceId}/telemetry"
  },
  "telemetry": [
    {
      "name": "temperature",
      "type": "number",
      "unit": "celsius",
      "generator": {
        "type": "random",
        "min": 20.0,
        "max": 30.0,
        "distribution": "uniform"
      },
      "intervalMs": 5000
    }
  ]
}
```

### Multi-Parameter Sensor (Temperature, Pressure, Humidity)

```json
{
  "id": "environmental-sensor-v1",
  "name": "Environmental Sensor",
  "description": "Multi-parameter environmental monitoring sensor",
  "version": "1.0.0",
  "type": "sensor",
  "protocol": "mqtt",
  "connection": {
    "broker": "mqtt-broker",
    "port": 1883,
    "clientIdPattern": "env-sensor-${deviceId}",
    "topicPattern": "devices/${deviceId}/telemetry",
    "qos": 1,
    "keepAlive": 60
  },
  "telemetry": [
    {
      "name": "temperature",
      "type": "number",
      "unit": "celsius",
      "generator": {
        "type": "random",
        "min": 15.0,
        "max": 35.0,
        "distribution": "normal",
        "mean": 22.0,
        "stddev": 3.0
      },
      "intervalMs": 5000
    },
    {
      "name": "pressure",
      "type": "number",
      "unit": "hPa",
      "generator": {
        "type": "random",
        "min": 980.0,
        "max": 1040.0,
        "distribution": "normal",
        "mean": 1013.25,
        "stddev": 10.0
      },
      "intervalMs": 10000
    },
    {
      "name": "humidity",
      "type": "number",
      "unit": "percent",
      "generator": {
        "type": "random",
        "min": 20,
        "max": 90,
        "distribution": "uniform"
      },
      "intervalMs": 5000
    },
    {
      "name": "airQualityIndex",
      "type": "integer",
      "unit": "AQI",
      "generator": {
        "type": "random",
        "min": 0,
        "max": 500,
        "distribution": "exponential"
      },
      "intervalMs": 30000
    }
  ],
  "metadata": {
    "manufacturer": "IoTix",
    "model": "ENV-100",
    "firmwareVersion": "2.1.0"
  }
}
```

### Binary Data Sensor (ECG with 200 Samples)

For sensors that produce raw binary data like ECG, accelerometer arrays, or audio samples:

```json
{
  "id": "ecg-monitor-v1",
  "name": "ECG Monitor",
  "description": "ECG monitor producing 200 samples per transmission",
  "version": "1.0.0",
  "type": "sensor",
  "protocol": "mqtt",
  "connection": {
    "broker": "mqtt-broker",
    "port": 1883,
    "clientIdPattern": "ecg-${deviceId}",
    "topicPattern": "devices/${deviceId}/ecg",
    "qos": 1
  },
  "telemetry": [
    {
      "name": "ecgSamples",
      "type": "binary",
      "generator": {
        "type": "custom",
        "handler": "ecg_generator",
        "config": {
          "samples": 200,
          "sampleSize": 16,
          "samplingRate": 500,
          "noiseLevel": 0.05
        }
      },
      "intervalMs": 400
    },
    {
      "name": "heartRate",
      "type": "integer",
      "unit": "bpm",
      "generator": {
        "type": "random",
        "min": 60,
        "max": 100,
        "distribution": "normal",
        "mean": 72,
        "stddev": 8
      },
      "intervalMs": 1000
    },
    {
      "name": "leadStatus",
      "type": "string",
      "generator": {
        "type": "constant",
        "value": "connected"
      },
      "intervalMs": 5000
    }
  ],
  "behaviors": [
    {
      "name": "arrhythmiaAlert",
      "trigger": {
        "type": "condition",
        "condition": "heartRate > 120 || heartRate < 50"
      },
      "action": {
        "type": "publish",
        "topic": "devices/${deviceId}/alerts",
        "payload": {
          "type": "arrhythmia",
          "heartRate": "${heartRate}"
        }
      }
    }
  ],
  "metadata": {
    "manufacturer": "IoTix Medical",
    "model": "ECG-200",
    "channels": 1,
    "resolution": "16-bit"
  }
}
```

### Replay from Historical Data File

```json
{
  "id": "replay-sensor-v1",
  "name": "Historical Data Replay Sensor",
  "type": "sensor",
  "protocol": "mqtt",
  "connection": {
    "broker": "mqtt-broker",
    "port": 1883,
    "topicPattern": "devices/${deviceId}/telemetry"
  },
  "telemetry": [
    {
      "name": "measurement",
      "type": "number",
      "generator": {
        "type": "replay",
        "dataFile": "/data/historical/sensor-readings.csv",
        "column": "value",
        "loop": true
      },
      "intervalMs": 1000
    }
  ]
}
```

### Industrial IoT Gateway

```json
{
  "id": "industrial-gateway-v1",
  "name": "Industrial IoT Gateway",
  "description": "Gateway aggregating data from multiple child sensors",
  "version": "1.0.0",
  "type": "gateway",
  "protocol": "mqtt",
  "connection": {
    "broker": "mqtt-broker",
    "port": 1883,
    "clientIdPattern": "gateway-${deviceId}",
    "topicPattern": "gateways/${deviceId}/data",
    "qos": 2
  },
  "telemetry": [
    {
      "name": "cpuUsage",
      "type": "number",
      "unit": "percent",
      "generator": {
        "type": "random",
        "min": 10,
        "max": 80,
        "distribution": "normal",
        "mean": 35,
        "stddev": 15
      },
      "intervalMs": 10000
    },
    {
      "name": "memoryUsage",
      "type": "number",
      "unit": "percent",
      "generator": {
        "type": "sequence",
        "start": 40,
        "step": 0.1,
        "min": 40,
        "max": 85,
        "wrap": true
      },
      "intervalMs": 10000
    },
    {
      "name": "connectedDevices",
      "type": "integer",
      "generator": {
        "type": "random",
        "min": 5,
        "max": 50,
        "distribution": "uniform"
      },
      "intervalMs": 30000
    }
  ],
  "commands": [
    {
      "name": "reboot",
      "topic": "gateways/${deviceId}/commands/reboot"
    },
    {
      "name": "updateFirmware",
      "topic": "gateways/${deviceId}/commands/update",
      "parameters": [
        {
          "name": "firmwareUrl",
          "type": "string",
          "required": true
        }
      ]
    }
  ],
  "behaviors": [
    {
      "name": "highCpuAlert",
      "trigger": {
        "type": "condition",
        "condition": "cpuUsage > 90"
      },
      "action": {
        "type": "publish",
        "topic": "gateways/${deviceId}/alerts",
        "payload": {
          "type": "highCpu",
          "value": "${cpuUsage}"
        }
      }
    }
  ]
}
```

---

## Generator Types

| Type | Description | Configuration |
|------|-------------|---------------|
| `random` | Random values within range | `min`, `max`, `distribution` (uniform, normal, exponential), `mean`, `stddev` |
| `sequence` | Incrementing/decrementing values | `start`, `step`, `min`, `max`, `wrap` |
| `constant` | Fixed value | `value` |
| `replay` | Replay from data file | `dataFile`, `column`, `loop` |
| `custom` | Custom Python handler | `handler`, `config` |

## Data Types

| Type | Description | Example |
|------|-------------|---------|
| `number` | Floating-point number | 22.5, 1013.25 |
| `integer` | Whole number | 72, 100 |
| `boolean` | True/false | true, false |
| `string` | Text string | "connected", "active" |
| `binary` | Raw binary data | ECG samples, images |

---

## Local Development Setup

For development without Docker:

### Prerequisites

- Python 3.10+
- Node.js 18+ (npm 9.0.0+)

### Install Dependencies

```bash
# Install Node.js packages
npm install
npm run build

# Create Python virtual environment
python3 -m venv iotix-env
source iotix-env/bin/activate  # Linux/macOS

# Install Python dependencies
pip install -r services/device-engine/requirements.txt
pip install -r services/device-engine/requirements-dev.txt
pip install -r services/test-engine/requirements.txt
pip install -r services/management-api/requirements.txt
```

### Run Services Locally

```bash
# Terminal 1: Device Engine
cd services/device-engine
export DEVICE_MODEL_PATH=/path/to/iotix/examples/device-models
uvicorn src.main:app --reload --port 8080

# Terminal 2: Test Engine
cd services/test-engine
uvicorn src.main:app --reload --port 8081

# Terminal 3: Management API
cd services/management-api
uvicorn src.main:app --reload --port 8082
```

---

## Testing

### TypeScript Packages

```bash
npm test                          # All workspace tests
cd packages/device-schema && npm test  # Specific package
```

### Python Services

```bash
source iotix-env/bin/activate

# Device Engine
cd services/device-engine
pytest tests/ -v --cov=src

# Test Engine
cd services/test-engine
pytest tests/ -v --cov=src

# Management API
cd services/management-api
pytest tests/ -v --cov=src
```

---

## API Quick Reference

### Device Engine (Port 8080)

```bash
# List device models
curl http://localhost:8080/api/v1/models

# Create a device
curl -X POST http://localhost:8080/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{"modelId": "temperature-sensor-v1"}'

# Start a device
curl -X POST http://localhost:8080/api/v1/devices/{device_id}/start

# Get device metrics
curl http://localhost:8080/api/v1/devices/{device_id}/metrics
```

### Test Engine (Port 8081)

```bash
# Create a test run
curl -X POST http://localhost:8081/api/v1/runs \
  -H "Content-Type: application/json" \
  -d '{"testCases": ["test_device_creation"]}'

# Get test run status
curl http://localhost:8081/api/v1/runs/{run_id}

# Get test report
curl http://localhost:8081/api/v1/runs/{run_id}/report?format=html
```

### Management API (Port 8082)

```bash
# Login (default admin user)
curl -X POST http://localhost:8082/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@iotix.local", "password": "admin"}'

# Use the returned token for authenticated requests
curl http://localhost:8082/api/v1/users \
  -H "Authorization: Bearer <TOKEN>"
```

---

## Configuration

### Environment Variables

#### Device Engine

| Variable | Default | Description |
|----------|---------|-------------|
| `DEVICE_MODEL_PATH` | `/app/device-models` | Path to device model JSON files |
| `MQTT_BROKER_HOST` | `localhost` | MQTT broker hostname |
| `MQTT_BROKER_PORT` | `1883` | MQTT broker port |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka bootstrap servers |
| `INFLUXDB_URL` | `http://localhost:8086` | InfluxDB URL |
| `INFLUXDB_TOKEN` | `` | InfluxDB API token |
| `INFLUXDB_ORG` | `iotix` | InfluxDB organization |
| `INFLUXDB_BUCKET` | `telemetry` | InfluxDB bucket name |
| `LOG_LEVEL` | `INFO` | Logging level |

#### Test Engine

| Variable | Default | Description |
|----------|---------|-------------|
| `DEVICE_ENGINE_URL` | `http://localhost:8080` | Device Engine URL |
| `INFLUXDB_URL` | `http://localhost:8086` | InfluxDB URL |
| `INFLUXDB_TOKEN` | `` | InfluxDB API token |
| `INFLUXDB_ORG` | `iotix` | InfluxDB organization |
| `INFLUXDB_BUCKET` | `telemetry` | InfluxDB bucket name |

#### Management API

| Variable | Default | Description |
|----------|---------|-------------|
| `DEVICE_ENGINE_URL` | `http://localhost:8080` | Device Engine URL |
| `TEST_ENGINE_URL` | `http://localhost:8081` | Test Engine URL |
| `JWT_SECRET` | `change-me-in-production` | JWT signing secret |

### Default Credentials (Development)

#### InfluxDB

| Setting | Value |
|---------|-------|
| URL | http://localhost:8086 |
| Username | `admin` |
| Password | `adminpassword` |
| Organization | `iotix` |
| Bucket | `telemetry` |
| API Token | `iotix-dev-token` |

#### Grafana

| Setting | Value |
|---------|-------|
| URL | http://localhost:3000 |
| Username | `admin` |
| Password | `admin` |

#### Management API

| Setting | Value |
|---------|-------|
| URL | http://localhost:8082 |
| Email | `admin@iotix.local` |
| Password | `admin` |

> **Warning**: These are development credentials. For production deployments, change all passwords and tokens, and store them securely using Kubernetes Secrets, HashiCorp Vault, or your cloud provider's secrets manager.

---

## Code Quality

```bash
# TypeScript
npm run lint
npm run format

# Python (per service)
black src/ tests/
ruff check src/ tests/
mypy src/
```

---

## License

Apache-2.0
