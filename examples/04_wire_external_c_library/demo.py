#!/usr/bin/env python3
"""Example 4: calling an external C library through pybind11.

Build the module first:
    ./examples/04_wire_external_c_library/build_and_run.sh

Or manually:
    cmake -S examples/04_wire_external_c_library -B /tmp/mylib_build
    cmake --build /tmp/mylib_build
    python examples/04_wire_external_c_library/demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# The compiled module is written next to this file by CMake.
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import _mylib
except ImportError:
    print("The _mylib extension is not built yet.")
    print("Run: ./examples/04_wire_external_c_library/build_and_run.sh")
    sys.exit(1)


def main() -> None:
    """Call into the wrapped C library and print the results."""
    print("=" * 62)
    print("Example 4 -- wrapping an external C library")
    print("=" * 62)

    # The C library reports its own version, separate from the Python package
    # version. Surfacing both makes a wrapper/library mismatch easy to spot.
    print(f"\nC library version : {_mylib.__mylib_version__}")

    samples = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], dtype=np.float64)
    print(f"input             : {samples.tolist()}")

    # --- Scalar return through an out-parameter ----------------------------
    # C signature: mylib_status_t mylib_mean(const double*, size_t, double*)
    # The binding hides the out-parameter and the status code entirely.
    print(f"\nmean()            : {_mylib.mean(samples)}")
    print(f"numpy reference   : {float(np.mean(samples))}")

    # --- Array in, array out -----------------------------------------------
    # The output array is allocated as a NumPy array before the call, so the C
    # code writes straight into the buffer Python receives -- no extra copy.
    smoothed = _mylib.moving_average(samples, 3)
    print(f"\nmoving_average(3) : {[round(v, 4) for v in smoothed.tolist()]}")
    print(f"input unchanged   : {samples.tolist()}")

    smoothed5 = _mylib.moving_average(samples, 5)
    print(f"moving_average(5) : {[round(v, 4) for v in smoothed5.tolist()]}")

    # --- C error codes surface as Python exceptions ------------------------
    print("\nC status codes become Python exceptions:")
    for description, call in (
        ("empty array (MYLIB_ERR_EMPTY_INPUT)", lambda: _mylib.mean(np.array([]))),
        ("2-D array", lambda: _mylib.mean(np.ones((2, 2)))),
        ("non-contiguous", lambda: _mylib.mean(np.arange(10.0)[::2])),
    ):
        try:
            call()
        except ValueError as error:
            print(f"  {description:36s} -> ValueError: {error}")

    print("\nDone.")


if __name__ == "__main__":
    main()
