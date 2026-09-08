"""Hai bảng NGƯỜI GẮN VỚI MỘT HỒ SƠ nhân sự — theo phiếu BM00../QT01/NS.

Cả hai đều là **chi tiết của hồ sơ**: không có màn danh sách riêng, không có mã
chứng từ, sửa trong tab của màn chi tiết nhân viên. Vì thế chúng KHÔNG có khóa
phân quyền riêng — xem `sensitive.py` để biết vì sao và đọc/ghi đi qua chốt nào.

Vì sao là BẢNG chứ không phải mấy cột phẳng trên `tab_employee`: phiếu giấy của
công ty cho khai NHIỀU người (cha, mẹ, vợ/chồng…), mỗi người một địa chỉ và một
số điện thoại. Nhét vào cột phẳng thì hoặc chỉ chứa được một người, hoặc đẻ ra
`contact_2_name`, `contact_3_name` — thứ không đếm được và không lọc được.
"""
from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class EmployeeContact(Base, AuditMixin):
    """Người báo tin trong trường hợp cần thiết.

    Phiếu ghi rõ **bắt buộc** — đây là số gọi khi có tai nạn lao động, nên hồ sơ
    trống ô này là một rủi ro có thật chứ không phải dữ liệu cho đẹp. Bắt buộc ở
    tầng FORM (Đợt 2), không ở tầng bảng: hàng trăm hồ sơ cũ chưa ai khai.
    """

    __tablename__ = "tab_employee_contact"

    #  ⚠️ `ondelete="CASCADE"`: xóa hồ sơ nhân sự là xóa luôn người báo tin của
    #  họ. Khác hẳn tài khoản đăng nhập (CR-023 giữ lại để truy vết ai làm gì) —
    #  ở đây không có dấu vết nào để giữ, chỉ còn dữ liệu cá nhân của một người
    #  thứ ba không còn lý do gì để hệ thống tiếp tục lưu.
    employee_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_employee.id", ondelete="CASCADE"), index=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    #  MÃ SỐ, xem `constants.RELATION_LABELS`. Quan hệ với NHÂN VIÊN.
    #
    #  Bản đầu để chữ tự do; khách chốt thành ô CHỌN ngày 08/09/2026, nên thành
    #  danh sách cố định và R2/QĐ-11 áp dụng: lưu SMALLINT, không lưu chữ. Chữ
    #  tự do làm mỗi người gõ một kiểu («vợ» · «Vợ» · «v/c»), không lọc nổi.
    relation: Mapped[int] = mapped_column(SmallInteger, default=0)
    address: Mapped[str] = mapped_column(String(500), default="")
    phone: Mapped[str] = mapped_column(String(25), default="")
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)


class EmployeeFamily(Base, AuditMixin):
    """Thành viên hộ gia đình — phục vụ kê khai BHXH khi ký hợp đồng chính thức.

    Ghi chú in đậm trên phiếu giấy. Khác `EmployeeContact` ở chỗ bảng này cần
    ngày sinh + CCCD (hồ sơ BHXH đòi), còn bảng kia cần địa chỉ để tìm người.
    Gộp hai bảng làm một thì mỗi dòng thừa một nửa số ô.
    """

    __tablename__ = "tab_employee_family"

    employee_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_employee.id", ondelete="CASCADE"), index=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    #  MÃ SỐ, dùng CHUNG bộ với `EmployeeContact.relation` — nhưng ở đây là quan
    #  hệ với CHỦ HỘ, không phải với nhân viên. Hồ sơ BHXH hỏi đúng như vậy, và
    #  nhân viên không phải lúc nào cũng là chủ hộ.
    relation: Mapped[int] = mapped_column(SmallInteger, default=0)
    #  Cùng quy ước với `Employee.gender`: 0 chưa khai · 1 nam · 2 nữ · 3 khác.
    gender: Mapped[int] = mapped_column(SmallInteger, default=0)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    phone: Mapped[str] = mapped_column(String(25), default="")
    id_number: Mapped[str] = mapped_column(String(20), default="")
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)
