from typing import Annotated

from pydantic import BaseModel, Field, field_validator

#  Giới hạn bám theo ĐÚNG cột trong `model.py` — `code` 50, `name` 100,
#  `description` 255. Không khai ở đây thì chuỗi dài hơn cột đi thẳng xuống
#  MySQL và vỡ ở tầng CSDL: người dùng nhận **500 internal_error** thay vì một
#  câu nói rõ sai chỗ nào (ép ra được 25/08/2026, tên 300 ký tự).
MaVaiTro = Annotated[str, Field(min_length=1, max_length=50)]
TenVaiTro = Annotated[str, Field(min_length=1, max_length=100)]
MoTaVaiTro = Annotated[str, Field(max_length=255)]


def _cat_khoang_trang(giaTri: str | None) -> str | None:
    """Cắt khoảng trắng TRƯỚC khi Pydantic đo độ dài.

    Không cắt thì `"   "` dài 3 ký tự nên lọt qua `min_length=1`, và vai trò ra
    một dòng trắng trong cột trái màn Phân quyền — nhìn như danh sách bị lỗi mà
    không ai đoán ra vì sao (ép ra được 25/08/2026).
    """
    return giaTri.strip() if isinstance(giaTri, str) else giaTri


class RoleCreate(BaseModel):
    code: MaVaiTro
    name: TenVaiTro
    description: MoTaVaiTro = ""

    _cat = field_validator("code", "name", "description", mode="before")(_cat_khoang_trang)


class RoleUpdate(BaseModel):
    name: TenVaiTro | None = None
    description: MoTaVaiTro | None = None

    _cat = field_validator("name", "description", mode="before")(_cat_khoang_trang)


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
