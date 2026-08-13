/* A deliberately plain C library.
 *
 * This stands in for the real external library you want to expose to Python.
 * It is written in C89-ish style with no CMake awareness of its own beyond a
 * minimal CMakeLists.txt, because that is the realistic case: most C libraries
 * worth wrapping predate modern CMake and know nothing about Python.
 *
 * Note the extern "C" guard. Without it, a C++ compiler would apply C++ name
 * mangling to these declarations and the linker would fail to find the symbols
 * in the C-compiled object file. Well-behaved C headers include this guard
 * themselves; if yours does not, wrap the #include on the C++ side instead:
 *
 *     extern "C" {
 *     #include <mylib.h>
 *     }
 */

#ifndef MYLIB_H
#define MYLIB_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Error codes returned by the functions below. C libraries typically signal
 * failure with a return code rather than an exception; the binding layer is
 * responsible for turning these into Python exceptions. */
typedef enum {
    MYLIB_OK = 0,
    MYLIB_ERR_NULL_POINTER = 1,
    MYLIB_ERR_EMPTY_INPUT = 2
} mylib_status_t;

/* Return a human-readable description of a status code. */
const char* mylib_status_message(mylib_status_t status);

/* Compute the arithmetic mean of `count` doubles starting at `values`.
 * Writes the result to *out_mean. Returns MYLIB_OK on success. */
mylib_status_t mylib_mean(const double* values, size_t count, double* out_mean);

/* Apply a simple moving average of width `window` over `count` input samples,
 * writing `count` outputs to `out_values` (edges use a shrinking window).
 * `out_values` must have room for `count` doubles. */
mylib_status_t mylib_moving_average(const double* values,
                                    size_t count,
                                    size_t window,
                                    double* out_values);

/* Library version string, e.g. "1.0.0". */
const char* mylib_version(void);

#ifdef __cplusplus
}  /* extern "C" */
#endif

#endif /* MYLIB_H */
