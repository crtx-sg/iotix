# Device Model Reference

Device models define the behavior, telemetry patterns, and protocol configuration for simulated IoT devices.

## Schema Overview

```json
{
  "id": "string",
  "name": "string",
  "type": "sensor|actuator|gateway|edge",
  "protocol": "mqtt|coap|http",
  "connection": { ... },
  "telemetry": [ ... ],
  "commands": [ ... ],
  "behaviors": [ ... ]
}
```

## Required Fields

### id (string)
Unique identifier for the device model.
- Pattern: `^[a-z0-9-]+$`
- Example: `"temperature-sensor-v1"`

### name (string)
Human-readable name for the device model.
- Example: `"Industrial Temperature Sensor"`

### type (string)
Device type classification.
- Values: `sensor`, `actuator`, `gateway`, `edge`

### protocol (string)
Communication protocol used by the device.
- Values: `mqtt`, `coap`, `http`

## Connection Configuration

### MQTT Connection

```json
{
  "connection": {
    "broker": "mqtt://broker.example.com:1883",
    "clientIdPattern": "device-${deviceId}",
    "topicPattern": "devices/${deviceId}/telemetry",
    "qos": 1,
    "cleanSession": true,
    "keepAlive": 60,
    "username": "device",
    "password": "${MQTT_PASSWORD}"
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| broker | string | required | MQTT broker URL |
| clientIdPattern | string | `device-${deviceId}` | Client ID template |
| topicPattern | string | `devices/${deviceId}/telemetry` | Publish topic template |
| qos | number | 1 | Quality of service (0, 1, 2) |
| cleanSession | boolean | true | Clean session flag |
| keepAlive | number | 60 | Keep-alive interval (seconds) |
| username | string | - | Authentication username |
| password | string | - | Authentication password |

### CoAP Connection

```json
{
  "connection": {
    "server": "coap://server.example.com:5683",
    "resourcePath": "/devices/${deviceId}/telemetry",
    "confirmable": true
  }
}
```

### HTTP Connection

```json
{
  "connection": {
    "baseUrl": "https://api.example.com",
    "path": "/v1/devices/${deviceId}/telemetry",
    "method": "POST",
    "headers": {
      "Authorization": "Bearer ${API_TOKEN}"
    }
  }
}
```

## Telemetry Attributes

Define what data the device sends:

```json
{
  "telemetry": [
    {
      "name": "temperature",
      "type": "number",
      "unit": "celsius",
      "generator": { ... },
      "intervalMs": 5000
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| name | string | Attribute name |
| type | string | Data type: `number`, `integer`, `boolean`, `string`, `object` |
| unit | string | Unit of measurement |
| generator | object | Value generator configuration |
| intervalMs | number | Send interval in milliseconds |

## Generator Types

### Random Generator

Generates random values within a range:

```json
{
  "generator": {
    "type": "random",
    "min": 18.0,
    "max": 28.0,
    "precision": 2,
    "distribution": "uniform"
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| min | number | 0 | Minimum value |
| max | number | 100 | Maximum value |
| precision | number | 2 | Decimal precision |
| distribution | string | `uniform` | `uniform`, `normal`, `exponential` |

### Sequence Generator

Generates sequential values:

```json
{
  "generator": {
    "type": "sequence",
    "start": 0,
    "step": 1,
    "wrap": 1000
  }
}
```

### Constant Generator

Returns a fixed value:

```json
{
  "generator": {
    "type": "constant",
    "value": "active"
  }
}
```

### Replay Generator

Replays historical data from a file:

```json
{
  "generator": {
    "type": "replay",
    "file": "/data/temperature-readings.json",
    "loop": true,
    "speedFactor": 1.0
  }
}
```

### Custom Generator (Python)

```json
{
  "generator": {
    "type": "custom",
    "script": "generators/sine_wave.py",
    "params": {
      "amplitude": 10,
      "period": 60
    }
  }
}
```

## Commands

Define commands the device can receive:

```json
{
  "commands": [
    {
      "name": "setTemperature",
      "topic": "devices/${deviceId}/commands/set-temp",
      "parameters": [
        {
          "name": "targetTemp",
          "type": "number",
          "required": true
        }
      ],
      "response": {
        "topic": "devices/${deviceId}/responses",
        "template": {"status": "ok", "setTo": "${targetTemp}"}
      }
    }
  ]
}
```

## Behaviors

Define state machine behaviors:

```json
{
  "behaviors": [
    {
      "name": "battery-drain",
      "type": "state-machine",
      "initialState": "full",
      "states": {
        "full": {
          "telemetry": {"batteryLevel": 100},
          "transitions": [
            {"to": "draining", "after": "1h"}
          ]
        },
        "draining": {
          "telemetry": {"batteryLevel": {"generator": {"type": "sequence", "start": 100, "step": -1}}},
          "transitions": [
            {"to": "low", "when": "batteryLevel < 20"}
          ]
        },
        "low": {
          "telemetry": {"batteryLevel": {"generator": {"type": "random", "min": 5, "max": 19}}}
        }
      }
    }
  ]
}
```

## Template Variables

Use these variables in connection strings and topics:

| Variable | Description |
|----------|-------------|
| `${deviceId}` | Unique device identifier |
| `${modelId}` | Device model ID |
| `${groupId}` | Device group ID (if grouped) |
| `${timestamp}` | Current ISO timestamp |
| `${ENV_VAR}` | Environment variable value |

## Complete Example

```json
{
  "id": "smart-thermostat",
  "name": "Smart Thermostat",
  "type": "sensor",
  "protocol": "mqtt",
  "connection": {
    "broker": "mqtt://localhost:1883",
    "topicPattern": "home/${groupId}/thermostats/${deviceId}/telemetry",
    "qos": 1
  },
  "telemetry": [
    {
      "name": "temperature",
      "type": "number",
      "unit": "celsius",
      "generator": {"type": "random", "min": 18, "max": 24, "precision": 1},
      "intervalMs": 30000
    },
    {
      "name": "humidity",
      "type": "number",
      "unit": "percent",
      "generator": {"type": "random", "min": 30, "max": 70},
      "intervalMs": 30000
    },
    {
      "name": "hvacMode",
      "type": "string",
      "generator": {"type": "constant", "value": "auto"},
      "intervalMs": 60000
    }
  ],
  "commands": [
    {
      "name": "setMode",
      "topic": "home/${groupId}/thermostats/${deviceId}/commands/mode",
      "parameters": [{"name": "mode", "type": "string", "required": true}]
    }
  ]
}
```
