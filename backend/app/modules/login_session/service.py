"""PHIÊN ĐĂNG NHẬP — mở, tra, dập dấu vết, thu hồi (bao-CR-360, CR-312 P3a).

Chia đôi theo **QĐ-D** (§11 của tài liệu gốc), và ranh giới đó là cả thiết kế:

- **Cửa chặn** (`resolve_session`) được gọi từ `core/auth.get_current_user` — chỗ
  duy nhất trong hệ biết lượt gọi này có cần đăng nhập hay không, và là chỗ được
  phép ném 401.
- **Dập dấu vết** (`touch_session`) được gọi từ `core/request_middleware` sau khi
  endpoint chạy xong — việc GHI, hỏng thì nuốt, không ảnh hưởng ai.

Hai nửa nối nhau bằng `RequestContext.session_id`.

⚠️ **Đệm tra phiên là một đánh đổi có chủ ý, không phải tối ưu vặt.** Không đệm
thì mỗi lượt gọi API thêm một truy vấn; đệm 60 giây thì *đá một thiết bị* có độ
trễ tối đa 60 giây. Chỗ cần hiệu lực TỨC THÌ — khóa tài khoản, đăng xuất mọi
thiết bị — đều đi bằng đường khác: `is_active` và `token_version` là cột của
`tab_user`, mà `get_current_user` đằng nào cũng đọc `tab_user` mỗi lượt gọi.

Tài liệu gốc: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §4.4, §5, §11.
"""
import logging
import time
import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.device_fingerprint import MAX_USER_AGENT, normalize_user_agent
from app.modules.login_session.constants import (LAST_SEEN_THROTTLE_SECONDS, LoginMethod,
                                                 RevokeReason, SESSION_CACHE_TTL_SECONDS,
                                                 DeviceType)
from app.modules.login_session.model import LoginSession

log = logging.getLogger("app.login_session")

#  {token_id: (session_id, user_id, expires_at)} — session_id = 0 nghĩa là ĐÃ
#  tra và phiên KHÔNG còn hiệu lực. Đệm cả câu trả lời "không" mới có tác dụng:
#  vé của một phiên đã bị đá thường bị thử lại liên tục cho tới khi client chịu
#  đăng xuất, và mỗi lần thử mà đi xuống DB thì đúng lúc bị tấn công là lúc tốn
#  truy vấn nhất.
_SESSION_CACHE: dict[str, tuple[int, int, float]] = {}

#  {session_id: mốc dập gần nhất} — tiết lưu `last_seen_at`. Dùng `monotonic`
#  chứ không `time()`: đồng hồ hệ thống nhảy lùi (NTP) thì cả tiết lưu đứng hình.
_LAST_TOUCH_AT: dict[int, float] = {}


def session_cache_clear(token_id: str | None = None) -> None:
    """Xóa đệm tra phiên — gọi ngay sau mọi lệnh thu hồi.

    Trong MỘT tiến trình thì đá thiết bị có hiệu lực tức thì nhờ hàm này; độ trễ
    60 giây ở §5 là nói về các tiến trình uvicorn KHÁC, thứ không chia sẻ bộ nhớ.
    """
    if token_id is None:
        _SESSION_CACHE.clear()
    else:
        _SESSION_CACHE.pop(token_id, None)


def touch_state_clear() -> None:
    """Xóa mốc tiết lưu `last_seen`. Chỉ dùng cho test (xem `conftest.py`)."""
    _LAST_TOUCH_AT.clear()


def describe_device(user_agent: str) -> dict:
    """`User-Agent` thô -> bốn mảnh để lưu: loại máy · hệ điều hành · trình duyệt · câu hiển thị.

    Dùng lại `normalize_user_agent` của `core/device_fingerprint.py` để **bảng
    phiên và dấu thiết bị trên `tab_request_log` cùng một cách đọc**. Hai nơi
    phân tích `User-Agent` theo hai luật khác nhau thì câu hỏi *"vẫn máy đó
    chứ"* — thứ phải so dòng phiên với dòng request — không trả lời được.
    """
    browser, os_family, kind = normalize_user_agent(user_agent).split("|")
    device_type = {"desktop": DeviceType.DESKTOP, "mobile": DeviceType.MOBILE,
                   "tablet": DeviceType.TABLET}.get(kind, DeviceType.UNKNOWN)
    if browser == "unknown" and os_family == "unknown":
        #  Không đoán được gì thì đừng khai là "Máy tính" — `desktop` chỉ là giá
        #  trị lùi của `_device_kind`, không phải một kết luận.
        device_type = DeviceType.UNKNOWN
    parts = [p for p in (_BROWSER_NAMES.get(browser, ""), _OS_NAMES.get(os_family, "")) if p]
    parts.append(_DEVICE_NAMES[device_type])
    return {"device_type": int(device_type), "os": os_family, "browser": browser,
            "device_label": " · ".join(parts)[:120]}


#  Chỉ để HIỂN THỊ. Mã lưu xuống DB vẫn là chuỗi thường của
#  `normalize_user_agent` (`chrome`, `windows`), vì đó là thứ dùng để lọc.
_BROWSER_NAMES = {"edge": "Edge", "opera": "Opera", "samsung": "Samsung Internet",
                  "firefox": "Firefox", "chrome": "Chrome", "safari": "Safari",
                  "tool": "Công cụ dòng lệnh", "bot": "Bot"}
_OS_NAMES = {"ios": "iOS", "android": "Android", "windows": "Windows",
             "macos": "macOS", "linux": "Linux"}
_DEVICE_NAMES = {DeviceType.DESKTOP: "Máy tính", DeviceType.MOBILE: "Điện thoại",
                 DeviceType.TABLET: "Máy tính bảng", DeviceType.UNKNOWN: "Không rõ thiết bị"}


def start_session(db: Session, user, *, ip: str = "", user_agent: str = "",
                  login_method: int = LoginMethod.PASSWORD) -> LoginSession:
    """Mở một phiên cho lần đăng nhập vừa thành công. Trả về dòng đã có `id`.

    Người gọi (`/api/auth/login`, `/api/auth/google`) lấy `token_id` +
    `token_version` của dòng này nhét vào claim `jti` / `ver` của cả hai vé.
    """
    now = datetime.now()
    device = describe_device(user_agent)
    session = LoginSession(
        user_id=user.id,
        token_id=str(uuid.uuid4()),
        token_version=int(getattr(user, "token_version", 1) or 1),
        ip=(ip or "")[:45],
        user_agent=(user_agent or "")[:MAX_USER_AGENT],
        last_seen_at=now,
        last_seen_ip=(ip or "")[:45],
        expires_at=now + timedelta(days=settings.REFRESH_EXPIRE_DAYS),
        login_method=int(login_method),
        **device,
    )
    db.add(session)
    db.commit()
    #  `last_seen_at` vừa điền ở trên, nên bấm luôn mốc tiết lưu: không có dòng
    #  này thì middleware của chính lượt `/api/auth/login` đó thấy "chưa dập bao
    #  giờ" và chạy thêm một `UPDATE` đè lại đúng giá trị vừa ghi.
    _LAST_TOUCH_AT[int(session.id)] = time.monotonic()
    #  Vé được ký NGAY sau lời gọi này, nên dòng phiên phải nằm dưới DB trước —
    #  không thì có một khoảng người dùng cầm vé hợp lệ mà tra ra "phiên không
    #  tồn tại", và cửa chặn sẽ đá đúng người vừa đăng nhập đúng.
    return session


def resolve_session(db: Session, token_id: str, user_id: int) -> int:
    """Tra `jti` -> id phiên còn hiệu lực. Trả **0** nếu không có / đã thu hồi.

    Có đệm 60 giây. Cố ý KHÔNG ném lỗi: nơi gọi là `get_current_user`, chỗ đó
    quyết định câu chặn và mã lỗi, còn đây chỉ trả lời một câu có/không.
    """
    if not token_id:
        return 0
    now = time.monotonic()
    hit = _SESSION_CACHE.get(token_id)
    if hit and hit[2] > now:
        session_id, owner_id = hit[0], hit[1]
    else:
        row = (db.query(LoginSession.id, LoginSession.user_id, LoginSession.revoked_at)
               .filter(LoginSession.token_id == token_id).first())
        session_id = int(row[0]) if (row and row[2] is None) else 0
        owner_id = int(row[1]) if row else 0
        _SESSION_CACHE[token_id] = (session_id, owner_id, now + SESSION_CACHE_TTL_SECONDS)
    #  ⚠️ Đệm lưu SỰ THẬT VỀ CÁI VÉ (phiên nào, của ai), rồi mới đối chiếu với
    #  người đang hỏi — thứ tự đó là bắt buộc. Bản đầu lưu kết quả đã đối chiếu
    #  sẵn, nên kẻ nào gửi một lượt gọi ghép `jti` thật với `sub` của người khác
    #  sẽ ghi đè đệm bằng câu "không có phiên nào", và **chính chủ bị đá ra
    #  trong 60 giây** — một cửa từ chối dịch vụ mở bằng đúng một request.
    #  Có bài kiểm canh: `test_jti_cua_nguoi_nay_ghep_sub_cua_nguoi_kia_bi_chan`.
    return session_id if (session_id and owner_id == user_id) else 0


def touch_is_due(session_id: int) -> bool:
    """Đã tới lúc dập `last_seen_at` chưa — kiểm TRƯỚC khi mở kết nối DB.

    Tách riêng khỏi `touch_session` đúng vì lý do đó: middleware chạy ở mọi lượt
    gọi, mà 99% số lượt rơi vào trong khoảng tiết lưu. Mở một `SessionLocal()`
    rồi mới phát hiện chưa tới lúc là trả giá kết nối cho một việc không làm.
    """
    if not session_id:
        return False
    last = _LAST_TOUCH_AT.get(int(session_id))
    return last is None or (time.monotonic() - last) >= LAST_SEEN_THROTTLE_SECONDS


def touch_session(db: Session, session_id: int, ip: str = "") -> bool:
    """Dập `last_seen_at` / `last_seen_ip`. Trả `True` nếu thật sự có ghi.

    Một câu `UPDATE`, không `SELECT` trước: giá trị cũ chẳng để làm gì, mà đọc
    trước khi ghi là nhân đôi số truy vấn của một việc chạy ở mọi lượt gọi.
    """
    if not touch_is_due(session_id):
        return False
    (db.query(LoginSession).filter(LoginSession.id == session_id)
     .update({LoginSession.last_seen_at: datetime.now(),
              LoginSession.last_seen_ip: (ip or "")[:45]}, synchronize_session=False))
    #  Đánh dấu SAU khi câu lệnh chạy được. Đánh dấu trước thì một lần ghi hỏng
    #  khóa luôn cả 5 phút kế tiếp, và dòng phiên đứng im mà không ai biết vì sao.
    _LAST_TOUCH_AT[int(session_id)] = time.monotonic()
    return True


def mark_refreshed(db: Session, session_id: int, ip: str = "") -> None:
    """Ghi nhận một lần gia hạn (QĐ-A) — thay cho dòng nhật ký `refresh` cũ."""
    (db.query(LoginSession).filter(LoginSession.id == session_id)
     .update({LoginSession.refreshed_at: datetime.now(),
              LoginSession.refresh_count: LoginSession.refresh_count + 1,
              LoginSession.last_seen_at: datetime.now(),
              LoginSession.last_seen_ip: (ip or "")[:45]}, synchronize_session=False))
    db.commit()
    _LAST_TOUCH_AT[int(session_id)] = time.monotonic()   # vừa dập rồi, xem `start_session`


def revoke_session(db: Session, session: LoginSession, reason: int,
                   revoked_by: int = 0) -> None:
    """Cắt MỘT phiên. Thu hồi lại phiên đã thu hồi thì bỏ qua, không ghi đè lý do
    cũ — lý do đầu tiên mới là lý do thật."""
    if session.revoked_at is not None:
        return
    session.revoked_at = datetime.now()
    session.revoked_by = int(revoked_by or 0)
    session.revoke_reason = int(reason)
    db.commit()
    session_cache_clear(session.token_id)


def revoke_user_sessions(db: Session, user_id: int, reason: int, revoked_by: int = 0,
                         except_session_id: int = 0) -> int:
    """Cắt mọi phiên còn sống của một người. Trả về số phiên đã cắt.

    `except_session_id` để giữ lại phiên đang thao tác — dùng cho *đổi mật khẩu*,
    nơi đá luôn chính người vừa bấm nút là hành vi khó hiểu.
    """
    query = db.query(LoginSession).filter(LoginSession.user_id == user_id,
                                          LoginSession.revoked_at.is_(None))
    if except_session_id:
        query = query.filter(LoginSession.id != except_session_id)
    rows = query.all()
    now = datetime.now()
    for row in rows:
        row.revoked_at = now
        row.revoked_by = int(revoked_by or 0)
        row.revoke_reason = int(reason)
    db.commit()
    for row in rows:
        session_cache_clear(row.token_id)
    return len(rows)


def force_relogin(db: Session, user, reason: int = RevokeReason.FORCE_RELOGIN,
                  revoked_by: int = 0) -> int:
    """Đăng xuất MỌI thiết bị, hiệu lực **tức thì**.

    Tăng `tab_user.token_version` là điểm mấu chốt: mọi vé cũ mang `ver` của đời
    trước, mà `get_current_user` đọc `tab_user` ở từng lượt gọi nên không qua
    đệm nào cả. Việc đánh dấu `revoked_at` bên dưới chỉ để màn *Phiên đăng nhập*
    hiện đúng — nó KHÔNG phải cơ chế chặn, và đừng đảo thứ tự hai việc này.
    """
    user.token_version = int(getattr(user, "token_version", 1) or 1) + 1
    db.commit()
    return revoke_user_sessions(db, user.id, reason, revoked_by)
