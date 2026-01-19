# Complexity Report

## Dataset characteristics

- Total ticks in CSV: **100,000**
- Symbols: **2** (AAPL, MSFT)
- Tick distribution across symbols: **approximately uniform** (max/min ≈ 50000/50000)
  - Counts: AAPL=50,000, MSFT=50,000
- Window size (k): **10**

## Strategies & theoretical complexity

- **NaiveMovingAverageStrategy**: recomputes `sum(history)` every tick. Time **O(n)** per tick, Space **O(n)**.
- **WindowedMovingAverageStrategy (k window)**: maintains deque + running sum. Time **O(1)** per tick, Space **O(k)**.
- **OptimizedMovingAverageStrategy**: running sum + count (cumulative mean). Time **O(1)** per tick, Space **O(1)** per symbol.

## Benchmarks

Measured with `timeit` (best of repeats) and `tracemalloc` peak allocations. See `profiler.py`.

### Input size: 1,000 ticks

| Strategy | Runtime (s) | Peak memory (MiB) |
|---|---:|---:|
| NaiveMovingAverageStrategy | 0.002029 | 0.012 |
| OptimizedMovingAverageStrategy | 0.001217 | 0.001 |
| WindowedMovingAverageStrategy(k=10) | 0.001302 | 0.003 |

### Input size: 10,000 ticks

| Strategy | Runtime (s) | Peak memory (MiB) |
|---|---:|---:|
| NaiveMovingAverageStrategy | 0.089468 | 0.116 |
| OptimizedMovingAverageStrategy | 0.013258 | 0.001 |
| WindowedMovingAverageStrategy(k=10) | 0.013616 | 0.003 |

### Input size: 100,000 ticks

| Strategy | Runtime (s) | Peak memory (MiB) |
|---|---:|---:|
| NaiveMovingAverageStrategy | 7.679972 | 1.224 |
| OptimizedMovingAverageStrategy | 0.126497 | 0.001 |
| WindowedMovingAverageStrategy(k=10) | 0.136667 | 0.003 |

## Scaling plots

![Runtime vs input size](plots/runtime_vs_input_size.png)

![Memory vs input size](plots/memory_vs_input_size.png)

## cProfile hotspots (top functions)

### NaiveMovingAverageStrategy @ 1,000 ticks
| Function | Calls | Total (s) | Cumulative (s) |
|---|---:|---:|---:|
| `strategies.py:40(generate_signals)` | 1000 | 0.001268 | 0.003167 |
| `{built-in method builtins.sum}` | 1000 | 0.000829 | 0.000829 |
| `<string>:2(__init__)` | 998 | 0.000679 | 0.000679 |
| `profiler.py:29(run_strategy)` | 1 | 0.000267 | 0.003483 |
| `{built-in method builtins.len}` | 2000 | 0.000113 | 0.000113 |

### WindowedMovingAverageStrategy(k=10) @ 1,000 ticks
| Function | Calls | Total (s) | Cumulative (s) |
|---|---:|---:|---:|
| `strategies.py:78(generate_signals)` | 1000 | 0.001511 | 0.002685 |
| `<string>:2(__init__)` | 998 | 0.000728 | 0.000728 |
| `profiler.py:29(run_strategy)` | 1 | 0.000287 | 0.003024 |
| `{built-in method builtins.len}` | 3000 | 0.000174 | 0.000174 |
| `{method 'append' of 'collections.deque' objects}` | 1000 | 0.000089 | 0.000089 |

### OptimizedMovingAverageStrategy @ 1,000 ticks
| Function | Calls | Total (s) | Cumulative (s) |
|---|---:|---:|---:|
| `strategies.py:128(generate_signals)` | 1000 | 0.001263 | 0.002277 |
| `<string>:2(__init__)` | 998 | 0.000719 | 0.000719 |
| `profiler.py:29(run_strategy)` | 1 | 0.000272 | 0.002600 |
| `{method 'get' of 'dict' objects}` | 2000 | 0.000160 | 0.000160 |
| `models.py:40(name)` | 998 | 0.000069 | 0.000069 |

### NaiveMovingAverageStrategy @ 10,000 ticks
| Function | Calls | Total (s) | Cumulative (s) |
|---|---:|---:|---:|
| `{built-in method builtins.sum}` | 10000 | 0.078084 | 0.078084 |
| `strategies.py:40(generate_signals)` | 10000 | 0.014518 | 0.104208 |
| `<string>:2(__init__)` | 9998 | 0.007380 | 0.007380 |
| `profiler.py:29(run_strategy)` | 1 | 0.003017 | 0.107860 |
| `{built-in method builtins.len}` | 20000 | 0.001406 | 0.001406 |

### WindowedMovingAverageStrategy(k=10) @ 10,000 ticks
| Function | Calls | Total (s) | Cumulative (s) |
|---|---:|---:|---:|
| `strategies.py:78(generate_signals)` | 10000 | 0.015473 | 0.028009 |
| `<string>:2(__init__)` | 9998 | 0.007850 | 0.007850 |
| `profiler.py:29(run_strategy)` | 1 | 0.002978 | 0.031550 |
| `{built-in method builtins.len}` | 30000 | 0.001764 | 0.001764 |
| `{method 'get' of 'dict' objects}` | 10000 | 0.000894 | 0.000894 |

### OptimizedMovingAverageStrategy @ 10,000 ticks
| Function | Calls | Total (s) | Cumulative (s) |
|---|---:|---:|---:|
| `strategies.py:128(generate_signals)` | 10000 | 0.012507 | 0.023230 |
| `<string>:2(__init__)` | 9998 | 0.007429 | 0.007429 |
| `profiler.py:29(run_strategy)` | 1 | 0.002863 | 0.026640 |
| `{method 'get' of 'dict' objects}` | 20000 | 0.001622 | 0.001622 |
| `strategies.py:17(_decision)` | 10000 | 0.000921 | 0.000921 |

### NaiveMovingAverageStrategy @ 100,000 ticks
| Function | Calls | Total (s) | Cumulative (s) |
|---|---:|---:|---:|
| `{built-in method builtins.sum}` | 100000 | 7.495986 | 7.495986 |
| `strategies.py:40(generate_signals)` | 100000 | 0.193947 | 7.829375 |
| `<string>:2(__init__)` | 99998 | 0.082345 | 0.082345 |
| `profiler.py:29(run_strategy)` | 1 | 0.039439 | 7.875240 |
| `{built-in method builtins.len}` | 200000 | 0.016362 | 0.016362 |

### WindowedMovingAverageStrategy(k=10) @ 100,000 ticks
| Function | Calls | Total (s) | Cumulative (s) |
|---|---:|---:|---:|
| `strategies.py:78(generate_signals)` | 100000 | 0.147603 | 0.265063 |
| `<string>:2(__init__)` | 99998 | 0.073512 | 0.073512 |
| `profiler.py:29(run_strategy)` | 1 | 0.028574 | 0.298876 |
| `{built-in method builtins.len}` | 300000 | 0.016786 | 0.016786 |
| `{method 'get' of 'dict' objects}` | 100000 | 0.008707 | 0.008707 |

### OptimizedMovingAverageStrategy @ 100,000 ticks
| Function | Calls | Total (s) | Cumulative (s) |
|---|---:|---:|---:|
| `strategies.py:128(generate_signals)` | 100000 | 0.116927 | 0.218328 |
| `<string>:2(__init__)` | 99998 | 0.072471 | 0.072471 |
| `profiler.py:29(run_strategy)` | 1 | 0.027697 | 0.251231 |
| `{method 'get' of 'dict' objects}` | 200000 | 0.015259 | 0.015259 |
| `models.py:40(name)` | 99998 | 0.007388 | 0.007388 |

## Narrative

The naive strategy scales poorly because each tick recomputes a full-history sum. The windowed strategy avoids full rescans by maintaining a fixed-size buffer and a running sum. The optimized strategy goes further by eliminating history storage entirely (cumulative mean), reducing both time and space, which should satisfy the <1s / <100MB target for 100k ticks on typical hardware.