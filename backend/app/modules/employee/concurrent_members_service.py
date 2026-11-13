"""NGƯỜI KIÊM NHIỆM Ở MỘT PHÒNG / MỘT CÔNG TY — dữ liệu chung cho bảng "Kiêm nhiệm" của trang phòng ban, trang công
ty và sơ đồ tổ chức (duoc-CR-755 giai đoạn 05; hai loại dòng ở duoc-CR-756).

Ai thấy dòng nào = phạm vi `employee.read` của người XEM áp lên "chỗ ngồi" của dòng
(`scoping.concurrent_row_visible_condition`): dòng loại Phòng ban ngồi ở (phòng dòng, công ty chính), dòng loại Công
ty B ngồi ở (mỗi phòng của người đó, B). Không có khóa quyền mới, và KHÔNG đổi phạm vi đọc hồ sơ: đây chỉ là dòng
tóm tắt, mở hồ sơ đầy đủ là việc của `include_concurrent` (Q1) ở các đường đọc hồ sơ.

Danh sách trắng trường (chống lộ liên lạc của người công ty khác): mã, họ tên, loại, chức vụ kiêm nhiệm, ngày,
công ty + phòng kiêm nhiệm, công ty + phòng CHÍNH (chỉ tên), công tắc, cờ `can_open`. KHÔNG điện thoại,
email, ngày sinh. Số truy vấn cố định (một truy vấn chính, một truy vấn `can_open`, hai truy vấn tên).
"""
from datetime import date

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.hr_concurrent_codes import (CONCURRENT_KIND_LABELS, CONCURRENT_STATUS_LABELS, ConcurrentKind,
                                          get_concurrent_status)
from app.core.scoping import apply_scope, concurrent_row_visible_condition
from app.core.vn_time import vn_today

from .concurrent_model import EmployeeConcurrent
from .concurrent_serializer import _names_map
from .concurrent_service import effective_filter
from .model import Employee

#  Trần dòng một lượt (bảng phòng ban nạp đủ, không phân trang). Phòng có hơn 200 người kiêm nhiệm cùng lúc
#  là chuyện không có thật; trần để một phòng dùng chung không kéo cả bảng về trình duyệt.
MAX_ROWS = 200
#  Sơ đồ tổ chức vẽ MỌI phòng người xem thấy nên trần cao hơn (vẫn là một truy vấn).
ORG_CHART_MAX_ROWS = 1000

#  Mã trạng thái nghỉ việc (`core/status_codes.EMPLOYEE_STATUS`).
_RESIGNED = "resigned"


def list_visible_members(db: Session, user, profile: dict, *, department_id: int | None = None,
                         company_id: int | None = None, kind: int | None = None, include_ended: bool = False,
                         effective_only: bool = False, limit: int = MAX_ROWS,
                         today: date | None = None) -> list[dict]:
    """Dòng kiêm nhiệm của nhân sự ĐANG LÀM mà người xem có phạm vi phủ "chỗ ngồi" của dòng.

    - lọc: `department_id` (dòng loại Phòng ban của phòng đó), `company_id` (dòng ở công ty đó — loại Phòng ban của
      người làm chính ở đó lẫn loại Công ty B), `kind` (1 | 2); không truyền thì không lọc chiều đó;
    - mặc định: dòng đang hiệu lực + sắp tới; `include_ended` thêm dòng đã hết; `effective_only` chỉ dòng
      đang hiệu lực (sơ đồ tổ chức);
    - dòng loại Phòng ban TRÙNG cặp (phòng chính, công ty chính) của chính người đó thì bỏ — không vẽ / đếm hai lần
      (loại Công ty không bao giờ trùng);
    - xếp theo họ tên rồi id dòng; cắt ở `limit`.
    """
    today = today or vn_today()
    C = EmployeeConcurrent
    q = (db.query(C, Employee.code, Employee.full_name, Employee.company_id, Employee.department_id)
         .join(Employee, Employee.id == C.employee_id)
         .filter(Employee.is_active.is_(True), Employee.status != _RESIGNED,
                 or_(C.kind == ConcurrentKind.COMPANY,
                     ~and_(C.department_id == Employee.department_id, C.company_id == Employee.company_id))))
    if department_id is not None:
        q = q.filter(C.department_id == department_id)
    if company_id is not None:
        q = q.filter(C.company_id == company_id)
    if kind is not None:
        q = q.filter(C.kind == kind)
    if effective_only:
        q = q.filter(effective_filter(today))
    elif not include_ended:
        q = q.filter(or_(C.to_date.is_(None), C.to_date >= today))

    visible = concurrent_row_visible_condition(C, Employee.department_id, user, profile, "read")
    if visible is not None:   # None = người xem thấy tất cả
        q = q.filter(visible)

    rows = q.order_by(Employee.full_name, C.id).limit(max(1, int(limit))).all()
    return _serialize(db, user, profile, rows, today)


def _serialize(db: Session, user, profile: dict, rows: list, today: date) -> list[dict]:
    if not rows:
        return []
    from app.modules.company.model import Company
    from app.modules.department.model import Department

    employee_ids = {r[0].employee_id for r in rows}
    #  `can_open` = hồ sơ đọc được THEO PHẠM VI có nhánh Q1 (một truy vấn trên tập id): dòng bật công tắc
    #  thường mở được, dòng tắt công tắc (hoặc ngoài tầm) chỉ xem tên.
    openable = {i for (i,) in apply_scope(
        db.query(Employee.id).filter(Employee.id.in_(employee_ids)),
        Employee, "employee", user, profile, "read", include_concurrent=True).all()}

    company_names = _names_map(db, Company, {c.company_id for c, *_ in rows} | {r[3] for r in rows})
    dept_names = _names_map(db, Department, {c.department_id for c, *_ in rows} | {r[4] for r in rows})

    out: list[dict] = []
    for c, code, full_name, primary_company_id, primary_department_id in rows:
        status = get_concurrent_status(c.from_date, c.to_date, today)
        row_kind = ConcurrentKind(c.kind or ConcurrentKind.DEPARTMENT)
        out.append({
            "id": c.id,
            "employee_id": c.employee_id,
            "code": code or "",
            "full_name": full_name or "",
            "kind": int(row_kind),
            "kind_label": CONCURRENT_KIND_LABELS[row_kind],
            "position_label": c.position_label or "",
            "company_id": c.company_id,
            "company_name": company_names.get(c.company_id, ""),
            "department_id": c.department_id,
            "department_name": dept_names.get(c.department_id, ""),
            "from_date": c.from_date.isoformat() if c.from_date else None,
            "to_date": c.to_date.isoformat() if c.to_date else None,
            "status": int(status),
            "status_label": CONCURRENT_STATUS_LABELS[status],
            "counts_scope": bool(c.counts_scope),
            "primary_company_id": primary_company_id or 0,
            "primary_company_name": company_names.get(primary_company_id or 0, ""),
            "primary_department_id": primary_department_id or 0,
            "primary_department_name": dept_names.get(primary_department_id or 0, ""),
            "can_open": c.employee_id in openable,
        })
    return out


def describe_concurrent(kind: int, department_name: str, company_name: str, position_label: str) -> str:
    """Một dòng kiêm nhiệm thành câu: loại Phòng ban *Phòng X (Chức vụ)*, loại Công ty *Công ty B (Chức vụ)*
    (duoc-CR-756). Thiếu tên / chức vụ thì bỏ phần đó."""
    if int(kind or ConcurrentKind.DEPARTMENT) == ConcurrentKind.COMPANY:
        #  Tên pháp nhân thường đã mở đầu bằng "Công ty ..." — không thêm lần nữa.
        text = (company_name if company_name.lower().startswith("công ty") else f"Công ty {company_name}") \
            if company_name else "Công ty không rõ"
    else:
        text = department_name or "Phòng không rõ"
    if position_label:
        text += f" ({position_label})"
    return text


def effective_roles_of(db: Session, employee_ids: set[int] | list[int], today: date | None = None
                       ) -> dict[int, list[dict]]:
    """Dòng kiêm nhiệm ĐANG HIỆU LỰC của nhiều người (kể cả dòng tắt công tắc) — mỗi dòng đã có loại, tên phòng,
    tên công ty và câu mô tả. Hai truy vấn cố định (dòng + tên), không N+1.

    Dùng cho `/api/auth/me` (người xem là chính chủ) và trợ lý AI (người đã nằm trong kết quả được phép xem) —
    cả hai chỉ gọi với id mà bên gọi ĐÃ xác nhận được đọc, hàm này không xét phạm vi.
    """
    ids = {int(i) for i in employee_ids if i}
    if not ids:
        return {}
    from app.modules.company.model import Company
    from app.modules.department.model import Department

    C = EmployeeConcurrent
    rows = (db.query(C).filter(C.employee_id.in_(ids), effective_filter(today or vn_today()))
            .order_by(C.id).all())
    company_names = _names_map(db, Company, {r.company_id for r in rows})
    dept_names = _names_map(db, Department, {r.department_id for r in rows})

    out: dict[int, list[dict]] = {}
    for r in rows:
        dept_name = dept_names.get(r.department_id, "")
        company_name = company_names.get(r.company_id, "")
        row_kind = ConcurrentKind(r.kind or ConcurrentKind.DEPARTMENT)
        out.setdefault(r.employee_id, []).append({
            "kind": int(row_kind), "kind_label": CONCURRENT_KIND_LABELS[row_kind],
            "department_id": r.department_id, "company_id": r.company_id,
            "department_name": dept_name, "company_name": company_name,
            "position_label": r.position_label or "", "counts_scope": bool(r.counts_scope),
            "text": describe_concurrent(row_kind, dept_name, company_name, r.position_label or ""),
        })
    #  Phòng ban trước (theo tên phòng), rồi Công ty (theo tên công ty).
    for items in out.values():
        items.sort(key=lambda x: (x["kind"], x["department_name"], x["company_name"], x["department_id"]))
    return out
