import os

class Config:
    # Environment
    GCP_KEY = os.environ.get("TRANSFORM_GCP_KEY")
    PROJECT_ID = os.environ.get("PROJECT_ID")
    GCS_BUCKET = os.environ.get("GCS_BUCKET_NAME")
    BQ_DATASET = os.environ.get("BQ_DATASET")

    # Spark Config
    APP_NAME = "GCS-to-BigQuery-ETL"
    DRIVER_MEMORY = "4g"
    SHUFFLE_PARTITIONS = "2"

    # Business Logic
    SESSION_TIMEOUT_SECONDS = 3600  # 60 mins