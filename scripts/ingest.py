import pandas as pd
from sqlalchemy import create_engine

def run():
    df = pd.DataFrame({
        "date": pd.date_range("2022-01-01", periods=30, freq="B"),  # ← was 10
        "open":  [100,102,101,103,104,105,104,106,107,108,
                  109,110,112,111,113,115,114,116,117,118,
                  119,121,120,122,123,124,125,126,127,128],
        "close": [102,101,103,104,106,104,105,108,110,111,
                  112,113,114,112,115,116,117,118,119,121,
                  120,121,123,124,125,126,127,129,130,131],
        "volume":[1000,1200,1100,1300,1500,1400,1600,1700,1800,1900,
                  1950,2000,2050,2100,2150,2200,2250,2300,2350,2400,
                  2450,2500,2550,2600,2650,2700,2750,2800,2850,2900]
    })
    engine = create_engine("postgresql://user:pass@postgres:5432/stocks")
    df.to_sql("raw_stocks", engine, if_exists="replace", index=False)
