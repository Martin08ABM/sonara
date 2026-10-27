# SPEC-002: Content ingestion, text processing and Apache 2.0

**Status: Implemented** — approved for implementation by the owner; local checks passed. Owner review is required before Verified.

## Objective and scope

Implement local ingestion of TXT, Markdown, EPUB, textual PDF and DOCX, structural representation, configurable lossless segmentation, provenance, structural events, deterministic JSON inspection and Apache-2.0 licensing. Preserve SPEC-001 APIs. No OCR, model inference, network providers, audio, UI, storage or other later features.

## Requirements

Select importers through an extensible registry; validate extensions, signatures, inputs, sizes and archive entries. Reject protected, unsafe, corrupt and textless documents using structured errors. Never run document code or fetch external resources. Use Unicode character offsets into extracted text; preserve source page when available. Extraction is format dependent and not byte-identical to document internals. Normalization must be explicit and reproducible. Keep classification preliminary and rule-based. Segments must reconstruct extracted text and respect section boundaries, paragraph boundaries where possible and configurable target and maximum sizes without splitting words.

## Acceptance and verification

Five formats, controlled errors, lossless reconstruction, provenance, configuration, JSON, security, backwards compatibility, Apache license and documentation must be verified with generated fixtures, pytest, Ruff and mypy. No model downloads or inference. Local checks lead to Implemented; Verified awaits owner review.

## Contracts and deterministic behavior

`Document` contains the input SHA-256 as stable identity and integrity digest, filename, format, available title/author/language, import timestamp, extracted and identity-normalized text, sections/elements, fragments and events. Sections cover the extracted text in order; fragments have section and element references, zero-based end-exclusive Unicode character offsets and PDF page where available. IDs and content are stable across identical imports; the timestamp varies and the filename varies on rename. Default JSON excludes the timestamp and sorts object keys; passing `include_imported_at=True` includes it. The filename and any caller-provided metadata affect serialized output. Reconstruction is `''.join(f.text for f in document.fragments) == document.extracted_text`.

Default target is 2,000 characters, maximum 4,000, configurable through `SegmentationConfig`. Boundaries favor structural lines and sections. The maximum is strict; if a single word cannot fit, `word_too_long` is raised rather than silently splitting it. All newlines and whitespace in extracted text are retained.

## Extraction and security

TXT and Markdown use UTF-8 (BOM removed); Markdown syntax is retained. EPUB follows the spine, joining supported XHTML blocks with blank lines, ignoring active elements; DOCX joins paragraph text with blank lines. Headings are recognized from Markdown markers, EPUB heading tags and DOCX Heading styles. PDF extraction follows pages via pypdf with no OCR; encoding, columns, fonts and layout can affect results. `ContentError.code` provides controlled errors without filenames or paths. Limits cover input bytes, archive entry count, declared expanded bytes, compression ratio and extracted text. ZIP entries are never extracted to disk; path traversal, symlinks, encryption, unsafe references, XML entities and external relationships are rejected. Imported content is data, never instructions. These safeguards are not a process sandbox; notably PDF decompression may consume memory before extracted-text limits can be applied. Nonstandard EPUB XHTML, complex DOCX constructs, images, footnotes, annotations and PDF layout may not be completely represented. PDF has no OCR and no visual coordinates. External resources are never fetched.

## Dependencies and license

`pypdf` (BSD-3-Clause) handles local PDF text and page metadata; `defusedxml` (PSF license) prevents XML entity/DTD attacks in EPUB and DOCX. ZIP and Unicode processing use the standard library. Sonara's own code is Apache-2.0 as accepted in ADR-001; external models, datasets and libraries retain independent licenses. No external assets are redistributed. No NOTICE is needed for the current project-owned material and separately installed dependencies.

## Local verification

On Python 3.14.8, editable installation and `pip check` succeeded. Pytest passed 37 tests, including all SPEC-001 tests and generated TXT, Markdown, EPUB, PDF and DOCX fixtures; Ruff lint and format checks and mypy passed. The CLI example imported a local Markdown file and wrote JSON. Package metadata reports `Apache-2.0`. CI has not run on GitHub and Python 3.11 has not been tested locally. The initial repository has no commits, so changes remain untracked; no commit, push or merge was made. Owner review remains pending before Verified.
