"""Tool `draft_survey_request`: SOẠN SẴN dữ liệu phiếu Yêu cầu báo giá (YCBG) — KHÔNG ghi DB.

Vì sao không tạo thẳng phiếu nháp: yêu cầu chốt là tránh đẻ nháp rác. Trợ lý chỉ gom thông
tin qua hội thoại rồi chuẩn hóa thành BẢN ĐỀ XUẤT; giao diện chat đọc args của tool call này
và hiện nút "Mở form tạo YCBG" đã điền sẵn — người dùng rà lại, tự bấm Tạo thì phiếu mới
sinh ra. Tool giữ đúng tầng 4 bảo mật (read-only, không ghi gì).
"""
from .base import ToolContext, ToolSpec

MAX_LINES = 20          # phiếu do trợ lý soạn không cần dài hơn — dài hơn thì tự lập tay
MAX_TEXT = 2000         # chặn model nhồi cả bài văn vào một ô

_PARAMS = {
    "type": "object",
    "properties": {
        "purpose": {
            "type": "string",
            "description": "Mục đích khảo sát / lý do cần mua — bắt buộc, nêu ngắn gọn.",
        },
        "note": {
            "type": "string",
            "description": "Ghi chú chung cho phiếu (nếu có).",
        },
        "lines": {
            "type": "array",
            "description": f"Danh sách mặt hàng cần khảo sát giá (tối đa {MAX_LINES} dòng).",
            "items": {
                "type": "object",
                "properties": {
                    "requirement_detail": {
                        "type": "string",
                        "description": "Tên hàng + thông số kỹ thuật & chất lượng — bắt buộc.",
                    },
                    "item_group": {"type": "string", "description": "Phân loại VTBB/NL (nếu biết)."},
                    "request_qty": {"type": "number", "description": "Số lượng dự kiến mua."},
                    "uom": {"type": "string", "description": "Đơn vị tính (cái, bộ, kg...)."},
                    "proposed_price": {
                        "type": "number",
                        "description": "Giá đề xuất VNĐ (nếu người dùng có ước lượng).",
                    },
                    "other_requirement": {
                        "type": "string",
                        "description": "Yêu cầu khác: bảo hành, hãng, thời hạn giao...",
                    },
                },
                "required": ["requirement_detail"],
            },
        },
    },
    "required": ["purpose", "lines"],
}

_DESC = (
    "SOẠN SẴN dữ liệu cho phiếu Yêu cầu báo giá (YCBG) từ thông tin người dùng cung cấp. "
    "KHÔNG tạo phiếu — chỉ chuẩn bị bản đề xuất; giao diện sẽ hiện nút mở form tạo YCBG đã "
    "điền sẵn để người dùng rà lại và tự bấm Tạo. Gọi khi người dùng muốn được giúp lập phiếu "
    "yêu cầu báo giá / xin báo giá một mặt hàng và đã cho biết tối thiểu: mặt hàng cần mua và "
    "mục đích. Thiếu thì hỏi lại cho đủ rồi mới gọi. Sau khi gọi, báo người dùng bấm nút "
    "'Tạo yêu cầu báo giá' ngay dưới câu trả lời để mở form — nhấn mạnh phiếu CHƯA được tạo."
)


def _clean_text(value, limit: int = MAX_TEXT) -> str:
    return str(value or "").strip()[:limit]


def _clean_number(value) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return 0.0
    return n if n >= 0 else 0.0


def _catalog_names(db, model) -> dict[str, str]:
    """Map tên viết thường -> tên đúng trong danh mục (chỉ mục đang hoạt động)."""
    rows = db.query(model.name).filter(model.is_active.is_(True)).all()
    return {name.strip().lower(): name for (name,) in rows if name}


def _match_catalog(value: str, catalog: dict[str, str]) -> str:
    """Khớp không phân biệt hoa thường với danh mục.

    Model hay điền "cái" trong khi danh mục là "Cái" — ô chọn trên form khớp đúng chuỗi
    nên hiện trống dù dữ liệu có. Khớp được thì trả về đúng chính tả danh mục; không khớp
    thì giữ nguyên (uom là chữ tự do trong DB, người dùng tự sửa trên form).
    """
    return catalog.get(value.strip().lower(), value) if value else value


def _run(ctx: ToolContext, args: dict) -> dict:
    # Người không có quyền tạo YCBG thì đừng soạn hộ — model sẽ báo lại đúng lý do.
    if not ctx.can("survey_request", "create"):
        return {"denied": True,
                "error": "Người dùng không có quyền tạo Yêu cầu báo giá (survey_request.create)."}

    purpose = _clean_text(args.get("purpose"), 500)
    raw_lines = args.get("lines")
    if not purpose or not isinstance(raw_lines, list) or not raw_lines:
        return {"error": "Thiếu purpose hoặc lines — hỏi người dùng bổ sung rồi gọi lại."}

    # Ô ĐVT / Phân loại trên form là ô CHỌN theo danh mục — chuẩn hóa chính tả cho khớp.
    from app.modules.catalog.model import ItemGroup, Unit

    units = _catalog_names(ctx.db, Unit)
    groups = _catalog_names(ctx.db, ItemGroup)

    lines = []
    for raw in raw_lines[:MAX_LINES]:
        if not isinstance(raw, dict):
            continue
        detail = _clean_text(raw.get("requirement_detail"))
        if not detail:
            continue
        lines.append({
            "requirement_detail": detail,
            "item_group": _match_catalog(_clean_text(raw.get("item_group"), 100), groups),
            "request_qty": _clean_number(raw.get("request_qty")),
            "uom": _match_catalog(_clean_text(raw.get("uom"), 50), units),
            "proposed_price": _clean_number(raw.get("proposed_price")),
            "other_requirement": _clean_text(raw.get("other_requirement")),
        })
    if not lines:
        return {"error": "Không có dòng hợp lệ nào (mỗi dòng cần requirement_detail)."}

    return {
        "status": "ready",
        "draft": {"purpose": purpose, "note": _clean_text(args.get("note"), 500), "lines": lines},
        "total": len(lines),
        # Nhắc lại cho model khỏi "tự nhận đã tạo phiếu" — lỗi hay gặp ở model nhỏ.
        "reminder": "Phiếu CHƯA được tạo. Hãy tóm tắt bản đề xuất và mời người dùng bấm nút "
                    "'Tạo yêu cầu báo giá' dưới câu trả lời để mở form đã điền sẵn.",
    }


DRAFT_SURVEY_REQUEST_SPEC = ToolSpec(
    name="draft_survey_request",
    description=_DESC,
    parameters=_PARAMS,
    handler=_run,
)
