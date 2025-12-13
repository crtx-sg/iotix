# Visualization & Reporting

## MODIFIED Requirements

### Requirement: InfluxDB Metrics Storage
The system SHALL store time-series metrics in InfluxDB with source tagging.

#### Scenario: Write device telemetry metrics
- **WHEN** a device generates telemetry
- **THEN** metrics are written to InfluxDB "telemetry" measurement
- **AND** tagged with device_id, model_id, group_id, and source
- **AND** source tag is "simulated" for virtual devices
- **AND** source tag is "physical" for proxy devices

#### Scenario: Write engine statistics
- **WHEN** the device engine is running
- **THEN** aggregate stats are written to InfluxDB "engine_stats" measurement every 5 seconds
- **AND** includes active_devices, active_simulated, active_physical, total_messages, total_bytes, and active_groups fields

#### Scenario: Write device lifecycle events
- **WHEN** a device lifecycle event occurs (created, started, stopped, deleted, bound, unbound)
- **THEN** the event is written to InfluxDB "device_events" measurement
- **AND** tagged with device_id, model_id, event_type, group_id, and source

#### Scenario: Write connection metrics
- **WHEN** a device connects or disconnects from a broker
- **THEN** the connection state is written to InfluxDB "connections" measurement
- **AND** tagged with source to distinguish simulated from physical

#### Scenario: Write test metrics
- **WHEN** a test executes
- **THEN** execution metrics (duration, pass/fail, assertions) are written
- **AND** tagged with test suite and run ID

#### Scenario: Configure retention policies
- **WHEN** a retention policy is defined (e.g., 30 days)
- **THEN** data older than the policy is automatically deleted
- **AND** downsampled aggregates can be retained longer

## ADDED Requirements

### Requirement: Source-Based Filtering
The system SHALL support filtering metrics by device source type.

#### Scenario: Filter telemetry by source
- **WHEN** a Grafana query includes source filter
- **THEN** only metrics matching the source type are returned
- **AND** supports values "simulated" and "physical"

#### Scenario: Query all sources
- **WHEN** a Grafana query does not include source filter
- **THEN** metrics from all source types are returned
- **AND** can be grouped by source for comparison

### Requirement: Hybrid Dashboard Panels
The system SHALL provide dashboard panels for hybrid device monitoring.

#### Scenario: View device count by source
- **WHEN** a user views the device overview dashboard
- **THEN** a panel shows device count breakdown by source type
- **AND** displays simulated and physical counts separately

#### Scenario: Compare telemetry by source
- **WHEN** a user views comparative dashboard
- **THEN** time series panels show simulated and physical data side-by-side
- **AND** uses distinct colors for each source type

#### Scenario: View physical device status
- **WHEN** a user views physical devices panel
- **THEN** a table shows all proxy devices with binding status
- **AND** displays bound source details (broker, topic, endpoint)
