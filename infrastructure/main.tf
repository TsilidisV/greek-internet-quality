# --------------------------------------------------------------------------------
# 1. Enable Required APIs
# --------------------------------------------------------------------------------
resource "google_project_service" "enabled_apis" {
  for_each = toset([
    "run.googleapis.com",
    "compute.googleapis.com",
    #"cloudscheduler.googleapis.com",   For triggering a job from GCP
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}