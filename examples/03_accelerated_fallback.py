#!/usr/bin/env python3
"""Example 3: the optional-acceleration pattern.

Shows how ``_accel.py`` lets one API serve both a compiled backend and a pure
Python one. This is the pattern to copy when your package should install
everywhere but run fast where a compiler was available.

Run:
    python examples/03_accelerated_fallback.py
"""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence

import template_python_project as tpp
from template_python_project import _accel


def _time_call(function: Callable[[], object], repetitions: int) -> float:
    """Return the average wall-clock seconds per call over ``repetitions``."""
    start = time.perf_counter()
    for _ in range(repetitions):
        function()
    return (time.perf_counter() - start) / repetitions


def _python_norm(values: Sequence[float]) -> float:
    """Pure-Python norm, bypassing whichever backend is installed.

    Reimplements the fallback so the comparison below is always native-vs-Python,
    even on a build where ``_accel`` would dispatch to the extension.
    """
    import math

    max_magnitude = max(abs(value) for value in values)
    if max_magnitude == 0.0:
        return 0.0
    return max_magnitude * math.sqrt(math.fsum((value / max_magnitude) ** 2 for value in values))


def main() -> None:
    """Demonstrate backend dispatch, result equality, and relative speed."""
    print("=" * 62)
    print("Example 3 -- accelerated path with pure-Python fallback")
    print("=" * 62)

    print(f"\nHAS_EXTENSION : {tpp.HAS_EXTENSION}")
    print(f"backend_name(): {tpp.backend_name()}")
    print(
        "\nThe same call works either way -- only the speed changes:\n"
        f"  tpp.vector_norm([3.0, 4.0]) = {tpp.vector_norm([3.0, 4.0])}"
    )

    # --- Both implementations must agree -----------------------------------
    print("\n1. Result agreement between backends:")
    sample = [float(i) * 0.5 for i in range(1, 2001)]
    dispatched = _accel.vector_norm(sample)
    reference = _python_norm(sample)
    print(f"   dispatched ({tpp.backend_name():6s}) : {dispatched!r}")
    print(f"   pure Python           : {reference!r}")
    print(f"   difference            : {abs(dispatched - reference):.3e}")

    # --- Statistics classes agree too --------------------------------------
    native_stats = tpp.RunningStatistics()
    native_stats.extend(sample)
    python_stats = _accel._PythonRunningStatistics()
    python_stats.extend(sample)
    print("\n2. RunningStatistics agreement:")
    print(f"   dispatched mean/var   : {native_stats.mean:.9f} / {native_stats.variance:.9f}")
    print(f"   pure-Python mean/var  : {python_stats.mean:.9f} / {python_stats.variance:.9f}")

    # --- Speed -------------------------------------------------------------
    # Timings on a tiny workload are dominated by call overhead; treat the
    # ratio as indicative, not as a benchmark.
    print("\n3. Relative speed (2000 elements, 200 repetitions):")
    repetitions = 200
    dispatched_seconds = _time_call(lambda: _accel.vector_norm(sample), repetitions)
    python_seconds = _time_call(lambda: _python_norm(sample), repetitions)
    print(f"   dispatched ({tpp.backend_name():6s}) : {dispatched_seconds * 1e6:9.2f} us/call")
    print(f"   pure Python           : {python_seconds * 1e6:9.2f} us/call")
    if dispatched_seconds > 0:
        print(f"   speedup               : {python_seconds / dispatched_seconds:9.2f}x")

    if not tpp.HAS_EXTENSION:
        print("\n   (No extension installed, so both rows run the same code.)")
        print("   Build it with ./build_ext.sh to see the native timing.")

    print("\nDone.")


if __name__ == "__main__":
    main()
