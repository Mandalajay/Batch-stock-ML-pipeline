# Batch Stock ML Pipeline

This project implements a **data-intensive batch ETL pipeline** for daily stock OHLCV data using the **Medallion Architecture** (Bronze → Silver → Gold).

- **Bronze**: raw append-only ingestions from multiple sources
- **Silver**: cleaned, deduplicated, idempotent upserts
- **Gold**: engineered features (moving averages, volume windows, returns) for ML/analytics

The pipeline is orchestrated by **Apache Airflow 2.9.3** running in Docker, with **PostgreSQL 15** as the data warehouse. It ingests both:

- Synthetic CSV (~1M rows)
- Public API (yfinance, AAPL OHLCV)

This satisfies the assignment's requirement for a **data-intensive pipeline**: heterogeneous sources, transformations, and ≥1,000,000 time-stamped records.

---

## Architecture

### Services (Docker Compose)

- `postgres`: stores Bronze/Silver/Gold tables
- `airflow`: DAGs, tasks, scheduler, webserver
- `ui` (optional): Streamlit dashboard for browsing Gold features

### Workflow (Airflow DAG)

1. **ingest_csv**: reads CSV from `landing/files/` → Bronze
2. **ingest_api**: fetches AAPL OHLCV from yfinance → Bronze
3. **build_silver**: SQL script dedupes/cleans → Silver (idempotent upserts)
4. **quality_check**: asserts non-nulls, valid ranges, row deltas
5. **transform_gold**: computes MA5, MA20, rolling volume, returns → Gold

### Data Model

```
bronze_price_raw(symbol, dt, open, high, low, close, volume)
price_silver(symbol, dt, open, high, low, close, volume)
features_gold(symbol, dt, ma5, ma20, vol10, ret1d)
```

---

## Setup & Reproducibility

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (optional, if running scripts locally)

### Clone & Start

```bash
git clone <this-repo>
cd batch-stock-ml-pipeline
docker compose up -d --build
```

### Initialize Airflow Metadata

Airflow DB and admin user are created automatically (`admin` / `admin`).

### Generate Demo Data

```bash
docker compose exec airflow bash -lc "python /opt/airflow/scripts/make_sample_csv.py --rows 1000000 --outfile /opt/airflow/landing/files/synthetic_1m.csv"
```

### Run the Pipeline

```bash
docker compose exec airflow bash -lc "airflow dags unpause batch_stock_pipeline"
docker compose exec airflow bash -lc "airflow dags trigger batch_stock_pipeline"
```

### Check Results

```bash
docker compose exec postgres psql -U user -d stocks -c "SELECT COUNT(*) FROM bronze_price_raw;"
docker compose exec postgres psql -U user -d stocks -c "SELECT COUNT(*) FROM price_silver;"
docker compose exec postgres psql -U user -d stocks -c "SELECT COUNT(*) FROM features_gold;"
```

### UI

- Airflow: [http://localhost:8080](http://localhost:8080) (admin/admin)
- Optional Streamlit: [http://localhost:8501](http://localhost:8501)

---

## Results

- **Bronze**: ~10M rows (multiple ingests)
- **Silver/Gold**: ~1M rows
- Pipeline runs end-to-end in minutes on a laptop, handling ~1M+ rows comfortably.
- Quality checks catch nulls/malformed rows; Silver deduping ensures idempotency.

---

## Reflection

### What Worked

- Medallion layering simplified contracts.
- Silver upserts guaranteed safe re-runs.
- Docker + Airflow made everything reproducible and observable.
- Vectorized transforms handled ~1M rows without tuning.

### What I'd Improve

- Move credentials into a secrets manager.
- Add a schema registry (even for batch).
- Partition/index by `(symbol, dt)` for large backfills.
- Expand data-quality checks (drift detection, completeness).

### Second Pipeline (Streaming)

- Ingest ticks/minute bars into Kafka (`prices.raw`).
- Spark/Flink jobs validate & conform → `prices.silver`.
- Aggregate event-time windows → `features.gold`.
- Sink with exactly-once guarantees into Postgres or a lakehouse.
- Nightly reconciliation ensures batch remains authoritative.

---

## Future Work — Real-Time Extension

To complement batch:

- **Kafka topics**: `prices.raw` → `prices.silver` → `features.gold`
- **Schema Registry**: Avro/Protobuf with compatibility checks
- **Processing**: Spark Structured Streaming or Flink
- **Features**: MA5, MA20, rolling volume, returns (event-time with watermarks)
- **Sinks**: Exactly-once to `features_gold_rt` (Postgres/lakehouse)
- **Ops**: Airflow triggers/monitors jobs, reconciliation tasks compare batch vs streaming

batch-stock-ml-pipeline/
│
├── airflow/
│   ├── dags/
│   ├── scripts/
│
├── sql/
│   ├── bronze.sql
│   ├── silver.sql
│   ├── gold.sql
│
├── landing/
│   └── files/
│
├── docker-compose.yml
├── README.md

