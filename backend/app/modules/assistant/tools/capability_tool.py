"""Hai công cụ NĂNG LỰC ĐỘI cho Trợ lý web / bot / cổng MCP (kh-AI1-2, doc/erp/tai-lieu-ai/22 §4, §6).

Máy tính số, AI viết chữ: mọi con số lấy từ `capability/ai_contract` + `stats_service` (anh Dược, duoc-CR-656/657); ở đây chỉ
quyết PHẠM VI theo người hỏi, đọc tham số và gọt kết quả cho gọn.

Quyền (A1 chốt 22/10, phương án A — *AI chỉ đề xuất, người quyết*):
  · có khóa báo cáo 16 «Năng lực theo loại việc» → thấy đủ số, phòng nào cũng được (bỏ trống = pháp nhân của mình);
  · trưởng phòng (`Department.manager_id`) không có khóa 16 → `team_capacity` chỉ trả THỨ TỰ gợi ý trong phòng mình + phòng
    con, không số; `task_type_stats` từ chối;
  · người khác → từ chối, câu giải thích nói cần khóa 16 và ai giao được.
Phòng ngoài phạm vi và phòng không tồn tại trả CÙNG một câu.
"""
from __future__ import annotations

from app.core.capability_codes import CYCLE_KIND_LABELS, CycleKind
from app.core.report_keys import ReportKey

from .base import ToolContext, ToolSpec

MAX_PEOPLE = 20
MAX_ROWS = 30
MAX_TEXT = 120
KIND_CODES = tuple(k.name.lower() for k in CycleKind)
REASON_LABELS = {"ON_LEAVE_TODAY": "đang nghỉ phép hôm nay",
                 "BELOW_THRESHOLD": "chưa đủ 5 việc cùng loại đã xong để đo tốc độ"}
LOAD_FIELDS = ("open_items_total", "work_open", "work_overdue", "work_estimate_hours_open", "approvals_pending",
               "approvals_overdue", "pr_handling", "po_handling", "survey_lines_handling", "docs_pending_issue",
               "on_leave_today", "leave_days_ahead")
STAT_FIELDS = ("n_done", "n_estimated", "below_threshold", "p50_days", "p90_days", "mean_days", "rework_rate",
               "first_pass_rate", "late_rate", "est_ratio_p50")
KEY_HINT = ("Số năng lực theo từng người cần khóa báo cáo 16 «Năng lực theo loại việc» — quản trị giao ở Phân quyền tài "
            "khoản → tab Báo cáo.")


def _deny(what: str) -> dict:
    return {"denied": True, "reason": f"Bạn không có quyền xem {what}. {KEY_HINT} Trưởng phòng không có khóa này vẫn hỏi "
                                      "được thứ tự gợi ý người trong phòng mình (team_capacity), không kèm số."}


def _has_key16(ctx: ToolContext) -> bool:
    from app.modules.report_access.service import can_view_report

    return can_view_report(ctx.db, ctx.user, ReportKey.WORK_CAPABILITY, ctx.profile)


def _load_departments(ctx: ToolContext) -> list:
    from app.modules.department.model import Department

    return list(ctx.db.query(Department.id, Department.code, Department.name, Department.parent, Department.manager_id,
                             Department.company_id).filter(Department.is_active == True))   # noqa: E712


def _add_children(depts: list, roots: set[int]) -> set[int]:
    """Phòng gốc + mọi phòng con cháu (dò theo `parent`; tập đã thăm chặn vòng lặp do dữ liệu hỏng)."""
    children: dict[int, list[int]] = {}
    for d in depts:
        children.setdefault(int(d.parent or 0), []).append(int(d.id))
    seen, stack = set(), list(roots)
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(children.get(cur, ()))
    return seen


def _match_department(depts: list, allowed: set[int] | None, raw: str) -> tuple[list[int], dict | None]:
    """Tên / mã phòng → id phòng (kèm phòng con). `allowed = None` là được mọi phòng. Lỗi trả dict cho model."""
    from app.modules.assistant.glossary import fold

    pool = [d for d in depts if allowed is None or int(d.id) in allowed]
    key = fold(raw)
    hit = [d for d in pool if (d.code or "").lower() == raw.strip().lower()] or \
          [d for d in pool if key and key in fold(d.name or "")]
    if not hit:
        return [], {"error": f"Không thấy phòng «{raw}» trong các phòng bạn được xem năng lực."}
    if len(hit) > 1:
        return [], {"need_choice": True, "error": f"Có {len(hit)} phòng khớp «{raw}» — hỏi người dùng chọn một.",
                    "choices": [{"code": d.code, "name": d.name} for d in hit[:10]]}
    return sorted(_add_children(depts, {int(hit[0].id)}) & (allowed if allowed is not None else {int(d.id) for d in depts})), None


def _parse_kind(raw) -> tuple[int, dict | None]:
    code = str(raw or "work_task").strip().lower()[:MAX_TEXT]
    if code not in KIND_CODES:
        return 0, {"error": f"Loại phiếu «{code}» không có. Dùng một trong: {', '.join(KIND_CODES)}."}
    return int(CycleKind[code.upper()]), None


def _find_task_type(ctx: ToolContext, raw) -> tuple[dict | None, dict | None]:
    from app.modules.assistant.glossary import fold
    from app.modules.work.task_type_model import WorkTaskType

    text = str(raw or "").strip()
    if not text:
        return None, None
    if len(text) > MAX_TEXT:
        return None, {"error": f"Tên loại việc dài quá {MAX_TEXT} ký tự."}
    rows = list(ctx.db.query(WorkTaskType.id, WorkTaskType.code, WorkTaskType.name)
                .filter(WorkTaskType.is_active == True))   # noqa: E712
    key = fold(text)
    hit = [r for r in rows if (r.code or "").lower() == text.lower()] or [r for r in rows if key and key in fold(r.name or "")]
    if not hit:
        return None, {"error": f"Không thấy loại việc «{text}» trong danh mục Loại việc của Dự án."}
    if len(hit) > 1:
        return None, {"need_choice": True, "error": f"Có {len(hit)} loại việc khớp «{text}» — hỏi người dùng chọn một.",
                      "choices": [{"code": r.code, "name": r.name} for r in hit[:10]]}
    return {"id": int(hit[0].id), "code": hit[0].code, "name": hit[0].name}, None


def _clamp_int(raw, default: int, lo: int, hi: int) -> int:
    try:
        return max(lo, min(int(raw), hi))
    except (TypeError, ValueError):
        return default


def _pick(row: dict | None, fields: tuple) -> dict:
    return {k: (row or {}).get(k) for k in fields}


def _team_capacity(ctx: ToolContext, args: dict) -> dict:
    from app.modules.capability import ai_contract

    detail = _has_key16(ctx)
    emp_id = int(getattr(ctx.user, "employee_id", 0) or 0)
    depts = _load_departments(ctx)
    managed = {int(d.id) for d in depts if emp_id and int(d.manager_id or 0) == emp_id}
    if not detail and not managed:
        return _deny("năng lực đội")
    allowed = None if detail else _add_children(depts, managed)
    kind, err = _parse_kind(args.get("kind"))
    if err:
        return err
    tt, err = _find_task_type(ctx, args.get("task_type"))
    if err:
        return err
    company_id, dept_ids = None, []
    raw_dept = str(args.get("department") or "").strip()[:MAX_TEXT]
    if raw_dept:
        dept_ids, err = _match_department(depts, allowed, raw_dept)
        if err:
            return err
    elif allowed is not None:
        dept_ids = sorted(allowed)
    else:
        from app.modules.employee.model import Employee

        #  Pháp nhân của CHÍNH người hỏi — không đọc dữ liệu người khác.
        if emp_id:
            company_id = int(ctx.db.query(Employee.company_id).filter(Employee.id == emp_id).scalar() or 0) or None
        if not company_id:
            return {"error": "Tài khoản chưa gắn pháp nhân — nêu tên phòng muốn xem."}
    limit = _clamp_int(args.get("limit"), 10, 1, MAX_PEOPLE)
    ranked = ai_contract.suggest_assignees(
        ctx.db, ctx.user, kind=kind, task_type_id=tt["id"] if tt else 0, company_id=company_id,
        department_ids=dept_ids or None, limit=limit, window_days=_clamp_int(args.get("window_days"), 180, 30, 365),
        profile=ctx.profile)
    people = []
    for r in ranked:
        item = {"rank": r["rank"], "employee_code": r["employee_code"], "full_name": r["full_name"],
                "reasons": [REASON_LABELS.get(x, x) for x in r["reasons"]]}
        if detail:
            item["stats"] = _pick(r.get("stats"), STAT_FIELDS)
            item["load"] = _pick(r.get("load"), LOAD_FIELDS)
        people.append(item)
    names = {int(d.id): d.name for d in depts}
    note = ("Thứ tự: không nghỉ hôm nay → đủ mẫu → ít việc đang ôm → trung vị ngắn → ít làm lại. Đây là ĐỀ XUẤT, người giao "
            "việc quyết; giải thích lý do, đừng tự cộng thành điểm.")
    if not detail:
        note += " Chỉ có thứ tự gợi ý, không có số. " + KEY_HINT
    else:
        note += " Thời gian tính bằng ngày lịch; tỷ lệ là số 0…1. Số `None` = chưa đủ 5 mẫu, nói «chưa đủ mẫu», đừng đoán."
    return {"kind": CycleKind(kind).name.lower(), "kind_label": CYCLE_KIND_LABELS[CycleKind(kind)], "task_type": tt,
            "departments": [names[i] for i in dept_ids if i in names][:20] or None, "company_id": company_id,
            "detail": detail, "total": len(people), "has_more": len(people) == limit, "people": people, "note": note}


def _task_type_stats(ctx: ToolContext, args: dict) -> dict:
    from app.modules.capability import stats_service
    from app.modules.capability.ai_contract import _window
    from app.modules.capability.stats_service import StatsFilter
    from app.modules.employee.model import Employee

    if not _has_key16(ctx):
        return _deny("thống kê năng lực theo loại việc")
    kinds: tuple[int, ...] = ()
    if args.get("kind"):
        kind, err = _parse_kind(args.get("kind"))
        if err:
            return err
        kinds = (kind,)
    tt, err = _find_task_type(ctx, args.get("task_type"))
    if err:
        return err
    dept_ids: list[int] = []
    raw_dept = str(args.get("department") or "").strip()[:MAX_TEXT]
    if raw_dept:
        dept_ids, err = _match_department(_load_departments(ctx), None, raw_dept)
        if err:
            return err
    emp_ids: tuple[int, ...] = ()
    person = str(args.get("person") or "").strip()[:MAX_TEXT]
    if person:
        emp = ctx.db.query(Employee.id).filter(Employee.code == person).first()
        if emp is None:
            return {"error": f"Không thấy nhân sự mã «{person}» — dùng employee_lookup để lấy mã."}
        emp_ids = (int(emp.id),)
    window = _clamp_int(args.get("window_days"), 180, 30, 365)
    d_from, d_to = _window(window)
    by_person = bool(args.get("by_person")) or bool(emp_ids)
    f = StatsFilter(date_from=d_from, date_to=d_to, kinds=kinds, task_type_ids=(tt["id"],) if tt else (),
                    department_ids=tuple(dept_ids), employee_ids=emp_ids,
                    unrestricted=not (dept_ids or emp_ids))          # khóa 16 = xem mọi phòng (doc 22 §4)
    rows = stats_service.task_type_stats(ctx.db, f, by_person=by_person)
    keep = ("kind_label", "task_type_name") + (("employee_code", "full_name") if by_person else ()) + STAT_FIELDS
    out = [{"kind": CycleKind(r["kind"]).name.lower(), **{k: r.get(k) for k in keep}} for r in rows[:MAX_ROWS]]
    return {"window": {"from": d_from.isoformat(), "to": d_to.isoformat(), "days": window}, "task_type": tt,
            "by_person": by_person, "total": len(rows), "has_more": len(rows) > MAX_ROWS, "rows": out,
            "note": ("Thời gian tính bằng ngày lịch từ lúc nhận tới lúc xong; tỷ lệ là số 0…1. Số `None` = chưa đủ 5 việc "
                     "cùng loại đã xong — nói «chưa đủ mẫu», đừng đoán. Dòng ước tính (nhập từ hệ cũ) chỉ đếm ở "
                     "n_estimated, không vào trung vị. Chậm có thể là việc khó: chỉ đo, không chấm điểm người.")}


_KIND_PARAM = {"type": "string", "enum": list(KIND_CODES),
               "description": ("Loại phiếu / việc: work_task = việc Dự án (mặc định), purchase_request = YCMH, survey_request "
                               "= YCBG, purchase_order = ĐMH, payment_request = YCTT, document = văn bản, vehicle_booking = đặt "
                               "xe, seal_request = duyệt dấu, room_booking = phòng họp, leave_request = nghỉ phép.")}
_TASK_TYPE_PARAM = {"type": "string", "description": "Tên hoặc mã loại việc Dự án (chỉ dùng với kind=work_task)."}
_WINDOW_PARAM = {"type": "integer", "description": "Số ngày nhìn lại để đo tốc độ (30–365, mặc định 180)."}

TEAM_CAPACITY_SPEC = ToolSpec(
    name="team_capacity",
    description=("Gợi ý AI NÊN GIAO cho một loại việc / ai đang rảnh trong phòng: xếp người theo nghỉ phép hôm nay, đủ mẫu, "
                 "số việc đang ôm, tốc độ, tỷ lệ làm lại. Câu hỏi kiểu 'ai đang rảnh làm X', 'giao việc này cho ai', "
                 "'tải việc phòng tôi'. Người có khóa báo cáo 16 thấy kèm số; trưởng phòng chỉ thấy thứ tự trong phòng "
                 "mình + phòng con. Chỉ đề xuất — người giao việc quyết."),
    parameters={"type": "object", "properties": {
        "department": {"type": "string", "description": "Tên hoặc mã phòng; bỏ trống = các phòng mình phụ trách."},
        "kind": _KIND_PARAM, "task_type": _TASK_TYPE_PARAM, "window_days": _WINDOW_PARAM,
        "limit": {"type": "integer", "description": f"Tối đa bao nhiêu người (mặc định 10, tối đa {MAX_PEOPLE})."}}},
    handler=_team_capacity,
)

TASK_TYPE_STATS_SPEC = ToolSpec(
    name="task_type_stats",
    description=("Thống kê tốc độ theo loại việc: trung vị / p90 số ngày từ nhận tới xong, tỷ lệ trễ, tỷ lệ phải làm lại, "
                 "số mẫu — theo loại hoặc theo từng người. Câu hỏi kiểu 'loại việc X thường mất bao lâu', 'ai làm YCMH "
                 "nhanh nhất', 'tỷ lệ làm lại của phòng Y'. Chỉ người có khóa báo cáo 16 «Năng lực theo loại việc»."),
    parameters={"type": "object", "properties": {
        "kind": _KIND_PARAM, "task_type": _TASK_TYPE_PARAM,
        "department": {"type": "string", "description": "Tên hoặc mã phòng (kèm phòng con); bỏ trống = mọi phòng."},
        "person": {"type": "string", "description": "Mã nhân sự (ví dụ NSU209) để xem riêng một người."},
        "by_person": {"type": "boolean", "description": "true = tách theo từng người (mặc định gộp theo loại việc)."},
        "window_days": _WINDOW_PARAM}},
    handler=_task_type_stats,
)

CAPABILITY_SPECS = [TEAM_CAPACITY_SPEC, TASK_TYPE_STATS_SPEC]
