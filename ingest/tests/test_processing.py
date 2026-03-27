import pytest
import io
import pandas as pd
import pyarrow.parquet as pq
from src.processing import process_raw_data, process_month, get_schema

def test_process_raw_data_empty():
    df = process_raw_data([])
    assert isinstance(df, pd.DataFrame)
    assert df.empty

def test_process_raw_data_valid(sample_raw_data):
    df = process_raw_data(sample_raw_data)
    
    assert not df.empty
    assert "ingested_at" in df.columns
    # Verify string casting worked
    assert pd.api.types.is_string_dtype(df["connection_id"])
    assert df["connection_id"].iloc[0] == "12345"
    # Verify datetime conversion worked
    assert pd.api.types.is_datetime64_any_dtype(df["measurement_time"])

def test_process_month_success(mocker, sample_raw_data, sample_dataframe):
    # Mock out the external network calls
    mock_fetch = mocker.patch("src.processing.fetch_data", return_value=sample_raw_data)
    mock_upload = mocker.patch("src.processing.upload_parquet_to_gcp")
    
    process_month(2023, 10)
    
    # 1. Did it fetch the right dates? (October has 31 days)
    mock_fetch.assert_called_once_with("2023-10-01", "2023-10-31")
    
    # 2. Did it upload to the right Hive partition path?
    mock_upload.assert_called_once()
    args, _ = mock_upload.call_args
    assert args[1] == "hyperion/year=2023/month=10/data.parquet"
    assert isinstance(args[0], pd.DataFrame) # It should pass a DataFrame

def test_process_month_no_data(mocker):
    # Simulate API returning an empty list
    mock_fetch = mocker.patch("src.processing.fetch_data", return_value=[])
    mock_upload = mocker.patch("src.processing.upload_parquet_to_gcp")
    
    process_month(2023, 10)
    
    mock_fetch.assert_called_once()
    mock_upload.assert_not_called() # Should abort early and not upload


def test_dataframe_to_parquet_with_real_schema(sample_dataframe):
    """Tests that our actual pipeline data serializes cleanly to Parquet."""
    buffer = io.BytesIO()
    schema = get_schema()

    # 1. Execute the exact command using our fixture data
    sample_dataframe.to_parquet(buffer, index=False, engine="pyarrow", schema=schema)

    # 2. Rewind the buffer
    buffer.seek(0)
    
    # 3. Read it back and verify data integrity
    recovered_df = pd.read_parquet(buffer, engine="pyarrow")
    
    # Check that the data survived the round-trip perfectly
    pd.testing.assert_frame_equal(sample_dataframe, recovered_df)

    # 4. Verify the PyArrow schema was strictly enforced
    buffer.seek(0)
    parquet_file = pq.ParquetFile(buffer)
    
    # We check equals() to ensure no columns were dropped or types altered
    assert parquet_file.schema_arrow.equals(schema)