# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

**Read [`AGENTS.md`](AGENTS.md) first.** It holds the language standards, the
commit-message style, and the staged-review workflow, and it applies to any
project built from this template. This file adds only what is specific to *this*
repository: its build contract, its architecture, and the traps found while
building it.

## Project overview

Python-first package template (by Pietro Califano) with an optional pybind11
extension for wiring external C/C++ libraries. Uses a `src` layout,
scikit-build-core as the PEP 517 backend, setuptools-scm for git-derived
versioning, and CMake + pybind11 for the compiled part.

The defining constraint: **`pip install .` is the only build entry point.**
scikit-build-core drives CMake from inside PEP 517, so there is no separate
compile step to run first. Anything that makes `pip install .` insufficient to
get a working package is a regression, however convenient it seems.

## Commands

```bash
# Setup (pip >= 25.1 required for --group)
python -m pip install --upgrade pip
python -m pip install --group dev -e .

# Build the extension (editable, fast local loop)
./build_ext.sh
./build_ext.sh --clean --verbose             # from scratch, full CMake output
./build_ext.sh -D TPP_FETCH_FMT=ON           # enable an external library
./build_ext.sh -D TPP_BUILD_EXTENSION=OFF    # skip the native module

# Test
pytest                                       # full suite
pytest -m unit                               # fast offline subset
pytest -m extension                          # native-only tests
./run_tests.sh

# Lint and type-check
ruff check . && ruff format --check .
mypy src tests
pre-commit run --all-files

# Docs
sphinx-build -b html doc doc/_build/html -W

# Package
python -m build && twine check --strict dist/*
```

After the first `./build_ext.sh`, `editable.rebuild = true` recompiles changed
C++ on the next import — the usual loop is just *edit, run tests*.

If an install fails with the uninformative `failed-wheel-build-for-install`,
the cached CMake build directory is usually stale — after a rebase, a branch
switch, or a toolchain change. Run `./build_ext.sh --clean`.

## Architecture

### Build chain

```
pip install .  ->  scikit-build-core  ->  CMakeLists.txt  ->  src/cpp/  ->  _core.so
                          |                                                     |
                   setuptools-scm                              installed INTO the package
                   (version from git tags)                                      |
                                                              _accel.py imports it or falls back
```

`SKBUILD_PROJECT_VERSION_FULL` carries the git-derived version into CMake, so
`_core.__version__` and `package.__version__` cannot disagree. Use `_FULL`, not
`SKBUILD_PROJECT_VERSION` — CMake's `project(VERSION)` truncates PEP 440
suffixes such as `.dev1`.

### Layout

| Path | Role |
| --- | --- |
| `src/template_python_project/` | The importable package |
| `src/template_python_project/_accel.py` | Optional-extension shim + pure-Python fallbacks |
| `src/template_python_project/_core.pyi` | Hand-maintained stubs for the compiled module |
| `src/cpp/template_ext.{hpp,cpp}` | Real C++ logic — **no pybind11 headers** |
| `src/cpp/bindings.cpp` | Binding glue only: types, docstrings, exceptions |
| `cmake/HandlePybind11.cmake` | Python/pybind11 discovery, `tpp_add_extension()` |
| `cmake/HandleExternalLibs.cmake` | The three external-library wiring patterns |
| `lib/` | Vendored external sources / git submodules |
| `examples/` | Runnable usage, incl. a full external-C-library walkthrough |
| `doc/developments/` | Staged development plans (template-only) |

## The fallback contract

`_accel.py` provides a pure-Python implementation for every native function.
This is not optional decoration — the package must import and work with no
extension, and CI enforces it in the `pure-python` job.

When you change native behaviour, change the fallback to match, **including
error messages**. `tests/test_extension.py` pins the two together; if you find
yourself weakening one of those equivalence tests, fix the code instead.

## C++ and binding conventions

- C++17 is the standard. Keep it; the extension must build on manylinux, macOS
  and MSVC.
- `snake_case` for functions and variables, `PascalCase` for types, trailing `_`
  for private members — matching `src/cpp/template_ext.hpp`.
- `ACHTUNG!` marks a critical warning in a comment.
- **Keep binding glue out of the logic.** `template_ext.{hpp,cpp}` must not
  include any pybind11 header. `bindings.cpp` does type conversion, docstrings
  and exception translation, and nothing else.
- Release the GIL (`py::gil_scoped_release`) around any long native call, and
  touch no Python object while it is released.
- Validate NumPy inputs rather than converting them. `py::array::forcecast`
  silently copies, which turns an in-place function into a no-op for the caller.

## Development plans

`CONTEXT.md` holds the working context for the change currently in flight.
Write to it before compaction to prevent context loss, and read it together
with this file when resuming. It is template-development state, so the
tailoring script removes it from a derived project.

Multi-step work gets a tracked plan in `doc/developments/<topic>_plan.md`:
staged, with `- [ ]` checkboxes per step, a **Stop Rule** stating what to do
when a stage cannot be validated, and a **Verification Log** holding real
command output, exit codes and excerpts.

Record what actually happened. If a command failed, the log says so. If a step
was skipped, the log says that too. Never write a verification entry for a
command that was not run, and never tick a checkbox before its verification has
actually passed.

## Testing

Markers are registered in `pyproject.toml`: `unit`, `integration`, `slow`,
`gpu`, `extension`. Native-only tests use the `requires_extension` skip marker
so the suite still passes without a compiler.

### Derived-project test policy

Do **not** copy template-conformance tests into a project derived from this
template. `tests/test_template_conformance.py` validates the template's own
generation and tailoring behaviour; it is not part of a derived project's
contract, and the tailoring script removes it for that reason.

Derived projects should test their own runtime behaviour, and prove packaging
through fresh out-of-tree install/consumer commands rather than by recursively
rebuilding themselves inside their own test suite.

## Things that are easy to get wrong

- **Do not add a `setup.py`.** The build is `pyproject.toml`-only by design.
- **Do not hand-edit `src/template_python_project/_version.py`.** It is
  generated by setuptools-scm and is gitignored.
- **Do not add `pythonpath = ["src"]` to the pytest config.** It shadows the
  installed package with the source tree, which never contains the compiled
  extension, so every native test silently skips while the suite reports green.
- **Do not pin `[tool.mypy] python_version`.** Pinning it makes mypy parse
  third-party stubs under those syntax rules, and modern numpy stubs use PEP 695
  syntax that only 3.12+ can parse. Version coverage comes from the CI matrix.
- **Do not use `py::array_t<T>(count)`** to allocate an output array — the
  single-`ssize_t` constructor yields stride 0 in pybind11 3.x. Use
  `py::array::ShapeContainer{...}`.
- **Do not link a static library without `POSITION_INDEPENDENT_CODE ON`.**
- **Do not pin a `FetchContent` dependency to a branch.** Tag or full SHA only.
- **Do not remove `fetch-depth: 0`** from CI checkouts; setuptools-scm needs the
  tags.

## Before claiming work is done

Run these and paste real output:

```bash
ruff check . && ruff format --check .
mypy src tests
pytest
pip install -e . -C wheel.cmake=false && pytest   # fallback path
python -m build && twine check --strict dist/*
```

Do not report success for a command you did not run.
