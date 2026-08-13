#include "template_ext.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace template_ext {

double vector_norm(const std::vector<double>& values) {
    if (values.empty()) {
        // pybind11 maps std::invalid_argument to Python's ValueError, so this
        // reaches the caller as a normal, catchable Python exception.
        throw std::invalid_argument("vector_norm requires at least one value");
    }

    // Two-pass scaled computation: dividing by the largest magnitude before
    // squaring avoids overflow for large inputs and underflow for tiny ones,
    // which a naive sum of squares would silently get wrong.
    double max_magnitude = 0.0;
    for (const double value : values) {
        max_magnitude = std::max(max_magnitude, std::abs(value));
    }

    if (max_magnitude == 0.0) {
        return 0.0;
    }

    double accumulated = 0.0;
    for (const double value : values) {
        const double scaled = value / max_magnitude;
        accumulated += scaled * scaled;
    }

    return max_magnitude * std::sqrt(accumulated);
}

void scale_in_place(double* data, const std::size_t count, const double factor) {
    if (data == nullptr && count != 0) {
        throw std::invalid_argument("scale_in_place received a null buffer");
    }

    for (std::size_t index = 0; index < count; ++index) {
        data[index] *= factor;
    }
}

void RunningStatistics::add(const double value) {
    // Welford's online algorithm: updates mean and M2 in one pass without
    // ever forming the catastrophically cancelling sum-of-squares.
    ++count_;
    const double delta = value - mean_;
    mean_ += delta / static_cast<double>(count_);
    const double delta_after = value - mean_;
    m2_ += delta * delta_after;
}

void RunningStatistics::extend(const std::vector<double>& values) {
    for (const double value : values) {
        add(value);
    }
}

double RunningStatistics::variance() const noexcept {
    if (count_ < 2) {
        return 0.0;
    }
    return m2_ / static_cast<double>(count_ - 1);
}

double RunningStatistics::stddev() const noexcept {
    return std::sqrt(variance());
}

void RunningStatistics::reset() noexcept {
    count_ = 0;
    mean_ = 0.0;
    m2_ = 0.0;
}

}  // namespace template_ext
