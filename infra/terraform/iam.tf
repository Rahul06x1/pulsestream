# Service accounts: one per workload, least-privilege.

resource "google_service_account" "adapter" {
  account_id   = "pulsestream-adapter"
  display_name = "PulseStream adapter (SSE -> Pub/Sub)"
}

resource "google_service_account" "mapper" {
  account_id   = "pulsestream-mapper"
  display_name = "PulseStream mapper (Pub/Sub -> BigQuery)"
}

resource "google_service_account" "redrive" {
  account_id   = "pulsestream-redrive"
  display_name = "PulseStream redrive (DLQ drainer)"
}

# Identity Pub/Sub uses to push to the mapper.
resource "google_service_account" "pubsub_push" {
  account_id   = "pulsestream-pubsub-push"
  display_name = "PulseStream Pub/Sub push identity"
}

# Adapter publishes to the events topic.
resource "google_pubsub_topic_iam_member" "adapter_publisher" {
  topic  = google_pubsub_topic.events.id
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.adapter.email}"
}

# Mapper writes to BigQuery.
resource "google_project_iam_member" "mapper_bq" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.mapper.email}"
}

resource "google_project_iam_member" "mapper_bq_jobs" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.mapper.email}"
}

# Redrive consumes the DLQ and writes to BigQuery.
resource "google_pubsub_subscription_iam_member" "redrive_subscriber" {
  subscription = google_pubsub_subscription.dlq_pull.id
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${google_service_account.redrive.email}"
}

resource "google_project_iam_member" "redrive_bq" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.redrive.email}"
}

resource "google_project_iam_member" "redrive_bq_jobs" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.redrive.email}"
}

# Pub/Sub push identity may invoke the mapper service.
resource "google_cloud_run_v2_service_iam_member" "push_invoke_mapper" {
  name     = google_cloud_run_v2_service.mapper.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.pubsub_push.email}"
}
