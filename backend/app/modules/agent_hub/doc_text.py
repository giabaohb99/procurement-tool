"""Đọc chữ trong tệp văn phòng (ai-CR-105) — pdf, Word, Excel, văn bản thường — để bot đọc báo cáo người dùng gửi
riêng hoặc tệp gửi trong nhóm. Chỉ đọc chữ; ảnh đi đường ảnh, ghi âm / video đi đường biên bản họp.
"""
from __future__ import annotations

import io
import subprocess
import tempfile
from pathlib import Path

MAX_CHARS = 60_000
XLSX_SHEETS = 5
XLSX_ROWS = 300

READABLE_EXT = {".pdf", ".docx", ".xlsx", ".xlsm", ".txt", ".csv", ".md", ".doc"}
READABLE_MIME = {
    "application/pdf", "text/plain", "text/csv", "text/markdown", "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel.sheet.macroenabled.12",
}


class DocTextError(ValueError):
    """Không đọc được tệp — câu nói được cho người dùng."""


def readable(name: str, mime: str) -> bool:
    return (mime or "") in READABLE_MIME or Path(name or "").suffix.lower() in READABLE_EXT


def extract(name: str, mime: str, data: bytes) -> str:
    ext = Path(name or "").suffix.lower()
    if ext == ".pdf" or mime == "application/pdf" or data[:4] == b"%PDF":
        text = _pdf(data)
    elif ext == ".docx" or mime.endswith("wordprocessingml.document"):
        text = _docx(data)
    elif ext in (".xlsx", ".xlsm") or "spreadsheetml" in (mime or "") or "macroenabled" in (mime or ""):
        text = _xlsx(data)
    elif ext == ".doc" or mime == "application/msword":
        text = _doc(data)
    else:
        text = data.decode("utf-8", errors="replace")
    text = "\n".join(line.rstrip() for line in text.splitlines() if line.strip())
    if not text.strip():
        raise DocTextError("tệp không có chữ đọc được (có thể là bản scan — gửi dạng ảnh để em đọc bằng mắt)")
    return text[:MAX_CHARS] + ("\n[… tệp dài, em chỉ đọc phần đầu]" if len(text) > MAX_CHARS else "")


def _pdf(data: bytes) -> str:
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages[:200])
    except Exception as e:  # noqa: BLE001 — pdf hỏng / có mật khẩu
        raise DocTextError(f"không mở được PDF ({type(e).__name__})") from None


def _docx(data: bytes) -> str:
    from docx import Document

    try:
        doc = Document(io.BytesIO(data))
    except Exception as e:  # noqa: BLE001
        raise DocTextError(f"không mở được tệp Word ({type(e).__name__})") from None
    lines = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            lines.append(" | ".join(c.text.strip() for c in row.cells))
    return "\n".join(lines)


def _xlsx(data: bytes) -> str:
    from openpyxl import load_workbook

    try:
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception as e:  # noqa: BLE001
        raise DocTextError(f"không mở được tệp Excel ({type(e).__name__})") from None
    out = []
    for ws in wb.worksheets[:XLSX_SHEETS]:
        out.append(f"## Trang tính: {ws.title}")
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i >= XLSX_ROWS:
                out.append("[… còn nữa]")
                break
            cells = ["" if v is None else str(v) for v in row]
            if any(cells):
                out.append(" | ".join(cells))
    return "\n".join(out)


def _doc(data: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as fh:
        fh.write(data)
        path = fh.name
    try:
        proc = subprocess.run(["antiword", path], capture_output=True, text=True, timeout=60)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        raise DocTextError("máy chủ chưa đọc được tệp .doc đời cũ — lưu lại thành .docx giúp em") from None
    finally:
        Path(path).unlink(missing_ok=True)
    if proc.returncode != 0:
        raise DocTextError("không đọc được tệp .doc này")
    return proc.stdout
