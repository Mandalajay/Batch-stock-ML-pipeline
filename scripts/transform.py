import pandas as pd
from sqlalchemy import create_engine

def run():
    engine = create_engine("postgresql://user:pass@postgres:5432/stocks")
    df = pd.read_sql("SELECT * FROM raw_stocks ORDER BY date", engine)

    # Simple features you already have
    df["ret1d"] = df["close"].pct_change()
    df["ma3"]   = df["close"].rolling(3).mean()

    # Extra features for Phase 3
    df["ma5"]   = df["close"].rolling(5).mean()
    df["ma20"]  = df["close"].rolling(20).mean()
    df["vol10"] = df["close"].rolling(10).std()            # 10-day volatility (std dev)

    # Data quality checks (basic)
    assert df["date"].notna().all(), "Null dates detected"
    assert (df["volume"] >= 0).all(), "Negative volume found"
    assert df["date"].is_monotonic_increasing, "Dates not sorted ascending"

    df.to_sql("features", engine, if_exists="replace", index=False)
