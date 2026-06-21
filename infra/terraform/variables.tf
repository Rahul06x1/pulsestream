variable "project_id" {
  type        = string
  description = "GCP project id."
}

variable "region" {
  type        = string
  default     = "europe-west2"
  description = "GCP region."
}

variable "bq_location" {
  type        = string
  default     = "EU"
  description = "BigQuery dataset location."
}

variable "image_tag" {
  type        = string
  description = "Container tag for all service images (commit SHA)."
}

variable "ar_repo_url" {
  type        = string
  description = "Artifact Registry repo URL, e.g. europe-west2-docker.pkg.dev/PROJECT/pulsestream"
}

variable "max_delivery_attempts" {
  type        = number
  default     = 5
  description = "Pub/Sub deliveries before a message is dead-lettered."
}

variable "alert_notification_channel" {
  type        = string
  default     = ""
  description = "Optional Monitoring notification channel id."
}
