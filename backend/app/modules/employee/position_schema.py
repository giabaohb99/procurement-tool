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

    Một dòng tên rỗng thì ô chọn chức vụ hiện một mục trắng không bấm trúng.

    ⚠️ Chỉ áp cho `name`. `code` để trống được vì bộ sinh CRUD tự cấp mã — xem
    chú thích ở `JobPositionCreate`.
    """
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field} không được để trống")
    return text


class JobPositionCreate(BaseModel):
    #  ⚠️ `code` ĐỂ TRỐNG ĐƯỢC, và đó là đường đi bình thường: bộ sinh CRUD tự
    #  cấp `cv001`, `cv002`… khi ô này rỗng (`code_prefix="cv"` ở controller).
    #
    #  Trước 08/09/2026 ô này bắt buộc, nên câu gợi ý trên biểu mẫu — *«bỏ trống
    #  thì hệ thống tự sinh»* — là một **lời hứa chưa từng chạy**: schema chặn
    #  rỗng trước khi bộ sinh kịp cấp mã, người dùng làm đúng như chỉ dẫn thì ăn
    #  lỗi 422. Đừng thêm lại `_require_text` cho `code` nếu không đồng thời gỡ
    #  `code_prefix` và sửa câu gợi ý.
    code: Str30 = ""
    name: Str100
    is_active: bool = True
    sort_order: int = 0
    note: Str500 = ""
    department_id: int = 0

    @field_validator("name")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        return _require_text(v, "Tên chức vụ")

    @field_validator("code")
    @classmethod
    def _code_lowercase(cls, v: str) -> str:
        """Mã chức vụ luôn CHỮ THƯỜNG (khách chốt 08/09/2026).

        ⚠️ Ép ở tầng schema chứ không ở giao diện, vì mã còn vào hệ qua **đường
        nhập CSV** và qua bất kỳ ai gọi thẳng API — vá mỗi ô nhập thì hai đường
        kia vẫn đẻ ra mã hoa.

        Nó cũng chữa một chỗ lệch có sẵn: chốt trùng mã của bộ sinh CRUD so bằng
        `==`, mà MySQL đối chiếu **không phân biệt hoa thường** còn SQLite của bộ
        test thì **có** — nên `TP` và `tp` là một dòng trên chạy thật nhưng là
        hai dòng trong test. Chuẩn hóa về một dạng thì hai nơi nói giống nhau.
        """
        return v.strip().lower()


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
