"""BỘ MÃ SỐ CỦA PHIÊN ĐĂNG NHẬP — theo R2/QĐ-11 (bao-CR-360, CR-312 P3a).

Ba cột phân loại của `tab_login_session` lưu `SMALLINT` + `IntEnum`; tiếng Việt
chỉ sống trong các `*_LABELS` và ở tầng hiển thị.

⚠️ **Ba bộ mã này KHÔNG có giá trị `0`.** Khác hẳn `employee/constants.py`, nơi
`0` nghĩa là *chưa khai*: một dòng phiên chỉ ra đời khi ai đó đăng nhập THẬT, nên
loại máy, cách đăng nhập đều biết ngay tại lúc ghi. Riêng loại máy không đoán
được thì có mã riêng **`9` = không rõ** — cố ý tách khỏi `0` để đọc dòng dữ liệu
là biết ngay *"đã xét mà chịu"* chứ không phải *"chưa ai điền"*.

`revoke_reason` thì để `NULL` khi phiên còn sống — `revoked_at IS NULL` là câu
hỏi "phiên còn hiệu lực không", nên đừng đẻ thêm một mã `0` nghĩa là chưa thu hồi.

Tài liệu gốc: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §4.4, §5.
"""
from enum import IntEnum


class DeviceType(IntEnum):
    """Loại máy, suy ra từ `User-Agent` (xem `core/device_fingerprint.py`)."""

    DESKTOP = 1
    MOBILE = 2
    TABLET = 3
    UNKNOWN = 9


DEVICE_TYPE_LABELS = {
    DeviceType.DESKTOP: "Máy tính",
    DeviceType.MOBILE: "Điện thoại",
    DeviceType.TABLET: "Máy tính bảng",
    DeviceType.UNKNOWN: "Không rõ",
}


class LoginMethod(IntEnum):
    """Cách người dùng vào hệ thống."""

    PASSWORD = 1
    GOOGLE = 2


LOGIN_METHOD_LABELS = {
    LoginMethod.PASSWORD: "Mật khẩu",
    LoginMethod.GOOGLE: "Google",
}


class RevokeReason(IntEnum):
    """Vì sao phiên bị cắt. Còn sống thì cột này `NULL`, không phải `0`."""

    SELF_LOGOUT = 1
    ADMIN_KICK = 2
    PASSWORD_CHANGED = 3
    FORCE_RELOGIN = 4
    ACCOUNT_LOCKED = 5


REVOKE_REASON_LABELS = {
    RevokeReason.SELF_LOGOUT: "Tự đăng xuất",
    RevokeReason.ADMIN_KICK: "Quản trị đá khỏi thiết bị",
    RevokeReason.PASSWORD_CHANGED: "Đổi mật khẩu",
    RevokeReason.FORCE_RELOGIN: "Bắt đăng nhập lại",
    RevokeReason.ACCOUNT_LOCKED: "Tài khoản bị khóa",
}

#  Tiết lưu dập `last_seen_at` (§4.4). Không có trần này thì mỗi lượt gọi API là
#  một lệnh UPDATE trên cùng một dòng — 3.000 lệnh ghi mỗi ngày để trả lời một
#  câu hỏi mà độ chính xác 5 phút là quá đủ.
LAST_SEEN_THROTTLE_SECONDS = 300

#  Đệm tra phiên trong tiến trình, cùng khuôn `_PERM_CACHE` của `core/auth.py`.
#  Đây là cái giá của việc đá được một thiết bị: hiệu lực **tối đa 60 giây**.
#  Đăng xuất mọi thiết bị thì KHÔNG qua đệm này — nó đi bằng `token_version`,
#  thứ đọc từ `tab_user` ở mọi lượt gọi (§5).
SESSION_CACHE_TTL_SECONDS = 60
