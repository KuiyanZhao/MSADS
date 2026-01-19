"""generate_sample_data.py
Generate a synthetic market_data.csv (timestamp, symbol, price) for local testing.
"""

from __future__ import annotations
import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List


def generate_prices(n: int, start: float, sigma: float, rng: random.Random) -> List[float]:
    """Simple random walk, clipped to stay positive."""
    prices: List[float] = []
    price = start
    for _ in range(n):
        price += rng.gauss(0.0, sigma)
        if price <= 0:
            price = start
        prices.append(price)
    return prices


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate a synthetic market_data.csv')
    parser.add_argument('--out', type=str, default='market_data.csv')
    parser.add_argument('--n', type=int, default=100000)
    parser.add_argument('--symbols', nargs='+', default=['AAPL'])
    parser.add_argument('--start-price', type=float, default=100.0)
    parser.add_argument('--sigma', type=float, default=1.0)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--start-time', type=str, default=None, help='ISO timestamp; default now()')
    parser.add_argument('--delta-seconds', type=int, default=1, help='Time step between rows.')
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    symbols = args.symbols

    start_time = datetime.fromisoformat(args.start_time) if args.start_time else datetime.now()
    dt = timedelta(seconds=args.delta_seconds)

    # Interleave symbols roughly evenly.
    per_symbol = (args.n + len(symbols) - 1) // len(symbols)
    prices_by_symbol = {
        sym: generate_prices(per_symbol, args.start_price, args.sigma, rng)
        for sym in symbols
    }

    with out_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'symbol', 'price'])

        t = start_time
        i_by_symbol = {sym: 0 for sym in symbols}
        written = 0
        while written < args.n:
            for sym in symbols:
                if written >= args.n:
                    break
                idx = i_by_symbol[sym]
                if idx >= len(prices_by_symbol[sym]):
                    continue
                writer.writerow([t.isoformat(sep=' '), sym, f"{prices_by_symbol[sym][idx]:.6f}"])
                i_by_symbol[sym] = idx + 1
                t += dt
                written += 1

    print(f'Wrote {args.n} rows to {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
