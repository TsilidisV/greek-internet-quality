import pytest
import requests
from requests.exceptions import RequestException
from src.clients import fetch_data, upload_parquet_to_gcp

def test_fetch_data_success(mocker, sample_raw_data):
    mock_response = mocker.Mock()
    mock_response.json.return_value = sample_raw_data
    mock_response.raise_for_status.return_value = None
    
    mocker.patch("requests.get", return_value=mock_response)
    
    result = fetch_data("2023-10-01", "2023-10-31")
    assert result == sample_raw_data

def test_upload_parquet_to_gcp(mocker, sample_dataframe):
    # Mock the GCS client, bucket, and blob
    mock_client_instance = mocker.Mock()
    mock_bucket = mock_client_instance.bucket.return_value
    mock_blob = mock_bucket.blob.return_value
    
    mocker.patch("src.clients.get_storage_client", return_value=mock_client_instance)
    
    from src.processing import get_schema
    schema = get_schema()
    
    upload_parquet_to_gcp(sample_dataframe, "test/path.parquet", schema)
    
    mock_bucket.blob.assert_called_once_with("test/path.parquet")
    mock_blob.upload_from_file.assert_called_once()
    
    # Check that content type was set correctly
    _, kwargs = mock_blob.upload_from_file.call_args
    assert kwargs["content_type"] == "application/octet-stream"