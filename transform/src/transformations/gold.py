from pyspark.sql import functions as F
from config import Config

def create_regional_metrics(df):
    """
    Logic to aggregate metrics by region and date.
    """
    return df \
        .groupBy("measurement_date", "connection_periphery") \
        .agg(
            F.count("measurement_id").alias("total_tests"),
            F.expr("avg(measured_downstream_mbps)").alias("avg_downstream_mbps"),
            F.expr("percentile_approx(measured_downstream_mbps, 0.5)").alias("p50_downstream_mbps"),
            F.expr("avg(measured_upstream_mbps)").alias("avg_upstream_mbps"),
            F.expr("avg(measured_rtt_msec)").alias("avg_rtt_msec"),
            F.expr("avg(measured_loss_percentage)").alias("avg_loss_percentage"),
            F.expr("avg(measured_jitter_msec)").alias("avg_jitter_msec"),
        )

def create_gold_retention(df):
    # 1. Classify the user
    classified_df = df.withColumn(
        "user_type",
        F.when(F.col("has_valid_baseline"), "Returning user")
         .otherwise("New/Transient user")
    )
    
    # 2. Group by Date AND User Type
    gold_retention = classified_df.groupBy("session_date", "user_type").agg(
        F.count("session_id").alias("total_sessions")
    ).orderBy("session_date", "user_type")
    
    return gold_retention
    
def create_gold_staircase(silver_sessions_df):
    # The behavior_bucket already exists now! Just group it.
    gold_staircase = silver_sessions_df.groupBy("session_date", "behavior_bucket").agg(
        F.count("session_id").alias("total_sessions"),
        F.expr("percentile_approx(avg_downstream, 0.5)").alias("median_downstream_mbps"),
        F.expr("percentile_approx(avg_loss, 0.5)").alias("median_loss_pct"),
        F.expr("percentile_approx(avg_jitter, 0.5)").alias("median_jitter_ms"),
        F.expr("percentile_approx(avg_rtt, 0.5)").alias("median_rtt_ms")
    ).orderBy("session_date", "behavior_bucket")
    
    return gold_staircase