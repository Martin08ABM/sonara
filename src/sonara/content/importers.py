"""Local-only document extraction. Archives are inspected, never unpacked."""

from __future__ import annotations

import io
import posixpath
import re
import stat
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Protocol
from urllib.parse import unquote, urlsplit
from zipfile import BadZipFile, ZipFile

from defusedxml import ElementTree as ET  # type: ignore[import-untyped]
from pypdf import PdfReader

from sonara.content.errors import ContentError


@dataclass(frozen=True)
class Limits:
    max_file_bytes: int = 20_000_000
    max_uncompressed_bytes: int = 50_000_000
    max_archive_entries: int = 2000
    max_compression_ratio: int = 200
    max_extracted_chars: int = 10_000_000

    def __post_init__(self) -> None:
        if any(type(x) is not int or x <= 0 for x in vars(self).values()):
            raise ValueError("Limits must be positive integers")


@dataclass(frozen=True)
class Part:
    text: str
    title: str | None = None
    source: str | None = None
    page: int | None = None
    headings: tuple[int, ...] = ()


@dataclass(frozen=True)
class Extraction:
    parts: tuple[Part, ...]
    title: str | None = None
    author: str | None = None
    language: str | None = None


class DocumentImporter(Protocol):
    def supports(self, extension: str) -> bool: ...
    def import_document(self, data: bytes, limits: Limits) -> Extraction: ...


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def safe_xml(data: bytes) -> ET.Element:
    return ET.fromstring(data, forbid_dtd=True, forbid_entities=True, forbid_external=True)


def archive(data: bytes, limits: Limits) -> ZipFile:
    try:
        z = ZipFile(io.BytesIO(data))
        entries = z.infolist()
        if len(entries) > limits.max_archive_entries:
            raise ContentError("archive_limit", "Archive entry limit exceeded")
        total = 0
        names = set()
        for item in entries:
            name = item.filename
            path = PurePosixPath(name)
            if (
                not name
                or "\\" in name
                or path.is_absolute()
                or ".." in path.parts
                or re.match(r"^[A-Za-z]:", name)
                or name in names
                or stat.S_ISLNK(item.external_attr >> 16)
            ):
                raise ContentError("unsafe_archive", "Unsafe archive entry")
            names.add(name)
            if item.flag_bits & 1:
                raise ContentError("protected", "Protected archive is not supported")
            total += item.file_size
            if (
                total > limits.max_uncompressed_bytes
                or item.file_size > limits.max_uncompressed_bytes
            ):
                raise ContentError("archive_limit", "Archive expanded size limit exceeded")
            if item.file_size > max(1, item.compress_size) * limits.max_compression_ratio:
                raise ContentError("archive_limit", "Archive compression ratio limit exceeded")
        return z
    except BadZipFile as exc:
        raise ContentError("corrupt", "Invalid compressed document") from exc


def resolve(base: str, target: str) -> str:
    url = urlsplit(target)
    if url.scheme or url.netloc or url.query or target.startswith(("/", "\\")):
        raise ContentError("external_reference", "External document reference is not allowed")
    path = unquote(url.path)
    if "\\" in path or ".." in PurePosixPath(path).parts:
        raise ContentError("unsafe_archive", "Unsafe document reference")
    result = posixpath.normpath(posixpath.join(posixpath.dirname(base), path))
    if result.startswith("../") or result.startswith("/"):
        raise ContentError("unsafe_archive", "Unsafe document reference")
    return result


class PlainTextImporter:
    extension = ".txt"

    def supports(self, extension: str) -> bool:
        return extension == self.extension

    def import_document(self, data: bytes, limits: Limits) -> Extraction:
        if data.startswith((b"%PDF-", b"PK\x03\x04")):
            raise ContentError("invalid_format", "Binary document is not plain text")
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ContentError("encoding", "Text must be UTF-8") from exc
        if "\x00" in text:
            raise ContentError("invalid_format", "Invalid text document")
        return Extraction((Part(text),))


class MarkdownImporter(PlainTextImporter):
    extension = ".md"


class PdfImporter:
    def supports(self, extension: str) -> bool:
        return extension == ".pdf"

    def import_document(self, data: bytes, limits: Limits) -> Extraction:
        if not data.startswith(b"%PDF-"):
            raise ContentError("invalid_format", "Invalid PDF signature")
        reader = PdfReader(io.BytesIO(data), strict=True)
        if reader.is_encrypted:
            raise ContentError("protected", "Protected PDF is not supported")
        parts = []
        count = 0
        for number, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            count += len(text)
            if count > limits.max_extracted_chars:
                raise ContentError("size_limit", "Extracted text limit exceeded")
            if text:
                parts.append(Part(text=text, page=number))
        meta = reader.metadata
        return Extraction(
            tuple(parts),
            str(meta.title) if meta and meta.title else None,
            str(meta.author) if meta and meta.author else None,
        )


class DocxImporter:
    def supports(self, extension: str) -> bool:
        return extension == ".docx"

    def import_document(self, data: bytes, limits: Limits) -> Extraction:
        with archive(data, limits) as z:
            names = z.namelist()
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise ContentError("invalid_format", "Invalid DOCX structure")
            for name in names:
                if name.endswith(".rels"):
                    root = safe_xml(z.read(name))
                    for rel in root:
                        if rel.attrib.get("TargetMode", "").lower() == "external":
                            raise ContentError(
                                "external_reference", "External document reference is not allowed"
                            )
            root = safe_xml(z.read("word/document.xml"))
            paragraphs: list[str] = []
            heading_indices: list[int] = []
            for paragraph in root.iter():
                if local_name(paragraph.tag) != "p":
                    continue
                texts = []
                for node in paragraph.iter():
                    name = local_name(node.tag)
                    if name == "t" and node.text:
                        texts.append(node.text)
                    elif name == "tab":
                        texts.append("\t")
                    elif name in {"br", "cr"}:
                        texts.append("\n")
                if any(
                    local_name(node.tag) == "pStyle"
                    and any(value.lower().startswith("heading") for value in node.attrib.values())
                    for node in paragraph.iter()
                ):
                    heading_indices.append(len(paragraphs))
                paragraphs.append("".join(texts))
            meta = {}
            if "docProps/core.xml" in names:
                for el in safe_xml(z.read("docProps/core.xml")):
                    if local_name(el.tag) in {"title", "creator", "language"} and el.text:
                        meta[local_name(el.tag)] = el.text
            heading_offsets = tuple(
                sum(len(p) + 2 for p in paragraphs[:index]) for index in heading_indices
            )
            return Extraction(
                (Part("\n\n".join(paragraphs), headings=heading_offsets),),
                meta.get("title"),
                meta.get("creator"),
                meta.get("language"),
            )


class EpubImporter:
    def supports(self, extension: str) -> bool:
        return extension == ".epub"

    def import_document(self, data: bytes, limits: Limits) -> Extraction:
        with archive(data, limits) as z:
            if z.read("mimetype") != b"application/epub+zip":
                raise ContentError("invalid_format", "Invalid EPUB signature")
            container = safe_xml(z.read("META-INF/container.xml"))
            rootfiles = [
                e.attrib.get("full-path", "")
                for e in container.iter()
                if local_name(e.tag) == "rootfile"
            ]
            if not rootfiles:
                raise ContentError("invalid_format", "Missing EPUB package")
            package = resolve("root", rootfiles[0])
            root = safe_xml(z.read(package))
            meta: dict[str, str] = {}
            manifest = {}
            spine = []
            for el in root.iter():
                name = local_name(el.tag)
                if name in {"title", "creator", "language"} and el.text and name not in meta:
                    meta[name] = el.text
                if name == "item" and "id" in el.attrib and "href" in el.attrib:
                    manifest[el.attrib["id"]] = resolve(package, el.attrib["href"])
                if name == "itemref" and el.attrib.get("idref"):
                    spine.append(el.attrib["idref"])
            parts = []
            for item in spine:
                if item not in manifest:
                    raise ContentError("corrupt", "Invalid EPUB spine")
                path = manifest[item]
                doc = safe_xml(z.read(path))
                for node in doc.iter():
                    for key, value in node.attrib.items():
                        if local_name(key) in {"href", "src"}:
                            url = urlsplit(value)
                            if url.scheme or url.netloc or value.startswith("//"):
                                raise ContentError(
                                    "external_reference",
                                    "External document reference is not allowed",
                                )
                body = next((e for e in doc.iter() if local_name(e.tag) == "body"), None)
                if body is None:
                    continue
                blocks: list[str] = []
                heading_indices: list[int] = []
                ignored = {"script", "style", "iframe", "object"}

                def block_text(node: object) -> str:
                    text = node.text or ""  # type: ignore[attr-defined]
                    for child in node:  # type: ignore[attr-defined]
                        tag = local_name(child.tag)
                        if tag not in ignored:
                            text += "\n" if tag == "br" else block_text(child)
                        text += child.tail or ""
                    return text

                def walk(node: object) -> None:
                    tag = local_name(node.tag)  # type: ignore[attr-defined]
                    if tag in ignored:
                        return
                    if tag in {"p", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "li", "pre"}:
                        if tag.startswith("h") and len(tag) == 2 and tag[1] in "123456":
                            heading_indices.append(len(blocks))
                        blocks.append(block_text(node))
                    else:
                        if node.text and node.text.strip():  # type: ignore[attr-defined]
                            blocks.append(node.text)  # type: ignore[attr-defined]
                        for child in node:  # type: ignore[attr-defined]
                            walk(child)
                            if child.tail and child.tail.strip():
                                blocks.append(child.tail)

                walk(body)
                text = "\n\n".join(blocks)
                if text:
                    headings = tuple(sum(len(b) + 2 for b in blocks[:i]) for i in heading_indices)
                    parts.append(Part(text + "\n\n", source=path, headings=headings))
            if parts:
                last = parts[-1]
                parts[-1] = Part(last.text[:-2], source=last.source, headings=last.headings)
            return Extraction(
                tuple(parts), meta.get("title"), meta.get("creator"), meta.get("language")
            )
