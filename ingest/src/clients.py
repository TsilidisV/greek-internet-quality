import io
import logging
import requests
import pandas as pd
import pyarrow as pa
from google.cloud import storage
from google.oauth2 import service_account
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import KEY_PATH, BUCKET_NAME, API_URL

logger = logging.getLogger(__name__)


def get_storage_client():
    """
    Initializes the GCS client.
    """
    try:
        if KEY_PATH:
            logger.info(f"Authenticating with local key file: {KEY_PATH}")
            credentials = service_account.Credentials.from_service_account_file(
                KEY_PATH
            )
            return storage.Client(credentials=credentials)

        logger.info("Authenticating with Application Default Credentials (ADC)")
        return storage.Client()

    except Exception as e:
        logger.error(f"Failed to initialize GCS client: {e}")
        raise


def upload_parquet_to_gcp(df: pd.DataFrame, destination_blob_name: str, schema: pa.schema):
    """
    Uploads a Pandas DataFrame as a parquet file to GCS.
    """
    try:
        client = get_storage_client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)

        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False, engine="pyarrow", schema=schema)
        buffer.seek(0)

        blob.upload_from_file(buffer, content_type="application/octet-stream")
        logger.info(f"Successfully uploaded: gs://{BUCKET_NAME}/{destination_blob_name}")

    except Exception as e:
        logger.error(f"Error uploading {destination_blob_name} to GCP: {e}")
        raise


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
    before_sleep=lambda retry_state: logger.warning(
        f"Request failed, retrying... (Attempt {retry_state.attempt_number})"
    ),
)
def fetch_data(date_from: str, date_to: str):
    """
    Fetches data from the API with exponential backoff retry logic.
    """
    params = {"date_from": date_from, "date_to": date_to}
    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    return response.json()