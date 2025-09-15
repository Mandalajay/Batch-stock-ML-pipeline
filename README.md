Phase 2 Implementation Summary (Batch Stock ML)
I implemented a minimal, dockerized batch data pipeline for stock-market ML preprocessing. The stack includes Apache Airflow for orchestration and PostgreSQL for storage. An ingestion script periodically loads OHLCV data (demo dataset) into a raw_stocks table. A transformation step computes simple yet informative features—such as a 3-day moving average and a 1-day return—and writes them to a curated features table for downstream model training. The Airflow DAG (batch_stock_pipeline) defines dependencies (ingest → transform) with a daily schedule and no catch-up, demonstrating basic reliability via task isolation and reproducible execution. The repository includes a docker-compose.yml that starts Airflow and Postgres, a lightweight README with steps to run the pipeline locally, and two scripts (ingest.py, transform.py) that encapsulate ETL logic. While this prototype focuses on a small dataset and pandas for simplicity, the modular design allows straightforward extension to distributed processing (e.g., Apache Spark), data quality checks, and additional features (volatility, rolling z-scores). This Phase 2 submission establishes the core implementation path from the Phase 1 design and prepares the groundwork for Phase 3 enhancements and evaluation.
user:admin
pass:admin

phase 3:
Perfect — let’s shape this into a **Phase 3 “Results & Evaluation” section** you can drop into your final report (about 1.5–2 pages with screenshots/tables). It uses your **real numbers** and adds the academic-style narrative.

---

# 📑 Results and Evaluation

### Data Processing Outcomes

The batch pipeline was executed successfully using Apache Airflow to orchestrate ingestion and transformation tasks. During the ingestion phase, a total of **30 rows** of synthetic stock OHLCV data were generated and inserted into the `raw_stocks` table in PostgreSQL. The dataset covered the period from **2022-01-03** to **2022-02-11**, representing 30 consecutive business days.

The transformation task produced a derived `features` table containing both the raw values and engineered indicators. These included short-term and medium-term moving averages (`ma3`, `ma5`, `ma20`), a 10-day rolling volatility measure (`vol10`), and one-day percentage returns (`ret1d`). Due to the rolling-window definitions, **early rows contained null values** until sufficient history was available. For example, `ma20` was only non-null after the twentieth row, while `vol10` became valid after the tenth row. This behavior confirms the correct implementation of time-dependent feature calculations.

### Feature Coverage and Validation

A direct SQL query validated the presence of computed indicators:

* **Total rows processed:** 30
* **Non-null `ma20` values:** 11
* **Non-null `vol10` values:** 21

These results are consistent with the rolling-window logic. The first 19 rows cannot yield a 20-day moving average, and the first 9 rows cannot yield a 10-day volatility value. This demonstrates the pipeline’s reliability in handling incomplete windows while still maintaining consistency for later rows.

### Sample Output Snapshot

A sample extract from the `features` table is shown below, covering the ten most recent rows:

| date       | close | ma3    | ma5   | ma20   | vol10 | ret1d   |
| ---------- | ----- | ------ | ----- | ------ | ----- | ------- |
| 2022-02-11 | 131   | 130.00 | 128.6 | 120.65 | 3.72  | 0.0091  |
| 2022-02-10 | 130   | 128.67 | 127.4 | 119.65 | 3.44  | 0.0078  |
| 2022-02-09 | 129   | 127.33 | 126.2 | 118.65 | 3.27  | 0.0157  |
| 2022-02-08 | 127   | 126.00 | 125.0 | 117.6  | 3.06  | 0.0079  |
| 2022-02-07 | 126   | 125.00 | 123.8 | 116.5  | 3.03  | 0.0080  |
| 2022-02-04 | 125   | 124.00 | 122.6 | 115.4  | 2.99  | 0.0081  |
| 2022-02-03 | 124   | 122.67 | 121.8 | 114.45 | 2.95  | 0.0081  |
| 2022-02-02 | 123   | 121.33 | 120.8 | 113.45 | 3.29  | 0.0165  |
| 2022-02-01 | 121   | 120.67 | 119.8 | 112.45 | 3.06  | 0.0083  |
| 2022-01-31 | 120   | 120.00 | 119.0 | 111.45 | 3.03  | -0.0083 |

This table confirms that the moving averages and volatility were populated correctly, with expected gaps in early rows due to insufficient history.

### Execution Monitoring and Logs

Screenshots captured from the Airflow **Graph View** and **Task Logs** confirm that both ingestion and transformation tasks completed successfully (green state). Log outputs also included runtime metrics such as row counts and task execution time, which remained minimal for this dataset (well under one second per task). These metrics will provide a baseline for scalability analysis in future extensions.

### Discussion of Rolling-Window Behavior

The evaluation highlights the importance of dataset length relative to the window sizes. Shorter datasets produce nulls in early feature columns until enough data points accumulate. In practice, this is expected and does not represent a pipeline error. Instead, it demonstrates the **correct functioning of time-series feature engineering**, where historical context is essential. With larger real-world stock datasets (thousands of rows), such warm-up periods become negligible relative to the overall dataset.




# Batch Stock ML – Dockerized Batch Pipeline

A minimal, containerized batch pipeline for stock-market ML feature engineering.
**Stack:** Docker Compose, Apache Airflow, PostgreSQL, Python (pandas/SQLAlchemy).

* Ingests synthetic OHLCV data to `raw_stocks`
* Computes `ma3`, `ma5`, `ma20`, `vol10`, `ret1d`
* Writes curated features to `features`

---

## 1) Prerequisites

* **Docker Desktop** with **WSL 2 backend** enabled on Windows (recommended). ([Microsoft Learn][1], [Docker Documentation][2])
* **Docker Compose V2** (bundled with Docker Desktop).
* \~4 GB RAM free and virtualization enabled (common WSL2 requirement). ([NUSites][3])

> Tip: Airflow’s official Docker quickstart is great for local learning; don’t treat the sample Compose file as production-hardening. ([Apache Airflow][4])

---

## 2) Repository Layout

```
batch-stock-ml-pipeline/
├─ docker-compose.yml
├─ airflow/
│  ├─ dags/
│  │  └─ batch_stock_pipeline.py
│  ├─ logs/
│  ├─ plugins/
│  └─ requirements.txt
├─ scripts/
│  ├─ ingest.py
│  └─ transform.py
├─ README.md
└─ Repo_Link.txt
```

---

## 3) Configuration

* **Environment variables**: set secrets/config via env vars, not hardcoded.
  You can use a `.env` file (Docker Compose will read it). ([Docker Documentation][5])

Example `.env` (optional):

```
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRES_DB=stocks
AIRFLOW_ADMIN_USER=admin
AIRFLOW_ADMIN_PASSWORD=admin
```

> Best-practice note on env vars in Compose. ([Docker Documentation][5])

---

## 4) Install dependencies (inside Airflow)

`airflow/requirements.txt` (already included):

```
pandas
SQLAlchemy
psycopg2-binary
```

Airflow installs these at container start (via mounted requirements).
`pandas.to_sql` relies on SQLAlchemy + the relevant DB driver (psycopg2 for Postgres). ([Pandas][6])

---

## 5) Bring the stack up

```bash
# from the repo root
docker compose up -d --build
```

* Airflow Web UI: [http://127.0.0.1:8080](http://127.0.0.1:8080)
  Login: `admin` / `admin` (or values from your `.env`)

Airflow in Docker quickstart references: ([Apache Airflow][4])

---

## 6) Run the pipeline

### 6.1 Enable & trigger the DAG (UI)

1. Open Airflow → find **`batch_stock_pipeline`**
2. Turn the toggle **ON**
3. Click **▶ Trigger**
4. Watch **Graph** → each task turns **green**

### 6.2 Or trigger via CLI

```bash
docker compose exec airflow airflow dags trigger batch_stock_pipeline
```

---

## 7) Validate results in Postgres

Connect into the Postgres service and run SQL:

```bash
# one-off SQL:
docker compose exec postgres \
  psql -U user -d stocks -c "SELECT COUNT(*) FROM raw_stocks;"

docker compose exec postgres \
  psql -U user -d stocks -c \
"SELECT date, close, ma3, ma5, ma20, vol10, ret1d
 FROM features ORDER BY date DESC LIMIT 10;"
```

* `psql` is the official CLI for PostgreSQL. ([PostgreSQL][7])

> More `psql` basics from the official manual & tutorial. ([PostgreSQL][8])

---

## 8) What the code does (quick)

* **`scripts/ingest.py`**: builds \~30 business-day OHLCV rows and writes `raw_stocks` via `pandas.DataFrame.to_sql(..., if_exists="replace")`. ([Pandas][6])
* **`scripts/transform.py`**: reads `raw_stocks`, asserts quality (non-null dates, ascending order, non-negative volume), computes rolling features with `pandas.DataFrame.rolling(...)`, writes to `features`.
* **`airflow/dags/batch_stock_pipeline.py`**: two-task DAG (ingest → transform), `@daily`, `catchup=False`.
* **`docker-compose.yml`**: brings up Airflow + Postgres, mounts DAGs/scripts/requirements for live editing. (Compose services/volumes networking and lifecycle.) ([Apache Airflow][4])

---

## 9) Common commands

```bash
# view logs
docker compose logs airflow --tail=200
docker compose logs postgres --tail=100

# restart a service after code changes (forces module reloads)
docker compose restart airflow

# rebuild after changing dependencies
docker compose up -d --build

# stop & remove containers (keeps volumes)
docker compose down
```

Docker Desktop + WSL2 setup guidance (Windows): ([Microsoft Learn][1], [Docker Documentation][2])

---

## 10) Troubleshooting

**Airflow UI not loading?**

* Check port mapping (`8080:8080`) is free; see `docker ps`.
* `docker compose logs airflow` to spot import errors or missing deps.
  (Install/confirm requirements; rebuild if needed.) ([Apache Airflow][4])

**DAG can’t import `ingest`/`transform`?**

* Ensure the DAG adds scripts to `PYTHONPATH`:

  ```python
  import sys; sys.path.append("/opt/airflow/scripts")
  ```

**`psql` errors or can’t connect?**

* Ensure DB is up: `docker ps` should show the Postgres service on `5432`.
* Re-run with correct creds from `.env`. See psql reference. ([PostgreSQL][7])

**`to_sql` fails (driver not found)?**

* Ensure `psycopg2-binary` is installed; rebuild the Airflow container.
  (Driver requirement is documented in `to_sql`.) ([Pandas][6])

---

## 11) Extending & scaling

* Swap **pandas → Spark** for larger data; keep orchestration/storage the same (Airflow can run heterogeneous tasks). ([Apache Airflow][4])
* Harden configs with `.env` and secrets management; avoid hardcoding credentials. ([Docker Documentation][5])


