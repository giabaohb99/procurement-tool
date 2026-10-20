"""HỢP ĐỒNG DỮ LIỆU CHO TRỢ LÝ AI (duoc-CR-657, D1d) — hai hàm thuần của dịch vụ, Agent 4 (A1) bọc lại thành công cụ MCP / trợ lý.

Máy tính số, AI viết chữ: mọi công thức (trung vị, p90, làm lại, tải) nằm ở `stats_service` / `workload_service`; A1 KHÔNG tự viết lại.

Quyền (hai lớp, hàm tự kiểm — A1 chỉ cần truyền đúng `user`):
  · người có khóa báo cáo 16 (`ReportKey.WORK_CAPABILITY`, mặc định chỉ quản trị): thấy số liệu theo từng người;
  · người KHÔNG có khóa: `suggest_assignees` chỉ trả THỨ TỰ gợi ý (id/mã/tên + lý do), không kèm số; `get_capability` từ chối.
  · Phạm vi do NGƯỜI GỌI quyết: phải truyền `company_id` / `department_ids` / `employee_ids` (trưởng phòng: phòng mình + phòng con;
    hàm không tự mở rộng). Không truyền phạm vi nào thì trả `[]`.

Số theo người chỉ có khi ≥ 5 mẫu CÙNG loại (`below_threshold` = True thì mọi số là `None` — hãy nói «chưa đủ mẫu», đừng suy đoán).
Dòng `is_estimated` không bao giờ vào trung vị/p90. Không có điểm tổng hợp: A1 tự cân tải với tốc độ và GIẢI THÍCH.
"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.capability_codes import CycleKind, CycleRole
from app.core.report_keys import ReportKey
from app.modules.capability import stats_math, stats_service, workload_service
from app.modules.capability.stats_service import StatsFilter
from app.modules.report_access.service import can_view_report

DEFAULT_WINDOW_DAYS = 180
MAX_LIMIT = 20


class CapabilityForbidden(PermissionError):
    """Người gọi chưa được giao khóa báo cáo «Năng lực theo loại việc»."""


def _window(days: int = DEFAULT_WINDOW_DAYS, now: datetime | None = None):
    today = ((now or datetime.utcnow()) + timedelta(hours=7)).date()
    return today - timedelta(days=days - 1), today


def suggest_assignees(db: Session, user, *, kind: int, task_type_id: int = 0, company_id: int | None = None,
                      department_ids: list[int] | None = None, employee_ids: list[int] | None = None,
                      limit: int = 5, window_days: int = DEFAULT_WINDOW_DAYS, now: datetime | None = None,
                      profile: dict | None = None) -> list[dict]:
    """Ứng viên xử lý loại việc `(kind, task_type_id)` trong phạm vi do người gọi truyền, đã xếp hạng.

    Thứ tự (KHÔNG phải điểm): ① không nghỉ hôm nay ② đủ mẫu (≥ 5) trước ③ ít việc đang ôm (`open_items_total`) ④ trung vị ngắn
    ⑤ làm lại ít. Mỗi ứng viên có `rank`, `reasons` (mã) và — chỉ khi người gọi có khóa 16 — `stats` + `load`.
    `task_type_id = 0` với kind khác `WORK_TASK` là bình thường (chỉ task Dự án có loại việc).
    """
    CycleKind(kind)                                         # ValueError nếu kind lạ
    detail = can_view_report(db, user, ReportKey.WORK_CAPABILITY, profile)
    if not (company_id or department_ids or employee_ids):
        return []
    limit = max(1, min(int(limit or 5), MAX_LIMIT))
    loads = workload_service.current_load(db, company_id=company_id, department_ids=department_ids,
                                          employee_ids=employee_ids, now=now)
    if not loads:
        return []
    d_from, d_to = _window(window_days, now)
    stats = stats_service.task_type_stats(db, StatsFilter(
        date_from=d_from, date_to=d_to, role=CycleRole.HANDLER, kinds=(kind,), task_type_ids=(task_type_id,) if task_type_id else (),
        employee_ids=tuple(r["employee_id"] for r in loads)), by_person=True)
    by_emp = {s["employee_id"]: s for s in stats if s["task_type_id"] == task_type_id}

    ranked = []
    for load in loads:
        s = by_emp.get(load["employee_id"])
        enough = bool(s) and not s["below_threshold"]
        reasons = (["ON_LEAVE_TODAY"] if load["on_leave_today"] else []) + ([] if enough else ["BELOW_THRESHOLD"])
        key = (load["on_leave_today"], not enough, load["open_items_total"],
               s["p50_days"] if enough and s["p50_days"] is not None else float("inf"),
               s["rework_rate"] if enough and s["rework_rate"] is not None else float("inf"))
        ranked.append((key, load, s, reasons))
    ranked.sort(key=lambda x: (x[0], x[1]["employee_id"]))

    out = []
    for i, (_k, load, s, reasons) in enumerate(ranked[:limit], start=1):
        item = {"rank": i, "employee_id": load["employee_id"], "employee_code": load["employee_code"],
                "full_name": load["full_name"], "reasons": reasons}
        if detail:
            item["stats"] = s or stats_math.summarize([], 0)
            item["load"] = load
        out.append(item)
    return out


def get_capability(db: Session, user, employee_id: int, *, kinds: list[int] | None = None, window_days: int = DEFAULT_WINDOW_DAYS,
                   now: datetime | None = None, profile: dict | None = None) -> dict:
    """Năng lực + tải hiện tại của MỘT người: `{"employee_id", "by_type": [...], "load": {...} | None}`.

    Raise `CapabilityForbidden` nếu người gọi không có khóa 16 (số theo người là dữ liệu nhạy cảm — chỉ quản trị mặc định).
    """
    if not can_view_report(db, user, ReportKey.WORK_CAPABILITY, profile):
        raise CapabilityForbidden("Chưa được giao xem báo cáo: Năng lực theo loại việc")
    d_from, d_to = _window(window_days, now)
    by_type = stats_service.task_type_stats(db, StatsFilter(
        date_from=d_from, date_to=d_to, role=CycleRole.HANDLER, kinds=tuple(kinds or ()), employee_ids=(employee_id,)), by_person=True)
    loads = workload_service.current_load(db, employee_ids=[employee_id], now=now)
    return {"employee_id": employee_id, "window_days": window_days, "by_type": by_type, "load": loads[0] if loads else None}
