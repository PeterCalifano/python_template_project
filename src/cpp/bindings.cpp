// pybind11 binding layer: the only file that knows about both C++ and Python.
//
// Keep this file thin. Real logic belongs in template_ext.cpp (or in the
// external library you are wrapping); this file's job is translating types,
// documenting the Python-facing API, and nothing else.
//
// The module is named `_core` with a leading underscore because it is a
// private implementation detail. Users import the friendly Python wrapper in
// template_python_project/_accel.py, which falls back to pure Python when this
// module was never compiled.

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>  // enables automatic std::vector <-> list conversion

#include <cstddef>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "template_ext.hpp"

namespace py = pybind11;

namespace {

/// Multiply a NumPy array in place, without copying its buffer.
///
/// The `py::array::c_style | py::array::forcecast` flags would silently copy a
/// non-contiguous or wrong-dtype input, which would make an "in place"
/// function quietly do nothing to the caller's array. So we take a bare
/// py::array_t<double> and validate instead of converting -- surprising the
/// caller with a clear error beats surprising them with a silent no-op.
void scale_array_in_place(py::array_t<double> array, const double factor) {
    // request(true) asks for writable access and throws if the array is
    // read-only, which is exactly the check we want.
    py::buffer_info info = array.request(true);

    if (info.ndim != 1) {
        throw std::invalid_argument("expected a 1-dimensional array");
    }

    // A negative or non-unit stride means the memory is not the simple
    // contiguous block that scale_in_place assumes.
    const auto expected_stride = static_cast<py::ssize_t>(sizeof(double));
    if (info.strides[0] != expected_stride) {
        throw std::invalid_argument(
            "expected a C-contiguous array; pass numpy.ascontiguousarray(arr)");
    }

    // Release the GIL: this is pure C++ work touching no Python objects, so
    // other threads can run while it proceeds. For a loop this short the win
    // is negligible, but the pattern is the point -- any genuinely expensive
    // native routine should do this.
    auto* data = static_cast<double*>(info.ptr);
    const auto count = static_cast<std::size_t>(info.shape[0]);
    {
        py::gil_scoped_release release;
        template_ext::scale_in_place(data, count, factor);
    }
}

}  // namespace

PYBIND11_MODULE(_core, m) {
    m.doc() = R"pbdoc(
        Compiled core of template_python_project.

        This is a private module. Import the public wrappers from
        ``template_python_project`` instead, which work whether or not this
        extension was built.
    )pbdoc";

    // ---- Module metadata --------------------------------------------------
    //
    // VERSION_INFO is defined by CMake as an already-quoted string literal
    // holding SKBUILD_PROJECT_VERSION_FULL -- the *exact* PEP 440 version
    // including any ".devN" suffix, which project(VERSION) would truncate.
    // It comes from the same git tag as the Python metadata, so the two halves
    // cannot report different versions. Do not stringify it again.
#ifdef VERSION_INFO
    m.attr("__version__") = VERSION_INFO;
#else
    m.attr("__version__") = "dev";
#endif

    // ---- Free functions ---------------------------------------------------

    m.def("vector_norm",
          &template_ext::vector_norm,
          py::arg("values"),
          R"pbdoc(
        Return the Euclidean (L2) norm of a sequence of floats.

        Uses a scaled two-pass computation, so it stays accurate for values
        near the floating-point range limits where a naive sum of squares
        would overflow or underflow.

        Args:
            values: A non-empty sequence of floats.

        Returns:
            The L2 norm as a float.

        Raises:
            ValueError: If ``values`` is empty.
    )pbdoc");

    m.def("scale_in_place",
          &scale_array_in_place,
          py::arg("array"),
          py::arg("factor"),
          R"pbdoc(
        Multiply a 1-D float64 NumPy array in place by ``factor``.

        The array's own buffer is modified with no copy, so this mutates the
        caller's data. The GIL is released during the computation.

        Args:
            array: A writable, C-contiguous 1-D ``numpy.float64`` array.
            factor: The scalar multiplier.

        Raises:
            ValueError: If the array is not 1-D, not C-contiguous, or read-only.
    )pbdoc");

    // ---- Bound class ------------------------------------------------------

    py::class_<template_ext::RunningStatistics>(m, "RunningStatistics", R"pbdoc(
        Streaming mean and variance using Welford's algorithm.

        Accumulates statistics in a single pass without storing the samples,
        and without the catastrophic cancellation of a naive sum-of-squares.
    )pbdoc")
        .def(py::init<>(), "Create an empty accumulator.")
        .def("add",
             &template_ext::RunningStatistics::add,
             py::arg("value"),
             "Incorporate a single observation.")
        .def("extend",
             &template_ext::RunningStatistics::extend,
             py::arg("values"),
             "Incorporate a sequence of observations.")
        .def("reset",
             &template_ext::RunningStatistics::reset,
             "Discard all accumulated state.")
        // def_property_readonly exposes these as attributes (`stats.mean`)
        // rather than calls (`stats.mean()`), which is the idiomatic Python
        // surface for a cheap derived value.
        .def_property_readonly("count", &template_ext::RunningStatistics::count,
                               "Number of observations seen so far.")
        .def_property_readonly("mean", &template_ext::RunningStatistics::mean,
                               "Arithmetic mean of the observations.")
        .def_property_readonly("variance", &template_ext::RunningStatistics::variance,
                               "Bessel-corrected sample variance.")
        .def_property_readonly("stddev", &template_ext::RunningStatistics::stddev,
                               "Sample standard deviation.")
        .def("__len__", &template_ext::RunningStatistics::count)
        .def("__repr__", [](const template_ext::RunningStatistics& self) {
            std::ostringstream stream;
            stream << "RunningStatistics(count=" << self.count()
                   << ", mean=" << self.mean()
                   << ", stddev=" << self.stddev() << ")";
            return stream.str();
        });
}
