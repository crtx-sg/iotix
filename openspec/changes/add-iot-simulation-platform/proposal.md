# Change: Add IoT Device Simulation Platform (iotix)

## Why

Organizations testing IoT systems face significant challenges: physical device provisioning is expensive, time-consuming, and limits test scale. Testing with real hardware cannot easily simulate edge cases, network failures, or scale to millions of devices. Current solutions are either proprietary (vendor lock-in), cloud-only (no on-premises option), or lack comprehensive test automation integration.

**iotix** addresses these gaps by providing a 100% open-source platform for virtualizing and simulating IoT devices at massive scale (1K to 1M+ devices), enabling comprehensive functional, performance, load, and edge-case testing without physical hardware.

## What Changes

### New Capabilities

- **Device Virtualization Layer**: JSON-based device models generating realistic telemetry, events, and behaviors across MQTT/CoAP/HTTP protocols with support for custom binary payloads
- **Orchestration & Backend**: Kubernetes-based container orchestration with Kafka message brokering for high-throughput (1M msgs/sec) device simulation
- **Network Simulation**: Chaos engineering integration for simulating latency, packet loss, and network partitions
- **Test Engine**: Robot Framework + JMeter integration for keyword-driven functional tests and performance/load testing with CI/CD hooks
- **Visualization & Reporting**: Grafana + InfluxDB dashboards for real-time metrics, connection monitoring, and test results
- **Management Layer**: ThingsBoard integration for device provisioning, rule-based scenarios, and simulation data visualization

### Architecture Principles

- 100% open-source stack (Apache/MIT licenses)
- Containerized microservices architecture
- Cloud-agnostic (Kubernetes on AWS/GCP or on-premises via MicroK8s)
- Protocol extensibility via plugin adapters
- Low-code device modeling with JSON schemas

## Impact

- **Affected specs**:
  - `specs/device-virtualization/spec.md` (NEW)
  - `specs/orchestration/spec.md` (NEW)
  - `specs/network-simulation/spec.md` (NEW)
  - `specs/test-engine/spec.md` (NEW)
  - `specs/visualization/spec.md` (NEW)
  - `specs/management/spec.md` (NEW)

- **Affected code**:
  - New microservices for device simulation, orchestration, and test execution
  - Configuration schemas for device models
  - Protocol adapters (MQTT, CoAP, HTTP)
  - Kubernetes manifests and Helm charts
  - CI/CD pipeline integrations

- **Dependencies** (all open-source):
  - Kubernetes/MicroK8s
  - Apache Kafka
  - VerneMQ or EMQX (MQTT broker)
  - Chaos Mesh
  - Robot Framework + JMeter
  - Grafana + InfluxDB
  - ThingsBoard

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Complexity of multi-component integration | Medium | High | Phased rollout; start with core simulation layer |
| Performance bottlenecks at scale | Medium | Medium | Kafka clustering; horizontal pod autoscaling |
| Learning curve for teams | Low | Medium | Comprehensive documentation; low-code device models |
| Protocol compatibility issues | Low | Low | Adapter pattern enables incremental protocol support |

## Success Criteria

1. Simulate 100K+ concurrent virtual devices on commodity hardware
2. Support MQTT, CoAP, HTTP protocols out-of-box
3. Execute automated test suites with CI/CD integration
4. Visualize real-time metrics for all simulated devices
5. Deploy on both cloud (AWS/GCP) and on-premises (MicroK8s)
