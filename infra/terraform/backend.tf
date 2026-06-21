# Remote state in GCS; bucket + prefix injected at init:
#   terraform init -backend-config="bucket=pulsestream-dev-tfstate" \
#                  -backend-config="prefix=terraform/state"
terraform {
  backend "gcs" {}
}
