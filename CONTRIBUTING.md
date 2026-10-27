# Contributing

Sonara’s own code uses Apache License 2.0. Contributions intentionally submitted for inclusion are subject to that license unless explicitly stated otherwise; consult section 5 of [LICENSE](LICENSE). Contribute only work you are entitled to submit, respect third-party rights, and review third-party license terms before inclusion. No separate contributor agreement or copyright assignment is required by this document. Consult `AGENTS.md` and the relevant specification before contributing.

## Setup and checks

Use Python 3.11+ and an isolated virtual environment, install with `python -m pip install -e ".[dev]"`, and run `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy`. See README for an example. Do not run the separate Laya experiment as a basic test: it may download a model.

## Proposals and SDD

Report bugs using the bug template with reproduction steps and expected/actual results. Use feature and specification templates to propose changes. The owner defines a feature; discuss design, write and review its SPEC, obtain approval, implement only approved scope, run automated tests and have the owner review the result. Update the SPEC when needed; merge to `main` only after owner approval. Track SPEC status as Draft, Approved, In Progress, Implemented or Verified. Record important technical decisions as ADRs under `docs/adr/`.

## Branches and pull requests

Create a separate branch for each feature, for example `git switch -c spec/002-feature` from the approved base. Use Conventional Commits and link the issue and SPEC. Complete the pull request template with summary, changes, tests, risks, limitations and documentation. Do not merge, push or publish without authorization.
