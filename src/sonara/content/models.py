"""Format-independent document structures and Unicode character offsets."""

import json
from dataclasses import asdict, dataclass
from typing import Literal

ElementKind = Literal["heading", "paragraph", "quote", "dialogue_candidate", "text"]
EventKind = Literal["DOCUMENT_START", "SECTION_START", "SECTION_END", "DOCUMENT_END"]


@dataclass(frozen=True)
class Element:
    id: str
    kind: ElementKind
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class Section:
    id: str
    title: str | None
    start: int
    end: int
    elements: tuple[Element, ...]
    source: str | None = None
    page: int | None = None


@dataclass(frozen=True)
class Fragment:
    document_id: str
    section_id: str
    index: int
    start: int
    end: int
    text: str
    element_ids: tuple[str, ...]
    page: int | None = None


@dataclass(frozen=True)
class StructuralEvent:
    kind: EventKind
    offset: int
    section_id: str | None = None


@dataclass(frozen=True)
class Document:
    id: str
    original_name: str | None
    format: str
    language: str | None
    title: str | None
    author: str | None
    imported_at: str
    integrity_sha256: str
    extracted_text: str
    normalized_text: str
    sections: tuple[Section, ...]
    fragments: tuple[Fragment, ...]
    events: tuple[StructuralEvent, ...]
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.id or not self.format or not self.extracted_text.strip():
            raise ValueError("Invalid document identity or empty content")
        if self.normalized_text != self.extracted_text:
            raise ValueError("Only identity normalization is supported")
        if (
            len(self.integrity_sha256) != 64
            or any(c not in "0123456789abcdef" for c in self.integrity_sha256)
            or self.id != self.integrity_sha256
        ):
            raise ValueError("Invalid document integrity digest")
        expected_events = [StructuralEvent("DOCUMENT_START", 0)]
        ids: set[str] = set()
        offset = 0
        for section in self.sections:
            if not section.id or section.id in ids:
                raise ValueError("Invalid or duplicate section ID")
            ids.add(section.id)
            expected_events.append(StructuralEvent("SECTION_START", section.start, section.id))
            if section.start != offset or section.end <= offset:
                raise ValueError("Invalid section offsets")
            for element in section.elements:
                if not element.id or element.id in ids:
                    raise ValueError("Invalid or duplicate element ID")
                ids.add(element.id)
                if element.kind not in {
                    "heading",
                    "paragraph",
                    "quote",
                    "dialogue_candidate",
                    "text",
                }:
                    raise ValueError("Invalid element kind")
                if element.start != offset or element.end <= offset:
                    raise ValueError("Invalid element offsets")
                if self.extracted_text[element.start : element.end] != element.text:
                    raise ValueError("Invalid element text")
                offset = element.end
            if offset != section.end:
                raise ValueError("Incomplete section")
            expected_events.append(StructuralEvent("SECTION_END", section.end, section.id))
        if offset != len(self.extracted_text):
            raise ValueError("Incomplete document sections")
        expected_events.append(StructuralEvent("DOCUMENT_END", len(self.extracted_text)))
        if self.events != tuple(expected_events):
            raise ValueError("Invalid structural events")
        if self.fragments:
            offset = 0
            for index, fragment in enumerate(self.fragments):
                if (
                    fragment.document_id != self.id
                    or fragment.index != index
                    or fragment.start != offset
                    or fragment.end <= offset
                    or self.extracted_text[fragment.start : fragment.end] != fragment.text
                ):
                    raise ValueError("Invalid fragment")
                fragment_section = next(
                    (s for s in self.sections if s.id == fragment.section_id), None
                )
                if fragment_section is None or not (
                    fragment_section.start <= fragment.start < fragment.end <= fragment_section.end
                ):
                    raise ValueError("Fragment crosses section boundary")
                expected = tuple(
                    e.id
                    for e in fragment_section.elements
                    if e.start < fragment.end and e.end > fragment.start
                )
                if fragment.element_ids != expected or fragment.page != fragment_section.page:
                    raise ValueError("Invalid fragment provenance")
                offset = fragment.end
            if offset != len(self.extracted_text):
                raise ValueError("Incomplete fragments")

    def to_json(self, *, include_imported_at: bool = False) -> str:
        data = asdict(self)
        if not include_imported_at:
            del data["imported_at"]
        return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
