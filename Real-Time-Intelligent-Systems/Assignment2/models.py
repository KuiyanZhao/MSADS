"""models.py
Core models and interfaces.
Requirements:
- MarketDataPoint: frozen dataclass with (timestamp, symbol, price)
- Strategy: abstract base class with generate_signals(tick) -> list
Complexity note:
- Storing N MarketDataPoint objects in a Python list is O(N) space.
  (There is per-object overhead in Python; Big-O focuses on growth rate.)
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass(frozen=True)
class MarketDataPoint:
    timestamp: datetime
    symbol: str
    price: float

@dataclass(frozen=True)
class Signal:
    """A simple trading signal emitted by a Strategy."""
    timestamp: datetime
    symbol: str
    action: str  # "BUY" or "SELL"
    price: float
    moving_average: float
    strategy: str

class Strategy(ABC):
    """Strategy interface.
    Each call consumes one MarketDataPoint (tick) and returns zero or more signals.
    """
    @abstractmethod
    def generate_signals(self, tick: MarketDataPoint) -> List[Signal]:
        raise NotImplementedError
    @property
    def name(self) -> str:
        return self.__class__.__name__
