# SPEC-001: Project bootstrap

**Status: Implemented**. Local checks passed on Python 3.14, but the files are not yet versioned and GitHub Actions has not run; do not advance to Verified until the remaining acceptance checks are met. The owner's task description authorizes this bootstrap scope. Status vocabulary: Draft → Approved → In Progress → Implemented → Verified; revisions may return to Draft for review. Owner review and integration into `main` remain separate.

## Objective and context

Establish a lightweight Python foundation and public documentation for Sonara, an expressive narration orchestrator. Narration is primary; content-aware conversation is complementary. Preserve the existing `NarrativeAI` experiment and environment. No architecture reference document was present in the inspected project.

## Scope and functional requirements

- Install a Python 3.11+ src-layout package with typed provider-independent data contracts and interchangeable LLM, TTS and expressive classifier protocols.
- Implement input validation and basic line segmentation preserving every character and its offsets; return structured results.
- Provide explicit environment configuration and standard logging; use fakes in tests. No actual inference, network calls or audio generation.
- Provide documentation, SDD instructions, GitHub templates and CI for tests, lint, formatting and types. Preserve previous experiments.

## Non-functional requirements and constraints

Local-first, modular, simple, typed, maintainable and lightweight; standard library only at runtime, no model downloads. No secrets in code. No implementation of SPEC-002 or later. No external API integration. Keep public documentation in English. Do not commit, push, merge or publish without authorization.

## Data contracts

- `TextSegment(text, start, end)` uses zero-based Python string offsets, with `end` exclusive. Text is nonempty and its length equals `end - start`.
- `Speaker(id, name)`, `Emotion(label)` and `VocalStyle(label)` require nonblank strings; labels are deliberately open-ended.
- `NarrationPlan(original_text, segments)` requires a nonblank original and a nonempty tuple of consecutive segments that cover it exactly. It does not yet contain expressive assignments.
- `ProviderCapabilities(name, languages)` contains a nonblank name and an optional tuple of nonblank language identifiers. Semantics of language identifiers are not standardized yet.
- `LLMProvider.complete(prompt) -> str`, `TTSProvider.synthesize(segment) -> bytes` and `ExpressiveClassifier.classify(segment) -> (Emotion, VocalStyle)` are structural interfaces. LLM and TTS also expose capabilities. Audio encoding, error handling and advanced provider lifecycle are undecided. Fakes exist only in tests; no provider is registered or invoked by the Core.

`TextService.process` rejects non-string and blank inputs and splits with `splitlines(keepends=True)`; segments preserve all characters including line endings and blank lines. It does not infer sentences or meanings. `Settings.from_env` reads `SONARA_LOG_LEVEL`; logging is configured only when explicitly requested. `.env` is not automatically loaded.

## Acceptance criteria and tests

Editable install succeeds; public modules import; contracts validate; fake providers satisfy protocols; service preserves text and rejects invalid input; configuration works; pytest, Ruff lint/format and mypy pass; CI and required documentation exist; prior experiment remains untouched; no model downloads or out-of-scope features. Tests cover preservation (including Unicode and line endings), invalid input/contracts, configuration and fake provider substitution. CI runs on Python 3.11 and 3.14 without invoking the Laya experiment.

## Limitations and pending decisions at SPEC-001

This section records the bootstrap state; SPEC-002 supersedes its content-ingestion and license limitations.

No speech, inference, speaker assignment, real providers, persistence, document ingestion or conversation. Classifier is a protocol only; a future approved integration will use Laya. Segmentation is line-based, not linguistic. Model/provider selection, context/memory, serialization, audio format, richer validation, licensing (MIT and Apache 2.0 are candidates), distribution and governance require owner decisions. Diagrams for unimplemented parts are proposals, not commitments. The `NarrativeAI` directory is retained to preserve existing material; the Python package is named Sonara.

## Verification evidence

On Python 3.14.8 in a separate virtual environment: editable installation succeeded, 10 pytest cases passed, all public modules imported, Ruff lint and format checks passed, and mypy found no issues. The example ran successfully. The CI workflow is configured but has not run on GitHub; Python 3.11 was not available for local verification. Git was initialized on `spec/001-bootstrap` without commits, so `AGENTS.md` and all other files remain untracked until the owner authorizes a commit. The pre-existing Laya experiment was not executed or modified.
