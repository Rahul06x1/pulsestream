# Observability: alert on push-subscription backlog age and on dead-letter buildup.

resource "google_monitoring_alert_policy" "push_backlog" {
  display_name = "PulseStream push subscription backlog"
  combiner     = "OR"

  conditions {
    display_name = "Oldest unacked message age > 5m"
    condition_threshold {
      filter = join(" AND ", [
        "resource.type=\"pubsub_subscription\"",
        "resource.label.subscription_id=\"${google_pubsub_subscription.events_push.name}\"",
        "metric.type=\"pubsub.googleapis.com/subscription/oldest_unacked_message_age\"",
      ])
      comparison      = "COMPARISON_GT"
      threshold_value = 300
      duration        = "300s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MAX"
      }
    }
  }

  notification_channels = var.alert_notification_channel == "" ? [] : [var.alert_notification_channel]
  documentation {
    content = "The mapper is not keeping up or is failing; messages are backing up and will be dead-lettered."
  }
}

resource "google_monitoring_alert_policy" "dlq_growth" {
  display_name = "PulseStream dead-letter queue growth"
  combiner     = "OR"

  conditions {
    display_name = "Undelivered messages in DLQ > 0"
    condition_threshold {
      filter = join(" AND ", [
        "resource.type=\"pubsub_subscription\"",
        "resource.label.subscription_id=\"${google_pubsub_subscription.dlq_pull.name}\"",
        "metric.type=\"pubsub.googleapis.com/subscription/num_undelivered_messages\"",
      ])
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "300s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MAX"
      }
    }
  }

  notification_channels = var.alert_notification_channel == "" ? [] : [var.alert_notification_channel]
  documentation {
    content = "Messages have been dead-lettered. Run the redrive job to drain and quarantine them."
  }
}
