"""profiler.py
Runtime and memory measurement utilities.
This module always uses:
- timeit (stdlib)
- cProfile + pstats (stdlib)
- tracemalloc (stdlib) to capture peak memory
"""

from __future__ import annotations
import cProfile
import pstats
import timeit
import tracemalloc
from dataclasses import dataclass
from io import StringIO
from typing import Callable, Dict, Iterable, List, Tuple
from models import MarketDataPoint, Strategy


@dataclass(frozen=True)
class ProfileResult:
    strategy: str
    n_ticks: int
    runtime_seconds: float
    peak_memory_bytes: int
    cprofile_top: List[Tuple[str, int, float, float]]


def run_strategy(strategy: Strategy, ticks: Iterable[MarketDataPoint]) -> int:
    """Run a strategy over ticks and return number of signals emitted."""
    signals_count = 0
    for tick in ticks:
        signals_count += len(strategy.generate_signals(tick))
    return signals_count


def measure_peak_memory_bytes(fn: Callable[[], None]) -> int:
    """Measure peak memory using tracemalloc.
    This measures allocations tracked by Python (not total RSS), but is consistent for comparing
    strategies that differ in Python object allocations.
    """
    tracemalloc.start()
    try:
        fn()
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return peak


def timeit_seconds(fn: Callable[[], None], repeat: int = 5, number: int = 1) -> float:
    """Return the best observed runtime over `repeat` runs."""
    timer = timeit.Timer(fn)
    runs = timer.repeat(repeat=repeat, number=number)
    return min(runs) / number


def cprofile_top(fn: Callable[[], None], sort_by: str = "tottime", limit: int = 15) -> List[Tuple[str, int, float, float]]:
    """Run cProfile and return top functions.
    Returns tuples: (function, calls, total_time, cumulative_time)
    """
    pr = cProfile.Profile()
    pr.enable()
    fn()
    pr.disable()

    s = StringIO()
    ps = pstats.Stats(pr, stream=s).strip_dirs().sort_stats(sort_by)

    rows: List[Tuple[str, int, float, float]] = []
    for func, stat in list(ps.stats.items()):
        cc, nc, tt, ct, _ = stat
        rows.append((pstats.func_std_string(func), nc, tt, ct))

    # Sort in python to ensure deterministic ordering
    if sort_by == "tottime":
        rows.sort(key=lambda r: r[2], reverse=True)
    else:
        rows.sort(key=lambda r: r[3], reverse=True)

    return rows[:limit]


def profile_strategy(
    strategy_factory: Callable[[], Strategy],
    ticks: List[MarketDataPoint],
    repeat: int = 3,
) -> ProfileResult:
    """Measure runtime + memory + cProfile hotspots for a strategy."""

    def run_once() -> None:
        strat = strategy_factory()
        run_strategy(strat, ticks)

    runtime = timeit_seconds(run_once, repeat=repeat, number=1)
    peak_mem = measure_peak_memory_bytes(run_once)
    top = cprofile_top(run_once, sort_by="tottime", limit=15)

    return ProfileResult(
        strategy=strategy_factory().__class__.__name__,
        n_ticks=len(ticks),
        runtime_seconds=runtime,
        peak_memory_bytes=peak_mem,
        cprofile_top=top,
    )


def profile_multiple(
    strategy_factories: Dict[str, Callable[[], Strategy]],
    ticks: List[MarketDataPoint],
    repeat: int = 3,
) -> List[ProfileResult]:
    """Profile multiple strategies on the same ticks."""
    results: List[ProfileResult] = []
    for name, factory in strategy_factories.items():
        res = profile_strategy(factory, ticks, repeat=repeat)
        # Overwrite strategy field with provided name
        res = ProfileResult(
            strategy=name,
            n_ticks=res.n_ticks,
            runtime_seconds=res.runtime_seconds,
            peak_memory_bytes=res.peak_memory_bytes,
            cprofile_top=res.cprofile_top,
        )
        results.append(res)
    return results
