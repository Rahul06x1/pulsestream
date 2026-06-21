# Pub/Sub: main topic + push subscription to the mapper, with a dead-letter topic and a
# pull subscription drained by the redrive job.

resource "google_pubsub_topic" "events" {
  name = "events"
}

resource "google_pubsub_topic" "dlq" {
  name = "events-dlq"
}

# Push subscription -> mapper Cloud Run service (OIDC-authenticated).
resource "google_pubsub_subscription" "events_push" {
  name  = "events-push-sub"
  topic = google_pubsub_topic.events.id

  ack_deadline_seconds = 30

  push_config {
    push_endpoint = google_cloud_run_v2_service.mapper.uri
    oidc_token {
      service_account_email = google_service_account.pubsub_push.email
    }
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dlq.id
    max_delivery_attempts = var.max_delivery_attempts
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}

# Pull subscription on the DLQ, drained by the redrive job.
resource "google_pubsub_subscription" "dlq_pull" {
  name                       = "events-dlq-sub"
  topic                      = google_pubsub_topic.dlq.id
  ack_deadline_seconds       = 60
  message_retention_duration = "604800s" # 7 days
}

# Pub/Sub's service agent must be allowed to publish to the DLQ and subscribe.
data "google_project" "current" {}

locals {
  pubsub_sa = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_pubsub_topic_iam_member" "dlq_publisher" {
  topic  = google_pubsub_topic.dlq.id
  role   = "roles/pubsub.publisher"
  member = local.pubsub_sa
}

resource "google_pubsub_subscription_iam_member" "events_subscriber" {
  subscription = google_pubsub_subscription.events_push.id
  role         = "roles/pubsub.subscriber"
  member       = local.pubsub_sa
}
