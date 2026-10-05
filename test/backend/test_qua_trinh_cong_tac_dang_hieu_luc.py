"""Cờ `is_current` («Đang hiệu lực» ở bảng, «Hiện tại» ở dòng thời gian) — 05/10/2026.

Lỗi bắt được khi bấm thử trên trình duyệt: nhập BÙ dòng Bổ nhiệm 03/10 SAU khi đã
có dòng Điều chuyển 04/10 → cả hai dòng nhóm chính cùng «Đang hiệu lực», vì
`is_current` cũ chỉ xét `to_date` rỗng. Dòng có `from_date` ở tương lai cũng bị
báo «Đang hiệu lực». Đừng xóa các bài dưới — chúng giữ hai lỗi đó không quay lại.
"""
from datetime import date, timedelta

from app.core.hr_work_history_codes import WorkEventType
from app.core.vn_time import vn_today
from app.modules.employee.work_history_model import EmployeeWorkHistory
from app.modules.employee.work_history_rules import compute_is_current
from app.modules.employee.work_history_serializer import serialize_list, serialize_one

TODAY = date(2026, 10, 5)
ACTOR = 1


def _mem(rid: int, event_type, from_date: date, to_date: date | None = None) -> EmployeeWorkHistory:
    """Dòng trong bộ nhớ, không chạm DB — `compute_is_current` là hàm thuần."""
    return EmployeeWorkHistory(id=rid, employee_id=1, event_type=int(event_type),
                               from_date=from_date, to_date=to_date)


def _db_row(db, eid, event_type, from_date, **kw) -> EmployeeWorkHistory:
    row = EmployeeWorkHistory(employee_id=eid, event_type=int(event_type), from_date=from_date,
                              created_by=ACTOR, updated_by=ACTOR, **kw)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# ── Hàm thuần ────────────────────────────────────────────────────────────────

def test_danh_sach_rong_tra_rong():
    assert compute_is_current([], TODAY) == {}


def test_nhap_bu_dong_chinh_cu_hon_khong_con_dang_hieu_luc():
    rows = [_mem(9, WorkEventType.TRANSFER, date(2026, 10, 4)),
            _mem(10, WorkEventType.APPOINT, date(2026, 10, 3))]
    assert compute_is_current(rows, TODAY) == {9: True, 10: False}


def test_dong_tuong_lai_chua_hieu_luc_va_chua_thay_dong_hien_tai():
    rows = [_mem(1, WorkEventType.HIRE, date(2026, 1, 1)),
            _mem(2, WorkEventType.TRANSFER, TODAY + timedelta(days=1))]
    assert compute_is_current(rows, TODAY) == {1: True, 2: False}


def test_dong_bat_dau_dung_hom_nay_thay_dong_cu_ngay_hom_nay():
    rows = [_mem(1, WorkEventType.HIRE, date(2026, 1, 1)),
            _mem(2, WorkEventType.APPOINT, TODAY)]
    assert compute_is_current(rows, TODAY) == {1: False, 2: True}


def test_ket_thuc_hom_nay_van_hieu_luc_ket_thuc_hom_qua_thi_het():
    rows = [_mem(1, WorkEventType.CONCURRENT, date(2026, 1, 1), to_date=TODAY),
            _mem(2, WorkEventType.CONCURRENT, date(2026, 1, 1), to_date=TODAY - timedelta(days=1))]
    assert compute_is_current(rows, TODAY) == {1: True, 2: False}


def test_kiem_nhiem_khong_bi_dong_chinh_moi_hon_thay():
    rows = [_mem(1, WorkEventType.CONCURRENT, date(2026, 3, 1)),
            _mem(2, WorkEventType.TRANSFER, date(2026, 9, 1))]
    assert compute_is_current(rows, TODAY) == {1: True, 2: True}


def test_kiem_nhiem_moi_hon_khong_thay_dong_chinh():
    rows = [_mem(1, WorkEventType.HIRE, date(2026, 1, 1)),
            _mem(2, WorkEventType.CONCURRENT, date(2026, 9, 1))]
    assert compute_is_current(rows, TODAY) == {1: True, 2: True}


def test_thoi_viec_thay_dong_chinh_truoc_do():
    rows = [_mem(1, WorkEventType.TRANSFER, date(2026, 6, 1)),
            _mem(2, WorkEventType.RESIGN, date(2026, 10, 1))]
    assert compute_is_current(rows, TODAY) == {1: False, 2: True}


def test_hai_dong_chinh_cung_ngay_bat_dau_khong_dong_nao_thay_dong_nao():
    #  Chồng lấn cùng ngày đã có cảnh báo riêng lúc lưu (`overlap_warnings`) —
    #  ở đây không tự chọn một bên, cả hai vẫn hiện để người dùng thấy mà sửa.
    rows = [_mem(1, WorkEventType.TRANSFER, date(2026, 9, 1)),
            _mem(2, WorkEventType.APPOINT, date(2026, 9, 1))]
    assert compute_is_current(rows, TODAY) == {1: True, 2: True}


def test_loai_la_khong_nam_trong_bo_ma_khong_vo_va_khong_bi_thay():
    rows = [_mem(1, 99, date(2026, 1, 1)),
            _mem(2, WorkEventType.TRANSFER, date(2026, 9, 1))]
    assert compute_is_current(rows, TODAY) == {1: True, 2: True}


# ── Qua serializer thật (DB) ─────────────────────────────────────────────────

def test_serialize_list_va_serialize_one_cung_ket_qua(world):
    db, eid = world.db, world.emp["a3"]
    today = vn_today()
    newer = _db_row(db, eid, WorkEventType.TRANSFER, today - timedelta(days=1))
    backfill = _db_row(db, eid, WorkEventType.APPOINT, today - timedelta(days=2))

    listed = {o["id"]: o["is_current"] for o in serialize_list(db, [newer, backfill])}
    assert listed == {newer.id: True, backfill.id: False}
    #  `serialize_one` (trả về sau POST/PATCH) trước đây chỉ thấy chính dòng đó
    #  → luôn True; nay phải tính trên mọi dòng của nhân sự.
    assert serialize_one(db, backfill)["is_current"] is False
    assert serialize_one(db, newer)["is_current"] is True
