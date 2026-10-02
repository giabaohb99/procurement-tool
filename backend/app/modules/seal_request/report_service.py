"""Bản THEO KỲ của Báo cáo Duyệt đóng dấu (phase 05, 5.2) — `GET /api/seal-requests/summary`.

Kỳ tính theo `created_at` (DateTime UTC → giờ VN, Q5.2 ngược với Đặt xe dùng ngày đi).
Một phiếu gắn NHIỀU công ty qua bảng nối `tab_seal_request_company` → chiều "công ty"
trả NHIỀU cặp `(id, tên)` cho một hàng (khung P01 cộng Tổng ĐỘC LẬP với `groups`, xem
`report_aggregate.aggregate` — một phiếu 2 công ty thì mỗi công ty +1, Tổng vẫn +1).

Review hiệu năng (01/10/2026, áp cho mọi `/summary` quy mô 20-100 người dùng):
- `FETCH_COLUMNS` dùng với `Query.with_entities(...)` ở `report_controller.py` — chỉ kéo
  đúng cột cần, KHÔNG nạp object ORM đầy đủ. Mọi lọc (kỳ, `is_deleted`, bỏ `SEAL_DRAFT`,
  `apply_scope`) đã nằm trong SQL WHERE từ trước.
- `decorate()` CHỈ tra nhãn loại dấu/phòng ban/văn thư/công ty khi `group_by` ĐANG DÙNG
  đúng chiều đó — nhánh `group_by=none` (Tổng quan) không tốn một truy vấn nhãn nào. Bảng
  nối công ty (`get_company_ids_map`, đã chống N+1 — `test_duyet_dau_gom_cong_ty.py`) chỉ
  hỏi khi `group_by=company`.
- `turnaround_hours` (giờ duyệt per-phiếu, KHÔNG gom được qua GROUP BY) tự chia lô 900
  id/lượt; "duyệt → đóng dấu" tính thẳng từ 2 cột `approved_at`/`completed_at` đã có sẵn
  trên hàng, không cần truy vấn thêm.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec
from app.core.report_period import to_local_date
from app.modules.approval.report_turnaround import turnaround_hours
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.user.model import User

from .model import SEAL_COMPLETED, SEAL_REJECTED, SEAL_STATUS_LABELS, SealRequest, SealType
from .service import get_company_ids_map

#  Đúng các cột `decorate()` cần — truyền cho `Query.with_entities(*FETCH_COLUMNS)`.
FETCH_COLUMNS = (
    SealRequest.id, SealRequest.created_at, SealRequest.status, SealRequest.copies,
    SealRequest.seal_type_id, SealRequest.department_id, SealRequest.requester_id,
    SealRequest.requester, SealRequest.completed_by, SealRequest.approved_at,
    SealRequest.completed_at,
)


def _parse_iso(value: str):
    """Chuỗi ISO (`datetime.isoformat(timespec='minutes')`) -> `datetime`, rác -> `None`."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _id_name_map(db: Session, id_col, name_col, ids: set[int]) -> dict[int, str]:
    ids = {i for i in ids if i}
    if not ids:
        return {}
    return dict(db.query(id_col, name_col).filter(id_col.in_(ids)).all())


def _clerk_names(db: Session, user_ids: set[int]) -> dict[int, str]:
    """`{user_id: tên nhân sự}` — hai truy vấn theo LÔ (User rồi Employee), cố định bất kể
    số dòng."""
    ids = {i for i in user_ids if i}
    if not ids:
        return {}
    users = dict(db.query(User.id, User.employee_id).filter(User.id.in_(ids)).all())
    emp_ids = {eid for eid in users.values() if eid}
    emps = _id_name_map(db, Employee.id, Employee.full_name, emp_ids)
    return {uid: emps.get(eid, "") for uid, eid in users.items()}


def decorate(db: Session, rows: list, group_by: str | None = None) -> list[dict]:
    """Ghép nhãn loại dấu/phòng ban/văn thư/công ty + giờ duyệt cho MỘT LÔ phiếu.

    `rows` là `Row` của `with_entities(*FETCH_COLUMNS)` — KHÔNG phải object ORM. Chỉ tra
    nhãn của ĐÚNG chiều `group_by` đang dùng (xem docstring đầu tệp)."""
    ids = [r.id for r in rows]
    company_map: dict[int, list[int]] = {}
    companies: dict[int, str] = {}
    if group_by == "company":
        company_map = get_company_ids_map(db, ids)
        all_cids = {cid for cids in company_map.values() for cid in cids}
        companies = _id_name_map(db, Company.id, Company.name, all_cids)
    depts = (_id_name_map(db, Department.id, Department.name, {r.department_id for r in rows})
            if group_by == "department" else {})
    #  "Loại dấu" là BREAKDOWN (luôn chạy bất kể `group_by`, xem `build_spec`) — khác
    #  company/department/clerk chỉ là DIMENSION (chỉ chạy khi được chọn Xem theo), nên
    #  KHÔNG được gate theo `group_by`. Bảng `tab_seal_type` nhỏ (master data), tra theo
    #  lô vẫn rẻ bất kể số dòng.
    types = _id_name_map(db, SealType.id, SealType.name, {r.seal_type_id for r in rows})
    clerks = (_clerk_names(db, {r.completed_by for r in rows}) if group_by == "clerk" else {})
    hours = turnaround_hours(db, "seal_request", ids)

    out = []
    for r in rows:
        approved, completed = _parse_iso(r.approved_at), _parse_iso(r.completed_at)
        ac_hours = ((completed - approved).total_seconds() / 3600
                    if approved and completed and completed >= approved else None)
        cids = company_map.get(r.id, [])
        out.append({
            "created_at": r.created_at, "status": r.status, "copies": r.copies or 0,
            "seal_type_id": r.seal_type_id, "seal_type_name": types.get(r.seal_type_id, ""),
            "department_id": r.department_id, "department_name": depts.get(r.department_id, ""),
            "requester_id": r.requester_id, "requester": r.requester or "",
            "completed_by": r.completed_by, "clerk_name": clerks.get(r.completed_by, ""),
            "company_ids": cids, "company_names": [companies.get(c, "") for c in cids],
            "approve_complete_hours": ac_hours,
            "approval_hours": hours.get(r.id),
        })
    return out


def build_spec() -> ReportSpec:
    metrics = [
        MetricSpec("requests", "Đề nghị", kind="int", value_of=lambda r: 1),
        MetricSpec("copies", "Số bản", kind="int", value_of=lambda r: r["copies"]),
        MetricSpec("completed", "Đã đóng dấu", kind="int",
                  value_of=lambda r: 1 if r["status"] == SEAL_COMPLETED else 0),
        #  Chỉ số PHỤ — tử số của `reject_rate`, không đứng riêng.
        MetricSpec("rejected", "Từ chối", kind="int", helper=True,
                  value_of=lambda r: 1 if r["status"] == SEAL_REJECTED else 0),
        MetricSpec("approval_hours_sum", "Tổng giờ duyệt", kind="hours", helper=True,
                  value_of=lambda r: r["approval_hours"] if r["approval_hours"] is not None else 0),
        MetricSpec("approval_hours_count", "Số phiếu có giờ duyệt", kind="int", helper=True,
                  value_of=lambda r: 1 if r["approval_hours"] is not None else 0),
        MetricSpec("ac_hours_sum", "Tổng giờ duyệt→đóng dấu", kind="hours", helper=True,
                  value_of=lambda r: r["approve_complete_hours"] or 0
                  if r["approve_complete_hours"] is not None else 0),
        MetricSpec("ac_hours_count", "Số phiếu có giờ duyệt→đóng dấu", kind="int", helper=True,
                  value_of=lambda r: 1 if r["approve_complete_hours"] is not None else 0),
    ]
    derived = [
        DerivedSpec("reject_rate", "Tỷ lệ từ chối", num="rejected", den="requests",
                   kind="percent", good="down"),
        #  `scale=1`: TRUNG BÌNH giờ, không phải tỷ lệ %.
        DerivedSpec("avg_approval_hours", "Thời gian duyệt TB", num="approval_hours_sum",
                   den="approval_hours_count", kind="hours", good="down", scale=1),
        DerivedSpec("avg_approve_complete_hours", "Thời gian duyệt → đóng dấu TB",
                   num="ac_hours_sum", den="ac_hours_count", kind="hours", good="down", scale=1),
    ]
    dimensions = {
        "seal_type": DimensionSpec("seal_type", "Loại dấu", key_of=lambda r: (
            [(r["seal_type_id"], r["seal_type_name"])] if r["seal_type_id"] else [])),
        #  Nhiều giá trị: một phiếu gắn nhiều công ty — Tổng vẫn tính độc lập (P01).
        "company": DimensionSpec("company", "Công ty", key_of=lambda r: (
            list(zip(r["company_ids"], r["company_names"])))),
        "department": DimensionSpec("department", "Phòng ban", key_of=lambda r: (
            [(r["department_id"], r["department_name"])] if r["department_id"] else [])),
        "requester": DimensionSpec("requester", "Người đề nghị", key_of=lambda r: (
            [(r["requester_id"], r["requester"])] if r["requester_id"] else [])),
        "clerk": DimensionSpec("clerk", "Văn thư", key_of=lambda r: (
            [(r["completed_by"], r["clerk_name"])] if r["completed_by"] else [])),
        "status": DimensionSpec("status", "Trạng thái", key_of=lambda r: (
            [(r["status"], SEAL_STATUS_LABELS.get(r["status"], ""))])),
    }
    breakdowns = {"status": dimensions["status"], "seal_type": dimensions["seal_type"]}
    return ReportSpec(date_of=lambda r: to_local_date(r["created_at"]), metrics=metrics,
                      derived=derived, dimensions=dimensions, breakdowns=breakdowns)
