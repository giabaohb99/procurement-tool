"""Luật thuần của HĐLĐ (`labor_contract/rules.py`): bảng chuyển trạng thái, ràng buộc ngày,
trạng thái hiệu lực. Không DB — chạy tức thì.

Tinh thần: tìm chỗ luật LỦNG (ngày biên, loại HĐ, EXPIRED lọt vào bảng chuyển), không chứng minh
đường đẹp chạy.
"""
from datetime import date

import pytest

from app.core.labor_contract_codes import LaborContractStatus as S, LaborContractType as T
from app.modules.labor_contract import rules
from app.modules.labor_contract.rules import RuleViolation, plan_transition

START = date(2026, 1, 1)
ALL = [int(s) for s in S]


def _plan(status, to, on_date=None, reason="", start=START):
    return plan_transition(status=int(status), start_date=start, to_status=int(to),
                           on_date=on_date, reason=reason)


# ── Bảng chuyển trạng thái: KIỂM TOÀN BỘ 5x5 ─────────────────────────────────────────
LEGAL = {(S.DRAFT, S.SIGNED), (S.DRAFT, S.CANCELLED), (S.SIGNED, S.TERMINATED)}


@pytest.mark.parametrize("frm", ALL)
@pytest.mark.parametrize("to", ALL)
def test_chi_ba_duong_chuyen_hop_le_con_lai_409(frm, to):
    if (S(frm), S(to)) in LEGAL:
        _plan(frm, to, on_date=date(2026, 6, 1), reason="lý do")   # đủ dữ kiện thì qua
    else:
        with pytest.raises(RuleViolation) as e:
            _plan(frm, to, on_date=date(2026, 6, 1), reason="lý do")
        assert e.value.status_code == 409


def test_expired_la_suy_ra_khong_bao_gio_la_diem_den_hay_diem_di():
    for frm in (S.EXPIRED, S.TERMINATED, S.CANCELLED):
        assert rules.allowed_transitions(int(frm)) == ()
    assert int(S.EXPIRED) not in sum(rules.TRANSITIONS.values(), ())


def test_trang_thai_la_va_so_am_khong_co_duong_chuyen():
    for bad in (0, -1, 99):
        assert rules.allowed_transitions(bad) == ()


# ── Điều kiện từng đường ──────────────────────────────────────────────────────────────
def test_ky_can_ngay_ky_va_khong_can_tep():
    with pytest.raises(RuleViolation) as e:
        _plan(S.DRAFT, S.SIGNED)
    assert e.value.status_code == 400 and "ngày ký" in e.value.message
    res = _plan(S.DRAFT, S.SIGNED, on_date=date(2026, 1, 5))   # không có tham số tệp nào — đại ca chốt
    assert res.status == int(S.SIGNED) and res.changes == {"sign_date": date(2026, 1, 5)}


@pytest.mark.parametrize("reason", ["", "   ", "\n\t"])
def test_huy_va_cham_dut_can_ly_do_khong_chap_nhan_khoang_trang(reason):
    with pytest.raises(RuleViolation):
        _plan(S.DRAFT, S.CANCELLED, reason=reason)
    with pytest.raises(RuleViolation):
        _plan(S.SIGNED, S.TERMINATED, on_date=date(2026, 6, 1), reason=reason)


def test_cham_dut_ngay_bien_bang_ngay_bat_dau_duoc_truoc_ngay_bat_dau_thi_khong():
    ok = _plan(S.SIGNED, S.TERMINATED, on_date=START, reason="x")
    assert ok.changes["terminated_date"] == START
    with pytest.raises(RuleViolation) as e:
        _plan(S.SIGNED, S.TERMINATED, on_date=date(2025, 12, 31), reason="x")
    assert "trước ngày bắt đầu" in e.value.message
    with pytest.raises(RuleViolation):
        _plan(S.SIGNED, S.TERMINATED, on_date=None, reason="x")


# ── effective_status ──────────────────────────────────────────────────────────────────
def test_het_han_chi_khi_da_ky_va_ngay_ket_thuc_da_qua_ngay_bien_la_chua():
    today = date(2026, 6, 30)
    assert rules.effective_status(int(S.SIGNED), date(2026, 6, 29), today) == int(S.EXPIRED)
    assert rules.effective_status(int(S.SIGNED), today, today) == int(S.SIGNED)    # hết hạn HÔM NAY vẫn hiệu lực
    assert rules.effective_status(int(S.SIGNED), None, today) == int(S.SIGNED)     # không thời hạn không bao giờ hết
    for st in (S.DRAFT, S.TERMINATED, S.CANCELLED):                               # chỉ SIGNED mới suy ra EXPIRED
        assert rules.effective_status(int(st), date(2000, 1, 1), today) == int(st)


# ── Ràng buộc ngày ────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ctype", [T.PROBATION, T.FIXED_TERM, T.SERVICE, T.COLLABORATOR])
def test_loai_co_thoi_han_bat_buoc_ngay_ket_thuc(ctype):
    with pytest.raises(ValueError, match="bắt buộc có ngày kết thúc"):
        rules.check_dates(int(ctype), START, None)
    rules.check_dates(int(ctype), START, START)   # ngày bằng nhau hợp lệ


def test_khong_xac_dinh_thoi_han_cam_ngay_ket_thuc_loai_khac_tuy_y():
    rules.check_dates(int(T.INDEFINITE), START, None)
    with pytest.raises(ValueError, match="không xác định thời hạn"):
        rules.check_dates(int(T.INDEFINITE), START, date(2027, 1, 1))
    rules.check_dates(int(T.OTHER), START, None)
    rules.check_dates(int(T.OTHER), START, date(2027, 1, 1))


def test_ngay_ket_thuc_truoc_ngay_bat_dau_va_thieu_ngay_bat_dau():
    with pytest.raises(ValueError, match="sau hoặc bằng"):
        rules.check_dates(int(T.FIXED_TERM), START, date(2025, 12, 31))
    with pytest.raises(ValueError, match="bắt buộc"):
        rules.check_dates(int(T.FIXED_TERM), None, date(2026, 12, 31))


def test_loai_hop_dong_ngoai_enum_bi_chan_o_tang_luat():
    for bad in (0, -1, 7, 99):
        with pytest.raises(ValueError):
            rules.check_dates(bad, START, START)


# ── Cảnh báo thời hạn (chỉ cảnh báo, không chặn) ───────────────────────────────────────
def test_xac_dinh_thoi_han_tren_36_thang_chi_canh_bao():
    assert rules.duration_warnings(int(T.FIXED_TERM), date(2026, 1, 1), date(2028, 12, 31)) == []   # đúng 36 tháng
    warn = rules.duration_warnings(int(T.FIXED_TERM), date(2026, 1, 1), date(2029, 1, 1))           # 36 tháng + 1 ngày
    assert len(warn) == 1 and "36" in warn[0]
    assert rules.duration_warnings(int(T.FIXED_TERM), date(2026, 1, 1), date(2040, 1, 1))
    assert rules.duration_warnings(int(T.PROBATION), date(2026, 1, 1), date(2040, 1, 1)) == []      # chỉ áp cho FIXED_TERM
    assert rules.duration_warnings(int(T.FIXED_TERM), date(2026, 1, 1), None) == []
