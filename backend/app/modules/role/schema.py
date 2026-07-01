from pydantic import BaseModel


class RoleCreate(BaseModel):
    code: str
    name: str
    description: str = ""


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class RoleOut(BaseModel):
    id: int
    code: str
    name: str
    description: str = ""
    model_config = {"from_attributes": True}


class PermissionItem(BaseModel):
    entity: str
    can_read: bool = False
    can_create: bool = False
    can_write: bool = False
    can_delete: bool = False
    can_approve: bool = False
    can_print: bool = False
    can_export: bool = False
    scope: str = "own"


class PermissionUpdate(BaseModel):
    """Cập nhật toàn bộ ma trận quyền của 1 vai trò."""

    permissions: list[PermissionItem]
