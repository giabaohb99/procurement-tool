"""DANH SÁCH BIẾN của mẫu HĐLĐ — `tab_labor_contract_variable` (duoc-CR-630).

Hai loại dòng, phân bằng `source` (`LaborContractVariableSource`):
  - HỆ THỐNG: 48 biến mã cứng ở `placeholder_catalog.py`. GIÁ TRỊ và việc biến có HỢP LỆ vẫn theo
    MÃ NGUỒN; dòng DB chỉ giữ thứ người dùng sửa được: nhãn, mô tả, ẩn khỏi danh sách hướng dẫn.
    Thiếu dòng DB không bao giờ làm mẫu bị từ chối.
  - TÙY CHỈNH: HR tự thêm, nhập tay theo từng hợp đồng (`tab_labor_contract.custom_values`).

Toàn hệ thống (không `company_id`) — PO chốt: biến dùng chung mọi pháp nhân.
"""
from sqlalchemy import Boolean, Index, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

#  Trần độ dài (schema khai ĐÚNG số này — luật backend-input-limits).
CODE_LEN, LABEL_LEN, DESCRIPTION_LEN, EXAMPLE_LEN, DEFAULT_LEN = 40, 200, 500, 255, 2000


class LaborContractVariable(Base, AuditMixin):
    __tablename__ = "tab_labor_contract_variable"
    __table_args__ = (
        UniqueConstraint("code", name="uq_labor_contract_variable_code"),
        Index("ix_labor_contract_variable_pick", "source", "is_active", "sort_order"),
    )

    #  snake_case ASCII; 40 ký tự để `code + "_bang_chu"` vẫn ≤ 49
    code: Mapped[str] = mapped_column(String(CODE_LEN))
    #  `LaborContractVariableSource` / `LaborContractVariableType` (core/labor_contract_codes.py)
    source: Mapped[int] = mapped_column(SmallInteger)
    value_type: Mapped[int] = mapped_column(SmallInteger, default=1)
    label: Mapped[str] = mapped_column(String(LABEL_LEN))
    description: Mapped[str] = mapped_column(String(DESCRIPTION_LEN), default="")
    example: Mapped[str] = mapped_column(String(EXAMPLE_LEN), default="")
    #  Dạng CHUẨN của kiểu. Chỉ biến tùy chỉnh. Được SAO vào hợp đồng lúc lập (không áp lúc sinh tệp).
    default_value: Mapped[str] = mapped_column(String(DEFAULT_LEN), default="")
    #  «Bắt buộc»: chặn Sinh tệp và chuyển sang Đã ký khi hợp đồng thiếu giá trị. Chỉ biến tùy chỉnh.
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    #  Ngừng dùng (chỉ biến tùy chỉnh; biến hệ thống luôn True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    #  Chỉ biến hệ thống: ẩn khỏi danh sách hướng dẫn / khung chèn, VẪN hợp lệ trong mẫu
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)
