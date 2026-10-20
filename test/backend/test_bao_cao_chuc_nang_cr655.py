"""duoc-CR-655 (D0c) — báo cáo «Mức dùng chức năng»: gom ngày, API gom theo chức năng/phòng ban, gác ReportKey 15, số truy vấn cố định.

Đi qua `TestClient` vì `require_report` gắn ở `dependencies=[...]`. Ngày gom dùng mốc 2026-01 nên `force=True`
(ngày đã quá hạn giữ sự kiện thô — chỉ test mới cần).
"""
import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.report_keys import REPORT_META, ReportKey
from app.core.subject_match import SUBJECT_ROLE
from app.core.ui_action_codes import UiAction
from app.core.usage_codes import FeatureKind as K
from app.core.usage_codes import UiEventType as E
from app.core.usage_codes import UiForm
from app.main import app
from app.modules.feature_usage import daily_builder
from app.modules.feature_usage.model import FeatureUsageDaily
from app.modules.report_access.seed_defaults import ensure_report_access_defaults
from app.modules.role.model import Permission, Role
from app.modules.usage_profile.model import UiEvent, UsageDaily
from app.modules.user.model import UserRole

from ho_so_lam_viec_factory import MON, TUE, make_company, make_dept, make_person, vn
from lich_lam_viec_factory import count_queries

ROOT = "/api/feature-usage"
PERIOD = {"preset": "custom", "date_from": "2026-01-05", "date_to": "2026-01-11"}


@pytest.fixture
def client_as(db):
    def make(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield make
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def admin(db, cap_quyen, gan_bao_cao):
    user, _ = make_person(db, "ADM")
    role = cap_quyen(user.id, "setting", scope="all", read=True, export=True)
    gan_bao_cao(SUBJECT_ROLE, role.id, ReportKey.FEATURE_USAGE)
    db.commit()
    return user


def ev(db, user, day, hhmm, etype, route="/pr", form=0, action=0, duration=0, result=None):
    db.add(UiEvent(user_id=user.id, occurred_at=vn(day, hhmm), event_type=int(etype), route_pattern=route,
                   form_key=form, action_key=action, duration_ms=duration, result_count=result))


@pytest.fixture
def world(db):
    """Hai phòng ban; 3 người. A,B ở phòng 1; C ở phòng 2. Sự kiện hai ngày."""
    co = make_company(db, "C1")
    d1, d2 = make_dept(db, co, "D1"), make_dept(db, co, "D2")
    (a, ea), (b, eb), (c, ec) = (make_person(db, "A", co, d1), make_person(db, "B", co, d1), make_person(db, "C", co, d2))
    for day in (MON, TUE):
        for u, e, d in ((a, ea, d1), (b, eb, d1), (c, ec, d2)):
            db.add(UsageDaily(user_id=u.id, day=day, employee_id=e.id, company_id=co.id, department_id=d.id, active=True))
    # A bấm Xuất Excel 2 lần thứ Hai + 1 lần thứ Ba; B 1 lần thứ Hai; C không bấm
    for _ in range(2):
        ev(db, a, MON, "09:00", E.UI_ACTION, action=int(UiAction.EXPORT_EXCEL))
    ev(db, a, TUE, "09:00", E.UI_ACTION, action=int(UiAction.EXPORT_EXCEL))
    ev(db, b, MON, "09:10", E.UI_ACTION, action=int(UiAction.EXPORT_EXCEL), route="/po")
    # Form YCMH: A mở 2 gửi 1 bỏ 1; C mở 1 bỏ 1
    for t in (E.FORM_OPEN, E.FORM_OPEN, E.FORM_SUBMIT, E.FORM_ABANDON):
        ev(db, a, MON, "10:00", t, route="/pr/new", form=int(UiForm.PURCHASE_REQUEST), duration=1000 if t == E.FORM_SUBMIT else 0)
    for t in (E.FORM_OPEN, E.FORM_ABANDON):
        ev(db, c, MON, "10:00", t, route="/pr/new", form=int(UiForm.PURCHASE_REQUEST))
    # màn hình + tìm kiếm + lỗi
    ev(db, a, MON, "08:00", E.PAGE_VIEW, route="/pr")
    ev(db, a, MON, "08:05", E.PAGE_LEAVE, route="/pr", duration=5000)
    ev(db, c, MON, "08:00", E.PAGE_VIEW, route="/pr")
    ev(db, a, MON, "08:10", E.SEARCH, route="/pr", result=0)
    ev(db, a, MON, "08:11", E.SEARCH, route="/pr", result=3)
    ev(db, b, MON, "08:12", E.CLIENT_ERROR, route="/po")
    db.commit()
    for day in (MON, TUE):
        daily_builder.aggregate_day(db, day, force=True)
    return {"co": co, "d1": d1, "d2": d2, "people": (a, b, c)}


# ── gom ngày ────────────────────────────────────────────────────────────────

def test_gom_ngay_dung_dong_va_cot(db, world):
    a, b, c = world["people"]
    rows = db.query(FeatureUsageDaily).filter_by(day=MON, user_id=a.id).all()
    by = {(r.kind, r.code, r.route): r for r in rows}
    assert by[(int(K.ACTION), int(UiAction.EXPORT_EXCEL), "/pr")].uses == 2
    form = by[(int(K.FORM), int(UiForm.PURCHASE_REQUEST), "")]
    assert (form.uses, form.completes, form.abandons, form.duration_ms) == (2, 1, 1, 1000)
    screen = by[(int(K.SCREEN), 0, "/pr")]
    assert (screen.uses, screen.duration_ms) == (1, 5000)
    search = by[(int(K.SEARCH), 0, "/pr")]
    assert (search.uses, search.fails) == (2, 1)
    assert rows[0].department_id == world["d1"].id and rows[0].company_id == world["co"].id


def test_gom_hai_lan_khong_nhan_doi(db, world):
    before = db.query(FeatureUsageDaily).count()
    daily_builder.aggregate_day(db, MON, force=True)
    assert db.query(FeatureUsageDaily).count() == before


def test_ngay_qua_han_bi_tu_choi_khi_khong_force(db):
    from app.modules.usage_profile.daily_builder import DayTooOldError
    with pytest.raises(DayTooOldError):
        daily_builder.aggregate_day(db, date(2026, 1, 5))


def test_su_kien_khong_co_ma_bi_bo_qua():
    rows = daily_builder.build_rows(MON, [(1, int(E.UI_ACTION), 0, 0, "/x", 3, 0, 0),
                                          (1, int(E.FORM_OPEN), 0, 0, "/x", 1, 0, 0)], {})
    assert rows == []


# ── API ─────────────────────────────────────────────────────────────────────

def test_summary_dem_nguoi_khac_nhau_qua_nhieu_ngay(db, world, admin, client_as):
    data = client_as(admin).get(f"{ROOT}/summary", params=PERIOD).json()["data"]
    export = next(i for i in data["actions"] if i["code"] == int(UiAction.EXPORT_EXCEL) and i["route"] == "/pr")
    assert export["users"] == 1 and export["uses"] == 3     # A: 2 + 1 qua hai ngày, đếm 1 người
    all_export = [i for i in data["actions"] if i["code"] == int(UiAction.EXPORT_EXCEL)]
    assert sum(i["uses"] for i in all_export) == 4
    form = data["forms"][0]
    assert (form["code"], form["users"], form["uses"], form["completes"], form["abandons"]) == (
        int(UiForm.PURCHASE_REQUEST), 2, 3, 1, 2)
    assert data["active_users"] == 3 and data["has_data"] and data["tracking_since"] == "2026-01-05"
    assert int(UiAction.EXPORT_EXCEL) not in data["unused_actions"] and int(UiAction.PRINT) in data["unused_actions"]
    assert int(UiForm.PURCHASE_REQUEST) not in data["unused_forms"] and int(UiForm.WORK_TASK) in data["unused_forms"]
    assert data["errors"][0]["route"] == "/po" and data["errors"][0]["uses"] == 1


def test_summary_loc_phong_ban(db, world, admin, client_as):
    data = client_as(admin).get(f"{ROOT}/summary", params={**PERIOD, "department_id": world["d2"].id}).json()["data"]
    assert data["active_users"] == 1 and data["actions"] == []
    assert data["forms"][0]["users"] == 1 and int(UiAction.EXPORT_EXCEL) in data["unused_actions"]


def test_summary_khong_lo_user_id(db, world, admin, client_as):
    text = client_as(admin).get(f"{ROOT}/summary", params=PERIOD).text
    assert "user_id" not in text


def test_summary_ky_rong_has_data_false(db, admin, client_as):
    data = client_as(admin).get(f"{ROOT}/summary", params=PERIOD).json()["data"]
    assert data["has_data"] is False and data["tracking_since"] is None and data["active_users"] == 0


def test_breakdown_theo_phong_ban_va_man(db, world, admin, client_as):
    resp = client_as(admin).get(f"{ROOT}/breakdown", params={**PERIOD, "kind": int(K.ACTION),
                                                              "code": int(UiAction.EXPORT_EXCEL)})
    data = resp.json()["data"]
    assert [(d["department_id"], d["users"], d["uses"]) for d in data["by_department"]] == [(world["d1"].id, 2, 4)]
    assert data["by_department"][0]["department_name"] == "Phòng D1"
    assert {(r["route"], r["uses"]) for r in data["by_route"]} == {("/pr", 3), ("/po", 1)}
    assert "user_id" not in resp.text


def test_breakdown_kind_la_422(db, admin, client_as):
    assert client_as(admin).get(f"{ROOT}/breakdown", params={**PERIOD, "kind": 77}).status_code == 422


def test_so_truy_van_co_dinh(db, world, admin, client_as):
    client = client_as(admin)
    client.get(f"{ROOT}/summary", params=PERIOD)   # làm nóng cache quyền
    _, sql = count_queries(db, lambda: client.get(f"{ROOT}/summary", params=PERIOD))
    feature_sql = [s for s in sql if "tab_feature_usage_daily" in s or "tab_usage_daily" in s]
    assert len(feature_sql) == 3, feature_sql
    _, sql = count_queries(db, lambda: client.get(f"{ROOT}/breakdown", params={
        **PERIOD, "kind": int(K.ACTION), "code": int(UiAction.EXPORT_EXCEL)}))
    assert len([s for s in sql if "tab_feature_usage_daily" in s]) == 2


# ── gác ─────────────────────────────────────────────────────────────────────

def test_thieu_khoa_15_la_403_du_co_setting_read(db, cap_quyen, client_as):
    user, _ = make_person(db, "MGR")
    cap_quyen(user.id, "setting", scope="all", read=True, export=True)
    client = client_as(user)
    for path in (f"{ROOT}/summary", f"{ROOT}/summary/export", f"{ROOT}/breakdown?kind=1"):
        assert client.get(path, params=PERIOD).status_code == 403, path


def test_khong_co_setting_la_403(db, client_as):
    user, _ = make_person(db, "NV")
    assert client_as(user).get(f"{ROOT}/summary", params=PERIOD).status_code == 403


def test_admin_sau_seed_mac_dinh_duoc_200_va_xuat_excel(db, world, client_as):
    boss, _ = make_person(db, "BOSS")
    role = Role(code="admin", name="Quản trị hệ thống")
    db.add(role)
    db.flush()
    db.add(UserRole(user_id=boss.id, role_id=role.id))
    db.add(Permission(role_id=role.id, entity="setting", scope="all", can_read=True, can_export=True))
    db.commit()
    ensure_report_access_defaults(db)
    client = client_as(boss)
    assert client.get(f"{ROOT}/summary", params=PERIOD).status_code == 200
    resp = client.get(f"{ROOT}/summary/export", params=PERIOD)
    assert resp.status_code == 200 and resp.content[:2] == b"PK"


def test_xuat_excel_can_setting_export(db, world, cap_quyen, gan_bao_cao, client_as):
    user, _ = make_person(db, "RD")
    role = cap_quyen(user.id, "setting", scope="all", read=True)
    gan_bao_cao(SUBJECT_ROLE, role.id, ReportKey.FEATURE_USAGE)
    db.commit()
    client = client_as(user)
    assert client.get(f"{ROOT}/summary", params=PERIOD).status_code == 200
    assert client.get(f"{ROOT}/summary/export", params=PERIOD).status_code == 403


def test_khoa_15_co_nhan_va_nhom():
    assert ReportKey.FEATURE_USAGE == 15
    assert REPORT_META[ReportKey.FEATURE_USAGE] == ("Mức dùng chức năng", "Quản trị")
