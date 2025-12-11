# API Documentation

IoTix provides REST APIs for managing device simulations, running tests, and administering the platform.

## Base URLs

| Service | Default URL | Description |
|---------|-------------|-------------|
| Device Engine | http://localhost:8080 | Device management and simulation |
| Test Engine | http://localhost:8081 | Test execution and scheduling |
| Management API | http://localhost:8082 | User and tenant management |

## Authentication

### Management API

The Management API requires authentication via Bearer token or API key.

**Login:**
```bash
curl -X POST http://localhost:8082/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@iotix.local", "password": "admin"}'
```

**Using Bearer Token:**
```bash
curl http://localhost:8082/api/v1/users \
  -H "Authorization: Bearer <token>"
```

**Using API Key:**
```bash
curl http://localhost:8082/api/v1/users \
  -H "X-API-Key: iotix_<key>"
```

## Device Engine API

### Models

#### List Models
```
GET /api/v1/models
```

#### Register Model
```
POST /api/v1/models
Content-Type: application/json

{
  "id": "temperature-sensor",
  "name": "Temperature Sensor",
  "type": "sensor",
  "protocol": "mqtt",
  ...
}
```

#### Get Model
```
GET /api/v1/models/{modelId}
```

#### Delete Model
```
DELETE /api/v1/models/{modelId}
```

### Devices

#### List Devices
```
GET /api/v1/devices?modelId=<id>&status=<status>&limit=50&offset=0
```

#### Create Device
```
POST /api/v1/devices
Content-Type: application/json

{
  "modelId": "temperature-sensor",
  "deviceId": "sensor-001",  // optional
  "groupId": "group-001"     // optional
}
```

**Response:**
```json
{
  "id": "device-abc123",
  "modelId": "temperature-sensor",
  "status": "created",
  "connectionState": "disconnected",
  "createdAt": "2024-01-15T10:30:00Z"
}
```

#### Get Device
```
GET /api/v1/devices/{deviceId}
```

#### Start Device
```
POST /api/v1/devices/{deviceId}/start
```

**Response:**
```json
{
  "id": "device-abc123",
  "status": "running",
  "connectionState": "connected"
}
```

#### Stop Device
```
POST /api/v1/devices/{deviceId}/stop
```

#### Delete Device
```
DELETE /api/v1/devices/{deviceId}
```

#### Get Device Metrics
```
GET /api/v1/devices/{deviceId}/metrics
```

**Response:**
```json
{
  "deviceId": "device-abc123",
  "messagesSent": 1500,
  "bytesSent": 45000,
  "lastTelemetry": {
    "temperature": 22.5,
    "timestamp": "2024-01-15T10:35:00Z"
  },
  "connectionDuration": 3600
}
```

### Device Groups

#### Create Group
```
POST /api/v1/groups
Content-Type: application/json

{
  "modelId": "temperature-sensor",
  "count": 100,
  "groupId": "building-a",  // optional
  "idPattern": "sensor-{index}"  // optional
}
```

**Response:**
```json
{
  "groupId": "group-xyz789",
  "modelId": "temperature-sensor",
  "deviceCount": 100,
  "status": "created"
}
```

#### Start Group
```
POST /api/v1/groups/{groupId}/start?staggerMs=100
```

Query Parameters:
- `staggerMs`: Delay between starting each device (default: 0)

#### Stop Group
```
POST /api/v1/groups/{groupId}/stop
```

#### Delete Group
```
DELETE /api/v1/groups/{groupId}
```

### Statistics

#### Get Engine Stats
```
GET /api/v1/stats
```

**Response:**
```json
{
  "activeDevices": 500,
  "totalDevices": 1000,
  "activeGroups": 5,
  "registeredModels": 10,
  "totalMessagesSent": 1500000,
  "totalBytesSent": 45000000,
  "uptimeSeconds": 86400
}
```

## Test Engine API

### Test Suites

#### List Suites
```
GET /api/v1/suites
```

#### Create Suite
```
POST /api/v1/suites
Content-Type: application/json

{
  "name": "Device Lifecycle Tests",
  "description": "Basic device creation and operation tests",
  "testCases": ["test_create_device", "test_start_device"],
  "tags": ["smoke", "device"],
  "timeoutSeconds": 3600
}
```

#### Get Suite
```
GET /api/v1/suites/{suiteId}
```

#### Delete Suite
```
DELETE /api/v1/suites/{suiteId}
```

### Test Runs

#### List Runs
```
GET /api/v1/runs?status=<status>&limit=50
```

#### Create Run
```
POST /api/v1/runs
Content-Type: application/json

{
  "suiteId": "suite-abc123",        // or testCases
  "testCases": ["test_1", "test_2"], // optional
  "deviceGroupId": "group-xyz",      // optional
  "variables": {"timeout": 30},      // optional
  "tags": ["regression"]             // optional
}
```

#### Get Run
```
GET /api/v1/runs/{runId}
```

**Response:**
```json
{
  "runId": "run-xyz789",
  "status": "passed",
  "startedAt": "2024-01-15T10:00:00Z",
  "finishedAt": "2024-01-15T10:05:00Z",
  "durationSeconds": 300,
  "totalTests": 10,
  "passed": 9,
  "failed": 1,
  "errors": 0,
  "skipped": 0,
  "results": [...]
}
```

#### Cancel Run
```
POST /api/v1/runs/{runId}/cancel
```

#### Get Report
```
GET /api/v1/runs/{runId}/report?format=json|html|junit|csv|markdown
```

### Schedules

#### List Schedules
```
GET /api/v1/schedules
```

#### Create Schedule
```
POST /api/v1/schedules
Content-Type: application/json

{
  "cron": "0 */6 * * *",
  "suiteId": "suite-abc123",
  "enabled": true,
  "notificationUrl": "https://hooks.slack.com/..."
}
```

#### Delete Schedule
```
DELETE /api/v1/schedules/{scheduleId}
```

### Webhook

Trigger test execution from CI/CD:

```
POST /api/v1/webhook
Content-Type: application/json

{
  "suiteId": "suite-abc123",
  "variables": {"branch": "main"}
}
```

## Management API

### Users

#### List Users
```
GET /api/v1/users?role=<role>&status=<status>&tenantId=<id>
```

#### Create User
```
POST /api/v1/users
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "Test User",
  "password": "secure-password",
  "role": "operator",
  "tenantId": "tenant-123"
}
```

#### Get User
```
GET /api/v1/users/{userId}
```

#### Update User
```
PATCH /api/v1/users/{userId}
Content-Type: application/json

{
  "name": "Updated Name",
  "role": "admin"
}
```

#### Delete User
```
DELETE /api/v1/users/{userId}
```

### Tenants

#### List Tenants
```
GET /api/v1/tenants
```

#### Create Tenant
```
POST /api/v1/tenants
Content-Type: application/json

{
  "name": "Acme Corp",
  "description": "Main tenant",
  "quota": {
    "maxDevices": 10000,
    "maxGroups": 500,
    "maxModels": 100
  }
}
```

#### Get Tenant
```
GET /api/v1/tenants/{tenantId}
```

#### Get Tenant Quota
```
GET /api/v1/tenants/{tenantId}/quota
```

#### Update Tenant
```
PATCH /api/v1/tenants/{tenantId}
```

#### Delete Tenant
```
DELETE /api/v1/tenants/{tenantId}
```

### API Keys

#### List API Keys
```
GET /api/v1/api-keys
```

#### Create API Key
```
POST /api/v1/api-keys
Content-Type: application/json

{
  "name": "CI/CD Integration",
  "permissions": ["devices:read", "devices:write"],
  "expiresInDays": 90
}
```

**Response:**
```json
{
  "key": "iotix_abc123...",  // only shown once
  "apiKey": {
    "id": "apikey-xyz",
    "name": "CI/CD Integration",
    "keyPrefix": "iotix_abc123",
    "createdAt": "2024-01-15T10:00:00Z"
  }
}
```

#### Delete API Key
```
DELETE /api/v1/api-keys/{keyId}
```

### Audit Logs

#### Query Audit Logs
```
GET /api/v1/audit-logs?userId=<id>&action=<action>&resource=<resource>&limit=100
```

#### Export Audit Logs
```
GET /api/v1/audit-logs/export?format=json|csv
```

## Error Responses

All APIs return errors in a consistent format:

```json
{
  "detail": "Error message here"
}
```

HTTP Status Codes:
- 400: Bad Request (invalid input)
- 401: Unauthorized (missing/invalid auth)
- 403: Forbidden (insufficient permissions)
- 404: Not Found
- 409: Conflict (duplicate resource)
- 500: Internal Server Error

## Rate Limiting

Production deployments should implement rate limiting. Default limits:
- 1000 requests/minute per IP
- 100 requests/minute per user for write operations

## OpenAPI Specifications

Interactive API documentation is available at:
- Device Engine: http://localhost:8080/docs
- Test Engine: http://localhost:8081/docs
- Management API: http://localhost:8082/docs
