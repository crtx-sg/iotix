# Deployment Guide

This guide covers deploying IoTix in various environments, from local development to production Kubernetes clusters.

## Local Development

### Docker Compose

The simplest way to run IoTix locally:

```bash
cd deploy/docker
docker-compose up -d
```

Services:
| Service | Port | URL |
|---------|------|-----|
| Device Engine | 8080 | http://localhost:8080 |
| Test Engine | 8081 | http://localhost:8081 |
| Management API | 8082 | http://localhost:8082 |
| MQTT Broker | 1883 | mqtt://localhost:1883 |
| Kafka | 9092 | localhost:9092 |
| InfluxDB | 8086 | http://localhost:8086 |
| Grafana | 3000 | http://localhost:3000 |

### Configuration

Create a `.env` file in `deploy/docker/`:

```env
# Device Engine
MQTT_BROKER_HOST=mqtt-broker
MQTT_BROKER_PORT=1883
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=iotix-dev-token

# Test Engine
DEVICE_ENGINE_URL=http://device-engine:8080

# Management API
JWT_SECRET=change-me-in-production

# Grafana
GF_SECURITY_ADMIN_PASSWORD=admin

# InfluxDB
DOCKER_INFLUXDB_INIT_PASSWORD=adminpassword
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.24+)
- Helm 3.x
- kubectl configured

### Using Helm

```bash
# Add the IoTix Helm repository
helm repo add iotix https://iotix.github.io/charts
helm repo update

# Install with default values
helm install iotix iotix/iotix \
  --namespace iotix \
  --create-namespace

# Or with custom values
helm install iotix iotix/iotix \
  --namespace iotix \
  --create-namespace \
  -f custom-values.yaml
```

### Custom Values

Create `custom-values.yaml`:

```yaml
# Global settings
global:
  imageRegistry: ""
  imagePullSecrets: []

# Device Engine
deviceEngine:
  replicas: 3
  resources:
    requests:
      memory: "256Mi"
      cpu: "100m"
    limits:
      memory: "1Gi"
      cpu: "1000m"
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilization: 70

# Test Engine
testEngine:
  replicas: 2
  resources:
    requests:
      memory: "256Mi"
      cpu: "100m"

# Management API
managementApi:
  replicas: 2
  jwt:
    secret: "your-production-secret"
    expiryHours: 24

# MQTT Broker
mqtt:
  broker: emqx  # or vernemq
  replicas: 3
  persistence:
    enabled: true
    size: 10Gi

# Kafka
kafka:
  enabled: true
  replicas: 3
  persistence:
    enabled: true
    size: 50Gi

# InfluxDB
influxdb:
  enabled: true
  persistence:
    enabled: true
    size: 100Gi

# Grafana
grafana:
  enabled: true
  adminPassword: "secure-password"
  persistence:
    enabled: true
    size: 5Gi

# Ingress
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: iotix.example.com
      paths:
        - path: /api/v1/devices
          service: device-engine
        - path: /api/v1/tests
          service: test-engine
        - path: /api/v1/admin
          service: management-api
  tls:
    - secretName: iotix-tls
      hosts:
        - iotix.example.com
```

### Manual Kubernetes Deployment

If not using Helm, apply manifests directly:

```bash
# Create namespace
kubectl create namespace iotix

# Apply configurations
kubectl apply -f deploy/k8s/configmap.yaml -n iotix
kubectl apply -f deploy/k8s/secrets.yaml -n iotix

# Deploy services
kubectl apply -f deploy/k8s/device-engine/ -n iotix
kubectl apply -f deploy/k8s/test-engine/ -n iotix
kubectl apply -f deploy/k8s/management-api/ -n iotix

# Deploy dependencies
kubectl apply -f deploy/k8s/mqtt/ -n iotix
kubectl apply -f deploy/k8s/kafka/ -n iotix
kubectl apply -f deploy/k8s/influxdb/ -n iotix
kubectl apply -f deploy/k8s/grafana/ -n iotix
```

## Production Considerations

### High Availability

1. **Device Engine**: Run 3+ replicas with HPA
2. **MQTT Broker**: Use clustered EMQX or VerneMQ
3. **Kafka**: 3+ broker replicas with replication factor 3
4. **InfluxDB**: Consider InfluxDB Enterprise for HA

### Resource Planning

For 100K concurrent devices:

| Component | Replicas | CPU | Memory |
|-----------|----------|-----|--------|
| Device Engine | 5-10 | 2 cores | 4Gi |
| MQTT Broker | 3 | 4 cores | 8Gi |
| Kafka | 3 | 2 cores | 8Gi |
| InfluxDB | 1 | 4 cores | 16Gi |

### Security

1. **TLS Everywhere**
   ```yaml
   mqtt:
     tls:
       enabled: true
       secretName: mqtt-tls
   ```

2. **Network Policies**
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: device-engine-network
   spec:
     podSelector:
       matchLabels:
         app: device-engine
     ingress:
       - from:
           - podSelector:
               matchLabels:
                 app: mqtt-broker
         ports:
           - port: 1883
   ```

3. **Secrets Management**
   - Use Kubernetes secrets or external vaults
   - Rotate JWT secrets regularly
   - Use managed identities where possible

### Monitoring

1. **Prometheus + Grafana**
   ```yaml
   monitoring:
     prometheus:
       enabled: true
       serviceMonitor:
         enabled: true
   ```

2. **Log Aggregation**
   - Deploy Fluentd/Fluent Bit for log collection
   - Send to Elasticsearch, Loki, or cloud logging

3. **Alerting**
   - Configure Grafana alerting
   - Set up PagerDuty/Slack integrations

### Backup & Recovery

1. **InfluxDB Backup**
   ```bash
   influx backup /backup/$(date +%Y%m%d) \
     --host http://influxdb:8086 \
     --token $INFLUXDB_TOKEN
   ```

2. **Configuration Backup**
   - Store device models in Git
   - Export Grafana dashboards
   - Backup Kubernetes secrets

## Network Simulation

### Chaos Mesh Setup

```bash
# Install Chaos Mesh
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm install chaos-mesh chaos-mesh/chaos-mesh \
  --namespace chaos-testing \
  --create-namespace

# Apply network chaos
kubectl apply -f deploy/chaos-mesh/templates/poor-cellular.yaml
```

### Available Templates

- `poor-cellular.yaml`: 200ms latency, 5% packet loss
- `intermittent-connectivity.yaml`: Periodic disconnections
- `satellite-link.yaml`: 600ms latency simulation

## Scaling Guidelines

### Horizontal Scaling

Device Engine scales based on:
- Number of active devices
- Telemetry message rate
- CPU utilization

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: device-engine-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: device-engine
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: active_devices
        target:
          type: AverageValue
          averageValue: 5000
```

### Vertical Scaling

For single-instance components (InfluxDB):
- Monitor resource usage
- Increase limits gradually
- Consider managed services for production

## Troubleshooting Deployment

### Common Issues

1. **Pods not starting**
   ```bash
   kubectl describe pod <pod-name> -n iotix
   kubectl logs <pod-name> -n iotix
   ```

2. **Service connectivity**
   ```bash
   kubectl exec -it <pod> -n iotix -- curl device-engine:8080/health
   ```

3. **MQTT connection issues**
   ```bash
   kubectl logs -l app=mqtt-broker -n iotix
   mosquitto_sub -h mqtt-broker.iotix.svc -t '#' -v
   ```

4. **Resource constraints**
   ```bash
   kubectl top pods -n iotix
   kubectl describe node
   ```
