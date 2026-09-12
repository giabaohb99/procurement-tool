"""Tool soạn nháp chứng từ: `draft_survey_request` (YCBG) + `draft_purchase_request` (YCMH)
— KHÔNG ghi DB.

Vì sao không tạo thẳng phiếu nháp: yêu cầu chốt là tránh đẻ nháp rác. Trợ lý chỉ gom thông
tin qua hội thoại rồi chuẩn hóa thành BẢN ĐỀ XUẤT; giao diện chat đọc args của tool call này
và hiện nút mở form tạo phiếu đã điền sẵn — người dùng rà lại, tự bấm Tạo thì phiếu mới
sinh ra. Tool giữ đúng tầng 4 bảo mật (read-only, không ghi gì).
"""
from datetime import date

from sqlalchemy import or_

#  Bộ mã buổi nghỉ nhập thẳng ở đầu tệp vì `_SESSION_BY_NAME` dựng lúc nạp module.
#  `leave/constants.py` chỉ phụ thuộc `datetime` nên không sinh vòng nhập.
from app.modules.leave.constants import (SESSION_AFTERNOON as LEAVE_SESSION_AFTERNOON,
                                         SESSION_FULL as LEAVE_SESSION_FULL,
                                         SESSION_HOURLY as LEAVE_SESSION_HOURLY,
                                         SESSION_MORNING as LEAVE_SESSION_MORNING)

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
                    "result_due_date": {
                        "type": "string",
                        "description": "Ngày cần có kết quả khảo sát của dòng, YYYY-MM-DD "
                                       "(nếu người dùng nêu).",
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
    "(3) HỎI THÊM theo ngữ cảnh: NGÀY CẦN KẾT QUẢ khảo sát (result_due_date), thông số/"
    "chất lượng, yêu cầu khác (bảo hành, hãng...), và 'có mua cho pháp nhân/công ty KHÁC "
    "công ty của bạn không?' — nếu có thì điền tham số company, không thì bỏ trống. "
    "Nhóm (3) chưa được nhắc tới thì gom hỏi CÙNG LƯỢT với nhóm (2) còn thiếu — hỏi đúng "
    "MỘT lượt duy nhất; người dùng trả lời 'chưa cần/không có' thì bỏ trống và gọi tool "
    "luôn, CẤM hỏi lại điều họ đã trả lời. "
    "KHÔNG tự bịa giá trị người dùng chưa nói "
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
    missing_quantity = False
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
            missing_quantity = True
        lines.append({
            "requirement_detail": detail,
            "item_group": group,
            "request_qty": qty,
            "uom": _match_catalog(_clean_text(raw.get("uom"), 50), units),
            "proposed_price": _clean_number(raw.get("proposed_price")),
            "other_requirement": _clean_text(raw.get("other_requirement")),
            # Ngày sai định dạng thì bỏ trống chứ không nổ lỗi — người dùng sửa trên form.
            "result_due_date": _iso_date(raw.get("result_due_date")) or "",
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
    if missing_quantity:
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
                    "warehouse": {
                        "type": "string",
                        "description": "Kho nhận hàng của dòng (tên kho, chữ tự do — nếu "
                                       "người dùng nêu).",
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
    "(3) HỎI THÊM theo ngữ cảnh: NGÀY CẦN HÀNG (need_date), KHO NHẬN hàng (warehouse từng "
    "dòng), thông số/yêu cầu kỹ thuật, và 'có mua cho pháp nhân/công ty KHÁC công ty của "
    "bạn không?' — nếu có thì điền tham số company, không thì bỏ trống. "
    "Nhóm (3) chưa được nhắc tới thì gom hỏi CÙNG LƯỢT với nhóm (2) còn thiếu — hỏi đúng "
    "MỘT lượt duy nhất; người dùng trả lời 'chưa cần/không có' thì bỏ trống và gọi tool "
    "luôn, CẤM hỏi lại điều họ đã trả lời. "
    "KHÔNG tự bịa giá trị người dùng chưa nói "
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
            "warehouse": _clean_text(raw.get("warehouse"), 255),
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


# ── Soạn nháp ĐƠN NGHỈ PHÉP (phân hệ Nghỉ phép, không phải Văn thư) ──────────────────────
#
#  ⚠️ **Tool này từng trỏ NHẦM MODULE** (sửa 12/09/2026, bao-CR-387). Bản đầu (CR-159) dựng
#  lúc hệ chưa có phân hệ Nghỉ phép, nên nó soạn một *Giấy nghỉ phép* ở **Văn thư**: gác bằng
#  `document.create`, tra `DocType` mã `GNP`, và nút chat mở form tạo văn bản. Từ CR-259
#  (03/09/2026) giấy GNP **do hệ tự sinh** sau khi đơn được duyệt (`leave/approval_bridge.py`,
#  QĐ-NP5), nên đường cũ dẫn người dùng đi tạo tay đúng thứ gói tri thức `40-nghi-phep.md`
#  cấm: *"tạo tay là ra một tờ giấy không gắn với quỹ phép nào"* — không giữ chỗ `pending_days`,
#  không trừ quỹ, không vào luồng duyệt của Nghỉ phép.
#
#  Nay tool soạn thẳng **đơn nghỉ phép** ở `/hr/leave-requests/new`. Vẫn KHÔNG ghi DB: chỉ
#  chuẩn hóa dữ liệu, người dùng tự bấm Lưu trên form (tầng 4 của `base.py`).

#  Mã buổi nghỉ do model gõ (chuỗi dễ đọc) -> SMALLINT của `leave/constants.py`. Model không
#  bao giờ được gõ số ở đây: bộ số là chuyện nội bộ của DB, đổi chỗ là model gõ sai im lặng.
_SESSION_BY_NAME = {
    "full": LEAVE_SESSION_FULL,
    "morning": LEAVE_SESSION_MORNING,
    "afternoon": LEAVE_SESSION_AFTERNOON,
    "hourly": LEAVE_SESSION_HOURLY,
}

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
            "description": "MÃ loại nghỉ trong danh mục của công ty (annual = phép năm, "
                           "unpaid = không lương, sick = ốm đau...). Không rõ thì bỏ trống — "
                           "tool tự lấy phép năm. Đừng bịa mã ngoài danh mục.",
        },
        "from_session": {
            "type": "string",
            "enum": list(_SESSION_BY_NAME),
            "description": "Buổi BẮT ĐẦU nghỉ: full (cả ngày) | morning (sáng) | "
                           "afternoon (chiều) | hourly (theo giờ). Mặc định full.",
        },
        "to_session": {
            "type": "string",
            "enum": list(_SESSION_BY_NAME),
            "description": "Buổi KẾT THÚC nghỉ: full | morning | afternoon | hourly. "
                           "Mặc định full. Nghỉ theo giờ thì CẢ HAI ô đều phải là hourly.",
        },
        "from_time": {
            "type": "string",
            "description": "Giờ bắt đầu HH:MM — chỉ khi nghỉ theo giờ (hourly).",
        },
        "to_time": {
            "type": "string",
            "description": "Giờ kết thúc HH:MM — chỉ khi nghỉ theo giờ (hourly).",
        },
        "days": {
            "type": "number",
            "description": "Số ngày phép xin nghỉ, CHỈ điền khi người dùng nói rõ một con số "
                           "khác với khoảng ngày (ví dụ nghỉ 5 ngày nhưng chỉ xin trừ 3 ngày "
                           "phép). Bỏ trống thì tool tự tính theo lịch làm việc và ngày lễ.",
        },
        "contact_phone": {"type": "string", "description": "SĐT liên hệ khi nghỉ (nếu có)."},
    },
    "required": ["from_date", "to_date", "reason"],
}

_LEAVE_DESC = (
    "SOẠN SẴN dữ liệu cho ĐƠN NGHỈ PHÉP của CHÍNH người hỏi, ở phân hệ Nhân sự ▸ Nghỉ phép. "
    "KHÔNG tạo đơn — chỉ chuẩn bị bản đề xuất; giao diện sẽ hiện nút mở form đơn nghỉ phép đã "
    "điền sẵn để người dùng rà lại và tự bấm Lưu. Form TỰ điền người nghỉ theo hồ sơ người "
    "hỏi — ĐỪNG hỏi lại. Gọi khi người dùng muốn xin nghỉ / lập đơn nghỉ phép và đã cho biết "
    "tối thiểu: NGÀY nghỉ (từ ngày - đến ngày) và LÝ DO; thiếu thì hỏi cho đủ rồi mới gọi, "
    "nghỉ nửa ngày thì hỏi buổi nào. Đủ thông tin thì PHẢI gọi ngay trong lượt trả lời — nút "
    "'Tạo đơn nghỉ phép' chỉ xuất hiện khi tool được gọi. Sau khi gọi: tóm tắt bản đề xuất, "
    "nói rõ đơn CHƯA được tạo và CHƯA gửi duyệt, và đọc nguyên các cảnh báo trong `warnings` "
    "nếu có (trùng đơn cũ, không đủ quỹ phép). ĐỪNG dùng tool này để tạo văn bản «Giấy nghỉ "
    "phép» ở Văn thư: giấy đó hệ TỰ SINH sau khi đơn được duyệt."
)


def _iso_date(value) -> str | None:
    """`YYYY-MM-DD` hợp lệ thì trả lại đúng chuỗi đó, sai thì `None` (model điền nên phải đỡ)."""
    from datetime import date

    try:
        return date.fromisoformat(str(value or "").strip()[:10]).isoformat()
    except ValueError:
        return None


def _hhmm(value) -> str:
    """`HH:MM` hợp lệ thì trả lại, sai thì chuỗi rỗng — giống `_iso_date`, model gõ nên phải đỡ."""
    from datetime import time

    raw = _clean_text(value, 8)
    try:
        parts = [int(p) for p in raw.split(":")[:2]]
        return time(*parts).strftime("%H:%M")
    except (TypeError, ValueError):
        return ""


def _pick_leave_type(db, wanted: str):
    """Loại nghỉ đang BẬT khớp `wanted` (khớp mã trước, rồi tới tên), mặc định phép năm.

    Danh mục loại nghỉ là DỮ LIỆU, không phải hằng số (`catalog_model.LeaveType`) — mỗi
    công ty một bộ. Nên không đóng cứng bộ 7 mã như `core/leave_codes.py`: tra sống rồi
    lùi về loại trừ quỹ phép năm, và trả cả danh sách để tool nói được "không có loại đó".
    """
    from app.modules.leave.catalog_model import LeaveType

    rows = (db.query(LeaveType).filter(LeaveType.is_active.is_(True))
            .order_by(LeaveType.sort_order, LeaveType.id).all())
    if not rows:
        return None, []
    key = (wanted or "").strip().lower()
    if key:
        for r in rows:
            if (r.code or "").lower() == key:
                return r, rows
        for r in rows:
            if (r.name or "").lower() == key:
                return r, rows
    #  Không nêu loại (hoặc nêu loại lạ) thì lấy loại trừ vào quỹ phép năm — đúng thứ 9/10
    #  tờ đơn dùng. Không có loại nào như vậy thì lấy dòng đầu danh mục.
    return next((r for r in rows if r.counts_balance), rows[0]), rows


def _run_leave(ctx: ToolContext, args: dict) -> dict:
    #  Gác bằng khóa của CHÍNH phân hệ Nghỉ phép. Bản cũ gác `document.create` vì nó soạn
    #  văn bản GNP — giữ lại thì người có quyền văn thư mà không được nộp đơn vẫn soạn được
    #  một tờ đơn họ không lưu nổi, còn người chỉ có `leave_request.create` thì bị chặn oan.
    if not ctx.can("leave_request", "create"):
        return {"denied": True,
                "error": "Người dùng không có quyền lập đơn nghỉ phép (leave_request.create)."}

    from app.modules.leave import balance_service, workday_service
    from app.modules.leave.constants import HOLDING_STATUSES, LEAVE_SESSION_LABELS
    from app.modules.leave.request_model import LeaveRequest
    from app.modules.employee.model import Employee

    emp_id = int(getattr(ctx.user, "employee_id", 0) or 0)
    if not emp_id:
        return {"error": "Tài khoản của người hỏi chưa gắn hồ sơ nhân sự nên chưa nộp đơn "
                         "nghỉ phép được — báo họ liên hệ phòng Nhân sự."}
    emp = ctx.db.get(Employee, emp_id)

    from_date = _iso_date(args.get("from_date"))
    to_date = _iso_date(args.get("to_date"))
    reason = _clean_text(args.get("reason"), 500)
    if not from_date or not to_date or not reason:
        return {"error": "Thiếu hoặc sai from_date / to_date (cần YYYY-MM-DD) hoặc reason — "
                         "hỏi người dùng bổ sung rồi gọi lại."}
    if to_date < from_date:
        return {"error": "«Đến ngày» đang trước «Từ ngày» — xác nhận lại ngày nghỉ với "
                         "người dùng rồi gọi lại."}

    #  Giá trị ngoài bộ mã thì về mặc định thay vì nổ lỗi: các ô này trên form là ô chọn,
    #  người dùng rà lại được; chặn cứng chỉ vì model gõ "morning " thừa dấu cách là quá tay.
    def _session(value) -> int:
        return _SESSION_BY_NAME.get(_clean_text(value, 20).lower(), LEAVE_SESSION_FULL)

    from_session, to_session = _session(args.get("from_session")), _session(args.get("to_session"))
    if (from_date == to_date and from_session == LEAVE_SESSION_AFTERNOON
            and to_session == LEAVE_SESSION_MORNING):
        #  Cùng câu chặn với `request_service.check_date_range` — một luật, một câu báo.
        return {"error": "Nghỉ từ buổi chiều đến buổi sáng CÙNG một ngày là khoảng trống — "
                         "hỏi lại người dùng buổi nghỉ."}

    hourly = LEAVE_SESSION_HOURLY in (from_session, to_session)
    from_time = _hhmm(args.get("from_time")) if hourly else ""
    to_time = _hhmm(args.get("to_time")) if hourly else ""
    if hourly and not (from_time and to_time):
        return {"error": "Nghỉ theo giờ phải có đủ from_time và to_time dạng HH:MM — hỏi "
                         "người dùng khung giờ rồi gọi lại."}
    if hourly:
        #  Khai theo giờ thì CẢ HAI ô buổi phải là «Theo giờ», nếu không backend chặn lúc lưu.
        from_session = to_session = LEAVE_SESSION_HOURLY

    leave_type, catalog = _pick_leave_type(ctx.db, _clean_text(args.get("leave_type"), 50))
    if leave_type is None:
        return {"error": "Danh mục Loại nghỉ đang trống hoặc tắt hết — báo người dùng liên hệ "
                         "phòng Nhân sự khai danh mục trước khi nộp đơn."}

    company_id = int(getattr(emp, "company_id", 0) or 0)
    span_days = (date.fromisoformat(to_date) - date.fromisoformat(from_date)).days + 1
    if span_days > workday_service.MAX_RANGE_DAYS:
        return {"error": f"Khoảng nghỉ dài {span_days} ngày, vượt trần "
                         f"{workday_service.MAX_RANGE_DAYS} ngày của một tờ đơn — nhiều khả "
                         "năng gõ nhầm năm, xác nhận lại với người dùng."}

    #  Số ngày GỢI Ý tính đúng như form: qua `workday_service`, tức đã trừ Chủ nhật và ngày
    #  lễ của pháp nhân. Đây là NƠI DUY NHẤT của công thức — bản cũ gọi `suggested_days()`
    #  của giấy GNP (đếm cả cuối tuần) nên cùng một tờ đơn ra hai con số khác nhau.
    kwargs = {"company_id": company_id, "exclude_holiday": bool(leave_type.exclude_holiday)}
    if hourly:
        from datetime import time as _time

        days = workday_service.count_hourly_days(
            ctx.db, date.fromisoformat(from_date), date.fromisoformat(to_date),
            _time.fromisoformat(from_time), _time.fromisoformat(to_time), **kwargs)
    else:
        days = workday_service.count_leave_days(
            ctx.db, date.fromisoformat(from_date), date.fromisoformat(to_date),
            from_session, to_session, **kwargs)
    try:
        asked = float(args.get("days"))
        days = asked if 0 < asked <= span_days else days
    except (TypeError, ValueError):
        pass

    warnings = []
    #  Hai chốt backend sẽ CHẶN lúc lưu. Nói trước ở đây để người dùng khỏi điền xong form
    #  mới ăn câu chặn — nhưng chỉ CẢNH BÁO, không tự sửa: quyết định là của họ.
    cap = float(leave_type.max_days_per_request or 0.0)   # 0 = không giới hạn
    if cap and days > cap:
        warnings.append(f"«{leave_type.name}» chỉ cho nghỉ tối đa {cap} ngày mỗi lần, "
                        f"đơn này đang {days} ngày.")
    other = (ctx.db.query(LeaveRequest)
             .filter(LeaveRequest.employee_id == emp_id,
                     LeaveRequest.is_deleted.is_(False),
                     LeaveRequest.status.in_(HOLDING_STATUSES),
                     LeaveRequest.from_date <= date.fromisoformat(to_date),
                     date.fromisoformat(from_date) <= LeaveRequest.to_date)
             .first())
    if other is not None:
        warnings.append(f"Đã có đơn «{other.code}» nghỉ từ {other.from_date} đến "
                        f"{other.to_date} trùng khoảng ngày này — hệ sẽ chặn lúc lưu.")
    remaining = None
    if leave_type.counts_balance:
        #  `remaining()` chỉ ĐỌC (`ensure_balance` mới là hàm cấp phát) — tool read-only
        #  không được gọi nhầm sang hàm kia.
        remaining = balance_service.remaining(
            ctx.db, emp_id, date.fromisoformat(from_date).year, leave_type.id)
        if days > remaining:
            #  `remaining()` trả 0.0 cho CẢ hai cảnh: hết phép, và chưa ai cấp quỹ năm nay.
            #  Nói cả hai — bảo người dùng "anh hết phép" khi thật ra Nhân sự chưa cấp quỹ
            #  là sai sự thật ở đúng chỗ họ không kiểm chứng được.
            warnings.append(
                f"Quỹ «{leave_type.name}» chỉ còn {remaining} ngày mà đơn xin {days} ngày — "
                "hệ không cho ứng phép, phần vượt phải chuyển sang loại nghỉ không lương."
                + (" (Còn 0 ngày cũng có thể do quỹ phép năm nay CHƯA được cấp — hỏi lại "
                   "phòng Nhân sự.)" if remaining == 0 else ""))

    return {
        "status": "ready",
        "total": 1,
        "draft": {
            #  `kind` để giao diện chat phân biệt bản nháp đơn nghỉ phép với YCBG/YCMH.
            #  ⚠️ **Cố ý KHÔNG có `employee_id`**: form mặc định người nghỉ là chính người
            #  đang lập đơn. Để trợ lý điền ô đó là mở đường nộp đơn HỘ người khác qua chat.
            "kind": "leave_request",
            "lines": [{"leave_type_id": leave_type.id,
                       "leave_type": leave_type.name, "days": days}],
            "from_date": from_date,
            "to_date": to_date,
            "from_session": from_session,
            "to_session": to_session,
            "from_time": from_time,
            "to_time": to_time,
            "reason": reason,
            "contact_phone": _clean_text(args.get("contact_phone"), 30),
        },
        "leave_type_label": leave_type.name,
        "from_session_label": LEAVE_SESSION_LABELS.get(from_session, ""),
        "to_session_label": LEAVE_SESSION_LABELS.get(to_session, ""),
        "total_days": days,
        "remaining_days": remaining,
        "warnings": warnings,
        "note": f"Số ngày {days} là GỢI Ý theo lịch làm việc (đã trừ Chủ nhật và ngày lễ) — "
                "người dùng sửa được trên form. Đơn này chỉ khai MỘT loại nghỉ; cần nhiều "
                "loại trong cùng khoảng ngày thì bấm «Thêm loại nghỉ» ngay trên form.",
        "reminder": "Đơn CHƯA được tạo và CHƯA gửi duyệt. Hãy tóm tắt bản đề xuất (ngày nghỉ, "
                    "loại nghỉ, số ngày, lý do) rồi mời người dùng bấm nút 'Tạo đơn nghỉ phép' "
                    "dưới câu trả lời để mở form đã điền sẵn — họ rà lại, bấm Lưu nháp rồi "
                    "Gửi duyệt.",
    }


DRAFT_LEAVE_REQUEST_SPEC = ToolSpec(
    name="draft_leave_request",
    description=_LEAVE_DESC,
    parameters=_LEAVE_PARAMS,
    handler=_run_leave,
)


# ── Gắn danh mục thật vào khai báo tool ──────────────────────────────────────────────────

_DRAFT_TOOL_NAMES = ("draft_survey_request", "draft_purchase_request", "draft_leave_request")


def inject_catalog_enums(defs, db) -> None:
    """Gắn `enum` danh mục THẬT của môi trường đang chạy vào khai báo 3 tool soạn nháp:
    Phân loại VTBB/NL (`item_group` — chỉ YCBG), pháp nhân nhận hóa đơn (`company`) và
    Loại nghỉ (`leave_type` — chỉ đơn nghỉ phép).

    Model thấy trước danh sách hợp lệ ngay trong schema nên hết bịa tên ngoài danh mục
    ("Thiết bị văn phòng / IT" — lỗi khách bắt được 26/08/2026) thay vì phải gọi sai rồi
    được tool sửa lưng. Phải deepcopy vì các def dùng CHUNG dict `_PARAMS` module-level —
    ghi thẳng enum vào đó là dính sang mọi request sau.
    """
    from copy import deepcopy

    from app.modules.catalog.model import ItemGroup
    from app.modules.company.model import Company
    from app.modules.leave.catalog_model import LeaveType

    try:
        groups = sorted({n for (n,) in db.query(ItemGroup.name)
                         .filter(ItemGroup.is_active.is_(True)).all() if n})
        companies = sorted({n for (n,) in db.query(Company.name)
                            .filter(Company.is_active.is_(True)).all() if n})
        #  Loại nghỉ gắn bằng MÃ (`code`) chứ không bằng tên: tên có dấu, người dùng gọi
        #  mỗi lúc một kiểu, còn mã thì `_pick_leave_type` tra thẳng. Tên đi kèm trong
        #  phần mô tả để model biết mã nào là gì.
        leave_types = [(c, n) for (c, n) in db.query(LeaveType.code, LeaveType.name)
                       .filter(LeaveType.is_active.is_(True))
                       .order_by(LeaveType.sort_order, LeaveType.id).all() if c]
    except Exception:  # noqa: BLE001 - danh mục lỗi thì giữ khai báo tĩnh, không sập lượt chat
        return
    if not groups and not companies and not leave_types:
        return

    for d in defs:
        if d.name not in _DRAFT_TOOL_NAMES:
            continue
        params = deepcopy(d.parameters)
        props = params.get("properties", {})
        if groups:
            item_group = (props.get("lines", {})
                          .get("items", {}).get("properties", {}).get("item_group"))
            if item_group is not None:
                item_group["enum"] = groups
        if companies:
            company = props.get("company")
            if company is not None:
                company["enum"] = companies
        leave_type = props.get("leave_type")
        if leave_types and leave_type is not None:
            leave_type["enum"] = [c for c, _ in leave_types]
            leave_type["description"] += (" Danh mục hiện có: "
                                          + " · ".join(f"{c} ({n})" for c, n in leave_types) + ".")
        d.parameters = params
