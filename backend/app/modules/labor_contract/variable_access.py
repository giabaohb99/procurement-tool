"""Ai được GHI danh mục biến (duoc-CR-630, PO chốt): chỉ người có phạm vi KHÔNG HẠN CHẾ (mọi pháp nhân).

Danh mục biến dùng chung mọi pháp nhân, nên HR chỉ quản một pháp nhân không được sửa nhãn / mặc định /
ngừng dùng ảnh hưởng mẫu của pháp nhân khác. Quyền hành động vẫn do `require(...)` ở controller gác;
hàm này chỉ thêm điều kiện «phạm vi của hành động đó là tất cả».
"""
from fastapi import HTTPException

from app.core.scoping import scope_condition

from .template_model import LaborContractTemplate

ENTITY = "labor_contract_template"
UNRESTRICTED_ONLY = ("Chỉ người có phạm vi «tất cả pháp nhân» ở quyền Mẫu hợp đồng lao động "
                     "mới được thêm, sửa hoặc xóa biến — danh mục biến dùng chung mọi pháp nhân")


def is_unrestricted(user, profile: dict, action: str) -> bool:
    """`scope_condition(...) is None` = mọi grant có quyền `action` gộp lại thấy TẤT CẢ (kể cả sau khi
    trừ loại trừ / giới hạn pháp nhân gán riêng theo người)."""
    return scope_condition(LaborContractTemplate, ENTITY, user, profile, action) is None


def ensure_unrestricted(user, profile: dict, action: str) -> None:
    if not is_unrestricted(user, profile, action):
        raise HTTPException(403, UNRESTRICTED_ONLY)
