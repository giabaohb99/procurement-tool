"""Tải đang ôm của từng người, tính NGAY LÚC HỎI (duoc-CR-656, D1c). Không ghi gì, không phụ thuộc `tab_work_cycle`.

`current_load(...)` tốn ĐÚNG ≤ 10 truy vấn bất kể bao nhiêu người (xem `workload_sources`).

⚠️ KHÔNG TỰ GÁC QUYỀN. Người gọi (đường API quản trị, công cụ của trợ lý) phải kiểm quyền và truyền phạm vi đã duyệt.
Mặc định an toàn: không truyền `company_id`, `department_ids` lẫn `employee_ids` thì trả `[]` — muốn cả công ty phải
truyền `company_id` rõ ràng.

Cố ý KHÔNG quy ra một điểm tải có trọng số (Q11): trả các số thành phần + `open_items_total` (tổng đếm thô);
cân nặng nhẹ giữa duyệt, việc dự án, đơn mua là việc của AI/người đọc, kèm lời giải thích.
Ba chỗ đại diện cần nói rõ khi diễn giải:
  · duyệt Thu mua (YCMH/YCBG/ĐMH) không gán người duyệt → chỉ YCMH tính cho `head_of_dept_id` (`pr_approval_pending`);
  · việc ủy quyền: vẫn tính ở người ủy quyền (`approvals_pending`), người được ủy quyền thấy thêm `delegated_in` (KHÔNG cộng vào tổng);
  · `pr_handling` / `survey_lines_handling` đếm theo người phụ trách từng DÒNG hàng.
"""
from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.modules.capability import workload_sources as src

MAX_PEOPLE = 500          # trần một lượt hỏi — phạm vi lớn hơn thì chia theo phòng ban
MAX_HORIZON_DAYS = 60


def current_load(db: Session, *, company_id: int | None = None, department_ids: list[int] | None = None,
                 employee_ids: list[int] | None = None, now: datetime | None = None,
                 horizon_days: int = 14) -> list[dict]:
    if not (company_id or department_ids or employee_ids):
        return []
    now = now or datetime.utcnow()
    horizon = max(1, min(int(horizon_days or 14), MAX_HORIZON_DAYS))
    today = (now + timedelta(hours=7)).date()          # `now` là UTC naive; VN = UTC+7, không có giờ mùa hè

    people = src.employees_in_scope(db, company_id, department_ids, employee_ids)[:MAX_PEOPLE]
    if not people:
        return []
    ids = [p.id for p in people]
    codes = [p.code for p in people if p.code]

    deleg = src.delegations_today(db, ids, today)
    #  Người ủy quyền có thể nằm NGOÀI phạm vi → nạp cả việc duyệt của họ trong cùng một câu.
    approvals = src.approvals_by_assignee(db, sorted(set(ids) | {f for f, _t, _e in deleg}), now)
    work = src.work_by_pic(db, ids, today.isoformat())
    pr_lines = src.pr_handling_by_code(db, codes)
    pr_wait = src.pr_approval_pending(db, ids)
    po = src.po_handling(db, ids)
    sr_lines = src.survey_lines_handling(db, codes)
    docs = src.docs_pending_issue(db, ids)
    leaves = src.leaves_in_window(db, ids, today, today + timedelta(days=horizon))

    own = _sum_by_person(approvals)
    delegated_in, delegated_out = defaultdict(lambda: [0, 0]), defaultdict(set)
    scope = set(ids)
    for from_id, to_id, entity in deleg:
        pend, over = _delegator_load(approvals, from_id, entity)
        if to_id in scope:
            delegated_in[to_id][0] += pend
            delegated_in[to_id][1] += over
        if from_id in scope:
            delegated_out[from_id].add(to_id)
    leave_today, leave_days = _leave_numbers(leaves, today, horizon)

    out = []
    for p in people:
        pend, over = own.get(p.id, (0, 0))
        w_open, w_over, w_hours = work.get(p.id, (0, 0, 0.0))
        row = {
            "employee_id": p.id, "employee_code": p.code, "full_name": p.full_name,
            "company_id": int(p.company_id or 0), "department_id": int(p.department_id or 0),
            "approvals_pending": pend, "approvals_overdue": over,
            "delegated_in": delegated_in[p.id][0] if p.id in delegated_in else 0,
            "delegated_in_overdue": delegated_in[p.id][1] if p.id in delegated_in else 0,
            "delegated_out_to": sorted(delegated_out.get(p.id, ())),
            "work_open": w_open, "work_overdue": w_over, "work_estimate_hours_open": round(w_hours, 2),
            "pr_handling": pr_lines.get(p.code, 0), "pr_approval_pending": pr_wait.get(p.id, 0),
            "po_handling": po.get(p.id, 0), "survey_lines_handling": sr_lines.get(p.code, 0),
            "docs_pending_issue": docs.get(p.id, 0),
            "on_leave_today": p.id in leave_today, "leave_days_ahead": leave_days.get(p.id, 0),
        }
        row["open_items_total"] = (row["approvals_pending"] + row["work_open"] + row["pr_handling"]
                                   + row["pr_approval_pending"] + row["po_handling"]
                                   + row["survey_lines_handling"] + row["docs_pending_issue"])
        row["computed_at"] = now.isoformat()
        out.append(row)
    return out


def _sum_by_person(approvals: dict) -> dict[int, tuple[int, int]]:
    out: dict[int, list[int]] = defaultdict(lambda: [0, 0])
    for (emp, _entity), (n, over) in approvals.items():
        out[emp][0] += n
        out[emp][1] += over
    return {k: (v[0], v[1]) for k, v in out.items()}


def _delegator_load(approvals: dict, from_id: int, entity: str) -> tuple[int, int]:
    """Việc duyệt của người ủy quyền mà người nhận được bấm thay: mọi loại nếu `entity` rỗng, ngược lại đúng loại đó."""
    pend = over = 0
    for (emp, ent), (n, o) in approvals.items():
        if emp == from_id and (not entity or ent == entity):
            pend, over = pend + n, over + o
    return pend, over


def _leave_numbers(leaves: list, today: date, horizon: int) -> tuple[set[int], dict[int, int]]:
    end = today + timedelta(days=horizon)
    on_today: set[int] = set()
    days: dict[int, int] = defaultdict(int)
    for emp, start, stop in leaves:
        if start <= today <= stop:
            on_today.add(emp)
        days[emp] += (min(stop, end) - max(start, today)).days + 1      # ngày LỊCH giao khoảng
    return on_today, dict(days)
