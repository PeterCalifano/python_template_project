# Active implementation context

Written before compaction so work can resume without loss. Read together with
[`AGENTS.md`](AGENTS.md).

## User request

Improve `python_template_project` by importing the good practices from the
sibling templates in `dev-tools/`, and add a pybind11 interface so external
C/C++ libraries can be wired in easily. Packaging must follow current PEP
practice (`pyproject.toml`-based or more modern). Runnable usage placeholders
were requested, including for the C/C++ binding path.

## Durable plan

`doc/developments/template_modernization_pybind11_plan.md` — staged, with
`- [ ]` checkboxes, a Stop Rule, and a Verification Log holding real output.

## Decisions already made

- **Backend: `hatchling` → `scikit-build-core`.** hatchling cannot build
  extension modules at all, so pybind11 forced the change. Verified that
  scikit-build-core covers every capability previously relied on: git
  versioning (via the `setuptools_scm` metadata provider), sdist control,
  wheel packages, `python -m build`, twine publishing, editable installs.
- **Python floor stays 3.10**; dev tooling moved to PEP 735
  `[dependency-groups]`, with `[project.optional-dependencies]` reserved for
  genuine runtime extras. Requires pip ≥ 25.1.
- **Code style: standard PEP 8** (not the Capitalized-function house style used
  in the C++ template's Python code). ruff `N` rules are enabled.
- **Pure-Python remains supported** via `wheel.cmake = false`, which drops CMake
  as a build dependency entirely and yields a `py3-none-any` wheel.

## Bugs found and fixed during implementation

These were real failures, not hypotheticals. Do not reintroduce them.

1. **Version truncation + double stringify.** CMake's `project(VERSION)` accepts
   only numeric `MAJOR.MINOR.PATCH`, so `0.3.0.dev1` became `0.3.0`; and
   `VERSION_INFO` was passed already-quoted then stringified again, yielding
   `"0.3.0"` with literal quotes. Fixed by using
   `SKBUILD_PROJECT_VERSION_FULL` and consuming the macro directly.
2. **`py::array_t<double>(count)` yields a zero-stride array** in pybind11 3.1.0.
   The single-`ssize_t` constructor forwards an empty strides container. Shape
   looked correct while every element read back as element 0, making correct C
   code appear broken. Fixed with an explicit `py::array::ShapeContainer`.
3. **mypy `python_version = "3.10"` broke on numpy stubs.** Modern numpy stubs
   use PEP 695 syntax that only 3.12+ parses. Removed the pin; version coverage
   now comes from the CI matrix.
4. **mypy marked the `_accel.py` fallbacks unreachable**, because `_core.pyi`
   always exists so the guarded import looks infallible. Scoped
   `warn_unreachable = false` to that one module.
5. **Container defects**: `/home/vscode/.cache` was root-owned (pip cache
   silently disabled), and a login shell reset `PATH` so pip installed into
   `~/.local` instead of `/opt/venv`. Fixed with a full-tree chown and an
   `/etc/profile.d` entry.

## Verification completed so far

- Baseline before any change: pytest / ruff / mypy / build all green.
- Extension builds; `cp312-cp312-linux_x86_64` wheel; native backend active.
- Full suite: **36 passed** with the extension.
- Fallback in an isolated venv with empty `LD_LIBRARY_PATH`: **25 passed,
  4 skipped**, identical numerical results.
- `wheel.cmake = false` produces a `py3-none-any` wheel.
- PEP 735 `pip install --group dev` works on pip 26.2.1.
- ruff, ruff-format, mypy all clean.
- Examples 1–4 run; example 4 output matches a standalone C harness.
- Docker image builds; extension compiles and 36 tests pass inside it.

## Remaining work

- Stage 8: `tailor_template_cleanup.sh` and `tests/test_template_conformance.py`.
- Stage 9: full gate from a clean state, then propose a commit split.
- `README.md` rewrite and `doc/index.rst` wiring (Stage 7, in progress).

## Constraints

- Do not stage, commit, push, or reset without explicit approval.
- Work is on branch `feat/scikit-build-core-pybind11-modernization`.
