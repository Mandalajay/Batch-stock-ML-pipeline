# Batch Stock ML Pipeline

This project implements a **data-intensive batch ETL pipeline** for daily stock OHLCV data using the **Medallion Architecture** (Bronze → Silver → Gold).

- **Bronze**: raw append-only ingestions from multiple sources
- **Silver**: cleaned, deduplicated, idempotent upserts
- **Gold**: engineered features (moving averages, volume windows, returns)

Orchestrated by **Apache Airflow 2.9.3** in Docker, using **PostgreSQL 15**. Ingests:

- Synthetic CSV (~1M rows)
- Public API (yfinance AAPL OHLCV)

This is a data-intensive pipeline (heterogeneous sources, transformations, ≥1M time-stamped records).

---

## Architecture

### Components (Docker Compose)

- `postgres`: data warehouse for Bronze/Silver/Gold
- `airflow`: scheduler, webserver, DAG execution
- `ui` (optional): Streamlit checking Gold data

### Airflow DAG: `batch_stock_pipeline`

1. `ingest_csv` → Bronze
2. `ingest_api` → Bronze
3. `build_silver` (dedupe/clean/upsert) → Silver
4. `quality_check` → validation
5. `transform_gold` → Gold

### Schema

- `bronze_price_raw(symbol, dt, open, high, low, close, volume)`
- `price_silver(symbol, dt, open, high, low, close, volume)`
- `features_gold(symbol, dt, ma5, ma20, vol10, ret1d)`

---

## Setup

### Requirements

- Docker & Docker Compose
- Python 3.11+ (if running scripts locally)

### Start

```bash
git clone <repo-url>
cd batch-stock-ml-pipeline
docker compose up -d --build
```

### Generate sample CSV

```bash
docker compose exec airflow bash -lc "python /opt/airflow/scripts/make_sample_csv.py --rows 1000000 --outfile /opt/airflow/landing/files/synthetic_1m.csv"
```

### Run pipeline

```bash
docker compose exec airflow bash -lc "airflow dags unpause batch_stock_pipeline"
docker compose exec airflow bash -lc "airflow dags trigger batch_stock_pipeline"
```

### Verify counts

```bash
docker compose exec postgres psql -U user -d stocks -c "SELECT COUNT(*) FROM bronze_price_raw;"
docker compose exec postgres psql -U user -d stocks -c "SELECT COUNT(*) FROM price_silver;"
docker compose exec postgres psql -U user -d stocks -c "SELECT COUNT(*) FROM features_gold;"
```

### Web UIs

- Airflow: http://localhost:8080 (admin/admin)
- Streamlit: http://localhost:8501 (optional)

---

## Outcomes

- Bronze: ~10M rows
- Silver/Gold: ~1M rows
- Fast end-to-end on laptop
- Idempotent Silver upserts, quality checks pass

---

## Improvements

- Secure credentials with secrets manager
- Add schema registry and versioning
- Partition/index by `(symbol, dt)`
- Add drift/completeness checks

---

## Optional future: real-time streaming

- Kafka topics: `prices.raw` → `prices.silver` → `features.gold`
- Spark/Flink streaming with event-time and watermarks
- Exactly-once sinks (Postgres/lakehouse)
- Airflow reconciliation with batch data

---

## Repo structure

```
batch-stock-ml-pipeline/
├── airflow/
│   ├── dags/
│   ├── scripts/
├── sql/
│   ├── bronze.sql
│   ├── silver.sql
│   ├── gold.sql
├── landing/files/
├── docker-compose.yml
├── README.md
```

