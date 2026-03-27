import pytest
from datetime import datetime
from typer.testing import CliRunner
from src.main import app 

runner = CliRunner()

def test_backfill_command(mocker):
    mock_process = mocker.patch("src.main.process_month")
    
    result = runner.invoke(app, ["backfill", "2023-01", "2023-03"])
    
    assert result.exit_code == 0
    assert mock_process.call_count == 3
    mock_process.assert_any_call(2023, 1)
    mock_process.assert_any_call(2023, 2)
    mock_process.assert_any_call(2023, 3)

def test_daily_command(mocker):
    mock_process = mocker.patch("src.main.process_month")
    mock_now = datetime(2023, 10, 15)
    mocker.patch("src.main.datetime").now.return_value = mock_now
    
    result = runner.invoke(app, ["daily"])
    
    assert result.exit_code == 0
    mock_process.assert_called_once_with(2023, 10)

def test_monthly_command_defaults_to_previous_month(mocker):
    mock_process = mocker.patch("src.main.process_month")
    mock_now = datetime(2023, 10, 15)
    mocker.patch("src.main.datetime").now.return_value = mock_now
    
    result = runner.invoke(app, ["monthly"])
    
    assert result.exit_code == 0
    mock_process.assert_called_once_with(2023, 9)

def test_monthly_command_explicit_args(mocker):
    mock_process = mocker.patch("src.main.process_month")
    
    result = runner.invoke(app, ["monthly", "2022", "5"])
    
    assert result.exit_code == 0
    mock_process.assert_called_once_with(2022, 5)