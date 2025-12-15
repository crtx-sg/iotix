# IoTix Setup Guide

Detailed setup, configuration, testing, and troubleshooting instructions for IoTix.

## Table of Contents

- [Docker Setup](#docker-setup)
- [Local Development Setup](#local-development-setup)
- [Configuration Reference](#configuration-reference)
- [Device Models](#device-models)
- [Launching Devices at Scale](#launching-devices-at-scale)
- [Device Dropout Simulation](#device-dropout-simulation)
- [Hybrid Device Testing](#hybrid-device-testing)
- [InfluxDB Reference](#influxdb-reference)
- [Grafana Configuration](#grafana-configuration)
- [Troubleshooting](#troubleshooting)

---

## Docker Setup

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Start Services

```bash
cd deploy/docker

# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Check service status
docker compose ps
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

### Docker Commands Reference

```bash
# Start all services
docker compose up -d

# View logs for specific service
docker compose logs -f device-engine
docker compose logs -f grafana

# Restart a service
docker compose restart device-engine

# Stop all services
docker compose down

# Full reset (removes all data volumes)
docker compose down -v

# Rebuild after code changes
docker compose build device-engine
docker compose up -d
```

---

## Local Development Setup

For development without Docker.

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

### Run Tests

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

### Code Quality

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

## Configuration Reference

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

> **Warning**: Change all passwords and tokens for production deployments.

---

## Device Models

Device models are JSON configurations that define how virtual IoT devices behave.

### Device Model Schema

```json
{
  "id": "string (required)",
  "name": "string (required)",
  "description": "string (optional)",
  "version": "string (optional, semver)",
  "type": "sensor | gateway | actuator | custom | proxy (required)",
  "protocol": "mqtt | coap | http (required)",
  "connection": { },
  "telemetry": [ ],
  "commands": [ ],
  "behaviors": [ ],
  "metadata": { }
}
```

### Register a Device Model

```bash
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

### Generator Types

| Type | Description | Configuration |
|------|-------------|---------------|
| `random` | Random values within range | `min`, `max`, `distribution` (uniform, normal, exponential), `mean`, `stddev` |
| `sequence` | Incrementing/decrementing values | `start`, `step`, `min`, `max`, `wrap` |
| `constant` | Fixed value | `value` |
| `replay` | Replay from data file | `dataFile`, `column`, `loop` |
| `custom` | Custom Python handler | `handler`, `config` |

### Data Types

| Type | Description | Example |
|------|-------------|---------|
| `number` | Floating-point number | 22.5, 1013.25 |
| `integer` | Whole number | 72, 100 |
| `boolean` | True/false | true, false |
| `string` | Text string | "connected", "active" |
| `binary` | Raw binary data | ECG samples, images |

### Example: Multi-Parameter Environmental Sensor

```json
{
  "id": "environmental-sensor-v1",
  "name": "Environmental Sensor",
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
      "generator": {"type": "random", "min": 15, "max": 35, "distribution": "normal", "mean": 22, "stddev": 3},
      "intervalMs": 5000
    },
    {
      "name": "humidity",
      "type": "number",
      "unit": "percent",
      "generator": {"type": "random", "min": 20, "max": 90},
      "intervalMs": 5000
    },
    {
      "name": "pressure",
      "type": "number",
      "unit": "hPa",
      "generator": {"type": "random", "min": 980, "max": 1040, "mean": 1013.25, "stddev": 10},
      "intervalMs": 10000
    }
  ]
}
```

### Example: Proxy Device Model

```json
{
  "id": "physical-sensor-proxy",
  "name": "Physical Sensor Proxy",
  "type": "proxy",
  "protocol": "http",
  "telemetry": [],
  "metadata": {"category": "proxy"}
}
```

---

## Launching Devices at Scale

### Create Device Groups

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

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `immediate` | Start all devices at once | Maximum throughput |
| `linear` | Fixed delay between each device | Controlled ramp-up |
| `batch` | Start in batches with delay | Balance speed and resources |
| `exponential` | Exponentially increasing delay | Gradual warm-up |

### Strategy Examples

```bash
# Immediate (all at once)
curl -X POST http://localhost:8080/api/v1/groups/my-sensors/start \
  -H "Content-Type: application/json" \
  -d '{"strategy": "immediate"}'

# Linear (10ms delay between each)
curl -X POST http://localhost:8080/api/v1/groups/my-sensors/start \
  -H "Content-Type: application/json" \
  -d '{"strategy": "linear", "delayMs": 10}'

# Batch (100 devices at a time, 1s between batches)
curl -X POST http://localhost:8080/api/v1/groups/my-sensors/start \
  -H "Content-Type: application/json" \
  -d '{"strategy": "batch", "batchSize": 100, "delayMs": 1000}'

# Exponential (gradual ramp-up)
curl -X POST http://localhost:8080/api/v1/groups/my-sensors/start \
  -H "Content-Type: application/json" \
  -d '{"strategy": "exponential", "delayMs": 1, "exponentBase": 1.1, "maxDelayMs": 5000}'
```

### Scaling Recommendations

| Device Count | Recommended Strategy | Configuration |
|--------------|---------------------|---------------|
| 1-100 | `immediate` | Default |
| 100-1,000 | `linear` | `delayMs: 10` |
| 1,000-10,000 | `batch` | `batchSize: 100, delayMs: 500` |
| 10,000-100,000 | `batch` | `batchSize: 500, delayMs: 1000` |
| 100,000+ | `batch` | `batchSize: 1000, delayMs: 2000` + Kubernetes HPA |

---

## Device Dropout Simulation

Simulate device failures for chaos engineering and resilience testing.

### Dropout Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `immediate` | All devices drop at once | Mass failure simulation |
| `linear` | Fixed delay between dropouts | Gradual degradation |
| `exponential` | Accelerating dropout rate | Cascading failure |
| `random` | Random dropouts in time window | Realistic failures |

### Examples

```bash
# Drop 50% immediately
curl -X POST http://localhost:8080/api/v1/groups/sensors/dropout \
  -H "Content-Type: application/json" \
  -d '{"strategy": "immediate", "percentage": 50}'

# Drop 100 devices with 1s delay between each
curl -X POST http://localhost:8080/api/v1/groups/sensors/dropout \
  -H "Content-Type: application/json" \
  -d '{"strategy": "linear", "count": 100, "delayMs": 1000}'

# Cascading failure (accelerating)
curl -X POST http://localhost:8080/api/v1/groups/sensors/dropout \
  -H "Content-Type: application/json" \
  -d '{"strategy": "exponential", "percentage": 30, "delayMs": 100, "exponentBase": 1.5}'

# Random dropouts over 60 seconds
curl -X POST http://localhost:8080/api/v1/groups/sensors/dropout \
  -H "Content-Type: application/json" \
  -d '{"strategy": "random", "percentage": 25, "durationMs": 60000}'
```

### Dropout with Automatic Reconnection

```bash
curl -X POST http://localhost:8080/api/v1/groups/sensors/dropout \
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
| `strategy` | string | `linear` | Dropout strategy |
| `count` | integer | - | Absolute number of devices to drop |
| `percentage` | float | - | Percentage of devices to drop (0-100) |
| `delayMs` | integer | `1000` | Base delay between dropouts |
| `durationMs` | integer | `60000` | Total duration for random strategy |
| `exponentBase` | float | `1.5` | Exponent for exponential strategy |
| `reconnect` | boolean | `false` | Auto-reconnect after dropout |
| `reconnectDelayMs` | integer | `0` | Delay before reconnection |

---

## Hybrid Device Testing

Test the hybrid device support with both simulated and physical devices.

### Step 1: Rebuild and Restart Services

```bash
cd deploy/docker

# Stop existing services
docker compose down

# Rebuild the device-engine
docker compose build device-engine

# Start all services
docker compose up -d

# Verify services are running
docker compose ps
```

### Step 2: Verify Services

```bash
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/models
```

### Step 3: Create Simulated Devices

```bash
# Create a group of simulated sensors
curl -X POST http://localhost:8080/api/v1/groups \
  -H "Content-Type: application/json" \
  -d '{
    "modelId": "temperature-sensor-v1",
    "count": 5,
    "groupId": "test-sensors"
  }'

# Start the devices
curl -X POST http://localhost:8080/api/v1/groups/test-sensors/start

# Check stats (should show running_simulated: 5)
curl http://localhost:8080/api/v1/stats
```

### Step 4: Create and Bind Proxy Device

```bash
# Register proxy model (if not auto-loaded)
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

# Create proxy device
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
```

### Step 5: Send Test Telemetry

```bash
# Send telemetry via webhook
curl -X POST http://localhost:8080/api/v1/webhooks/physical-test-1 \
  -H "Content-Type: application/json" \
  -d '{"temperature": 25.5, "humidity": 60}'

# Check stats (should show running_physical: 1)
curl http://localhost:8080/api/v1/stats
```

### Step 6: Verify in Grafana

1. Open http://localhost:3000 (admin/admin)
2. Go to Dashboards > IoTix Device Overview
3. Verify:
   - **Simulated Devices**: 5
   - **Physical Devices**: 1
   - **Telemetry by Source**: pie chart showing both
   - Temperature/humidity charts with data

### Step 7: Cleanup

```bash
# Stop and delete simulated group
curl -X POST http://localhost:8080/api/v1/groups/test-sensors/stop
curl -X DELETE http://localhost:8080/api/v1/groups/test-sensors

# Unbind and delete proxy device
curl -X POST http://localhost:8080/api/v1/devices/physical-test-1/unbind
curl -X DELETE http://localhost:8080/api/v1/devices/physical-test-1
```

---

## InfluxDB Reference

### Access

- URL: http://localhost:8086
- Credentials: admin / adminpassword

### Sample Queries

```flux
// Query telemetry (last 15 minutes)
from(bucket: "telemetry")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "telemetry")
  |> filter(fn: (r) => r._field == "temperature")

// Query by device
from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r.device_id == "device-0")

// Query by source (physical only)
from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r.source == "physical")

// Query device events
from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "device_events")

// Compare simulated vs physical
from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r._field == "temperature")
  |> group(columns: ["source"])
  |> aggregateWindow(every: 1m, fn: mean)
```

### Schema

| Measurement | Tags | Fields |
|-------------|------|--------|
| `telemetry` | device_id, model_id, group_id, source | temperature, humidity, etc. |
| `engine_stats` | (none) | active_devices, total_messages, active_simulated, active_physical |
| `device_events` | device_id, model_id, event_type, source | value |
| `connections` | device_id, protocol, source | connected, latency_ms |

### Data Retention

| Bucket | Default Retention |
|--------|-------------------|
| `telemetry` | infinite |
| `_monitoring` | 7 days |
| `_tasks` | 3 days |

**Change retention (e.g., 30 days):**

```bash
# Get bucket ID
docker compose exec influxdb influx bucket list --org iotix --token iotix-dev-token

# Set 30-day retention
docker compose exec influxdb influx bucket update \
  --id <BUCKET_ID> \
  --retention 720h \
  --org iotix \
  --token iotix-dev-token
```

**Reset all data:**

```bash
docker compose down
docker volume rm docker_influxdb-data
docker compose up -d
```

---

## Grafana Configuration

### Access

- URL: http://localhost:3000
- Credentials: admin / admin

### Pre-configured Dashboard

Dashboards > Browse > IoTix Device Overview

### Manual Data Source Setup

1. Configuration > Data Sources > Add data source
2. Select InfluxDB
3. Configure:
   - Query Language: Flux
   - URL: http://influxdb:8086
   - Organization: iotix
   - Token: iotix-dev-token
   - Default Bucket: telemetry

---

## Troubleshooting

### Grafana not starting (permission denied)

```bash
chmod -R 755 deploy/docker/config/grafana/provisioning
chmod 644 deploy/docker/config/grafana/provisioning/**/*.yml
chmod 644 deploy/docker/config/grafana/provisioning/**/*.json
docker compose restart grafana
```

### "Unknown device model" error

Device models must be registered before creating devices:

```bash
# Check existing models
curl http://localhost:8080/api/v1/models

# Register a model if needed
curl -X POST http://localhost:8080/api/v1/models \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### Pydantic validation errors

Rebuild Docker image after code changes:

```bash
cd deploy/docker
docker compose down
docker compose build device-engine
docker compose up -d
```

### InfluxDB metrics not appearing in Grafana

Check environment variables:

```bash
docker compose exec device-engine env | grep INFLUX
# Should show:
# INFLUXDB_URL=http://influxdb:8086
# INFLUXDB_TOKEN=iotix-dev-token
# INFLUXDB_ORG=iotix
# INFLUXDB_BUCKET=telemetry
```

### Kafka not starting (invalid cluster ID)

```bash
docker compose down
docker volume rm docker_kafka-data
docker compose up -d
```

### Code changes not reflected

```bash
docker compose build device-engine
docker compose up -d
```

### Grafana login fails

Reset Grafana data:

```bash
docker compose rm -f grafana
docker volume rm docker_grafana-data
docker compose up -d grafana
```

### MQTT broker connection timeout

Ensure device models use `mqtt-broker` (Docker service name):

```bash
curl -s http://localhost:8080/api/v1/models | jq '.[].connection.broker'
# Should show "mqtt-broker"
```

If incorrect, reset:

```bash
docker compose down
docker volume rm docker_device-models-data
docker compose build device-engine
docker compose up -d
```

### Webhook not receiving data

1. Check device is bound:
   ```bash
   curl http://localhost:8080/api/v1/devices/{device_id}/binding
   ```

2. Verify webhook URL from bind response

3. Ensure `Content-Type: application/json` header in POST

### MQTT proxy not working

1. Check broker connectivity:
   ```bash
   docker compose exec device-engine nc -zv external-broker.example.com 1883
   ```

2. Verify credentials

3. Check topic format

### Physical device data not in Grafana

1. Query InfluxDB directly:
   ```flux
   from(bucket: "telemetry")
     |> range(start: -5m)
     |> filter(fn: (r) => r.source == "physical")
   ```

2. Check Grafana source filter includes "physical"

3. Verify dashboard time range covers recent data
