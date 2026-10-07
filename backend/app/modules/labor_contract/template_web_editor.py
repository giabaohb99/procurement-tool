"""Soạn mẫu hợp đồng NGAY TRÊN WEB (duoc-CR-606, 07/10/2026).

Trước đây muốn sửa một chữ trong mẫu phải tải .docx về, sửa bằng Word, tải lên lại — và tự gõ tay
`{{ ho_ten }}`, gõ sai một chữ là bị chặn. Nay: mở .docx thành HTML cho trình soạn thảo của phân hệ
Văn bản (`document.docx_html`), lưu thì dựng lại .docx (`document.html_docx`) rồi kiểm ĐÚNG như lúc
tải lên (`inspect_template`: biến lạ, Jinja ngoài `{{ biến }}`, gói zip) và thay tệp như «Thay tệp».

Đánh đổi đã biết: bộ chuyển chỉ giữ thân văn bản (chữ, bảng, ảnh, căn lề, cỡ chữ) và lề TRÁI / PHẢI
của bản gốc; đầu trang / chân trang và vài định dạng riêng của Word không qua được — màn hình phải
nói trước khi người dùng bấm Lưu.
"""
import re
import zipfile
from io import BytesIO

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.file_registry import direct_policy
from app.modules.document.docx_html import docx_to_html
from app.modules.document.html_docx import html_to_docx

from . import template_service
from .docx_engine import inspect_template
from .template_model import LaborContractTemplate
from .template_schema import MARGIN_MAX_MM, MARGIN_MIN_MM, MAX_PLACEHOLDERS, TemplateContentIn

DEFAULT_LEFT_MM, DEFAULT_RIGHT_MM = 30, 20
_TWIPS_PER_MM = 1440 / 25.4
_PGMAR_RE = re.compile(r"<w:pgMar\b[^>]*>")
_ATTR_RE = re.compile(r'w:(left|right)="(-?\d+)"')


def _clamp(mm: int) -> int:
    return max(MARGIN_MIN_MM, min(MARGIN_MAX_MM, mm))


def page_margins_mm(docx_bytes: bytes) -> tuple[int, int]:
    """Lề trái / phải (mm) của khổ cuối trong .docx; không đọc được thì lề Nghị định 30 (30 / 20)."""
    try:
        with zipfile.ZipFile(BytesIO(docx_bytes)) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    except (zipfile.BadZipFile, KeyError):
        return DEFAULT_LEFT_MM, DEFAULT_RIGHT_MM
    found = _PGMAR_RE.findall(xml)
    if not found:
        return DEFAULT_LEFT_MM, DEFAULT_RIGHT_MM
    attrs = dict(_ATTR_RE.findall(found[-1]))
    left = round(int(attrs.get("left", 0)) / _TWIPS_PER_MM) or DEFAULT_LEFT_MM
    right = round(int(attrs.get("right", 0)) / _TWIPS_PER_MM) or DEFAULT_RIGHT_MM
    return _clamp(left), _clamp(right)


def read_content(db: Session, row: LaborContractTemplate) -> dict:
    """Tệp mẫu hiện tại → HTML + lề, cho trang soạn trên web."""
    data = template_service.read_template_file(db, row)
    try:
        html = docx_to_html(data)
    except Exception as exc:  # tệp Word lạ — vẫn còn đường tải về sửa bằng Word
        raise HTTPException(422, "Không mở được tệp mẫu để soạn trên web — hãy tải về sửa bằng Word "
                                 "rồi dùng «Thay tệp».") from exc
    left, right = page_margins_mm(data)
    return {"html": html, "margin_left_mm": left, "margin_right_mm": right}


def save_content(db: Session, user, row: LaborContractTemplate, data: TemplateContentIn) -> None:
    """HTML → .docx → kiểm như tải lên → thay tệp. Biến sai ném `TemplateRejected` (422 kèm chip)."""
    file_bytes = html_to_docx(data.html, margin_left_mm=data.margin_left_mm,
                              margin_right_mm=data.margin_right_mm)
    _, max_mb = direct_policy(template_service.KIND)
    if len(file_bytes) > max_mb * 1024 * 1024:
        raise HTTPException(422, f"Mẫu sau khi lưu lớn hơn {max_mb} MB — bớt ảnh hoặc nén ảnh lại")
    placeholders = inspect_template(file_bytes)
    if len(placeholders) > MAX_PLACEHOLDERS:
        raise HTTPException(422, "Mẫu dùng quá nhiều biến")
    filename = (row.original_filename or "").strip() or f"{row.name}.docx"
    if not filename.lower().endswith(".docx"):
        filename = f"{filename.rsplit('.', 1)[0]}.docx"
    template_service.swap_file(db, user, row, file_bytes, placeholders, filename)
