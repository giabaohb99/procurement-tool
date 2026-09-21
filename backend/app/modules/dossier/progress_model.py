"""TIẾN ĐỘ một tờ hồ sơ TRÊN MỘT CHỨNG TỪ — `tab_dossier_progress` (21/09/2026).

⚠️ **Đây là thứ tách «đã có giấy trong kho» khỏi «đã xong cho phiếu này».**
Trước bảng này, thẻ *Hồ sơ cần hoàn thành* đọc thẳng `tab_dossier.status`, nên
tick xong ở một tờ YCBG là hai chục phiếu khác cũng hiện «đã xong» — con số
tiến độ của mọi phiếu giống hệt nhau và không nói lên điều gì.

Ranh giới giữa hai bảng, đọc kỹ trước khi thêm cột:

* **Thuộc về TỜ GIẤY** → ở `tab_dossier`: tên, loại, ngày cấp, hạn hiệu lực,
  nơi lưu bản gốc, người giữ hồ sơ. Đổi một lần, đúng cho mọi phiếu.
* **Thuộc về VIỆC LÀM HỒ SƠ CHO PHIẾU NÀY** → ở đây: tới đâu rồi, ai đang làm,
  hẹn xong hôm nào, ghi chú riêng, tệp đã nộp cho phiếu này.

Hạn hiệu lực KHÔNG nằm ở đây dù khối *Báo cáo thực hiện* có cột đó: một tờ giấy
chỉ có một ngày hết hạn, chép nó xuống từng phiếu là dựng ra n bản của cùng một
sự thật rồi chờ chúng lệch nhau.

⚠️ **Dòng chỉ sinh ra khi có người ĐỘNG VÀO.** Không có dòng = «Chưa bắt đầu,
bắt buộc, chưa ai nhận» — đúng mặc định, nên không đi đẻ sẵn n×m dòng rỗng lúc
mở phiếu. Xem `progress_service.merge`.
"""
from datetime import date

from sqlalchemy import (BigInteger, Boolean, Date, SmallInteger, String,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

from .constants import DP_IDLE


class DossierProgress(Base, AuditMixin):
    __tablename__ = "tab_dossier_progress"
    __table_args__ = (
        #  ⚠️ Ràng buộc DUY NHẤT là chốt chống ghi trùng, không phải để tra cho
        #  nhanh. Thiếu nó thì hai lượt bấm gần nhau (mạng chậm, bấm đúp) đẻ ra
        #  hai dòng cho cùng một ô tick, và lần đọc sau lấy trúng dòng nào là
        #  tùy thứ tự của MySQL — trạng thái nhảy qua lại không lý do.
        UniqueConstraint("doc_kind", "doc_id", "dossier_id", name="uq_dossier_progress"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    #  CHỨNG TỪ mang tờ hồ sơ này. `doc_kind` là mã CHUỖI cố định
    #  (`purchase_request | purchase_order | survey_request | survey`) — cùng bộ
    #  với `applicability.DOC_KINDS`, không phải mã số: nó là khóa định tuyến
    #  sang bốn bảng khác nhau, đọc thẳng trong log và câu SQL mới lần ra được.
    doc_kind: Mapped[str] = mapped_column(String(30), index=True)
    doc_id: Mapped[int] = mapped_column(BigInteger, index=True)
    #  Tờ hồ sơ trong kho. Không khai FK, cùng nếp với phần còn lại của repo.
    dossier_id: Mapped[int] = mapped_column(BigInteger, index=True)

    #  Bộ mã DP_* (4 mức) — KHÁC thang của `tab_dossier.status`, xem `constants.py`.
    status: Mapped[int] = mapped_column(SmallInteger, default=DP_IDLE, index=True)
    #  Tờ giấy này có bắt buộc với PHIẾU NÀY không. Cùng một tờ có thể bắt buộc
    #  ở đơn nhập khẩu mà không bắt buộc ở đơn mua trong nước — nên cờ nằm ở
    #  đây chứ không nằm trên tờ hồ sơ.
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    assignee_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  Hẹn xong hôm nào CHO PHIẾU NÀY. Khác hẳn `expiry_date` của tờ giấy.
    planned_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    #  Ghi chú riêng của phiếu — KHÔNG đè `tab_dossier.note` (mô tả dùng chung).
    note: Mapped[str] = mapped_column(String(1000), default="")
    #  Tên tệp hoặc link bản đã nộp cho phiếu này.
    file_note: Mapped[str] = mapped_column(String(500), default="")
