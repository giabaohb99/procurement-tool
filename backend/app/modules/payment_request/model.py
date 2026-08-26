from sqlalchemy import BigInteger, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class PaymentRequest(Base, AuditMixin):
    """Phiếu yêu cầu thanh toán — CHỈ 1 NCC/phiếu, gom nhiều khoản nợ (nhiều PO). In được."""

    __tablename__ = "tab_payment_request"

    code: Mapped[str] = mapped_column(String(50), default="")          # YCTT00045
    supplier_code: Mapped[str] = mapped_column(String(50), default="", index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), default="")
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    source_type: Mapped[str] = mapped_column(String(20), default="goods")  # goods | shipping
    request_date: Mapped[str] = mapped_column(String(10), default="")
    # CR-035 — hình thức thanh toán do người lập phiếu chọn; quyết định bản in có in
    # cụm "Thông tin chuyển khoản" hay để trống. transfer = Chuyển khoản, cash = Tiền mặt.
    payment_method: Mapped[str] = mapped_column(String(20), default="transfer")
    # CR-146 (ticket #12) — cờ THANH TOÁN TRƯỚC: 0 = thanh toán công nợ (mặc định),
    # 1 = trả trước cho đơn hàng. Quyết định câu nội dung trên bản in:
    # "Thanh toán công nợ ..." hay "Thanh toán trước cho nhà cung cấp ...".
    prepay: Mapped[int] = mapped_column(SmallInteger, default=0)
    total: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    note: Mapped[str] = mapped_column(Text, default="")
    reject_reason: Mapped[str] = mapped_column(Text, default="")   # lý do từ chối (khi cancelled)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    # draft | submitted | approved | paid | cancelled (Đã từ chối)


class PaymentRequestLine(Base, AuditMixin):
    """Dòng đề nghị chi. CR-066: mã PO / số hóa đơn / ngày hóa đơn là dữ liệu NHẬP TAY được
    (bản nháp cho sửa), không còn bắt buộc phải soi ngược từ khoản công nợ. payable_id = 0
    nghĩa là dòng gõ tay trên form trắng, chưa gắn khoản nợ nào."""

    __tablename__ = "tab_payment_request_line"

    request_id: Mapped[int] = mapped_column(BigInteger, index=True)
    payable_id: Mapped[int] = mapped_column(BigInteger, default=0)
    po_code: Mapped[str] = mapped_column(String(50), default="")
    invoice_no: Mapped[str] = mapped_column(String(50), default="")
    # Ngày hóa đơn — mặc định lấy từ dòng giao hàng (tab_po_delivery.invoice_date), sửa tay được
    invoice_date: Mapped[str] = mapped_column(String(10), default="")
    amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
