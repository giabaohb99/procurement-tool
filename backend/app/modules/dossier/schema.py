"""Schema của HỒ SƠ — xem `model.py`.

⚠️ Mọi ô chuỗi khai `max_length` khớp ĐÚNG `String(n)` ở model, mọi ô số khai
dải, mọi ô ngày khai dải NĂM. Bài học duoc-CR-316: thiếu khai thì chuỗi dài /
ngày năm 0001 đi thẳng xuống MySQL và người dùng nhận «mã sự cố» thay vì câu
*«tối đa n ký tự»*.

⚠️ **SQLite của bộ test KHÔNG ép độ dài `VARCHAR`**, nên bài kiểm nào ghi xuống
DB rồi khẳng định là xanh giả — phải kiểm thẳng ở tầng schema
(`pytest.raises(ValidationError)`).
"""
from datetime import date
from typing import Annotated

from pydantic import (BaseModel, Field, StringConstraints, field_validator,
                      model_validator)

from .applicability import validate_conditions, validate_doc_kinds
from .constants import (DOSSIER_DRAFT, DOSSIER_STATUS_LABELS,
                        DOSSIER_STATUS_VALUES)
from .field_schema import validate_field_schema

Str30 = Annotated[str, StringConstraints(max_length=30)]
Str100 = Annotated[str, StringConstraints(max_length=100)]
Str200 = Annotated[str, StringConstraints(max_length=200)]
Str1000 = Annotated[str, StringConstraints(max_length=1000)]

#  MySQL `DATE` nhận tới năm 9999. Một tờ giấy phép thì không: gõ nhầm năm 9999
#  vào ô hạn hiệu lực là hồ sơ đó **không bao giờ vào danh sách sắp hết hạn**,
#  im lặng, và đó đúng là thứ cả phân hệ này sinh ra để theo dõi.
MIN_DOSSIER_YEAR = 1900
MAX_DOSSIER_YEAR = 2200
DossierDate = Annotated[
    date,
    Field(ge=date(MIN_DOSSIER_YEAR, 1, 1), le=date(MAX_DOSSIER_YEAR, 12, 31)),
]

#  `0` = chưa gắn. Trần chặn tràn `BigInteger` và chặn luôn mấy con số vô nghĩa
#  gõ nhầm từ bàn phím số.
RefId = Annotated[int, Field(ge=0, le=9_999_999_999)]
StatusCode = Annotated[int, Field(ge=0, le=32767)]


def _check_status(v: int) -> int:
    if v not in DOSSIER_STATUS_VALUES:
        raise ValueError(
            "Tình trạng hồ sơ không hợp lệ. Nhận: "
            + ", ".join(f"{k} ({DOSSIER_STATUS_LABELS[k]})" for k in DOSSIER_STATUS_VALUES)
        )
    return v


def _check_dates(issued: date | None, expiry: date | None) -> None:
    """Hạn hiệu lực không thể TRƯỚC ngày cấp.

    Cho phép BẰNG nhau — giấy cấp và hết hiệu lực trong cùng một ngày là chuyện
    có thật với giấy phép một lần.

    ⚠️ Chỉ so khi có ĐỦ CẢ HAI. `PATCH` sửa riêng ô hạn thì không có ngày cấp để
    so, và chặn lúc đó là chặn nhầm một thao tác hợp lệ. Đổi lại: sửa riêng một
    ô vẫn tạo ra được cặp ngược đời — chốt này bắt ca thường gặp, không bắt mọi
    ca (cùng lý lẽ với `check_resign_after_hire` của hồ sơ nhân sự).
    """
    if issued and expiry and expiry < issued:
        raise ValueError("Hạn hiệu lực không được trước ngày cấp")


class DossierCreate(BaseModel):
    #  ⚠️ Bỏ trống là CỐ Ý — bộ sinh CRUD cấp `HS0001` qua `code_prefix`. Khác
    #  hẳn danh mục Loại hồ sơ (ở đó `code` bắt buộc vì mã phải nói lên nghĩa):
    #  hồ sơ là chứng từ phát sinh hằng ngày, bắt nghĩ ra mã trước khi lưu được
    #  là dựng một rào chắn ngay cửa vào.
    code: Str30 = ""
    name: Str200
    dossier_type_id: RefId
    #  ⚠️ **Không phải ô người dùng khai** — `controller._before_create` ghi đè nó
    #  bằng tên đọc từ danh mục, luôn luôn. Có mặt ở đây chỉ vì bộ sinh CRUD dựng
    #  bản ghi bằng `Model(**data.model_dump())`, tức là không nhìn thấy trường
    #  nào nằm ngoài schema này.
    dossier_type_name: Str100 = ""
    status: StatusCode = DOSSIER_DRAFT
    issued_date: DossierDate | None = None
    expiry_date: DossierDate | None = None
    owner_employee_id: RefId = 0
    department_id: RefId = 0
    company_id: RefId = 0
    storage_location: Str200 = ""
    note: Str1000 = ""
    extra_fields: dict = {}
    #  TRƯỜNG RIÊNG của hồ sơ này — người lập tự khai tại chỗ. Cùng cấu trúc với
    #  `field_schema` của loại; giá trị đi chung vào `extra_fields`.
    custom_fields: list = []
    #  ĐIỀU KIỆN ÁP DỤNG — xem `applicability.py`. Mặc định RỖNG = hồ sơ không
    #  hiện ra ở chứng từ nào, đúng hành vi cũ của mọi hồ sơ đang có.
    apply_doc_kinds: list = []
    apply_conditions: list = []
    #  TIÊN QUYẾT — `id` các tờ phải hoàn thành trước tờ này. Vòng lặp và id
    #  không tồn tại thì chặn ở `controller._before_*` (cần `db` nên không kiểm
    #  được bằng validator của Pydantic).
    depends: list[int] = []

    @field_validator("custom_fields")
    @classmethod
    def _check_custom(cls, v: list) -> list:
        return validate_field_schema(v)

    @field_validator("apply_doc_kinds")
    @classmethod
    def _check_kinds(cls, v: list) -> list:
        return validate_doc_kinds(v)

    @field_validator("apply_conditions")
    @classmethod
    def _check_conditions(cls, v: list) -> list:
        return validate_conditions(v)

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, v: str) -> str:
        text = (v or "").strip()
        if not text:
            raise ValueError("Tên hồ sơ không được để trống")
        return text

    @field_validator("code")
    @classmethod
    def _code_uppercase(cls, v: str) -> str:
        #  Chuẩn hoá về CHỮ HOA vì chốt trùng mã của bộ sinh so bằng `==`, mà
        #  MySQL đối chiếu không phân biệt hoa thường còn SQLite của bộ test thì
        #  có — `hs001` và `HS001` là một dòng trên chạy thật nhưng hai dòng
        #  trong test. Cùng luật với `DossierTypeCreate`.
        return (v or "").strip().upper()

    @field_validator("dossier_type_id")
    @classmethod
    def _type_required(cls, v: int) -> int:
        #  Loại hồ sơ là thứ quyết định biểu mẫu có những ô nào — hồ sơ không có
        #  loại thì không có bộ trường nào để khai, và cũng không lọc ra được.
        if not v:
            raise ValueError("Hồ sơ phải thuộc một loại hồ sơ")
        return v

    @field_validator("status")
    @classmethod
    def _status_known(cls, v: int) -> int:
        return _check_status(v)

    @model_validator(mode="after")
    def _dates_in_order(self):
        _check_dates(self.issued_date, self.expiry_date)
        return self


class DossierUpdate(BaseModel):
    #  ⚠️ `code` KHÔNG sửa được sau khi tạo — cùng lý lẽ với mã loại hồ sơ: mã là
    #  thứ tệp Excel và các màn khác dùng để trỏ tới dòng này.
    name: Str200 | None = None
    dossier_type_id: RefId | None = None
    status: StatusCode | None = None
    issued_date: DossierDate | None = None
    expiry_date: DossierDate | None = None
    owner_employee_id: RefId | None = None
    department_id: RefId | None = None
    company_id: RefId | None = None
    storage_location: Str200 | None = None
    note: Str1000 | None = None
    extra_fields: dict | None = None
    custom_fields: list | None = None
    apply_doc_kinds: list | None = None
    apply_conditions: list | None = None
    depends: list[int] | None = None

    @field_validator("custom_fields")
    @classmethod
    def _check_custom(cls, v: list | None) -> list | None:
        return None if v is None else validate_field_schema(v)

    @field_validator("apply_doc_kinds")
    @classmethod
    def _check_kinds(cls, v: list | None) -> list | None:
        return None if v is None else validate_doc_kinds(v)

    @field_validator("apply_conditions")
    @classmethod
    def _check_conditions(cls, v: list | None) -> list | None:
        return None if v is None else validate_conditions(v)

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, v: str | None) -> str | None:
        if v is None:
            return None
        text = v.strip()
        if not text:
            raise ValueError("Tên hồ sơ không được để trống")
        return text

    @field_validator("dossier_type_id")
    @classmethod
    def _type_not_cleared(cls, v: int | None) -> int | None:
        if v is not None and not v:
            raise ValueError("Hồ sơ phải thuộc một loại hồ sơ")
        return v

    @field_validator("status")
    @classmethod
    def _status_known(cls, v: int | None) -> int | None:
        return None if v is None else _check_status(v)

    @model_validator(mode="after")
    def _dates_in_order(self):
        _check_dates(self.issued_date, self.expiry_date)
        return self


class DossierResponse(BaseModel):
    id: int
    code: str = ""
    name: str = ""
    dossier_type_id: int = 0
    dossier_type_name: str = ""
    status: int = DOSSIER_DRAFT
    issued_date: date | None = None
    expiry_date: date | None = None
    owner_employee_id: int = 0
    department_id: int = 0
    company_id: int = 0
    #  Ba cái tên đọc qua quan hệ `lazy="joined"` của model — không phải cột.
    owner_name: str = ""
    department_name: str = ""
    company_name: str = ""
    storage_location: str = ""
    note: str = ""
    extra_fields: dict = {}
    #  Đọc qua thuộc tính `custom_field_defs` của model, KHÔNG đọc thẳng cột:
    #  cột có thể đang `NULL` với hồ sơ lập trước khi có nó.
    custom_fields: list = Field(default_factory=list, validation_alias="custom_field_defs")
    #  Cũng đọc qua thuộc tính, cùng lý do: cột `NULL` với mọi hồ sơ lập trước
    #  21/09/2026, mà `None` ra API thì chỗ nào quên `?? []` sẽ nổ khi mở hồ sơ cũ.
    apply_doc_kinds: list = Field(default_factory=list,
                                  validation_alias="apply_doc_kind_list")
    apply_conditions: list = Field(default_factory=list,
                                   validation_alias="apply_condition_list")
    #  Cùng lý do cột `NULL`, đọc qua thuộc tính chứ không đọc thẳng cột.
    depends: list = Field(default_factory=list, validation_alias="depend_list")

    @field_validator("extra_fields", mode="before")
    @classmethod
    def _none_is_empty(cls, v):
        #  Cột `NULL` với hồ sơ lập trước khi loại khai ô nào. Trả `None` ra API
        #  thì mọi chỗ dùng phải tự `or {}`, và chỗ quên thì nổ đúng lúc ai đó
        #  mở một hồ sơ cũ — thứ chỉ lộ ra trên dữ liệu thật.
        return v if isinstance(v, dict) else {}

    #  ---- Bốn trường dưới SUY RA, không cột nào chứa chúng ----
    #  Đọc thẳng từ thuộc tính của model (`from_attributes`) chứ KHÔNG khai lại
    #  bằng `computed_field`: xuất CSV lấy giá trị trên chính đối tượng ORM, nên
    #  luật nằm ở schema thì tệp Excel ra cột rỗng. Một luật, một chỗ — xem
    #  `model.py` và `expiry.py`.
    status_label: str = ""
    expiry_state: int = 0
    expiry_state_label: str = ""
    #  Số ngày còn lại; âm = đã quá hạn; `None` = vô thời hạn (KHÁC `0`, vốn đọc
    #  ra «hết hạn hôm nay»).
    expiry_days: int | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}
