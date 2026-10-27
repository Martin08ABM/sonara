# Sonara

Sonara is an early-stage foundation for an open source intelligent, expressive and interactive narration engine. Its central goal is to improve interpretation and naturalness of speech synthesis through orchestration of language models, expressive classification and vocal planning. Contextual conversation is a complementary goal. Sonara is neither a foundation model nor a conventional chatbot.

## Problem and philosophy

Plain TTS may miss speakers, emotion and context. Sonara aims to translate that context into expressive plans while keeping processing local-first, components replaceable and resource-constrained devices in mind. Remote services should be explicit and configurable.

## Status

**Early development:** typed contracts, provider interfaces, a basic text service and local content ingestion for TXT, Markdown, EPUB, textual PDF and DOCX are implemented. There is no speech, inference, Laya integration, LLM or TTS connection, contextual conversation, OCR or persistence yet. The existing `test_laya.py` is a separate experiment and may download a checkpoint if run; it is not a Sonara test.

## Architecture and planned features

The Core depends on provider-independent contracts, not implementations. Future work may interpret context, identify speakers/emotions/styles, plan expressive narration, exchange LLM and TTS providers, use Laya behind a classifier interface, discuss content during playback. These features require approved specifications. See [architecture](docs/architecture/README.md), [SPEC-001](docs/specs/SPEC-001-bootstrap.md), [SPEC-002](docs/specs/SPEC-002-content-ingestion.md) and [ADRs](docs/adr/README.md).

## Development setup

Python 3.11 or later is required. Create a fresh virtual environment, then:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python examples/basic_text.py
python examples/import_document.py path/to/document.txt output.json
python -m pytest
ruff check .
ruff format --check .
mypy
```

If `.venv` already exists, use a separate environment instead of replacing it. Configure `SONARA_LOG_LEVEL` through the environment; `.env.example` documents supported values. The package does not automatically load `.env` files. See [contributing](CONTRIBUTING.md) and [development](docs/development/README.md).

## Contributions and license

Propose work and follow the SDD process in [CONTRIBUTING.md](CONTRIBUTING.md). Sonara’s own code is distributed under [Apache License 2.0](LICENSE). Third-party libraries, Laya, LLMs, TTS engines, model weights and datasets retain their own licenses; they are not relicensed by Sonara.
