# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

**Read [`AGENTS.md`](AGENTS.md) as well** — it holds the conventions and the
list of things that are easy to get wrong. This file is the command reference
and architectural map.

## Project overview

Python-first package template (by Pietro Califano) with an optional pybind11
extension for wiring external C/C++ libraries. Uses a `src` layout,
scikit-build-core as the PEP 517 backend, setuptools-scm for git-derived
versioning, and CMake + pybind11 for the compiled part.

The defining constraint: **`pip install .` is the only build entry point.**
scikit-build-core drives CMake from inside PEP 517, so there is no separate
compile step to run first.

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
pytest --doctest-modules src                 # the docstring Example: blocks
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
`_core.__version__` and `package.__version__` cannot disagree. (Use
`_FULL`, not `SKBUILD_PROJECT_VERSION` — CMake's `project(VERSION)` truncates
PEP 440 suffixes like `.dev1`.)

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

### Key invariants

1. **The package imports without the extension.** `_accel.py` guards the native
   import and provides a pure-Python fallback for every function. CI's
   `pure-python` job enforces this.
2. **Fallback and native behaviour match, including error messages.**
   `tests/test_extension.py` pins them together.
3. **The version has a single source**: git tags.
4. **No `setup.py`.** `pyproject.toml` only.

## Conventions

- Python: PEP 8, mandatory type hints, Google docstrings, floor 3.10.
- C++: C++17, logic separated from bindings, `ACHTUNG!` marks critical warnings.
- Options are prefixed `TPP_` and default to `OFF` (except `TPP_BUILD_EXTENSION`).
- Version format: git tag `vX.Y.Z`; between tags, `X.Y+1.0.devN`
  (`release-branch-semver`, no local segment).

## Before claiming completion

Run the full gate and paste real output — see the checklist at the end of
`AGENTS.md`. Do not report success for a command you did not run.
