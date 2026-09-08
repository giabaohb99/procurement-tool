"""Chữ ký trên bản in Đơn mua hàng — `resolve_print_signers`.

Bản in ĐMH có công tắc Có/Không chữ ký như phiếu YCMH. Ảnh chữ ký lấy từ tài khoản:
ô "Người lập" theo người tạo đơn, ô "Trưởng bộ phận" / "Trưởng phòng" theo người bấm
Duyệt — người duyệt không có cột riêng nên phải tra nhật ký thao tác.

Điều dễ hỏng nhất: đơn bị Hủy duyệt (CR-108) về Nháp rồi sửa lại mà chữ ký người duyệt
cũ vẫn nằm trên bản in — thành ra một đơn CHƯA ai duyệt lại có chữ ký duyệt.
"""
from app.core.audit import record
from app.modules.employee.model import Employee
from app.modules.purchase_order.controller import resolve_print_signers
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.user.model import User


def _nguoi_dung(db, full_name: str, signature: str = "", is_active: bool = True) -> User:
    emp = Employee(full_name=full_name, code=full_name.replace(" ", ""))
    db.add(emp)
    db.commit()
    db.refresh(emp)
    user = User(email=f"{emp.code}@dego.vn", employee_id=emp.id, signature=signature,
                is_active=is_active)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _don(db, status: str = "approved", created_by: int = 0, code: str = "PO-KY") -> PurchaseOrder:
    po = PurchaseOrder(code=code, status=status, supplier_code="NCC01",
                       supplier_name="NCC Một", created_by=created_by, updated_by=created_by)
    db.add(po)
    db.commit()
    db.refresh(po)
    return po


def test_returns_creator_and_approver_signatures(db):
    lap = _nguoi_dung(db, "Nguyen Van Lap", "https://cdn/ky-lap.png")
    duyet = _nguoi_dung(db, "Tran Thi Duyet", "https://cdn/ky-duyet.png")
    po = _don(db, created_by=lap.id)
    record(db, duyet.id, "purchase_order", po.id, "approved")

    out = resolve_print_signers(db, po)

    assert out["creator_name"] == "Nguyen Van Lap"
    assert out["creator_signature"] == "https://cdn/ky-lap.png"
    assert out["approver_name"] == "Tran Thi Duyet"
    assert out["approver_signature"] == "https://cdn/ky-duyet.png"


def test_takes_the_most_recent_approval_not_the_first(db):
    """Hủy duyệt rồi duyệt lại: phải là chữ ký người duyệt LẦN SAU."""
    lap = _nguoi_dung(db, "Nguyen Van Lap", "https://cdn/ky-lap.png")
    cu = _nguoi_dung(db, "Le Van Cu", "https://cdn/ky-cu.png")
    moi = _nguoi_dung(db, "Pham Thi Moi", "https://cdn/ky-moi.png")
    po = _don(db, created_by=lap.id)
    record(db, cu.id, "purchase_order", po.id, "approved")
    record(db, cu.id, "purchase_order", po.id, "draft", "Hủy duyệt để sửa")
    record(db, moi.id, "purchase_order", po.id, "approved")

    out = resolve_print_signers(db, po)

    assert out["approver_name"] == "Pham Thi Moi"
    assert out["approver_signature"] == "https://cdn/ky-moi.png"


def test_drops_approver_when_the_order_went_back_to_draft(db):
    lap = _nguoi_dung(db, "Nguyen Van Lap", "https://cdn/ky-lap.png")
    duyet = _nguoi_dung(db, "Tran Thi Duyet", "https://cdn/ky-duyet.png")
    po = _don(db, status="draft", created_by=lap.id)
    record(db, duyet.id, "purchase_order", po.id, "approved")   # lần duyệt trước khi bị hủy duyệt

    out = resolve_print_signers(db, po)

    assert out["approver_name"] == ""
    assert out["approver_signature"] == ""
    # Người lập thì vẫn in — đơn nháp in ra vẫn phải biết ai lập.
    assert out["creator_name"] == "Nguyen Van Lap"


def test_drops_approver_on_a_cancelled_order(db):
    duyet = _nguoi_dung(db, "Tran Thi Duyet", "https://cdn/ky-duyet.png")
    po = _don(db, status="cancelled")
    record(db, duyet.id, "purchase_order", po.id, "approved")

    assert resolve_print_signers(db, po)["approver_signature"] == ""


def test_keeps_signing_boxes_for_orders_received_or_completed(db):
    """Duyệt xong đơn còn chạy tiếp qua nhiều trạng thái — chữ ký duyệt phải theo suốt."""
    duyet = _nguoi_dung(db, "Tran Thi Duyet", "https://cdn/ky-duyet.png")
    for status in ("approved", "partial", "received", "completed"):
        po = _don(db, status=status, code=f"PO-KY-{status}")
        record(db, duyet.id, "purchase_order", po.id, "approved")
        assert resolve_print_signers(db, po)["approver_signature"] == "https://cdn/ky-duyet.png"


def test_returns_empty_strings_when_nobody_uploaded_a_signature(db):
    """Chưa ai tải chữ ký lên thì ô ký để trống — vẫn phải ra HỌ TÊN để ký tay."""
    lap = _nguoi_dung(db, "Nguyen Van Lap")
    duyet = _nguoi_dung(db, "Tran Thi Duyet")
    po = _don(db, created_by=lap.id)
    record(db, duyet.id, "purchase_order", po.id, "approved")

    out = resolve_print_signers(db, po)

    assert out["creator_signature"] == ""
    assert out["approver_signature"] == ""
    assert out["creator_name"] == "Nguyen Van Lap"
    assert out["approver_name"] == "Tran Thi Duyet"


def test_survives_an_order_with_no_creator_and_no_audit_row(db):
    """Đơn cũ nhập từ dữ liệu ngoài: `created_by = 0`, không có dòng nhật ký nào."""
    po = _don(db, created_by=0)

    out = resolve_print_signers(db, po)

    assert out["creator_signature"] == ""
    assert out["approver_name"] == ""
    # `resolve_actor` trả "Hệ thống" khi không có người — đừng in ảnh chữ ký của ai cả.
    assert out["creator_name"] == "Hệ thống"


def test_ignores_audit_rows_of_another_order(db):
    """Lọc theo `entity_id`: đơn khác duyệt rồi không làm đơn này có chữ ký."""
    duyet = _nguoi_dung(db, "Tran Thi Duyet", "https://cdn/ky-duyet.png")
    khac = _don(db, code="PO-KY-KHAC")
    record(db, duyet.id, "purchase_order", khac.id, "approved")
    po = _don(db)

    assert resolve_print_signers(db, po)["approver_name"] == ""
