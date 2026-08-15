"""QUYỀN TRÊN TỪNG VĂN BẢN — ai được thấy, đọc, sửa, xóa **văn bản cụ thể này**.

Đây là lớp thứ BA, đứng cạnh hai lớp đã có chứ không thay thế lớp nào:

| Lớp | Câu hỏi nó trả lời | Ở đâu |
|---|---|---|
| Vai trò (`require`) | Người này có được đụng vào *loại việc* văn bản không | `core/permissions.py` |
| Phạm vi (`apply_scope`) | Trong đó thì thấy được *nhóm* văn bản nào | `core/scoping.py` |
| **Bảng này** | Riêng *văn bản này* thì mở thêm / khóa bớt cho ai | ở đây |

Vì sao cần lớp thứ ba: hai lớp trên chỉ cắt theo pháp nhân / phòng ban / người
tạo. Nhưng "gửi bản quy chế lương cho một người ở phòng khác đọc" và "phòng nhân
sự thấy hết trừ đúng một văn bản" đều không diễn đạt được bằng phạm vi — mà đó
lại là hai việc hằng ngày (`van-thu` G05, G06).

Bốn điều đã cân nhắc và cố ý làm như vậy:

1. **CẤM thắng CHO PHÉP.** Một dòng `effect = 2` ăn đứt mọi dòng cho phép và ăn
   đứt cả phạm vi vai trò. Người đã bị cấm đích danh mà vẫn đọc được vì tình cờ
   có một vai trò rộng thì cái nút "cấm" là vô nghĩa.
2. **Thu hồi là ĐÁNH DẤU, không xóa dòng** (G19, G20). Xóa đi thì ba tháng sau
   không trả lời được câu "hồi tháng 7 ai đọc được văn bản này".
3. **Có hạn.** `valid_to` để trống = không hạn; đặt hạn thì hết ngày là tự mất
   quyền, không cần ai nhớ đi thu hồi.
4. **Cấp cho bốn loại đối tượng**, không chỉ cá nhân: người · phòng ban · pháp
   nhân · vai trò. Chia cho cả phòng mà phải chọn từng người thì người mới vào
   phòng không có quyền, người chuyển đi vẫn còn.
"""
from datetime import date, datetime

from sqlalchemy import (BigInteger, Boolean, Date, DateTime, Index, SmallInteger,
                        String)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

SUBJECT_EMPLOYEE = 1
SUBJECT_DEPARTMENT = 2
SUBJECT_COMPANY = 3
SUBJECT_ROLE = 4

SUBJECT_LABELS = {
    SUBJECT_EMPLOYEE: "Người",
    SUBJECT_DEPARTMENT: "Phòng ban",
    SUBJECT_COMPANY: "Pháp nhân",
    SUBJECT_ROLE: "Vai trò",
}

EFFECT_ALLOW = 1
EFFECT_DENY = 2

EFFECT_LABELS = {EFFECT_ALLOW: "Cho phép", EFFECT_DENY: "Cấm"}


class DocumentAccess(Base, AuditMixin):
    __tablename__ = "tab_document_access"
    __table_args__ = (
        Index("ix_document_access_subject", "subject_kind", "subject_id"),
        Index("ix_document_access_doc", "document_id", "effect"),
    )
    #  ⚠️ CỐ Ý không có UNIQUE cho "một dòng đang sống mỗi (văn bản × đối tượng ×
    #  chiều tác động)". Đã cân nhắc: `revoked_at IS NULL` thì UNIQUE không chặn
    #  được (nhiều NULL vẫn hợp lệ), còn cột sinh kiểu `open_slot` thì hàm nối
    #  chuỗi của MySQL và SQLite khác nhau nên bộ kiểm thử không chạy được.
    #  Chống trùng làm ở `access_service.grant()`: có dòng còn sống thì SỬA dòng
    #  đó chứ không thêm dòng mới. Hai người bấm chia cùng lúc, xấu nhất là hai
    #  dòng cho phép y hệt nhau — thừa chứ không sai quyền.

    document_id: Mapped[int] = mapped_column(BigInteger)

    #  1 người (id NHÂN SỰ) · 2 phòng ban · 3 pháp nhân · 4 vai trò.
    subject_kind: Mapped[int] = mapped_column(SmallInteger, default=SUBJECT_EMPLOYEE)
    subject_id: Mapped[int] = mapped_column(BigInteger)

    #  1 cho phép · 2 cấm. CẤM thắng — xem chú thích đầu tệp.
    effect: Mapped[int] = mapped_column(SmallInteger, default=EFFECT_ALLOW)

    #  "Thấy" và "đọc" là MỘT: văn bản không cho đọc thì cũng không được hiện ra
    #  trong danh sách (K03 — kết quả tìm kiếm không lộ cả tiêu đề). Tách hai
    #  cột chỉ tổ đẻ ra tổ hợp "thấy tên mà không mở được", thứ không ai muốn.
    can_read: Mapped[bool] = mapped_column(Boolean, default=True)
    can_write: Mapped[bool] = mapped_column(Boolean, default=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False)

    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    #  Trống = không hạn.
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    #  Vì sao chia — ô bắt buộc trên giao diện chia sẻ đặc cách (G15).
    reason: Mapped[str] = mapped_column(String(500), default="")

    #  Thu hồi: ghi mốc, KHÔNG xóa dòng.
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_by: Mapped[int] = mapped_column(BigInteger, default=0)
    revoke_reason: Mapped[str] = mapped_column(String(500), default="")
