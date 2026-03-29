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

WITH cleaned AS (
  SELECT DISTINCT ON (symbol, dt)
         symbol::text AS symbol,
         dt::date     AS dt,
         open::numeric  AS open,
         high::numeric  AS high,
         low::numeric   AS low,
         close::numeric AS close,
         GREATEST(0, COALESCE(volume,0))::bigint AS volume
  FROM bronze_price_raw
  WHERE symbol IS NOT NULL
    AND dt     IS NOT NULL
    AND open   IS NOT NULL
    AND high   IS NOT NULL
    AND low    IS NOT NULL
    AND close  IS NOT NULL
    AND volume IS NOT NULL
  ORDER BY symbol, dt, dt DESC
)
INSERT INTO price_silver (symbol, dt, open, high, low, close, volume)
SELECT c.symbol, c.dt, c.open, c.high, c.low, c.close, c.volume
FROM cleaned c
ON CONFLICT (symbol, dt) DO UPDATE
SET open   = EXCLUDED.open,
    high   = EXCLUDED.high,
    low    = EXCLUDED.low,
    close  = EXCLUDED.close,
    volume = EXCLUDED.volume;
