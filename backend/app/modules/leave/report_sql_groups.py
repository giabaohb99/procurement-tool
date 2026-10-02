"""Nhóm (`groups`, "Xem theo") và xếp hạng (`breakdowns`) của `/api/leave-requests/summary` —
GOM theo ĐÚNG MỘT chiều ở SQL (`report_sql_metrics.dim_columns`), nên số NHÓM trả về bị chặn
bởi số giá trị PHÂN BIỆT của chiều đó (vài nghìn nhân sự tối đa ở quy mô công ty thật), không
phải bởi số đơn/số dòng — khác hẳn bản cũ (`report_aggregate.aggregate()`) vốn phải nạp TOÀN
BỘ hàng thô vào Python rồi mới gom theo chiều (gói B, review hiệu năng 01/10/2026).
"""
from __future__ import annotations

from typing import Callable

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.report_aggregate import BREAKDOWN_LIMIT, EMPTY_LABEL, GROUP_LIMIT, OTHER_GROUP_KEY
from app.core.report_compute import compute_derived
from app.modules.leave.report_sql_metrics import (DERIVED, dim_columns, header_aggregate,
                                                   line_aggregate, merge_dim_rows, totals_dict)
from app.modules.leave.request_model import LeaveRequest, LeaveRequestLine


def groups_for_dim(db: Session, scoped_query, header_subq, dim: str,
                   label_of: Callable[[int], str]) -> list[dict]:
    """`groups` (Xem theo) CỦA MỘT KỲ — CHƯA sắp hạng/hợp kỳ so sánh, việc đó do
    `report_compute.merge_groups_by_key` lo (gọi SAU, ở `report_service.py`). Trả về theo thứ
    tự `first_date` TĂNG DẦN — tiêu chí phụ khi HÒA ĐIỂM về sau, xem `merge_dim_rows`."""
    header_col, line_col = dim_columns(dim, header_subq)
    merged = merge_dim_rows(
        header_aggregate(db, scoped_query, group_col=header_col, with_first_date=True),
        line_aggregate(db, header_subq, group_col=line_col, with_first_date=True), label_of)
    out = []
    for key, bucket in sorted(merged.items(), key=lambda kv: kv[1]["first_date"]):
        values = dict(bucket)
        label = values.pop("label")
        values.pop("first_date")
        values.update(compute_derived(values, DERIVED))
        out.append({"key": key, "label": label, "values": values})
    return out


def _raw_key_filter(dim_col, keys: list[str]):
    """Điều kiện SQL "giá trị CHIỀU này nằm trong tập khóa đã chuẩn hóa" — khóa `""` nghĩa là
    0 (`merge_dim_rows`/`bucket_rows` gộp falsy về đó); `keys` LUÔN không rỗng (caller canh)."""
    ints = [int(k) for k in keys if k != ""]
    conds = [dim_col.in_(ints)] if ints else []
    if "" in keys:
        conds.append(dim_col == 0)
    return conds[0] if len(conds) == 1 else or_(*conds)


def cap_groups(db: Session, scoped_query, header_subq, dim: str, groups: list[dict],
              rank: str) -> list[dict]:
    """Trần `GROUP_LIMIT` nhóm — mirror `report_aggregate._cap_groups` (gói A3, 01/10/2026):
    MỘT báo cáo không được thoát trần mà 12 báo cáo còn lại dùng khung chung phải chịu, đặc
    biệt `group_by=employee` CHÍNH LÀ ca GROUP_LIMIT sinh ra để chặn (~5.000 nhân sự ra ~5.000
    nhóm/~1MB JSON, xem load-test gói A3). KHÔNG tái dùng được hàm gốc — nó cộng lại từ
    `buckets[key]["rows"]` (hàng Python), mà đường SQL này không còn giữ hàng thô — nên tính
    LẠI phần dư bằng MỘT TRUY VẤN TỔNG lọc đúng tập khóa bị gộp, tránh lỗi "cộng tỷ lệ dẫn
    xuất" (trung bình-của-trung-bình) nếu cộng thẳng `values` đã tính của từng nhóm. Gọi SAU
    `groups_for_dim`, TRƯỚC `report_compute.merge_groups_by_key` — đúng thứ tự `aggregate()`
    gốc (cắt trần MỘT KỲ rồi mới ghép kỳ so sánh, nên "(Các nhóm khác)" của 2 kỳ ghép theo
    đúng một khóa chuỗi cố định `OTHER_GROUP_KEY`)."""
    sorted_groups = sorted(groups, key=lambda g: g["values"].get(rank, 0) or 0, reverse=True)
    if len(sorted_groups) <= GROUP_LIMIT:
        return sorted_groups
    kept, overflow = sorted_groups[:GROUP_LIMIT - 1], sorted_groups[GROUP_LIMIT - 1:]
    header_col, line_col = dim_columns(dim, header_subq)
    overflow_keys = [g["key"] for g in overflow]
    h_row = header_aggregate(db, scoped_query.filter(_raw_key_filter(header_col, overflow_keys)),
                             group_col=None)
    l_row = line_aggregate(db, header_subq, group_col=None,
                           extra_filter=_raw_key_filter(line_col, overflow_keys))
    other_values = totals_dict(h_row, l_row)
    other_values.update(compute_derived(other_values, DERIVED))
    kept.append({"key": OTHER_GROUP_KEY, "label": f"(Các nhóm khác — {len(overflow)} nhóm)",
                "values": other_values})
    return kept


def _rank_items(rows: dict[str, dict]) -> list[dict]:
    """Sắp giảm dần, bỏ giá trị 0/rỗng, cắt ngọn `BREAKDOWN_LIMIT` — cùng luật
    `report_aggregate.aggregate()` dùng cho MỌI breakdown."""
    items = [{"key": k, "label": b["label"], "value": b["value"]} for k, b in rows.items()]
    items = sorted((i for i in items if i["value"]), key=lambda x: x["value"], reverse=True)
    return items[:BREAKDOWN_LIMIT]


def breakdown_by_status(db: Session, scoped_query, label_of: Callable[[int], str]) -> list[dict]:
    """"Trạng thái" — xếp theo SỐ ĐƠN (`rank_by` mặc định của khung, "requests"). Trạng thái
    DRAFT đã bị lọc ở `scoped_requests` nên khóa không bao giờ rỗng/0 trong thực tế, nhưng vẫn
    chuẩn hóa như mọi chiều khác để không phụ thuộc giả định đó. Nạp theo `first_date` TĂNG
    DẦN trước khi xếp hạng — cùng tiêu chí hòa điểm với `groups_for_dim`, xem `merge_dim_rows`."""
    rows = header_aggregate(db, scoped_query, group_col=LeaveRequest.status, with_first_date=True)
    out = {}
    for r in sorted(rows, key=lambda r: r.first_date):
        k = "" if not r.key else str(r.key)
        out[k] = {"label": label_of(r.key) if k else EMPTY_LABEL, "value": int(r.requests or 0)}
    return _rank_items(out)


def breakdown_leave_type_by_days(db: Session, header_subq, type_name: dict) -> list[dict]:
    """Mục 5 — "Top loại nghỉ" xếp theo TỔNG NGÀY ĐÃ DUYỆT (`days_approved`, tính từ DÒNG —
    có mặt ở CẢ loại chính lẫn loại phụ của đơn), KHÔNG xếp theo `rank_by` mặc định của khung
    ("requests", chỉ đếm loại CHÍNH) — loại nghỉ chỉ xuất hiện ở DÒNG PHỤ của mọi đơn (không
    bao giờ là loại chính) trước đây luôn rơi xuống đáy bất kể dùng bao nhiêu ngày (xem
    `TestBreakdownLoaiNghiXepTheoNgay`). Nạp theo `first_date` TĂNG DẦN — cùng tiêu chí hòa
    điểm với `groups_for_dim`."""
    rows = line_aggregate(db, header_subq, group_col=LeaveRequestLine.leave_type_id,
                          with_first_date=True)
    out = {}
    for r in sorted(rows, key=lambda r: r.first_date):
        k = "" if not r.key else str(r.key)
        out[k] = {"label": type_name.get(r.key, "") if k else EMPTY_LABEL,
                  "value": float(r.days_approved or 0)}
    return _rank_items(out)
