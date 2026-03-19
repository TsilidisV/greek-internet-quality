# --------------------------------------------------------------------------------
# 2. Service Accounts & Security
# --------------------------------------------------------------------------------
resource "time_sleep" "wait_for_sa" {
  depends_on      = [google_service_account.transformer_sa]
  create_duration = "30s"
}

### Transformation ###
# Create a dedicated Service Account for the Transformer Job
resource "google_service_account" "transformer_sa" {
  account_id   = "transformer-sa"
  display_name = "Transformer Job Service Account"
  depends_on   = [google_project_service.enabled_apis]
  description  = "Used locally and by Github Actions to transform and load data to BigQuery"
}

### Ingestor ###
# Create the Service Account for the Ingestor
resource "google_service_account" "ingestor_sa" {
  account_id   = "ingestor-sa"
  display_name = "Ingestor Service Account (GitHub Actions)"
  description  = "Used locally and by Github Actions to ingest data to GCS"
}

### DASHBOARD ###
# This account is used by the Streamlit dashboard to authenticate with BigQuery.
resource "google_service_account" "dashboard_sa" {
  account_id   = "streamlit-dashboard-sa"
  display_name = "Streamlit Dashboard Service Account"
  description  = "Used locally and by Streamlit to read data from BigQuery"
}

# Grant permission to run BigQuery jobs (required to run queries)
resource "google_project_iam_member" "dashboard_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.dashboard_sa.email}"
}

# Grant permission to read data from BigQuery datasets
resource "google_project_iam_member" "dashboard_bq_data_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.dashboard_sa.email}"
}

# Grant the Dashboard Service Account permission to use the BigQuery Storage Read API 
# (required for efficient data fetching in pandas/Streamlit)
resource "google_project_iam_member" "dashboard_bq_read_session_user" {
  project = var.project_id
  role    = "roles/bigquery.readSessionUser"
  member  = "serviceAccount:${google_service_account.dashboard_sa.email}"
}

# Allow the Ingestor SA (GitHub Actions) to invoke the Cloud Run Job
resource "google_cloud_run_v2_job_iam_member" "ingestor_invoke_permissions" {
  name     = google_cloud_run_v2_job.pyspark_job.name
  location = google_cloud_run_v2_job.pyspark_job.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.ingestor_sa.email}"
}

# Allow the Ingestor SA to view execution status (needed for the --wait flag)
resource "google_cloud_run_v2_job_iam_member" "ingestor_viewer_permissions" {
  name     = google_cloud_run_v2_job.pyspark_job.name
  location = google_cloud_run_v2_job.pyspark_job.location
  role     = "roles/run.viewer"
  member   = "serviceAccount:${google_service_account.ingestor_sa.email}"
}

# --------------------------------------------------------------------------------
# Workload Identity Federation (GitHub Actions)
# --------------------------------------------------------------------------------

# 1. Create the Identity Pool
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-actions-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Identity pool for GitHub Actions OIDC"
}

# 2. Create the Provider (Tells GCP to trust GitHub's authentication tokens)
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-actions-provider"
  display_name                       = "GitHub Actions Provider"

  # Maps GitHub's token attributes to GCP's token attributes
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  # SECURITY: Only allow YOUR specific repository to authenticate through this provider
  attribute_condition = "assertion.repository == '${var.github_repo_full_name}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# 3. Allow identities in the Pool (specifically your repo) to impersonate the Ingestor SA
resource "google_service_account_iam_member" "ingestor_wif_binding" {
  service_account_id = google_service_account.ingestor_sa.name
  role               = "roles/iam.workloadIdentityUser"
  
  # The principal is dynamically constructed based on the pool and the repository attribute
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_repo_full_name}"
}