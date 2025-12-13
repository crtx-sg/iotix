# Change: Add Hybrid Device Support

## Status: PROPOSED

Awaiting review and approval.

## Why

Organizations often need to test IoT systems in mixed environments where both simulated and physical devices coexist. Current iotix architecture only supports simulated devices, forcing users to maintain separate monitoring systems for physical hardware during integration testing. This creates blind spots in end-to-end testing scenarios and prevents unified visibility across hybrid deployments.

**Use Cases**:
- Integration testing: Validate backend behavior with a mix of 1000 simulated devices + 10 physical prototypes
- Gradual migration: Monitor physical devices alongside simulated replacements during hardware phase-out
- Edge case reproduction: Capture real device telemetry patterns to improve simulation fidelity
- Production shadow testing: Compare simulated device behavior against production physical devices

## What Changes

### New Capabilities

- **Proxy Device Type**: New device type that subscribes to external device topics and forwards telemetry to InfluxDB without generating its own data
- **Multi-Protocol Proxy Support**: Proxy devices support MQTT, HTTP webhook, and CoAP observation for ingesting physical device data
- **Hybrid Device Groups**: Device groups can contain a mix of simulated and proxy (physical) devices
- **Source Tagging**: All metrics tagged with `source: simulated | physical | proxy` for filtering and comparison
- **Device Discovery**: Optional auto-discovery of physical devices via MQTT wildcard subscriptions or mDNS
- **Telemetry Passthrough**: Physical device payloads forwarded with minimal transformation, preserving original structure
- **Unified Dashboards**: Grafana dashboards updated to show combined and comparative views

### Architecture Changes

```
                    ┌─────────────────────────────────────────────────────┐
                    │                   iotix Platform                     │
                    ├─────────────────────────────────────────────────────┤
Physical Devices    │                                                      │
┌─────────┐        │  ┌─────────────┐                                     │
│ Sensor  │──MQTT──┼─▶│   Proxy     │──┐                                  │
└─────────┘        │  │   Device    │  │                                  │
┌─────────┐        │  └─────────────┘  │    ┌─────────────┐              │
│ Gateway │──HTTP──┼─▶│   Proxy     │──┼───▶│  InfluxDB   │───▶ Grafana  │
└─────────┘        │  │   Device    │  │    │  (tagged)   │              │
┌─────────┐        │  └─────────────┘  │    └─────────────┘              │
│ Actuator│──CoAP──┼─▶│   Proxy     │──┘          ▲                      │
└─────────┘        │  │   Device    │             │                      │
                    │  └─────────────┘             │                      │
                    │                              │                      │
Simulated Devices   │  ┌─────────────┐             │                      │
                    │  │  Virtual    │─────────────┘                      │
                    │  │  Devices    │                                    │
                    │  └─────────────┘                                    │
                    └─────────────────────────────────────────────────────┘
```

### API Changes

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/models` | POST | Extended to accept `type: "proxy"` device models |
| `/api/v1/devices/{id}/bind` | POST | **NEW**: Bind proxy device to external device topic/endpoint |
| `/api/v1/devices/{id}/unbind` | POST | **NEW**: Unbind proxy device from external source |
| `/api/v1/discovery/start` | POST | **NEW**: Start auto-discovery for physical devices |
| `/api/v1/discovery/stop` | POST | **NEW**: Stop auto-discovery |
| `/api/v1/discovery/devices` | GET | **NEW**: List discovered physical devices |

## Impact

- **Affected specs**:
  - `specs/device-virtualization/spec.md` (MODIFIED) - Add proxy device type, binding operations
  - `specs/visualization/spec.md` (MODIFIED) - Add source tagging, hybrid dashboards

- **Affected code**:
  - `services/device-engine/src/device.py` - Add ProxyDevice class
  - `services/device-engine/src/adapters/` - Add proxy adapters for each protocol
  - `services/device-engine/src/models.py` - Extend DeviceType enum, add binding models
  - `services/device-engine/src/manager.py` - Support hybrid groups, discovery
  - `services/device-engine/src/main.py` - New API endpoints
  - `services/device-engine/src/metrics.py` - Add source tagging
  - `deploy/docker/grafana/dashboards/` - Update dashboard JSON

- **Dependencies**:
  - No new external dependencies required
  - Optional: zeroconf (Python) for mDNS discovery

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Physical device message format incompatibility | Medium | Medium | Configurable payload transformers; passthrough mode for unknown formats |
| Network security concerns (external device access) | Medium | High | Explicit binding required; no auto-accept; network policy documentation |
| Performance impact from high-volume physical devices | Low | Medium | Rate limiting per proxy device; async message processing |
| Confusion between simulated and physical data | Low | High | Mandatory source tagging; distinct dashboard panels; color coding |

## Success Criteria

1. [ ] Proxy device type successfully ingests MQTT messages from external broker topics
2. [ ] Proxy device type successfully receives HTTP webhook POSTs from physical devices
3. [ ] Proxy device type successfully observes CoAP resources from physical devices
4. [ ] Hybrid device groups support mixed simulated and proxy devices
5. [ ] All metrics tagged with source type (simulated/physical/proxy)
6. [ ] Grafana dashboards show unified and comparative views
7. [ ] Auto-discovery identifies physical devices on MQTT broker
8. [ ] Documentation covers hybrid deployment scenarios
