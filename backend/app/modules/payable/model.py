from sqlalchemy import BigInteger, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class Payable(Base, AuditMixin):
    """Khoản công nợ phải trả — SINH NGẦM khi nhận hàng. 1 dòng = 1 lần giao × 1 luồng.

    source_type: goods = nợ NCC bán hàng ; shipping = nợ đơn vị vận chuyển ;
                 import_cost = nợ một dòng chi phí thu mua (bao-CR-319 P5, mở cho mọi loại đơn bao-CR-453,
                 ref_type = "import_cost", ref_id = id dòng `tab_po_cost`).
    """

    __tablename__ = "tab_payable"

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    # bao-CR-414 GĐ4 — phòng XỬ LÝ đơn hàng lúc khoản nợ sinh ra. Từ bao-CR-484 (đại ca
    # chốt 25/09/2026): = ô «Phòng xử lý» của đơn, 0 = thu mua chung / nợ không có đơn —
    # KHÔNG còn lùi về phòng lập đơn (`payable.service.debt_dept_of`). Cột ẩn: không hiện,
    # không lọc trên màn; chỉ để phạm vi `dept_proc` / `dept` / loại trừ phòng bắt được
    # công nợ của phòng mình. Nợ cũ gán lại bằng `resync_departments_from_orders`.
    department_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    supplier_code: Mapped[str] = mapped_column(String(50), default="", index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), default="")
    source_type: Mapped[str] = mapped_column(String(20), default="goods", index=True)
    ref_type: Mapped[str] = mapped_column(String(20), default="delivery")
    ref_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    po_id: Mapped[int] = mapped_column(BigInteger, default=0)
    po_code: Mapped[str] = mapped_column(String(50), default="", index=True)
    invoice_no: Mapped[str] = mapped_column(String(50), default="")
    incur_date: Mapped[str] = mapped_column(String(10), default="", index=True)  # ngày phát sinh (= ngày nhận)
    period: Mapped[str] = mapped_column(String(7), default="", index=True)        # YYYY (lọc/nhóm theo năm)
    due_date: Mapped[str] = mapped_column(String(10), default="", index=True)     # hạn trả
    amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)   # trước VAT
    vat: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(18, 2), default=0)    # phải trả = amount + vat
    paid_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    remaining: Mapped[float] = mapped_column(Numeric(18, 2), default=0)  # tính sẵn = total - paid
    # MÃ cố định, xem PAYABLE_STATUS trong app/core/status_codes.py (B-05): unpaid | partial | paid.
    # Không ai nhập cột này — service.recalc_status() tính lại từ paid_amount so với total.
    status: Mapped[str] = mapped_column(String(20), default="unpaid", index=True)
