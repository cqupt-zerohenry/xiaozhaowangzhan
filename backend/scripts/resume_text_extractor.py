"""CLI script: extract plain text from resume files (PDF/DOC/DOCX/TXT/MD)."""
from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

logger = logging.getLogger(__name__)


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    normalized = (
        text.replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\x00", "")
        .replace("\u200b", "")
    )
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _read_plain_text(path: Path) -> str:
    encodings = ("utf-8", "utf-8-sig", "gb18030", "gbk", "latin-1")
    for enc in encodings:
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return ""


def _run_cmd(cmd: list[str], timeout: int = 15) -> str:
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout
    except FileNotFoundError:
        return ""
    except Exception:
        logger.exception("Command execution failed: %s", cmd)
    return ""


def _extract_pdf(path: Path) -> str:
    # Python parser first.
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(str(path))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        if text.strip():
            return text
    except Exception:
        logger.exception("PyPDF2 extraction failed")

    # Tool fallback if available on host.
    return _run_cmd(["pdftotext", str(path), "-"])


def _extract_docx(path: Path) -> str:
    try:
        from docx import Document

        doc = Document(str(path))
        text = "\n".join((p.text or "") for p in doc.paragraphs)
        if text.strip():
            return text
    except Exception:
        logger.exception("python-docx extraction failed")

    # Fallback: unzip XML and read text nodes.
    try:
        with zipfile.ZipFile(path) as zf:
            xml_bytes = zf.read("word/document.xml")
        root = ElementTree.fromstring(xml_bytes)
        texts = [node.text for node in root.iter() if node.text]
        return "\n".join(texts)
    except Exception:
        logger.exception("DOCX XML fallback extraction failed")
        return ""


def _extract_doc(path: Path) -> str:
    # macOS built-in textutil first.
    for cmd in (
        ["textutil", "-convert", "txt", "-stdout", str(path)],
        ["antiword", str(path)],
        ["catdoc", str(path)],
    ):
        text = _run_cmd(cmd)
        if text.strip():
            return text
    return ""


def extract_text(path: Path) -> tuple[str, str]:
    ext = path.suffix.lower().lstrip(".")
    if ext == "pdf":
        text = _extract_pdf(path)
    elif ext == "docx":
        text = _extract_docx(path)
    elif ext == "doc":
        text = _extract_doc(path)
    elif ext in {"txt", "md"}:
        text = _read_plain_text(path)
    else:
        return "", f"unsupported extension: {ext or 'unknown'}"

    normalized = _normalize_text(text)
    if not normalized:
        return "", f"cannot extract text from {ext or 'file'}"
    return normalized, ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract plain text from resume file.")
    parser.add_argument("input_file", help="Path to input file")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(json.dumps({"ok": False, "text": "", "error": "file not found"}, ensure_ascii=False))
        return 2

    text, error = extract_text(input_path)
    ok = bool(text.strip())
    print(json.dumps({"ok": ok, "text": text, "error": error}, ensure_ascii=False))
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
