"""duoc-CR-656 (D1c) — tải đang ôm tính tức thì: từng nguồn đúng số, loại trừ đúng, ≤ 10 truy vấn, mặc định an toàn, API chỉ quản trị."""
import itertools
import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.subject_match import SUBJECT_ROLE
from app.main import app
from app.modules.approval.delegation_model import Delegation
from app.modules.approval.instance_model import (INSTANCE_RUNNING, TASK_PENDING, ApprovalInstance,
                                                 ApprovalTask)
from app.modules.capability import workload_service as wl
from app.modules.document.model import Document, STATUS_PENDING_ISSUE
from app.modules.leave.request_model import LeaveRequest
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine
from app.modules.work.task_model import WorkTask, WorkTaskAssignee

from ho_so_lam_viec_factory import make_company, make_dept, make_person
from lich_lam_viec_factory import count_queries

_ENTITY_IDS = itertools.count(1)       # mỗi phiên duyệt một chứng từ riêng (ràng buộc một phiên chạy / chứng từ)
NOW = datetime(2026, 10, 20, 3, 0)           # 10:00 VN thứ Ba 20/10/2026
TODAY = date(2026, 10, 20)


@pytest.fixture
def world(db):
    co = make_company(db, "C1")
    d1, d2 = make_dept(db, co, "D1"), make_dept(db, co, "D2")
    people = {}
    for code, dept in (("A", d1), ("B", d1), ("C", d2)):
        user, emp = make_person(db, code, co, dept)
        people[code] = emp
    db.commit()
    return type("W", (), dict(co=co, d1=d1, d2=d2, **{k.lower(): v for k, v in people.items()}))


def by_code(rows):
    return {r["employee_code"]: r for r in rows}


def approval(db, assignee, entity="purchase_request", due=None, status=TASK_PENDING, inst_status=INSTANCE_RUNNING):
    inst = ApprovalInstance(entity=entity, entity_id=next(_ENTITY_IDS), flow_id=1, status=inst_status)
    db.add(inst)
    db.flush()
    db.add(ApprovalTask(instance_id=inst.id, assignee_employee_id=assignee, status=status, due_at=due))


def work(db, pic, status=1, due="", est=None, deleted=None, kind=1):
    t = WorkTask(list_id=1, title="x", status=status, due_date=due, estimate_hours=est, deleted_at=deleted)
    db.add(t)
    db.flush()
    db.add(WorkTaskAssignee(task_id=t.id, employee_id=pic, kind=kind))


def test_khong_truyen_pham_vi_thi_khong_tra_gi_va_khong_dung_db(db, world):
    _, queries = count_queries(db, lambda: wl.current_load(db, now=NOW))
    assert wl.current_load(db, now=NOW) == [] and queries == []


def test_duyet_dang_cho_va_qua_han_chi_tinh_phien_con_mo(db, world):
    approval(db, world.a.id, due=NOW - timedelta(hours=1))                     # quá hạn
    approval(db, world.a.id, due=NOW + timedelta(hours=5))
    approval(db, world.a.id, status=3)                                         # đã quyết
    approval(db, world.a.id, inst_status=3)                                    # phiên đã đóng mà việc còn treo
    db.commit()
    a = by_code(wl.current_load(db, company_id=world.co.id, now=NOW))["A"]
    assert (a["approvals_pending"], a["approvals_overdue"]) == (2, 1)


def test_viec_du_an_chi_tinh_pic_dang_mo_chua_xoa_mem_va_cong_gio_uoc_luong(db, world):
    work(db, world.a.id, due="2026-10-19", est=3)                              # quá hạn
    work(db, world.a.id, due="2026-10-20", est=2.5)                            # hạn hôm nay: CHƯA quá hạn
    work(db, world.a.id, status=2)                                             # đã xong
    work(db, world.a.id, status=3)                                             # đã hủy
    work(db, world.a.id, deleted=NOW)                                          # xóa mềm
    work(db, world.a.id, kind=2)                                               # người theo dõi
    db.commit()
    a = by_code(wl.current_load(db, company_id=world.co.id, now=NOW))["A"]
    assert (a["work_open"], a["work_overdue"], a["work_estimate_hours_open"]) == (2, 1, 5.5)


def test_uy_quyen_tinh_o_nguoi_uy_quyen_va_nguoi_nhan_thay_so_rieng(db, world):
    approval(db, world.a.id, entity="purchase_request", due=NOW - timedelta(hours=1))
    approval(db, world.a.id, entity="document")
    db.add_all([
        Delegation(from_employee_id=world.a.id, to_employee_id=world.b.id, entity="", from_date=TODAY, to_date=TODAY + timedelta(days=3)),
        Delegation(from_employee_id=world.a.id, to_employee_id=world.c.id, entity="document", from_date=TODAY, to_date=TODAY),
        Delegation(from_employee_id=world.a.id, to_employee_id=world.c.id, entity="", from_date=TODAY - timedelta(days=9),
                   to_date=TODAY - timedelta(days=1)),                          # hết hạn
        Delegation(from_employee_id=world.a.id, to_employee_id=world.c.id, entity="", from_date=TODAY, to_date=TODAY, is_active=False),
    ])
    db.commit()
    rows = by_code(wl.current_load(db, company_id=world.co.id, now=NOW))
    assert rows["A"]["approvals_pending"] == 2 and rows["A"]["delegated_out_to"] == [world.b.id, world.c.id]
    assert (rows["B"]["delegated_in"], rows["B"]["delegated_in_overdue"]) == (2, 1)       # ủy quyền mọi loại
    assert rows["C"]["delegated_in"] == 1                                                  # chỉ loại `document`
    assert rows["B"]["approvals_pending"] == 0 and rows["B"]["open_items_total"] == 0      # KHÔNG cộng trùng vào tổng


def test_uy_quyen_tu_nguoi_ngoai_pham_vi_van_duoc_dem(db, world):
    approval(db, world.c.id)                                                    # C ở phòng 2, nằm ngoài phạm vi phòng 1
    db.add(Delegation(from_employee_id=world.c.id, to_employee_id=world.a.id, entity="", from_date=TODAY, to_date=TODAY))
    db.commit()
    rows = by_code(wl.current_load(db, department_ids=[world.d1.id], now=NOW))
    assert set(rows) == {"A", "B"} and rows["A"]["delegated_in"] == 1


def test_thu_mua_cac_nguon_dem_dung_va_loai_tru_trang_thai(db, world):
    def pr(status, head=0, **kw):
        row = PurchaseRequest(code=f"P{uuid.uuid4().hex[:6]}", status=status, head_of_dept_id=head, company_id=world.co.id, **kw)
        db.add(row)
        db.flush()
        return row

    open_pr, done_pr, gone_pr = pr("processing"), pr("completed"), pr("processing", is_deleted=True)
    for p, line in ((open_pr, "ordered"), (open_pr, "no_po"), (done_pr, "ordered"), (gone_pr, "ordered"), (open_pr, "completed")):
        db.add(PurchaseRequestItem(pr_id=p.id, product_name="h", assignee=world.a.code, line_status=line))
    pr("submitted", head=world.b.id)
    pr("submitted", head=world.b.id)
    pr("approved", head=world.b.id)                                             # đã duyệt: hết chờ duyệt

    for status, deleted in (("received", False), ("approved", False), ("completed", False), ("draft", False), ("approved", True)):
        db.add(PurchaseOrder(code=f"O{uuid.uuid4().hex[:6]}", status=status, nspt_id=world.a.id, is_deleted=deleted, company_id=world.co.id))

    live = SurveyRequest(code="S1", status="processing", company_id=world.co.id)
    dead = SurveyRequest(code="S2", status="done", company_id=world.co.id)
    db.add_all([live, dead])
    db.flush()
    for req, assignee, line_status, pr_code in ((live, world.b.code, "", ""), (live, world.b.code, "resurvey", ""),
                                                 (live, world.b.code, "completed", ""), (live, world.b.code, "", "PYC9"),
                                                 (dead, world.b.code, "", ""), (live, "KHONG_AI", "", "")):
        db.add(SurveyRequestLine(survey_request_id=req.id, assignee=assignee, line_status=line_status, pr_code=pr_code))

    for status, drafter in ((STATUS_PENDING_ISSUE, world.c.id), (4, world.c.id)):
        db.add(Document(origin=1, doc_type_id=1, company_id=world.co.id, owner_employee_id=world.c.id,
                        drafter_employee_id=drafter, title="t", status=status))
    db.commit()

    rows = by_code(wl.current_load(db, company_id=world.co.id, now=NOW))
    assert rows["A"]["pr_handling"] == 1                                         # đếm PHIẾU, không đếm dòng; bỏ phiếu xong/xóa/dòng xong
    assert rows["A"]["po_handling"] == 1 and rows["B"]["pr_approval_pending"] == 2
    assert rows["B"]["survey_lines_handling"] == 2
    assert rows["C"]["docs_pending_issue"] == 1
    assert rows["A"]["open_items_total"] == 2 and rows["B"]["open_items_total"] == 4


def test_nghi_phep_dang_nghi_hom_nay_va_so_ngay_sap_toi_trong_horizon(db, world):
    def leave(emp, start, stop, status=3):
        db.add(LeaveRequest(code=f"L{uuid.uuid4().hex[:6]}", employee_id=emp, from_date=start, to_date=stop, status=status,
                            company_id=world.co.id))

    leave(world.a.id, TODAY - timedelta(days=1), TODAY + timedelta(days=1))      # đang nghỉ: hôm nay + mai trong khoảng
    leave(world.a.id, TODAY + timedelta(days=10), TODAY + timedelta(days=11))    # sắp nghỉ, trong 14 ngày
    leave(world.b.id, TODAY + timedelta(days=30), TODAY + timedelta(days=31))    # ngoài horizon
    leave(world.b.id, TODAY, TODAY + timedelta(days=2), status=2)                # chưa duyệt
    db.commit()
    rows = by_code(wl.current_load(db, company_id=world.co.id, now=NOW, horizon_days=14))
    assert rows["A"]["on_leave_today"] is True and rows["A"]["leave_days_ahead"] == 2 + 2
    assert rows["B"]["on_leave_today"] is False and rows["B"]["leave_days_ahead"] == 0


def test_nhan_su_nghi_viec_khong_xuat_hien_va_loc_theo_nhan_su(db, world):
    world.c.status = "resigned"
    db.commit()
    assert set(by_code(wl.current_load(db, company_id=world.co.id, now=NOW))) == {"A", "B"}
    assert set(by_code(wl.current_load(db, employee_ids=[world.a.id], now=NOW))) == {"A"}


def test_so_truy_van_toi_da_10_voi_5_va_200_nhan_su_va_now_duoc_tiem(db, world):
    co_id = world.co.id          # đọc trước: thuộc tính hết hạn sau commit sẽ tự đẻ thêm một câu SELECT trong lúc đo
    _, few = count_queries(db, lambda: wl.current_load(db, company_id=co_id, now=NOW))
    for i in range(200):
        make_person(db, f"X{i}", world.co, world.d1)
    db.commit()
    rows, many = count_queries(db, lambda: wl.current_load(db, company_id=co_id, now=NOW))
    assert len(rows) == 203 and len(many) == len(few) <= 10
    assert all(r["computed_at"] == NOW.isoformat() for r in rows)


@pytest.fixture
def client_as(db):
    def make(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield make
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def test_api_chi_quan_tri_va_bat_buoc_chon_pham_vi(db, world, cap_quyen, gan_bao_cao, client_as):
    staff, _ = make_person(db, "STAFF", world.co, world.d1)
    admin, _ = make_person(db, "ADMIN", world.co, world.d1)
    cap_quyen(staff.id, "work_task", scope="all", read=True)
    admin_role = cap_quyen(admin.id, "setting", scope="all", read=True)
    gan_bao_cao(SUBJECT_ROLE, admin_role.id, 16)            # duoc-CR-657: /load gác thêm khóa báo cáo 16
    db.commit()
    assert client_as(staff).get("/api/work-capability/load", params={"company_id": world.co.id}).status_code == 403
    assert client_as(admin).get("/api/work-capability/load").status_code == 422
    res = client_as(admin).get("/api/work-capability/load", params={"company_id": world.co.id})
    assert res.status_code == 200 and res.json()["data"]["count"] >= 3
    assert client_as(admin).get("/api/work-capability/load", params={"company_id": world.co.id, "horizon_days": 999}).status_code == 422
