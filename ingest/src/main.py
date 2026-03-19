import typer
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from .processing import process_month
from .config import logger

app = typer.Typer()


@app.command()
def backfill(start_date_str: str, end_date_str: str):
    """
    Iterates through a date range month-by-month.
    Format: 'YYYY-MM'
    """
    start_date = datetime.strptime(start_date_str, "%Y-%m")
    end_date = datetime.strptime(end_date_str, "%Y-%m")

    # Normalize to the 1st of the month to avoid partial month logic
    current_date = start_date.replace(day=1)
    end_date_normalized = end_date.replace(day=1)

    logger.info(f"Starting backfill from {start_date_str} to {end_date_str}")

    while current_date <= end_date_normalized:
        process_month(current_date.year, current_date.month)
        current_date += relativedelta(months=1)

    logger.info("Backfill completed.")


@app.command()
def daily():
    """
    Refreshes the current month's partition.
    Useful for keeping the current month up-to-date until the monthly job runs.
    """
    today = datetime.now()
    # Process current month
    logger.info("Starting daily refresh of current month.")
    process_month(today.year, today.month)
    logger.info("Daily refresh finished.")


@app.command()
def monthly(
    year: int = typer.Argument(None, help="Year (YYYY). Defaults to previous month."),
    month: int = typer.Argument(None, help="Month (1-12). Defaults to previous month."),
):
    """
    Runs the ingestion pipeline for a specific month.
    Defaults to the previous month.
    """
    today = datetime.now()
    
    if year is None or month is None:
        # Default to previous month
        target = today - relativedelta(months=1)
        year = target.year
        month = target.month
        logger.info(f"No date specified, defaulting to previous month: {year}-{month:02d}")

    process_month(year, month)


if __name__ == "__main__":
    app()