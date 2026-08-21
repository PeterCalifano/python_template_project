#!/usr/bin/env python3
"""Example 2: talking to the compiled pybind11 extension directly.

This example reaches past the public wrapper and imports the private ``_core``
module, to show exactly what the C++ exposes. Application code should normally
use the ``template_python_project`` wrappers instead -- this is here so you can
see the binding surface while learning or debugging it.

Build the extension first:
    ./build_ext.sh

Run:
    python examples/02_pybind11_extension_usage.py
"""

from __future__ import annotations

import sys

import numpy as np

import template_python_project as tpp


def main() -> int:
    """Exercise the native extension directly. Returns a process exit code."""
    print("=" * 62)
    print("Example 2 -- pybind11 extension usage")
    print("=" * 62)

    if not tpp.HAS_EXTENSION:
        print("\nThe compiled extension is not available in this install.")
        print("Build it with:  ./build_ext.sh")
        print("(Example 3 shows the fallback path that works without it.)")
        return 1

    # Importing the private module is what application code should NOT do;
    # it is done here only to show the raw binding surface.
    from template_python_project import _core

    # --- Module metadata ---------------------------------------------------
    # C++ and Python versions come from the same git tag, injected into CMake
    # as SKBUILD_PROJECT_VERSION_FULL, so they cannot drift apart.
    print(f"\n_core.__version__   : {_core.__version__}")
    print(f"package __version__ : {tpp.__version__}")
    print(f"agree               : {_core.__version__ == tpp.__version__}")
    print(f"\nmodule docstring    : {(_core.__doc__ or '').strip().splitlines()[0]}")

    # --- Bound free function -----------------------------------------------
    # std::vector<double> <-> Python list conversion is automatic thanks to
    # the <pybind11/stl.h> include in bindings.cpp.
    print("\n1. Free function (std::vector<double> <-> list):")
    print(f"   _core.vector_norm([3.0, 4.0]) = {_core.vector_norm([3.0, 4.0])}")

    # --- Bound class with properties ---------------------------------------
    print("\n2. Bound C++ class with read-only properties:")
    stats = _core.RunningStatistics()
    for value in (2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0):
        stats.add(value)
    print(f"   repr     : {stats!r}")
    print(f"   count    : {stats.count}")
    print(f"   mean     : {stats.mean}")
    print(f"   variance : {stats.variance:.6f}")
    print(f"   stddev   : {stats.stddev:.6f}")
    print(f"   len()    : {len(stats)}   (via __len__)")

    # --- Zero-copy NumPy interop -------------------------------------------
    # This is the interesting one. The C++ receives a pointer to the array's
    # own memory; nothing is copied in either direction.
    print("\n3. Zero-copy NumPy mutation:")
    data = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
    address_before = data.__array_interface__["data"][0]
    print(f"   before        : {data.tolist()}")
    _core.scale_in_place(data, 2.5)
    address_after = data.__array_interface__["data"][0]
    print(f"   after         : {data.tolist()}")
    print(f"   buffer moved  : {address_before != address_after}  (False == no copy)")

    # A view over the same memory proves the original buffer was modified.
    big = np.ones(6, dtype=np.float64)
    view = big[:3]
    _core.scale_in_place(big, 7.0)
    print(f"   view sees it  : {view.tolist()}")

    # --- Exception translation ---------------------------------------------
    print("\n4. C++ exceptions become Python exceptions:")
    for description, call in (
        ("empty input (std::invalid_argument)", lambda: _core.vector_norm([])),
        ("2-D array", lambda: _core.scale_in_place(np.ones((2, 2)), 2.0)),
        ("non-contiguous array", lambda: _core.scale_in_place(np.arange(10.0)[::2], 2.0)),
    ):
        try:
            call()
        except ValueError as error:
            print(f"   {description:36s} -> ValueError: {error}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
