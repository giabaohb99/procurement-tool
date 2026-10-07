"""MẪU HỢP ĐỒNG LAO ĐỘNG theo pháp nhân — `tab_labor_contract_template`.

Mỗi mẫu = một tệp .docx do HR tải lên, gắn ĐÚNG MỘT pháp nhân + ĐÚNG MỘT loại HĐ.
Tệp lưu ở `tab_file` (riêng tư, không qua `FileLink`); `file_id` là FK MỀM.
"""
from sqlalchemy import JSON, BigInteger, Boolean, Index, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class LaborContractTemplate(Base, AuditMixin):
    __tablename__ = "tab_labor_contract_template"
    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_labor_contract_template_company_name"),
        Index("ix_labor_contract_template_pick", "company_id", "contract_type", "is_active"),
    )

    company_id: Mapped[int] = mapped_column(BigInteger, index=True)
    #  `LaborContractType` (core/labor_contract_codes.py)
    contract_type: Mapped[int] = mapped_column(SmallInteger)
    name: Mapped[str] = mapped_column(String(200))
    note: Mapped[str] = mapped_column(String(500), default="")
    #  FK MỀM → tab_file.id
    file_id: Mapped[int] = mapped_column(BigInteger, default=0)
    original_filename: Mapped[str] = mapped_column(String(255), default="")
    #  Danh sách biến phát hiện lúc tải lên (list[str]; trần kích thước ở schema/service)
    placeholders: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
