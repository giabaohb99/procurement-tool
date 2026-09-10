"""LUẬT GHI NHẬT KÝ — khai MỘT chỗ, dùng cho cả ba lớp (bao-CR-312, P1).

Ba nhóm luật sống chung ở đây vì cả ba đều là câu trả lời cho *"cái gì KHÔNG
được ghi"*, và rải chúng ra ba tệp là cách chắc chắn nhất để sau này một chỗ
được sửa còn hai chỗ kia thì không:

1. **Lượt nào ghi** — ghi hết, kể cả GET (đổi luật 10/09/2026), trừ đường gọi
   máy dội và trừ chính đường nhật ký.
2. **Bảng nào không được ghi** — NT-5: lớp tự động không bao giờ ghi chính nó,
   thiếu là vòng lặp vô hạn. P4 (sự kiện ORM) đọc `NO_LOG_TABLES` ở đây.
3. **Che dữ liệu nhạy cảm** — theo tên khóa cho body, theo tên cột cho ORM, và
   theo MỐC CHUỖI cho vết lỗi. Ghi nhầm MỘT lần là chuỗi băm mật khẩu nằm trong
   nhật ký vĩnh viễn.
4. **Giữ bao lâu** — dòng đọc 90 ngày, dòng ghi 16 tháng.

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
MAX_REFERER = 300

# --------------------------------------------------------------------------
# 1. Lượt nào được ghi
# --------------------------------------------------------------------------
WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")

#  ⚠️ ĐỔI LUẬT 10/09/2026 — TRƯỚC ĐÂY KHÔNG GHI GET, NAY GHI HẾT.
#  Luật cũ (Q6: chỉ ghi `/export`, `/print`, đuôi `/view`) để hở đúng nhóm nguy
#  hiểm nhất: **đọc trộm không để lại dấu**. Xem hết danh sách NCC kèm giá, mở
#  hồ sơ đọc CCCD với số tài khoản, dò id từng phiếu xem cái nào lọt — không
#  thao tác nào trong số đó là POST, nên không thao tác nào để lại một chữ.
#  Tệ hơn: `should_log_request` quyết định TRƯỚC khi gọi endpoint, nên **GET ăn
#  403 cũng không ghi** — câu "lượt bị chặn nay để lại dấu" của P1 hóa ra chỉ
#  đúng với lượt GHI.
#  Cái giá đã đo trên prod (24h): GET 7.440 · POST 87 · PATCH 51 · DELETE 5.
#  GET nhiều gấp **52 lần** phần còn lại, nên ba thứ dưới đây là điều kiện để
#  luật mới không tự bóp chết mình: bỏ hai đầu gọi máy dội (`SKIP_GET_PREFIXES`),
#  KHÔNG đệm thân trả về của GET thành công (§`should_capture_response`), và
#  dọn dòng GET sau 90 ngày (`GET_RETENTION_DAYS`).
GET_LOGGED_MARKERS = ()   # giữ tên cho mã cũ; luật ngoại lệ nay vô nghĩa vì ghi hết
GET_LOGGED_SUFFIXES = ()

#  NT-5 — đường dẫn KHÔNG bao giờ ghi.
#  `/api/health` bị Docker gọi mỗi vài giây; `/api/uploads` là tệp tĩnh; hai nhóm
#  `/api/system-logs` (P5) và `/api/audit-logs` là chính màn ĐỌC nhật ký — ghi
#  chúng thì mỗi lần mở màn lại đẻ thêm dòng để đọc.
SKIP_PATH_PREFIXES = (
    "/api/health",
    "/api/uploads",
    "/api/system-logs",
    "/api/audit-logs",
    "/docs",
    "/redoc",
    "/openapi.json",
)

#  Máy tự dội, KHÔNG phải người đọc dữ liệu: giao diện hỏi chuông và cảnh báo
#  theo nhịp, cả hai cộng lại là **4.427 trong 7.440 lượt GET mỗi ngày (59,5%)**
#  trên prod. Ghi chúng là đổi 60% dung lượng bảng lấy 0 thông tin.
#  Chỉ chặn GET — `PATCH /api/notifications/{id}` (đánh dấu đã đọc) vẫn ghi, vì
#  đó là thao tác thật của người dùng.
SKIP_GET_PREFIXES = (
    "/api/notifications",
    "/api/alerts",
)

#  ⚠️ QĐ-A ĐÃ BỎ 10/09/2026. Luật cũ: gia hạn phiên THÀNH CÔNG không đẻ dòng,
#  vì 126 lượt/ngày là gần nửa số lời gọi không phải GET. Hai lẽ khiến nó sai:
#  (1) so với 7.440 lượt GET/ngày nay ghi hết, 126 dòng không còn là con số;
#  (2) `/auth/refresh` là chỗ **token bị cắp lộ ra rõ nhất** — refresh token
#  sống 7 ngày còn access token vài chục phút, nên kẻ cắp BUỘC phải quay lại
#  đúng đường này. Bỏ ghi nó là bịt mắt ngay tại cửa mình muốn canh (BM-003).
REFRESH_PATH = "/api/auth/refresh"


def should_log_request(method: str, path: str) -> bool:
    """Lượt này có ghi `tab_request_log` không — quyết TRƯỚC khi gọi endpoint.

    Quyết sớm vì nó chi phối cả việc có đọc thân request hay không: lượt không
    ghi thì không đụng vào body, không đệm response.
    """
    for prefix in SKIP_PATH_PREFIXES:
        if path.startswith(prefix):
            return False
    if method == "GET":
        return not any(path.startswith(p) for p in SKIP_GET_PREFIXES)
    return True


def should_skip_by_result(path: str, status_code: int) -> bool:
    """Biết kết quả rồi mới bỏ được. Nay không bỏ gì cả — xem QĐ-A ở trên.

    Giữ hàm (và lời gọi trong middleware) vì đây là chỗ MÓC SẴN cho luật
    "bỏ theo kết quả" sau này; xóa đi thì P3 phải đi dựng lại đúng chỗ này.
    """
    return False


def should_capture_response(method: str, status_code: int) -> bool:
    """Có đệm thân trả về để đọc không.

    ⚠️ GET **thành công thì KHÔNG đệm**, và đây là điều kiện sống của luật ghi
    hết GET. Hai lý do, cái thứ hai nặng hơn:

    1. **Tiền.** Đệm nghĩa là nuốt trọn thân vào RAM rồi dựng lại `Response` cho
       từng lượt trong 3.000 lượt GET mỗi ngày, mà thân danh sách là thứ to
       nhất hệ thống.
    2. **Đúng thứ ta vừa đi bịt.** Thân của `GET /api/suppliers` LÀ bảng giá
       nhà cung cấp; thân của `GET /api/employees/{id}` LÀ số căn cước với số
       tài khoản. Chép chúng vào một bảng chỉ-thêm là tự tay nhân bản dữ liệu
       nhạy cảm sang chỗ có ít người canh hơn — chính là lỗ mà `mask_payload`
       và `redact_raw_inputs` vừa dựng lên để chặn.

    Câu cần trả lời với một lượt đọc là *"ai đọc cái gì, lúc nào, có bị chặn
    không"* — `path` + `query_string` + `http_status` nói đủ. Nội dung họ đọc
    được thì tra lại bằng chính dữ liệu, không cần bản chụp.

    GET **lỗi** thì vẫn đệm: thân 4xx/5xx nhỏ, và đó mới là thứ cần đọc.
    """
    if method == "GET":
        return not (200 <= status_code < 300)
    return True


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

#  ⚠️ KHỚP CHÍNH XÁC LÀ KHÔNG ĐỦ, và hai danh sách trên sẽ không bao giờ đuổi
#  kịp tên khóa thật. `PUT /api/settings` gửi `smtp_password`,
#  `r2_secret_access_key`, `r2_access_key_id` — không cái nào trùng khít với
#  `SENSITIVE_BODY_KEYS`, mà cả ba đều là bí mật hạ tầng, và đích đến là một
#  bảng CHỈ-THÊM: ghi nhầm một lần là nằm đó tới lúc hết hạn lưu.
#  Nên khóa nào CHỨA một trong các mảnh dưới đây cũng bị che. Thà che nhầm một
#  ô vô hại — mất chút giá trị lúc đi tra — còn hơn lọt một lần không gỡ lại được.
#  Cố ý KHÔNG có mảnh `key` trần: nó nuốt cả `keyword`, `product_key`, `monkey`.
SENSITIVE_KEY_MARKERS = (
    "password",
    "passwd",
    "token",
    "secret",
    "credential",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
)


def is_sensitive_key(name) -> bool:
    """Tên khóa (thân request) hay tên cột (P4) này có cấm ghi giá trị không."""
    low = str(name or "").lower()
    if low in SENSITIVE_BODY_KEYS or low in SENSITIVE_COLUMNS:
        return True
    return any(marker in low for marker in SENSITIVE_KEY_MARKERS)


def is_sensitive_column(name: str) -> bool:
    """Bí danh theo NGỮ CẢNH CỘT — cùng một luật, gọi từ tầng ORM (P4)."""
    return is_sensitive_key(name)


def mask_payload(value, _depth: int = 0):
    """Chép sâu một cấu trúc JSON, thay giá trị của khóa nhạy cảm bằng `***`.

    Chép chứ không sửa tại chỗ: `value` là body người dùng vừa gửi, endpoint
    còn đọc nó sau middleware.
    """
    if _depth > 8:  # thân lồng sâu bất thường — không đi tiếp, đừng để đệ quy chạy hoang
        return MASKED
    if isinstance(value, dict):
        return {
            key: (MASKED if is_sensitive_key(key) else mask_payload(val, _depth + 1))
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [mask_payload(item, _depth + 1) for item in value]
    return value


#  Khóa mang GIÁ TRỊ THÔ của người gửi trong thân lỗi, dù bản thân tên khóa
#  chẳng nói gì. Đây là lỗ mà luật che-theo-tên-khóa ở trên KHÔNG bịt được:
#  `validation_exception_handler` trả `details=exc.errors()`, và Pydantic v2 gắn
#  vào mỗi mục một khóa `input` = đúng thứ người dùng vừa gõ vào ô đó. Gõ mật
#  khẩu sai kiểu là mật khẩu nguyên văn nằm trong `response_body`, dù
#  `request_body` của cùng dòng ấy đã che thành `***`.
RAW_INPUT_KEYS = frozenset({"input"})


def redact_raw_inputs(value, _depth: int = 0):
    """Bỏ giá trị của `input` trong thân lỗi, giữ lại một dấu vết ngắn.

    Bỏ HẲN chứ không che có điều kiện, vì hai lẽ:

    1. `type` + `loc` + `msg` đã trả lời đủ câu *"phiếu này hỏng ở ô nào, vì
       sao"* — `input` là mảnh duy nhất mang dữ liệu người dùng mà không thêm
       được gì cho việc đi tra.
    2. Nó cũng là mảnh duy nhất KHÔNG có trần kích thước: lỗi `json_invalid`
       đặt vào đó **toàn bộ** chuỗi thân request, còn một phiếu 200 dòng sai
       kiểu thì đẻ 200 mục, mỗi mục kèm cả dòng.
    """
    if _depth > 8:
        return MASKED
    if isinstance(value, dict):
        return {
            key: (_input_trace(val) if str(key).lower() in RAW_INPUT_KEYS
                  else redact_raw_inputs(val, _depth + 1))
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [redact_raw_inputs(item, _depth + 1) for item in value]
    return value


def _input_trace(value) -> dict:
    """Thứ thay chỗ một `input`: đủ để biết người ta gửi CÁI GÌ, không biết là gì."""
    return {"_omitted": True, "type": type(value).__name__,
            "size": len(value) if isinstance(value, (str, bytes, list, dict)) else 0}


# --------------------------------------------------------------------------
# 4. Che vết lỗi (`error_detail`)
# --------------------------------------------------------------------------
#  ⚠️ LỖ THỨ BA, và là lỗ khó thấy nhất trong ba.
#  `mask_payload` che theo tên khóa, `redact_raw_inputs` bỏ giá trị thô — cả hai
#  đi trên CẤU TRÚC JSON. Còn `error_detail` là `traceback.format_exc()`: một
#  CHUỖI, nên không lớp nào ở trên chạm tới nó.
#  Mà SQLAlchemy nhét thẳng giá trị tham số vào chuỗi đó. Vết thật lấy từ máy:
#
#      [SQL: INSERT INTO tab_user (username, password_hash) VALUES (%(u)s, %(p)s)]
#      [parameters: {'u': 'admin', 'p': '$2b$12$...bam-mat-khau...', 'e': 'x@y.z'}]
#
#  Nghĩa là một cú 500 lúc tạo tài khoản chép nguyên chuỗi băm mật khẩu vào bảng
#  CHỈ-THÊM — đúng thứ `SENSITIVE_BODY_KEYS` dựng ra để chặn, đi vòng qua cửa sau.
#  Tệ hơn: nó nổ đúng lúc 500, tức đúng lúc quản trị mở nhật ký ra đọc.
#
#  Giữ `[SQL: ...]` vì trong đó chỉ có **chỗ giữ tham số** (`%(u)s`), không có giá
#  trị — mất nó thì đọc vết lỗi không biết câu nào hỏng.
ERROR_DETAIL_MARKERS = ("[parameters:", "[cached since")

#  Những đoạn Python/SQLAlchemy dán SAU khối tham số. Cắt tới mốc gần nhất trong
#  số này thì giữ lại được phần còn lại của vết lỗi — quan trọng với ngoại lệ
#  lồng nhau, nơi khối tham số nằm giữa chứ không nằm cuối.
ERROR_DETAIL_RESUMES = (
    "\n(Background on this error",
    "\nDuring handling of the above exception",
    "\nThe above exception was the direct cause",
)


def _resume_at(out: str, start: int) -> int:
    """Vị trí mốc kết gần nhất sau `start`; không có mốc nào thì hết chuỗi.

    Không tìm được mốc thì cắt tới cuối — mất phần đuôi vết lỗi, nhưng đó là
    hướng hỏng ĐÚNG: thà khó tra một sự cố còn hơn để lọt dữ liệu.
    """
    found = [i for i in (out.find(r, start) for r in ERROR_DETAIL_RESUMES) if i >= 0]
    return min(found) if found else len(out)


def mask_error_detail(detail: str | None) -> str | None:
    """Bỏ khối `[parameters: {...}]` khỏi vết lỗi, giữ nguyên phần còn lại.

    Cắt theo MỐC chứ không đếm ngoặc: giá trị tham số có thể chứa `]`, có thể
    xuống dòng, và một chuỗi tiếng Việt vài trăm ký tự thì đếm ngoặc sai là cắt
    nhầm cả vết lỗi. Tìm mốc mở, nhảy tới mốc đóng đã biết, bỏ khúc giữa.
    """
    if not detail:
        return detail
    out = detail
    for marker in ERROR_DETAIL_MARKERS:
        #  ⚠️ PHẢI CÓ `cursor`. Chuỗi thay vào có chứa CHÍNH `marker` (cố ý — đọc
        #  vết lỗi phải thấy chỗ nào đã bị che), nên tìm lại từ đầu là gặp lại nó
        #  ở đúng vị trí cũ và vòng lặp không bao giờ thoát. Bản đầu treo đúng
        #  kiểu đó, và nó treo trong middleware — tức treo cả lượt gọi API.
        cursor = 0
        while True:
            start = out.find(marker, cursor)
            if start < 0:
                break
            masked = f"{marker} {MASKED}]"
            out = out[:start] + masked + out[_resume_at(out, start):]
            cursor = start + len(masked)
    return out


# --------------------------------------------------------------------------
# 5. Tóm tắt thân trả về 2xx
# --------------------------------------------------------------------------
#  Bản đầu chỉ giữ `data.id`, và nó hụt ở ba ca gặp hằng ngày:
#  `POST /api/purchase-orders/{id}/approve` trả về cả phiếu mà không có khóa
#  `id` lồng trong `data` -> ghi rỗng; `POST .../import` trả `{"created": 120}`
#  -> mất luôn con số duy nhất đáng nhớ; API duyệt hàng loạt trả một DANH SÁCH
#  -> không biết đã đụng vào những phiếu nào.
#  Nên giữ **khóa ĐỊNH DANH + khóa ĐẾM**, cắt phần còn lại. Danh sách này cố ý
#  ngắn: mỗi khóa thêm vào là dung lượng nhân cho mọi dòng 2xx.
SUMMARY_KEYS = ("id", "code", "doc_code", "status", "count", "created", "updated",
                "skipped", "failed", "total")

#  Trần số id giữ lại của một thao tác hàng loạt. Duyệt 500 phiếu một lượt thì
#  20 id đầu đủ để lần ra lô, không cần chép cả danh sách vào nhật ký.
MAX_SUMMARY_IDS = 20


def summarize_success(data):
    """Rút gọn `data` của một thân 2xx còn phần định danh được.

    Trả `None` khi không rút ra được gì — khác hẳn `{}`: `None` nghĩa là *"thân
    này không có khóa nào đáng nhớ"*, còn `{}` đọc ra như *"đã cố mà rỗng"*.
    """
    if isinstance(data, dict):
        brief = {key: data[key] for key in SUMMARY_KEYS
                 if key in data and not isinstance(data[key], (dict, list))}
        return brief or None
    if isinstance(data, list):
        ids = [item.get("id") for item in data[:MAX_SUMMARY_IDS]
               if isinstance(item, dict) and item.get("id") is not None]
        brief = {"_count": len(data)}
        if ids:
            brief["ids"] = ids
        return brief
    return None


# --------------------------------------------------------------------------
# 6. Hạn lưu
# --------------------------------------------------------------------------
#  Khách chốt giữ nhật ký **16 tháng** (Q2) — đủ để soi lại một kỳ quyết toán.
#  Nhưng con số ấy chốt hồi luật còn là KHÔNG GHI GET. Nay ghi hết GET, giữ 16
#  tháng nghĩa là ~1,1 triệu dòng đọc mỗi năm nằm cạnh vài chục nghìn dòng ghi,
#  và bảng sẽ chậm đúng ở màn dựng ra để tra nó.
#  Nên tách hai hạn: dòng **đọc** sống 90 ngày, dòng **ghi** giữ đủ 16 tháng.
#  Không phá cam kết — 90 ngày cho GET là nhiều HƠN 0 ngày của luật cũ; cam kết
#  16 tháng đứng trên tập dữ liệu hồi đó, mà hồi đó tập đó không có GET nào.
#  Bản đẩy lên R2 hằng tháng vẫn giữ NGUYÊN VẸN cả hai loại trước khi dọn, nên
#  90 ngày là hạn của bản TRA NHANH, không phải hạn của chứng cứ.
GET_RETENTION_DAYS = 90
LOG_RETENTION_MONTHS = 16

#  Xóa theo lô. `DELETE` một phát vài trăm nghìn dòng khóa bảng đủ lâu để mọi
#  lượt gọi API đứng chờ ghi nhật ký — dọn rác mà thành sự cố.
CLEANUP_BATCH_SIZE = 2000
CLEANUP_MAX_BATCHES = 500
