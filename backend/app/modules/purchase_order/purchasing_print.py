"""Dữ liệu "Mẫu thu mua" của màn In YCMH từ ĐMH (duoc-CR-777, anh Được chốt 17/11/2026).

Khác mẫu thường (dựng từ phiếu YCMH nguồn, `controller.get_po_purchase_request`) ở bốn chỗ:

- **Người đề xuất** = người ĐANG ĐĂNG NHẬP (người thu mua bấm in), kèm chữ ký tài khoản của chính họ.
- **Trưởng phòng ban / bộ phận** = QUẢN LÝ TRỰC TIẾP của người đó (`Employee.manager_id`), kèm chữ ký — không phải
  trưởng phòng ghi trên YCMH. Hồ sơ chưa gán quản lý trực tiếp thì để trống, không đoán.
- **NCC do bộ phận đề xuất** = NCC của ĐMH; che khi người xem thiếu `supplier.read` (cùng luật che NCC của bản in YCMH).
- **Bảng hàng** = các dòng của ĐMH (SL đặt, đơn giá, VAT của ĐMH), bỏ dòng đã Hủy. Thành tiền theo NGUYÊN TỆ của đơn,
  cùng công thức `po_item.amount` (SL × giá × (100 + VAT) / 100, làm tròn 2 số lẻ).

Gác ở nơi gọi: quyền ĐỌC đơn mua hàng và đơn nằm trong phạm vi đọc của người đó.
"""
from sqlalchemy.orm import Session

from app.core.audit import resolve_signature
from app.core.print_signers import person_block
from app.modules.employee.model import Employee

from .model import POItem, PurchaseOrder

#  Dòng đã Hủy không còn là hàng sẽ mua — không in.
_SKIPPED_PROGRESS = ("cancelled",)


def _line_amount(qty: float, price: float, vat: float) -> float:
    return round(qty * price * (100 + vat) / 100, 2)


def _proposer(db: Session, user) -> tuple[dict, Employee | None]:
    """Người đang đăng nhập: tên theo hồ sơ nhân sự (lùi về tên tài khoản), chức vụ, phòng, chữ ký tài khoản."""
    emp = db.get(Employee, user.employee_id) if getattr(user, "employee_id", 0) else None
    name = (emp.full_name if emp else "") or getattr(user, "full_name", "") or getattr(user, "email", "") or ""
    return ({"employee_id": emp.id if emp else 0, "name": name,
             "position": (emp.position or "") if emp else "",
             "department": (emp.department_name or "") if emp else "",
             "signature": resolve_signature(db, user.id)}, emp)


def _manager(db: Session, emp: Employee | None) -> dict:
    manager_id = int(emp.manager_id or 0) if emp else 0
    manager = db.get(Employee, manager_id) if manager_id else None
    return {"employee_id": manager_id if manager else 0, **person_block(db, manager_id if manager else 0),
            "position": (manager.position or "") if manager else ""}


def build_purchasing_print(db: Session, po: PurchaseOrder, items: list[POItem], user, show_supplier: bool) -> dict:
    """Khối dữ liệu Mẫu thu mua cho một ĐMH (`items` = dòng của đơn, đã nạp sẵn)."""
    proposer, emp = _proposer(db, user)
    lines, subtotal, vat_total = [], 0.0, 0.0
    for it in items:
        if (it.progress_status or "") in _SKIPPED_PROGRESS:
            continue
        qty, price, vat = float(it.qty_order or 0), float(it.price or 0), float(it.vat or 0)
        before = round(qty * price, 2)
        amount = _line_amount(qty, price, vat)
        subtotal += before
        vat_total += amount - before
        lines.append({"line_id": it.id, "product_code": it.product_code or "", "product_name": it.product_name or "",
                      "invoice_name": it.invoice_name or "", "spec": it.spec or "", "item_group": it.item_group or "",
                      "unit": it.unit or "", "qty": qty, "price": price, "vat": vat, "amount": amount})
    return {
        "po_id": po.id, "po_code": po.code, "order_date": po.order_date or "", "currency": po.currency or "VND",
        "proposer": proposer,
        "manager": _manager(db, emp),
        "supplier": ({"code": po.supplier_code or "", "name": po.supplier_name or ""} if show_supplier
                     else {"code": "", "name": ""}),
        "supplier_hidden": not show_supplier,
        "items": lines,
        "subtotal": round(subtotal, 2),
        "vat": round(vat_total, 2),
        "total": round(subtotal + vat_total, 2),
    }
