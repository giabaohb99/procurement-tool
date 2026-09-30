"""Tổng hợp Báo cáo mua hàng kiểu Haravan (P03, `GET /api/reports/procurement/summary`).

`report_aggregate.build_report` chỉ gọi MỘT `fetch(d_from, d_to)`, nhưng báo cáo này có
HAI nguồn với HAI cột ngày khác nhau (Q3.2 đã chốt): chi phí mua theo `Payable.incur_date`,
giá trị đặt + số ĐMH theo `PurchaseOrder.order_date`. Giải pháp (`procurement_summary_rows.py`):
GỘP hai nguồn vào MỘT danh sách hàng có kiểu (`Row.kind`) — mỗi `MetricSpec` chỉ đọc đúng kiểu
hàng của mình (trả 0 cho kiểu kia), `date_of` chọn đúng cột ngày theo kiểu hàng. Nhờ vậy mỗi
khoản tiền vẫn được lọc đúng theo cột ngày nghĩa của nó, không phải chọn đại một cột chung.

Công nợ còn lại / quá hạn là chỉ số THỜI ĐIỂM — tính qua tham số `snapshot` của `build_report`,
KHÔNG cộng dồn theo kỳ. Hệ thống không lưu lịch sử số dư nên đây là XẤP XỈ (xem `notes` của
hợp đồng trả về): dùng số dư HIỆN TẠI của các khoản nợ phát sinh trước/trong ngày mốc.

Review 28/09/2026: phòng ban của hàng "payable" nay tra được (Finding #3, xem
`procurement_summary_rows.payable_rows`) nên áp luôn phạm vi phòng ban của bảng nguồn
`/api/reports/matrix` (`report_dept_scope`, M4) — trước đó chưa áp được vì chưa có phòng ban
để lọc theo.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_period import Period, to_local_date
from app.modules.company.model import Company
from app.modules.department.model import Department

from . import procurement_summary_rows as rows
from . import service as report_service
from .procurement_grouped_rows import grouped_po_rows

EMPTY_LABEL = "(Chưa gắn)"
#  Hai chiều nhạy cảm — chỉ NGƯỜI ĐƯỢC XEM ĐMH (`_can_see_ncc`) mới ép được `group_by` này.
_NCC_DIMENSIONS = ("supplier", "nspt")


def _build_spec(db: Session, show_ncc: bool) -> ReportSpec:
    company_name = {c.id: c.name for c in db.query(Company).all()}

    metrics = [
        MetricSpec("spend", "Chi phí mua hàng", kind="money",
                  value_of=lambda r: r.spend if r.kind == "payable" else 0),
        MetricSpec("order_value", "Giá trị đặt hàng", kind="money",
                  value_of=lambda r: r.order_value if r.kind == "po" else 0),
        MetricSpec("po_count", "Số ĐMH", kind="int",
                  distinct_of=lambda r: r.po_id if r.kind == "po" else None),
        MetricSpec("deliveries_done", "Lần giao đã nhận", kind="int", helper=True,
                  value_of=lambda r: r.deliveries_done if r.kind == "po" else 0),
        MetricSpec("on_time_deliveries", "Lần giao đúng hạn", kind="int",
                  value_of=lambda r: r.on_time_deliveries if r.kind == "po" else 0),
        #  Hai chỉ số THỜI ĐIỂM (`snapshot=True`, M1) — `value_of` luôn 0 (bị `drop_snapshot`
        #  bỏ khỏi trend/groups), `snapshot()` GHI ĐÈ giá trị thật lên `totals` sau khi
        #  build_report cộng dồn xong. Khai MetricSpec ở đây chỉ để `meta` có nhãn/loại.
        MetricSpec("debt_remaining", "Công nợ còn lại", kind="money", snapshot=True, value_of=lambda r: 0),
        MetricSpec("debt_overdue", "Công nợ quá hạn", kind="money", good="down", snapshot=True,
                  value_of=lambda r: 0),
    ]
    derived = [DerivedSpec("on_time_rate", "Giao đúng hạn", num="on_time_deliveries",
                          den="deliveries_done", good="up")]

    dimensions = {
        "department": DimensionSpec("department", "Bộ phận",
                                    key_of=lambda r: [(r.department, r.department)] if r.department else []),
        "item_group": DimensionSpec("item_group", "Nhóm hàng",
                                    key_of=lambda r: [(r.item_group, r.item_group)] if r.item_group else []),
        "company": DimensionSpec("company", "Công ty",
                                 key_of=(lambda r: [(r.company_id, company_name.get(r.company_id, EMPTY_LABEL))]
                                        if r.company_id else [])),
    }
    if show_ncc:
        dimensions["supplier"] = DimensionSpec(
            "supplier", "Nhà cung cấp",
            key_of=lambda r: [(r.supplier, r.supplier)] if r.supplier else [])
        dimensions["nspt"] = DimensionSpec(
            "nspt", "NSPT", key_of=lambda r: [(r.nspt, r.nspt)] if r.nspt else [])

    return ReportSpec(date_of=lambda r: to_local_date(r.date_str), metrics=metrics, derived=derived,
                      dimensions=dimensions, breakdowns=dimensions, rank_by="order_value")


def compute_procurement_summary(db: Session, user, period: Period, company_id, group_by: str | None,
                                show_ncc: bool) -> dict:
    """Hợp đồng chuẩn `build_report` cho `/api/reports/procurement/summary` (+ `/export`).

    `group_by` ép về NCC/NSPT khi không có `purchase_order.read` -> 403 ngay (bao-CR-437 —
    `/api/reports/procurement` cũ KHÔNG chặn NCC ở backend, route mới này vá lỗ đó).

    M4 (review 28/09/2026): áp CÙNG phạm vi phòng ban với bảng nguồn `/api/reports/matrix`
    (`report_dept_scope`) — phòng ban YÊU CẦU chỉ thấy chi phí/giá trị đặt của phòng mình,
    không còn thấy TOÀN CÔNG TY như trước (route mới không được LỎNG hơn bảng nó tách ra từ).
    """
    if group_by in _NCC_DIMENSIONS and not show_ncc:
        raise HTTPException(403, "Không có quyền xem báo cáo theo Nhà cung cấp / NSPT")
    cid = rows.valid_company_id(company_id)   # L3: chuỗi không phải số nguyên -> 422, không 500
    spec = _build_spec(db, show_ncc)
    dept_name = {d.id: d.name for d in db.query(Department).all()}
    allow = report_service.report_dept_scope(db, user)   # None = xem hết; set() = chỉ phòng allow

    #  P05 (review hiệu năng 28/09/2026): `build_report` gọi `fetch()` tối đa 2 lần (kỳ này +
    #  kỳ so sánh) — gộp cả hai khoảng ngày vào MỘT lượt truy vấn ĐMH/Payable (`grouped_po_rows`/
    #  `payable_rows` nhận LIST khoảng), rồi `fetch()` chỉ CHIA LẠI tập đã có sẵn trong Python
    #  bằng `row_in_range`, khỏi hỏi DB lại lần hai với khoảng ngày khác.
    #  P06: `grouped_po_rows` (thay `rows.po_rows`) gom số LẦN GIAO ở SQL GROUP BY — xem
    #  docstring `procurement_grouped_rows.py` vì sao `order_value`/`po_count` vẫn ở mức dòng.
    ranges = [(period.date_from, period.date_to)]
    if period.compare != "none" and period.compare_from and period.compare_to:
        ranges.append((period.compare_from, period.compare_to))
    combined_all = grouped_po_rows(db, cid, ranges) + rows.payable_rows(db, cid, ranges, dept_name)
    if allow is not None:
        combined_all = [r for r in combined_all if r.department in allow]

    def fetch(d_from, d_to):
        return [r for r in combined_all if rows.row_in_range(r.date_str, d_from, d_to)]

    #  bao-CR-533: công nợ còn lại / quá hạn tính trên TOÀN công ty (`debt_snapshot` không biết
    #  phòng ban) — người chỉ có phạm vi phòng (`allow` là tập) từng thấy tổng nợ cả công ty trong
    #  khi mọi dòng chi phí khác đã khoanh đúng phòng mình. Chưa có luật chia nợ theo phòng, nên
    #  với họ bỏ hẳn hai chỉ số đó (vắng khóa = «—», như nhóm ở M1) thay vì đưa một con số sai phạm vi.
    data = build_report(fetch, spec, period, group_by=group_by,
                        snapshot=rows.debt_snapshot(db, cid) if allow is None else None)
    data["notes"] = data.get("notes", []) + [
        "Chi phí mua hàng lấy Phòng XỬ LÝ của ĐMH liên quan (không có ĐMH thì gộp vào "
        "'(Chưa gắn)'); nhóm hàng/NSPT của chi phí cũng suy từ ĐMH đó — ĐMH có nhiều nhóm hàng "
        "thì chia chi phí theo tỷ trọng giá trị đặt của từng nhóm.",
        "Công nợ còn lại/quá hạn tính theo số dư HIỆN TẠI của các khoản phát sinh trước mốc kỳ "
        "— hệ thống không lưu lịch sử số dư nên với kỳ trong quá khứ đây là số GẦN ĐÚNG.",
    ]
    return data
