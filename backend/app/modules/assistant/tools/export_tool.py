"""Tool `export_report_file`: XUẤT nội dung trợ lý tổng hợp thành file Word (.docx) chuẩn DEGO.

Khác các tool loại A (read-only), tool này GHI hai thứ — một object lên storage và một dòng
`tab_file` (StoredFile) — nhưng không đụng chứng từ nghiệp vụ nào. File thuộc về NGƯỜI HỎI
(created_by), chỉ chủ file tải được qua `GET /api/assistant/files/{id}/download`; giao diện
chat đọc khóa `file` trên tool call và hiện nút "Tải báo cáo".

Dữ liệu trong báo cáo là chữ model đã tổng hợp TRONG hội thoại (kết quả các tool tra cứu đã
qua apply_scope) — tool này không tự tra thêm gì, nên không mở lối rò dữ liệu mới.
"""
from io import BytesIO

from .base import ToolContext, ToolSpec

MAX_SECTIONS = 15
MAX_PARAS = 20          # đoạn văn mỗi mục
MAX_BULLETS = 30
MAX_COLS = 6
MAX_ROWS = 200
MAX_CELL = 300
MAX_TEXT = 2000

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

_PARAMS = {
    "type": "object",
    "properties": {
        "filename": {
            "type": "string",
            "description": "Tên tệp không dấu, không đuôi (vd: bao-cao-chi-tieu-thang-7).",
        },
        "title": {"type": "string", "description": "Tiêu đề lớn của báo cáo — bắt buộc."},
        "subtitle": {"type": "string", "description": "Phụ đề ngắn dưới tiêu đề (nếu có)."},
        "meta": {
            "type": "array",
            "description": "Thông tin chung dạng nhãn-giá trị (Kỳ báo cáo, Phạm vi, Người lập...).",
            "items": {
                "type": "object",
                "properties": {"label": {"type": "string"}, "value": {"type": "string"}},
                "required": ["label", "value"],
            },
        },
        "summary": {
            "type": "array",
            "description": "3-6 gạch đầu dòng tóm tắt cho hộp TL;DR đầu báo cáo.",
            "items": {"type": "string"},
        },
        "sections": {
            "type": "array",
            "description": f"Các mục nội dung theo thứ tự (tối đa {MAX_SECTIONS}).",
            "items": {
                "type": "object",
                "properties": {
                    "heading": {"type": "string", "description": "Tên mục — bắt buộc."},
                    "paragraphs": {
                        "type": "array", "items": {"type": "string"},
                        "description": "Các đoạn văn của mục.",
                    },
                    "bullets": {
                        "type": "array", "items": {"type": "string"},
                        "description": "Các gạch đầu dòng của mục.",
                    },
                    "table": {
                        "type": "object",
                        "description": f"Bảng số liệu (tối đa {MAX_COLS} cột x {MAX_ROWS} dòng); "
                                       "cột STT tự thêm, đừng khai.",
                        "properties": {
                            "columns": {"type": "array", "items": {"type": "string"}},
                            "rows": {
                                "type": "array",
                                "items": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                        "required": ["columns", "rows"],
                    },
                },
                "required": ["heading"],
            },
        },
    },
    "required": ["title", "sections"],
}

_DESC = (
    "XUẤT nội dung đã tổng hợp trong hội thoại thành file báo cáo Word (.docx) định dạng chuẩn "
    "DEGO để người dùng tải về. Gọi khi người dùng muốn 'xuất file', 'tạo file báo cáo', 'lưu "
    "thành Word'. Đổ số liệu THẬT đã tra cứu được trong hội thoại vào sections (đoạn văn, gạch "
    "đầu dòng, bảng) — không bịa số. Trong chuỗi có thể dùng <strong>chữ đậm</strong> và <br>. "
    "Sau khi gọi, báo người dùng bấm nút 'Tải báo cáo' ngay dưới câu trả lời để lưu file về máy."
)


def _clean(value, limit: int = MAX_TEXT) -> str:
    return str(value or "").strip()[:limit]


def _clean_sections(raw_sections: list) -> list[dict]:
    sections = []
    for raw in raw_sections[:MAX_SECTIONS]:
        if not isinstance(raw, dict):
            continue
        heading = _clean(raw.get("heading"), 200)
        if not heading:
            continue
        sec: dict = {"heading": heading, "paragraphs": [], "bullets": [], "table": None}
        for p in (raw.get("paragraphs") or [])[:MAX_PARAS]:
            text = _clean(p)
            if text:
                sec["paragraphs"].append(text)
        for b in (raw.get("bullets") or [])[:MAX_BULLETS]:
            text = _clean(b)
            if text:
                sec["bullets"].append(text)
        table = raw.get("table")
        if isinstance(table, dict):
            cols = [_clean(c, 100) for c in (table.get("columns") or [])[:MAX_COLS]]
            cols = [c for c in cols if c]
            rows = []
            for row in (table.get("rows") or [])[:MAX_ROWS]:
                if isinstance(row, list):
                    #  Kẹp mỗi dòng về đúng số cột — model hay trả dòng lệch cột.
                    values = [_clean(v, MAX_CELL) for v in row[:len(cols)]]
                    values += [""] * (len(cols) - len(values))
                    rows.append(values)
            if cols and rows:
                sec["table"] = {"columns": cols, "rows": rows}
        if sec["paragraphs"] or sec["bullets"] or sec["table"]:
            sections.append(sec)
    return sections


def render_docx(spec: dict) -> bytes:
    """Dựng file .docx từ spec ĐÃ chuẩn hóa. Tách riêng để test không cần DB/storage."""
    from datetime import datetime

    from ..report import docx_blocks as blk

    doc = blk.new_document()
    blk.header(doc, ["BÁO CÁO NỘI BỘ", "Trích xuất bởi Trợ lý AI",
                     f"Ngày lập: {datetime.now():%d/%m/%Y}"])
    blk.title(doc, spec["title"])
    if spec.get("subtitle"):
        blk.subtitle(doc, spec["subtitle"])
    if spec.get("meta"):
        blk.meta_table(doc, spec["meta"])
    if spec.get("summary"):
        blk.tldr_box(doc, "TÓM TẮT NHANH", spec["summary"])
    for i, sec in enumerate(spec["sections"], start=1):
        blk.section_bar(doc, f"{i}. {sec['heading']}")
        for text in sec["paragraphs"]:
            blk.paragraph(doc, text)
        for text in sec["bullets"]:
            blk.bullet(doc, text)
        if sec["table"]:
            blk.data_table(doc, sec["table"]["columns"], sec["table"]["rows"])
    blk.note(doc, "Số liệu do Trợ lý AI tổng hợp từ dữ liệu hệ thống tại thời điểm lập — "
                  "đối chiếu lại trên màn hình báo cáo khi cần chốt số.")
    blk.footer(doc, "DEGO HOLDING · Tài liệu nội bộ",
               "Sinh tự động bởi Trợ lý AI — Công cụ thu mua")

    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _run(ctx: ToolContext, args: dict) -> dict:
    title = _clean(args.get("title"), 200)
    raw_sections = args.get("sections")
    if not title or not isinstance(raw_sections, list) or not raw_sections:
        return {"error": "Thiếu title hoặc sections — gom đủ nội dung rồi gọi lại."}

    sections = _clean_sections(raw_sections)
    if not sections:
        return {"error": "Không có mục nội dung hợp lệ nào (mỗi mục cần heading + nội dung)."}

    meta = []
    for m in (args.get("meta") or [])[:10]:
        if isinstance(m, dict) and _clean(m.get("label"), 100):
            meta.append((_clean(m.get("label"), 100), _clean(m.get("value"), 500)))

    spec = {
        "title": title,
        "subtitle": _clean(args.get("subtitle"), 300),
        "meta": meta,
        "summary": [_clean(s, 500) for s in (args.get("summary") or [])[:8] if _clean(s)],
        "sections": sections,
    }
    data = render_docx(spec)

    from app.core.storage import dated_key, safe_name, upload_fileobj
    from app.modules.attachment.model import StoredFile

    base = safe_name(_clean(args.get("filename"), 80) or "bao-cao-tro-ly-ai")
    filename = base if base.lower().endswith(".docx") else f"{base}.docx"
    #  Tạo bản ghi trước (flush lấy id) để đặt key theo cấu trúc chung của storage —
    #  giống hệt _store_one của module attachment.
    sf = StoredFile(filename=filename, file_key="", url="", content_type=DOCX_MIME,
                    size=len(data), created_by=ctx.user.id, updated_by=ctx.user.id)
    ctx.db.add(sf)
    ctx.db.flush()
    key = dated_key("assistant-report", filename, sf.id)
    upload_fileobj(BytesIO(data), key, DOCX_MIME)
    sf.file_key = key
    ctx.db.commit()

    return {
        "status": "created",
        "file": {
            "id": sf.id,
            "filename": filename,
            "size": len(data),
            "download_url": f"/api/assistant/files/{sf.id}/download",
        },
        "total": len(sections),
        # Nhắc model khỏi tự chế link markdown — nút tải do giao diện chat dựng.
        "reminder": "File đã sẵn sàng. Báo người dùng bấm nút 'Tải báo cáo' ngay dưới câu "
                    "trả lời để lưu về máy — ĐỪNG tự chèn đường link.",
    }


EXPORT_REPORT_FILE_SPEC = ToolSpec(
    name="export_report_file",
    description=_DESC,
    parameters=_PARAMS,
    handler=_run,
)
