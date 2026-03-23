# --------------------------------------------------------------------------------
# 7. GitHub Integration
# --------------------------------------------------------------------------------

# Fetch the existing repository
data "github_repository" "repo" {
  full_name = var.github_repo_full_name
}

# --------------------------------------------------------------------------------
# Action Secrets
# --------------------------------------------------------------------------------

resource "github_actions_secret" "gcp_project_id" {
  repository      = data.github_repository.repo.name
  secret_name     = "GCP_PROJECT_ID"
  plaintext_value = var.project_id
}

resource "github_actions_secret" "gcp_region" {
  repository      = data.github_repository.repo.name
  secret_name     = "GCP_REGION"
  plaintext_value = var.region
}

resource "github_actions_secret" "gcs_bucket_name" {
  repository      = data.github_repository.repo.name
  secret_name     = "GCS_BUCKET_NAME"
  plaintext_value = google_storage_bucket.data_lake.name # References the bucket created in storage.tf
}

resource "github_actions_secret" "job_name" {
  repository      = data.github_repository.repo.name
  secret_name     = "JOB_NAME"
  plaintext_value = var.job_name
}

resource "github_actions_secret" "gcp_workload_identity_provider" {
  repository      = data.github_repository.repo.name
  secret_name     = "GCP_WORKLOAD_IDENTITY_PROVIDER"
  plaintext_value = google_iam_workload_identity_pool_provider.github_provider.name
}

resource "github_actions_secret" "gcp_service_account" {
  repository      = data.github_repository.repo.name
  secret_name     = "GCP_SERVICE_ACCOUNT"
  plaintext_value = google_service_account.ingestor_sa.email
}
