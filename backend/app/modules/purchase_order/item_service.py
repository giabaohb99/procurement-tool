"""ĐMH — lưu dòng hàng (điền sẵn thông số, tên trên hóa đơn, tiền tệ, ngày dự kiến) và ô bắt buộc của dòng
(bao-CR-715 tách từ service.py).
"""
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.catalog import lead_time

from .model import DEFAULT_CURRENCY, OrderType, POItem, PurchaseOrder
from .base_service import PROG_CANCELLED, PROG_COMPLETED, deliveries_of, items_of, rate_of
from .delivery_service import _cleanup_delivery, _save_deliveries


def _product_specs_map(db: Session, items) -> dict:
    """Thông số kỹ thuật của các SP xuất hiện trong payload (1 query, không N+1).
    Dùng để tự điền "Xuất xứ / TSKT / chất liệu" cho dòng hàng MỚI còn bỏ trống."""
    from app.modules.product.model import Product
    codes = {(getattr(r, "product_code", "") or "").strip() for r in (items or [])}
    codes.discard("")
    if not codes:
        return {}
    rows = db.query(Product.code, Product.specs).filter(Product.code.in_(codes)).all()
    return {c: (s or "") for c, s in rows if s}


def product_invoice_names_map(db: Session, codes) -> dict[str, str]:
    """Tên trên hóa đơn của sản phẩm master theo mã (1 query, không N+1). duoc-CR-663.
    Chỉ trả mã có tên khác rỗng. Dùng chung cho lúc LƯU dòng ĐMH và lúc bù dữ liệu cũ."""
    from app.modules.product.model import Product
    codes = {(c or "").strip() for c in (codes or [])}
    codes.discard("")
    if not codes:
        return {}
    rows = db.query(Product.code, Product.invoice_name).filter(Product.code.in_(codes)).all()
    return {c: n.strip() for c, n in rows if n and n.strip()}


def fill_blank_invoice_name(db: Session, fields: dict, cache: dict | None = None) -> dict:
    """Điền "Tên trên hóa đơn" từ sản phẩm master vào `fields` (dict cột dòng ĐMH) khi còn trống.
    Dùng chung cho nhập Excel và sao chép ĐMH (duoc-CR-663); `cache` {mã: tên} để khỏi truy vấn lặp.
    Không ghi đè tên đã có; master không có tên thì giữ nguyên (trống)."""
    if (fields.get("invoice_name") or "").strip():
        return fields
    code = (fields.get("product_code") or "").strip()
    if not code:
        return fields
    if cache is None or code not in cache:
        found = product_invoice_names_map(db, [code]).get(code, "")
        if cache is not None:
            cache[code] = found
    else:
        found = cache[code]
    if found:
        fields["invoice_name"] = found
    return fields


def pr_expected_map(db: Session, pr_code: str) -> dict[str, str]:
    """{mã hàng -> thời gian dự kiến có hàng} của phiếu YCMH nguồn.

    Không có khóa ngoại giữa dòng YCMH và dòng ĐMH: cầu nối duy nhất là
    `PurchaseOrder.pr_code` + `product_code`. Mã hàng là DUY NHẤT trên phiếu YCMH
    (app/core/utils.assert_unique_product_codes) nên map theo mã trỏ đúng một dòng nguồn.
    Phía ĐMH được phép trùng mã (bao-CR-308) — các dòng trùng cùng chiếu về một dòng YCMH,
    cùng nhận một ngày dự kiến là đúng nghiệp vụ.
    """
    if not (pr_code or "").strip():
        return {}
    from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
    pr = db.query(PurchaseRequest).filter(PurchaseRequest.code == pr_code).first()
    if not pr:
        return {}
    rows = db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).all()
    return {(r.product_code or "").strip(): (r.expected_date or "").strip()
            for r in rows if (r.product_code or "").strip() and (r.expected_date or "").strip()}


def _save_items(db: Session, po: PurchaseOrder, items, user_id: int):
    """Upsert dòng hàng + các lần giao theo id (giữ id ổn định để side-effect idempotent)."""
    if items is None:
        return
    existing_items = {it.id: it for it in items_of(db, po.id)}
    # bao-CR-308: ĐMH ĐƯỢC PHÉP trùng mã hàng (mua theo bộ chứng từ: cùng mã, khác lô /
    # khác Tên trên hóa đơn). An toàn vì đồng bộ về YCMH cộng GỘP theo mã
    # (sync_from_purchase_orders), còn nhận hàng/công nợ/lịch sử đi theo ID dòng.
    # YCMH vẫn chặn trùng (assert_unique_product_codes) — trùng bên đó mới làm tiến độ
    # nhân đôi. Giao diện hỏi xác nhận trước khi lưu để chặn gõ nhầm.
    keep_item_ids = set()
    specs_by_code = _product_specs_map(db, items)
    inv_names = product_invoice_names_map(db, [getattr(r, "product_code", "") for r in items])
    std_map = lead_time.std_days_map(db)          # số ngày QĐ theo phân loại (mốc dài nhất)
    # Dự kiến có hàng: chép XUỐNG từ dòng YCMH nguồn, CHỈ khi ô trên ĐMH còn trống.
    # Đặt ở backend (không chỉ ở nút "Tạo ĐMH" bên giao diện) để nhập khẩu và dòng thêm sau
    # cũng được điền. Dòng không gắn YCMH, hoặc mã hàng không có trên YCMH: nhập tay bình thường.
    pr_expected = pr_expected_map(db, po.pr_code)
    for raw in items:
        delivs = raw.deliveries or []
        data = raw.model_dump(exclude={"deliveries"})
        # bao-CR-367: bỏ nhịp "có Số hóa đơn mà trống Ngày hóa đơn -> lấy ngày hôm nay".
        # Cùng lý do với `_save_deliveries`: ngày hóa đơn là ngày in trên tờ giấy, đoán hộ
        # bằng ngày nhập liệu là ghi một con số sai mà không ai phát hiện ra.
        # Dòng MỚI chưa có "Xuất xứ / TSKT / chất liệu" -> lấy Thông số kỹ thuật của SP.
        # Chỉ điền lúc TẠO dòng: dòng đang sửa mà người dùng cố ý xóa trắng thì giữ trắng.
        if not (data.get("spec") or "").strip() and not data.get("id"):
            data["spec"] = specs_by_code.get((data.get("product_code") or "").strip(), "")
        # duoc-CR-663: "Tên trên hóa đơn" GHI VÀO CỘT lúc lưu (lấy từ sản phẩm master theo mã hàng
        # khi ô còn trống) — trước đây chỉ suy ở lúc trả (serializer) nên báo cáo / xuất file /
        # truy vấn thẳng cột đều thấy trống. Người dùng đã gõ tên thì giữ nguyên; master không có
        # tên thì để trống (không đoán từ tên hàng).
        if not (data.get("invoice_name") or "").strip():
            data["invoice_name"] = inv_names.get((data.get("product_code") or "").strip(), "")
        # bao-CR-319: dòng không khai loại tiền / tỷ giá thì lấy theo ĐƠN. Không để trống hay
        # để 0 nằm trong CSDL — nhân với 0 là mất trắng số tiền mà không báo lỗi.
        if not (data.get("currency") or "").strip():
            data["currency"] = (po.currency or "").strip() or DEFAULT_CURRENCY
        if not float(data.get("exchange_rate") or 0):
            data["exchange_rate"] = rate_of(po) if data["currency"] == (po.currency or DEFAULT_CURRENCY) else 1
        # bao-CR-319 P3 — ĐƠN NHẬP KHẨU: VAT dòng hàng luôn 0, khóa ở BACKEND.
        # Hóa đơn của NCC nước ngoài không có thuế GTGT Việt Nam; thuế GTGT hàng nhập nộp
        # cho ngân sách nhà nước theo tờ khai và đã khai thành một dòng ở bảng chi phí nhập
        # khẩu. Để người dùng gõ VAT ở dòng hàng nữa là cộng thuế HAI LẦN, đồng thời sinh
        # công nợ thuế cho chính NCC bán hàng — người không hề nhận khoản đó.
        if int(po.order_type or OrderType.DOMESTIC) == int(OrderType.IMPORT):
            data["vat"] = 0
        if not (data.get("expected_date") or "").strip():
            exp_from_pr = pr_expected.get((data.get("product_code") or "").strip(), "")
            if exp_from_pr:
                data["expected_date"] = exp_from_pr
            elif not data.get("id") and not (po.pr_code or "").strip() and (data.get("item_group") or "").strip():
                # Dòng MỚI trên ĐMH độc lập (không gắn YCMH) -> tự tính theo ngày QĐ phân loại
                _base = (po.order_date or "").strip() or date.today().isoformat()
                data["expected_date"] = lead_time.regulated_date(std_map, data.get("item_group") or "", _base)
        iid = data.pop("id", None)
        if iid and iid in existing_items:
            it = existing_items[iid]
            # Dòng đã Hoàn thành / Hủy đơn → KHÓA: giữ nguyên, không cho sửa (kể cả lần giao)
            if (it.progress_status or "") in (PROG_COMPLETED, PROG_CANCELLED):
                keep_item_ids.add(it.id)
                continue
            # Dòng ĐÃ NHẬN HÀNG → khóa nhận diện sản phẩm. Đổi mã hàng/tên hàng/ĐVT lúc này
            # sẽ dời phiếu nhập kho + tồn kho đã ghi nhận sang hàng khác (sai số liệu kho).
            if float(it.qty_received or 0) > 0:
                line_name = (it.product_name or "").strip() or (it.product_code or "").strip() or f"#{it.id}"
                for f, label in (("product_code", "Mã hàng"), ("product_name", "Tên hàng"), ("unit", "ĐVT")):
                    new_v = (data.get(f) or "").strip()
                    old_v = (getattr(it, f, "") or "").strip()
                    if new_v != old_v:
                        raise HTTPException(
                            400,
                            f"Dòng '{line_name}' đã nhận hàng — không đổi được {label} "
                            f"('{old_v}' → '{new_v}'). Hãy hủy dòng này rồi thêm dòng mới.",
                        )
            for k, v in data.items():
                setattr(it, k, v)
            it.updated_by = user_id
        else:
            it = POItem(po_id=po.id, created_by=user_id, updated_by=user_id, **data)
            db.add(it)
        db.flush()
        keep_item_ids.add(it.id)
        _save_deliveries(db, po, it, delivs, user_id, std_map)

    # Xóa dòng hàng (và lần giao + side-effect) không còn trong payload
    for old_id, it in existing_items.items():
        if old_id not in keep_item_ids:
            for d in deliveries_of(db, old_id):
                _cleanup_delivery(db, d.id)
                db.delete(d)
            db.delete(it)
    db.flush()


# ───────────────────────── Trường BẮT BUỘC trước khi GỬI DUYỆT ─────────────────────────
# CR-095 (phiếu hỗ trợ TK19082601): khách chốt danh sách ô phải điền xong mới được
# trình đơn. Trước đây chỉ chặn thiếu NCC và thiếu dòng hàng (CR-073), nên đơn gửi lên
# vẫn có thể trống ĐVT, kho nhận, đơn giá — người duyệt không có gì để duyệt.
#
# Chặn ở lúc GỬI DUYỆT chứ không chặn lúc LƯU: người lập thường lưu nháp nhiều lần rồi
# mới điền đủ (chờ NCC báo giá, chờ kho xác nhận). Chặn lúc lưu là ép nhập một lượt.
#
# KHÔNG có VAT trong danh sách dù khách liệt kê: cột lưu số, giá trị 0 vừa nghĩa là
# "chưa nhập" vừa nghĩa là "hàng không chịu thuế / thuế suất 0%" — hai thứ đó không phân
# biệt được, chặn thì khóa luôn mặt hàng 0% hợp lệ. Ô nào để trống KHÔNG bắt buộc thì
# giữ nguyên: xuất xứ/TSKT, mã & tên HH thành phẩm, ngày giao chứng từ cho KT, ghi chú.
REQUIRED_LINE_FIELDS: list[tuple[str, str]] = [
    ("product_code", "Mã hàng"),
    ("item_group", "Phân loại"),
    ("product_name", "Tên hàng"),
    ("invoice_name", "Tên trên hóa đơn"),
    ("required_date", "Ngày yêu cầu có hàng"),
    ("expected_date", "Ngày dự kiến có hàng"),
    ("unit", "ĐVT"),
    ("warehouse_code", "Kho nhận mặc định"),
    ("qty_request", "SL yêu cầu"),
    ("qty_order", "SL đặt NCC"),
    ("price", "Đơn giá"),
]
# Ô số: 0 ở đây là "chưa nhập" thật — dòng hàng không có số lượng hoặc không có giá thì
# không phải là dòng để đặt mua.
_NUMERIC_FIELDS = {"qty_request", "qty_order", "price"}


def missing_line_fields(item: POItem) -> list[str]:
    """Nhãn các ô còn trống của MỘT dòng hàng, theo thứ tự hiện trên màn Chi tiết dòng."""
    missing = []
    for field, label in REQUIRED_LINE_FIELDS:
        value = getattr(item, field, None)
        is_empty = float(value or 0) <= 0 if field in _NUMERIC_FIELDS else not str(value or "").strip()
        if is_empty:
            missing.append(label)
    return missing
