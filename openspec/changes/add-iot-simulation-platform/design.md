# Design: IoT Device Simulation Platform (iotix)

## Context

The platform targets QA teams, developers, and DevOps engineers who need to test IoT applications at scale without physical hardware. Key stakeholders include:
- QA engineers writing functional and load tests
- DevOps teams managing CI/CD pipelines
- Platform engineers deploying and scaling the infrastructure
- IoT developers creating device models

**Constraints**:
- 100% open-source components (Apache/MIT licenses)
- Must support both cloud and on-premises deployment
- Must scale from 1K to 1M+ simulated devices
- Must integrate with existing CI/CD tools

## Goals / Non-Goals

### Goals
- Provide scalable virtual device simulation (100K+ devices)
- Support major IoT protocols (MQTT, CoAP, HTTP) with extensibility
- Enable automated testing with CI/CD integration
- Offer real-time visualization and monitoring
- Simulate network conditions (latency, packet loss, partitions)
- Enable low-code device model creation via JSON schemas

### Non-Goals
- Replace production IoT platforms (ThingsBoard, AWS IoT)
- Provide device firmware development tools
- Offer end-user mobile applications
- Support proprietary protocols without community adapters

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           iotix Platform                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │  Management UI  │  │  Grafana        │  │  ThingsBoard    │              │
│  │  (React/Vue)    │  │  Dashboards     │  │  Integration    │              │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
│           │                    │                    │                        │
│  ─────────┴────────────────────┴────────────────────┴─────────  API Layer   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        Test Engine Service                               ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    ││
│  │  │ Robot       │  │ JMeter      │  │ Test        │  │ CI/CD       │    ││
│  │  │ Framework   │  │ Load Tests  │  │ Scheduler   │  │ Hooks       │    ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     Device Virtualization Layer                          ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    ││
│  │  │ Device      │  │ Telemetry   │  │ Behavior    │  │ Protocol    │    ││
│  │  │ Model Mgr   │  │ Generator   │  │ Engine      │  │ Adapters    │    ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    ││
│  │                                                                          ││
│  │  Device Models: [Sensor] [Gateway] [Actuator] [Custom]                  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      Network Simulation Layer                            ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                      ││
│  │  │ Chaos Mesh  │  │ Latency     │  │ Partition   │                      ││
│  │  │ Controller  │  │ Injector    │  │ Simulator   │                      ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘                      ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     Orchestration & Message Layer                        ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    ││
│  │  │ Kubernetes  │  │ Apache      │  │ VerneMQ/    │  │ InfluxDB    │    ││
│  │  │ Orchestrator│  │ Kafka       │  │ EMQX        │  │ Time-series │    ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

## Decisions

### D1: Device Model Format - JSON Schema

**Decision**: Use JSON-based device model definitions with JSON Schema validation.

**Rationale**:
- Human-readable and editable without specialized tools
- Schema validation catches errors early
- Supports inheritance and composition for device types
- Easy to version control and diff
- Low learning curve for teams

**Alternatives Considered**:
- YAML: Similar benefits but JSON has better tooling ecosystem
- Custom DSL: Higher learning curve, maintenance burden
- Code-based (Python): More flexible but requires programming knowledge

### D2: Message Broker - VerneMQ (primary) with EMQX (alternative)

**Decision**: Support both VerneMQ and EMQX as MQTT brokers, with VerneMQ as the default.

**Rationale**:
- VerneMQ excels at clustering and shared subscriptions
- EMQX offers superior performance and built-in dashboard
- Both are Apache 2.0 licensed
- Choice allows users to optimize for their needs

**Alternatives Considered**:
- Mosquitto: Simpler but lacks clustering for scale
- RabbitMQ: MQTT plugin less mature than native brokers
- HiveMQ CE: Feature-limited community edition

### D3: Load Testing - Locust with MQTT Plugin

**Decision**: Use Locust.io with locust-plugins for device simulation at scale.

**Rationale**:
- Python-based, easy to extend
- Scales to thousands of concurrent "users" (devices)
- Built-in web UI for monitoring
- Active community with MQTT support via locust-plugins
- Integrates well with CI/CD

**Alternatives Considered**:
- JMeter: Good for HTTP but MQTT support less ergonomic
- Gatling: Scala-based, steeper learning curve
- Custom Python scripts: Reinventing the wheel

### D4: Chaos Engineering - Chaos Mesh

**Decision**: Use Chaos Mesh for network simulation and fault injection.

**Rationale**:
- Cloud-native, Kubernetes-native design
- Declarative experiment definitions (CRDs)
- Supports network chaos (latency, loss, partition)
- Visual dashboard for experiment management
- CNCF sandbox project with active development

**Alternatives Considered**:
- Litmus: Similar but less mature network chaos
- Gremlin: Commercial, violates open-source requirement
- tc/netem directly: Low-level, harder to orchestrate

### D5: Deployment Model - Kubernetes with Helm Charts

**Decision**: Package all components as Helm charts for Kubernetes deployment.

**Rationale**:
- Industry-standard for container orchestration
- Helm provides templating and release management
- Works on cloud (EKS, GKE, AKS) and on-premises (MicroK8s, k3s)
- Enables horizontal scaling via HPA

**Alternatives Considered**:
- Docker Compose: Simpler but lacks production scaling
- Nomad: Less ecosystem support
- Bare containers: No orchestration benefits

### D6: Metrics Storage - InfluxDB + Grafana

**Decision**: Use InfluxDB for time-series metrics with Grafana for visualization.

**Rationale**:
- InfluxDB optimized for time-series IoT data
- Grafana has extensive plugin ecosystem
- Both have strong open-source versions
- Native integration between the two

**Alternatives Considered**:
- Prometheus: Pull-based model less suited to ephemeral device metrics
- TimescaleDB: PostgreSQL-based, heavier setup
- ClickHouse: More complex for pure time-series use case

## Component Design

### Device Virtualization Layer

```
┌────────────────────────────────────────────────────────────┐
│                  Device Model Manager                       │
├────────────────────────────────────────────────────────────┤
│  - Load/validate device model JSON definitions             │
│  - Manage device lifecycle (create, start, stop, destroy)  │
│  - Support device groups and batch operations              │
│  - Provide REST API for device management                  │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│                   Telemetry Generator                       │
├────────────────────────────────────────────────────────────┤
│  - Generate realistic sensor data based on model specs     │
│  - Support statistical distributions (normal, uniform)     │
│  - Handle historical replay mode                           │
│  - Support custom payload generators (binary hooks)        │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│                    Behavior Engine                          │
├────────────────────────────────────────────────────────────┤
│  - Execute device state machines                           │
│  - Handle events and commands                              │
│  - Simulate device failures and recoveries                 │
│  - Support scripted behavior sequences                     │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│                   Protocol Adapters                         │
├────────────────────────────────────────────────────────────┤
│  - MQTT Adapter (paho-mqtt)                                │
│  - CoAP Adapter (aiocoap)                                  │
│  - HTTP Adapter (requests/aiohttp)                         │
│  - Plugin interface for custom protocols                   │
└────────────────────────────────────────────────────────────┘
```

### Device Model Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": { "type": "string" },
    "name": { "type": "string" },
    "type": { "enum": ["sensor", "gateway", "actuator", "custom"] },
    "protocol": { "enum": ["mqtt", "coap", "http"] },
    "connection": {
      "type": "object",
      "properties": {
        "broker": { "type": "string" },
        "port": { "type": "integer" },
        "topic_pattern": { "type": "string" },
        "qos": { "type": "integer", "minimum": 0, "maximum": 2 }
      }
    },
    "telemetry": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "type": { "enum": ["number", "boolean", "string", "binary"] },
          "generator": {
            "type": "object",
            "properties": {
              "type": { "enum": ["random", "sequence", "replay", "custom"] },
              "min": { "type": "number" },
              "max": { "type": "number" },
              "distribution": { "enum": ["uniform", "normal", "exponential"] }
            }
          },
          "interval_ms": { "type": "integer" }
        }
      }
    },
    "behaviors": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "trigger": { "type": "string" },
          "action": { "type": "string" },
          "params": { "type": "object" }
        }
      }
    }
  },
  "required": ["id", "name", "type", "protocol"]
}
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Kafka adds operational complexity | Provide simplified single-node mode for development; Strimzi operator for production |
| Learning curve for Chaos Mesh | Pre-built experiment templates; comprehensive documentation |
| VerneMQ clustering configuration | Helm chart with sensible defaults; documented scaling patterns |
| InfluxDB storage at scale | Retention policies; optional downsampling; cloud-managed option |
| Cross-component debugging | Distributed tracing with OpenTelemetry; centralized logging |

## Migration Plan

This is a greenfield project. No migration required.

**Phased Rollout**:
1. Phase 1: Core device virtualization + MQTT
2. Phase 2: Orchestration layer + scaling
3. Phase 3: Test engine integration
4. Phase 4: Network simulation
5. Phase 5: Visualization and management

## Open Questions

1. **Q1**: Should we support device model inheritance (e.g., `sensor` base type extended by `temperature_sensor`)?
   - Recommendation: Yes, via JSON Schema `$ref` and `allOf`

2. **Q2**: What is the minimum Kubernetes cluster size for 100K devices?
   - Needs benchmarking; initial estimate: 3-5 worker nodes (4 CPU, 16GB RAM each)

3. **Q3**: Should the platform include a web-based device model editor?
   - Recommendation: Defer to Phase 2; JSON files + schema validation sufficient initially

4. **Q4**: How to handle custom binary payloads?
   - Proposal: Python plugin hooks with defined input/output interfaces
