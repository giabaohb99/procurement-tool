"""duoc-CR-717 — bài kiểm cho các điểm code-review backend (H1, H2, M1–M4, L1–L6).

Khung dùng chung (http · hr · make_type · make_policy · assign_body) nhập từ `test_nghi_phep_chinh_sach_cr717.py`.
SQLite KHÔNG tái hiện được REPEATABLE READ — H1 / L4 chứng minh bằng cách soi câu SQL biên dịch sang MySQL có khóa.
"""
import uuid
from datetime import date

import pytest
from pydantic import ValidationError
from sqlalchemy import event
from sqlalchemy.dialects import mysql
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.request_context import RequestContext, reset_context, set_context
from app.modules.employee.model import Employee
from app.modules.leave import accrual_service, balance_service, policy_allocation, policy_assignment_service
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.constants import LeaveAccrualMode
from app.modules.leave.policy_allocation_math import AssignmentSpan, compute_allocated
from app.modules.leave.policy_assignment_scope import writable_employee_query
from app.modules.leave.policy_model import LeavePolicy, LeavePolicyAssignment, LeavePolicyLine
from app.modules.leave.policy_schema import AssignmentUpdate, PolicyUpdate
from app.core.auth import get_perm_profile
from app.core.scoping import get_scoped
from test_nghi_phep_chinh_sach_cr717 import (assign_body, frozen_today, http, hr, make_policy,  # noqa: F401
                                             make_type, TODAY, YEAR)
from test_nghi_phep_phan_bo_hang_loat_cr717 import _Counter, _bulk_body, _more_employees

LIST = "/api/leave-policy-assignments"
BULK = f"{LIST}/bulk"
PREVIEW = f"{LIST}/preview"
POLICIES = "/api/leave-policies"
FULL, PRORATA, MONTHLY = (int(LeaveAccrualMode.FULL_YEAR), int(LeaveAccrualMode.PRORATA_HIRE),
                          int(LeaveAccrualMode.MONTHLY))


@pytest.fixture
def mysql_view(db, monkeypatch):
    """Bật khóa hàng ở SQLite (SQLite bỏ qua `FOR UPDATE`) và ghi lại mọi SELECT dưới dạng SQL MySQL."""
    monkeypatch.setattr(policy_allocation, "ROW_LOCK_DIALECTS", ("sqlite",))
    seen: list[str] = []

    def spy(state):
        if state.is_select:
            seen.append(str(state.statement.compile(dialect=mysql.dialect())))

    event.listen(db, "do_orm_execute", spy)
    yield seen
    event.remove(db, "do_orm_execute", spy)


def _selects(seen, table):
    """SELECT trên `table` TRƯỚC commit — bỏ các lần nạp lại thuộc tính hết hạn sau commit (`WHERE <bảng>.id = %s`, không LIMIT)."""
    return [sql for sql in seen if f"FROM {table} " in sql
            and not (f"WHERE {table}.id = %s" in sql and "LIMIT" not in sql)]


def _locked(sql):
    return "FOR UPDATE" in sql or "SHARE MODE" in sql or "FOR SHARE" in sql


# ═════════════════ H1 — đọc có khóa trên mọi đường ghi ═════════════════

def test_h1_with_row_lock_bien_dich_sang_mysql_co_khoa(db):
    from types import SimpleNamespace
    fake_mysql = SimpleNamespace(bind=SimpleNamespace(dialect=SimpleNamespace(name="mysql")))
    query = db.query(LeavePolicyAssignment).filter(LeavePolicyAssignment.employee_id.in_([1, 2]))
    shared = str(policy_allocation.with_row_lock(fake_mysql, query).statement.compile(dialect=mysql.dialect()))
    assert "SHARE MODE" in shared.upper() or "FOR SHARE" in shared.upper()
    exclusive = str(policy_allocation.with_row_lock(fake_mysql, query, exclusive=True).statement.compile(
        dialect=mysql.dialect()))
    assert "FOR UPDATE" in exclusive.upper()
    #  SQLite giữ nguyên câu (không có khóa hàng).
    assert policy_allocation.with_row_lock(db, query) is query


def test_h1_tao_va_hang_loat_doc_phan_bo_va_dong_goi_co_khoa(db, world, hr, http, mysql_view):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    db.commit()
    mysql_view.clear()
    assert http(hr.user, "POST", LIST, json=assign_body(world.emp["a1"], policy.id)).status_code == 200
    for table in ("tab_leave_policy_assignment", "tab_leave_policy_line"):
        reads = _selects(mysql_view, table)
        assert reads and all(_locked(sql) for sql in reads), (table, reads)   # tạo một người
    #  Dòng gói bị khóa DÙNG CHUNG (chặn "xóa gói" chen giữa); lần đọc thường của controller đi trước là để trả 404 sớm.
    assert any("SHARE" in sql for sql in _selects(mysql_view, "tab_leave_policy"))
    assert any("FOR UPDATE" in sql for sql in _selects(mysql_view, "tab_leave_balance"))
    mysql_view.clear()
    r = http(hr.user, "POST", BULK, json=_bulk_body(policy.id, [world.emp["a3"], world.emp["b1"]]))
    assert r.status_code == 200, r.text
    for table in ("tab_leave_policy_assignment", "tab_leave_policy_line"):
        reads = _selects(mysql_view, table)
        assert reads and all(_locked(sql) for sql in reads), (table, reads)   # hàng loạt
    balance_locks = [sql for sql in _selects(mysql_view, "tab_leave_balance") if "FOR UPDATE" in sql]
    assert len(balance_locks) == 1                                            # MỘT câu khóa mọi dòng quỹ


def test_h1_sua_va_xoa_doc_lai_phan_bo_co_khoa(db, world, hr, http, mysql_view):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    db.commit()
    aid = http(hr.user, "POST", LIST, json=assign_body(world.emp["a1"], policy.id)).json()["data"]["assignment"]["id"]
    mysql_view.clear()
    assert http(hr.user, "PATCH", f"{LIST}/{aid}", json={"effective_to": "2026-12-31"}).status_code == 200
    reads = _selects(mysql_view, "tab_leave_policy_assignment")
    assert len(reads) >= 3 and all(_locked(sql) for sql in reads[1:]), reads   # [0] = get_scoped trước khóa nhân sự
    mysql_view.clear()
    assert http(hr.user, "DELETE", f"{LIST}/{aid}", params={"recalc_current_year": "true"}).status_code == 200
    reads = _selects(mysql_view, "tab_leave_policy_assignment")
    assert len(reads) >= 2 and all(_locked(sql) for sql in reads[1:]), reads


def test_l4_xoa_goi_khoa_doc_quyen_dong_goi_va_doc_phan_bo_co_khoa(db, world, hr, http, mysql_view):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    db.commit()
    mysql_view.clear()
    assert http(hr.user, "DELETE", f"{POLICIES}/{policy.id}").status_code == 200
    gate = [sql for sql in _selects(mysql_view, "tab_leave_policy") if "FOR UPDATE" in sql]
    assert gate, mysql_view
    assignments = _selects(mysql_view, "tab_leave_policy_assignment")
    assert assignments and all(_locked(sql) for sql in assignments)


def test_l4_tao_phan_bo_cho_goi_da_xoa_la_404(db, world, hr):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    emp = db.get(Employee, world.emp["a1"])
    db.delete(policy)
    db.flush()
    with pytest.raises(Exception) as exc:
        policy_assignment_service.create_one(db, hr.user, emp, policy, date(2026, 7, 1), None, "", True, False,
                                             YEAR, TODAY, actor_employee_id=0, actor_is_admin=True)
    assert getattr(exc.value, "status_code", 0) == 404


# ═════════════════ H2 — phạm vi GHI quỹ ═════════════════

def _company_hr(world, db, scope="company"):
    """Người giữ `employee.read = all` (vai trò khác) nhưng chỉ GHI quỹ phép trong phạm vi công ty mình."""
    actor = world.grant("a3", "leave_balance", scope=scope, actions=("read", "write"))
    world.grant("a3", "employee", scope="all", actions=("read",))
    db.commit()
    return actor


def test_h2_tao_ngoai_pham_vi_ghi_quy_404(db, world, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    actor = _company_hr(world, db)
    assert http(actor.user, "POST", LIST, json=assign_body(world.emp["b1"], policy.id)).status_code == 404
    assert db.query(LeavePolicyAssignment).count() == 0
    assert db.query(LeaveBalance).count() == 0
    assert http(actor.user, "POST", LIST, json=assign_body(world.emp["a1"], policy.id)).status_code == 200


def test_h2_hang_loat_va_xem_truoc_cung_mot_chot(db, world, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    actor = _company_hr(world, db)
    data = http(actor.user, "POST", BULK, json=_bulk_body(policy.id, [world.emp["a1"], world.emp["b1"]])).json()["data"]
    assert data["created"] == 1
    assert [s["employee_id"] for s in data["skipped"]] == [world.emp["b1"]] and data["skipped"][0]["reason"]
    assert db.query(LeavePolicyAssignment).filter_by(employee_id=world.emp["b1"]).count() == 0
    items = http(actor.user, "POST", PREVIEW, json={"policy_id": policy.id, "effective_from": "2026-09-01",
                                                    "employee_ids": [world.emp["a2"], world.emp["b1"]]}
                 ).json()["data"]["items"]
    by_id = {i["employee_id"]: i for i in items}
    assert by_id[world.emp["b1"]]["conflict"] == "scope" and by_id[world.emp["b1"]]["conflict_message"]
    assert by_id[world.emp["a2"]]["conflict"] is None
    #  Chọn theo bộ lọc công ty B: không ai nằm trong phạm vi ghi.
    only = http(actor.user, "POST", PREVIEW, json={"policy_id": policy.id, "effective_from": "2026-09-01",
                                                   "company_id": world.co["B"]}).json()["data"]
    assert only["items"] == [] and only["total"] == 0


def test_h2_admin_khong_bi_chan(db, world, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    actor = world.grant("a3", "leave_balance", scope="all", actions=("read", "write"), role_code="admin")
    world.grant("a3", "employee", scope="all", actions=("read",))
    db.commit()
    assert http(actor.user, "POST", LIST, json=assign_body(world.emp["b1"], policy.id)).status_code == 200


@pytest.mark.parametrize("kind", ["company", "own", "all", "exc_company", "inc_company_only"])
def test_h2_dieu_kien_khop_get_scoped(db, world, kind):
    """Điều kiện dựng trên cột hồ sơ phải CHO KẾT QUẢ y hệt `get_scoped(phân bổ, leave_balance, write)` về sau."""
    policy = make_policy(db, "P", {})
    for key in ("a1", "a3", "b1"):
        emp = db.get(Employee, world.emp[key])
        db.add(LeavePolicyAssignment(employee_id=emp.id, company_id=emp.company_id, policy_id=policy.id,
                                     effective_from=date(2026, 1, 1)))
    kw = {"exc_company": dict(exc_company=["B"]), "inc_company_only": dict(inc_company=["A"])}.get(kind, {})
    scope = {"exc_company": "all", "inc_company_only": "all"}.get(kind, kind)
    actor = world.grant("a3", "leave_balance", scope=scope, actions=("read", "write"), **kw)
    world.grant("a3", "employee", scope="all", actions=("read",))
    db.commit()
    profile = get_perm_profile(db, actor.user)
    allowed = {e.id for e in writable_employee_query(db, actor.user).all()}
    for key in ("a1", "a3", "b1"):
        row = db.query(LeavePolicyAssignment).filter_by(employee_id=world.emp[key]).one()
        in_scope = get_scoped(db, LeavePolicyAssignment, "leave_balance", row.id, actor.user, profile, "write")
        assert (world.emp[key] in allowed) == (in_scope is not None), (kind, key)


# ═════════════════ M1 — D5 áp cho sửa / xóa ═════════════════

def test_m1_sua_xoa_phan_bo_cua_chinh_minh_403_admin_qua(db, world, hr, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    emp = db.get(Employee, world.emp["a2"])
    mine = LeavePolicyAssignment(employee_id=emp.id, company_id=emp.company_id, policy_id=policy.id,
                                 effective_from=date(2026, 1, 1))
    db.add(mine)
    db.commit()
    assert http(hr.user, "PATCH", f"{LIST}/{mine.id}", json={"effective_to": "2026-12-31"}).status_code == 403
    assert http(hr.user, "DELETE", f"{LIST}/{mine.id}").status_code == 403
    assert db.query(LeavePolicyAssignment).filter_by(id=mine.id).one().effective_to is None
    #  Của người khác vẫn sửa được.
    other = db.get(Employee, world.emp["a3"])
    theirs = LeavePolicyAssignment(employee_id=other.id, company_id=other.company_id, policy_id=policy.id,
                                   effective_from=date(2026, 1, 1))
    db.add(theirs)
    db.commit()
    assert http(hr.user, "PATCH", f"{LIST}/{theirs.id}", json={"note": "x"}).status_code == 200
    world.grant("a2", "leave_balance", scope="all", actions=("write",), role_code="admin")
    assert http(hr.user, "PATCH", f"{LIST}/{mine.id}", json={"effective_to": "2026-12-31"}).status_code == 200
    assert http(hr.user, "DELETE", f"{LIST}/{mine.id}").status_code == 200


# ═════════════════ M2 — phân bổ phủ các tháng trước ngày vào làm ═════════════════

def _span(start, end, days, type_id=1):
    return AssignmentSpan(start, end, {type_id: days})


@pytest.mark.parametrize("start", [date(2026, 10, 1), date(2026, 10, 16), date(2026, 7, 1), date(2026, 1, 1)])
def test_m2_full_year_phan_bo_tu_ngay_vao_lam_ra_so_cua_goi(start):
    hire = date(2026, 10, 1)
    assert compute_allocated(12.0, FULL, hire, YEAR, [_span(start, None, 15.0)], 1) == 15.0
    assert compute_allocated(12.0, FULL, hire, YEAR, [_span(start, None, 0.0)], 1) == 0.0     # gói thử việc 0 ngày


@pytest.mark.parametrize("mode", [PRORATA, MONTHLY])
def test_m2_prorata_va_monthly_chia_theo_thang_lam_viec_tu_so_cua_goi(mode):
    hire = date(2026, 10, 1)
    expected = accrual_service.prorate_allocation(15.0, mode, hire, YEAR)
    assert compute_allocated(12.0, mode, hire, YEAR, [_span(date(2026, 10, 1), None, 15.0)], 1) == expected
    assert compute_allocated(12.0, mode, hire, YEAR, [_span(date(2026, 10, 16), None, 15.0)], 1) == expected


def test_m2_phan_bo_sau_thang_vao_lam_khong_keo_lui():
    hire, span = date(2026, 3, 1), _span(date(2026, 7, 1), None, 24.0)       # tháng 1-6 vẫn theo luật loại
    assert compute_allocated(12.0, FULL, hire, YEAR, [span], 1) == accrual_service.round_half_up((6 * 12 + 6 * 24) / 12)


def test_m2_keo_lui_khong_lan_vao_phan_bo_truoc_do():
    hire = date(2026, 3, 1)
    spans = [_span(date(2026, 1, 1), date(2026, 2, 28), 20.0), _span(date(2026, 3, 5), None, 15.0)]
    assert compute_allocated(12.0, FULL, hire, YEAR, spans, 1) == accrual_service.round_half_up((2 * 20 + 10 * 15) / 12)


def test_m2_cap_quy_that_qua_api(db, world, hr, http):
    lt = make_type(db, accrual_mode=FULL)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    emp = db.get(Employee, world.emp["a3"])
    emp.hire_date = date(2026, 6, 1)
    db.commit()
    r = http(hr.user, "POST", LIST, json=assign_body(world.emp["a3"], policy.id, start="2026-06-01"))
    assert r.status_code == 200, r.text
    row = db.query(LeaveBalance).filter_by(employee_id=emp.id, year=YEAR, leave_type_id=lt.id).one()
    assert row.allocated_days == 15.0


# ═════════════════ M3 — không savepoint: lô lỗi không để lại nhật ký ma ═════════════════

def test_m3_bulk_loi_khong_de_lai_change_log_ma(db, world, hr, monkeypatch):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    emps = [db.get(Employee, world.emp[k]) for k in ("a1", "a3", "b1")]
    db.commit()
    calls = {"nested": 0}
    real_nested = db.begin_nested
    monkeypatch.setattr(db, "begin_nested", lambda *a, **k: (calls.__setitem__("nested", calls["nested"] + 1),
                                                              real_nested(*a, **k))[1])
    ctx = RequestContext(request_id=uuid.uuid4().bytes, user_id=hr.user.id)
    token = set_context(ctx)
    try:
        def boom(*a, **k):
            raise OperationalError("INSERT", {}, Exception("deadlock"))

        monkeypatch.setattr(policy_assignment_service, "reconcile_plan", boom)
        with pytest.raises(OperationalError):
            policy_assignment_service.create_bulk(db, hr.user, emps, policy, date(2026, 7, 1), None, True, False,
                                                  YEAR, TODAY, actor_employee_id=0, actor_is_admin=True)
        assert any(e.row_id is not None for e in ctx.changes)     # bộ theo dõi đang chạy (đã gom thay đổi)
        db.rollback()
        assert ctx.changes == []                                  # quay đầu → không dòng nào được đóng dấu
    finally:
        reset_context(token)
    assert calls["nested"] == 0 and db.query(LeavePolicyAssignment).count() == 0


# ═════════════════ M4 — số truy vấn đường ghi hàng loạt không tăng theo số người ═════════════════

def _statements(db, call):
    """Chạy `call()` và trả danh sách câu SQL đã chạy."""
    seen: list[str] = []

    def hit(_conn, _cursor, statement, *_rest):
        seen.append(statement.lstrip()[:6].upper())

    engine = db.get_bind()
    event.listen(engine, "before_cursor_execute", hit)
    try:
        call()
    finally:
        event.remove(engine, "before_cursor_execute", hit)
    return seen


def test_m4_bulk_ghi_so_cau_doc_va_khoa_co_dinh(db, world, hr, http):
    """Đọc / khóa: số câu SELECT KHÔNG tăng theo số người. Ghi: mỗi dòng ORM mới / sửa là một câu INSERT / UPDATE
    (lấy khóa chính tự tăng + `updated_at` là biểu thức SQL nên ORM không gộp được) — chặn trần tuyến tính nhỏ."""
    lt, lt2 = make_type(db), make_type(db, "sick", annual_quota_days=6.0)
    policy = make_policy(db, "P15", {lt.id: 15.0, lt2.id: 8.0})
    groups = {n: _more_employees(db, world, n, prefix=f"G{n}_") for n in (1, 2, 9, 25)}
    for emps in groups.values():
        for emp in emps[::2]:                                  # nửa số người đã có dòng quỹ (tính lại), nửa chưa (cấp mới)
            balance_service.ensure_balance(db, emp, YEAR, lt)
    db.commit()
    ids = {n: [e.id for e in emps] for n, emps in groups.items()}     # nạp lại thuộc tính hết hạn TRƯỚC khi đếm

    def run(n):
        def call():
            r = http(hr.user, "POST", BULK, json=_bulk_body(policy.id, ids[n]))
            assert r.status_code == 200 and r.json()["data"]["created"] == n, r.text
        return _statements(db, call)

    run(1)                                                     # làm nóng bộ nhớ hồ sơ quyền
    runs = {n: run(n) for n in (2, 9, 25)}
    reads = {n: statements.count("SELECT") for n, statements in runs.items()}
    assert reads[2] == reads[9] == reads[25], reads
    for n, statements in runs.items():
        writes = len(statements) - reads[n]
        assert writes <= 5 * n + 10, (n, writes)
    rows = db.query(LeaveBalance).filter(LeaveBalance.employee_id.in_(ids[25]), LeaveBalance.year == YEAR).all()
    assert len(rows) == 50 and {r.allocated_days for r in rows if r.leave_type_id == lt.id} == {13.5}


# ═════════════════ L1 — chỉ nhân sự đang làm ═════════════════

def test_l1_nguoi_da_nghi_viec_404_va_skipped(db, world, hr, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    db.get(Employee, world.emp["a3"]).is_active = False
    db.commit()
    assert http(hr.user, "POST", LIST, json=assign_body(world.emp["a3"], policy.id)).status_code == 404
    data = http(hr.user, "POST", BULK, json=_bulk_body(policy.id, [world.emp["a3"], world.emp["a1"]])).json()["data"]
    assert data["created"] == 1 and [s["employee_id"] for s in data["skipped"]] == [world.emp["a3"]]
    assert db.query(LeaveBalance).filter_by(employee_id=world.emp["a3"]).count() == 0


# ═════════════════ L2 — thay dòng gói: audit giữ số cũ, PUT vỡ UNIQUE → 409 ═════════════════

def test_l2_thay_dong_audit_giu_so_cu_va_moi(db, world, hr, http):
    from app.modules.audit.model import AuditLog
    lt = make_type(db)
    policy = make_policy(db, "P", {lt.id: 12.0})
    db.commit()
    r = http(hr.user, "PUT", f"{POLICIES}/{policy.id}/lines",
             json={"items": [{"leave_type_id": lt.id, "annual_days": 15}]})
    assert r.status_code == 200, r.text
    msg = db.query(AuditLog).filter_by(entity="leave_type", entity_id=policy.id).order_by(AuditLog.id.desc()).first().message
    assert "trước" in msg and f"{lt.name}: 12" in msg and f"{lt.name}: 15" in msg


def test_l2_put_dong_dong_thoi_vo_unique_tra_409(db, world, hr, http, monkeypatch):
    lt = make_type(db)
    policy = make_policy(db, "P", {lt.id: 12.0})
    db.commit()

    def clash():
        raise IntegrityError("INSERT", {}, Exception("uq_policy_type"))

    monkeypatch.setattr(db, "commit", clash)
    r = http(hr.user, "PUT", f"{POLICIES}/{policy.id}/lines", json={"items": [{"leave_type_id": lt.id, "annual_days": 15}]})
    assert r.status_code == 409
    monkeypatch.undo()
    assert [l.annual_days for l in db.query(LeavePolicyLine).filter_by(policy_id=policy.id)] == [12.0]   # đã quay đầu


# ═════════════════ L3 — PATCH không nhận null cho cột NOT NULL ═════════════════

@pytest.mark.parametrize("field", ["name", "note", "is_active"])
def test_l3_policy_update_chan_null(field):
    with pytest.raises(ValidationError):
        PolicyUpdate(**{field: None})
    assert PolicyUpdate().model_dump(exclude_unset=True) == {}


def test_l3_assignment_update_chan_null_nhung_cho_effective_to_null():
    with pytest.raises(ValidationError):
        AssignmentUpdate(note=None)
    assert AssignmentUpdate(effective_to=None).model_dump(exclude_unset=True) == {"effective_to": None}


def test_l3_patch_name_null_422(db, world, hr, http):
    policy = make_policy(db, "P", {})
    db.commit()
    assert http(hr.user, "PATCH", f"{POLICIES}/{policy.id}", json={"name": None}).status_code == 422
    assert http(hr.user, "PATCH", f"{POLICIES}/{policy.id}", json={"is_active": None}).status_code == 422
    assert http(hr.user, "PATCH", f"{POLICIES}/{policy.id}", json={"name": "Tên mới"}).status_code == 200


# ═════════════════ L5 — hồ sơ nhân sự mất ═════════════════

def test_l5_sua_phan_bo_khi_ho_so_mat_404_nhung_xoa_duoc(db, world, hr, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    ghost = Employee(code="GHOST", full_name="Ghost", company_id=world.co["A"], department_id=world.dept["A.kt"],
                     is_active=True)
    db.add(ghost)
    db.flush()
    for start in ("2026-01-01", "2026-03-01"):
        db.add(LeavePolicyAssignment(employee_id=ghost.id, company_id=ghost.company_id, policy_id=policy.id,
                                     effective_from=date.fromisoformat(start),
                                     effective_to=date(2026, 2, 28) if start == "2026-01-01" else None))
    db.commit()
    first = db.query(LeavePolicyAssignment).filter_by(employee_id=ghost.id).order_by(
        LeavePolicyAssignment.effective_from).first()
    db.delete(ghost)
    db.commit()
    #  Kéo dài lượt đầu sẽ chồng lượt hai — không có hồ sơ cũng KHÔNG được lọt.
    assert http(hr.user, "PATCH", f"{LIST}/{first.id}", json={"effective_to": None}).status_code == 404
    assert db.query(LeavePolicyAssignment).filter_by(id=first.id).one().effective_to == date(2026, 2, 28)
    assert http(hr.user, "DELETE", f"{LIST}/{first.id}").status_code == 200


# ═════════════════ L6 — tìm kiếm ═════════════════

def test_l6_search_co_tran_do_dai_va_loc_trong_sql(db, world, hr, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    db.commit()
    assert http(hr.user, "POST", LIST, json=assign_body(world.emp["a3"], policy.id, recalc_current_year=False)).status_code == 200
    assert http(hr.user, "GET", LIST, params={"search": "x" * 101}).status_code == 422
    seen: list[str] = []

    def spy(state):
        if state.is_select:
            seen.append(str(state.statement.compile(dialect=mysql.dialect())))

    event.listen(db, "do_orm_execute", spy)
    try:
        r = http(hr.user, "GET", LIST, params={"search": "a3"})
    finally:
        event.remove(db, "do_orm_execute", spy)
    assert [i["employee_code"] for i in r.json()["data"]["items"]] == ["A3"]
    #  Không còn câu nạp cả bảng nhân sự (SELECT id, full_name, code không WHERE).
    assert not [s for s in seen if "FROM tab_employee" in s and "WHERE" not in s and "full_name" in s and "JOIN" not in s]
    assert any("LIKE" in s for s in seen)
    #  `%` người gõ là chữ thường, không phải ký tự đại diện.
    assert http(hr.user, "GET", LIST, params={"search": "%"}).json()["data"]["items"] == []
