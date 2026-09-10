# THIẾT KẾ LẠI NHẬT KÝ (LOG) & PHIÊN ĐĂNG NHẬP

**Bản:** 2.4 — 09/09/2026 · **CR:** bao-CR-312 · **Trạng thái: 12 CÂU HỎI §11 ĐÃ CHỐT 08/09/2026 (theo đề xuất, riêng Q2 khách đổi thành 16 tháng + gói theo năm). Bản 2.4 tính lại dung lượng bằng SỐ ĐO THẬT trên prod 09/09 và chốt thêm ba điều chỉnh (QĐ-A gia hạn phiên · QĐ-B khóa nối nhị phân · QĐ-C nhật ký ra khỏi sao lưu hằng đêm, đóng gói theo tháng). P0 tách thành bao-CR-313 (xong, deploy 09/09); **P1 xong mã 09/09 trên `erp-v2`, chưa commit** — middleware + `tab_request_log` + cột ngữ cảnh, QĐ-A và QĐ-B đúng ngay từ migration `f4d37c7600d0`; P2 trở đi chưa gõ mã.**

Bản 1.0 (07/09) chỉ đề xuất *thêm* hai bảng bên cạnh nhật ký cũ. Bản 2.0 (08/09 sáng) thiết kế
lại chính dòng nhật ký. Bản 2.1 bổ sung hai thứ bản 2.0 còn thiếu khi đối chiếu với câu hỏi
của khách: **gọi vào endpoint nào, input/output của lần gọi đó là gì**, và **điều khiển phiên**
(chặn · đá · đăng xuất mọi thiết bị · bắt đăng nhập lại). Bản 2.2 trả lời câu *"sao tách nhiều
bảng, vậy giao diện xem ở đâu, log hệ thống gom lại và debug thế nào"*: thêm §8 **một màn gom cả
ba bảng**, cho việc nền và lỗi 500 (traceback) chảy vào cùng dòng, và ba chỗ hiện **phiên đăng
nhập** (Quản trị · Trang cá nhân · hồ sơ Nhân sự). Bản 2.4 (09/09) **đo lại nhịp thật trên prod
thay cho các con số ước** ở §9, và vì phép đo lòi ra ba chỗ lãng phí nên chốt thêm ba điều
chỉnh: **QĐ-A** gia hạn phiên thành công không đẻ dòng nhật ký (§4.1), **QĐ-B** khóa nối
`request_id` lưu nhị phân (§4.5), và **QĐ-C** bốn bảng nhật ký ra khỏi bản sao lưu hằng đêm,
đổi lại đóng gói lên R2 mỗi tháng thay vì mỗi năm (§9).

Tệp này phần lớn vẫn là bản thiết kế để bàn. **Đã gõ mã: P0** (tách ra `bao-CR-313`, xong và
deploy 09/09) và **P1** (xong mã trên `erp-v2` ngày 09/09, chưa commit) — hai đợt đó nay mô tả
thứ chạy thật, và chỗ nào bản làm khác bản vẽ thì có dấu ⚠️ ngay tại mục đó (§4.1 có hai chỗ).
P2 trở đi chưa có dòng mã nào. Đọc kèm `so-ghi-nhan-loi-bao-mat.md` (BM-001…BM-007) và
`change-log-bao.md` (bao-CR-311).

---

## 1. Đo lại — một dòng nhật ký hôm nay chứa gì

Năm dòng `update` gần nhất trên bản đang chạy, chép nguyên văn:

```
('purchase_order', 129, 'update', '', 24, 2026-09-07 15:39:05)
('purchase_order', 129, 'update', '', 24, 2026-09-07 15:37:04)
('purchase_order', 135, 'update', '', 24, 2026-09-07 15:33:54)
('purchase_order', 132, 'update', '', 24, 2026-09-07 15:31:03)
('purchase_order', 132, 'update', '', 24, 2026-09-07 15:31:01)
```

Đọc ra tiếng Việt: *"tài khoản 24 đã sửa đơn mua hàng số 129."* Hết. Không biết sửa trường nào,
không biết từ giá trị nào sang giá trị nào, không biết gọi vào đâu, gửi lên cái gì, ngồi ở đâu,
và hai dòng cách nhau 2 phút không phân biệt được là hai lần sửa thật hay một lần bấm lưu hai nhịp.

Số đo trên bản đang chạy (08/09/2026), **4.201 dòng**:

| Đo | Con số | Nghĩa là |
|---|---|---|
| Dòng có `message` **rỗng** | **2.940 / 4.201 = 70%** | 7 trên 10 dòng không có một chữ nào |
| Riêng `update` + rỗng | **1.769** | phần lớn nhật ký là câu "ai đó đã sửa cái gì đó" |
| Độ dài `message` trung bình | **14 ký tự** | tính cả dòng rỗng; dòng có chữ trung bình ~48 |
| Số `action` khác nhau trong DB | **28** | |
| `ACTION_LABEL` trên prod | **13 nhãn** *(9 cũ + 4 của CR-311)* | |
| → Dòng hiện **mã tiếng Anh trần** cho người dùng | **1.135 / 4.201 = 27%** | `item_progress_auto` 286 · `login` 262 · `assign` 197 · `document_status` 131 · `login_failed` 84 · … |
| `created_by = 0` | **84** | đúng bằng số `login_failed` — chưa đăng nhập nên chưa có ai |
| Cỡ bảng | 0,8 MB · ~112 dòng/ngày | dung lượng **không** phải vấn đề, thông tin mới là vấn đề |
| *(đo lại 09/09/2026)* | **4.531 dòng · 0,88 MB** · **124 dòng/ngày** (30 ngày) · **214** (7 ngày) · đỉnh **409** | nhịp đang tăng, xem §9 |

Sáu câu hỏi một nhật ký phải trả lời được, và hôm nay:

| Câu hỏi | Hôm nay |
|---|---|
| **Ai** đã làm? | Được — *nếu* chỗ đó có gọi `record(...)`. 213 lời gọi rải trong 54 tệp, quên chỗ nào thì im lặng vĩnh viễn (đúng ca YCBG05092603) |
| Gọi vào **endpoint nào**, gửi lên **cái gì**, nhận về **cái gì**? | **KHÔNG.** Không có tầng nào ghi request |
| Đổi **từ giá trị nào sang giá trị nào**? | **KHÔNG.** Không chỗ nào lưu giá trị cũ |
| **Từ đâu, thiết bị gì, phiên nào**? | **KHÔNG**, trừ đúng lúc đăng nhập, mà IP còn nhét trong câu chữ |
| Lần bấm này gồm **những dòng nào**? | **KHÔNG.** Một cú Duyệt đụng 5 bảng ra 5 dòng rời rạc |
| Bị **chặn** (403) thì có dấu không? | **KHÔNG.** Lượt bị chặn không để lại gì |

---

## 2. Log nằm ở đâu trong tiến trình

Đây là câu quyết định mọi thứ phía sau. Nhật ký phải **bọc NGOÀI endpoint**, không nằm trong
endpoint — nằm trong thì lượt bị 401/403 (chưa tới endpoint) không bao giờ có dấu.

```
Trình duyệt / app
   │
   ▼
Cloudflare tunnel → nginx → uvicorn  (IP thật lấy bằng core/client_ip.get_client_ip, có từ
   │                                  bao-CR-313 — KHÔNG bật --proxy-headers, xem BM-004)
   ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│ [VÀO]  RequestContextMiddleware — chạy TRƯỚC mọi thứ của API                        │
│        · sinh request_id (UUID)                                                     │
│        · đọc ip thật, user_agent                                                    │
│        · đọc header Authorization → giải mã JWT → jti → tra tab_login_session       │
│          (đệm 60 giây) → session_id, user_id, token_version                         │
│        · đặt ContextVar(user_id, session_id, request_id, ip, actor_kind)            │
│        · đọc và giữ lại body vào (đã che mật khẩu / token, cắt 64 KB)               │
├────────────────────────────────────────────────────────────────────────────────────┤
│   get_current_user / require(...)  → 401 · 403 dừng Ở ĐÂY, nhưng vẫn nằm trong bọc  │
│   endpoint → service                                                                │
│      ├─ record(...)            → tab_audit_log     (lớp kể chuyện, đặt tay)          │
│      └─ db.flush()             → before_flush/after_flush → tab_change_log           │
│                                  (lớp máy ghi, tự động, gom vào bộ đệm)            │
├────────────────────────────────────────────────────────────────────────────────────┤
│ [RA]   cùng middleware — chạy SAU khi có response (kể cả exception)                 │
│        · http_status, thời gian xử lý                                               │
│        · body ra: chỉ giữ khi status ≠ 2xx, hoặc chỉ giữ message + id (xem Q9)      │
│        · ghi tab_request_log (chỉ cho request KHÔNG phải GET, xem §7)               │
│        · xả bộ đệm change_log, điền changed_fields / change_count lên audit cùng     │
│          request_id                                                                 │
└────────────────────────────────────────────────────────────────────────────────────┘
   │
   ▼
nginx → trình duyệt
```

Ba lớp, ba câu hỏi, nối bằng **một `request_id`**:

| Lớp | Bảng | Trả lời | Sinh bởi |
|---|---|---|---|
| **Lời gọi** | `tab_request_log` *(mới)* | Ai, từ đâu, gọi vào endpoint nào, gửi gì, nhận gì, mất bao lâu, có bị chặn không | Middleware, **tự động** |
| **Câu chuyện** | `tab_audit_log` *(sửa)* | Về mặt nghiệp vụ đã làm gì: *"Duyệt phiếu YCMH0912"* | `record(...)` đặt tay |
| **Máy ghi** | `tab_change_log` *(mới)* | Trường nào đổi, từ gì sang gì | Sự kiện ORM, **tự động** |

Cộng một bảng **phiên**: `tab_login_session` — ai đang đăng nhập bằng thiết bị gì, và là chỗ để
**chặn / đá / đăng xuất mọi thiết bị**.

Việc chạy nền (Celery) và script nhập liệu không đi qua middleware: chúng tự đặt ngữ cảnh với
`actor_kind = 2 / 3`, `created_by = 0`. **Đừng gán bừa cho một người thật.** Từ bản 2.2 chúng
**vẫn có một dòng `tab_request_log`** (`source = 2 / 3`, `route = "celery:backup_r2"` hay
`route = "script:import_ncc"`) — mỗi lần chạy nền là một "lần bấm" như API, để §8 hiện chung một
dòng chảy. Cơ chế: một `with request_context(source=2, route=...)` bọc quanh task, làm đúng việc
[VÀO]/[RA] của middleware.

---

## 3. Nguyên tắc thiết kế

**NT-1. Dữ kiện nào cần lọc thì phải là một CỘT, không được nằm trong câu chữ.** Hôm nay IP nằm
trong `"Đăng nhập thành công (IP 1.2.3.4)"`. Sau thiết kế lại, `message` chỉ là câu tóm tắt cho
người đọc — **cấm để nó là nơi DUY NHẤT chứa một dữ kiện.**

**NT-2. Ngữ cảnh do máy điền, không do người viết mã nhớ.** Ai · phiên · IP · lần bấm — bốn thứ
này không xuất hiện trong tham số `record(...)`; middleware đặt `ContextVar`, mọi dòng tự đọc.
Hệ quả: **213 lời gọi hiện có không phải sửa một chữ.**

**NT-3. Ba lớp nối bằng `request_id`, không gộp.** Nhồi input/output hay trước/sau vào
`tab_audit_log` là hỏng cả ba: bảng kể chuyện phình lên, mà vẫn không lọc được.

**NT-4. `action` là một bộ mã ĐÓNG.** Khai `ACTION_CATALOG` theo khuôn `core/status_catalog.py`,
**có nhãn tiếng Việt là điều kiện để tồn tại**, cộng một test quét mọi chuỗi `action` dùng trong
mã. Bỏ hẳn cơ chế "nhớ cập nhật `dict` nhãn" — chính nó đẻ ra 27% dòng hiện mã Anh trần, và đã
lệch thật: prod 13 nhãn, `erp-v2` ~40.

**NT-5. Lớp tự động không được phép tự ghi chính nó** — danh sách bảng loại trừ khai một chỗ.

---

## 4. BẢNG THIẾT KẾ

### 4.1. `tab_request_log` — mỗi lời gọi API hoặc mỗi lần chạy nền một dòng — MỚI

> **Bản 2.5 (10/09/2026, `bao-CR-346`) đã ĐẢO luật lọc của mục này.** Trước đây chỉ ghi
> lượt không phải GET cộng vài đuôi đường dẫn, và bỏ lượt gia hạn phiên thành công (QĐ-A).
> Nay **ghi hết**, trừ hai đầu gọi máy dội và đường của chính nhật ký. Lý do và cái giá
> phải trả nằm ngay dưới bảng cột.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | BIGINT | |
| `request_id` | BINARY(16), unique | **Khóa nối** sang audit và change_log — nhị phân, xem QĐ-B §4.5 |
| `source` | SMALLINT | `1` API · `2` Celery · `3` script — việc nền cũng là một dòng ở đây (bản 2.2), để màn §8 có một dòng chảy |
| `created_at` | DATETIME | lúc nhận request (UTC) |
| `user_id` | BIGINT, index | `0` nếu chưa đăng nhập (đăng nhập thất bại, token hỏng) |
| `session_id` | BIGINT, index | trỏ `tab_login_session`; `NULL` nếu chưa có phiên |
| `ip` | VARCHAR(45), index | |
| `method` | VARCHAR(8) | `GET` · `POST` · `PATCH` · `PUT` · `DELETE` (bản 2.5 thêm `GET`) |
| `path` | VARCHAR(300) | đường dẫn thật: `/api/purchase-orders/129/items/4412` |
| `route` | VARCHAR(200), index | **mẫu route**: `/api/purchase-orders/{id}/items/{item_id}` — để gom *"endpoint này ai gọi"* |
| `query_string` | VARCHAR(1000) | `?...` nguyên văn — với GET thì đây chính là phần nội dung, *"ai tìm gì, lọc gì"* |
| `device_hash` | BINARY(8), index, NULL | **MỚI 2.5** — dấu thiết bị đã chuẩn hóa, xem ghi chú "Dấu thiết bị" dưới bảng |
| `referer` | VARCHAR(300) | **MỚI 2.5** — màn hình nào phát ra lượt gọi này |
| `request_body` | JSON | body vào, **đã che** (§6), cắt **64 KB**; **GET không có thân nên bỏ qua hẳn**; multipart **không đọc** — xem ghi chú dưới bảng |
| `http_status` | SMALLINT | `200` · `403` · `422` · `500`… — **đây là chỗ ghi lượt bị chặn** |
| `response_body` | JSON | body ra — **GET thành công: KHÔNG giữ gì** (bản 2.5); GET hỏng và mọi lượt ghi: giữ nguyên văn nếu không phải 2xx, còn 2xx thì tóm tắt `message` + khóa định danh (Q9) |
| `error_code` | VARCHAR(60) | mã lỗi trong phong bì `{success:false, error:{code}}` |
| `error_detail` | TEXT | **chỉ khi 5xx hoặc task nền văng lỗi**: traceback Python, cắt 16 KB. Đây là "log hệ thống" theo nghĩa debug — hôm nay nó chỉ có trong `docker logs` và trôi mất sau vài ngày |
| `duration_ms` | INT | thời gian xử lý |
| `audit_count`, `change_count` | SMALLINT | đếm dòng con ở hai lớp kia — biết có gì để mở |

⚠️ **Multipart: P1 KHÔNG đọc thân, kể cả để lấy tên tệp** (khác bản thiết kế, chốt 09/09/2026).
Bóc tên tệp đòi phải đọc hết luồng tải lên rồi ráp lại cho endpoint — tức nuốt trọn một tệp
20 MB vào RAM chỉ để ghi được một chuỗi tên, ở tầng chạy trước **mọi** request. Đổi lại chỉ ghi
`{"content_type": ..., "size": ...}`. Tên tệp không mất: nó nằm ở `tab_file` và ở dòng audit của
chính thao tác đính kèm, tra bằng cùng một `request_id`.

**`request_id` in ra cả log của uvicorn.** Một `logging.Filter` đọc `ContextVar` và gắn
`request_id` vào mọi dòng log ứng dụng phát ra trong lúc xử lý request đó. Cùng một mã nằm ở DB
lẫn `docker logs`, cần đào sâu hơn traceback (log debug, câu SQL) thì copy mã sang container là
ra. Log của nginx / Cloudflare (lượt chưa tới API) **vẫn ở ngoài**, không kéo về DB.

#### Luật lọc — bản 2.5 (10/09/2026, `bao-CR-346`)

**Ghi hết, kể cả GET.** Danh sách bỏ chỉ còn ba nhóm, khai ở `core/logging_policy.py`:

| Nhóm | Đường dẫn | Vì sao bỏ |
|---|---|---|
| Máy dội máy (**chỉ bỏ GET**) | `/api/notifications` · `/api/alerts` | 4.427 trong 7.440 lượt GET một ngày trên prod — **59,5%** — chỉ để vẽ con số trên hình cái chuông. `PATCH /api/notifications/{id}` (bấm "đã đọc") **vẫn ghi**: đó là thao tác của người. |
| Đường của chính nhật ký | `/api/system-logs` · `/api/audit-logs` | NT-5 — mở màn đọc nhật ký mà lại đẻ thêm dòng nhật ký để đọc |
| Hạ tầng | `/api/health` · `/api/uploads` · `/docs` · `/redoc` · `/openapi.json` | không phải thao tác nghiệp vụ |

**Vì sao đảo luật cũ.** Ba lý do, lý do thứ hai mới là lý do nặng:

1. **Đọc trộm không để lại gì.** Cả phân hệ nhân sự, công nợ, hợp đồng đều là dữ liệu mà
   thiệt hại nằm ở chỗ **bị xem**, không phải bị sửa. Một người tải toàn bộ danh sách
   nhân sự kèm số tài khoản ngân hàng về máy, theo luật cũ, không để lại một dòng nào.
2. **Lượt GET bị chặn cũng mất luôn.** `should_log_request()` quyết định **trước khi
   endpoint chạy**, tức trước khi biết kết quả. Nên một cú dò `GET /api/employees/9` ăn
   403 cũng bị bỏ y như một lượt xem hợp lệ — đúng cái lượt đáng nhìn nhất thì không ghi.
3. **Danh sách đuôi đường dẫn luôn thiếu.** Luật cũ nhặt `/export`, `/print`, `/view`,
   nhưng `/download`, `/preview`, `/chain/zip` cũng là tải dữ liệu ra ngoài mà không nằm
   trong danh sách. Mỗi lần ai đó đặt một đuôi mới là danh sách hụt thêm một chỗ, trong
   im lặng. *(Tiện thể: `"/export"` khớp cả `/api/exports`, một lỗi đã có sẵn.)*

**Cái giá, và đã trả bằng gì.** Ghi hết là ~3.000 dòng/ngày thay vì ~265. Ba khoản trả:

- **Dung lượng** → cơ chế dọn dòng GET quá **90 ngày** (§4.1.1 ngay dưới).
- **Nhân đôi dữ liệu nhạy cảm** → GET thành công **không lưu `response_body`**. Chép thân
  trả về của lượt đọc là sao nguyên phần dữ liệu đó sang một bảng **không có
  `employee_sensitive` gác cửa**. Vẫn tra được *"ai xem gì"* qua `path` + `query_string`.
- **Màn `/system/logs` bị loãng** → P5 phải mặc định lọc **chỉ hiện lượt GHI**, xem GET là
  một ô tick bật thêm. Đây là việc của tầng ĐỌC, không phải lý do để không ghi.

**QĐ-A (bản 2.4) đã BỎ.** Luật cũ không ghi lượt `POST /api/auth/refresh` thành công.
Hai lẽ khiến nó sai: (a) 126 lượt/ngày là con số không đáng kể cạnh ~3.000 GET/ngày, tức
lý lẽ "làm loãng" đã tự tan khi luật GET đảo; (b) `/auth/refresh` **chính là** nơi một
refresh token bị cắp lộ mặt — nó thành công ở máy kẻ trộm, nên đúng cái ca bị bỏ mới là ca
cần nhìn (**BM-003**). Hàm `should_skip_by_result()` **giữ lại nhưng luôn trả `False`**:
đó là chỗ móc sẵn cho P3, khi có `tab_login_session.last_seen_ip` để so.

**Dấu thiết bị (`device_hash`).** Đổi IP một mình là tín hiệu **yếu** (4G nhảy sang wifi,
nhà mạng đổi IP động). Đổi **thiết bị** giữa cùng một phiên mới là tín hiệu mạnh. Nhưng
băm thẳng `User-Agent` thô thì hỏng ngay tuần đầu: chuỗi đó mang số hiệu bản vá
(`Chrome/126.0.6478.127`) mà Chrome tự cập nhật vài tuần một lần — sáng thứ Hai cả công ty
đổi dấu cùng lúc, cảnh báo kêu trăm lần vào ngày không có gì xảy ra, và sau ba lần như thế
thì không ai đọc cảnh báo nữa. Nên **chuẩn hóa trước khi băm**, chỉ giữ ba mảnh không đổi
theo bản vá: `chrome|windows|desktop` (`core/device_fingerprint.py`).

⚠️ **Cố ý KHÔNG có cột `user_agent`.** Miền giá trị sau chuẩn hóa là tập **đóng**, chưa tới
hai trăm tổ hợp, nên `device_label()` dựng sẵn cả bảng và **tra ngược 8 byte ra chữ**. Lưu
thêm chuỗi thô ~200 byte trên **mọi** dòng là vài trăm MB để chép đi chép lại vài chục giá
trị giống hệt nhau. Chuỗi `User-Agent` nguyên văn thuộc về `tab_login_session` (P3) — nơi
một lần đăng nhập chỉ có một dòng.

Đánh đổi đã biết: hai máy Windows cùng chạy Chrome ra **cùng một dấu**. Cột này để **loại
trừ** (*"dấu vẫn thế, khỏi xét"*), không phải để định danh máy.

#### 4.1.1. Dọn dòng GET quá 90 ngày — điều kiện ĐI KÈM, không phải tối ưu

`request_log.cleanup`, chạy **03:40 mỗi ngày** (`core/celery_app.py`).

| | Hạn giữ | Vì sao |
|---|---|---|
| Dòng **GET** | **90 ngày** (`GET_RETENTION_DAYS`) | ~3.000 dòng/ngày. Giữ đủ 16 tháng là ~1,4 triệu dòng đọc nằm chen giữa vài chục nghìn dòng thao tác thật, và bảng chậm đúng ở màn dựng ra để tra nó. |
| Dòng **GHI** (POST/PATCH/PUT/DELETE) | **16 tháng** (QĐ-C) | không bao giờ bị việc dọn này đụng tới |

⚠️ **Chốt quan trọng nhất của việc dọn không phải chuyện dung lượng.** Nó chỉ xóa khi
`is_remote_storage_ready()` đúng — tức khi đã có bản sao ngoài máy trên R2. Xóa bản **duy
nhất** của một dòng nhật ký là **hủy chứng cứ**, và một việc chạy nền lúc 3 giờ sáng không
phải chỗ để chuyện đó xảy ra vì lỡ thiếu một biến môi trường. Chưa cấu hình R2 thì việc dọn
tự tắt (`status: skipped`), không phải lỗi.

⚠️ **Xóa theo LÔ 2.000 dòng, không xóa một phát.** Một câu `DELETE` quét vài trăm nghìn
dòng giữ khóa đủ lâu để **mọi lượt gọi API đứng chờ ghi nhật ký** — dọn rác mà thành sự cố
toàn hệ. Chạm trần 500 lô thì ghi cảnh báo và để lần chạy sau, chứ không dừng im lặng.

**Lịch 03:40 là cố ý, không phải số ngẫu nhiên**: phải chạy **sau** việc đóng gói tháng lúc
03:00. Ngày 1 hằng tháng hai việc cùng thức dậy; đảo thứ tự thì có đêm dọn trước, đóng gói
sau, và phần bị dọn không nằm trong gói nào.

#### 4.1.2. Đóng gói ra R2 — kéo từ P6 lên sớm

`audit.archive`, **03:00 ngày 1 hằng tháng**, key `{env}/log-archive/{YYYY-MM}/{bảng}.jsonl.gz`
kèm tệp `.sha256`.

**Vì sao không đợi P6.** QĐ-C đã loại bốn bảng nhật ký khỏi bản sao lưu hằng đêm — hợp lý,
vì chúng phình nhanh và không cần khôi phục cùng dữ liệu nghiệp vụ. Nhưng gói R2 lại xếp ở
P6, giai đoạn **cuối**. Khoảng giữa hai mốc đó, nhật ký tồn tại **đúng một bản, nằm trên
chính cái máy** mà kẻ tấn công đang đứng. Nhật ký chỉ có giá trị khi người bị nó ghi lại
không xóa được nó.

Ba thứ đã sửa trong việc đóng gói (`modules/audit/tasks.py`):

1. **Chép đủ cột** — bản cũ liệt kê tay 7 trường, trong khi `tab_audit_log` nay có 20 cột,
   nghĩa là bản lưu trữ rụng sạch `request_id`, `ip`, `session_id`, `actor_kind`, `doc_code`,
   đúng phần ngữ cảnh mà cả CR-312 dựng ra. Nay đọc cột từ mapper. Thêm cả `tab_request_log`.
2. **Có `.sha256`** — không có nó thì "bản lưu trữ" chỉ là một tệp gz, không ai chứng minh
   được nó chưa bị thay. `gzip(mtime=0)` để cùng dữ liệu luôn ra cùng byte, không thì mỗi
   lần chạy một mã băm khác và mã băm hết nói lên điều gì.
3. **Hỏng thì ném lỗi** — bản cũ nuốt mọi ngoại lệ rồi trả `{"status": "failed"}`, mà không
   ai đọc giá trị trả về của một việc chạy nền.

⚠️ **Chưa cấu hình R2 thì TỪ CHỐI chạy, không ghi tạm xuống `uploads/`.** `upload_fileobj`
mặc định lùi về ghi tệp local, mà `uploads/` được `main.py` gắn ra `/api/uploads` bằng
`StaticFiles` **không có lớp gác nào** — bản lưu trữ chứa nguyên nhật ký toàn hệ sẽ nằm ở
một URL công khai đoán được. Thà không có bản lưu trữ còn hơn có một bản ai cũng tải được.

**Việc phải làm ở P3, ghi ra đây kẻo quên:** `bao-CR-313` ghi **mọi** lần gia hạn thành công
thành một dòng `tab_audit_log` `action=refresh` — đúng cho lúc chưa có bảng phiên, nhưng nó
cộng ~126 dòng audit/ngày. Khi P3 dựng xong `tab_login_session`, quay lại
`auth/controller.py` bỏ dòng `record(...)` cho nhánh thành công và chuyển sang cập nhật
phiên; hai nhánh `refresh_failed` giữ nguyên. *(Dòng `request_log` thì **giữ** — đó là phần
QĐ-A đã bỏ.)*

### 4.2. `tab_audit_log` — lớp kể chuyện (sửa lại)

Cột `entity` · `entity_id` · `action` · `message` giữ nguyên tên để **không phải viết lại 213 lời
gọi**. Phần còn lại thêm mới.

| Cột | Kiểu | Có chưa | Ai điền | Trả lời |
|---|---|---|---|---|
| `id` · `created_at` | | có | tự động | Lúc nào |
| `created_by` | BIGINT | có | **middleware** | Ai — `0` = không phải người |
| `actor_kind` | SMALLINT | **MỚI** | middleware | `1` người · `2` hệ thống (Celery/seed) · `3` script nhập liệu · `4` tích hợp. Hôm nay `0` vừa là "hệ thống" vừa là "không biết" |
| `on_behalf_of` | BIGINT | **MỚI** | lời gọi | Làm hộ ai (hành chính lập đơn hộ) |
| `session_id` | BIGINT, index | **MỚI** | middleware | Phiên nào → thiết bị |
| `request_id` | BINARY(16), index | **MỚI** | middleware | Thuộc lần bấm nào → endpoint, input, output (QĐ-B §4.5) |
| `ip` | VARCHAR(45) | **MỚI** | middleware | Giữ riêng dù tra được qua request_id, vì việc nền và script **không có request** |
| `entity` · `entity_id` | | có | lời gọi | Trên cái gì |
| `doc_code` | VARCHAR(50) | **MỚI** | lời gọi | **Số phiếu tại thời điểm đó** — phiếu xóa rồi thì `entity_id` không tra ngược ra được |
| `parent_entity` / `parent_id` | VARCHAR(50) / BIGINT | **MỚI** | lời gọi | Dòng thuộc phiếu nào — dấu vết trên dòng đang mồ côi |
| `action` | VARCHAR(30) | có | lời gọi | Ràng bởi `ACTION_CATALOG` |
| `action_group` | SMALLINT | **MỚI** | suy từ catalog | `1` xem · `2` sửa · `3` duyệt · `4` xóa · `5` đăng nhập · `6` xuất dữ liệu · `7` phân quyền — để lọc và cảnh báo |
| `message` | TEXT | có | lời gọi | Câu cho người đọc — **phụ** (NT-1) |
| `changed_fields` | VARCHAR(500) | **MỚI** | tự động | Tên trường đã đổi, phẳng. **Cố ý lặp** dữ liệu của change_log để dòng thời gian hiện *"Sửa: đơn giá, số lượng"* không phải join |
| `change_count` | SMALLINT | **MỚI** | tự động | Biết có nên hiện nút *Xem chi tiết* không |

Bỏ so với bản 2.0: cột `result` — trạng thái thành công/bị chặn nay nằm ở `tab_request_log.http_status`,
đúng chỗ của nó (lượt bị 403 chưa tới `record(...)` nên audit không có dòng để mà ghi `result`).
`user_agent` cũng không ở đây — thuộc bảng phiên.

### 4.3. `tab_change_log` — lớp máy ghi — MỚI

**Một dòng = MỘT TRƯỜNG** cho thao tác sửa; thêm/xóa thì chụp nguyên bản ghi. Câu hỏi hay hỏi nhất
khi truy sự cố là *"đơn giá dòng này ai đổi"* — với một dòng mỗi trường là `WHERE field='unit_price'`,
với JSON là bới bằng hàm.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` · `created_at` · `created_by` | | chuẩn `AuditMixin` |
| `request_id` | BINARY(16), index | nối sang request_log + audit (QĐ-B §4.5) |
| `session_id` | BIGINT, index | |
| `table_name` | VARCHAR(64), index | tên bảng thật, vd `tab_purchase_order_item` |
| `row_id` | BIGINT, index | |
| `op` | SMALLINT | `1` thêm · `2` sửa · `3` xóa |
| `field` | VARCHAR(64), index | chỉ khi `op = 2` |
| `before_value` · `after_value` | TEXT | chỉ khi `op = 2` |
| `snapshot_json` | JSON | chỉ khi `op = 1` / `3` — chụp cả bản ghi (đã che) |
| `is_masked` | BOOLEAN | trường bị che, giá trị không ghi |

Chỉ số ghép: `(table_name, row_id, id)` để dựng lịch sử một dòng dữ liệu; `(request_id)` để dựng
lại một lần bấm.

### 4.4. `tab_login_session` — mỗi lần đăng nhập THÀNH CÔNG một dòng — MỚI

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | BIGINT | |
| `user_id` | BIGINT, index | |
| `token_id` | CHAR(36), unique | UUID, **nhét vào claim `jti`** của cả access lẫn refresh token |
| `token_version` | SMALLINT | chép từ `tab_user.token_version` lúc đăng nhập (xem §5) |
| `ip` | VARCHAR(45) | IPv6 45 ký tự, đừng để 15 |
| `user_agent` | VARCHAR(500) | nguyên văn |
| `device_type` | SMALLINT | `1` máy tính · `2` điện thoại · `3` máy tính bảng · `9` không rõ |
| `os` · `browser` | VARCHAR(60) | bóc từ user-agent (`user-agents` hoặc `ua-parser`) — để lọc |
| `device_label` | VARCHAR(120) | chuỗi hiện cho người: *"Chrome 128 · Windows 11 · máy tính"* |
| `login_method` | SMALLINT | `1` mật khẩu · `2` Google |
| `last_seen_at` | DATETIME | dập mỗi lời gọi API, **tiết lưu 5 phút** |
| `last_seen_ip` | VARCHAR(45) | IP gần nhất — phiên đổi IP giữa chừng là dấu hiệu đáng xem |
| `refreshed_at` | DATETIME | lần `/refresh` gần nhất — hôm nay refresh **không ghi gì** (BM-003) |
| `refresh_count` | INT | **MỚI bản 2.4** — đếm số lần gia hạn của phiên. Theo QĐ-A (§4.1) gia hạn thành công chỉ dập hai cột này thay vì đẻ dòng nhật ký; số đếm cộng `refreshed_at` đủ trả lời *"phiên này còn sống bao lâu, gia hạn bao nhiêu lần"* |
| `expires_at` | DATETIME | = lúc đăng nhập + 7 ngày (hạn refresh) |
| `revoked_at` · `revoked_by` · `revoke_reason` | DATETIME / BIGINT / SMALLINT | `1` tự đăng xuất · `2` quản trị đá · `3` đổi mật khẩu · `4` bắt đăng nhập lại · `5` tài khoản bị khóa |

Đăng nhập **thất bại KHÔNG ghi vào bảng này** — nó đã có một dòng `tab_request_log`
(`route=/api/auth/login`, `http_status=401`, `ip`) cộng một dòng `tab_audit_log`
(`action=login_failed`). Dò *"IP nào thử nhiều tài khoản"* là một câu `GROUP BY ip` trên request_log.

### 4.5. QĐ-B (bản 2.4) — `request_id` lưu nhị phân, không lưu chuỗi

`request_id` là **cột duy nhất có mặt ở cả ba bảng và có chỉ mục ở cả ba** — mỗi dòng nhật ký,
dù ở lớp nào, đều cõng nó hai lần (một lần dữ liệu, một lần chỉ mục). Khai `CHAR(36)` trên bảng
`utf8mb4` thì khóa chỉ mục dài tới **144 byte** trong bộ nhớ, còn trên đĩa mỗi dòng mất chừng
36 byte dữ liệu + 48 byte chỉ mục. Nhân với ~316.000 dòng/năm của cả ba bảng là **~26 MB/năm chỉ
để lưu sợi dây nối**. Đổi sang `BINARY(16)` (UUID dạng 16 byte) còn **~14 MB/năm**, và quan
trọng hơn: mỗi lần mở một dòng trên màn §8 là ba truy vấn `IN (request_id…)` đi qua đúng khóa này.

| Việc | Cách làm |
|---|---|
| Kiểu cột | `BINARY(16)` ở cả `tab_request_log` (unique), `tab_audit_log` (index), `tab_change_log` (index) |
| Sinh mã | `uuid.uuid4().bytes` trong middleware; ContextVar giữ **bản nhị phân**, đổi sang chuỗi lúc trả API |
| API và giao diện | Vẫn là chuỗi 36 ký tự có gạch (`str(uuid.UUID(bytes=b))`) — người dùng copy mã đi tra không đổi gì |
| Tra tay trong DB | `WHERE request_id = UUID_TO_BIN('3f1c9a2e-…')` và `SELECT BIN_TO_UUID(request_id)` — MySQL 8 có sẵn hai hàm này. **Ghi vào HDSD nội bộ**, vì gõ nhầm `WHERE request_id = '3f1c…'` sẽ ra rỗng chứ không báo lỗi, dễ tưởng mất dữ liệu |
| Log uvicorn | In dạng chuỗi như cũ (§4.1) — chỗ đó là chữ cho người đọc, không phải khóa |

**`token_id` của `tab_login_session` giữ nguyên `CHAR(36)`**: nó nằm trong claim `jti` của JWT nên
buộc phải là chuỗi, mà bảng phiên chỉ khoảng **2.000 dòng/năm** (đo thật: 5,6 lượt đăng nhập/ngày)
— đổi sang nhị phân không tiết kiệm được gì đáng kể mà thêm một chỗ phải chuyển đổi.

---

## 5. ĐIỀU KHIỂN PHIÊN — chặn, đá, đăng xuất mọi thiết bị, bắt đăng nhập lại

Có bảng phiên rồi thì **bốn thao tác này gần như miễn phí**. Cơ chế nằm ở `get_current_user`:

```
giải mã JWT → (sub, jti, ver, type, exp)
  1. user = db.get(User, sub); không active         → 401 "tài khoản bị khóa"
  2. ver != user.token_version                       → 401 "phiên hết hiệu lực, đăng nhập lại"
  3. session = tra jti (đệm 60 giây); revoked_at có  → 401 "phiên đã bị đăng xuất"
  4. dập last_seen_at nếu > 5 phút
```

Thêm **một cột** `tab_user.token_version SMALLINT DEFAULT 1`. Đây là điểm mấu chốt của "đăng
xuất mọi thiết bị": **tăng `token_version` lên 1 là mọi token cũ của người đó chết ngay**, không
phải đi tìm và đánh dấu từng dòng phiên. Đánh dấu `revoked_at` các phiên cũ vẫn làm, nhưng chỉ
để màn *Phiên đăng nhập* hiện đúng — không phải cơ chế chặn.

| Thao tác | Ai bấm | Làm gì trong DB | Hiệu lực |
|---|---|---|---|
| **Đá một thiết bị** | chính chủ (ở Trang cá nhân) hoặc quản trị | `revoked_at` trên đúng dòng phiên, `revoke_reason = 1/2` | tối đa 60 giây (đệm) |
| **Đăng xuất mọi thiết bị** | chính chủ hoặc quản trị | `token_version += 1`; đánh dấu mọi phiên `revoke_reason = 4` | **ngay lập tức** — không qua đệm vì `token_version` đọc từ `User` mỗi request |
| **Bắt đăng nhập lại** (sau khi đổi quyền, đổi mật khẩu) | tự động | `token_version += 1`, `revoke_reason = 3/4` | ngay lập tức |
| **Chặn tài khoản** | quản trị | `is_active = false` (đã có) + `token_version += 1` + `revoke_reason = 5` | ngay lập tức. Hôm nay `is_active=false` đã chặn được rồi — cái thiếu là **không ghi lại** và không thấy phiên nào đang mở |

Đăng xuất bình thường: `revoked_at` trên phiên hiện tại. Hôm nay `/logout` **chỉ ghi một dòng
nhật ký, token vẫn sống tới hết hạn** (BM-002). `/refresh`: xoay access token mới **cùng `jti`**,
dập `refreshed_at` — không tạo phiên mới, không mất lịch sử.

Cái giá, nói thẳng: mỗi lời gọi API thêm một truy vấn tra phiên (đệm 60 giây theo khuôn
`_PERM_CACHE`) — `db.get(User)` thì `get_current_user` **đã làm sẵn** từ trước, nên kiểm
`token_version` không tốn thêm gì.

---

## 6. GHI NHẬN THÔNG TIN NHƯ THẾ NÀO — ba nguồn, một sợi dây

### Nguồn 1 — Middleware: tự động, mọi lời gọi API

Xem sơ đồ §2. Ghi `tab_request_log`, đặt `ContextVar`, cuối request xả bộ đệm. `record(...)` và
tầng ORM **không nhận thêm tham số** — đọc `ContextVar`. Đây là lý do thiết kế lại được mà không
mở 54 tệp.

### Nguồn 2 — `record(...)`: câu chuyện, đặt tay

Chữ ký cũ **giữ nguyên**, thêm tham số tùy chọn:

```python
record(db, user_id, entity, entity_id, action, message="",
       doc_code="", parent=None, on_behalf_of=0)
```

Ba việc làm dần (không chặn P1): rút dữ kiện đang nhồi trong `message` ra cột (trước hết
`login`/`login_failed`); chỗ ghi trên **dòng** thì khai `parent`; chỗ có số phiếu thì truyền
`doc_code`.

### Nguồn 3 — Sự kiện ORM: trước/sau, tự động, không bỏ sót

```
before_flush  → duyệt session.new / dirty / deleted
              → inspect(obj).attrs.<cot>.history → (cũ, mới)
              → gom vào bộ đệm theo request_id (KHÔNG ghi DB trong flush — đệ quy)
after_flush   → điền row_id cho dòng vừa thêm
cuối request  → ghi cả bộ đệm + changed_fields / change_count lên audit cùng request_id
```

### Che dữ liệu nhạy cảm — khai MỘT chỗ, dùng cho cả ba lớp

| Chỗ | Luật |
|---|---|
| `tab_request_log.request_body` | Che theo **tên khóa**: trùng khít `password`, `old_password`, `new_password`, `token`, `refresh_token`, `id_token`, `access_token`, `secret`… **hoặc CHỨA** một trong `SENSITIVE_KEY_MARKERS` → ghi `"***"`. Header `Authorization` **không bao giờ** ghi |
| `tab_request_log.response_body` | Cùng luật trên, **cộng thêm** một lớp thứ hai: `redact_raw_inputs()` bỏ giá trị của khóa `input` trong thân lỗi — xem ghi chú ⚠️ dưới bảng |
| `tab_request_log.error_detail` | `mask_error_detail()` cắt khối `[parameters: {...}]` khỏi vết lỗi — xem ghi chú ⚠️ thứ ba dưới bảng |
| `tab_change_log` | Che theo **tên cột**: `password_hash`, `google_sub`, `reset_token`, mọi cột tên có `token`/`secret`. Bảng `tab_user` mặc định **cấm hết trừ khi cho phép** |
| `snapshot_json` | cùng danh sách cột |

Ghi nhầm một lần là chuỗi băm mật khẩu nằm trong nhật ký vĩnh viễn — test canh phải có từ đợt đầu.

⚠️ **Khớp CHÍNH XÁC tên khóa là không đủ, và bản P1 đầu tiên đã lọt vì thế** (rà soát
10/09/2026). Màn *Cấu hình hệ thống* gửi `PUT /api/settings` với `smtp_password`,
`r2_secret_access_key`, `r2_access_key_id` — **không cái nào trùng khít** danh sách, nên cả ba
bí mật hạ tầng đi thẳng vào bảng chỉ-thêm dưới dạng nguyên văn. Nay `is_sensitive_key()` là
**nơi duy nhất** trả lời câu *"khóa này có cấm ghi giá trị không"*, dùng chung cho cả thân
request lẫn tên cột của P4, và nó khớp cả theo mảnh (`password` · `token` · `secret` ·
`credential` · `api_key` · `access_key` · `private_key`). Cố ý **không** có mảnh `key` trần —
nó nuốt luôn `keyword`, `product_key`.

⚠️ **Thân lỗi 422 vác theo giá trị thô dưới một cái tên vô can.**
`validation_exception_handler` trả `details=exc.errors()`, và Pydantic v2 gắn vào mỗi mục một
khóa **`input`** = đúng thứ người dùng vừa gõ. Gõ mật khẩu sai kiểu là mật khẩu nguyên văn nằm
trong `response_body`, **trong khi `request_body` của chính dòng đó đã che thành `***`** — che
một đầu thì bằng không che. Nặng hơn nữa là lỗi `json_invalid`: `input` khi đó là **toàn bộ**
chuỗi thân request. Luật: `redact_raw_inputs()` thay giá trị bằng dấu vết
`{"_omitted": true, "type": "list", "size": 1}` — đủ để biết người ta gửi *cái gì*, không biết
*là gì*. Bỏ hẳn chứ không che có điều kiện, vì `type` + `loc` + `msg` đã trả lời đủ câu "hỏng ô
nào, vì sao", còn `input` là mảnh duy nhất **không có trần kích thước**.
Người gọi vẫn nhận đủ thân thật; chỉ bản LƯU LẠI mới bị lược.

⚠️ **Lỗ thứ ba, và là lỗ khó thấy nhất trong ba** (`bao-CR-346`). Hai luật trên đều đi trên
**cấu trúc JSON**. Còn `error_detail` là `traceback.format_exc()` — một **chuỗi**, nên không
lớp nào ở trên chạm tới nó. Mà SQLAlchemy nhét thẳng giá trị tham số vào chuỗi đó; vết thật
lấy từ máy:

```
[SQL: INSERT INTO tab_user (username, password_hash) VALUES (%(u)s, %(p)s)]
[parameters: {'u': 'admin', 'p': '$2b$12$...bam-mat-khau...', 'e': 'x@y.z'}]
```

Nghĩa là một cú 500 lúc tạo tài khoản chép nguyên chuỗi băm mật khẩu vào bảng chỉ-thêm —
đúng thứ `SENSITIVE_BODY_KEYS` dựng ra để chặn, đi vòng qua cửa sau. Tệ hơn: nó nổ đúng lúc
500, tức đúng lúc quản trị mở nhật ký ra đọc. `mask_error_detail()` cắt theo **mốc** chứ
không đếm ngoặc (giá trị tham số có thể chứa `]`, có thể xuống dòng), và **giữ** `[SQL: ...]`
vì trong đó chỉ có chỗ giữ tham số `%(u)s`, không có giá trị — mất nó thì đọc vết lỗi không
biết câu nào hỏng.

### Bốn cái bẫy, xử từ đầu

1. **`record(...)` tự `db.commit()`** — nhiều service commit nhiều nhịp. Gom bộ đệm, ghi cuối.
2. **Không tự ghi chính mình** — loại trừ `tab_audit_log`, `tab_change_log`, `tab_request_log`,
   `tab_login_session` (`last_seen_at` dập liên tục), `tab_notification`. Thiếu là vòng lặp vô hạn.
3. **Nhập liệu hàng loạt phải gộp** — `khaosatsanpham.xlsx` 2.666 phiếu ghi từng trường là vài chục
   nghìn dòng một lượt. `actor_kind = 3` bật cờ gộp: một dòng tổng kết, không chi tiết.
4. **Body vào phải đọc một lần rồi trả lại cho endpoint** — Starlette đọc stream body một lần;
   middleware đọc xong phải nhét lại (`request._body`) không thì endpoint nhận body rỗng.

### Một lần bấm nút trông như thế nào sau khi làm

Người dùng sửa đơn giá + số lượng một dòng ĐMH rồi bấm Lưu:

```
tab_request_log
  request_id=3f1c…  user_id=24  session_id=87  ip=27.64.133.181
  PATCH /api/purchase-orders/129/items/4412   route=/api/purchase-orders/{id}/items/{item_id}
  request_body={"unit_price":15000,"qty":120}  http_status=200  duration_ms=84
  response_body={"message":"Đã cập nhật","data":{"id":4412}}

tab_audit_log  (request_id=3f1c…)
  purchase_order/129  doc_code=DMH25090012  action=update  action_group=2
  created_by=24  actor_kind=1  session_id=87  ip=27.64.133.181
  changed_fields="unit_price, qty"  change_count=2
  message="Cập nhật dòng «Thùng carton 3 lớp»"

tab_change_log  (request_id=3f1c…)
  tab_purchase_order_item/4412  op=2  unit_price  12000 → 15000
  tab_purchase_order_item/4412  op=2  qty         100   → 120

tab_login_session/87
  user 24 · Chrome 128 · Windows 11 · máy tính · đăng nhập 07/09 08:12 bằng Google
```

So với dòng thật hôm nay: `('purchase_order', 129, 'update', '', 24, …)`.

Và một lượt **bị chặn**, hôm nay không có dấu gì:

```
tab_request_log
  user_id=31  DELETE /api/purchase-orders/129  http_status=403
  error_code=FORBIDDEN  response_body={"error":{"message":"Không có quyền xóa đơn mua hàng"}}
```

### Cùng lần bấm đó, đúng từng cột (dạng JSON)

Bốn bản ghi thật của cú `PATCH` ở trên — đây cũng là thứ `GET /api/system-logs/{request_id}` (§8)
trả về, gói trong một phong bì.

```json
{
  "request": {
    "id": 51820,
    "request_id": "3f1c9a2e-7b41-4d0c-9e8a-2c6f1d0b7e55",
    "source": 1,
    "created_at": "2026-09-08T10:41:17.208Z",
    "user_id": 24,
    "session_id": 87,
    "ip": "27.64.133.181",
    "method": "PATCH",
    "path": "/api/purchase-orders/129/items/4412",
    "route": "/api/purchase-orders/{id}/items/{item_id}",
    "query_string": "",
    "request_body": {"unit_price": 15000, "qty": 120, "note": "NCC báo tăng giá từ tháng 9"},
    "http_status": 200,
    "response_body": {"message": "Đã cập nhật", "data": {"id": 4412}},
    "error_code": null,
    "error_detail": null,
    "duration_ms": 84,
    "audit_count": 1,
    "change_count": 3
  },
  "audit": [
    {
      "id": 4213,
      "created_at": "2026-09-08T10:41:17.271Z",
      "created_by": 24,
      "actor_kind": 1,
      "on_behalf_of": 0,
      "session_id": 87,
      "request_id": "3f1c9a2e-7b41-4d0c-9e8a-2c6f1d0b7e55",
      "ip": "27.64.133.181",
      "entity": "purchase_order",
      "entity_id": 129,
      "doc_code": "DMH25090012",
      "parent_entity": null,
      "parent_id": null,
      "action": "update",
      "action_group": 2,
      "message": "Cập nhật dòng «Thùng carton 3 lớp»",
      "changed_fields": "unit_price, qty, note",
      "change_count": 3
    }
  ],
  "changes": [
    {"id": 90311, "table_name": "tab_purchase_order_item", "row_id": 4412, "op": 2,
     "field": "unit_price", "before_value": "12000.0000", "after_value": "15000.0000", "is_masked": false},
    {"id": 90312, "table_name": "tab_purchase_order_item", "row_id": 4412, "op": 2,
     "field": "qty", "before_value": "100", "after_value": "120", "is_masked": false},
    {"id": 90313, "table_name": "tab_purchase_order_item", "row_id": 4412, "op": 2,
     "field": "note", "before_value": "", "after_value": "NCC báo tăng giá từ tháng 9", "is_masked": false}
  ],
  "session": {
    "id": 87,
    "user_id": 24,
    "token_version": 3,
    "ip": "27.64.133.181",
    "device_type": 1,
    "os": "Windows 11",
    "browser": "Chrome 128",
    "device_label": "Chrome 128 · Windows 11 · máy tính",
    "login_method": 2,
    "created_at": "2026-09-07T08:12:40Z",
    "last_seen_at": "2026-09-08T10:41:17Z",
    "last_seen_ip": "27.64.133.181",
    "refreshed_at": "2026-09-08T09:12:40Z",
    "expires_at": "2026-09-14T08:12:40Z",
    "revoked_at": null
  }
}
```

Đăng nhập **thất bại** — chưa có ai, chưa có phiên, mật khẩu đã che, không có `changes`:

```json
{
  "request": {
    "request_id": "b8e2…", "source": 1, "user_id": 0, "session_id": null,
    "ip": "118.71.139.127", "method": "POST", "path": "/api/auth/login",
    "route": "/api/auth/login",
    "request_body": {"username": "dttoanh.idagroup@gmail.com", "password": "***"},
    "http_status": 401, "error_code": "INVALID_CREDENTIALS",
    "response_body": {"success": false, "error": {"code": "INVALID_CREDENTIALS",
                      "message": "Sai tên đăng nhập hoặc mật khẩu"}},
    "duration_ms": 212, "audit_count": 1, "change_count": 0
  },
  "audit": [{"entity": "auth", "entity_id": 0, "action": "login_failed", "action_group": 5,
             "created_by": 0, "actor_kind": 1, "ip": "118.71.139.127",
             "message": "Đăng nhập thất bại: dttoanh.idagroup@gmail.com"}],
  "changes": [],
  "session": null
}
```

Một task nền văng lỗi — cũng là một dòng, có traceback:

```json
{
  "request": {
    "request_id": "c41d…", "source": 2, "user_id": 0, "session_id": null, "ip": null,
    "method": null, "path": null, "route": "celery:backup_r2",
    "request_body": {"buckets": ["procurement-prod"], "kind": "daily"},
    "http_status": 500, "error_code": "TASK_FAILED",
    "error_detail": "Traceback (most recent call last):\n  File \"app/tasks/backup.py\", line 41 …\nbotocore.exceptions.EndpointConnectionError: …",
    "duration_ms": 30412, "audit_count": 0, "change_count": 0
  },
  "audit": [], "changes": [], "session": null
}
```

---

## 7. Ai được đọc — BM-001 không được lặp lại

Hôm nay `/api/audit-logs` gác bằng **đúng một thứ: đã đăng nhập**. Bất kỳ ai đăng nhập cũng đọc
được nhật ký mọi phân hệ, kể cả 262 dòng `login` + 84 dòng `login_failed` có IP nhà riêng + email.

Thiết kế lại **tách bốn đường đọc, bốn cửa**:

| Đường đọc | Dùng để | Cửa |
|---|---|---|
| **Dòng thời gian một phiếu** — bắt buộc `entity` **và** `entity_id` | người dùng xem lịch sử phiếu mình mở được | Quyền của **chính chứng từ đó**: `require(entity,'read')` + `get_scoped` trên bản ghi thật. Không cần khóa mới |
| **Tra cứu toàn hệ** — audit + request_log, lọc theo người / ngày / IP / route / `action_group` | quản trị, lúc truy sự cố | Khóa **mới** `audit` |
| **Trước/sau** (`tab_change_log`) và **body vào/ra** (`request_body`) | quản trị | Khóa **mới** `change_log` — tách riêng vì **giá trị cũ và body vào có thể chứa tên NCC**, mà cả cơ chế phương án là để giấu NCC với người yêu cầu (đúng lý do bao-CR-311 không ghi tên NCC vào dấu vết) |
| **Phiên đăng nhập** | tự xem + tự đá thiết bị của mình / quản trị xem tất cả + đá + đăng xuất mọi thiết bị | Khóa **mới** `login_session`, phạm vi `own` cho người thường; hành động đá người khác = `login_session.delete` |

`entity = auth` **chỉ** ra ở đường 2 — khai thành danh sách cấm, đừng để lọt đường 1 bằng
`entity=auth&entity_id=<id user>`.

**Phân quyền.** `ENTITIES` hiện **55** *(đếm lại 09/09/2026 — bản 2.3 ghi 53, số đó có trước
`employee_sensitive` của duoc-CR-314 và `job_position` của duoc-CR-320)*, `SCOPE_FIELDS` khai đủ
55/55 (test `test_pham_vi_khai_du_b07.py` canh — **nhớ sửa số đếm trong test**, kẻo tưởng mình gõ
sai). Thêm `audit`, `change_log`, `login_session` → **58**; `login_session` lọc theo `user_id`,
hai cái kia `PUBLIC` vì đã gác bằng khóa quản trị. Vai trò đang chạy **không tự có** khóa mới
(D-018) — tick tay hoặc `SEED_FORCE_SYNC=true` một lần.

---

## 8. GIAO DIỆN — một màn, ba bảng ở dưới

### 8.1. Vì sao tách bảng mà người dùng không thấy tách

Tách là chuyện **lưu trữ**, không phải chuyện **xem** — như kế toán có sổ cái, sổ chi tiết, sổ
quỹ nhưng tra một màn. Ba lý do tách, mỗi lý do là một thứ mất đi nếu gộp:

| Nếu gộp một bảng | Mất gì |
|---|---|
| Một lần bấm sửa 3 trường = body vào phải lặp 3 lần, hoặc 3 trường nhét vào một JSON | **Không lọc được** *"ai từng sửa `unit_price`"* — phải bới JSON |
| Body vào + giá trị cũ (có thể chứa tên NCC) nằm cùng dòng với câu *"Duyệt phiếu"* mà người yêu cầu được đọc | **Không tách quyền được** — cho xem lịch sử phiếu là lộ NCC (§7) |
| Request 6 tháng, nhật ký nghiệp vụ 24 tháng chung một bảng | **Không dọn riêng được** — giữ theo cái dài nhất, bảng phình gấp 4 |
| Celery / script không có body vào; 213 lời gọi `record()` cũ vẫn phải chạy | Bảng gộp phải chấp nhận **một nửa cột rỗng** tùy dòng — đọc rất khó |

Nhưng phía trên chỉ có **một màn**: một dòng trên màn = một `request_id`, backend gộp ba bảng
lại, giao diện không biết có ba bảng.

### 8.2. Màn `/system/logs` — Nhật ký hệ thống (phân hệ Quản trị, `frontend-v2`)

```
NHẬT KÝ HỆ THỐNG                                  [Theo dõi trực tiếp: BẬT]  [Xuất Excel]
+ Lọc ---------------------------------------------------------------------------------+
| Người [v]  Phiếu [DMH25090012]  Endpoint [v]  IP [    ]  Trường [unit_price]         |
| Từ [08/09 00:00] Đến [08/09 23:59]   Kết quả (o) Tất cả ( ) Chỉ lỗi ( ) Chỉ bị chặn  |
| Nhóm: [Thu mua v]  Nguồn: [API v] [Celery v] [Script v]                              |
+--------------------------------------------------------------------------------------+
 Theo giờ  (cột đỏ = lỗi)                  Theo endpoint: PATCH /po/{id} 41 · POST /login 12 (3 lỗi)

 Lúc       Ai               Thiết bị         Lần bấm                                  Kết quả   Đổi
 10:41:17  H.G.Bảo          Chrome·Win11     Cập nhật dòng «Thùng carton» DMH25090012  200·84ms  3 trường
 10:39:02  N.T.Anh          Safari·iPhone    Xóa Đơn mua hàng DMH25090012              403       -
 10:35:55  hệ thống         celery           Sao lưu R2 (2 tệp, 41 MB)                 ok·12s    -
 10:31:40  (chưa đăng nhập) 118.71.139.127   Đăng nhập thất bại dttoanh.idagroup@…     401       -
 10:30:12  T.V.Minh         Chrome·Win10     Duyệt YCMH0912                            200       7 trường / 3 bảng
 09:58:03  H.G.Bảo          Chrome·Win11     PATCH /api/surveys/88/lines/301           500 !     traceback
```

Cột *Lần bấm* lấy `message` của dòng audit đầu tiên trong request; request không có audit
(403, 500 trước khi tới service) thì hiện `METHOD path`. Cột *Đổi* đọc `change_count` +
số bảng khác nhau trong change_log.

Bấm một dòng mở **ngăn chi tiết bốn tab**:

| Tab | Hiện gì | Lấy từ | Cần khóa |
|---|---|---|---|
| **Tổng quan** | Một câu ghép: *ai, lúc nào, từ máy nào, gọi vào đâu, kết quả gì, đổi gì* | cả ba | `audit` |
| **Request** | Method · route · body vào (đã che) · mã trả về · body ra khi lỗi · **traceback nếu 500** · `request_id` có nút copy | `tab_request_log` | `change_log` (vì body vào) — thiếu thì tab **ẩn**, không 403 |
| **Thay đổi** | Bảng *Bảng / Dòng / Trường / Trước / Sau*, tô đỏ-xanh; gom theo bảng khi một cú Duyệt đụng 3 bảng | `tab_change_log` | `change_log` |
| **Phiên** | Thiết bị, IP, đăng nhập lúc nào, **các lần bấm khác trong cùng phiên** (± 30 phút), nút *Đá phiên này* | `tab_login_session` | `login_session` |

**Theo dõi trực tiếp** = poll 5 giây khi bật, để vừa thao tác ở tab kia vừa xem log chạy — cách
debug hay dùng nhất.

### 8.3. Bốn lối vào debug

Mỗi lối là một bộ lọc sẵn, khớp đúng cách người ta hỏi khi có sự cố:

| Người ta hỏi | Lối vào | Đi tiếp |
|---|---|---|
| *"Phiếu YCBG05092603 sao hiện sai?"* | Gõ **mã phiếu** → mọi lần bấm từng chạm phiếu đó, kể cả trên dòng con (nhờ `parent_entity`) | Mở lần bấm nghi ngờ → tab *Thay đổi* thấy `survey_request_line_id` bị gắn nhầm → tab *Request* thấy body gửi lên id nào → **biết là code hay tay** |
| *"Hôm nay hệ thống lỗi gì?"* | Tick **Chỉ lỗi** + biểu đồ theo giờ | Nhóm theo `error_code` + `route` → *"`PATCH /surveys/{id}/lines/{line}` lỗi 500 lặp 6 lần từ 09:58"* → tab *Request* đọc traceback, không cần vào container |
| *"Tài khoản này có bị lộ không?"* | Gõ **người** hoặc **IP** | Thấy 2 phiên cùng lúc Hà Nội + Cần Thơ → tab *Phiên* → **Đăng xuất mọi thiết bị** |
| *"Ai đổi đơn giá dòng này?"* | Lọc **Trường = `unit_price`** + mã phiếu | Ra đúng dòng, trước/sau, người, máy — là câu `WHERE field='unit_price'`, lý do §4.3 chọn một dòng mỗi trường |

### 8.4. API cho màn — hai endpoint, ba truy vấn một trang

| Endpoint | Trả về | Khóa |
|---|---|---|
| `GET /api/system-logs?user_id&doc_code&route&ip&field&table&from&to&status=error\|blocked\|all&action_group&source&page` | Trang danh sách, mỗi phần tử = một `request_id` kèm audit đầu tiên + `change_count`. **Đúng 3 truy vấn cho cả trang** bất kể bao nhiêu dòng: 1 trên request_log (phân trang) + 2 `IN (request_id...)` sang audit và change_log. Lọc theo `doc_code`/`field`/`table` là lọc trước trên bảng con lấy tập `request_id` rồi mới vào request_log — vẫn 3 truy vấn. Test đếm truy vấn canh như `steps_service` của Nghỉ phép | `audit` |
| `GET /api/system-logs/{request_id}` | Gói đầy đủ đúng hình JSON ở §6: `{request, audit[], changes[], session}`. Thiếu `change_log` thì `request.request_body`/`response_body`/`error_detail` và `changes` **bị lược** khỏi phong bì — lược ở backend, không ở giao diện | `audit` (+ `change_log`) |
| `GET /api/system-logs/summary?from&to` | Số liệu cho biểu đồ theo giờ + theo endpoint + theo `error_code` | `audit` |

`/api/audit-logs` cũ (dòng thời gian một phiếu) **giữ nguyên chữ ký** cho `AuditTimeline` của
CRUD v2, chỉ vá cửa (bao-CR-313) và trả thêm `request_id` + `changed_fields` + `change_count` để
bật nút *Xem chi tiết* dẫn sang `/system/logs?request_id=…`.

### 8.5. Phiên đăng nhập hiện ở BA chỗ — một bảng, một API

Bảng `tab_login_session` chỉ có một, API cũng một
(`GET /api/login-sessions?user_id&active_only`, `POST /api/login-sessions/{id}/revoke`,
`POST /api/users/{id}/logout-all`), khác nhau ở **phạm vi** và **nút bấm**:

| Chỗ | Ai xem | Thấy gì | Nút | Khóa |
|---|---|---|---|---|
| **Quản trị › Phiên đăng nhập** (`/system/sessions`) | quản trị | Mọi phiên **đang mở** toàn hệ; lọc người / IP / thiết bị / phương thức; cảnh báo phiên đổi IP giữa chừng, một người nhiều phiên | *Đá phiên* · *Đăng xuất mọi thiết bị* · *Bắt đăng nhập lại* | `login_session` phạm vi `all` + `login_session.delete` |
| **Trang cá nhân › Thiết bị của tôi** (`/me`, tab mới) | mọi người | Phiên của **chính mình**: thiết bị, IP, đăng nhập lúc nào, hoạt động gần nhất; phiên hiện tại được đánh dấu | *Đá thiết bị này* · *Đăng xuất mọi thiết bị khác* (Q10) | `login_session` phạm vi `own` — cấp mặc định cho mọi vai trò |
| **Nhân sự › hồ sơ nhân viên › tab "Tài khoản & thiết bị"** (`/hr/employees/:id`) | hành chính nhân sự | Tài khoản gắn với nhân sự này (`tab_user.employee_id` — **id nhân sự khác id tài khoản**, xem luật `assignee_id`), phiên đang mở, **lịch sử đăng nhập 90 ngày** = phiên thành công + `login_failed` từ audit | *Khóa tài khoản + đăng xuất mọi thiết bị* — nút của quy trình **nghỉ việc**; không có nút đá lẻ | `login_session` phạm vi `all` (đọc) — cấp cho vai trò nhân sự, **không** cấp `delete`; khóa tài khoản đi qua khóa `user.write` sẵn có |

Vì sao Nhân sự **nên có** tab này: ba câu HR hay hỏi — *"người này còn dùng hệ thống không"*,
*"nghỉ việc rồi mà còn phiên nào sống không"*, *"đăng nhập lúc 2 giờ sáng từ đâu"* — đều là câu
trên bảng phiên, và hôm nay không ai trả lời được. Vì sao **không** cho HR đá lẻ: đá một thiết bị
là việc quản trị/bảo mật; HR cần đúng một thao tác trọn gói lúc nghỉ việc.

**Lịch sử đăng nhập** không phải bảng mới: đọc `tab_login_session` (thành công, kể cả đã
revoke) **hợp** với `tab_audit_log WHERE entity='auth' AND action='login_failed'` (thất bại), sắp
theo thời gian. Cột: lúc · kết quả · phương thức · thiết bị · IP · kết thúc thế nào
(`revoke_reason`).

---

## 9. Dữ liệu cũ và dung lượng

| Việc | Kết luận |
|---|---|
| 4.201 dòng audit cũ | Cột mới `NULL`. Request/phiên/trước-sau **chưa từng tồn tại**, không backfill được |
| **346 dòng `login` + `login_failed`** | **Backfill được, nên làm**: bóc IP trong `message` ra cột `ip` bằng regex |
| 1.769 dòng `update` rỗng | Vô nghĩa mãi mãi. Không xóa (bằng chứng "có người đụng vào lúc đó") |
| 1.135 dòng đang hiện mã Anh | Đọc được ngay khi khai `ACTION_CATALOG`, không sửa dữ liệu |

**Vì sao `action` giữ VARCHAR** dù R2/QĐ-11 nói cái mới phải là số: đã có 4.201 dòng thật và đọc
thẳng trong DB lúc truy sự cố là việc thường xuyên — giống ca Thu mua (QĐ-9): **giữ mã chuỗi,
ràng bằng bộ mã đóng**. Mọi cột *mới* (`actor_kind`, `action_group`, `op`, `device_type`,
`login_method`, `revoke_reason`) đều **SMALLINT + IntEnum** đúng R2.

### Dung lượng — tính lại bằng số đo thật (bản 2.4, đo prod 09/09/2026)

Bản 2.3 tính trên các con số ước. Bản 2.4 đo thẳng trên hệ thật, **nhịp dùng khớp gần đúng, hai
chỗ lệch đều lệch về phía an toàn**:

| Chỉ số | Bản 2.3 ước | Đo thật 09/09/2026 |
|---|---|---|
| Dòng audit / ngày | 112 | **124** (trung bình 30 ngày) · **214** (7 ngày qua) · đỉnh **409** (07/09) |
| Lượt không phải GET / ngày | ~300 | **265** (nginx prod, 24 giờ) |
| Trong đó `POST /api/auth/refresh` | không tính riêng | **126 — chiếm 48%** → QĐ-A §4.1 |
| Lượt đăng nhập / ngày | ~40 | **5,6** (169 dòng `login` trong 30 ngày) — người dùng đăng nhập một lần rồi ngồi cả ngày |
| Số dòng trung bình một phiếu YCMH | không tính | **1,9** — phiếu ngắn, nên một lần sửa đẻ ~8 dòng change chứ không phải ~28 |
| Cỡ thật một dòng audit trên đĩa | — | **203 B** (0,88 MB / 4.531 dòng, đã gồm chỉ mục) |
| **Cỡ toàn bộ CSDL prod** | — | **18,7 MB** |

Con số cuối là thứ đáng nhớ nhất: **bật nhật ký lên là CSDL phình gấp 7–12 lần so với hôm nay**,
và toàn bộ phần phình đó là nhật ký chứ không phải dữ liệu nghiệp vụ.

> ⚠️ **Bảng dưới là số của bản 2.4 và dòng `tab_request_log` đã HẾT HẠN.** Bản 2.5 ghi cả
> GET (§4.1), nên dòng đó thành: ~3.000 dòng/ngày, **~350 B/dòng** (GET không có `request_body`,
> không giữ `response_body`) → **~380 MB/năm nếu giữ nguyên**. Đó đúng là lý do §4.1.1 tồn tại:
> hạn **90 ngày** cho dòng GET kéo phần đọc về **~95 MB ổn định**, còn phần ghi giữ đủ 16 tháng
> vẫn là ~41 MB. Tổng bốn bảng ổn định quanh **~215 MB** thay vì ~120 MB — vượt khung 180 MB đã
> trình khách, nhưng ổ VPS còn 23 GB và bốn bảng này đã ra khỏi bản sao lưu hằng đêm (QĐ-C) nên
> không kéo theo chi phí R2 tăng theo cấp số. Cần siết thêm thì hạ `GET_RETENTION_DAYS` — một
> hằng, một chỗ.

| Bảng | Cỡ dòng | Dòng/ngày *(đo)* | Một năm | Giữ trong DB |
|---|---|---|---|---|
| `tab_request_log` — *(số bản 2.4, xem cảnh báo trên)* | ~800 B | ~140 | **~41 MB** | **16 tháng** |
| `tab_audit_log` sau khi thêm cột | ~500 B | 124 | **~23 MB** | **16 tháng** |
| `tab_change_log` — một dòng mỗi trường, cộng ảnh chụp lúc thêm/xóa | ~130 B | ~480 | **~25 MB** | **16 tháng** |
| `tab_login_session` | ~700 B | ~6 | **~1,5 MB** | **16 tháng** sau `revoked_at` |

Cỡ dòng `request_log` tính theo **mix endpoint thật** chứ không phải một số trung bình chung: hai
đường nặng nhất là `PATCH /api/purchase-requests/{id}` (35 lượt/ngày) và `PATCH
/api/purchase-orders/{id}` (14 lượt/ngày), body chừng 600 B; phần còn lại (duyệt · nộp · gán ·
đánh dấu đã đọc) chỉ vài chục byte.

Tổng **~90 MB/năm** ở nhịp hiện tại; giữ 16 tháng thì CSDL ổn định quanh **~120 MB**. Nếu nhịp
dùng lên bằng tuần bận nhất đã đo (gấp 1,7 lần) thì **~150 MB/năm, ~200 MB ổn định** — vẫn nằm
dưới khung 180 MB đã trình khách, **không phải đi xin duyệt lại**. Nếu giữ **cả body ra cho 2xx**
thì request_log gấp đôi — đó là Q9. Con số giả định đã có chốt gộp nhập liệu hàng loạt (§6 bẫy 3);
không có nó, một lần `import` nuốt trọn ngân sách cả năm.

Ổ đĩa VPS còn **23 GB trống**, nên vài trăm MB **không phải vấn đề**. Vấn đề nằm ở chỗ khác:

**Sao lưu hằng đêm — chỗ tốn thật, bản 2.3 chưa tính.** Hôm nay mỗi bản dump nén còn **1,09 MB**,
giữ `BACKUP_KEEP = 30` bản (2 lần/ngày, ~15 ngày) → tổng trên R2 đúng **33 MB**. Thêm ~120 MB
nhật ký vào CSDL, nén lại chừng 8–15 MB mỗi bản → **250–450 MB trên R2**, gấp gần chục lần hiện
nay, và mỗi lượt dump dài thêm, ngày hai lần. Mà nhật ký **đã có đường lưu trữ riêng của nó**
(bảng dưới), nên nằm trong bản sao lưu hằng đêm là **lưu hai lần cùng một thứ**.

**QĐ-C (bản 2.4, chốt 09/09/2026) — bốn bảng nhật ký KHÔNG nằm trong bản sao lưu hằng đêm.**
Nhật ký đi đường lưu trữ riêng của nó (bảng dưới), sao lưu hằng đêm quay về đúng việc của nó là
giữ **dữ liệu nghiệp vụ**. Đánh đổi đã biết và chấp nhận: **phục hồi từ bản sao lưu sẽ ra một hệ
thống trắng nhật ký**, muốn có lại phải nạp từ gói trên R2 — đúng tinh thần §12, nhật ký để truy
trách nhiệm chứ không phải để khôi phục dữ liệu.

| Việc | Cách làm |
|---|---|
| Dump hai lượt, nối lại | `modules/backup/service.py` chạy **hai** lượt `mysqldump` rồi nối thành một tệp `.sql`: lượt 1 dump cả CSDL kèm `--ignore-table=<db>.tab_request_log` (và ba bảng kia); lượt 2 `--no-data` **đúng bốn bảng đó**. **Không được** chỉ dùng `--ignore-table` một lượt: cờ đó bỏ luôn cả `CREATE TABLE`, phục hồi xong bảng **không tồn tại**, mà `alembic_version` lại đang ở head nên `alembic upgrade head` không dựng lại — hệ thống chạy lên rồi chết ở truy vấn đầu tiên chạm nhật ký |
| Giữ nguyên phân vùng | Lượt `--no-data` giữ cả mệnh đề `PARTITION BY RANGE` nên bảng phục hồi ra đúng hình, chỉ rỗng ruột |
| Khai một chỗ | Danh sách bốn bảng khai **một hằng** trong `backup/service.py`, dùng lại cho cả hai lượt và cho tác vụ đóng gói — ba nơi chép tay là ba nơi lệch nhau |
| Kiểm lại sau khi bật | Phục hồi thử một bản vào CSDL rác, chạy `start.prod.sh`, mở một màn có dòng thời gian: phải lên **rỗng**, không phải lỗi 500 |

**Kèm theo QĐ-C: đổi nhịp đóng gói từ MỖI NĂM sang MỖI THÁNG.** Gói theo năm là đúng cho lưu
trữ dài hạn, nhưng nếu nhật ký không còn trong bản sao lưu hằng đêm nữa thì **từ tháng 1 tới
tháng 12 sẽ có một khoảng trống**: mất CSDL giữa năm là mất trắng nhật ký của cả năm đang chạy,
vì gói của năm đó chưa tồn tại. Nên tác vụ đóng gói chạy **đầu mỗi tháng cho tháng vừa xong**;
mất nhiều nhất là nhật ký của tháng đang chạy. Cam kết với khách ở Q2 **không đổi** — vẫn 16
tháng, vẫn lưu trữ riêng trên R2, chỉ là gói nhỏ hơn và dày hơn.

**Hạn giữ và gói lưu trữ (Q2, khách chốt 08/09/2026).** Một hạn chung **16 tháng** cho cả bốn
bảng — đủ để so cùng kỳ năm trước (12 tháng) cộng một quý đối chiếu. Nhật ký **không đi theo
sao lưu**: sao lưu DB lên R2 chỉ giữ ngắn hạn, còn nhật ký phải giữ được lâu hơn thế, nên tách
thành **gói lưu trữ riêng**, để riêng:

| Việc | Cách làm |
|---|---|
| Chia bảng theo năm | Bốn bảng nhật ký **PARTITION BY RANGE (YEAR(created_at))**, mỗi năm một phân vùng. Dọn một năm cũ = `DROP PARTITION`, không `DELETE` từng dòng trên bảng vài triệu dòng |
| Đóng gói một tháng | Task Celery beat chạy **đầu mỗi tháng** (QĐ-C, trên): xuất trọn tháng vừa xong của bốn bảng ra `log-<năm>-<tháng>.jsonl.gz` (kèm `.sha256`), đẩy lên R2 thư mục `log-archive/<năm>/`, **khác** thư mục sao lưu DB và **không** nằm trong luật xóa sao lưu cũ. Phân vùng vẫn theo năm — gói theo tháng chỉ là nhịp xuất, không phải cách chia bảng |
| Xóa trong DB | Task Celery beat **hằng đêm** bỏ phân vùng nào **cả năm đó đã quá 16 tháng** *và* **đủ 12 gói tháng** của năm đó đã có trên R2 (kiểm `.sha256` từng gói) — thiếu dù một gói thì **không xóa**, ghi cảnh báo |
| Đọc lại gói cũ | Không nạp lại vào bảng đang chạy. Nạp vào bảng `*_archive` riêng hoặc đọc thẳng tệp; màn §8 có ô *Năm* chỉ liệt kê năm còn trong DB, năm đã gói thì hiện đường dẫn gói |
| Lịch sử cũ trước khi bật | 4.201 dòng audit hiện có nằm trong phân vùng năm của chúng, cùng luật |

`DROP PARTITION` là thao tác không hoàn tác được, nên thứ tự **gói xong mới xóa** là luật cứng,
và task xóa phải chạy **sau** task đóng gói ít nhất một ngày.

---

## 10. Chia đợt

| Đợt | Nội dung | Được gì ngay | Phụ thuộc |
|---|---|---|---|
| **P0** | **Gác cửa đọc** (BM-001) — tách đường đọc, chặn `entity=auth` | Bịt lỗ đang mở trên prod. Đã tách thành **bao-CR-313**, xong 09/09/2026 | — |
| **P1** | Middleware ngữ cảnh (IP lấy bằng `core/client_ip.get_client_ip` của bao-CR-313, không bật `--proxy-headers`) + **`tab_request_log`** + 6 cột ngữ cảnh trên audit. Kèm **QĐ-A** (bỏ qua gia hạn phiên thành công, §4.1) và **QĐ-B** (`request_id` là `BINARY(16)`, §4.5) — hai thứ này phải đúng **ngay từ migration đầu**, sửa sau là đổi kiểu cột trên bảng đã vài trăm nghìn dòng | **Endpoint nào · input · output · IP · lượt bị chặn** — 213 lời gọi cũ không sửa | — |
| **P2** | `ACTION_CATALOG` + nhãn bắt buộc + test canh + `action_group` | 1.135 dòng đang hiện mã Anh đọc được ngay | — |
| **P3** | `tab_login_session` + `jti` + `token_version` + 4 thao tác điều khiển phiên + ba chỗ hiện phiên (§8.5: Quản trị · Trang cá nhân · tab Nhân sự). **Kèm việc dọn:** bỏ dòng audit `refresh` cho nhánh gia hạn **thành công** mà bao-CR-313 đang ghi, chuyển sang dập `refreshed_at` / `refresh_count` / `last_seen_ip` theo QĐ-A | **Thiết bị gì · đá · đăng xuất mọi thiết bị · bắt đăng nhập lại** (BM-002) | P1 |
| **P4** | `tab_change_log` + sự kiện ORM + che cột + chốt gộp nhập liệu | **Trước/sau** — nặng nhất, làm sau cùng trong nhóm nền | P1 |
| **P5** | Màn `/system/logs` (§8.2–8.4): danh sách gộp theo `request_id`, ngăn 4 tab, theo dõi trực tiếp, biểu đồ; `/api/audit-logs` trả thêm `request_id` để *Xem chi tiết* từ dòng thời gian phiếu | **Gom một chỗ, debug trên giao diện** | P2, P4 (tab *Thay đổi* ẩn khi chưa có P4 — màn vẫn dùng được ngay sau P1) |
| **P1b** | **`bao-CR-346` (10/09/2026)** — đảo luật lọc thành *ghi hết GET* (§4.1), che vết lỗi SQL, `device_hash` + `referer`, `record(...)` cho `role/` + `user/`, và **kéo hai việc của P6 lên**: đóng gói R2 hằng tháng (§4.1.2) + dọn dòng GET 90 ngày (§4.1.1) | **Ai ĐỌC cái gì** — thứ P1 hoàn toàn không có. Và nhật ký có bản sao thứ hai ngoài máy | P1 |
| **P6** | Phân vùng theo năm + dọn 16 tháng (§9) + **QĐ-C: tách bốn bảng nhật ký khỏi sao lưu hằng đêm bằng dump hai lượt** (§9) + cảnh báo: đăng nhập IP lạ, phiên đổi IP giữa chừng, xóa hàng loạt trong một `request_id`, nhiều 403 liên tiếp. *(Phần đóng gói R2 hằng tháng đã làm ở P1b.)* | Nhật ký giữ được lâu hơn sao lưu mà DB không phình | P3, P4 |

**P1 là phần đáng làm nhất so với công bỏ ra**: một middleware trả lời được 4 trong 6 câu hỏi ở §1
(endpoint, input/output, từ đâu, bị chặn) mà không đụng 213 lời gọi, không đụng ORM.

⚠️ **Vì sao kéo gói R2 ra khỏi P6.** QĐ-C loại bốn bảng nhật ký khỏi bản sao lưu hằng đêm,
nhưng gói R2 lại xếp ở giai đoạn cuối. Khoảng giữa hai mốc đó, nhật ký tồn tại **đúng một
bản, nằm trên chính cái máy** mà kẻ tấn công đang đứng — mà nhật ký chỉ có giá trị khi người
bị nó ghi lại không xóa được nó. Hai quyết định đúng riêng lẻ, xếp sai thứ tự thành một lỗ.

---

## 11. Câu hỏi đã chốt

**Khách chốt cả 12 câu ngày 08/09/2026 theo đúng cột đề xuất, trừ Q2** (đổi từ ba hạn khác
nhau thành một hạn 16 tháng + gói theo năm). Cột phải là **quyết định**, không còn là đề xuất.

| | Câu hỏi | Chốt 08/09/2026 |
|---|---|---|
| **Q1** | Sửa thì ghi **một dòng mỗi trường** hay chụp **nguyên bản ghi**? | Một dòng mỗi trường (lọc được theo trường; đo lại bản 2.4 còn **~25 MB/năm**, không phải 65 MB như ước ban đầu — phiếu thật chỉ 1,9 dòng) |
| **Q2** | Giữ bao lâu? | **16 tháng** cho cả bốn bảng; sau 16 tháng được xóa, nhưng **mỗi năm đóng một gói lưu trữ riêng** lên R2 trước khi xóa (§9). Khách nói rõ: sao lưu hệ thống không giữ lâu, riêng nhật ký thì giữ theo năm được |
| **Q3** | Ai đọc **trước/sau** và **body vào**? | Khóa riêng `change_log`, chỉ quản trị — có thể chứa tên NCC |
| **Q4** | Có làm **đá thiết bị / đăng xuất mọi thiết bị / bắt đăng nhập lại** không? | **Có**, cả bốn — thêm một cột `token_version` là xong phần nền |
| **Q5** | Đăng nhập **thất bại** ghi ở đâu? | `tab_request_log` (`401`) + `tab_audit_log` (`login_failed`); **không** vào bảng phiên |
| **Q6** | Có ghi lượt **XEM** không? | Không ghi GET, **trừ** xuất dữ liệu và xem tệp đính kèm |
| **Q7** | Nhập liệu hàng loạt ghi chi tiết hay gộp? | **Gộp** |
| **Q8** | Backfill IP từ `message` của 346 dòng đăng nhập cũ? | **Có** |
| **Q9** | `response_body` giữ **luôn** hay **chỉ khi lỗi**? | **Chỉ khi lỗi**; 2xx giữ `message` + `data.id`. Kết quả thành công đã nằm ở change_log rồi, giữ thêm là gấp đôi dung lượng để lưu thứ có sẵn |
| **Q10** | Người thường có được **tự đá thiết bị của mình** không? | **Có** — tab *Thiết bị của tôi* ở Trang cá nhân, phạm vi `own` |
| **Q11** | Hồ sơ **Nhân sự** có tab *Tài khoản & thiết bị* không, và HR được làm gì? | **Có** — đọc phiên + lịch sử đăng nhập 90 ngày; một nút *Khóa + đăng xuất mọi thiết bị* cho nghỉ việc; **không** đá lẻ (§8.5) |
| **Q12** | Lỗi 500 / task nền văng lỗi có lưu **traceback vào DB** không? | **Có**, `error_detail` cắt 16 KB, cùng hạn giữ 16 tháng — để debug trên màn, không phải vào container |

### Chốt thêm ở bản 2.4 — quyết định kỹ thuật nội bộ, không phải hỏi khách

Ba mục dưới đây sinh ra từ đợt đo lại prod ngày 09/09/2026, không đổi phạm vi cũng không đổi
cam kết với khách, chỉ đổi cách làm bên trong:

| | Việc | Chốt |
|---|---|---|
| **QĐ-A** | Gia hạn phiên có ghi nhật ký không? | **Thành công thì không ghi** (chỉ dập `refreshed_at` / `refresh_count`); **đổi IP hoặc thất bại thì ghi đủ**. Cắt 46.000 dòng rác/năm mà vẫn đóng BM-003 — §4.1 |
| **QĐ-B** | `request_id` lưu kiểu gì? | **`BINARY(16)`** ở cả ba bảng, hiện ra ngoài vẫn là chuỗi 36 ký tự; `token_id` giữ `CHAR(36)` — §4.5 |
| **QĐ-C** | Bốn bảng nhật ký có nằm trong bản sao lưu hằng đêm không? | **Không** — dump hai lượt (`--ignore-table` cho dữ liệu + `--no-data` để giữ cấu trúc); đánh đổi: phục hồi ra hệ thống trắng nhật ký. Kèm theo, nhịp đóng gói lên R2 đổi từ mỗi năm sang **mỗi tháng** để năm đang chạy không chỉ còn một bản. Làm ở P6 — §9 |

---

## 12. Những gì thiết kế này KHÔNG làm

- **Không dựng lại được lịch sử đã qua.** Từ ngày bật trở đi mới có request / trước-sau / phiên.
- **Không thay được sao lưu.** Nhật ký để truy trách nhiệm, không phải để khôi phục dữ liệu.
- **Không chặn thao tác sai** — chỉ ghi lại. Muốn chặn là việc ở từng nghiệp vụ.
- **Không ghi GET thường** — ai *xem* phiếu nào không truy được, trừ xuất dữ liệu và tệp đính kèm (Q6).
- **Không sửa 213 lời gọi `record(...)` cho hay hơn.** Ngữ cảnh tự giàu lên, còn `message` rỗng
  thì vẫn rỗng — muốn có câu chữ tử tế phải sửa từng chỗ, làm dần.
- **Không thay `docker logs`.** Màn §8 chỉ có thứ đã vào tới middleware hoặc task nền: log nginx,
  Cloudflare, lỗi lúc uvicorn chưa khởi động xong vẫn phải xem ở container; `request_id` in vào
  log là sợi dây nối sang, không phải kéo hết về DB.
