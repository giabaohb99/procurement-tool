"""bao-CR-397 — ô "TP/BP mua hàng" trên bản in Phiếu đề xuất mua hàng.

Trước CR này ô đó in NGƯỜI BẤM Điều phối. Trên prod người bấm là admin thu mua
(Châu Phúc Hậu) nên tên admin in vào ô trưởng phòng — khách bắt lỗi trên phiếu PYC12092604.
Nay `_approval_signers` trả thêm `purchasing_head_name/_signature` = TRƯỞNG PHÒNG của phòng
ban mà người điều phối thuộc (`Department.manager_id`), và chỉ lùi về người điều phối khi
không suy ra được trưởng phòng. `dispatcher_*` giữ nguyên để tương thích.

Chữ ký trưởng phòng tra theo NHÂN SỰ (`resolve_signature_by_employee`) chứ không theo
người bấm nút — ảnh phải khớp đúng tên đang in.
"""
from app.core.audit import record
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.purchase_request.controller import _approval_signers
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.user.model import User


def _department(db, name: str, manager_id: int = 0) -> Department:
    dept = Department(code=name.replace(" ", "").upper()[:20], name=name,
                      manager_id=manager_id)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


def _employee(db, full_name: str, department_id: int = 0) -> Employee:
    emp = Employee(full_name=full_name, code=full_name.replace(" ", ""),
                   department_id=department_id)
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


def _user(db, emp: Employee | None, signature: str = "", email: str = "",
          is_active: bool = True) -> User:
    user = User(email=email or f"{emp.code}@dego.vn", employee_id=emp.id if emp else 0,
                signature=signature, is_active=is_active)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _pr(db, status: str = "dispatched", code: str = "PYC-TP") -> PurchaseRequest:
    pr = PurchaseRequest(code=code, status=status, requester="Nguoi Yeu Cau",
                         department="Phong De Xuat", created_by=1, updated_by=1)
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pr


def _purchasing_world(db, head_signature: str = "https://cdn/ky-truong-phong.png"):
    """Phòng thu mua có trưởng phòng (Ngân) và một admin (Hậu) — admin bấm Điều phối."""
    dept = _department(db, "San xuat - Thu mua")
    head = _employee(db, "Pham Khanh Ngan", dept.id)
    _user(db, head, head_signature)
    dept.manager_id = head.id
    db.commit()
    admin = _employee(db, "Chau Phuc Hau", dept.id)
    admin_user = _user(db, admin, "https://cdn/ky-admin.png")
    return dept, head, admin_user


def test_prints_the_department_head_not_the_dispatcher(db):
    """Đúng ca prod: admin thu mua điều phối -> ô TP/BP mua hàng phải ra TRƯỞNG PHÒNG."""
    _, _, admin_user = _purchasing_world(db)
    pr = _pr(db)
    record(db, admin_user.id, "purchase_request", pr.id, "dispatched")

    out = _approval_signers(db, pr)

    assert out["purchasing_head_name"] == "Pham Khanh Ngan"
    assert out["purchasing_head_signature"] == "https://cdn/ky-truong-phong.png"
    # Người bấm nút vẫn được trả ở cặp cũ — không phá ai đang đọc `dispatcher_*`.
    assert out["dispatcher_name"] == "Chau Phuc Hau"
    assert out["dispatcher_signature"] == "https://cdn/ky-admin.png"


def test_head_signature_follows_the_head_not_the_dispatcher(db):
    """Trưởng phòng chưa tải chữ ký: ô ra TÊN trưởng phòng và KHÔNG mượn ảnh của admin."""
    _, _, admin_user = _purchasing_world(db, head_signature="")
    pr = _pr(db)
    record(db, admin_user.id, "purchase_request", pr.id, "dispatched")

    out = _approval_signers(db, pr)

    assert out["purchasing_head_name"] == "Pham Khanh Ngan"
    assert out["purchasing_head_signature"] == ""


def test_falls_back_to_the_dispatcher_when_the_department_has_no_head(db):
    dept = _department(db, "Phong chua co truong")
    admin = _employee(db, "Chau Phuc Hau", dept.id)
    admin_user = _user(db, admin, "https://cdn/ky-admin.png")
    pr = _pr(db)
    record(db, admin_user.id, "purchase_request", pr.id, "dispatched")

    out = _approval_signers(db, pr)

    assert out["purchasing_head_name"] == "Chau Phuc Hau"
    assert out["purchasing_head_signature"] == "https://cdn/ky-admin.png"


def test_falls_back_when_the_dispatcher_has_no_employee_or_department(db):
    """Tài khoản chưa gắn nhân sự (admin kỹ thuật) hoặc nhân sự chưa có phòng."""
    no_emp = _user(db, None, "https://cdn/ky-sys.png", email="admin@dego.vn")
    pr1 = _pr(db, code="PYC-TP-1")
    record(db, no_emp.id, "purchase_request", pr1.id, "dispatched")
    assert _approval_signers(db, pr1)["purchasing_head_name"] == "admin@dego.vn"

    no_dept = _employee(db, "Le Khong Phong")
    no_dept_user = _user(db, no_dept, "https://cdn/ky-khong-phong.png")
    pr2 = _pr(db, code="PYC-TP-2")
    record(db, no_dept_user.id, "purchase_request", pr2.id, "dispatched")
    out = _approval_signers(db, pr2)
    assert out["purchasing_head_name"] == "Le Khong Phong"
    assert out["purchasing_head_signature"] == "https://cdn/ky-khong-phong.png"


def test_falls_back_when_the_head_points_to_a_deleted_employee(db):
    """`manager_id` trỏ tới id đã bị xóa — không được nổ, cũng không in tên rỗng."""
    dept = _department(db, "Thu mua", manager_id=999_999)
    admin = _employee(db, "Chau Phuc Hau", dept.id)
    admin_user = _user(db, admin)
    pr = _pr(db)
    record(db, admin_user.id, "purchase_request", pr.id, "dispatched")

    assert _approval_signers(db, pr)["purchasing_head_name"] == "Chau Phuc Hau"


def test_stays_empty_before_the_dispatch_step(db):
    """Phiếu mới Đã duyệt (chưa điều phối) hoặc bị trả về: ô rỗng dù nhật ký còn dòng cũ."""
    _, _, admin_user = _purchasing_world(db)
    for status, code in (("approved", "PYC-TP-A"), ("draft", "PYC-TP-D")):
        pr = _pr(db, status=status, code=code)
        record(db, admin_user.id, "purchase_request", pr.id, "dispatched")
        out = _approval_signers(db, pr)
        assert out["purchasing_head_name"] == ""
        assert out["purchasing_head_signature"] == ""


def test_uses_the_most_recent_dispatch(db):
    """Điều phối lại bởi người phòng khác: lấy trưởng phòng của LẦN SAU."""
    _, _, admin_user = _purchasing_world(db)
    other_dept = _department(db, "Phong khac")
    other_head = _employee(db, "Truong Phong Khac", other_dept.id)
    other_dept.manager_id = other_head.id
    db.commit()
    other_staff = _employee(db, "Nhan Vien Khac", other_dept.id)
    other_user = _user(db, other_staff)
    pr = _pr(db)
    record(db, admin_user.id, "purchase_request", pr.id, "dispatched")
    record(db, other_user.id, "purchase_request", pr.id, "dispatched")

    assert _approval_signers(db, pr)["purchasing_head_name"] == "Truong Phong Khac"
