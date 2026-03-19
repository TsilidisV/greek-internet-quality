from pyspark.sql.functions import col, to_timestamp, sha2, when, to_date

def clean_bronze_data(df):
    """
    Transforms raw Bronze data into cleansed Silver data.
    """
    # Type casting and hashing
    df = df.withColumn("measurement_time", to_timestamp(col("measurement_time"))) \
           .withColumn("measurement_date", to_date(col("measurement_time"))) \
           .withColumn("user_id", sha2(col("client_ip"), 256)) \
           .drop("client_ip")

    # Handle NaNs
    string_cols = ["connection_municipality", "connection_regional_unit", "connection_periphery"]
    for c in string_cols:
        df = df.withColumn(c, when((col(c) == "NaN") | (col(c).isNull()), 'N/A').otherwise(col(c)))

    # Quality Filters
    df = df.filter(col("measurement_time").isNotNull()) \
           .filter(col("measured_downstream_mbps") >= 0)
           
    return df