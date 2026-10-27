"""
Optional Apache Spark analysis for local/Colab environments with Java + PySpark.
This script is separate from Streamlit Cloud deployment because a hosted Streamlit
app is not a full Hadoop/HDFS cluster.
Run from project root:
    spark-submit scripts/spark_analysis.py data/hospital_waiting_data.csv
"""
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, to_timestamp, unix_timestamp, when

input_path = sys.argv[1] if len(sys.argv) > 1 else "data/hospital_waiting_data.csv"

spark = (
    SparkSession.builder
    .appName("HospitalWaitingTimeAnalyzer")
    .master("local[*]")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

df = spark.read.option("header", True).option("inferSchema", True).csv(input_path)

required = {"Patient_ID", "Department", "Arrival_Time", "Consultation_Start", "Day"}
missing = required.difference(df.columns)
if missing:
    raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))

df = (
    df.withColumn("arrival_ts", to_timestamp(col("Arrival_Time"), "HH:mm"))
      .withColumn("consultation_ts", to_timestamp(col("Consultation_Start"), "HH:mm"))
      .withColumn(
          "Waiting_Minutes",
          (unix_timestamp(col("consultation_ts")) - unix_timestamp(col("arrival_ts"))) / 60
      )
      .withColumn(
          "Waiting_Minutes",
          when(col("Waiting_Minutes") < 0, col("Waiting_Minutes") + 1440)
          .otherwise(col("Waiting_Minutes"))
      )
      .filter(col("Waiting_Minutes").isNotNull() & (col("Waiting_Minutes") >= 0))
)

print("\n=== Overall summary ===")
df.agg(
    count("*").alias("Patients"),
    avg("Waiting_Minutes").alias("Average_Wait_Minutes")
).show(truncate=False)

print("\n=== Department summary ===")
df.groupBy("Department").agg(
    count("*").alias("Patients"),
    avg("Waiting_Minutes").alias("Average_Wait_Minutes")
).orderBy(col("Average_Wait_Minutes").desc()).show(truncate=False)

print("\n=== Day summary ===")
df.groupBy("Day").agg(
    count("*").alias("Patients"),
    avg("Waiting_Minutes").alias("Average_Wait_Minutes")
).orderBy("Day").show(truncate=False)

spark.stop()
