from pyspark.sql.functions import col, lag, unix_timestamp, when, sum as _sum, concat_ws, count, expr
from pyspark.sql.window import Window
from config import Config

def create_sessionization(df):
    """
    Logic to sessionize user tests.
    """
    # 1. Define Windows
    window_user_time = Window.partitionBy("user_id").orderBy("measurement_time")
    window_session_gap = Window.partitionBy("user_id").orderBy("session_start_time")

    timeout = Config.SESSION_TIMEOUT_SECONDS

    # 2. Flag new sessions
    df = df.withColumn("prev_measurement_time", lag("measurement_time").over(window_user_time)) \
           .withColumn("time_gap_seconds", unix_timestamp("measurement_time") - unix_timestamp("prev_measurement_time"))

    df = df.withColumn("is_new_session", 
           when(col("time_gap_seconds") > timeout, 1)
           .when(col("prev_measurement_time").isNull(), 1)
           .otherwise(0))

    # 3. Create Session ID
    df = df.withColumn("user_session_seq", _sum("is_new_session").over(window_user_time)) \
           .withColumn("session_id", concat_ws("-", col("user_id"), col("user_session_seq")))

    # 4. Aggregate to Session Level (Restored missing columns)
    gold_user_sessions_base = df.groupBy("session_id", "user_id").agg(
        expr("min(measurement_time)").alias("session_start_time"),
        expr("max(measurement_time)").alias("session_end_time"),
        count("measurement_id").alias("total_tests_in_session"),
        expr("avg(measured_downstream_mbps)").alias("avg_session_downstream_mbps") # RESTORED
    )

    # 5. Calculate time since last session (Restored logic)
    gold_user_sessions = gold_user_sessions_base.withColumn(
        "prev_session_start_time", 
        lag("session_start_time").over(window_session_gap)
    ).withColumn(
        "time_since_last_session_seconds",
        unix_timestamp("session_start_time") - unix_timestamp("prev_session_start_time")
    ).drop("prev_session_start_time")

    return gold_user_sessions

def create_regional_metrics(df):
    """
    Logic to aggregate metrics by region and date.
    """
    return df \
        .groupBy("measurement_date", "connection_periphery") \
        .agg(
            count("measurement_id").alias("total_tests"),
            expr("avg(measured_downstream_mbps)").alias("avg_downstream_mbps"),
            expr("percentile_approx(measured_downstream_mbps, 0.5)").alias("p50_downstream_mbps"),
            expr("avg(measured_upstream_mbps)").alias("avg_upstream_mbps"),
            expr("avg(measured_rtt_msec)").alias("avg_rtt_msec"),
            expr("avg(measured_loss_percentage)").alias("avg_loss_percentage"),
            expr("avg(measured_jitter_msec)").alias("avg_jitter_msec"),
        )