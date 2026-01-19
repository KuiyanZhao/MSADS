# Assignment 2

This assignment ingests market data from a CSV file and applies multiple moving-average trading strategies with different runtime and space complexities. It profiles runtime and peak memory allocations across input sizes (1k, 10k, 100k ticks) and generates a markdown report with plots.

## Files

- `data_loader.py` — CSV parsing (built-in `csv`) and `MarketDataPoint` creation.
- `models.py` — `MarketDataPoint` (frozen dataclass), `Signal` dataclass, `Strategy` base class.
- `strategies.py` — Naive/windowed/optimized moving-average strategies with Big-O annotations.
- `profiler.py` — `timeit` + `cProfile` + `tracemalloc` peak memory, returns structured metrics.
- `reporting.py` — plot generation and `complexity_report.md` creation.
- `main.py` — orchestrates ingestion → profiling → report generation.
- `generate_sample_data.py` — generates a synthetic `market_data.csv`.
- `tests/` — pytest unit tests.

## Setup

Python 3.10+.

```bash
pip install -r libs.txt
````

## Generate sample data

```bash
python generate_sample_data.py --out market_data.csv --n 100000 --symbols AAPL MSFT
```

## Run benchmarks and generate report

```bash
python main.py --csv market_data.csv --window-size 10 --out-dir .
```

Outputs:

* `complexity_report.md`
* `plots/runtime_vs_input_size.png`
* `plots/memory_vs_input_size.png`

## Run tests

```bash
pytest -q
```
