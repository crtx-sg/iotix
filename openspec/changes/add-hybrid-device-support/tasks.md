# Tasks: Hybrid Device Support

## 1. Core Infrastructure

- [ ] 1.1 Add `proxy` to DeviceType enum in `models.py`
- [ ] 1.2 Create `BindingConfig` Pydantic model for binding configuration
- [ ] 1.3 Create `BindingStatus` response model
- [ ] 1.4 Add `source` parameter to `MetricsWriter.write_telemetry()` method
- [ ] 1.5 Add `source` tag to all InfluxDB write operations
- [ ] 1.6 Update `write_engine_stats()` to include `active_simulated` and `active_physical` counts

## 2. ProxyDevice Implementation

- [ ] 2.1 Create `ProxyDevice` class in `services/device-engine/src/proxy_device.py`
- [ ] 2.2 Implement `bind()` method for establishing external connection
- [ ] 2.3 Implement `unbind()` method for disconnecting
- [ ] 2.4 Implement `on_telemetry()` passthrough handler
- [ ] 2.5 Implement `to_dict()` including binding status
- [ ] 2.6 Implement `get_metrics()` for proxy-specific metrics

## 3. Protocol Proxy Adapters

### 3.1 MQTT Proxy Adapter
- [ ] 3.1.1 Create `MqttProxyAdapter` class in `adapters/mqtt_proxy.py`
- [ ] 3.1.2 Implement `bind()` to subscribe to external MQTT topic
- [ ] 3.1.3 Implement `unbind()` to unsubscribe and disconnect
- [ ] 3.1.4 Implement message callback to forward to ProxyDevice

### 3.2 HTTP Proxy Adapter
- [ ] 3.2.1 Create `HttpProxyAdapter` class in `adapters/http_proxy.py`
- [ ] 3.2.2 Implement `bind()` to register webhook endpoint
- [ ] 3.2.3 Implement `unbind()` to remove webhook endpoint
- [ ] 3.2.4 Add webhook route handler in `main.py`

### 3.3 CoAP Proxy Adapter
- [ ] 3.3.1 Create `CoApProxyAdapter` class in `adapters/coap_proxy.py`
- [ ] 3.3.2 Implement `bind()` to observe external CoAP resource
- [ ] 3.3.3 Implement `unbind()` to cancel observation
- [ ] 3.3.4 Implement notification callback to forward to ProxyDevice

## 4. Device Manager Updates

- [ ] 4.1 Update `DeviceManager` to handle proxy device creation
- [ ] 4.2 Add `bind_device()` method to manager
- [ ] 4.3 Add `unbind_device()` method to manager
- [ ] 4.4 Update `get_stats()` to separate simulated/physical counts
- [ ] 4.5 Update hybrid group handling (skip proxy devices for dropout)

## 5. REST API Endpoints

- [ ] 5.1 Add `POST /api/v1/devices/{id}/bind` endpoint
- [ ] 5.2 Add `POST /api/v1/devices/{id}/unbind` endpoint
- [ ] 5.3 Update `GET /api/v1/devices/{id}` to include binding info
- [ ] 5.4 Update device list endpoint to filter by type/source

## 6. Grafana Dashboard Updates

- [ ] 6.1 Add "Device Count by Source" pie chart panel
- [ ] 6.2 Add "Telemetry by Source" comparative time series panel
- [ ] 6.3 Add "Physical Devices" status table panel
- [ ] 6.4 Update existing queries to support source filtering
- [ ] 6.5 Add source-based color scheme (blue=simulated, green=physical)

## 7. Testing

- [ ] 7.1 Unit tests for ProxyDevice class
- [ ] 7.2 Unit tests for MqttProxyAdapter
- [ ] 7.3 Unit tests for HttpProxyAdapter
- [ ] 7.4 Unit tests for CoApProxyAdapter
- [ ] 7.5 Integration test for hybrid device group
- [ ] 7.6 Integration test for source tagging in InfluxDB

## 8. Documentation

- [ ] 8.1 Update README with hybrid device support section
- [ ] 8.2 Add example proxy device model JSON
- [ ] 8.3 Document binding API endpoints
- [ ] 8.4 Add troubleshooting section for physical device connectivity
