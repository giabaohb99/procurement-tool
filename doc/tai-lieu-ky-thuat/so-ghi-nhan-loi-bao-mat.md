# SỔ GHI NHẬN LỖI BẢO MẬT

**Bản 1.0 — 07/09/2026.** Mở sổ nhân ticket YCBG05092603.

---

## 0. Vì sao có tệp này

Ngày 07/09/2026 khách báo một phiếu Yêu cầu báo giá hiện kết quả khảo sát của mặt hàng khác.
Truy ra được thủ phạm, nhưng phải mở database đọc cột `created_by` của chính dòng dữ liệu —
vì thao tác đó không ghi một dòng nhật ký nào. Đi soát vòng quanh chỗ đó thì lòi ra **bảy chỗ
hở**, trong đó **một chỗ đang mở trên hệ thật**.

Trước hôm nay không có chỗ nào ghi lại những phát hiện kiểu này. Chúng nằm rải trong nhật ký
trò chuyện, trong bình luận mã nguồn, trong trí nhớ của người phát hiện — nghĩa là **lần sau
gặp lại vẫn phải tìm lại từ đầu**, và không ai trả lời được câu "hệ thống mình còn hở chỗ nào"
mà không đi soát lại toàn bộ.

Tệp này là câu trả lời cho câu hỏi đó. Nó **không** phải tài liệu thiết kế — thiết kế cách vá
nằm ở tệp riêng của từng CR. Nó là **danh sách**: cái gì hở, hở tới đâu, ai đã vá chưa.

---

## 1. Cách ghi

**Một phát hiện = một dòng `BM-xxx`**, đánh số tăng dần, không tái sử dụng số. Xóa một dòng
là mất dấu, nên phát hiện sai thì **đổi trạng thái sang `Bác bỏ` kèm lý do**, đừng xóa.

**Mức độ** — đo bằng *"ai khai thác được"* và *"khai thác xong lấy được gì"*, không đo bằng
cảm giác:

| Mức | Nghĩa |
|---|---|
| **Cao** | Người ngoài, hoặc bất kỳ tài khoản nội bộ nào, lấy được dữ liệu / quyền không thuộc về họ. Vá trước, không xếp hàng. |
| **Trung bình** | Cần điều kiện kèm theo (token đã lộ, tài khoản đã có sẵn quyền cao, thời điểm cụ thể), hoặc hậu quả là *không truy được* chứ chưa mất dữ liệu. |
| **Thấp** | Làm yếu khả năng phòng thủ về sau, chưa gây hại ngay. |

**Trạng thái:** `Mở` → `Đang vá (bao-CR-xxx)` → `Đã vá (ngày, sha)` → hoặc `Chấp nhận rủi ro`
(phải ghi ai chấp nhận và vì sao) / `Bác bỏ`.

**Mỗi dòng bắt buộc có BẰNG CHỨNG** — đường dẫn `tệp:dòng`, hoặc số đo trên hệ thật. Không
ghi phỏng đoán vào sổ này; nghi ngờ thì đi đo trước.

**Khi nào ghi:** thấy là ghi, kể cả khi vá được ngay trong ngày. Dòng đã vá vẫn có giá trị —
nó là bằng chứng cho lần soát sau rằng chỗ này từng hở.

---

## 2. Danh sách

| ID | Mức | Phát hiện | Trạng thái |
|---|---|---|---|
| BM-001 | **Cao** | `/api/audit-logs` chỉ gác bằng đăng nhập — mọi tài khoản đọc được nhật ký của mọi phân hệ | **Đang vá (bao-CR-313).** `erp-v2` đã gác từ 05/09 (d413481f). `main`: mã + 16 test xong local 08/09/2026, **chưa commit, prod vẫn hở** |
| BM-002 | **Cao** | Không có phiên đăng nhập phía máy chủ — token lộ thì không thu hồi được | **Mở** |
| BM-003 | Trung bình | Gia hạn token không để lại dấu vết nào | Đang vá (bao-CR-313) — mã xong local 08/09/2026, chưa commit |
| BM-004 | Trung bình | Giới hạn tần suất đăng nhập dùng chung MỘT xô cho cả công ty | Đang vá (bao-CR-313) — mã xong local 08/09/2026, chưa commit; phải kiểm `CF-Connecting-IP` trên dev sau deploy |
| BM-005 | Trung bình | Nhật ký không lưu giá trị trước / sau — không chứng minh được đã đổi gì | Đang vá (bao-CR-312, mới ở mức đề xuất) |
| BM-006 | Thấp | Dấu vết là tùy chọn theo từng lời gọi — quên gọi là mất | Vá một phần (bao-CR-311) |
| BM-007 | Thấp | Dòng nhật ký không có IP / trình duyệt / mã lượt gọi | Đang vá (bao-CR-312, mới ở mức đề xuất) |

---

### BM-001 — Nhật ký của cả hệ đọc được bằng bất kỳ tài khoản nào

**Mức: Cao. Trạng thái: MỞ, đang chạy trên hệ thật.**

`backend/app/modules/audit/controller.py:28` — toàn bộ phân hệ nhật ký là **một endpoint duy
nhất**, và nó gác bằng đúng một thứ: `user=Depends(get_current_user)`. Không `require(entity,
"read")`, không `apply_scope`. Tham số `entity` do người gọi truyền thẳng vào câu truy vấn, và
`entity_id` **được phép bỏ trống** — bỏ trống nghĩa là lấy nhật ký của *mọi* bản ghi thuộc
entity đó, tới 500 dòng một lượt.

Nghĩa là bất kỳ ai đăng nhập được — nhân viên thời vụ, tài khoản demo, người vừa bị hạ quyền
nhưng chưa khóa — gọi được:

```
GET /api/audit-logs?entity=auth&limit=500
```

Đo trên hệ thật ngày 07/09/2026: bảng có **18 entity**, riêng `auth` **341 dòng**. Nội dung
thật của những dòng đó:

```
login         | Đăng nhập Google (IP 27.64.133.181)
login_failed  | Đăng nhập thất bại: tài khoản 'dttoanh.idagroup@gmail.com'
                — Sai tài khoản hoặc mật khẩu (IP 118.71.139.127)
```

Tức là lấy được **địa chỉ IP nhà riêng của từng người**, **email tài khoản**, và **lịch sử ai
gõ sai mật khẩu lúc nào**. Đổi `entity` sang `payment_request` · `payable` · `supplier` ·
`employee` · `purchase_order` thì ra nhật ký của các phân hệ đó — 1813 dòng đơn mua hàng, 82
dòng yêu cầu thanh toán — bất kể người gọi có quyền vào phân hệ đó hay không.

Đây là **chỗ duy nhất trong hệ bỏ qua cả hai trục phân quyền**. Mọi controller khác đều đi qua
`require(...)` rồi `apply_scope(...)`; endpoint này viết từ sớm và không ai soát lại.

Hai điều đáng nói thêm:

1. **Nó làm nặng thêm mọi lỗi khác trong sổ này.** Bất cứ thông tin nhạy cảm nào lỡ lọt vào ô
   `message` đều thành công khai nội bộ. Đó chính là lý do bao-CR-311 cố ý **không ghi tên nhà
   cung cấp** vào dấu vết phương án — lúc quyết định, lý do đưa ra là "người yêu cầu có khóa
   `survey_request.read`". Lý do đó **nhẹ hơn sự thật**: không cần khóa nào cả, chỉ cần đăng
   nhập. Quyết định vẫn đúng, nhưng đúng vì một lý do nghiêm trọng hơn.
2. **Không có dấu vết của việc đọc trộm.** Endpoint này không ghi lại chính nó, nên nếu chuyện
   đã xảy ra rồi thì hôm nay không cách nào biết.

**Hướng vá (bao-CR-313, xem mục 3).** Gác bằng khóa `read` của **chính entity được hỏi** —
tra `ENTITIES`, entity lạ thì 400. Riêng `auth` (và mọi entity không phải chứng từ) chỉ mở cho
vai trò quản trị. Cấm bỏ trống `entity_id` trừ khi có khóa cấp cao. Bước hai là chạy
`apply_scope` trên chính bản ghi được hỏi, để người chỉ thấy phiếu phòng mình thì cũng chỉ đọc
được nhật ký phiếu phòng mình.

**Cập nhật 08/09/2026 — đã gõ mã trên `main`, chưa commit.** Khi bắt tay mới thấy `erp-v2`
đã có `_guard` từ 05/09 (d413481f, minhduoc-tran) nên `main` chép lại + thêm ba chốt. Luật
cuối cùng KHÁC hướng vá ở trên ba chỗ, ghi lại để khỏi cãi nhau sau:

- Entity lạ trả **403 chứ không 400**, cùng mã với "không có khóa" — người dò không phân
  biệt được "entity không tồn tại" với "tồn tại mà tôi không được xem".
- `entity_id` bỏ trống **được phép**, nhưng lọc theo tập id nằm trong phạm vi (`entity_id IN
  (SELECT id ... WHERE <phạm vi>)`) — Help Center cần lối này cho màn *Lịch sử*. Không kèm
  id mà cũng không lọc mới là lỗ hổng, còn kèm hay không kèm thì cùng một phạm vi.
- Người có khóa `setting` (`read` hoặc `write`) đọc được **mọi** entity kể cả `auth` — lọc
  theo entity không được khắt khe hơn "không lọc". Đây là màn nhật ký đăng nhập của quản trị.

Thêm: `faq` ghi dấu vết dưới tên riêng nhưng gác bằng khóa `help_article` → bảng alias
`PERMISSION_KEY_ALIAS` trong `audit/controller.py`. Hồ sơ của chính mình (`user`/`employee`
+ id mình) đọc được không cần khóa. Test: `test/backend/test_va_nhat_ky_cr313.py` (9 ca).

---

### BM-002 — Không có phiên đăng nhập phía máy chủ

**Mức: Cao. Trạng thái: MỞ.**

`backend/app/core/auth.py:26` — token chứa đúng ba trường: `sub` (id người dùng), `type`,
`exp`. Không có `jti`, không có bảng phiên nào phía máy chủ.

Hệ quả, theo thứ tự nặng dần:

- **Đăng xuất không đăng xuất.** `auth/controller.py:79` chỉ ghi một dòng nhật ký rồi trả về;
  token vẫn hợp lệ đến khi hết hạn. Người dùng bấm Đăng xuất trên máy công cộng, đóng trình
  duyệt, yên tâm — token trong bộ nhớ trình duyệt đó vẫn dùng được.
- **Token lộ là mất tới 7 ngày.** `ACCESS_EXPIRE_MIN = 60`, `REFRESH_EXPIRE_DAYS = 7`
  (`core/config.py:15`). Refresh token lọt ra ngoài thì đẻ access token mới suốt một tuần.
- **Không thu hồi được một phiên.** Biện pháp duy nhất là khóa cả tài khoản
  (`is_active = False`) — `get_current_user` đọc lại `User` mỗi lượt gọi nên khóa **có** ăn
  ngay, nhưng nó khóa luôn cả người thật. Không có cách nào cắt riêng cái máy bị mất.
- **Không trả lời được câu hỏi đơn giản nhất.** "Tài khoản này đang đăng nhập ở đâu, mấy
  máy?" — hôm nay không có câu trả lời. Chỉ có các dòng `login` rời rạc trong nhật ký, không
  nối được với thao tác nào sau đó.

**Hướng vá:** bảng `tab_login_session` + `jti` trong token — đã thiết kế ở
[`nhat-ky-va-phien-dang-nhap.md`](nhat-ky-va-phien-dang-nhap.md) §3.1 (bao-CR-312, đợt P1).
Nhưng CR đó là một công trình 6 đợt; **phần khóa phiên nên tách ra làm trước**, xem mục 3.

---

### BM-003 — Gia hạn token không để lại dấu vết

**Mức: Trung bình. Trạng thái: MỞ.**

`auth/controller.py:86` — `POST /api/auth/refresh` không gọi `audit_record`, cũng không đọc
IP. Đăng nhập có ghi IP, đăng xuất có ghi IP, còn **suốt bảy ngày ở giữa thì không có dòng
nào**. Một refresh token bị lấy cắp sẽ tự gia hạn im lặng cho tới khi hết hạn, và nhật ký chỉ
thấy đúng một lần đăng nhập hợp lệ từ đầu.

**Hướng vá:** ghi một dòng cho mỗi lượt refresh kèm IP. Rẻ, làm được ngay, không chờ CR-312 —
gộp vào bao-CR-313.

**Cập nhật 08/09/2026 — đã gõ mã trên `main`, chưa commit.** Mỗi lượt gia hạn là một dòng
`auth`: `refresh` (thành công, `created_by` = người dùng) hoặc `refresh_failed` (token hỏng →
`created_by = 0`; tài khoản bị khóa → `created_by` = id đó), đều kèm IP thật. Nhãn `Gia hạn
phiên` / `Gia hạn phiên thất bại` thêm vào `ACTION_LABEL`. Ước lượng thêm ~8 dòng/người/ngày
trên prod — chấp nhận được cho tới khi `tab_login_session` (CR-312 P1) thay thế.
Test: `test/backend/test_client_ip_cr313.py` (3 ca refresh).

---

### BM-004 — Giới hạn tần suất đăng nhập dùng chung một xô

**Mức: Trung bình. Trạng thái: MỞ.**

`core/limiter.py:5` khai `Limiter(key_func=get_remote_address)`. `get_remote_address` đọc
`request.client.host` — tức **IP của kết nối TCP**, không phải của người dùng.

Trên hệ thật, uvicorn chạy `--host 0.0.0.0 --port 8000 --workers 2`, **không có
`--proxy-headers`** (`backend/start.prod.sh:50`), và đứng sau nginx trong cùng mạng Docker. Nên
mọi lượt gọi đều mang cùng một IP container. Bằng chứng nằm ngay trong log của api:

```
INFO:  172.20.0.6:55018 - "GET /api/notifications?page=1&page_size=8 HTTP/1.1" 200 OK
```

`172.20.0.6` là nginx, không phải người dùng. Nghĩa là `LOGIN_RATE_LIMIT=10/minute` là
**10 lượt/phút cho toàn công ty gộp lại**, và hai chuyện xảy ra cùng lúc:

- **Chống dò mật khẩu yếu hơn tưởng.** Kẻ dò chỉ tiêu chung xô với người thật, nhưng 10 lượt
  mỗi phút liên tục vẫn là **14.400 lượt/ngày** — thừa cho một danh sách mật khẩu phổ biến.
- **Người thật bị chặn.** Sáng thứ Hai, người thứ 11 đăng nhập trong cùng một phút ăn HTTP 429
  dù gõ đúng mật khẩu. Đây không phải giả thuyết mà là hệ quả số học của cấu hình hiện tại.

Một chi tiết **may**: `default_limits=["300/minute"]` khai trong cùng tệp đang **vô hiệu**, vì
`SlowAPIMiddleware` chưa được gắn vào `app` (`main.py` chỉ gắn handler lỗi). Nếu nó có hiệu
lực thì cả hệ thống đã trần 300 lượt gọi mỗi phút — một màn danh sách mở ra là hết. Đừng "sửa"
bằng cách gắn middleware vào mà chưa xử lý chuyện IP.

**Hướng vá:** chạy uvicorn với `--proxy-headers --forwarded-allow-ips=<dải nginx>` để
`request.client.host` thành IP thật, hoặc đổi `key_func` sang hàm đọc `X-Forwarded-For` giống
`_client_ip` sẵn có ở `auth/controller.py:22`. Chọn hướng nào cũng phải xác nhận nginx thật sự
đặt header đó và **không cho client tự đặt** — nếu không thì đổi xong ai cũng tự khai IP giả để
thoát giới hạn, tệ hơn hiện tại.

**Cập nhật 08/09/2026 — đã gõ mã trên `main`, chưa commit.** Đã soi cấu hình thật trên VPS:
nginx (`docker/nginx.prod.conf`) đặt `X-Real-IP = $remote_addr` và `X-Forwarded-For =
$proxy_add_x_forwarded_for` — tức **NỐI THÊM** vào giá trị client gửi, nên phần tử ĐẦU của
XFF là thứ client tự đặt được (và `_client_ip` cũ của đăng nhập lấy đúng phần tử đó → dòng
`login_failed` từng ghi IP giả được). Cloudflared chạy dạng container `cloudflare_tunnel`,
không mở cổng công khai, nên mọi lượt vào đều qua Cloudflare và `CF-Connecting-IP` là header
duy nhất client không đặt được. Chọn **không** bật `--proxy-headers` (nó cũng tin XFF), mà
viết `core/client_ip.py::get_client_ip` dùng chung cho limiter lẫn nhật ký đăng nhập, thứ
tự tin cậy: `CF-Connecting-IP` → phần tử **CUỐI** của XFF (do nginx nối, không giả được) →
`request.client.host`. Dấu hiệu hỏng nhìn thấy được: nếu sau deploy nhật ký đăng nhập hiện
IP `172.x` thì `CF-Connecting-IP` không tới api. **Việc còn lại sau deploy dev:** curl từ
VPS với `X-Forwarded-For: 9.9.9.9` + mật khẩu sai, dòng `login_failed` phải ghi IP công
khai của VPS, không phải `9.9.9.9` hay `172.x`. Test: `test_client_ip_cr313.py` (5 ca IP).

---

### BM-005 — Nhật ký không lưu giá trị trước / sau

**Mức: Trung bình. Trạng thái: đang vá (bao-CR-312, mới ở mức đề xuất).**

`tab_audit_log` có đúng bốn cột nghiệp vụ: `entity`, `entity_id`, `action`, `message`. `message`
là văn xuôi do người viết mã tự đặt. Không có chỗ nào lưu **giá trị cũ** và **giá trị mới**,
nên câu "dòng này trước đó ghi gì" không trả lời được — kể cả khi có dòng nhật ký.

Đây là gốc rễ khiến ticket 07/09 phải mở database. Thiết kế vá: `tab_change_log` sinh tự động
bằng sự kiện SQLAlchemy — [`nhat-ky-va-phien-dang-nhap.md`](nhat-ky-va-phien-dang-nhap.md) §3.2.

---

### BM-006 — Dấu vết là tùy chọn theo từng lời gọi

**Mức: Thấp. Trạng thái: vá một phần (bao-CR-311).**

Ghi nhật ký hôm nay là **213 lời gọi `record(db, ...)` rải trong 54 tệp**. Không có gì bắt buộc
chúng phải có mặt: viết một endpoint mới mà quên gọi thì thao tác đó lặng lẽ không để lại dấu.
Đúng chuyện đã xảy ra với ba thao tác phương án của Yêu cầu báo giá — chạy từ ngày đầu, không
ai để ý, tới khi cần truy thì không có gì để đọc.

bao-CR-311 (07/09/2026) vá **bốn** chỗ. Còn lại thì vẫn theo cơ chế cũ. Vá tận gốc là chuyển
việc ghi xuống tầng ORM để không phụ thuộc trí nhớ người viết mã — bao-CR-312.

---

### BM-007 — Dòng nhật ký không có IP / trình duyệt / mã lượt gọi

**Mức: Thấp. Trạng thái: đang vá (bao-CR-312, mới ở mức đề xuất).**

IP hiện chỉ được ghi ở đúng ba chỗ (`login`, `login_failed`, `logout`) và ghi **lẫn trong câu
văn** `message`, nên lọc theo IP là đi so chuỗi. Mọi dòng nhật ký khác không có IP, không có
trình duyệt, không có mã lượt gọi để gom các thay đổi của cùng một lần bấm nút.

Vá: ba cột `session_id` / `request_id` / `ip` trên `tab_audit_log` —
[`nhat-ky-va-phien-dang-nhap.md`](nhat-ky-va-phien-dang-nhap.md) §3.3. **Dòng cũ để NULL, không
đắp lại được.**

---

## 3. Việc phải làm, theo thứ tự

Thứ tự dưới đây xếp theo *"đang hở trên hệ thật"* trước, *"làm nền cho về sau"* sau. Nó **khác**
thứ tự trong `nhat-ky-va-phien-dang-nhap.md` — tệp đó xếp theo thứ tự kỹ thuật.

### Việc 1 — bao-CR-313: vá BM-001 + BM-003 + BM-004

Ba lỗi nhỏ, cùng một vùng mã, làm chung một đợt. Đây là **việc gấp**: BM-001 đang mở trên hệ
thật và không cần kỹ năng gì để khai thác — chỉ cần một tài khoản hợp lệ và thanh địa chỉ.

| Việc | Tệp |
|---|---|
| Gác `/api/audit-logs` bằng khóa `read` của chính entity được hỏi; entity ngoài `ENTITIES` thì 400 | `modules/audit/controller.py` |
| `auth` và các entity không phải chứng từ: chỉ vai trò quản trị | nt |
| Cấm bỏ trống `entity_id` trừ khi có khóa cấp cao | nt |
| Chạy `apply_scope` trên bản ghi được hỏi | nt |
| Ghi dấu vết + IP cho `/api/auth/refresh` | `modules/auth/controller.py` |
| Sửa `key_func` của limiter đọc đúng IP người dùng (hoặc bật `--proxy-headers`) | `core/limiter.py` / `start.prod.sh` |

**Hai chỗ dễ vỡ, phải kiểm trước khi giao:**

1. Màn nào đang gọi `/api/audit-logs` mà **người dùng thường không có khóa `read`** của entity
   đó? Siết xong là họ thấy dòng thời gian trống, không phải lỗi 403 — im lặng, khó phát hiện.
   Phải rà cả `frontend/` lẫn `frontend-v2/` (`AuditTimeline` của lớp CRUD dùng chung).
2. Sửa limiter mà nginx không đặt `X-Forwarded-For`, hoặc đặt nhưng cho client ghi đè, thì
   **thành ra tệ hơn hiện tại**: ai cũng tự khai IP giả để vượt giới hạn. Xác nhận cấu hình
   nginx trước khi đổi mã.

**Cần bao nhiêu test:** một tệp test cho phân quyền của `/api/audit-logs` (tài khoản không có
khóa gọi vào phải 403, entity lạ phải 400, bỏ trống `entity_id` khi không đủ quyền phải bị
chặn). Đây là chỗ vừa hở, để test canh.

### Việc 2 — tách khóa phiên ra khỏi bao-CR-312, làm trước

BM-002 nặng, mà bao-CR-312 là công trình 6 đợt. Phần trả lời được BM-002 chỉ là một mẩu của
đợt P1: bảng `tab_login_session`, `jti` trong token, `get_current_user` kiểm phiên còn sống,
`logout` đóng phiên. **Không cần** `tab_change_log`, không cần bắt sự kiện ORM, không cần màn
hình quản lý phiên.

Làm mẩu đó trước thì đăng xuất có hiệu lực thật và thu hồi được token — hai thứ đáng giá ngay.
Phần còn lại của CR-312 vẫn theo lịch cũ.

Đánh đổi phải biết: thêm **một truy vấn cho mỗi lượt gọi API**. Giảm bằng bộ nhớ đệm 60 giây
trong tiến trình, đúng kiểu `_PERM_CACHE` đang dùng cho hồ sơ quyền.

### Việc 3 — bao-CR-312 đầy đủ

Giữ nguyên như đã thiết kế: BM-005 và BM-007. Vẫn đang chờ chốt 6 câu hỏi ở §6 của
[`nhat-ky-va-phien-dang-nhap.md`](nhat-ky-va-phien-dang-nhap.md).

### Việc 4 — đưa việc soát vào nếp

Sổ này chỉ có giá trị nếu được mở ra. Ba việc nhỏ:

- Thêm một dòng vào `doc/tai-lieu-ky-thuat/quy-trinh-tai-lieu.md`: thấy lỗ hổng thì ghi vào
  đây trước, rồi mới cấp CR vá.
- Endpoint mới **đụng dữ liệu của nhiều người** thì phải trả lời được câu "ai gọi được cái
  này" trước khi giao. BM-001 tồn tại vì câu đó chưa từng được hỏi cho phân hệ nhật ký.
- Rà lại sổ mỗi khi mở một phân hệ mới ra ngoài (diễn đàn, trung tâm hướng dẫn, trợ lý AI) —
  phân hệ mới thường mở rộng số người có "một tài khoản hợp lệ", mà đó chính là điều kiện duy
  nhất mà BM-001 đòi hỏi.

---

## 4. Sổ này KHÔNG làm gì

- **Không phải bản đánh giá an toàn đầy đủ.** Bảy dòng ở đây là những gì lòi ra khi soát quanh
  MỘT ticket, không phải kết quả của một đợt rà có phương pháp. Chưa ai soi tải tệp lên, chưa
  soi khâu nhập/xuất dữ liệu, chưa soi phần tích hợp ngoài, chưa soi lớp mạng và cấu hình VPS.
  **Không có dòng nào ở đây không có nghĩa là chỗ đó sạch** — nghĩa là chưa ai nhìn.
- **Không thay tài liệu thiết kế.** Cách vá nằm ở tệp của từng CR.
- **Không dựng lại được quá khứ.** Mọi thứ trong sổ này chỉ vá được từ lúc vá trở đi.
