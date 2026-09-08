from datetime import date

from sqlalchemy import JSON, BigInteger, Boolean, Date, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import Base, AuditMixin
from app.core.status_codes import EMPLOYEE_STATUS

from .constants import (EDUCATION_LEVEL_LABELS, EMPLOYMENT_TYPE_LABELS,
                        JOB_LEVEL_LABELS, MARITAL_STATUS_LABELS, label_of)


class Employee(Base, AuditMixin):
    """Nhân viên — thuộc công ty & phòng ban; gắn với tài khoản qua tab_user.employee_id."""

    __tablename__ = "tab_employee"

    code: Mapped[str] = mapped_column(String(25), unique=True)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(25), default="")
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  ⚠️ `position` là NHÃN ĐÃ CHÉP từ danh mục, `position_id` mới là sự thật
    #  (duoc-CR-320). Giữ cột chữ vì mười chỗ đang đọc thẳng nó để in phiếu,
    #  xuất Excel và dựng hồ sơ cho trợ lý AI — và vì hồ sơ cũ chưa map vẫn phải
    #  giữ nguyên chữ người ta đã gõ. **Chỉ ghi vào cột này qua
    #  `position_service`**, hai đường: lưu hồ sơ và đổi tên trong danh mục.
    position: Mapped[str] = mapped_column(String(100), default="")   # Vị trí / Chức vụ — nhãn hiển thị
    #  `0` = chưa gán chức vụ trong danh mục (hồ sơ cũ, hoặc chức danh lẻ chưa
    #  ai khai). Không có khóa ngoại cứng — cùng quy ước `department_id` /
    #  `manager_id`; chốt id-có-thật nằm ở `position_service.check_assignable`.
    position_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    # CR-022: KHÔNG dùng nữa. Trước đây ô "Vai trò" ở màn Nhân sự tự cấp quyền cho tài khoản; nay
    # quyền chỉ gán ở "Phân quyền tài khoản" (tab_user_role). Cột giữ lại để không mất dữ liệu cũ.
    role_name: Mapped[str] = mapped_column(String(100), default="")
    # B-03: lưu MÃ tiếng Anh (`app/core/status_codes.EMPLOYEE_STATUS`), không lưu chữ tiếng Việt.
    # Nhãn hiển thị đi kèm ở `status_label` bên dưới.
    status: Mapped[str] = mapped_column(String(50), default="official")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    #  QĐ-NP3 (03/09/2026) — hai cột nền của phân hệ Nghỉ phép. CHỈ THÊM, không
    #  sửa cột nào đang có (quy tắc 1 của bộ ERP).
    #
    #  `hire_date` là mốc tính THÂM NIÊN, thứ quyết định người này được cộng mấy
    #  ngày phép (`tab_leave_type_seniority`). Cho phép NULL vì hồ sơ cũ chưa ai
    #  nhập; `balance_service` coi NULL là 0 năm và màn Quỹ phép trưng cảnh báo
    #  ra — chặn thì cả công ty không cấp được quỹ cho tới khi nhập xong.
    hire_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    #  `gender` để LỌC loại nghỉ (thai sản chỉ hiện với nữ). `0` = chưa khai, và
    #  chưa khai thì KHÔNG bị chặn — xem `leave/constants.GENDER_UNKNOWN`.
    #  ⚠️ Bộ mã của HỒ SƠ có thêm `3` («Khác», 08/09/2026) mà loại nghỉ không có:
    #  khai «Khác» thì bị chặn khỏi loại nghỉ giới hạn nam/nữ. Xem
    #  `employee/constants.GENDER_*`.
    gender: Mapped[int] = mapped_column(SmallInteger, default=0)

    # ── HỒ SƠ NHÂN SỰ mở rộng (08/09/2026) ──────────────────────────────────
    #  Thiết kế: `doc/erp/hrm/01-ho-so-nhan-su.md`. CHỈ THÊM CỘT, không sửa cột
    #  nào đang có (quy tắc 1 của bộ ERP) — 11 cột phía trên giữ nguyên hình
    #  dạng, mọi màn hình và mọi bản in cũ chạy y như trước.
    #
    #  Mọi cột đều để trống được. Hồ sơ đang chạy trên hệ thật có vài trăm dòng
    #  chưa ai nhập; bắt buộc một ô nào ở tầng bảng nghĩa là Nhân sự không lưu
    #  nổi hồ sơ cũ cho tới khi nhập bù xong (D-018 đã dạy đúng bài này với
    #  `hire_date`). Ô nào bắt buộc thì bắt ở tầng FORM, không ở tầng cột.
    #
    #  Cột nào thuộc NHÓM NHẠY CẢM khai ở `sensitive.py`, không đánh dấu ở đây —
    #  một danh sách một chỗ, để serializer, CSV và trợ lý AI cùng đọc.

    # Nhóm 1 — thông tin cá nhân
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    place_of_birth: Mapped[str] = mapped_column(String(255), default="")
    ethnicity: Mapped[str] = mapped_column(String(50), default="")
    religion: Mapped[str] = mapped_column(String(50), default="")
    marital_status: Mapped[int] = mapped_column(SmallInteger, default=0)
    children_count: Mapped[int] = mapped_column(SmallInteger, default=0)
    #  Email CÁ NHÂN — tách hẳn khỏi `email` (email công việc). `email` là cột
    #  đồng bộ sang tài khoản đăng nhập (`_sync_user_email_from_employee`); đổ
    #  gmail cá nhân vào đó là đổi luôn tên đăng nhập của người ta.
    personal_email: Mapped[str] = mapped_column(String(255), default="")
    tax_code: Mapped[str] = mapped_column(String(20), default="")
    education_level: Mapped[int] = mapped_column(SmallInteger, default=0)
    major: Mapped[str] = mapped_column(String(255), default="")

    # Nhóm 2 — công việc
    #  ⚠️ `manager_id` KHÔNG phải trường hiển thị cho đẹp. Đây là dữ liệu mà vai
    #  tương đối «người quản lý trực tiếp» của bộ máy duyệt đọc
    #  (`APPROVER_DIRECT_MANAGER`). Sai ô này thì đơn từ chạy sai đường một cách
    #  im lặng — không có màn nào báo, vì bộ máy duyệt vẫn tìm ra MỘT người.
    #  `0` = chưa gán, và luồng duyệt lùi về trưởng bộ phận để đơn không kẹt.
    manager_id: Mapped[int] = mapped_column(BigInteger, default=0)
    employment_type: Mapped[int] = mapped_column(SmallInteger, default=0)
    job_level: Mapped[int] = mapped_column(SmallInteger, default=0)
    work_location: Mapped[str] = mapped_column(String(255), default="")
    #  Ngày nghỉ việc — đi CẶP với `status`, không thay thế nó. Điền ngày mà quên
    #  đổi trạng thái thì người này vẫn là nhân sự đang làm ở mọi chỗ khác.
    resign_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Nhóm 3 — liên hệ
    #  MỘT trường chữ gộp, cố ý không tách tỉnh/phường/địa chỉ như HrOnline:
    #  phiếu giấy của công ty cũng ghi một dòng, mà tách ba ô thì phải nuôi thêm
    #  một danh mục địa giới hành chính — thứ vừa đổi cả nước năm 2025.
    permanent_address: Mapped[str] = mapped_column(String(500), default="")
    current_address: Mapped[str] = mapped_column(String(500), default="")

    # Nhóm 4 — ngân hàng nhận lương
    bank_account_no: Mapped[str] = mapped_column(String(50), default="")
    bank_account_name: Mapped[str] = mapped_column(String(255), default="")
    bank_name: Mapped[str] = mapped_column(String(100), default="")
    bank_branch: Mapped[str] = mapped_column(String(255), default="")

    # Nhóm 5 — giấy tờ, BHXH/BHYT
    id_number: Mapped[str] = mapped_column(String(20), default="")
    id_issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    id_issue_place: Mapped[str] = mapped_column(String(255), default="")
    id_expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    id_front_image: Mapped[str] = mapped_column(String(500), default="")
    id_back_image: Mapped[str] = mapped_column(String(500), default="")
    #  CHỈ lưu số phục vụ hồ sơ. Nghiệp vụ báo tăng/giảm BHXH nằm ngoài phạm vi
    #  (NS4 đã quyết không lấy) — đừng dựng luồng nào bám vào cột này.
    #
    #  Tình trạng sổ (dùng sổ cũ / cấp mới) KHÔNG cần cột riêng: có số nghĩa là
    #  dùng sổ cũ, rỗng nghĩa là chưa có.
    social_insurance_no: Mapped[str] = mapped_column(String(20), default="")
    health_care_place: Mapped[str] = mapped_column(String(255), default="")
    health_care_code: Mapped[str] = mapped_column(String(20), default="")

    # Nhóm 7 — tùy biến
    #  MỘT cột JSON cho nhu cầu lẻ, có trần số khóa (`MAX_EXTRA_FIELDS`).
    #  `nullable=True` vì hàng trăm dòng cũ không có gì để điền; tầng đọc coi
    #  `NULL` là `{}` (xem `extra_fields_map`).
    extra_fields: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    department = relationship(
        "Department",
        primaryjoin="foreign(Employee.department_id) == Department.id",
        uselist=False,
        viewonly=True
    )

    # Pháp nhân chủ quản — nối theo company_id giống department. Chỉ đọc: hồ sơ
    # nhân sự do phân hệ Nhân sự quản lý, ở đây không sửa qua quan hệ này.
    company = relationship(
        "Company",
        primaryjoin="foreign(Employee.company_id) == Company.id",
        uselist=False,
        viewonly=True
    )

    # Tài khoản đăng nhập gắn với nhân sự (nếu đã được cấp). Ảnh đại diện chỉ lưu MỘT chỗ
    # là tab_user.avatar — nhân sự đọc ké qua đây để khỏi có 2 nguồn dữ liệu lệch nhau.
    user = relationship(
        "User",
        primaryjoin="foreign(User.employee_id) == Employee.id",
        uselist=False,
        viewonly=True
    )

    #  Người quản lý TRỰC TIẾP — nối theo `manager_id`, chỉ đọc.
    #
    #  ⚠️ Đừng lẫn với `manager_name` bên dưới: cái đó là trưởng PHÒNG BAN (đọc
    #  qua `department.manager_name`), đã có từ lâu và nhiều màn đang dùng. Hai
    #  người này thường khác nhau — trưởng phòng của phòng Kinh doanh không phải
    #  người quản lý trực tiếp của một nhân viên đang biệt phái.
    direct_manager = relationship(
        "Employee",
        primaryjoin="foreign(Employee.manager_id) == remote(Employee.id)",
        uselist=False,
        viewonly=True,
    )

    @property
    def direct_manager_name(self) -> str:
        return (self.direct_manager.full_name or "") if self.direct_manager else ""

    @property
    def marital_status_label(self) -> str:
        return label_of(MARITAL_STATUS_LABELS, self.marital_status)

    @property
    def education_level_label(self) -> str:
        return label_of(EDUCATION_LEVEL_LABELS, self.education_level)

    @property
    def employment_type_label(self) -> str:
        return label_of(EMPLOYMENT_TYPE_LABELS, self.employment_type)

    @property
    def job_level_label(self) -> str:
        return label_of(JOB_LEVEL_LABELS, self.job_level)

    @property
    def extra_fields_map(self) -> dict:
        """`extra_fields` luôn đọc ra một dict, kể cả khi cột đang `NULL`.

        Hàng trăm dòng có trước cột này mang `NULL`. Trả `None` ra API thì mọi
        chỗ dùng phải tự `or {}`, và chỗ nào quên thì nổ `NoneType` đúng lúc mở
        một hồ sơ cũ — thứ chỉ lộ ra trên dữ liệu thật.
        """
        return self.extra_fields if isinstance(self.extra_fields, dict) else {}

    @property
    def department_name(self) -> str | None:
        return self.department.name if self.department else None

    @property
    def company_name(self) -> str | None:
        return self.company.name if self.company else None

    @property
    def manager_name(self) -> str | None:
        return self.department.manager_name if self.department else None

    @property
    def user_id(self) -> int:
        return self.user.id if self.user else 0

    @property
    def avatar(self) -> str:
        return (self.user.avatar or "") if self.user else ""

    @property
    def signature(self) -> str:
        #  Ảnh chữ ký cũng lưu ở tài khoản đăng nhập (tab_user.signature) — cùng
        #  chỗ với chữ ký người dùng tự đặt ở Trang cá nhân, tránh 2 nguồn lệch.
        return (self.user.signature or "") if self.user else ""

    @property
    def status_label(self) -> str:
        """Nhãn tiếng Việt của `status` (B-03).

        Mã lạ -> trả rỗng chứ KHÔNG trả lại chính mã: giao diện đã có sẵn nhánh lùi
        `status_label || status`, còn ở đây trả rỗng thì nhìn dữ liệu là biết ngay dòng nào
        chưa chạy migration. Cột này cũng là cột XUẤT CSV (xem controller) nên đừng bỏ.
        """
        return EMPLOYEE_STATUS.label_of(self.status)
