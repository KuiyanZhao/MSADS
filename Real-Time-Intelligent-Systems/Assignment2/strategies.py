"""strategies.py
Naive and optimized moving-average strategies.
A "moving average" strategy here emits:
- BUY  if current price > moving average
- SELL if current price < moving average
- No signal if equal
"""

from __future__ import annotations

from collections import deque
from typing import Deque, Dict, List

from models import MarketDataPoint, Signal, Strategy


def _decision(price: float, avg: float) -> str | None:
    """Return BUY/SELL decision based on price vs avg."""
    if price > avg:
        return "BUY"
    if price < avg:
        return "SELL"
    return None


class NaiveMovingAverageStrategy(Strategy):
    """Recompute moving average from scratch for every tick.
    Per tick (single symbol worst case):
    - Append price to history: amortized O(1)
    - Recompute average: sum(history) is O(n)
    => Time: O(n) per tick
    - Space: O(n) to store full history
    Total over N ticks (single symbol): O(N^2)
    """

    def __init__(self) -> None:
        # O(n) space overall as the list grows with ticks
        self._prices_by_symbol: Dict[str, List[float]] = {}

    def generate_signals(self, tick: MarketDataPoint) -> List[Signal]:
        prices = self._prices_by_symbol.setdefault(tick.symbol, [])
        prices.append(tick.price)  # amortized O(1)

        # O(n) time: sums over the entire history list
        avg = sum(prices) / len(prices)
        action = _decision(tick.price, avg)
        if action is None:
            return []
        return [
            Signal(
                timestamp=tick.timestamp,
                symbol=tick.symbol,
                action=action,
                price=tick.price,
                moving_average=avg,
                strategy=self.name,
            )
        ]


class WindowedMovingAverageStrategy(Strategy):
    """Fixed-size window moving average with O(1) updates.
    Per tick:
    - Maintain a deque(maxlen=k) and a running sum.
    - Update running sum by adding new price and (if full) subtracting the ejected old price.
    Complexity per tick:
    - Time: O(1)
    - Space: O(k) per symbol (window size)
    """

    def __init__(self, window_size: int = 10) -> None:
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        self.window_size = window_size
        self._windows: Dict[str, Deque[float]] = {}
        self._sums: Dict[str, float] = {}

    def generate_signals(self, tick: MarketDataPoint) -> List[Signal]:
        window = self._windows.get(tick.symbol)
        if window is None:
            window = deque(maxlen=self.window_size)
            self._windows[tick.symbol] = window
            self._sums[tick.symbol] = 0.0

        running_sum = self._sums[tick.symbol]

        # O(1): if full, I can see which element will be removed
        if len(window) == window.maxlen:
            running_sum -= window[0]

        window.append(tick.price)  # O(1)
        running_sum += tick.price  # O(1)
        self._sums[tick.symbol] = running_sum

        avg = running_sum / len(window)  # O(1)

        action = _decision(tick.price, avg)
        if action is None:
            return []
        return [
            Signal(
                timestamp=tick.timestamp,
                symbol=tick.symbol,
                action=action,
                price=tick.price,
                moving_average=avg,
                strategy=self.name,
            )
        ]


class OptimizedMovingAverageStrategy(Strategy):
    """Refactor of the naive strategy to reduce time AND space.
    This computes the *cumulative* moving average (mean of all observed prices for a symbol)
    incrementally.
    Per tick:
    - Update running_sum and count: O(1)
    - Compute avg = running_sum / count: O(1)
    Complexity:
    - Time: O(1) per tick
    - Space: O(1) per symbol (running_sum + count)
     """

    def __init__(self) -> None:
        self._running_sum: Dict[str, float] = {}
        self._count: Dict[str, int] = {}

    def generate_signals(self, tick: MarketDataPoint) -> List[Signal]:
        s = self._running_sum.get(tick.symbol, 0.0)
        c = self._count.get(tick.symbol, 0)

        # O(1) updates
        s += tick.price
        c += 1
        self._running_sum[tick.symbol] = s
        self._count[tick.symbol] = c

        avg = s / c  # O(1)

        action = _decision(tick.price, avg)
        if action is None:
            return []
        return [
            Signal(
                timestamp=tick.timestamp,
                symbol=tick.symbol,
                action=action,
                price=tick.price,
                moving_average=avg,
                strategy=self.name,
            )
        ]
