"""QUỸ PHÉP — số ngày một người có, trong một năm, cho một loại nghỉ.

Đây là bảng làm nên lý do tồn tại của cả đợt. Ràng buộc §6.1 của kế hoạch:
*số phép còn lại phải hiện NGAY trên form lúc nộp* — doc gọi đó là "chi tiết
nhỏ, nhưng nó cắt phần lớn số đơn sai và phần lớn câu hỏi gửi về phòng Nhân sự".
Muốn hiện được thì phải có chỗ để hỏi, và chỗ đó là đây.

**Số còn lại KHÔNG lưu thành cột.** Nó là hiệu:

    còn lại = allocated + seniority + carried + adjusted − used − pending

Lưu thêm một cột `remaining` thì có hai nguồn sự thật, và cái thứ hai sẽ lệch —
sớm hay muộn. `balance_service.remaining_days()` là nơi duy nhất tính.
"""
from sqlalchemy import BigInteger, Float, Index, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class LeaveBalance(Base, AuditMixin):
    """Quỹ phép của (nhân sự × năm × loại nghỉ)."""

    __tablename__ = "tab_leave_balance"
    __table_args__ = (
        #  Ràng buộc này là thứ giữ cho quỹ không bị nhân đôi. Hai dòng cùng
        #  (người, năm, loại) thì `remaining_days` đọc trúng dòng nào là hên xui,
        #  và trừ phép sẽ trừ vào dòng còn lại.
        UniqueConstraint("employee_id", "year", "leave_type_id",
                         name="uq_leave_balance_emp_year_type"),
        Index("ix_leave_balance_emp_year", "employee_id", "year"),
    )

    employee_id: Mapped[int] = mapped_column(BigInteger, default=0)
    year: Mapped[int] = mapped_column(SmallInteger, default=0)
    leave_type_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  Chép từ hồ sơ nhân sự lúc lập quỹ — để `apply_scope` lọc được theo pháp
    #  nhân mà không phải JOIN sang `tab_employee` ở mọi câu truy vấn.
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)

    # --- các khoản CỘNG ---------------------------------------------------
    #  Hạn mức cơ bản, chép từ `LeaveType.annual_quota_days` lúc cấp phát.
    #  CHÉP chứ không đọc thẳng: đổi hạn mức giữa năm thì quỹ đã cấp của năm nay
    #  phải giữ nguyên, luật mới áp cho lần cấp sau.
    allocated_days: Mapped[float] = mapped_column(Float, default=0.0)
    #  Cộng thêm theo bậc thâm niên (`tab_leave_type_seniority`), tính tại thời
    #  điểm cấp phát. Tách khỏi `allocated_days` để màn Quỹ phép giải thích được
    #  "12 + 2" thay vì trưng ra con số 14 không rõ từ đâu ra.
    seniority_days: Mapped[float] = mapped_column(Float, default=0.0)
    #  Chuyển từ năm trước sang (Q2 — chỉ khi `LeaveType.carry_over` bật).
    carried_days: Mapped[float] = mapped_column(Float, default=0.0)
    #  Nhân sự chỉnh tay, cộng hoặc TRỪ. Cột duy nhất mang được số âm — mọi cột
    #  khác là số ngày nên không âm bao giờ.
    adjusted_days: Mapped[float] = mapped_column(Float, default=0.0)

    # --- các khoản TRỪ ----------------------------------------------------
    #  Đã nghỉ thật — cộng vào khi đơn được DUYỆT.
    used_days: Mapped[float] = mapped_column(Float, default=0.0)
    #  GIỮ CHỖ cho đơn đang chờ duyệt. Không có cột này thì nộp mười đơn liền
    #  tay đều lọt, vì đơn nào cũng thấy quỹ còn nguyên — lỗi cổ điển của mọi hệ
    #  nghỉ phép. Trả lại khi đơn bị từ chối / trả về / hủy.
    pending_days: Mapped[float] = mapped_column(Float, default=0.0)

    note: Mapped[str] = mapped_column(String(500), default="")

    # --- đọc --------------------------------------------------------------
    @property
    def total_days(self) -> float:
        """Tổng quỹ được hưởng, chưa trừ gì."""
        return round(self.allocated_days + self.seniority_days
                     + self.carried_days + self.adjusted_days, 2)

    @property
    def remaining_days(self) -> float:
        """Số ngày còn nghỉ được — đã trừ cả phần đang chờ duyệt.

        Làm tròn 2 chữ số vì `Float` cộng dồn nửa ngày ra `13.999999999999998`,
        và người dùng đọc con số đó thì tưởng hệ thống hỏng.
        """
        return round(self.total_days - self.used_days - self.pending_days, 2)
