import pytest
import pandas as pd
from datetime import datetime, timezone

from src.processing import process_raw_data

@pytest.fixture
def sample_raw_data():
    """Provides a sample of raw JSON data returned by the API."""
    return [
        {
            "measurement_time": "2026-02-05 05:24:55",
            "connection_id": 12345,
            "client_ip": "80.191.12",
            "measurement_id": 331110,
            "measured_downstream_mbps": 312.58,
            "measured_upstream_mbps": 148.34,
            "measured_rtt_msec": 3.0,
            "measured_loss_percentage": 0.0223584284507252,
            "measured_jitter_msec": 0.0,
            "client_operating_system": "Windows 10 x64",
            "client_operating_system_version": "10",
            "client_operating_system_architecture": "x64",
            "ISP": "",
            "contract_download_mbps": 300.0,
            "contract_upload_mbps": 30.0,
            "connection_postal_code": 19016.0,
            "connection_municipality_id": 9226.0,
            "connection_municipality": "ΣΠΑΤΩΝ - ΑΡΤΕΜΙΔΟΣ",
            "connection_regional_unit_id": 44.0,
            "connection_regional_unit": "Ανατολικής Αττικής",
            "connection_periphery_id": 9.0,
            "connection_periphery": "ΑΤΤΙΚΗΣ"
        }
    ]

@pytest.fixture
def sample_dataframe(sample_raw_data):
    """Provides a processed Pandas DataFrame."""

    return process_raw_data(sample_raw_data)