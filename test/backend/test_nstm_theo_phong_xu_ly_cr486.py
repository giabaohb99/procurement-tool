"""bao-CR-486 — NSTM phụ trách đi theo PHÒNG XỬ LÝ của phiếu.

Đại ca soi dev 25/09/2026: YCBG của nhà máy (phòng xử lý = Dego Organic) mà ô «NSTM phụ trách»
liệt kê cả người thu mua chung. Giao diện đang lọc danh mục nhân sự theo TÊN phòng có chữ
«thu mua» — vừa lọt người ngoài, vừa lọt cả phòng «Sản xuất -Thu mua» vào mọi phiếu. Nay:
  · `assignable_staff(ticket)`: phòng xử lý ≠ 0 → người thu mua THUỘC phòng đó; = 0 → người
    bậc proc/all KHÔNG thuộc phòng tự mua nào. Hai đường API `/assignable-staff` cho YCMH · YCBG.
  · cửa ghi (`assign` YCMH, `set_line_assignee_` YCBG) chặn mã ngoài phòng xử lý; bỏ gán vẫn được.
"""
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.modules.category_assignee.service import assignable_staff, check_assignee_allowed
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.purchase_request import controller as pr_ctl
from app.modules.purchase_request import service as pr_service
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import AssignIn, AssignItemIn
from app.modules.role.model import Permission, Role
from app.modules.survey_request import controller as sr_ctl
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine
from app.modules.user.model import User, UserRole

_n = {"i": 0}


def _staff(db, seed, name: str, dept_id: int, scope: str | None) -> Employee:
    """Nhân sự ở phòng `dept_id`; `scope` ≠ None thì có tài khoản giữ vai trò thu mua bậc đó."""
    _n["i"] += 1
    emp = Employee(code=f"T486{_n['i']:02d}", full_name=name, company_id=seed.company_id,
                   department_id=dept_id, is_active=True)
    db.add(emp)
    db.flush()
    user = User(email=emp.code, employee_id=emp.id, password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    if scope:
        role = Role(code=f"R486{_n['i']:02d}", name="Vai trò test")
        db.add(role)
        db.flush()
        db.add(Permission(role_id=role.id, entity="purchase_request", scope=scope,
                          can_read=True, can_write=True))
        db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    return emp


@pytest.fixture
def world(db, seed):
    factory = Department(code="NM486", name="Nhà máy", company_id=seed.company_id, is_active=True)
    central = Department(code="TM486", name="Thu mua", company_id=seed.company_id, is_active=True)
    db.add_all([factory, central])
    db.flush()
    return SimpleNamespace(
        factory=factory.id, central=central.id,
        f_buyer=_staff(db, seed, "Thu mua nhà máy", factory.id, "dept_proc"),
        f_worker=_staff(db, seed, "Công nhân nhà máy", factory.id, None),
        c_buyer=_staff(db, seed, "Thu mua chung", central.id, "proc"),
        c_admin=_staff(db, seed, "Admin thu mua", central.id, "all"),
        outsider=_staff(db, seed, "Kế toán", 0, None),
    )


def _pr(db, seed, handler_dept_id: int, code: str) -> PurchaseRequest:
    pr = PurchaseRequest(code=code, company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="Nhà máy",
                         handler_dept_id=handler_dept_id, status="dispatched",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    db.add(PurchaseRequestItem(pr_id=pr.id, product_code="SP01", product_name="Hàng", item_group="Nhãn",
                               qty=1, unit="cái", price=1, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    db.refresh(pr)
    return pr


def test_factory_ticket_lists_only_factory_buyers(db, seed, world):
    pr = _pr(db, seed, world.factory, "PYC-486-NM")
    codes = [e.code for e in assignable_staff(db, pr)]
    assert codes == [world.f_buyer.code], "chỉ người THU MUA của phòng xử lý — không công nhân, không thu mua chung"


def test_central_ticket_lists_central_buyers_but_not_self_purchasing_departments(db, seed, world):
    pr = _pr(db, seed, 0, "PYC-486-TM")
    codes = {e.code for e in assignable_staff(db, pr)}
    assert codes == {world.c_buyer.code, world.c_admin.code}
    assert world.f_buyer.code not in codes, "nhà máy là phòng tự mua → không nằm trong bộ thu mua chung"


def test_inactive_and_role_less_people_never_show(db, seed, world):
    world.c_buyer.is_active = False
    db.commit()
    pr = _pr(db, seed, 0, "PYC-486-OFF")
    assert [e.code for e in assignable_staff(db, pr)] == [world.c_admin.code]


def test_write_gate_rejects_people_outside_the_handling_department(db, seed, world):
    factory_pr = _pr(db, seed, world.factory, "PYC-486-G1")
    check_assignee_allowed(db, factory_pr, world.f_buyer.code)
    check_assignee_allowed(db, factory_pr, world.f_worker.code)   # cùng phòng thì cửa ghi cho — luật LỎNG hơn gợi ý
    check_assignee_allowed(db, factory_pr, "")
    with pytest.raises(HTTPException) as e:
        check_assignee_allowed(db, factory_pr, world.c_buyer.code)
    assert e.value.status_code == 400 and "phòng xử lý" in e.value.detail

    central_pr = _pr(db, seed, 0, "PYC-486-G2")
    check_assignee_allowed(db, central_pr, world.c_buyer.code)
    check_assignee_allowed(db, central_pr, world.outsider.code)
    with pytest.raises(HTTPException) as e:
        check_assignee_allowed(db, central_pr, world.f_buyer.code)
    assert "phòng tự mua" in e.value.detail
    with pytest.raises(HTTPException):
        check_assignee_allowed(db, central_pr, "KHONG-CO-MA-NAY")


def test_pr_assign_endpoint_blocks_and_keeps_nothing_half_written(db, seed, world):
    pr = _pr(db, seed, world.factory, "PYC-486-AS")
    item = pr_service.items_of(db, pr.id)[0]
    with pytest.raises(HTTPException):
        pr_service.assign(db, pr.id, AssignIn(items=[AssignItemIn(id=item.id, assignee=world.c_buyer.code)]),
                          seed.u_nstm_id)
    db.refresh(item)
    assert not item.assignee
    pr_service.assign(db, pr.id, AssignIn(items=[AssignItemIn(id=item.id, assignee=world.f_buyer.code)]),
                      seed.u_nstm_id)
    db.refresh(item)
    assert item.assignee == world.f_buyer.code
    #  Gửi lại đúng người đang giữ (màn hình gửi cả bảng mỗi lần lưu) không bị kiểm lại.
    pr_service.assign(db, pr.id, AssignIn(items=[AssignItemIn(id=item.id, assignee=world.f_buyer.code)]),
                      seed.u_nstm_id)


def test_survey_line_assignee_endpoint_blocks_outsiders(db, seed, world, monkeypatch, cap_quyen):
    user = SimpleNamespace(id=seed.u_nstm_id)
    cap_quyen(user.id, "survey_request", scope="all", read=True, write=True)
    monkeypatch.setattr(sr_ctl, "_in_scope", lambda db, sid, u, action: None)
    monkeypatch.setattr(sr_ctl, "_notify", lambda *a, **kw: None)
    s = SurveyRequest(code="YCBG-486", company_id=seed.company_id, requester="Người YC",
                      requester_id=seed.emp_req_id, department="Nhà máy", handler_dept_id=world.factory,
                      status="processing", created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(s)
    db.flush()
    ln = SurveyRequestLine(survey_request_id=s.id, request_qty=1, uom="kg",
                           created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(ln)
    db.commit()

    with pytest.raises(HTTPException) as e:
        sr_ctl.set_line_assignee_(s.id, ln.id, {"assignee": world.c_buyer.code}, BackgroundTasks(),
                                  db=db, user=user)
    assert e.value.status_code == 400
    sr_ctl.set_line_assignee_(s.id, ln.id, {"assignee": world.f_buyer.code}, BackgroundTasks(),
                              db=db, user=user)
    db.refresh(ln)
    assert ln.assignee == world.f_buyer.code


def test_assignable_staff_endpoints_return_the_same_list(db, seed, world, monkeypatch):
    user = SimpleNamespace(id=seed.u_nstm_id)
    pr = _pr(db, seed, world.factory, "PYC-486-EP")
    monkeypatch.setattr(pr_ctl, "_in_scope", lambda db, pid, u, action: pr)
    out = pr_ctl.assignable_staff_(pr.id, db=db, user=user)
    import json
    items = json.loads(out.body)["data"]["items"]
    assert [i["code"] for i in items] == [world.f_buyer.code]
    assert items[0]["department_id"] == world.factory
