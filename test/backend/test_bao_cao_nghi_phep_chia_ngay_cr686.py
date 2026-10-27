"""duoc-CR-686 — Báo cáo Tình hình nghỉ phép: CHIA NGÀY THEO KỲ/MỐC, chỉ số mới, lọc phòng ban,
danh sách «bấm số» (`/summary/rows`). Lịch mặc định: T2-T7 làm, CN nghỉ (chưa gán lịch nào).

Lịch tháng 9-11/2026 dùng trong bài: 28/09 = T2 · 30/09 = T4 · 01/10 = T5 · 03/10 = T7 ·
04/10 = CN · 31/10 = T7 · 01/11 = CN · 02/11 = T2.
"""
import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.report_keys import ReportKey
from app.core.report_period import parse_period
from app.core.subject_match import SUBJECT_ROLE
from app.main import app
from app.modules.leave import report_service
from app.modules.leave.catalog_model import Holiday, LeaveType
from app.modules.leave.constants import (LR_APPROVED, LR_PENDING, LR_REJECTED, SESSION_AFTERNOON,
                                         SESSION_MORNING)
from app.modules.leave.report_day_split import build_split_requests, overlapping_rows
from app.modules.leave.report_rows import scoped_base
from app.modules.leave.request_model import LeaveRequest, LeaveRequestLine, LeaveRequestPeriod

SEP = {"preset": "custom", "date_from": "2026-09-01", "date_to": "2026-09-30", "compare": "none"}
OCT = {"preset": "custom", "date_from": "2026-10-01", "date_to": "2026-10-31", "compare": "none"}
NOV = {"preset": "custom", "date_from": "2026-11-01", "date_to": "2026-11-30", "compare": "none"}


def _type(db, code, *, paid=True, exclude_holiday=True):
    lt = LeaveType(code=code, name=f"Loại {code}", is_paid=paid, exclude_holiday=exclude_holiday)
    db.add(lt)
    db.flush()
    return lt


def _req(db, world, code, actor, lt, d_from, d_to, total, *, status=LR_APPROVED, lines=None,
         from_session=1, to_session=1, periods=None, dept_key="A.kt", submitted_at=None):
    req = LeaveRequest(code=code, company_id=world.co["A"], department_id=world.dept[dept_key],
                       employee_id=actor.employee.id, created_by=actor.user.id,
                       leave_type_id=lt.id, from_date=d_from, to_date=d_to, status=status,
                       from_session=from_session, to_session=to_session, total_days=total,
                       is_deleted=False, submitted_at=submitted_at)
    db.add(req)
    db.flush()
    for t, days in (lines or [(lt.id, total)]):
        db.add(LeaveRequestLine(request_id=req.id, leave_type_id=t, days=days))
    for i, (a, b, days) in enumerate(periods or []):
        db.add(LeaveRequestPeriod(request_id=req.id, from_date=a, to_date=b, days=days,
                                  sort_order=i))
    return req


@pytest.fixture
def ctx(db, world):
    world.grant("a1", "leave_request", scope="all", actions=("read", "export"))
    actor = world.actor("a1")
    return actor, actor.profile()


def _summary(db, actor, prof, params, group_by=None, **kw):
    return report_service.build_summary(db, actor.user, prof, parse_period(params), group_by, **kw)


class TestChiaNgayTheoKy:
    def test_don_vat_qua_thang_chia_dung_hai_ben(self, db, world, ctx):
        actor, prof = ctx
        lt = _type(db, "PN")
        #  T2 28/09 → T7 03/10: 6 ngày làm, 3 ngày mỗi tháng. Đếm ĐƠN vẫn theo ngày bắt đầu.
        _req(db, world, "NP-1", actor, lt, date(2026, 9, 28), date(2026, 10, 3), 6)
        db.commit()
        sep = _summary(db, actor, prof, SEP)["totals"]["current"]
        octo = _summary(db, actor, prof, OCT)["totals"]["current"]
        assert sep["days_approved"] == pytest.approx(3) and sep["requests"] == 1
        assert octo["days_approved"] == pytest.approx(3) and octo["requests"] == 0

    def test_don_gon_trong_ky_giu_nguyen(self, db, world, ctx):
        actor, prof = ctx
        lt = _type(db, "PN")
        _req(db, world, "NP-1", actor, lt, date(2026, 9, 7), date(2026, 9, 9), 3)
        db.commit()
        assert _summary(db, actor, prof, SEP)["totals"]["current"]["days_approved"] == 3

    def test_trong_so_theo_lich_chu_nhat_khong_co_ngay(self, db, world, ctx):
        actor, prof = ctx
        lt = _type(db, "PN")
        #  T7 31/10 → T3 03/11: làm T7, T2, T3 (CN 01/11 nghỉ) → tháng 10 được 1/3, KHÔNG phải 1/4.
        _req(db, world, "NP-1", actor, lt, date(2026, 10, 31), date(2026, 11, 3), 3)
        db.commit()
        assert _summary(db, actor, prof, OCT)["totals"]["current"]["days_approved"] == pytest.approx(1)
        assert _summary(db, actor, prof, NOV)["totals"]["current"]["days_approved"] == pytest.approx(2)

    def test_nua_buoi_o_bien(self, db, world, ctx):
        actor, prof = ctx
        lt = _type(db, "PN")
        #  29/09 (cả ngày) · 30/09 · 01/10 (chỉ buổi sáng) = 1 + 1 + 0.5 = 2.5 ngày.
        _req(db, world, "NP-1", actor, lt, date(2026, 9, 29), date(2026, 10, 1), 2.5,
             to_session=SESSION_MORNING)
        db.commit()
        assert _summary(db, actor, prof, SEP)["totals"]["current"]["days_approved"] == pytest.approx(2)
        assert _summary(db, actor, prof, OCT)["totals"]["current"]["days_approved"] == pytest.approx(0.5)

    def test_nua_buoi_chieu_ngay_dau(self, db, world, ctx):
        actor, prof = ctx
        lt = _type(db, "PN")
        #  30/09 từ buổi chiều (0.5) + 01/10 cả ngày (1) = 1.5.
        _req(db, world, "NP-1", actor, lt, date(2026, 9, 30), date(2026, 10, 1), 1.5,
             from_session=SESSION_AFTERNOON)
        db.commit()
        assert _summary(db, actor, prof, SEP)["totals"]["current"]["days_approved"] == pytest.approx(0.5)
        assert _summary(db, actor, prof, OCT)["totals"]["current"]["days_approved"] == pytest.approx(1)

    def test_ngay_le_khong_co_trong_so(self, db, world, ctx):
        actor, prof = ctx
        lt = _type(db, "PN")
        db.add(Holiday(company_id=0, date=date(2026, 9, 30), name="Nghỉ lễ", is_active=True))
        #  29/09 · 30/09 (lễ) · 01/10 → làm 29/09 và 01/10: mỗi tháng đúng 1 ngày.
        _req(db, world, "NP-1", actor, lt, date(2026, 9, 29), date(2026, 10, 1), 2)
        db.commit()
        assert _summary(db, actor, prof, SEP)["totals"]["current"]["days_approved"] == pytest.approx(1)
        assert _summary(db, actor, prof, OCT)["totals"]["current"]["days_approved"] == pytest.approx(1)

    def test_tong_trong_so_bang_0_chia_deu_theo_ngay_lich(self, db, world, ctx):
        actor, prof = ctx
        lt = _type(db, "PN")
        for d in (date(2026, 9, 30), date(2026, 10, 1)):
            db.add(Holiday(company_id=0, date=d, name="Lễ", is_active=True))
        _req(db, world, "NP-1", actor, lt, date(2026, 9, 30), date(2026, 10, 1), 2)
        db.commit()
        assert _summary(db, actor, prof, SEP)["totals"]["current"]["days_approved"] == pytest.approx(1)
        assert _summary(db, actor, prof, OCT)["totals"]["current"]["days_approved"] == pytest.approx(1)

    def test_don_nhieu_khoang_chia_theo_tung_khoang(self, db, world, ctx):
        actor, prof = ctx
        lt = _type(db, "PN")
        #  Khoảng 1: 28-29/09 (2 ngày) · khoảng 2: 05-06/10 (2 ngày); khe 30/09-04/10 đi làm.
        _req(db, world, "NP-1", actor, lt, date(2026, 9, 28), date(2026, 10, 6), 4,
             periods=[(date(2026, 9, 28), date(2026, 9, 29), 2),
                      (date(2026, 10, 5), date(2026, 10, 6), 2)])
        db.commit()
        assert _summary(db, actor, prof, SEP)["totals"]["current"]["days_approved"] == pytest.approx(2)
        assert _summary(db, actor, prof, OCT)["totals"]["current"]["days_approved"] == pytest.approx(2)

    def test_don_nhieu_loai_chia_dong_theo_ty_le_va_ngay_khong_luong(self, db, world, ctx):
        actor, prof = ctx
        pn, kl = _type(db, "PN"), _type(db, "KL", paid=False)
        _req(db, world, "NP-1", actor, pn, date(2026, 9, 28), date(2026, 10, 3), 6,
             lines=[(pn.id, 4), (kl.id, 2)])
        db.commit()
        data = _summary(db, actor, prof, SEP, "leave_type")
        by = {g["label"]: g["current"] for g in data["groups"]}
        assert by["Loại PN"]["days_approved"] == pytest.approx(2)
        assert by["Loại KL"]["days_approved"] == pytest.approx(1)
        assert data["totals"]["current"]["days_unpaid"] == pytest.approx(1)
        top = {i["label"]: i["value"] for i in data["breakdowns"]["leave_type"]}
        assert top == {"Loại PN": pytest.approx(2), "Loại KL": pytest.approx(1)}

    def test_don_bat_dau_truoc_ky_tao_nhom_moi_va_khong_dem_don(self, db, world, ctx):
        actor, prof = ctx
        lt = _type(db, "PN")
        _req(db, world, "NP-1", actor, lt, date(2026, 8, 31), date(2026, 9, 2), 3)   # T2-T4
        db.commit()
        data = _summary(db, actor, prof, SEP, "department")
        totals = data["totals"]["current"]
        assert totals["days_approved"] == pytest.approx(2) and totals["requests"] == 0
        (grp,) = data["groups"]
        assert grp["current"]["days_approved"] == pytest.approx(2) and grp["current"]["requests"] == 0

    def test_cho_duyet_cung_chia_va_tu_choi_khong_tinh(self, db, world, ctx):
        actor, prof = ctx
        lt = _type(db, "PN")
        _req(db, world, "NP-1", actor, lt, date(2026, 9, 28), date(2026, 10, 3), 6, status=LR_PENDING)
        _req(db, world, "NP-2", actor, lt, date(2026, 9, 28), date(2026, 10, 3), 6, status=LR_REJECTED)
        db.commit()
        octo = _summary(db, actor, prof, OCT)["totals"]["current"]
        assert octo["days_pending"] == pytest.approx(3) and octo["days_approved"] == 0

    def test_xu_huong_ngay_chia_ve_dung_moc(self, db, world, ctx):
        actor, prof = ctx
        lt = _type(db, "PN")
        _req(db, world, "NP-1", actor, lt, date(2026, 9, 28), date(2026, 9, 30), 3)
        db.commit()
        p = {"preset": "custom", "date_from": "2026-09-28", "date_to": "2026-10-04", "compare": "none"}
        trend = _summary(db, actor, prof, p)["trend"]
        assert [t["current"]["days_approved"] for t in trend][:4] == pytest.approx([1, 1, 1, 0])

    def test_xu_huong_tuan_don_qua_hai_tuan(self, db, world, ctx):
        actor, prof = ctx
        lt = _type(db, "PN")
        #  T6 02/10 → T3 06/10: T6, T7 | T2, T3 (CN nghỉ) → tuần 1 được 2, tuần 2 được 2.
        _req(db, world, "NP-1", actor, lt, date(2026, 10, 2), date(2026, 10, 6), 4)
        db.commit()
        p = {"preset": "custom", "date_from": "2026-09-01", "date_to": "2026-12-31", "compare": "none"}
        data = _summary(db, actor, prof, p)
        assert sum(t["current"]["days_approved"] for t in data["trend"]) == pytest.approx(4)

    def test_ky_so_sanh_cung_chia_ngay(self, db, world, ctx):
        actor, prof = ctx
        lt = _type(db, "PN")
        _req(db, world, "NP-1", actor, lt, date(2026, 9, 28), date(2026, 10, 3), 6)
        db.commit()
        p = {"preset": "custom", "date_from": "2026-10-01", "date_to": "2026-10-31", "compare": "previous"}
        data = _summary(db, actor, prof, p)
        assert data["totals"]["current"]["days_approved"] == pytest.approx(3)
        assert data["totals"]["compare"]["days_approved"] == pytest.approx(3)


class TestNgayLeLapKyDai:
    def test_le_lap_hang_nam_khong_mat_khi_co_don_dai_keo_cua_so_qua_400_ngay(self, db, world, ctx):
        actor, prof = ctx
        lt = _type(db, "PN")
        #  02/09 là lễ LẶP hằng năm. Đơn 31/08 (T2) → 02/09 (T4): làm 31/08 + 01/09, 02/09 là lễ.
        db.add(Holiday(company_id=0, date=date(2025, 9, 2), name="Quốc khánh", is_recurring=True,
                       is_active=True))
        _req(db, world, "NP-NGAN", actor, lt, date(2026, 8, 31), date(2026, 9, 2), 2)
        #  Đơn dài từ 02/06/2025 kéo cửa sổ nạp ngày lễ lên hơn 400 ngày.
        _req(db, world, "NP-DAI", actor, lt, date(2025, 6, 2), date(2026, 9, 1), 300)
        db.commit()
        base = scoped_base(db, actor.user, prof)
        rows = [r for r in overlapping_rows(base, date(2026, 9, 1), date(2026, 9, 30))
                if r.code in ("NP-NGAN", "NP-DAI")]
        assert len(rows) == 2
        short = next(s for s in build_split_requests(db, rows, set()) if s.code == "NP-NGAN")
        assert short.day_share.get(date(2026, 9, 2), 0) == pytest.approx(0)
        assert short.share_where(lambda d: d >= date(2026, 9, 1)) == pytest.approx(0.5)


class TestChiSoMoi:
    def test_don_cho_duyet_qua_3_ngay_va_ngay_tb_moi_nguoi(self, db, world, ctx):
        actor, prof = ctx
        lt = _type(db, "PN")
        now = datetime.utcnow()
        _req(db, world, "NP-OLD", actor, lt, date(2026, 9, 7), date(2026, 9, 7), 1,
             status=LR_PENDING, submitted_at=now - timedelta(days=4))
        _req(db, world, "NP-NEW", actor, lt, date(2026, 9, 8), date(2026, 9, 8), 1,
             status=LR_PENDING, submitted_at=now - timedelta(hours=10))
        _req(db, world, "NP-OK1", actor, lt, date(2026, 9, 9), date(2026, 9, 10), 2)
        _req(db, world, "NP-OK2", actor, lt, date(2026, 9, 14), date(2026, 9, 14), 1)
        db.commit()
        t = _summary(db, actor, prof, SEP)["totals"]["current"]
        assert t["requests_pending_over_3d"] == 1
        assert t["people_on_leave"] == 1 and t["avg_days_per_person"] == pytest.approx(3.0)

    def test_meta_co_chi_so_moi_va_drilldown(self, db, world, ctx):
        actor, prof = ctx
        meta = _summary(db, actor, prof, SEP)["meta"]
        keys = {m["key"] for m in meta["metrics"]}
        assert {"days_unpaid", "requests_pending_over_3d", "avg_days_per_person"} <= keys
        assert meta["drilldown_metrics"] == ["requests", "days_approved", "days_pending",
                                             "requests_pending_over_3d"]


class TestLocPhongBan:
    def test_chi_thu_hep_khong_mo_rong_pham_vi(self, db, world):
        world.grant("a1", "leave_request", scope="dept", actions=("read",))
        actor = world.actor("a1")
        lt = _type(db, "PN")
        _req(db, world, "NP-KT", actor, lt, date(2026, 9, 7), date(2026, 9, 7), 1)
        other = world.actor("a2") if "a2" in world._actors else actor
        _req(db, world, "NP-MUA", other, lt, date(2026, 9, 8), date(2026, 9, 8), 1, dept_key="A.mua")
        db.commit()
        prof = actor.profile()
        base = _summary(db, actor, prof, SEP)["totals"]["current"]["requests"]
        assert base == 1                                    # phạm vi dept: chỉ phòng mình
        mine = _summary(db, actor, prof, SEP, department_id=world.dept["A.kt"])
        assert mine["totals"]["current"]["requests"] == 1
        foreign = _summary(db, actor, prof, SEP, department_id=world.dept["A.mua"])
        assert foreign["totals"]["current"]["requests"] == 0   # chọn phòng ngoài phạm vi → 0, không lộ


def _count(db, fn):
    n = []
    eng = db.get_bind()

    def on(conn, cur, stmt, *a):
        n.append(stmt)

    event.listen(eng, "before_cursor_execute", on)
    try:
        fn()
    finally:
        event.remove(eng, "before_cursor_execute", on)
    return len(n)


class TestSoTruyVanCoDinh:
    def test_don_vat_bien_5_va_50_cung_so_truy_van(self, db, world, ctx):
        actor, prof = ctx
        lt = _type(db, "PN")

        def add(n, start):
            for i in range(n):
                _req(db, world, f"NP-X{start + i}", actor, lt, date(2026, 9, 28), date(2026, 10, 3), 6,
                     periods=[(date(2026, 9, 28), date(2026, 10, 3), 6)])
            db.commit()

        def run():
            _summary(db, actor, prof, SEP, "department")

        add(5, 0)
        c5 = _count(db, run)
        add(45, 5)
        c50 = _count(db, run)
        assert c5 == c50, (c5, c50)


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
    def _setup(self, db, world, gan_bao_cao, key=ReportKey.LEAVE_USAGE):
        world.grant("a1", "leave_request", scope="all", actions=("read",))
        actor = world.actor("a1")
        if key is not None:
            gan_bao_cao(SUBJECT_ROLE, actor.roles[-1].id, key)
        return actor

    def test_thieu_quyen_bao_cao_403(self, db, world, gan_bao_cao, http):
        actor = self._setup(db, world, gan_bao_cao, key=None)
        r = http(actor.user, "/api/leave-requests/summary/rows", metric="requests", **SEP)
        assert r.status_code == 403

    def test_metric_la_422_va_route_khong_bi_id_nuot(self, db, world, gan_bao_cao, http):
        actor = self._setup(db, world, gan_bao_cao)
        assert http(actor.user, "/api/leave-requests/summary/rows", metric="salary", **SEP).status_code == 422
        ok = http(actor.user, "/api/leave-requests/summary/rows", metric="requests", **SEP)
        assert ok.status_code == 200 and ok.json()["success"] is True

    def test_days_approved_cong_cot_so_ngay_bang_con_so_tren_bang(self, db, world, gan_bao_cao, http):
        actor = self._setup(db, world, gan_bao_cao)
        lt = _type(db, "PN")
        _req(db, world, "NP-A", actor, lt, date(2026, 9, 28), date(2026, 10, 3), 6)
        _req(db, world, "NP-B", actor, lt, date(2026, 8, 31), date(2026, 9, 2), 3)
        _req(db, world, "NP-C", actor, lt, date(2026, 9, 14), date(2026, 9, 14), 1)
        db.commit()
        d = http(actor.user, "/api/leave-requests/summary/rows", metric="days_approved", **SEP).json()["data"]
        total = _summary(db, actor, actor.profile(), SEP)["totals"]["current"]["days_approved"]
        assert d["total"] == 3
        assert sum(r["days"] for r in d["rows"]) == pytest.approx(total)
        assert {r["code"] for r in d["rows"]} == {"NP-A", "NP-B", "NP-C"}
        assert d["rows"][0]["link"].startswith("/hr/leave-requests/")

    def test_danh_sach_cho_qua_3_ngay_khop_the_so(self, db, world, gan_bao_cao, http):
        """E2E 27/10/2026: phép trừ 72 giờ lọt vào chú thích nên danh sách ra cả đơn mới gửi —
        thẻ ghi 1, danh sách ra 2. Danh sách phải bằng đúng con số trên thẻ."""
        actor = self._setup(db, world, gan_bao_cao)
        lt = _type(db, "PN")
        now = datetime.utcnow()
        _req(db, world, "NP-CU", actor, lt, date(2026, 9, 7), date(2026, 9, 7), 1, status=LR_PENDING,
             submitted_at=now - timedelta(days=5))
        _req(db, world, "NP-MOI", actor, lt, date(2026, 9, 8), date(2026, 9, 8), 1, status=LR_PENDING,
             submitted_at=now - timedelta(hours=10))
        db.commit()
        kpi = http(actor.user, "/api/leave-requests/summary", **SEP).json()["data"]["totals"]["current"]
        r = http(actor.user, "/api/leave-requests/summary/rows", metric="requests_pending_over_3d",
                 **SEP).json()["data"]
        assert [x["code"] for x in r["rows"]] == ["NP-CU"]
        assert r["total"] == kpi["requests_pending_over_3d"] == 1

    def test_loc_nhom_phong_ban_va_don_cho_qua_3_ngay(self, db, world, gan_bao_cao, http):
        actor = self._setup(db, world, gan_bao_cao)
        lt = _type(db, "PN")
        old = datetime.utcnow() - timedelta(days=5)
        _req(db, world, "NP-KT", actor, lt, date(2026, 9, 7), date(2026, 9, 7), 1, status=LR_PENDING,
             submitted_at=old)
        _req(db, world, "NP-MUA", actor, lt, date(2026, 9, 8), date(2026, 9, 8), 1, status=LR_PENDING,
             submitted_at=old, dept_key="A.mua")
        db.commit()
        r = http(actor.user, "/api/leave-requests/summary/rows", metric="requests_pending_over_3d",
                 group_by="department", group_key=str(world.dept["A.kt"]), **SEP).json()["data"]
        assert [x["code"] for x in r["rows"]] == ["NP-KT"]
        miss = http(actor.user, "/api/leave-requests/summary/rows", metric="requests",
                    group_by="department", group_key="__other__", **SEP)
        assert miss.status_code == 422
