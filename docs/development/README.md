# Development

See [CONTRIBUTING](../../CONTRIBUTING.md) for setup and SDD. The existing `test_laya.py` and `.venv` predate the bootstrap: preserve them and do not run that experiment in routine checks.

## Content ingestion

`ContentService.import_file(path)` selects a registered importer, validates file bytes and returns a `Document` already segmented. `import_text(text, metadata=None)` is the equivalent for Unicode text. Set `Limits` and `SegmentationConfig` when creating the service. The example runs locally:

```sh
python examples/import_document.py path/to/book.epub output.json
```

`Document.to_json()` excludes the variable import timestamp by default; pass `include_imported_at=True` to include it. To verify reconstruction, compare `''.join(fragment.text for fragment in document.fragments)` with `document.extracted_text`. Offsets are zero-based Unicode code-point indexes into `extracted_text`, end-exclusive, never byte or source-file coordinates. `normalized_text` is currently an exact identity copy. IDs are SHA-256 of input bytes (UTF-8 for `import_text`); section and fragment IDs/offsets are deterministic for the same input and segmentation, while `imported_at` changes. The original filename is preserved without its directory. A renamed identical file keeps its ID but changes its JSON filename.

To add a format, implement `DocumentImporter.supports(extension)` and `import_document(data, limits)`, returning `Extraction` and `Part` objects. Pass the importer in a custom `ImporterRegistry` with any other desired importers. Validate its actual format and security before parsing; do not introduce external resource loading. Add small generated fixtures and document extraction transformations and provenance.

TXT/Markdown require UTF-8; a UTF-8 BOM is removed. Markdown source syntax is preserved. EPUB spine XHTML blocks and DOCX paragraphs are joined using two newlines, and scripts/styles are ignored. PDF pages use pypdf extraction in page order without OCR; text order, spacing, columns and visual structure may be inaccurate. PDF decompression can consume significant memory before post-extraction limits apply: process untrusted PDFs with OS isolation/resource limits where needed. Fragmentation prefers line boundaries near the target (default 2,000 characters), never crosses sections, and has a default hard maximum of 4,000; long paragraphs split at whitespace, and a single word exceeding the maximum produces `word_too_long`. Extraction positions refer only to the extracted representation, not the source file.
