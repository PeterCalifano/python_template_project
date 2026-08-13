#!/usr/bin/env python3
"""Example 1: the pure-Python surface of the package.

Nothing here needs a compiler. This is what a consumer sees after a plain
``pip install template_python_project``, whether or not the extension was built.

Run:
    python examples/01_pure_python_usage.py
"""

from __future__ import annotations

import template_python_project as tpp


def main() -> None:
    """Exercise the pure-Python API and print the results."""
    print("=" * 62)
    print("Example 1 -- pure-Python usage")
    print("=" * 62)

    # --- Package metadata --------------------------------------------------
    # The version comes from the git tag via setuptools-scm, so it is never
    # hand-edited and never stale.
    print(f"\nPackage version : {tpp.__version__}")
    print(f"Active backend  : {tpp.backend_name()}")
    print(f"Extension built : {tpp.HAS_EXTENSION}")

    # --- The simplest possible public function -----------------------------
    print(f"\nhello()         : {tpp.hello()!r}")

    # --- A computation that works identically on both backends -------------
    vectors = {
        "3-4-5 triangle": [3.0, 4.0],
        "unit basis     ": [1.0, 0.0, 0.0],
        "mixed signs    ": [1.5, -2.25, 3.125],
    }
    print("\nvector_norm():")
    for label, values in vectors.items():
        print(f"  {label} {values} -> {tpp.vector_norm(values):.6f}")

    # --- Error handling ----------------------------------------------------
    # The C++ throws std::invalid_argument; pybind11 translates it to a normal
    # Python ValueError, so callers write ordinary try/except.
    print("\nError handling:")
    try:
        tpp.vector_norm([])
    except ValueError as error:
        print(f"  vector_norm([]) raised ValueError: {error}")

    print("\nDone.")


if __name__ == "__main__":
    main()
