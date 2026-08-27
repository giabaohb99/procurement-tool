"""Tool soạn nháp chứng từ: `draft_survey_request` (YCBG) + `draft_purchase_request` (YCMH)
— KHÔNG ghi DB.

Vì sao không tạo thẳng phiếu nháp: yêu cầu chốt là tránh đẻ nháp rác. Trợ lý chỉ gom thông
tin qua hội thoại rồi chuẩn hóa thành BẢN ĐỀ XUẤT; giao diện chat đọc args của tool call này
và hiện nút mở form tạo phiếu đã điền sẵn — người dùng rà lại, tự bấm Tạo thì phiếu mới
sinh ra. Tool giữ đúng tầng 4 bảo mật (read-only, không ghi gì).
"""
from sqlalchemy import or_

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
        "company": {
            "type": "string",
            "description": "Công ty/pháp nhân NHẬN HÓA ĐƠN — CHỈ điền khi người dùng nói mua "
                           "cho pháp nhân KHÁC công ty của họ; bỏ trống thì form tự lấy công "
                           "ty của người hỏi. Điền đúng tên trong danh mục hệ thống.",
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
                    "item_group": {
                        "type": "string",
                        "description": "Phân loại VTBB/NL — CHỈ điền khi chắc chắn đúng tên "
                                       "trong danh mục hệ thống; không chắc thì BỎ TRỐNG, "
                                       "đừng tự đặt tên mới (ô này là ô chọn, tên lạ sẽ bị bỏ).",
                    },
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
    "điền sẵn để người dùng rà lại và tự bấm Tạo. Vai trò của bạn: gom đủ thông tin qua hội "
    "thoại rồi đổ vào form hộ người dùng. Ba nhóm thông tin: "
    "(1) Form TỰ ĐIỀN theo hồ sơ người hỏi: người yêu cầu, chức vụ, phòng ban, công ty nhận "
    "hóa đơn — ĐỪNG hỏi lại nhóm này. "
    "(2) PHẢI CÓ trước khi gọi: mặt hàng cần khảo sát giá, SỐ LƯỢNG dự kiến (kèm đơn vị "
    "tính) và mục đích. "
    "(3) HỎI THÊM theo ngữ cảnh: thông số/chất lượng, yêu cầu khác (bảo hành, hãng...), và "
    "'có mua cho pháp nhân/công ty KHÁC công ty của bạn không?' — nếu có thì điền tham số "
    "company, không thì bỏ trống. "
    "Thiếu gì gom hỏi trong MỘT lượt rồi mới gọi. KHÔNG tự bịa giá trị người dùng chưa nói "
    "(số lượng, thông số, phân loại); họ nói chưa biết số lượng thì mới để 0. Đủ thông tin "
    "thì PHẢI gọi ngay trong lượt trả lời — nút 'Tạo yêu cầu báo giá' trên giao diện chỉ "
    "xuất hiện khi tool được gọi, trả lời suông thì người dùng không có nút nào để bấm. Sau "
    "khi gọi, báo người dùng bấm nút 'Tạo yêu cầu báo giá' ngay dưới câu trả lời để mở form "
    "— nhấn mạnh phiếu CHƯA được tạo."
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


def _apply_company(ctx: ToolContext, args: dict, result: dict) -> None:
    """Khớp tham số `company` (pháp nhân nhận hóa đơn) với danh mục công ty.

    Bỏ trống là bình thường — form tự lấy công ty của người hỏi. Model chỉ điền khi người
    dùng nói mua cho pháp nhân KHÁC, nên khớp được thì đè vào draft (company_id + tên);
    không khớp thì KHÔNG đè (form giữ mặc định) và trả danh sách hợp lệ để model nêu lại.
    """
    raw = _clean_text(args.get("company"), 255)
    if not raw:
        return
    from app.modules.company.model import Company

    rows = ctx.db.query(Company).filter(Company.is_active.is_(True)).all()
    q = raw.lower()
    hit = next((c for c in rows
                if q in {(c.name or "").strip().lower(), (c.short_name or "").strip().lower(),
                         (c.code or "").strip().lower()}), None)
    if hit:
        result["draft"]["company_id"] = hit.id
        result["draft"]["company_name"] = hit.name
        result["reminder"] += (f" Công ty nhận hóa đơn đã đặt theo yêu cầu: {hit.name} — "
                               "nhắc lại cho người dùng biết.")
    else:
        result["invalid_company"] = raw
        result["companies"] = sorted(c.name for c in rows if c.name)
        result["reminder"] += (" Tên công ty nhận hóa đơn KHÔNG khớp danh mục nên form vẫn "
                               "để công ty của người hỏi — nêu danh sách công ty hợp lệ "
                               "(companies) để người dùng chọn đúng pháp nhân.")


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
    dropped_groups = []   # phân loại model bịa ngoài danh mục — bỏ trống, kể lại cho model
    thieu_so_luong = False
    for raw in raw_lines[:MAX_LINES]:
        if not isinstance(raw, dict):
            continue
        detail = _clean_text(raw.get("requirement_detail"))
        if not detail:
            continue
        #  Ô Phân loại trên form là ô CHỌN đúng danh mục — khác ô ĐVT chữ tự do. Tên lạ
        #  đổ vào ô chọn là form lỗi (bắt được khi khách test 26/08), nên không khớp thì
        #  BỎ TRỐNG chứ không giữ nguyên như uom.
        raw_group = _clean_text(raw.get("item_group"), 100)
        group = groups.get(raw_group.lower(), "") if raw_group else ""
        if raw_group and not group:
            dropped_groups.append(raw_group)
        qty = _clean_number(raw.get("request_qty"))
        if qty <= 0:
            thieu_so_luong = True
        lines.append({
            "requirement_detail": detail,
            "item_group": group,
            "request_qty": qty,
            "uom": _match_catalog(_clean_text(raw.get("uom"), 50), units),
            "proposed_price": _clean_number(raw.get("proposed_price")),
            "other_requirement": _clean_text(raw.get("other_requirement")),
        })
    if not lines:
        return {"error": "Không có dòng hợp lệ nào (mỗi dòng cần requirement_detail)."}

    result = {
        "status": "ready",
        "draft": {"purpose": purpose, "note": _clean_text(args.get("note"), 500), "lines": lines},
        "total": len(lines),
        # Nhắc lại cho model khỏi "tự nhận đã tạo phiếu" — lỗi hay gặp ở model nhỏ.
        "reminder": "Phiếu CHƯA được tạo. Hãy tóm tắt bản đề xuất và mời người dùng bấm nút "
                    "'Tạo yêu cầu báo giá' dưới câu trả lời để mở form đã điền sẵn.",
    }
    if dropped_groups:
        result["invalid_item_groups"] = dropped_groups
        result["item_groups"] = sorted(groups.values())
        result["reminder"] += (" Phân loại bạn điền KHÔNG có trong danh mục nên đã bị bỏ trống "
                               "— nói rõ điều này và nêu danh sách phân loại hợp lệ "
                               "(item_groups) để người dùng chọn, hoặc chọn trên form.")
    if thieu_so_luong:
        result["reminder"] += (" Có dòng chưa có số lượng — nhắc người dùng bổ sung số lượng "
                               "trên form trước khi bấm Tạo.")
    _apply_company(ctx, args, result)
    return result


DRAFT_SURVEY_REQUEST_SPEC = ToolSpec(
    name="draft_survey_request",
    description=_DESC,
    parameters=_PARAMS,
    handler=_run,
)


# ── Soạn nháp Yêu cầu mua hàng (YCMH) ─────────────────────────────────────────────────────

_PR_PARAMS = {
    "type": "object",
    "properties": {
        "purpose": {
            "type": "string",
            "description": "Mục đích mua hàng — bắt buộc, nêu ngắn gọn.",
        },
        "note": {"type": "string", "description": "Ghi chú chung cho phiếu (nếu có)."},
        "need_date": {
            "type": "string",
            "description": "Ngày cần hàng của cả phiếu, định dạng YYYY-MM-DD (nếu người dùng nêu).",
        },
        "company": {
            "type": "string",
            "description": "Công ty/pháp nhân NHẬN HÓA ĐƠN — CHỈ điền khi người dùng nói mua "
                           "cho pháp nhân KHÁC công ty của họ; bỏ trống thì form tự lấy công "
                           "ty của người hỏi. Điền đúng tên trong danh mục hệ thống.",
        },
        "lines": {
            "type": "array",
            "description": f"Danh sách mặt hàng cần mua (tối đa {MAX_LINES} dòng).",
            "items": {
                "type": "object",
                "properties": {
                    "product": {
                        "type": "string",
                        "description": "Mã hàng HOẶC tên/mô tả mặt hàng — bắt buộc. Có mã thì "
                                       "điền mã, không thì mô tả để hệ thống tự tra danh mục.",
                    },
                    "qty": {"type": "number", "description": "Số lượng cần mua."},
                    "uom": {"type": "string", "description": "Đơn vị tính (cái, bộ, kg...)."},
                    "price": {
                        "type": "number",
                        "description": "Đơn giá dự kiến VNĐ (nếu người dùng có ước lượng).",
                    },
                    "required_date": {
                        "type": "string",
                        "description": "Ngày cần hàng riêng của dòng, YYYY-MM-DD (nếu có).",
                    },
                    "note": {"type": "string", "description": "Ghi chú của dòng (thông số, yêu cầu...)."},
                },
                "required": ["product"],
            },
        },
    },
    "required": ["purpose", "lines"],
}

_PR_DESC = (
    "SOẠN SẴN dữ liệu cho phiếu Yêu cầu mua hàng (YCMH) từ thông tin người dùng cung cấp. "
    "KHÔNG tạo phiếu — chỉ chuẩn bị bản đề xuất; giao diện sẽ hiện nút mở form tạo YCMH đã "
    "điền sẵn để người dùng rà lại và tự bấm Tạo. Gọi khi người dùng muốn được giúp lập "
    "phiếu yêu cầu MUA hàng (đề nghị mua, không phải xin báo giá). Ba nhóm thông tin: "
    "(1) Form TỰ ĐIỀN theo hồ sơ người hỏi: người yêu cầu, chức vụ, phòng ban, công ty nhận "
    "hóa đơn — ĐỪNG hỏi lại nhóm này. "
    "(2) PHẢI CÓ trước khi gọi: mặt hàng, SỐ LƯỢNG (kèm đơn vị tính nếu chưa rõ) và mục đích. "
    "(3) HỎI THÊM theo ngữ cảnh: ngày cần hàng, thông số/yêu cầu kỹ thuật, và 'có mua cho "
    "pháp nhân/công ty KHÁC công ty của bạn không?' — nếu có thì điền tham số company, "
    "không thì bỏ trống. "
    "Thiếu gì gom hỏi trong MỘT lượt rồi mới gọi. KHÔNG tự bịa giá trị người dùng chưa nói "
    "(số lượng, ngày cần hàng, thông số). Đủ thông tin thì PHẢI gọi ngay trong lượt trả lời "
    "— nút 'Tạo yêu cầu mua hàng' trên giao diện chỉ xuất hiện khi tool được gọi. Sau khi "
    "gọi, báo người dùng bấm nút đó để mở form — nhấn mạnh phiếu CHƯA được tạo; dòng nào "
    "chưa khớp được mã hàng trong danh mục thì nhắc họ chọn lại mã trên form."
)


def _match_product(db, query: str):
    """Khớp một dòng với danh mục sản phẩm: đúng mã trước, rồi mới tìm theo tên.

    Chỉ nhận khi tìm theo tên ra ĐÚNG MỘT kết quả — nhiều hơn thì trả danh sách gợi ý để
    model nói lại với người dùng, tự chọn bừa dòng đầu là điền sai mã vào phiếu thật.
    """
    from app.modules.product.model import Product

    exact = (db.query(Product)
             .filter(Product.code == query, Product.is_active.is_(True)).first())
    if exact:
        return exact, []
    like = f"%{query}%"
    rows = (db.query(Product)
            .filter(Product.is_active.is_(True))
            .filter(or_(Product.code.like(like), Product.name.like(like),
                        Product.hh_name.like(like)))
            .limit(6).all())
    if len(rows) == 1:
        return rows[0], []
    return None, [{"code": r.code, "name": r.name, "unit": r.unit} for r in rows[:5]]


def _run_purchase(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("purchase_request", "create"):
        return {"denied": True,
                "error": "Người dùng không có quyền tạo Yêu cầu mua hàng (purchase_request.create)."}

    purpose = _clean_text(args.get("purpose"), 500)
    raw_lines = args.get("lines")
    if not purpose or not isinstance(raw_lines, list) or not raw_lines:
        return {"error": "Thiếu purpose hoặc lines — hỏi người dùng bổ sung rồi gọi lại."}

    from app.modules.catalog.model import Unit

    units = _catalog_names(ctx.db, Unit)

    lines = []
    unmatched = []   # dòng chưa khớp mã + gợi ý — model dùng để nhắc người dùng
    for raw in raw_lines[:MAX_LINES]:
        if not isinstance(raw, dict):
            continue
        query = _clean_text(raw.get("product"), 255)
        if not query:
            continue
        product, suggestions = _match_product(ctx.db, query)
        line = {
            "product_code": product.code if product else "",
            "product_name": product.name if product else query,
            "item_group": product.item_group if product else "",
            "qty": _clean_number(raw.get("qty")),
            # ĐVT: danh mục sản phẩm là nguồn chuẩn; model chỉ điền khi chưa khớp được mã.
            "unit": (product.unit if product and product.unit
                     else _match_catalog(_clean_text(raw.get("uom"), 50), units)),
            "price": _clean_number(raw.get("price")),
            "required_date": _clean_text(raw.get("required_date"), 10),
            "note": _clean_text(raw.get("note"), 500),
        }
        lines.append(line)
        if not product:
            unmatched.append({"product": query, "suggestions": suggestions})
    if not lines:
        return {"error": "Không có dòng hợp lệ nào (mỗi dòng cần product)."}

    result = {
        "status": "ready",
        "draft": {
            "purpose": purpose,
            "note": _clean_text(args.get("note"), 500),
            "need_date": _clean_text(args.get("need_date"), 10),
            "lines": lines,
        },
        "total": len(lines),
        "reminder": "Phiếu CHƯA được tạo. Hãy tóm tắt bản đề xuất và mời người dùng bấm nút "
                    "'Tạo yêu cầu mua hàng' dưới câu trả lời để mở form đã điền sẵn.",
    }
    if unmatched:
        result["unmatched"] = unmatched
        result["reminder"] += (" Có dòng chưa khớp được mã hàng trong danh mục — liệt kê gợi ý "
                               "(nếu có) và nhắc người dùng chọn lại mã trên form.")
    if any(line["qty"] <= 0 for line in lines):
        result["reminder"] += (" Có dòng chưa có số lượng — nhắc người dùng bổ sung số lượng "
                               "trên form trước khi bấm Tạo.")
    _apply_company(ctx, args, result)
    return result


DRAFT_PURCHASE_REQUEST_SPEC = ToolSpec(
    name="draft_purchase_request",
    description=_PR_DESC,
    parameters=_PR_PARAMS,
    handler=_run_purchase,
)


# ── Soạn nháp Giấy nghỉ phép (văn bản loại GNP) ──────────────────────────────────────────

_LEAVE_PARAMS = {
    "type": "object",
    "properties": {
        "from_date": {
            "type": "string",
            "description": "Ngày bắt đầu nghỉ, YYYY-MM-DD — bắt buộc. Người dùng nói ngày "
                           "tương đối (mai, thứ hai tuần sau...) thì tự quy ra theo ngày hôm nay.",
        },
        "to_date": {
            "type": "string",
            "description": "Ngày kết thúc nghỉ, YYYY-MM-DD — bắt buộc. Nghỉ một ngày thì "
                           "bằng from_date.",
        },
        "reason": {"type": "string", "description": "Lý do nghỉ — bắt buộc, nêu ngắn gọn."},
        "leave_type": {
            "type": "string",
            "description": "Loại nghỉ: annual (phép năm) | unpaid (không lương) | sick (ốm đau) "
                           "| maternity (thai sản) | wedding (cưới hỏi) | funeral (tang chế) "
                           "| comp_off (nghỉ bù). Không rõ thì bỏ trống (mặc định annual).",
        },
        "from_session": {
            "type": "string",
            "description": "Buổi bắt đầu: full (cả ngày) | morning (sáng) | afternoon (chiều). "
                           "Mặc định full.",
        },
        "to_session": {
            "type": "string",
            "description": "Buổi kết thúc: full | morning | afternoon. Mặc định full.",
        },
        "contact_phone": {"type": "string", "description": "SĐT liên hệ khi nghỉ (nếu có)."},
    },
    "required": ["from_date", "to_date", "reason"],
}

_LEAVE_DESC = (
    "SOẠN SẴN dữ liệu cho ĐƠN NGHỈ PHÉP (văn bản loại Giấy nghỉ phép) của CHÍNH người hỏi. "
    "KHÔNG tạo văn bản — chỉ chuẩn bị bản đề xuất; giao diện sẽ hiện nút mở form tạo văn bản "
    "đã điền sẵn để người dùng rà lại và tự bấm Tạo. Form TỰ điền người làm đơn và phòng ban "
    "theo hồ sơ người hỏi — ĐỪNG hỏi lại. Gọi khi người dùng muốn xin nghỉ phép / "
    "lập đơn nghỉ phép và đã cho biết tối thiểu: NGÀY nghỉ (từ ngày - đến ngày) và LÝ DO. "
    "Thiếu thì hỏi lại cho đủ rồi mới gọi; nghỉ nửa ngày thì hỏi buổi nào. Đủ thông tin thì "
    "PHẢI gọi ngay trong lượt trả lời — nút 'Tạo đơn nghỉ phép' chỉ xuất hiện khi tool được "
    "gọi. Sau khi gọi, báo người dùng bấm nút đó để mở form — nhấn mạnh đơn CHƯA được tạo và "
    "tổng số ngày chỉ là GỢI Ý (đếm cả cuối tuần), sửa được trên form."
)


def _ngay_iso(value) -> str | None:
    """`YYYY-MM-DD` hợp lệ thì trả lại đúng chuỗi đó, sai thì `None` (model điền nên phải đỡ)."""
    from datetime import date

    try:
        return date.fromisoformat(str(value or "").strip()[:10]).isoformat()
    except ValueError:
        return None


def _run_leave(ctx: ToolContext, args: dict) -> dict:
    #  Đơn nghỉ phép là văn bản nội bộ — cần quyền tạo văn bản, giống lập tay trên màn Văn thư.
    if not ctx.can("document", "create"):
        return {"denied": True,
                "error": "Người dùng không có quyền tạo văn bản (document.create)."}

    from app.core.leave_codes import LEAVE_SESSION_SET, LEAVE_TYPE_SET
    from app.modules.doc_catalog.model import DocType
    from app.modules.document.type_metadata import (BUOI_CA_NGAY, BUOI_CHIEU,
                                                    BUOI_SANG, LOAI_NGHI_PHEP,
                                                    NGHI_PHEP_NAM, so_ngay_goi_y)
    from app.modules.employee.model import Employee

    #  Form tạo văn bản cần `doc_type_id` thật của môi trường đang chạy — tra sống, không
    #  đóng cứng id.
    gnp = (ctx.db.query(DocType)
           .filter(DocType.code == LOAI_NGHI_PHEP, DocType.is_active.is_(True)).first())
    if gnp is None:
        return {"error": "Danh mục chưa khai loại văn bản Giấy nghỉ phép (mã GNP) hoặc loại "
                         "này đang tắt — báo người dùng liên hệ quản trị Văn thư."}

    tu_ngay = _ngay_iso(args.get("from_date"))
    den_ngay = _ngay_iso(args.get("to_date"))
    ly_do = _clean_text(args.get("reason"), 500)
    if not tu_ngay or not den_ngay or not ly_do:
        return {"error": "Thiếu hoặc sai from_date / to_date (cần YYYY-MM-DD) hoặc reason — "
                         "hỏi người dùng bổ sung rồi gọi lại."}
    if den_ngay < tu_ngay:
        return {"error": "«Đến ngày» đang trước «Từ ngày» — xác nhận lại ngày nghỉ với "
                         "người dùng rồi gọi lại."}

    #  Giá trị ngoài bộ mã thì về mặc định thay vì nổ lỗi: các ô này trên form là ô chọn,
    #  người dùng rà lại được; chặn cứng chỉ vì model gõ "morning " thừa dấu cách là quá tay.
    def _trong_bo(value, bo, mac_dinh: str) -> str:
        ma = _clean_text(value, 20)
        return ma if ma in bo.values else mac_dinh

    buoi_di = _trong_bo(args.get("from_session"), LEAVE_SESSION_SET, BUOI_CA_NGAY)
    buoi_ve = _trong_bo(args.get("to_session"), LEAVE_SESSION_SET, BUOI_CA_NGAY)
    if tu_ngay == den_ngay and buoi_di == BUOI_CHIEU and buoi_ve == BUOI_SANG:
        return {"error": "Nghỉ từ buổi chiều đến buổi sáng CÙNG một ngày là khoảng trống — "
                         "hỏi lại người dùng buổi nghỉ."}
    loai_nghi = _trong_bo(args.get("leave_type"), LEAVE_TYPE_SET, NGHI_PHEP_NAM)

    #  Cùng công thức gợi ý số ngày với form (đếm cả cuối tuần — người duyệt là chốt cuối).
    so_ngay = so_ngay_goi_y(tu_ngay, den_ngay, buoi_di, buoi_ve)

    emp = (ctx.db.get(Employee, ctx.user.employee_id)
           if getattr(ctx.user, "employee_id", None) else None)
    ten = emp.full_name if emp else ""
    d1, d2 = tu_ngay[8:10] + "/" + tu_ngay[5:7], den_ngay[8:10] + "/" + den_ngay[5:7]
    khoang = d1 if tu_ngay == den_ngay else f"{d1} - {d2}"
    #  Tài khoản chưa gắn nhân sự thì tiêu đề bỏ tên — backend vẫn tự điền người nghỉ
    #  theo người tạo lúc lưu, không chặn ở đây.
    title = " ".join(p for p in ("Giấy nghỉ phép", ten) if p) + f" ({khoang}/{den_ngay[:4]})"

    return {
        "status": "ready",
        "total": 1,
        "draft": {
            #  `kind` để giao diện chat phân biệt bản nháp văn bản với bản nháp YCBG/YCMH.
            "kind": "leave_request",
            "doc_type_id": gnp.id,
            "doc_type_code": gnp.code,
            "title": title,
            "leave": {
                "leave_type": loai_nghi,
                "from_date": tu_ngay,
                "from_session": buoi_di,
                "to_date": den_ngay,
                "to_session": buoi_ve,
                "total_days": so_ngay,
                "reason": ly_do,
                "contact_phone": _clean_text(args.get("contact_phone"), 30),
            },
        },
        "leave_type_label": LEAVE_TYPE_SET.labels.get(loai_nghi, loai_nghi),
        "note": f"Tổng số ngày {so_ngay} chỉ là GỢI Ý — đếm cả thứ Bảy/Chủ nhật vì hệ chưa "
                "có lịch làm việc; người dùng sửa được trên form và người duyệt là chốt cuối.",
        "reminder": "Đơn CHƯA được tạo. Hãy tóm tắt bản đề xuất (ngày nghỉ, loại nghỉ, số "
                    "ngày gợi ý, lý do) và mời người dùng bấm nút 'Tạo đơn nghỉ phép' dưới "
                    "câu trả lời để mở form đã điền sẵn — họ rà lại rồi tự bấm Tạo.",
    }


DRAFT_LEAVE_REQUEST_SPEC = ToolSpec(
    name="draft_leave_request",
    description=_LEAVE_DESC,
    parameters=_LEAVE_PARAMS,
    handler=_run_leave,
)


# ── Gắn danh mục thật vào khai báo tool ──────────────────────────────────────────────────

_DRAFT_TOOL_NAMES = ("draft_survey_request", "draft_purchase_request")


def inject_catalog_enums(defs, db) -> None:
    """Gắn `enum` danh mục THẬT của môi trường đang chạy vào khai báo 2 tool soạn nháp:
    Phân loại VTBB/NL (`item_group` — chỉ YCBG) và pháp nhân nhận hóa đơn (`company`).

    Model thấy trước danh sách hợp lệ ngay trong schema nên hết bịa tên ngoài danh mục
    ("Thiết bị văn phòng / IT" — lỗi khách bắt được 26/08/2026) thay vì phải gọi sai rồi
    được tool sửa lưng. Phải deepcopy vì các def dùng CHUNG dict `_PARAMS` module-level —
    ghi thẳng enum vào đó là dính sang mọi request sau.
    """
    from copy import deepcopy

    from app.modules.catalog.model import ItemGroup
    from app.modules.company.model import Company

    try:
        groups = sorted({n for (n,) in db.query(ItemGroup.name)
                         .filter(ItemGroup.is_active.is_(True)).all() if n})
        companies = sorted({n for (n,) in db.query(Company.name)
                            .filter(Company.is_active.is_(True)).all() if n})
    except Exception:  # noqa: BLE001 - danh mục lỗi thì giữ khai báo tĩnh, không sập lượt chat
        return
    if not groups and not companies:
        return

    for d in defs:
        if d.name not in _DRAFT_TOOL_NAMES:
            continue
        params = deepcopy(d.parameters)
        if groups:
            item_group = (params.get("properties", {}).get("lines", {})
                          .get("items", {}).get("properties", {}).get("item_group"))
            if item_group is not None:
                item_group["enum"] = groups
        if companies:
            company = params.get("properties", {}).get("company")
            if company is not None:
                company["enum"] = companies
        d.parameters = params
