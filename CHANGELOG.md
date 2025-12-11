# Changelog

All notable changes to IoTix will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-XX-XX

### Added

#### Core Platform
- Initial release of IoTix - IoT Device Simulation Platform
- Device Engine service for managing simulated IoT devices
- Support for MQTT, CoAP, and HTTP protocols
- Device model schema with JSON Schema validation
- Telemetry generators: random, sequence, constant, replay

#### Device Management
- REST API for device lifecycle management (create, start, stop, delete)
- Device groups for batch operations on multiple devices
- Staggered device startup for realistic simulation
- Device metrics and telemetry tracking

#### Test Engine
- Test execution service with REST API
- Test suite and test run management
- Scheduled test execution with cron expressions
- Webhook triggers for CI/CD integration
- Report generation in HTML, JUnit XML, CSV, and Markdown formats

#### Robot Framework Integration
- `robotframework-iotix` library package
- Keywords for device and group management
- Telemetry validation keywords
- Example test suites

#### Load Testing
- Locust load test examples for MQTT device simulation
- JMeter test plan templates
- CI/CD integration templates for GitHub Actions, GitLab CI, and Jenkins

#### Orchestration
- Kubernetes deployment via Helm charts
- Horizontal Pod Autoscaler (HPA) configuration
- MQTT broker deployment (Mosquitto/EMQX/VerneMQ)
- Kafka integration for high-throughput messaging

#### Network Simulation
- Chaos Mesh integration for network fault injection
- Pre-built templates: poor cellular, intermittent connectivity, satellite link
- Latency, packet loss, and network partition simulation

#### Visualization & Reporting
- InfluxDB metrics storage
- Grafana dashboards: Device Overview, Test Results, System Health
- Configurable alerting with Slack and email notifications
- Metrics writer for device telemetry

#### Management
- User and tenant management API
- Role-based access control (RBAC)
- API key authentication
- Audit logging with export functionality
- ThingsBoard integration client

#### Infrastructure
- Docker Compose setup for local development
- Multi-service Docker configuration
- GitHub Actions CI pipeline
- TypeScript device schema validation package

### Security
- JWT-based authentication for Management API
- API key support with configurable permissions
- CORS configuration for cross-origin requests

### Documentation
- Getting Started guide
- Device Model Reference
- API Documentation
- Deployment Guide
- Example device models (temperature sensor, gateway, actuator)

## [0.0.1] - 2024-XX-XX

### Added
- Initial project structure
- Basic proof of concept

---

## Release Notes Format

### Types of Changes
- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes

[Unreleased]: https://github.com/iotix/iotix/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/iotix/iotix/releases/tag/v0.1.0
[0.0.1]: https://github.com/iotix/iotix/releases/tag/v0.0.1
