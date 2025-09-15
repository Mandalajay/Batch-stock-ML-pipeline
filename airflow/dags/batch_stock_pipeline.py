import sys
sys.path.append("/opt/airflow/scripts")  # so `import ingest` works inside container

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import ingest, transform

with DAG(
    "batch_stock_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
) as dag:
    t_ingest = PythonOperator(task_id="ingest", python_callable=ingest.run)
    t_transform = PythonOperator(task_id="transform", python_callable=transform.run)
    t_ingest >> t_transform
