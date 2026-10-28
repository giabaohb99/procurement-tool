"""Kế hoạch nhân sự theo kỳ — `tab_headcount_plan` (+ dòng vị trí, văn bản liên kết). Thiết kế: `doc/erp/hrm/06-ke-hoach-nhan-su.md`.

Một kế hoạch = MỘT kỳ (loại kỳ + số thứ tự) × một pháp nhân × một phòng (`department_id = 0` là cả pháp nhân).
FK MỀM (không khai `ForeignKey`), khuôn `tab_labor_contract`; tồn tại của pháp nhân / phòng kiểm ở `service`.
Xóa CỨNG: ràng buộc duy nhất sẽ chặn lập lại nếu xóa mềm. Bảng khoản chi phí / mẫu ở `cost_model.py`.

Hai cột đợt 4 `planned_headcount` · `planned_payroll_monthly` đã BỎ (migration `hcplan03`): báo cáo A4 / A5 đọc kế hoạch
có hiệu lực theo tháng qua `effective.py`. Tiền (đồng NGUYÊN) chỉ trả cho người đọc được HĐLĐ của pháp nhân đó.
"""
from datetime import date

from sqlalchemy import BigInteger, Date, Index, JSON, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class HeadcountPlan(Base, AuditMixin):
    __tablename__ = "tab_headcount_plan"
    __table_args__ = (
        UniqueConstraint("year", "period_type", "period_no", "company_id", "department_id",
                         name="uq_headcount_plan_period"),
        Index("ix_headcount_plan_company_year", "company_id", "year"),
    )

    year: Mapped[int] = mapped_column(SmallInteger)
    period_type: Mapped[int] = mapped_column(SmallInteger, default=1, server_default="1")   # PlanPeriodType
    period_no: Mapped[int] = mapped_column(SmallInteger, default=1, server_default="1")     # Năm 1 · Bán niên 1–2 · Quý 1–4 · Tháng 1–12
    company_id: Mapped[int] = mapped_column(BigInteger)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)   # 0 = toàn pháp nhân
    basis_no: Mapped[str] = mapped_column(String(100), default="", server_default="")   # số căn cứ, vd «12/QĐ-BGĐ»
    basis_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    approver_employee_id: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    template_id: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")   # chỉ để biết đã chép từ mẫu nào
    note: Mapped[str] = mapped_column(String(500), default="")


class HeadcountPlanLine(Base, AuditMixin):
    """Một vị trí (`position_id = 0` = «Không theo vị trí») × định biên từng kỳ con × số tiền các khoản nhập theo vị trí."""

    __tablename__ = "tab_headcount_plan_line"
    __table_args__ = (UniqueConstraint("plan_id", "position_id", name="uq_headcount_plan_line"),)

    plan_id: Mapped[int] = mapped_column(BigInteger, index=True)
    position_id: Mapped[int] = mapped_column(BigInteger, default=0)
    headcounts: Mapped[list] = mapped_column(JSON, default=list)   # độ dài = số kỳ con của loại kỳ
    amounts: Mapped[dict] = mapped_column(JSON, default=dict)      # {mã khoản cách tính 1: đồng / người / tháng}
    note: Mapped[str] = mapped_column(String(500), default="")


class HeadcountPlanDocument(Base, AuditMixin):
    """Kế hoạch × văn bản liên kết (phân hệ Văn bản). Liên kết KHÔNG cấp thêm quyền đọc văn bản cho ai."""

    __tablename__ = "tab_headcount_plan_document"
    __table_args__ = (UniqueConstraint("plan_id", "document_id", name="uq_headcount_plan_document"),)

    plan_id: Mapped[int] = mapped_column(BigInteger, index=True)
    document_id: Mapped[int] = mapped_column(BigInteger)
