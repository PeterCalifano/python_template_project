# Python Template Project

Reusable Python package template with a `src` layout, **optional pybind11
extension for wiring external C/C++ libraries**, modern PEP-compliant packaging,
tests, docs, containers, and CI.

Built on [scikit-build-core](https://scikit-build-core.readthedocs.io/), so
`pip install .` compiles the extension. There is no separate build step — and
with one setting the same template produces a pure-Python package instead.

## Why this template

| | |
| --- | --- |
| **Packaging** | PEP 517/518/621 (`pyproject.toml` only, no `setup.py`), PEP 735 dependency groups, PEP 639 licence expression, PEP 561 typing marker |
| **Versioning** | Single source of truth: git tags, via setuptools-scm. The same version reaches C++, so the two can never disagree |
| **Extensions** | pybind11 + CMake, with three documented ways to wire an external C/C++ library |
| **Degrades gracefully** | The package imports and works with no compiler; CI proves it on every run |
| **Quality gate** | ruff + ruff-format, strict mypy, pytest across 4 Pythons × 3 OSes, pre-commit |
| **Distribution** | cibuildwheel for manylinux/macOS/Windows, PyPI Trusted Publishing (no stored tokens) |

## Quick start

```bash
python -m pip install --upgrade pip        # pip >= 25.1 needed for --group
python -m pip install --group dev -e .     # installs and compiles the extension
pytest
```

Check what you got:

```bash
python -c "import template_python_project as t; print(t.__version__, t.backend_name())"
# 0.3.0.dev1 native
```

Then run the examples:

```bash
python examples/01_pure_python_usage.py
python examples/02_pybind11_extension_usage.py
python examples/03_accelerated_fallback.py
./examples/04_wire_external_c_library/build_and_run.sh
```

## Wiring an external C/C++ library

The main event. Pick the pattern that matches how the library reaches your
machine — all three are documented with worked code in
[`cmake/HandleExternalLibs.cmake`](cmake/HandleExternalLibs.cmake):

| Pattern | Use when | Enable |
| --- | --- | --- |
| `find_package()` | Installed via apt / brew / conda / vcpkg | `-C cmake.define.TPP_USE_SYSTEM_EIGEN=ON` |
| `FetchContent` | Pinned upstream source, built with your flags | `-C cmake.define.TPP_FETCH_FMT=ON` |
| `add_subdirectory()` | Vendored source or git submodule under `lib/` | `-C cmake.define.TPP_USE_VENDORED_LIBS=ON` |

Each gives you a CMake **target**; linking it brings include paths, compile
flags, transitive dependencies, and RPATH along automatically.

[`examples/04_wire_external_c_library/`](examples/04_wire_external_c_library/README.md)
is a complete working miniature: a plain C library with `extern "C"`, opaque
status codes and out-parameters, wrapped with pybind11 so that C status codes
arrive in Python as ordinary `ValueError`s and arrays cross the boundary with
no copy.

Full guide: [`doc/extensions.md`](doc/extensions.md).

## Layout

```
├── src/
│   ├── template_python_project/   # the importable package
│   │   ├── _accel.py              # optional-extension shim + pure-Python fallbacks
│   │   ├── _core.pyi              # stubs for the compiled module
│   │   └── py.typed               # PEP 561
│   └── cpp/
│       ├── template_ext.{hpp,cpp} # real C++ logic (no pybind11 headers)
│       └── bindings.cpp           # binding glue only
├── cmake/                         # pybind11 discovery + external-library wiring
├── lib/                           # vendored external sources / submodules
├── examples/                      # runnable usage, incl. the C-library walkthrough
├── tests/                         # pytest, passing with and without the extension
├── doc/                           # Sphinx docs
├── container/ .devcontainer/      # Python + C/C++ toolchain images
└── CMakeLists.txt                 # driven by scikit-build-core, not run by hand
```

## Common commands

```bash
./build_ext.sh                       # editable install + compile
./build_ext.sh --clean --verbose     # from scratch, full CMake output
./build_ext.sh -D TPP_FETCH_FMT=ON   # turn on an external library

pytest                               # full suite
pytest -m unit                       # fast offline subset

ruff check . && ruff format --check .
mypy src tests
pre-commit run --all-files

sphinx-build -b html doc doc/_build/html -W
python -m build && twine check --strict dist/*
```

After the first `./build_ext.sh`, changed C++ recompiles automatically on the
next import.

## Making it your project

Run the tailoring script from a POSIX environment: Linux or macOS directly, or
WSL on Windows.

```bash
./tailor_template_cleanup.sh --list      # preview, changes nothing

./tailor_template_cleanup.sh --apply \
    --project-name my-cool-lib \
    --package-name my_cool_lib --yes
```

This renames the distribution and import package everywhere and removes the
template-only files. Add `--no-extension` for a pure-Python project — it strips
`src/cpp/`, `cmake/`, and `CMakeLists.txt`, and sets `wheel.cmake = false` so
CMake is no longer a build dependency at all.

Full guide: [`doc/template_usage.md`](doc/template_usage.md).

## Dependency groups

Development tooling uses PEP 735 `[dependency-groups]`, not extras:

```bash
pip install --group dev -e .      # test + lint + ext + release
pip install --group test .        # regular consumer install + tests
pip install --group docs . -C wheel.cmake=false
```

**Requires pip ≥ 25.1** (or uv). `[project.optional-dependencies]` is reserved
for genuine runtime extras, which is why `dev` and `docs` are not there.
Editable native development needs the `ext` group in the active environment;
the `dev` group includes it, and `build_ext.sh` installs it explicitly.

## Versioning and release

Versions come from git tags; nothing to hand-edit.

```bash
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0        # builds wheels and publishes
```

Publishing uses PyPI Trusted Publishing (OIDC), so no API token is stored in the
repository. `release_to_pypi.sh` remains as a token-based local fallback.

Between tags you get e.g. `0.3.0.dev1`: `release-branch-semver` bumps the minor
on non-release branches, and the `+g<sha>` local segment is stripped because
PyPI rejects it.

## Other helpers

- `./run_tests.sh` — pytest through the current interpreter
- `./conda_install.sh` — create or reuse a conda env and install
- `container/Dockerfile.python` — Python + C/C++ toolchain image (CUDA base
  available via `--build-arg`)
- `.devcontainer/` — VS Code dev container with Python and C++ tooling

## Documentation

| Page | Contents |
| --- | --- |
| [`doc/template_usage.md`](doc/template_usage.md) | Renaming, tailoring, versioning, publishing, what CI checks |
| [`doc/extensions.md`](doc/extensions.md) | pybind11 workflow, the three wiring patterns, stubs, wheels |
| [`examples/README.md`](examples/README.md) | What each example demonstrates |
| [`AGENTS.md`](AGENTS.md) | Language, review, and commit conventions inherited by tailored projects |

## Licence

MIT — see [LICENSE](LICENSE).
