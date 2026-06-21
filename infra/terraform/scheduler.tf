# Cloud Scheduler periodically runs the redrive job to drain any dead-lettered messages.

resource "google_service_account" "scheduler" {
  account_id   = "pulsestream-scheduler"
  display_name = "PulseStream scheduler"
}

resource "google_cloud_run_v2_job_iam_member" "scheduler_run_redrive" {
  name     = google_cloud_run_v2_job.redrive.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_cloud_scheduler_job" "redrive" {
  name      = "pulsestream-redrive-hourly"
  region    = var.region
  schedule  = "0 * * * *"
  time_zone = "Etc/UTC"

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.redrive.name}:run"
    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }

  retry_config {
    retry_count = 3
  }
}
