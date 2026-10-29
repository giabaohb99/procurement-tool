"""duoc-CR-686 — Báo cáo Biến động nhân sự (A1): lọc phòng ban, ghi chú thiếu ngày vào làm,
danh sách «bấm số» `/api/employees/summary/rows`."""
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
from app.modules.employee import report_service
from app.modules.employee.model import Employee
from app.modules.employee.sensitive import SENSITIVE_FIELDS

SEP = {"preset": "custom", "date_from": "2026-09-01", "date_to": "2026-09-30", "compare": "none"}
ROWS = "/api/employees/summary/rows"


def _emp(db, world, code, dept="A.kt", co="A", **kw):
    e = Employee(code=code, full_name=f"NV {code}", company_id=world.co[co],
                 department_id=world.dept[dept], **kw)
    db.add(e)
    db.flush()
    return e


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


@pytest.fixture
def staff(db, world):
    """Kế toán: 1 vào mới (05/09), 1 nghỉ việc (20/09), 1 ổn định. Thu mua: 1 vào mới (10/09)."""
    world.grant("a1", "employee", scope="all", actions=("read",))
    _emp(db, world, "VAO1", hire_date=date(2026, 9, 5))
    _emp(db, world, "NGHI1", hire_date=date(2020, 1, 1), status="resigned", resign_date=date(2026, 9, 20))
    _emp(db, world, "ONDINH", hire_date=date(2020, 1, 1))
    _emp(db, world, "VAO2", dept="A.mua", hire_date=date(2026, 9, 10))
    db.commit()
    return world.actor("a1")


class TestLocPhongBan:
    def test_loc_phong_chi_dem_phong_do(self, db, world, staff):
        period = parse_period(SEP)
        allv = report_service.build_summary(db, staff.user, staff.profile(), period, None)
        kt = report_service.build_summary(db, staff.user, staff.profile(), period, None,
                                          department_id=world.dept["A.kt"])
        t_all, t_kt = allv["totals"]["current"], kt["totals"]["current"]
        assert (t_all["new_hires"], t_kt["new_hires"]) == (2, 1)
        assert t_kt["departures"] == 1 and t_kt["headcount_end"] == 2

    def test_khong_mo_rong_pham_vi(self, db, world, staff):
        world.grant("a2", "employee", scope="dept", actions=("read",))
        a2 = world.actor("a2")   # a2 thuộc phòng A.kt
        data = report_service.build_summary(db, a2.user, a2.profile(), parse_period(SEP), None,
                                            department_id=world.dept["A.mua"])
        assert data["totals"]["current"]["new_hires"] == 0


class TestGhiChu:
    def test_dem_ho_so_dang_lam_thieu_ngay_vao_va_sua_cau_lich_su(self, db, world, staff):
        _emp(db, world, "THIEU1")
        _emp(db, world, "THIEU2")
        _emp(db, world, "THIEU3", status="resigned", resign_date=date(2025, 1, 1))  # đã nghỉ: không đếm
        db.commit()
        data = report_service.build_summary(db, staff.user, staff.profile(), parse_period(SEP), None)
        notes = " ".join(data["notes"])
        #  Thế giới mẫu cũng có nhân sự không khai hire_date nên số cụ thể lấy thẳng từ DB.
        n = db.query(Employee).filter(Employee.status != "resigned", Employee.hire_date.is_(None)).count()
        assert f"Có {n} hồ sơ đang làm thiếu ngày vào làm" in notes
        assert "chưa lưu lịch sử điều chuyển" not in notes
        assert "Quá trình công tác" in notes


class TestDanhSachBamSo:
    @pytest.fixture(autouse=True)
    def _gan(self, staff, gan_bao_cao):
        gan_bao_cao(SUBJECT_ROLE, staff.roles[-1].id, ReportKey.HR_HEADCOUNT)

    def test_meta_co_drilldown_metrics(self, db, world, staff):
        meta = report_service.build_summary(db, staff.user, staff.profile(), parse_period(SEP), None)["meta"]
        assert meta["drilldown_metrics"] == ["new_hires", "departures", "headcount_end"]

    def test_vao_moi_khop_con_so_va_co_lien_ket(self, db, world, staff, http):
        d = http(staff.user, ROWS, metric="new_hires", **SEP).json()["data"]
        assert [r["code"] for r in d["rows"]] == ["VAO1", "VAO2"] and d["total"] == 2
        assert d["rows"][0]["link"].startswith("/hr/employees/")
        assert [c["key"] for c in d["columns"]] == ["code", "full_name", "company", "department",
                                                     "position", "hire_date", "resign_date", "status"]

    def test_nghi_viec_va_dinh_bien_cuoi_ky(self, db, world, staff, http):
        dep = http(staff.user, ROWS, metric="departures", **SEP).json()["data"]
        assert [r["code"] for r in dep["rows"]] == ["NGHI1"] and dep["rows"][0]["resign_date"] == "2026-09-20"
        end = http(staff.user, ROWS, metric="headcount_end", **SEP).json()["data"]
        total = report_service.build_summary(db, staff.user, staff.profile(), parse_period(SEP), None)
        assert end["total"] == total["totals"]["current"]["headcount_end"] == 3   # VAO1, ONDINH, VAO2

    def test_loc_nhom_phong_ban(self, db, world, staff, http):
        d = http(staff.user, ROWS, metric="headcount_end", group_by="department",
                 group_key=str(world.dept["A.mua"]), **SEP).json()["data"]
        assert [r["code"] for r in d["rows"]] == ["VAO2"]
        only = http(staff.user, ROWS, metric="headcount_end", department_id=world.dept["A.kt"], **SEP).json()["data"]
        assert {r["code"] for r in only["rows"]} == {"VAO1", "ONDINH"}

    def test_metric_la_422_nhom_gop_422(self, db, world, staff, http):
        assert http(staff.user, ROWS, metric="salary", **SEP).status_code == 422
        assert http(staff.user, ROWS, metric="new_hires", group_by="department",
                    group_key="__other__", **SEP).status_code == 422

    def test_thieu_hire_date_de_trong_khong_dien_ngay_tao(self, db, world, staff, http):
        _emp(db, world, "THIEU")
        db.commit()
        d = http(staff.user, ROWS, metric="headcount_end", department_id=world.dept["A.kt"],
                 preset="custom", date_from="2026-12-01", date_to="2026-12-31", compare="none").json()["data"]
        row = next(r for r in d["rows"] if r["code"] == "THIEU")
        assert row["hire_date"] is None

    def test_khong_lo_truong_nhay_cam(self, db, world, staff, http):
        d = http(staff.user, ROWS, metric="headcount_end", **SEP).json()["data"]
        keys = {c["key"] for c in d["columns"]} | {k for r in d["rows"] for k in r}
        assert not keys & set(SENSITIVE_FIELDS)

    def test_thieu_quyen_bao_cao_403(self, db, world, http):
        world.grant("a3", "employee", scope="all", actions=("read",))
        a3 = world.actor("a3")
        assert http(a3.user, ROWS, metric="new_hires", **SEP).status_code == 403
