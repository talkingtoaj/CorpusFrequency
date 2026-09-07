"""Pull plain text out of an uploaded file.

PDF extraction uses pypdf rather than tika: tika shells out to a Java
server, which is a poor fit for a hosted service that should start fast
and run in a slim container.
"""

import io
import json

import docx2txt
from pypdf import PdfReader


class UnsupportedDocument(Exception):
    """Raised when a file's extension is not one we can read."""


def _from_docx(handle):
    return docx2txt.process(handle) or ""


def _from_pdf(handle):
    reader = PdfReader(handle)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _from_json(handle):
    """Unpack the song-export shape the original project was built around.

    Falls back to concatenating every string value found, so an unfamiliar
    JSON file yields something usable rather than an error.
    """
    contents = json.loads(handle.read().decode("utf-8"))
    entries = contents.get("data") if isinstance(contents, dict) else None
    if isinstance(entries, list):
        parts = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for value in entry.values():
                if isinstance(value, str):
                    parts.append(strip_tags(value))
        return " ".join(parts)
    return " ".join(_strings(contents))


def _strings(node):
    if isinstance(node, str):
        yield strip_tags(node)
    elif isinstance(node, dict):
        for value in node.values():
            yield from _strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _strings(value)


def strip_tags(markup):
    """Remove anything between angle brackets, leaving a space behind."""
    out = []
    depth = 0
    for character in markup:
        if character == "<":
            depth += 1
            out.append(" ")
        elif character == ">":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(character)
    return "".join(out)


def _from_text(handle):
    raw = handle.read()
    if isinstance(raw, bytes):
        # Corpus files come from all sorts of places; never fail ingest on
        # one bad byte.
        return raw.decode("utf-8", errors="replace")
    return raw


READERS = {
    ".docx": _from_docx,
    ".pdf": _from_pdf,
    ".json": _from_json,
    ".txt": _from_text,
    ".md": _from_text,
    ".csv": _from_text,
}

SUPPORTED_EXTENSIONS = sorted(READERS)


def extract(filename, data):
    """Return the plain text of `data`, dispatching on `filename`'s suffix."""
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    reader = READERS.get(suffix)
    if reader is None:
        raise UnsupportedDocument(
            f"Cannot read '{filename}'. Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    handle = io.BytesIO(data) if isinstance(data, bytes) else data
    text = reader(handle)
    # Collapse newlines so sentence tokenisation is not thrown by layout.
    return text.replace("\r", " ").replace("\n", " ")
