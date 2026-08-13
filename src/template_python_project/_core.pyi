"""Type stubs for the compiled ``_core`` extension module.

Regenerate after changing ``src/cpp/bindings.cpp``::

    pybind11-stubgen template_python_project._core -o src/

The checked-in copy is edited by hand afterwards, because stubgen cannot infer
docstring-only details such as which exceptions a binding raises.
"""

from collections.abc import Sequence

import numpy as np
import numpy.typing as npt

__version__: str

def vector_norm(values: Sequence[float]) -> float:
    """Return the Euclidean (L2) norm of a non-empty sequence of floats."""

def scale_in_place(array: npt.NDArray[np.float64], factor: float) -> None:
    """Multiply a writable, C-contiguous 1-D float64 array in place."""

class RunningStatistics:
    """Streaming mean and variance using Welford's algorithm."""

    def __init__(self) -> None: ...
    def add(self, value: float) -> None: ...
    def extend(self, values: Sequence[float]) -> None: ...
    def reset(self) -> None: ...
    @property
    def count(self) -> int: ...
    @property
    def mean(self) -> float: ...
    @property
    def variance(self) -> float: ...
    @property
    def stddev(self) -> float: ...
    def __len__(self) -> int: ...
    def __repr__(self) -> str: ...
