"""LUẬT GHI NHẬT KÝ — khai MỘT chỗ, dùng cho cả ba lớp (bao-CR-312, P1).

Ba nhóm luật sống chung ở đây vì cả ba đều là câu trả lời cho *"cái gì KHÔNG
được ghi"*, và rải chúng ra ba tệp là cách chắc chắn nhất để sau này một chỗ
được sửa còn hai chỗ kia thì không:

1. **Lượt nào ghi** — không ghi GET (trừ xuất dữ liệu và xem tệp), không ghi
   chính đường nhật ký, không ghi gia hạn phiên thành công (QĐ-A).
2. **Bảng nào không được ghi** — NT-5: lớp tự động không bao giờ ghi chính nó,
   thiếu là vòng lặp vô hạn. P4 (sự kiện ORM) đọc `NO_LOG_TABLES` ở đây.
3. **Che dữ liệu nhạy cảm** — theo tên khóa cho body, theo tên cột cho ORM.
   Ghi nhầm MỘT lần là chuỗi băm mật khẩu nằm trong nhật ký vĩnh viễn.

Tài liệu gốc: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §6.
"""

MASKED = "***"

#  Trần kích thước, theo §4.1. Cắt chứ không bỏ: một body 10 MB vẫn cho biết
#  endpoint nào bị gọi, chỉ là không giữ trọn.
MAX_BODY_BYTES = 64 * 1024
MAX_ERROR_DETAIL_BYTES = 16 * 1024
MAX_QUERY_STRING = 1000
MAX_PATH = 300
MAX_ROUTE = 200

# --------------------------------------------------------------------------
# 1. Lượt nào được ghi
# --------------------------------------------------------------------------
WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")

#  Ngoại lệ của luật "không ghi GET" (Q6): hai loại *xem* có giá trị truy vết.
GET_LOGGED_MARKERS = ("/export", "/print")
GET_LOGGED_SUFFIXES = ("/view",)

#  NT-5 — đường dẫn KHÔNG bao giờ ghi.
#  `/api/health` bị Docker gọi mỗi vài giây; `/api/uploads` là tệp tĩnh; nhóm
#  `/api/system-logs` (P5) là chính màn đọc nhật ký — ghi nó thì mỗi lần mở màn
#  lại đẻ thêm dòng để đọc.
SKIP_PATH_PREFIXES = (
    "/api/health",
    "/api/uploads",
    "/api/system-logs",
    "/docs",
    "/redoc",
    "/openapi.json",
)

#  QĐ-A (§4.1): gia hạn phiên THÀNH CÔNG không đẻ dòng nào — 126 lượt/ngày, gần
#  nửa số lời gọi không phải GET, mỗi dòng chỉ nói "vẫn người đó, vẫn đang mở
#  máy". Thất bại thì ghi đủ (401), vì đó mới là dấu hiệu của BM-003.
#  ⚠️ Vế "IP đổi thì ghi" nằm ở P3 — nó cần `tab_login_session.last_seen_ip` để
#  so, mà bảng phiên chưa có ở P1.
REFRESH_PATH = "/api/auth/refresh"


def should_log_request(method: str, path: str) -> bool:
    """Lượt này có ghi `tab_request_log` không — quyết TRƯỚC khi gọi endpoint.

    Quyết sớm vì nó chi phối cả việc có đọc thân request hay không: lượt không
    ghi thì không đụng vào body, không đệm response.
    """
    for prefix in SKIP_PATH_PREFIXES:
        if path.startswith(prefix):
            return False
    if method in WRITE_METHODS:
        return True
    if method == "GET":
        if any(marker in path for marker in GET_LOGGED_MARKERS):
            return True
        if any(path.endswith(suffix) for suffix in GET_LOGGED_SUFFIXES):
            return True
    return False


def should_skip_by_result(path: str, status_code: int) -> bool:
    """QĐ-A — biết kết quả rồi mới bỏ được: gia hạn phiên THÀNH CÔNG thì bỏ."""
    return path == REFRESH_PATH and 200 <= status_code < 300


# --------------------------------------------------------------------------
# 2. NT-5 — bảng mà lớp tự động không được ghi
# --------------------------------------------------------------------------
#  `tab_login_session` nằm trong danh sách vì `last_seen_at` bị dập mỗi lời gọi
#  API: ghi lại nó nghĩa là mỗi request đẻ một dòng thay đổi, rồi dòng đó lại là
#  một thay đổi. `tab_notification` thì mỗi thao tác sinh vài chục dòng chuông.
NO_LOG_TABLES = frozenset({
    "tab_audit_log",
    "tab_change_log",
    "tab_request_log",
    "tab_login_session",
    "tab_notification",
})

# --------------------------------------------------------------------------
# 3. Che dữ liệu nhạy cảm
# --------------------------------------------------------------------------
#  Che theo TÊN KHÓA trong body (`tab_request_log.request_body`). Header
#  `Authorization` không bao giờ được ghi — middleware không đụng tới headers.
SENSITIVE_BODY_KEYS = frozenset({
    "password",
    "old_password",
    "new_password",
    "confirm_password",
    "token",
    "access_token",
    "refresh_token",
    "id_token",
    "reset_token",
    "secret",
    "client_secret",
    "credential",
})

#  Che theo TÊN CỘT (`tab_change_log`, `snapshot_json`) — P4 dùng.
SENSITIVE_COLUMNS = frozenset({
    "password_hash",
    "google_sub",
    "reset_token",
})


def is_sensitive_column(name: str) -> bool:
    """Cột có phải loại cấm ghi giá trị không — khớp tên rời lẫn tên có đuôi."""
    low = (name or "").lower()
    return low in SENSITIVE_COLUMNS or "token" in low or "secret" in low or "password" in low


def mask_payload(value, _depth: int = 0):
    """Chép sâu một cấu trúc JSON, thay giá trị của khóa nhạy cảm bằng `***`.

    Chép chứ không sửa tại chỗ: `value` là body người dùng vừa gửi, endpoint
    còn đọc nó sau middleware.
    """
    if _depth > 8:  # thân lồng sâu bất thường — không đi tiếp, đừng để đệ quy chạy hoang
        return MASKED
    if isinstance(value, dict):
        return {
            key: (MASKED if str(key).lower() in SENSITIVE_BODY_KEYS
                  else mask_payload(val, _depth + 1))
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [mask_payload(item, _depth + 1) for item in value]
    return value
