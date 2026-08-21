# PR 1 Review Remediation Plan

## Purpose

Address the correctness, tailoring, documentation, workflow, and contribution-template findings
from the review of PR [#1](https://github.com/PeterCalifano/python_template_project/pull/1).
Remote PR text updates and signed, review-gated commits were authorized. The user pushed the six
review batches; tagging remains unauthorized.

## Status Key

- `[x]` completed with evidence in the verification log
- `[ ]` pending external verification

## Stage 0 - Keep VS Code state outside the repository

- [x] Identify the in-repository browse database owner.
- [x] Change the C/C++ browse database path from an absolute workspace path to a relative filename,
      which cpptools resolves under VS Code's workspace storage.
- [x] Ignore the existing database and its SQLite `-shm` and `-wal` sidecars.
- [x] Validate and stage the isolated workspace-hygiene batch.

## Stage 1 - Separate install contracts

- [x] Confirm all 12 compiled CI failures have the same cause: an editable rebuild runs after
      pip removes its temporary isolated build environment, so pybind11 is no longer discoverable.
- [x] Use regular `pip install --group test . -v` in the Python/platform matrix.
- [x] Add one Linux/Python 3.12 editable-rebuild job with persistent `ext` dependencies,
      `--no-build-isolation`, a native-source timestamp change, and a rebuilt-binary assertion.
- [x] Keep `HAS_EXTENSION` assertions in both compiled installation paths.
- [x] Explain isolated and active editable dependencies in the CMake diagnostic and user docs.
- [x] Make the `ext` group the build helper's authoritative dependency set.
- [ ] Confirm the replacement GitHub jobs on Linux, macOS, Windows, and Python 3.10-3.13 after an
      authorized commit and push.

## Stage 2 - Address live PR review threads

- [x] Fetch the four authoritative, unresolved review threads from the base repository.
- [x] Confirm all four findings still apply to the current branch.
- [x] Reject wrong-dtype arrays before native or fallback mutation.
- [x] Translate read-only native arrays to the documented `ValueError` contract.
- [x] Fall back only when the native module is absent and preserve present-module import failures.
- [x] Replace the Conda helper's removed extras with composable dependency groups.
- [x] Pass the focused native tests, Ruff, mypy, shell syntax, ShellCheck, and captured Conda command
      paths.
- [ ] Reply to or resolve the GitHub threads after explicit remote-review authorization.

## Stage 3 - Repair and simplify tailoring

- [x] Replace the conditional `git mv` branch with one filesystem rename.
- [x] Preserve and rename `python_template_project.code-workspace`.
- [x] Correct the workspace source name used by the script.
- [x] Exercise standard and `--no-extension` tailoring in initialized temporary Git repositories.
- [x] Assert removal of native files, `_core.pyi`, native tests, and template-only files.
- [x] Assert the renamed workspace, absence of old placeholders, and working pure-Python import.
- [x] Pass 26 focused conformance tests without coverage warnings masking the result.

## Stage 4 - Define inherited guidance

- [x] Retain generic `AGENTS.md` in derived projects.
- [x] Remove template-maintainer-specific `CLAUDE.md` during tailoring.
- [x] Remove README and usage-guide claims that derived projects inherit `CLAUDE.md`.
- [x] Confirm retained guidance names no removed source-template paths or extension-only commands.
- [x] Keep the source template's maintenance workflow documented in its own `CLAUDE.md`.

## Stage 5 - Correct documentation and checks

- [x] Make the `backend_name()` example valid for both native and Python backends.
- [x] Run mypy on the minimum supported Python, 3.10, and document that policy accurately.
- [x] Make a clean-clone pre-commit run understand the generated `_version.py` boundary without
      requiring a project installation first.
- [x] Replace the in-place fallback command with a disposable environment and backend assertion.
- [x] Narrow Ruff's Markdown exclusion from every Markdown file to `AGENTS.md`.
- [x] Replace speculative stale-cache advice with first-error diagnosis and conditional cleanup.
- [x] Remove donor-specific and inflated comments that do not define a project contract.
- [x] Pass Ruff, Ruff format, mypy on Python 3.10, Sphinx with warnings as errors, and pre-commit.

## Stage 6 - Adapt contribution templates

- [x] Copy the donor issue and PR templates as a byte-identical review baseline.
- [x] Use the repository's existing `bug` and `enhancement` labels.
- [x] Replace CUDA, OptiX, MATLAB, and testfield choices with this repository's owning surfaces.
- [x] Link to this repository's template-usage and extension guides.
- [x] Keep the concise four-section PR template.
- [x] Require reproduction commands, the first real error, environment details, and a validation
      plan in the issue forms.
- [x] Test YAML parsing, labels, unique IDs, dropdown options, contact ownership, and PR headings.
- [x] Confirm both linked documents exist on the PR branch. Their canonical `main` links become
      reachable when the PR is merged.

## Stage 7 - Full acceptance and handoff

- [x] Pass all 64 tests from a fresh regular native installation.
- [x] Prove an editable native source change rebuilds the shared object; pass four native tests.
- [x] Assert the Python backend, then pass 60 fallback tests with four expected native skips.
- [x] Pass all four runnable examples, including the external C library build.
- [x] Build the docs, sdist, and wheel; pass strict Twine checks and reinstall the sdist.
- [x] Replace the retired `macos-13` runner with `macos-15-intel`; pass actionlint.
- [x] Inspect the complete candidate diff against `main` for scope, stale comments, dead branches,
      and duplicated policy.
- [x] Inspect the complete staged index and validate an exported exact-index snapshot.
- [x] Refresh the remote PR description with final, verified results.
- [ ] Confirm all required PR checks after an authorized commit and push.

## Stage 8 - Address post-push platform failures

- [x] Confirm the replacement install contract on every matrix leg: the extension builds and loads
      on Linux, macOS, and Windows for Python 3.10-3.13.
- [x] Trace all macOS failures to Bash 4 lowercase expansion under the runner's Bash 3.2.
- [x] Replace Bash 4 expansion and GNU-only in-place editing with Bash 3.2 and BSD/GNU sed
      compatible operations.
- [x] Trace all Windows failures to native Python resolving the WSL launcher as `bash.exe`.
- [x] Define the tailoring script as a POSIX-environment tool and skip its template-only tests on
      native Windows; document WSL as the Windows execution path.
- [ ] Confirm the replacement GitHub matrix after the portability fix is reviewed, committed, and
      pushed.

## Staging and Commit Proposal

Prepare one batch at a time and stop after staging it for review:

1. **Workspace hygiene** - `.gitignore` and cpptools database location.
   Subject: `Keep VS Code browse data outside the repository`
2. **CI installation contracts** - regular matrix installs, editable rebuild, dependency ownership,
   CMake diagnostics, dependent install docs, and runner labels.
   Subject: `[BUGFIX] Separate consumer and editable extension checks`
3. **PR review corrections (mixed)** - native array and import failure contracts plus the small
   Conda dependency-group correction reported by the same review.
   Subject: `[BUGFIX] Address extension and Conda review failures`
4. **Tailoring correctness** - filesystem rename, workspace preservation, initialized-Git tests,
   and derived guidance policy.
   Subject: `[BUGFIX] Repair tailoring in derived Git projects`
5. **Documentation and verification cleanup** - backend example, mypy/Ruff policy, fallback
   verification, and simplified troubleshooting guidance.
   Subject: `Align guidance with verified project behavior`
6. **Contribution templates and review record** - repository-specific issue/PR templates,
   conformance checks, test dependencies, and this plan.
   Subject: `Align contribution templates with the Python project`

## Verification Log

- **Workspace hygiene:** the staged JSONC payload parsed after removing comments; `git check-ignore`
  matched the base database and both SQLite sidecars; every pre-commit hook passed in a clean
  installed exact-index snapshot.
- **Live PR diagnosis:** `gh pr checks 1` and `gh run view 32424012455 --log-failed` showed 12
  compiled failures caused by pybind11 disappearing before editable CMake reconfiguration.
- **Live review threads:** the base PR's GraphQL review threads reported four current findings:
  wrong-dtype conversion, read-only exception translation, hidden native import failures, and stale
  Conda extras. Focused native tests passed 30 checks, and captured helper invocations used `dev`
  plus optional `docs` dependency groups.
- **Native consumer install:** fresh Python 3.12 environment, `pip install --group test . -v`,
  `HAS_EXTENSION is True`, 64 tests passed.
- **Editable rebuild:** fresh Python 3.12 environment, active `test` and `ext` groups,
  `pip install --no-build-isolation -e .`, shared-object mtime advanced, four native tests passed.
- **Fallback install:** fresh Python 3.12 environment, regular install with `wheel.cmake=false`,
  `HAS_EXTENSION is False`, 60 tests passed and four native tests skipped.
- **Tailoring and forms:** `pytest -q -o addopts='' tests/test_template_conformance.py` passed
  26 tests in initialized Git fixtures.
- **Exact tailoring batch:** 22 conformance tests passed from an exported index after the fixture
  supplied the build-generated version boundary explicitly; this prevents an ignored local
  `_version.py` from masking clean-clone failures.
- **Static checks:** Ruff lint and format passed; mypy passed for 9 source files locally and under
  Python 3.10 in `python:3.10-slim` with a writable temporary cache.
- **Clean-clone checks:** an exported index with no `_version.py` and no prior installation passed
  every pre-commit hook after the generated module override also ignored missing imports.
- **Docs and examples:** Sphinx 9.1.0 passed with `-W --keep-going`; all four examples passed.
- **Artifacts:** sdist and wheel built, strict Twine checks passed, and the sdist reinstalled with
  the native backend.
- **Repository checks:** pre-commit passed every hook; actionlint passed after replacing the retired
  macOS label; `bug` and `enhancement` labels exist in the target repository.
- **Contact links:** both source documents exist on the PR branch. Canonical `main` URLs currently
  return 404 and are expected to resolve only after merge.
- **Remote PR:** `gh pr edit 1 --body-file -` and `gh pr view 1 --json body` confirmed the concise
  four-section description and its explicit post-push CI limitation.
- **Final exact index:** exported snapshots passed 64 native tests, 60 fallback tests with four
  native skips, clean-clone pre-commit, actionlint, editable native rebuilding, all examples,
  warning-as-error docs, package builds, strict Twine checks, and sdist reinstall.
- **First replacement CI:** run `32475100995` confirmed native installation on all 12 matrix legs.
  Linux passed; macOS exposed Bash 3.2 incompatibilities in tailoring, and native Windows resolved
  the WSL launcher instead of a POSIX execution environment. Static checks, editable rebuilding,
  examples, documentation, artifacts, and the separate docs workflow passed.

## PR Description Draft

```markdown
## Summary

Modernize the Python package template around scikit-build-core and pybind11 while preserving a
fully functional pure-Python fallback. This update also resolves the review findings in CI,
extension failure handling, tailoring, documentation, and contribution templates.

## Main Changes

- Replace hatchling with scikit-build-core, setuptools-scm versioning, PEP 735 dependency groups,
  and modern package metadata; keep regular consumer installs separate from editable rebuilds.
- Add the typed pybind11 extension, equivalent Python fallback, external-library examples, and
  cross-platform package, wheel, documentation, and release workflows.
- Enforce native array and import-error contracts, repair Git-based tailoring, remove template-only
  inherited guidance, and add repository-specific issue and pull-request templates.

## Testing / Validation

- Fresh native install: 64 tests passed with `HAS_EXTENSION is True`.
- Fresh editable install: the extension rebuilt after a native source change; four native tests
  passed.
- Fresh fallback install: 60 tests passed and four native tests skipped after asserting
  `HAS_EXTENSION is False`.
- Ruff, Ruff format, mypy on Python 3.10, Sphinx with warnings as errors, all four examples,
  clean-clone pre-commit, actionlint, package builds, strict Twine checks, and sdist reinstall
  passed.
- Template conformance: 26 tests passed, including standard and pure-Python tailoring in temporary
  Git repositories and contribution-form validation.

## Notes For Reviewers

- Review the regular install, editable rebuild, fallback, extension failure, and derived-project
  tailoring contracts separately.
- Python 3.10 remains the minimum. PEP 735 dependency groups require pip 25.1 or newer.
- Cross-platform replacement jobs remain pending until these local fixes are committed and pushed.
```
