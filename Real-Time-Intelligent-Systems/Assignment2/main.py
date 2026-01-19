"""main.py
Orchestrates ingestion, strategy execution, profiling, and report generation.
This will:
- Read ticks from CSV using data_loader.read_market_data
- Profile strategies on 1k / 10k / 100k ticks
- Write plots and complexity_report.md
"""
import argparse
from collections import Counter
from pathlib import Path
from data_loader import read_market_data
from profiler import profile_multiple
from reporting import generate_complexity_report
from strategies import (
    NaiveMovingAverageStrategy,
    OptimizedMovingAverageStrategy,
    WindowedMovingAverageStrategy,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Runtime & space complexity profiling for moving-average strategies."
    )
    parser.add_argument(
        "--csv", type=str, default="market_data.csv", help="Path to market data CSV."
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=10,
        help="Window size k for WindowedMovingAverageStrategy.",
    )
    parser.add_argument(
        "--out-dir", type=str, default=".", help="Output directory for report and plots."
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=3,
        help="Number of repeats for timeit (best-of used).",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    ticks = read_market_data(csv_path)
    if not ticks:
        raise SystemExit("No ticks loaded from CSV.")

    # Dataset characteristics
    symbol_counts = Counter(t.symbol for t in ticks)
    symbols = sorted(symbol_counts.keys())

    sizes = [1000, 10_000, 100_000]
    max_available = len(ticks)
    sizes = [n for n in sizes if n <= max_available]
    if not sizes:
        sizes = [max_available]  # Always do at least one size.

    factories = {
        "NaiveMovingAverageStrategy": lambda: NaiveMovingAverageStrategy(),
        f"WindowedMovingAverageStrategy(k={args.window_size})": lambda: WindowedMovingAverageStrategy(
            window_size=args.window_size
        ),
        "OptimizedMovingAverageStrategy": lambda: OptimizedMovingAverageStrategy(),
    }

    all_results = []
    for n in sizes:
        subset = ticks[:n]

        # Naive is significantly slower; keep repeats low to avoid very long runs.
        all_results.extend(
            profile_multiple(
                {"NaiveMovingAverageStrategy": factories["NaiveMovingAverageStrategy"]},
                subset,
                repeat=1,
            )
        )

        # Profile the remaining strategies with the requested repeat count.
        all_results.extend(
            profile_multiple(
                {
                    k: v
                    for k, v in factories.items()
                    if not k.startswith("NaiveMovingAverageStrategy")
                },
                subset,
                repeat=args.repeat,
            )
        )

    out_dir = Path(args.out_dir)
    md_path = generate_complexity_report(
        all_results,
        out_dir,
        dataset_total_ticks=len(ticks),
        symbols=symbols,
        symbol_counts=symbol_counts,
        window_size=args.window_size,
    )
    print(f"Wrote report: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
