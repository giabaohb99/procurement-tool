"""Schema của DANH MỤC LOẠI HỒ SƠ — xem `type_model.py`.

⚠️ Mọi ô chuỗi khai `max_length` khớp ĐÚNG `String(n)` ở model, và ô số khai
dải. Bài học duoc-CR-316: thiếu khai thì chuỗi dài / số khổng lồ đi thẳng xuống
MySQL và người dùng nhận «mã sự cố» thay vì câu *«tối đa n ký tự»*.

⚠️ **SQLite của bộ test KHÔNG ép độ dài `VARCHAR`**, nên bài kiểm nào ghi xuống
DB rồi khẳng định là xanh giả — phải kiểm thẳng ở tầng schema
(`pytest.raises(ValidationError)`). Xem `test/backend/test_loai_ho_so.py`.
"""
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator

from .field_schema import validate_field_schema

#  Bí danh đặt theo CON SỐ để nơi dùng đối chiếu thẳng được với `String(n)` ở
#  model. Khai tại chỗ chứ không mượn `employee/field_limits.py`: bí danh bên đó
#  thuộc về hồ sơ nhân sự, kéo sang đây là hai module dính nhau vì một dòng
#  `Annotated`.
Str30 = Annotated[str, StringConstraints(max_length=30)]
Str100 = Annotated[str, StringConstraints(max_length=100)]
Str500 = Annotated[str, StringConstraints(max_length=500)]

#  Trần 1200 tháng = 100 năm. Không có thứ giấy tờ nào hiệu lực lâu hơn thế, mà
#  bỏ trần thì một lần gõ nhầm ra `999999` là cột `SMALLINT` tràn và MySQL nổ.
ValidMonths = Annotated[int, Field(ge=0, le=1200)]
#  `sort_order` nằm dưới DB nhưng không lên giao diện — vẫn phải chặn tràn
#  `Integer`, và trần 32767 là chỗ `SMALLINT` của các danh mục khác vỡ.
SortOrder = Annotated[int, Field(ge=0, le=32767)]


def _require_text(value: str, field: str) -> str:
    """Cắt khoảng trắng thừa và chặn ô rỗng.

    Một dòng tên rỗng thì ô chọn loại hồ sơ hiện một mục trắng không bấm trúng.
    """
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field} không được để trống")
    return text


class DossierTypeCreate(BaseModel):
    #  ⚠️ `code` BẮT BUỘC ở đây, và controller CỐ Ý không khai `code_prefix`:
    #  loại hồ sơ có mã nói lên nghĩa (`HD`, `GP`, `ATLD`) chứ không phải số thứ
    #  tự, nên để máy cấp `lhs001` là đẻ ra một danh mục không ai đọc được. Giao
    #  diện cũng bắt buộc ô này — hai phía phải nói cùng một luật, kẻo lặp lại
    #  lỗi của Chức vụ: câu gợi ý hứa «bỏ trống thì tự sinh» trong khi schema
    #  chặn rỗng trước đó.
    code: Str30
    name: Str100
    description: Str500 = ""
    default_valid_months: ValidMonths = 0
    is_active: bool = True
    sort_order: SortOrder = 0
    #  BỘ TRƯỜNG TÙY BIẾN của loại này — xem `field_schema.py`. Để rỗng là hợp
    #  lệ: nhiều loại giấy tờ chỉ cần mã, tên, hạn.
    field_schema: list = []

    @field_validator("field_schema")
    @classmethod
    def _check_schema(cls, v: list) -> list:
        return validate_field_schema(v)

    @field_validator("code")
    @classmethod
    def _code_uppercase(cls, v: str) -> str:
        """Mã loại hồ sơ luôn CHỮ HOA.

        Ép ở tầng schema chứ không ở giao diện, vì mã còn vào hệ qua đường nhập
        CSV và qua bất kỳ ai gọi thẳng API — vá mỗi ô nhập thì hai đường kia vẫn
        đẻ ra mã thường.

        Nó cũng chữa một chỗ lệch có sẵn: chốt trùng mã của bộ sinh CRUD so bằng
        `==`, mà MySQL đối chiếu **không phân biệt hoa thường** còn SQLite của bộ
        test thì **có** — nên `hd` và `HD` là một dòng trên chạy thật nhưng là
        hai dòng trong test. Chuẩn hóa về một dạng thì hai nơi nói giống nhau.
        """
        return _require_text(v, "Mã loại hồ sơ").upper()

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, v: str) -> str:
        return _require_text(v, "Tên loại hồ sơ")


class DossierTypeUpdate(BaseModel):
    #  ⚠️ `code` KHÔNG sửa được — cùng lý lẽ với mã chức vụ và mã phòng họp: mã
    #  là thứ tệp CSV và các màn khác dùng để trỏ tới dòng này.
    name: Str100 | None = None
    description: Str500 | None = None
    default_valid_months: ValidMonths | None = None
    is_active: bool | None = None
    sort_order: SortOrder | None = None
    field_schema: list | None = None

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, v: str | None) -> str | None:
        return None if v is None else _require_text(v, "Tên loại hồ sơ")

    @field_validator("field_schema")
    @classmethod
    def _check_schema(cls, v: list | None) -> list | None:
        return None if v is None else validate_field_schema(v)


class DossierTypeResponse(BaseModel):
    id: int
    code: str = ""
    name: str = ""
    description: str = ""
    default_valid_months: int = 0
    is_active: bool = True
    sort_order: int = 0
    #  Đọc qua thuộc tính `field_defs` của model, KHÔNG đọc thẳng cột: cột có thể
    #  đang `NULL` với loại khai từ trước khi có bộ trường, mà `None` ra tới
    #  TypeScript là mọi chỗ dùng phải tự `?? []`.
    field_schema: list = Field(default_factory=list, validation_alias="field_defs")
    #  Số ô tùy biến — bày thành một cột của bảng danh mục, để nhìn danh sách là
    #  biết loại nào đã khai khuôn biểu mẫu, loại nào còn trống.
    field_count: int = 0

    model_config = {"from_attributes": True, "populate_by_name": True}
