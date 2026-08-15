"""Chuyển tệp tài liệu thành HTML an toàn để chèn vào trình soạn thảo.

HTML/Markdown dùng chung bộ lọc của Help Center. DOCX được đọc trực tiếp từ
OpenXML để không phải phụ thuộc vào một dịch vụ chuyển đổi bên ngoài; DOC nhị
phân đời cũ được trích chữ bằng ``antiword`` có sẵn trong image API.
"""
from __future__ import annotations

import html
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from io import BytesIO
from xml.etree import ElementTree

import markdown

from app.modules.help_center.import_service import sanitize_html

MAX_FILE_SIZE = 10 * 1024 * 1024
TEXT_EXTS = {"html", "htm", "md", "markdown"}
WORD_EXTS = {"doc", "docx"}
ALLOWED_EXTS = TEXT_EXTS | WORD_EXTS

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W = f"{{{_W_NS}}}"


def _extension(filename: str) -> str:
    return (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()


def _decode_text(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1258", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Không đọc được nội dung tệp Word")


def _plain_text_to_html(text: str) -> str:
    """Đổi đầu ra chữ trần của antiword thành các đoạn có thể sửa trong editor."""
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n").replace("\r", "\n"))
    rendered = []
    for block in blocks:
        lines = [html.escape(line.rstrip()) for line in block.split("\n")]
        value = "<br>".join(lines).strip()
        if value:
            rendered.append(f"<p>{value}</p>")
    return "".join(rendered)


def _text_document_to_html(ext: str, raw: bytes) -> str:
    text = _decode_text(raw)
    if ext in {"md", "markdown"}:
        return markdown.markdown(
            text,
            extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
        )
    body = re.search(r"<body[^>]*>(.*)</body>", text, re.I | re.S)
    return body.group(1) if body else text


def _doc_to_html(raw: bytes) -> str:
    antiword = shutil.which("antiword")
    if not antiword:
        raise ValueError("Máy chủ chưa có bộ đọc tệp .doc")

    path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as temp:
            temp.write(raw)
            path = temp.name
        completed = subprocess.run(
            [antiword, path],
            capture_output=True,
            check=False,
            timeout=20,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError("Tệp .doc mất quá nhiều thời gian để xử lý") from exc
    finally:
        if path:
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass

    if completed.returncode != 0:
        detail = _decode_text(completed.stderr).strip()
        raise ValueError(detail or "Không đọc được tệp .doc")
    return _plain_text_to_html(_decode_text(completed.stdout))


def _run_html(run: ElementTree.Element) -> str:
    parts: list[str] = []
    for node in run:
        if node.tag == f"{_W}t":
            parts.append(html.escape(node.text or ""))
        elif node.tag == f"{_W}tab":
            parts.append("&emsp;")
        elif node.tag in {f"{_W}br", f"{_W}cr"}:
            parts.append("<br>")
    value = "".join(parts)
    if not value:
        return ""

    properties = run.find(f"{_W}rPr")
    if properties is None:
        return value
    if properties.find(f"{_W}b") is not None:
        value = f"<strong>{value}</strong>"
    if properties.find(f"{_W}i") is not None:
        value = f"<em>{value}</em>"
    if properties.find(f"{_W}u") is not None:
        value = f"<u>{value}</u>"
    if properties.find(f"{_W}strike") is not None:
        value = f"<s>{value}</s>"
    return value


def _paragraph_html(paragraph: ElementTree.Element) -> str:
    value = "".join(_run_html(run) for run in paragraph.iter(f"{_W}r"))
    properties = paragraph.find(f"{_W}pPr")
    style = properties.find(f"{_W}pStyle") if properties is not None else None
    style_name = style.get(f"{_W}val", "") if style is not None else ""
    heading = re.search(r"(?:heading|tiêuđề|tieude)\s*([1-6])", style_name, re.I)
    if heading:
        level = heading.group(1)
        return f"<h{level}>{value}</h{level}>"
    return f"<p>{value}</p>"


def _table_html(table: ElementTree.Element) -> str:
    rows: list[str] = []
    for row in table.findall(f"{_W}tr"):
        cells: list[str] = []
        for cell in row.findall(f"{_W}tc"):
            content = "".join(_paragraph_html(p) for p in cell.findall(f"{_W}p"))
            cells.append(f"<td>{content}</td>")
        if cells:
            rows.append(f"<tr>{''.join(cells)}</tr>")
    return f"<table><tbody>{''.join(rows)}</tbody></table>" if rows else ""


def _docx_to_html(raw: bytes) -> str:
    try:
        with zipfile.ZipFile(BytesIO(raw)) as archive:
            document_xml = archive.read("word/document.xml")
        root = ElementTree.fromstring(document_xml)
    except (zipfile.BadZipFile, KeyError, ElementTree.ParseError) as exc:
        raise ValueError("Tệp .docx không hợp lệ hoặc đã bị hỏng") from exc

    body = root.find(f"{_W}body")
    if body is None:
        raise ValueError("Tệp .docx không có nội dung")

    rendered: list[str] = []
    for child in body:
        if child.tag == f"{_W}p":
            rendered.append(_paragraph_html(child))
        elif child.tag == f"{_W}tbl":
            rendered.append(_table_html(child))
    return "".join(rendered)


def parse_document_file(filename: str, raw: bytes) -> dict:
    """Tệp → HTML đã lọc; ném ``ValueError`` nếu không thể nhập."""
    ext = _extension(filename)
    if ext not in ALLOWED_EXTS:
        raise ValueError("Chỉ nhận tệp .doc, .docx, .md, .markdown, .html, .htm")
    if not raw:
        raise ValueError("Tệp không có nội dung")
    if len(raw) > MAX_FILE_SIZE:
        raise ValueError("Tệp vượt quá 10MB")

    if ext in TEXT_EXTS:
        content = sanitize_html(_text_document_to_html(ext, raw))
    elif ext == "docx":
        content = sanitize_html(_docx_to_html(raw))
    else:
        content = sanitize_html(_doc_to_html(raw))

    if not re.sub(r"<[^>]+>", "", content).strip() and "<table" not in content:
        raise ValueError("Không tìm thấy nội dung có thể chèn trong tệp")
    return {"filename": filename, "content_html": content}
