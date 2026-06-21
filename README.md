<div align="center">

# PulseStream

### Real-time event ingestion on Google Cloud — Pub/Sub, dead-letters & redrive

[![CI](https://github.com/Rahul06x1/pulsestream/actions/workflows/ci.yaml/badge.svg)](https://github.com/Rahul06x1/pulsestream/actions/workflows/ci.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

PulseStream ingests a high-volume **public real-time stream** — Wikimedia
[EventStreams](https://stream.wikimedia.org/?doc) recent changes (no auth) — into BigQuery
with decoupled producer/consumer, schema validation, at-least-once delivery, dead-letter
handling, and near-real-time metrics. A self-contained portfolio project demonstrating
resilient **streaming/event-driven** data engineering.

> Standalone learning project. The only data source is a public, keyless event stream.

---

## Architecture

```
Wikimedia EventStreams (SSE)
        │
        ▼
  ADAPTER  (Cloud Run service, min-instances=1)
   • consumes SSE, normalizes, validates contract
   • publishes → Pub/Sub topic `events`  (attr: event_type)
        │
        ▼
  Pub/Sub `events` ──push(OIDC)──► MAPPER (Cloud Run service)
        │                            • decode + JSON-Schema validate
        │                            • streaming insert → BigQuery
        │ (after N failed deliveries)
        ▼
  Dead-letter topic `events-dlq`
        │  pull
        ▼
  events-dlq-sub ──► REDRIVE (Cloud Run job, scheduled hourly)
                       • retry insert, else quarantine
                       ▼
BigQuery `events`:  raw_stream ──► per_minute_metrics (materialized view)
                    dead_letters (quarantine)
Observability: alerts on push-backlog age + DLQ depth
```

**Three units, one contract** (`schemas/event.schema.json`):
- **adapter** — long-lived SSE consumer → Pub/Sub producer.
- **mapper** — Pub/Sub *push* subscriber → BigQuery sink. HTTP status drives delivery
  (`204` ack, `400` invalid → dead-letter, `500` transient → retry).
- **redrive** — drains the dead-letter subscription; re-inserts or quarantines, then acks.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Messaging | Pub/Sub (topic, push subscription, dead-letter topic, DLQ) |
| Compute | Cloud Run services (adapter, mapper) + Cloud Run job (redrive) |
| Warehouse | BigQuery (partitioned/clustered table + materialized view) |
| Validation | JSON Schema (shared contract + drift test) |
| Orchestration | Cloud Scheduler (redrive) |
| IaC | Terraform (GCS remote state) |
| CI/CD | GitHub Actions (matrix build) + Workload Identity Federation |
| Tooling | ruff, pytest |

---

## Repository layout

```
pulsestream/
├── adapter/   # Cloud Run service: SSE -> Pub/Sub  (normalize, publish)
├── mapper/    # Cloud Run service: Pub/Sub push -> BigQuery  (validate, insert)
├── redrive/   # Cloud Run job: drain DLQ -> reinsert/quarantine
├── schemas/   # event.schema.json — the shared event contract
├── infra/terraform/  # Pub/Sub, BigQuery, Cloud Run, IAM, monitoring, scheduler
└── .github/   # CI (matrix lint/test + tf validate), deploy (WIF), dependabot
```

---

## Run the tests locally

```bash
for svc in adapter mapper redrive; do
  (cd $svc && pip install -e . pytest ruff && ruff check . && pytest -q)
done
```

The adapter can also be run against the live stream locally (publishes to a real topic):

```bash
cd adapter && pip install -e .
export GCP_PROJECT=your-gcp-project PUBSUB_TOPIC=events
python main.py   # opens SSE, publishes events; GET :8080 for /healthz + counts
```

---

## Deploy

1. Create a GCP project; enable Pub/Sub, Cloud Run, BigQuery, Cloud Scheduler, Artifact
   Registry. Create an Artifact Registry repo `pulsestream`, a Terraform-state bucket, and
   a Workload Identity Federation pool bound to this repo.
2. Set repo Actions **variables**: `GCP_PROJECT_ID`, `WIF_PROVIDER`, `DEPLOYER_SA`,
   `TFSTATE_BUCKET`.
3. Push to `main` — `deploy.yaml` builds all three images (matrix) and runs
   `terraform plan`/`apply`.

---

## Design notes

- **Decoupling** — the adapter never blocks on BigQuery; Pub/Sub absorbs spikes and
  guarantees at-least-once delivery to the mapper.
- **Poison-message safety** — invalid events are dead-lettered after `max_delivery_attempts`
  and ultimately quarantined to `dead_letters`, so nothing is silently dropped or retried
  forever.
- **Contract enforcement** — one JSON Schema is shared by adapter and mapper; a contract
  test fails CI if the bundled copy drifts from `schemas/`.
- **Idempotent redrive** — the job is safe to run repeatedly; it acks only what it has
  handled.
- **Observable** — alerts on subscription backlog age and DLQ depth ship with the infra.
- **Cost-aware** — mapper scales to zero; `raw_stream` is partitioned by day and clustered
  by `event_type`/`wiki`; pause the scheduler and `terraform destroy` when idle.

---

## Skills demonstrated

Event-driven architecture · Pub/Sub (push subscriptions, dead-letter queues, retry
policy) · Cloud Run services + jobs · BigQuery streaming inserts + materialized views ·
schema/contract validation · idempotency & at-least-once semantics · dead-letter
quarantine & redrive · Terraform with remote state · matrix CI/CD with Workload Identity
Federation · observability (backlog/DLQ alerting).

---

## Teardown

```bash
cd infra/terraform && terraform destroy
```
