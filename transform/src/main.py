import logging
from session import create_spark_session
from config import Config
from transformations.silver import (
    clean_bronze_data,
    create_user_sessions
)
# Assuming you place the two new functions in transformations.gold
from transformations.gold import (
    create_regional_metrics,
    create_gold_retention,
    create_gold_staircase
)

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
        input_path = f"gs://{Config.GCS_BUCKET}/hyperion/"
        bronze_df = spark.read.option("mergeSchema", "true").parquet(input_path)

        # ---------------------------------------------------------
        # 2. TRANSFORM & WRITE SILVER (Base Measurements)
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
        # 3. TRANSFORM & WRITE SILVER (Enriched Sessions)
        # ---------------------------------------------------------
        silver_sessions_df = create_user_sessions(silver_df)
        
        silver_sessions_table = f"{Config.BQ_DATASET}.silver_user_sessions"
        
        silver_sessions_df.write.format("bigquery") \
            .option("writeMethod", "indirect") \
            .option("temporaryGcsBucket", Config.GCS_BUCKET) \
            .option("table", silver_sessions_table) \
            .option("partitionField", "session_date") \
            .option("partitionType", "DAY") \
            .option("clusteredFields", "user_id,behavior_bucket") \
            .mode("overwrite") \
            .save()

        logger.info(f"Silver Enriched Sessions table written to {silver_sessions_table}")

        # ---------------------------------------------------------
        # 4. TRANSFORM & WRITE GOLD (Aggregated Metrics & Dashboards)
        # ---------------------------------------------------------
        
        # 4a. Existing Regional Metrics
        gold_regional_df = create_regional_metrics(silver_df)
        regional_table = f"{Config.BQ_DATASET}.gold_regional_metrics"
        gold_regional_df.write.format("bigquery") \
            .option("writeMethod", "direct") \
            .option("table", regional_table) \
            .mode("overwrite") \
            .save()
            
        logger.info(f"Gold regional table written to {regional_table}")

        # 4b. Gold: User Retention (For the Pie Chart)
        gold_retention_df = create_gold_retention(silver_sessions_df)
        retention_table = f"{Config.BQ_DATASET}.gold_user_retention"
        gold_retention_df.write.format("bigquery") \
            .option("writeMethod", "direct") \
            .option("table", retention_table) \
            .mode("overwrite") \
            .save()
            
        logger.info(f"Gold User Retention table written to {retention_table}")

        # 4c. Gold: Frustration Staircase (For the Twin Plot)
        gold_staircase_df = create_gold_staircase(silver_sessions_df)
        staircase_table = f"{Config.BQ_DATASET}.gold_frustration_staircase"
        gold_staircase_df.write.format("bigquery") \
            .option("writeMethod", "direct") \
            .option("table", staircase_table) \
            .mode("overwrite") \
            .save()
            
        logger.info(f"Gold Frustration Staircase table written to {staircase_table}")

    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        raise e
    finally:
        if spark:
            spark.stop()

if __name__ == "__main__":
    main()