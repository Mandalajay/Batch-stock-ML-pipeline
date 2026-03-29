-- schemas
CREATE SCHEMA IF NOT EXISTS public;

-- Bronze
CREATE TABLE IF NOT EXISTS bronze_price_raw (
  symbol  TEXT NOT NULL,
  dt      DATE NOT NULL,
  open    NUMERIC,
  high    NUMERIC,
  low     NUMERIC,
  close   NUMERIC,
  volume  BIGINT
);
CREATE INDEX IF NOT EXISTS idx_bronze_symbol_dt ON bronze_price_raw(symbol, dt);

-- Silver
CREATE TABLE IF NOT EXISTS price_silver (
  symbol  TEXT NOT NULL,
  dt      DATE NOT NULL,
  open    NUMERIC NOT NULL,
  high    NUMERIC NOT NULL,
  low     NUMERIC NOT NULL,
  close   NUMERIC NOT NULL,
  volume  BIGINT   NOT NULL CHECK (volume >= 0),
  PRIMARY KEY (symbol, dt)
);

-- Gold
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

-- optional view
CREATE OR REPLACE VIEW latest_features AS
SELECT *
FROM features_gold fg
WHERE (fg.symbol, fg.dt) IN (
  SELECT symbol, max(dt) FROM features_gold GROUP BY symbol
);
