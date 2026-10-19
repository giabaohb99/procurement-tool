"""duoc-CR-641 — hồi quy cho các lỗi của đợt review 19/10/2026 (H1, H3, M1, M3, M4, L1, L4). Mỗi bài ghi tên lỗi."""
from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.modules.employee.model import Employee
from app.modules.seal_request.model import SealRequest
from app.modules.usage_profile import backfill as backfill_mod
from app.modules.usage_profile import daily_builder, report_route_keys as rrk
from app.modules.usage_profile.daily_builder import DayTooOldError, aggregate_day, write_rows
from app.modules.usage_profile.daily_docs import proxy_columns
from app.modules.usage_profile.daily_sources import load_day_sources
from app.modules.usage_profile.model import UsageDaily
from app.modules.usage_profile.snapshot_metrics_flow import work_task_metrics
from app.modules.usage_profile.telemetry_service import scrub_message

from ho_so_lam_viec_factory import MON, TUE, add_request, make_person, vn
from app.modules.leave.request_model import LeaveRequest
from app.modules.leave.constants import LR_DRAFT

TODAY_OK = date(2026, 1, 20)


@pytest.fixture
def hom_nay_gan(monkeypatch):
    monkeypatch.setattr(daily_builder, "vn_today", lambda: TODAY_OK)


def _lech_id_nhan_su_va_tai_khoan(db):
    """Tạo vài nhân sự thừa để id nhân sự ≠ id tài khoản, đúng tình huống thật (hai dãy id độc lập)."""
    for i in range(3):
        db.add(Employee(code=f"PAD{i}", full_name=f"Pad {i}", is_active=True, status="official"))
    db.flush()


def _seal(db, created_by_user, requester_user):
    s = SealRequest(code=f"DD{created_by_user.id}{requester_user.id}", created_by=created_by_user.id,
                    requester_id=requester_user.id, created_at=vn(MON, "10:00"))
    db.add(s)
    db.commit()


def _proxy(db):
    src = load_day_sources(db, MON)
    user_emp = {u[0]: u[2] or 0 for u in src.users}
    emp_user = {u[2]: u[0] for u in src.users if u[2]}
    return proxy_columns(src.proxy_docs, src.approval_proxies, user_emp, emp_user)


# ── H1 ────────────────────────────────────────────────────────────────────────

def test_h1_phieu_dong_dau_tu_lap_cho_minh_khong_phai_bam_ho(db):
    """Bug H1: SealRequest.requester_id là id TÀI KHOẢN, bị so với id NHÂN SỰ nên phiếu tự lập luôn bị tính bấm hộ."""
    _lech_id_nhan_su_va_tai_khoan(db)
    a, _ = make_person(db, "H1A")
    _seal(db, a, a)
    done, received = _proxy(db)
    assert not done and not received


def test_h1_phieu_dong_dau_lap_ho_nguoi_khac_tinh_ca_hai_phia(db):
    _lech_id_nhan_su_va_tai_khoan(db)
    a, _ = make_person(db, "H1B")
    b, _ = make_person(db, "H1C")
    _seal(db, a, b)
    done, received = _proxy(db)
    assert done == {a.id: 1} and received == {b.id: 1}


def test_h1_don_nghi_phep_tu_lap_khong_phai_bam_ho_con_lap_ho_thi_co(db):
    _lech_id_nhan_su_va_tai_khoan(db)
    a, ea = make_person(db, "H1D")
    b, eb = make_person(db, "H1E")
    db.add_all([
        LeaveRequest(code="NPS1", employee_id=ea.id, leave_type_id=0, from_date=TUE, to_date=TUE, status=LR_DRAFT,
                     created_by=a.id, created_at=vn(MON, "10:00")),             # tự lập
        LeaveRequest(code="NPS2", employee_id=eb.id, leave_type_id=0, from_date=TUE, to_date=TUE, status=LR_DRAFT,
                     created_by=a.id, created_at=vn(MON, "11:00"))])            # a lập hộ b
    db.commit()
    done, received = _proxy(db)
    assert done == {a.id: 1} and received == {b.id: 1}


# ── H3 ────────────────────────────────────────────────────────────────────────

def test_h3_gom_lai_ngay_qua_han_giu_nguon_bi_tu_choi_va_khong_xoa_so_cu(db, monkeypatch):
    """Bug H3: gom lại ngày cũ DELETE+INSERT từ nguồn đã bị dọn → số tốt thành 0."""
    monkeypatch.setattr(daily_builder, "vn_today", lambda: MON + timedelta(days=90))
    user, emp = make_person(db, "H3A")
    db.add(UsageDaily(user_id=user.id, day=MON, employee_id=emp.id, api_reads=77))
    db.commit()
    with pytest.raises(DayTooOldError):
        aggregate_day(db, MON)
    with pytest.raises(DayTooOldError):
        write_rows(db, MON, [])
    assert db.query(UsageDaily).filter_by(user_id=user.id, day=MON).one().api_reads == 77
    #  ngày 89 ngày trước vẫn được; force bỏ qua kiểm tra và ghi cảnh báo
    aggregate_day(db, MON + timedelta(days=1))
    assert aggregate_day(db, MON, force=True) >= 0


def test_h3_backfill_kep_ngay_dau_ve_moc_an_toan_va_force_thi_khong(monkeypatch):
    today = date(2026, 10, 19)
    monkeypatch.setattr(daily_builder, "vn_today", lambda: today)
    monkeypatch.setattr(backfill_mod, "vn_today", lambda: today)
    seen = []
    monkeypatch.setattr(backfill_mod, "aggregate_day", lambda db, day, force=False: seen.append((day, force)))
    monkeypatch.setattr(backfill_mod, "SessionLocal", lambda: SimpleNamespace(rollback=lambda: None, close=lambda: None))
    safe = today - timedelta(days=daily_builder.MAX_REAGGREGATE_AGE_DAYS)
    backfill_mod.backfill(90, sleep_s=0)
    assert seen and min(d for d, _ in seen) == safe
    seen.clear()
    backfill_mod.backfill(3, start=date(2026, 1, 1), sleep_s=0, force=True)
    assert [d for d, _ in seen] == [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)] and all(f for _, f in seen)
    seen.clear()
    backfill_mod.backfill(3, start=date(2026, 1, 1), sleep_s=0)
    assert min(d for d, _ in seen) >= safe


# ── M1 ────────────────────────────────────────────────────────────────────────

def test_m1_server_che_email_so_dai_va_query_string_roi_cat_do_dai():
    """Bug M1: thông điệp lỗi do client gửi được lưu nguyên văn, chỉ FE che (không tin được)."""
    out = scrub_message("Lỗi với a.nguyen+x@dego.vn tại /po/1?q=nguyen%20van&page=2 cccd 012345678901 mã 12345")
    assert "@" not in out and "q=nguyen" not in out and "012345678901" not in out
    assert "12345" in out        # dãy ngắn hơn 6 chữ số giữ lại
    assert len(scrub_message("x" * 1000)) == 200
    assert scrub_message("Sao lỗi vậy? ok") == "Sao lỗi vậy? ok"


# ── M3 ────────────────────────────────────────────────────────────────────────

def test_m3_hoat_dong_truoc_ngay_nghi_khong_bi_co_sau_nghi_viec(db, hom_nay_gan):
    """Bug M3: dùng status HIỆN TẠI nên gom lại ngày trước khi nghỉ vẫn báo «hoạt động sau nghỉ việc»."""
    user, _ = make_person(db, "M3A", status="resigned", resign=TUE)
    add_request(db, user, vn(MON, "10:00"), "GET", "/api/x")
    add_request(db, user, vn(TUE + timedelta(days=1), "10:00"), "GET", "/api/x")
    db.commit()
    aggregate_day(db, MON)
    aggregate_day(db, TUE + timedelta(days=1))
    flags = {r.day: r.active_after_resign for r in db.query(UsageDaily).filter_by(user_id=user.id)}
    assert flags == {MON: False, TUE + timedelta(days=1): True}


def test_m3_thieu_ngay_nghi_thi_dung_trang_thai_du_phong(db, hom_nay_gan):
    user, _ = make_person(db, "M3B", status="resigned", resign=None)
    add_request(db, user, vn(MON, "10:00"), "GET", "/api/x")
    db.commit()
    aggregate_day(db, MON)
    assert db.query(UsageDaily).filter_by(user_id=user.id).one().active_after_resign is True


# ── M4 ────────────────────────────────────────────────────────────────────────

def test_m4_post_khong_phai_nghiep_vu_khong_tinh_la_luot_ghi(db, hom_nay_gan):
    """Bug M4: đánh dấu đã đọc thông báo / lưu tùy chỉnh / chat trợ lý bị tính là «ghi», làm nhiễu ngoài giờ/mobile/422."""
    user, _ = make_person(db, "M4A")
    for method, route, status in (("POST", "/api/notifications/{nid}/read", 200), ("POST", "/api/notifications/read-all", 200),
                                  ("PUT", "/api/me/preferences/theme", 200), ("POST", "/api/assistant/chat", 422)):
        add_request(db, user, vn(MON, "22:30"), method, route, status=status)
    add_request(db, user, vn(MON, "22:31"), "POST", "/api/purchase-requests", status=422)   # nghiệp vụ thật, ngoài giờ
    add_request(db, user, vn(MON, "22:32"), "GET", "/api/notifications")                   # đọc thật
    db.commit()
    aggregate_day(db, MON)
    row = db.query(UsageDaily).filter_by(user_id=user.id).one()
    assert (row.api_writes, row.api_reads, row.writes_offhours, row.http_422) == (1, 1, 1, 1)
    assert row.active and sum(row.hourly) == 6      # vẫn là hoạt động trong ngày


# ── L1 ────────────────────────────────────────────────────────────────────────

def test_l1_dung_han_so_theo_ngay_vn_va_qua_han_tinh_tai_cuoi_cua_so():
    """Bug L1: completed_at UTC bị so thẳng với due VN; work_overdue_open dùng hôm nay thật nên dựng lại tuần cũ ra số khác."""
    done_late = datetime(2026, 1, 5, 17, 30)    # 00:30 VN ngày 06/01 → trễ hạn 05/01
    done_ok = datetime(2026, 1, 5, 16, 30)      # 23:30 VN ngày 05/01 → đúng hạn
    tasks = [(1, "2026-01-05", done_late, 2), (1, "2026-01-05", done_ok, 2),
             (1, "2026-01-08", None, 1), (1, "2026-01-12", None, 1)]
    out = work_task_metrics(tasks, {1: 10}, date(2026, 1, 12))
    assert out[10].values["work_on_time_rate"] == 0.5
    assert out[10].values["work_overdue_open"] == 1      # hạn 12/01 chưa quá hạn tại cuối cửa sổ (loại trừ) 12/01


# ── L4 ────────────────────────────────────────────────────────────────────────

def test_l4_ket_qua_rong_khong_bi_nho_vinh_vien(monkeypatch):
    """Bug L4: lần đầu nạp app lỗi → `{}` bị lru_cache giữ cả vòng đời worker."""
    import app.main as main_mod
    monkeypatch.setattr(rrk, "_cache", None)
    monkeypatch.setattr(main_mod, "app", SimpleNamespace(routes=[]))
    assert rrk.report_route_keys() == {}
    monkeypatch.undo()
    monkeypatch.setattr(rrk, "_cache", None)
    assert rrk.report_route_keys()      # lần sau dựng lại được
