"""Text extraction from the file types a user can upload."""

import io
import json

import pytest
from docx import Document as DocxDocument

from corpus.services.extract import UnsupportedDocument, extract, strip_tags


def test_plain_text_round_trips():
    assert extract("a.txt", "Bir iki üç.".encode()) == "Bir iki üç."


def test_newlines_are_flattened():
    """Layout must not break sentence tokenisation."""
    assert "\n" not in extract("a.txt", b"one\ntwo\r\nthree")


def test_docx_is_read():
    document = DocxDocument()
    document.add_paragraph("İstanbul çok güzeldir.")
    buffer = io.BytesIO()
    document.save(buffer)
    assert "İstanbul" in extract("a.docx", buffer.getvalue())


def test_json_is_unpacked():
    payload = json.dumps({"data": [{"title": "Işık", "songxml": "<b>parlak</b>"}]})
    text = extract("a.json", payload.encode())
    assert "Işık" in text
    assert "parlak" in text
    assert "<b>" not in text


def test_unfamiliar_json_still_yields_text():
    payload = json.dumps({"nested": {"deep": ["merhaba", "dünya"]}})
    text = extract("a.json", payload.encode())
    assert "merhaba" in text and "dünya" in text


def test_unsupported_extension_is_rejected():
    with pytest.raises(UnsupportedDocument):
        extract("virus.exe", b"...")


def test_undecodable_bytes_do_not_break_ingest():
    """Corpus files come from everywhere; never fail on one bad byte."""
    assert extract("a.txt", b"caf\xff") is not None


def test_strip_tags_leaves_a_space_behind():
    assert strip_tags("<b>a</b><i>b</i>").split() == ["a", "b"]
