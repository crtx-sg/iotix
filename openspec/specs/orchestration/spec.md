# orchestration Specification

## Purpose
TBD - created by archiving change add-iot-simulation-platform. Update Purpose after archive.
## Requirements
### Requirement: Kubernetes Deployment
The system SHALL deploy all components as containerized workloads on Kubernetes.

#### Scenario: Deploy via Helm chart
- **WHEN** the Helm chart is installed on a Kubernetes cluster
- **THEN** all platform components are deployed with correct configurations
- **AND** services are exposed according to chart values

#### Scenario: Configure resource limits
- **WHEN** Helm values specify CPU and memory limits
- **THEN** pods are created with the specified resource constraints
- **AND** horizontal pod autoscaling respects these limits

#### Scenario: Support multiple deployment targets
- **WHEN** deploying to MicroK8s, k3s, EKS, GKE, or AKS
- **THEN** the platform functions correctly
- **AND** uses cloud-native storage and networking where available

### Requirement: Horizontal Scaling
The system SHALL scale device simulation pods horizontally based on load.

#### Scenario: Auto-scale on device count
- **WHEN** the number of simulated devices exceeds pod capacity
- **THEN** Kubernetes HPA creates additional simulation pods
- **AND** devices are distributed across available pods

#### Scenario: Scale down on reduced load
- **WHEN** device count decreases below threshold
- **THEN** excess pods are gracefully terminated
- **AND** devices are redistributed to remaining pods

#### Scenario: Manual scaling override
- **WHEN** an operator specifies a fixed replica count
- **THEN** the system maintains the specified number of pods
- **AND** disables auto-scaling for that deployment

### Requirement: Message Broker Integration
The system SHALL use Apache Kafka for internal high-throughput message routing.

#### Scenario: Publish device telemetry to Kafka
- **WHEN** a device generates telemetry
- **THEN** the data is published to a Kafka topic
- **AND** partitioned by device ID for ordering

#### Scenario: Consume telemetry for processing
- **WHEN** a consumer subscribes to a Kafka topic
- **THEN** it receives messages in partition order
- **AND** can process at its own pace with offset tracking

#### Scenario: Handle broker failure
- **WHEN** a Kafka broker becomes unavailable
- **THEN** producers buffer messages locally
- **AND** resume publishing when the broker recovers

### Requirement: MQTT Broker Clustering
The system SHALL deploy clustered MQTT brokers for device connectivity.

#### Scenario: Deploy VerneMQ cluster
- **WHEN** VerneMQ is selected as the MQTT broker
- **THEN** a multi-node cluster is deployed
- **AND** supports shared subscriptions for load balancing

#### Scenario: Deploy EMQX cluster
- **WHEN** EMQX is selected as the MQTT broker
- **THEN** a multi-node cluster is deployed
- **AND** the EMQX dashboard is accessible

#### Scenario: Handle MQTT broker failover
- **WHEN** an MQTT broker node fails
- **THEN** connected devices automatically reconnect to healthy nodes
- **AND** message delivery continues with at-least-once semantics

### Requirement: Service Discovery
The system SHALL use Kubernetes service discovery for inter-component communication.

#### Scenario: Discover simulation service
- **WHEN** the test engine needs to communicate with the simulation layer
- **THEN** it resolves the service via Kubernetes DNS
- **AND** load balances across available pods

#### Scenario: Discover external endpoints
- **WHEN** components need to reach external services (ThingsBoard, InfluxDB)
- **THEN** endpoints are configured via ConfigMaps or Secrets
- **AND** support both in-cluster and external addresses

### Requirement: Configuration Management
The system SHALL manage configuration via Kubernetes ConfigMaps and Secrets.

#### Scenario: Store device models in ConfigMap
- **WHEN** device model JSON files are provided
- **THEN** they are stored in a ConfigMap
- **AND** mounted into simulation pods

#### Scenario: Store credentials in Secrets
- **WHEN** broker credentials or API keys are required
- **THEN** they are stored in Kubernetes Secrets
- **AND** injected as environment variables or files

#### Scenario: Hot-reload configuration
- **WHEN** a ConfigMap is updated
- **THEN** pods detect the change
- **AND** reload device models without restart (where supported)

### Requirement: Logging and Monitoring
The system SHALL emit structured logs and expose Prometheus metrics.

#### Scenario: Structured JSON logging
- **WHEN** a component logs an event
- **THEN** the log is formatted as JSON
- **AND** includes correlation IDs for distributed tracing

#### Scenario: Expose Prometheus metrics
- **WHEN** Prometheus scrapes the /metrics endpoint
- **THEN** it receives metrics for device counts, message rates, and error rates
- **AND** metrics are labeled by component and device group

#### Scenario: Integrate with existing monitoring
- **WHEN** the cluster has an existing Prometheus/Grafana stack
- **THEN** the platform ServiceMonitors are discovered
- **AND** dashboards can be imported

