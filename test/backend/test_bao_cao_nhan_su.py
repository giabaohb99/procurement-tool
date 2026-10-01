"""Phase 04 — Báo cáo Nhân sự: biến động & cơ cấu (`GET /api/employees/summary`).

Canh: phạm vi dữ liệu bậc `dept` áp đúng như bảng Nhân sự gốc; không lộ trường
nhạy cảm/chiều tuổi (R2 — `employee.sensitive.SENSITIVE_FIELDS`); nghỉ việc
thiếu `resign_date` không tính vào chỉ số; đường `/summary` không bị `/{id}`
nuốt; số truy vấn SQL CỐ ĐỊNH, không tăng theo số nhân sự.
"""
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import event
from starlette.datastructures import QueryParams

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.report_period import parse_period
from app.main import app
from app.modules.employee import report_controller, report_service
from app.modules.employee.model import Employee
from app.modules.employee.report_headcount_events import resign_events
from app.modules.employee.sensitive import SENSITIVE_FIELDS

PERIOD_09 = {"preset": "custom", "date_from": "2026-09-01", "date_to": "2026-09-30", "compare": "none"}


def _period():
    return parse_period(PERIOD_09)


def _assert_no_sensitive_keys(obj) -> None:
    """Duyệt đệ quy MỌI khóa trong JSON — không khóa nào trong `SENSITIVE_FIELDS`."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in SENSITIVE_FIELDS, f"khóa nhạy cảm lọt ra JSON: {k}"
            _assert_no_sensitive_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            _assert_no_sensitive_keys(v)


class TestPhamViDuLieu:
    def test_scope_dept_chi_dem_nhan_su_phong_minh(self, db, world):
        world.grant("a1", "employee", scope="dept", actions=("read",))
        db.add(Employee(code="PV01", full_name="Trong phong", company_id=world.co["A"],
                        department_id=world.dept["A.kt"], hire_date=date(2026, 9, 10)))
        db.add(Employee(code="PV02", full_name="Khac phong", company_id=world.co["A"],
                        department_id=world.dept["A.mua"], hire_date=date(2026, 9, 12)))
        db.commit()
        actor = world.actor("a1")

        data = report_service.build_summary(db, actor.user, actor.profile(), _period(), None)
        assert data["totals"]["current"]["new_hires"] == 1  # chỉ đếm người CÙNG PHÒNG A.kt


class TestKhongLoDuLieuNhayCam:
    def test_json_khong_chua_khoa_nhay_cam_va_khong_co_chieu_tuoi(self, db, world):
        world.grant("a1", "employee", scope="all", actions=("read",))
        actor = world.actor("a1")
        data = report_service.build_summary(db, actor.user, actor.profile(), _period(), "company")
        _assert_no_sensitive_keys(data)
        dim_keys = {d["key"] for d in data["meta"]["dimensions"]}
        assert not any("age" in k or "birth" in k or "tuoi" in k for k in dim_keys)


class TestNghiViecThieuNgay:
    def test_resigned_khong_co_resign_date_khong_tinh_vao_chi_so(self, db, world):
        world.grant("a1", "employee", scope="all", actions=("read",))
        db.add(Employee(code="NV_NV01", full_name="Nghi khong ngay", company_id=world.co["A"],
                        department_id=world.dept["A.kt"], status="resigned",
                        hire_date=date(2024, 1, 1), resign_date=None))
        db.commit()
        actor = world.actor("a1")

        data = report_service.build_summary(db, actor.user, actor.profile(), _period(), None)
        assert data["totals"]["current"]["departures"] == 0
        #  M3 (Q4.3): "đang làm" = status ≠ resigned — hồ sơ resigned THIẾU ngày cũng KHÔNG
        #  được coi là đang làm (trước đây lọt vào Định biên vì resign_date NULL luôn "chưa nghỉ").
        assert data["totals"]["current"]["headcount_end"] == 0
        assert any("thiếu ngày nghỉ việc" in n for n in data["notes"])
        assert any("không được coi là đang làm" in n for n in data["notes"])


class TestLocCongTy:
    """H1 — `company_id` lọc SAU `apply_scope`, chỉ THU HẸP thêm."""

    def test_chon_cong_ty_a_khong_thay_so_cong_ty_b(self, db, world):
        world.grant("a1", "employee", scope="all", actions=("read",))
        db.add(Employee(code="CTA1", full_name="Cty A", company_id=world.co["A"],
                        department_id=world.dept["A.kt"], hire_date=date(2026, 9, 10)))
        db.add(Employee(code="CTB1", full_name="Cty B", company_id=world.co["B"],
                        department_id=world.dept["B.kt"], hire_date=date(2026, 9, 12)))
        db.commit()
        actor = world.actor("a1")

        data = report_service.build_summary(db, actor.user, actor.profile(), _period(), None,
                                            company_id=world.co["A"])
        assert data["totals"]["current"]["new_hires"] == 1  # chỉ công ty A, không cộng công ty B

    def test_company_id_rac_nem_422(self, db, world):
        world.grant("a1", "employee", scope="all", actions=("read",))
        actor = world.actor("a1")
        request = SimpleNamespace(query_params=QueryParams(
            [("preset", "this_month"), ("company_id", "abc")]))
        with pytest.raises(HTTPException) as exc:
            report_controller.employee_summary(request, db=db, user=actor.user)
        assert exc.value.status_code == 422


class TestNhomCoCau:
    """Mục 4 — "Xem theo" phải hiện ĐỊNH BIÊN theo nhóm, kể cả nhóm không có sự kiện."""

    def test_phong_khong_su_kien_van_hien_dien_bien_va_sap_theo_dinh_bien_cuoi_ky(self, db, world):
        world.grant("a1", "employee", scope="all", actions=("read",))
        #  Phòng ỔN ĐỊNH: 3 người vào từ lâu, không ai vào/nghỉ trong kỳ 09/2026 → KHÔNG sự kiện.
        for i in range(3):
            db.add(Employee(code=f"ON{i}", full_name=f"Ổn định {i}", company_id=world.co["A"],
                            department_id=world.dept["A.kt"], hire_date=date(2020, 1, 1)))
        #  Phòng có 1 người VÀO MỚI trong kỳ → CÓ sự kiện.
        db.add(Employee(code="MOI1", full_name="Người mới", company_id=world.co["A"],
                        department_id=world.dept["A.mua"], hire_date=date(2026, 9, 5)))
        db.commit()
        actor = world.actor("a1")

        data = report_service.build_summary(db, actor.user, actor.profile(), _period(), "department")
        groups = {g["label"]: g for g in data["groups"]}
        assert groups["Phòng Kế toán"]["current"]["headcount_end"] == 3
        assert groups["Phòng Kế toán"]["current"]["new_hires"] == 0  # không sự kiện, vẫn phải hiện
        assert groups["Phòng Thu mua"]["current"]["headcount_end"] == 1
        order = [g["label"] for g in data["groups"]]
        assert order.index("Phòng Kế toán") < order.index("Phòng Thu mua")  # 3 > 1, xếp trước


class TestThamNienTinhTaiNgaySuKien:
    """Mục 5 — sự kiện NGHỈ tính thâm niên tại `resign_date`, không phải "hôm nay"."""

    def test_su_kien_nghi_dung_resign_date_khong_dung_hom_nay(self, db, world):
        world.grant("a1", "employee", scope="all", actions=("read",))
        db.add(Employee(code="NG01", full_name="Nghỉ đã lâu", company_id=world.co["A"],
                        department_id=world.dept["A.kt"], status="resigned",
                        hire_date=date(2015, 1, 1), resign_date=date(2016, 1, 1)))
        db.commit()
        actor = world.actor("a1")

        events = resign_events(db, actor.user, actor.profile(), date(2015, 12, 1), date(2016, 2, 1))
        assert len(events) == 1
        #  Thâm niên tại NGÀY NGHỈ (2016-01-01, ~1 năm kể từ 2015-01-01) phải rơi "Dưới 1 năm" —
        #  tính theo "hôm nay" thật (2026+) sẽ sai thành "Trên 5 năm".
        assert events[0].seniority_label != "Trên 5 năm"


class TestThuTuRoute:
    def test_summary_dang_ky_truoc_duong_dong_id(self):
        """`/summary` phải nằm TRƯỚC `/{id}` trong bảng route, nếu không FastAPI khớp nhầm
        `int("summary")` ở route động và trả 422 thay vì chạy đúng handler."""
        paths = [r.path for r in app.routes if getattr(r, "path", "").startswith("/api/employees")]
        assert paths.index("/api/employees/summary") < paths.index("/api/employees/{eid}")

    def test_testclient_goi_summary_tra_200(self, db, world):
        world.grant("a1", "employee", scope="all", actions=("read",))
        actor = world.actor("a1")
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: actor.user
        try:
            client = TestClient(app)
            resp = client.get("/api/employees/summary", params={"preset": "this_month"})
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.dependency_overrides.pop(get_current_user, None)
        assert resp.status_code == 200
        assert resp.json()["success"] is True


class TestSoTruyVanCoDinh:
    def test_so_truy_van_khong_tang_theo_so_nhan_su(self, db, world):
        """5 nhân sự và 50 nhân sự phải ra CÙNG số câu SQL — không truy vấn nào lặp theo hàng."""
        world.grant("a1", "employee", scope="all", actions=("read",))
        actor = world.actor("a1")
        period = _period()
        #  Lấy `prof` MỘT LẦN trước khi đếm — `get_perm_profile` tự cache 60s (`_PERM_CACHE`),
        #  nên gọi nó TRONG closure đo sẽ cộng lố/thiếu truy vấn giữa lần "nguội"/"ấm" cache,
        #  đo nhầm hiệu ứng cache thay vì hiệu ứng số nhân sự.
        prof = actor.profile()

        def _add(n: int, start: int):
            for i in range(n):
                db.add(Employee(code=f"BULK{start + i}", full_name=f"NV {start + i}",
                                company_id=world.co["A"], department_id=world.dept["A.kt"],
                                hire_date=date(2026, 9, 5)))
            db.commit()

        def _count_queries(fn) -> int:
            statements: list[str] = []

            def _on_exec(conn, cursor, statement, *args):
                statements.append(statement)

            engine = db.get_bind()
            event.listen(engine, "before_cursor_execute", _on_exec)
            try:
                fn()
            finally:
                event.remove(engine, "before_cursor_execute", _on_exec)
            return len(statements)

        _add(5, 0)
        c5 = _count_queries(
            lambda: report_service.build_summary(db, actor.user, prof, period, "department"))
        _add(45, 5)
        c50 = _count_queries(
            lambda: report_service.build_summary(db, actor.user, prof, period, "department"))
        assert c5 > 0
        assert c5 == c50, f"số truy vấn tăng theo số nhân sự: {c5} (5 người) != {c50} (50 người)"
