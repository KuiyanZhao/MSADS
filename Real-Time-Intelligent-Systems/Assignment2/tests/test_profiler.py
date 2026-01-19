from datetime import datetime, timedelta

from models import MarketDataPoint
from profiler import profile_strategy
from strategies import OptimizedMovingAverageStrategy


def test_profiler_outputs_hotspots_and_peak_memory():
    t0 = datetime(2026, 1, 1, 0, 0, 0)
    dt = timedelta(seconds=1)

    ticks = [
        MarketDataPoint(t0 + i * dt, "AAPL", 100.0 + i * 0.01)
        for i in range(2000)
    ]

    res = profile_strategy(lambda: OptimizedMovingAverageStrategy(), ticks, repeat=1)

    # Basic sanity checks: profiler captured metrics and hotspots.
    assert res.runtime_seconds > 0
    assert res.peak_memory_bytes >= 0
    assert res.cprofile_top, "Expected non-empty cProfile hotspot table"
