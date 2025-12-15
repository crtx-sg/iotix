# Network Simulation

## ADDED Requirements

### Requirement: Chaos Mesh Integration
The system SHALL integrate with Chaos Mesh for network fault injection.

#### Scenario: Install Chaos Mesh dependency
- **WHEN** the platform is deployed with network simulation enabled
- **THEN** Chaos Mesh CRDs and controllers are installed
- **AND** the chaos-daemon runs on simulation nodes

#### Scenario: Verify Chaos Mesh health
- **WHEN** the platform performs health checks
- **THEN** Chaos Mesh controller availability is verified
- **AND** alerts are raised if unavailable

### Requirement: Network Latency Injection
The system SHALL inject configurable network latency to simulate real-world conditions.

#### Scenario: Add fixed latency
- **WHEN** a latency experiment specifies a fixed delay (e.g., 100ms)
- **THEN** all packets from target devices experience the configured delay
- **AND** latency is applied bidirectionally

#### Scenario: Add variable latency with jitter
- **WHEN** a latency experiment specifies delay with jitter (e.g., 100ms +/- 20ms)
- **THEN** packet delays vary within the specified range
- **AND** jitter distribution follows a normal curve

#### Scenario: Target specific device groups
- **WHEN** a latency experiment targets a device group label
- **THEN** only devices in that group experience latency
- **AND** other devices communicate normally

### Requirement: Packet Loss Simulation
The system SHALL simulate packet loss to test device resilience.

#### Scenario: Apply percentage-based packet loss
- **WHEN** a packet loss experiment specifies 10% loss rate
- **THEN** approximately 10% of packets are dropped
- **AND** loss is applied randomly across all packets

#### Scenario: Apply burst packet loss
- **WHEN** a packet loss experiment specifies burst loss
- **THEN** packets are dropped in bursts simulating radio interference
- **AND** burst duration and frequency are configurable

#### Scenario: Correlate packet loss
- **WHEN** a packet loss experiment specifies correlation percentage
- **THEN** successive packet losses are correlated
- **AND** simulates realistic network degradation patterns

### Requirement: Network Partition Simulation
The system SHALL simulate network partitions to test split-brain scenarios.

#### Scenario: Create full partition
- **WHEN** a partition experiment isolates a device group
- **THEN** devices in the group cannot communicate with the broker
- **AND** the partition persists for the configured duration

#### Scenario: Create partial partition
- **WHEN** a partition experiment allows specific traffic (e.g., only ICMP)
- **THEN** matching traffic passes while other traffic is blocked
- **AND** simulates firewall or routing issues

#### Scenario: Heal partition automatically
- **WHEN** the partition duration expires
- **THEN** network connectivity is restored
- **AND** devices reconnect automatically

### Requirement: Bandwidth Throttling
The system SHALL limit bandwidth to simulate constrained networks.

#### Scenario: Apply rate limiting
- **WHEN** a bandwidth experiment specifies 1 Mbps limit
- **THEN** traffic is throttled to the specified rate
- **AND** excess packets are queued or dropped

#### Scenario: Simulate cellular network profiles
- **WHEN** a pre-defined profile (3G, 4G, satellite) is selected
- **THEN** corresponding bandwidth, latency, and loss are applied
- **AND** simulates real-world IoT connectivity

### Requirement: Chaos Experiment Management
The system SHALL provide APIs and UI for managing chaos experiments.

#### Scenario: Create experiment via API
- **WHEN** a POST request creates a NetworkChaos resource
- **THEN** the experiment is scheduled
- **AND** returns the experiment status

#### Scenario: List active experiments
- **WHEN** a GET request queries active experiments
- **THEN** all running experiments are returned with their parameters
- **AND** affected device counts are included

#### Scenario: Stop experiment immediately
- **WHEN** a DELETE request targets an experiment
- **THEN** the experiment is stopped immediately
- **AND** network conditions return to normal

#### Scenario: Schedule experiment window
- **WHEN** an experiment specifies a time window
- **THEN** chaos is applied only during that window
- **AND** automatically stops outside the window

### Requirement: Experiment Templates
The system SHALL provide pre-built experiment templates for common scenarios.

#### Scenario: Use "poor cellular" template
- **WHEN** the "poor-cellular" template is applied
- **THEN** 200ms latency, 5% packet loss, and 500kbps bandwidth are configured
- **AND** the template can be customized before application

#### Scenario: Use "intermittent connectivity" template
- **WHEN** the "intermittent-connectivity" template is applied
- **THEN** periodic 30-second partitions occur every 5 minutes
- **AND** simulates devices going in and out of coverage

#### Scenario: Create custom template
- **WHEN** a user saves an experiment configuration as a template
- **THEN** the template is stored for reuse
- **AND** can be shared across teams
