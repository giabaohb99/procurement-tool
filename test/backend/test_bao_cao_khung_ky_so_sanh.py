"""P01 khung báo cáo — `report_period.py`: preset, kỳ so sánh, độ hạt, cận UTC/VN.

Không cần fixture `seed` — hầu hết test là hàm THUẦN với `today` cố định. Riêng
`range_filter` cần chạy được câu SQL thật (khác nhau giữa 'str'/'date'/'datetime_utc') nên
dựng bảng tạm qua SQLAlchemy Core, không đụng model nghiệp vụ nào (framework này KHÔNG
thuộc về một bảng cụ thể).
"""
from datetime import date, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import Date, DateTime, Integer, MetaData, String, Table, Column, select

from app.core.report_period import bucket_axis, parse_period, range_filter, resolve_granularity, to_local_date

TODAY = date(2026, 9, 28)  # thứ Hai — cùng ngày "hôm nay" dùng cho phần lớn preset test


# ── Preset mặc định + so sánh kiểu lịch/cuộn/năm ────────────────────────────────
def test_default_preset_la_thang_nay_so_sanh_ky_truoc():
    p = parse_period({}, today=TODAY)
    assert p.preset == "this_month" and p.compare == "previous"
    assert (p.date_from, p.date_to) == (date(2026, 9, 1), TODAY)
    assert (p.compare_from, p.compare_to) == (date(2026, 8, 1), date(2026, 8, 28))


def test_preset_today_va_yesterday_qua_bien_thang():
    p = parse_period({"preset": "today"}, today=TODAY)
    assert (p.date_from, p.date_to) == (TODAY, TODAY)
    assert (p.compare_from, p.compare_to) == (date(2026, 9, 27), date(2026, 9, 27))

    p2 = parse_period({"preset": "yesterday"}, today=date(2026, 9, 1))
    assert (p2.date_from, p2.date_to) == (date(2026, 8, 31), date(2026, 8, 31))
    assert (p2.compare_from, p2.compare_to) == (date(2026, 8, 30), date(2026, 8, 30))


def test_preset_last_7_va_30_days_lui_cung_so_ngay():
    p7 = parse_period({"preset": "last_7_days"}, today=TODAY)
    assert (p7.date_from, p7.date_to) == (date(2026, 9, 22), TODAY)
    assert (p7.compare_from, p7.compare_to) == (date(2026, 9, 15), date(2026, 9, 21))

    p30 = parse_period({"preset": "last_30_days"}, today=TODAY)
    assert (p30.date_from, p30.date_to) == (date(2026, 8, 30), TODAY)
    assert (p30.compare_from, p30.compare_to) == (date(2026, 7, 31), date(2026, 8, 29))


def test_preset_lich_cat_ve_cuoi_thang_khi_thang_dich_ngan_hon():
    """31/03 → kỳ trước phải cắt về 28/02 (2026 không nhuận) — đúng ví dụ trong plan."""
    p = parse_period({"preset": "this_month"}, today=date(2026, 3, 31))
    assert (p.date_from, p.date_to) == (date(2026, 3, 1), date(2026, 3, 31))
    assert (p.compare_from, p.compare_to) == (date(2026, 2, 1), date(2026, 2, 28))


def test_preset_this_quarter_lui_dung_3_thang():
    """1/07–28/09 → 1/04–28/06 — đúng ví dụ trong plan."""
    p = parse_period({"preset": "this_quarter"}, today=TODAY)
    assert (p.date_from, p.date_to) == (date(2026, 7, 1), TODAY)
    assert (p.compare_from, p.compare_to) == (date(2026, 4, 1), date(2026, 6, 28))


def test_preset_this_year_va_last_year():
    p = parse_period({"preset": "this_year"}, today=TODAY)
    assert (p.date_from, p.date_to) == (date(2026, 1, 1), TODAY)
    assert (p.compare_from, p.compare_to) == (date(2025, 1, 1), date(2025, 9, 28))

    p2 = parse_period({"preset": "last_year"}, today=TODAY)
    assert (p2.date_from, p2.date_to) == (date(2025, 1, 1), date(2025, 12, 31))
    assert (p2.compare_from, p2.compare_to) == (date(2024, 1, 1), date(2024, 12, 31))


def test_compare_year_29_02_lui_ve_28_02():
    """compare=year: 2028 nhuận (29/02 có thật), 2027 không — phải cắt về 28/02."""
    p = parse_period({"preset": "today", "compare": "year"}, today=date(2028, 2, 29))
    assert (p.date_from, p.date_to) == (date(2028, 2, 29), date(2028, 2, 29))
    assert (p.compare_from, p.compare_to) == (date(2027, 2, 28), date(2027, 2, 28))


def test_preset_custom_compare_previous_la_cuon_khong_cat_lich():
    p = parse_period({"preset": "custom", "date_from": "2026-09-10", "date_to": "2026-09-20"})
    assert (p.date_from, p.date_to) == (date(2026, 9, 10), date(2026, 9, 20))
    assert (p.compare_from, p.compare_to) == (date(2026, 8, 30), date(2026, 9, 9))


def test_compare_none_khong_co_ky_so_sanh():
    p = parse_period({"preset": "this_month", "compare": "none"}, today=TODAY)
    assert p.compare == "none"
    assert p.compare_from is None and p.compare_to is None


def test_preset_duoc_loi_ra_trong_period():
    p = parse_period({"preset": "last_7_days"}, today=TODAY)
    assert p.as_dict()["preset"] == "last_7_days"


# ── Chặn đầu vào sai — 422 ───────────────────────────────────────────────────────
def test_preset_la_sai_nem_422():
    with pytest.raises(HTTPException) as exc:
        parse_period({"preset": "thang-trang"}, today=TODAY)
    assert exc.value.status_code == 422


def test_compare_sai_nem_422():
    with pytest.raises(HTTPException) as exc:
        parse_period({"compare": "khong-hop-le"}, today=TODAY)
    assert exc.value.status_code == 422


def test_custom_thieu_ngay_nem_422():
    with pytest.raises(HTTPException):
        parse_period({"preset": "custom", "date_from": "2026-09-01"}, today=TODAY)


def test_custom_sai_dinh_dang_nem_422():
    with pytest.raises(HTTPException):
        parse_period({"preset": "custom", "date_from": "10-09-2026", "date_to": "2026-09-20"})


def test_den_truoc_tu_nem_422():
    with pytest.raises(HTTPException):
        parse_period({"preset": "custom", "date_from": "2026-09-20", "date_to": "2026-09-10"})


def test_khoang_vuot_1096_ngay_nem_422():
    with pytest.raises(HTTPException) as exc:
        parse_period({"preset": "custom", "date_from": "2020-01-01", "date_to": "2023-06-01"})
    assert exc.value.status_code == 422


# ── Độ hạt: ≤31 ngày / ≤92 tuần / còn lại tháng ─────────────────────────────────
def test_do_hat_nguong_31_32_92_93_ngay():
    assert resolve_granularity(date(2026, 1, 1), date(2026, 1, 31)) == "day"        # 31 ngày
    assert resolve_granularity(date(2026, 1, 1), date(2026, 2, 1)) == "week"        # 32 ngày
    assert resolve_granularity(date(2026, 1, 1), date(2026, 1, 1) + timedelta(days=91)) == "week"   # 92
    assert resolve_granularity(date(2026, 1, 1), date(2026, 1, 1) + timedelta(days=92)) == "month"  # 93


def test_bucket_axis_tuan_bat_dau_thu_hai_cat_theo_bien_ky():
    d_from, d_to = date(2026, 9, 30), date(2026, 10, 20)  # thứ Tư -> thứ Ba, lệch giữa tuần
    axis = bucket_axis(d_from, d_to, "week")
    assert [a["key"] for a in axis] == ["2026-09-28", "2026-10-05", "2026-10-12", "2026-10-19"]
    assert axis[0]["label"] == "30/09-04/10"    # cắt về d_from, không lùi về thứ Hai 28/09
    assert axis[-1]["label"] == "19/10-20/10"   # cắt về d_to


# ── Giờ VN vs UTC ─────────────────────────────────────────────────────────────
def test_to_local_date_utc_17h30_sang_ngay_vn_hom_sau():
    assert to_local_date(datetime(2026, 9, 27, 17, 30)) == date(2026, 9, 28)
    assert to_local_date(datetime(2026, 9, 27, 16, 59)) == date(2026, 9, 27)
    assert to_local_date("2026-09-28") == date(2026, 9, 28)
    assert to_local_date(date(2026, 9, 28)) == date(2026, 9, 28)
    assert to_local_date(None) is None
    assert to_local_date("khong-phai-ngay") is None


def test_range_filter_str(db):
    meta = MetaData()
    t = Table("t_bckyss_str", meta, Column("id", Integer, primary_key=True), Column("d", String(20)))
    meta.create_all(db.get_bind())
    db.execute(t.insert(), [{"id": 1, "d": "2026-09-01"}, {"id": 2, "d": "2026-09-28"},
                             {"id": 3, "d": "2026-09-29"}])
    db.commit()
    cond = range_filter(t.c.d, "str", date(2026, 9, 1), date(2026, 9, 28))
    ids = sorted(r[0] for r in db.execute(select(t.c.id).where(cond)))
    assert ids == [1, 2]


def test_range_filter_date(db):
    meta = MetaData()
    t = Table("t_bckyss_date", meta, Column("id", Integer, primary_key=True), Column("d", Date))
    meta.create_all(db.get_bind())
    db.execute(t.insert(), [{"id": 1, "d": date(2026, 9, 1)}, {"id": 2, "d": date(2026, 9, 28)},
                             {"id": 3, "d": date(2026, 9, 29)}])
    db.commit()
    cond = range_filter(t.c.d, "date", date(2026, 9, 1), date(2026, 9, 28))
    ids = sorted(r[0] for r in db.execute(select(t.c.id).where(cond)))
    assert ids == [1, 2]


def test_range_filter_datetime_utc_bien_17h_vn_hom_sau(db):
    """Kỳ VN [28/09, 28/09] -> cận UTC là [27/09 17:00, 28/09 17:00) — đúng luật +7h."""
    meta = MetaData()
    t = Table("t_bckyss_dt", meta, Column("id", Integer, primary_key=True), Column("d", DateTime))
    meta.create_all(db.get_bind())
    db.execute(t.insert(), [
        {"id": 1, "d": datetime(2026, 9, 27, 16, 59, 0)},  # VN 27/09 23:59 -> ngoài kỳ
        {"id": 2, "d": datetime(2026, 9, 27, 17, 30, 0)},  # VN 28/09 00:30 -> trong kỳ
        {"id": 3, "d": datetime(2026, 9, 28, 16, 59, 0)},  # VN 28/09 23:59 -> trong kỳ
        {"id": 4, "d": datetime(2026, 9, 28, 17, 0, 0)},   # VN 29/09 00:00 -> ngoài kỳ (biên trên)
    ])
    db.commit()
    cond = range_filter(t.c.d, "datetime_utc", date(2026, 9, 28), date(2026, 9, 28))
    ids = sorted(r[0] for r in db.execute(select(t.c.id).where(cond)))
    assert ids == [2, 3]
