"""Chuyển tệp tài liệu thành HTML an toàn để chèn vào trình soạn thảo.

HTML/Markdown dùng chung bộ lọc của Help Center. DOCX được đọc trực tiếp từ
OpenXML; PDF có lớp chữ được dựng lại qua pdfplumber, PDF scan được giữ dưới
dạng ảnh trang; DOC nhị phân đời cũ được trích chữ bằng ``antiword``.
"""
from __future__ import annotations

import html
import os
import re
import shutil
import subprocess
import tempfile
from uuid import uuid4
import markdown

from app.modules.help_center.import_service import sanitize_html

from .docx_html import docx_to_html

MAX_FILE_SIZE = 10 * 1024 * 1024
# Trình soạn thảo có phân trang theo kích thước DOM thật. Cho một tài liệu vô
# hạn node đi qua thì trình duyệt phải đo hàng trăm trang trong một lượt và có
# thể khóa tab. Giới hạn theo NỘI DUNG SAU CHUYỂN ĐỔI (không chỉ dung lượng file,
# vì DOCX nén rất nhỏ nhưng bung ra có thể cực lớn).
MAX_CONTENT_SIZE = 2 * 1024 * 1024
MAX_STRUCTURAL_NODES = 12_000
TEXT_EXTS = {"html", "htm", "md", "markdown"}
WORD_EXTS = {"doc", "docx"}
PDF_EXTS = {"pdf"}
ALLOWED_EXTS = TEXT_EXTS | WORD_EXTS | PDF_EXTS

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


def parse_document_file(filename: str, raw: bytes) -> dict:
    """Tệp → HTML đã lọc; ném ``ValueError`` nếu không thể nhập."""
    ext = _extension(filename)
    if ext not in ALLOWED_EXTS:
        raise ValueError("Chỉ nhận tệp .doc, .docx, .pdf, .md, .markdown, .html, .htm")
    if not raw:
        raise ValueError("Tệp không có nội dung")
    if len(raw) > MAX_FILE_SIZE:
        raise ValueError("Tệp vượt quá 10MB")

    import_trace = None
    if ext in TEXT_EXTS:
        content = sanitize_html(_text_document_to_html(ext, raw))
    elif ext == "docx":
        content = sanitize_html(docx_to_html(raw))
    elif ext == "pdf":
        # Import lười để API vẫn khởi động và phục vụ DOCX/HTML trong lúc image
        # cũ chưa được rebuild dependency pdfplumber.
        from .pdf_html import pdf_to_html_with_trace

        import_id = uuid4().hex[:12]
        converted, import_trace = pdf_to_html_with_trace(raw, import_id)
        content = sanitize_html(converted)
    else:
        content = sanitize_html(_doc_to_html(raw))

    if (
        not re.sub(r"<[^>]+>", "", content).strip()
        and "<table" not in content
        and "<img" not in content
    ):
        raise ValueError("Không tìm thấy nội dung có thể chèn trong tệp")

    # Đếm những node tác động trực tiếp tới bố cục/pagination. Đây là ngưỡng
    # bảo vệ UX, không phải giới hạn nghiệp vụ; ảnh base64 làm HTML dài nhưng
    # chỉ là một node nên cần kiểm tra riêng cả kích thước lẫn số node.
    structural_nodes = len(re.findall(
        r"<(?:p|h[1-6]|li|tr|br|img|blockquote|pre)\b",
        content,
        re.I,
    ))
    if (
        len(content.encode("utf-8")) > MAX_CONTENT_SIZE
        or structural_nodes > MAX_STRUCTURAL_NODES
    ):
        raise ValueError(
            "Tài liệu quá lớn để soạn trực tuyến. Vui lòng chia thành tệp nhỏ hơn "
            "(tối đa khoảng 12.000 dòng/khối nội dung)."
        )

    result = {
        "filename": filename,
        "content_html": content,
        "structural_nodes": structural_nodes,
    }
    if import_trace:
        result["import_trace"] = import_trace
    return result
