# Mutation Testing

**Sprint 4b** introduced mutation testing via [mutmut](https://github.com/boxed/mutmut)
to catch **semantic gaps** in our test suite that line/branch coverage cannot
detect. A mutant is a small, semantically meaningful change to source code
(e.g. `>` → `>=`, `True` → `False`, `+` → `-`); a strong test suite **kills**
the mutant by failing on the change.

## Why mutation testing?

Line coverage answers "did this line execute?" but not "did the test verify
the line's *behaviour*?". Mutation testing closes that gap:

| Metric            | Detects                                              |
|-------------------|------------------------------------------------------|
| Line coverage     | Code paths your tests touch.                          |
| Branch coverage   | Boolean branches your tests exercise.                |
| **Mutation score** | Whether your tests verify *meaning*, not just *execution*. |

A line can be 100 % covered yet have 0 % mutation score: the tests touch it
but never actually assert anything useful about its result.

## Where we run it

We mutate **`rebuild/domain/`** — the smallest, most stable, most assertion-rich
layer:

- `endpoint.py` (`Endpoint`, `EndpointStatus`, `EndpointResult`)
- `commit.py`, `context.py`, `day_result.py`
- `dsl.py`, `dsl_v2.py`
- `events.py`, `models.py`, `mvp_protocol.py`, `timeline.py`

Application services and infrastructure layers are excluded because their
tests rely heavily on subprocess/HTTP fixtures where mutants tend to "survive
trivially" (false negatives).

## Running locally

```bash
# Install dev extras (includes mutmut)
pip install -e '.[dev]'

# Full run (10–30 min on rebuild/domain/)
./scripts/run_mutation_tests.sh

# Single file
PATHS=rebuild/domain/endpoint.py ./scripts/run_mutation_tests.sh

# Skip slow tests for faster feedback
FAST=1 ./scripts/run_mutation_tests.sh
```

The script writes a Markdown report to `docs/mutation_results.md` with the
killed/survived breakdown.

## Inspecting surviving mutants

```bash
mutmut results            # list all surviving mutant IDs
mutmut show <mutant_id>   # diff for a specific mutant
mutmut show all           # all diffs
mutmut html               # browsable HTML report at html/index.html
```

For each survivor, ask:

1. Is this a real test gap? → write a regression test that kills the mutant.
2. Is it semantically equivalent (e.g. mutating an unreachable branch)? → use
   `# pragma: no mutate` or a `mutmut.ini` exclusion.
3. Is the mutated code dead/redundant? → delete it.

## CI integration

[`.github/workflows/mutation.yml`](../.github/workflows/mutation.yml) runs the
full mutation analysis nightly at 03:00 UTC and on `workflow_dispatch`. The
report is uploaded as a build artifact (`mutation-report-<run_id>`) and the
mutmut cache is preserved for 7 days for incremental runs.

The workflow is **non-blocking** for PRs — too slow for fast feedback.
A surviving-mutant *threshold gate* (default 75 % score) is enforced via
`scripts/run_mutation_tests.sh`'s exit code, so CI fails when the suite
regresses below the bar.

## Tuning

The `[tool.mutmut]` table in [`pyproject.toml`](../pyproject.toml) controls
mutation behaviour:

```toml
[tool.mutmut]
paths_to_mutate = "rebuild/domain/"
runner = "python -m pytest -x --tb=no -q"
tests_dir = "tests/"
also_copy = ["tests/", "pyproject.toml"]
```

Switch `runner` to `pytest -k 'not slow' -x --tb=no -q` to skip slow tests
during exploratory runs (also available via `FAST=1`).

## Future work

- **Differential mutation testing on PRs** (Sprint 5+): only mutate files
  changed in the PR, gate at 80 % score for those files. Fast feedback,
  high signal.
- **Multi-job parallel runs** to halve CI time.
- **Apply to `rebuild/application/services/regression_service.py`** —
  the regression-detection logic is high-leverage and pure-Python.
