#include "mylib.h"

#define MYLIB_VERSION_STRING "1.0.0"

const char* mylib_version(void) {
    return MYLIB_VERSION_STRING;
}

const char* mylib_status_message(mylib_status_t status) {
    switch (status) {
        case MYLIB_OK:
            return "ok";
        case MYLIB_ERR_NULL_POINTER:
            return "null pointer argument";
        case MYLIB_ERR_EMPTY_INPUT:
            return "input must contain at least one element";
        default:
            return "unknown error";
    }
}

mylib_status_t mylib_mean(const double* values, size_t count, double* out_mean) {
    size_t index;
    double total = 0.0;

    if (values == NULL || out_mean == NULL) {
        return MYLIB_ERR_NULL_POINTER;
    }
    if (count == 0) {
        return MYLIB_ERR_EMPTY_INPUT;
    }

    for (index = 0; index < count; ++index) {
        total += values[index];
    }

    *out_mean = total / (double)count;
    return MYLIB_OK;
}

mylib_status_t mylib_moving_average(const double* values,
                                    size_t count,
                                    size_t window,
                                    double* out_values) {
    size_t index;

    if (values == NULL || out_values == NULL) {
        return MYLIB_ERR_NULL_POINTER;
    }
    if (count == 0 || window == 0) {
        return MYLIB_ERR_EMPTY_INPUT;
    }

    for (index = 0; index < count; ++index) {
        /* Centred window, clamped at both edges. */
        size_t half = window / 2;
        size_t start = (index > half) ? (index - half) : 0;
        size_t stop = index + half + 1;
        size_t position;
        double total = 0.0;
        size_t used = 0;

        if (stop > count) {
            stop = count;
        }

        for (position = start; position < stop; ++position) {
            total += values[position];
            ++used;
        }

        out_values[index] = total / (double)used;
    }

    return MYLIB_OK;
}
