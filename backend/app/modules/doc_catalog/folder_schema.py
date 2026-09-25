"""Schema CÂY THƯ MỤC VĂN BẢN.

`max_length` khớp ĐÚNG `String(n)` của `folder_model.py` (CR-316) — chuỗi dài
phải dừng ở 422, không rơi xuống MySQL rồi văng 500.

Các API chỉ ĐỌC (`/tree`, `/search`, `/{id}`) trả `dict` dựng tay ở
`folder_tree_service.py`, không đi qua Pydantic response model — cùng lối với
`document`/`help_center`: tránh phải đồng bộ hai nơi mỗi khi thêm một khóa.
"""
from typing import Literal

from pydantic import BaseModel, Field

from .folder_constants import LINK_MODE_ADD

#  Trần số id một lượt gửi (M5, rà soát 23/09/2026) — `move_documents`/
#  `bulk_unlink` commit + kiểm quyền TỪNG văn bản trong vòng lặp; không trần
#  thì 10 nghìn id là 10 nghìn commit trong một request. 500 đủ rộng cho một
#  trang danh sách chọn hết, hẹp đủ để không nghẽn.
MAX_BULK_IDS = 500


class FolderCreate(BaseModel):
    #  `0` = tạo THƯ MỤC TỰ DO ở gốc cây (mở 24/09/2026, xem
    #  `folder_free_root_service.py`); > 0 = thư mục con như cũ.
    parent_id: int = Field(ge=0)
    name: str = Field(min_length=1, max_length=150)
    code: str = Field(default="", max_length=50)
    description: str = Field(default="", max_length=500)
    sort_order: int | None = None


class FolderUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=150)
    code: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    sort_order: int | None = None
    #  Ngừng dùng/khôi phục đi qua đây (0=chưa gửi giữ nguyên). Dải hợp lệ kiểm
    #  ở service theo `FolderStatus`, không khóa cứng `le=` ở đây để thêm trạng
    #  thái sau không phải sửa schema.
    status: int | None = None
    #  Mức quyền NỀN (phase 04, duoc-CR-475) — chỉ người mức QUẢN LÝ đổi được
    #  (route `PATCH /{folder_id}` đã gác bằng `ensure_level(..., MANAGE)`).
    #  `None` = không gửi, giữ nguyên; dải hợp lệ (0-3) kiểm ở
    #  `folder_service.update_folder` theo `FolderAccessLevel`.
    default_access: int | None = None


class FolderMoveIn(BaseModel):
    #  `0` = chuyển ra GỐC cây (mở 24/09/2026).
    new_parent_id: int = Field(ge=0)


class FolderReorderItem(BaseModel):
    id: int = Field(gt=0)
    sort_order: int


class FolderReorderIn(BaseModel):
    items: list[FolderReorderItem] = Field(min_length=1, max_length=MAX_BULK_IDS)


class FolderLinkIn(BaseModel):
    """`POST /documents/link` — gắn HÀNG LOẠT văn bản vào một thư mục.

    `mode` khai `Literal` (M4, rà soát 23/09/2026) — trước đó kiểm ở
    `model_post_init` bằng `raise ValueError`, mà Pydantic v2 KHÔNG bọc lỗi từ
    hook này thành `ValidationError`: mode sai lọt thẳng thành lỗi 500 chưa bắt,
    không phải 422 như một trường sai kiểu bình thường.
    """

    document_ids: list[int] = Field(min_length=1, max_length=MAX_BULK_IDS)
    folder_id: int = Field(gt=0)
    mode: Literal["add", "replace"] = LINK_MODE_ADD


class FolderUnlinkIn(BaseModel):
    """`POST /documents/unlink` — gỡ HÀNG LOẠT văn bản khỏi một thư mục."""

    document_ids: list[int] = Field(min_length=1, max_length=MAX_BULK_IDS)
    folder_id: int = Field(gt=0)


class DocumentFolderSetIn(BaseModel):
    """`PUT /api/documents/{id}/folders` — đặt lại TOÀN BỘ thư mục của MỘT văn bản."""

    folder_ids: list[int] = Field(default_factory=list, max_length=MAX_BULK_IDS)
    primary_id: int | None = None
