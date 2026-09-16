"""Bảng `tab_sync_log` — QUYỂN SỔ ĐỒNG BỘ DUY NHẤT của cả hệ thống.

Một bảng cho mọi hệ ngoài (POS365, app đặt xe / duyệt dấu cũ, sau này là đồng bộ
đơn hàng) và cho cả hai hạt dữ liệu:

* `grain = RUN`    — một LƯỢT CHẠY: con trỏ thời gian, đếm kéo/ghi/bỏ qua.
* `grain = RECORD` — một BẢN GHI đi qua, trỏ về lượt chạy sinh ra nó qua `run_id`.

Trước đây POS365 có bảng riêng `tab_pos_sync_run` còn app đặt xe định dựng bảng
riêng nữa. Bỏ hẳn lối đó: hai bảng nghĩa là hai màn hình, hai bộ mã trạng thái
lệch nhau (POS365 đánh RUNNING=1, bản kia đánh PENDING=1), và từ một lượt chạy
không bấm sang được những bản ghi nó vừa ghi. Một bảng thì `run_id` nối cha-con,
mã trạng thái chỉ còn một bộ, và thêm hệ nguồn mới không đẻ thêm bảng nào.

Ba luật bắt buộc của quyển sổ (doc/dong-bo-dat-xe-duyet-dau/mo-ta-ky-thuat.md §3.2),
vi phạm một điều là sổ mất tác dụng:

1. **Ghi trước khi làm, không phải ghi sau.** Nhận tín hiệu thì chèn ngay một dòng
   trạng thái *chờ* rồi mới xử lý. Ghi sau thì tiến trình chết giữa chừng không
   để lại dấu vết nào.
2. **Một dòng = một sự kiện, không ghi đè lịch sử.** Phiếu đổi trạng thái năm lần
   thì có năm dòng. Nhìn vào sổ phải dựng lại được câu chuyện.
3. **Không bao giờ xóa dòng lỗi.** Dọn sổ chỉ dọn dòng *thành công* cũ hơn sáu
   tháng, bằng một việc chạy nền riêng, và phải ghi lại đã dọn bao nhiêu dòng.
"""
from sqlalchemy import BigInteger, Index, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

from .constants import (
    ACTION_LABELS,
    DIRECTION_LABELS,
    GRAIN_LABELS,
    STATUS_LABELS,
    SyncAction,
    SyncDirection,
    SyncGrain,
    SyncStatus,
    WARNING_SEPARATOR,
)
from .registry import get_source, warning_labels


class SyncLog(Base, AuditMixin):
    __tablename__ = "tab_sync_log"

    # Mã hệ nguồn, khai ở `registry.py` (vd "datxe", "pos365").
    source: Mapped[str] = mapped_column(String(20), default="", index=True)
    # 1 lượt chạy · 2 bản ghi — xem SyncGrain.
    grain: Mapped[int] = mapped_column(
        SmallInteger, default=int(SyncGrain.RECORD), index=True)
    # Dòng RECORD trỏ về dòng RUN sinh ra nó. 0 = không sinh từ lượt chạy nào
    # (vd tín hiệu webhook bắn lẻ), hoặc chính dòng này là một lượt chạy.
    run_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    # 1 nhận về · 2 gửi đi — xem SyncDirection.
    direction: Mapped[int] = mapped_column(SmallInteger, default=int(SyncDirection.INBOUND))
    # Đối tượng đồng bộ, do từng nguồn tự khai (vd "vehicle_booking", "pos_order").
    entity: Mapped[str] = mapped_column(String(50), default="")
    # 1 tạo · 2 cập nhật · 3 đổi trạng thái · 4 xóa — xem SyncAction.
    action: Mapped[int] = mapped_column(SmallInteger, default=int(SyncAction.CREATE))

    # Mã bên hệ ngoài. KHÔNG unique: một bản ghi sinh nhiều dòng sổ theo thời gian.
    legacy_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    # Mã bên ERP. Bằng 0 khi chưa tạo được bản ghi tương ứng.
    local_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)

    # 1 chờ · 2 đang chạy · 3 thành công · 4 lỗi · 5 bỏ qua — xem SyncStatus.
    status: Mapped[int] = mapped_column(
        SmallInteger, default=int(SyncStatus.PENDING), index=True)
    # NGUYÊN VĂN câu trả lời hoặc câu lỗi của bên kia. Thành công thì ngắn;
    # lỗi thì đây là chỗ người vận hành đọc để hiểu chuyện gì xảy ra.
    message: Mapped[str] = mapped_column(Text, default="")
    # NGUYÊN CỤC dữ liệu: JSON bên kia gửi sang (dòng RECORD) hoặc kết quả chi
    # tiết của lượt chạy (dòng RUN, vd bảng lệch của vòng đối chiếu). MEDIUMTEXT
    # vì TEXT chỉ chứa 64KB, mà một phiếu kèm danh sách dòng có thể vượt.
    payload: Mapped[str] = mapped_column(
        Text().with_variant(MEDIUMTEXT(), "mysql"), default="")
    # Băm phần dữ liệu nghiệp vụ, để biết "có thật sự đổi gì không" -> bỏ qua.
    content_hash: Mapped[str] = mapped_column(String(64), default="")
    # Mã sự kiện, UNIQUE nên nhận lại lần hai là nhận ra ngay. Chiều nhận về thì
    # bên gửi sinh; chiều gửi đi và dòng RUN thì `service.make_event_id` sinh.
    # ⚠️ KHÔNG được để rỗng: MySQL coi mỗi chuỗi rỗng là một giá trị thật nên
    # dòng thứ hai sẽ đụng khóa. Luôn tạo dòng qua `service.py`.
    event_id: Mapped[str] = mapped_column(String(64), default="", unique=True)

    attempt_count: Mapped[int] = mapped_column(SmallInteger, default=0)
    # Chuỗi ISO, giờ Việt Nam. Với dòng RUN đây chính là lúc BẮT ĐẦU chạy.
    last_tried_at: Mapped[str] = mapped_column(String(20), default="")
    finished_at: Mapped[str] = mapped_column(String(20), default="")
    # Danh sách cờ cảnh báo ngăn bằng dấu phẩy — hằng số khai ở constants.py và
    # registry.py. Dòng THÀNH CÔNG vẫn có thể mang cờ; đó là cách lọc lại được
    # mọi bản ghi có dữ liệu bịa.
    warnings: Mapped[str] = mapped_column(String(255), default="")

    # --- Chỉ dòng RUN mới điền -------------------------------------------
    # Mã công việc của lượt chạy, do nguồn khai ở `registry.jobs`
    # (vd "pull_orders", "check_voids"). Dòng RECORD để rỗng.
    job: Mapped[str] = mapped_column(String(50), default="", index=True)
    # Con trỏ thời gian của lượt kéo. Chỉ TIẾN khi lượt đó thành công — hệ ngoài
    # sập thì chu kỳ sau tự kéo bù.
    cursor_from: Mapped[str] = mapped_column(String(30), default="")
    cursor_to: Mapped[str] = mapped_column(String(30), default="")
    fetched: Mapped[int] = mapped_column(Integer, default=0)
    written: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        # Màn hình sổ lọc theo nguồn + trạng thái rồi xếp mới nhất lên đầu.
        Index("ix_sync_log_source_status", "source", "status", "id"),
        # Tra "phiếu abcf đã đi qua những gì" — kể cả khi trùng mã giữa hai nguồn.
        Index("ix_sync_log_source_legacy", "source", "entity", "legacy_id"),
        # Mốc kéo lần trước: lượt chạy SUCCESS gần nhất của một công việc.
        Index("ix_sync_log_job_status", "source", "job", "status", "id"),
    )

    @property
    def grain_label(self) -> str:
        return GRAIN_LABELS.get(self.grain, "")

    @property
    def direction_label(self) -> str:
        return DIRECTION_LABELS.get(self.direction, "")

    @property
    def action_label(self) -> str:
        return ACTION_LABELS.get(self.action, "")

    @property
    def status_label(self) -> str:
        return STATUS_LABELS.get(self.status, "")

    @property
    def source_label(self) -> str:
        source = get_source(self.source)
        return source.label if source else self.source

    @property
    def entity_label(self) -> str:
        source = get_source(self.source)
        return source.entity_label(self.entity) if source else self.entity

    @property
    def job_label(self) -> str:
        source = get_source(self.source)
        return source.job_label(self.job) if source else self.job

    @property
    def warning_list(self) -> list[str]:
        return [f for f in (self.warnings or "").split(WARNING_SEPARATOR) if f]

    @property
    def warning_label_list(self) -> list[str]:
        labels = warning_labels(self.source if get_source(self.source) else "")
        return [labels.get(f, f) for f in self.warning_list]
