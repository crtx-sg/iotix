# Device Virtualization Layer

## ADDED Requirements

### Requirement: Proxy Device Type
The system SHALL support a proxy device type that forwards telemetry from external physical devices to InfluxDB.

#### Scenario: Create proxy device model
- **WHEN** a user provides a device model with type "proxy"
- **THEN** the system validates the model against the proxy schema
- **AND** registers the model for instantiation

#### Scenario: Instantiate proxy device
- **WHEN** a create request is received for a proxy model
- **THEN** the system creates a proxy device in "created" state
- **AND** the device does not generate telemetry until bound

### Requirement: Proxy Device Binding
The system SHALL support binding proxy devices to external telemetry sources.

#### Scenario: Bind proxy device to MQTT topic
- **WHEN** a bind request specifies protocol "mqtt" with broker, port, and topic
- **THEN** the proxy device subscribes to the external MQTT topic
- **AND** incoming messages are forwarded to InfluxDB with source tag "physical"
- **AND** the device status changes to "running"

#### Scenario: Bind proxy device to HTTP webhook
- **WHEN** a bind request specifies protocol "http"
- **THEN** the system creates a webhook endpoint for the proxy device
- **AND** returns the webhook URL to the caller
- **AND** incoming HTTP POST payloads are forwarded to InfluxDB with source tag "physical"

#### Scenario: Bind proxy device to CoAP resource
- **WHEN** a bind request specifies protocol "coap" with resource URI
- **THEN** the proxy device starts observing the external CoAP resource
- **AND** notifications are forwarded to InfluxDB with source tag "physical"

#### Scenario: Unbind proxy device
- **WHEN** an unbind request is made for a bound proxy device
- **THEN** the device stops receiving external telemetry
- **AND** the device status changes to "stopped"

#### Scenario: Reject bind for non-proxy device
- **WHEN** a bind request is made for a non-proxy device type
- **THEN** the system returns an error indicating bind is only for proxy devices

### Requirement: Proxy Device Passthrough
The system SHALL forward external telemetry payloads without transformation.

#### Scenario: Passthrough JSON payload
- **WHEN** a proxy device receives a JSON payload from an external source
- **THEN** all fields from the payload are written to InfluxDB as-is
- **AND** the source tag is set to "physical"

#### Scenario: Track proxy device metrics
- **WHEN** a proxy device receives telemetry
- **THEN** the system increments messages_received counter
- **AND** updates bytes_received with payload size
- **AND** updates last_telemetry_at timestamp

### Requirement: Hybrid Device Groups
The system SHALL support device groups containing both simulated and proxy devices.

#### Scenario: Create hybrid device group
- **WHEN** a user creates a device group with mixed device types
- **THEN** the system creates both virtual and proxy devices in the group
- **AND** tracks devices by type within the group

#### Scenario: Start hybrid device group
- **WHEN** a start command is issued for a hybrid group
- **THEN** virtual devices start generating telemetry
- **AND** proxy devices remain in their current binding state
- **AND** launch strategies apply only to virtual devices

#### Scenario: Get hybrid group statistics
- **WHEN** statistics are requested for a hybrid group
- **THEN** the response includes breakdown by device type
- **AND** shows simulated_count and physical_count separately

#### Scenario: Dropout not supported for proxy devices
- **WHEN** a dropout simulation is requested for a hybrid group
- **THEN** only virtual devices are affected by the dropout
- **AND** proxy devices continue receiving external telemetry

### Requirement: Proxy Device REST API
The system SHALL provide REST API endpoints for proxy device operations.

#### Scenario: Bind device via API
- **WHEN** a POST request is made to /api/v1/devices/{id}/bind with binding config
- **THEN** the system binds the proxy device to the external source
- **AND** returns the binding status

#### Scenario: Unbind device via API
- **WHEN** a POST request is made to /api/v1/devices/{id}/unbind
- **THEN** the system unbinds the proxy device
- **AND** returns success status

#### Scenario: Get binding status via API
- **WHEN** a GET request is made to /api/v1/devices/{id}
- **THEN** the response includes binding configuration if bound
- **AND** shows the external source details

## MODIFIED Requirements

### Requirement: Device Type Support
The system SHALL support the following device types: sensor, gateway, actuator, custom, and proxy.

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

#### Scenario: Create proxy device
- **WHEN** a device model specifies type "proxy"
- **THEN** the system creates a device that forwards external telemetry
- **AND** the device requires binding before receiving data
