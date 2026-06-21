# Cloud Run: adapter service (always-on consumer), mapper service (push target),
# redrive job (on-demand DLQ drainer).

resource "google_cloud_run_v2_service" "adapter" {
  name     = "pulsestream-adapter"
  location = var.region

  template {
    service_account = google_service_account.adapter.email
    # Keep one instance warm so the SSE consumer runs continuously.
    scaling {
      min_instance_count = 1
      max_instance_count = 1
    }
    containers {
      image = "${var.ar_repo_url}/adapter:${var.image_tag}"
      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }
      env {
        name  = "PUBSUB_TOPIC"
        value = google_pubsub_topic.events.name
      }
      resources {
        limits = { cpu = "1", memory = "512Mi" }
      }
    }
  }
}

resource "google_cloud_run_v2_service" "mapper" {
  name     = "pulsestream-mapper"
  location = var.region

  template {
    service_account = google_service_account.mapper.email
    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
    containers {
      image = "${var.ar_repo_url}/mapper:${var.image_tag}"
      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }
      env {
        name  = "BQ_DATASET"
        value = google_bigquery_dataset.events.dataset_id
      }
      resources {
        limits = { cpu = "1", memory = "512Mi" }
      }
    }
  }
}

resource "google_cloud_run_v2_job" "redrive" {
  name     = "pulsestream-redrive"
  location = var.region

  template {
    template {
      service_account = google_service_account.redrive.email
      max_retries     = 1
      containers {
        image = "${var.ar_repo_url}/redrive:${var.image_tag}"
        env {
          name  = "GCP_PROJECT"
          value = var.project_id
        }
        env {
          name  = "DLQ_SUBSCRIPTION"
          value = google_pubsub_subscription.dlq_pull.name
        }
        env {
          name  = "BQ_DATASET"
          value = google_bigquery_dataset.events.dataset_id
        }
        resources {
          limits = { cpu = "1", memory = "512Mi" }
        }
      }
    }
  }
}
