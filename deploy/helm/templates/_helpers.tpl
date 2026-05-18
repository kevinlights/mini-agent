{{/*
Expand the name of the chart.
展开 Chart 的名称。
*/}}
{{- define "mini-agent.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
创建默认的完全限定应用名称。
*/}}
{{- define "mini-agent.fullname" -}}
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
Create backend fully qualified name.
创建后端完全限定名称。
*/}}
{{- define "mini-agent.backend.fullname" -}}
{{ include "mini-agent.fullname" . }}-backend
{{- end }}

{{/*
Create frontend fully qualified name.
创建前端完全限定名称。
*/}}
{{- define "mini-agent.frontend.fullname" -}}
{{ include "mini-agent.fullname" . }}-frontend
{{- end }}

{{/*
Create chart name and version as used by the chart label.
创建 Chart 标签使用的名称和版本。
*/}}
{{- define "mini-agent.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
公共标签
*/}}
{{- define "mini-agent.labels" -}}
helm.sh/chart: {{ include "mini-agent.chart" . }}
{{ include "mini-agent.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
选择器标签
*/}}
{{- define "mini-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "mini-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
