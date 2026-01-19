"""
reporting.py
Markdown and plot generation.
Outputs:
- plots/runtime_vs_input_size.png
- plots/memory_vs_input_size.png
- complexity_report.md
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Mapping

import matplotlib.pyplot as plt

from profiler import ProfileResult


def _maybe_add_naive_extrapolation(results: List[ProfileResult], target_size: int) -> List[ProfileResult]:
    """If NaiveMovingAverageStrategy is missing for target_size, add an extrapolated point.

    The naive implementation is O(n) per tick and O(n^2) total over N ticks. If we have a measured
    runtime for a smaller base size, we can extrapolate:
        T(N) ≈ T(base) * (N/base)^2
    Space for naive is O(N) (stores full history), so we extrapolate:
        M(N) ≈ M(base) * (N/base)

    This is intentionally labeled as "extrapolated" in the strategy name.
    """
    if any(r.strategy == "NaiveMovingAverageStrategy" and r.n_ticks == target_size for r in results):
        return results

    naive = [r for r in results if r.strategy == "NaiveMovingAverageStrategy"]
    if not naive:
        return results

    base = max(naive, key=lambda r: r.n_ticks)
    if base.n_ticks <= 0 or base.n_ticks >= target_size:
        return results

    factor_time = (target_size / base.n_ticks) ** 2
    factor_mem = (target_size / base.n_ticks)

    est_runtime = base.runtime_seconds * factor_time
    est_mem = int(base.peak_memory_bytes * factor_mem)

    results = list(results)
    results.append(
        ProfileResult(
            strategy="NaiveMovingAverageStrategy (extrapolated)",
            n_ticks=target_size,
            runtime_seconds=est_runtime,
            peak_memory_bytes=est_mem,
            cprofile_top=[],
        )
    )
    return results


def _group_by_strategy(results: List[ProfileResult]) -> Dict[str, List[ProfileResult]]:
    grouped: Dict[str, List[ProfileResult]] = {}
    for r in results:
        grouped.setdefault(r.strategy, []).append(r)
    for lst in grouped.values():
        lst.sort(key=lambda x: x.n_ticks)
    return grouped


def plot_runtime_vs_input_size(results: List[ProfileResult], out_path: Path) -> None:
    grouped = _group_by_strategy(results)
    plt.figure()
    for strategy, lst in grouped.items():
        xs = [r.n_ticks for r in lst]
        ys = [r.runtime_seconds for r in lst]
        plt.plot(xs, ys, marker="o", label=strategy)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Input size (ticks)")
    plt.ylabel("Runtime (seconds)")
    plt.title("Runtime vs input size")
    plt.legend()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def plot_memory_vs_input_size(results: List[ProfileResult], out_path: Path) -> None:
    grouped = _group_by_strategy(results)
    plt.figure()
    for strategy, lst in grouped.items():
        xs = [r.n_ticks for r in lst]
        ys = [r.peak_memory_bytes / (1024 * 1024) for r in lst]
        plt.plot(xs, ys, marker="o", label=strategy)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Input size (ticks)")
    plt.ylabel("Peak Python allocations (MiB)")
    plt.title("Memory vs input size")
    plt.legend()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def _md_table_for_size(results: List[ProfileResult], n_ticks: int) -> str:
    rows = [r for r in results if r.n_ticks == n_ticks]
    rows.sort(key=lambda r: r.strategy)

    header = "| Strategy | Runtime (s) | Peak memory (MiB) |\n|---|---:|---:|"
    lines = [header]
    for r in rows:
        lines.append(f"| {r.strategy} | {r.runtime_seconds:.6f} | {r.peak_memory_bytes / (1024 * 1024):.3f} |")
    return "\n".join(lines)


def _hotspots_md(results: List[ProfileResult], top_n: int = 5) -> str:
    parts: List[str] = []
    for r in results:
        if not r.cprofile_top:
            continue
        parts.append(f"### {r.strategy} @ {r.n_ticks:,} ticks")
        parts.append("| Function | Calls | Total (s) | Cumulative (s) |")
        parts.append("|---|---:|---:|---:|")
        for func, calls, tt, ct in r.cprofile_top[:top_n]:
            parts.append(f"| `{func}` | {calls} | {tt:.6f} | {ct:.6f} |")
        parts.append("")
    return "\n".join(parts)


def _format_dataset_characteristics(
    dataset_total_ticks: Optional[int],
    symbols: Optional[List[str]],
    symbol_counts: Optional[Mapping[str, int]],
    window_size: Optional[int],
) -> str:
    parts: List[str] = []
    parts.append("## Dataset characteristics")
    parts.append("")

    if dataset_total_ticks is not None:
        parts.append(f"- Total ticks in CSV: **{dataset_total_ticks:,}**")
    else:
        parts.append("- Total ticks in CSV: *(not provided)*")

    if symbols is not None:
        parts.append(f"- Symbols: **{len(symbols)}** ({', '.join(symbols)})")
    else:
        parts.append("- Symbols: *(not provided)*")

    if symbol_counts:
        counts = list(symbol_counts.values())
        mn, mx = min(counts), max(counts)
        # simple uniformity heuristic
        if mn == 0:
            uniform_note = "skewed (some symbols have 0 ticks)"
        else:
            ratio = mx / mn
            uniform_note = "approximately uniform" if ratio <= 1.2 else "skewed"
        # show counts (sorted by count desc)
        top = sorted(symbol_counts.items(), key=lambda kv: kv[1], reverse=True)
        parts.append(f"- Tick distribution across symbols: **{uniform_note}** (max/min ≈ {mx}/{mn})")
        parts.append("  - Counts: " + ", ".join(f"{s}={c:,}" for s, c in top))
    else:
        parts.append("- Tick distribution across symbols: *(not provided)*")

    if window_size is not None:
        parts.append(f"- Window size (k): **{window_size}**")
    else:
        parts.append("- Window size (k): *(not provided)*")

    parts.append("")
    return "\n".join(parts)


def generate_complexity_report(
    results: List[ProfileResult],
    out_dir: str | Path,
    *,
    dataset_total_ticks: Optional[int] = None,
    symbols: Optional[List[str]] = None,
    symbol_counts: Optional[Mapping[str, int]] = None,
    window_size: Optional[int] = None,
) -> Path:
    out_dir = Path(out_dir)

    sizes_present = {r.n_ticks for r in results}
    if 100_000 in sizes_present:
        results = _maybe_add_naive_extrapolation(results, target_size=100_000)

    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    runtime_plot = plots_dir / "runtime_vs_input_size.png"
    memory_plot = plots_dir / "memory_vs_input_size.png"

    plot_runtime_vs_input_size(results, runtime_plot)
    plot_memory_vs_input_size(results, memory_plot)

    sizes = sorted({r.n_ticks for r in results})

    md_parts: List[str] = []
    md_parts.append("# Complexity Report")
    md_parts.append("")

    # dataset characteristics section
    md_parts.append(
        _format_dataset_characteristics(
            dataset_total_ticks=dataset_total_ticks,
            symbols=symbols,
            symbol_counts=symbol_counts,
            window_size=window_size,
        )
    )

    md_parts.append("## Strategies & theoretical complexity")
    md_parts.append("")
    md_parts.append("- **NaiveMovingAverageStrategy**: recomputes `sum(history)` every tick. Time **O(n)** per tick, Space **O(n)**.")
    md_parts.append("- **WindowedMovingAverageStrategy (k window)**: maintains deque + running sum. Time **O(1)** per tick, Space **O(k)**.")
    md_parts.append("- **OptimizedMovingAverageStrategy**: running sum + count (cumulative mean). Time **O(1)** per tick, Space **O(1)** per symbol.")
    md_parts.append("")
    md_parts.append("## Benchmarks")
    md_parts.append("")
    md_parts.append("Measured with `timeit` (best of repeats) and `tracemalloc` peak allocations. See `profiler.py`.")
    md_parts.append("")

    for n in sizes:
        md_parts.append(f"### Input size: {n:,} ticks")
        md_parts.append("")
        md_parts.append(_md_table_for_size(results, n))
        md_parts.append("")

    md_parts.append("## Scaling plots")
    md_parts.append("")

    runtime_rel = runtime_plot.relative_to(out_dir).as_posix()
    memory_rel = memory_plot.relative_to(out_dir).as_posix()
    md_parts.append(f"![Runtime vs input size]({runtime_rel})")
    md_parts.append("")
    md_parts.append(f"![Memory vs input size]({memory_rel})")
    md_parts.append("")

    md_parts.append("## cProfile hotspots (top functions)")
    md_parts.append("")
    md_parts.append(_hotspots_md(results, top_n=5))

    md_parts.append("## Narrative")
    md_parts.append("")
    narrative = (
        "The naive strategy scales poorly because each tick recomputes a full-history sum. "
        "The windowed strategy avoids full rescans by maintaining a fixed-size buffer and a running sum. "
        "The optimized strategy goes further by eliminating history storage entirely (cumulative mean), "
        "reducing both time and space, which should satisfy the <1s / <100MB target for 100k ticks on typical hardware."
    )
    if any("extrapolated" in r.strategy for r in results):
        narrative += (
            "\n\n**Note:** `NaiveMovingAverageStrategy` at 100,000 ticks is labeled as *extrapolated* because "
            "running the true O(n^2) naive implementation at that scale is typically impractical. The report "
            "extrapolates time using O(n^2) scaling from the largest measured naive run and extrapolates memory "
            "using O(n) scaling."
        )
    md_parts.append(narrative)

    md_path = out_dir / "complexity_report.md"
    md_path.write_text("\n".join(md_parts), encoding="utf-8")
    return md_path
