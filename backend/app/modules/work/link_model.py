"""Phân hệ Công việc — PHỤ THUỘC việc trước–sau (B-15).

Quy ước chung của phân hệ (employee_id, ngày dạng chuỗi, IntEnum) nằm ở đầu
`model.py` — đọc trước. Thiết kế: `doc/erp/cong-viec/01-danh-sach-tinh-nang.md`
§4b (cụm Gantt mở rộng).
"""
from sqlalchemy import BigInteger, ForeignKey, Index, Integer, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base
from app.modules.work.model import WorkLinkType


class WorkTaskLink(Base, AuditMixin):
    """Một mũi tên phụ thuộc trên Gantt: việc TRƯỚC → việc SAU.

    Bốn luật, ba cái đầu DB giữ được, cái cuối thì không:

    1. **Hai đầu cùng một list.** `list_id` lưu sẵn để vẽ Gantt lấy hết mũi tên
       của dự án bằng MỘT query, khỏi join hai lượt sang `tab_work_task`.
    2. **Không tự nối vào chính mình** — chặn ở service.
    3. **Một cặp việc chỉ một mũi tên**, bất kể loại: unique
       `(predecessor_id, successor_id)`. Vẽ hai mũi tên chồng nhau giữa cùng một
       cặp thì nhìn như một, mà xóa mãi không hết.
    4. ⚠️ **KHÔNG được có vòng lặp** (A→B→C→A). Đây là thứ khóa ngoại không diễn
       đạt nổi, và tài liệu QLDA của Văn thư tự ghi nhận bên đó CHƯA chặn — nên
       `link_service.create_link` duyệt đồ thị trước khi ghi.

    `lag_days` là độ trễ (ngày) cộng vào mốc của việc sau; âm = chồng lấn. Hiện
    chỉ LƯU và hiện lên mũi tên, chưa có bộ dời lịch tự động — dời lịch dây
    chuyền là quyết định riêng, làm sau khi có ai đó thực sự cần.
    """

    __tablename__ = "tab_work_task_link"
    __table_args__ = (
        Index("uq_work_task_link", "predecessor_id", "successor_id", unique=True),
    )

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    list_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_list.id", ondelete="CASCADE"), index=True
    )
    predecessor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_task.id", ondelete="CASCADE"), index=True
    )
    successor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_task.id", ondelete="CASCADE"), index=True
    )
    link_type: Mapped[int] = mapped_column(SmallInteger, default=int(WorkLinkType.FS))
    lag_days: Mapped[int] = mapped_column(Integer, default=0)
