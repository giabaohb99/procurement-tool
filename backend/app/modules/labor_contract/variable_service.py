"""Nghiệp vụ Danh sách biến mẫu HĐLĐ (duoc-CR-630): liệt kê, tạo, sửa, xóa, đếm nơi đang dùng.

Hai loại dòng (xem `variable_model.py`): HỆ THỐNG chỉ sửa nhãn / mô tả / ẩn, mã bất biến, không xóa;
TÙY CHỈNH sửa đủ nhưng KHÓA mã + kiểu khi đã được dùng (mẫu chứa biến hoặc hợp đồng giữ giá trị), và
chỉ xóa được khi chưa ai dùng — còn lại phải «Ngừng dùng». Quyền ghi (phạm vi tất cả) gác ở controller.
"""
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.labor_contract_codes import LaborContractVariableSource as Src
from app.core.scoping import apply_scope

from .variable_access import ENTITY as TEMPLATE_ENTITY
from .lookup import names_map
from .placeholder_catalog import KNOWN_KEYS
from .template_model import LaborContractTemplate
from .variable_model import LaborContractVariable as V
from .variable_registry import contract_value_count, template_usage
from . import variable_rules as rules

SYSTEM_EDITABLE = frozenset({"label", "description", "is_hidden"})


class VariableInUse(Exception):
    """Biến đang được dùng — controller đổi thành 409 kèm `details`."""

    def __init__(self, message: str, details: dict):
        super().__init__(message)
        self.message, self.details = message, details


def list_variables(db: Session, *, q: str, source: int | None, value_type: int | None,
                   is_active: bool | None, offset: int, limit: int) -> tuple[int, list[V]]:
    #  Dòng hệ thống có mã không còn trong code (bỏ biến khỏi `placeholder_catalog`) thì không trả.
    query = db.query(V).filter(or_(V.source == int(Src.CUSTOM), V.code.in_(KNOWN_KEYS)))
    if source:
        query = query.filter(V.source == source)
    if value_type:
        query = query.filter(V.value_type == value_type)
    if is_active is not None:
        query = query.filter(V.is_active == is_active)
    keyword = (q or "").strip()[:100]
    if keyword:
        #  Mã biến chứa dấu «_» nên KHÔNG bỏ nó đi như ô tìm mẫu — thoát ký tự đại diện của LIKE.
        like = "%" + keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        query = query.filter(or_(V.code.like(like, escape="\\"), V.label.like(like, escape="\\")))
    total = query.count()
    return total, query.order_by(V.source, V.sort_order, V.code).offset(offset).limit(limit).all()


def get_or_404(db: Session, vid: int, lock: bool = False) -> V:
    q = db.query(V).filter(V.id == vid)
    if lock:
        q = q.with_for_update().populate_existing()
    row = q.first()
    if row is None or (int(row.source) == int(Src.SYSTEM) and row.code not in KNOWN_KEYS):
        raise HTTPException(404, "Không tìm thấy biến")
    return row


def usage(db: Session, user, profile: dict, row: V) -> dict:
    """Mẫu đang chứa biến (CHỈ mẫu người xem thấy theo phạm vi + SỐ mẫu còn lại) và số hợp đồng giữ giá trị."""
    used = template_usage(db, row.code)
    visible_ids = set()
    if used:
        visible_ids = {i for (i,) in apply_scope(
            db.query(LaborContractTemplate.id).filter(LaborContractTemplate.id.in_([u[0] for u in used])),
            LaborContractTemplate, TEMPLATE_ENTITY, user, profile, "read").all()}
    from app.modules.company.model import Company

    visible = [u for u in used if u[0] in visible_ids]
    companies = names_map(db, Company, {u[2] for u in visible})
    return {"templates": [{"id": i, "name": n, "company_name": companies.get(c, "")} for i, n, c in visible],
            "template_count": len(used), "hidden_template_count": len(used) - len(visible),
            "contract_count": contract_value_count(db, row.code)}


def _locked_reason(db: Session, row: V) -> dict | None:
    """None nếu chưa ai dùng; ngược lại số mẫu / số hợp đồng đang giữ biến."""
    templates, contracts = len(template_usage(db, row.code)), contract_value_count(db, row.code)
    return {"template_count": templates, "contract_count": contracts} if (templates or contracts) else None


def code_locked(db: Session, row: V) -> bool:
    return int(row.source) == int(Src.SYSTEM) or _locked_reason(db, row) is not None


def _in_use_sentence(templates: int, contracts: int) -> str:
    return f"Biến đang dùng trong {templates} mẫu / {contracts} hợp đồng"


def create(db: Session, user, data) -> V:
    if db.query(V).filter(V.source == int(Src.CUSTOM)).count() >= rules.MAX_CUSTOM_VARIABLES:
        raise HTTPException(422, f"Tối đa {rules.MAX_CUSTOM_VARIABLES} biến tùy chỉnh")
    if db.query(V.id).filter(V.code == data.code).first():
        raise HTTPException(400, "Mã biến đã tồn tại")
    row = V(source=int(Src.CUSTOM), created_by=user.id, updated_by=user.id, is_hidden=False,
            **data.model_dump())
    db.add(row)
    _commit_unique(db)
    db.refresh(row)
    return row


def _commit_unique(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:   # đua tạo/đổi mã trùng: ràng buộc unique ở DB là chốt thật
        db.rollback()
        raise HTTPException(409, "Mã biến đã tồn tại (vừa có người tạo trùng)") from None


def update(db: Session, user, row: V, data) -> V:
    fields = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if int(row.source) == int(Src.SYSTEM):
        extra = sorted(set(fields) - SYSTEM_EDITABLE)
        if extra:
            raise HTTPException(422, "Biến hệ thống chỉ sửa được tên hiển thị, mô tả và ẩn/hiện — "
                                     f"không sửa được: {', '.join(extra)}")
    else:
        _prepare_custom_update(db, row, fields)
    for key, value in fields.items():
        setattr(row, key, value)
    row.updated_by = user.id
    _commit_unique(db)
    db.refresh(row)
    return row


def _prepare_custom_update(db: Session, row: V, fields: dict) -> None:
    if "is_hidden" in fields:
        raise HTTPException(422, "Biến tùy chỉnh không ẩn được — hãy dùng «Ngừng dùng»")
    if "code" in fields:
        fields["code"] = fields["code"].strip()
    code_changes = "code" in fields and fields["code"] != row.code
    type_changes = "value_type" in fields and fields["value_type"] != row.value_type
    if code_changes:
        try:
            rules.check_code(fields["code"])
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from None
    if code_changes or type_changes:
        reason = _locked_reason(db, row)
        if reason:
            what = "mã" if code_changes else "kiểu giá trị"
            raise HTTPException(409, f"{_in_use_sentence(reason['template_count'], reason['contract_count'])} "
                                     f"— không đổi được {what}")
    if code_changes and db.query(V.id).filter(V.code == fields["code"], V.id != row.id).first():
        raise HTTPException(400, "Mã biến đã tồn tại")
    if "default_value" in fields or type_changes:
        try:
            fields["default_value"] = rules.normalize_value(
                fields.get("value_type", row.value_type), fields.get("default_value", row.default_value))
        except ValueError as exc:
            raise HTTPException(422, f"Giá trị mặc định: {exc}") from None


def delete(db: Session, user, profile: dict, row: V) -> str:
    """Xóa CỨNG biến chưa ai dùng; trả mã để ghi nhật ký. Đang dùng → `VariableInUse`."""
    if int(row.source) == int(Src.SYSTEM):
        raise HTTPException(409, "Biến hệ thống không xóa được — hãy dùng «Ẩn»")
    info = usage(db, user, profile, row)
    if info["template_count"] or info["contract_count"]:
        raise VariableInUse(
            f"{_in_use_sentence(info['template_count'], info['contract_count'])} — không xóa được, "
            "hãy chọn «Ngừng dùng»",
            {"templates": info["templates"], "hidden_template_count": info["hidden_template_count"],
             "contract_count": info["contract_count"]})
    code = row.code
    db.delete(row)
    db.commit()
    return code
