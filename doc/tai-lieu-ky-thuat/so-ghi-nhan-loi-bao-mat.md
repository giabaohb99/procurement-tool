# SỔ GHI NHẬN LỖI BẢO MẬT

**Bản 1.0 — 07/09/2026.** Mở sổ nhân ticket YCBG05092603.
**Bản 1.1 — 09/09/2026.** bao-CR-313 đã deploy prod + dev: **BM-001 đóng**, **BM-004 đóng**,
BM-003 vá một phần (còn phiên phía máy chủ ở P3). Bốn dòng còn lại chưa đổi.
**Bản 1.2 — 10/09/2026.** Soát lại chính lớp nhật ký trước khi đẩy bao-CR-346 lên: thêm
**bảy dòng BM-008 … BM-014**, trong đó bốn dòng bao-CR-346 vá luôn và ba dòng còn mở.
Sửa hai chỗ hết hạn trong sổ: QĐ-A (bỏ dòng `refresh` thành công) **đã bị đảo**, và
BM-005 / BM-007 nay đã có mã chạy thật chứ không còn "mới ở mức đề xuất".
**Bản 1.3 — 10/09/2026 (chiều).** bao-CR-312 P1 + P1b **đã deploy PROD** (`main` `e21023d1`):
**BM-008 … BM-011 đóng nốt phía prod**, nợ kỹ thuật N-010 trả xong. BM-002 vẫn mở trên prod
vì P3a chưa lên `main`.

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
| BM-001 | **Cao** | `/api/audit-logs` chỉ gác bằng đăng nhập — mọi tài khoản đọc được nhật ký của mọi phân hệ | **Đã vá (09/09/2026, `main` f023c747 + 2de0b2d4 — đã deploy prod; `erp-v2` 682010c3 — đã deploy dev).** Đo lại trên prod: 230/233 tài khoản đang hoạt động ăn 403 ở `entity=auth` và ở lối duyệt toàn hệ, 3 tài khoản quản trị qua được |
| BM-002 | **Cao** | Không có phiên đăng nhập phía máy chủ — token lộ thì không thu hồi được | **Mở** — chờ P3 của bao-CR-312 |
| BM-003 | Trung bình | Gia hạn token không để lại dấu vết nào | **Vá một phần (09/09/2026, `main` f023c747 — đã deploy prod; `erp-v2` abff1298 — đã deploy dev).** `/api/auth/refresh` nay ghi `refresh` / `refresh_failed` kèm IP. Còn phần phiên phía máy chủ ở P3. ~~P3 sẽ bỏ chính dòng `refresh` thành công này theo QĐ-A~~ — **QĐ-A đã bị đảo 10/09/2026**, dòng `refresh` thành công GIỮ LẠI, xem BM-009 |
| BM-004 | Trung bình | Giới hạn tần suất đăng nhập dùng chung MỘT xô cho cả công ty | **Đã vá (09/09/2026, `main` f023c747 — đã deploy prod; `erp-v2` abff1298 — đã deploy dev).** Đã kiểm trên hệ thật: dấu vết đăng nhập mang IP công cộng thật (118.71.139.127, 27.64.133.181), không phải `172.x` → `CF-Connecting-IP` tới được api. Kiểm trên dev với header giả `X-Forwarded-For: 6.6.6.6` + `X-Real-IP: 7.7.7.7`: dòng ghi vẫn là IP thật (180.93.2.176), header giả bị bỏ qua |
| BM-005 | Trung bình | Nhật ký không lưu giá trị trước / sau — không chứng minh được đã đổi gì | **Mở** — `tab_change_log` nằm ở P4 của bao-CR-312, chưa viết dòng mã nào |
| BM-006 | Thấp | Dấu vết là tùy chọn theo từng lời gọi — quên gọi là mất | Vá một phần (bao-CR-311 + bao-CR-346) — xem BM-010 |
| BM-007 | Thấp | Dòng nhật ký không có IP / trình duyệt / mã lượt gọi | **Vá phần lớn (P1 của bao-CR-312, `erp-v2` 2eba1274 — mới deploy dev).** `tab_request_log` ghi IP + `request_id` + tuyến gọi; `tab_audit_log` có `request_id` / `ip` / `actor_kind`. Còn dấu thiết bị ở bao-CR-346 |
| BM-008 | Trung bình | Giá trị dữ liệu thật bị chép nguyên vào `error_detail` của dòng nhật ký khi câu SQL nổ | **Đã vá + ĐÃ ĐÓNG CẢ HAI PHÍA (bao-CR-346, 10/09/2026) — `erp-v2` 337fa9bb deploy dev; `main` e21023d1 deploy prod chiều 10/09** — `mask_error_detail`, xem chi tiết bên dưới |
| BM-009 | Trung bình | Thao tác **ĐỌC** không để lại dấu vết nào — kể cả tải tệp đính kèm và cả lượt bị chặn 403 | **Đã vá + ĐÃ ĐÓNG CẢ HAI PHÍA (bao-CR-346, 10/09/2026) — `erp-v2` 337fa9bb deploy dev; `main` e21023d1 deploy prod chiều 10/09** — ghi hết mọi GET |
| BM-010 | Trung bình | Đổi phân quyền và đổi tài khoản **không gọi `record()`** — vùng nhạy cảm nhất lại là vùng trắng | **Đã vá + ĐÃ ĐÓNG CẢ HAI PHÍA (bao-CR-346, 10/09/2026) — `erp-v2` 337fa9bb deploy dev; `main` e21023d1 deploy prod chiều 10/09** |
| BM-011 | Trung bình | Nhật ký chỉ có MỘT bản, nằm trên đúng cái máy kẻ tấn công đang đứng | **Đã vá + ĐÃ ĐÓNG CẢ HAI PHÍA (bao-CR-346, 10/09/2026) — `erp-v2` 337fa9bb deploy dev; `main` e21023d1 deploy prod chiều 10/09** — đóng gói ra R2 hàng tháng |
| BM-012 | Thấp | Token hết hạn thì dòng nhật ký ghi `user_id = 0` — không phân biệt được "khách vãng lai" với "người có tài khoản, token vừa hết hạn" | **Mở** |
| BM-013 | Thấp | `record()` tự `commit()` — giao dịch nghiệp vụ bị rollback vẫn để lại dấu vết ma | **Mở** |
| BM-014 | Trung bình | `CF-Connecting-IP` được tin **vô điều kiện** — ai gọi thẳng vào api là tự khai IP của mình | **Mở** |

✅ **Bốn dòng BM-008…BM-011 nay đã đóng trên CẢ HAI phía** (cập nhật chiều 10/09/2026).
Chúng vá lớp nhật ký của bao-CR-312 P1, và P1 vốn chưa từng lên prod — đó là lý do sổ này
từng ghi *"prod CHƯA"*. Nợ kỹ thuật **N-010 đã trả**: `main` `2daf6ffb` (P1) + `e21023d1`
(P1b) đã deploy prod, migration chạy tới head `94f0a2c4e43c`, `tab_request_log` có thật trên
hệ thật.

Cách trả nợ: **cherry-pick, không merge** (`quy-trinh-nhanh-va-deploy.md` §A.4), và migration
`f4d37c7600d0` giữ **nguyên mã revision**, chỉ đổi `down_revision` sang head của `main`
(`d2f45a8c9e10`) — giữ nguyên mã để hai nhánh không đẻ ra hai bảng `tab_request_log` khác id.
Đánh đổi đã biết: tệp migration đó nay khác nhau ở hai nhánh, nên lần merge `main` → `erp-v2`
tới sẽ đụng độ đúng ở dòng `down_revision` — **giữ bản của `erp-v2` (`d7f2a9c4e1b8`)**.

⚠️ Vẫn còn hở trên prod: **P2 và P3a** (`bao-CR-358` + `bao-CR-360`) chưa lên `main`, nên
`tab_login_session` và bộ mã hành động chưa có trên hệ thật. Riêng **BM-002 (đăng xuất không
có hiệu lực)** vì vậy **vẫn mở trên prod**, dù đã có mã chạy trên `erp-v2`.

---

### BM-001 — Nhật ký của cả hệ đọc được bằng bất kỳ tài khoản nào

**Mức: Cao. Trạng thái: ĐÃ VÁ 09/09/2026** — `main` `f023c747` + `2de0b2d4` (deploy prod),
`erp-v2` `682010c3` (deploy dev). Phần mô tả dưới đây giữ nguyên ở thì hiện tại của lúc phát
hiện; kết quả đo sau khi vá ghi ở cuối mục.

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

**Đã vá thế nào (09/09/2026).** Hàm `_guard` trong `audit/controller.py` cắt route làm hai chế
độ, đúng hai chế độ giao diện đang dùng: **widget lịch sử** (luôn kèm `entity`) đòi khóa `read`
của chính entity đó rồi soi phạm vi của chính bản ghi đó; **màn Nhật ký hệ thống** (không kèm
`entity`) đòi khóa quản trị `setting` (`read` HOẶC `write`). Ba chỗ lệch so với hướng vá ban
đầu, đều là chỗ vá thô sẽ hỏng việc thật:

- entity lạ trả **403 chứ không 400** — 400 nói với người gọi rằng entity đó không tồn tại,
  tức là biến endpoint thành máy dò danh sách entity;
- **không cấm bỏ trống `entity_id`** mà lọc theo đúng tập id nằm trong phạm vi
  (`AuditLog.entity_id.in_(...)`) — cấm là giết lối lọc theo loại chứng từ của quản trị. Đo
  ngày 05/09/2026: tài khoản `TESTREQ` (phạm vi `own`) thấy 0 phiếu mua hàng trong danh sách,
  mở thẳng một phiếu thì 403, mà vẫn đọc được nhật ký của **25** phiếu — chính là chỗ này;
- **hai ngoại lệ hẹp**: hồ sơ của chính mình (`/me` dựng `AuditTimeline entity="user"` cho mọi
  người, mà `user.read` là khóa quản trị tài khoản) và bí danh `faq` → `help_article`.

Đo lại trên prod sau khi deploy: gọi `_guard` với **cả 233 tài khoản đang hoạt động** — 230 ăn
403 ở `entity=auth` và ở lối duyệt toàn hệ, 3 tài khoản quản trị qua được. Vế đối chứng cũng
đo: sáu Yêu cầu báo giá gần nhất vẫn trả 1–17 dòng lịch sử cho chính người tạo, tức là dòng
thời gian của người dùng thường không chết.

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

**Mức: Trung bình. Trạng thái: VÁ MỘT PHẦN 09/09/2026** — `main` `f023c747` (deploy prod),
`erp-v2` `abff1298` (deploy dev). Phần còn lại (phiên phía máy chủ) nằm ở P3 của bao-CR-312.

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
trên prod — chấp nhận được cho tới khi `tab_login_session` (CR-312 **P3**, không phải P1) thay thế.
Test: `test/backend/test_client_ip_cr313.py` (3 ca refresh).

**Cập nhật 09/09/2026 — đo thật, và hình vá cuối cùng đã chốt.** Đếm log nginx prod 24 giờ:
**126 lượt `POST /api/auth/refresh` mỗi ngày**, chiếm **48%** tổng số lượt gọi không phải GET
(265). Nghĩa là cách vá tạm ở trên **cộng thêm ~126 dòng audit/ngày, gấp đôi lượng audit hiện
tại (124 dòng/ngày)** — giữ lâu thì nhật ký loãng đúng kiểu BM-005 đang than. Bản 2.4 của
`nhat-ky-va-phien-dang-nhap.md` chốt **QĐ-A** làm hình vá cuối: gia hạn **thành công** chỉ dập
`refreshed_at` / `refresh_count` / `last_seen_ip` trên `tab_login_session`, **không** đẻ dòng
nhật ký; chỉ ghi khi **IP khác lần trước** (`refresh_ip_changed`) hoặc **gia hạn thất bại**.
BM-003 vẫn đóng, vì thứ chứng minh token bị cắp là **phiên đổi IP giữa chừng**, không phải sự
tồn tại của 126 dòng giống hệt nhau mỗi ngày. **Cách vá tạm của CR-313 giữ nguyên** cho tới khi
P3 dựng xong bảng phiên — lúc đó phải quay lại `auth/controller.py` bỏ dòng `record(...)` ở
nhánh thành công.

**Deploy 09/09/2026 — đo trên hệ thật.** Sau khi deploy prod, hai dòng `refresh` đầu tiên rơi
vào bảng trong vòng vài phút, mang IP công cộng thật (118.71.139.127 và 27.64.133.181) chứ
không phải `172.x` — tức `CF-Connecting-IP` tới được api, đúng dấu hiệu đã đặt ra ở BM-004.

---

### BM-004 — Giới hạn tần suất đăng nhập dùng chung một xô

**Mức: Trung bình. Trạng thái: ĐÃ VÁ 09/09/2026** — `main` `f023c747` (deploy prod),
`erp-v2` `abff1298` (deploy dev).

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
IP `172.x` thì `CF-Connecting-IP` không tới api. Test: `test_client_ip_cr313.py` (5 ca IP).

**Cập nhật 09/09/2026 — đã deploy và đã kiểm bằng header giả.** Trên dev, curl từ VPS với
`X-Forwarded-For: 6.6.6.6` + `X-Real-IP: 7.7.7.7` và mật khẩu sai: dòng `login_failed` ghi
`IP 180.93.2.176` — IP công khai thật của VPS đi vòng qua Cloudflare — chứ không phải hai giá
trị giả, cũng không phải `172.x`. Trên prod, dấu vết đăng nhập/gia hạn mang IP công cộng của
người dùng thật (118.71.139.127, 27.64.133.181). Cả hai vế của hướng vá đều đứng: đọc được IP
thật, và client không tự khai IP được. `default_limits` vẫn để nguyên trạng thái vô hiệu —
`SlowAPIMiddleware` **không** được gắn thêm, đúng cảnh báo ở đoạn trên.

---

### BM-005 — Nhật ký không lưu giá trị trước / sau

**Mức: Trung bình. Trạng thái: mở — nằm ở P4 của bao-CR-312, chưa viết dòng mã nào.**

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

**Mức: Thấp. Trạng thái: vá phần lớn (P1 của bao-CR-312, `erp-v2` 2eba1274 — mới deploy dev).**

Mô tả dưới đây là hiện trạng LÚC MỞ DÒNG (07/09/2026). P1 đã dựng `tab_request_log` (một dòng
một lượt gọi API, có IP + `request_id` + tuyến gọi) và thêm `request_id` / `ip` / `session_id` /
`actor_kind` vào `tab_audit_log`. Phần trình duyệt / thiết bị nằm ở bao-CR-346 (`device_hash`).

IP hiện chỉ được ghi ở đúng ba chỗ (`login`, `login_failed`, `logout`) và ghi **lẫn trong câu
văn** `message`, nên lọc theo IP là đi so chuỗi. Mọi dòng nhật ký khác không có IP, không có
trình duyệt, không có mã lượt gọi để gom các thay đổi của cùng một lần bấm nút.

Vá: ba cột `session_id` / `request_id` / `ip` trên `tab_audit_log` —
[`nhat-ky-va-phien-dang-nhap.md`](nhat-ky-va-phien-dang-nhap.md) §3.3. **Dòng cũ để NULL, không
đắp lại được.**

---

### BM-008 — Giá trị dữ liệu thật bị chép nguyên vào `error_detail`

**Mức: Trung bình. Trạng thái: ĐÃ ĐÓNG CẢ HAI PHÍA (bao-CR-346, 10/09/2026) — `erp-v2` 337fa9bb deploy dev; `main` `e21023d1` deploy prod cùng chiều hôm đó.**

Bảy dòng BM-001…BM-007 đều hỏi *"nhật ký có ghi đủ không"*. Bảy dòng tiếp theo, mở ngày
10/09/2026, hỏi câu ngược lại — **chính lớp nhật ký có tự nó là một chỗ hở không** — và câu
trả lời đầu tiên là có.

Middleware bắt ngoại lệ rồi lưu `str(exc)` vào cột `error_detail`. Với `IntegrityError` của
SQLAlchemy, `str(exc)` **có sẵn khối `[parameters: ...]`** — tức toàn bộ giá trị của câu
`INSERT`/`UPDATE` vừa nổ, nguyên văn. Một lần lưu hồ sơ nhân sự đụng ràng buộc trùng là số
CCCD, số tài khoản ngân hàng, ngày sinh nằm thẳng trong bảng nhật ký, ở dạng chữ, **không đi
qua lớp che trường nhạy cảm nào** — `modules/employee/sensitive.py` gác cửa serializer, mà
đường này không đi qua serializer.

Nặng thêm vì bảng nhật ký sinh ra để cho **nhiều người đọc hơn** dữ liệu gốc: người đi tra sự
cố không nhất thiết có `employee_sensitive.read`.

Vá: `mask_error_detail` ở `core/logging_policy.py` §4 — cắt từ mốc `[parameters:` /
`[cached since` tới mốc nối lại gần nhất, thay bằng `[đã che]`. **Cố ý vẫn để lại chữ
`[parameters:`** để người đọc vết lỗi biết chỗ đó bị che chứ không tưởng là câu lỗi cụt.

⚠️ Bản vá đầu **treo vô hạn**: chuỗi thay vào chứa chính mốc đang tìm, nên `find` từ đầu gặp
lại nó ở đúng vị trí cũ. Nó treo **trong middleware**, tức treo cả lượt gọi API rồi rút cạn
pool kết nối — một lỗi 500 bình thường biến thành hệ thống đứng. Chốt bằng con trỏ `cursor`,
và bằng test `test_che_vet_loi_khong_treo_khi_khong_co_moc_ket`.

---

### BM-009 — Thao tác ĐỌC không để lại dấu vết nào

**Mức: Trung bình. Trạng thái: ĐÃ ĐÓNG CẢ HAI PHÍA (bao-CR-346, 10/09/2026) — `erp-v2` 337fa9bb deploy dev; `main` `e21023d1` deploy prod cùng chiều hôm đó.**

Bản P1 cố ý bỏ GET để tiết kiệm dung lượng (QĐ-A). Hệ quả: **rò rỉ dữ liệu là loại sự cố duy
nhất mà nhật ký không nói được gì cả.** Một tài khoản ngồi đọc lần lượt 3.000 hồ sơ nhân sự,
hoặc tải về toàn bộ tệp đính kèm của một chuỗi chứng từ, để lại đúng **không dòng nào**. Ba
biểu hiện cụ thể:

- `/api/attachments/{id}/view` có `record()` gọi tay, nhưng `/download`, `/preview` và
  `/chain/zip` thì không — mà `/download` mới là đường lấy tệp về;
- lượt bị chặn **403 cũng không ghi**, nên "ai đó đang dò quanh những cửa họ không có quyền"
  là tín hiệu tấn công rõ nhất mà hệ thống lại mù hoàn toàn;
- luật lọc cũ so `"/export"` bằng `in`, nên vô tình khớp cả `/api/exports`.

Đại ca chốt **ghi hết mọi GET** (10/09/2026), chỉ trừ hai đường thăm dò `/api/notifications` +
`/api/alerts` (59,5% tổng GET, không mang thông tin gì) và chính các đường đọc nhật ký (NT-5 —
lớp nhật ký không ghi lại chính nó). **QĐ-A bị đảo cùng lúc**: dòng `refresh` thành công giữ
lại, vì đó đúng là chỗ token bị cắp lộ ra (BM-003).

Ba cái giá phải trả và cách trả: dung lượng → dọn dòng GET quá **90 ngày** (§4.1.1 của
[`nhat-ky-va-phien-dang-nhap.md`](nhat-ky-va-phien-dang-nhap.md)); nhật ký loãng → GET
**không chép thân trả về**, chỉ giữ mã trạng thái + tuyến gọi; ghi chậm → GET bỏ hẳn nhịp
`await request.body()`.

---

### BM-010 — Đổi phân quyền và đổi tài khoản không gọi `record()`

**Mức: Trung bình. Trạng thái: ĐÃ ĐÓNG CẢ HAI PHÍA (bao-CR-346, 10/09/2026) — `erp-v2` 337fa9bb deploy dev; `main` `e21023d1` deploy prod cùng chiều hôm đó.**

Đây là ca cụ thể của BM-006, nhưng rơi đúng vào vùng tệ nhất: `modules/role/` và
`modules/user/` **không có một lời gọi `record()` nào**. Tự nâng quyền cho mình, gán thêm vai
trò, mở rộng phạm vi dữ liệu, đổi mật khẩu người khác — không thao tác nào để lại dấu.

Vá: thêm `record(...)` vào các đường ghi của hai module, và **`describe_permission_change` kể
lại phần CHÊNH của ma trận quyền** thay vì chỉ ghi "đã cập nhật phân quyền" — bấm Lưu mà
không đổi gì thì câu kể rỗng, không sinh dòng rác. Đi kèm là hai lỗi nhóm hành động:
`ACTION_GROUP_PERMISSION` trước đó **không dòng nào rơi vào**, và mã đóng phiếu rơi nhầm vào
`không rõ`.

---

### BM-011 — Nhật ký chỉ có một bản, trên chính máy bị tấn công

**Mức: Trung bình. Trạng thái: ĐÃ ĐÓNG CẢ HAI PHÍA (bao-CR-346, 10/09/2026) — `erp-v2` 337fa9bb deploy dev; `main` `e21023d1` deploy prod cùng chiều hôm đó.**

Toàn bộ bốn bảng nhật ký nằm trong MySQL trên VPS, và **bị loại khỏi bản sao lưu đêm** (QĐ-C,
cố ý — nếu không thì bản sao phình gấp mấy lần phần dữ liệu nghiệp vụ). Ai vào được máy đó thì
xóa dấu vết của mình bằng một câu `DELETE`, và không có bản nào ở nơi khác để đối chiếu.

Vá: kéo phần **đóng gói ra R2** từ P6 lên làm sớm — mỗi tháng gói các dòng cũ thành tệp đẩy
lên kho ngoài. Việc dọn 90 ngày của BM-009 cũng đi qua đó.

⚠️ Vá xong lại suýt mở một lỗ to hơn: `upload_fileobj` **tự lùi về ghi vào `uploads/` khi
chưa cấu hình R2**, mà `main.py:130` mount thư mục đó ở `/api/uploads` bằng `StaticFiles`
**không gác quyền**. Tức một môi trường quên cấu hình R2 sẽ **xuất bản cả kho nhật ký ra URL
công khai đoán được**. Chốt: cả việc đóng gói lẫn việc dọn đều **từ chối chạy** khi R2 chưa
sẵn sàng (`is_remote_storage_ready`) — thà không có bản sao còn hơn có bản sao ai cũng tải về
được. Test canh: `test_khong_co_ban_sao_ngoai_may_thi_khong_xoa_gi`.

---

### BM-012 — Token hết hạn ghi thành `user_id = 0`

**Mức: Thấp. Trạng thái: mở.**

`_peek_user_id` (`core/request_middleware.py:57`) giải mã token **không tra DB**; token hỏng,
hết hạn, hay sai chữ ký đều trả về `0`. Nên trong `tab_request_log`, "người lạ chưa đăng nhập"
và "người có tài khoản, token vừa hết hạn" là **cùng một giá trị**.

Chưa vá vì cửa quyền thật nằm ở `get_current_user`, đây chỉ là chỗ ghi. Cách vá khi làm P3:
đọc `sub` **kể cả khi token hết hạn** (`options={"verify_exp": False}`) rồi ghi kèm một cờ
`token_expired`, chứ đừng gộp vào `0`.

---

### BM-013 — `record()` tự commit, để lại dấu vết ma

**Mức: Thấp. Trạng thái: mở.**

`core/audit.py` kết bằng `db.commit()`. Nếu thao tác nghiệp vụ nổ **sau** lời gọi `record(...)`
và giao dịch bị rollback, dòng dấu vết vẫn nằm lại — nhật ký khẳng định một việc chưa từng xảy
ra. Ngược chiều với mọi dòng khác trong sổ này: ở đây nhật ký **thừa**, không thiếu.

Cố ý chưa vá ở P1: đổi nhịp commit là đổi hành vi của **213 lời gọi đang chạy thật** mà chưa
có gì bù lại. Vá cùng P4, khi việc ghi chuyển xuống tầng ORM và gom một lần cuối request.

---

### BM-014 — `CF-Connecting-IP` được tin vô điều kiện

**Mức: Trung bình. Trạng thái: mở.**

`get_client_ip` (`core/client_ip.py:31`) lấy `CF-Connecting-IP` đầu tiên, không kiểm tra người
gọi có thật là Cloudflare không. Cả sự an toàn của nó dựa vào một giả định **nằm ngoài mã
nguồn**: "mọi lượt vào đều phải qua Cloudflare vì tunnel không mở cổng công khai".

Giả định đó đúng hôm nay. Ngày nào nó sai — ai đó vào được mạng nội bộ Docker, hoặc một lần
deploy publish cổng 8000 ra ngoài — thì kẻ gọi **tự khai IP của mình**, và cả nhật ký lẫn
xô giới hạn tần suất đăng nhập (`core/limiter.py` khóa theo đúng hàm này) đều nghe theo. Nghĩa
là BM-004 mở lại kèm theo, ở dạng khó thấy hơn.

Vá: chỉ tin `CF-Connecting-IP` khi peer TCP nằm trong dải IP Cloudflare, hoặc khi có một
header bí mật do cloudflared đặt. Chưa làm vì cần đụng cấu hình hạ tầng, không chỉ mã nguồn.

---

## 3. Việc phải làm, theo thứ tự

Thứ tự dưới đây xếp theo *"đang hở trên hệ thật"* trước, *"làm nền cho về sau"* sau. Nó **khác**
thứ tự trong `nhat-ky-va-phien-dang-nhap.md` — tệp đó xếp theo thứ tự kỹ thuật.

### Việc 1 — bao-CR-313: vá BM-001 + BM-003 + BM-004 — **XONG 09/09/2026**

Ba lỗi nhỏ, cùng một vùng mã, làm chung một đợt. Đây là **việc gấp**: BM-001 đang mở trên hệ
thật và không cần kỹ năng gì để khai thác — chỉ cần một tài khoản hợp lệ và thanh địa chỉ.

Đã deploy prod (`main` `f023c747` + `2de0b2d4`) và dev (`erp-v2` `682010c3`), không kèm
migration nào — `alembic current` của prod vẫn là `c9d3e7a1f5b6 (head)`.

| Việc | Tệp | Kết quả |
|---|---|---|
| Gác `/api/audit-logs` bằng khóa `read` của chính entity được hỏi; entity ngoài `ENTITIES` thì 403 | `modules/audit/controller.py` | Xong (403 chứ không 400 — xem BM-001) |
| `auth` và các entity không phải chứng từ: chỉ vai trò quản trị | nt | Xong (khóa `setting`, nhận `read` HOẶC `write`) |
| Cấm bỏ trống `entity_id` trừ khi có khóa cấp cao | nt | **Đổi cách làm:** không cấm, mà lọc theo tập id trong phạm vi |
| Chạy `apply_scope` trên bản ghi được hỏi | nt | Xong (`scope_condition` tách từ `apply_scope`) |
| Ghi dấu vết + IP cho `/api/auth/refresh` | `modules/auth/controller.py` | Xong |
| Sửa `key_func` của limiter đọc đúng IP người dùng (hoặc bật `--proxy-headers`) | `core/limiter.py` / `start.prod.sh` | Xong bằng `core/client_ip.py`; **không** bật `--proxy-headers` |

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

**Đã làm:** `main` có `test_va_nhat_ky_cr313.py` (8 ca) + `test_client_ip_cr313.py` (7 ca);
`erp-v2` giữ `test_va_nhat_ky_thao_tac.py` (11 ca, có từ 05/09) và thêm
`test_va_nhat_ky_cr313.py` (3 ca cho ba chốt chuyển ngược) + `test_client_ip_cr313.py`.
Cả hai vế đều có test: vế chặn, và vế **không được chặn nhầm** người dùng thường.

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
