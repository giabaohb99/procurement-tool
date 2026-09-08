from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.status_codes import EMPLOYEE_STATUS

from .constants import (EDUCATION_LEVEL_LABELS, EMPLOYMENT_TYPE_LABELS,
                        GENDER_VALUES, JOB_LEVEL_LABELS, MARITAL_STATUS_LABELS,
                        MAX_EXTRA_FIELDS, RELATION_LABELS)
from .field_limits import (MAX_PEOPLE_ROWS, ProfileDate, Str20, Str25, Str50,
                           Str100, Str255, Str500, check_extra_fields,
                           check_resign_after_hire)

#  Bí danh của `datetime.date` — cùng lý do với `schema.DateOnly` của Nghỉ phép:
#  lớp nào có trường tên là `date` thì tên đó che mất kiểu. Ở đây chưa có trường
#  nào tên vậy, nhưng giữ một tên rõ ràng cho các cột ngày thì đọc dễ hơn.
#
#  ⚠️ Từ duoc-CR-316 nó KÈM RÀNG BUỘC DẢI NĂM (`ProfileDate`, 1900..2200). Mọi
#  ô ngày của hồ sơ đi qua bí danh này, nên không có chỗ nào lọt: MySQL nhận tới
#  năm 9999, mà `hire_date` năm 0001 là hai nghìn năm thâm niên — một số ngày
#  phép mà không dòng mã nào coi là vô lý.
DateOnly = ProfileDate


class EmployeeBase(BaseModel):
    #  ⚠️ Bí danh `Str<n>` = `max_length=n` khớp ĐÚNG `String(n)` ở `model.py`.
    #  Thiếu nó thì chuỗi dài đi thẳng xuống cột và MySQL là chỗ đầu tiên phản
    #  đối — người dùng nhận 500 «lỗi không lường trước» thay vì câu «tối đa n
    #  ký tự». Lỗ hổng này có ở CẢ trường cũ (từ trước duoc-CR-314), vá luôn.
    code: Str25 = ""
    full_name: Str255
    email: Str255 = ""
    phone: Str25 = ""
    company_id: int = 0
    department_id: int = 0
    #  ⚠️ `position` là NHÃN, `position_id` là thứ giao diện GỬI LÊN
    #  (duoc-CR-320). Giữ cả hai trong schema vì đường CSV và seed vẫn ghi chữ
    #  thẳng; nhưng khi lần lưu có `position_id` thì nhãn bị `position_service`
    #  ghi đè — gửi kèm một chuỗi khác là nó bị bỏ, đúng như mong muốn.
    position: Str100 = ""
    position_id: int = 0
    role_name: Str100 = ""
    status: Str50 = "official"      # B-03: MÃ, xem `EMPLOYEE_STATUS`
    is_active: bool = True

    #  ⚠️ QĐ-NP3 — hai cột này có trong bảng từ 03/09/2026 nhưng **không nằm
    #  trong schema nào cho tới 07/09/2026**, nên API không nhận cũng không trả:
    #  cả hai luật nghỉ phép dựa vào chúng đều im lặng không chạy.
    #
    #  · `hire_date` là mốc tính THÂM NIÊN. Rỗng thì `balance_service` coi là
    #    0 năm, tức mọi người mất phần ngày phép cộng thêm mà không ai báo.
    #  · `gender` để chặn loại nghỉ theo giới (thai sản). `0` = chưa khai, và
    #    chưa khai thì KHÔNG bị chặn — nên khi không ô nào khai được, chốt giới
    #    tính coi như không tồn tại.
    #
    #  Cả hai đều để trống được: hồ sơ cũ chưa ai nhập, và chặn thì cả công ty
    #  không sửa nổi hồ sơ cho tới khi Nhân sự nhập bù hàng trăm dòng (D-018).
    hire_date: DateOnly | None = None
    gender: int = 0

    @field_validator("gender", mode="before")
    @classmethod
    def _gender_none_is_unknown(cls, v):
        """`NULL` trong cột → `0` (chưa khai), đừng để nó nổ ở tầng đọc.

        Cột khai `default=0` nhưng đó là mặc định lúc INSERT: bản ghi dựng trong
        bộ nhớ mà chưa flush vẫn mang `None`, và dòng cũ có trước cột này cũng
        có thể `NULL`. Ném ở đây thì **cả màn danh sách nhân sự** trả 500 vì một
        ô chưa ai nhập — đắt hơn nhiều so với việc đọc nó thành «chưa khai».
        """
        return 0 if v is None else v

    # ── HỒ SƠ MỞ RỘNG (08/09/2026) ──────────────────────────────────────────
    #  Mọi trường đều CÓ MẶC ĐỊNH, không trường nào bắt buộc ở tầng schema. Bản
    #  giao diện cũ (`frontend/`, đang đóng băng) gửi PATCH thiếu hết đám này —
    #  bắt buộc một ô là màn hồ sơ ở bản đang chạy thật gãy ngay lúc deploy.
    #  Ô nào bắt buộc thì bắt ở tầng FORM của `frontend-v2`.

    # Nhóm 1 — cá nhân
    date_of_birth: DateOnly | None = None
    place_of_birth: Str255 = ""
    ethnicity: Str50 = ""
    religion: Str50 = ""
    marital_status: int = 0
    children_count: int = 0
    personal_email: Str255 = ""
    tax_code: Str20 = ""
    education_level: int = 0
    major: Str255 = ""

    # Nhóm 2 — công việc
    manager_id: int = 0
    employment_type: int = 0
    job_level: int = 0
    work_location: Str255 = ""
    resign_date: DateOnly | None = None

    # Nhóm 3 — liên hệ
    permanent_address: Str500 = ""
    current_address: Str500 = ""

    # Nhóm 4 — ngân hàng
    bank_account_no: Str50 = ""
    bank_account_name: Str255 = ""
    bank_name: Str100 = ""
    bank_branch: Str255 = ""

    # Nhóm 5 — giấy tờ, BHXH/BHYT
    id_number: Str20 = ""
    id_issue_date: DateOnly | None = None
    id_issue_place: Str255 = ""
    id_expiry_date: DateOnly | None = None
    #  Hai ảnh CCCD đi qua cửa upload riêng (`POST /employees/{id}/id-image`),
    #  KHÔNG nhận đường dẫn gõ tay từ client: nhận chuỗi tự do là để người ta trỏ
    #  ô này vào một URL bất kỳ, và bản in hồ sơ sẽ ngoan ngoãn tải về.
    id_front_image: Str500 = ""
    id_back_image: Str500 = ""
    social_insurance_no: Str20 = ""
    health_care_place: Str255 = ""
    health_care_code: Str20 = ""

    # Nhóm 7 — tùy biến
    extra_fields: dict = {}

    @field_validator("extra_fields", mode="before")
    @classmethod
    def _extra_fields_none_is_empty(cls, v):
        """Cột `NULL` (hàng trăm dòng có trước cột này) → `{}`, đừng để nổ."""
        return {} if v is None else v

    #  ⚠️ Cùng bài học với `_gender_none_is_unknown` phía trên, lần này là 26 cột
    #  một lúc: `default=""` / `default=0` trên model là mặc định lúc INSERT,
    #  KHÔNG phải lúc dựng đối tượng. Một `Employee(code=..., full_name=...)`
    #  chưa flush mang `None` ở mọi cột không truyền vào — mà đó chính là cách
    #  hàng chục bài test và vài đường nhập liệu đang dựng bản ghi.
    #
    #  Thiếu hai hàm này thì `EmployeeOut.model_validate(...)` ném 26 lỗi cùng
    #  lúc, và triệu chứng ở chạy thật là **cả màn danh sách nhân sự trả 500**
    #  vì một ô chưa ai nhập. Đọc `None` thành «chưa khai» rẻ hơn nhiều.
    _NONE_TO_BLANK_TEXT = (
        "place_of_birth", "ethnicity", "religion", "personal_email", "tax_code", "major",
        "work_location", "permanent_address", "current_address",
        "bank_account_no", "bank_account_name", "bank_name", "bank_branch",
        "id_number", "id_issue_place", "id_front_image", "id_back_image",
        "social_insurance_no", "health_care_place", "health_care_code",
    )
    _NONE_TO_ZERO_CODE = (
        "marital_status", "children_count", "education_level",
        "employment_type", "job_level", "manager_id",
        #  Cột mới của duoc-CR-320 — cùng bẫy: hàng trăm hồ sơ có trước cột này
        #  mang `NULL`, và một `None` ở đây là **cả màn danh sách nhân sự trả
        #  500**, không phải một ô trống.
        "position_id",
    )

    @field_validator(*_NONE_TO_BLANK_TEXT, mode="before")
    @classmethod
    def _text_none_is_blank(cls, v):
        return "" if v is None else v

    @field_validator(*_NONE_TO_ZERO_CODE, mode="before")
    @classmethod
    def _code_none_is_unknown(cls, v):
        return 0 if v is None else v


def _check_code_value(v: int | None, labels: dict[int, str], field: str) -> int | None:
    """Mã số phải nằm trong bộ mã đã khai — dùng chung cho cả Create lẫn Update.

    Chặn ở đây chứ không để `SMALLINT` nhận bừa: giá trị lạ thì `label_of` trả
    rỗng, và màn hình hiện một ô trắng mà không ai giải thích được vì sao. Cùng
    lý lẽ với `_check_gender` (B-03) — chỉ khác là ở đây gom một hàm cho bốn ô,
    vì chép bốn bản thì bốn bản trôi khỏi nhau.
    """
    if v is None:
        return None
    if int(v) not in labels:
        allowed = " / ".join(f"{k}" for k in labels)
        raise ValueError(f"{field} chỉ nhận: {allowed}")
    return int(v)


def _check_gender_value(v: int) -> int:
    """Giới tính chỉ nhận `GENDER_VALUES` — một hàm cho cả ba schema.

    Ba bản chép rời trước đây (Create · Update · thành viên hộ gia đình) là ba
    chỗ phải nhớ sửa mỗi lần bộ mã đổi; thêm mã `3` («Khác») lộ ra ngay điều đó.
    """
    if int(v) not in GENDER_VALUES:
        raise ValueError(
            "Giới tính chỉ nhận 0 (chưa khai), 1 (nam), 2 (nữ) hoặc 3 (khác)"
        )
    return int(v)


def _check_extra_fields(v: dict | None) -> dict:
    """Ràng buộc ô JSON tùy biến — bốn chiều, xem `field_limits`.

    Trần SỐ KHÓA một mình không cứu được gì: 20 khóa × 2MB = 40MB một hồ sơ, và
    MySQL nhận hết. Phải chặn cả độ dài khóa, độ dài giá trị, tổng kích thước,
    và cấm giá trị lồng nhau.
    """
    return check_extra_fields(v, MAX_EXTRA_FIELDS)


class EmployeeCreate(EmployeeBase):
    # Chặn ở CẢ Create lẫn Update. Chỉ chặn một bên thì màn còn lại vẫn ghi chữ tự do vào
    # lại cột, và cột lại đẻ giá trị lạ đúng như trước B-03.
    #
    # Cố ý KHÔNG nhận "Chính thức" rồi âm thầm đổi thành `official`: dịch hộ thì bản giao
    # diện chưa vá vẫn chạy được và sẽ không ai vá nữa. Thà 422 ngay lúc deploy.
    # (Đường CSV nhập từ tệp người dùng là ngoại lệ có chủ đích — nó dịch, xem controller.)
    #
    # `allow_blank=False`: khác `legal_type` của NCC (rỗng = chưa chọn, và là tình trạng của
    # gần hết dữ liệu thật), nhân sự thì LUÔN có tình trạng làm việc — rỗng không mang nghĩa gì.
    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str) -> str:
        return EMPLOYEE_STATUS.validate(v, allow_blank=False)

    @field_validator("gender")
    @classmethod
    def _check_gender(cls, v: int) -> int:
        return _check_gender_value(v)

    @field_validator("marital_status")
    @classmethod
    def _check_marital(cls, v: int) -> int:
        return _check_code_value(v, MARITAL_STATUS_LABELS, "Tình trạng hôn nhân")

    @field_validator("education_level")
    @classmethod
    def _check_education(cls, v: int) -> int:
        return _check_code_value(v, EDUCATION_LEVEL_LABELS, "Trình độ học vấn")

    @field_validator("employment_type")
    @classmethod
    def _check_employment(cls, v: int) -> int:
        return _check_code_value(v, EMPLOYMENT_TYPE_LABELS, "Hình thức nhân viên")

    @field_validator("job_level")
    @classmethod
    def _check_job_level(cls, v: int) -> int:
        return _check_code_value(v, JOB_LEVEL_LABELS, "Cấp bậc")

    @field_validator("extra_fields")
    @classmethod
    def _check_extra(cls, v: dict) -> dict:
        return _check_extra_fields(v)

    @field_validator("children_count")
    @classmethod
    def _check_children(cls, v: int) -> int:
        if v < 0 or v > 30:
            raise ValueError("Số con nhận từ 0 đến 30")
        return v

    #  Nghỉ việc không thể TRƯỚC ngày vào làm. Xem `check_resign_after_hire`
    #  để biết vì sao chốt này chỉ bắt được ca gửi CẢ HAI ô cùng lúc.
    @model_validator(mode="after")
    def _check_resign_after_hire(self):
        check_resign_after_hire(self.hire_date, self.resign_date)
        return self


class EmployeeUpdate(BaseModel):
    full_name: Str255 | None = None
    email: Str255 | None = None
    phone: Str25 | None = None
    company_id: int | None = None
    department_id: int | None = None
    position: Str100 | None = None
    position_id: int | None = None
    role_name: Str100 | None = None
    status: Str50 | None = None
    is_active: bool | None = None
    #  `None` = không gửi (giữ nguyên). Muốn XÓA ngày vào làm thì gửi `null`
    #  tường minh — Pydantic phân biệt được hai thứ đó qua `exclude_unset`.
    hire_date: DateOnly | None = None
    gender: int | None = None

    #  ⚠️ Cùng luật `None` = KHÔNG GỬI với `hire_date` ở trên. `exclude_unset`
    #  trong `update_employee` mới là thứ phân biệt "không gửi" với "gửi null để
    #  xóa" — đừng đổi sang `model_dump()` trần, làm vậy là mỗi lần lưu hồ sơ từ
    #  một form chỉ có 10 ô sẽ xóa trắng 30 ô còn lại.
    date_of_birth: DateOnly | None = None
    place_of_birth: Str255 | None = None
    ethnicity: Str50 | None = None
    religion: Str50 | None = None
    marital_status: int | None = None
    children_count: int | None = None
    personal_email: Str255 | None = None
    tax_code: Str20 | None = None
    education_level: int | None = None
    major: Str255 | None = None

    manager_id: int | None = None
    employment_type: int | None = None
    job_level: int | None = None
    work_location: Str255 | None = None
    resign_date: DateOnly | None = None

    permanent_address: Str500 | None = None
    current_address: Str500 | None = None

    bank_account_no: Str50 | None = None
    bank_account_name: Str255 | None = None
    bank_name: Str100 | None = None
    bank_branch: Str255 | None = None

    id_number: Str20 | None = None
    id_issue_date: DateOnly | None = None
    id_issue_place: Str255 | None = None
    id_expiry_date: DateOnly | None = None
    social_insurance_no: Str20 | None = None
    health_care_place: Str255 | None = None
    health_care_code: Str20 | None = None

    extra_fields: dict | None = None

    #  ⚠️ `id_front_image` / `id_back_image` CỐ Ý KHÔNG có ở đây — hai ô ảnh chỉ
    #  đặt được qua cửa upload (`POST /employees/{id}/id-image`). Cho PATCH ghi
    #  thẳng là cho client trỏ ô ảnh CCCD vào một URL ngoài, và mọi màn hình lẫn
    #  bản in sẽ tải nó về hộ.

    @field_validator("marital_status")
    @classmethod
    def _check_marital(cls, v: int | None) -> int | None:
        return _check_code_value(v, MARITAL_STATUS_LABELS, "Tình trạng hôn nhân")

    @field_validator("education_level")
    @classmethod
    def _check_education(cls, v: int | None) -> int | None:
        return _check_code_value(v, EDUCATION_LEVEL_LABELS, "Trình độ học vấn")

    @field_validator("employment_type")
    @classmethod
    def _check_employment(cls, v: int | None) -> int | None:
        return _check_code_value(v, EMPLOYMENT_TYPE_LABELS, "Hình thức nhân viên")

    @field_validator("job_level")
    @classmethod
    def _check_job_level(cls, v: int | None) -> int | None:
        return _check_code_value(v, JOB_LEVEL_LABELS, "Cấp bậc")

    @field_validator("extra_fields")
    @classmethod
    def _check_extra(cls, v: dict | None) -> dict | None:
        return None if v is None else _check_extra_fields(v)

    @field_validator("children_count")
    @classmethod
    def _check_children(cls, v: int | None) -> int | None:
        if v is not None and (v < 0 or v > 30):
            raise ValueError("Số con nhận từ 0 đến 30")
        return v

    @field_validator("gender")
    @classmethod
    def _check_gender(cls, v: int | None) -> int | None:
        """`0` chưa khai · `1` nam · `2` nữ · `3` khác — xem `constants.GENDER_*`.

        Chặn ở đây chứ không để cột `SMALLINT` nhận bừa: giá trị lạ thì
        `check_gender` của nghỉ phép so `want != got` ra True và chặn nhầm loại
        nghỉ, mà không chỗ nào giải thích được vì sao.
        """
        return v if v is None else _check_gender_value(v)

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str | None) -> str | None:
        # `None` = không gửi trường này (PATCH), cho qua. Nhưng `""` là CÓ gửi và gửi rỗng:
        # hồ sơ mang giá trị cũ ngoài bộ mã thì ô chọn không khớp mục nào, để rỗng lọt qua là
        # bấm lưu xong xóa trắng trạng thái thật của một con người mà không ai biết.
        if v is None:
            return None
        return EMPLOYEE_STATUS.validate(v, allow_blank=False)

    #  Nghỉ việc không thể TRƯỚC ngày vào làm. Xem `check_resign_after_hire`
    #  để biết vì sao chốt này chỉ bắt được ca gửi CẢ HAI ô cùng lúc.
    @model_validator(mode="after")
    def _check_resign_after_hire(self):
        check_resign_after_hire(self.hire_date, self.resign_date)
        return self


class EmployeeOut(EmployeeBase):
    id: int
    code: str
    # B-03: nhãn tiếng Việt gửi kèm để giao diện khỏi khai lại bảng mã bằng tay.
    # Đọc từ `Employee.status_label` (property trên model).
    status_label: str = ""
    department_name: str | None = None
    #  Pháp nhân của nhân sự. Đọc từ property `Employee.company_name`; danh sách
    #  phải `selectinload(Employee.company)` — xem `service.list_employees` — nếu
    #  không mỗi dòng tự lazy-load thành N+1.
    company_name: str | None = None
    manager_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None   # bao-CR-294 — cột "Ngày cập nhật" ở màn danh sách
    # Ảnh đại diện lấy từ tài khoản đăng nhập (tab_user.avatar). Danh sách phải
    # selectinload(Employee.user) — xem service.list_employees — để không thành N+1.
    avatar: str = ""
    # Ảnh chữ ký cá nhân, cũng đọc từ tài khoản đăng nhập (tab_user.signature).
    signature: str = ""

    #  Nhãn tiếng Việt của bốn ô mã số — gửi kèm để giao diện khỏi khai lại bảng
    #  mã bằng tay, đúng lối `status_label` của B-03. Đọc từ property trên model.
    marital_status_label: str = ""
    education_level_label: str = ""
    employment_type_label: str = ""
    job_level_label: str = ""
    #  Tên người quản lý TRỰC TIẾP (`manager_id`). ⚠️ Khác `manager_name` phía
    #  trên — cái đó là trưởng PHÒNG BAN. Danh sách phải
    #  `selectinload(Employee.direct_manager)`, không thì mỗi dòng một truy vấn.
    direct_manager_name: str = ""

    model_config = {"from_attributes": True}


class EmployeeDetailOut(EmployeeOut):
    """Bản dùng cho MÀN CHI TIẾT — kèm id tài khoản đăng nhập để biết đã cấp tài khoản chưa."""

    user_id: int = 0


# ── Hai bảng con của hồ sơ (xem `contact_model.py`) ─────────────────────────
#  Không có `Create`/`Update` riêng cho từng dòng: cả bảng đặt lại MỘT LƯỢT bằng
#  `PUT`, giống `set_employee_departments`. Sửa từng dòng thì phải nuôi thêm id
#  tạm ở tầng giao diện cho dòng chưa lưu, mà đây là bảng ba–bốn dòng nằm trong
#  một tab — người dùng bấm Lưu của cả hồ sơ, không bấm Lưu của từng dòng.

class EmployeeContactIn(BaseModel):
    #  Độ dài khớp `contact_model.EmployeeContact`. Bảng con đi cửa API riêng
    #  nên có schema riêng — đúng chỗ dễ quên khai giới hạn nhất.
    full_name: Str255 = ""
    #  MÃ SỐ (`RELATION_LABELS`), không phải chữ. Xem `contact_model`.
    relation: int = 0
    address: Str500 = ""
    phone: Str25 = ""

    @field_validator("relation")
    @classmethod
    def _check_relation(cls, v: int) -> int:
        return _check_code_value(v, RELATION_LABELS, "Quan hệ")


class EmployeeContactOut(EmployeeContactIn):
    id: int
    sort_order: int = 0
    model_config = {"from_attributes": True}


class EmployeeFamilyIn(BaseModel):
    full_name: Str255 = ""
    relation: int = 0
    gender: int = 0

    @field_validator("relation")
    @classmethod
    def _check_relation(cls, v: int) -> int:
        return _check_code_value(v, RELATION_LABELS, "Quan hệ")
    date_of_birth: DateOnly | None = None
    phone: Str25 = ""
    id_number: Str20 = ""

    @field_validator("gender")
    @classmethod
    def _check_gender(cls, v: int) -> int:
        # Cùng quy ước với `Employee.gender` — 0 chưa khai · 1 nam · 2 nữ · 3 khác.
        return _check_gender_value(v)


class EmployeeFamilyOut(EmployeeFamilyIn):
    id: int
    sort_order: int = 0
    model_config = {"from_attributes": True}


#  ⚠️ TRẦN SỐ DÒNG. Không có nó thì `PUT` 5000 dòng lọt thẳng — đã thử được
#  trên MySQL thật ngày 08/09/2026. Đây là bảng «cha, mẹ, vợ/chồng» nằm trong
#  một tab, vài chục dòng đã vô lý; và `sort_order` là `SMALLINT` nên dòng thứ
#  32768 còn tràn kiểu. Trần đặt ở SCHEMA chứ không ở service: chặn trước khi
#  xóa sạch bảng cũ, kẻo một lần gửi hỏng là mất luôn dữ liệu đang có.
class EmployeeContactsIn(BaseModel):
    """Đặt lại TOÀN BỘ danh sách người báo tin của một hồ sơ."""

    items: list[EmployeeContactIn] = Field(default_factory=list, max_length=MAX_PEOPLE_ROWS)


class EmployeeFamiliesIn(BaseModel):
    """Đặt lại TOÀN BỘ danh sách thành viên hộ gia đình của một hồ sơ."""

    items: list[EmployeeFamilyIn] = Field(default_factory=list, max_length=MAX_PEOPLE_ROWS)
