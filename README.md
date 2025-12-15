# IoTix

Open-source IoT device simulation platform for testing at scale. Supports MQTT, CoAP, HTTP, and custom protocols to simulate 1K to 1M+ IoT devices.

## Features

- **Device Virtualization**: JSON-based device models with realistic telemetry generation
- **Multi-Protocol Support**: MQTT, CoAP, HTTP out-of-the-box with extensible adapter pattern
- **Scalable Architecture**: Docker Compose for development, Kubernetes for production
- **Test Automation**: Robot Framework, JMeter, and Locust integration
- **Real-time Monitoring**: Grafana dashboards with InfluxDB metrics storage
- **Multi-tenant Management**: User/tenant management with RBAC and audit logging

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   CLIENTS                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Web UI   │  │ REST API │  │   CLI    │  │ CI/CD    │  │ External Systems │   │
│  │          │  │ Clients  │  │          │  │ Pipelines│  │ (ThingsBoard)    │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘   │
└───────┼─────────────┼─────────────┼─────────────┼─────────────────┼─────────────┘
        │             │             │             │                 │
        └─────────────┴──────┬──────┴─────────────┴─────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────────────────────┐
│                    MANAGEMENT LAYER                                              │
│  ┌─────────────────────────┴─────────────────────────┐                          │
│  │              Management API (:8082)                │                          │
│  │  ┌───────────┐ ┌───────────┐ ┌─────────────────┐  │                          │
│  │  │   Auth    │ │   RBAC    │ │  Audit Logging  │  │                          │
│  │  │  (JWT)    │ │           │ │                 │  │                          │
│  │  └───────────┘ └───────────┘ └─────────────────┘  │                          │
│  │  ┌───────────┐ ┌───────────┐ ┌─────────────────┐  │                          │
│  │  │   User    │ │  Tenant   │ │    API Key      │  │                          │
│  │  │Management │ │Management │ │   Management    │  │                          │
│  │  └───────────┘ └───────────┘ └─────────────────┘  │                          │
│  └───────────────────────┬───────────────────────────┘                          │
└──────────────────────────┼──────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────────────────────────────────┐
│  TEST LAYER   │  │ DEVICE LAYER  │  │              INFRASTRUCTURE               │
│               │  │               │  │                                           │
│ ┌───────────┐ │  │ ┌───────────┐ │  │  ┌─────────────┐    ┌─────────────────┐  │
│ │   Test    │ │  │ │  Device   │ │  │  │    Kafka    │    │    InfluxDB     │  │
│ │  Engine   │─┼──┼▶│  Engine   │─┼──┼─▶│   (:9092)   │    │    (:8086)      │  │
│ │  (:8081)  │ │  │ │  (:8080)  │ │  │  │             │    │                 │  │
│ └───────────┘ │  │ └─────┬─────┘ │  │  │  Telemetry  │    │  Time-series    │  │
│               │  │       │       │  │  │   Events    │    │    Metrics      │  │
│ ┌───────────┐ │  │       │       │  │  └─────────────┘    └────────┬────────┘  │
│ │  Suites   │ │  │       │       │  │                              │           │
│ │  Runs     │ │  │       ▼       │  │                              ▼           │
│ │ Schedules │ │  │ ┌───────────┐ │  │                     ┌─────────────────┐  │
│ │  Reports  │ │  │ │ Protocol  │ │  │                     │     Grafana     │  │
│ └───────────┘ │  │ │ Adapters  │ │  │                     │    (:3000)      │  │
└───────────────┘  │ │           │ │  │                     │                 │  │
                   │ │┌─────────┐│ │  │                     │   Dashboards    │  │
                   │ ││  MQTT   ││ │  │                     │    Alerts       │  │
                   │ │└────┬────┘│ │  │                     └─────────────────┘  │
                   │ │┌─────────┐│ │  │                                          │
                   │ ││  CoAP   ││ │  └──────────────────────────────────────────┘
                   │ │└─────────┘│ │
                   │ │┌─────────┐│ │
                   │ ││  HTTP   ││ │
                   │ │└─────────┘│ │
                   │ └─────┬─────┘ │
                   └───────┼───────┘
                           │
                           ▼
              ┌────────────────────────┐
              │     MQTT Broker        │
              │   (Mosquitto :1883)    │
              │                        │
              │  ┌──────────────────┐  │
              │  │ Virtual Devices  │  │
              │  │    publish to    │  │
              │  │   MQTT topics    │  │
              │  └──────────────────┘  │
              └────────────────────────┘
```

### Component Interactions

#### Core Services

| Component | Port | Description |
|-----------|------|-------------|
| **Device Engine** | 8080 | Core simulation service. Creates and manages virtual IoT devices, generates telemetry data, and publishes to MQTT/CoAP/HTTP endpoints. |
| **Test Engine** | 8081 | Test execution service. Manages test suites, runs, schedules, and generates reports. Integrates with Robot Framework, JMeter, and Locust. |
| **Management API** | 8082 | Administration service. Handles user authentication (JWT), RBAC, tenant management, API keys, and audit logging. |

#### Infrastructure Services

| Component | Port | Description |
|-----------|------|-------------|
| **MQTT Broker** | 1883 | Eclipse Mosquitto message broker. Virtual devices publish telemetry to MQTT topics. External systems can subscribe to receive data. |
| **Kafka** | 9092 | High-throughput message streaming. Used for telemetry events and inter-service communication at scale. |
| **InfluxDB** | 8086 | Time-series database. Stores device metrics, telemetry history, and performance data. |
| **Grafana** | 3000 | Visualization and monitoring. Provides dashboards for real-time metrics, device status, and alerting. |

### Data Flow

```
1. DEVICE CREATION
   User/API ──▶ Management API ──▶ Device Engine ──▶ Create Virtual Device

2. TELEMETRY GENERATION
   Device Engine ──▶ Generate Data ──▶ Protocol Adapter ──▶ MQTT Broker
                                                         ──▶ Kafka (events)
                                                         ──▶ InfluxDB (metrics)

3. MONITORING
   InfluxDB ──▶ Grafana ──▶ Dashboards/Alerts ──▶ User

4. TEST EXECUTION
   User/CI ──▶ Test Engine ──▶ Device Engine ──▶ Run Tests ──▶ Generate Reports
```

### Protocol Support

| Protocol | Port | Use Case |
|----------|------|----------|
| **MQTT** | 1883 | Primary IoT protocol. Lightweight pub/sub messaging for sensors and actuators. |
| **CoAP** | 5683 | Constrained devices. UDP-based protocol for resource-limited IoT devices. |
| **HTTP** | 8080 | REST APIs. Standard HTTP/HTTPS for device management and data ingestion. |

---

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
# Check all services are running
docker compose ps

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

### Troubleshooting

**Grafana not starting (permission denied)**

If Grafana fails to start with permission errors on provisioning files, the docker-compose is configured to run Grafana as root (`user: "0"`) to avoid these issues. If you still encounter problems:

```bash
# Fix permissions manually
chmod -R 755 deploy/docker/config/grafana/provisioning
chmod 644 deploy/docker/config/grafana/provisioning/**/*.yml
chmod 644 deploy/docker/config/grafana/provisioning/**/*.json

# Restart Grafana
docker compose restart grafana
```

**"Unknown device model" error when creating devices**

Device models must be registered before creating device instances. Either:
1. Models are auto-loaded from the `device-models` volume on startup
2. Register models manually via the API:

```bash
# Check existing models
curl http://localhost:8080/api/v1/models

# Register a model if none exist
curl -X POST http://localhost:8080/api/v1/models \
  -H "Content-Type: application/json" \
  -d '{
    "id": "temperature-sensor-v1",
    "name": "Temperature Sensor",
    "type": "sensor",
    "protocol": "mqtt",
    "connection": {
      "broker": "mqtt-broker",
      "port": 1883,
      "topicPattern": "sensors/{deviceId}/temperature"
    },
    "telemetry": [{
      "name": "temperature",
      "type": "number",
      "unit": "celsius",
      "intervalMs": 5000,
      "generator": {
        "type": "random",
        "min": 18.0,
        "max": 28.0
      }
    }]
  }'
```

Models registered via API are automatically persisted to disk and will survive container restarts.

**Pydantic validation errors on API responses**

If you see validation errors like "Field required" with snake_case field names, ensure you've rebuilt the Docker image after code changes:

```bash
cd deploy/docker
docker compose down
docker compose build device-engine
docker compose up -d
```

**InfluxDB metrics not appearing in Grafana**

Ensure the device-engine has the correct InfluxDB credentials. Check the environment variables:

```bash
docker compose exec device-engine env | grep INFLUX
```

Should show:
```
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=iotix-dev-token
INFLUXDB_ORG=iotix
INFLUXDB_BUCKET=telemetry
```

If missing, the docker-compose.yml should include these environment variables for the device-engine service.

**Kafka not starting (invalid cluster ID)**

If Kafka fails with cluster ID errors, remove the Kafka data volume and restart:

```bash
docker compose down
docker volume rm docker_kafka-data
docker compose up -d
```

**Code changes not reflected after restart**

Docker caches built images. After making code changes, rebuild the affected service:

```bash
# Rebuild a specific service
docker compose build device-engine

# Or rebuild all services
docker compose build

# Then restart
docker compose up -d
```

**Grafana login fails with admin/admin**

If you previously logged in and changed the password (or were prompted to), the password is persisted in the Grafana data volume. To reset:

```bash
cd deploy/docker

# Stop, remove container and volume, then restart
docker compose rm -f grafana
docker volume rm docker_grafana-data
docker compose up -d grafana
```

Now login with `admin`/`admin`. You can skip the password change prompt or set a new password.

**MQTT broker connection timeout**

If devices fail to start with "Timeout connecting to MQTT broker", ensure the device model has the correct broker hostname. For Docker deployments, the broker should be `mqtt-broker` (the Docker service name), not `mosquitto` or `localhost`:

```bash
# Check broker in registered models
curl -s http://localhost:8080/api/v1/models | jq '.[].connection.broker'

# Should show "mqtt-broker" for all models
```

If models have incorrect broker, delete the device-models volume and rebuild:

```bash
docker compose down
docker volume rm docker_device-models-data
docker compose build device-engine
docker compose up -d
```

---

## Quick Reference Commands

### Device Models

```bash
# List all registered models
curl http://localhost:8080/api/v1/models

# Get a specific model
curl http://localhost:8080/api/v1/models/temperature-sensor-v1

# Register a new model
curl -X POST http://localhost:8080/api/v1/models \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my-sensor-v1",
    "name": "My Sensor",
    "type": "sensor",
    "protocol": "mqtt",
    "connection": {
      "broker": "mqtt-broker",
      "port": 1883,
      "topicPattern": "sensors/{deviceId}/data"
    },
    "telemetry": [{
      "name": "value",
      "type": "number",
      "intervalMs": 5000,
      "generator": {"type": "random", "min": 0, "max": 100}
    }]
  }'
```

### Device Groups

```bash
# Create a device group
curl -X POST http://localhost:8080/api/v1/groups \
  -H "Content-Type: application/json" \
  -d '{
    "modelId": "temperature-sensor-v1",
    "count": 10,
    "groupId": "my-sensors"
  }'

# Start a device group
curl -X POST http://localhost:8080/api/v1/groups/my-sensors/start

# Start with launch strategy (linear ramp-up)
curl -X POST "http://localhost:8080/api/v1/groups/my-sensors/start" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "linear",
    "delayMs": 100
  }'

# Stop a device group
curl -X POST http://localhost:8080/api/v1/groups/my-sensors/stop

# Delete a device group
curl -X DELETE http://localhost:8080/api/v1/groups/my-sensors

# Simulate device dropouts
curl -X POST http://localhost:8080/api/v1/groups/my-sensors/dropout \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "linear",
    "percentage": 20,
    "delayMs": 1000
  }'
```

### Devices

```bash
# List all devices
curl http://localhost:8080/api/v1/devices

# List devices in a group
curl "http://localhost:8080/api/v1/devices?groupId=my-sensors"

# Get device details
curl http://localhost:8080/api/v1/devices/device-0

# Get device metrics
curl http://localhost:8080/api/v1/devices/device-0/metrics

# Start/stop individual device
curl -X POST http://localhost:8080/api/v1/devices/device-0/start
curl -X POST http://localhost:8080/api/v1/devices/device-0/stop
```

### Engine Stats

```bash
# Get engine statistics
curl http://localhost:8080/api/v1/stats

# Health check
curl http://localhost:8080/health
```

### InfluxDB Queries

Access InfluxDB at http://localhost:8086 (admin/adminpassword)

```flux
// Query telemetry data (last 15 minutes)
from(bucket: "telemetry")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "telemetry")
  |> filter(fn: (r) => r._field == "temperature")

// Query by device
from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "telemetry")
  |> filter(fn: (r) => r.device_id == "device-0")

// Query device events
from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "device_events")

// Query engine stats
from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "engine_stats")

// Aggregate temperature by device (mean per 1 minute)
from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "telemetry")
  |> filter(fn: (r) => r._field == "temperature")
  |> aggregateWindow(every: 1m, fn: mean)
  |> yield(name: "mean_temperature")
```

### InfluxDB Schema

InfluxDB stores time-series data in the `telemetry` bucket with the following measurements:

| Measurement | Tags | Fields | Description |
|-------------|------|--------|-------------|
| `telemetry` | device_id, model_id, group_id | temperature, humidity, pressure, unit | Device telemetry readings |
| `engine_stats` | (none) | active_devices, total_messages, total_bytes, active_groups | Engine-wide statistics (updated every 5s) |
| `device_events` | device_id, model_id, event_type, group_id | value | Device lifecycle events (created, started, stopped) |
| `connections` | device_id, protocol | connected, latency_ms | Connection status and latency |

### InfluxDB Data Retention

| Bucket | Default Retention | Description |
|--------|-------------------|-------------|
| `telemetry` | infinite | Device metrics persist forever until manually deleted |
| `_monitoring` | 7 days | Internal InfluxDB monitoring |
| `_tasks` | 3 days | Internal task data |

**Data persistence:**
- Container restart: Data persists (stored in Docker volume)
- `docker compose down`: Data persists (volume remains)
- `docker compose down -v`: Data is **deleted** (removes volumes)

**Change retention policy** (e.g., 30 days):

```bash
# Get bucket ID
docker compose exec influxdb influx bucket list --org iotix --token iotix-dev-token

# Set 30-day retention (720 hours)
docker compose exec influxdb influx bucket update \
  --id <BUCKET_ID> \
  --retention 720h \
  --org iotix \
  --token iotix-dev-token
```

**Reset all InfluxDB data:**

```bash
docker compose down
docker volume rm docker_influxdb-data
docker compose up -d
```

### Grafana

Access Grafana at http://localhost:3000 (admin/admin)

**Pre-configured dashboard**: Dashboards > Browse > IoTix Device Telemetry

**Manual data source setup** (if needed):
1. Go to Configuration > Data Sources > Add data source
2. Select InfluxDB
3. Configure:
   - Query Language: Flux
   - URL: http://influxdb:8086
   - Organization: iotix
   - Token: iotix-dev-token
   - Default Bucket: telemetry

### Docker Commands

```bash
# Start all services
cd deploy/docker
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f device-engine
docker compose logs -f grafana

# Restart a service
docker compose restart device-engine

# Stop all services
docker compose down

# Full reset (removes all data)
docker compose down -v
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

## Launching Devices at Scale

IoTix supports launching thousands of devices with configurable launch strategies to control resource utilization and simulate realistic deployment scenarios.

### Creating a Device Group

Create a group of devices from a model:

```bash
# Create 5000 temperature sensors
curl -X POST http://localhost:8080/api/v1/groups \
  -H "Content-Type: application/json" \
  -d '{
    "modelId": "temperature-sensor-v1",
    "count": 5000,
    "groupId": "temp-sensors-batch-1",
    "idPattern": "temp-sensor-{index}"
  }'
```

### Launch Strategies

When starting a device group, you can choose from four launch strategies:

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `immediate` | Start all devices at once | Maximum throughput, sufficient resources |
| `linear` | Fixed delay between each device | Controlled ramp-up, predictable load |
| `batch` | Start in batches with delay between batches | Balance between speed and resource management |
| `exponential` | Exponentially increasing delay | Gradual warm-up, stress testing |

### Strategy Examples

#### 1. Immediate (All at Once)

Start all 5000 devices simultaneously:

```bash
curl -X POST http://localhost:8080/api/v1/groups/temp-sensors-batch-1/start \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "immediate"
  }'
```

#### 2. Linear (Fixed Delay)

Start devices with 10ms delay between each:

```bash
curl -X POST http://localhost:8080/api/v1/groups/temp-sensors-batch-1/start \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "linear",
    "delayMs": 10
  }'
```

Timeline for 5000 devices: ~50 seconds total

#### 3. Batch (Groups with Delay)

Start 100 devices at a time, with 1 second between batches:

```bash
curl -X POST http://localhost:8080/api/v1/groups/temp-sensors-batch-1/start \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "batch",
    "batchSize": 100,
    "delayMs": 1000
  }'
```

Timeline for 5000 devices: 50 batches × 1s = ~50 seconds

#### 4. Exponential (Gradual Ramp-up)

Start with small delay, increasing exponentially:

```bash
curl -X POST http://localhost:8080/api/v1/groups/temp-sensors-batch-1/start \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "exponential",
    "delayMs": 1,
    "exponentBase": 1.1,
    "maxDelayMs": 5000
  }'
```

Delay pattern: 1ms, 1.1ms, 1.21ms, 1.33ms... (capped at 5000ms)

### Launch Configuration Reference

```json
{
  "strategy": "batch",
  "delayMs": 1000,
  "batchSize": 100,
  "maxDelayMs": 60000,
  "exponentBase": 1.5
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `strategy` | string | `immediate` | Launch strategy: `immediate`, `linear`, `batch`, `exponential` |
| `delayMs` | integer | `0` | Base delay in milliseconds |
| `batchSize` | integer | `100` | Number of devices per batch (for `batch` strategy) |
| `maxDelayMs` | integer | `60000` | Maximum delay cap (for `exponential` strategy) |
| `exponentBase` | float | `1.5` | Exponent multiplier (for `exponential` strategy) |

### Scaling Recommendations

| Device Count | Recommended Strategy | Configuration |
|--------------|---------------------|---------------|
| 1-100 | `immediate` | Default |
| 100-1,000 | `linear` | `delayMs: 10` |
| 1,000-10,000 | `batch` | `batchSize: 100, delayMs: 500` |
| 10,000-100,000 | `batch` | `batchSize: 500, delayMs: 1000` |
| 100,000+ | `batch` | `batchSize: 1000, delayMs: 2000` + Kubernetes HPA |

### Managing Device Groups

```bash
# List devices in a group
curl "http://localhost:8080/api/v1/devices?groupId=temp-sensors-batch-1"

# Stop all devices in a group
curl -X POST http://localhost:8080/api/v1/groups/temp-sensors-batch-1/stop

# Delete a group and all its devices
curl -X DELETE http://localhost:8080/api/v1/groups/temp-sensors-batch-1
```

### Monitoring Scale Launches

During large-scale launches, monitor progress via:

```bash
# Get engine statistics
curl http://localhost:8080/api/v1/stats

# Response includes:
# - deviceCount: Total devices
# - runningDeviceCount: Currently running
# - messagesSent: Total messages published
```

Use Grafana dashboards at http://localhost:3000 for real-time visualization of:
- Device connection rates
- Telemetry throughput
- Resource utilization
- Error rates

---

## Device Dropout Simulation

IoTix supports simulating device dropouts and failures for chaos engineering and resilience testing. This allows you to test how your IoT backend handles various failure scenarios.

### Dropout Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `immediate` | All specified devices drop at once | Mass failure, network outage simulation |
| `linear` | Fixed delay between each dropout | Gradual degradation testing |
| `exponential` | Exponentially increasing dropout rate | Cascading failure simulation |
| `random` | Random dropouts within a time window | Realistic unpredictable failure patterns |

### Basic Dropout Examples

```bash
# Drop 50% of devices in a group immediately
curl -X POST http://localhost:8080/api/v1/groups/sensor-group/dropout \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "immediate",
    "percentage": 50
  }'

# Drop 100 devices with linear delay (1 second between each)
curl -X POST http://localhost:8080/api/v1/groups/sensor-group/dropout \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "linear",
    "count": 100,
    "delayMs": 1000
  }'

# Exponential dropout (accelerating failure cascade)
curl -X POST http://localhost:8080/api/v1/groups/sensor-group/dropout \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "exponential",
    "percentage": 30,
    "delayMs": 100,
    "exponentBase": 1.5
  }'

# Random dropouts over 60 seconds
curl -X POST http://localhost:8080/api/v1/groups/sensor-group/dropout \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "random",
    "percentage": 25,
    "durationMs": 60000
  }'
```

### Dropout with Automatic Reconnection

Simulate temporary failures where devices automatically recover:

```bash
# Drop 20% of devices, reconnect after 30 seconds
curl -X POST http://localhost:8080/api/v1/groups/sensor-group/dropout \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "linear",
    "percentage": 20,
    "delayMs": 500,
    "reconnect": true,
    "reconnectDelayMs": 30000
  }'
```

### Dropout Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy` | string | `linear` | Dropout strategy: `immediate`, `linear`, `exponential`, `random` |
| `count` | integer | - | Absolute number of devices to drop (takes precedence over percentage) |
| `percentage` | float | - | Percentage of devices to drop (0-100) |
| `delayMs` | integer | `1000` | Base delay between dropouts in milliseconds |
| `durationMs` | integer | `60000` | Total duration for random strategy |
| `exponentBase` | float | `1.5` | Exponent multiplier for exponential strategy |
| `reconnect` | boolean | `false` | Whether devices should reconnect after dropout |
| `reconnectDelayMs` | integer | `0` | Delay before reconnection attempt |

### Chaos Engineering Scenarios

**Scenario 1: Network Partition**
```bash
# Simulate network partition affecting 30% of devices
curl -X POST http://localhost:8080/api/v1/groups/production-sensors/dropout \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "immediate",
    "percentage": 30,
    "reconnect": true,
    "reconnectDelayMs": 120000
  }'
```

**Scenario 2: Cascading Failure**
```bash
# Simulate cascading failure starting slow then accelerating
curl -X POST http://localhost:8080/api/v1/groups/critical-sensors/dropout \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "exponential",
    "percentage": 50,
    "delayMs": 1000,
    "exponentBase": 2.0
  }'
```

**Scenario 3: Random Real-World Failures**
```bash
# Simulate random device failures over 5 minutes
curl -X POST http://localhost:8080/api/v1/groups/field-devices/dropout \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "random",
    "count": 200,
    "durationMs": 300000,
    "reconnect": true,
    "reconnectDelayMs": 60000
  }'
```

---

## Hybrid Device Support (Physical Devices)

IoTix supports integrating real physical IoT devices alongside simulated devices. This allows you to:

- **Mix simulated and physical devices** in the same device groups
- **Forward telemetry from external sources** (MQTT brokers, HTTP webhooks) to InfluxDB
- **Compare simulated vs physical device behavior** side-by-side in Grafana
- **Test IoT backends** with a blend of predictable simulated data and real-world physical data

### How Proxy Devices Work

Proxy devices act as passthrough adapters that:

1. **Subscribe to external telemetry sources** (external MQTT topics or HTTP webhooks)
2. **Forward received data to InfluxDB** with `source=physical` tag
3. **Appear in dashboards** alongside simulated devices

### Creating a Proxy Device

First, register a proxy device model:

```bash
# Register a proxy device model
curl -X POST http://localhost:8080/api/v1/models \
  -H "Content-Type: application/json" \
  -d '{
    "id": "physical-sensor-proxy",
    "name": "Physical Sensor Proxy",
    "type": "proxy",
    "protocol": "http",
    "telemetry": [],
    "metadata": {"category": "proxy"}
  }'
```

Then create a device instance:

```bash
# Create a proxy device
curl -X POST http://localhost:8080/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{
    "modelId": "physical-sensor-proxy",
    "deviceId": "my-physical-sensor-1"
  }'
```

### Binding to External Sources

#### HTTP Webhook Binding

Bind a proxy device to receive telemetry via HTTP POST:

```bash
# Bind to HTTP webhook
curl -X POST http://localhost:8080/api/v1/devices/my-physical-sensor-1/bind \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "protocol": "http"
    }
  }'

# Response includes the webhook URL
# {
#   "deviceId": "my-physical-sensor-1",
#   "status": "bound",
#   "webhookUrl": "/api/v1/webhooks/my-physical-sensor-1"
# }
```

External devices can then POST telemetry to the webhook:

```bash
# Send telemetry from external device
curl -X POST http://localhost:8080/api/v1/webhooks/my-physical-sensor-1 \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 23.5,
    "humidity": 45.2,
    "batteryLevel": 87
  }'
```

#### MQTT Binding

Bind a proxy device to subscribe to an external MQTT topic:

```bash
# Bind to external MQTT broker
curl -X POST http://localhost:8080/api/v1/devices/my-physical-sensor-1/bind \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "protocol": "mqtt",
      "broker": "external-broker.example.com",
      "port": 1883,
      "topic": "devices/physical-001/telemetry",
      "qos": 1,
      "username": "iotix-reader"
    }
  }'
```

### Unbinding Devices

```bash
# Unbind a device from its external source
curl -X POST http://localhost:8080/api/v1/devices/my-physical-sensor-1/unbind
```

### Checking Binding Status

```bash
# Get binding status
curl http://localhost:8080/api/v1/devices/my-physical-sensor-1/binding

# Response
# {
#   "bound": true,
#   "protocol": "http",
#   "webhookUrl": "/api/v1/webhooks/my-physical-sensor-1",
#   "boundAt": "2025-01-15T10:30:00Z"
# }
```

### Hybrid Device Groups

You can create groups containing both simulated and proxy devices:

```bash
# Create simulated devices in a group
curl -X POST http://localhost:8080/api/v1/groups \
  -H "Content-Type: application/json" \
  -d '{
    "modelId": "temperature-sensor-v1",
    "count": 10,
    "groupId": "hybrid-sensors"
  }'

# Add a proxy device to the same group
curl -X POST http://localhost:8080/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{
    "modelId": "physical-sensor-proxy",
    "deviceId": "physical-sensor-001",
    "groupId": "hybrid-sensors"
  }'
```

**Note:** Proxy devices are automatically excluded from dropout simulations since they represent real physical devices.

### Source Tagging

All metrics are tagged with their source:

| Source | Description |
|--------|-------------|
| `simulated` | Data from virtual devices (default) |
| `physical` | Data from proxy devices (external sources) |

### Grafana Filtering

The Grafana dashboard includes a `source` filter variable. Use it to:

- View **all data** (simulated + physical)
- View **only simulated** device data
- View **only physical** device data

Dashboard panels include:
- **Simulated Devices** - Count of running simulated devices
- **Physical Devices** - Count of running proxy/physical devices
- **Telemetry by Source** - Pie chart showing data distribution

### InfluxDB Queries by Source

```flux
// Query only physical device telemetry
from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "telemetry")
  |> filter(fn: (r) => r.source == "physical")

// Query only simulated device telemetry
from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "telemetry")
  |> filter(fn: (r) => r.source == "simulated")

// Compare simulated vs physical temperature readings
from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "telemetry" and r._field == "temperature")
  |> group(columns: ["source"])
  |> aggregateWindow(every: 1m, fn: mean)
```

### Engine Statistics

The `/api/v1/stats` endpoint now includes:

```json
{
  "total_devices": 15,
  "running_devices": 12,
  "running_simulated": 10,
  "running_physical": 2,
  "total_proxy_devices": 3,
  "total_groups": 2,
  "total_models": 5
}
```

### Testing Hybrid Device Support

Follow these steps to test the hybrid device support after deployment:

#### Step 1: Rebuild and Restart Services

```bash
cd deploy/docker

# Stop existing services
docker compose down

# Rebuild the device-engine with new changes
docker compose build device-engine

# Start all services
docker compose up -d

# Verify services are running
docker compose ps
```

#### Step 2: Verify Services are Ready

```bash
# Check device-engine health
curl http://localhost:8080/health

# Check available models
curl http://localhost:8080/api/v1/models
```

#### Step 3: Run Simulated Device Test

```bash
# Create a group of simulated temperature sensors
curl -X POST http://localhost:8080/api/v1/groups \
  -H "Content-Type: application/json" \
  -d '{
    "modelId": "temperature-sensor-v1",
    "count": 5,
    "groupId": "test-sensors"
  }'

# Start the device group
curl -X POST http://localhost:8080/api/v1/groups/test-sensors/start

# Check engine stats (should show running_simulated: 5)
curl http://localhost:8080/api/v1/stats
```

#### Step 4: Test Proxy Device

```bash
# Register proxy device model (if not auto-loaded)
curl -X POST http://localhost:8080/api/v1/models \
  -H "Content-Type: application/json" \
  -d '{
    "id": "physical-sensor-proxy",
    "name": "Physical Sensor Proxy",
    "type": "proxy",
    "protocol": "http",
    "telemetry": [],
    "metadata": {"category": "proxy"}
  }'

# Create a proxy device
curl -X POST http://localhost:8080/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{
    "modelId": "physical-sensor-proxy",
    "deviceId": "physical-test-1"
  }'

# Bind to HTTP webhook
curl -X POST http://localhost:8080/api/v1/devices/physical-test-1/bind \
  -H "Content-Type: application/json" \
  -d '{"config": {"protocol": "http"}}'

# Send test telemetry via webhook
curl -X POST http://localhost:8080/api/v1/webhooks/physical-test-1 \
  -H "Content-Type: application/json" \
  -d '{"temperature": 25.5, "humidity": 60}'

# Check stats (should show running_physical: 1)
curl http://localhost:8080/api/v1/stats
```

#### Step 5: View in Grafana

1. Open http://localhost:3000 (admin/admin)
2. Go to Dashboards → IoTix Device Overview
3. You should see:
   - **Simulated Devices**: 5
   - **Physical Devices**: 1
   - **Telemetry by Source**: pie chart showing both sources
   - Temperature and humidity charts with data from both sources

#### Step 6: View Logs

```bash
# Watch device-engine logs
docker compose logs -f device-engine
```

#### Step 7: Cleanup

```bash
# Stop and delete the test group
curl -X POST http://localhost:8080/api/v1/groups/test-sensors/stop
curl -X DELETE http://localhost:8080/api/v1/groups/test-sensors

# Unbind and delete proxy device
curl -X POST http://localhost:8080/api/v1/devices/physical-test-1/unbind
curl -X DELETE http://localhost:8080/api/v1/devices/physical-test-1
```

### Troubleshooting Physical Device Connectivity

**Webhook not receiving data**

1. Ensure the device is bound:
   ```bash
   curl http://localhost:8080/api/v1/devices/{device_id}/binding
   ```

2. Check the webhook URL is correct (returned in bind response)

3. Verify the POST request includes `Content-Type: application/json` header

**MQTT subscription not working**

1. Check broker connectivity from the device-engine container:
   ```bash
   docker compose exec device-engine nc -zv external-broker.example.com 1883
   ```

2. Verify credentials are correct

3. Check topic format matches what the external device publishes to

**Data not appearing in Grafana**

1. Verify data is in InfluxDB:
   ```flux
   from(bucket: "telemetry")
     |> range(start: -5m)
     |> filter(fn: (r) => r.source == "physical")
   ```

2. Check the source filter in Grafana includes "physical"

3. Ensure the dashboard time range covers recent data

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
