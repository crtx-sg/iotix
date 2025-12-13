# Design: Hybrid Device Support

## Context

The iotix platform currently focuses on simulated device testing. However, real-world IoT testing scenarios often require validating backend systems with actual hardware prototypes alongside simulated devices.

**Stakeholders**:
- QA engineers needing unified test environments
- Hardware engineers validating physical prototypes
- DevOps teams managing hybrid deployments

**Constraints**:
- Must not break existing simulated device functionality
- Must maintain 100% open-source requirement
- Simple passthrough mode (no complex transformations)

## Goals / Non-Goals

### Goals
- Enable proxy devices that forward external device telemetry to InfluxDB
- Support MQTT, HTTP webhook, and CoAP protocols for physical device ingestion
- Allow hybrid device groups mixing simulated and physical devices
- Tag all metrics with source type for filtering
- Provide unified visualization across device types

### Non-Goals
- Bidirectional control of physical devices (telemetry ingestion only)
- Complex payload transformation pipelines
- Auto-discovery of physical devices (defer to future)
- Non-JSON payload support (Protobuf, binary - defer to future)
- Command forwarding to physical devices

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        Hybrid Device Architecture                         │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  External Physical Devices          iotix Device Engine                   │
│  ┌─────────────────┐               ┌────────────────────────────────────┐│
│  │ Physical Device │───MQTT───────▶│  MqttProxyAdapter                  ││
│  │ (MQTT Client)   │               │  - Subscribe to external topics    ││
│  └─────────────────┘               └──────────────┬─────────────────────┘│
│                                                   │                       │
│  ┌─────────────────┐               ┌──────────────▼─────────────────────┐│
│  │ Physical Device │───HTTP POST──▶│  HttpProxyAdapter                  ││
│  │ (HTTP Sender)   │               │  - Webhook endpoint per device     ││
│  └─────────────────┘               └──────────────┬─────────────────────┘│
│                                                   │                       │
│  ┌─────────────────┐               ┌──────────────▼─────────────────────┐│
│  │ Physical Device │◀──CoAP───────▶│  CoApProxyAdapter                  ││
│  │ (CoAP Server)   │   observe     │  - Observe external resources      ││
│  └─────────────────┘               └──────────────┬─────────────────────┘│
│                                                   │                       │
│                                    ┌──────────────▼─────────────────────┐│
│                                    │  ProxyDevice                       ││
│                                    │  - Passthrough payload forwarding  ││
│                                    │  - Tags source: "physical"         ││
│                                    └──────────────┬─────────────────────┘│
│                                                   │                       │
│  Simulated Devices                 ┌──────────────▼─────────────────────┐│
│  ┌─────────────────┐               │  MetricsWriter                     ││
│  │ VirtualDevice   │──────────────▶│  - source tag: simulated|physical  ││
│  └─────────────────┘               └──────────────┬─────────────────────┘│
│                                                   │                       │
│                                    ┌──────────────▼─────────────────────┐│
│                                    │  InfluxDB → Grafana                ││
│                                    │  - Unified dashboards              ││
│                                    └────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────┘
```

## Decisions

### D1: Proxy Device as Separate Type

**Decision**: Introduce `proxy` as a new device type distinct from existing types.

**Rationale**:
- Clear separation: virtual devices generate data, proxy devices forward data
- Simpler mental model for users
- Allows different lifecycle (no telemetry generators)
- Enables type-specific API endpoints (bind/unbind)

### D2: Protocol-Specific Proxy Adapters

**Decision**: Create dedicated proxy adapters for MQTT, HTTP, and CoAP.

**Rationale**:
- Each protocol has unique ingestion semantics
- Consistent with existing adapter pattern
- Easy to extend with new protocols

### D3: Source Tagging

**Decision**: Add mandatory `source` tag to all InfluxDB measurements.

**Values**: `simulated` | `physical`

**Rationale**:
- Enables filtering in Grafana queries
- Allows comparative dashboards
- Low overhead (single tag per data point)

### D4: Simple Passthrough Mode

**Decision**: Forward payloads as-is without transformation.

**Rationale**:
- Simplest implementation
- Preserves original device data structure
- No complex configuration required
- Users can handle transformation externally if needed

### D5: Explicit Binding

**Decision**: Proxy devices require explicit binding via API call.

**Rationale**:
- Security: No auto-accept of external data
- Auditability: Binding operations are logged
- Clarity: Users explicitly define data flow

## Component Design

### ProxyDevice Class

```python
class ProxyDevice:
    """Proxy device that forwards external telemetry to InfluxDB."""

    def __init__(self, device_id: str, model: DeviceModelConfig, group_id: str | None = None):
        self.device_id = device_id
        self.model = model
        self.group_id = group_id
        self.status = DeviceStatus.CREATED
        self.binding: BindingConfig | None = None
        self._adapter: ProxyAdapterBase | None = None
        self.messages_received = 0
        self.bytes_received = 0

    async def bind(self, config: BindingConfig) -> None:
        """Bind to external device source."""
        # Create protocol-specific adapter
        # Start listening/subscribing
        # Update status to RUNNING

    async def unbind(self) -> None:
        """Unbind from external device source."""
        # Stop adapter
        # Update status to STOPPED

    async def on_telemetry(self, payload: dict) -> None:
        """Handle incoming telemetry - passthrough to InfluxDB."""
        # Write to InfluxDB with source="physical" tag
```

### Binding Configuration

```json
{
  "protocol": "mqtt",
  "broker": "external-broker.local",
  "port": 1883,
  "topic": "devices/sensor-001/telemetry",
  "qos": 1
}
```

### Updated InfluxDB Schema

| Measurement | Tags | Fields |
|-------------|------|--------|
| telemetry | device_id, model_id, group_id, **source** | Passthrough payload fields |
| device_events | device_id, model_id, event_type, group_id, **source** | value |
| connections | device_id, protocol, **source** | connected, latency_ms |

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Payload format varies across devices | Passthrough preserves original; consistent tagging enables filtering |
| Security exposure | Explicit binding required; credentials via environment variables |
| Dashboard confusion | Mandatory source tagging; color-coded visualizations |

## Migration Plan

Additive feature. No migration required.

**Phases**:
1. Phase 1: ProxyDevice class + MQTT proxy adapter + source tagging
2. Phase 2: HTTP webhook proxy adapter
3. Phase 3: CoAP observe proxy adapter
4. Phase 4: Grafana dashboard updates
