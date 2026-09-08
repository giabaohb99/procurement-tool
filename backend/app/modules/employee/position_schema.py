"""Schema của DANH MỤC CHỨC VỤ — xem `position_model.py`.

⚠️ Mọi ô chuỗi khai `max_length` khớp ĐÚNG `String(n)` ở model. Bài học
duoc-CR-316: thiếu khai thì chuỗi dài đi thẳng xuống MySQL và người dùng nhận
«mã sự cố» thay vì câu *«tối đa n ký tự»* — và **SQLite của bộ test không ép độ
dài `VARCHAR`**, nên chỗ này phải có test ở tầng schema mới bắt được.
"""
from pydantic import BaseModel, Field, field_validator

from .field_limits import Str30, Str100, Str500


def _require_text(value: str, field: str) -> str:
    """Cắt khoảng trắng thừa và chặn ô rỗng.

    Chặn ở đây vì `code` và `name` là hai thứ người dùng NHÌN THẤY để phân biệt
    các dòng danh mục. Một dòng tên rỗng thì ô chọn chức vụ hiện một mục trắng
    không bấm trúng, còn mã rỗng thì ràng buộc duy nhất chỉ cho phép **đúng
    một** dòng như vậy tồn tại — lần thứ hai người dùng gặp lỗi trùng mã mà
    không hiểu trùng với cái gì.
    """
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field} không được để trống")
    return text


class JobPositionCreate(BaseModel):
    code: Str30
    name: Str100
    is_active: bool = True
    sort_order: int = 0
    note: Str500 = ""
    department_id: int = 0

    @field_validator("code", "name")
    @classmethod
    def _not_blank(cls, v: str, info) -> str:
        return _require_text(v, "Mã chức vụ" if info.field_name == "code" else "Tên chức vụ")


class JobPositionUpdate(BaseModel):
    #  ⚠️ `code` KHÔNG sửa được — cùng lý lẽ với mã phòng họp: mã là thứ tệp CSV
    #  nhập/xuất và các màn khác dùng để trỏ tới dòng này.
    name: Str100 | None = None
    is_active: bool | None = None
    sort_order: int | None = None
    note: Str500 | None = None
    department_id: int | None = None

    @field_validator("name")
    @classmethod
    def _not_blank(cls, v: str | None) -> str | None:
        return None if v is None else _require_text(v, "Tên chức vụ")


class JobPositionResponse(BaseModel):
    id: int
    code: str = ""
    name: str = ""
    is_active: bool = True
    sort_order: int = 0
    note: str = ""
    department_id: int = 0

    model_config = {"from_attributes": True}


#  ⚠️ CỐ Ý KHÔNG trả kèm «số người đang giữ chức vụ này». Bộ sinh CRUD dựng câu
#  trả lời bằng `OutSchema.model_validate(obj)` trên từng dòng, nên muốn có số
#  đó phải hoặc thêm một property truy vấn DB (một câu đếm cho MỖI dòng danh
#  sách — đúng khuôn N+1), hoặc viết tay lại cả bộ CRUD cho một con số. Người
#  dùng vẫn biết trước khi mất dữ liệu: chốt `before_delete` đếm và nói rõ
#  «đang có N hồ sơ giữ chức vụ này».
