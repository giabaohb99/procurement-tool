"""Dựng dữ liệu ra cho Danh sách biến (duoc-CR-630): dòng quản lý, danh sách hướng dẫn, ô nhập theo HĐ."""
from sqlalchemy.orm import Session

from app.core.labor_contract_codes import LaborContractVariableSource as Src, LaborContractVariableType as T

from .lookup import user_names
from .placeholder_catalog import PLACEHOLDERS
from .template_model import LaborContractTemplate
from .variable_model import LaborContractVariable
from .variable_registry import custom_rows
from .variable_rules import money_word_key
from .variable_schema import VariableOut

CUSTOM_GROUP = "Biến tùy chỉnh"
_CATALOG = {p.key: p for p in PLACEHOLDERS}


def template_counts(db: Session, codes: list[str]) -> dict[str, int]:
    """Số mẫu (mọi pháp nhân) đang chứa từng mã — MỘT lượt quét bảng mẫu cho cả trang."""
    sets = [set(ph or []) for (ph,) in db.query(LaborContractTemplate.placeholders).all()]
    return {c: sum(1 for s in sets if c in s or money_word_key(c) in s) for c in codes}


def serialize_variables(db: Session, rows: list[LaborContractVariable]) -> list[dict]:
    counts = template_counts(db, [r.code for r in rows])
    creators = user_names(db, {r.created_by for r in rows})
    out = []
    for r in rows:
        system = int(r.source) == int(Src.SYSTEM)
        out.append(VariableOut(
            id=r.id, code=r.code, source=r.source, value_type=r.value_type, label=r.label,
            description=r.description or "", example=r.example or "", default_value=r.default_value or "",
            is_required=bool(r.is_required), is_active=bool(r.is_active), is_hidden=bool(r.is_hidden),
            sort_order=r.sort_order or 0, template_count=counts.get(r.code, 0),
            group=_CATALOG[r.code].group if system and r.code in _CATALOG else CUSTOM_GROUP,
            created_at=r.created_at, created_by_name=creators.get(r.created_by, ""),
        ).model_dump())
    return out


def guide_list(db: Session) -> list[dict]:
    """Danh sách cho khung chèn biến / bảng hướng dẫn: biến hệ thống KHÔNG ẩn (nhãn + mô tả theo DB,
    thiếu dòng DB thì theo mã nguồn) + biến tùy chỉnh ĐANG DÙNG + `<mã>_bang_chu` của biến tiền."""
    sys_rows = {r.code: r for r in db.query(LaborContractVariable)
                .filter(LaborContractVariable.source == int(Src.SYSTEM)).all()}
    out = []
    for p in PLACEHOLDERS:
        row = sys_rows.get(p.key)
        if row is not None and row.is_hidden:
            continue
        out.append({"key": p.key, "label": row.label if row else p.label, "group": p.group,
                    "example": p.example, "description": (row.description if row else "") or ""})
    for r in custom_rows(db, active_only=True):
        out.append({"key": r.code, "label": r.label, "group": CUSTOM_GROUP,
                    "example": r.example or "", "description": r.description or ""})
        if int(r.value_type) == int(T.MONEY):
            out.append({"key": money_word_key(r.code), "label": f"{r.label} (bằng chữ)", "group": CUSTOM_GROUP,
                        "example": "", "description": ""})
    return out


def input_fields(db: Session, include_inactive: bool = False) -> list[dict]:
    """Ô nhập của hộp Lập/Sửa HĐ: biến tùy chỉnh (mặc định chỉ ĐANG DÙNG; `include_inactive` để hộp
    Sửa hiện giá trị biến đã ngừng dùng ở chế độ chỉ đọc)."""
    return [{"code": r.code, "label": r.label, "description": r.description or "",
             "value_type": r.value_type, "default_value": r.default_value or "",
             "is_required": bool(r.is_required), "is_active": bool(r.is_active),
             "sort_order": r.sort_order or 0}
            for r in custom_rows(db, active_only=not include_inactive)]
