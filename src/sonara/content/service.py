"""Content ingestion orchestration, segmentation and deterministic export."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from sonara.content.errors import ContentError
from sonara.content.importers import (
    DocumentImporter,
    DocxImporter,
    EpubImporter,
    Extraction,
    Limits,
    MarkdownImporter,
    Part,
    PdfImporter,
    PlainTextImporter,
)
from sonara.content.models import Document, Element, ElementKind, Fragment, Section, StructuralEvent


@dataclass(frozen=True)
class SegmentationConfig:
    target_chars: int = 2000
    max_chars: int = 4000

    def __post_init__(self) -> None:
        if (
            type(self.target_chars) is not int
            or type(self.max_chars) is not int
            or not 0 < self.target_chars <= self.max_chars
        ):
            raise ValueError("Expected 0 < target_chars <= max_chars")


class ImporterRegistry:
    def __init__(self, importers: tuple[DocumentImporter, ...] | None = None) -> None:
        self.importers = (
            importers
            if importers is not None
            else (
                PlainTextImporter(),
                MarkdownImporter(),
                EpubImporter(),
                PdfImporter(),
                DocxImporter(),
            )
        )

    def select(self, extension: str) -> DocumentImporter:
        matches = [item for item in self.importers if item.supports(extension.lower())]
        if len(matches) != 1:
            raise ContentError("unsupported_format", "Unsupported or ambiguous document format")
        return matches[0]


def _kind(text: str) -> ElementKind:
    stripped = text.lstrip()
    if re.match(r"#{1,6}\s+\S", stripped):
        return "heading"
    if stripped.startswith(">"):
        return "quote"
    if stripped.startswith(("—", "–")):
        return "dialogue_candidate"
    return "paragraph" if stripped else "text"


def _parts_with_headings(parts: tuple[Part, ...], format_name: str) -> list[Part]:
    result = []
    for part in parts:
        if not part.text:
            continue
        starts = list(part.headings)
        if format_name == "md":
            starts += [m.start() for m in re.finditer(r"(?m)^#{1,6}[ \t]+\S[^\r\n]*", part.text)]
        boundaries = sorted(set([0, *starts, len(part.text)]))
        for a, b in zip(boundaries, boundaries[1:]):
            text = part.text[a:b]
            first = text.splitlines()[0] if text else ""
            title = None
            if a in starts:
                title = re.sub(r"^#{1,6}[ \t]+", "", first) if format_name == "md" else first
            result.append(
                Part(
                    text,
                    title=title or part.title,
                    source=part.source,
                    page=part.page,
                    headings=(0,) if a in starts else (),
                )
            )
    return result


def _build(
    extraction: Extraction,
    identity: str,
    fmt: str,
    original_name: str | None,
    extra: Mapping[str, str],
) -> Document:
    parts = _parts_with_headings(extraction.parts, fmt)
    text = "".join(part.text for part in parts)
    if not text.strip():
        raise ContentError("no_text", "Document has no extractable text")
    sections = []
    events: list[StructuralEvent] = [StructuralEvent("DOCUMENT_START", 0)]
    offset = 0
    for index, part in enumerate(parts):
        section_id = f"{identity}:s{index}"
        start = offset
        elements: list[Element] = []
        # Preserve line endings and blank lines by attaching separators to preceding blocks.
        blocks = re.findall(r"(?:[^\r\n]*(?:\r\n|\r|\n|$))", part.text)
        for line in blocks:
            if not line:
                continue
            end = offset + len(line)
            elements.append(
                Element(
                    f"{section_id}:e{len(elements)}",
                    "heading" if offset - start in part.headings else _kind(line),
                    offset,
                    end,
                    line,
                )
            )
            offset = end
        sections.append(
            Section(section_id, part.title, start, offset, tuple(elements), part.source, part.page)
        )
        events.extend(
            (
                StructuralEvent("SECTION_START", start, section_id),
                StructuralEvent("SECTION_END", offset, section_id),
            )
        )
    events.append(StructuralEvent("DOCUMENT_END", len(text)))
    return Document(
        identity,
        original_name,
        fmt,
        extraction.language,
        extraction.title,
        extraction.author,
        datetime.now(timezone.utc).isoformat(),
        identity,
        text,
        text,
        tuple(sections),
        (),
        tuple(events),
        tuple(sorted(extra.items())),
    )


def segment_document(
    document: Document, config: SegmentationConfig = SegmentationConfig()
) -> Document:
    fragments: list[Fragment] = []
    text = document.extracted_text
    for section in document.sections:
        pos = section.start
        while pos < section.end:
            hard_end = min(pos + config.max_chars, section.end)
            if hard_end == section.end:
                end = hard_end
            else:
                boundaries = [e.end for e in section.elements if pos < e.end <= hard_end]
                # Prefer a structural boundary near the target, not an arbitrarily tiny line.
                near = [b for b in boundaries if b >= pos + config.target_chars]
                if near:
                    end = near[0]
                elif boundaries and boundaries[-1] >= pos + config.target_chars // 2:
                    end = boundaries[-1]
                else:
                    split_points = [
                        i for i in range(pos + 1, hard_end + 1) if text[i - 1].isspace()
                    ]
                    if not split_points and text[hard_end].isspace():
                        split_points = [hard_end]
                    if not split_points:
                        raise ContentError(
                            "word_too_long", "A word exceeds the maximum segment size"
                        )
                    preferred = [i for i in split_points if i <= pos + config.target_chars]
                    end = preferred[-1] if preferred else split_points[0]
            overlapping = tuple(e.id for e in section.elements if e.start < end and e.end > pos)
            fragments.append(
                Fragment(
                    document.id,
                    section.id,
                    len(fragments),
                    pos,
                    end,
                    text[pos:end],
                    overlapping,
                    section.page,
                )
            )
            pos = end
    return replace(document, fragments=tuple(fragments))


class ContentService:
    def __init__(
        self,
        registry: ImporterRegistry | None = None,
        limits: Limits | None = None,
        segmentation: SegmentationConfig | None = None,
    ) -> None:
        self.registry = registry or ImporterRegistry()
        self.limits = limits or Limits()
        self.segmentation = segmentation or SegmentationConfig()

    def import_file(self, path: str | Path) -> Document:
        file = Path(path)
        extension = file.suffix.lower()
        importer = self.registry.select(extension)
        try:
            with file.open("rb") as stream:
                data = stream.read(self.limits.max_file_bytes + 1)
            if len(data) > self.limits.max_file_bytes:
                raise ContentError("size_limit", "Document file size limit exceeded")
            if not data:
                raise ContentError("empty", "Document is empty")
            extraction = importer.import_document(data, self.limits)
            if sum(len(part.text) for part in extraction.parts) > self.limits.max_extracted_chars:
                raise ContentError("size_limit", "Extracted text limit exceeded")
            result = _build(
                extraction, hashlib.sha256(data).hexdigest(), extension[1:], file.name, {}
            )
            return self.segment_document(result)
        except ContentError:
            raise
        except OSError:
            raise ContentError("read_error", "Unable to read document") from None
        except Exception:
            raise ContentError("corrupt", "Unable to parse document") from None

    def import_text(self, text: str, metadata: Mapping[str, str] | None = None) -> Document:
        if not isinstance(text, str) or not text.strip():
            raise ContentError("empty", "Text is empty")
        if (
            len(text.encode("utf-8")) > self.limits.max_file_bytes
            or len(text) > self.limits.max_extracted_chars
        ):
            raise ContentError("size_limit", "Text size limit exceeded")
        info = dict(metadata or {})
        if any(not isinstance(k, str) or not isinstance(v, str) for k, v in info.items()):
            raise ContentError("metadata", "Metadata keys and values must be strings")
        extraction = Extraction(
            (Part(text),),
            info.pop("title", None),
            info.pop("author", None),
            info.pop("language", None),
        )
        return self.segment_document(
            _build(extraction, hashlib.sha256(text.encode("utf-8")).hexdigest(), "text", None, info)
        )

    def segment_document(self, document: Document) -> Document:
        return segment_document(document, self.segmentation)
