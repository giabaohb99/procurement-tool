"""Phase 04 — Báo cáo Nghỉ phép (`GET /api/leave-requests/summary`) và Quỹ phép
năm (`GET /api/leave-balances/summary`).

Canh: phạm vi `own` của đơn nghỉ HỢP người LẬP lẫn người NGHỈ, không nới thêm
"đang có việc duyệt"; đơn khai nhiều loại nghỉ nhóm đúng theo từng loại nhưng
Tổng chỉ đếm 1 đơn; đường `/summary` không bị `/{rid}`/`/{bid}` nuốt; số truy
vấn SQL CỐ ĐỊNH, không tăng theo số đơn/số dòng quỹ phép.
"""
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import event
from starlette.datastructures import QueryParams

from app.core.report_period import parse_period
from app.main import app
from app.modules.employee.model import Employee
from app.modules.leave import (balance_report_controller, balance_report_service,
                               report_controller, report_service)
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import LR_APPROVED, LR_PENDING
from app.modules.leave.request_model import LeaveRequest, LeaveRequestLine

PERIOD_09 = {"preset": "custom", "date_from": "2026-09-01", "date_to": "2026-09-30", "compare": "none"}
YEAR_2026 = {"preset": "custom", "date_from": "2026-01-01", "date_to": "2026-12-31", "compare": "none"}


def _period(params=PERIOD_09):
    return parse_period(params)


def _leave_type(db, code: str, name: str) -> LeaveType:
    lt = LeaveType(code=code, name=name)
    db.add(lt)
    db.flush()
    return lt


def _request(db, code: str, *, company_id: int, department_id: int, employee_id: int,
            created_by: int, leave_type_id: int, status: int = LR_PENDING,
            from_date=date(2026, 9, 5), to_date=date(2026, 9, 5)) -> LeaveRequest:
    req = LeaveRequest(code=code, company_id=company_id, department_id=department_id,
                       employee_id=employee_id, created_by=created_by, leave_type_id=leave_type_id,
                       from_date=from_date, to_date=to_date, status=status, is_deleted=False)
    db.add(req)
    db.flush()
    return req


class TestPhamViOwnHopLapVaNghi:
    def test_own_thay_don_lap_ho_va_don_cua_minh_khong_thay_don_nguoi_khac(self, db, world):
        world.grant("a1", "leave_request", scope="own", actions=("read",))
        a1, a2, a3 = world.actor("a1"), world.actor("a2"), world.actor("a3")
        lt = _leave_type(db, "PN", "Phép năm")
        # a1 LẬP HỘ a2 — a1 phải thấy (created_by = mình)
        _request(db, "NP-01", company_id=world.co["A"], department_id=world.dept["A.kt"],
                employee_id=a2.employee.id, created_by=a1.user.id, leave_type_id=lt.id)
        # a2 lập hộ, NGƯỜI NGHỈ là a1 — a1 phải thấy (employee_id = mình)
        _request(db, "NP-02", company_id=world.co["A"], department_id=world.dept["A.kt"],
                employee_id=a1.employee.id, created_by=a2.user.id, leave_type_id=lt.id)
        # của người khác hoàn toàn — a1 KHÔNG được thấy
        _request(db, "NP-03", company_id=world.co["A"], department_id=world.dept["A.mua"],
                employee_id=a3.employee.id, created_by=a3.user.id, leave_type_id=lt.id)
        db.commit()

        data = report_service.build_summary(db, a1.user, a1.profile(), _period(), None)
        assert data["totals"]["current"]["requests"] == 2


class TestDonNhieuLoaiNghi:
    def test_nhom_theo_tung_loai_tong_chi_dem_1_don(self, db, world):
        world.grant("a1", "leave_request", scope="all", actions=("read",))
        a1 = world.actor("a1")
        lt_a = _leave_type(db, "LA", "Loại A")
        lt_b = _leave_type(db, "LB", "Loại B")
        req = _request(db, "NP-MULTI-01", company_id=world.co["A"], department_id=world.dept["A.kt"],
                      employee_id=a1.employee.id, created_by=a1.user.id, leave_type_id=lt_a.id,
                      status=LR_APPROVED, from_date=date(2026, 9, 5), to_date=date(2026, 9, 9))
        db.add(LeaveRequestLine(request_id=req.id, leave_type_id=lt_a.id, days=3))
        db.add(LeaveRequestLine(request_id=req.id, leave_type_id=lt_b.id, days=2))
        db.commit()

        data = report_service.build_summary(db, a1.user, a1.profile(), _period(), "leave_type")
        groups = {g["label"]: g["current"]["days_approved"] for g in data["groups"]}
        assert groups["Loại A"] == 3 and groups["Loại B"] == 2
        assert data["totals"]["current"]["days_approved"] == 5
        assert data["totals"]["current"]["requests"] == 1


class TestLocCongTy:
    """H1 — `company_id` lọc SAU `apply_scope`, chỉ THU HẸP thêm."""

    def test_leave_request_chon_cong_ty_a_khong_thay_cong_ty_b(self, db, world):
        world.grant("a1", "leave_request", scope="all", actions=("read",))
        a1 = world.actor("a1")
        lt = _leave_type(db, "PNLC", "Phép năm LC")
        _request(db, "NP-CTA", company_id=world.co["A"], department_id=world.dept["A.kt"],
                employee_id=a1.employee.id, created_by=a1.user.id, leave_type_id=lt.id)
        _request(db, "NP-CTB", company_id=world.co["B"], department_id=world.dept["B.kt"],
                employee_id=a1.employee.id, created_by=a1.user.id, leave_type_id=lt.id)
        db.commit()

        data = report_service.build_summary(db, a1.user, a1.profile(), _period(), None,
                                            company_id=world.co["A"])
        assert data["totals"]["current"]["requests"] == 1

    def test_leave_request_company_id_rac_nem_422(self, db, world):
        world.grant("a1", "leave_request", scope="all", actions=("read",))
        a1 = world.actor("a1")
        request = SimpleNamespace(query_params=QueryParams(
            [("preset", "this_month"), ("company_id", "abc")]))
        with pytest.raises(HTTPException) as exc:
            report_controller.leave_request_summary(request, db=db, user=a1.user)
        assert exc.value.status_code == 422

    def test_leave_balance_chon_cong_ty_a_khong_thay_cong_ty_b(self, db, world):
        world.grant("a1", "leave_balance", scope="all", actions=("read",))
        a1, a2 = world.actor("a1"), world.actor("a2")
        lt = _leave_type(db, "PNLCB", "Phép năm LCB")
        db.add(LeaveBalance(employee_id=a1.employee.id, year=2026, leave_type_id=lt.id,
                            company_id=world.co["A"], allocated_days=5))
        db.add(LeaveBalance(employee_id=a2.employee.id, year=2026, leave_type_id=lt.id,
                            company_id=world.co["B"], allocated_days=99))
        db.commit()

        data = balance_report_service.build_summary(db, a1.user, a1.profile(), _period(YEAR_2026),
                                                     None, company_id=world.co["A"])
        assert data["totals"]["current"]["granted"] == 5.0

    def test_leave_balance_company_id_rac_nem_422(self, db, world):
        world.grant("a1", "leave_balance", scope="all", actions=("read",))
        a1 = world.actor("a1")
        request = SimpleNamespace(query_params=QueryParams(
            [("preset", "this_year"), ("company_id", "xyz")]))
        with pytest.raises(HTTPException) as exc:
            balance_report_controller.leave_balance_summary(request, db=db, user=a1.user)
        assert exc.value.status_code == 422


class TestQuyPhepSoSanhNamCoDinh:
    """H2 — năm so sánh LUÔN `date_to.year - 1`, bất kể `compare_to` thật của kỳ."""

    def test_preset_thang_nay_compare_previous_ra_dung_nam_truoc(self, db, world):
        world.grant("a1", "leave_balance", scope="all", actions=("read",))
        a1 = world.actor("a1")
        lt = _leave_type(db, "PNY", "Phép năm Y")
        db.add(LeaveBalance(employee_id=a1.employee.id, year=2026, leave_type_id=lt.id,
                            company_id=world.co["A"], allocated_days=12))
        db.add(LeaveBalance(employee_id=a1.employee.id, year=2025, leave_type_id=lt.id,
                            company_id=world.co["A"], allocated_days=10))
        db.commit()

        period = parse_period({"preset": "this_month", "compare": "previous"}, today=date(2026, 9, 15))
        #  `compare_to` CHUNG của khung chỉ lùi 1 THÁNG (08/2026) — vẫn là năm 2026, KHÔNG phải
        #  năm trước. Dịch vụ Quỹ phép phải tự ép năm so sánh = 2025, không dùng thẳng giá trị này.
        assert period.compare_to.year == 2026
        data = balance_report_service.build_summary(db, a1.user, a1.profile(), period, None)
        assert data["totals"]["current"]["granted"] == 12.0
        assert data["totals"]["compare"]["granted"] == 10.0


class TestBreakdownLoaiNghiXepTheoNgay:
    """Mục 5 — "Top loại nghỉ" xếp theo TỔNG NGÀY, loại chỉ nằm ở dòng phụ không bị rớt."""

    def test_loai_chi_o_dong_phu_van_len_dau_neu_nhieu_ngay_hon(self, db, world):
        world.grant("a1", "leave_request", scope="all", actions=("read",))
        a1 = world.actor("a1")
        lt_a = _leave_type(db, "BDA", "Loại A")
        lt_c = _leave_type(db, "BDC", "Loại C")
        #  3 đơn: loại CHÍNH luôn là A (1 ngày/đơn = 3 ngày tổng), loại PHỤ luôn là C
        #  (4 ngày/đơn = 12 ngày tổng) — C không bao giờ là loại chính của đơn nào.
        for i in range(3):
            req = _request(db, f"NP-BD-{i}", company_id=world.co["A"], department_id=world.dept["A.kt"],
                          employee_id=a1.employee.id, created_by=a1.user.id, leave_type_id=lt_a.id,
                          status=LR_APPROVED)
            db.add(LeaveRequestLine(request_id=req.id, leave_type_id=lt_a.id, days=1))
            db.add(LeaveRequestLine(request_id=req.id, leave_type_id=lt_c.id, days=4))
        db.commit()

        data = report_service.build_summary(db, a1.user, a1.profile(), _period(), None)
        labels = [i["label"] for i in data["breakdowns"]["leave_type"]]
        assert labels.index("Loại C") < labels.index("Loại A")  # 12 ngày > 3 ngày


class TestThuTuRoute:
    def test_leave_request_summary_truoc_duong_dong_id(self):
        paths = [r.path for r in app.routes if getattr(r, "path", "").startswith("/api/leave-requests")]
        assert paths.index("/api/leave-requests/summary") < paths.index("/api/leave-requests/{rid}")

    def test_leave_balance_summary_truoc_duong_dong_id(self):
        paths = [r.path for r in app.routes if getattr(r, "path", "").startswith("/api/leave-balances")]
        assert paths.index("/api/leave-balances/summary") < paths.index("/api/leave-balances/{bid}")


def _count_queries(db, fn) -> int:
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


class TestSoTruyVanCoDinhNghiPhep:
    def test_leave_request_so_truy_van_khong_tang_theo_so_don(self, db, world):
        world.grant("a1", "leave_request", scope="all", actions=("read",))
        a1 = world.actor("a1")
        lt = _leave_type(db, "PN2", "Phép năm")
        #  Lấy `prof` MỘT LẦN trước khi đếm — tránh đo lẫn hiệu ứng cache 60s của
        #  `get_perm_profile` (nguội/ấm) vào phép so sánh 5-đơn vs 50-đơn.
        prof = a1.profile()

        def _add(n: int, start: int):
            for i in range(n):
                req = _request(db, f"NP-BULK-{start + i}", company_id=world.co["A"],
                              department_id=world.dept["A.kt"], employee_id=a1.employee.id,
                              created_by=a1.user.id, leave_type_id=lt.id, status=LR_APPROVED)
                db.add(LeaveRequestLine(request_id=req.id, leave_type_id=lt.id, days=1))
            db.commit()

        _add(5, 0)
        c5 = _count_queries(db, lambda: report_service.build_summary(
            db, a1.user, prof, _period(), "department"))
        _add(45, 5)
        c50 = _count_queries(db, lambda: report_service.build_summary(
            db, a1.user, prof, _period(), "department"))
        assert c5 > 0
        assert c5 == c50, f"số truy vấn tăng theo số đơn: {c5} (5 đơn) != {c50} (50 đơn)"

    def test_leave_balance_so_truy_van_khong_tang_theo_so_dong(self, db, world):
        world.grant("a1", "leave_balance", scope="all", actions=("read",))
        a1 = world.actor("a1")
        lt = _leave_type(db, "PN3", "Phép năm")
        prof = a1.profile()

        def _add(n: int, start: int):
            #  Ràng buộc `uq_leave_balance_emp_year_type` cấm 2 dòng cùng (nhân sự, năm, loại)
            #  — mỗi dòng quỹ phép thêm phải là MỘT nhân sự khác, không ảnh hưởng số truy vấn
            #  (bảng Nhân sự vẫn chỉ tra MỘT lượt, bất kể tra ra bao nhiêu dòng).
            for i in range(n):
                emp = Employee(code=f"QP_BULK_{start + i}", full_name=f"NV quỹ {start + i}",
                               company_id=world.co["A"], department_id=world.dept["A.kt"])
                db.add(emp)
                db.flush()
                db.add(LeaveBalance(employee_id=emp.id, year=2026, leave_type_id=lt.id,
                                    company_id=world.co["A"], allocated_days=12))
            db.commit()

        _add(5, 0)
        c5 = _count_queries(db, lambda: balance_report_service.build_summary(
            db, a1.user, prof, _period(YEAR_2026), "department"))
        _add(45, 5)
        c50 = _count_queries(db, lambda: balance_report_service.build_summary(
            db, a1.user, prof, _period(YEAR_2026), "department"))
        assert c5 > 0
        assert c5 == c50, f"số truy vấn tăng theo số dòng quỹ phép: {c5} (5 dòng) != {c50} (50 dòng)"
