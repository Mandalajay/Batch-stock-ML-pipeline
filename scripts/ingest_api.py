import os
from datetime import datetime
import time
import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine


DB_URL = os.getenv(
    "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN",
    os.getenv("DATABASE_URL", "postgresql+psycopg2://user:pass@postgres:5432/stocks"),
)


def fetch_to_bronze(symbol: str, start: str, end: str | None = None, interval: str = "1d", retries: int = 3, delay: int = 5) -> int:
    """
    Download OHLCV via yfinance and append to bronze_price_raw.
    yfinance returns either 'Date' or 'Datetime' index depending on interval.
    Fixed to handle MultiIndex columns from newer yfinance versions.
    """
    end = end or datetime.utcnow().strftime("%Y-%m-%d")
    last_err = None
    
    for attempt in range(1, retries + 1):
        try:
            # Use multi_level_index=False to prevent MultiIndex columns for single ticker
            data = yf.download(
                symbol, 
                start=start, 
                end=end, 
                interval=interval, 
                auto_adjust=False, 
                progress=False,
                multi_level_index=False
            )
            
            if data is None or data.empty:
                raise ValueError("No data returned from yfinance")

            # Reset index to convert Date/Datetime index to column
            df = data.reset_index()
            
            # Handle column names - check if MultiIndex still exists (fallback)
            new_columns = []
            for col in df.columns:
                if isinstance(col, tuple):
                    # For MultiIndex, take the first level (the metric name)
                    new_columns.append(col[0].lower())
                else:
                    # For regular string columns
                    new_columns.append(str(col).lower())
            
            df.columns = new_columns

            # Date column can be 'date' or 'datetime' based on interval
            if "date" in df.columns:
                dt_series = pd.to_datetime(df["date"]).dt.date
            elif "datetime" in df.columns:
                dt_series = pd.to_datetime(df["datetime"]).dt.date
            else:
                raise ValueError("Expected 'date' or 'datetime' column from yfinance")

            # Create standardized output DataFrame
            out = pd.DataFrame({
                "symbol": symbol,
                "dt": dt_series,
                "open": df["open"].astype(float),
                "high": df["high"].astype(float),
                "low": df["low"].astype(float),
                "close": df["close"].astype(float),
                "volume": df.get("volume", pd.Series([0]*len(df))).fillna(0).astype("Int64"),
            })

            # Insert into database
            engine = create_engine(DB_URL)
            with engine.begin() as conn:
                out.to_sql("bronze_price_raw", conn, if_exists="append", index=False)
            
            print(f"[ingest_api] Successfully inserted {len(out)} rows for {symbol}")
            return len(out)

        except Exception as e:
            last_err = e
            print(f"[ingest_api] Attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(delay)

    raise RuntimeError(f"[ingest_api] Failed for {symbol} {start}..{end}. Last error: {last_err}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python ingest_api.py <symbol> <start_date> [end_date]")
        print("Example: python ingest_api.py AAPL 2022-01-01 2022-02-11")
        sys.exit(1)
    
    sym = sys.argv[1]
    start = sys.argv[2]
    end = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        n = fetch_to_bronze(sym, start, end)
        print(f"Successfully inserted {n} rows into bronze_price_raw for {sym} from {start} to {end}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
