#!/usr/bin/env bash
# Build the external-C-library binding example and run its demo.
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
BUILD_DIR="${SCRIPT_DIR}/build"

info() { printf '\033[34m[INFO]\033[0m %s\n' "$*"; }
die() { printf '\033[31m[ERROR]\033[0m %s\n' "$*" >&2; exit 1; }

command -v cmake >/dev/null 2>&1 || die "cmake is required"
command -v "${PYTHON}" >/dev/null 2>&1 || die "python interpreter not found: ${PYTHON}"

"${PYTHON}" -c "import pybind11" >/dev/null 2>&1 \
    || die "pybind11 is not installed. Run: ${PYTHON} -m pip install pybind11"

info "Configuring"
cmake -S "${SCRIPT_DIR}" -B "${BUILD_DIR}" \
      -DCMAKE_BUILD_TYPE=Release \
      -DPython_EXECUTABLE="$(command -v "${PYTHON}")"

info "Building"
cmake --build "${BUILD_DIR}" --parallel

info "Running demo"
"${PYTHON}" "${SCRIPT_DIR}/demo.py"
