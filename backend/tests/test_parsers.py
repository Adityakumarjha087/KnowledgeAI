import io

import pytest
from docx import Document as DocxDocument

from app.ingestion.parsers import parse_document


def _docx_bytes(paragraphs):
    doc = DocxDocument()
    for p in paragraphs:
        doc.add_paragraph(p)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def test_parse_docx_joins_paragraphs():
    text, pages = parse_document(_docx_bytes(["Leave policy", "Sick leave is 10 days."]), "docx")

    assert "Leave policy" in text
    assert "Sick leave is 10 days." in text
    assert pages == 1


def test_extension_is_case_and_dot_insensitive():
    text, _ = parse_document(b"hello", ".TXT")

    assert text == "hello"


def test_long_text_page_estimate_scales_with_length():
    _, pages = parse_document(b"a" * 9500, "md")

    assert pages == 3


def test_invalid_utf8_bytes_are_dropped_instead_of_failing():
    text, _ = parse_document(b"ok \xff\xfe done", "txt")

    assert text == "ok  done"


def test_unsupported_extension_is_rejected():
    with pytest.raises(ValueError, match="Unsupported file format: exe"):
        parse_document(b"MZ", "exe")
