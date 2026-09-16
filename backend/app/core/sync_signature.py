"""Chữ ký chia sẻ giữa ERP và các hệ ngoài (máy nói với máy, KHÔNG phải token người dùng).

Cách ký: `HMAC-SHA256(secret, "<timestamp>.<path>.<body>")` viết dạng hex. Bên nhận
ký lại đúng công thức rồi so bằng `hmac.compare_digest` — **đừng bao giờ so bằng
`==`**, so chuỗi thường rò rỉ thời gian và mở đường dò từng ký tự.

Hai chốt nữa, thiếu là chữ ký vô dụng:

- **Lệch giờ quá 5 phút thì từ chối.** Không chốt thì kẻ nghe lén bắt được một
  yêu cầu hợp lệ là phát lại được mãi mãi.
- **Khóa theo TỪNG NGUỒN.** Mỗi hệ ngoài khai `secret_setting` riêng trong
  `modules/sync_log/registry.py`; khóa nằm ở `.env` hai đầu, không commit, dev
  khác prod. Lộ khóa của một hệ thì chỉ hệ đó phải xoay.
"""
import hashlib
import hmac
import time

from app.modules.sync_log.constants import SIGNATURE_MAX_SKEW_SECONDS
from app.modules.sync_log.registry import get_source

HEADER_SOURCE = "X-Sync-Source"
HEADER_TIMESTAMP = "X-Sync-Timestamp"
HEADER_SIGNATURE = "X-Sync-Signature"


def build_signature(secret: str, timestamp: str, path: str, body: str = "") -> str:
    """Ký một cục dữ liệu. Tách riêng để test được mà không cần settings."""
    payload = f"{timestamp}.{path}.{body}".encode("utf-8")
    return hmac.new((secret or "").encode("utf-8"), payload, hashlib.sha256).hexdigest()


def sign_headers(source_code: str, path: str, body: str = "") -> dict[str, str]:
    """Bộ header để GỬI ĐI. Nguồn chưa khai hoặc chưa có khóa thì ném lỗi ngay
    thay vì lặng lẽ ký bằng chuỗi rỗng."""
    source = get_source(source_code)
    if source is None:
        raise ValueError(f"Hệ nguồn '{source_code}' chưa được khai trong registry")
    secret = source.secret()
    if not secret:
        raise ValueError(
            f"Hệ nguồn '{source_code}' chưa có khóa ký ({source.secret_setting} trong .env)")
    timestamp = str(int(time.time()))
    return {
        HEADER_SOURCE: source.code,
        HEADER_TIMESTAMP: timestamp,
        HEADER_SIGNATURE: build_signature(secret, timestamp, path, body),
    }


def verify_signature(
    source_code: str,
    path: str,
    body: str,
    timestamp: str,
    signature: str,
    now: float | None = None,
) -> tuple[bool, str]:
    """Kiểm chữ ký của yêu cầu NHẬN VỀ.

    Trả `(hợp lệ, lý do)`. Lý do là câu tiếng Việt ghi thẳng vào sổ; cố ý KHÔNG
    nói rõ chữ ký sai ở chỗ nào.
    """
    source = get_source(source_code)
    if source is None:
        return False, "Hệ nguồn không hợp lệ"
    if not source.is_enabled():
        return False, "Hệ nguồn đang tắt đồng bộ"
    secret = source.secret()
    if not secret:
        return False, "Hệ nguồn chưa cấu hình khóa ký"
    if not timestamp or not signature:
        return False, "Thiếu header chữ ký"
    try:
        sent_at = int(timestamp)
    except (TypeError, ValueError):
        return False, "Dấu thời gian không hợp lệ"
    current = int(now if now is not None else time.time())
    if abs(current - sent_at) > SIGNATURE_MAX_SKEW_SECONDS:
        return False, "Dấu thời gian lệch quá xa"
    expected = build_signature(secret, timestamp, path, body)
    #  LƯU Ý: `hmac.compare_digest` NÉM TypeError khi chuỗi có ký tự ngoài ASCII —
    #  gửi một header chữ ký chứa tiếng Việt là đổ 500 thay vì bị từ chối gọn.
    #  So bằng BYTES để mọi rác đều đi hết đường và ra cùng một câu trả lời.
    if not hmac.compare_digest(expected.encode("utf-8"),
                               (signature or "").encode("utf-8")):
        return False, "Chữ ký không khớp"
    return True, ""
