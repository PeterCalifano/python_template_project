## Summary

<!-- What changes, and why. One or two sentences. -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Packaging / build system
- [ ] Documentation
- [ ] CI/CD
- [ ] Refactor (no behaviour change)

## Verification

<!--
Paste real command output, not a claim that it passed. Anything unverified
should be stated as unverified.
-->

```
# ruff check . && ruff format --check .
# mypy src tests
# pytest
```

- [ ] `ruff check .` and `ruff format --check .` pass
- [ ] `mypy src tests` passes
- [ ] `pytest` passes **with** the compiled extension
- [ ] `pytest` passes **without** it (`pip install -e . -C wheel.cmake=false`)
- [ ] `python -m build` succeeds and `twine check --strict dist/*` passes

## If this touches the extension or CMake

- [ ] `./build_ext.sh --clean` succeeds from scratch
- [ ] `_core.pyi` regenerated if the binding surface changed
      (`pybind11-stubgen template_python_project._core -o src/`)
- [ ] The pure-Python fallback in `_accel.py` still matches the C++ behaviour
- [ ] Any new external library is wired through `cmake/HandleExternalLibs.cmake`
      with a pinned version

## If this touches the template's own structure

- [ ] `./tailor_template_cleanup.sh --list` still reports the right files
- [ ] Renaming still works end to end (see `tests/test_template_conformance.py`)
- [ ] `doc/` updated to match
