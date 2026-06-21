output "adapter_url" {
  value       = google_cloud_run_v2_service.adapter.uri
  description = "Adapter service URL (exposes /healthz)."
}

output "mapper_url" {
  value       = google_cloud_run_v2_service.mapper.uri
  description = "Mapper service URL (Pub/Sub push target)."
}

output "events_topic" {
  value       = google_pubsub_topic.events.name
  description = "Main events topic."
}

output "dlq_subscription" {
  value       = google_pubsub_subscription.dlq_pull.name
  description = "Dead-letter subscription drained by redrive."
}
