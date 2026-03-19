import logging
from session import create_spark_session
from config import Config
from transformations.silver import clean_bronze_data
from transformations.gold import create_sessionization, create_regional_metrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("GCStoBQ_ETL")

def main():
    spark = None
    try:
        spark = create_spark_session()
        
        # ---------------------------------------------------------
        # 1. READ BRONZE
        # ---------------------------------------------------------
        input_path = f"gs://{Config.GCS_BUCKET}/hyperion/year=2023/"
        bronze_df = spark.read.option("mergeSchema", "true").parquet(input_path)

        # ---------------------------------------------------------
        # 2. TRANSFORM & WRITE SILVER
        # ---------------------------------------------------------
        silver_df = clean_bronze_data(bronze_df)
        
        silver_table = f"{Config.BQ_DATASET}.silver_measurements"
        
        silver_df.write.format("bigquery") \
            .option("writeMethod", "indirect") \
            .option("temporaryGcsBucket", Config.GCS_BUCKET) \
            .option("table", silver_table) \
            .option("partitionField", "measurement_date") \
            .option("partitionType", "DAY") \
            .option("clusteredFields", "user_id,connection_regional_unit") \
            .mode("overwrite") \
            .save()

        logger.info(f"Silver table written to {silver_table}")

        # ---------------------------------------------------------
        # 3. TRANSFORM & WRITE GOLD (Sessionization)
        # ---------------------------------------------------------
        # Pass the in-memory silver_df directly to avoid re-reading from BQ
        gold_sessions_df = create_sessionization(silver_df)
        
        gold_table = f"{Config.BQ_DATASET}.gold_sessionization"
        
        gold_sessions_df.write.format("bigquery") \
            .option("writeMethod", "direct") \
            .option("table", gold_table) \
            .mode("overwrite") \
            .save()

        logger.info(f"Gold session table written to {gold_table}")

        # ---------------------------------------------------------
        # 4. TRANSFORM & WRITE GOLD (Regional Metrics)
        # ---------------------------------------------------------
        gold_regional_df = create_regional_metrics(silver_df)
        
        regional_table = f"{Config.BQ_DATASET}.gold_regional_metrics"
        
        gold_regional_df.write.format("bigquery") \
            .option("writeMethod", "direct") \
            .option("table", regional_table) \
            .mode("overwrite") \
            .save()
            
        logger.info(f"Gold regional table written to {regional_table}")

    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        raise e
    finally:
        if spark:
            spark.stop()

if __name__ == "__main__":
    main()