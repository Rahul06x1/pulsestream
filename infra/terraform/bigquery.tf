# BigQuery sink: raw stream table, per-minute materialized view, quarantine table.

resource "google_bigquery_dataset" "events" {
  dataset_id  = "events"
  location    = var.bq_location
  description = "PulseStream event stream and derived metrics."
}

resource "google_bigquery_table" "raw_stream" {
  dataset_id          = google_bigquery_dataset.events.dataset_id
  table_id            = "raw_stream"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "ingest_ts"
  }
  clustering = ["event_type", "wiki"]

  schema = jsonencode([
    { name = "ingest_ts", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "event_id", type = "STRING", mode = "REQUIRED" },
    { name = "event_type", type = "STRING", mode = "REQUIRED" },
    { name = "wiki", type = "STRING", mode = "REQUIRED" },
    { name = "title", type = "STRING", mode = "NULLABLE" },
    { name = "user", type = "STRING", mode = "NULLABLE" },
    { name = "occurred_at", type = "TIMESTAMP", mode = "NULLABLE" },
    { name = "bot", type = "BOOL", mode = "NULLABLE" },
    { name = "payload", type = "JSON", mode = "NULLABLE" },
  ])
}

resource "google_bigquery_table" "dead_letters" {
  dataset_id          = google_bigquery_dataset.events.dataset_id
  table_id            = "dead_letters"
  deletion_protection = false

  schema = jsonencode([
    { name = "received_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "reason", type = "STRING", mode = "NULLABLE" },
    { name = "raw", type = "STRING", mode = "NULLABLE" },
  ])
}

resource "google_bigquery_table" "per_minute_metrics" {
  dataset_id          = google_bigquery_dataset.events.dataset_id
  table_id            = "per_minute_metrics"
  deletion_protection = false

  materialized_view {
    query = <<-SQL
      SELECT
        TIMESTAMP_TRUNC(ingest_ts, MINUTE) AS minute,
        event_type,
        COUNT(*) AS event_count
      FROM `${var.project_id}.${google_bigquery_dataset.events.dataset_id}.raw_stream`
      GROUP BY minute, event_type
    SQL
  }

  depends_on = [google_bigquery_table.raw_stream]
}
