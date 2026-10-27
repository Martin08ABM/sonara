import io
import json
import zipfile
from pathlib import Path

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from sonara.content import ContentError, ContentService, Limits, SegmentationConfig


def make_zip(entries: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, value in entries.items():
            z.writestr(name, value)
    return buf.getvalue()


def epub(body: str = "<h1>Heading</h1><p>¡Hola, niña!</p>") -> bytes:
    return make_zip(
        {
            "mimetype": "application/epub+zip",
            "META-INF/container.xml": '<container><rootfile full-path="OPS/book.opf"/></container>',
            "OPS/book.opf": "<package><metadata><title>Book</title><creator>Ana</creator>"
            '<language>es</language></metadata><manifest><item id="a" href="one.xhtml"/>'
            '</manifest><spine><itemref idref="a"/></spine></package>',
            "OPS/one.xhtml": f"<html><body>{body}</body></html>",
        }
    )


def docx(extra: dict[str, str] | None = None) -> bytes:
    entries = {
        "[Content_Types].xml": "<Types/>",
        "word/document.xml": '<w:document xmlns:w="urn:word"><w:body>'
        "<w:p><w:r><w:t>¡Hola, niña!</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>—Sí.</w:t></w:r></w:p></w:body></w:document>",
    }
    entries.update(extra or {})
    return make_zip(entries)


def pdf(text: bool = True) -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    if text:
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
        )
        stream = DecodedStreamObject()
        stream.set_data(b"BT /F1 12 Tf 20 200 Td (Hello Sonara) Tj ET")
        page[NameObject("/Contents")] = writer._add_object(stream)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def write(tmp_path: Path, name: str, data: bytes) -> Path:
    path = tmp_path / name
    path.write_bytes(data)
    return path


@pytest.mark.parametrize(
    ("name", "data", "expected"),
    [
        ("book.txt", "¡Niña!\r\n—Sí.  “Vale”\n".encode(), "¡Niña!\r\n—Sí.  “Vale”\n"),
        ("book.md", "# Título\n\n—Hola.\n".encode(), "# Título\n\n—Hola.\n"),
        ("book.epub", epub(), "Heading\n\n¡Hola, niña!"),
        ("book.docx", docx(), "¡Hola, niña!\n\n—Sí."),
        ("book.pdf", pdf(), "Hello Sonara"),
    ],
)
def test_all_formats(tmp_path: Path, name: str, data: bytes, expected: str) -> None:
    document = ContentService().import_file(write(tmp_path, name, data))
    assert expected in document.extracted_text
    assert "".join(f.text for f in document.fragments) == document.extracted_text
    assert all(document.extracted_text[f.start : f.end] == f.text for f in document.fragments)
    if name.endswith("pdf"):
        assert document.fragments[0].page == 1
    if name.endswith("epub"):
        assert (document.title, document.author, document.language) == ("Book", "Ana", "es")


def test_segments_metadata_and_events(tmp_path: Path) -> None:
    text = "# Título\n\n—Buenos días.\n\n" + ("niño y niña. " * 80) + "\n\n# Final\n—Adiós."
    path = write(tmp_path, "book.md", text.encode())
    service = ContentService(segmentation=SegmentationConfig(40, 60))
    doc = service.import_file(path)
    assert len(doc.sections) == 2
    assert doc.sections[0].elements[0].kind == "heading"
    assert any(e.kind == "dialogue_candidate" for s in doc.sections for e in s.elements)
    assert all(len(f.text) <= 60 for f in doc.fragments)
    assert "".join(f.text for f in doc.fragments) == text
    assert doc.events[0].kind == "DOCUMENT_START" and doc.events[-1].kind == "DOCUMENT_END"
    again = service.import_file(path)
    assert doc.id == again.id and doc.to_json() == again.to_json()
    assert "imported_at" not in json.loads(doc.to_json())
    assert "imported_at" in json.loads(doc.to_json(include_imported_at=True))
    assert any(e.kind == "quote" for e in service.import_text("> quote").sections[0].elements)


def test_word_limit_and_short_dialogue() -> None:
    service = ContentService(segmentation=SegmentationConfig(8, 12))
    result = service.import_text("—Hola.\n\nOtra cosa.")
    assert result.fragments[0].text.startswith("—Hola.")
    with pytest.raises(ContentError, match="word") as exc:
        service.import_text("x" * 20)
    assert exc.value.code == "word_too_long"
    with pytest.raises(ValueError):
        SegmentationConfig(100, 10)


@pytest.mark.parametrize(
    ("name", "data", "code"),
    [
        ("x.xyz", b"hi", "unsupported_format"),
        ("x.txt", b"", "empty"),
        ("x.txt", b"\xff", "encoding"),
        ("x.pdf", b"bad", "invalid_format"),
        ("x.pdf", pdf(False), "no_text"),
        ("x.epub", b"PK garbage", "corrupt"),
        ("x.epub", make_zip({"../bad": "oops"}), "unsafe_archive"),
        (
            "x.docx",
            docx(
                {
                    "word/_rels/document.xml.rels": (
                        '<Relationships><Relationship TargetMode="External" '
                        'Target="https://example.org"/></Relationships>'
                    )
                }
            ),
            "external_reference",
        ),
        ("x.epub", epub('<p><img src="https://example.org/x"/></p>'), "external_reference"),
        ("x.docx", make_zip({"word/document.xml": "bad"}), "invalid_format"),
    ],
)
def test_structured_errors(tmp_path: Path, name: str, data: bytes, code: str) -> None:
    with pytest.raises(ContentError) as exc:
        ContentService().import_file(write(tmp_path, name, data))
    assert exc.value.code == code
    assert str(tmp_path) not in str(exc.value)


def test_limits_and_read_error(tmp_path: Path) -> None:
    with pytest.raises(ContentError) as exc:
        ContentService(limits=Limits(max_file_bytes=3)).import_file(
            write(tmp_path, "big.txt", b"1234")
        )
    assert exc.value.code == "size_limit"
    with pytest.raises(ContentError) as exc:
        ContentService().import_file(tmp_path / "missing.txt")
    assert exc.value.code == "read_error"
    with pytest.raises(ContentError) as exc:
        ContentService(limits=Limits(max_archive_entries=1)).import_file(
            write(tmp_path, "x.epub", epub())
        )
    assert exc.value.code == "archive_limit"


def test_exact_word_boundary_and_spaces() -> None:
    service = ContentService(segmentation=SegmentationConfig(5, 10))
    for text in ["1234567890 x", "a" + " " * 30 + "b"]:
        doc = service.import_text(text)
        assert "".join(f.text for f in doc.fragments) == text
        assert all(len(f.text) <= 10 for f in doc.fragments)


def test_epub_scripts_are_not_imported(tmp_path: Path) -> None:
    data = epub("<p>Hello<script>evil()</script> world<br/>next</p>")
    doc = ContentService().import_file(write(tmp_path, "x.epub", data))
    assert doc.extracted_text == "Hello world\nnext"


def test_archive_traversal_and_expansion(tmp_path: Path) -> None:
    data = make_zip({"/absolute": "x"})
    with pytest.raises(ContentError) as exc:
        ContentService().import_file(write(tmp_path, "bad.docx", data))
    assert exc.value.code == "unsafe_archive"
    with pytest.raises(ContentError) as exc:
        ContentService(limits=Limits(max_uncompressed_bytes=10)).import_file(
            write(tmp_path, "big.docx", docx())
        )
    assert exc.value.code == "archive_limit"


def test_protected_pdf(tmp_path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=30, height=30)
    writer.encrypt("secret")
    stream = io.BytesIO()
    writer.write(stream)
    with pytest.raises(ContentError) as exc:
        ContentService().import_file(write(tmp_path, "secret.pdf", stream.getvalue()))
    assert exc.value.code == "protected"


def test_epub_heading_structure(tmp_path: Path) -> None:
    doc = ContentService().import_file(write(tmp_path, "book.epub", epub()))
    assert doc.sections[0].title == "Heading"
    assert doc.sections[0].elements[0].kind == "heading"
    assert "".join(fragment.text for fragment in doc.fragments) == doc.extracted_text


def test_docx_heading_structure(tmp_path: Path) -> None:
    document = (
        '<w:document xmlns:w="urn:word"><w:body><w:p>'
        '<w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
        "<w:r><w:t>Chapter</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>Content</w:t></w:r></w:p></w:body></w:document>"
    )
    path = write(tmp_path, "book.docx", docx({"word/document.xml": document}))
    result = ContentService().import_file(path)
    assert result.sections[0].title == "Chapter"
    assert result.sections[0].elements[0].kind == "heading"


def test_xml_entities_rejected(tmp_path: Path) -> None:
    data = epub("<p>&secret;</p>")
    # Rebuild a hostile XHTML document containing a DTD and external entity.
    data = make_zip(
        {
            "mimetype": "application/epub+zip",
            "META-INF/container.xml": '<container><rootfile full-path="book.opf"/></container>',
            "book.opf": '<package><manifest><item id="x" href="x.xhtml"/></manifest>'
            '<spine><itemref idref="x"/></spine></package>',
            "x.xhtml": '<!DOCTYPE html [<!ENTITY secret SYSTEM "file:///etc/passwd">]>'
            "<html><body><p>&secret;</p></body></html>",
        }
    )
    with pytest.raises(ContentError) as exc:
        ContentService().import_file(write(tmp_path, "hostile.epub", data))
    assert exc.value.code == "corrupt"


def test_invalid_document_contract() -> None:
    from dataclasses import replace

    doc = ContentService().import_text("Some text")
    with pytest.raises(ValueError, match="events"):
        replace(doc, events=())
    with pytest.raises(ValueError, match="integrity"):
        replace(doc, integrity_sha256="bad")
    fragment = replace(doc.fragments[0], end=1)
    with pytest.raises(ValueError, match="fragment"):
        replace(doc, fragments=(fragment,))


def test_import_without_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import socket

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Unexpected network access")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    for name, data in [("a.epub", epub()), ("b.docx", docx()), ("c.pdf", pdf())]:
        doc = ContentService().import_file(write(tmp_path, name, data))
        assert doc.fragments
