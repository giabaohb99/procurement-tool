"""HỒ SƠ — `tab_dossier` (phân hệ Hồ sơ, 16/09/2026).

Một dòng = một bộ giấy tờ công ty đang giữ: giấy phép con, hợp đồng nguyên tắc,
chứng nhận kiểm định… Phần khung (mã · tên · loại · nơi giữ · hạn hiệu lực) là
CỘT THẬT; phần riêng của từng loại nằm trong ô JSON `extra_fields`, khai ở
`tab_dossier_type.field_schema`.

⚠️ **Ranh giới cột thật / ô JSON là quyết định phải giữ.** Cột thật thì lọc,
sắp xếp, báo cáo và đánh chỉ mục được; ô JSON thì không thứ nào trong số đó. Mọi
trường ở đây đều có mặt vì **mọi loại hồ sơ đều có nó** — thứ chỉ vài loại cần
thì khai vào bộ trường tùy biến. Ngược lại, nhu cầu nào lặp lại ở mọi loại thì
phải kéo lên thành cột, đừng để nó sống mãi dưới JSON (xem `field_schema.py`).
"""
from datetime import date

from sqlalchemy import JSON, BigInteger, Date, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import AuditMixin, Base

from .constants import (DOSSIER_DRAFT, DOSSIER_STATUS_LABELS,
                        EXPIRY_STATE_LABELS)
from .expiry import expiry_state as calc_expiry_state


class Dossier(Base, AuditMixin):
    """Một bộ hồ sơ."""

    __tablename__ = "tab_dossier"

    #  Máy tự cấp `HS0001`, `HS0002`… khi người dùng bỏ trống (`code_prefix` của
    #  bộ sinh CRUD). Vẫn cho gõ đè, vì nhiều bộ giấy tờ đã có sẵn số hiệu in
    #  trên bìa và bắt đặt lại mã là hai hệ thống đánh số cho cùng một thứ.
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(200))

    #  ---- Loại hồ sơ: HAI CỘT CHO MỘT SỰ THẬT, cố ý (bài học duoc-CR-320) ----
    #  `dossier_type_id` là khóa; `dossier_type_name` là NHÃN ĐÃ CHÉP. Giữ cột
    #  chữ vì bản in, tệp Excel và `core/audit` đọc thẳng nó — nối bảng lúc in ra
    #  một tờ giấy là thêm một đường vỡ ở đúng lúc không ai sửa được.
    #
    #  ⚠️ Toàn hệ chỉ có HAI đường ghi vào cột nhãn, cả hai ở `service.py`:
    #  `sync_type_label` (lưu hồ sơ) và `propagate_type_rename` (đổi tên trong
    #  danh mục). Thêm đường thứ ba là nhãn trôi, và bản in đưa cho cơ quan nhà
    #  nước ra tên loại cũ trong khi màn hình hiện tên mới.
    dossier_type_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    dossier_type_name: Mapped[str] = mapped_column(String(100), default="")

    #  Vòng đời do NGƯỜI đặt. «Hết hạn» KHÔNG nằm ở đây — nó suy ra từ
    #  `expiry_date`, xem ghi chú dài ở `constants.py`.
    status: Mapped[int] = mapped_column(SmallInteger, default=DOSSIER_DRAFT, index=True)

    #  Ngày cấp / ngày ký trên chính tờ giấy.
    issued_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    #  ⚠️ `NULL` = **vô thời hạn**, một câu trả lời thật (giấy chứng nhận đăng ký
    #  doanh nghiệp), không phải ô chưa ai nhập. Chỗ nào đọc cột này mà coi
    #  `NULL` là thiếu dữ liệu thì sẽ đi nhắc người dùng điền một thứ không tồn
    #  tại. Có chỉ mục vì màn danh sách sắp theo nó để trả lời câu hỏi thường
    #  gặp nhất của cả phân hệ: «cái nào sắp hết hạn?».
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    #  ---- Ba chiều PHẠM VI DỮ LIỆU ----
    #  Khai trong `SCOPE_FIELDS["dossier"]` bằng ĐÚNG ba cột này, nên chúng không
    #  phải trường bày cho đẹp: đổi tên hay bỏ cột nào là `apply_scope` mất một
    #  chiều lọc, im lặng. `0` = chưa gắn.
    owner_employee_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)

    #  Nơi giữ BẢN GIẤY — «Tủ A2 · P. Hành chính». Chuỗi tự do chứ không phải
    #  danh mục: mỗi công ty gọi chỗ cất giấy tờ một kiểu, và dựng một danh mục
    #  cho nó là bắt người dùng khai một cây thư mục trước khi lưu được tờ đầu tiên.
    storage_location: Mapped[str] = mapped_column(String(200), default="")
    note: Mapped[str] = mapped_column(String(1000), default="")

    #  Giá trị của BỘ TRƯỜNG TÙY BIẾN, khóa lấy từ `field_schema` của loại.
    #  `NULL` đọc ra `{}` (xem `extra_fields_map`) — hồ sơ lập trước khi loại có
    #  ô nào đều mang `NULL`, trả `None` ra API thì mọi chỗ dùng phải tự `or {}`
    #  và chỗ nào quên thì nổ `NoneType` đúng lúc mở một hồ sơ cũ.
    extra_fields: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    #  ---- Quan hệ CHỈ ĐỌC để bày tên ----
    #  ⚠️ `lazy="joined"` là bắt buộc, không phải tinh chỉnh. Bộ sinh CRUD gọi
    #  serializer cho TỪNG dòng; để mặc định `lazy="select"` thì một trang 50
    #  dòng bắn 150 truy vấn phụ chỉ để lấy ba cái tên (đúng bài N+1 của
    #  duoc-CR-322). `joined` gộp hết vào một câu lệnh.
    #
    #  Ba cái tên này CỐ Ý không chép thành cột như `dossier_type_name`: hồ sơ
    #  nhân sự và danh mục phòng ban đã có đường xử lý đổi tên của riêng chúng,
    #  chép thêm ở đây là dựng ba nguồn sự thật nữa phải đồng bộ.
    owner = relationship(
        "Employee",
        primaryjoin="foreign(Dossier.owner_employee_id) == Employee.id",
        uselist=False, viewonly=True, lazy="joined",
    )
    department = relationship(
        "Department",
        primaryjoin="foreign(Dossier.department_id) == Department.id",
        uselist=False, viewonly=True, lazy="joined",
    )
    company = relationship(
        "Company",
        primaryjoin="foreign(Dossier.company_id) == Company.id",
        uselist=False, viewonly=True, lazy="joined",
    )

    @property
    def extra_fields_map(self) -> dict:
        """`extra_fields` luôn đọc ra một dict, kể cả khi cột đang `NULL`."""
        return self.extra_fields if isinstance(self.extra_fields, dict) else {}

    @property
    def owner_name(self) -> str:
        return self.owner.name if self.owner else ""

    @property
    def department_name(self) -> str:
        return self.department.name if self.department else ""

    @property
    def company_name(self) -> str:
        return self.company.name if self.company else ""

    #  ---- Nhãn: đọc ở ĐÂY chứ không ở schema ----
    #  ⚠️ Xuất CSV lấy giá trị bằng `getattr(item, field)` trên chính đối tượng
    #  ORM (`core/csv_utils.export_csv_response`), **không** đi qua phong bì API.
    #  Khai mấy nhãn này thành `computed_field` của Pydantic thì tệp Excel xuất
    #  ra có cột «Tình trạng» rỗng trơn ở mọi dòng — không lỗi, không cảnh báo.
    @property
    def status_label(self) -> str:
        return DOSSIER_STATUS_LABELS.get(self.status, "")

    @property
    def expiry_state(self) -> int:
        return calc_expiry_state(self.expiry_date)[0]

    @property
    def expiry_state_label(self) -> str:
        return EXPIRY_STATE_LABELS.get(self.expiry_state, "")

    @property
    def expiry_days(self) -> int | None:
        """Số ngày còn lại; âm = đã quá hạn; `None` = vô thời hạn."""
        return calc_expiry_state(self.expiry_date)[1]
