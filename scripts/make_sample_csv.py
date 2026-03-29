#!/usr/bin/env python3
"""
Generate large synthetic daily OHLCV CSV(s) efficiently.

Examples:
  python /opt/airflow/scripts/make_sample_csv.py --rows 1000000 \
    --outfile /opt/airflow/landing/files/synthetic_1m.csv

  # split into parts of 200k rows
  python /opt/airflow/scripts/make_sample_csv.py --rows 1000000 \
    --outfile /opt/airflow/landing/files/synthetic_1m.csv --split-rows 200000
"""
import argparse, csv, math, os
from typing import List, Iterator
import numpy as np
import pandas as pd

def business_days(start: str, days: int) -> List[str]:
    return [d.date().isoformat() for d in pd.bdate_range(start=start, periods=days)]

def synth_symbol_series(days: int, start_price=100.0, drift=0.0002, vol=0.02, seed: int | None=None):
    rs = np.random.RandomState(seed) if seed is not None else np.random
    pct = rs.normal(drift, vol, size=days)
    close = np.empty(days)
    close[0] = start_price * (1 + pct[0])
    for i in range(1, days):
        close[i] = close[i-1] * (1 + pct[i])

    gap = rs.normal(0.0, 0.002, size=days)
    openp = np.empty_like(close)
    openp[0] = close[0] / (1.0 + pct[0])
    for i in range(1, days):
        openp[i] = close[i-1] * (1.0 + gap[i])

    spread = np.abs(rs.normal(0.003, 0.003, size=days))
    high = np.maximum(openp, close) * (1.0 + spread)
    low = np.minimum(openp, close) * (1.0 - spread)
    volume = rs.randint(500_000, 10_000_000, size=days, dtype=np.int64)
    return {"open": openp, "high": high, "low": low, "close": close, "volume": volume}

def file_writer(outpath: str, header: list[str]) -> Iterator[csv.writer]:
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    f = open(outpath, "w", newline="")
    w = csv.writer(f); w.writerow(header)
    try:
        yield w
    finally:
        f.close()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--outfile", default="/opt/airflow/landing/files/synthetic.csv")
    p.add_argument("--rows", type=int, default=None)
    p.add_argument("--num-symbols", type=int, default=200)
    p.add_argument("--days", type=int, default=5000)
    p.add_argument("--start-date", default="2000-01-03")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--split-rows", type=int, default=0)
    a = p.parse_args()

    rs = np.random.RandomState(a.seed)
    if a.rows and a.rows > 0:
        days = 5000
        num_symbols = math.ceil(a.rows / days)
    else:
        num_symbols, days = a.num_symbols, a.days

    dates = business_days(a.start_date, days)
    header = ["date","open","high","low","close","volume","symbol"]
    total = part_rows = part_idx = 0

    def next_out(idx): 
        if a.split_rows and a.split_rows > 0:
            base, ext = os.path.splitext(a.outfile)
            return f"{base}.part{idx:02d}{ext or '.csv'}"
        return a.outfile

    outpath = next_out(part_idx)
    cm = file_writer(outpath, header); w = next(cm)
    try:
        for s in range(num_symbols):
            sym = f"SYM{s+1:04d}"
            series = synth_symbol_series(days, start_price=100 + 0.5*s,
                                         seed=int(rs.randint(0, 2**31 - 1)))
            for i, d in enumerate(dates):
                w.writerow([d,
                            f"{series['open'][i]:.2f}",
                            f"{series['high'][i]:.2f}",
                            f"{series['low'][i]:.2f}",
                            f"{series['close'][i]:.2f}",
                            int(series['volume'][i]),
                            sym])
                total += 1; part_rows += 1
                if a.split_rows and part_rows >= a.split_rows:
                    cm.close(); part_rows = 0; part_idx += 1
                    outpath = next_out(part_idx)
                    cm = file_writer(outpath, header); w = next(cm)
        print(f"Wrote ~{total} rows")
    finally:
        try: cm.close()
        except: pass

if __name__ == "__main__":
    main()
