"""Công cụ CHỈ ĐỌC sổ việc chạy ngầm (bao-CR-703) — hỏi bằng lời "đêm qua việc nền nào lỗi", "sao lưu chạy chưa".

Cùng dữ liệu màn Hệ thống > Việc chạy ngầm (`job_run.service`), gác cùng quyền `setting.read` (quản trị).
"""
from datetime import datetime

from app.core.export_xlsx import VN_OFFSET
from app.core.job_run_codes import JobRunStatus

from .base import ToolContext, ToolSpec, denied

MAX_RUNS = 20
MAX_JOBS = 60


def _background_jobs(ctx: ToolContext, args: dict) -> dict:
    from app.modules.job_run import service

    if not ctx.can("setting", "read"):
        return denied("sổ việc chạy ngầm (cần quyền quản trị cấu hình hệ thống)")
    code = str(args.get("job") or "").strip()[:120]
    if code:
        try:
            limit = min(max(1, int(args.get("runs") or 5)), MAX_RUNS)
        except (TypeError, ValueError):
            limit = 5
        out = service.list_runs(ctx.db, code, page=1, page_size=limit)
        if not out["total"]:
            return {"job": code, "items": [], "total": 0,
                    "note": "Không có lần chạy nào ghi trong sổ cho mã việc này — xem lại mã (gọi không kèm job để lấy "
                            "danh sách mã), hoặc việc chưa chạy lần nào kể từ khi bật sổ."}
        return {"job": code, "items": out["items"], "total": out["total"], "has_more": out["total"] > limit,
                "url": "/system/background-jobs"}
    status = args.get("status")
    status = {"error": int(JobRunStatus.FAILED), "failed": int(JobRunStatus.FAILED), "running": int(JobRunStatus.RUNNING),
              "skipped": int(JobRunStatus.SKIPPED), "ok": int(JobRunStatus.SUCCESS), "never": 0}.get(str(status or ""))
    data = service.list_jobs(ctx.db, group=str(args.get("group") or "")[:20], status=status,
                             q=str(args.get("q") or "")[:100])
    items = [{k: j[k] for k in ("code", "name", "purpose", "group_label", "schedule_label", "enabled", "next_run_at",
                                "runs_7d", "failed_7d", "avg_duration_ms_7d")}
             | {"last_run": ({k: j["last_run"][k] for k in ("started_at", "duration_ms", "status_label", "summary",
                                                             "error")} if j["last_run"] else None)}
             for j in data["items"][:MAX_JOBS]]
    return {"items": items, "total": len(data["items"]), "has_more": len(data["items"]) > MAX_JOBS,
            "now": (datetime.utcnow() + VN_OFFSET).isoformat(timespec="minutes"), "url": "/system/background-jobs",
            "groups": data["groups"],
            "note": "Giờ là giờ Việt Nam. Muốn xem các lần chạy của một việc thì gọi lại với job = code."}


BACKGROUND_JOBS_SPEC = ToolSpec(
    name="background_jobs",
    description=("Sổ VIỆC CHẠY NGẦM của ERP (sao lưu, dọn dữ liệu, đồng bộ, nhắc việc, gom số...): tên, mục đích, lịch, "
                 "lần chạy gần nhất (trạng thái, thời lượng, lỗi), số lần chạy / lỗi 7 ngày, lần chạy kế. Dùng cho câu "
                 "kiểu 'đêm qua việc nền nào lỗi', 'sao lưu chạy chưa', 'việc dọn nhật ký chạy bao lâu'. Kèm job = mã việc "
                 "để xem N lần chạy gần nhất của việc đó. Chỉ quản trị (quyền xem cấu hình hệ thống)."),
    parameters={"type": "object", "properties": {
        "status": {"type": "string", "enum": ["error", "running", "skipped", "ok", "never"],
                   "description": "Lọc theo trạng thái lần chạy GẦN NHẤT (error = lỗi, never = chưa chạy lần nào)."},
        "group": {"type": "string", "enum": ["cleanup", "backup", "sync", "reminder", "stats", "monitor", "bot"],
                  "description": "Lọc theo nhóm việc."},
        "q": {"type": "string", "description": "Tìm theo tên / mã / mục đích việc (không dấu)."},
        "job": {"type": "string", "description": "Mã việc (code trong danh sách, vd backup.run) để xem các lần chạy."},
        "runs": {"type": "integer", "description": f"Số lần chạy gần nhất khi có job (mặc định 5, tối đa {MAX_RUNS})."}}},
    handler=_background_jobs,
)
