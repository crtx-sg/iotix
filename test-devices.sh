  #!/bin/bash
  BASE_URL="http://localhost:8080"

  echo "=== Registering device model ==="
  curl -s -X POST $BASE_URL/api/v1/models \
    -H "Content-Type: application/json" \
    -d '{
      "id": "temperature-sensor-v1",
      "name": "Temperature Sensor",
      "type": "sensor",
      "protocol": "mqtt",
      "connection": {"broker": "mqtt-broker", "port": 1883, "topicPattern": "sensors/{deviceId}/temperature"},
      "telemetry": [{"name": "temperature", "type": "number", "unit": "celsius", "intervalMs": 5000, "generator": {"type": "random", "min": 18.0, "max": 28.0}}]
    }' | jq .

  echo -e "\n=== Creating device group (10 devices) ==="
  curl -s -X POST $BASE_URL/api/v1/groups \
    -H "Content-Type: application/json" \
    -d '{"modelId": "temperature-sensor-v1", "count": 10, "groupId": "temp-sensors"}' | jq .

  echo -e "\n=== Starting device group ==="
  curl -s -X POST $BASE_URL/api/v1/groups/temp-sensors/start | jq .

  echo -e "\n=== Engine stats ==="
  curl -s $BASE_URL/api/v1/stats | jq .

  echo -e "\n=== View data at: ==="
  echo "InfluxDB: http://localhost:8086 (admin/adminpassword)"
  echo "Grafana:  http://localhost:3000 (admin/admin)"
