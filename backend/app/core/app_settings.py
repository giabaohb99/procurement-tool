"""Cấu hình hiệu lực (effective settings).
- Key thường: lưu DB (plaintext), DB ĐÈ .env.
- Key bí mật (SMTP password, R2 keys): lưu DB **đã mã hóa** (Fernet, khóa suy từ JWT_SECRET),
  API không bao giờ trả ngược giá trị (chỉ trạng thái đã cấu hình/chưa). .env là fallback.
Có cache in-process ngắn để tránh query mỗi lần.
"""
import base64
import hashlib
import time

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings as _env

# key DB → (kiểu, thuộc tính fallback .env) — sửa & hiển thị được
REGISTRY = {
    "email_enabled": ("bool", "EMAIL_ENABLED"),
    "smtp_host": ("str", "SMTP_HOST"),
    "smtp_port": ("int", "SMTP_PORT"),
    "smtp_from": ("str", "SMTP_FROM"),
    "smtp_user": ("str", "SMTP_USER"),
    "email_test_override": ("str", "EMAIL_TEST_OVERRIDE"),
    "r2_endpoint": ("str", "R2_ENDPOINT"),
    "r2_bucket": ("str", "R2_BUCKET"),
    "r2_public_url": ("str", "R2_PUBLIC_URL"),
    "pr_dispatch_enabled": ("bool", "PR_DISPATCH_ENABLED"),
    "pr_dispatch_skip_rules": ("str", "PR_DISPATCH_SKIP_RULES"),   # bao-CR-497
    "pr_options_enabled": ("bool", "PR_OPTIONS_ENABLED"),
    #  Cảnh báo mở/tải tệp đính kèm văn bản — sửa được ngay trên màn Cấu hình
    #  hệ thống, không cần deploy (đúng thứ cần khi đang có nghi vấn rò tài liệu).
    "doc_file_alert_threshold": ("int", "DOC_FILE_ALERT_THRESHOLD"),
    "doc_file_alert_window_min": ("int", "DOC_FILE_ALERT_WINDOW_MIN"),
    "doc_file_alert_recipients": ("str", "DOC_FILE_ALERT_RECIPIENTS"),
    #  Hạn XEM tệp đính kèm văn bản — TẠM TẮT (duoc-CR-478). Đọc ở MỘT chỗ duy
    #  nhất: `document/attachment_window.py view_window_expired()`.
    "doc_attachment_view_window_enabled": ("bool", "DOC_ATTACHMENT_VIEW_WINDOW_ENABLED"),
    #  Cụm Trợ lý AI (bao-CR-429). Khóa API là thứ NGƯỜI DÙNG tự đăng ký lấy về
    #  rồi tự dán vào — bắt họ mở SSH sửa .env là chặn đúng người đáng ra tự làm
    #  được. Model và trần câu hỏi cũng đổi luôn được vì chúng chỉ là lựa chọn
    #  chi phí, sai thì sửa lại, không hỏng dữ liệu.
    "ai_enabled": ("bool", "AI_ENABLED"),
    "ai_default_provider": ("str", "AI_DEFAULT_PROVIDER"),
    "ai_claude_model": ("str", "AI_CLAUDE_MODEL"),
    "ai_gemini_model": ("str", "AI_GEMINI_MODEL"),
    "ai_daily_msg_limit": ("int", "AI_DAILY_MSG_LIMIT"),
    "ai_lookup_model": ("str", "AI_LOOKUP_MODEL"),
    #  Cụm đồng bộ app đặt xe / duyệt dấu CŨ (bao-CR-429 nhịp 3). Đây đúng là chỗ
    #  cần sửa nóng nhất: khi đường máy-gọi-máy giữa hai hệ trục trặc thì thứ phải
    #  làm ngay là TẮT nó, mà tắt bằng `.env` nghĩa là sửa tệp rồi dựng lại dịch vụ.
    "sync_datxe_enabled": ("bool", "SYNC_DATXE_ENABLED"),
    "sync_legacy_api_base": ("str", "SYNC_LEGACY_API_BASE"),
    "sync_datxe_auto_create": ("bool", "SYNC_DATXE_AUTO_CREATE"),
    "legacy_firebase_db_url": ("str", "LEGACY_FIREBASE_DB_URL"),
    #  Cụm POS365 (Điểm cà phê).
    "pos365_base_url": ("str", "POS365_BASE_URL"),
    "pos365_username": ("str", "POS365_USERNAME"),
    "pos365_payment_account_id": ("int", "POS365_PAYMENT_ACCOUNT_ID"),
    #  Email của luồng duyệt — ba ô này vốn chỉ bật ở môi trường thử, tức đúng
    #  loại phải bật tắt liên tục mà không ai muốn deploy vì nó.
    "email_workflow_enabled": ("bool", "EMAIL_WORKFLOW_ENABLED"),
    "email_test_manager": ("str", "EMAIL_TEST_MANAGER"),
    "email_test_staff": ("str", "EMAIL_TEST_STAFF"),
    #  Thông số chung.
    "frontend_url": ("str", "FRONTEND_URL"),
    "notification_keep_days": ("int", "NOTIFICATION_KEEP_DAYS"),
    "backup_keep": ("int", "BACKUP_KEEP"),
}

#  BỐN khóa AI CỐ Ý ở lại `.env`, đừng dời theo cho đủ bộ:
#  `AI_EMBED_MODEL` + `AI_EMBED_DIM` — đổi là MỌI vector đã nhúng thành vô nghĩa
#  và phải dựng lại cả kho; một ô nhập trên màn hình không nói được cái giá đó.
#  `QDRANT_URL` + `AI_RAG_ENABLED` — gắn với việc container `qdrant` có chạy hay
#  không, tức chuyện của người dựng máy chứ không phải lựa chọn nghiệp vụ.

# key bí mật → thuộc tính fallback .env — NHẬP được nhưng không hiển thị lại
SECRETS = {
    "smtp_password": "SMTP_PASSWORD",
    "r2_access_key_id": "R2_ACCESS_KEY_ID",
    "r2_secret_access_key": "R2_SECRET_ACCESS_KEY",
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "gemini_api_key": "GEMINI_API_KEY",
    "sync_shared_secret": "SYNC_SHARED_SECRET",
    "legacy_firebase_secret": "LEGACY_FIREBASE_SECRET",
    "pos365_password": "POS365_PASSWORD",
}

#  Những khóa CỐ Ý ở lại `.env`, chia theo lý do (bao-CR-429 nhịp 3):
#
#  1. Dời xuống đây là NÓI DỐI, vì giá trị bị chụp lại lúc nạp module.
#     `BACKUP_ONCE_DAILY`, `SYNC_DATXE_PULL_MINUTES`, `POS365_PULL_MINUTES` và
#     `POS365_HARD_OFF` được đọc trong lúc dựng `beat_schedule` ở `celery_app.py`,
#     tức người dùng bấm Lưu xong màn hình báo thành công mà lịch chạy vẫn y
#     nguyên cho tới khi ai đó dựng lại `celery-beat`. Một ô không có tác dụng
#     còn tệ hơn không có ô nào.
#  2. Sai một lần là hỏng không cứu được: `STORAGE_PREFIX` (gõ nhầm thì tệp môi
#     trường thử ghi đè lên thư mục thật), `EMAIL_HARD_OFF` (cầu dao chặn thư ở
#     môi trường thử — để cùng chỗ với thứ nó chặn là mất ý nghĩa cầu dao),
#     `LEGACY_R2_*` (chỉ đọc kho tệp app cũ, đã cố ý không đi qua bảng này).
#  3. Không phải lựa chọn nghiệp vụ mà là chuyện dựng máy: `DB_*`, `JWT_SECRET`,
#     hạn thẻ ra vào, `CORS_ORIGINS`, `TRUSTED_PROXY_CIDRS`, `LOGIN_RATE_LIMIT`,
#     `ADMIN_*`, `SEED_*`, `DEV_MODE`, `REDIS_URL`.
#  4. `GOOGLE_CLIENT_ID` có BẢN SAO ở phía màn hình; sửa một bên là hai bên lệch
#     nhau và đăng nhập Google chết, nên phải sửa cả hai cùng lúc lúc deploy.
#  5. `SYNC_DEFAULT_COMPANY_ID` và `SYNC_NOTIFY_ON_IMPORT` KHÔNG có chỗ nào đọc —
#     bày lên màn hình là hứa một nút không nối vào đâu cả. Đáng chú ý:
#     `SYNC_NOTIFY_ON_IMPORT` tự mô tả là chặn bão thông báo lúc nạp hàng loạt,
#     nhưng cái chặn đó chưa từng được viết.

_cache: dict = {}
_exp = 0.0
_TTL = 30.0


def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(_env.JWT_SECRET.encode()).digest())
    return Fernet(key)


def encrypt(s: str) -> str:
    return _fernet().encrypt(s.encode()).decode()


def _decrypt(s: str) -> str:
    try:
        return _fernet().decrypt(s.encode()).decode()
    except (InvalidToken, Exception):
        return ""


def _load():
    global _cache, _exp
    from app.core.database import SessionLocal
    from app.modules.setting.model import Setting
    db = SessionLocal()
    try:
        _cache = {s.skey: s.svalue for s in db.query(Setting).all()}
    finally:
        db.close()
    _exp = time.time() + _TTL


def refresh():
    global _exp
    _exp = 0.0


def _cast(t: str, raw: str):
    if t == "bool":
        return str(raw).strip().lower() in ("1", "true", "yes", "on")
    if t == "int":
        try:
            return int(raw)
        except (ValueError, TypeError):
            return 0
    return raw


def get(key: str):
    """Giá trị hiệu lực: DB (nếu có) → .env. Secret được giải mã khi trả về (chỉ dùng nội bộ)."""
    if time.time() > _exp:
        _load()
    raw = _cache.get(key)
    if key in SECRETS:
        if raw not in (None, ""):
            dec = _decrypt(raw)
            if dec:
                return dec
        return getattr(_env, SECRETS[key], "")
    if key in REGISTRY:
        t, env_attr = REGISTRY[key]
        if raw not in (None, ""):
            return _cast(t, raw)
        return getattr(_env, env_attr)
    return getattr(_env, key.upper(), None)


def secret_configured(key: str) -> bool:
    if time.time() > _exp:
        _load()
    if _cache.get(key):
        return True
    return bool(getattr(_env, SECRETS.get(key, ""), ""))
