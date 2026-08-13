# Using this template

How to turn `python_template_project` into your project.

## The three names

Three distinct names matter, and conflating them is the most common source of
confusion:

| Name | Where it lives | Used by |
| --- | --- | --- |
| **Repository slug** | The directory / Git remote name | Humans, Git hosting |
| **Distribution name** | `[project].name` in `pyproject.toml` | `pip install <name>` |
| **Import package name** | The directory under `src/` | `import <name>` |

The template uses `template_python_project` for both the distribution and the
import package. The import package name is the one that shows up in user code,
so choose it first.

Distribution names may contain hyphens (`my-cool-lib`); import package names
may not (`my_cool_lib`). The tailoring script handles both.

## Renaming: the one-command path

```bash
./tailor_template_cleanup.sh --list          # preview, changes nothing

./tailor_template_cleanup.sh --apply \
    --project-name my-cool-lib \
    --package-name my_cool_lib \
    --yes
```

This renames the package directory and updates every reference across
`pyproject.toml`, `src/`, `tests/`, `doc/`, `examples/`, `CMakeLists.txt`,
`cmake/`, `.github/workflows/`, `conda_install.sh`, and the VS Code workspace
file. It also removes the files that only matter while developing the template
itself:

- `AGENTS.md`, `CLAUDE.md`, `CONTEXT.md`, `TODO`
- `doc/developments/`
- `tests/test_template_conformance.py`
- `python_template_project.code-workspace`

Extra flags:

| Flag | Effect |
| --- | --- |
| `--no-extension` | Remove the entire pybind11/CMake stack, leaving a pure-Python project |
| `--keep-examples` | Keep `examples/` (removed by default, since they document the template) |
| `--root <dir>` | Operate on a copy elsewhere instead of in place |
| `--dry-run` | Print every change without writing anything |

After running it, verify:

```bash
pip install --upgrade pip
pip install --group dev -e .
pytest
```

## Renaming by hand

If you would rather not run the script, change these:

1. `[project].name` in `pyproject.toml`
2. `[tool.scikit-build] wheel.packages`
3. `[tool.setuptools_scm] write_to`
4. `[tool.pytest.ini_options] addopts` (the `--cov=` target)
5. `[tool.coverage.run] source`
6. The `[[tool.mypy.overrides]]` module names
7. `[tool.cibuildwheel] before-test`
8. `src/template_python_project/` → `src/<your_package>/`
9. `doc/conf.py` (`project`, the import in the version lookup, `autodoc_mock_imports`)
10. `doc/api.rst`
11. `tests/*.py` imports
12. `.github/workflows/*.yml` (the import assertions)
13. `conda_install.sh` (`env_name`, final message)

The CMake side needs no edits: it takes the name from `SKBUILD_PROJECT_NAME`,
which comes from `[project].name`.

## Choosing a shape

### Pure Python, no compiler

```bash
./tailor_template_cleanup.sh --apply --no-extension \
    --project-name my-lib --package-name my_lib --yes
```

Removes `src/cpp/`, `cmake/`, `CMakeLists.txt`, and `build_ext.sh`, and sets
`wheel.cmake = false`. Wheels become `py3-none-any` and CMake stops being a
build dependency. You can then also drop `pybind11` from
`[build-system].requires`.

### Python with a compiled core

Keep everything. Replace the placeholder in `src/cpp/` with your real code, or
wire an external library — see [`extensions.md`](extensions.md).

### Python wrapping an existing C/C++ library

The main use case. Start from
[`examples/04_wire_external_c_library/`](https://github.com/PeterCalifano/python_template_project/blob/main/examples/04_wire_external_c_library/README.md),
which is a complete working miniature, then pick a wiring pattern from
[`extensions.md`](extensions.md).

## Versioning

Versions come from git tags via `setuptools-scm`. There is no version string to
edit anywhere.

```bash
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0        # triggers .github/workflows/wheels.yml
```

Between tags you get a development version such as `1.1.0.dev3`. Note the
configured schemes:

- `version_scheme = "release-branch-semver"` bumps the **minor** on a
  non-release branch, so the commit after `v0.2.0` reports `0.3.0.dev1`.
- `local_scheme = "no-local-version"` strips the `+g<sha>` suffix, which PyPI
  rejects.

The same version reaches CMake as `SKBUILD_PROJECT_VERSION_FULL`, so
`_core.__version__` and `package.__version__` can never disagree.

## Dependency groups (PEP 735)

Development tooling lives in `[dependency-groups]`, not in extras:

```bash
pip install --group dev -e .     # everything
pip install --group test -e .    # just pytest
pip install --group docs -e .    # just Sphinx
```

**This requires pip ≥ 25.1.** Upgrade first: `pip install --upgrade pip`.

`[project.optional-dependencies]` is reserved for genuine *runtime* extras —
things a user of the installed package may need — which is why `dev` and `docs`
are no longer there.

## Publishing

The workflow uses **PyPI Trusted Publishing**, so no API token is stored in the
repository. One-time setup:

1. Create the project on PyPI.
2. At <https://pypi.org/manage/account/publishing/>, add a GitHub publisher:
   your repo, workflow `wheels.yml`, environment `pypi`.
3. Create the `pypi` environment in the repository settings.

Then `git push origin v1.0.0` builds and publishes. `release_to_pypi.sh` remains
as a token-based local fallback.

## What CI checks

| Workflow | Trigger | Checks |
| --- | --- | --- |
| `ci.yml` | push / PR | ruff, ruff-format, mypy; tests on 4 Pythons × 3 OSes; a pure-Python install; the examples; docs; sdist/wheel build |
| `wheels.yml` | `v*.*.*` tag / manual | cibuildwheel across 5 platforms, then Trusted Publishing |
| `docs_pages.yml` | push / PR to docs | Sphinx with `-W`, then GitHub Pages deploy |

Note that `ci.yml` asserts the extension **actually built** rather than
accepting a silent fallback — otherwise the suite could pass while testing none
of the C++.
