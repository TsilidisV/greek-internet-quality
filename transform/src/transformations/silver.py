from pyspark.sql.functions import col, sha2, when, to_date
from pyspark.sql import functions as F
from pyspark.sql.window import Window

def clean_bronze_data(df):
    """
    Transforms raw Bronze data into cleansed Silver data.
    """
    # measurement_time is already a proper timestamp! 
    # Just derive the date and hash the IP.
    df = df.withColumn("measurement_date", to_date(col("measurement_time"))) \
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


def create_user_sessions(df, session_timeout_minutes=30, max_days_between_sessions=14):
    """
    Groups individual speed tests into sessions, adds session dates, and compares 
    performance against the user's previous session for frustration tracking.
    """
    # 1. Window to order tests chronologically per user
    user_time_window = Window.partitionBy("user_id").orderBy("measurement_time")

    # 2. Calculate time difference (in seconds) from the user's previous test
    df_lagged = df.withColumn("prev_time", F.lag("measurement_time").over(user_time_window))
    df_diff = df_lagged.withColumn(
        "time_diff_sec",
        F.unix_timestamp("measurement_time") - F.unix_timestamp("prev_time")
    )

    # 3. Flag new sessions
    timeout_sec = session_timeout_minutes * 60
    df_flags = df_diff.withColumn(
        "is_new_session",
        F.when(
            F.col("time_diff_sec").isNull() | (F.col("time_diff_sec") > timeout_sec), 
            1
        ).otherwise(0)
    )

    # 4. Create a unique Session ID per user using a cumulative sum
    df_sessions = df_flags.withColumn(
        "session_id",
        F.sum("is_new_session").over(user_time_window)
    )

    # 5. Aggregate metrics to the Session Level AND ADD THE DATE
    session_stats = df_sessions.groupBy("user_id", "session_id").agg(
        F.min("measurement_time").alias("session_start"),
        F.max("measurement_time").alias("session_end"),
        F.count("measurement_id").alias("test_count"),
        F.mean("measured_downstream_mbps").alias("avg_downstream"),
        F.mean("measured_upstream_mbps").alias("avg_upstream"),
        F.mean("measured_rtt_msec").alias("avg_rtt"),
        F.mean("measured_loss_percentage").alias("avg_loss"),
        F.mean("measured_jitter_msec").alias("avg_jitter")
    ).withColumn(
        "session_date", 
        F.to_date(F.col("session_start")) # <--- NEW: Extract the date for dashboard filtering
    )

    # 6. Compare with the Previous Session applying the Time Decay Rule
    user_session_window = Window.partitionBy("user_id").orderBy("session_start")
    
    sessions_with_lag = session_stats.withColumn(
        "prev_session_end", F.lag("session_end").over(user_session_window)
    ).withColumn(
        "prev_session_downstream", F.lag("avg_downstream").over(user_session_window)
    ).withColumn(
        "prev_session_loss", F.lag("avg_loss").over(user_session_window)
    )

    sessions_with_gap = sessions_with_lag.withColumn(
        "days_since_prev_session",
        (F.unix_timestamp("session_start") - F.unix_timestamp("prev_session_end")) / (24 * 3600)
    )

    # 7. Apply the decay rule AND a minimum valid baseline (e.g., ignore near-zero speeds)
    final_df = sessions_with_gap.withColumn(
        "has_valid_baseline",
        F.when(
            (F.col("days_since_prev_session").isNotNull()) & 
            (F.col("days_since_prev_session") <= max_days_between_sessions),
            True
        ).otherwise(False)
    ).withColumn(
        "speed_drop_pct",
        F.when(
            F.col("has_valid_baseline"),
            ((F.col("prev_session_downstream") - F.col("avg_downstream")) / F.col("prev_session_downstream")) * 100
        ).otherwise(None) 
    )

    final_df_with_buckets = final_df.withColumn(
        "behavior_bucket",
        F.when(F.col("test_count") == 1, "1. Single Test")
         .when((F.col("test_count") >= 2) & (F.col("test_count") <= 3), "2. Moderate (2-3)")
         .when(F.col("test_count") >= 4, "3. High (4+)")
         .otherwise("Unknown")
    )
    
    return final_df_with_buckets