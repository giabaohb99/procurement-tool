"""Gói A3 (hiệu năng báo cáo, 01/10/2026) — `report_aggregate.aggregate()`: trần `GROUP_LIMIT`
nhóm. Trước gói này `groups` không có trần — `group_by=employee` ở quy mô hàng nghìn nhân sự ra
hàng nghìn nhóm/JSON cả MB (load-test, công nợ phép năm). Dữ liệu giả bằng `SimpleNamespace`,
không đụng model nghiệp vụ nào (cùng khuôn `test_bao_cao_khung_gom_nhom_va_xuat.py`).
"""
from datetime import date
from types import SimpleNamespace

from app.core.report_aggregate import (DimensionSpec, GROUP_LIMIT, MetricSpec,
                                       OTHER_GROUP_KEY, ReportSpec, aggregate, build_report)
from app.core.report_period import parse_period


def _row(dept, amount):
    return SimpleNamespace(date="2026-09-05", dept=dept, amount=amount)


def _spec() -> ReportSpec:
    dept = DimensionSpec("dept", "Phòng", key_of=lambda r: [(r.dept, r.dept)])
    #  `rank_by="amount"` TƯỜNG MINH — mỗi nhóm chỉ có 1 dòng (count luôn =1, mọi nhóm HÒA
    #  NHAU nếu xếp theo count mặc định), nên phải chỉ rõ chỉ số xếp hạng để test không phụ
    #  thuộc vào tie-break ổn định của `list.sort()`.
    return ReportSpec(
        date_of=lambda r: date.fromisoformat(r.date),
        metrics=[MetricSpec("count", "Số dòng", kind="int", value_of=lambda r: 1),
                MetricSpec("amount", "Giá trị", kind="money", value_of=lambda r: r.amount)],
        dimensions={"dept": dept}, rank_by="amount",
    )


def _rows_vuot_tran(n_extra: int):
    """`GROUP_LIMIT + n_extra` nhóm, mỗi nhóm 1 dòng, `amount` TĂNG DẦN theo thứ tự tên nhóm để
    xếp hạng (giảm dần theo `amount`, chỉ số đầu) predictable — nhóm "P0000" có amount LỚN NHẤT
    nên đứng ĐẦU, các nhóm "PNNNN" lớn dần tên thì amount NHỎ dần nên rơi vào phần GỘP."""
    n = GROUP_LIMIT + n_extra
    return [_row(f"P{i:05d}", n - i) for i in range(n)]


def test_duoi_tran_khong_bi_gop():
    rows = _rows_vuot_tran(-1)   # đúng GROUP_LIMIT - 1 nhóm -> KHÔNG vượt trần
    data = aggregate(rows, _spec(), date(2026, 9, 1), date(2026, 9, 30), "day", "dept")
    assert len(data["groups"]) == GROUP_LIMIT - 1
    assert all(g["key"] != OTHER_GROUP_KEY for g in data["groups"])


def test_dung_tran_khong_bi_gop():
    rows = _rows_vuot_tran(0)   # đúng GROUP_LIMIT nhóm -> "<=" nên KHÔNG kích hoạt gộp
    data = aggregate(rows, _spec(), date(2026, 9, 1), date(2026, 9, 30), "day", "dept")
    assert len(data["groups"]) == GROUP_LIMIT
    assert all(g["key"] != OTHER_GROUP_KEY for g in data["groups"])


def test_vuot_tran_gop_thanh_dung_1_hang_tong_so_luong_khong_doi():
    rows = _rows_vuot_tran(50)   # GROUP_LIMIT + 50 nhóm -> vượt trần, phải gộp
    data = aggregate(rows, _spec(), date(2026, 9, 1), date(2026, 9, 30), "day", "dept")
    groups = data["groups"]
    assert len(groups) == GROUP_LIMIT   # luôn ĐÚNG GROUP_LIMIT, không hơn
    assert groups[-1]["key"] == OTHER_GROUP_KEY   # hàng gộp luôn ở CUỐI (đã sort giảm dần)
    assert groups[-1]["label"] == "(Các nhóm khác — 51 nhóm)"   # 50 extra + 1 nhóm cuối cùng rơi vào lô cắt


def test_gop_tinh_lai_tu_hang_khong_cong_values_da_tinh():
    """`other_values` phải bằng TỔNG của đúng các hàng bị gộp — không phải tổng `values` các
    nhóm bị gộp (khác biệt vô nghĩa với `count`/`amount` kiểu cộng dồn thường, nhưng chứng minh
    luật ĐÚNG đường đi: tính lại từ rows, không lấy lại từ dict `values` đã có)."""
    rows = _rows_vuot_tran(10)   # GROUP_LIMIT+10 nhóm, mỗi nhóm có amount = n - i
    data = aggregate(rows, _spec(), date(2026, 9, 1), date(2026, 9, 30), "day", "dept")
    other = next(g for g in data["groups"] if g["key"] == OTHER_GROUP_KEY)
    n = GROUP_LIMIT + 10
    #  299 nhóm TOP (amount lớn nhất, tức i nhỏ nhất: i=0..298) giữ nguyên; phần GỘP là
    #  i=299..n-1 (n - 299 nhóm), amount = n - i cho từng nhóm đó.
    overflow_is = range(GROUP_LIMIT - 1, n)
    assert other["values"]["count"] == len(overflow_is)
    assert other["values"]["amount"] == sum(n - i for i in overflow_is)


def test_totals_khong_doi_khi_groups_bi_gop():
    """`totals` CỘNG TRỰC TIẾP trên toàn bộ hàng (luật cốt lõi của khung) — trần `groups` không
    được làm `totals` hụt mất phần dữ liệu bị gộp."""
    rows = _rows_vuot_tran(50)
    n = GROUP_LIMIT + 50
    data = aggregate(rows, _spec(), date(2026, 9, 1), date(2026, 9, 30), "day", "dept")
    assert data["totals"]["count"] == n
    assert data["totals"]["amount"] == sum(n - i for i in range(n))


def test_build_report_hop_khoa_other_xuyen_hai_ky():
    """`merge_groups_by_key` ghép khóa `OTHER_GROUP_KEY` XUYÊN HAI KỲ bình thường vì cả hai kỳ
    dùng chung một chuỗi khóa cố định — không bị tách thành hai hàng khác nhau."""
    rows_cur = _rows_vuot_tran(20)
    rows_cmp = _rows_vuot_tran(5)

    def fetch(d_from, d_to):
        return rows_cur if d_from.month == 9 else rows_cmp

    period = parse_period({"preset": "custom", "date_from": "2026-09-01", "date_to": "2026-09-30",
                           "compare": "previous"})
    report = build_report(fetch, _spec(), period, group_by="dept")
    other_rows = [g for g in report["groups"] if g["key"] == OTHER_GROUP_KEY]
    assert len(other_rows) == 1   # MỘT hàng duy nhất, không phải hai hàng trùng khóa
    assert other_rows[0]["current"] is not None and other_rows[0]["compare"] is not None
