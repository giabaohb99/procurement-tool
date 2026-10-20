"""Xuất Excel báo cáo «Mức dùng chức năng» (duoc-CR-655): tiêu đề cột cố định, ô chữ lọc ký tự mở đầu công thức."""
from sqlalchemy.orm import Session

from app.core.export_xlsx import Col, xlsx_response
from app.core.ui_action_codes import UI_ACTION_LABELS
from app.core.usage_codes import FEATURE_KIND_LABELS, UI_FORM_LABELS
from app.core.usage_codes import FeatureKind as K
from app.modules.export_log.model import ExportLog

from . import service

ENTITY = "feature_usage"
COLUMNS = [
    Col("kind", "Loại", width=16), Col("name", "Chức năng", width=34), Col("route", "Màn hình", width=40),
    Col("users", "Số người dùng", kind="int", width=14), Col("uses", "Số lần", kind="int", width=12),
    Col("completes", "Đã gửi", kind="int", width=12), Col("abandons", "Bỏ dở", kind="int", width=12),
    Col("abandon_rate", "Tỷ lệ bỏ dở", kind="percent", width=14), Col("fails", "Không ra kết quả", kind="int", width=16),
]


def _safe(text: str) -> str:
    """Ô chữ không được mở đầu bằng ký tự công thức (= + - @) kẻo Excel hiểu là công thức."""
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


def _name(i: dict) -> str:
    if i["kind"] == int(K.ACTION):
        return UI_ACTION_LABELS.get(i["code"], f"Mã {i['code']}")
    if i["kind"] == int(K.FORM):
        return UI_FORM_LABELS.get(i["code"], f"Mã {i['code']}")
    return ""


def export_summary(db: Session, user, f: service.Filters):
    data = service.summary(db, f)
    rows = []
    for key in ("actions", "forms", "screens", "searches", "errors"):
        for i in data[key]:
            opened = i["uses"] if i["kind"] == int(K.FORM) else 0
            rows.append({**i, "kind": FEATURE_KIND_LABELS[K(i["kind"])], "name": _name(i), "route": _safe(i["route"]),
                         "abandon_rate": round(i["abandons"] / opened * 100, 2) if opened else None})
    name = f"muc-dung-chuc-nang-{f.date_from}-{f.date_to}"
    response = xlsx_response(name, COLUMNS, rows, "Chuc nang")
    db.add(ExportLog(entity=ENTITY, fmt="xlsx", row_count=len(rows), filename=f"{name}.xlsx",
                     file_size=len(response.body), file_id=0, filter_summary="", created_by=user.id,
                     updated_by=user.id))
    db.commit()
    return response
