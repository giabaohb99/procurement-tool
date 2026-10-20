"""duoc-CR-656 (D1a) — tính vòng đời phiếu: hàm THUẦN, không DB.

Định nghĩa «xong» / «làm lại» của từng loại phiếu nằm ở `cycle_specs.SPECS`; bài này là hợp đồng của chúng.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from app.core.capability_codes import CycleKind, CycleOutcome, CycleRole
from app.modules.capability.cycle_compute import Facts, compute_cycles
from app.modules.capability.cycle_specs import SPEC_BY_KIND, SPECS, Ev, event_from_status_change

T0 = datetime(2026, 10, 1, 1, 0)           # 08:00 VN
NOW = datetime(2026, 10, 30, 0, 0)


def at(days=0.0, hours=0):
    return T0 + timedelta(days=days, hours=hours)


def run(kind, **kw):
    kw.setdefault("entity_id", 1)
    kw.setdefault("created_at", T0)
    kw.setdefault("creator_id", 7)
    return compute_cycles(SPEC_BY_KIND[kind], Facts(**kw), NOW, today_vn=date(2026, 10, 30))


def by_role(rows, role):
    return [r for r in rows if r["role"] == int(role)]


# ── Hợp đồng cấu hình ─────────────────────────────────────────────────────────────────

def test_moi_loai_phieu_deu_co_dinh_nghia_va_khong_chong_nhau():
    assert {s.kind for s in SPECS} == set(CycleKind)
    for s in SPECS:
        assert s.done and not (s.done & s.cancelled) and not (s.done & s.rejected), s.kind


@pytest.mark.parametrize("kind,before,after,expected", [
    (CycleKind.PURCHASE_REQUEST, "approved", "completed", Ev.DONE),
    (CycleKind.PURCHASE_REQUEST, "submitted", "rejected", None),            # mơ hồ: audit mới biết từ chối hay trả về
    (CycleKind.SURVEY_REQUEST, "processing", "rejected", Ev.RETURN),        # YCBG: rejected = Trả về
    (CycleKind.SURVEY_REQUEST, "processing", "survey_done", None),          # Q2: «xong» của YCBG là `done`
    (CycleKind.SURVEY_REQUEST, "survey_done", "done", Ev.DONE),
    (CycleKind.PURCHASE_ORDER, "submitted", "rejected", Ev.RETURN),
    (CycleKind.PURCHASE_ORDER, "partial", "received", Ev.DONE),             # «Đã nhận đủ» = xong (20/10)
    (CycleKind.PAYMENT_REQUEST, "approved", "paid", Ev.DONE),
    (CycleKind.DOCUMENT, "2", "3", Ev.DONE),
    (CycleKind.DOCUMENT, "2", "9", Ev.RETURN),
    (CycleKind.DOCUMENT, "2", "10", Ev.REJECT),
    (CycleKind.VEHICLE_BOOKING, "4", "5", Ev.DONE),
    (CycleKind.VEHICLE_BOOKING, "2", "8", Ev.RETURN),
    (CycleKind.SEAL_REQUEST, "3", "4", Ev.DONE),
    (CycleKind.ROOM_BOOKING, "2", "3", Ev.DONE),
    (CycleKind.LEAVE_REQUEST, "2", "5", Ev.RETURN),
    (CycleKind.WORK_TASK, "1", "2", Ev.DONE),
    (CycleKind.WORK_TASK, "2", "1", Ev.REOPEN),
    (CycleKind.WORK_TASK, "3", "1", None),                                  # hủy rồi khôi phục không phải làm lại
])
def test_anh_xa_doi_trang_thai_thanh_su_kien(kind, before, after, expected):
    assert event_from_status_change(SPEC_BY_KIND[kind], before, after) == expected


# ── YCMH ──────────────────────────────────────────────────────────────────────────────

def test_ycmh_tra_ve_mot_lan_roi_xong_dem_dung_lam_lai_va_thoi_gian():
    rows = run(CycleKind.PURCHASE_REQUEST, status="completed",
               events=[(at(1), Ev.RETURN), (at(4), Ev.DONE)], handlers=[(9, at(0.5))])
    creator, = by_role(rows, CycleRole.CREATOR)
    handler, = by_role(rows, CycleRole.HANDLER)
    assert creator["outcome"] == int(CycleOutcome.DONE) and creator["rework_count"] == 1
    assert creator["done_at"] == at(4) and creator["cycle_hours"] == 96.0            # 4 ngày lịch
    assert handler["employee_id"] == 9 and handler["cycle_hours"] == 84.0            # tính từ lúc được giao
    assert not creator["is_estimated"]


def test_ycmh_rejected_ma_lan_cuoi_la_tra_ve_thi_van_dang_chay():
    rows = run(CycleKind.PURCHASE_REQUEST, status="rejected", events=[(at(1), Ev.REJECT), (at(2), Ev.RETURN)])
    assert rows[0]["outcome"] == int(CycleOutcome.OPEN) and rows[0]["rework_count"] == 1


def test_ycmh_rejected_that_la_tu_choi_va_khong_tinh_lam_lai():
    rows = run(CycleKind.PURCHASE_REQUEST, status="rejected", events=[(at(1), Ev.REJECT)])
    assert rows[0]["outcome"] == int(CycleOutcome.REJECTED)
    assert rows[0]["rework_count"] == 0 and rows[0]["done_at"] is None and rows[0]["cycle_hours"] is None


def test_huy_khong_co_ngay_xong():
    rows = run(CycleKind.PAYMENT_REQUEST, status="cancelled", events=[(at(1), Ev.CANCEL)])
    assert rows[0]["outcome"] == int(CycleOutcome.CANCELLED) and rows[0]["done_at"] is None


def test_hai_nguon_ke_cung_mot_lan_tra_ve_chi_tinh_mot():
    """Nhật ký thay đổi và audit cùng ghi «rejected» của YCBG cách nhau vài giây → một lần làm lại."""
    rows = run(CycleKind.SURVEY_REQUEST, status="processing",
               events=[(at(1), Ev.RETURN), (at(1) + timedelta(seconds=3), Ev.RETURN), (at(3), Ev.RETURN)])
    assert rows[0]["rework_count"] == 2


# ── Văn bản (sticky) ──────────────────────────────────────────────────────────────────

def test_van_ban_het_hieu_luc_van_la_da_xong_viec_soan_va_lay_lan_dau():
    rows = run(CycleKind.DOCUMENT, status="6", events=[(at(2), Ev.DONE), (at(2, 1), Ev.DONE)])  # 3 rồi 4, sau đó hết hạn
    assert rows[0]["outcome"] == int(CycleOutcome.DONE) and rows[0]["done_at"] == at(2)


# ── Task Dự án ────────────────────────────────────────────────────────────────────────

def test_task_mo_lai_hai_lan_roi_xong_lay_lan_cuoi_va_dem_hai_lan_lam_lai():
    ev = [(at(1), Ev.DONE), (at(2), Ev.REOPEN), (at(3), Ev.DONE), (at(4), Ev.REOPEN), (at(6), Ev.DONE)]
    rows = run(CycleKind.WORK_TASK, status="2", events=ev, task_type_id=5,
               estimate_hours=Decimal("4"), actual_hours=Decimal("6"), review_outcome=1)
    r = rows[0]
    assert r["done_at"] == at(6) and r["rework_count"] == 2 and r["task_type_id"] == 5
    assert (r["estimate_hours"], r["actual_hours"], r["review_outcome"]) == (Decimal("4"), Decimal("6"), 1)


def test_task_dang_mo_lai_thi_chua_xong():
    rows = run(CycleKind.WORK_TASK, status="1", events=[(at(1), Ev.DONE), (at(2), Ev.REOPEN)])
    assert rows[0]["outcome"] == int(CycleOutcome.OPEN) and rows[0]["done_at"] is None and rows[0]["rework_count"] == 1


def test_task_nhieu_pic_moi_nguoi_mot_dong_cung_thoi_gian_tron_vong():
    rows = run(CycleKind.WORK_TASK, status="2", events=[(at(2), Ev.DONE)], handlers=[(11, at(0)), (12, at(1)), (11, at(0))])
    handlers = by_role(rows, CycleRole.HANDLER)
    assert sorted(r["employee_id"] for r in handlers) == [11, 12]                    # trùng người không đẻ hai dòng
    assert {r["employee_id"]: r["cycle_hours"] for r in handlers} == {11: 48.0, 12: 24.0}
    assert len(by_role(rows, CycleRole.CREATOR)) == 1


def test_khong_co_nguoi_lap_thi_khong_co_dong_nguoi_lap():
    rows = run(CycleKind.WORK_TASK, status="2", creator_id=0, events=[(at(1), Ev.DONE)], handlers=[(11, at(0))])
    assert [r["role"] for r in rows] == [int(CycleRole.HANDLER)]


# ── Dự phòng khi nhật ký thiếu ────────────────────────────────────────────────────────

def test_xong_ma_khong_co_dau_vet_thi_uoc_tu_cot_moc_cua_bang_va_danh_dau():
    rows = run(CycleKind.WORK_TASK, status="2", done_ts=at(3), updated_at=at(9))
    assert rows[0]["done_at"] == at(3) and rows[0]["is_estimated"] is True
    rows = run(CycleKind.PURCHASE_REQUEST, status="completed", updated_at=at(5))        # không có cột mốc → updated_at
    assert rows[0]["done_at"] == at(5) and rows[0]["is_estimated"] is True


def test_moc_xong_truoc_moc_bat_dau_thi_bo_gio_chu_khong_ghi_so_am():
    rows = run(CycleKind.PURCHASE_REQUEST, status="completed", events=[(at(-2), Ev.DONE)])
    assert rows[0]["done_at"] == at(-2) and rows[0]["cycle_hours"] is None


# ── Trễ hạn theo NGÀY VN ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("done_utc,late", [
    (datetime(2026, 10, 20, 16, 0), False),    # 23:00 ngày 20 giờ VN — đúng hạn
    (datetime(2026, 10, 20, 18, 0), True),     # 01:00 ngày 21 giờ VN — trễ
])
def test_tre_han_so_theo_ngay_viet_nam(done_utc, late):
    rows = run(CycleKind.WORK_TASK, status="2", due_date="2026-10-20", events=[(done_utc, Ev.DONE)])
    assert rows[0]["is_late"] is late


def test_task_dang_mo_qua_han_hom_nay_thi_tre_va_huy_thi_khong_tinh():
    assert run(CycleKind.WORK_TASK, status="1", due_date="2026-10-20")[0]["is_late"] is True
    assert run(CycleKind.WORK_TASK, status="1", due_date="2026-11-20")[0]["is_late"] is False
    assert run(CycleKind.WORK_TASK, status="3", due_date="2026-10-01")[0]["is_late"] is None
    assert run(CycleKind.WORK_TASK, status="1", due_date="")[0]["is_late"] is None
