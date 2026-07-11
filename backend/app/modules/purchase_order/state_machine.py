"""Máy trạng thái tiến độ dòng PO (progress_status).

Module thuần Python, KHÔNG đụng DB — nhận sẵn object po/item/deliveries (đã
load từ DB ở service gọi) và chỉ tính toán/validate trên dữ liệu trong bộ nhớ.
Nhờ vậy dễ unit-test độc lập (xem phase-05).

v1: chỉ kiểm tra "có giá trị / > 0".
# TODO v2: validate định dạng invoice_no (ĐMH#####) và thứ tự ngày tháng.
"""

from __future__ import annotations

from typing import Any, Callable

# Luồng tiến độ chính (tuần tự) và các trạng thái ngoại lệ (không theo tuần tự)
PROGRESS_FLOW = [
    "Chưa đặt hàng",
    "Đã đặt hàng",
    "Đã nhận hàng",
    "Đã gửi ĐMH cho KT",
    "Hoàn thành",
]
EXCEPTION_STATES = ["Tạm ngưng", "Hủy đơn"]

# Tên hiển thị tiếng Việt cho từng field — dùng để báo user cột nào còn thiếu
FIELD_LABELS: dict[str, str] = {
    "misa_code": "Mã đơn Misa",
    "supplier_name": "Nhà cung cấp",
    "order_date": "Ngày đặt hàng NCC",
    "payment_terms": "Hình thức thanh toán NCC",
    "qty_order": "Số lượng đặt NCC",
    "price": "Đơn giá",
    "vat": "VAT",
    "expected_date": "Ngày dự kiến nhận tại kho",
    "carrier_code": "Đơn vị vận chuyển",
    "received_date": "Ngày nhận thực tế",
    "ship_qty": "Số lượng gửi vận chuyển",
    "ship_unit": "ĐVT vận chuyển",
    "received_qty": "Số lượng đã nhận",
    "delivery_count": "Số lần nhận",
    "shipping_unit_price": "Đơn giá/ĐVT vận chuyển",
    "invoice_no": "Số hóa đơn",
    "pay_confirm_date": "Ngày KT xác nhận thanh toán",
}


def _to_float(value: Any) -> float:
    """Ép an toàn về float, giá trị rỗng/không hợp lệ → 0."""
    try:
        return float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _missing_dat_hang(po: Any, item: Any, deliveries: list) -> list[str]:
    """Điều kiện chuyển sang 'Đã đặt hàng'."""
    missing: list[str] = []
    if not getattr(po, "misa_code", ""):
        missing.append("misa_code")
    if not getattr(po, "supplier_name", ""):
        missing.append("supplier_name")
    if not getattr(po, "order_date", ""):
        missing.append("order_date")
    if not getattr(po, "payment_terms", ""):
        missing.append("payment_terms")
    if _to_float(getattr(item, "qty_order", 0)) <= 0:
        missing.append("qty_order")
    if _to_float(getattr(item, "price", 0)) <= 0:
        missing.append("price")
    if _to_float(getattr(item, "vat", 0)) < 0:
        missing.append("vat")
    if not any(getattr(d, "expected_date", "") for d in deliveries):
        missing.append("expected_date")
    if not any(getattr(d, "carrier_code", "") for d in deliveries):
        missing.append("carrier_code")
    return missing


def _missing_nhan_hang(po: Any, item: Any, deliveries: list) -> list[str]:
    """Điều kiện chuyển sang 'Đã nhận hàng'."""
    missing: list[str] = []
    if not any(getattr(d, "received_date", "") for d in deliveries):
        missing.append("received_date")
    if not any(_to_float(getattr(d, "ship_qty", 0)) > 0 for d in deliveries):
        missing.append("ship_qty")
    if not any(getattr(d, "ship_unit", "") for d in deliveries):
        missing.append("ship_unit")
    if not any(_to_float(getattr(d, "received_qty", 0)) > 0 for d in deliveries):
        missing.append("received_qty")
    if len(deliveries) < 1:
        missing.append("delivery_count")
    # Đơn giá/ĐVT vận chuyển: coi như đã điền nếu tồn tại ít nhất 1 lần giao
    if not deliveries:
        missing.append("shipping_unit_price")
    return missing


def _missing_dmh_kt(po: Any, item: Any, deliveries: list) -> list[str]:
    """Điều kiện chuyển sang 'Đã gửi ĐMH cho KT': item-level ưu tiên, fallback delivery."""
    invoice_ok = bool(getattr(item, "invoice_no", "")) or any(
        getattr(d, "invoice_no", "") for d in deliveries
    )
    return [] if invoice_ok else ["invoice_no"]


def _missing_hoan_thanh(po: Any, item: Any, deliveries: list) -> list[str]:
    """Điều kiện chuyển sang 'Hoàn thành': xác nhận thanh toán cấp dòng."""
    return [] if getattr(item, "pay_confirm_date", "") else ["pay_confirm_date"]


# Bảng tra hàm kiểm tra thiếu field theo từng trạng thái đích trong PROGRESS_FLOW
_MISSING_CHECKERS: dict[str, Callable[[Any, Any, list], list[str]]] = {
    "Chưa đặt hàng": lambda po, item, deliveries: [],  # trạng thái khởi tạo, luôn hợp lệ
    "Đã đặt hàng": _missing_dat_hang,
    "Đã nhận hàng": _missing_nhan_hang,
    "Đã gửi ĐMH cho KT": _missing_dmh_kt,
    "Hoàn thành": _missing_hoan_thanh,
}


def _current_status(item: Any) -> str:
    return getattr(item, "progress_status", "") or "Chưa đặt hàng"


def get_allowed_statuses(po: Any, item: Any, deliveries: list) -> list[dict]:
    """Trả list trạng thái khả dụng cho dropdown chuyển tiến độ.

    Chỉ trạng thái NGAY KẾ TIẾP trong flow mới có thể disabled=False (khi đủ
    điều kiện). Mọi trạng thái khác trong flow (đã qua / xa hơn kế tiếp) →
    disabled=True. Các trạng thái ngoại lệ (Tạm ngưng/Hủy đơn) luôn khả dụng.
    """
    current = _current_status(item)
    try:
        current_idx = PROGRESS_FLOW.index(current)
    except ValueError:
        current_idx = 0

    result: list[dict] = []
    for idx, status in enumerate(PROGRESS_FLOW):
        missing_keys = _MISSING_CHECKERS[status](po, item, deliveries)
        missing_labels = [FIELD_LABELS[k] for k in missing_keys]
        if idx == current_idx + 1:
            disabled = len(missing_keys) > 0
        else:
            disabled = True
        result.append({"status": status, "disabled": disabled, "missing": missing_labels})

    for status in EXCEPTION_STATES:
        result.append({"status": status, "disabled": False, "missing": []})

    return result


def validate_transition(
    po: Any, item: Any, deliveries: list, target: str, is_manager: bool
) -> dict:
    """Kiểm tra một transition cụ thể trước khi service ghi DB."""
    all_states = PROGRESS_FLOW + EXCEPTION_STATES
    if target not in all_states:
        return {"ok": False, "missing_fields": [], "error": f"Trạng thái '{target}' không hợp lệ"}

    current = _current_status(item)
    if target == current:
        return {"ok": True, "missing_fields": [], "error": None}

    # Trạng thái ngoại lệ: bỏ qua rule tuần tự (lý do xử lý ở service riêng)
    if target in EXCEPTION_STATES:
        return {"ok": True, "missing_fields": [], "error": None}

    target_idx = PROGRESS_FLOW.index(target)
    try:
        current_idx = PROGRESS_FLOW.index(current)
    except ValueError:
        # current đang là trạng thái ngoại lệ (Tạm ngưng/Hủy đơn) hoặc rỗng —
        # không áp rule lùi/nhảy cóc, chỉ kiểm tra field còn thiếu.
        current_idx = None

    if current_idx is not None:
        if target_idx < current_idx:
            if not is_manager:
                return {"ok": False, "missing_fields": [], "error": "Không được lùi trạng thái"}
        elif target_idx > current_idx + 1:
            next_status = PROGRESS_FLOW[current_idx + 1]
            return {
                "ok": False,
                "missing_fields": [],
                "error": f"Không được nhảy cóc, phải qua '{next_status}' trước",
            }

    missing_keys = _MISSING_CHECKERS[target](po, item, deliveries)
    missing_labels = [FIELD_LABELS[k] for k in missing_keys]
    return {"ok": len(missing_labels) == 0, "missing_fields": missing_labels, "error": None}


def is_short_delivery(item: Any, deliveries: list) -> bool:
    """Cảnh báo 'Giao thiếu' (không chặn): tổng received_qty < qty_order."""
    total_received = sum(_to_float(getattr(d, "received_qty", 0)) for d in deliveries)
    qty_order = _to_float(getattr(item, "qty_order", 0))
    return total_received < qty_order
