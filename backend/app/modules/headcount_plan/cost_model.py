"""Nhóm chi phí, mẫu khoản chi phí và khoản đã chép vào kế hoạch (duoc-CR-690).

Mã nguồn KHÔNG ghi cứng khoản nào: nhóm, mẫu, khoản đều là DỮ LIỆU người dùng sửa được. Kế hoạch lập từ mẫu thì
CHÉP khoản sang `tab_headcount_plan_cost_item` (bản chụp) — sửa mẫu về sau không làm con số đã duyệt trôi.
Hai bảng khoản (mẫu / kế hoạch) cùng cột, khác khóa cha → dùng chung `CostItemColumns`.
"""
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Integer, JSON, Numeric, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class HrCostGroup(Base, AuditMixin):
    __tablename__ = "tab_hr_cost_group"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class HrCostTemplate(Base, AuditMixin):
    __tablename__ = "tab_hr_cost_template"

    name: Mapped[str] = mapped_column(String(150), unique=True)
    note: Mapped[str] = mapped_column(String(500), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class CostItemColumns:
    """Cột chung của một khoản chi phí. `code` là KHÓA tham chiếu giữa các khoản và cột số tiền của dòng vị trí."""

    code: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(150))
    group_id: Mapped[int] = mapped_column(BigInteger, default=0)
    calc_method: Mapped[int] = mapped_column(SmallInteger)                       # CostCalcMethod
    rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=0)               # % cho PERCENT_OF
    factor: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)             # số tháng cho MONTHS_OF
    cap_amount: Mapped[int] = mapped_column(BigInteger, default=0)                # 0 = không trần
    amount: Mapped[int] = mapped_column(BigInteger, default=0)                    # PER_HEAD_ONCE / LUMP_SUM
    base_codes: Mapped[list] = mapped_column(JSON, default=list)                  # list[str]
    applies_to: Mapped[int] = mapped_column(SmallInteger, default=1)              # CostAppliesTo
    position_ids: Mapped[list] = mapped_column(JSON, default=list)                # list[int]
    months: Mapped[list] = mapped_column(JSON, default=list)                      # list[1..12]; rỗng = mỗi tháng
    actual_source: Mapped[int] = mapped_column(SmallInteger, default=0)           # ActualSource
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class HrCostTemplateItem(Base, AuditMixin, CostItemColumns):
    __tablename__ = "tab_hr_cost_template_item"
    __table_args__ = (UniqueConstraint("template_id", "code", name="uq_hr_cost_template_item"),)

    template_id: Mapped[int] = mapped_column(BigInteger, index=True)


class HeadcountPlanCostItem(Base, AuditMixin, CostItemColumns):
    __tablename__ = "tab_headcount_plan_cost_item"
    __table_args__ = (UniqueConstraint("plan_id", "code", name="uq_headcount_plan_cost_item"),)

    plan_id: Mapped[int] = mapped_column(BigInteger, index=True)
