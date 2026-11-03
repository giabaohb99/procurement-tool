"""duoc-CR-717 giai đoạn 01 — PHÂN BỔ HÀNG LOẠT, XEM TRƯỚC, DANH SÁCH, PHẠM VI, ĐẾM TRUY VẤN.

Dùng chung khung với `test_nghi_phep_chinh_sach_cr717.py` (http · hr · make_type · make_policy).
"""
from datetime import date

import pytest
from sqlalchemy import event
from sqlalchemy.exc import OperationalError

from app.modules.employee.model import Employee
from app.modules.leave import balance_service, policy_assignment_service
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.policy_model import LeavePolicyAssignment
from test_nghi_phep_chinh_sach_cr717 import (assign_body, frozen_today, http, hr, make_policy,  # noqa: F401
                                             make_type, TODAY, YEAR)

BULK = "/api/leave-policy-assignments/bulk"
PREVIEW = "/api/leave-policy-assignments/preview"
LIST = "/api/leave-policy-assignments"


def _bulk_body(policy_id, ids, start="2026-07-01", **kw):
    body = {"policy_id": policy_id, "effective_from": start, "employee_ids": ids,
            "recalc_current_year": True, "close_previous": False}
    body.update(kw)
    return body


def _more_employees(db, world, n, company="A", dept="A.kt", prefix="E"):
    emps = [Employee(code=f"{prefix}{i:04d}", full_name=f"Người {prefix}{i}", company_id=world.co[company],
                     department_id=world.dept[dept], is_active=True) for i in range(n)]
    db.add_all(emps)
    db.flush()
    return emps


class _Counter:
    def __init__(self, db):
        self.engine, self.n = db.get_bind(), 0

    def _hit(self, *_a):
        self.n += 1

    def __enter__(self):
        event.listen(self.engine, "before_cursor_execute", self._hit)
        return self

    def __exit__(self, *_a):
        event.remove(self.engine, "before_cursor_execute", self._hit)


# ── Hàng loạt ────────────────────────────────────────────────────────────────────

def test_hang_loat_hai_tao_mot_bo_qua_co_ly_do(db, world, hr, http):
    lt = make_type(db)
    old, new = make_policy(db, "OLD", {lt.id: 20.0}), make_policy(db, "P15", {lt.id: 15.0})
    db.commit()
    assert http(hr.user, "POST", LIST, json=assign_body(world.emp["a1"], old.id, start="2026-01-01")).status_code == 200
    ids = [world.emp["a1"], world.emp["a3"], world.emp["b1"], world.emp["a3"]]   # a3 lặp: chỉ tính một lần
    r = http(hr.user, "POST", BULK, json=_bulk_body(new.id, ids))
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["created"] == 2
    assert len(data["skipped"]) == 1 and data["skipped"][0]["employee_id"] == world.emp["a1"]
    assert "Gói OLD" in data["skipped"][0]["reason"] and data["skipped"][0]["name"] == "Nhân sự a1"
    assert data["balances"]["created"] == 2 and data["balances"]["recalculated"] == []
    assert db.query(LeavePolicyAssignment).filter_by(policy_id=new.id).count() == 2
    rows = {b.employee_id: b.allocated_days for b in db.query(LeaveBalance).filter_by(year=YEAR).all()}
    #  a1 vẫn theo gói OLD (20), hai người mới được cấp theo gói P15 từ 01/07: (6×12+6×15)/12 = 13.5.
    assert rows[world.emp["a3"]] == rows[world.emp["b1"]] == 13.5
    assert world.emp["a1"] in rows


def test_hang_loat_tinh_lai_dong_co_san_va_bo_qua_tu_phan_bo(db, world, hr, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    a3 = db.get(Employee, world.emp["a3"])
    balance_service.ensure_balance(db, a3, YEAR, lt)
    db.commit()
    r = http(hr.user, "POST", BULK, json=_bulk_body(policy.id, [world.emp["a3"], world.emp["a2"]], start="2026-01-01"))
    data = r.json()["data"]
    assert data["created"] == 1 and data["balances"]["recalculated"] == [
        {"leave_type_id": lt.id, "before": 12.0, "after": 15.0, "employee_id": a3.id}]
    #  a2 là chính người bấm → bị bỏ qua (403 ở đường đơn lẻ, skipped ở hàng loạt).
    assert [s["employee_id"] for s in data["skipped"]] == [world.emp["a2"]]


def test_hang_loat_ngoai_pham_vi_vao_skipped(db, world, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    actor = world.grant("a3", "leave_balance", scope="all", actions=("read", "write"))
    world.grant("a3", "employee", scope="dept", actions=("read", "write"))
    db.commit()
    r = http(actor.user, "POST", BULK, json=_bulk_body(policy.id, [world.emp["a1"], world.emp["a3"], 99999]))
    data = r.json()["data"]
    assert data["created"] == 0 and {s["employee_id"] for s in data["skipped"]} == {
        world.emp["a1"], world.emp["a3"], 99999}
    assert db.query(LeavePolicyAssignment).count() == 0


def test_hang_loat_501_nguoi_422_va_rong_422(db, world, hr, http):
    policy = make_policy(db, "P", {})
    db.commit()
    assert http(hr.user, "POST", BULK, json=_bulk_body(policy.id, list(range(1, 502)))).status_code == 422
    assert http(hr.user, "POST", BULK, json=_bulk_body(policy.id, [])).status_code == 422
    assert http(hr.user, "POST", BULK, json=_bulk_body(9999, [world.emp["a1"]])).status_code == 404


def test_hang_loat_loi_csdl_cuon_ca_lo(db, world, hr, http, monkeypatch):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    db.commit()

    def boom(*args, **kw):
        raise OperationalError("INSERT", {}, Exception("chi tiết nội bộ không được lộ"))

    monkeypatch.setattr(policy_assignment_service, "reconcile_plan", boom)
    r = http(hr.user, "POST", BULK, json=_bulk_body(policy.id, [world.emp["a1"], world.emp["a3"], world.emp["b1"]]))
    assert r.status_code == 500
    assert "OperationalError" in r.text and "chi tiết nội bộ" not in r.text
    assert db.query(LeavePolicyAssignment).count() == 0      # chưa lưu gì


# ── Xem trước ────────────────────────────────────────────────────────────────────

def test_xem_truoc_khong_ghi_va_bao_xung_dot(db, world, hr, http):
    lt = make_type(db)
    old, new = make_policy(db, "OLD", {lt.id: 20.0}), make_policy(db, "P15", {lt.id: 15.0})
    a3 = db.get(Employee, world.emp["a3"])
    balance_service.ensure_balance(db, a3, YEAR, lt)
    db.commit()
    assert http(hr.user, "POST", LIST, json=assign_body(world.emp["a1"], old.id, start="2026-01-01")).status_code == 200
    n_assign, balances = db.query(LeavePolicyAssignment).count(), {
        b.id: (b.allocated_days, b.updated_by) for b in db.query(LeaveBalance).all()}

    body = {"policy_id": new.id, "effective_from": "2026-07-01",
            "employee_ids": [world.emp["a1"], world.emp["a3"], world.emp["a2"], world.emp["b1"]]}
    r = http(hr.user, "POST", PREVIEW, json=body)
    assert r.status_code == 200, r.text
    items = {i["employee_id"]: i for i in r.json()["data"]["items"]}
    assert items[world.emp["a1"]]["conflict"] == "overlap" and items[world.emp["a1"]]["changes"] == []
    assert items[world.emp["a1"]]["current"]["policy_name"] == "Gói OLD"
    assert items[world.emp["a2"]]["conflict"] == "self"
    assert items[world.emp["a3"]]["conflict"] is None
    assert items[world.emp["a3"]]["changes"] == [{"leave_type_id": lt.id, "before": 12.0, "after": 13.5}]
    assert items[world.emp["a3"]]["department_name"] == "Phòng Thu mua"
    assert items[world.emp["b1"]]["changes"] == [{"leave_type_id": lt.id, "before": 12.0, "after": 13.5}]   # chưa có dòng → số sẽ cấp
    #  Kết thúc chính sách cũ: a1 hết xung đột, số trước/sau tính theo gói mới thay gói cũ.
    r = http(hr.user, "POST", PREVIEW, json={**body, "close_previous": True, "employee_ids": [world.emp["a1"]]})
    only = r.json()["data"]["items"][0]
    assert only["conflict"] is None and only["changes"][0]["after"] == 17.5      # (6×20 + 6×15)/12 = 17.5
    #  Không ghi gì: số phân bổ và số dòng quỹ nguyên vẹn.
    assert db.query(LeavePolicyAssignment).count() == n_assign
    assert db.query(LeaveBalance).count() == len(balances)
    assert {b.id: (b.allocated_days, b.updated_by) for b in db.query(LeaveBalance).all()} == balances
    assert db.query(LeavePolicyAssignment).filter_by(policy_id=old.id).one().effective_to is None


def test_xem_truoc_chinh_sach_ngung_dung_va_bo_loc(db, world, hr, http):
    lt = make_type(db)
    off = make_policy(db, "OFF", {lt.id: 15.0}, active=False)
    on = make_policy(db, "ON", {lt.id: 15.0})
    old = make_policy(db, "OLD", {lt.id: 20.0})
    db.commit()
    r = http(hr.user, "POST", PREVIEW, json={"policy_id": off.id, "effective_from": "2026-07-01",
                                             "employee_ids": [world.emp["a3"]]})
    assert r.json()["data"]["items"][0]["conflict"] == "inactive"
    assert http(hr.user, "POST", LIST, json=assign_body(world.emp["a1"], old.id, start="2026-01-01")).status_code == 200
    base = {"policy_id": on.id, "effective_from": "2026-07-01", "company_id": world.co["A"]}
    ids = {i["employee_id"] for i in http(hr.user, "POST", PREVIEW, json=base).json()["data"]["items"]}
    assert world.emp["a1"] not in ids and world.emp["a3"] in ids           # mặc định bỏ người đang có phân bổ
    ids = {i["employee_id"] for i in http(hr.user, "POST", PREVIEW, json={**base, "only_without_active": False}
                                          ).json()["data"]["items"]}
    assert world.emp["a1"] in ids
    ids = {i["employee_id"] for i in http(hr.user, "POST", PREVIEW, json={**base, "department_id": world.dept["A.mua"]}
                                          ).json()["data"]["items"]}
    assert ids == {world.emp["a3"]}
    assert world.emp["b1"] not in {i["employee_id"] for i in http(hr.user, "POST", PREVIEW, json=base).json()["data"]["items"]}


def test_xem_truoc_tran_500_nguoi(db, world, hr, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    _more_employees(db, world, 510, company="B", dept="B.hc")
    db.commit()
    r = http(hr.user, "POST", PREVIEW, json={"policy_id": policy.id, "effective_from": "2026-07-01",
                                             "company_id": world.co["B"]})
    data = r.json()["data"]
    assert len(data["items"]) == 500 and data["total"] == 511 and data["truncated"] is True   # 510 + b1


def test_xem_truoc_so_truy_van_co_dinh(db, world, hr, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    old = make_policy(db, "OLD", {lt.id: 20.0})
    emps = _more_employees(db, world, 30)
    for emp in emps[:15]:
        balance_service.ensure_balance(db, emp, YEAR, lt)
    for emp in emps[15:20]:
        db.add(LeavePolicyAssignment(employee_id=emp.id, company_id=emp.company_id, policy_id=old.id,
                                     effective_from=date(2025, 1, 1)))
    db.commit()

    def count(ids):
        with _Counter(db) as c:
            r = http(hr.user, "POST", PREVIEW, json={"policy_id": policy.id, "effective_from": "2026-07-01",
                                                     "close_previous": True, "employee_ids": ids})
        assert r.status_code == 200
        return c.n

    count([emps[0].id])                                        # làm nóng bộ nhớ hồ sơ quyền
    assert count([emps[0].id]) == count([e.id for e in emps]) == count([e.id for e in emps[:7]])


def test_danh_sach_so_truy_van_co_dinh(db, world, hr, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    for emp in _more_employees(db, world, 30):
        db.add(LeavePolicyAssignment(employee_id=emp.id, company_id=emp.company_id, policy_id=policy.id,
                                     effective_from=date(2026, 1, 1)))
    db.commit()

    def count(size):
        with _Counter(db) as c:
            r = http(hr.user, "GET", LIST, params={"page_size": size})
        assert r.status_code == 200 and len(r.json()["data"]["items"]) == size
        return c.n

    count(1)
    assert count(1) == count(30)


# ── Danh sách + phạm vi ──────────────────────────────────────────────────────────

def test_danh_sach_loc_va_trang_thai(db, world, hr, http):
    lt = make_type(db)
    p1, p2 = make_policy(db, "P1", {lt.id: 15.0}), make_policy(db, "P2", {lt.id: 16.0})
    db.commit()
    for emp, policy, start, end in (("a1", p1, "2026-01-01", "2026-05-31"), ("a1", p2, "2026-06-01", None),
                                    ("a3", p1, "2026-09-01", None), ("b1", p1, "2025-01-01", "2025-12-31")):
        assert http(hr.user, "POST", LIST, json=assign_body(world.emp[emp], policy.id, start=start, end=end,
                                                            recalc_current_year=False)).status_code == 200
    items = http(hr.user, "GET", LIST).json()["data"]
    assert items["total"] == 4
    state = {(i["employee_code"], i["policy_name"]): i["state"] for i in items["items"]}
    assert state == {("A1", "Gói P1"): 3, ("A1", "Gói P2"): 2, ("A3", "Gói P1"): 1, ("B1", "Gói P1"): 3}
    got = lambda **p: {(i["employee_code"], i["policy_id"]) for i in  # noqa: E731
                       http(hr.user, "GET", LIST, params=p).json()["data"]["items"]}
    assert got(employee_id=world.emp["a1"]) == {("A1", p1.id), ("A1", p2.id)}
    assert got(policy_id=p2.id) == {("A1", p2.id)}
    assert got(company_id=world.co["B"]) == {("B1", p1.id)}
    assert got(active_on="2026-03-01") == {("A1", p1.id)}
    assert got(active_on=TODAY.isoformat()) == {("A1", p2.id)}
    assert got(search="a3") == {("A3", p1.id)} and got(search="NHân sự B1") == {("B1", p1.id)}
    assert got(search="không có ai tên vậy") == set()


def test_pham_vi_own_chi_thay_phan_bo_cua_minh(db, world, hr, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    db.commit()
    ids = {}
    for emp in ("a1", "a3", "b1"):
        r = http(hr.user, "POST", LIST, json=assign_body(world.emp[emp], policy.id, recalc_current_year=False))
        ids[emp] = r.json()["data"]["assignment"]["id"]
    viewer = world.grant("a1", "leave_balance", scope="own", actions=("read",))
    items = http(viewer.user, "GET", LIST).json()["data"]["items"]
    assert [i["employee_code"] for i in items] == ["A1"]
    assert http(viewer.user, "GET", f"{LIST}/{ids['a1']}").status_code == 200
    assert http(viewer.user, "GET", f"{LIST}/{ids['a3']}").status_code == 404     # gõ id vào URL vẫn 404
    #  Không có quyền ghi → không tạo / sửa / xóa được.
    assert http(viewer.user, "DELETE", f"{LIST}/{ids['a1']}").status_code == 403
    assert http(viewer.user, "POST", LIST, json=assign_body(world.emp["a3"], policy.id)).status_code == 403


def test_pham_vi_cong_ty_khong_thay_cong_ty_khac(db, world, hr, http):
    lt = make_type(db)
    policy = make_policy(db, "P15", {lt.id: 15.0})
    db.commit()
    for emp in ("a1", "b1"):
        assert http(hr.user, "POST", LIST, json=assign_body(world.emp[emp], policy.id,
                                                            recalc_current_year=False)).status_code == 200
    viewer = world.grant("a3", "leave_balance", scope="company", actions=("read", "write"))
    world.grant("a3", "employee", scope="company", actions=("read", "write"))
    assert {i["employee_code"] for i in http(viewer.user, "GET", LIST).json()["data"]["items"]} == {"A1"}
    b_assignment = db.query(LeavePolicyAssignment).filter_by(employee_id=world.emp["b1"]).one()
    assert http(viewer.user, "PATCH", f"{LIST}/{b_assignment.id}", json={"note": "x"}).status_code == 404
    assert http(viewer.user, "DELETE", f"{LIST}/{b_assignment.id}").status_code == 404
