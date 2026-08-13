# Compiled extensions and external C/C++ libraries

This template ships a working pybind11 extension and three documented ways to
wire an external C or C++ library into it. This page covers the workflow; the
runnable walkthrough is in
[`examples/04_wire_external_c_library/`](https://github.com/PeterCalifano/python_template_project/blob/main/examples/04_wire_external_c_library/README.md).

## How the build fits together

```
pip install .
      |
      v
scikit-build-core                (PEP 517 backend, from [build-system])
      |  injects SKBUILD_PROJECT_NAME / _VERSION / _VERSION_FULL
      v
CMakeLists.txt                   (root; options, standards, visibility)
      |-- cmake/HandlePybind11.cmake      finds Python + pybind11
      |-- cmake/HandleExternalLibs.cmake  wires your external libraries
      v
src/cpp/CMakeLists.txt           tpp_add_extension(_core ...)
      |
      v
_core.<abi>.so  installed INTO  template_python_project/
      |
      v
template_python_project/_accel.py  imports it, or falls back to pure Python
```

The important consequence: **there is no separate build step.** `pip install .`
compiles the extension. A user who clones the repository and runs
`pip install -e .` gets a working compiled package, and a user who installs the
wheel from PyPI gets the same thing precompiled.

## Everyday commands

```bash
./build_ext.sh                       # editable install, compiles the extension
./build_ext.sh --clean --verbose     # from scratch, with full CMake output
./build_ext.sh -D TPP_FETCH_FMT=ON   # enable an external library
pytest                               # run the suite
```

After the first `./build_ext.sh`, `editable.rebuild = true` recompiles changed
C++ automatically on the next import, so the usual loop is *edit, run tests*.

## Passing CMake options

Three routes, in increasing order of locality:

```toml
# 1. Permanent, for everyone: pyproject.toml
[tool.scikit-build.cmake.define]
TPP_USE_SYSTEM_EIGEN = "ON"
```

```bash
# 2. Per install
pip install . -C cmake.define.TPP_USE_SYSTEM_EIGEN=ON

# 3. Per shell, via environment
SKBUILD_CMAKE_DEFINE="TPP_USE_SYSTEM_EIGEN=ON" pip install .
```

Built-in options, all defined in `CMakeLists.txt` and
`cmake/HandleExternalLibs.cmake`:

| Option | Default | Effect |
| --- | --- | --- |
| `TPP_BUILD_EXTENSION` | `ON` | Build the native module at all |
| `TPP_ENABLE_LTO` | `OFF` | Link-time optimization |
| `TPP_WARNINGS_AS_ERRORS` | `OFF` | `-Werror` / `/WX` |
| `TPP_USE_SYSTEM_EIGEN` | `OFF` | Pattern 1 demo (`find_package`) |
| `TPP_FETCH_FMT` | `OFF` | Pattern 2 demo (`FetchContent`) |
| `TPP_USE_VENDORED_LIBS` | `OFF` | Pattern 3 demo (`add_subdirectory`) |

## Wiring an external library

Full commentary lives in
[`cmake/HandleExternalLibs.cmake`](../cmake/HandleExternalLibs.cmake). The
summary:

### Pattern 1 — `find_package()`, the library is installed

```cmake
find_package(Eigen3 3.3 REQUIRED NO_MODULE)
tpp_register_external_target(Eigen3::Eigen)
```

Cheapest option. Prefer `CONFIG` mode so you consume the library's own exported
targets. Use this for anything available from apt, brew, conda, or vcpkg.

### Pattern 2 — `FetchContent`, pinned upstream source

```cmake
FetchContent_Declare(fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG        11.0.2)     # a tag or full SHA, never a branch
FetchContent_MakeAvailable(fmt)
tpp_register_external_target(fmt::fmt-header-only)
```

Use when the library is unpackaged, or when it must be compiled with the same
flags and ABI as your extension. **Always pin.** A branch reference makes the
build non-reproducible and lets an upstream push break your wheels.

### Pattern 3 — `add_subdirectory()`, vendored source

```bash
git submodule add https://github.com/org/mylib.git lib/mylib
git submodule update --init --recursive
pip install . -C cmake.define.TPP_USE_VENDORED_LIBS=ON
```

Every directory under `lib/` with a `CMakeLists.txt` is picked up
automatically. Most control, most reproducible, and the only option for a
private library that cannot be fetched publicly.

### A C library with no CMake support

Wrap it in an `IMPORTED` target once, then treat it like any modern dependency:

```cmake
find_package(PkgConfig REQUIRED)
pkg_check_modules(MYLIB REQUIRED IMPORTED_TARGET mylib>=1.2)
tpp_register_external_target(PkgConfig::MYLIB)
```

The fully manual `find_path`/`find_library` form is documented in
`cmake/HandleExternalLibs.cmake`.

## Writing the bindings

Keep three responsibilities separate, as `src/cpp/` does:

| File | Responsibility |
| --- | --- |
| `template_ext.hpp` / `.cpp` | Real C++ logic. Knows nothing about Python. |
| `bindings.cpp` | Type conversion, docstrings, exception translation. Nothing else. |
| `_accel.py` | Optional import, pure-Python fallback, public API. |

This split is what lets the C++ be reused from other C++, the bindings stay
short enough to read, and the package import without a compiler.

### Exception translation

pybind11 maps standard C++ exceptions to Python ones automatically:

| C++ | Python |
| --- | --- |
| `std::invalid_argument`, `std::domain_error`, `std::out_of_range` | `ValueError` / `IndexError` |
| `std::runtime_error` | `RuntimeError` |
| `std::bad_alloc` | `MemoryError` |

A C library that reports failure by return code needs an explicit translation
step; see `raise_on_error()` in the example bindings.

### NumPy without copying

```cpp
py::buffer_info info = array.request(true);   // true = require writable
auto* data = static_cast<double*>(info.ptr);
{
    py::gil_scoped_release release;           // no Python objects touched
    my_c_function(data, count);
}
```

Validate rather than convert. `py::array::forcecast` silently copies a
mismatched input, which turns an in-place function into a no-op from the
caller's point of view.

### Releasing the GIL

Wrap any long-running native call in `py::gil_scoped_release` so other Python
threads can run. Touching **any** Python object while the GIL is released is
undefined behaviour, so release only around the pure-native section.

## Type stubs

The compiled module carries no type information, so `_core.pyi` is checked in.
Regenerate it after changing the binding surface:

```bash
pybind11-stubgen template_python_project._core -o src/
```

Review the result: stubgen cannot infer which exceptions a function raises, so
those docstring details are added by hand.

## Building a pure-Python project instead

Two different things, often confused:

| What you want | How | Resulting wheel |
| --- | --- | --- |
| Skip the extension for one build | `-C cmake.define.TPP_BUILD_EXTENSION=OFF` | still platform-tagged |
| A genuinely pure-Python project | `wheel.cmake = false` | `py3-none-any` |

For a permanently pure-Python project, use the tailoring script — it removes
the C++ tree and fixes `pyproject.toml` in one step:

```bash
./tailor_template_cleanup.sh --apply --no-extension --yes
```

You can then also drop `pybind11` from `[build-system].requires`, at which
point CMake is no longer a build dependency at all.

## Two traps

Both were hit while writing this template, and both are commented in the source
at the point they matter.

**Static libraries must be position-independent.** Anything linked into a
Python extension (a shared object) needs `POSITION_INDEPENDENT_CODE ON`, or
linking fails with `relocation R_X86_64_PC32 against symbol ... can not be used
when making a shared object`.

**`py::array_t<T> out(count)` yields a zero-stride array.** The single-`ssize_t`
constructor forwards an empty strides container; in pybind11 3.x that produces
stride 0, so the shape looks right but every element reads back as element 0 —
and correct C++ appears to compute nonsense. Use an explicit shape container:

```cpp
py::array_t<double> output(py::array::ShapeContainer{static_cast<py::ssize_t>(count)});
```

## Distributing binary wheels

`.github/workflows/wheels.yml` builds manylinux (x86_64 + aarch64), macOS
(Intel + Apple silicon), and Windows wheels with `cibuildwheel`, on `v*.*.*`
tags or manual dispatch. Configuration lives in `[tool.cibuildwheel]`, including
a post-build check that fails the build if a wheel ships without its extension.

If you link a **shared** third-party library, its `.so`/`.dylib`/`.dll` must
travel inside the wheel. `auditwheel repair` (Linux) and `delocate` (macOS) do
this, and cibuildwheel runs them automatically. `tpp_add_extension` already sets
`$ORIGIN`/`@loader_path` RPATH so a bundled library resolves from beside the
module. Static linking avoids the problem entirely and is the default here.
