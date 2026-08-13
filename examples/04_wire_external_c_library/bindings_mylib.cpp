// Binding layer for the external C library in mylib/.
//
// This file is the worked answer to "how do I expose a C library to Python?".
// Three jobs, and only these three:
//
//   1. include the C header correctly from C++,
//   2. translate C error codes into Python exceptions, and
//   3. translate NumPy arrays into the raw pointers C expects.
//
// Copy this file into src/cpp/ and adjust it to your real library.

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include <stdexcept>
#include <string>

// mylib.h already carries its own extern "C" guard, so a plain include is
// correct. If your header lacks one, wrap it instead:
//
//     extern "C" {
//     #include <legacy_lib.h>
//     }
#include "mylib.h"

namespace py = pybind11;

namespace {

/// Turn a C status code into a Python exception.
///
/// C libraries report failure by return value. Letting that convention leak
/// into Python would force every caller to check return codes, which is not
/// how Python code is written -- so the boundary is where it gets converted.
void raise_on_error(const mylib_status_t status) {
    if (status == MYLIB_OK) {
        return;
    }

    const std::string message = mylib_status_message(status);

    switch (status) {
        case MYLIB_ERR_NULL_POINTER:
            throw std::invalid_argument("mylib: " + message);
        case MYLIB_ERR_EMPTY_INPUT:
            // Becomes ValueError on the Python side.
            throw std::invalid_argument("mylib: " + message);
        default:
            // Becomes RuntimeError on the Python side.
            throw std::runtime_error("mylib: " + message);
    }
}

/// Validate a 1-D float64 array and return a pointer to its buffer.
///
/// Centralizing this check means every binding below gets the same guarantees
/// and the same error messages.
const double* as_contiguous_1d(const py::array_t<double>& array, std::size_t& out_count) {
    const py::buffer_info info = array.request();

    if (info.ndim != 1) {
        throw std::invalid_argument("expected a 1-dimensional array");
    }
    if (info.strides[0] != static_cast<py::ssize_t>(sizeof(double))) {
        throw std::invalid_argument(
            "expected a C-contiguous array; pass numpy.ascontiguousarray(arr)");
    }

    out_count = static_cast<std::size_t>(info.shape[0]);
    return static_cast<const double*>(info.ptr);
}

double mean(const py::array_t<double>& values) {
    std::size_t count = 0;
    const double* data = as_contiguous_1d(values, count);

    double result = 0.0;
    mylib_status_t status = MYLIB_OK;
    {
        // No Python objects are touched inside, so the GIL can be released.
        py::gil_scoped_release release;
        status = mylib_mean(data, count, &result);
    }
    raise_on_error(status);
    return result;
}

py::array_t<double> moving_average(const py::array_t<double>& values, const std::size_t window) {
    std::size_t count = 0;
    const double* data = as_contiguous_1d(values, count);

    // Allocate the output as a NumPy array up front, so the C library writes
    // straight into the buffer Python will receive -- no intermediate copy.
    //
    // ACHTUNG! Construct with an explicit *shape container*, not the
    // `array_t(ssize_t count)` overload. That overload forwards an empty
    // strides container (`array({count}, {}, ...)`), which in pybind11 3.x
    // produces an array with stride 0: shape looks right, every element reads
    // back as element 0, and the C code appears to have computed garbage.
    // Passing the shape explicitly makes pybind11 compute C-contiguous strides.
    py::array_t<double> output(py::array::ShapeContainer{static_cast<py::ssize_t>(count)});
    auto* out_data = static_cast<double*>(output.request(true).ptr);

    mylib_status_t status = MYLIB_OK;
    {
        py::gil_scoped_release release;
        status = mylib_moving_average(data, count, window, out_data);
    }
    raise_on_error(status);
    return output;
}

}  // namespace

PYBIND11_MODULE(_mylib, m) {
    m.doc() = "Python bindings for the external C library 'mylib'.";

    // Expose the *library's* version, which is independent of the Python
    // package version. Reporting both makes debugging a version mismatch
    // between wrapper and library straightforward.
    m.attr("__mylib_version__") = mylib_version();

    m.def("mean", &mean, py::arg("values"),
          R"pbdoc(
        Arithmetic mean of a 1-D float64 array, computed by the C library.

        Raises:
            ValueError: If the array is empty, not 1-D, or not C-contiguous.
    )pbdoc");

    m.def("moving_average", &moving_average, py::arg("values"), py::arg("window") = 3,
          R"pbdoc(
        Centred moving average, computed by the C library.

        The window shrinks at the array edges. Returns a new array; the input
        is not modified.

        Raises:
            ValueError: If the array is empty, not 1-D, or not C-contiguous.
    )pbdoc");
}
