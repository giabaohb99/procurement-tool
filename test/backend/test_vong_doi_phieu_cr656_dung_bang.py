"""duoc-CR-656 (D1a) — dựng `tab_work_cycle` từ DB: nguồn sự kiện, người xử lý, lặp lại không nhân đôi, gia tăng, số truy vấn.

Dữ liệu dựng thẳng vào bảng (có mốc `created_at` tường minh) vì cần kiểm cả nhật ký thay đổi lẫn audit mà hai lớp đó
chỉ tự ghi khi có ngữ cảnh yêu cầu.
"""
from datetime import datetime, timedelta

import pytest

from app.core.capability_codes import CycleKind, CycleOutcome, CycleRole
from app.modules.audit.model import AuditLog
from app.modules.capability import cycle_builder
from app.modules.capability.model import WorkCycle
from app.modules.change_log.model import ChangeLog
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.seal_request.model import SealRequest
from app.modules.setting.model import Setting
from app.modules.work.task_model import WorkTask, WorkTaskAssignee

from ho_so_lam_viec_factory import make_company, make_dept, make_person
from lich_lam_viec_factory import count_queries

T0 = datetime(2026, 10, 1, 1, 0)
NOW = datetime(2026, 10, 30, 0, 0)
PR, PO, SEAL, TASK = (int(CycleKind.PURCHASE_REQUEST), int(CycleKind.PURCHASE_ORDER),
                      int(CycleKind.SEAL_REQUEST), int(CycleKind.WORK_TASK))


def day(n, hours=0):
    return T0 + timedelta(days=n, hours=hours)


def audit(db, entity, eid, action, at):
    db.add(AuditLog(entity=entity, entity_id=eid, action=action, message="", created_at=at))


def status_log(db, table, rid, before, after, at):
    db.add(ChangeLog(table_name=table, row_id=rid, op=2, field="status", before_value=before, after_value=after, created_at=at))


@pytest.fixture
def world(db):
    co = make_company(db, "C1")
    d1, d2 = make_dept(db, co, "D1"), make_dept(db, co, "D2")
    (req_u, req), (nstm_u, nstm), (nspt_u, nspt) = (make_person(db, "REQ", co, d1), make_person(db, "NV9", co, d2),
                                                    make_person(db, "NSPT", co, d2))
    db.commit()
    return type("W", (), dict(co=co, d1=d1, d2=d2, req=req, req_u=req_u, nstm=nstm, nspt=nspt, nspt_u=nspt_u))


def make_pr(db, w, code="PYC1", status="completed", received="2026-10-02"):
    pr = PurchaseRequest(code=code, requester_id=w.req.id, status=status, received_date=received,
                         company_id=w.co.id, created_at=T0, updated_at=day(4))
    db.add(pr)
    db.flush()
    db.add(PurchaseRequestItem(pr_id=pr.id, product_name="Hàng", assignee=w.nstm.code, line_status="completed"))
    return pr


def rows_of(db, kind):
    return db.query(WorkCycle).filter(WorkCycle.kind == kind).order_by(WorkCycle.role, WorkCycle.employee_id).all()


def test_ycmh_day_du_tu_audit_nguoi_lap_va_nguoi_xu_ly_theo_dong_hang(db, world):
    pr = make_pr(db, world)
    for action, d in (("submitted", 0.1), ("returned", 1), ("submitted", 1.5), ("completed", 4)):
        audit(db, "purchase_request", pr.id, action, day(d))
    db.commit()

    cycle_builder.build_all(db, None, NOW, {PR})
    creator, handler = rows_of(db, PR)
    assert (creator.employee_id, creator.role) == (world.req.id, int(CycleRole.CREATOR))
    assert creator.outcome == int(CycleOutcome.DONE) and creator.rework_count == 1 and not creator.is_estimated
    assert creator.done_at == day(4) and creator.cycle_hours == 96.0
    assert creator.department_id == world.d1.id                                  # phòng của NGƯỜI, không của phiếu
    assert (handler.employee_id, handler.role) == (world.nstm.id, int(CycleRole.HANDLER))
    #  Mốc giao việc = ngày tiếp nhận 02/10 (00:00 giờ VN = 01/10 17:00 UTC).
    assert handler.started_at == datetime(2026, 10, 1, 17, 0) and handler.cycle_hours == 80.0
    assert handler.department_id == world.d2.id


def test_ycmh_hoan_thanh_tu_dong_khong_audit_van_co_dong_danh_dau_uoc_tinh(db, world):
    make_pr(db, world)
    db.commit()
    cycle_builder.build_all(db, None, NOW, {PR})
    creator = rows_of(db, PR)[0]
    assert creator.outcome == int(CycleOutcome.DONE) and creator.is_estimated is True and creator.done_at == day(4)


def test_nhat_ky_thay_doi_va_audit_cung_ke_mot_su_kien_khong_dem_hai_lan(db, world):
    pr = make_pr(db, world)
    audit(db, "purchase_request", pr.id, "completed", day(4))
    status_log(db, "tab_purchase_request", pr.id, "purchased", "completed", day(4) + timedelta(seconds=2))
    db.commit()
    cycle_builder.build_all(db, None, NOW, {PR})
    assert rows_of(db, PR)[0].is_estimated is False and rows_of(db, PR)[0].done_at in (day(4), day(4) + timedelta(seconds=2))


def test_don_mua_hang_nguoi_lap_di_qua_tai_khoan_va_nguoi_phu_trach_theo_nspt(db, world):
    po = PurchaseOrder(code="DMH1", status="completed", company_id=world.co.id, nspt_id=world.nspt.id,
                       created_by=world.req_u.id, created_at=T0, updated_at=day(3))
    db.add(po)
    db.flush()
    status_log(db, "tab_purchase_order", po.id, "submitted", "rejected", day(1))     # ĐMH: rejected = Trả về
    status_log(db, "tab_purchase_order", po.id, "approved", "completed", day(3))
    db.commit()
    cycle_builder.build_all(db, None, NOW, {PO})
    creator, handler = rows_of(db, PO)
    assert creator.employee_id == world.req.id and creator.rework_count == 1 and creator.done_at == day(3)
    assert handler.employee_id == world.nspt.id


def test_duyet_dau_nguoi_xu_ly_la_tai_khoan_van_thu_doi_sang_nhan_su(db, world):
    seal = SealRequest(code="D1", status=4, requester_id=world.req.id, company_id=world.co.id, completed_by=world.nspt_u.id,
                       approved_at=day(1).isoformat(), completed_at=day(2).isoformat(), created_at=T0, updated_at=day(2))
    db.add(seal)
    db.commit()
    cycle_builder.build_all(db, None, NOW, {int(CycleKind.SEAL_REQUEST)})
    creator, handler = rows_of(db, int(CycleKind.SEAL_REQUEST))
    assert handler.employee_id == world.nspt.id and handler.started_at == day(1)
    assert creator.done_at == day(2) and creator.is_estimated is True                  # không có nhật ký → cột `completed_at`


def test_task_nhieu_pic_moi_nguoi_mot_dong_va_task_xoa_mem_bi_go(db, world):
    keep = WorkTask(list_id=1, title="a", status=2, creator_employee_id=world.req.id, task_type_id=3, created_at=T0,
                    updated_at=day(2), completed_at=day(2), due_date="2026-10-02")
    gone = WorkTask(list_id=1, title="b", status=1, creator_employee_id=world.req.id, created_at=T0, updated_at=day(2))
    db.add_all([keep, gone])
    db.flush()
    db.add_all([WorkTaskAssignee(task_id=keep.id, employee_id=world.nstm.id, kind=1, created_at=day(1)),
                WorkTaskAssignee(task_id=keep.id, employee_id=world.nspt.id, kind=1, created_at=day(0)),
                WorkTaskAssignee(task_id=keep.id, employee_id=world.req.id, kind=2)])        # người theo dõi: không tính
    status_log(db, "tab_work_task", keep.id, "1", "2", day(1))
    status_log(db, "tab_work_task", keep.id, "2", "1", day(1, 2))
    status_log(db, "tab_work_task", keep.id, "1", "2", day(2))
    db.commit()
    cycle_builder.build_all(db, None, NOW, {TASK})
    rows = rows_of(db, TASK)
    rows = [r for r in rows if r.entity_id == keep.id]
    assert len(rows) == 3                                                                  # 1 người lập + 2 PIC
    assert all(r.rework_count == 1 and r.done_at == day(2) and r.task_type_id == 3 for r in rows)
    assert all(r.is_late is True for r in rows)                                            # hạn 02/10, xong 03/10 → trễ

    gone.deleted_at = day(3)
    db.commit()
    cycle_builder.build_all(db, None, NOW, {TASK})
    assert {r.entity_id for r in rows_of(db, TASK)} == {keep.id}


def test_chay_lai_khong_nhan_doi_dong(db, world):
    make_pr(db, world, "A")
    make_pr(db, world, "B")
    db.commit()
    cycle_builder.build_all(db, None, NOW, {PR})
    first = [(r.entity_id, r.role, r.employee_id) for r in rows_of(db, PR)]
    cycle_builder.build_all(db, None, NOW, {PR})
    cycle_builder.build_all(db, None, NOW + timedelta(days=1), {PR})
    assert [(r.entity_id, r.role, r.employee_id) for r in rows_of(db, PR)] == first and len(first) == 4


def test_gia_tang_chi_tinh_lai_phieu_cham_toi_va_watermark_tien(db, world):
    old = make_pr(db, world, "OLD")
    old.updated_at = datetime(2026, 1, 1)
    db.commit()
    result = cycle_builder.run_incremental(db, now=NOW)                                # lần đầu: dựng toàn bộ
    assert result["since"] is None and result["rows"][PR] == 2
    mark = db.query(Setting).filter(Setting.skey == cycle_builder.WATERMARK_KEY).one()
    assert datetime.fromisoformat(mark.svalue) == NOW

    #  Phiếu mới chạm sau watermark; phiếu cũ bị xóa dòng chu kỳ bằng tay phải KHÔNG được dựng lại (chứng tỏ không quét hết).
    fresh = make_pr(db, world, "NEW")
    fresh.updated_at = NOW + timedelta(hours=1)
    db.query(WorkCycle).filter(WorkCycle.entity_id == old.id).delete()
    db.commit()
    later = cycle_builder.run_incremental(db, now=NOW + timedelta(days=1))
    assert later["rows"][PR] == 2 and {r.entity_id for r in rows_of(db, PR)} == {fresh.id}
    assert datetime.fromisoformat(db.query(Setting).filter(Setting.skey == cycle_builder.WATERMARK_KEY).one().svalue) \
        == NOW + timedelta(days=1)


def test_so_truy_van_khong_tang_theo_so_phieu(db, world):
    for i in range(5):
        make_pr(db, world, f"S{i}")
    db.commit()
    _, few = count_queries(db, lambda: cycle_builder.build_all(db, None, NOW, {PR}))
    for i in range(120):
        make_pr(db, world, f"B{i}")
    db.commit()
    _, many = count_queries(db, lambda: cycle_builder.build_all(db, None, NOW, {PR}))
    assert len(rows_of(db, PR)) == 250
    assert len(many) == len(few), (len(few), len(many))
    assert len(many) <= 14
