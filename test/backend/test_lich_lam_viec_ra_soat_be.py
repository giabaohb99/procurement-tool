"""Lịch làm việc — vá các lỗi từ đợt rà soát code backend (M1–M4, L1–L6).

Mỗi bài ghi tên lỗi nó khóa. `api`/`_mk_schedule`... mượn từ `test_lich_lam_viec_api`.
"""
import importlib.util
import uuid
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import text

from app.core.database import get_db
from app.core.auth import get_current_user
from app.main import app
from app.modules.user.model import User
from app.modules.work_schedule import assignment_service as svc
from app.modules.work_schedule.model import WorkScheduleAssignment as A
from app.modules.work_schedule.template_schema import DayIn, ScheduleCreate
from lich_lam_viec_factory import assign, make_world
from test_lich_lam_viec_api import (FULL, _assign_body, _body, _days, _mk_schedule,  # noqa: F401
                                    api)

URL = "/api/work-schedule-assignments"


# ── M1 / L2: giờ có múi giờ / có giây ────────────────────────────────────────

@pytest.mark.parametrize("field,value", [
    ("start_time", "08:00Z"), ("end_time", "17:00+07:00"), ("lunch_start", "12:00Z"),
    ("lunch_end", "13:00-01:00"),
    ("start_time", "08:00:30"), ("end_time", "17:00:01"), ("lunch_start", "12:00:59"),
    ("start_time", "08:00:00.5"),
])
def test_gio_co_mui_gio_hoac_giay_bi_tu_choi_422_khong_no_500(api, field, value):
    """Bug M1: "08:00Z" làm so sánh time aware/naive ném TypeError -> 500.
    Bug L2: "08:00:30" qua kiểm start<end rồi `_minutes` bỏ giây -> ngày FULL 0 giờ."""
    with pytest.raises(ValidationError):
        DayIn(weekday=0, **{**FULL, field: value})
    days = _days(d0={**FULL, field: value})
    assert api.post("/api/work-schedules", json=_body(days=days)).status_code == 422


def test_gio_hop_le_hh_mm_van_qua_va_nua_ngay_cam_gio_nghi_trua():
    DayIn(weekday=0, **FULL)
    DayIn(weekday=0, day_kind=3, start_time="08:00", end_time="12:00")
    #  L3: nửa ngày KHÔNG được có ô nghỉ trưa. Loại ngày thắng giờ (xem docstring `DayIn`).
    with pytest.raises(ValidationError):
        DayIn(weekday=0, day_kind=3, start_time="08:00", end_time="12:00",
              lunch_start="09:00", lunch_end="10:00")
    ScheduleCreate(**_body())


# ── M2: chốt UNIQUE + đua tạo ────────────────────────────────────────────────

def test_hai_lenh_tao_gan_cung_doi_tuong_cung_ngay_khong_sinh_dong_trung(api, db, monkeypatch):
    """Bug M2: SELECT rồi INSERT không khóa -> bấm đúp sinh hai dòng. Giả lập đua bằng cách
    làm `_overlaps` mù (như thể lệnh kia chưa commit): chốt UNIQUE phải đỡ, trả 400 sạch."""
    sid = _mk_schedule(api)["id"]
    assert api.post(URL, json=_assign_body(1, 0, sid, "2026-11-01")).status_code == 201
    monkeypatch.setattr(svc, "_overlaps", lambda *a, **k: [])
    res = api.post(URL, json=_assign_body(1, 0, sid, "2026-11-01"))
    assert res.status_code == 400 and "cùng ngày" in res.text
    assert db.query(A).filter_by(target_level=1, effective_from=date(2026, 11, 1)).count() == 1


def test_bang_gan_co_unique_va_khong_con_chi_muc_thua_ix_wsd_schedule():
    """Bug M2 + L6: UNIQUE phải nằm ở model; `ix_wsd_schedule` thừa vì đã có uq (schedule_id, weekday)."""
    from app.modules.work_schedule.model import WorkScheduleAssignment, WorkScheduleDay
    names = {c.name for c in WorkScheduleAssignment.__table__.constraints}
    assert "uq_wsa_target_from" in names
    assert "ix_wsd_schedule" not in {i.name for i in WorkScheduleDay.__table__.indexes}
    assert "uq_work_schedule_day" in {c.name for c in WorkScheduleDay.__table__.constraints}


# ── M3: phạm vi `employee` cho dòng gán cấp Nhân sự ───────────────────────────

def _as(api, user):
    app.dependency_overrides[get_current_user] = lambda: user


def test_dong_gan_cap_nhan_su_ngoai_pham_vi_bi_giau_o_danh_sach_va_chi_tiet(api, db, cap_quyen):
    """Bug M3: `work_schedule` PUBLIC nên ai có `read` cũng thấy tên + lịch của nhân sự ngoài tầm."""
    company, dept, hr_emp = api.world
    _, _, mine = make_world(db, "RS1")
    _, _, other = make_world(db, "RS2")
    sid = _mk_schedule(api)["id"]
    sys_row = api.post(URL, json=_assign_body(1, 0, sid, "2026-01-01")).json()["data"]
    mine_row = api.post(URL, json=_assign_body(4, mine.id, sid, "2026-02-01")).json()["data"]
    other_row = api.post(URL, json=_assign_body(4, other.id, sid, "2026-02-01")).json()["data"]
    dept_row = api.post(URL, json=_assign_body(3, dept.id, sid, "2026-02-01")).json()["data"]

    nv = User(email="rs-nv@dego.vn", employee_id=mine.id, is_active=True)
    db.add(nv)
    db.commit()
    cap_quyen(nv.id, "work_schedule", scope="all", read=True, create=True, write=True, delete=True)
    cap_quyen(nv.id, "employee", scope="own", read=True)
    _as(api, nv)

    ids = {r["id"] for r in api.get(URL).json()["data"]["items"]}
    assert ids == {sys_row["id"], mine_row["id"], dept_row["id"]}   # thiếu other_row
    assert api.get(f"{URL}?target_level=4&target_id={other.id}").json()["data"]["total"] == 0
    assert api.get(f"{URL}/{other_row['id']}").status_code == 404
    assert api.get(f"{URL}/{mine_row['id']}").status_code == 200
    assert api.get(f"{URL}/{dept_row['id']}").status_code == 200
    #  Quyền ghi cũng phải đứng trong tầm: không sửa/xóa/gán cho người ngoài phạm vi.
    assert api.patch(f"{URL}/{other_row['id']}", json={"note": "x"}).status_code == 404
    assert api.delete(f"{URL}/{other_row['id']}").status_code == 404
    assert api.post(URL, json=_assign_body(4, other.id, sid, "2026-09-01")).status_code == 400
    assert api.post(URL, json=_assign_body(4, mine.id, sid, "2026-09-01")).status_code == 201
    #  Đổi đích sang người ngoài tầm cũng bị chặn.
    assert api.patch(f"{URL}/{mine_row['id']}", json={"target_id": other.id}).status_code == 400


def test_khong_co_quyen_employee_thi_khong_thay_dong_nhan_su_nao(api, db, cap_quyen):
    _, _, e = make_world(db, "RS3")
    sid = _mk_schedule(api)["id"]
    sys_row = api.post(URL, json=_assign_body(1, 0, sid, "2026-01-01")).json()["data"]
    api.post(URL, json=_assign_body(4, e.id, sid, "2026-02-01"))
    u = User(email="rs-x@dego.vn", employee_id=0, is_active=True)
    db.add(u)
    db.commit()
    cap_quyen(u.id, "work_schedule", scope="all", read=True)
    _as(api, u)
    assert [r["id"] for r in api.get(URL).json()["data"]["items"]] == [sys_row["id"]]


def test_danh_sach_gan_so_truy_van_khong_tang_theo_so_nhan_su(api, db, cap_quyen):
    """Lọc phạm vi bằng truy vấn con: không N+1."""
    from lich_lam_viec_factory import count_queries
    sid = _mk_schedule(api)["id"]
    me = None
    for i in range(6):
        _, _, e = make_world(db, f"NQ{i}")
        me = me or e
        api.post(URL, json=_assign_body(4, e.id, sid, "2026-02-01"))
    nv = User(email="rs-q@dego.vn", employee_id=me.id, is_active=True)
    db.add(nv)
    db.commit()
    cap_quyen(nv.id, "work_schedule", scope="all", read=True)
    cap_quyen(nv.id, "employee", scope="all", read=True)
    _as(api, nv)
    api.get(URL)   # làm nóng bộ nhớ đệm hồ sơ quyền (60s) để chỉ đếm truy vấn của chính danh sách
    _, q6 = count_queries(db, lambda: api.get(URL))
    for i in range(6, 12):
        _, _, e = make_world(db, f"NQ{i}")
        api.post(URL, json=_assign_body(4, e.id, sid, "2026-02-01"))
    _, q12 = count_queries(db, lambda: api.get(URL))
    assert len(q12) == len(q6)


# ── L1: tên lịch ở estimate-days ─────────────────────────────────────────────

def test_estimate_days_khong_lo_ten_lich_cua_nguoi_ngoai_pham_vi(api, db, cap_quyen):
    """Bug L1: `employee_id` bất kỳ -> trả `schedule_name` của người đó dù ngoài tầm."""
    _, _, mine = make_world(db, "ES1")
    _, _, other = make_world(db, "ES2")
    sid = _mk_schedule(api, name="Lịch riêng ES")["id"]
    for e in (mine, other):
        assert api.post(URL, json=_assign_body(4, e.id, sid, "2026-01-01")).status_code == 201
    nv = User(email="es@dego.vn", employee_id=mine.id, is_active=True)
    db.add(nv)
    db.commit()
    cap_quyen(nv.id, "leave_request", scope="own", read=True)
    cap_quyen(nv.id, "employee", scope="own", read=True)
    _as(api, nv)
    base = "/api/leave-requests/tools/estimate-days?from_date=2026-03-02&to_date=2026-03-03"
    res = api.get(f"{base}&employee_id={other.id}")
    assert res.status_code == 200, res.text
    assert res.json()["data"]["schedule_name"] == ""
    assert api.get(f"{base}&employee_id={mine.id}").json()["data"]["schedule_name"] == "Lịch riêng ES"
    assert api.get(base).json()["data"]["schedule_name"] == "Lịch riêng ES"


# ── L5: vai trò khai sau vòng setdefault vẫn có read ─────────────────────────

def test_moi_vai_tro_deu_co_it_nhat_read_work_schedule():
    """Bug L5: coffee_admin / coffee_counter / market_lookup khai SAU vòng `setdefault` nên hụt `read`."""
    from app.seed import STD_ROLES
    for code, info in STD_ROLES.items():
        acts, scope = info["perms"].get("work_schedule", ([], ""))
        assert "read" in acts, f"{code} thiếu work_schedule.read"
    assert "write" not in STD_ROLES["coffee_admin"]["perms"]["work_schedule"][0]
    assert "write" in STD_ROLES["hr_leave"]["perms"]["work_schedule"][0]


# ── M4: xóa dòng gán mở lại lịch cũ ──────────────────────────────────────────

def _spans(api, level=1, tid=None):
    q = f"{URL}?target_level={level}" + (f"&target_id={tid}" if tid is not None else "")
    rows = api.get(q).json()["data"]["items"]
    return sorted((r["effective_from"], r["effective_to"], r["schedule_id"]) for r in rows)


def test_xoa_dong_gan_vua_tao_mo_lai_dong_cu_khong_thoi_han(api):
    """Bug M4: xóa C không hoàn tác việc P bị đóng -> khoảng của C thành lỗ hổng."""
    a = _mk_schedule(api)["id"]
    b = _mk_schedule(api, name="Mẫu B")["id"]
    api.post(URL, json=_assign_body(1, 0, a, "2026-01-01"))
    c = api.post(URL, json=_assign_body(1, 0, b, "2026-11-01")).json()["data"]
    assert _spans(api) == [("2026-01-01", "2026-10-31", a), ("2026-11-01", None, b)]
    assert api.delete(f"{URL}/{c['id']}").status_code == 200
    assert _spans(api) == [("2026-01-01", None, a)]


def test_xoa_lich_tam_noi_lai_ve_mot_dong_voi_han_goc(api, db):
    a = _mk_schedule(api)["id"]
    b = _mk_schedule(api, name="Mẫu B")["id"]
    api.post(URL, json=_assign_body(1, 0, a, "2026-01-01"))
    c = api.post(URL, json=_assign_body(1, 0, b, "2026-11-01", "2026-11-30")).json()["data"]
    assert len(_spans(api)) == 3
    assert api.delete(f"{URL}/{c['id']}").status_code == 200
    assert _spans(api) == [("2026-01-01", None, a)]
    assert db.query(A).count() == 1


def test_sua_ngay_dong_goc_roi_xoa_thi_khong_mo_lai(api):
    a = _mk_schedule(api)["id"]
    b = _mk_schedule(api, name="Mẫu B")["id"]
    api.post(URL, json=_assign_body(1, 0, a, "2026-01-01"))
    c = api.post(URL, json=_assign_body(1, 0, b, "2026-11-01")).json()["data"]
    assert api.patch(f"{URL}/{c['id']}", json={"effective_from": "2026-11-15"}).status_code == 200
    assert api.delete(f"{URL}/{c['id']}").status_code == 200
    assert _spans(api) == [("2026-01-01", "2026-10-31", a)]   # không đoán: để HR tự quyết


def test_mo_lai_ma_se_chong_dong_khac_thi_bo_qua(api, db):
    a = _mk_schedule(api)["id"]
    b = _mk_schedule(api, name="Mẫu B")["id"]
    api.post(URL, json=_assign_body(1, 0, a, "2026-01-01"))
    c = api.post(URL, json=_assign_body(1, 0, b, "2026-11-01", "2026-11-30")).json()["data"]
    #  Chen tay một dòng vào khoảng của C sau khi C đã có (vd dữ liệu nhập từ nguồn khác).
    assign(db, __import__("app.core.work_schedule_codes", fromlist=["x"]).WorkScheduleLevel.SYSTEM,
           0, b, date(2026, 11, 10), date(2026, 11, 12))
    db.commit()
    assert api.delete(f"{URL}/{c['id']}").status_code == 200
    spans = _spans(api)
    assert ("2026-01-01", "2026-10-31", a) in spans       # P giữ nguyên, không mở lại
    assert ("2026-12-01", None, a) in spans               # R còn đó (đã gỡ liên kết)
    assert all(r.linked_assignment_id is None for r in db.query(A).all())


def test_xoa_dong_khong_lien_ket_khong_co_tac_dung_phu(api):
    a = _mk_schedule(api)["id"]
    x = api.post(URL, json=_assign_body(1, 0, a, "2026-01-01", "2026-03-31")).json()["data"]
    api.post(URL, json=_assign_body(1, 0, a, "2026-06-01", "2026-06-30"))
    assert api.delete(f"{URL}/{x['id']}").status_code == 200
    assert _spans(api) == [("2026-06-01", "2026-06-30", a)]


# ── Migration: cấp quyền cho vai trò có sẵn ──────────────────────────────────

def _load_migration():
    import app
    #  `app/` nằm cạnh `migrations/` cả trên máy lẫn trong container (/app/migrations).
    path = Path(app.__file__).resolve().parent.parent / "migrations/versions/wsched01_lich_lam_viec.py"
    spec = importlib.util.spec_from_file_location("wsched01_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_migration_cap_quyen_work_schedule_dung_vai_tro_va_idempotent(db, monkeypatch):
    from app.modules.role.model import Permission, Role
    for code in ("admin", "hr_leave", "hr_profile", "staff", "coffee_counter"):
        db.add(Role(code=code, name=code))
    db.flush()
    staff = db.query(Role).filter_by(code="staff").one()
    #  Vai trò đã có dòng (đã chỉnh tay/seed) thì migration KHÔNG ghi đè.
    db.add(Permission(role_id=staff.id, entity="work_schedule", scope="own", can_read=False))
    db.commit()
    mig = _load_migration()
    conn = db.connection()
    monkeypatch.setattr(mig.op, "get_bind", lambda: conn)
    mig._grant_permissions()
    mig._grant_permissions()          # chạy lần hai: không sinh thêm dòng
    rows = {r.code: p for r, p in db.query(Role, Permission).join(
        Permission, Permission.role_id == Role.id).filter(Permission.entity == "work_schedule")}
    assert len(rows) == 5 and db.query(Permission).filter_by(entity="work_schedule").count() == 5
    for code in ("admin", "hr_leave", "hr_profile"):
        p = rows[code]
        assert (p.can_read, p.can_create, p.can_write, p.can_delete, p.scope) == (True,) * 4 + ("all",)
    p = rows["coffee_counter"]
    assert (p.can_read, p.can_create, p.can_write, p.can_delete) == (True, False, False, False)
    assert rows["staff"].scope == "own" and rows["staff"].can_read is False
    monkeypatch.setattr(mig.op, "get_bind", lambda: db.connection())
    db.execute(text("DELETE FROM tab_permission WHERE entity = 'work_schedule'"))
    assert db.query(Permission).filter_by(entity="work_schedule").count() == 0
