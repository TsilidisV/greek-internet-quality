# --------------------------------------------------------------------------------
# 3. Data Lake (GCS)
# --------------------------------------------------------------------------------
resource "google_storage_bucket" "data_lake" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = true # Allows deleting bucket even if it has files (careful!)

  uniform_bucket_level_access = true
  storage_class               = "STANDARD" # Required for Free Tier

  depends_on = [google_project_service.enabled_apis]
}

# Grant the Transformer Service Account access to read/write GCS
resource "google_storage_bucket_iam_member" "sa_gcs_admin" {
  bucket = google_storage_bucket.data_lake.name
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.transformer_sa.email}"
}

# Grant the Ingestor permission to upload to the Data Lake
# "objectAdmin" allows writing, overwriting, and deleting files in this specific bucket
resource "google_storage_bucket_iam_member" "ingestor_gcs_writer" {
  bucket = google_storage_bucket.data_lake.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.ingestor_sa.email}"
}

# --------------------------------------------------------------------------------
# 4. Data Warehouse (BigQuery)
# --------------------------------------------------------------------------------
resource "google_bigquery_dataset" "warehouse" {
  dataset_id  = var.dataset_id
  location    = var.region
  description = "Medallion architecture warehouse"

  depends_on = [google_project_service.enabled_apis]
}

# Grant the Transformer Service Account access to write to BigQuery
resource "google_project_iam_member" "sa_bq_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.transformer_sa.email}"
}

resource "google_project_iam_member" "sa_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.transformer_sa.email}"
}

# Grant the Transformer Service Account permission to use the BigQuery Storage Read API (required by Spark)
resource "google_project_iam_member" "sa_bq_read_session_user" {
  project = var.project_id
  role    = "roles/bigquery.readSessionUser"
  member  = "serviceAccount:${google_service_account.transformer_sa.email}"
}