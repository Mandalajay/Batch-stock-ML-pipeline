import sys; sys.path.append("/opt/airflow/scripts")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from datetime import datetime, timedelta
import ingest_csv, ingest_api, transform_features

CSV_PATH = "/opt/airflow/landing/files/aapl_sample.csv"

with DAG(
    dag_id="batch_stock_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=1)},
    template_searchpath=["/opt/airflow/sql"], 
    max_active_runs=1,          # ← only 1 run at a time
    max_active_tasks=4,  # <-- THIS makes "build_silver.sql" resolvable
) as dag:
    t_ingest_csv = PythonOperator(
        task_id="ingest_csv",
        python_callable=lambda: ingest_csv.load_csv_to_bronze(CSV_PATH),
    )

    t_ingest_api = PythonOperator(
        task_id="ingest_api",
        python_callable=lambda: ingest_api.fetch_to_bronze("AAPL", "2022-01-01", "2022-02-11", retries=3),
    )

    t_build_silver = SQLExecuteQueryOperator(
        task_id="build_silver",
        conn_id="postgres_default",
        sql="build_silver.sql",          # <-- only the filename; Airflow finds it via template_searchpath
        hook_params={"schema": "stocks"},# (optional) points at DB schema
    )

    t_transform = PythonOperator(
        task_id="transform_gold",
        python_callable=transform_features.compute_features,
    )

    [t_ingest_csv, t_ingest_api] >> t_build_silver >> t_transform
