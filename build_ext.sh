#!/usr/bin/env bash
# Fast local edit/compile/test loop for the pybind11 extension.
#
# Installs the package editable with build isolation disabled, so CMake reuses
# a persistent build directory instead of reconfiguring from scratch each time.
# After the first run, `editable.rebuild = true` in pyproject.toml recompiles
# changed sources automatically on import -- so you usually run this once.

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

PYTHON="${PYTHON:-python3}"
BUILD_DIR="build/dev"
CMAKE_DEFINES=()
VERBOSE=0
CLEAN=0

info() { printf '\033[34m[INFO]\033[0m %s\n' "$*"; }
die() { printf '\033[31m[ERROR]\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
    cat <<'USAGE'
Usage: ./build_ext.sh [options]

Options:
  -c, --clean            Remove the build directory before building
  -v, --verbose          Verbose CMake and compiler output
  -D KEY=VALUE           Pass a CMake define (repeatable)
                         e.g. -D TPP_USE_SYSTEM_EIGEN=ON
  -p, --python PATH      Python interpreter to use (default: python3)
  -h, --help             Show this help

Examples:
  ./build_ext.sh                              # build and install editable
  ./build_ext.sh --clean --verbose            # clean rebuild, full output
  ./build_ext.sh -D TPP_FETCH_FMT=ON          # enable an external library
  ./build_ext.sh -D TPP_BUILD_EXTENSION=OFF   # pure-Python install
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -c|--clean) CLEAN=1; shift ;;
        -v|--verbose) VERBOSE=1; shift ;;
        -D) [[ $# -ge 2 ]] || die "-D requires KEY=VALUE"; CMAKE_DEFINES+=("$2"); shift 2 ;;
        -p|--python) [[ $# -ge 2 ]] || die "--python requires a path"; PYTHON="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) die "Unknown option: $1 (try --help)" ;;
    esac
done

command -v "${PYTHON}" >/dev/null 2>&1 || die "Python interpreter not found: ${PYTHON}"

if [[ ${CLEAN} -eq 1 ]]; then
    # Only ever remove the conventional in-repository build path.
    if [[ -d "${BUILD_DIR}" ]]; then
        info "Removing ${BUILD_DIR}"
        rm -rf "${BUILD_DIR}"
    fi
fi

info "Ensuring build dependencies are present"
"${PYTHON}" -m pip install --upgrade --quiet pip
"${PYTHON}" -m pip install --quiet "scikit-build-core>=0.11" "pybind11>=2.13,<4" "setuptools-scm>=8"

PIP_ARGS=(--no-build-isolation -e . -C "build-dir=${BUILD_DIR}")

for define in "${CMAKE_DEFINES[@]:-}"; do
    [[ -n "${define}" ]] || continue
    PIP_ARGS+=(-C "cmake.define.${define}")
done

if [[ ${VERBOSE} -eq 1 ]]; then
    PIP_ARGS+=(-C logging.level=INFO -C build.verbose=true -v)
fi

info "Building: pip install ${PIP_ARGS[*]}"
"${PYTHON}" -m pip install "${PIP_ARGS[@]}"

info "Verifying import"
"${PYTHON}" - <<'PYCHECK'
import template_python_project as tpp

print(f"  version : {tpp.__version__}")
print(f"  backend : {tpp.backend_name()}")
print(f"  ext     : {tpp.HAS_EXTENSION}")
PYCHECK

info "Done. Run ./run_tests.sh to execute the test suite."
