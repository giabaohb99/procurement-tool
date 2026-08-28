"""Việc cần làm — trạng thái ĐÃ ĐÁNH DẤU XONG theo từng tài khoản (CR-215).

Trước đây "Đánh dấu làm hết" ở tab Việc cần làm chỉ ghi localStorage của trình
duyệt: chuông cảnh báo (/api/alerts) và khối cảnh báo dashboard không biết gì,
đổi máy là hiện lại. Bảng này lưu khóa việc đã ẩn theo TÀI KHOẢN; cả ba nơi cùng
đọc nên đánh dấu một chỗ là ẩn mọi chỗ, khôi phục được.

Đánh dấu xong là ẨN KHỎI DANH SÁCH CỦA TÔI, không phải xử lý hộ nghiệp vụ:
phiếu vẫn chờ duyệt, khoản nợ vẫn quá hạn — màn nghiệp vụ tương ứng vẫn thấy đủ.
"""
from sqlalchemy import BigInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class UserTaskDismiss(Base, AuditMixin):
    """Một dòng = một việc (task_key) mà một tài khoản đã đánh dấu xong.

    `task_key` do backend sinh, ổn định theo bản ghi gốc + mức cảnh báo:
    - Phiếu chờ duyệt:  ``pr:{id}`` · ``sr:{id}`` · ``po:{id}``
    - Chờ tôi ký (bộ máy duyệt): ``sign:{task_id}``
    - Cảnh báo: ``delivery:{delivery_id}:{level}`` · ``payable:{id}:{level}``
      · ``contract:{id}:{level}`` — kèm level để cảnh báo "sắp tới hạn" đã ẩn
      vẫn NỔI LẠI khi leo thang thành "quá hạn".
    """
    __tablename__ = "tab_user_task_dismiss"
    __table_args__ = (
        UniqueConstraint("user_id", "task_key", name="uq_user_task_key"),
    )

    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    task_key: Mapped[str] = mapped_column(String(64))
