"""PHẠM VI ÁP DỤNG của văn bản (F01–F04).

Ba kiểu: pháp nhân · phòng ban · cá nhân. **Không có kiểu chức danh** — điều kiện
dạng "trưởng phòng trở lên" viết trong nội dung văn bản, không khai thành dữ liệu.

Bốn quy tắc tính "ai thuộc phạm vi", đọc kỹ trước khi sửa:

1. Các dòng **bao gồm** cộng dồn với nhau.
2. Chiều cụ thể hơn thắng: **cá nhân > phòng ban > pháp nhân**.
3. Cùng một chiều thì **loại trừ thắng** bao gồm.
4. **Không có dòng nào = toàn bộ pháp nhân ban hành** — và chỉ pháp nhân đó.

Ví dụ: bao gồm Công ty A, loại trừ phòng Kế toán, rồi bao gồm đích danh chị B
trong phòng đó → chị B thấy, những thành viên Kế toán còn lại không thấy.
"""
from sqlalchemy import (BigInteger, Boolean, CheckConstraint, Index,
                        SmallInteger, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

DIM_COMPANY = 1     # pháp nhân
DIM_DEPARTMENT = 2  # phòng ban
DIM_EMPLOYEE = 3    # cá nhân

DIM_LABELS = {
    DIM_COMPANY: "Pháp nhân",
    DIM_DEPARTMENT: "Phòng ban",
    DIM_EMPLOYEE: "Cá nhân",
}

MODE_INCLUDE = 1  # bao gồm
MODE_EXCLUDE = 2  # loại trừ

MODE_LABELS = {
    MODE_INCLUDE: "Bao gồm",
    MODE_EXCLUDE: "Loại trừ",
}


class DocumentScope(Base, AuditMixin):
    __tablename__ = "tab_document_scope"
    __table_args__ = (
        #  F03 — chọn phòng ban thì BẮT BUỘC kèm pháp nhân.
        #
        #  Một phòng ban có mặt ở 13 pháp nhân; chọn trơ trọi "phòng Kế toán" là
        #  văn bản lan sang cả 13 công ty. Đây là lỗi rất dễ mắc và rất khó phát
        #  hiện sau khi đã ban hành, nên chặn ở TẦNG DỮ LIỆU chứ không chỉ ở
        #  giao diện — giao diện còn có đường vòng, ràng buộc này thì không.
        CheckConstraint(
            "dim <> 2 OR company_id IS NOT NULL",
            name="ck_document_scope_department_needs_company",
        ),
        #  Khai trùng một dòng y hệt không thêm nghĩa gì, chỉ làm bảng phình và
        #  làm người đọc tưởng có hai điều kiện khác nhau.
        UniqueConstraint("document_id", "dim", "company_id", "department_id",
                         "employee_id", "mode", name="uq_document_scope"),
        #  Màn "văn bản áp dụng cho tôi" tra ngược từ người sang văn bản.
        Index("ix_document_scope_company", "company_id", "mode"),
        Index("ix_document_scope_department", "department_id", "mode"),
        Index("ix_document_scope_employee", "employee_id", "mode"),
    )

    document_id: Mapped[int] = mapped_column(BigInteger, index=True)
    dim: Mapped[int] = mapped_column(SmallInteger, default=DIM_COMPANY)

    company_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    department_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    employee_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    #  F04 — chọn Tập đoàn kèm cờ này thì áp cho mọi công ty con **hiện tại và
    #  tương lai**. Vì thế phải tính lúc đọc chứ không bung sẵn thành nhiều dòng:
    #  bung sẵn thì công ty con mở sau này không được áp.
    include_children: Mapped[bool] = mapped_column(Boolean, default=False)

    mode: Mapped[int] = mapped_column(SmallInteger, default=MODE_INCLUDE)
