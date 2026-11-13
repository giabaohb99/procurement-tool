"""Tool PHÉP CỦA NHÂN SỰ KHÁC cho Nhân sự / quản lý — `employee_leave_summary` (duoc-CR-757).

Trả lời "anh Nam còn mấy ngày phép", "phòng Kế toán năm nay ai nghỉ bao nhiêu ngày", "chị Hà theo lịch làm việc nào".
Chỉ đọc. Người hỏi về CHÍNH mình vẫn dùng được (nếu có khóa), nhưng `my_leave_summary` đầy đủ hơn.

Gác đúng như màn **Quỹ phép** (`/hr/leave-balances`), không mở rộng:

1. Khóa `leave_balance.read` — thiếu thì `denied`.
2. Người được trả về = phạm vi XEM `employee` (`apply_scope`) GIAO phạm vi `leave_balance` áp lên chính hồ sơ đó
   (`_balance_seat`: cột `company_id` / `employee_id` của quỹ phép ứng với `Employee.company_id` / `Employee.id`,
   cùng kiểu chỗ ngồi giả lập `scoping._employee_seat`). Dòng quỹ còn đi qua `apply_scope(LeaveBalance, ...)` một lần
   nữa. Ngoài phạm vi và không tồn tại trả CÙNG một câu.
3. Danh sách trường TRẮNG: mã, họ tên, phòng, lịch làm việc, số ngày. Không lương, không dữ liệu nhạy cảm.
4. **Ngày đã nghỉ đọc từ ĐƠN NGHỈ nên đi theo phạm vi `leave_request`**, không theo phạm vi quỹ phép / hồ sơ
   (duoc-CR-757 C1): số ngày nghỉ ốm, không lương, thai sản gần dữ liệu sức khỏe, trước nay chỉ thấy ở màn Đơn nghỉ
   phép. Thiếu `leave_request.read` → `taken_by_type` rỗng; có thì lọc bằng `scope_condition(LeaveRequest, ...)`
   ngay trong câu GROUP BY (không thêm truy vấn).

Số còn lại chỉ qua `balance_service.available_days_map` (không `ensure_balance`, không tự cộng trừ cột). Ngày đã nghỉ
và tên lịch dùng chung `leave_taken_schedule` với `my_leave_summary`. Số truy vấn CỐ ĐỊNH bất kể bao nhiêu người.
"""
import re

from app.core.scoping import apply_scope, scope_condition
from app.core.text_fold import fold
from app.core.vn_time import vn_today
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.leave import balance_service
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.request_model import LeaveRequest
from app.modules.work_schedule.resolver_many import load_day_plans_many

from .base import ToolContext, ToolSpec, denied
from .leave_taken_schedule import (SCHEDULE_GLOSSARY, TAKEN_GLOSSARY, TAKEN_SCOPE_NOTE, build_empty_taken,
                                   build_schedule_label, taken_by_type_many)
from .leave_tool import _type_names

MAX_ROWS = 50
NOT_FOUND = "Không tìm thấy nhân sự nào khớp trong phạm vi bạn được xem."
#  Người dùng / model hay gõ kèm chữ loại đơn vị ("phòng Kế toán") trong khi tên phòng trong danh mục thường không có.
_DEPT_PREFIX = re.compile(r"^(?:(?:phong ban|phong|ban|bo phan)\s+|p\.\s*)")

_PARAMS = {
    "type": "object",
    "properties": {
        "employee": {"type": "string", "description": "Mã nhân viên hoặc một phần họ tên (không cần dấu)."},
        "department": {"type": "string", "description": "ID hoặc một phần tên phòng ban — liệt kê nhân sự ĐANG LÀM "
                                                         "của phòng đó."},
        "year": {"type": "integer", "description": "Năm quỹ phép (ví dụ 2026). Bỏ trống = năm hiện tại."},
        "limit": {"type": "integer", "description": f"Số người tối đa (mặc định 20, trần {MAX_ROWS})."},
    },
}

_DESC = (
    "Tra QUỸ PHÉP và SỐ NGÀY ĐÃ NGHỈ của NHÂN SỰ KHÁC — dành cho Nhân sự / quản lý có quyền xem Quỹ phép. Gọi khi hỏi "
    "'anh X còn mấy ngày phép', 'phòng Y năm nay ai nghỉ bao nhiêu', 'chị Z đang theo lịch làm việc nào'. Phải có "
    "`employee` (mã NV hoặc tên) hoặc `department` (tên / ID phòng). Mỗi người trả: `balances` từng loại trừ quỹ "
    "(remaining_days là số còn nghỉ được — đừng tự cộng trừ), `taken_by_type` ngày nghỉ mọi loại kể cả không lương "
    "(approved_days = đã / đang nghỉ, approved_upcoming_days = đã duyệt nhưng chưa tới ngày), `taken_total_days` = số "
    "ngày ĐÃ nghỉ, và `work_schedule` lịch đang áp hôm nay. Ngày đã nghỉ theo phạm vi xem đơn nghỉ phép của người hỏi "
    "nên có thể rỗng dù quỹ vẫn có. Kết quả đã lọc theo phạm vi của người hỏi: rỗng nghĩa "
    "là không có trong phạm vi họ được xem, nói đúng như vậy, đừng khẳng định người đó không tồn tại. Hỏi phép của "
    "CHÍNH mình thì dùng my_leave_summary. Không có lương hay thông tin cá nhân."
)


def _clamp(value, default: int, hi: int = MAX_ROWS) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(n, hi))


def _year(value) -> int:
    try:
        year = int(value)
    except (TypeError, ValueError):
        return vn_today().year
    return year if 2000 <= year <= 2100 else vn_today().year


def _balance_seat():
    """Chỗ ngồi giả lập để áp phạm vi `leave_balance` (đọc `company_id` + `employee_id`) lên HỒ SƠ nhân sự."""
    return type("_BalanceSeat", (), {"company_id": Employee.company_id, "employee_id": Employee.id})


def _match_departments(db, raw: str) -> list[int]:
    """ID phòng theo số hoặc theo một phần tên (bỏ dấu, so trong bộ nhớ — bảng phòng nhỏ)."""
    raw = raw.strip()
    if raw.isdigit():
        return [int(raw)] if int(raw) > 0 else []   # "0" sẽ trúng người chưa gắn phòng
    full = fold(raw).strip()
    bare = _DEPT_PREFIX.sub("", full).strip() or full
    return [r.id for r in db.query(Department.id, Department.name).all()
            if bare and (bare in fold(r.name or "") or full in fold(r.name or ""))]


def _visible_employees(ctx: ToolContext, keyword: str, dept_ids: list[int] | None) -> list:
    """Nhân sự trong phạm vi (employee ∩ leave_balance), lọc phòng ở SQL, từ khóa ở Python (tiếng Việt có dấu)."""
    q = ctx.db.query(Employee.id, Employee.code, Employee.full_name, Employee.department_id, Employee.company_id,
                     Employee.is_active)
    q = apply_scope(q, Employee, "employee", ctx.user, ctx.profile)
    cond = scope_condition(_balance_seat(), "leave_balance", ctx.user, ctx.profile)
    if cond is not None:
        q = q.filter(cond)
    if dept_ids is not None:
        if not dept_ids:   # tên phòng không khớp phòng nào → rỗng (`IN [0]` sẽ trúng người chưa gắn phòng)
            return []
        q = q.filter(Employee.department_id.in_(dept_ids), Employee.is_active.is_(True))
    rows = q.order_by(Employee.full_name, Employee.id).all()
    if not keyword:
        return rows
    exact = [r for r in rows if (r.code or "").lower() == keyword.lower()]
    if exact:
        return exact
    needle = fold(keyword)
    return [r for r in rows if needle in fold(r.full_name or "") or needle in fold(r.code or "")]


def _balances_by_employee(ctx: ToolContext, ids: list[int], year: int, types: dict) -> dict[int, list]:
    rows = ctx.db.query(LeaveBalance).filter(LeaveBalance.employee_id.in_(ids), LeaveBalance.year == year)
    rows = apply_scope(rows, LeaveBalance, "leave_balance", ctx.user, ctx.profile).all()
    available = balance_service.available_days_map(ctx.db, rows)   # một lượt cho cả danh sách
    out: dict[int, list] = {}
    for r in rows:
        info = types.get(r.leave_type_id) or {}
        out.setdefault(r.employee_id, []).append({
            "leave_type": info.get("name", ""), "leave_type_code": info.get("code", ""),
            "allocated_days": r.allocated_days, "total_days": r.total_days, "used_days": r.used_days,
            "pending_days": r.pending_days, "remaining_days": available[r.id]})
    for items in out.values():
        items.sort(key=lambda x: x["leave_type"])
    return out


def _run(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("leave_balance"):
        return denied("quỹ phép của nhân sự (leave_balance.read)")
    keyword = str(args.get("employee") or "").strip()[:100]
    dept_raw = str(args.get("department") or "").strip()[:100]
    if not keyword and not dept_raw:
        return {"error": "Cần cho biết nhân sự (mã hoặc tên) hoặc phòng ban cần tra."}
    year, limit = _year(args.get("year")), _clamp(args.get("limit"), 20)

    dept_ids = _match_departments(ctx.db, dept_raw) if dept_raw else None
    matched = _visible_employees(ctx, keyword, dept_ids)
    if not matched:
        return {"year": year, "employees": [], "total": 0, "has_more": False, "note": NOT_FOUND}
    page = matched[:limit]
    ids = [r.id for r in page]

    types = _type_names(ctx.db)
    names = {d.id: d.name for d in ctx.db.query(Department.id, Department.name)
             .filter(Department.id.in_({r.department_id for r in page} or {0})).all()}
    balances = _balances_by_employee(ctx, ids, year, types)
    today = vn_today()
    if ctx.can("leave_request"):
        cond = scope_condition(LeaveRequest, "leave_request", ctx.user, ctx.profile)
        taken = taken_by_type_many(ctx.db, ids, year, types, scope_cond=cond, today=today)
    else:
        taken = build_empty_taken(ids)
    plans = load_day_plans_many(ctx.db, page, today, today)

    employees = [{
        "code": r.code, "full_name": r.full_name, "department_name": names.get(r.department_id, ""),
        "is_active": bool(r.is_active),
        "work_schedule": build_schedule_label(plans, r.id, today),
        "balances": balances.get(r.id, []),
        **taken[r.id],
    } for r in page]
    has_more = len(matched) > len(page)
    note = (f"Còn {len(matched) - len(page)} người nữa — thu hẹp bằng tên / phòng hoặc tăng limit."
            if has_more else "")
    return {"year": year, "employees": employees, "total": len(matched), "has_more": has_more, "note": note,
            "url": "/hr/leave-balances",
            "glossary": {
                "balances": "Quỹ từng loại TRỪ quỹ: remaining_days = số còn nghỉ được (đã trừ ngày đang giữ chỗ "
                            "pending_days và phần chưa tới tháng của loại cộng dần). Rỗng = Nhân sự chưa cấp quỹ năm "
                            "này, hoặc dòng quỹ nằm ngoài phạm vi bạn xem (vd quỹ cấp khi người đó còn ở pháp nhân cũ).",
                "taken_by_type": TAKEN_GLOSSARY + TAKEN_SCOPE_NOTE,
                "work_schedule": SCHEDULE_GLOSSARY}}


EMPLOYEE_LEAVE_SUMMARY_SPEC = ToolSpec(
    name="employee_leave_summary",
    description=_DESC,
    parameters=_PARAMS,
    handler=_run,
)
