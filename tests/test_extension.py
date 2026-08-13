"""Tests for the optional pybind11 extension and its pure-Python fallback.

The suite is written so it passes in both build configurations:

* with the extension compiled, the native path is exercised, and
* with ``TPP_BUILD_EXTENSION=OFF``, the native-only tests skip and the
  fallback carries the behavioural assertions.

The most valuable tests here are the *equivalence* ones: they pin the two
implementations to the same observable behaviour, so the fallback cannot quietly
drift away from the C++ it stands in for.
"""

from __future__ import annotations

import math
from typing import ClassVar

import numpy as np
import pytest

import template_python_project as tpp
from template_python_project._accel import _PythonRunningStatistics

# Skips every native test in one place when the extension was not built.
requires_extension = pytest.mark.skipif(
    not tpp.HAS_EXTENSION,
    reason="compiled extension not available in this build",
)


class TestBackendDiscovery:
    """The shim must report honestly which implementation is in use."""

    @pytest.mark.unit
    def test_backend_name_matches_has_extension(self) -> None:
        expected = "native" if tpp.HAS_EXTENSION else "python"
        assert tpp.backend_name() == expected

    @pytest.mark.unit
    def test_package_imports_regardless_of_extension(self) -> None:
        # The whole point of _accel.py: import never depends on the binary.
        assert isinstance(tpp.HAS_EXTENSION, bool)
        assert tpp.hello() == "hello from template_python_project"


class TestVectorNorm:
    """Norm behaviour, checked against values computed independently."""

    @pytest.mark.unit
    def test_pythagorean_triple(self) -> None:
        assert tpp.vector_norm([3.0, 4.0]) == pytest.approx(5.0)

    @pytest.mark.unit
    def test_single_element(self) -> None:
        assert tpp.vector_norm([-7.5]) == pytest.approx(7.5)

    @pytest.mark.unit
    def test_all_zeros(self) -> None:
        assert tpp.vector_norm([0.0, 0.0, 0.0]) == pytest.approx(0.0)

    @pytest.mark.unit
    def test_matches_numpy(self) -> None:
        values = [1.5, -2.25, 3.125, 0.0, 42.0]
        assert tpp.vector_norm(values) == pytest.approx(float(np.linalg.norm(values)))

    @pytest.mark.unit
    def test_empty_input_raises_value_error(self) -> None:
        # C++ std::invalid_argument must surface as a Python ValueError.
        with pytest.raises(ValueError, match="at least one value"):
            tpp.vector_norm([])

    @pytest.mark.unit
    def test_survives_overflow_prone_magnitudes(self) -> None:
        # A naive sum of squares overflows here; the scaled algorithm must not.
        large = 1e200
        assert tpp.vector_norm([large, large]) == pytest.approx(large * math.sqrt(2.0))

    @pytest.mark.unit
    def test_survives_underflow_prone_magnitudes(self) -> None:
        tiny = 1e-200
        assert tpp.vector_norm([tiny, tiny]) == pytest.approx(tiny * math.sqrt(2.0))


class TestScaleInPlace:
    """The zero-copy NumPy path must mutate the caller's own buffer."""

    @pytest.mark.unit
    def test_mutates_caller_array(self) -> None:
        data = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        tpp.scale_in_place(data, 2.0)
        np.testing.assert_allclose(data, [2.0, 4.0, 6.0])

    @pytest.mark.unit
    def test_no_copy_is_made(self) -> None:
        # Holding a view proves the original buffer was modified, not replaced.
        data = np.arange(5, dtype=np.float64)
        view = data[:]
        tpp.scale_in_place(data, 3.0)
        np.testing.assert_allclose(view, [0.0, 3.0, 6.0, 9.0, 12.0])

    @pytest.mark.unit
    def test_rejects_two_dimensional_array(self) -> None:
        data = np.ones((2, 2), dtype=np.float64)
        with pytest.raises(ValueError, match="1-dimensional"):
            tpp.scale_in_place(data, 2.0)

    @pytest.mark.unit
    def test_rejects_non_contiguous_array(self) -> None:
        # Every other element: stride is 2 * itemsize, so the buffer is not
        # the contiguous block the C++ assumes. Silently copying here would
        # make an in-place function a no-op from the caller's perspective.
        data = np.arange(10, dtype=np.float64)[::2]
        with pytest.raises(ValueError, match="contiguous"):
            tpp.scale_in_place(data, 2.0)

    @pytest.mark.unit
    def test_rejects_readonly_array(self) -> None:
        data = np.arange(4, dtype=np.float64)
        data.flags.writeable = False
        # Both backends must report this the same way; the fallback's message
        # is deliberately worded to match pybind11's.
        with pytest.raises(ValueError, match="read-only"):
            tpp.scale_in_place(data, 2.0)

    @pytest.mark.unit
    def test_empty_array_is_a_no_op(self) -> None:
        data = np.array([], dtype=np.float64)
        tpp.scale_in_place(data, 5.0)
        assert data.size == 0


class TestRunningStatistics:
    """Welford accumulator behaviour."""

    # Sample with a mean of exactly 5.0 and a known sample variance.
    SAMPLE: ClassVar[list[float]] = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]

    @pytest.mark.unit
    def test_empty_accumulator(self) -> None:
        stats = tpp.RunningStatistics()
        assert stats.count == 0
        assert stats.mean == pytest.approx(0.0)
        assert stats.variance == pytest.approx(0.0)

    @pytest.mark.unit
    def test_single_sample_has_zero_variance(self) -> None:
        stats = tpp.RunningStatistics()
        stats.add(42.0)
        assert stats.count == 1
        assert stats.mean == pytest.approx(42.0)
        # Bessel correction is undefined for n=1; the contract is 0.0.
        assert stats.variance == pytest.approx(0.0)

    @pytest.mark.unit
    def test_matches_numpy_mean_and_variance(self) -> None:
        stats = tpp.RunningStatistics()
        stats.extend(self.SAMPLE)
        assert stats.count == len(self.SAMPLE)
        assert stats.mean == pytest.approx(float(np.mean(self.SAMPLE)))
        # ddof=1 is the Bessel-corrected sample variance.
        assert stats.variance == pytest.approx(float(np.var(self.SAMPLE, ddof=1)))
        assert stats.stddev == pytest.approx(float(np.std(self.SAMPLE, ddof=1)))

    @pytest.mark.unit
    def test_add_and_extend_agree(self) -> None:
        by_add = tpp.RunningStatistics()
        for value in self.SAMPLE:
            by_add.add(value)
        by_extend = tpp.RunningStatistics()
        by_extend.extend(self.SAMPLE)
        assert by_add.mean == pytest.approx(by_extend.mean)
        assert by_add.variance == pytest.approx(by_extend.variance)

    @pytest.mark.unit
    def test_reset_clears_state(self) -> None:
        stats = tpp.RunningStatistics()
        stats.extend(self.SAMPLE)
        stats.reset()
        assert stats.count == 0
        assert stats.mean == pytest.approx(0.0)

    @pytest.mark.unit
    def test_dunder_len(self) -> None:
        stats = tpp.RunningStatistics()
        stats.extend(self.SAMPLE)
        assert len(stats) == len(self.SAMPLE)

    @pytest.mark.unit
    def test_repr_is_informative(self) -> None:
        stats = tpp.RunningStatistics()
        stats.extend(self.SAMPLE)
        assert "RunningStatistics" in repr(stats)
        assert "count=8" in repr(stats)

    @pytest.mark.unit
    def test_numerically_stable_for_large_offsets(self) -> None:
        # A naive sum-of-squares variance loses all precision here because the
        # squares are ~1e18 while the true variance is ~1. Welford does not.
        offset = 1e9
        values = [offset + delta for delta in (1.0, 2.0, 3.0, 4.0, 5.0)]
        stats = tpp.RunningStatistics()
        stats.extend(values)
        assert stats.variance == pytest.approx(2.5, rel=1e-9)


class TestBackendEquivalence:
    """Native and pure-Python paths must be observationally identical.

    These are the tests that stop the fallback from drifting away from the C++.
    """

    @requires_extension
    @pytest.mark.extension
    def test_norm_agrees_between_backends(self) -> None:
        from template_python_project import _core

        for values in ([3.0, 4.0], [1e-8, 2e-8], [1.0] * 100, [-5.0, 12.0]):
            native = _core.vector_norm(values)
            reference = float(np.linalg.norm(values))
            assert native == pytest.approx(reference)

    @requires_extension
    @pytest.mark.extension
    def test_statistics_agree_between_backends(self) -> None:
        from template_python_project import _core

        sample = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]

        native = _core.RunningStatistics()
        native.extend(sample)
        fallback = _PythonRunningStatistics()
        fallback.extend(sample)

        assert native.count == fallback.count
        assert native.mean == pytest.approx(fallback.mean)
        assert native.variance == pytest.approx(fallback.variance)
        assert native.stddev == pytest.approx(fallback.stddev)

    @pytest.mark.unit
    def test_fallback_norm_matches_numpy(self) -> None:
        # Exercises the pure-Python branch directly even when the native
        # module is present, so the fallback is never left untested.
        from template_python_project import _accel

        values = [1.5, -2.25, 3.125, 42.0]
        max_magnitude = max(abs(v) for v in values)
        expected = max_magnitude * math.sqrt(math.fsum((v / max_magnitude) ** 2 for v in values))
        assert expected == pytest.approx(float(np.linalg.norm(values)))
        assert _accel.vector_norm(values) == pytest.approx(expected)


class TestExtensionMetadata:
    """Version agreement between the Python and C++ halves."""

    @requires_extension
    @pytest.mark.extension
    def test_extension_version_matches_package(self) -> None:
        from template_python_project import _core

        # CMake receives the version from scikit-build-core, which gets it
        # from setuptools-scm -- so these must not be able to disagree.
        assert _core.__version__ == tpp.__version__

    @requires_extension
    @pytest.mark.extension
    def test_extension_exposes_expected_api(self) -> None:
        from template_python_project import _core

        for name in ("vector_norm", "scale_in_place", "RunningStatistics"):
            assert hasattr(_core, name), f"_core is missing {name}"
