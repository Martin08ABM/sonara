# Agent instructions for Sonara

These rules apply to all contributors and agents, including Codex and OpenCode. Read the repository files and relevant SPEC every session; do not rely on conversation memory. The owner retains authority over architecture, features, important dependencies, publication and strategy. Agents implement and verify approved work, not redefine objectives.

## Architecture

- Use a modular architecture. Keep the Core independent of concrete providers and data contracts provider-independent.
- Connect LLMs through interchangeable interfaces and decouple TTS engines. Laya is initially the fixed specialized classifier, isolated behind an interface.
- Avoid circular dependencies and coupling business logic to external frameworks.

## Development and security

- Follow SDD for all new features: consult the relevant specification before coding and implement only approved scope.
- Prefer simple, readable, typed, maintainable code and follow repository conventions. Add tests for new functionality and avoid unrelated changes.
- Justify new dependencies. Do not download models or datasets without authorization when not needed for the task.
- Never commit credentials; use environment variables for secrets. Never run destructive commands without explicit authorization or publish private data or local user files.
- Prioritize local processing. Remote connections must be explicit and configurable.

## Documentation

- Keep README current, document significant architectural changes, and create ADRs for important technical decisions. Keep specifications in `docs/specs/`.
- Never describe future functionality as implemented. Keep primary public documentation in English; use Mermaid diagrams when useful.

## Git and collaboration

- Keep `main` stable; develop each feature on an independent branch. Use descriptive Conventional Commits and associate changes with Issues and SPECs.
- Prepare pull requests with summary, tests and limitations. Never merge into `main`, push, or publish a release without authorization.

## Verification

Before finishing a task, run relevant tests, check lint and formatting, check types where appropriate, review possible regressions, report changed files and failures or checks not run, and verify acceptance criteria.

## Licensing

- Apache License 2.0 is the official license for Sonara's own code. New files must respect it; do not change the project license without owner authorization.
- Review licenses before incorporating third-party code and do not copy code incompatible with project distribution terms. External libraries, Laya, LLMs, TTS engines, model weights and datasets retain their own licenses.
