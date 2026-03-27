import logging
from datetime import datetime, timezone
import pandas as pd
import pyarrow as pa
from dateutil.relativedelta import relativedelta

from .clients import fetch_data, upload_parquet_to_gcp

logger = logging.getLogger(__name__)


def get_schema() -> pa.schema:
    """Defines the output schema."""
    return pa.schema([
        ('measurement_time', pa.timestamp('us', tz='Europe/Athens')),
        ('connection_id', pa.string()), 
        ('client_ip', pa.string()),
        ('measurement_id', pa.int64()),
        ('measured_downstream_mbps', pa.float64()),
        ('measured_upstream_mbps', pa.float64()),
        ('measured_rtt_msec', pa.float64()),
        ('measured_loss_percentage', pa.float64()),
        ('measured_jitter_msec', pa.float64()),
        ('client_operating_system', pa.string()),
        ('client_operating_system_version', pa.string()),
        ('client_operating_system_architecture', pa.string()),
        ('ISP', pa.string()),
        ('contract_download_mbps', pa.float64()),
        ('contract_upload_mbps', pa.float64()),
        ('connection_postal_code', pa.string()),
        ('connection_municipality_id', pa.string()),
        ('connection_municipality', pa.string()),
        ('connection_regional_unit_id', pa.string()),
        ('connection_regional_unit', pa.string()),
        ('connection_periphery_id', pa.string()),
        ('connection_periphery', pa.string()),
        ('ingested_at', pa.timestamp('us', tz='UTC'))
    ])


def process_raw_data(data: list) -> pd.DataFrame:
    """
    Converts raw JSON list to a cleaned DataFrame with proper types.
    """
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    df = df.astype({
        "connection_postal_code": "string",
        "connection_id": "string",
        "connection_municipality_id": "string",
        "connection_regional_unit_id": "string",
        "connection_periphery_id": "string"
    })

    df['measurement_time'] = pd.to_datetime(df['measurement_time'])
    # Apply the Europe/Athens timezone
    if df['measurement_time'].dt.tz is None:
        # If the API string lacks an offset (naive), just stamp it as Athens time
        df['measurement_time'] = df['measurement_time'].dt.tz_localize('Europe/Athens')
    else:
        # If the API string includes an offset (e.g., +02:00), standardize it to the named tz
        df['measurement_time'] = df['measurement_time'].dt.tz_convert('Europe/Athens')

    df["ingested_at"] = datetime.now(timezone.utc)

    return df


def process_month(year: int, month: int):
    """
    Orchestrates fetching and uploading for a specific month.
    Writes a single file to: hyperion/year=YYYY/month=MM/data.parquet
    """
    # 1. Calculate Date Range
    start_date = datetime(year, month, 1)
    end_date = start_date + relativedelta(months=1) - relativedelta(days=1)
    
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    logger.info(f"Processing month: {year}-{month:02d} ({start_str} to {end_str})")

    # 2. Fetch Data
    data = fetch_data(start_str, end_str)

    if not data:
        logger.warning(f"No data found for {year}-{month:02d}. Skipping upload.")
        return

    # 3. Process Data
    df = process_raw_data(data)

    # 4. Define Hive Path (Monthly Partition)
    hive_path = (
        f"hyperion/"
        f"year={year}/"
        f"month={month:02d}/"
        f"data.parquet"
    )

    # 5. Upload
    upload_parquet_to_gcp(df, hive_path, get_schema())