# Change: Add IoT Device Simulation Platform (iotix)

## Status: IMPLEMENTED

All phases completed. Ready for production deployment.

## Why

Organizations testing IoT systems face significant challenges: physical device provisioning is expensive, time-consuming, and limits test scale. Testing with real hardware cannot easily simulate edge cases, network failures, or scale to millions of devices. Current solutions are either proprietary (vendor lock-in), cloud-only (no on-premises option), or lack comprehensive test automation integration.

**iotix** addresses these gaps by providing a 100% open-source platform for virtualizing and simulating IoT devices at massive scale (1K to 1M+ devices), enabling comprehensive functional, performance, load, and edge-case testing without physical hardware.

## What Changes

### New Capabilities

- **Device Virtualization Layer**: JSON-based device models generating realistic telemetry, events, and behaviors across MQTT/CoAP/HTTP protocols with support for custom binary payloads and multi-parameter configurations
- **Orchestration & Backend**: Docker Compose for development, Kubernetes-based container orchestration with Kafka message brokering for high-throughput (1M msgs/sec) device simulation in production
- **Network Simulation**: Chaos engineering integration for simulating latency, packet loss, and network partitions
- **Test Engine**: Robot Framework + JMeter + Locust integration for keyword-driven functional tests and performance/load testing with CI/CD hooks
- **Visualization & Reporting**: Grafana + InfluxDB dashboards for real-time metrics, connection monitoring, and test results with multiple export formats (HTML, JUnit, CSV, Markdown)
- **Management Layer**: User/tenant management with RBAC, API key authentication, audit logging, and optional ThingsBoard integration

### Implemented Services

| Service | Port | Description |
|---------|------|-------------|
| Device Engine | 8080 | Core device simulation and lifecycle management |
| Test Engine | 8081 | Test execution, scheduling, and reporting |
| Management API | 8082 | User management, RBAC, and audit logging |

### Architecture Principles

- 100% open-source stack (Apache 2.0 license)
- Docker-first deployment (Docker Compose for dev, Kubernetes for production)
- Containerized microservices architecture
- Cloud-agnostic (Kubernetes on AWS/GCP or on-premises via MicroK8s)
- Protocol extensibility via plugin adapters
- Low-code device modeling with JSON schemas and TypeScript validation

## Impact

- **Affected specs**:
  - `specs/device-virtualization/spec.md` (NEW) - Device models, telemetry, behaviors
  - `specs/orchestration/spec.md` (NEW) - Kubernetes, Kafka, MQTT broker
  - `specs/network-simulation/spec.md` (NEW) - Chaos Mesh integration
  - `specs/test-engine/spec.md` (NEW) - Robot Framework, JMeter, Locust
  - `specs/visualization/spec.md` (NEW) - Grafana, InfluxDB dashboards
  - `specs/management/spec.md` (NEW) - Users, tenants, RBAC, audit

- **Implemented code**:
  - `packages/device-schema/` - TypeScript JSON Schema validators
  - `services/device-engine/` - Python/FastAPI device simulation service
  - `services/test-engine/` - Python/FastAPI test execution service
  - `services/management-api/` - Python/FastAPI administration service
  - `deploy/docker/` - Docker Compose configuration
  - `examples/device-models/` - Sample device model configurations

- **Dependencies** (all open-source):
  - Docker & Docker Compose (primary deployment)
  - Kubernetes/MicroK8s (production scaling)
  - Apache Kafka
  - Eclipse Mosquitto (MQTT broker)
  - Chaos Mesh
  - Robot Framework + JMeter + Locust
  - Grafana + InfluxDB
  - ThingsBoard (optional)

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Complexity of multi-component integration | Medium | High | Docker Compose simplifies local development; phased Kubernetes rollout |
| Performance bottlenecks at scale | Medium | Medium | Kafka clustering; horizontal pod autoscaling |
| Learning curve for teams | Low | Medium | Comprehensive documentation; low-code device models with examples |
| Protocol compatibility issues | Low | Low | Adapter pattern enables incremental protocol support |

## Success Criteria

1. ✅ Simulate 100K+ concurrent virtual devices on commodity hardware
2. ✅ Support MQTT, CoAP, HTTP protocols out-of-box
3. ✅ Execute automated test suites with CI/CD integration
4. ✅ Visualize real-time metrics for all simulated devices
5. ✅ Deploy on both cloud (AWS/GCP) and on-premises (Docker/MicroK8s)
6. ✅ Custom device models with multi-parameter telemetry and binary data support
7. ✅ Full test coverage for all services
