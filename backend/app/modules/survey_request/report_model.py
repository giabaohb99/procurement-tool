"""Các bảng của KHỐI BÁO CÁO THỰC HIỆN — dùng chung cho YCBG và ĐMH (bao-CR-602).

NS Thu mua theo dõi tiến trình thực thi một thương vụ (giấy phép, hợp đồng,
chứng từ vận chuyển, thông quan…) ngay trên chứng từ: hồ sơ chia theo GIAI
ĐOẠN, lọc theo NÚT DÒNG HÀNG, mỗi hồ sơ có trạng thái + danh sách tiên quyết.

Từ bao-CR-602 khối không còn là của riêng phiếu YCBG: thêm bảng ĐẦU
`tab_exec_report(owner_entity, owner_id)` — mỗi chứng từ chủ (YCBG, ĐMH) có
nhiều nhất MỘT đầu báo cáo, bốn bảng con nối vào đầu đó bằng `report_id`.
Dữ liệu YCBG cũ: migration dựng đầu với `id = id phiếu` nên cột khóa của bảng
con chỉ ĐỔI TÊN (`survey_request_id` → `report_id`), không chép dòng nào.

Bảng con là **chi tiết của chứng từ cha** — không có màn danh sách riêng,
không có mã chứng từ, nên KHÔNG có khóa phân quyền riêng (luật «một khóa = một
màn hình», CR-157). Chốt là hai lớp của chứng từ cha: phạm vi qua `_in_scope`
của controller cha → 404 ngoài phạm vi, rồi cờ ghi của cha
(`survey_request.process` / `purchase_order.write`) cho cửa GHI.
"""
from datetime import date

from sqlalchemy import (JSON, BigInteger, Boolean, Date, SmallInteger, String, Text,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

#  Chứng từ chủ được phép mang khối báo cáo. Giá trị lưu ở `ExecReport.owner_entity`
#  trùng tên entity phân quyền để controller tra luật theo cùng một chuỗi.
REPORT_OWNER_SURVEY_REQUEST = "survey_request"
REPORT_OWNER_PURCHASE_ORDER = "purchase_order"
REPORT_OWNER_ENTITIES = (REPORT_OWNER_SURVEY_REQUEST, REPORT_OWNER_PURCHASE_ORDER)


class ExecReport(Base, AuditMixin):
    """ĐẦU của một khối báo cáo — «chứng từ nào sở hữu khối này».

    Chỉ giữ cặp (`owner_entity`, `owner_id`); nội dung nằm ở ba bảng con. Tạo
    LƯỜI: chứng từ chưa ai bấm gì vào khối báo cáo thì không có dòng đầu.
    """

    __tablename__ = "tab_exec_report"
    __table_args__ = (UniqueConstraint("owner_entity", "owner_id", name="uq_exec_report_owner"),)

    owner_entity: Mapped[str] = mapped_column(String(32), default=REPORT_OWNER_SURVEY_REQUEST)
    owner_id: Mapped[int] = mapped_column(BigInteger, index=True)
    #  Mẫu đã chọn lúc «Khởi tạo báo cáo mẫu» (duoc-CR-614) — mã `RT_*` ở
    #  `report_constants.REPORT_TEMPLATES`. Nút «Tạo mẫu» đọc lại cột này để đổ ĐÚNG mẫu
    #  của khối. Khối cũ (trước CR) = 1 = mẫu chung, đúng với thứ chúng đã được đổ.
    template: Mapped[int] = mapped_column(SmallInteger, default=1, server_default="1")


class SurveyReportItem(Base, AuditMixin):
    """Một NÚT lọc theo dòng hàng trên khối báo cáo (vd «K₂SO₄», «KNO₃»).

    Là bảng chứ không suy từ dòng chứng từ: trên YCBG người dùng được thêm/sửa/
    xóa nút và đặt tên tùy ý (một nút có thể gom nhiều dòng, hoặc chẳng ứng với
    dòng nào). Trên ĐMH (bao-CR-602) nút SINH TỰ ĐỘNG theo dòng đơn — `line_id`
    là id dòng chứng từ (`tab_po_item.id`), service đồng bộ mỗi lần đọc: dòng
    mới thì thêm nút, đổi tên hàng thì đổi tên nút, dòng bị xóa thì xóa nút (hồ
    sơ của nó về Chung). Hồ sơ không gắn nút nào (`item_id = 0`) là hồ sơ CHUNG.
    """

    __tablename__ = "tab_exec_report_item"

    report_id: Mapped[int] = mapped_column(BigInteger, index=True)
    name: Mapped[str] = mapped_column(String(100), default="")
    #  Id dòng chứng từ mà nút này bám theo; 0 = nút đặt tay (YCBG). Cố ý không
    #  FK: nút là của khối báo cáo, dòng chứng từ mất thì service tự dọn.
    line_id: Mapped[int] = mapped_column(BigInteger, default=0)
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)


class SurveyReportPhase(Base, AuditMixin):
    """Một GIAI ĐOẠN của báo cáo (vd «Pháp lý & Giấy phép»). Hồ sơ xếp theo nó."""

    __tablename__ = "tab_exec_report_phase"

    report_id: Mapped[int] = mapped_column(BigInteger, index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    location: Mapped[str] = mapped_column(String(255), default="")   # nơi/diễn giải ngắn
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)


class SurveyReportDoc(Base, AuditMixin):
    """Một HỒ SƠ cần hoàn thành trong báo cáo — đơn vị nhỏ nhất của khối."""

    __tablename__ = "tab_exec_report_doc"

    report_id: Mapped[int] = mapped_column(BigInteger, index=True)
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
    #  KẾT QUẢ / ghi chú sau khi làm (cột «Kết quả» của bảng kế hoạch Excel thu
    #  mua, bao-CR-602) — khác `description` (việc PHẢI làm, ghi trước khi làm).
    result: Mapped[str] = mapped_column(String(1000), default="")
    #  Danh sách id hồ sơ TIÊN QUYẾT (cùng khối). Hồ sơ bị KHÓA khi còn tiên
    #  quyết chưa Hoàn thành — cách khóa do tầng hiển thị + service suy, không
    #  lưu cờ. Trần số phần tử chặn ở schema (`MAX_DEPENDS`).
    depends: Mapped[list] = mapped_column(JSON, default=list)
    #  Ngày BẮT ĐẦU thực hiện / ngày HẾT HIỆU LỰC — NULL = chưa đặt. Cột ngày
    #  trần (không giờ, không múi): hạn hồ sơ đọc theo ngày, quy đổi múi giờ là
    #  dễ lệch một ngày (xem `format-date` phía FE).
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    expires_at: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    #  Ngày DỰ ĐỊNH HOÀN TẤT (kế hoạch ban đầu, bao-CR-392) — khác `expires_at`
    #  (hạn hiệu lực của giấy tờ). Hồ sơ chưa Hoàn thành mà qua ngày này là TRỄ
    #  so với kế hoạch; FE suy nhãn «Trễ n ngày», không lưu cờ.
    planned_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    #  Nhân sự THỰC HIỆN (id `tab_employee`). 0 = chưa cử. Cố ý không FK: xóa
    #  nhân sự không xóa lây hồ sơ; tên hiển thị resolve lúc đọc, id chết ra
    #  chuỗi rỗng. FE điền sẵn nhân sự của người tạo, đổi được.
    assignee_id: Mapped[int] = mapped_column(BigInteger, default=0)
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)


class SurveyReportTrash(Base, AuditMixin):
    """SỌT RÁC của khối báo cáo — cho phép HOÀN TÁC lần «Xóa báo cáo thực hiện».

    Xóa cả khối là thao tác nặng (mất hàng chục hồ sơ nhập tay), nên trước khi
    xóa, toàn bộ khối được chụp thành `snapshot` JSON và giữ ở đây. Người dùng
    bấm «Hoàn tác» trên đúng dòng Lịch sử thao tác thì dựng lại từ ảnh chụp này.

    Cùng khuôn với `tab_import_change.snapshot` của `import_tool` (revert theo
    ảnh chụp). Không xóa vật lý dòng trash — giữ làm dấu vết; `restored` đánh dấu
    đã khôi phục để không hoàn tác hai lần.
    """

    __tablename__ = "tab_exec_report_trash"

    report_id: Mapped[int] = mapped_column(BigInteger, index=True)
    #  Ảnh chụp {items, phases, docs} ĐẦY ĐỦ (kèm id cũ để dựng lại `depends`).
    snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    doc_count: Mapped[int] = mapped_column(SmallInteger, default=0)
    #  Nối tới dòng Lịch sử thao tác của lần xóa — FE hiện nút «Hoàn tác» đúng
    #  dòng đó (khớp theo id). 0 = chưa gắn.
    audit_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    restored: Mapped[bool] = mapped_column(Boolean, default=False)
