# --------------------------------------------------------------------------------
# 5. Cloud Run Job (The Transformer Runner)
# --------------------------------------------------------------------------------
resource "google_cloud_run_v2_job" "pyspark_job" {
  name                = var.job_name
  location            = var.region
  deletion_protection = false

  template {
    template {
      service_account = google_service_account.transformer_sa.email

      containers {
        image = "docker.io/${var.docker_image}"

        # Optimization for Free Tier:
        # Keep resources just high enough for Spark/Pandas but low enough to save credits.
        resources {
          limits = {
            cpu    = "2"
            memory = "5Gi"
          }
        }

        # Pass environment variables if your code needs them
        env {
          name  = "GCS_BUCKET_NAME"
          value = google_storage_bucket.data_lake.name
        }
        env {
          name  = "BQ_DATASET"
          value = google_bigquery_dataset.warehouse.dataset_id
        }
      }
    }
  }

  depends_on = [
    google_project_service.enabled_apis,
    time_sleep.wait_for_sa
  ]
}

# --------------------------------------------------------------------------------
# 6. Cloud Scheduler (The Trigger)
# --------------------------------------------------------------------------------
# Create a Service Account specifically for the Scheduler to invoke Cloud Run
#resource "google_service_account" "scheduler_sa" {
#  account_id   = "scheduler-invoker"
#  display_name = "Cloud Scheduler Invoker SA"
#  depends_on   = [google_project_service.enabled_apis]
#}
#
## Allow the Scheduler SA to invoke the Cloud Run Job
#resource "google_cloud_run_v2_job_iam_member" "scheduler_invoke_permissions" {
#  name     = google_cloud_run_v2_job.pyspark_job.name
#  location = google_cloud_run_v2_job.pyspark_job.location
#  role     = "roles/run.invoker"
#  member   = "serviceAccount:${google_service_account.scheduler_sa.email}"
#}
#
#resource "google_cloud_scheduler_job" "daily_trigger" {
#  name             = "trigger-transform-daily"
#  description      = "Triggers the Transformer Cloud Run Job once daily"
#  schedule         = "0 8 * * *" # Runs at 8:00 AM UTC daily
#  time_zone        = "Etc/UTC"
#  attempt_deadline = "320s"
#  region           = var.region
#
#  http_target {
#    http_method = "POST"
#    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${var.job_name}:run"
#
#    oauth_token {
#      service_account_email = google_service_account.scheduler_sa.email
#    }
#  }
#
#  depends_on = [google_cloud_run_v2_job.pyspark_job]
#}