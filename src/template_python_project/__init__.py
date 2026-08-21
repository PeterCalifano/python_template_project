"""Reusable Python package template with optional pybind11 acceleration.

The public API is deliberately small; it exists to demonstrate the shape of a
package that ships both pure-Python code and a compiled extension.

Example:
    import template_python_project as tpp

    print(tpp.hello())
    print(tpp.vector_norm([3.0, 4.0]))

Output:
    hello from template_python_project
    5.0
"""

from ._accel import (
    HAS_EXTENSION,
    RunningStatistics,
    backend_name,
    scale_in_place,
    vector_norm,
)
from ._version import __version__
from .core import hello

__all__ = [
    "HAS_EXTENSION",
    "RunningStatistics",
    "__version__",
    "backend_name",
    "hello",
    "scale_in_place",
    "vector_norm",
]
