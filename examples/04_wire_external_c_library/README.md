# Wiring an external C library

A complete, self-contained miniature of the thing this template exists for:
taking a C library that knows nothing about Python and exposing it as a Python
module.

```bash
./build_and_run.sh
```

That configures CMake, compiles the C library and the bindings, and runs
`demo.py`. Expected output:

```
C library version : 1.0.0
input             : [1.0, 2.0, ..., 8.0]

mean()            : 4.5
numpy reference   : 4.5

moving_average(3) : [1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 7.5]
input unchanged   : [1.0, 2.0, ..., 8.0]

C status codes become Python exceptions:
  empty array (MYLIB_ERR_EMPTY_INPUT)  -> ValueError: mylib: input must contain ...
```

## What is here

| File | Role |
| --- | --- |
| `mylib/mylib.h` | C header: `extern "C"` guard, status-code enum, pointer+length API |
| `mylib/mylib.c` | The implementation. Plain C, no Python awareness |
| `mylib/CMakeLists.txt` | Minimal modern-CMake wrapper exposing `mylib::mylib` |
| `bindings_mylib.cpp` | The pybind11 layer |
| `CMakeLists.txt` | Pattern 3 wiring (`add_subdirectory`) |
| `build_and_run.sh` | Builds and runs the demo |
| `demo.py` | Calls the wrapped library from Python |

## The C library is deliberately awkward

Real C libraries are not written for convenient wrapping, so this one imitates
the usual friction:

- **Status codes instead of exceptions.** `mylib_mean()` returns
  `mylib_status_t` and writes its result through an out-parameter.
- **Pointer + length instead of containers.** No `std::vector`, no ownership.
- **An `extern "C"` guard.** Without it a C++ compiler would mangle the names
  and linking would fail.

The binding layer absorbs all three, so Python callers see an ordinary function
returning a float and raising `ValueError`.

## What the bindings do

Exactly three things, and nothing else:

1. **Include the C header correctly.** `mylib.h` carries its own `extern "C"`
   guard; a header without one must be wrapped at the include site.
2. **Translate errors.** `raise_on_error()` converts each status code into the
   matching Python exception. Letting return codes leak into Python would force
   every caller to check them, which is not how Python is written.
3. **Translate data.** `as_contiguous_1d()` validates a NumPy array and hands C
   a raw pointer into the array's own buffer. Output arrays are allocated as
   NumPy arrays up front, so C writes straight into what Python receives.

The GIL is released around each native call via `py::gil_scoped_release`.

## Two traps this example encodes

Both are real failures hit while writing this template.

**Static libraries must be position-independent.** `mylib/CMakeLists.txt` sets
`POSITION_INDEPENDENT_CODE ON`. Without it, linking the static library into the
extension (a shared object) fails with `relocation R_X86_64_PC32 against
symbol ... can not be used when making a shared object`.

**`py::array_t<double> out(count)` produces a zero-stride array.** The
single-`ssize_t` constructor forwards an *empty strides container*, and in
pybind11 3.x that yields stride 0. The shape looks correct, but every element
reads back as element 0 — so perfectly correct C appears to compute nonsense.
Use an explicit shape container:

```cpp
py::array_t<double> output(py::array::ShapeContainer{static_cast<py::ssize_t>(count)});
```

It is marked `ACHTUNG!` in `bindings_mylib.cpp`, and
`tests/test_examples.py` asserts it stays that way.

## Adapting this to your library

1. Delete `mylib/` and point at your real library instead — usually a git
   submodule under `lib/`, or `find_package()` / `FetchContent` if it is
   installed or fetchable. See [`../../doc/extensions.md`](../../doc/extensions.md).
2. Copy `bindings_mylib.cpp` into `src/cpp/` and rewrite it against your
   headers, keeping the three responsibilities separate.
3. Register the target so the extension links it:
   ```cmake
   tpp_register_external_target(yourlib::yourlib)
   ```
4. Rebuild with `./build_ext.sh` and add tests under `tests/`.

Note that this example builds its own standalone module (`_mylib`) rather than
extending the package's `_core`, so you can run it without touching the rest of
the template.
