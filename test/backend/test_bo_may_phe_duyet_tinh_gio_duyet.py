"""Gói A4 (hiệu năng báo cáo, 01/10/2026) — `approval.report_turnaround.turnaround_hours` nhận
THÊM một SELECTABLE id (ngoài iterable CŨ), chạy ĐÚNG MỘT truy vấn thay vì chia lô 900.

Dữ liệu tối thiểu qua fixture `db` của conftest — module này không phụ thuộc Company/Department.
"""
from datetime import datetime, timedelta

from sqlalchemy import event, select

from app.modules.approval.instance_model import (INSTANCE_APPROVED, INSTANCE_REJECTED,
                                                 INSTANCE_RUNNING, ApprovalInstance)
from app.modules.approval.report_turnaround import turnaround_hours

ENTITY = "test_entity"
STARTED = datetime(2026, 1, 1, 8, 0)


def _instance(db, entity_id, *, status, hours, entity=ENTITY):
    finished = STARTED + timedelta(hours=hours) if hours is not None else None
    db.add(ApprovalInstance(entity=entity, entity_id=entity_id, flow_id=1, status=status,
                            started_at=STARTED, finished_at=finished))
    db.flush()


def _count_queries(db, fn):
    """Cùng khuôn `test_bao_cao_hanh_chinh.py::_count_queries` — đếm số câu lệnh xuống DB."""
    counted: list[str] = []

    def _on_exec(conn, cursor, statement, *args):
        counted.append(statement)

    event.listen(db.get_bind(), "before_cursor_execute", _on_exec)
    try:
        result = fn()
    finally:
        event.remove(db.get_bind(), "before_cursor_execute", _on_exec)
    return result, counted


# ── Hành vi CŨ (iterable id) giữ nguyên ──────────────────────────────────────────
def test_list_id_tra_dung_gio_duyet_cua_phien_ket_thuc(db):
    _instance(db, 1, status=INSTANCE_APPROVED, hours=2.5)
    _instance(db, 2, status=INSTANCE_REJECTED, hours=1.0)
    assert turnaround_hours(db, ENTITY, [1, 2]) == {1: 2.5, 2: 1.0}


def test_list_id_bo_qua_gia_tri_falsy_khong_cham_db():
    #  `db=None` chứng minh hàm KHÔNG đụng DB khi mọi id đều falsy — nếu còn đụng thì test này tự
    #  nổ (AttributeError trên None) thay vì phải mock.
    assert turnaround_hours(None, ENTITY, [0, None, 0]) == {}


def test_list_id_phien_dang_chay_hoac_thieu_moc_thoi_gian_khong_tinh(db):
    _instance(db, 1, status=INSTANCE_RUNNING, hours=5)       # chưa xong — bỏ
    _instance(db, 2, status=INSTANCE_APPROVED, hours=None)   # thiếu finished_at — bỏ
    assert turnaround_hours(db, ENTITY, [1, 2]) == {}


def test_list_id_nhieu_phien_cung_entity_lay_phien_MOI_NHAT(db):
    #  Hai phiên ĐÃ KẾT THÚC của CÙNG một entity_id (gửi lại sau khi bị trả về/từ chối) — id
    #  CAO HƠN (tạo sau) phải thắng, bất kể id nào approved/rejected.
    _instance(db, 10, status=INSTANCE_REJECTED, hours=9.0)   # id thấp hơn — phiên CŨ
    _instance(db, 10, status=INSTANCE_APPROVED, hours=3.0)   # id cao hơn — phiên MỚI, phải thắng
    assert turnaround_hours(db, ENTITY, [10]) == {10: 3.0}


def test_list_id_qua_900_van_chia_lo_dung_khong_lech_bien(db, monkeypatch):
    """Ép `_CHUNK` xuống 2 để mô phỏng ranh giới lô với bộ dữ liệu nhỏ — 5 id/lô 2 = 3 lô
    (2+2+1); mỗi entity_id chỉ thuộc ĐÚNG một lô (set id KHÔNG trùng giữa các lô) nên không có
    rủi ro lô sau ghi đè sai lô trước, nhưng việc merge qua `out.update(...)` vẫn phải đúng."""
    import app.modules.approval.report_turnaround as rt
    monkeypatch.setattr(rt, "_CHUNK", 2)
    for i in range(1, 6):
        _instance(db, i, status=INSTANCE_APPROVED, hours=float(i))
    assert turnaround_hours(db, ENTITY, list(range(1, 6))) == {i: float(i) for i in range(1, 6)}


def test_list_id_rong_tra_rong():
    assert turnaround_hours(None, ENTITY, []) == {}


# ── Gói A4: SELECTABLE id — đúng 1 truy vấn, không chia lô ───────────────────────
def test_select_tra_dung_ket_qua_va_loai_phien_chua_xong(db):
    _instance(db, 10, status=INSTANCE_APPROVED, hours=3.0)
    _instance(db, 11, status=INSTANCE_APPROVED, hours=4.0)
    _instance(db, 12, status=INSTANCE_RUNNING, hours=99)   # chưa xong — phải bị loại dù khớp id

    id_select = select(ApprovalInstance.entity_id).where(
        ApprovalInstance.entity == ENTITY, ApprovalInstance.entity_id.in_([10, 11, 12]))
    out, queries = _count_queries(db, lambda: turnaround_hours(db, ENTITY, id_select))
    assert out == {10: 3.0, 11: 4.0}
    assert len(queries) == 1   # KHÔNG chia lô dù entity_id.in_ liệt kê 3 id


def test_scalar_subquery_cung_hoat_dong(db):
    """`.scalar_subquery()` (khuyến nghị — không cảnh báo coercion của SQLAlchemy) phải hoạt
    động giống hệt `select()` thô."""
    _instance(db, 20, status=INSTANCE_APPROVED, hours=1.5)
    scalar = select(ApprovalInstance.entity_id).where(
        ApprovalInstance.entity == ENTITY, ApprovalInstance.entity_id == 20).scalar_subquery()
    assert turnaround_hours(db, ENTITY, scalar) == {20: 1.5}


def test_subquery_tu_object_cung_hoat_dong(db):
    _instance(db, 30, status=INSTANCE_REJECTED, hours=2.0)
    sub = (select(ApprovalInstance.entity_id)
          .where(ApprovalInstance.entity == ENTITY, ApprovalInstance.entity_id == 30)
          .subquery())
    assert turnaround_hours(db, ENTITY, sub) == {30: 2.0}


def test_select_rong_tra_rong_khong_loi(db):
    id_select = select(ApprovalInstance.entity_id).where(ApprovalInstance.entity == "khong-ton-tai")
    assert turnaround_hours(db, ENTITY, id_select) == {}


def test_select_va_list_cho_cung_mot_ket_qua_tren_cung_du_lieu(db):
    """Hai cách gọi (iterable CŨ và selectable MỚI) phải cho ra kết quả GIỐNG HỆT nhau trên cùng
    tập dữ liệu — A4 chỉ đổi CÁCH TRUY VẤN, không đổi Ý NGHĨA."""
    for i in range(1, 4):
        _instance(db, i, status=INSTANCE_APPROVED, hours=float(i) * 1.25)
    via_list = turnaround_hours(db, ENTITY, [1, 2, 3])
    id_select = select(ApprovalInstance.entity_id).where(
        ApprovalInstance.entity == ENTITY, ApprovalInstance.entity_id.in_([1, 2, 3]))
    via_select = turnaround_hours(db, ENTITY, id_select)
    assert via_list == via_select == {1: 1.25, 2: 2.5, 3: 3.75}
