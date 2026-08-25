from pydantic import BaseModel


class RoleCreate(BaseModel):
    code: str
    name: str
    description: str = ""


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class RoleOrder(BaseModel):
    """Toàn bộ dãy vai trò theo đúng thứ tự muốn lưu."""

    role_ids: list[int]


class RoleOut(BaseModel):
    id: int
    code: str
    name: str
    description: str = ""
    sort_order: int = 0
    model_config = {"from_attributes": True}


class PermissionItem(BaseModel):
    entity: str
    can_read: bool = False
    can_create: bool = False
    can_write: bool = False
    can_delete: bool = False
    can_approve: bool = False
    can_cancel: bool = False
    can_print: bool = False
    can_export: bool = False
    scope: str = "own"


class PermissionUpdate(BaseModel):
    """Cập nhật toàn bộ ma trận quyền của 1 vai trò."""

    permissions: list[PermissionItem]
