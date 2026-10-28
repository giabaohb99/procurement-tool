"""duoc-CR-690 (phase 22) — bộ tính chi phí nhân sự theo kỳ `headcount_plan/costing.py` (hàm thuần, không DB).

Canh: từng cách tính (1–5), trần / người, áp theo vị trí, tháng rơi, chia đều quỹ cả phòng (dư dồn tháng đầu), kỳ con của
4 loại kỳ (định biên áp đúng tháng của kỳ con), gộp nhóm / tổng / bình quân, và mọi luật kiểm hợp lệ (câu tiếng Việt).
"""
from decimal import Decimal

import pytest

from app.modules.headcount_plan.costing import (CostItem, PlanCalcError, PlanLine, compute_plan, period_label,
                                                period_layout, period_months)

YEAR, HALF, QUARTER, MONTH = 1, 2, 3, 4
PER_HEAD, PERCENT, MONTHS_OF, ONCE, LUMP = 1, 2, 3, 4, 5
ALL, SELECTED, WHOLE = 1, 2, 3


def item(code, method=PER_HEAD, **kw):
    kw.setdefault("name", code)
    if "rate" in kw:
        kw["rate"] = Decimal(str(kw["rate"]))
    if "factor" in kw:
        kw["factor"] = Decimal(str(kw["factor"]))
    return CostItem(code=code, calc_method=method, **kw)


def line(pos, hc, **amounts):
    return PlanLine(position_id=pos, headcounts=tuple(hc), amounts=amounts)


def calc(items, lines, pt=YEAR, no=1, **kw):
    return compute_plan(pt, no, 2026, items, lines, **kw)


def row(res, code):
    return next(i for i in res["items"] if i["code"] == code)


# ---- Kỳ và kỳ con -----------------------------------------------------------------------------
@pytest.mark.parametrize("pt,no,keys,months", [
    (YEAR, 1, ["Q1", "Q2", "Q3", "Q4"], list(range(1, 13))),
    (HALF, 2, ["Q3", "Q4"], list(range(7, 13))),
    (HALF, 1, ["Q1", "Q2"], list(range(1, 7))),
    (QUARTER, 3, ["M07", "M08", "M09"], [7, 8, 9]),
    (MONTH, 11, ["M11"], [11]),
])
def test_ky_con_cua_bon_loai_ky(pt, no, keys, months):
    assert [p["key"] for p in period_layout(pt, no)] == keys
    assert period_months(pt, no) == months


@pytest.mark.parametrize("pt,no", [(YEAR, 2), (HALF, 3), (QUARTER, 5), (MONTH, 13), (9, 1), (QUARTER, 0)])
def test_ky_sai_so_thu_tu(pt, no):
    with pytest.raises(PlanCalcError):
        period_layout(pt, no)


def test_nhan_ky():
    assert [period_label(2026, YEAR, 1), period_label(2026, HALF, 2), period_label(2026, QUARTER, 3),
            period_label(2026, MONTH, 7)] == ["2026", "H2-2026", "Q3-2026", "07/2026"]


def test_dinh_bien_ky_con_ap_cho_dung_cac_thang_cua_ky_con():
    res = calc([item("L")], [line(1, [1, 2, 3, 4], L=1000)])
    assert row(res, "L")["values"] == [3000, 6000, 9000, 12000]     # Q1: 1 người × 3 tháng, Q2: 2 × 3 …
    assert res["monthly"][4]["headcount"] == 2 and res["monthly"][12]["items"]["L"] == 4000
    assert res["headcount"] == [1, 2, 3, 4]
    assert res["total"]["total"] == 30000


def test_ky_thang_mot_cot_ky_quy_ba_cot_thang():
    res = calc([item("L")], [line(1, [5], L=100)], MONTH, 7)
    assert [p["key"] for p in res["periods"]] == ["M07"] and row(res, "L")["values"] == [500]
    res = calc([item("L")], [line(1, [1, 2, 3], L=100)], QUARTER, 2)
    assert row(res, "L")["values"] == [100, 200, 300]


# ---- Cách tính 1: số tiền / người / tháng ------------------------------------------------------
def test_cach_1_nhieu_vi_tri_va_thang_roi():
    items = [item("L"), item("AN", months=(3, 4))]
    res = calc(items, [line(1, [2, 2, 2, 2], L=10, AN=5), line(2, [1, 1, 1, 1], L=20, AN=7)])
    assert row(res, "L")["total"] == (2 * 10 + 20) * 12
    assert row(res, "AN")["values"] == [(2 * 5 + 7) * 1, (2 * 5 + 7) * 1, 0, 0]   # chỉ T3 (Q1) và T4 (Q2)


def test_cach_1_chi_ap_cho_vi_tri_da_chon_va_khong_nhap_la_0():
    res = calc([item("PC", applies_to=SELECTED, position_ids=(2,))],
               [line(1, [3] * 4, PC=100), line(2, [1] * 4, PC=100), line(0, [1] * 4)])
    assert row(res, "PC")["total"] == 100 * 12     # chỉ vị trí 2; số nhập ở vị trí 1 bị bỏ qua


# ---- Cách tính 2: % trên khoản khác -------------------------------------------------------------
def test_cach_2_phan_tram_khong_tran():
    res = calc([item("L"), item("PC"), item("BH", PERCENT, rate=17.5, base_codes=("L", "PC"))],
               [line(1, [4] * 4, L=12_000_000, PC=1_000_000)])
    assert row(res, "BH")["values"][0] == round(4 * 13_000_000 * 0.175 * 3)


def test_cach_2_tran_tinh_theo_tung_nguoi_chu_khong_theo_tong():
    items = [item("L"), item("BH", PERCENT, rate=17.5, base_codes=("L",), cap_amount=46_800_000)]
    res = calc(items, [line(1, [2] * 4, L=60_000_000), line(2, [3] * 4, L=10_000_000)])
    month = 2 * 46_800_000 * 0.175 + 3 * 10_000_000 * 0.175
    assert row(res, "BH")["values"][0] == round(month * 3)


def test_cach_2_lam_tron_nua_len_tung_thang():
    res = calc([item("L"), item("T", PERCENT, rate=3, base_codes=("L",))], [line(1, [1], L=50)], MONTH, 1)
    assert row(res, "T")["total"] == 2          # 1.5 → 2


def test_cach_2_goc_la_khoan_so_thang_va_ap_rieng_cho_vi_tri():
    items = [item("L"), item("B13", MONTHS_OF, factor=1, base_codes=("L",), months=(12,)),
             item("X", PERCENT, rate=10, base_codes=("B13",), applies_to=SELECTED, position_ids=(1,))]
    res = calc(items, [line(1, [1] * 4, L=100), line(2, [1] * 4, L=500)])
    assert row(res, "X")["values"] == [0, 0, 0, 10]     # 10% của (thưởng T12 vị trí 1 = 100), vị trí 2 không áp


# ---- Cách tính 3: số tháng của một khoản ---------------------------------------------------------
def test_cach_3_thuong_thang_13_roi_vao_thang_12():
    res = calc([item("L"), item("B13", MONTHS_OF, factor=1.5, base_codes=("L",), months=(12,))],
               [line(1, [1, 1, 1, 2], L=1000)])
    assert row(res, "B13")["values"] == [0, 0, 0, 3000]      # 2 người × 1,5 × 1000 (định biên Q4)


# ---- Cách tính 4 và 5 -------------------------------------------------------------------------
def test_cach_4_so_tien_moi_nguoi_moi_lan():
    res = calc([item("Q83", ONCE, amount=500_000, months=(3,))], [line(1, [4, 5, 5, 5])])
    assert row(res, "Q83")["values"] == [2_000_000, 0, 0, 0]


def test_cach_5_quy_ca_phong_chia_deu_cac_thang_roi_vao_du_don_thang_dau():
    res = calc([item("DL", LUMP, amount=50_000_000, applies_to=WHOLE, months=(6,))], [line(1, [1] * 4)])
    assert row(res, "DL")["values"] == [0, 50_000_000, 0, 0]
    res = calc([item("T", LUMP, amount=100, applies_to=WHOLE)], [line(1, [1] * 4)])        # mọi tháng của kỳ
    assert row(res, "T")["total"] == 100 and res["monthly"][1]["items"]["T"] == 9 and res["monthly"][12]["items"]["T"] == 8
    res = calc([item("T", LUMP, amount=300, applies_to=WHOLE)], [line(1, [1, 1, 1])], QUARTER, 1)
    assert row(res, "T")["values"] == [100, 100, 100]


# ---- Gộp nhóm, tổng, bình quân -----------------------------------------------------------------
def test_gop_nhom_tong_va_binh_quan_dau_nguoi():
    items = [item("L", group_id=1), item("PC", group_id=1), item("AN", ONCE, amount=10, group_id=2, months=(1,))]
    res = calc(items, [line(1, [1] * 4, L=100, PC=20)], group_names={1: "Quỹ lương", 2: "Phúc lợi"})
    assert [g["name"] for g in res["groups"]] == ["Quỹ lương", "Phúc lợi"]
    assert res["groups"][0]["total"] == 120 * 12 and res["groups"][1]["total"] == 10
    assert res["total"]["total"] == 1450 and res["total"]["values"] == [370, 360, 360, 360]
    assert res["avg_per_head"] == 1450             # 1 người bình quân cả kỳ


def test_nhom_xep_theo_thu_tu_cua_danh_muc_nhom():
    #  HDSD CR-690: ô «Thứ tự trên bảng tự tính» của Nhóm chi phí từng bị bỏ qua (nhóm xếp theo khoản đầu tiên).
    items = [item("L", group_id=1), item("AN", ONCE, amount=10, group_id=2, months=(1,))]
    res = calc(items, [line(1, [1] * 4, L=100)], group_names={1: "Quỹ lương", 2: "Phúc lợi"}, group_sort={1: 20, 2: 10})
    assert [g["name"] for g in res["groups"]] == ["Phúc lợi", "Quỹ lương"]


def test_binh_quan_none_khi_khong_co_nguoi_va_thu_tu_theo_sort_order():
    res = calc([item("B", sort_order=2, name="B"), item("A", sort_order=1, name="A")], [])
    assert res["avg_per_head"] is None and [i["code"] for i in res["items"]] == ["A", "B"]
    assert res["headcount"] == [0, 0, 0, 0] and res["total"]["total"] == 0


def test_monthly_cho_bao_cao_phase_24():
    res = calc([item("L")], [line(1, [1, 2, 0, 0], L=10)])
    assert res["monthly"][1] == {"headcount": 1, "items": {"L": 10}}
    assert res["monthly"][5] == {"headcount": 2, "items": {"L": 20}} and res["monthly"][9]["headcount"] == 0


# ---- Ví dụ §5 của tài liệu thiết kế: Kế toán · Năm 2026 -----------------------------------------
def test_vi_du_ke_toan_nam_2026():
    items = [item("L", group_id=1), item("PCCV", group_id=1), item("AN", group_id=1),
             item("BHXH", PERCENT, rate=17.5, base_codes=("L", "PCCV"), cap_amount=46_800_000, group_id=2),
             item("BHYT", PERCENT, rate=3, base_codes=("L", "PCCV"), cap_amount=46_800_000, group_id=2),
             item("B13", MONTHS_OF, factor=1, base_codes=("L",), months=(12,), group_id=3),
             item("Q83", ONCE, amount=500_000, months=(3,), group_id=3)]
    res = calc(items, [line(1, [0, 1, 1, 1], L=25_000_000, PCCV=3_000_000, AN=730_000),
                       line(2, [4, 4, 5, 5], L=12_000_000, PCCV=1_000_000, AN=730_000)])
    q1_kt = 4 * 3 * (12_000_000 + 1_000_000 + 730_000)
    assert row(res, "L")["values"][0] == 4 * 3 * 12_000_000
    assert row(res, "AN")["values"][0] == 4 * 3 * 730_000
    assert row(res, "BHXH")["values"][0] == round(4 * 13_000_000 * 0.175 * 3)
    assert row(res, "Q83")["values"] == [4 * 500_000, 0, 0, 0]
    assert row(res, "B13")["values"] == [0, 0, 0, 25_000_000 + 5 * 12_000_000]
    assert sum(res["groups"][0]["values"][:1]) == q1_kt
    assert res["headcount"] == [4, 5, 6, 6]


# ---- Kiểm hợp lệ ---------------------------------------------------------------------------------
def bad(items, lines=(), pt=YEAR, no=1, match=""):
    with pytest.raises(PlanCalcError, match=match):
        compute_plan(pt, no, 2026, list(items), list(lines))


def test_ma_trung_va_ma_rong():
    bad([item("A"), item("A")], match="trùng")
    bad([item("")], match="thiếu mã")


def test_khoan_goc_khong_ton_tai_tro_percent_hoac_tu_tro():
    bad([item("P", PERCENT, rate=1, base_codes=("X",))], match="không còn trong kế hoạch")
    bad([item("L"), item("P1", PERCENT, rate=1, base_codes=("L",)), item("P2", PERCENT, rate=1, base_codes=("P1",))],
        match="không dùng được ở «Tính trên khoản»")
    bad([item("P", PERCENT, rate=1, base_codes=("P",))], match="không dùng được ở «Tính trên khoản»")
    bad([item("P", PERCENT, rate=1, base_codes=())], match="chưa chọn «Tính trên khoản»")
    bad([item("L"), item("O", ONCE, amount=1, months=(1,)), item("P", PERCENT, rate=1, base_codes=("O",))], match="Tính trên khoản")


def test_so_thang_phai_dung_mot_goc_va_co_thang_roi():
    bad([item("L"), item("B", MONTHS_OF, factor=1, base_codes=("L", "L"), months=(12,))], match="đúng một khoản ở «Tính trên khoản»")
    bad([item("L"), item("B", MONTHS_OF, factor=1, base_codes=("L",))], match="chưa chọn tháng chi")
    bad([item("L"), item("B", MONTHS_OF, factor=1, base_codes=("B",), months=(1,))], match="không còn trong kế hoạch|Tính trên khoản")


def test_thang_ngoai_ky():
    bad([item("A", ONCE, amount=1, months=(12,))], pt=QUARTER, no=1, match="ngoài kỳ")
    bad([item("A", ONCE, amount=1, months=(2,))], pt=MONTH, no=1, match="ngoài kỳ")


def test_ca_phong_chi_voi_quy_ca_phong_va_vi_tri_da_chon_phai_co_vi_tri():
    bad([item("A", ONCE, amount=1, applies_to=WHOLE)], match="cả phòng")
    bad([item("A", applies_to=SELECTED)], match="ít nhất một vị trí")


def test_so_am_va_ma_la():
    bad([item("A", ONCE, amount=-1)], match="không được âm")
    bad([item("A", PERCENT, rate=-1, base_codes=())], match="không được âm")
    bad([item("A", 9)], match="cách tính không hợp lệ")
    bad([item("A", applies_to=7)], match="phạm vi áp dụng")


def test_dong_dinh_bien_sai():
    bad([item("L")], [line(1, [1, 2, 3])], match="đúng 4 số")
    bad([item("L")], [line(1, [1, 1, 1, -1])], match="không được âm")
    bad([item("L")], [line(1, [1] * 4), line(1, [2] * 4)], match="một dòng")
    bad([item("L")], [line(1, [1] * 4, X=5)], match="không phải khoản nhập theo vị trí")
    bad([item("L")], [line(1, [1] * 4, L=-5)], match="không được âm")
    bad([item("P", ONCE, amount=1, months=(1,))], [line(1, [1] * 4, P=5)], match="không phải khoản nhập theo vị trí")


def test_muc_chung_cua_khoan_hang_thang_dung_khi_vi_tri_de_trong():
    #  Anh Được: «chỗ thêm khoản không quản lý được tiền à» — khoản hằng tháng có mức chung (amount) cho mọi vị trí,
    #  vị trí nào nhập số riêng (> 0) thì số riêng thắng; % tính trên cả hai.
    items = [item("AN", amount=730_000), item("BH", PERCENT, rate=10, base_codes=("AN",))]
    res = calc(items, [line(1, [2] * 4), line(2, [1] * 4, AN=1_000_000)])
    assert row(res, "AN")["values"][0] == (2 * 730_000 + 1_000_000) * 3
    assert row(res, "BH")["values"][0] == (2 * 73_000 + 100_000) * 3
