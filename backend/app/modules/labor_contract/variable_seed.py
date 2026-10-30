"""Nạp 48 dòng biến HỆ THỐNG vào `tab_labor_contract_variable` (duoc-CR-630).

INSERT-ONLY (D-018): dòng đã có KHÔNG bao giờ bị cập nhật — HR đã sửa nhãn/mô tả/ẩn trên giao diện
thì lần deploy sau không được ghi đè. Mã không còn trong `placeholder_catalog` thì dòng DB bị bỏ qua
ở mọi chỗ đọc (không xóa).
"""
import logging

from sqlalchemy.orm import Session

from app.core.labor_contract_codes import LaborContractVariableSource, LaborContractVariableType

from .placeholder_catalog import KNOWN_KEYS, PLACEHOLDERS
from .variable_model import LaborContractVariable

log = logging.getLogger("app.labor_contract")


def ensure_system_variables(db: Session) -> int:
    """Chèn dòng cho biến hệ thống chưa có; trả số dòng chèn. Nơi gọi tự commit."""
    rows = db.query(LaborContractVariable.code, LaborContractVariable.source).all()
    have = {c for c, _ in rows}
    for code, source in rows:   # dòng TÙY CHỈNH trùng mã hệ thống: lệch dữ liệu, chỉ cảnh báo (không tự sửa)
        if int(source) == int(LaborContractVariableSource.CUSTOM) and code in KNOWN_KEYS:
            log.warning("Biến tùy chỉnh \"%s\" trùng mã biến hệ thống — giá trị hệ thống sẽ thắng", code)
    added = 0
    for order, p in enumerate(PLACEHOLDERS, start=1):
        if p.key in have:
            continue
        db.add(LaborContractVariable(
            code=p.key, source=int(LaborContractVariableSource.SYSTEM),
            value_type=int(LaborContractVariableType.TEXT), label=p.label, description="",
            example=p.example, is_active=True, is_hidden=False, sort_order=order))
        added += 1
    if added:
        db.flush()
    return added
