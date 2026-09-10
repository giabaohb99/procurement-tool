"""`tab_login_session` — mỗi lần đăng nhập THÀNH CÔNG một dòng (bao-CR-360, P3a).

Đây là thứ đóng **BM-002**: hôm nay JWT không có phiên phía máy chủ, nên bấm
*Đăng xuất* chỉ xóa token ở trình duyệt — vé vẫn sống tới hết hạn, refresh token
bị cắp thì sống bảy ngày, và không ai trả lời được câu *"tài khoản này đang đăng
nhập ở những máy nào"*.

Không dùng `AuditMixin`: bảng này không có người "sửa", chỉ có chính hệ thống dập
`last_seen_*` / `refreshed_at` / `revoked_*`, nên `updated_by` là cột chết. `id`
và `created_at` khai tay; `created_at` chính là **giờ đăng nhập**.

⚠️ **Đăng nhập THẤT BẠI không vào bảng này** (Q5). Nó đã có một dòng
`tab_request_log` (`/api/auth/login`, `http_status=401`) cộng một dòng
`tab_audit_log` (`action=login_failed`). Đổ thất bại vào đây thì bảng phiên —
thứ người dùng nhìn thẳng ở màn *Thiết bị của tôi* — đầy rác của người đang dò
mật khẩu, mà câu hỏi *"IP nào thử nhiều tài khoản"* thì `tab_request_log` trả
lời gọn hơn bằng một `GROUP BY ip`.

Tài liệu gốc: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §4.4, §5.
"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base


class LoginSession(Base):
    __tablename__ = "tab_login_session"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)

    #  Khóa nối giữa vé và phiên: giá trị này nằm trong claim `jti` của CẢ access
    #  lẫn refresh token. Giữ `CHAR(36)` chứ không đổi nhị phân như `request_id`
    #  (QĐ-B): claim JWT buộc phải là chuỗi, mà bảng này chỉ ~2.000 dòng/năm nên
    #  đổi kiểu chẳng tiết kiệm gì, chỉ thêm một chỗ phải chuyển đi chuyển lại.
    token_id: Mapped[str] = mapped_column(String(36), default="", unique=True)
    #  Chép từ `tab_user.token_version` lúc đăng nhập. Giữ ở đây để đọc một dòng
    #  phiên là biết nó thuộc "đời" nào, khỏi phải đoán bằng cách so với giá trị
    #  hiện tại của người dùng — thứ đã đổi mất rồi.
    token_version: Mapped[int] = mapped_column(SmallInteger, default=1)

    ip: Mapped[str] = mapped_column(String(45), default="")     # IPv6 dài 45, đừng để 15
    #  ⚠️ Ở ĐÂY thì lưu `User-Agent` NGUYÊN VĂN, khác `tab_request_log` (chỗ đó
    #  cố ý chỉ giữ dấu băm 8 byte). Lý do là nhịp ghi: bảng này mỗi lần đăng
    #  nhập một dòng (~6 dòng/ngày), còn bảng kia mỗi lượt gọi một dòng
    #  (~3.000/ngày). Cùng một chuỗi 150 byte, ở đây tốn ~1 MB/năm và cho biết
    #  ĐÚNG bản trình duyệt; ở kia tốn ~200 MB để lưu đi lưu lại vài chục giá
    #  trị giống hệt nhau.
    user_agent: Mapped[str] = mapped_column(String(500), default="")
    device_type: Mapped[int] = mapped_column(SmallInteger, default=9)   # DeviceType
    os: Mapped[str] = mapped_column(String(60), default="")
    browser: Mapped[str] = mapped_column(String(60), default="")
    #  Chuỗi hiện cho NGƯỜI đọc ở màn «Thiết bị của tôi» (P3b). Dựng sẵn lúc ghi
    #  chứ không ghép lúc đọc: ba mảnh ở trên là mã để LỌC, còn câu này là thứ
    #  người dùng nhìn để nhận ra máy của mình.
    device_label: Mapped[str] = mapped_column(String(120), default="")
    login_method: Mapped[int] = mapped_column(SmallInteger, default=1)  # LoginMethod

    #  Dập ở MIDDLEWARE, không phải ở dependency (QĐ-D) — tiết lưu 5 phút.
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    #  Phiên đổi IP giữa chừng là dấu hiệu đáng xem (cảnh báo ở P6). Muốn so thì
    #  phải giữ CẢ HAI: `ip` là lúc đăng nhập, cột này là gần nhất.
    last_seen_ip: Mapped[str] = mapped_column(String(45), default="")

    #  QĐ-A: gia hạn phiên THÀNH CÔNG không đẻ dòng nhật ký nữa, chỉ dập hai cột
    #  này. Số đếm cộng mốc thời gian đủ trả lời "phiên sống bao lâu, gia hạn mấy
    #  lần" mà không tốn 46.000 dòng rác mỗi năm.
    refreshed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    refresh_count: Mapped[int] = mapped_column(Integer, default=0)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)

    #  `revoked_at IS NULL` = phiên còn hiệu lực. Đừng thêm cột `is_active` song
    #  song: hai nguồn sự thật cho một câu hỏi thì sớm muộn lệch nhau.
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    revoked_by: Mapped[int] = mapped_column(BigInteger, default=0)   # 0 = chính hệ thống
    revoke_reason: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)  # RevokeReason
