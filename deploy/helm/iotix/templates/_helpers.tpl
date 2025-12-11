{{/*
Expand the name of the chart.
*/}}
{{- define "iotix.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "iotix.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "iotix.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "iotix.labels" -}}
helm.sh/chart: {{ include "iotix.chart" . }}
{{ include "iotix.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "iotix.selectorLabels" -}}
app.kubernetes.io/name: {{ include "iotix.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "iotix.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "iotix.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Device Engine fullname
*/}}
{{- define "iotix.deviceEngine.fullname" -}}
{{- printf "%s-device-engine" (include "iotix.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Test Engine fullname
*/}}
{{- define "iotix.testEngine.fullname" -}}
{{- printf "%s-test-engine" (include "iotix.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
MQTT Broker fullname
*/}}
{{- define "iotix.mqtt.fullname" -}}
{{- printf "%s-mqtt" (include "iotix.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Get MQTT broker host
*/}}
{{- define "iotix.mqtt.host" -}}
{{- if .Values.mqtt.enabled }}
{{- include "iotix.mqtt.fullname" . }}
{{- else }}
{{- .Values.mqtt.externalHost | default "localhost" }}
{{- end }}
{{- end }}

{{/*
Get Kafka bootstrap servers
*/}}
{{- define "iotix.kafka.bootstrapServers" -}}
{{- if .Values.kafka.enabled }}
{{- printf "%s-kafka:9092" .Release.Name }}
{{- else }}
{{- .Values.kafka.externalBootstrapServers | default "localhost:9092" }}
{{- end }}
{{- end }}

{{/*
Get InfluxDB URL
*/}}
{{- define "iotix.influxdb.url" -}}
{{- if .Values.influxdb.enabled }}
{{- printf "http://%s-influxdb:8086" .Release.Name }}
{{- else }}
{{- .Values.influxdb.externalUrl | default "http://localhost:8086" }}
{{- end }}
{{- end }}
