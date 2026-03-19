# session.py

from pyspark.sql import SparkSession
from config import Config
import logging

logger = logging.getLogger("GCStoBQ_ETL")

def create_spark_session():
    logger.info("Initializing SparkSession...")
    
    # Define the JARs needed
    # 1. GCS Connector (Required for reading/writing to gs://)
    gcs_connector_jar = "https://repo1.maven.org/maven2/com/google/cloud/bigdataoss/gcs-connector/hadoop3-2.2.22/gcs-connector-hadoop3-2.2.22-shaded.jar"
    
    # 2. BigQuery Connector (Already handled by packages, but good to know)
    bq_package = "com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.35.0"

    builder = SparkSession.builder \
        .appName(Config.APP_NAME) \
        .master("local[*]") \
        .config("spark.driver.memory", Config.DRIVER_MEMORY) \
        .config("spark.sql.shuffle.partitions", Config.SHUFFLE_PARTITIONS) \
        .config("spark.jars", gcs_connector_jar) \
        .config("spark.jars.packages", bq_package) \
        .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem") \
        .config("spark.hadoop.fs.AbstractFileSystem.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS")

    if Config.GCP_KEY:
        logger.info("Using local GCP key.")
        builder = builder.config("spark.hadoop.google.cloud.auth.service.account.json.keyfile", Config.GCP_KEY)
    else:
        logger.info("Using Application Default Credentials (ADC).")

    if Config.PROJECT_ID:
        builder = builder.config("parentProject", Config.PROJECT_ID)

    spark = builder.getOrCreate()
    logger.info("SparkSession initialized successfully.")
    return spark