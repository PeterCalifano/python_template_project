# Examples

Runnable placeholders showing how to use this template, from the pure-Python
surface through to wrapping a real external C library. Every example prints its
output, so you can check it against what the docs claim.

Run them from the repository root after installing the package.

| Example | Needs a compiler? | Shows |
| --- | --- | --- |
| [`01_pure_python_usage.py`](01_pure_python_usage.py) | no | The public API, version metadata, error handling |
| [`02_pybind11_extension_usage.py`](02_pybind11_extension_usage.py) | yes | The raw pybind11 binding surface: free functions, a bound class, zero-copy NumPy, exception translation |
| [`03_accelerated_fallback.py`](03_accelerated_fallback.py) | optional | The optional-acceleration pattern: same API, native or pure-Python backend, with a timing comparison |
| [`04_wire_external_c_library/`](04_wire_external_c_library/) | yes | **Wrapping an external C library end to end** — the main event |
| [`gpu/`](gpu/) | n/a | Where project-specific GPU/Jetson setup notes belong |

## Quick start

```bash
# Pure-Python only -- no compiler needed
pip install -e .
python examples/01_pure_python_usage.py

# With the compiled extension
./build_ext.sh
python examples/02_pybind11_extension_usage.py
python examples/03_accelerated_fallback.py

# The external C library walkthrough (self-contained; builds its own module)
./examples/04_wire_external_c_library/build_and_run.sh
```

## Example 4: wiring an external C/C++ library

This is the one to read if you came here to wrap an existing library. It is a
complete, self-contained miniature of the real thing:

```
04_wire_external_c_library/
├── mylib/                 # a plain C library that knows nothing about Python
│   ├── mylib.h            #   extern "C" guard, opaque status codes
│   ├── mylib.c            #   pointer + length API, out-parameters
│   └── CMakeLists.txt     #   minimal modern-CMake wrapper around it
├── bindings_mylib.cpp     # the pybind11 layer: types in, exceptions out
├── CMakeLists.txt         # Pattern 3 wiring (add_subdirectory)
├── build_and_run.sh       # builds and runs the demo
└── demo.py                # calls the wrapped library from Python
```

Run it and you will see the C library's own version, a scalar computed through
a C out-parameter, an array-in/array-out call with no intermediate copy, and C
status codes arriving as ordinary Python `ValueError`s.

### The three wiring patterns

All three are documented with worked code in
[`cmake/HandleExternalLibs.cmake`](../cmake/HandleExternalLibs.cmake). Pick by
how the library reaches your machine:

| Pattern | Use when | Enable with |
| --- | --- | --- |
| `find_package()` | The library is installed (apt, brew, conda, vcpkg) | `-C cmake.define.TPP_USE_SYSTEM_EIGEN=ON` |
| `FetchContent` | You want a pinned upstream source built with your flags | `-C cmake.define.TPP_FETCH_FMT=ON` |
| `add_subdirectory()` | The source is vendored here, usually a git submodule | `-C cmake.define.TPP_USE_VENDORED_LIBS=ON` |

Whichever you choose, the payoff is identical: you get a CMake **target**, and
linking that one target brings include paths, compile flags, transitive
dependencies, and RPATH along with it. That is why this goes through CMake
rather than hand-written `-I`/`-L`/`-l` flags.

### Adapting it to your library

1. Replace `mylib/` with your library — or delete it and switch to
   `find_package()` / `FetchContent` in `cmake/HandleExternalLibs.cmake`.
2. Copy `bindings_mylib.cpp` into `src/cpp/`, and rewrite it against your real
   headers. Keep the three responsibilities separate: include correctly,
   convert types, translate errors.
3. Register the library's target so the extension links it:
   `tpp_register_external_target(yourlib::yourlib)`.
4. Rebuild with `./build_ext.sh` and add tests under `tests/`.

### Two traps worth knowing about

Both are real failures that this template hit while being written, and both are
commented at the point they matter in the source.

**Position-independent code.** A static library linked into a Python extension
(a shared object) must be compiled with `POSITION_INDEPENDENT_CODE ON`.
Without it, linking fails with `relocation R_X86_64_PC32 against symbol ...
can not be used when making a shared object`. See `mylib/CMakeLists.txt`.

**`py::array_t<double> out(count)` produces a zero-stride array.** The
single-`ssize_t` constructor forwards an *empty strides container*, and in
pybind11 3.x that yields stride 0 — the shape looks correct, but every element
reads back as element 0, so the C code appears to have computed nonsense while
being perfectly correct. Construct with an explicit shape container instead:

```cpp
py::array_t<double> output(py::array::ShapeContainer{static_cast<py::ssize_t>(count)});
```

See `bindings_mylib.cpp`, where this is marked `ACHTUNG!`.
