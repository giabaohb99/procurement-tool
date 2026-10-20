"""Xuất Excel báo cáo «Năng lực theo loại việc» (duoc-CR-657): một dòng cho mỗi loại việc + mỗi (loại việc × người).

Dưới ngưỡng mẫu: ô số để TRỐNG và cột «Ghi chú» ghi «chưa đủ mẫu» — không điền 0 (0 ngày là một con số có nghĩa).
Ô chữ lọc ký tự mở đầu công thức do `xlsx_response` lo.
"""
from sqlalchemy.orm import Session

from app.core.export_xlsx import Col, xlsx_response
from app.modules.capability import stats_service
from app.modules.export_log.model import ExportLog

ENTITY = "work_capability"
COLUMNS = [
    Col("level", "Mức", width=12), Col("kind_label", "Loại phiếu", width=22), Col("task_type_name", "Loại việc", width=26),
    Col("full_name", "Người xử lý", width=26), Col("employee_code", "Mã NV", width=12),
    Col("n_done", "Số xong", kind="int", width=10), Col("n_estimated", "Số ước tính (loại khỏi số liệu)", kind="int", width=18),
    Col("mean_days", "TB (ngày)", kind="decimal", width=11), Col("p50_days", "Trung vị (ngày)", kind="decimal", width=14),
    Col("p90_days", "P90 (ngày)", kind="decimal", width=11), Col("max_days", "Chậm nhất (ngày)", kind="decimal", width=15),
    Col("rework_rate", "Làm lại / phiếu (%)", kind="percent", width=14), Col("late_rate", "Tỷ lệ trễ hạn", kind="percent", width=14),
    Col("est_ratio_p50", "Thực tế / ước lượng", kind="decimal", width=16), Col("note", "Ghi chú", width=30),
]


def _rows(data: dict) -> list[dict]:
    out = []
    for level, items in (("Loại việc", data["types"]), ("Người", data["people"])):
        for r in items:
            note = "chưa đủ mẫu" if r["below_threshold"] else ""
            rate = lambda v: None if v is None else round(v * 100, 1)  # noqa: E731
            out.append({**r, "rework_rate": rate(r["rework_rate"]), "late_rate": rate(r["late_rate"]), "level": level, "note": note, "full_name": r.get("full_name", "")})
    return out


def export_summary(db: Session, user, f: stats_service.StatsFilter):
    rows = _rows(stats_service.fetch_stats(db, f))
    name = f"nang-luc-theo-loai-viec-{f.date_from}-{f.date_to}"
    response = xlsx_response(name, COLUMNS, rows, "Nang luc")
    db.add(ExportLog(entity=ENTITY, fmt="xlsx", row_count=len(rows), filename=f"{name}.xlsx",
                     file_size=len(response.body), file_id=0, filter_summary="", created_by=user.id, updated_by=user.id))
    db.commit()
    return response
