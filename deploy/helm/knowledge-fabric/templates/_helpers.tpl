{{/*
Expand the name of the chart.
*/}}
{{- define "knowledge-fabric.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "knowledge-fabric.fullname" -}}
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
{{- define "knowledge-fabric.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "knowledge-fabric.labels" -}}
helm.sh/chart: {{ include "knowledge-fabric.chart" . }}
{{ include "knowledge-fabric.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "knowledge-fabric.selectorLabels" -}}
app.kubernetes.io/name: {{ include "knowledge-fabric.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "knowledge-fabric.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "knowledge-fabric.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Determine Postgres Host
*/}}
{{- define "knowledge-fabric.postgresHost" -}}
{{- if .Values.postgresql.external.enabled }}
{{- .Values.postgresql.external.host }}
{{- else }}
{{- printf "%s-postgresql" (include "knowledge-fabric.fullname" .) }}
{{- end }}
{{- end }}

{{/*
Determine Postgres Port
*/}}
{{- define "knowledge-fabric.postgresPort" -}}
{{- if .Values.postgresql.external.enabled }}
{{- .Values.postgresql.external.port | toString }}
{{- else }}
{{- "5432" }}
{{- end }}
{{- end }}

{{/*
Determine Postgres Database
*/}}
{{- define "knowledge-fabric.postgresDatabase" -}}
{{- if .Values.postgresql.external.enabled }}
{{- .Values.postgresql.external.database }}
{{- else }}
{{- .Values.postgresql.auth.database }}
{{- end }}
{{- end }}

{{/*
Determine Postgres Username
*/}}
{{- define "knowledge-fabric.postgresUser" -}}
{{- if .Values.postgresql.external.enabled }}
{{- .Values.postgresql.external.username }}
{{- else }}
{{- .Values.postgresql.auth.username }}
{{- end }}
{{- end }}
