import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Settings
KEY_PATH = os.getenv("INGESTOR_GCP_KEY")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
API_URL = "https://data.gov.gr/api/v1/query/hyperion"

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)