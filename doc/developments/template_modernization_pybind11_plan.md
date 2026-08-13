# Template Modernization and pybind11 Interface

## Context

`python_template_project` is the Python-first counterpart to
`cpp_cuda_template_project`, but it has drifted behind its siblings. It has no
agent-facing documentation, no staged-development convention, no tailoring
script (its own `TODO` item #1), a dead `cython_src/` placeholder, and a build
backend (`hatchling`) that **cannot compile extension modules at all**.

The goal is twofold:

1. Import the practices that already work in the sibling templates
   (`cpp_cuda_template_project`, `TheJuliaPlayground`, `opencl-interface`),
   adapted to a Python-first repository.
2. Add a first-class pybind11 interface so external C/C++ libraries can be wired
   in with `find_package` / `FetchContent` / submodule, without ever breaking
   plain `pip install .`.

Packaging must stay PEP-compliant and modern: PEP 517/518/621 (`pyproject.toml`
only, no `setup.py`), PEP 735 dependency groups, PEP 561 typing marker, PEP 621
metadata, and PEP 639 licence expressions.

### Why scikit-build-core replaces hatchling

`hatchling` has no extension-module support, so pybind11 forces a backend
change. `scikit-build-core` was verified to cover every capability currently
relied upon:

| Capability            | Today (hatchling)          | After (scikit-build-core)                                        |
| --------------------- | -------------------------- | ---------------------------------------------------------------- |
| Version from git tags | `hatch-vcs`                | `metadata.version.provider = "scikit_build_core.metadata.setuptools_scm"` |
| Version file          | `hatch.build.hooks.vcs`    | `[tool.setuptools_scm] write_to`                                  |
| sdist contents        | `hatch.build.targets.sdist`| `sdist.include` / `sdist.exclude`                                 |
| wheel packages        | `hatch.build.targets.wheel`| `wheel.packages`                                                  |
| `python -m build`     | yes                        | yes (PEP 517, backend-agnostic)                                   |
| twine / PyPI publish  | yes                        | yes (backend-agnostic)                                            |
| Editable install      | yes                        | yes, plus `editable.rebuild = true` for the compiled module       |
| Pure-Python mode      | n/a                        | `wheel.cmake = false` — CMake is then **not** a build dependency  |

`hatch-vcs` is itself a thin wrapper over `setuptools-scm`, so the existing
`src/template_python_project/_version.py` (already setuptools-scm generated) is
a drop-in. Bonus: `${SKBUILD_PROJECT_VERSION}` feeds the same git-derived
version into CMake, so the C++ and Python sides cannot drift.

### Decisions taken

- Python floor stays `>=3.10`; dev/docs/test tooling moves to PEP 735
  `[dependency-groups]`, and `[project.optional-dependencies]` is reserved for
  genuine **runtime** extras only (correct semantics, no duplication).
- Example code follows standard PEP 8 (`snake_case` functions and methods,
  `PascalCase` classes, `_private` prefix) — ruff `N` rules stay enabled.
- Imported from siblings: agent docs, the `doc/developments/` staged-plan
  convention, a tailoring/rename script, dev-hygiene tooling, and a
  devcontainer / Docker / CI stack built for Python apps that may carry C/C++
  through pybind11.

## Stop Rule

If a stage cannot be validated honestly, stop immediately and record the failing
command, exit code, output excerpt, suspected owner, and next action in the
Verification Log below before reporting.

## Target Layout

```
python_template_project/
├── AGENTS.md  CLAUDE.md  CONTEXT.md      # new: agent-facing docs
├── CMakeLists.txt                        # new: root, drives the extension
├── pyproject.toml                        # rewritten: scikit-build-core + PEP 735
├── .pre-commit-config.yaml               # new
├── tailor_template_cleanup.sh            # new: rename + strip template-only files
├── build_ext.sh                          # new: local extension dev loop
├── run_tests.sh  conda_install.sh  release_to_pypi.sh
├── cmake/
│   ├── HandlePybind11.cmake              # new: pybind11 discovery + module macro
│   └── HandleExternalLibs.cmake          # new: 3 documented wiring patterns
├── src/
│   ├── template_python_project/
│   │   ├── __init__.py  core.py  _version.py
│   │   ├── py.typed                      # new: PEP 561
│   │   ├── _accel.py                     # new: optional-extension import shim
│   │   └── _core.pyi                     # new: stubs for the compiled module
│   └── cpp/                              # new: replaces src/*/cython_src/
│       ├── CMakeLists.txt
│       ├── bindings.cpp                  # PYBIND11_MODULE(_core, m)
│       ├── template_ext.cpp / .hpp       # example native implementation
│       └── README.md
├── lib/                                  # existing: external sources / submodules
├── tests/
│   ├── test_smoke.py
│   ├── test_extension.py                 # new: skipped when ext absent
│   └── test_template_conformance.py      # new: template-only self-checks
├── doc/
│   ├── developments/                     # new: this plan lives here
│   ├── template_usage.md  extensions.md  # new
│   └── conf.py  index.rst  api.rst
├── .github/
│   ├── workflows/{ci,wheels,docs_pages}.yml
│   ├── ISSUE_TEMPLATE/{bug_report,feature_request,config}.yml
│   └── pull_request_template.md
├── container/Dockerfile.python           # updated: + toolchain
└── .devcontainer/devcontainer.json       # updated: + C++ tooling
```

---

## Stage 0 — Baseline

- [x] Create branch `feat/scikit-build-core-pybind11-modernization`.
- [x] Record the current baseline: `python -m pytest -q`, `ruff check .`,
      `mypy src tests`, `python -m build`. Save output to the Verification Log.
- [x] Confirm `git describe --tags` resolves, so setuptools-scm has a version
      source (the repo currently has no `v*.*.*` tag — if absent, note that the
      `fallback_version` path is the one under test).

## Stage 1 — Packaging backend migration

- [x] Rewrite `[build-system]` in `pyproject.toml`:
      `requires = ["scikit-build-core>=0.11", "pybind11>=2.13,<4", "setuptools-scm>=8"]`,
      `build-backend = "scikit_build_core.build"`.
- [x] Replace the three `[tool.hatch.*]` blocks with `[tool.scikit-build]`:
      `minimum-version = "build-system.requires"`, `build-dir = "build/{wheel_tag}"`,
      `wheel.packages = ["src/template_python_project"]`,
      `metadata.version.provider = "scikit_build_core.metadata.setuptools_scm"`,
      `sdist.include = ["src/template_python_project/_version.py"]`,
      `sdist.exclude = ["build/", "dist/", "doc/_build/", "**/__pycache__/"]`,
      `editable.rebuild = true`, `editable.verbose = false`.
- [x] Add `[tool.setuptools_scm]` with
      `write_to = "src/template_python_project/_version.py"`,
      `fallback_version = "0.1.0"`, and `tag_regex`/`local_scheme` mirroring the
      working configuration in `../opencl-interface/pyproject.toml`.
- [x] Migrate `dev`, `docs` from `[project.optional-dependencies]` to PEP 735
      `[dependency-groups]`, split into `test`, `lint`, `docs`, `ext`, and a
      `dev` group that composes them with `{ include-group = ... }`.
- [x] Keep only genuine runtime extras in `[project.optional-dependencies]`
      (rename `cuda_related` → `cuda`; PEP 685 requires normalized extra names,
      so the underscore form is non-conforming).
- [x] Switch `license = { text = "MIT" }` to the PEP 639 form
      `license = "MIT"` + `license-files = ["LICENSE"]`; drop the now-redundant
      `License ::` classifier. Add `Programming Language :: Python :: 3.13`.
- [x] Add `[project.urls]` (Homepage / Repository / Documentation / Issues).
- [x] **Document the pip floor**: `pip install --group dev` needs pip ≥ 25.1.
      Update `run_tests.sh` and `conda_install.sh` to `pip install --upgrade pip`
      first, and state the requirement in `README.md`.

**Verify:** `python -m build` produces both sdist and wheel; `pip install -e .`
succeeds; `python -c "import template_python_project as p; print(p.__version__)"`
prints a git-derived version; `tar tf dist/*.tar.gz` shows `_version.py` present
and `build/` absent.

## Stage 2 — pybind11 extension and external-library wiring

- [x] Add root `CMakeLists.txt`:
      `cmake_minimum_required(VERSION 3.20...3.31)`,
      `project(${SKBUILD_PROJECT_NAME} VERSION ${SKBUILD_PROJECT_VERSION} LANGUAGES CXX)`,
      `set(CMAKE_CXX_STANDARD 17)`, option `TPP_BUILD_EXTENSION` (default `ON`),
      then `add_subdirectory(src/cpp)`.
- [x] Add `cmake/HandlePybind11.cmake` — `set(PYBIND11_FINDPYTHON ON)`,
      `find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)`,
      `find_package(pybind11 CONFIG REQUIRED)`. Discovery works because
      scikit-build-core sets `search.site-packages = true` and pybind11 is in
      `build-system.requires`.
- [x] Add `cmake/HandleExternalLibs.cmake` documenting and demonstrating the
      three wiring patterns, each behind an `option()` so they are inert by
      default:
      1. `find_package(Foo CONFIG REQUIRED)` — system/conda-installed library;
      2. `FetchContent_Declare(... GIT_TAG <pinned>)` — pinned upstream source;
      3. `add_subdirectory(lib/foo)` — vendored git submodule under `lib/`.
- [x] Add `src/cpp/bindings.cpp` with `PYBIND11_MODULE(_core, m)` exposing a
      small but non-trivial surface: a free function, a bound class with
      properties, a `py::array_t<double>` zero-copy NumPy path, and
      `m.attr("__version__") = VERSION_INFO` fed from `${PROJECT_VERSION}`.
- [x] Add `src/cpp/template_ext.{hpp,cpp}` as the "real" native implementation
      the bindings call into — this is the seam a derived project replaces with
      its actual external library.
- [x] `src/cpp/CMakeLists.txt`: `pybind11_add_module(_core MODULE ...)`,
      `target_compile_definitions(_core PRIVATE VERSION_INFO=${PROJECT_VERSION})`,
      `install(TARGETS _core DESTINATION template_python_project)` — the `.so`
      lands **inside** the Python package.
- [x] Delete `src/template_python_project/cython_src/` and its README mention;
      pybind11 supersedes it.
- [x] Add `build_ext.sh` — thin wrapper over
      `pip install --no-build-isolation -ve . -C build-dir=build` for a fast
      local edit/compile/import loop.
- [x] Document the pure-Python escape hatch in `doc/extensions.md`: set
      `wheel.cmake = false` and drop `pybind11`/CMake from `build-system.requires`.

**Verify:** `pip install -e .` compiles `_core`;
`python -c "from template_python_project import _core; print(_core.__version__)"`;
touch a `.cpp` file, re-import, and confirm `editable.rebuild` recompiles;
`auditwheel show dist/*.whl` (in the manylinux CI job) reports a valid tag.

## Stage 3 — Python-side integration

- [x] Add `src/template_python_project/py.typed` (PEP 561).
- [x] Add `_accel.py`: a documented shim that imports `_core` inside
      `try/except ImportError`, exposes `HAS_EXTENSION: bool`, and provides a
      pure-Python fallback so the package **imports cleanly with no extension**.
- [x] Re-export the accelerated entry points from `__init__.py`, keeping
      `hello()` and `__version__` intact so existing consumers do not break.
- [x] Add `_core.pyi` stubs; add `pybind11-stubgen` to the `ext` dependency
      group and document the regeneration command.
- [x] Add `tests/test_extension.py` covering: the shim's fallback path, native
      vs. pure-Python numerical agreement, the NumPy zero-copy round-trip, and
      an exception-translation check. Guard with
      `pytest.importorskip("template_python_project._core")` and the existing
      `unit` / `integration` markers.
- [x] Populate `examples/` with runnable usage placeholders (currently only a
      `.gitkeep` and `gpu/README.md`):
      - `examples/01_pure_python_usage.py` — the pure-Python API surface;
      - `examples/02_pybind11_extension_usage.py` — calling the native `_core`
        module directly, the bound class, and the NumPy zero-copy path, with a
        graceful message when the extension is absent;
      - `examples/03_accelerated_fallback.py` — the `HAS_EXTENSION` shim showing
        identical results on both paths plus a timing comparison;
      - `examples/04_wire_external_c_library/` — a self-contained miniature C
        library (`mylib.c` / `mylib.h` / `CMakeLists.txt`) plus the pybind11
        binding and a `README.md` walking through all three CMake wiring
        patterns end to end;
      - `examples/README.md` — index and run instructions.
      Every example prints its output, so the docstrings can show expected
      results.

**Verify:** `pytest -q` passes with the extension built; `pytest -q` still
passes after `pip install --no-deps .` with `TPP_BUILD_EXTENSION=OFF` (fallback
path exercised); `mypy src tests` is clean.

## Stage 4 — Tooling and hygiene

- [x] Expand `[tool.ruff.lint] select` from `["E","F","I"]` to
      `["E","F","I","W","B","UP","SIM","RUF","N","C4","PT","PTH","TID","ANN","D"]`,
      with `[tool.ruff.lint.pydocstyle] convention = "google"` and a
      `per-file-ignores` entry relaxing `D`/`ANN` for `tests/`.
- [x] Enable `[tool.ruff.format]` and wire `ruff format --check` into CI.
- [x] Tighten mypy: add `strict = true`, then a
      `[[tool.mypy.overrides]] module = "template_python_project._core"` block
      with `ignore_missing_imports = true` as the stub-gap escape valve.
- [x] Add `--strict-markers` and `--strict-config` to pytest `addopts`.
- [x] Add `.pre-commit-config.yaml`: `ruff` + `ruff-format`, `mypy`,
      `check-yaml`/`check-toml`/`end-of-file-fixer`/`trailing-whitespace`,
      `cmake-format`, and `validate-pyproject`.
- [x] Extend `.gitignore` for `build/{wheel_tag}/`, `_skbuild/`, `compile_commands.json`,
      `*.pyi.bak`, and `.cache/`.

**Verify:** `pre-commit run --all-files` passes; `ruff check .`,
`ruff format --check .`, `mypy src tests` all clean.

## Stage 5 — Container and devcontainer for Python + C++

- [x] Rewrite `container/Dockerfile.python`: keep a slim Python base, add
      `build-essential cmake ninja-build ccache gdb pkg-config git`, set
      `CMAKE_GENERATOR=Ninja` and a ccache dir, and pre-create a venv so the
      devcontainer install is fast and non-root-safe.
- [x] Add a second stage or a documented `--build-arg` for CUDA-capable bases,
      mirroring how `cpp_cuda_template_project/.devcontainer/cuda-setup.sh`
      keeps GPU setup off the default path.
- [x] Update `.devcontainer/devcontainer.json`: add `ms-vscode.cpptools`,
      `ms-vscode.cmake-tools`, `ms-python.debugpy`, `tamasfe.even-better-toml`;
      set `"postCreateCommand"` to `pip install --upgrade pip && pip install --group dev -e .`;
      add `cmake.configureOnOpen: false` and
      `C_Cpp.default.compileCommands` pointing at the scikit-build build dir.
- [x] Refresh `.vscode/settings.json` and `.vscode/c_cpp_properties.json` to
      match (compile_commands path, pytest args, ruff as formatter).

**Verify:** `docker build -f container/Dockerfile.python .` succeeds; inside the
container `pip install -e .` compiles the extension and `pytest -q` passes.

## Stage 6 — CI/CD

- [x] Rewrite `.github/workflows/build_test_wheel.yml` → `ci.yml`:
      matrix `python-version: [3.10, 3.11, 3.12, 3.13]` × `os: [ubuntu, macos, windows]`
      (fail-fast off), steps = upgrade pip → `pip install --group dev -e .` →
      `ruff check` → `ruff format --check` → `mypy` → `pytest` with coverage
      upload. Add `concurrency` cancel-in-progress and `permissions: contents: read`.
- [x] Add `.github/workflows/wheels.yml` using `pypa/cibuildwheel`: builds
      manylinux / macOS (x86_64 + arm64) / Windows wheels plus the sdist on tags
      `v*.*.*` and on `workflow_dispatch`; uploads artifacts. Configure
      `[tool.cibuildwheel]` in `pyproject.toml` with `test-command = "pytest {project}/tests"`
      and `test-groups = ["test"]`.
- [x] Add a `publish` job gated on tags using **PyPI Trusted Publishing (OIDC)**
      via `pypa/gh-action-pypi-publish`, with `permissions: id-token: write` and
      a `pypi` environment. Reduce `release_to_pypi.sh` to a documented local
      fallback and note that the token path is now the secondary route.
- [x] Add `.github/workflows/docs_pages.yml` modelled on
      `cpp_cuda_template_project/.github/workflows/docs_pages.yml`: build Sphinx,
      verify `doc/_build/html/index.html` exists, upload the Pages artifact, and
      deploy only on the default branch or explicit `workflow_dispatch` input.
- [x] Add `.github/ISSUE_TEMPLATE/{bug_report.yml,feature_request.yml,config.yml}`
      and `pull_request_template.md`, adapted from the cpp template.

**Verify:** `act` or a pushed branch shows the CI matrix green; the wheels job
produces one sdist and ≥ 3 platform wheels; `twine check dist/*` passes.

## Stage 7 — Documentation and agent-facing files

- [x] Add `AGENTS.md` — Python-first house rules: the PEP 8 convention chosen
      here, mandatory type hints, dataclasses over dicts, enums over Literals,
      the `doc/developments/` staged-plan protocol, and the derived-project test
      policy adapted from `cpp_cuda_template_project/AGENTS.md` (do **not**
      import template-conformance tests into derived projects).
- [x] Add `CLAUDE.md` — build/test/lint command reference, architecture summary,
      and a pointer to `AGENTS.md`.
- [x] Add `CONTEXT.md` — pre-compaction context file, same protocol the sibling
      template uses.
- [x] Add `doc/template_usage.md` (what to rename, how to tailor) and
      `doc/extensions.md` (pybind11 workflow, the three external-library wiring
      patterns, stub regeneration, pure-Python opt-out).
- [x] Add `doc/index.rst` entries for the new pages and keep `doc/api.rst`
      working with the compiled module (`autodoc_mock_imports` for `_core` when
      docs build without a compiler).
- [x] Rewrite `README.md`: new quick start (`pip install --group dev -e .`),
      the pybind11 story, the pure-Python opt-out, and the tailoring command.
- [x] Clear the completed entries from `TODO` and leave only what remains.

**Verify:** `sphinx-build -b html doc doc/_build/html -W` succeeds with warnings
as errors; every internal link in `README.md` resolves.

## Stage 8 — Tailoring script

- [x] Add `tailor_template_cleanup.sh`, structured after
      `../TheJuliaPlayground/tailor_template_cleanup.sh` (the simpler of the two
      donors) with `--list` / `--apply` / `--yes` / `--root` and the same
      `info`/`warn`/`die` helpers and `trap` cleanup.
- [x] `--project-name <dist>` / `--package-name <import>` rename the
      distribution and import package in one step, updating `pyproject.toml`,
      `src/<pkg>/`, `doc/conf.py`, `doc/api.rst`, `tests/`, `CMakeLists.txt`,
      `src/cpp/CMakeLists.txt`, `.github/workflows/`, `conda_install.sh`, and
      `*.code-workspace`. **This closes `TODO` item #1.**
- [x] `--no-extension` strips the pybind11 stack: removes `src/cpp/`, `cmake/`,
      the root `CMakeLists.txt`, sets `wheel.cmake = false`, and drops
      `pybind11` from `build-system.requires`.
- [x] Template-development-only paths removed on `--apply`: `AGENTS.md`,
      `CLAUDE.md`, `CONTEXT.md`, `TODO`, `doc/developments/`,
      `tests/test_template_conformance.py`, `python_template_project.code-workspace`.
- [x] Add `tests/test_template_conformance.py` (template-only): asserts
      `--list` is non-destructive, that a `--apply` dry run in a temporary copy
      leaves no `template_python_project` string behind, and that
      `pyproject.toml` parses and declares the expected backend.

**Verify:** copy the repo to a temp dir, run
`./tailor_template_cleanup.sh --apply --project-name demo-pkg --package-name demo_pkg --yes`,
then `pip install -e .` and `pytest -q` inside the tailored copy; repeat with
`--no-extension` and confirm no compiler is invoked.

## Stage 9 — Final verification and handoff

- [x] Run the full gate from a clean clone: `pip install --group dev -e .`,
      `ruff check .`, `ruff format --check .`, `mypy src tests`, `pytest`,
      `python -m build`, `twine check dist/*`, `sphinx-build -W`.
- [x] Verify the built wheel in a fresh venv with an empty `LD_LIBRARY_PATH`,
      matching the isolated-import discipline recorded in
      `cpp_cuda_template_project/CONTEXT.md`.
- [x] Fill in the Verification Log below with real command output.
- [x] Propose a dependency-ordered commit split; do not commit or push without
      explicit approval.

---

## Verification Log

_(populated during execution — each entry records command, exit code, and an
output excerpt)_

- [x] **Stage 0 baseline** — all green before any change.
  - `git describe --tags` → 0 → `v0.2.0-1-g28a287f` (tags `v0.1.0`, `v0.2.0` exist).
  - `python3 -m venv .venv && pip install --upgrade pip` → 0 → pip 26.2.1
    (above the PEP 735 `--group` floor of 25.1).
  - `pip install -e '.[dev,docs]'` → 0; `import template_python_project` →
    `0.2.1.dev1+g28a287fea`.
  - `pytest -q` → 0 → `1 passed`, coverage 100% over 16 statements.
  - `ruff check .` → 0 → `All checks passed!`.
  - `mypy src tests` → 0 → `Success: no issues found in 4 source files`.
  - `python -m build` → 0 → built
    `template_python_project-0.2.1.dev1+g28a287fea.d20260812` sdist + py3-none-any wheel.
  - Local toolchain probe: `cmake` 3.28.3, `ninja`, `g++`, `numpy` present;
    `ruff`/`mypy`/`build`/`pybind11`/`scikit_build_core` absent from system
    Python (venv-only from here on).
- [x] **Stage 1 packaging** — `hatchling` -> `scikit-build-core`.
  - `python -m build` -> 0 -> `template_python_project-0.3.0.dev1.tar.gz` +
    `...-cp312-cp312-linux_x86_64.whl` (a real platform wheel, previously `py3-none-any`).
  - `twine check --strict dist/*` -> 0 -> both PASSED.
  - `pip install --group dev` -> 0 on pip 26.2.1; pytest/mypy/build/pybind11/
    pybind11-stubgen/twine/ruff all resolved. PEP 735 confirmed working.
  - `pip wheel . -C wheel.cmake=false` -> `py3-none-any` wheel, confirming the
    pure-Python mode drops CMake as a build dependency.
  - Version moved from `0.2.1.dev1+g28a287fea` to `0.3.0.dev1`: expected, from
    `release-branch-semver` (minor bump off a release branch) plus
    `local_scheme = "no-local-version"` (PyPI rejects `+g<sha>`).

- [x] **Stage 2 extension** — pybind11 module builds and imports.
  - `./build_ext.sh` -> 0 -> `version 0.3.0.dev1 / backend native / ext True`.
  - **Bug found and fixed**: `_core.__version__` was `'"0.3.0"'` — two defects
    in one line. CMake's `project(VERSION)` truncated `.dev1`, and an
    already-quoted `VERSION_INFO` was stringified again. Verified via
    `CMakeCache.txt`: `SKBUILD_PROJECT_VERSION=0.3.0` vs
    `SKBUILD_PROJECT_VERSION_FULL=0.3.0.dev1`. Fixed by using `_FULL` and
    consuming the macro directly. Now asserted by
    `test_extension_version_matches_package`.

- [x] **Stage 3 Python integration** — both backends verified.
  - Native: `pytest -q` -> 0 -> **36 passed**.
  - Fallback in a fresh venv with `env -u LD_LIBRARY_PATH`: **54 passed,
    4 skipped**, numerically identical results.
  - **Bug found and fixed**: read-only-array error messages differed between
    backends ("read-only" vs "writable") with no common substring. The
    fallback's wording now matches pybind11's.
  - Examples 1-4 all run. Example 3 reports a 13.46x native speedup with
    backends agreeing to 1.09e-11.
  - **Bug found and fixed** in example 4: `py::array_t<double>(count)` yields a
    **zero-stride** array in pybind11 3.1.0 (the single-`ssize_t` constructor
    forwards an empty strides container), so every element read back as element
    0 while the C was correct. Isolated by instrumenting the binding and
    comparing against a standalone C harness
    (`out=1.5 2 3 3.5` in C vs `[1.5,1.5,1.5,1.5]` in Python; `strides: (0,)`).
    Fixed with an explicit `py::array::ShapeContainer`; now asserted by
    `test_output_array_uses_explicit_shape_container`.

- [x] **Stage 4 tooling** — expanded ruff, strict mypy, pre-commit.
  - `ruff check .` -> 0 -> All checks passed; `ruff format --check .` -> 0.
  - `mypy src tests` -> 0 -> Success, 9 source files.
  - **Bug found and fixed**: `[tool.mypy] python_version = "3.10"` made mypy
    fail parsing numpy 2.5 stubs, which use PEP 695 syntax needing 3.12+. Pin
    removed; the CI matrix now provides real version coverage.
  - **Bug found and fixed**: mypy marked the `_accel.py` fallbacks unreachable,
    because `_core.pyi` always exists so the guarded import looks infallible.
    `warn_unreachable` scoped off for that one module, with rationale.
  - **Bug found and fixed via ruff's import sorting**: `tomllib` is 3.11+, but
    the package supports 3.10 — the conformance test would have failed to
    import on the 3.10 CI leg. Now a guarded import with a `tomli` fallback.

- [x] **Stage 5 containers** — image builds and compiles the extension.
  - `docker build -f container/Dockerfile.python` -> 0.
  - In-container `pip install .` + `pytest` -> **36 passed**, backend native.
  - **Two image bugs found and fixed**: `/home/vscode/.cache` was root-owned so
    pip's cache was silently disabled, and a login shell (`bash -lc`) reset
    `PATH`, so pip installed into `~/.local` against the system interpreter
    instead of `/opt/venv`. After the fix: `which python -> /opt/venv/bin/python`,
    `sys.prefix -> /opt/venv`, no warnings.
  - **This is what exposed the most serious bug of the whole change** (below).

- [x] **Stage 6 CI/CD** — workflows written and validated.
  - All 7 YAML files parse (`yaml.safe_load`), and all 3 JSONC configs parse.
  - `ci.yml` asserts the extension actually built rather than accepting a
    silent fallback, and has a dedicated `pure-python` job for the no-compiler
    path.
  - **Critical bug found and fixed**: `pythonpath = ["src"]` in the pytest
    config put the *source* tree ahead of the installed package. The compiled
    `_core` lives in site-packages, never in `src/`, so pytest imported a
    package that could never have its extension: every native test silently
    skipped while the suite reported green. Hidden locally because an editable
    install maps `src/` back to the build tree; the non-editable container
    install is what revealed it. Removed, with an `ACHTUNG!` comment, and now
    asserted by `test_pytest_does_not_put_src_on_pythonpath`.

- [x] **Stage 7 documentation** — docs build clean.
  - `sphinx-build -b html doc doc/_build/html -W --keep-going` -> 0 ->
    `build succeeded` (after fixing two myst cross-reference warnings by giving
    example 04 its own README and using repository URLs for out-of-tree links).

- [x] **Stage 8 tailoring** — script works end to end.
  - `--list` -> 0, non-destructive (verified by a tree snapshot before/after).
  - Full rename in a throwaway copy -> 0; no `template_python_project` string
    survives anywhere; `[project].name = "demo-pkg"`;
    `wheel.packages = ["src/demo_pkg"]`; template-only files removed.
  - `--no-extension` -> 0; `src/cpp`, `cmake`, `CMakeLists.txt`, `build_ext.sh`
    removed; `wheel.cmake = false`; the tailored package still imports and
    computes `vector_norm([3,4]) == 5.0` with no compiler.
  - Refuses a mistyped `--root` pointing at an unrelated directory, and rejects
    a non-identifier package name.
  - **Closes `TODO` item #1.**

- [x] **Stage 9 full gate** — everything green.
  - `ruff check .` / `ruff format --check .` -> 0 (24 files).
  - `mypy src tests` -> 0 (9 files).
  - `pytest` -> 0 -> **58 passed** with the extension.
  - Fallback config -> **54 passed, 4 skipped**.
  - `python -m build` -> 0; `twine check --strict dist/*` -> 0, both PASSED.
  - Wheel in a fresh venv with `env -u LD_LIBRARY_PATH` -> imports, backend
    native, C++ and Python versions agree.
  - **sdist rebuilds from scratch** in an isolated build -> extension present.
  - Wheel contains `_core...so`, `_core.pyi`, `py.typed`, `_version.py`.
  - sdist excludes `build/`, `dist/`, `.venv/`, `.github/`; includes all sources.
  - `sphinx-build -W` -> 0.

### Post-gate additions

- **pre-commit executed for real** (not merely configured): `pre-commit run
  --all-files` -> 0, and again with every untracked file passed explicitly
  (`--files ...`) -> 0, since `--all-files` only sees git-tracked files and
  would otherwise have skipped the new YAML and CMake.
- **Bug found and fixed by that run**: the `mixed-line-ending --fix=lf` hook
  rewrote `doc/make.bat` from CRLF to LF, which breaks a Windows batch file.
  Restored with `git checkout` and `.bat` excluded from the three whitespace
  hooks.
- **gersemi (CMake formatter) removed after evaluation.** It wanted to reformat
  all six CMake files, exploding compact calls across many lines
  (`find_package(pybind11 CONFIG REQUIRED PATHS ... NO_DEFAULT_PATH)` -> seven
  lines). That works against CMake whose purpose here is to be read and copied.
  A hook that always fails is worse than no hook; the rationale is recorded in
  `.pre-commit-config.yaml` so it is not re-added by reflex.
- **shellcheck** now runs at `--severity=warning` with `SC1091` excluded (it
  fires on `source "$(conda info --base)/..."`, whose target does not exist
  until runtime).

### Final gate, all green

| Check | Result |
| --- | --- |
| `ruff check .` | PASS |
| `ruff format --check .` | PASS |
| `mypy src tests` | PASS (9 files) |
| `pytest` (native) | PASS — 58 passed |
| `pytest` (fallback, isolated venv) | PASS — 54 passed, 4 skipped |
| `sphinx-build -W` | PASS |
| `python -m build` | PASS |
| `twine check --strict` | PASS |
| `pre-commit run --all-files` | PASS |
| Examples 01-04 | PASS |
| Wheel in fresh venv, empty `LD_LIBRARY_PATH` | PASS |
| sdist rebuilds from scratch | PASS |
| Docker image build + in-container tests | PASS — 36 passed |

## Known Risks

- **pip < 25.1 cannot resolve `--group`.** Mitigated by upgrading pip in every
  script, container, and CI job, and by stating the floor in `README.md`.
- ~~No `v*.*.*` tag exists in this repo yet.~~ **Resolved at Stage 0**: tags
  `v0.1.0` and `v0.2.0` exist and `git describe --tags` returns
  `v0.2.0-1-g28a287f`, so setuptools-scm has a real version source. The
  `fallback_version` setting remains only as a sdist-without-git safety net.
- **pybind11 3.x is released** (3.1.0 current). The pin `>=2.13,<4` admits it;
  Stage 2 must confirm `pybind11_add_module` behaviour on the installed version
  before assuming 2.x semantics.
- **cibuildwheel cost.** The wheels workflow is tag- and dispatch-triggered
  only, never on every push, so ordinary PRs stay cheap.
