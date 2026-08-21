// Native implementation behind the Python bindings.
//
// This header is deliberately free of every pybind11 detail. Keeping the real
// C++ logic separate from the binding glue in bindings.cpp means:
//
//   * the library can be unit-tested and reused from other C++ code,
//   * the binding layer stays thin enough to read in one sitting, and
//   * replacing this placeholder with your actual external library is a
//     localized change -- you rewrite bindings.cpp against the real headers
//     and delete this file.
//
// This is the seam a derived project replaces. See cmake/HandleExternalLibs.cmake.

#ifndef TEMPLATE_EXT_HPP
#define TEMPLATE_EXT_HPP

#include <cstddef>
#include <vector>

namespace template_ext {

/// Euclidean (L2) norm of a sequence of doubles.
///
/// Throws std::invalid_argument when the input is empty, to demonstrate how a
/// C++ exception surfaces on the Python side.
double vector_norm(const std::vector<double>& values);

/// Scale a contiguous buffer in place by a constant factor.
///
/// Takes a raw pointer and a length rather than a container so that the
/// binding layer can hand it a NumPy array's own memory with no copy.
void scale_in_place(double* data, std::size_t count, double factor);

/// Numerically stable streaming mean and variance (Welford's algorithm).
///
/// Exists to give the bindings a stateful class to expose: constructor,
/// mutating method, read-only properties, and a repr.
class RunningStatistics {
public:
    RunningStatistics() = default;

    /// Incorporate one more observation.
    void add(double value);

    /// Incorporate a batch of observations.
    void extend(const std::vector<double>& values);

    /// Number of observations seen so far.
    [[nodiscard]] std::size_t count() const noexcept { return count_; }

    /// Arithmetic mean; 0.0 when no observation has been seen.
    [[nodiscard]] double mean() const noexcept { return mean_; }

    /// Sample variance (Bessel-corrected); 0.0 for fewer than two samples.
    [[nodiscard]] double variance() const noexcept;

    /// Square root of the sample variance.
    [[nodiscard]] double stddev() const noexcept;

    /// Discard all accumulated state.
    void reset() noexcept;

private:
    std::size_t count_ = 0;
    double mean_ = 0.0;
    // Sum of squared deviations from the running mean (Welford's M2).
    double m2_ = 0.0;
};

}  // namespace template_ext

#endif  // TEMPLATE_EXT_HPP
