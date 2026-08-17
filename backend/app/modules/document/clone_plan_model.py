"""KẾ HOẠCH CLONE — khai lúc TẠO, chạy lúc BAN HÀNH (F06 phần đầu).

Vì sao cần một bảng riêng thay vì bấm clone lúc nào cần: `create_clones()` từ
chối văn bản chưa ban hành (*"Chỉ clone được văn bản đã ban hành"*), và từ chối
đúng — bản clone chép nội dung của phiên bản đang dùng, mà văn bản nháp thì chưa
có phiên bản nào đang dùng để chép.

Nhưng người soạn BIẾT ngay từ lúc lập văn bản là nó sẽ tách bản riêng cho những
pháp nhân nào. Bắt họ nhớ để mấy tuần sau quay lại khai lại là chỗ việc rơi:
văn bản ban hành xong, không ai bấm clone, mười hai pháp nhân con không nhận
được gì và không ai biết là đang thiếu.

Nên tách làm hai nhịp: **khai dự định** ở đây, **sinh bản nháp thật** khi văn
bản đã ban hành. Dự định không tự chạy — clone đẻ ra văn bản thật, không nên là
tác dụng phụ âm thầm của việc bấm nút Duyệt. Nó chỉ tick sẵn đúng những pháp
nhân đã khai để việc còn lại là bấm một nút.

Dòng kế hoạch bị **xóa ngay khi bản clone tương ứng được tạo** (xem
`consume_plan`) — để cùng một pháp nhân không nằm ở cả hai chỗ, vừa "dự kiến"
vừa "đã có".
"""
from datetime import date

from sqlalchemy import BigInteger, Date, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class DocumentClonePlan(Base, AuditMixin):
    __tablename__ = "tab_document_clone_plan"
    __table_args__ = (
        #  Một pháp nhân chỉ đứng một lần trong kế hoạch của một văn bản. Khai
        #  trùng không thêm nghĩa gì, chỉ làm bảng theo dõi đếm sai.
        UniqueConstraint("document_id", "company_id", name="uq_document_clone_plan"),
    )

    document_id: Mapped[int] = mapped_column(BigInteger, index=True)
    company_id: Mapped[int] = mapped_column(BigInteger)

    #  Hạn và ghi chú khai một lần cho cả đợt nhưng lưu theo từng dòng: lúc sinh
    #  bản clone thật, mỗi pháp nhân nhận đúng hạn của mình, và sau này muốn
    #  giãn hạn cho riêng một nơi thì không phải đổi cấu trúc bảng.
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str] = mapped_column(String(500), default="")
