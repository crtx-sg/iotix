# IoTix

Open-source IoT device simulation platform for testing at scale. Supports MQTT, CoAP, HTTP protocols to simulate 1K to 1M+ virtual IoT devices, with hybrid support for integrating real physical devices.

## Features

- **Device Virtualization**: JSON-based device models with realistic telemetry generation
- **Hybrid Device Support**: Mix simulated and physical devices in the same environment
- **Multi-Protocol Support**: MQTT, CoAP, HTTP out-of-the-box with extensible adapter pattern
- **Scalable Architecture**: Docker Compose for development, Kubernetes for production
- **Test Automation**: Robot Framework, JMeter, and Locust integration
- **Real-time Monitoring**: Grafana dashboards with InfluxDB metrics storage
- **Chaos Engineering**: Device dropout simulation for resilience testing

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SOURCES                                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                      │
│  │ Physical Device │  │ Physical Device │  │ Physical Device │                      │
│  │  (MQTT Client)  │  │ (HTTP Sender)   │  │  (CoAP Server)  │                      │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘                      │
│           │                    │                    │                                │
│      External MQTT        HTTP POST            CoAP Observe                          │
│        Topics              Webhooks             Resources                            │
└───────────┼────────────────────┼────────────────────┼────────────────────────────────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────────────────────────┐
│                         DEVICE ENGINE (:8080)                                        │
│  ┌─────────────────────────────┴─────────────────────────────┐                      │
│  │                     Proxy Adapters                         │                      │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │                      │
│  │  │ MQTT Proxy  │  │ HTTP Proxy  │  │  CoAP Proxy     │    │                      │
│  │  │  Adapter    │  │  Adapter    │  │   Adapter       │    │                      │
│  │  └──────┬──────┘  └──────┬──────┘  └───────┬─────────┘    │                      │
│  └─────────┼────────────────┼─────────────────┼──────────────┘                      │
│            │                │                 │                                      │
│            └────────────────┼─────────────────┘                                      │
│                             ▼                                                        │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                         Device Manager                                        │   │
│  │  ┌─────────────────────────┐    ┌─────────────────────────┐                  │   │
│  │  │     ProxyDevice         │    │     VirtualDevice       │                  │   │
│  │  │   source: "physical"    │    │   source: "simulated"   │                  │   │
│  │  │   - Passthrough mode    │    │   - Telemetry generators│                  │   │
│  │  │   - External binding    │    │   - Protocol adapters   │                  │   │
│  │  └───────────┬─────────────┘    └───────────┬─────────────┘                  │   │
│  └──────────────┼──────────────────────────────┼────────────────────────────────┘   │
│                 │                              │                                     │
│                 └──────────────┬───────────────┘                                     │
│                                ▼                                                     │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                      Protocol Adapters (Outbound)                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                           │   │
│  │  │    MQTT     │  │    CoAP     │  │    HTTP     │                           │   │
│  │  └──────┬──────┘  └─────────────┘  └─────────────┘                           │   │
│  └─────────┼────────────────────────────────────────────────────────────────────┘   │
└────────────┼────────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                              INFRASTRUCTURE                                         │
│                                                                                     │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────────────┐  │
│  │   MQTT Broker   │   │    InfluxDB     │   │           Grafana               │  │
│  │  (Mosquitto)    │   │    (:8086)      │   │          (:3000)                │  │
│  │    :1883        │   │                 │   │                                 │  │
│  │                 │   │  ┌───────────┐  │   │  ┌─────────────────────────┐   │  │
│  │  Simulated &    │   │  │ telemetry │  │──▶│  │ Device Overview         │   │  │
│  │  External       │   │  │  bucket   │  │   │  │ - Simulated vs Physical │   │  │
│  │  Devices        │   │  │           │  │   │  │ - Source filtering      │   │  │
│  │  publish here   │   │  │  source:  │  │   │  │ - Telemetry by source   │   │  │
│  │                 │   │  │  simulated│  │   │  └─────────────────────────┘   │  │
│  │                 │   │  │  physical │  │   │                                 │  │
│  └─────────────────┘   │  └───────────┘  │   └─────────────────────────────────┘  │
│                        └─────────────────┘                                         │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
SIMULATED DEVICES:
  Device Engine → VirtualDevice → Generate Telemetry → MQTT Broker → InfluxDB (source=simulated)

PHYSICAL DEVICES:
  External Device → ProxyAdapter → ProxyDevice → InfluxDB (source=physical)

MONITORING:
  InfluxDB → Grafana → Dashboards (filter by source: simulated | physical | all)
```

### Services

| Component | Port | Description |
|-----------|------|-------------|
| **Device Engine** | 8080 | Core simulation service. Manages virtual and proxy devices, generates telemetry. |
| **Test Engine** | 8081 | Test execution service. Manages test suites, runs, schedules, and reports. |
| **Management API** | 8082 | Administration service. Authentication, RBAC, tenant management. |
| **MQTT Broker** | 1883 | Eclipse Mosquitto. Simulated devices publish telemetry here. |
| **InfluxDB** | 8086 | Time-series database. Stores all device metrics with source tagging. |
| **Grafana** | 3000 | Visualization. Dashboards for simulated and physical device metrics. |

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/iotix/iotix.git
cd iotix

# Start all services
cd deploy/docker
docker compose up -d

# Verify services are running
docker compose ps
curl http://localhost:8080/health
```

### Service URLs

| Service | URL |
|---------|-----|
| Device Engine API | http://localhost:8080/docs |
| Grafana Dashboard | http://localhost:3000 (admin/admin) |
| InfluxDB | http://localhost:8086 |

### Create Your First Devices

```bash
# Create a group of 5 simulated sensors
curl -X POST http://localhost:8080/api/v1/groups \
  -H "Content-Type: application/json" \
  -d '{"modelId": "temperature-sensor-v1", "count": 5, "groupId": "my-sensors"}'

# Start the devices
curl -X POST http://localhost:8080/api/v1/groups/my-sensors/start

# Check stats
curl http://localhost:8080/api/v1/stats
```

### Add a Physical Device (Proxy)

```bash
# Create a proxy device for external telemetry
curl -X POST http://localhost:8080/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{"modelId": "physical-sensor-proxy", "deviceId": "physical-001"}'

# Bind to HTTP webhook
curl -X POST http://localhost:8080/api/v1/devices/physical-001/bind \
  -H "Content-Type: application/json" \
  -d '{"config": {"protocol": "http"}}'

# Send telemetry from external device
curl -X POST http://localhost:8080/api/v1/webhooks/physical-001 \
  -H "Content-Type: application/json" \
  -d '{"temperature": 25.5, "humidity": 60}'
```

For detailed setup, configuration, and troubleshooting, see **[SETUP.md](SETUP.md)**.

---

## Device Types

### Simulated Devices (VirtualDevice)

Virtual devices generate telemetry based on JSON model configurations:

```json
{
  "id": "temperature-sensor-v1",
  "name": "Temperature Sensor",
  "type": "sensor",
  "protocol": "mqtt",
  "telemetry": [{
    "name": "temperature",
    "type": "number",
    "intervalMs": 5000,
    "generator": {"type": "random", "min": 18, "max": 28}
  }]
}
```

### Proxy Devices (Physical)

Proxy devices forward telemetry from external physical devices:

```json
{
  "id": "physical-sensor-proxy",
  "name": "Physical Sensor Proxy",
  "type": "proxy",
  "protocol": "http",
  "telemetry": []
}
```

**Binding protocols:**
- **HTTP**: External devices POST to `/api/v1/webhooks/{device_id}`
- **MQTT**: Subscribe to external MQTT broker topics

---

## API Quick Reference

### Devices

```bash
# List devices
curl http://localhost:8080/api/v1/devices

# Create device
curl -X POST http://localhost:8080/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{"modelId": "temperature-sensor-v1"}'

# Start/Stop device
curl -X POST http://localhost:8080/api/v1/devices/{id}/start
curl -X POST http://localhost:8080/api/v1/devices/{id}/stop
```

### Device Groups

```bash
# Create group
curl -X POST http://localhost:8080/api/v1/groups \
  -H "Content-Type: application/json" \
  -d '{"modelId": "temperature-sensor-v1", "count": 100, "groupId": "sensors"}'

# Start/Stop group
curl -X POST http://localhost:8080/api/v1/groups/sensors/start
curl -X POST http://localhost:8080/api/v1/groups/sensors/stop

# Simulate dropouts (chaos engineering)
curl -X POST http://localhost:8080/api/v1/groups/sensors/dropout \
  -H "Content-Type: application/json" \
  -d '{"strategy": "linear", "percentage": 20, "delayMs": 1000}'
```

### Proxy Device Binding

```bash
# Bind to HTTP webhook
curl -X POST http://localhost:8080/api/v1/devices/{id}/bind \
  -H "Content-Type: application/json" \
  -d '{"config": {"protocol": "http"}}'

# Bind to external MQTT
curl -X POST http://localhost:8080/api/v1/devices/{id}/bind \
  -H "Content-Type: application/json" \
  -d '{"config": {"protocol": "mqtt", "broker": "external.mqtt.com", "port": 1883, "topic": "sensors/data"}}'

# Unbind
curl -X POST http://localhost:8080/api/v1/devices/{id}/unbind

# Check binding status
curl http://localhost:8080/api/v1/devices/{id}/binding
```

### Engine Stats

```bash
curl http://localhost:8080/api/v1/stats

# Response:
# {
#   "total_devices": 15,
#   "running_devices": 12,
#   "running_simulated": 10,
#   "running_physical": 2,
#   "total_proxy_devices": 3
# }
```

---

## Grafana Dashboards

The IoTix Device Overview dashboard includes:

| Panel | Description |
|-------|-------------|
| **Active Devices** | Total running devices |
| **Simulated Devices** | Count of running virtual devices |
| **Physical Devices** | Count of running proxy devices |
| **Telemetry by Source** | Pie chart: simulated vs physical |
| **Temperature/Humidity** | Time-series telemetry charts |

**Source Filter**: Use the `source` dropdown to filter by `simulated`, `physical`, or `All`.

---

## InfluxDB Schema

All metrics include a `source` tag for filtering:

| Measurement | Tags | Description |
|-------------|------|-------------|
| `telemetry` | device_id, model_id, **source** | Device telemetry readings |
| `device_events` | device_id, event_type, **source** | Lifecycle events |
| `connections` | device_id, protocol, **source** | Connection status |
| `engine_stats` | - | Engine-wide statistics |

**Source values**: `simulated` or `physical`

```flux
// Query physical device telemetry only
from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r.source == "physical")

// Compare simulated vs physical
from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r._field == "temperature")
  |> group(columns: ["source"])
  |> aggregateWindow(every: 1m, fn: mean)
```

---

## Project Structure

```
iotix/
├── services/
│   ├── device-engine/       # Core simulation service
│   │   └── src/
│   │       ├── device.py           # VirtualDevice
│   │       ├── proxy_device.py     # ProxyDevice (physical)
│   │       ├── manager.py          # DeviceManager
│   │       └── adapters/           # Protocol adapters
│   │           ├── mqtt.py         # Outbound MQTT
│   │           ├── mqtt_proxy.py   # Inbound MQTT proxy
│   │           └── http_proxy.py   # Inbound HTTP webhook
│   ├── test-engine/         # Test execution
│   └── management-api/      # Administration
├── examples/
│   └── device-models/       # Sample device models
├── deploy/
│   ├── docker/              # Docker Compose
│   └── grafana/dashboards/  # Grafana dashboards
└── openspec/                # Specifications
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [SETUP.md](SETUP.md) | Detailed setup, configuration, troubleshooting |
| [openspec/](openspec/) | Architecture specifications |
| [API Docs](http://localhost:8080/docs) | Swagger API documentation |

---

## License

Apache-2.0
