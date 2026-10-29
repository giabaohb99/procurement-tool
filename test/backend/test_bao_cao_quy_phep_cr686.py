"""duoc-CR-686 — Báo cáo Quỹ phép năm (C2): `employee_status`, lọc phòng ban, chỉ số mới,
«Chưa được cấp quỹ» và danh sách «bấm số» `/api/leave-balances/summary/rows`."""
import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.report_keys import ReportKey
from app.core.report_period import parse_period
from app.core.subject_match import SUBJECT_ROLE
from app.main import app
from app.modules.employee.model import Employee
from app.modules.leave import balance_report_service
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.balance_report_spec import valid_employee_status
from app.modules.leave.catalog_model import LeaveType

YEAR = {"preset": "custom", "date_from": "2026-01-01", "date_to": "2026-12-31", "compare": "none"}
ROWS = "/api/leave-balances/summary/rows"


def _type(db, code, counts=True):
    lt = LeaveType(code=code, name=f"Loại {code}", counts_balance=counts)
    db.add(lt)
    db.flush()
    return lt


def _emp(db, world, code, dept="A.kt", **kw):
    e = Employee(code=code, full_name=f"NV {code}", company_id=world.co["A"],
                 department_id=world.dept[dept], hire_date=date(2020, 1, 1), **kw)
    db.add(e)
    db.flush()
    return e


def _bal(db, world, emp, lt, **kw):
    db.add(LeaveBalance(employee_id=emp.id, year=2026, leave_type_id=lt.id,
                        company_id=world.co["A"], **kw))


@pytest.fixture
def setup(db, world):
    """4 nhân sự: VUOT (còn -1), CHUA (cấp 12, chưa dùng), HET (đã nghỉ việc), THIEU (không quỹ)."""
    world.grant("a1", "leave_balance", scope="all", actions=("read",))
    world.grant("a1", "employee", scope="all", actions=("read",))
    #  Nhân sự của thế giới mẫu không có quỹ nào — cho nghỉ việc để không lẫn vào số «chưa được cấp».
    db.query(Employee).update({Employee.status: "resigned"})
    lt = _type(db, "PN")
    vuot, chua = _emp(db, world, "VUOT"), _emp(db, world, "CHUA", dept="A.mua")
    het = _emp(db, world, "HET", status="resigned", resign_date=date(2026, 3, 1))
    _emp(db, world, "THIEU")
    _bal(db, world, vuot, lt, allocated_days=10, seniority_days=1, carried_days=2, adjusted_days=-1,
         used_days=13, carried_expired_days=1.5)
    _bal(db, world, chua, lt, allocated_days=12)
    _bal(db, world, het, lt, allocated_days=12, used_days=3)
    db.commit()
    return world.actor("a1")


def _summary(db, actor, **kw):
    return balance_report_service.build_summary(db, actor.user, actor.profile(), parse_period(YEAR),
                                                kw.pop("group_by", None), **kw)


class TestTrangThaiNhanSu:
    def test_mac_dinh_chi_nguoi_dang_lam(self, db, world, setup):
        t = _summary(db, setup)["totals"]["current"]
        assert t["granted"] == 10 + 1 + 2 - 1 + 12      # VUOT + CHUA, không có HET

    def test_resigned_va_all(self, db, world, setup):
        assert _summary(db, setup, employee_status="resigned")["totals"]["current"]["granted"] == 12
        assert _summary(db, setup, employee_status="all")["totals"]["current"]["granted"] == 36

    def test_gia_tri_la_422(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as e:
            valid_employee_status("nope")
        assert e.value.status_code == 422
        assert valid_employee_status("") == "working" and valid_employee_status("all") == "all"


class TestLocPhongBan:
    def test_theo_phong_hien_tai_cua_nguoi_giu_quy(self, db, world, setup):
        t = _summary(db, setup, department_id=world.dept["A.mua"])["totals"]["current"]
        assert t["granted"] == 12 and t["people_unused"] == 1

    def test_khong_mo_rong_pham_vi(self, db, world, setup):
        world.grant("a2", "leave_balance", scope="own", actions=("read",))
        a2 = world.actor("a2")
        t = _summary(db, a2, department_id=world.dept["A.mua"])["totals"]["current"]
        assert t["granted"] == 0


class TestChiSoMoi:
    def test_cau_phan_va_dem_nguoi(self, db, world, setup):
        t = _summary(db, setup)["totals"]["current"]
        assert (t["allocated"], t["seniority"], t["carried"], t["adjusted"]) == (22, 1, 2, -1)
        assert t["carried_expired"] == 1.5
        assert t["people_over_quota"] == 1      # VUOT: 12 - 13 = -1
        assert t["people_unused"] == 1          # CHUA

    def test_chua_duoc_cap_quy_chi_o_tong(self, db, world, setup):
        data = _summary(db, setup, group_by="department")
        assert data["totals"]["current"]["people_missing_balance"] == 1      # THIEU
        assert all("people_missing_balance" not in g["current"] for g in data["groups"])
        meta = {m["key"]: m for m in data["meta"]["metrics"]}
        assert meta["people_missing_balance"]["snapshot"] is True

    def test_loai_khong_tinh_quy_khong_coi_la_co_quy(self, db, world, setup):
        kl = _type(db, "KL", counts=False)
        thieu = db.query(Employee).filter_by(code="THIEU").one()
        _bal(db, world, thieu, kl, allocated_days=5)
        db.commit()
        assert _summary(db, setup)["totals"]["current"]["people_missing_balance"] == 1

    def test_nguoi_vao_sau_nam_va_nguoi_da_nghi_khong_tinh(self, db, world, setup):
        _emp(db, world, "MOI2027").hire_date = date(2027, 2, 1)
        db.commit()
        assert _summary(db, setup)["totals"]["current"]["people_missing_balance"] == 1
        assert _summary(db, setup, employee_status="resigned")["totals"]["current"]["people_missing_balance"] == 0


class TestChuaNghiTheoNguoi:
    def test_da_nghi_phep_nam_con_quy_om_chua_dung_khong_tinh(self, db, world, setup):
        om = _type(db, "OM")
        vuot = db.query(Employee).filter_by(code="VUOT").one()
        chua = db.query(Employee).filter_by(code="CHUA").one()
        _bal(db, world, vuot, om, allocated_days=5)    # VUOT: quỹ ốm chưa đụng, nhưng đã dùng phép năm
        _bal(db, world, chua, om, allocated_days=5)    # CHUA: cả hai quỹ chưa đụng → vẫn tính
        db.commit()
        t = _summary(db, setup)["totals"]["current"]
        assert t["people_unused"] == 1                 # chỉ CHUA (không phải 2 dòng, không phải VUOT)
        by_type = {g["label"]: g["current"]["people_unused"]
                   for g in _summary(db, setup, group_by="leave_type")["groups"]}
        assert by_type["Loại OM"] == 1 and by_type["Loại PN"] == 1

    def test_drilldown_mot_dong_moi_nguoi_khop_con_so(self, db, world, setup):
        om = _type(db, "OM")
        for code in ("VUOT", "CHUA"):
            _bal(db, world, db.query(Employee).filter_by(code=code).one(), om, allocated_days=5,
                 used_days=6 if code == "VUOT" else 0)
        db.commit()
        from app.modules.leave import balance_report_drill_rows as drill
        from app.core.report_period import parse_period as pp
        for metric in ("people_over_quota", "people_unused"):
            d = drill.build_rows(db, setup.user, setup.profile(), pp(YEAR), {"metric": metric},
                                 None, None, "working")
            n = _summary(db, setup)["totals"]["current"][metric]
            assert d["total"] == n == len({r["employee_code"] for r in d["rows"]})
        d = drill.build_rows(db, setup.user, setup.profile(), pp(YEAR), {"metric": "people_unused"},
                             None, None, "working")
        assert d["rows"][0]["allocated"] == 17 and d["rows"][0]["leave_type"] == "Loại OM, Loại PN"


@pytest.fixture
def http(db):
    def call(user, path, **params):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            client = TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})
            return client.get(path, params=params)
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.dependency_overrides.pop(get_current_user, None)
    return call


class TestDanhSachBamSo:
    @pytest.fixture(autouse=True)
    def _gan(self, setup, gan_bao_cao):
        gan_bao_cao(SUBJECT_ROLE, setup.roles[-1].id, ReportKey.LEAVE_BALANCE)

    def test_meta_drilldown(self, db, setup):
        assert _summary(db, setup)["meta"]["drilldown_metrics"] == [
            "remaining", "people_over_quota", "people_unused", "carried_expired",
            "people_missing_balance"]

    def test_khop_tung_chi_so(self, db, setup, http):
        def rows(metric, **kw):
            r = http(setup.user, ROWS, metric=metric, **YEAR, **kw)
            assert r.status_code == 200, r.text
            return r.json()["data"]
        assert [r["employee_code"] for r in rows("remaining")["rows"]] == ["CHUA", "VUOT"]
        over = rows("people_over_quota")
        assert [r["employee_code"] for r in over["rows"]] == ["VUOT"] and over["rows"][0]["remaining"] == -1
        assert [r["employee_code"] for r in rows("people_unused")["rows"]] == ["CHUA"]
        assert [r["employee_code"] for r in rows("carried_expired")["rows"]] == ["VUOT"]
        miss = rows("people_missing_balance")
        assert [r["employee_code"] for r in miss["rows"]] == ["THIEU"]
        assert [c["key"] for c in miss["columns"]] == ["employee_code", "employee_name", "company",
                                                        "department", "hire_date"]

    def test_loc_nhom_phong_ban_va_trang_thai(self, db, setup, world, http):
        r = http(setup.user, ROWS, metric="remaining", group_by="department",
                 group_key=str(world.dept["A.mua"]), **YEAR).json()["data"]
        assert [x["employee_code"] for x in r["rows"]] == ["CHUA"]
        r = http(setup.user, ROWS, metric="remaining", employee_status="all", **YEAR).json()["data"]
        assert r["total"] == 3

    def test_metric_la_422_va_employee_status_la_422(self, db, setup, http):
        assert http(setup.user, ROWS, metric="x", **YEAR).status_code == 422
        assert http(setup.user, ROWS, metric="remaining", employee_status="zzz", **YEAR).status_code == 422

    def test_thieu_quyen_bao_cao_403(self, db, world, http):
        world.grant("a3", "leave_balance", scope="all", actions=("read",))
        assert http(world.actor("a3").user, ROWS, metric="remaining", **YEAR).status_code == 403
