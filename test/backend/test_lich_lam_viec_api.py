"""Lịch làm việc phase 02 — schema, nghiệp vụ gán lịch và API qua HTTP.

Chú ý: SQLite không ép độ dài VARCHAR nên mọi trần kiểm ở tầng SCHEMA (`ValidationError`).
Quy tắc gán chồng (chốt 05/10/2026): POST tự đóng dòng «không thời hạn» bắt đầu TRƯỚC `from`
mới; mọi chồng khác 400; PATCH KHÔNG BAO GIỜ tự đóng.
"""
import uuid
from datetime import date, time

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.auth import get_current_user
from app.core.database import get_db
from app.main import app
from app.modules.audit.model import AuditLog
from app.modules.user.model import User
from app.modules.work_schedule.assignment_schema import AssignmentCreate
from app.modules.work_schedule.template_schema import ScheduleCreate
from lich_lam_viec_factory import make_world

FULL = {"day_kind": 2, "start_time": "08:00", "end_time": "17:00",
        "lunch_start": "12:00", "lunch_end": "13:00"}
OFF = {"day_kind": 1}


def _days(**over):
    days = [{"weekday": i, **FULL} for i in range(6)] + [{"weekday": 6, **OFF}]
    for wd, patch in over.items():
        days[int(wd[1:])] = {"weekday": int(wd[1:]), **patch}
    return days


def _body(**kw):
    return {"name": "Mẫu A", "note": "", "is_active": True, "days": _days(), **kw}


def _assign_body(level=1, target=0, schedule_id=1, start="2026-11-01", end=None):
    return {"target_level": level, "target_id": target, "schedule_id": schedule_id,
            "effective_from": start, "effective_to": end, "note": ""}


# ── Schema ────────────────────────────────────────────────────────────────────

def _week_with(extra=None, drop=0):
    days = _days()
    return days[:len(days) - drop] + (extra or [])


@pytest.mark.parametrize("days", [
    _week_with(drop=1),                                   # 6 dòng
    _week_with(extra=[{"weekday": 6, **OFF}]),            # 8 dòng
    _week_with(drop=1, extra=[{"weekday": 5, **OFF}]),    # trùng thứ 5, thiếu thứ 6
    _week_with(drop=1, extra=[{"weekday": 7, **OFF}]),    # weekday 7
    [],                                                   # rỗng
])
def test_schema_sai_so_dong_hoac_trung_thu(days):
    with pytest.raises(ValidationError):
        ScheduleCreate(**_body(days=days))


@pytest.mark.parametrize("bad", [
    {"weekday": -1, **OFF}, {"weekday": 0, "day_kind": 0}, {"weekday": 0, "day_kind": 5},
    {"weekday": 0, **{**FULL, "start_time": "17:00", "end_time": "08:00"}},          # start > end
    {"weekday": 0, **{**FULL, "start_time": "08:00", "end_time": "08:00"}},          # giờ làm = 0
    {"weekday": 0, **{**FULL, "lunch_end": None}},                                   # trưa thiếu nửa
    {"weekday": 0, **{**FULL, "lunch_start": "07:00", "lunch_end": "09:00"}},        # trưa ngoài khung
    {"weekday": 0, **{**FULL, "lunch_start": "13:00", "lunch_end": "12:00"}},        # trưa ngược
    {"weekday": 0, "day_kind": 3, "start_time": "08:00", "end_time": "12:00",
     "lunch_start": "10:00", "lunch_end": "11:00"},                                  # nửa ngày kèm trưa
    {"weekday": 0, "day_kind": 3},                                                   # nửa ngày thiếu giờ
])
def test_schema_ngay_sai(bad):
    days = _days()
    days[0] = bad
    with pytest.raises(ValidationError):
        ScheduleCreate(**_body(days=days))


def test_schema_ngay_off_kem_gio_bi_ep_null():
    days = _days(d6={**OFF, "start_time": "08:00", "end_time": "17:00", "lunch_start": "12:00"})
    days[6]["weekday"] = 6
    sched = ScheduleCreate(**_body(days=days))
    d = sched.days[6]
    assert (d.start_time, d.end_time, d.lunch_start, d.lunch_end) == (None,) * 4


def test_schema_ten_va_ghi_chu_co_tran():
    with pytest.raises(ValidationError):
        ScheduleCreate(**_body(name="x" * 151))
    with pytest.raises(ValidationError):
        ScheduleCreate(**_body(name="   "))
    with pytest.raises(ValidationError):
        ScheduleCreate(**_body(note="x" * 501))
    assert ScheduleCreate(**_body(name="x" * 150)).name == "x" * 150


@pytest.mark.parametrize("kw", [
    {"end": "2026-10-31"},                       # to < from
    {"start": "1900-01-01"}, {"start": "9999-01-01"},
    {"level": 1, "target": 5},                   # SYSTEM kèm đích
    {"level": 2, "target": 0},                   # COMPANY không đích
    {"level": 9, "target": 1},                   # cấp lạ
    {"level": 0, "target": 0},                   # cấp 0
])
def test_schema_gan_sai(kw):
    with pytest.raises(ValidationError):
        AssignmentCreate(**_assign_body(**kw))


def test_schema_gan_to_bang_from_la_hop_le():
    a = AssignmentCreate(**_assign_body(end="2026-11-01"))
    assert a.effective_to == date(2026, 11, 1)


# ── HTTP ──────────────────────────────────────────────────────────────────────

@pytest.fixture
def api(db, cap_quyen):
    """Người dùng đủ 4 quyền ở `work_schedule` + đọc `employee` toàn công ty."""
    company, dept, emp = make_world(db, "AP1")
    user = User(email="hr@dego.vn", employee_id=emp.id, is_active=True)
    db.add(user)
    db.commit()
    cap_quyen(user.id, "work_schedule", scope="all", read=True, create=True, write=True, delete=True)
    cap_quyen(user.id, "employee", scope="all", read=True)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    client = TestClient(app, headers={"Authorization": f"Bearer t-{uuid.uuid4().hex}"})
    client.world = (company, dept, emp)
    client.user = user
    yield client
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _mk_schedule(api, name="Mẫu A", **kw):
    res = api.post("/api/work-schedules", json=_body(name=name, **kw))
    assert res.status_code == 201, res.text
    return res.json()["data"]


def test_tao_mau_tra_du_hinh_dang_hop_dong(api):
    data = _mk_schedule(api, days=_days(d5={"day_kind": 3, "start_time": "08:00", "end_time": "12:00"}))
    assert [d["weekday"] for d in data["days"]] == list(range(7))
    assert data["days"][5]["day_kind"] == 3 and data["days"][5]["lunch_start"] is None
    assert data["days"][0]["start_time"] == "08:00"
    assert data["weekly_workdays"] == 5.5 and data["assignment_count"] == 0
    lst = api.get("/api/work-schedules").json()["data"]
    assert lst["total"] == 1 and lst["items"][0]["id"] == data["id"]


def test_trung_ten_mau_400(api):
    _mk_schedule(api)
    assert api.post("/api/work-schedules", json=_body()).status_code == 400


def test_sua_mau_thay_tron_7_dong_va_khong_ep_ten_cua_chinh_no(api):
    sid = _mk_schedule(api)["id"]
    res = api.patch(f"/api/work-schedules/{sid}", json={"name": "Mẫu A", "days": _days(d6=FULL | {"weekday": 6})})
    assert res.status_code == 200, res.text
    assert res.json()["data"]["weekly_workdays"] == 7.0
    assert api.patch(f"/api/work-schedules/{sid}", json={"days": _days()[:3]}).status_code == 422


def test_xoa_mau_dang_gan_400_va_gan_mau_da_tat_400(api):
    sid = _mk_schedule(api)["id"]
    assert api.post("/api/work-schedule-assignments", json=_assign_body(schedule_id=sid)).status_code == 201
    res = api.delete(f"/api/work-schedules/{sid}")
    assert res.status_code == 400 and "đang được gán" in res.text
    assert api.get(f"/api/work-schedules/{sid}").json()["data"]["assignment_count"] == 1
    off = _mk_schedule(api, name="Tắt", is_active=False)["id"]
    res = api.post("/api/work-schedule-assignments", json=_assign_body(schedule_id=off, start="2027-01-01"))
    assert res.status_code == 400 and "đã tắt" in res.text
    free = _mk_schedule(api, name="Rảnh")["id"]
    assert api.delete(f"/api/work-schedules/{free}").status_code == 200


def test_gan_doi_tuong_khong_ton_tai_hoac_mau_khong_ton_tai_400(api):
    sid = _mk_schedule(api)["id"]
    assert api.post("/api/work-schedule-assignments", json=_assign_body(3, 99999, sid)).status_code == 400
    assert api.post("/api/work-schedule-assignments", json=_assign_body(2, 99999, sid)).status_code == 400
    assert api.post("/api/work-schedule-assignments", json=_assign_body(4, 99999, sid)).status_code == 400
    assert api.post("/api/work-schedule-assignments", json=_assign_body(1, 0, 99999)).status_code == 400


def test_danh_sach_gan_tra_ten_doi_tuong_va_loc(api):
    _, dept, _ = api.world
    sid = _mk_schedule(api)["id"]
    api.post("/api/work-schedule-assignments", json=_assign_body(1, 0, sid, "2026-01-01", "2026-12-31"))
    api.post("/api/work-schedule-assignments", json=_assign_body(3, dept.id, sid, "2026-02-01"))
    data = api.get("/api/work-schedule-assignments").json()["data"]
    assert data["total"] == 2
    assert data["items"][0]["effective_from"] == "2026-02-01"           # mặc định from giảm dần
    row = data["items"][0]
    assert (row["target_level_label"], row["target_name"]) == ("Phòng ban", dept.name)
    assert row["schedule_name"] == "Mẫu A"
    assert api.get("/api/work-schedule-assignments?target_level=3").json()["data"]["total"] == 1
    assert api.get("/api/work-schedule-assignments?target_level=abc").json()["data"]["total"] == 2


def test_chong_khoang_400_ke_ca_trung_mep_mot_ngay(api):
    sid = _mk_schedule(api)["id"]
    api.post("/api/work-schedule-assignments", json=_assign_body(1, 0, sid, "2026-11-01", "2026-11-30"))
    res = api.post("/api/work-schedule-assignments",
                   json=_assign_body(1, 0, sid, "2026-11-30", "2026-12-31"))   # trùng đúng 1 ngày
    assert res.status_code == 400 and "Mẫu A" in res.text and "01/11/2026" in res.text
    # Dòng mới nằm trọn TRONG dòng cũ cũng là chồng.
    assert api.post("/api/work-schedule-assignments",
                    json=_assign_body(1, 0, sid, "2026-11-10", "2026-11-12")).status_code == 400
    # Sát mép (cũ kết thúc 30/11, mới từ 01/12) thì được.
    assert api.post("/api/work-schedule-assignments",
                    json=_assign_body(1, 0, sid, "2026-12-01", "2026-12-31")).status_code == 201


def test_tao_gan_moi_tu_dong_dong_dong_khong_thoi_han_cu_va_ghi_audit(api, db):
    sid = _mk_schedule(api)["id"]
    old = api.post("/api/work-schedule-assignments", json=_assign_body(1, 0, sid, "2026-01-01")).json()["data"]
    res = api.post("/api/work-schedule-assignments", json=_assign_body(1, 0, sid, "2026-11-01"))
    assert res.status_code == 201, res.text
    got = api.get(f"/api/work-schedule-assignments/{old['id']}").json()["data"]
    assert got["effective_to"] == "2026-10-31"
    assert db.query(AuditLog).filter_by(entity="work_schedule", entity_id=old["id"],
                                        action="update").count() == 1


def test_gan_lich_tam_co_han_thi_het_han_quay_lai_lich_cu_khong_rot_xuong_cap_rong(api, db):
    """Lỗi bản đầu: lịch tạm CÓ hạn đóng HẲN dòng cũ vô hạn → hết tạm, người đó rơi tụt về lịch
    phòng ban/hệ thống thay vì lịch riêng của mình. Nay dòng cũ bị cắt đôi, nửa sau mở lại."""
    a_id = _mk_schedule(api)["id"]
    b_id = _mk_schedule(api, name="Mẫu B")["id"]
    old = api.post("/api/work-schedule-assignments", json=_assign_body(1, 0, a_id, "2026-01-01")).json()["data"]
    res = api.post("/api/work-schedule-assignments", json=_assign_body(1, 0, b_id, "2026-11-01", "2026-11-30"))
    assert res.status_code == 201, res.text
    rows = api.get("/api/work-schedule-assignments?target_level=1").json()["data"]["items"]
    spans = sorted((r["effective_from"], r["effective_to"], r["schedule_id"]) for r in rows)
    assert spans == [("2026-01-01", "2026-10-31", a_id), ("2026-11-01", "2026-11-30", b_id),
                     ("2026-12-01", None, a_id)]
    assert old["id"] in {r["id"] for r in rows}
    # Phần nối lại cũng có dấu vết audit — không có dòng nào tự sinh ra mà không ai biết.
    resumed = next(r for r in rows if r["effective_from"] == "2026-12-01")
    assert db.query(AuditLog).filter_by(entity="work_schedule", entity_id=resumed["id"],
                                        action="create").count() == 1


def test_dong_khong_thoi_han_bat_dau_cung_ngay_hoac_sau_from_moi_thi_400_va_khong_bi_dong(api):
    sid = _mk_schedule(api)["id"]
    old = api.post("/api/work-schedule-assignments", json=_assign_body(1, 0, sid, "2026-05-01")).json()["data"]
    cases = [
        _assign_body(1, 0, sid, "2026-05-01"),                 # cùng ngày bắt đầu
        _assign_body(1, 0, sid, "2026-03-01"),                 # dòng cũ bắt đầu SAU from mới
        _assign_body(1, 0, sid, "2026-03-01", "2026-05-01"),   # mới có hạn, chạm ngày đầu dòng cũ
    ]
    for body in cases:
        assert api.post("/api/work-schedule-assignments", json=body).status_code == 400, body
    assert api.get(f"/api/work-schedule-assignments/{old['id']}").json()["data"]["effective_to"] is None
    # Mới có hạn và kết thúc TRƯỚC dòng cũ thì không chồng.
    assert api.post("/api/work-schedule-assignments",
                    json=_assign_body(1, 0, sid, "2026-03-01", "2026-04-30")).status_code == 201


def test_gan_moi_bat_dau_sau_dong_cu_co_han_ma_chong_van_400(api):
    sid = _mk_schedule(api)["id"]
    api.post("/api/work-schedule-assignments", json=_assign_body(1, 0, sid, "2026-01-01", "2026-06-30"))
    res = api.post("/api/work-schedule-assignments", json=_assign_body(1, 0, sid, "2026-06-01"))
    assert res.status_code == 400    # dòng cũ CÓ hạn → không tự đóng


def test_patch_khong_bao_gio_tu_dong_va_khong_tu_chan_chinh_no(api):
    sid = _mk_schedule(api)["id"]
    a = api.post("/api/work-schedule-assignments", json=_assign_body(1, 0, sid, "2026-01-01", "2026-03-31")).json()["data"]
    b = api.post("/api/work-schedule-assignments", json=_assign_body(1, 0, sid, "2026-04-01")).json()["data"]
    # Sửa chính nó (đổi ghi chú) không bị chặn bởi chính nó.
    assert api.patch(f"/api/work-schedule-assignments/{a['id']}", json={"note": "x"}).status_code == 200
    # Kéo dài `a` chồng lên `b` → 400, và `b` KHÔNG bị đóng.
    res = api.patch(f"/api/work-schedule-assignments/{a['id']}", json={"effective_to": "2026-05-31"})
    assert res.status_code == 400
    assert api.get(f"/api/work-schedule-assignments/{b['id']}").json()["data"]["effective_to"] is None
    # Mở `a` thành không thời hạn cũng chồng `b`.
    assert api.patch(f"/api/work-schedule-assignments/{a['id']}", json={"effective_to": None}).status_code == 400
    # Rút ngắn thì được; đổi cấp sang SYSTEM kèm đích → 400.
    assert api.patch(f"/api/work-schedule-assignments/{a['id']}", json={"effective_to": "2026-02-28"}).status_code == 200
    assert api.patch(f"/api/work-schedule-assignments/{a['id']}", json={"target_id": 7}).status_code == 400


def test_xoa_gan_roi_dem_assignment_count_ve_0(api):
    sid = _mk_schedule(api)["id"]
    a = api.post("/api/work-schedule-assignments", json=_assign_body(1, 0, sid, "2026-01-01")).json()["data"]
    assert api.get(f"/api/work-schedules/{sid}").json()["data"]["assignment_count"] == 1
    assert api.delete(f"/api/work-schedule-assignments/{a['id']}").status_code == 200
    assert api.get(f"/api/work-schedules/{sid}").json()["data"]["assignment_count"] == 0
    assert api.get(f"/api/work-schedule-assignments/{a['id']}").status_code == 404


def test_tools_effective_fallback_co_gan_va_ngoai_pham_vi(api, db, cap_quyen):
    company, dept, emp = api.world
    res = api.get(f"/api/work-schedules/tools/effective?employee_id={emp.id}&on_date=2026-01-05").json()["data"]
    assert res["is_fallback"] and res["schedule_id"] == 0 and res["level"] == 0
    sid = _mk_schedule(api)["id"]
    api.post("/api/work-schedule-assignments", json=_assign_body(3, dept.id, sid, "2026-01-01"))
    res = api.get(f"/api/work-schedules/tools/effective?employee_id={emp.id}&on_date=2026-01-05").json()["data"]
    assert res["schedule_name"] == "Mẫu A" and res["level_label"] == "Phòng ban"
    assert res["target_name"] == dept.name and res["effective_from"] == "2026-01-01"
    assert api.get("/api/work-schedules/tools/effective?employee_id=99999").status_code == 404
    assert api.get(f"/api/work-schedules/tools/effective?employee_id={emp.id}&on_date=1900-01-01").status_code == 422

    # Người chỉ có `employee.read` phạm vi «own» KHÔNG được xem lịch của người khác.
    _, _, other = make_world(db, "AP2")
    user2 = User(email="nv2@dego.vn", employee_id=other.id, is_active=True)
    db.add(user2)
    db.commit()
    cap_quyen(user2.id, "employee", scope="own", read=True)
    app.dependency_overrides[get_current_user] = lambda: user2
    assert api.get(f"/api/work-schedules/tools/effective?employee_id={emp.id}").status_code == 404
    assert api.get(f"/api/work-schedules/tools/effective?employee_id={other.id}").status_code == 200


def test_khong_co_quyen_ghi_thi_bi_chan(api, db, cap_quyen):
    _, _, emp = api.world
    user3 = User(email="doc@dego.vn", employee_id=emp.id, is_active=True)
    db.add(user3)
    db.commit()
    cap_quyen(user3.id, "work_schedule", scope="all", read=True)
    app.dependency_overrides[get_current_user] = lambda: user3
    assert api.get("/api/work-schedules").status_code == 200
    assert api.post("/api/work-schedules", json=_body()).status_code == 403
    assert api.post("/api/work-schedule-assignments", json=_assign_body()).status_code == 403
    assert api.delete("/api/work-schedules/1").status_code == 403
