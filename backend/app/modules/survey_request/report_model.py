"""Ba bảng của KHỐI BÁO CÁO THỰC HIỆN trên phiếu Yêu cầu báo giá (YCBG).

NS Thu mua theo dõi tiến trình thực thi một thương vụ (giấy phép, hợp đồng,
chứng từ vận chuyển, thông quan…) ngay trên phiếu YCBG: hồ sơ chia theo GIAI
ĐOẠN, lọc theo NÚT DÒNG HÀNG, mỗi hồ sơ có trạng thái + danh sách tiên quyết.

Cả ba đều là **chi tiết của phiếu YCBG cha** — không có màn danh sách riêng,
không có mã chứng từ, nên KHÔNG có khóa phân quyền riêng (luật «một khóa = một
màn hình», CR-157). Chốt là hai lớp của phiếu cha: phạm vi qua `_in_scope`
(controller YCBG) → 404 ngoài phạm vi, rồi cờ `process` (NS Thu mua) cho cửa GHI.
"""
from sqlalchemy import JSON, BigInteger, Boolean, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class SurveyReportItem(Base, AuditMixin):
    """Một NÚT lọc theo dòng hàng trên khối báo cáo (vd «K₂SO₄», «KNO₃»).

    Là bảng chứ không suy từ `tab_survey_request_line`: người dùng được
    thêm/sửa/xóa nút và đặt tên tùy ý (một nút có thể gom nhiều dòng, hoặc
    chẳng ứng với dòng nào). Hồ sơ không gắn nút nào (`item_id = 0`) là hồ sơ
    CHUNG — hiện ở mọi nút.
    """

    __tablename__ = "tab_survey_request_report_item"

    survey_request_id: Mapped[int] = mapped_column(BigInteger, index=True)
    name: Mapped[str] = mapped_column(String(100), default="")
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)


class SurveyReportPhase(Base, AuditMixin):
    """Một GIAI ĐOẠN của báo cáo (vd «Pháp lý & Giấy phép»). Hồ sơ xếp theo nó."""

    __tablename__ = "tab_survey_request_report_phase"

    survey_request_id: Mapped[int] = mapped_column(BigInteger, index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    location: Mapped[str] = mapped_column(String(255), default="")   # nơi/diễn giải ngắn
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)


class SurveyReportDoc(Base, AuditMixin):
    """Một HỒ SƠ cần hoàn thành trong báo cáo — đơn vị nhỏ nhất của khối."""

    __tablename__ = "tab_survey_request_report_doc"

    survey_request_id: Mapped[int] = mapped_column(BigInteger, index=True)
    phase_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    #  0 = hồ sơ CHUNG (mọi nút dòng hàng). Cố ý không FK: xóa nút thì service
    #  trả hồ sơ về 0 chứ không xóa lây hồ sơ.
    item_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    required: Mapped[bool] = mapped_column(Boolean, default=True)     # Bắt buộc?
    #  MÃ SỐ — xem `report_constants.REPORT_DOC_STATUS_LABELS` (R2/QĐ-11).
    status: Mapped[int] = mapped_column(SmallInteger, default=0, index=True)
    #  Tên tệp hoặc link tài liệu (Drive…) — chữ tự do, chưa nối kho đính kèm.
    file_note: Mapped[str] = mapped_column(String(500), default="")
    #  Danh sách id hồ sơ TIÊN QUYẾT (cùng phiếu). Hồ sơ bị KHÓA khi còn tiên
    #  quyết chưa Hoàn thành — cách khóa do tầng hiển thị + service suy, không
    #  lưu cờ. Trần số phần tử chặn ở schema (`MAX_DEPENDS`).
    depends: Mapped[list] = mapped_column(JSON, default=list)
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)
