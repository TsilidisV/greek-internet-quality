# github actions
variable "project_id" {
  description = "The GCP Project ID"
  type        = string
  default     = "greek-internet-quality"
}

# github actions
variable "region" {
  description = "The GCP region for resources (Must be us-central1, us-west1, or us-east1 for Free Tier GCS)"
  type        = string
  default     = "us-east1"
}

# github actions
variable "bucket_name" {
  description = "Globally unique name for the GCS bucket"
  type        = string
  default     = "greek-internet-data"
}

variable "dataset_id" {
  description = "The BigQuery Dataset ID"
  type        = string
  default     = "greek_internet_warehouse"
}

variable "docker_image" {
  description = "The Docker Hub image URL (e.g., docker.io/username/image:tag)"
  type        = string
  default     = "vtsilidis/greek-internet-pyspark:latest"
}

# github actions
variable "job_name" {
  description = "Name of the Cloud Run Job"
  type        = string
  default     = "pyspark-internet-job"
}

variable "github_repo_full_name" {
  description = "Github repository name"
  type        = string
  default     = "TsilidisV/greece-internet-quality"
}

variable "github_token" {
  description = "GitHub Personal Access Token for Terraform"
  type        = string
  sensitive   = true # This hides the value from terminal output!
}