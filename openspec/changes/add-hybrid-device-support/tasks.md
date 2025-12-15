# Tasks: Hybrid Device Support

## 1. Core Infrastructure

- [x] 1.1 Add `proxy` to DeviceType enum in `models.py`
- [x] 1.2 Create `BindingConfig` Pydantic model for binding configuration
- [x] 1.3 Create `BindingStatus` response model
- [x] 1.4 Add `source` parameter to `MetricsWriter.write_telemetry()` method
- [x] 1.5 Add `source` tag to all InfluxDB write operations
- [x] 1.6 Update `write_engine_stats()` to include `active_simulated` and `active_physical` counts

## 2. ProxyDevice Implementation

- [x] 2.1 Create `ProxyDevice` class in `services/device-engine/src/proxy_device.py`
- [x] 2.2 Implement `bind()` method for establishing external connection
- [x] 2.3 Implement `unbind()` method for disconnecting
- [x] 2.4 Implement `on_telemetry()` passthrough handler
- [x] 2.5 Implement `to_dict()` including binding status
- [x] 2.6 Implement `get_metrics()` for proxy-specific metrics

## 3. Protocol Proxy Adapters

### 3.1 MQTT Proxy Adapter
- [x] 3.1.1 Create `MqttProxyAdapter` class in `adapters/mqtt_proxy.py`
- [x] 3.1.2 Implement `bind()` to subscribe to external MQTT topic
- [x] 3.1.3 Implement `unbind()` to unsubscribe and disconnect
- [x] 3.1.4 Implement message callback to forward to ProxyDevice

### 3.2 HTTP Proxy Adapter
- [x] 3.2.1 Create `HttpProxyAdapter` class in `adapters/http_proxy.py`
- [x] 3.2.2 Implement `bind()` to register webhook endpoint
- [x] 3.2.3 Implement `unbind()` to remove webhook endpoint
- [x] 3.2.4 Add webhook route handler in `main.py`

### 3.3 CoAP Proxy Adapter
- [ ] 3.3.1 Create `CoApProxyAdapter` class in `adapters/coap_proxy.py` (deferred - not in MVP)
- [ ] 3.3.2 Implement `bind()` to observe external CoAP resource (deferred)
- [ ] 3.3.3 Implement `unbind()` to cancel observation (deferred)
- [ ] 3.3.4 Implement notification callback to forward to ProxyDevice (deferred)

## 4. Device Manager Updates

- [x] 4.1 Update `DeviceManager` to handle proxy device creation
- [x] 4.2 Add `bind_device()` method to manager
- [x] 4.3 Add `unbind_device()` method to manager
- [x] 4.4 Update `get_stats()` to separate simulated/physical counts
- [x] 4.5 Update hybrid group handling (skip proxy devices for dropout)

## 5. REST API Endpoints

- [x] 5.1 Add `POST /api/v1/devices/{id}/bind` endpoint
- [x] 5.2 Add `POST /api/v1/devices/{id}/unbind` endpoint
- [x] 5.3 Add `GET /api/v1/devices/{id}/binding` endpoint for binding status
- [x] 5.4 Add `POST /api/v1/webhooks/{device_id}` webhook receiver endpoint

## 6. Grafana Dashboard Updates

- [x] 6.1 Add "Simulated Devices" stat panel
- [x] 6.2 Add "Physical Devices" stat panel
- [x] 6.3 Add "Telemetry by Source" pie chart panel
- [x] 6.4 Add source filter variable for dashboard filtering
- [x] 6.5 Add source-based color scheme (blue=simulated, green=physical)

## 7. Testing

- [ ] 7.1 Unit tests for ProxyDevice class (deferred)
- [ ] 7.2 Unit tests for MqttProxyAdapter (deferred)
- [ ] 7.3 Unit tests for HttpProxyAdapter (deferred)
- [ ] 7.4 Unit tests for CoApProxyAdapter (deferred)
- [ ] 7.5 Integration test for hybrid device group (deferred)
- [ ] 7.6 Integration test for source tagging in InfluxDB (deferred)

## 8. Documentation

- [x] 8.1 Update README with hybrid device support section
- [x] 8.2 Add example proxy device model JSON (`examples/device-models/physical-sensor-proxy.json`)
- [x] 8.3 Document binding API endpoints (in README)
- [x] 8.4 Add troubleshooting section for physical device connectivity (in README)
