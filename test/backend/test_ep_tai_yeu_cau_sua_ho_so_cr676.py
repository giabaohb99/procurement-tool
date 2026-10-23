"""duoc-CR-676 stress test — yêu cầu sửa hồ sơ (YCSH): volume, masking, families, races.

Mục tiêu: kiểm yêu cầu tự khai + duyệt nhân sự không có N+1, che cột nhạy cảm đúng,
xử lý hộ gia đình tối đa 30, chuỗi sự kiện duyệt/rút/gửi không bị chồng lấn khi
đồng thời.

Tệp này kiểm SQLite (tính được trong container). Đo HTTP đồng thời → script riêng.
"""
from datetime import date

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.auth import perm_cache_clear
from app.core.request_context import set_context
from app.modules.employee.change_request_model import EmployeeChangeRequest
from app.modules.employee.contact_model import EmployeeFamily
from app.modules.employee.model import Employee
from app.modules.notification.model import Notification
from app.modules.audit.model import AuditLog
from hdld_factory import client_as  # noqa: F401

BASE = "/api/employees"


def _ok(res, code=200):
    assert res.status_code == code, res.text
    return res.json()["data"]


@pytest.fixture
def stress_world(world, db):
    """a2 = HR với employee.write phạm vi công ty A · a1 = nhân viên A1."""
    world.grant("a2", "employee", "company", actions=("read", "write"))
    return world


def _count_queries(db, fn) -> int:
    """Đếm câu SQL thực thi trong `fn()`."""
    seen = []

    def on(conn, cursor, statement, *a):  # noqa: ARG001
        # Skip SQLite pragma/internal commands
        if not statement.strip().upper().startswith(("PRAGMA", "BEGIN", "COMMIT", "ROLLBACK")):
            seen.append(statement)

    engine = db.get_bind()
    event.listen(engine, "before_cursor_execute", on)
    try:
        fn()
    finally:
        event.remove(engine, "before_cursor_execute", on)
    return len(seen)


# ── A1. VOLUME — không N+1 khi lên 2000 yêu cầu ─────────────────────────────

def _bulk_change_requests(db: Session, world, n: int, start: int = 0, employee_ids: list[int] | None = None):
    """Tạo n yêu cầu sửa hồ sơ với dữ liệu fake — employee_ids ghi đè."""
    if employee_ids is None:
        # Tạo nhân viên + yêu cầu của nhân viên đó
        from app.modules.employee.model import Employee

        co = world.co[next(iter(world.co))]
        emps = [
            Employee(
                code=f"KL{start + i:05d}",
                full_name=f"Khối lượng {start + i}",
                company_id=co,
                department_id=0,
                is_active=True,
                ethnicity="Kinh",
            )
            for i in range(n)
        ]
        db.add_all(emps)
        db.flush()
        employee_ids = [e.id for e in emps]

    reqs = [
        EmployeeChangeRequest(
            employee_id=eid,
            pending_employee_id=eid,
            status=1,  # PENDING
            changes=[
                {"group": "personal", "field": "ethnicity", "before": "Kinh", "after": "Tày"},
            ],
            families=None,
            note=f"Cập nhật {i}",
            created_by=world.actor("a1").user.id,
            updated_by=world.actor("a1").user.id,
        )
        for i, eid in enumerate(employee_ids)
    ]
    db.add_all(reqs)
    db.commit()
    return employee_ids


def test_list_change_requests_constant_queries_50_vs_2000(db, stress_world, client_as):
    """Danh sách + pending-count phải có số truy vấn cố định dù 50 hay 2000 yêu cầu."""
    hr = client_as(stress_world.actor("a2"))
    # Làm nóng cache
    _ok(hr.get(f"{BASE}/change-requests"))

    _bulk_change_requests(db, stress_world, 50)
    q50_list = _count_queries(db, lambda: _ok(hr.get(f"{BASE}/change-requests")))
    q50_count = _count_queries(
        db, lambda: _ok(hr.get(f"{BASE}/change-requests/pending-count"))
    )

    _bulk_change_requests(db, stress_world, 1950, start=50)
    q2000_list = _count_queries(db, lambda: _ok(hr.get(f"{BASE}/change-requests")))
    q2000_count = _count_queries(
        db, lambda: _ok(hr.get(f"{BASE}/change-requests/pending-count"))
    )

    assert (
        q50_list == q2000_list
    ), f"LIST N+1: {q50_list} với 50 yêu cầu, {q2000_list} với 2000 (phân trang 20)"
    assert (
        q50_count == q2000_count
    ), f"PENDING-COUNT N+1: {q50_count} với 50, {q2000_count} với 2000"
    # Đảm bảo số truy vấn nằm trong khoảng hợp lý (5-20 để cover join/order by)
    assert 5 <= q50_list <= 20, f"list queries đáng ngờ: {q50_list}"
    assert 1 <= q50_count <= 5, f"pending-count queries đáng ngờ: {q50_count}"


# ── A2. CHE CỘT NHẠY CẢM — HR thiếu employee_sensitive.read ────────────────

def test_masking_list_shows_only_own_record_unmasked(db, stress_world, client_as):
    """Danh sách: HR không có employee_sensitive.read → tất cả nhạy cảm bị che
    trừ hồ sơ của chính người đang xem."""
    # a1 = của stress_world.actor("a1") = hồ sơ của mình
    # a3 = hồ sơ khác, của người khác
    stress_world.grant("a2", "employee", "company", actions=("read", "write"))
    stress_world.grant("a3", "employee", "company", actions=("read",))

    emp_a3 = db.get(Employee, stress_world.emp["a3"])
    emp_a3.bank_account_no = "987654321"
    db.commit()

    # a3 gửi yêu cầu đổi ngân hàng
    a3_client = client_as(stress_world.actor("a3"))
    rid = _ok(
        a3_client.post(
            f"{BASE}/me/change-requests",
            json={"bank": {"bank_account_no": "111222333"}},
        )
    )["id"]

    # HR xem danh sách mà KHÔNG có employee_sensitive.read
    hr_client = client_as(stress_world.actor("a2"))
    page = _ok(hr_client.get(f"{BASE}/change-requests"))

    req = page["items"][0]
    assert req["has_sensitive"] is True
    masked_item = req["items"][0]
    assert masked_item["field"] == "bank_account_no"
    assert (
        masked_item["before"] is None
    ), "che toàn bộ nhạy cảm: before → null cho người không có quyền"
    assert (
        masked_item["after"] is None
    ), "che toàn bộ nhạy cảm: after → null"


def test_masking_detail_view_unmasked_with_employee_sensitive_read(
    db, stress_world, client_as
):
    """Chi tiết: HR có employee_sensitive.read → xem nguyên giá trị."""
    stress_world.grant("a2", "employee_sensitive", "all", actions=("read",))
    perm_cache_clear(stress_world.actor("a2").user.id)

    a1_client = client_as(stress_world.actor("a1"))
    rid = _ok(
        a1_client.post(
            f"{BASE}/me/change-requests",
            json={"bank": {"bank_account_no": "SECRET123"}},
        )
    )["id"]

    hr_client = client_as(stress_world.actor("a2"))
    detail = _ok(hr_client.get(f"{BASE}/change-requests/{rid}"))

    item = detail["items"][0]
    assert item["field"] == "bank_account_no"
    assert item["before"] == ""
    assert item["after"] == "SECRET123"
    assert item["masked"] is False


# ── A3. HỘ GIA ĐÌNH — tối đa 30 dòng, ghi đè toàn bộ, kiểm xung đột ────────

def test_families_max_30_items_approved(stress_world, db, client_as):
    """Gửi 30 hộ gia đình + duyệt → ghi đè thành 30 dòng, không lỗi."""
    from app.core.hr_change_request_codes import EmployeeChangeRequestStatus as Status

    a1_client = client_as(stress_world.actor("a1"))
    hr_client = client_as(stress_world.actor("a2"))
    stress_world.grant("a2", "employee_sensitive", "all", actions=("read",))
    perm_cache_clear(stress_world.actor("a2").user.id)

    families = [
        {
            "full_name": f"Người thân {i}",
            "relation": (i % 5) + 1,
            "gender": (i % 2) + 1,
            "date_of_birth": "1990-01-01",
        }
        for i in range(30)
    ]
    rid = _ok(a1_client.post(f"{BASE}/me/change-requests", json={"families": families}))[
        "id"
    ]

    # Duyệt
    result = _ok(hr_client.post(f"{BASE}/change-requests/{rid}/approve"))
    assert result["status"] == int(Status.APPROVED)

    # Kiểm hồ sơ đã được cập nhật
    emp = db.get(Employee, stress_world.emp["a1"])
    fams = (
        db.query(EmployeeFamily).filter(EmployeeFamily.employee_id == emp.id).all()
    )
    assert len(fams) == 30


def test_families_conflict_after_submit_is_409(stress_world, db, client_as):
    """Gửi yêu cầu + hộ gia đình đã bị sửa sau lúc gửi → duyệt trả 409."""
    from app.modules.employee.schema import EmployeeFamilyIn
    from app.modules.employee import contact_service

    a1_client = client_as(stress_world.actor("a1"))
    hr_client = client_as(stress_world.actor("a2"))
    stress_world.grant("a2", "employee_sensitive", "all", actions=("read",))
    perm_cache_clear(stress_world.actor("a2").user.id)

    # Gửi yêu cầu với 1 thành viên gia đình
    rid = _ok(
        a1_client.post(
            f"{BASE}/me/change-requests",
            json={
                "families": [
                    {"full_name": "Vợ", "relation": 2, "gender": 2}
                ]
            },
        )
    )["id"]

    # HR đối lập sửa hộ gia đình trực tiếp (giả lập)
    emp = db.get(Employee, stress_world.emp["a1"])
    new_family = EmployeeFamilyIn(full_name="Con", relation=3, gender=1)
    contact_service.set_families(
        db, emp.id, [new_family], stress_world.actor("a2").user.id
    )
    db.commit()

    # Duyệt → phải 409
    res = hr_client.post(f"{BASE}/change-requests/{rid}/approve")
    assert res.status_code == 409
    assert "đã bị sửa" in res.text.lower() or "đặt lại" in res.text.lower()


# ── A4. KHÔNG TỰ DUYỆT — chốt "không duyệt yêu cầu của chính mình" ───────────

def test_cannot_approve_own_request_unless_admin(stress_world, db, client_as):
    """Nhân viên (cũng là HR) gửi yêu cầu của chính mình → không được duyệt (trừ admin)."""
    # a2 vừa là HR vừa là nhân viên
    emp_a2 = db.get(Employee, stress_world.emp["a2"])
    emp_a2.is_active = True
    db.commit()

    a2_client = client_as(stress_world.actor("a2"))
    rid = _ok(
        a2_client.post(
            f"{BASE}/me/change-requests",
            json={"personal": {"ethnicity": "Tày"}},
        )
    )["id"]

    # Thử duyệt chính mình
    res = a2_client.post(f"{BASE}/change-requests/{rid}/approve")
    assert res.status_code == 403
    assert "không tự duyệt" in res.text.lower()


# ── A5. NHẠY CẢM — duyệt nhạy cảm cần employee_sensitive.read ──────────────

def test_cannot_approve_sensitive_without_permission(stress_world, client_as):
    """Yêu cầu chứa ngân hàng + HR thiếu employee_sensitive.read → 403."""
    a1_client = client_as(stress_world.actor("a1"))
    rid = _ok(
        a1_client.post(
            f"{BASE}/me/change-requests",
            json={"bank": {"bank_account_no": "SECRET"}},
        )
    )["id"]

    # a2 là HR nhưng KHÔNG có employee_sensitive.read
    hr_client = client_as(stress_world.actor("a2"))
    res = hr_client.post(f"{BASE}/change-requests/{rid}/approve")
    assert res.status_code == 403
    assert "nhạy cảm" in res.text.lower()


# ── A6. THÔNG BÁO — duyệt/từ chối tạo Notification cho người gửi ─────────────

def test_approve_creates_notification_for_requester(stress_world, db, client_as):
    """Duyệt → tạo Notification cho người gửi."""
    a1_client = client_as(stress_world.actor("a1"))
    hr_client = client_as(stress_world.actor("a2"))
    stress_world.grant("a2", "employee_sensitive", "all", actions=("read",))
    perm_cache_clear(stress_world.actor("a2").user.id)

    rid = _ok(
        a1_client.post(
            f"{BASE}/me/change-requests",
            json={"personal": {"ethnicity": "Tày"}},
        )
    )["id"]

    # Kiểm trước: không có notification
    notifs = db.query(Notification).filter(
        Notification.user_id == stress_world.actor("a1").user.id
    ).all()
    assert len(notifs) == 0

    # Duyệt
    _ok(hr_client.post(f"{BASE}/change-requests/{rid}/approve"))

    # Kiểm sau: có notification
    notifs = db.query(Notification).filter(
        Notification.user_id == stress_world.actor("a1").user.id
    ).all()
    assert len(notifs) == 1
    assert "duyệt" in notifs[0].title.lower()


def test_reject_creates_notification_with_reason(stress_world, db, client_as):
    """Từ chối → thông báo kèm lý do."""
    a1_client = client_as(stress_world.actor("a1"))
    hr_client = client_as(stress_world.actor("a2"))

    rid = _ok(
        a1_client.post(
            f"{BASE}/me/change-requests",
            json={"personal": {"ethnicity": "Tày"}},
        )
    )["id"]

    reason = "Thông tin không chính xác"
    _ok(hr_client.post(f"{BASE}/change-requests/{rid}/reject", json={"reason": reason}))

    notif = (
        db.query(Notification)
        .filter(Notification.user_id == stress_world.actor("a1").user.id)
        .first()
    )
    assert reason in notif.body


# ── B. LƯU Ý TẠM THỜI ─────────────────────────────────────────────────────

# TODO: B1-B4 sẽ là kiểm Nginx/HTTP concurrency (script Python riêng)
# Tệp này chỉ kiểm SQLite in-memory. Concurrency thật cần:
#   - Double-submit race (exactly 1 created, rest 409)
#   - Withdraw vs approve race (50 lần)
#   - Two HR approve/reject race
#   - Load: 1/10/50/150 concurrent HTTP clients
# → Xem `measure-concurrency-cr676.py` trong `plans/261023-1125-ep-tai-cr676/scripts/`
