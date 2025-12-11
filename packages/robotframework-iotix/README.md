# Robot Framework IoTix Library

Robot Framework library for IoTix device simulation platform testing.

## Installation

```bash
pip install robotframework-iotix
```

## Usage

```robotframework
*** Settings ***
Library    IotixLibrary    base_url=http://localhost:8080

*** Test Cases ***
Create And Start Device
    ${device}=    Create Device    model_id=temperature-sensor
    Should Not Be Empty    ${device}[id]
    Start Device    ${device}[id]
    Device Should Be Running    ${device}[id]
    [Teardown]    Delete Device    ${device}[id]
```

## Keywords

### Device Model Keywords
- `Register Device Model` - Register a new device model
- `Get Device Model` - Get a device model by ID
- `List Device Models` - List all device models

### Device Keywords
- `Create Device` - Create a new device instance
- `Get Device` - Get device details
- `Start Device` - Start a device
- `Stop Device` - Stop a device
- `Delete Device` - Delete a device
- `Get Device Metrics` - Get device metrics
- `Device Should Be Running` - Assert device is running
- `Device Should Be Connected` - Assert device is connected

### Group Keywords
- `Create Device Group` - Create a group of devices
- `Start Device Group` - Start all devices in a group
- `Stop Device Group` - Stop all devices in a group
- `Delete Device Group` - Delete a device group

### Utility Keywords
- `Wait For Telemetry` - Wait for device to send telemetry
- `Get Stats` - Get engine statistics

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| base_url | http://localhost:8080 | Device engine API URL |
| timeout | 30 | Request timeout in seconds |

## License

Apache License 2.0
