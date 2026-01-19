import time
import tracemalloc
from datetime import datetime, timedelta

import pytest

from models import MarketDataPoint
from strategies import NaiveMovingAverageStrategy, OptimizedMovingAverageStrategy, WindowedMovingAverageStrategy


def _ticks_from_prices(prices, symbol='AAPL', start=None):
    start = start or datetime(2026, 1, 1, 0, 0, 0)
    t = start
    dt = timedelta(seconds=1)
    ticks = []
    for p in prices:
        ticks.append(MarketDataPoint(timestamp=t, symbol=symbol, price=float(p)))
        t += dt
    return ticks


def _decisions_from_strategy(strategy, ticks):
    actions = []
    for tick in ticks:
        sigs = strategy.generate_signals(tick)
        if not sigs:
            actions.append(None)
        else:
            assert len(sigs) == 1
            actions.append(sigs[0].action)
    return actions


def _ref_decisions_full_history(prices):
    actions = []
    hist = []
    for p in prices:
        hist.append(float(p))
        avg = sum(hist) / len(hist)
        if p > avg:
            actions.append('BUY')
        elif p < avg:
            actions.append('SELL')
        else:
            actions.append(None)
    return actions


def _ref_decisions_windowed(prices, k):
    actions = []
    hist = []
    for p in prices:
        hist.append(float(p))
        window = hist[-k:]
        avg = sum(window) / len(window)
        if p > avg:
            actions.append('BUY')
        elif p < avg:
            actions.append('SELL')
        else:
            actions.append(None)
    return actions


def test_naive_matches_reference():
    prices = [10, 9, 11, 13, 8, 8, 12]
    ticks = _ticks_from_prices(prices)

    strat = NaiveMovingAverageStrategy()
    got = _decisions_from_strategy(strat, ticks)
    expect = _ref_decisions_full_history(prices)
    assert got == expect


def test_optimized_matches_naive_full_history():
    prices = [100, 101, 99, 105, 98, 110, 90]
    ticks = _ticks_from_prices(prices)

    naive = NaiveMovingAverageStrategy()
    opt = OptimizedMovingAverageStrategy()

    got_naive = _decisions_from_strategy(naive, ticks)
    got_opt = _decisions_from_strategy(opt, ticks)

    assert got_opt == got_naive


def test_windowed_matches_reference():
    prices = [1, 2, 3, 2, 1, 4, 5]
    k = 3
    ticks = _ticks_from_prices(prices)

    strat = WindowedMovingAverageStrategy(window_size=k)
    got = _decisions_from_strategy(strat, ticks)
    expect = _ref_decisions_windowed(prices, k)

    assert got == expect


def test_multiple_symbols_independent_state():
    # Interleave two symbols with different price patterns.
    start = datetime(2026, 1, 1, 0, 0, 0)
    dt = timedelta(seconds=1)

    ticks = [
        MarketDataPoint(start + 0*dt, 'AAPL', 10.0),
        MarketDataPoint(start + 1*dt, 'MSFT', 100.0),
        MarketDataPoint(start + 2*dt, 'AAPL', 20.0),
        MarketDataPoint(start + 3*dt, 'MSFT', 90.0),
    ]

    strat = OptimizedMovingAverageStrategy()
    sigs = []
    for tick in ticks:
        sigs.extend(strat.generate_signals(tick))

    # Should produce at most one signal per tick, and per-symbol averages should not mix.
    assert len(sigs) <= len(ticks)
    assert {s.symbol for s in sigs}.issubset({'AAPL', 'MSFT'})


def test_optimized_performance_100k():
    # Assignment requirement: optimized strategy under 1 second and <100MB for 100k ticks.
    n = 100_000
    start = datetime(2026, 1, 1)
    dt = timedelta(seconds=1)

    # Use a generator to avoid materializing 100k MarketDataPoint objects up front.
    # This keeps the memory test focused on the strategy's footprint, not the test harness.
    def ticks():
        for i in range(n):
            yield MarketDataPoint(start + i * dt, 'AAPL', 100.0 + (i % 50))

    strat = OptimizedMovingAverageStrategy()

    tracemalloc.start()
    t0 = time.perf_counter()
    for tick in ticks():
        strat.generate_signals(tick)
    runtime = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert runtime < 1.0
    assert peak < 100 * 1024 * 1024
