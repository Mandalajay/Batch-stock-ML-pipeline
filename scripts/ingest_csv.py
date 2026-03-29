import os
import pandas as pd
from sqlalchemy import create_engine

DB_URL = os.getenv(
    "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN",
    os.getenv("DATABASE_URL", "postgresql+psycopg2://user:pass@postgres:5432/stocks"),
)

def load_csv_to_bronze(path: str) -> int:
    """
    Load a CSV with columns: date, open, high, low, close, volume, symbol
    Writes to bronze_price_raw with proper types.
    """
    df = pd.read_csv(path)
    df.columns = [c.lower() for c in df.columns]

    # normalize names
    if "dt" not in df.columns:
        if "date" in df.columns:
            df["dt"] = pd.to_datetime(df["date"]).dt.date
        else:
            raise ValueError("CSV must contain a 'date' column")

    out = pd.DataFrame({
        "symbol": df["symbol"].astype(str),
        "dt": df["dt"],
        "open": df["open"].astype(float),
        "high": df["high"].astype(float),
        "low": df["low"].astype(float),
        "close": df["close"].astype(float),
        "volume": df["volume"].fillna(0).astype("Int64"),
    })

    engine = create_engine(DB_URL)
    with engine.begin() as conn:
        out.to_sql("bronze_price_raw", conn, if_exists="append", index=False)

    return len(out)
