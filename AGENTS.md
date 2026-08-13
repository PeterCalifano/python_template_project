# Agents instructions

## Language and programming standards

### Language-agnostic software engineering guidelines

- Follow the owning component's established conventions and keep each change
  within the smallest coherent scope that satisfies the requested behavior.
- Prefer small, cohesive functions and classes with explicit contracts. Add an
  abstraction only when it clarifies ownership, reuse, or a stable interface.
- Use descriptive names and keep one authoritative source for each policy or
  piece of state. Avoid hidden coupling and duplicated decision logic.
- Validate external inputs at system boundaries and report actionable failures.
  Do not silently fall back to behavior that changes the advertised contract.
- Test observable behavior, invariants, and failure modes rather than internal
  implementation details or tunable defaults.
- During review and optimization, actively seek behavior-preserving ways to
  reduce complexity and improve performance, maintainability, readability, and
  implementation clarity. Simplify unnecessary nested loops, helper functions,
  conditional branches, indirection, and abstractions that do not enforce a
  useful contract.
- Keep refactoring within the reviewed scope and preserve public behavior unless
  a contract change is explicitly requested. Make performance optimization
  evidence-driven through profiling, measurement, or algorithmic analysis, and
  document any tradeoff that increases complexity.
- Use 100 columns as a soft limit. Keep assignments and function calls on one
  line when they remain readable; otherwise wrap at semantic boundaries and
  align continuation lines with the expression they continue.
- Treat newlines as logical separators. Keep statements that implement the same
  small step together, and use a blank line between distinct steps.
- Introduce each non-obvious logical block with a concise comment describing its
  purpose, rationale, or invariant. Do not translate individual statements into
  prose.

### Python

- Preserve the Python 3.10 minimum configured in `pyproject.toml`. Do not use
  syntax or standard-library APIs introduced after that version unless the
  project metadata, Ruff and mypy targets, CI, and documentation are upgraded
  together.
- Follow PEP 8 for naming and formatting. Use `snake_case` for functions,
  methods, and variables, `PascalCase` for classes, and a leading underscore for
  internal APIs. Use a trailing underscore only to avoid a keyword or name
  collision.
- Follow PEP 257 and use Google-style docstrings for modules, public classes,
  public methods, and public functions. Document arguments, returns, raised
  exceptions, important invariants, and examples where applicable.
- Add precise type annotations to every function and method signature, class
  attribute, and dataclass field. Keep `src` and `tests` suitable for the
  configured mypy checks, avoid untyped definitions, and isolate or justify any
  unavoidable `Any` boundary.
- Follow the configured Ruff rules and 100-column line length. Keep imports
  explicit and ordered, and do not silence a lint or type diagnostic without a
  documented reason.
- Prefer dataclasses to unstructured dictionaries for stable records. Prefer an
  enum to string or integer literals when a choice has more than two values.
- Prefer functions for stateless transformations and classes when state,
  ownership, or a durable behavioral interface is required.
- Use Matplotlib for general plots and prefer seaborn for statistical plots.
  Use Pillow or OpenCV for image-specific work when those domains apply.
- Use PyTorch for machine-learning implementations, with scikit-learn for
  supporting workflows where useful. Preserve ONNX export compatibility for
  model APIs unless the task explicitly excludes it.
- When building libraries or complex functionality, provide runnable examples
  or demos with expected output. Include relevant visualizations or output data
  when they materially help verify behavior.
- Use pytest for runtime behavior. Test public contracts, edge cases, and
  failures, and run the configured Ruff and mypy checks for affected code.

## Commit and staged-review workflow

### Commit-message style

- Do not use Conventional Commits prefixes such as `feat:`, `fix:`, or
  `docs:`.
- Write the subject in the imperative mood and sentence case, with no trailing
  period. Aim for approximately 50-70 characters when the change can be
  described clearly within that range.
- Optionally end the subject with a short parenthetical scope when it adds
  useful context, for example `Align type checks with supported Python
  (pyproject.toml)`.
- Use an optional leading tag only when its meaning applies:
  - `[MAJOR]` for a significant capability, architectural change, or broad
    contract or workflow change;
  - `[BUGFIX]` for a correctness defect or regression;
  - `[HOTFIX]` for an urgent, narrowly targeted correction;
  - no tag for routine enhancements, tests, documentation, or maintenance.
- Use an optional body for changes that need rationale or a behavioral summary.
  Format it as imperative `-` bullets, put one blank line between bullets, omit
  terminal periods, and indent wrapped continuation lines beneath the bullet
  text.
- Describe intent, important design decisions, and behavioral consequences in
  the body instead of merely listing changed files.
- Never add `Co-Authored-By` or other AI-attribution trailers.

### Authorization and batch sequence

1. Never create or amend a commit unless the user explicitly instructs the
   agent to commit. Requests to implement, finish, stage, or continue, including
   the keyword `next`, do not grant commit permission.
2. Treat commit, tag, and push authorization independently. Permission to
   commit does not imply permission to tag or push.
3. Inspect the worktree and current index before preparing a batch. Preserve and
   report unrelated user-owned staged or unstaged work; never reset, overwrite,
   or absorb it merely to simplify the batch.
4. Partition completed work into coherent functional batches. Include directly
   dependent tests and necessary documentation with their implementation unless
   a concrete review or ownership boundary requires separation. Do not create
   micro-batches that are too small to review meaningfully.
5. A mixed batch is allowed when a few small changes do not justify independent
   review units. Label it clearly as mixed, explain why the items belong
   together, and never use it to hide a substantial independent feature or fix.
6. Before staging, review the complete candidate diff for correctness, scope,
   formatting, comments, and documentation. Run proportionate tests and static
   checks, and apply the staged-code quality gate below to every new or
   substantially modified source file.
7. Stage only the reviewed batch with an explicit path or hunk allowlist. Then
   inspect the complete index with `git diff --cached` and run
   `git diff --cached --check`. Repeat relevant validation against the staged
   result when index contents or generated inputs can affect the outcome.
8. Report the staged paths, functional purpose, verification evidence, caveats,
   exclusions, and exact proposed commit subject and body. Stop for user review
   without preparing or staging another batch.
9. Advance only after the user responds with the exact keyword `next`. Interpret
   `next` as permission to prepare the following batch, never as permission to
   commit the current batch.
10. Before advancing, confirm that the previous batch is no longer staged. If
    the index is still populated, stop and ask the user to commit or clear it,
    or to give a separate explicit instruction for the agent to commit.
11. When the user explicitly requests both actions, such as `commit and next`,
    commit the approved batch with the reviewed message, verify that the index
    is clear, and only then prepare the following batch.

## Staged-code review quality gate

Before handing staged changes to the user for commit review, inspect the complete
Git index with `git diff --cached`. Apply this gate to files staged by either the
user or the agent. This review does not authorize staging, committing, or
rewriting unrelated code.

For every staged Python source file that is new or substantially modified:

- Add or update the module-level Google-style docstring and documentation for
  each public class, function, and method.
- Keep type annotations complete and compatible with the configured mypy target.
- Organize related statements into visually separated blocks. Each block must
  implement one immediate objective or implementation step, not a broad feature.
- Introduce each non-obvious block with a concise comment explaining its purpose
  and, when relevant, why that approach is required.
- Prefer purpose-, invariant-, and contract-oriented comments. Do not add
  comments that merely translate individual statements into prose.
- Preserve useful existing comments and documentation unless the staged change
  makes them incorrect.
- Review the staged result as a reader will receive it rather than reviewing
  only the lines changed during implementation.

Limit cleanup to the intended scope of the staged work. Do not rewrite unrelated
legacy code merely because the same file is staged. Do not report the changes as
ready for review until this pass is complete; summarize any documentation or
readability cleanup performed during the pass.

### Python pattern

```python
"""Load and validate observation records.

This module owns file parsing and domain validation. Selection policy remains
with the caller.

Example:
    observations = load_valid_observations(Path("observations.csv"))
    print(len(observations))

Output:
    3
"""


def load_valid_observations(input_path: Path) -> list[Observation]:
    """Load valid observations while preserving their input order.

    Args:
        input_path: Path to the delimited observation file.

    Returns:
        Valid observations in input order.

    Raises:
        ValueError: If an input row cannot be parsed.

    Example:
        observations = load_valid_observations(Path("observations.csv"))
        print(len(observations))

    Output:
        3
    """
    # Parse all rows through one path so malformed input produces consistent
    # diagnostics.
    parsed_observations = parse_observations(input_path)

    # Enforce the domain validity contract without changing source ordering.
    valid_observations = [
        observation
        for observation in parsed_observations
        if observation.is_valid()
    ]

    return valid_observations
```
