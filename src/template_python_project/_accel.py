"""Optional-acceleration shim over the compiled ``_core`` extension.

This module is the reason the package imports cleanly whether or not the
pybind11 extension was ever compiled. It tries the native import once, records
the outcome in :data:`HAS_EXTENSION`, and exposes a single public API that
dispatches to whichever implementation is available.

Two properties make this worth the indirection:

* A pure-Python consumer never sees an :exc:`ImportError` when no binary was built.
* A present but broken binary still reports its original import failure.
* The pure-Python fallbacks double as an executable specification of what the
  C++ is supposed to do, which is what :mod:`tests.test_extension` checks.

Example:
    from template_python_project import _accel

    print(_accel.vector_norm([3.0, 4.0]))

Output:
    5.0
"""

from __future__ import annotations

import math
from importlib.util import find_spec
from typing import TYPE_CHECKING, Final

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Sequence

    import numpy.typing as npt

__all__ = [
    "HAS_EXTENSION",
    "RunningStatistics",
    "backend_name",
    "scale_in_place",
    "vector_norm",
]

if TYPE_CHECKING:
    from . import _core
elif find_spec(f"{__package__}._core") is None:
    _core = None
else:
    from . import _core

#: ``True`` when the compiled extension is available for this installation.
HAS_EXTENSION: Final[bool] = _core is not None


def backend_name() -> str:
    """Return the active backend, ``"native"`` or ``"python"``.

    Returns:
        The name of the implementation currently in use.

    Example:
        print(backend_name() in {"native", "python"})

    Output:
        True
    """
    return "native" if HAS_EXTENSION else "python"


def vector_norm(values: Sequence[float]) -> float:
    """Return the Euclidean (L2) norm of ``values``.

    Dispatches to the compiled implementation when available. Both paths use
    the same scaled two-pass algorithm, so results agree to within floating
    point rounding.

    Args:
        values: A non-empty sequence of floats.

    Returns:
        The L2 norm.

    Raises:
        ValueError: If ``values`` is empty.

    Example:
        print(vector_norm([3.0, 4.0]))

    Output:
        5.0
    """
    if _core is not None:
        result: float = _core.vector_norm(list(values))
        return result

    if len(values) == 0:
        raise ValueError("vector_norm requires at least one value")

    # Mirror the C++ scaled computation rather than using math.hypot, so that
    # the fallback is a faithful specification of the native behaviour.
    max_magnitude = max(abs(value) for value in values)
    if max_magnitude == 0.0:
        return 0.0

    accumulated = math.fsum((value / max_magnitude) ** 2 for value in values)
    return max_magnitude * math.sqrt(accumulated)


def scale_in_place(array: npt.NDArray[np.float64], factor: float) -> None:
    """Multiply a 1-D float64 array in place by ``factor``.

    The native path mutates the array's buffer directly with no copy and
    releases the GIL while doing so.

    Args:
        array: A writable, C-contiguous 1-D ``numpy.float64`` array.
        factor: The scalar multiplier.

    Raises:
        ValueError: If the array is not float64, 1-D, C-contiguous, or writable.

    Example:
        import numpy as np

        data = np.array([1.0, 2.0, 3.0])
        scale_in_place(data, 2.0)
        print(data.tolist())

    Output:
        [2.0, 4.0, 6.0]
    """
    if _core is not None:
        _core.scale_in_place(array, factor)
        return

    if array.dtype != np.dtype(np.float64):
        raise ValueError("expected a float64 array")
    if array.ndim != 1:
        raise ValueError("expected a 1-dimensional array")
    if not array.flags["C_CONTIGUOUS"]:
        raise ValueError("expected a C-contiguous array; pass numpy.ascontiguousarray(arr)")
    if not array.flags["WRITEABLE"]:
        # Wording deliberately echoes pybind11's own "buffer source array is
        # read-only", so callers can match on one phrase across both backends.
        raise ValueError("buffer source array is read-only")

    array *= factor


class _PythonRunningStatistics:
    """Pure-Python fallback for the native ``RunningStatistics``.

    Implements Welford's online algorithm, matching ``template_ext.cpp`` step
    for step so the two backends produce identical results.

    Example:
        stats = _PythonRunningStatistics()
        stats.extend([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
        print(stats.mean)
        print(round(stats.variance, 4))

    Output:
        5.0
        4.5714
    """

    def __init__(self) -> None:
        """Create an empty accumulator."""
        self._count = 0
        self._mean = 0.0
        self._m2 = 0.0

    def add(self, value: float) -> None:
        """Incorporate a single observation.

        Args:
            value: The observation to add.
        """
        self._count += 1
        delta = value - self._mean
        self._mean += delta / self._count
        self._m2 += delta * (value - self._mean)

    def extend(self, values: Sequence[float]) -> None:
        """Incorporate a sequence of observations.

        Args:
            values: The observations to add.
        """
        for value in values:
            self.add(value)

    def reset(self) -> None:
        """Discard all accumulated state."""
        self._count = 0
        self._mean = 0.0
        self._m2 = 0.0

    @property
    def count(self) -> int:
        """Number of observations seen so far."""
        return self._count

    @property
    def mean(self) -> float:
        """Arithmetic mean of the observations."""
        return self._mean

    @property
    def variance(self) -> float:
        """Bessel-corrected sample variance; 0.0 for fewer than two samples."""
        if self._count < 2:
            return 0.0
        return self._m2 / (self._count - 1)

    @property
    def stddev(self) -> float:
        """Sample standard deviation."""
        return math.sqrt(self.variance)

    def __len__(self) -> int:
        """Return the number of observations seen so far."""
        return self._count

    def __repr__(self) -> str:
        """Return a debug representation matching the native class."""
        return f"RunningStatistics(count={self.count}, mean={self.mean}, stddev={self.stddev})"


# Bind the name once at import time rather than dispatching per call, so
# `RunningStatistics` is a real class that isinstance() and typing understand.
RunningStatistics = _core.RunningStatistics if _core is not None else _PythonRunningStatistics
