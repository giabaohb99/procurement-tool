"""`tab_request_log` — LỚP MÁY: mỗi lượt gọi một dòng (bao-CR-312, P1).

Đây là lớp trả lời *"endpoint nào, ai gọi, gửi gì, nhận lại gì, từ IP nào, mất
bao lâu"* — và quan trọng nhất: **lượt BỊ CHẶN**. Hôm nay một cú `DELETE` ăn
403 không để lại dấu vết nào ở đâu cả, vì `record(...)` nằm sau cửa quyền nên
chưa kịp chạy.

Không dùng `AuditMixin`: bảng này chỉ THÊM, không bao giờ sửa, nên
`updated_at` / `updated_by` là hai cột chết trên vài trăm nghìn dòng mỗi năm.
`created_by` cũng bỏ — người gọi đã nằm ở `user_id`, để hai cột cùng nghĩa là
sớm muộn có chỗ đọc nhầm cột.

Tài liệu gốc: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §4.1.
"""
from datetime import datetime

from sqlalchemy import BINARY, JSON, BigInteger, DateTime, Integer, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base
from app.core.logging_codes import SOURCE_API


class RequestLog(Base):
    __tablename__ = "tab_request_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    #  QĐ-B (§4.5): `BINARY(16)` chứ không `CHAR(36)`. Đây là cột duy nhất có
    #  mặt VÀ có chỉ mục ở cả ba bảng nhật ký, nên mỗi byte nhân lên ba lần —
    #  đổi kiểu sau, lúc bảng đã vài trăm nghìn dòng, là một cuộc `ALTER` dài.
    request_id: Mapped[bytes] = mapped_column(BINARY(16), unique=True)
    source: Mapped[int] = mapped_column(SmallInteger, default=SOURCE_API)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)  # 0 = chưa đăng nhập
    session_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)  # P3
    ip: Mapped[str] = mapped_column(String(45), default="", index=True)  # IPv6 dài 45, đừng để 15

    method: Mapped[str] = mapped_column(String(8), default="")
    path: Mapped[str] = mapped_column(String(300), default="")
    #  Mẫu route (`/api/purchase-orders/{id}/items/{item_id}`) — để gom câu hỏi
    #  "endpoint này ai gọi"; `path` thì mỗi lượt một giá trị khác nhau.
    route: Mapped[str] = mapped_column(String(200), default="", index=True)
    query_string: Mapped[str] = mapped_column(String(1000), default="")

    #  `none_as_null`: không có thân thì để NULL của SQL, đừng ghi chuỗi JSON
    #  `null` — nếu không thì `WHERE request_body IS NULL` không khớp gì cả và
    #  người đi tra tưởng mọi lượt đều có thân.
    request_body: Mapped[dict | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    http_status: Mapped[int] = mapped_column(SmallInteger, default=0, index=True)
    #  Q9: chỉ giữ nguyên văn khi KHÔNG phải 2xx; 2xx chỉ giữ `message` + `data.id`.
    response_body: Mapped[dict | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    error_code: Mapped[str] = mapped_column(String(60), default="")
    #  Q12: traceback của 5xx, cắt 16 KB — để tra trên màn thay vì chui vào
    #  `docker logs`, nơi vết trôi mất sau vài ngày.
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    audit_count: Mapped[int] = mapped_column(SmallInteger, default=0)
    change_count: Mapped[int] = mapped_column(SmallInteger, default=0)
