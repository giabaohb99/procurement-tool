"""duoc-CR-689 — báo cáo F1 «Sử dụng phòng họp» (khóa 28): `/api/room-usage/summary` (+ export, rows).

Canh: định nghĩa chỉ số (phiếu đã duyệt tính giờ, hủy / từ chối chỉ vào tỷ lệ hủy, giờ làm việc theo lịch hệ
thống trừ lễ), các chiều xem (phòng, pháp nhân, phòng ban, khung giờ, thứ), phạm vi, danh sách `/rows`,
gác khóa báo cáo ở cả ba đường và số truy vấn CỐ ĐỊNH.
"""
import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.report_keys import ReportKey
from app.core.report_period import parse_period
from app.core.scoping import apply_scope
from app.core.subject_match import SUBJECT_EMPLOYEE
from app.main import app
from app.modules.leave.catalog_model import Holiday
from app.modules.meeting_room import report_service as service
from app.modules.meeting_room.constants import RB_APPROVED, RB_CANCELLED, RB_DRAFT, RB_REJECTED
from app.modules.meeting_room.model import MeetingRoom, RoomBooking
from app.modules.report_access.model import ReportAccess

BASE = "/api/room-usage/summary"
P = {"preset": "custom", "date_from": "2026-06-01", "date_to": "2026-06-07", "compare": "none"}   # T2…CN
_seq = {"n": 0}


@pytest.fixture
def client_as(db):
    def make(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield make
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _room(db, world, code, cap, co="B") -> MeetingRoom:
    r = MeetingRoom(code=code, name=f"Phòng {code}", company_id=world.co[co], capacity=cap, is_active=True)
    db.add(r)
    db.flush()
    return r


def _bk(db, world, room, start, end, *, status=RB_APPROVED, people=0, dept="B.hc", co="B") -> RoomBooking:
    _seq["n"] += 1
    b = RoomBooking(code=f"RB{_seq['n']:05d}", room_id=room.id, company_id=world.co[co],
                    department_id=world.dept[dept], title=f"Họp {_seq['n']}", status=status,
                    start_at=datetime.fromisoformat(start), end_at=datetime.fromisoformat(end),
                    attendee_count=people)
    db.add(b)
    db.flush()
    return b


def _setup(db, world):
    r1, r2 = _room(db, world, "P1", 10), _room(db, world, "P2", 0)
    _bk(db, world, r1, "2026-06-02T09:00", "2026-06-02T11:00", people=5)                    # T3
    _bk(db, world, r1, "2026-06-02T14:00", "2026-06-02T15:00", people=15, dept="B.kt")
    _bk(db, world, r1, "2026-06-03T09:00", "2026-06-03T10:00", status=RB_CANCELLED, people=4)
    _bk(db, world, r1, "2026-06-04T09:00", "2026-06-04T10:00", status=RB_REJECTED)
    _bk(db, world, r1, "2026-06-04T10:00", "2026-06-04T11:00", status=RB_DRAFT)             # bỏ qua
    _bk(db, world, r2, "2026-06-04T13:00", "2026-06-04T14:00", people=3)
    _bk(db, world, r2, "2026-05-30T09:00", "2026-05-30T10:00", people=3)                    # ngoài kỳ
    db.commit()
    return r1, r2


def _actor(db, world, client_as, scope="all", report=True, key="a1"):
    world.grant(key, "room_booking", scope, actions=("read", "export"))
    actor = world.actor(key)
    if report:
        db.add(ReportAccess(report_key=int(ReportKey.ROOM_USAGE), subject_kind=SUBJECT_EMPLOYEE,
                            subject_id=actor.employee.id, effect=1, reason="t", created_by=0, updated_by=0))
        db.commit()
    return actor, client_as(actor.user)


def _get(client, path=BASE, **extra):
    return client.get(path, params={**P, **extra})


def test_dinh_nghia_chi_so(db, world, client_as):
    _setup(db, world)
    _, client = _actor(db, world, client_as)
    resp = _get(client)
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    cur = data["totals"]["current"]
    assert cur["bookings"] == 3 and cur["booked_hours"] == 4
    assert cur["cancelled"] == 2
    assert cur["available_hours"] == 96                    # 2 phòng × 6 ngày làm (T2–T7) × 8 giờ
    assert cur["occupancy"] == round(4 / 96 * 100, 1)
    assert cur["cancel_rate"] == 40.0                      # 2 / (3 + 2)
    assert cur["attendees_avg"] == round(23 / 3, 1)
    assert cur["capacity_use"] == 100.0                    # (5+15) / (10+10); phòng sức chứa 0 bỏ khỏi mẫu số
    assert data["meta"]["group_by"] == "room" and data["meta"]["drilldown_metrics"] == [
        "bookings", "booked_hours", "cancelled"]
    meta = {m["key"]: m for m in data["meta"]["metrics"]}
    assert meta["occupancy"]["additive"] is False and meta["bookings"]["additive"] is True


def test_nhom_theo_phong_va_ngay_le(db, world, client_as):
    r1, _ = _setup(db, world)
    db.add(Holiday(company_id=0, date=__import__("datetime").date(2026, 6, 5), name="Lễ", is_recurring=False,
                   is_active=True))
    db.commit()
    _, client = _actor(db, world, client_as)
    groups = {g["label"]: g["current"] for g in _get(client).json()["data"]["groups"]}
    assert groups["P1 — Phòng P1"]["available_hours"] == 40 and groups["P1 — Phòng P1"]["bookings"] == 2
    assert groups["P1 — Phòng P1"]["occupancy"] == round(3 / 40 * 100, 1)
    assert groups["P2 — Phòng P2"]["bookings"] == 1


def test_cac_chieu_khac(db, world, client_as):
    _setup(db, world)
    _, client = _actor(db, world, client_as)
    hour = {g["label"]: g["current"] for g in _get(client, group_by="hour").json()["data"]["groups"]}
    assert hour["9h"]["bookings"] == 1 and hour["9h"]["available_hours"] == 12      # 2 phòng × 6 ngày × 1 giờ
    assert "12h" not in hour                                                         # nghỉ trưa không có sức chứa
    total = _get(client, group_by="hour").json()["data"]["totals"]["current"]
    assert total["available_hours"] == 96
    wd = {g["label"]: g["current"] for g in _get(client, group_by="weekday").json()["data"]["groups"]}
    assert wd["Thứ ba"]["bookings"] == 2 and wd["Thứ ba"]["available_hours"] == 16
    dept = _get(client, group_by="department").json()["data"]["groups"]
    labels = {g["label"]: g["current"] for g in dept}
    assert "Phòng Hành chính" in labels and "Phòng Kế toán" in labels and len(dept) == 2
    assert labels["Phòng Hành chính"]["occupancy"] is None                           # phòng ban đặt: không có giờ làm việc
    co = _get(client, group_by="company").json()["data"]["groups"]
    assert len(co) == 1 and co[0]["current"]["bookings"] == 3
    assert _get(client, group_by="bogus").status_code == 422


def test_xem_theo_gio_chia_gio_phieu_vao_tung_khung_ke_ca_23h(db, world, client_as):
    r1 = _room(db, world, "P1", 10)
    _bk(db, world, r1, "2026-06-02T09:30", "2026-06-02T11:15", people=4)         # 9h .5 · 10h 1 · 11h .25
    _bk(db, world, r1, "2026-06-02T22:30", "2026-06-03T00:00", people=2)         # 22h .5 · 23h 1
    db.commit()
    _, client = _actor(db, world, client_as)
    data = _get(client, group_by="hour").json()["data"]
    hour = {g["label"]: g["current"] for g in data["groups"]}
    assert (hour["9h"]["booked_hours"], hour["10h"]["booked_hours"], hour["11h"]["booked_hours"]) == (0.5, 1, 0.25)
    assert hour["22h"]["booked_hours"] == 0.5 and hour["23h"]["booked_hours"] == 1
    assert hour["9h"]["bookings"] == 1 and hour["10h"]["bookings"] == 0 and hour["23h"]["bookings"] == 0
    assert hour["22h"]["bookings"] == 1                                            # lượt đặt chỉ ở khung bắt đầu
    assert data["totals"]["current"]["bookings"] == 2 and data["totals"]["current"]["booked_hours"] == 3.25
    assert hour["10h"]["available_hours"] == 6                                     # 6 ngày làm × 1 giờ
    assert all(h["occupancy"] is None or h["occupancy"] <= 100 for h in hour.values() if h["available_hours"])
    rows = _get(client, BASE + "/rows", metric="booked_hours", group_by="hour", group_key="10").json()["data"]
    assert rows["total"] == 1                                                      # phiếu 09:30–11:15 nằm ở khung 10h
    assert _get(client, BASE + "/rows", metric="bookings", group_by="hour", group_key="10").json()["data"]["total"] == 0


def test_loc_phong_ban_dat_va_phap_nhan(db, world, client_as):
    _setup(db, world)
    _, client = _actor(db, world, client_as)
    cur = _get(client, department_id=world.dept["B.kt"]).json()["data"]["totals"]["current"]
    assert cur["bookings"] == 1 and cur["available_hours"] == 0 and cur["occupancy"] is None
    other = _get(client, company_id=world.co["A"]).json()["data"]["totals"]["current"]
    assert other["bookings"] == 0 and other["available_hours"] == 0


def test_pham_vi_chi_thay_phieu_trong_pham_vi(db, world, client_as):
    _setup(db, world)
    _, client = _actor(db, world, client_as, scope="dept")        # a1 ở A.kt, phiếu đều thuộc B
    assert _get(client).json()["data"]["totals"]["current"]["bookings"] == 0


def test_rows_khop_so(db, world, client_as):
    _setup(db, world)
    _, client = _actor(db, world, client_as)
    rows = _get(client, BASE + "/rows", metric="bookings").json()["data"]
    assert rows["total"] == 3 and [c["key"] for c in rows["columns"]] == [
        "code", "room", "title", "requester", "department", "start_at", "end_at", "attendees", "status"]
    assert all(r["status"] == "Đã duyệt" and r["link"].startswith("/hr/room-bookings/") for r in rows["rows"])
    canc = _get(client, BASE + "/rows", metric="cancelled").json()["data"]
    assert canc["total"] == 2 and {r["status"] for r in canc["rows"]} == {"Đã hủy", "Từ chối"}
    grp = _get(client, BASE + "/rows", metric="bookings", group_by="weekday", group_key="2").json()["data"]
    assert grp["total"] == 2
    hr = _get(client, BASE + "/rows", metric="bookings", group_by="hour", group_key="13").json()["data"]
    assert hr["total"] == 1
    for bad in ({"metric": "occupancy"}, {}, {"metric": "bookings", "group_by": "room", "group_key": "__other__"},
                {"metric": "bookings", "group_by": "bogus", "group_key": "1"}):
        assert _get(client, BASE + "/rows", **bad).status_code == 422


@pytest.mark.parametrize("suffix", ["", "/export", "/rows"])
def test_chua_giao_bao_cao_403_ca_ba_duong(db, world, client_as, suffix):
    _, client = _actor(db, world, client_as, report=False)
    assert _get(client, BASE + suffix, metric="bookings").status_code == 403


def test_export_xlsx(db, world, client_as):
    _setup(db, world)
    _, client = _actor(db, world, client_as)
    r = _get(client, BASE + "/export", group_by="room")
    assert r.status_code == 200 and "spreadsheetml" in r.headers["content-type"]


def test_so_truy_van_khong_tang_theo_so_phieu(db, world):
    world.grant("a1", "room_booking", "all", actions=("read",))
    actor = world.actor("a1")
    prof = actor.profile()
    period = parse_period({**P, "compare": "previous"})
    room = _room(db, world, "Q1", 10)

    def count(group_by) -> int:
        stmts: list[str] = []

        def listener(conn, cur, stmt, *args):
            stmts.append(stmt)

        eng = db.get_bind()
        event.listen(eng, "before_cursor_execute", listener)
        try:
            service.build_summary(db, apply_scope(db.query(RoomBooking), RoomBooking, "room_booking", actor.user,
                                                  prof), period, group_by)
        finally:
            event.remove(eng, "before_cursor_execute", listener)
        return len(stmts)

    def add(n):
        for i in range(n):
            _bk(db, world, room, "2026-06-02T09:00", "2026-06-02T10:00", people=i)
        db.commit()

    add(5)
    c5 = {g: count(g) for g in ("room", "hour", "department")}
    add(45)
    assert all(v > 0 for v in c5.values()) and c5 == {g: count(g) for g in c5}
