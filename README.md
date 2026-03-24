# Python Template Project

Reusable Python library template with a `src` layout, Hatch-based packaging, pytest, mypy, Ruff, Sphinx docs, Docker, CI, and optional conda helpers.

## Template Naming Model

Three names matter in this template:

- Repository/template slug: the repository name on disk or in Git hosting.
- Distribution name: `[project].name` in `pyproject.toml`, used by packaging tools such as `pip install`.
- Import package name: the directory under `src/`, which determines Python imports such as `import template_python_project`.

By default, this template uses the same value for the distribution and import package names:

- Distribution name: `template_python_project`
- Import package: `template_python_project`
- Package path: `src/template_python_project/`

When creating a real library, update all three deliberately. The import package name is the critical one for user-facing Python code.

## Quick Start

```bash
python -m pip install --upgrade pip
python -m pip install -e .[dev]
pytest -q
python -m build
```

Build documentation:

```bash
python -m pip install -e .[docs]
sphinx-build -b html doc doc/_build/html
```

## What To Rename For A New Project

1. Change `[project].name` in `pyproject.toml` if the distribution name should change.
2. Rename `src/template_python_project/` to the new import package name.
3. Update all references to `template_python_project` across:
   - `pyproject.toml`
   - `doc/conf.py`
   - `doc/api.rst`
   - `tests/test_smoke.py`
   - CI or helper scripts if they mention the package explicitly

## Included Features

- `src`-layout packaging with Hatch and optional VCS-based versioning
- Baseline package module and smoke test
- `pytest` + coverage configuration
- `ruff` and `mypy` configuration
- Sphinx docs with API reference
- GitHub Actions CI
- Docker build example
- Optional conda bootstrap helper
- Optional Cython/GPU extension points

## Optional Helpers

- `./run_tests.sh` runs `pytest` through the current Python interpreter.
- `./conda_install.sh` creates or reuses a conda env and installs this package.
- `./release_to_pypi.sh` builds artifacts and uploads them with `twine` when `PYPI_TOKEN` is set.

## Optional Extension Points

- `src/template_python_project/cython_src/` contains an example `.pyx` file for projects that add Cython later.
- `examples/gpu/README.md` documents where to place project-specific GPU or Jetson setup steps. Those steps are intentionally not part of the default install path.
