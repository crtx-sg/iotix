# device-virtualization Specification

## Purpose
TBD - created by archiving change add-iot-simulation-platform. Update Purpose after archive.
## Requirements
### Requirement: Device Model Definition
The system SHALL support JSON-based device model definitions that specify device type, protocol, telemetry attributes, and behaviors.

#### Scenario: Create device model from JSON
- **WHEN** a user provides a valid JSON device model definition
- **THEN** the system validates the model against the schema
- **AND** registers the model for instantiation

#### Scenario: Reject invalid device model
- **WHEN** a user provides an invalid JSON device model
- **THEN** the system returns validation errors with specific field violations
- **AND** does not register the model

### Requirement: Device Type Support
The system SHALL support the following device types: sensor, gateway, actuator, and custom.

#### Scenario: Create sensor device
- **WHEN** a device model specifies type "sensor"
- **THEN** the system creates a device that publishes telemetry data

#### Scenario: Create gateway device
- **WHEN** a device model specifies type "gateway"
- **THEN** the system creates a device that can aggregate and forward messages from child devices

#### Scenario: Create actuator device
- **WHEN** a device model specifies type "actuator"
- **THEN** the system creates a device that receives commands and publishes state changes

#### Scenario: Create custom device
- **WHEN** a device model specifies type "custom" with a behavior script
- **THEN** the system creates a device that executes the custom behavior logic

### Requirement: Protocol Adapters
The system SHALL support MQTT, CoAP, and HTTP protocols via pluggable adapters.

#### Scenario: MQTT protocol communication
- **WHEN** a device model specifies protocol "mqtt"
- **THEN** the device connects to the configured MQTT broker
- **AND** publishes/subscribes using MQTT semantics (topics, QoS)

#### Scenario: CoAP protocol communication
- **WHEN** a device model specifies protocol "coap"
- **THEN** the device communicates using CoAP methods (GET, PUT, POST, DELETE)
- **AND** supports observable resources

#### Scenario: HTTP protocol communication
- **WHEN** a device model specifies protocol "http"
- **THEN** the device communicates using HTTP/HTTPS requests
- **AND** supports standard REST patterns

#### Scenario: Custom protocol adapter
- **WHEN** a custom protocol adapter is registered
- **THEN** the system loads the adapter plugin
- **AND** devices can use the custom protocol

### Requirement: Telemetry Generation
The system SHALL generate realistic telemetry data based on device model specifications.

#### Scenario: Random value generation
- **WHEN** a telemetry attribute specifies generator type "random"
- **THEN** the system generates values within the configured min/max range
- **AND** applies the specified distribution (uniform, normal, exponential)

#### Scenario: Sequence value generation
- **WHEN** a telemetry attribute specifies generator type "sequence"
- **THEN** the system generates incrementing or decrementing values
- **AND** supports configurable start, step, min, max, and wrap behavior

#### Scenario: Constant value generation
- **WHEN** a telemetry attribute specifies generator type "constant"
- **THEN** the system returns the same configured value on each interval

#### Scenario: Historical replay
- **WHEN** a telemetry attribute specifies generator type "replay"
- **THEN** the system replays data from a historical dataset file
- **AND** maintains timing intervals from the original data
- **AND** supports looping when data is exhausted

#### Scenario: Custom payload generation
- **WHEN** a telemetry attribute specifies generator type "custom"
- **THEN** the system invokes the custom Python hook
- **AND** uses the returned payload (including binary formats)

### Requirement: Multi-Parameter Telemetry
The system SHALL support device models with multiple telemetry parameters of different types and intervals.

#### Scenario: Multiple numeric parameters
- **WHEN** a device model defines multiple telemetry attributes (e.g., temperature, pressure, humidity)
- **THEN** the system generates values for each attribute independently
- **AND** each attribute can have its own generator configuration and interval

#### Scenario: Mixed data types
- **WHEN** a device model defines telemetry with different data types (number, integer, boolean, string, binary)
- **THEN** the system generates appropriate values for each type
- **AND** serializes the payload according to the protocol requirements

#### Scenario: Independent intervals
- **WHEN** telemetry attributes specify different intervalMs values
- **THEN** the system publishes each attribute at its configured interval
- **AND** attributes are not synchronized unless explicitly configured

### Requirement: Binary Data Support
The system SHALL support binary telemetry data for sensors that produce raw binary output (e.g., ECG, images, audio).

#### Scenario: Binary array telemetry
- **WHEN** a telemetry attribute specifies type "binary" with a samples count
- **THEN** the system generates the specified number of samples as a binary array
- **AND** supports configurable sample size (8-bit, 16-bit, 32-bit)

#### Scenario: Replay from binary file
- **WHEN** a telemetry attribute specifies generator type "replay" with a binary data file
- **THEN** the system reads chunks from the binary file at each interval
- **AND** transmits raw bytes without JSON encoding

#### Scenario: Custom binary generator
- **WHEN** a telemetry attribute specifies generator type "custom" with a binary handler
- **THEN** the custom Python function returns raw bytes
- **AND** the system transmits the binary payload directly

### Requirement: Device Lifecycle Management
The system SHALL manage the complete lifecycle of virtual devices: create, start, stop, and destroy.

#### Scenario: Create device instance
- **WHEN** a create request is received for a registered model
- **THEN** the system instantiates the device in a "created" state
- **AND** assigns a unique device ID

#### Scenario: Start device instance
- **WHEN** a start command is issued for a created device
- **THEN** the device establishes protocol connection
- **AND** begins telemetry generation according to its model

#### Scenario: Stop device instance
- **WHEN** a stop command is issued for a running device
- **THEN** the device gracefully disconnects
- **AND** ceases telemetry generation

#### Scenario: Destroy device instance
- **WHEN** a destroy command is issued for a device
- **THEN** the system removes all device resources
- **AND** the device ID is released

### Requirement: Device Group Operations
The system SHALL support batch operations on device groups for managing large numbers of devices.

#### Scenario: Create device group
- **WHEN** a user defines a device group with a model and count
- **THEN** the system creates the specified number of device instances
- **AND** assigns sequential or template-based IDs

#### Scenario: Start device group
- **WHEN** a start command is issued for a device group
- **THEN** all devices in the group start with configurable launch strategy
- **AND** the system reports aggregate start status

#### Scenario: Stop device group
- **WHEN** a stop command is issued for a device group
- **THEN** all devices in the group stop gracefully
- **AND** the system reports aggregate stop status

### Requirement: Scale Launch Strategies
The system SHALL support multiple launch strategies for starting large numbers of devices with controlled resource utilization.

#### Scenario: Immediate launch strategy
- **WHEN** a device group is started with strategy "immediate"
- **THEN** the system starts all devices concurrently
- **AND** maximizes startup throughput

#### Scenario: Linear launch strategy
- **WHEN** a device group is started with strategy "linear" and a delay value
- **THEN** the system starts devices one at a time with fixed delay between each
- **AND** provides predictable, controlled ramp-up

#### Scenario: Batch launch strategy
- **WHEN** a device group is started with strategy "batch", batch size, and delay
- **THEN** the system starts devices in batches of the specified size
- **AND** waits for the configured delay between batches
- **AND** balances speed with resource management

#### Scenario: Exponential launch strategy
- **WHEN** a device group is started with strategy "exponential", base delay, and exponent
- **THEN** the system starts devices with exponentially increasing delays
- **AND** delays are calculated as: delay_ms × (exponent_base ^ device_index)
- **AND** delays are capped at a configurable maximum

#### Scenario: Launch configuration
- **WHEN** a launch configuration is provided
- **THEN** the system accepts the following parameters:
  - strategy: immediate | linear | batch | exponential
  - delayMs: base delay in milliseconds
  - batchSize: number of devices per batch (for batch strategy)
  - maxDelayMs: maximum delay cap (for exponential strategy)
  - exponentBase: multiplier for exponential delay calculation

### Requirement: Device Dropout Simulation
The system SHALL support simulating device dropouts/failures for chaos engineering and resilience testing.

#### Scenario: Immediate dropout strategy
- **WHEN** a device group dropout is initiated with strategy "immediate"
- **THEN** the system disconnects all specified devices at once
- **AND** simulates sudden mass device failure

#### Scenario: Linear dropout strategy
- **WHEN** a device group dropout is initiated with strategy "linear" and a delay value
- **THEN** the system disconnects devices one at a time with fixed delay between each
- **AND** simulates gradual device degradation

#### Scenario: Exponential dropout strategy
- **WHEN** a device group dropout is initiated with strategy "exponential", base delay, and exponent
- **THEN** the system disconnects devices with exponentially increasing delays
- **AND** delays are calculated as: delay_ms × (exponent_base ^ device_index)
- **AND** simulates accelerating failure cascade

#### Scenario: Random dropout strategy
- **WHEN** a device group dropout is initiated with strategy "random" and a duration window
- **THEN** the system disconnects devices at random intervals within the time window
- **AND** simulates unpredictable real-world failure patterns

#### Scenario: Dropout configuration
- **WHEN** a dropout configuration is provided
- **THEN** the system accepts the following parameters:
  - strategy: immediate | linear | exponential | random
  - count: absolute number of devices to drop (optional)
  - percentage: percentage of devices to drop (optional, used if count not specified)
  - delayMs: base delay between dropouts in milliseconds
  - durationMs: total duration for dropout simulation (for random strategy)
  - exponentBase: multiplier for exponential delay calculation
  - reconnect: whether devices should reconnect after dropout
  - reconnectDelayMs: delay before reconnection attempt

#### Scenario: Dropout with automatic reconnection
- **WHEN** a dropout configuration specifies reconnect: true
- **THEN** the system disconnects the devices according to the strategy
- **AND** after reconnectDelayMs, the affected devices attempt to reconnect
- **AND** the system reports reconnection success/failure

#### Scenario: Dropout via API
- **WHEN** a POST request is made to /api/v1/groups/{groupId}/dropout with dropout config
- **THEN** the system initiates the dropout simulation
- **AND** returns the number of devices affected and estimated duration

### Requirement: Device Behavior Engine
The system SHALL execute device behaviors defined as state machines with triggers and actions.

#### Scenario: Event-triggered behavior
- **WHEN** a device receives an event matching a behavior trigger
- **THEN** the system executes the corresponding action
- **AND** updates the device state

#### Scenario: Time-based behavior
- **WHEN** a behavior specifies a time-based trigger
- **THEN** the system executes the action at the scheduled time
- **AND** supports cron-style scheduling

#### Scenario: Simulated failure behavior
- **WHEN** a behavior defines a failure condition
- **THEN** the device can simulate disconnections, errors, or degraded performance
- **AND** optionally recovers after a configured duration

### Requirement: Device REST API
The system SHALL provide a REST API for device management operations.

#### Scenario: List devices via API
- **WHEN** a GET request is made to /api/v1/devices
- **THEN** the system returns a paginated list of devices with status

#### Scenario: Create device via API
- **WHEN** a POST request is made to /api/v1/devices with a model reference
- **THEN** the system creates and returns the device instance

#### Scenario: Control device via API
- **WHEN** a POST request is made to /api/v1/devices/{id}/start or /stop
- **THEN** the system executes the lifecycle command and returns status

#### Scenario: Get device metrics via API
- **WHEN** a GET request is made to /api/v1/devices/{id}/metrics
- **THEN** the system returns current telemetry and connection statistics

