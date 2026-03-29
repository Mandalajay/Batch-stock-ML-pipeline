#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text

DB_URL = os.getenv(
    "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN",
    os.getenv("DATABASE_URL", "postgresql+psycopg2://user:pass@postgres:5432/stocks")
)

SQL = """
CREATE TABLE IF NOT EXISTS features_gold (
  symbol  TEXT NOT NULL,
  dt      DATE NOT NULL,
  ma3     NUMERIC,
  ma5     NUMERIC,
  ma20    NUMERIC,
  vol10   NUMERIC,
  ret1d   NUMERIC,
  PRIMARY KEY (symbol, dt)
);

WITH feats AS (
  SELECT
    symbol,
    dt,
    AVG(close) OVER (PARTITION BY symbol ORDER BY dt ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)  AS ma3,
    AVG(close) OVER (PARTITION BY symbol ORDER BY dt ROWS BETWEEN 4 PRECEDING AND CURRENT ROW)  AS ma5,
    AVG(close) OVER (PARTITION BY symbol ORDER BY dt ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS ma20,
    AVG(volume::numeric) OVER (PARTITION BY symbol ORDER BY dt ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) AS vol10,
    (close - LAG(close) OVER (PARTITION BY symbol ORDER BY dt))
      / NULLIF(LAG(close) OVER (PARTITION BY symbol ORDER BY dt), 0) AS ret1d
  FROM price_silver
)
INSERT INTO features_gold (symbol, dt, ma3, ma5, ma20, vol10, ret1d)
SELECT symbol, dt, ma3, ma5, ma20, vol10, ret1d
FROM feats
ON CONFLICT (symbol, dt) DO UPDATE
SET ma3 = EXCLUDED.ma3,
    ma5 = EXCLUDED.ma5,
    ma20 = EXCLUDED.ma20,
    vol10 = EXCLUDED.vol10,
    ret1d = EXCLUDED.ret1d;
"""

def compute_features():
    engine = create_engine(DB_URL, pool_pre_ping=True)
    with engine.begin() as conn:
        conn.execute(text(SQL))
    print("[transform_features] features_gold updated")
    return "ok"

if __name__ == "__main__":
    print(compute_features())
