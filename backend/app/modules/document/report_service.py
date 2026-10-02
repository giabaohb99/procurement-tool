"""Báo cáo Văn bản (phase 05, mục 5.3) — khung `report_aggregate.build_report`.

Nguồn/phạm vi Y HỆT danh sách văn bản: `documents_query` (chỉ `origin=1`) lọc thêm
`access_service.visible_condition(user, profile, 'read')` — văn bản bị chặn (deny
đích danh / văn bản cá nhân không liên quan) không vào BẤT KỲ số nào của báo cáo
này (quyết định Q5.3). `visible_condition` trả `None` nghĩa "không lọc gì thêm"
(vai trò phạm vi *tất cả*) — PHẢI guard `is not None` trước khi `.filter()`, nếu
không `.filter(None)` lọc ra 0 dòng cho chính người được thấy hết (review M5).
Văn bản NHÁP (`STATUS_DRAFT`) bị loại khỏi TOÀN BỘ báo cáo (review mục 6, thống
nhất với Đặt xe/Đóng dấu bỏ DRAFT) — áp ở `_base_query` nên mọi chỉ số/nhóm đều
nhất quán, không riêng "Tạo mới".

Kỳ theo `created_at` (ngày lập, Q5.2). Bốn chỉ số KHÔNG tính được từ tập hàng đã
lọc theo `created_at` — "Đã ban hành" (theo `issued_at`), "Chờ duyệt"/"Cần rà
soát" (trạng thái HIỆN TẠI, hệ thống không lưu lịch sử) và "Hết hạn trong kỳ"
(theo `expire_date`) — đi qua `snapshot()` của `build_report`, dùng LẠI đúng
`_base_query` (cùng điều kiện nhìn thấy + cùng lọc công ty), không nới quyền ở
đâu cả. Bốn truy vấn này là `.count()` thuần SQL, không vòng lặp Python.

Hiệu năng: `fetch_rows` CỐ Ý giữ MỨC DÒNG (một văn bản một hàng), KHÔNG gộp
thêm bằng SQL `GROUP BY` kiểu `survey/report_grouped_fetch.py` — "Thời gian
duyệt TB" cần đúng số giờ của TỪNG văn bản (`turnaround_hours`, không cộng dồn
được qua `GROUP BY` vì phụ thuộc phiên duyệt MỚI NHẤT của riêng nó), nên mọi
hàng đã phải mang đủ thông tin đó; gộp trước rồi tính giờ sau là hai lượt dữ
liệu, không rẻ hơn. Bù lại: CHỈ nạp cột cần (`with_entities`, không nạp
`Document` ORM đầy đủ) và mọi nhãn (loại/công ty/phòng/người soạn/độ khẩn) tra
THEO LÔ — số truy vấn CỐ ĐỊNH (không tăng theo số văn bản).

Chiều "loại/công ty/phòng/người soạn" khóa THEO ID, tên chỉ làm NHÃN (review
M4) — hai phòng cùng tên "Phòng Kế toán" ở hai công ty khác nhau, hoặc hai
người soạn trùng tên, trước đây gộp lầm vào MỘT nhóm vì khóa bằng chuỗi tên.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.report_aggregate import (DerivedSpec, DimensionSpec, MetricSpec, ReportSpec,
                                       build_report)
from app.core.report_period import MIN_REPORT_YEAR, Period, range_filter, to_local_date
from app.modules.approval.report_turnaround import turnaround_hours
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.doc_catalog.model import DocType
from app.modules.doc_catalog.security_level_service import label_maps
from app.modules.employee.model import Employee
from app.modules.report.procurement_summary_rows import valid_company_id

from .access_service import visible_condition
from .model import STATUS_DRAFT, STATUS_LABELS, STATUS_SUBMITTED, Document
from .query import documents_query

ENTITY = "document"
#  Cận dưới cho truy vấn "tính tới mốc X" (snapshot) — khớp `MIN_REPORT_YEAR` của
#  `report_period` để không quét lố xuống những năm dữ liệu không hợp lệ.
_FLOOR = date(MIN_REPORT_YEAR, 1, 1)

NOTE = ("'Chờ duyệt'/'Cần rà soát' tính theo trạng thái HIỆN TẠI của văn bản LẬP TRƯỚC mốc "
       "cuối kỳ — hệ thống không lưu lịch sử trạng thái, nên ở kỳ so sánh đây là số GẦN ĐÚNG. "
       "Văn bản Nháp không tính vào báo cáo này.")


def _base_query(db: Session, user, profile, company_id: int | None = None):
    """Nguồn DUY NHẤT của mọi truy vấn báo cáo — bỏ Nháp, lọc quyền, lọc công ty (nếu có)."""
    q = documents_query(db).filter(Document.status != STATUS_DRAFT)
    visible = visible_condition(user, profile, "read")
    if visible is not None:   # None = vai trò phạm vi *tất cả*, KHÔNG được lọc thành 0 dòng (M5)
        q = q.filter(visible)
    if company_id:
        q = q.filter(Document.company_id == company_id)
    return q


def fetch_rows(db: Session, user, profile, company_id: int | None, d_from: date, d_to: date) -> list[dict]:
    """Văn bản LẬP trong kỳ — nguồn của Tổng/xu hướng/Xem theo. Nhãn loại/công ty/
    phòng/người soạn/độ khẩn tra theo LÔ, không hỏi lại DB cho từng dòng."""
    q = _base_query(db, user, profile, company_id)
    q = q.filter(range_filter(Document.created_at, "datetime_utc", d_from, d_to))
    cols = q.with_entities(Document.id, Document.created_at, Document.status, Document.doc_type_id,
                           Document.company_id, Document.department_id,
                           Document.drafter_employee_id, Document.urgency).all()
    if not cols:
        return []

    #  Gói A4 (01/10/2026): subquery ID cùng `q` đã lọc (kỳ+quyền+công ty) thay vì list Python —
    #  đúng MỘT truy vấn `IN (SELECT ...)`, không chia lô 900 (3 năm có thể vượt xa 900 dòng).
    hours = turnaround_hours(db, ENTITY, q.with_entities(Document.id).scalar_subquery())
    type_ids = {r.doc_type_id for r in cols if r.doc_type_id}
    doc_types = ({t_id: (name, group) for t_id, name, group in
                 db.query(DocType.id, DocType.name, DocType.group_code)
                 .filter(DocType.id.in_(type_ids)).all()} if type_ids else {})
    company_ids = {r.company_id for r in cols if r.company_id}
    companies = ({c_id: name for c_id, name in db.query(Company.id, Company.name)
                 .filter(Company.id.in_(company_ids)).all()} if company_ids else {})
    dept_ids = {r.department_id for r in cols if r.department_id}
    departments = ({d_id: name for d_id, name in db.query(Department.id, Department.name)
                   .filter(Department.id.in_(dept_ids)).all()} if dept_ids else {})
    drafter_ids = {r.drafter_employee_id for r in cols if r.drafter_employee_id}
    drafters = ({e_id: name for e_id, name in db.query(Employee.id, Employee.full_name)
                .filter(Employee.id.in_(drafter_ids)).all()} if drafter_ids else {})
    _, urgency_labels = label_maps(db)

    rows = []
    for r in cols:
        type_name, group_code = doc_types.get(r.doc_type_id, (None, None))
        rows.append({
            "created_at": r.created_at,
            "status_label": STATUS_LABELS.get(r.status, str(r.status)),
            "doc_type_id": r.doc_type_id, "doc_type_name": type_name, "group_code": group_code,
            "company_id": r.company_id, "company_name": companies.get(r.company_id),
            "department_id": r.department_id, "department_name": departments.get(r.department_id),
            "drafter_id": r.drafter_employee_id, "drafter_name": drafters.get(r.drafter_employee_id),
            "urgency_label": urgency_labels.get(r.urgency) or str(r.urgency or ""),
            "turnaround_hours": hours.get(r.id),
        })
    return rows


def _id_dim(key: str, label: str, id_key: str, name_key: str) -> DimensionSpec:
    """Chiều khóa THEO ID, nhãn lấy tên đã tra — tránh gộp lầm hai tên trùng (M4)."""
    def key_of(r):
        rid = r.get(id_key)
        if not rid:
            return []
        return [(rid, r.get(name_key) or f"#{rid}")]
    return DimensionSpec(key, label, key_of=key_of)


def build_spec() -> ReportSpec:
    metrics = [
        MetricSpec("created", "Tạo mới", kind="int", value_of=lambda r: 1),
        #  Hai chỉ số PHỤ — chỉ để làm mẫu số/tử số của `avg_turnaround_hours`.
        MetricSpec("turnaround_sum", "Tổng giờ duyệt", kind="hours", helper=True,
                  value_of=lambda r: r["turnaround_hours"] if r.get("turnaround_hours") is not None else 0),
        MetricSpec("turnaround_count", "Số văn bản có thời gian duyệt", kind="int", helper=True,
                  value_of=lambda r: 1 if r.get("turnaround_hours") is not None else 0),
        #  Bốn chỉ số THỜI ĐIỂM (`snapshot=True`, M1) — `value_of` luôn 0 (bị `drop_snapshot`
        #  bỏ khỏi trend/groups), `snapshot()` của `build_report` GHI ĐÈ giá trị thật lên
        #  `totals` sau khi cộng dồn xong (xem `make_snapshot` bên dưới). Khai ở đây chỉ để
        #  `meta` có nhãn/loại cho FE và cho cột Excel.
        MetricSpec("issued", "Đã ban hành", kind="int", snapshot=True, value_of=lambda r: 0),
        MetricSpec("pending", "Chờ duyệt", kind="int", snapshot=True, value_of=lambda r: 0),
        MetricSpec("expiring", "Hết hạn trong kỳ", kind="int", snapshot=True, value_of=lambda r: 0),
        MetricSpec("needs_review", "Cần rà soát", kind="int", snapshot=True, value_of=lambda r: 0),
    ]
    derived = [DerivedSpec("avg_turnaround_hours", "Thời gian duyệt TB", num="turnaround_sum",
                          den="turnaround_count", kind="hours", good="down", scale=1)]
    #  `scale=1`: mặc định của DerivedSpec là ×100 cho tỷ lệ % — đây là TRUNG BÌNH giờ.
    dimensions = {
        "doc_type": _id_dim("doc_type", "Loại văn bản", "doc_type_id", "doc_type_name"),
        "group_code": DimensionSpec("group_code", "Nhóm loại", key_of=lambda r: (
            [(r["group_code"], f"Nhóm {r['group_code']}")] if r.get("group_code") else [])),
        "company": _id_dim("company", "Công ty ban hành", "company_id", "company_name"),
        "department": _id_dim("department", "Phòng chủ trì", "department_id", "department_name"),
        "drafter": _id_dim("drafter", "Người soạn", "drafter_id", "drafter_name"),
        "status": DimensionSpec("status", "Trạng thái", key_of=lambda r: (
            [(r["status_label"], r["status_label"])] if r.get("status_label") else [])),
        "urgency": DimensionSpec("urgency", "Mức khẩn", key_of=lambda r: (
            [(r["urgency_label"], r["urgency_label"])] if r.get("urgency_label") else [])),
    }
    return ReportSpec(date_of=lambda r: to_local_date(r.get("created_at")), metrics=metrics,
                      derived=derived, dimensions=dimensions, breakdowns=dimensions)


def make_snapshot(db: Session, user, profile, company_id: int | None, period: Period):
    """`snapshot(as_of)` của `build_report` — bốn chỉ số không đi theo tập hàng
    `created_at` của kỳ. `as_of` chỉ có thể là `period.date_to` (kỳ này) hoặc
    `period.compare_to` (kỳ so sánh, khi có) — suy ngược lại cặp (từ, đến) đúng
    của kỳ đó từ chính `period` đã đóng gói sẵn, để "Hết hạn trong kỳ" lọc được
    theo CẢ KHOẢNG chứ không chỉ một mốc."""

    def snap(as_of: date) -> dict:
        d_from, d_to = (period.date_from, period.date_to) if as_of == period.date_to \
            else (period.compare_from, period.compare_to)
        base = _base_query(db, user, profile, company_id)
        issued = base.filter(range_filter(Document.issued_at, "datetime_utc", d_from, d_to)).count()
        cutoff = base.filter(range_filter(Document.created_at, "datetime_utc", _FLOOR, as_of))
        pending = cutoff.filter(Document.status == STATUS_SUBMITTED).count()
        needs_review = cutoff.filter(Document.needs_review.is_(True)).count()
        expiring = base.filter(range_filter(Document.expire_date, "date", d_from, d_to)).count()
        return {"issued": issued, "pending": pending, "expiring": expiring,
               "needs_review": needs_review}

    return snap


def build_summary(db: Session, user, profile, period: Period, group_by: str | None,
                  company_id_raw=None) -> dict:
    """Hợp đồng chuẩn `build_report` cho `/api/documents/summary` (+ `/export`)."""
    company_id = valid_company_id(company_id_raw)

    def fetch(d_from, d_to):
        return fetch_rows(db, user, profile, company_id, d_from, d_to)

    data = build_report(fetch, build_spec(), period, group_by=group_by,
                        snapshot=make_snapshot(db, user, profile, company_id, period))
    data["notes"] = data.get("notes", []) + [NOTE]
    return data
