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
**Bản 1.4 — 14/09/2026.** bao-CR-394 vá **BM-014** (chỉ tin header IP khi peer TCP nằm trong
dải proxy tin cậy) và **BM-012** (token hết hạn vẫn ghi `user_id` + cờ `token_expired`);
bao-CR-395 = P3b của bao-CR-312 (màn hình phiên + khóa `login_session`), **BM-002 đóng trên
dev**. Cả hai mới ở local `erp-v2`, **chưa commit, chưa deploy**. Đính chính: đoạn "P2 và P3a
chưa lên `main`" ở bản 1.3 đã **hết hạn** — gộp `erp-v2` → `main` ngày 11/09 đã đưa cả P2 lẫn
P3a lên prod (`b5787ccc` là tổ tiên của `main`), nên đăng xuất trên prod **đã có hiệu lực**;
prod chỉ còn thiếu màn hình đá phiên của P3b. BM-013 **hoãn sang P4**, chưa vá.
**Bản 1.5 — 14/09/2026 (chiều).** Thêm **BM-015**: hồ sơ nhân sự chuyển *Nghỉ việc* mà tài
khoản đăng nhập **vẫn mở, phiên vẫn sống** — phát hiện khi đại ca hỏi *"nhân viên đổi trạng
thái thì có khóa token lại không"*. Vá ngay trong bao-CR-400 (local `erp-v2`, chưa commit),
kèm tab *Lịch sử đăng nhập* ở Trang cá nhân để người dùng tự thấy phiên lạ.
**Bản 1.6 — 14/09/2026 (tối).** Hai việc. (1) Đính chính trạng thái: bao-CR-394 + bao-CR-395
đã commit `erp-v2` `00b740b5` và bao-CR-400 đã commit `e89ab592`, **cả hai đã deploy DEV** —
mọi chỗ ghi *"chưa commit, chưa deploy"* ở bản 1.4 và 1.5 nay hết hạn; prod vẫn chờ gộp.
(2) **BM-005 đóng trên dev** bằng bao-CR-402 (P4 của bao-CR-312): `tab_change_log` + lớp sự
kiện ORM ghi trước/sau từng cột. **BM-013 vẫn mở nhưng đã có quyết định có đo đạc** — gỡ
`db.commit()` khỏi `record()` là **KHÔNG làm**, lỗ dấu-vết-ma đóng ở lớp thay đổi thay vì lớp
kể chuyện; lý do và hai chỗ sẽ hỏng ghi ngay dưới dòng BM-013.
**Bản 1.7 — 14/09/2026 (đêm).** Đợt rà **có phương pháp** đầu tiên, theo lệnh đại ca *"rà soát
các vấn đề bảo mật của hệ thống"*: soát **11 lớp phòng thủ** thay vì soát quanh một ticket.
Thêm **tám dòng BM-016 … BM-023**. Không dòng nào trùng vùng với 15 dòng cũ — chúng nằm ở
**cấu hình** và **lớp mạng**, đúng hai chỗ mà §4 của sổ này vẫn ghi là *"chưa ai nhìn"*. Hai
dòng đóng ngay bằng quyết định chứ không bằng mã: **BM-016** (chính sách mật khẩu) và
**BM-017** (xác thực hai lớp) — đại ca **chấp nhận rủi ro**, lý do ghi tại dòng. Một dòng lòi
ra trong lúc trả lời câu hỏi *"đổi `JWT_SECRET` có ảnh hưởng gì tới prod không"*: **BM-023** —
bí mật nằm trong DB mà giải mã hỏng thì **không phát ra tiếng động nào**, và thứ chết trước
tiên là **sao lưu**. Kèm theo: đính chính §4, thêm **Việc 5** ở §3, và thêm hẳn **§5 — kịch bản
kiểm thử bảo mật**, vì một dòng BM không có bài kiểm canh thì lần sau nó hở lại trong im lặng.

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
| BM-002 | **Cao** | Không có phiên đăng nhập phía máy chủ — token lộ thì không thu hồi được | **Đã vá trên dev (P3a bao-CR-360 + P3b bao-CR-395, 14/09/2026, `erp-v2` `00b740b5` — đã deploy dev).** Prod đã có P2 + P3a từ gộp 11/09 (`tab_login_session`, đăng xuất đóng phiên thật) — còn thiếu màn hình đá phiên / bắt đăng nhập lại của P3b; tới lúc đó quản trị vẫn cắt được máy lạ bằng cách khóa tài khoản |
| BM-003 | Trung bình | Gia hạn token không để lại dấu vết nào | **Vá một phần (09/09/2026, `main` f023c747 — đã deploy prod; `erp-v2` abff1298 — đã deploy dev).** `/api/auth/refresh` nay ghi `refresh` / `refresh_failed` kèm IP. Còn phần phiên phía máy chủ ở P3. ~~P3 sẽ bỏ chính dòng `refresh` thành công này theo QĐ-A~~ — **QĐ-A đã bị đảo 10/09/2026**, dòng `refresh` thành công GIỮ LẠI, xem BM-009 |
| BM-004 | Trung bình | Giới hạn tần suất đăng nhập dùng chung MỘT xô cho cả công ty | **Đã vá (09/09/2026, `main` f023c747 — đã deploy prod; `erp-v2` abff1298 — đã deploy dev).** Đã kiểm trên hệ thật: dấu vết đăng nhập mang IP công cộng thật (118.71.139.127, 27.64.133.181), không phải `172.x` → `CF-Connecting-IP` tới được api. Kiểm trên dev với header giả `X-Forwarded-For: 6.6.6.6` + `X-Real-IP: 7.7.7.7`: dòng ghi vẫn là IP thật (180.93.2.176), header giả bị bỏ qua |
| BM-005 | Trung bình | Nhật ký không lưu giá trị trước / sau — không chứng minh được đã đổi gì | **Đã vá trên dev (bao-CR-402 = P4 của bao-CR-312, 14/09/2026, local `erp-v2` — chưa commit).** `tab_change_log` (migration `d5f7a9c1b3e2`) + `core/change_tracker.py` bám sự kiện ORM, ghi trước/sau **từng cột** cho mọi bảng trừ `NO_LOG_TABLES`. Prod chưa có |
| BM-006 | Thấp | Dấu vết là tùy chọn theo từng lời gọi — quên gọi là mất | Vá một phần (bao-CR-311 + bao-CR-346) — xem BM-010 |
| BM-007 | Thấp | Dòng nhật ký không có IP / trình duyệt / mã lượt gọi | **Vá phần lớn (P1 của bao-CR-312, `erp-v2` 2eba1274 — mới deploy dev).** `tab_request_log` ghi IP + `request_id` + tuyến gọi; `tab_audit_log` có `request_id` / `ip` / `actor_kind`. Còn dấu thiết bị ở bao-CR-346 |
| BM-008 | Trung bình | Giá trị dữ liệu thật bị chép nguyên vào `error_detail` của dòng nhật ký khi câu SQL nổ | **Đã vá + ĐÃ ĐÓNG CẢ HAI PHÍA (bao-CR-346, 10/09/2026) — `erp-v2` 337fa9bb deploy dev; `main` e21023d1 deploy prod chiều 10/09** — `mask_error_detail`, xem chi tiết bên dưới |
| BM-009 | Trung bình | Thao tác **ĐỌC** không để lại dấu vết nào — kể cả tải tệp đính kèm và cả lượt bị chặn 403 | **Đã vá + ĐÃ ĐÓNG CẢ HAI PHÍA (bao-CR-346, 10/09/2026) — `erp-v2` 337fa9bb deploy dev; `main` e21023d1 deploy prod chiều 10/09** — ghi hết mọi GET |
| BM-010 | Trung bình | Đổi phân quyền và đổi tài khoản **không gọi `record()`** — vùng nhạy cảm nhất lại là vùng trắng | **Đã vá + ĐÃ ĐÓNG CẢ HAI PHÍA (bao-CR-346, 10/09/2026) — `erp-v2` 337fa9bb deploy dev; `main` e21023d1 deploy prod chiều 10/09** |
| BM-011 | Trung bình | Nhật ký chỉ có MỘT bản, nằm trên đúng cái máy kẻ tấn công đang đứng | **Đã vá + ĐÃ ĐÓNG CẢ HAI PHÍA (bao-CR-346, 10/09/2026) — `erp-v2` 337fa9bb deploy dev; `main` e21023d1 deploy prod chiều 10/09** — đóng gói ra R2 hàng tháng |
| BM-012 | Thấp | Token hết hạn thì dòng nhật ký ghi `user_id = 0` — không phân biệt được "khách vãng lai" với "người có tài khoản, token vừa hết hạn" | **Đã vá (bao-CR-394, 14/09/2026, `erp-v2` `00b740b5` — đã deploy dev, prod chờ gộp).** `_peek_user_id` đọc `sub` kể cả khi hết hạn, `tab_request_log.error_code = token_expired` |
| BM-013 | Thấp | `record()` tự `commit()` — giao dịch nghiệp vụ bị rollback vẫn để lại dấu vết ma | **Mở, đã chốt cách xử (bao-CR-402, 14/09/2026): KHÔNG gỡ `db.commit()`.** Lỗ đóng ở **lớp thay đổi** — `tab_change_log` chỉ ghi thứ đã commit thật. Lớp `core/audit.py` giữ nguyên nhịp cũ; đo 273 lời gọi ở 62 tệp tìm ra **hai chỗ hỏng ngay** nếu gỡ, xem dưới |
| BM-014 | Trung bình | `CF-Connecting-IP` được tin **vô điều kiện** — ai gọi thẳng vào api là tự khai IP của mình | **Đã vá (bao-CR-394, 14/09/2026, `erp-v2` `00b740b5` — đã deploy dev, prod chờ gộp).** Chỉ tin header khi peer TCP nằm trong `TRUSTED_PROXY_CIDRS` |
| BM-015 | **Cao** | Hồ sơ nhân sự chuyển *Nghỉ việc* (hoặc tắt hoạt động) mà **tài khoản đăng nhập vẫn mở, phiên đang sống vẫn dùng tiếp** — HR tưởng đã "cho nghỉ" là xong | **Đã vá (bao-CR-400, 14/09/2026, `erp-v2` `e89ab592` — đã deploy dev, prod chờ gộp).** `update_employee` / `detach_users` khóa mọi tài khoản gắn kèm + `force_relogin` với lý do `EMPLOYEE_RESIGNED = 6`, cùng giao dịch với hồ sơ |
| BM-016 | Trung bình | **Không có bất kỳ chính sách mật khẩu nào** — `password: str` trần ở cả ba cửa (tạo tài khoản · quản trị đặt lại · quên mật khẩu). Đặt mật khẩu `1` là hệ thống nhận | **Chấp nhận rủi ro — đại ca chốt 14/09/2026.** Lý do: hệ nội bộ, tài khoản do quản trị cấp chứ không ai tự đăng ký, và `LOGIN_RATE_LIMIT` đã chặn dò tự động. Bằng chứng: `auth/schema.py:20`, `user/schema.py:9` + `:14` — không chỗ nào có `min_length` |
| BM-017 | Thấp | Không có **xác thực hai lớp**, kể cả cho nhóm tài khoản quản trị đọc được nhật ký toàn hệ | **Chấp nhận rủi ro — đại ca chốt 14/09/2026.** Đây là lớp *tăng cường*, không phải lỗ đang hở; ghi vào sổ để lần rà sau không phải phát hiện lại |
| BM-018 | **Cao** *(có điều kiện)* | `JWT_SECRET` có giá trị mặc định `change_me_please` và **không có chốt nào chặn app khởi động với nó**. Môi trường nào quên đặt thì bất kỳ ai cũng **tự ký được vé hợp lệ cho bất kỳ tài khoản nào** — mất sạch mọi lớp phòng thủ phía trên | **Mở.** Bằng chứng: `core/config.py:13`. ⚠️ **Điều kiện kích hoạt CHƯA ĐO trên prod/dev** — xem Việc 5. Vá = thêm chốt khởi động, **không phải xoay khóa** (xoay khóa kéo theo BM-023) |
| BM-019 | Trung bình | Hai tệp nginx của prod **không đặt một header bảo mật nào** — trang ERP **nhúng iframe được** vào site bất kỳ (clickjacking), không HSTS, không `nosniff`, không `Referrer-Policy` | **Mở.** Bằng chứng: `docker/nginx.prod.conf` + `docker/nginx.erp.prod.conf` chỉ có `Cache-Control`. Nghịch lý đáng ghi: cửa **xem tệp đính kèm** làm rất kỹ (`attachment/controller.py:490` + `:493` — CSP `sandbox` + `nosniff`), còn cả ứng dụng thì trống |
| BM-020 | Trung bình | Trần tần suất cho endpoint **nghiệp vụ** đã khai nhưng **chưa có hiệu lực** — một tài khoản hợp lệ rút sạch dữ liệu trong phạm vi của mình ở tốc độ tối đa, không lớp nào cản | **Mở.** Bằng chứng: `core/limiter.py:13-16` — `default_limits=["300/minute"]` kèm **chính comment trong mã ghi là CHƯA có hiệu lực**; `main.py:115` chỉ gắn `state.limiter` + handler. Toàn hệ chỉ **4 endpoint** của `auth` có `@limiter.limit` |
| BM-021 | Thấp | `/api/uploads` được gắn bằng `StaticFiles`, **không kiểm quyền** — thứ gì rơi vào thư mục đó là công khai với mọi người | **Mở (rủi ro thấp trên prod).** Bằng chứng: `main.py:134`. Mã nguồn **tự cảnh báo ở ba chỗ**: `core/storage.py:53-54`, `core/file_registry.py:71`, `audit/tasks.py:123-131`. Prod dùng R2 nên đường lùi ghi-local không chạy — rủi ro là *ai đó ghi nhầm vào đó về sau* |
| BM-022 | Trung bình | CORS bật `allow_credentials=True` với `allow_origins` đọc từ `.env` — **giá trị thật trên prod chưa ai xác minh** | **Mở, CHƯA ĐO.** Bằng chứng: `main.py:125-131`, `config.py:166`. Nếu giá trị prod là `*` thì dòng này lên mức **Cao**; đo trước rồi mới kết luận, xem Việc 5 |
| BM-023 | Trung bình | Bí mật lưu trong DB (**mật khẩu SMTP, khóa R2**) giải mã hỏng thì **im lặng tuyệt đối**: `_decrypt` nuốt *mọi* lỗi trả chuỗi rỗng, `get()` lặng lẽ rơi về `.env`, `.env` trống thì trả rỗng. Hậu quả nặng nhất không phải mail chết mà là **sao lưu tự động lên R2 chết mà không ai biết** — phát hiện ra đúng vào lúc cần khôi phục | **Mở.** Bằng chứng: `core/app_settings.py:55-59` (`except (InvalidToken, Exception): return ""`) + `:95-100` (nhánh `if dec:` rơi về `.env`). Phát hiện khi trả lời câu hỏi về xoay `JWT_SECRET` |

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

~~⚠️ Vẫn còn hở trên prod: **P2 và P3a** (`bao-CR-358` + `bao-CR-360`) chưa lên `main`, nên
`tab_login_session` và bộ mã hành động chưa có trên hệ thật. Riêng **BM-002 (đăng xuất không
có hiệu lực)** vì vậy **vẫn mở trên prod**, dù đã có mã chạy trên `erp-v2`.~~
**Hết hạn từ 11/09/2026** (đính chính ở bản 1.4): gộp `erp-v2` → `main` hôm đó đã đưa P2 + P3a
lên prod — `git merge-base --is-ancestor b5787ccc origin/main` trả về đúng. Đăng xuất trên prod
đã đóng phiên thật. Thứ prod còn thiếu là P3b (màn hình phiên), xem BM-002.

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

**Mức: Cao. Trạng thái: ĐÃ VÁ TRÊN DEV 14/09/2026** (P3a bao-CR-360 + P3b bao-CR-395, `erp-v2`
`00b740b5` — đã deploy dev). Prod có P2 + P3a từ 11/09 (đăng xuất đóng phiên thật, `jti` trong token,
`get_current_user` kiểm phiên còn sống); màn hình quản trị phiên của P3b chưa lên prod. Mô tả
dưới đây giữ ở thì hiện tại của lúc phát hiện.

**Cái gì đã đóng từng hệ quả:**

- *Đăng xuất không đăng xuất* → P3a: `logout` đặt `revoked_at`, `get_current_user` từ chối
  phiên đã cắt (bộ đệm 60 giây trong tiến trình). Prod đã có.
- *Không thu hồi được một phiên* → P3b: `POST /api/login-sessions/{id}/revoke` (đá một máy),
  `POST /api/login-sessions/users/{user_id}/logout-all` (tăng `token_version`, ăn ngay), và
  người dùng tự đá máy lạ của mình qua `/api/auth/sessions*`. Khóa mới `login_session`
  (`read` · `delete`), `_SYS_ENTITIES`. Dev.
- *"Tài khoản này đang đăng nhập ở đâu?"* → màn `/system/sessions` + thẻ *Phiên đăng nhập* ở
  tab Tài khoản của hồ sơ nhân sự + tab *Thiết bị của tôi* ở `/me` (chỉ `frontend-v2`).
- *Token lộ là mất tới 7 ngày* → vẫn đúng về thời hạn, nhưng nay **cắt được** thay vì chờ hết
  hạn. Rút ngắn `REFRESH_EXPIRE_DAYS` là việc riêng, chưa quyết.

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

**Mức: Trung bình. Trạng thái: ĐÃ VÁ TRÊN DEV (bao-CR-402 = P4 của bao-CR-312, 14/09/2026,
local `erp-v2` — chưa commit). Prod chưa có.**

`tab_audit_log` có đúng bốn cột nghiệp vụ: `entity`, `entity_id`, `action`, `message`. `message`
là văn xuôi do người viết mã tự đặt. Không có chỗ nào lưu **giá trị cũ** và **giá trị mới**,
nên câu "dòng này trước đó ghi gì" không trả lời được — kể cả khi có dòng nhật ký.

Đây là gốc rễ khiến ticket 07/09 phải mở database. Thiết kế vá: `tab_change_log` sinh tự động
bằng sự kiện SQLAlchemy — [`nhat-ky-va-phien-dang-nhap.md`](nhat-ky-va-phien-dang-nhap.md) §3.2.

**Bản vá (bao-CR-402).** Bảng `tab_change_log` (migration `d5f7a9c1b3e2`) + `core/change_tracker.py`
bám ba sự kiện của `Session`: `before_flush` đọc `history` từng cột và **gom vào bộ đệm trong bộ
nhớ**, `after_flush` điền khóa chính cho dòng vừa thêm, `after_commit` đóng dấu. Cuối mỗi lượt
gọi, middleware ghi cả bộ đệm xuống bảng. Người viết mã **không phải gọi gì** — đó là điểm khác
căn bản với `record(...)`, và là thứ BM-006 cũng đang chờ.

Bốn luật cứng của lớp này, ghi ngay trong docstring của mô-đun:

1. **Không bao giờ ghi DB bên trong flush** — làm vậy là gọi lại chính flush đó, đệ quy.
2. **Không tự ghi nhật ký về bảng nhật ký** (`NO_LOG_TABLES`) — thiếu chốt này là vòng lặp vô hạn.
3. **Nhập liệu hàng loạt phải GỘP** (`actor_kind = 3`, hoặc chạm trần 500 dòng chi tiết) — một dòng tổng thay
   cho vài vạn dòng chi tiết.
4. **Chỉ ghi thứ đã COMMIT.** Quay đầu là vứt bộ đệm. Đây chính là câu trả lời của P4 cho
   **BM-013** ở lớp thay đổi.

Cột nhạy cảm bị che bằng `is_sensitive_column()` dùng chung với hai lớp kia
(`core/logging_policy.py`); `tab_user` là **cấm hết trừ danh sách được nêu tên**. 27 bài kiểm ở
`test/backend/test_nhat_ky_lop_orm_cr402.py`.

⚠️ **Một cái bẫy đáng nhớ, tìm ra lúc viết bài kiểm.** Giá trị cũ chỉ nằm sẵn trong `history`
khi thuộc tính **đã được nạp**. Bản ghi vừa đi qua một `commit` trong cùng phiên thì mọi cột hết
hạn, và lúc gán đè SQLAlchemy **không đọc lại** — nó ghi nhận giá trị cũ là *"không có"*, và
`load_history()` cũng không cứu được vì dấu đã đóng. Dòng nhật ký khi đó chỉ còn nửa câu
(*"đổi thành 15000"*, không nói đổi từ đâu) — đúng nửa mà BM-005 sinh ra để đóng. `_fetch_old_values`
bù bằng một truy vấn thẳng xuống DB trong `before_flush`, hợp lệ vì câu `UPDATE` chưa được phát.

---

### BM-006 — Dấu vết là tùy chọn theo từng lời gọi

**Mức: Thấp. Trạng thái: vá một phần (bao-CR-311).**

Ghi nhật ký hôm nay là **273 lời gọi `record(db, ...)` rải trong 62 tệp** *(số cũ trong sổ này
ghi 213/54 — đếm thiếu, xem ghi chú ở BM-013)*. Không có gì bắt buộc
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

**Mức: Thấp. Trạng thái: ĐÃ VÁ 14/09/2026** (bao-CR-394, `erp-v2` `00b740b5` — đã deploy dev).

`_peek_user_id` (`core/request_middleware.py:57`) giải mã token **không tra DB**; token hỏng,
hết hạn, hay sai chữ ký đều trả về `0`. Nên trong `tab_request_log`, "người lạ chưa đăng nhập"
và "người có tài khoản, token vừa hết hạn" là **cùng một giá trị**.

Chưa vá vì cửa quyền thật nằm ở `get_current_user`, đây chỉ là chỗ ghi. Cách vá khi làm P3:
đọc `sub` **kể cả khi token hết hạn** (`options={"verify_exp": False}`) rồi ghi kèm một cờ
`token_expired`, chứ đừng gộp vào `0`.

**Đã vá đúng cách đó.** `_peek_user_id` nay trả `(user_id, expired)`: gặp
`ExpiredSignatureError` thì giải mã lại với `verify_exp=False` để giữ `sub`; token sai chữ ký
vẫn về `0` (không tin `sub` của token giả). `RequestContext` thêm cờ `token_expired`; dòng
`tab_request_log` có `status_code = 401` mà cờ bật thì `error_code = "token_expired"` — tra
"ai bị văng vì hết hạn" là một câu `WHERE`. Không đổi schema. Test:
`test_nhat_ky_lop_may_cr312.py` (thêm ca token hết hạn).

---

### BM-013 — `record()` tự commit, để lại dấu vết ma

**Mức: Thấp. Trạng thái: MỞ, nhưng đã chốt cách xử ở bao-CR-402 (14/09/2026) — `db.commit()`
trong `record()` GIỮ NGUYÊN, cố ý. Lỗ đóng ở lớp thay đổi, không đóng ở lớp kể chuyện.**

`core/audit.py` kết bằng `db.commit()`. Nếu thao tác nghiệp vụ nổ **sau** lời gọi `record(...)`
và giao dịch bị rollback, dòng dấu vết vẫn nằm lại — nhật ký khẳng định một việc chưa từng xảy
ra. Ngược chiều với mọi dòng khác trong sổ này: ở đây nhật ký **thừa**, không thiếu.

Cố ý chưa vá ở P1: đổi nhịp commit là đổi hành vi của các lời gọi đang chạy thật mà chưa
có gì bù lại. Vá cùng P4, khi việc ghi chuyển xuống tầng ORM và gom một lần cuối request.

#### Đã đo, và quyết ngược lại (bao-CR-402)

Trước khi gỡ dòng `db.commit()`, P4 đi đếm **toàn bộ lời gọi bằng AST** chứ không grep: **273
lời gọi ở 62 tệp**.

⚠️ **Con số 213/54 ghi khắp các bản tài liệu trước là đếm THIẾU 87 chỗ.** Nguyên nhân: 14 tệp
import bí danh — `from app.core.audit import record as audit_record` — nên lời gọi mang tên
`audit_record(...)` và mọi phép grep chuỗi `record(` trượt hết. Lần rà sau phải hỏi cả hai tên.

Phân loại 273 chỗ đó tìm ra **hai chỗ hỏng ngay** nếu gỡ commit, cả hai ở
`document/file_access_log.py`:

* Hàm đó **đọc lại `tab_audit_log` trong cùng lượt gọi** — nó đếm số lần mở tệp (kể cả dòng vừa
  ghi) để so ngưỡng cảnh báo, và tra dòng `file_alert` để khỏi báo trùng. Không commit là bộ
  đếm lệch, ngưỡng cảnh báo sai theo.
* `_raise_alert` của chính tệp đó `db.add(Notification(...))` rồi **trông vào `record(...)`
  commit hộ**. Cả chuỗi hàm gọi nó không có `commit` nào, và lời gọi ngoài cùng nằm trong một
  `except` nuốt lỗi. Gỡ ra là thư cảnh báo mất **trong im lặng** — hỏng đúng kiểu khó phát hiện
  nhất.

Thêm **96 lời gọi** không có `commit` nào trong cùng hàm; phần lớn nhờ hàm con commit trước,
nhưng "phần lớn" không đủ để đổi một nhịp đang chạy thật trên prod.

**Chốt:** P4 đóng lỗ dấu-vết-ma ở **lớp thay đổi** — `core/change_tracker.py` chỉ ghi thứ đã
COMMIT, quay đầu là vứt bộ đệm. Câu hỏi *"việc này có thật sự xảy ra không"* nay trả lời được
bằng `tab_change_log`. Lớp `core/audit.py` giữ nguyên; lý do viết thẳng vào docstring của
`record()` để người sau không đi gỡ lại. Dòng BM-013 **để mở** vì lớp kể chuyện vẫn còn hở —
đóng hẳn thì phải gỡ commit, và đó là một CR riêng có sửa hai chỗ nói trên.

---

### BM-014 — `CF-Connecting-IP` được tin vô điều kiện

**Mức: Trung bình. Trạng thái: ĐÃ VÁ 14/09/2026** (bao-CR-394, `erp-v2` `00b740b5` — đã deploy dev).

`get_client_ip` (`core/client_ip.py:31`) lấy `CF-Connecting-IP` đầu tiên, không kiểm tra người
gọi có thật là Cloudflare không. Cả sự an toàn của nó dựa vào một giả định **nằm ngoài mã
nguồn**: "mọi lượt vào đều phải qua Cloudflare vì tunnel không mở cổng công khai".

Giả định đó đúng hôm nay. Ngày nào nó sai — ai đó vào được mạng nội bộ Docker, hoặc một lần
deploy publish cổng 8000 ra ngoài — thì kẻ gọi **tự khai IP của mình**, và cả nhật ký lẫn
xô giới hạn tần suất đăng nhập (`core/limiter.py` khóa theo đúng hàm này) đều nghe theo. Nghĩa
là BM-004 mở lại kèm theo, ở dạng khó thấy hơn.

Vá: chỉ tin `CF-Connecting-IP` khi peer TCP nằm trong dải IP Cloudflare, hoặc khi có một
header bí mật do cloudflared đặt. Chưa làm vì cần đụng cấu hình hạ tầng, không chỉ mã nguồn.

**Đã vá — không cần đụng hạ tầng.** Trong stack của mình, peer TCP của api **không bao giờ**
là Cloudflare: cloudflared chạy trong mạng Docker và nginx đứng giữa, nên mọi lượt hợp lệ tới
api đều từ một IP **nội bộ** (`172.x` / `10.x`). Vì vậy dải tin cậy là dải mạng riêng, không
phải dải Cloudflare: `settings.TRUSTED_PROXY_CIDRS` (mặc định
`10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,127.0.0.0/8`, đổi được qua `.env`).
`get_client_ip` chỉ đọc `CF-Connecting-IP` rồi tới hop cuối của `X-Forwarded-For` khi
`request.client.host` nằm trong dải đó; ngoài dải thì **lấy đúng IP TCP**, header có gì cũng
bỏ. CIDR gõ sai bị bỏ qua (có log), host không phải IP (như `testclient`) coi là không tin.
Cái còn hở về lý thuyết: ai đã vào được mạng Docker nội bộ thì vẫn khai IP giả được — nhưng
người đó đã đứng cạnh database rồi, IP giả là chuyện nhỏ nhất. Test:
`test_client_ip_cr313.py` (thêm ca peer ngoài dải + CIDR hỏng).

---

### BM-015 — Nghỉ việc trên hồ sơ nhân sự không khóa tài khoản, không cắt phiên

**Mức: Cao. Trạng thái: ĐÃ VÁ 14/09/2026** (bao-CR-400, `erp-v2` `e89ab592` — đã deploy dev).

Hai bảng, hai công tắc, không nối nhau. `tab_employee.status = resigned` (hoặc
`is_active = 0`) là điều HR bấm khi cho nghỉ việc; `tab_user.is_active` là thứ cửa
`get_current_user` thật sự kiểm. Trước bao-CR-400, `update_employee` chỉ ghi cột hồ sơ — tài
khoản gắn kèm vẫn `is_active = 1`, `token_version` không đổi, mọi phiên đang mở trên máy
người đó **dùng tiếp tới khi token tự hết hạn**, và người đó **đăng nhập lại được** ngày mai.
Chỉ có đường **xóa** hồ sơ (`detach_users`, CR-023) là khóa tài khoản, mà HR không xóa hồ sơ
người nghỉ việc — phải giữ để tính lương, bảo hiểm.

Vì sao xếp **Cao**: đây đúng là kịch bản mà cả bộ máy phiên (P3a/P3b) được dựng để trả lời —
*"nghỉ việc rồi mà còn phiên nào sống không"* (§8.5 của
[`nhat-ky-va-phien-dang-nhap.md`](nhat-ky-va-phien-dang-nhap.md)) — và câu trả lời đang là
*"còn, và HR không biết"*. Không cần kỹ năng gì để khai thác: người nghỉ việc mở lại tab đã
đăng nhập trên máy nhà.

**Đã vá — trong cùng giao dịch với hồ sơ, không tự mở lại.**

- `employee/service.py`: `has_left_company()` bắt đúng lúc **chuyển** (cũ ≠ mới) sang
  `resigned` hoặc tắt `is_active`; lưu lại y nguyên một hồ sơ đã nghỉ thì không khóa lại
  (không đẻ dấu vết trùng). `lock_linked_users()` khóa mọi `tab_user.employee_id = eid` và gọi
  `force_relogin(..., RevokeReason.EMPLOYEE_RESIGNED, commit=False)` — tăng `token_version`
  nên **ăn ngay ở lượt gọi kế**, không đợi bộ đệm 60 giây như đá phiên lẻ. Khóa nằm **trong**
  `try` của `update_employee`, trước `commit()` duy nhất: email trùng làm hồ sơ rollback thì
  khóa cũng rollback (có test).
- `detach_users()` (xóa hồ sơ / import CSV) đổi lý do từ `ACCOUNT_LOCKED` sang
  `EMPLOYEE_RESIGNED` để bảng phiên nói đúng vì sao.
- `RevokeReason.EMPLOYEE_RESIGNED = 6` (nhãn *Nghỉ việc*), khai ở `login_session/constants.py`
  và bản TypeScript `REVOKE_REASON` của `login-session-api.ts`.
- **Cố ý KHÔNG tự mở lại tài khoản** khi hồ sơ quay về *Đang làm*: mở khóa là quyết định của
  HR/quản trị (nút *Mở khóa* ở tab Tài khoản), vì hồ sơ mở lại thường là sửa tay nhầm chứ
  không phải người đó quay lại làm.
- Dấu vết: hai dòng audit — `employee` (`update`, ghi chú "khóa n tài khoản") và `user`
  (`lock`, lý do nghỉ việc) — để tra được từ cả hai phía.

Phía người dùng, cùng CR: tab **Lịch sử đăng nhập** ở `/me` (`GET /api/auth/sessions/history`,
khóa cứng vào `user.id` người gọi, 90 ngày mặc định / trần 365 / 1000 dòng) + số **phiên đang
mở** (`alive_count` trên `GET /api/auth/sessions`, đếm độc lập với bộ lọc). Người thường tự
thấy máy lạ và lần gõ sai mật khẩu vào tài khoản mình mà không cần HR — cùng bộ dựng
`build_login_history` với cửa quản trị, một bản vẽ hai chỗ vẽ.

Test: `test_nghi_viec_da_phien_cr400.py` (12 ca: chuyển trạng thái / tắt hoạt động / lưu lại
không khóa đôi / mở lại không mở khóa / rollback theo hồ sơ / xóa hồ sơ / `alive_count` /
lịch sử khóa vào chính mình / hai cửa chung một bộ dựng).

**Còn hở, ghi để biết:** tài khoản **không gắn hồ sơ nhân sự** (`employee_id = 0`, như
`admin`, tài khoản kỹ thuật) nằm ngoài đường này — nghỉ việc của họ vẫn phải khóa tay ở màn
Người dùng. Và HR chuyển trạng thái qua **import CSV** đi đường `detach_users` cũ (khóa + gỡ
liên kết) chứ không đi `has_left_company` — cùng kết quả khóa, nhưng gỡ liên kết luôn.

### BM-016 — Không có chính sách mật khẩu — CHẤP NHẬN RỦI RO

Ba cửa đặt mật khẩu, không cửa nào kiểm gì: `auth/schema.py:20` (`ResetPasswordInput`),
`user/schema.py:9` (tạo tài khoản), `user/schema.py:14` (quản trị đặt lại). Cả ba khai
`password: str` trần — không `min_length`, không kiểm độ mạnh, không cấm trùng tên đăng nhập.

Hai điều kiện làm nó dễ khai thác hơn vẻ ngoài: tên đăng nhập là **mã nhân viên** (đoán được
từ danh bạ), và tài khoản demo đặt mật khẩu **bằng đúng mã tài khoản**.

**Quyết định 14/09/2026 (đại ca): chấp nhận rủi ro.** Lý do: hệ nội bộ, **không ai tự đăng
ký** — tài khoản do quản trị cấp; và trần tần suất đăng nhập theo IP thật (BM-004 đã vá) đã
chặn được dò tự động, tức là con đường khai thác chính đã đóng.

**Điều kiện đảo lại quyết định** — ghi ra để lần sau khỏi phải cãi: hệ mở cho người ngoài công
ty tự đăng nhập (nhà cung cấp), hoặc mở cổng tự đăng ký, hoặc có một lần rò mật khẩu thật.

### BM-017 — Không có xác thực hai lớp — CHẤP NHẬN RỦI RO

Rà toàn `backend/app`: không có `totp`, `mfa`, `two_factor`, `otp` ở bất kỳ đâu.

**Quyết định 14/09/2026 (đại ca): chấp nhận rủi ro.** Đây là lớp **tăng cường**, không phải
lỗ đang hở — nó không mở thêm đường vào nào, nó chỉ làm một token đã lộ khó dùng hơn. Mà câu
*"token lộ thì sao"* trong hệ này đã có hai câu trả lời rồi: BM-002 (phiên phía máy chủ, thu
hồi được từng vé) và BM-015 (nghỉ việc là đá phiên ngay).

### BM-018 — `JWT_SECRET` mặc định, không có chốt khởi động

`core/config.py:13` khai `JWT_SECRET: str = "change_me_please"`, và **không chỗ nào kiểm**.
App khởi động bình thường với khóa đó.

Nếu một môi trường đang chạy bằng khóa mặc định thì **mọi dòng khác trong sổ này thành vô
nghĩa**: khóa đã nằm công khai trong mã nguồn, nên ai cũng tự ký được vé cho `admin`. Phân
quyền hai trục, `apply_scope`, nhật ký ba tầng — tất cả đứng **sau** cửa xác thực, mà cửa đó
mở toang.

⚠️ **Chưa đo.** Đó là *điều kiện*, không phải sự thật đã xác minh. Sổ này cấm ghi phỏng đoán,
nên mức **Cao** ở bảng là mức *nếu điều kiện đúng* — đo xong mới chốt. Xem Việc 5.

#### Vá bằng chốt khởi động — KHÔNG phải bằng xoay khóa

Cách vá là **một chốt lúc app khởi động**: môi trường không phải local mà `JWT_SECRET` còn là
giá trị mặc định (hoặc ngắn hơn ngưỡng) thì **từ chối chạy**. Rủi ro bằng 0, và nó canh cho
mọi lần deploy về sau chứ không chỉ hôm nay.

**Xoay khóa là việc khác hẳn, và nó KHÔNG miễn phí.** `JWT_SECRET` trong hệ này mang **bốn**
vai trò chứ không phải một:

| Vai trò | Ở đâu | Xoay khóa thì sao |
|---|---|---|
| Ký vé access + refresh | `core/auth.py:38` + `:62`, `core/request_middleware.py:79` | Mọi người đang đăng nhập **bị đá ra**. Phiền một lần, chấp nhận được |
| **Khóa Fernet mã hóa bí mật trong DB** — mật khẩu SMTP, khóa R2 | `core/app_settings.py:47` | **Giá trị trong `tab_setting` thành rác vĩnh viễn** |
| Khóa Fernet mã hóa mật khẩu hộp thư | `notification/mailbox_model.py:16`, `mailbox_service.py:34` | Như trên |
| Ký `confirm_token` của trợ lý AI | `assistant/tools/update_tool.py:119` | Token đang treo chết — tự hết hạn 15 phút, không sao |

Và vì **BM-023**, hai dòng giữa hỏng **trong im lặng**: thứ chết đầu tiên là **sao lưu tự động
lên R2**, tức đúng cái lưới đỡ mà người ta chỉ sờ tới khi đã ngã.

Nếu có ngày phải xoay khóa thật, thứ tự bắt buộc:

1. **Đo trước:** `tab_setting` có dòng `smtp_password` / `r2_access_key_id` /
   `r2_secret_access_key` không, và `.env` của môi trường đó có đủ ba giá trị lùi không.
2. Bí mật **chỉ** nằm trong DB → **giải mã bằng khóa cũ trước**, đổi khóa, rồi mã hóa lại bằng
   khóa mới. Một script `rekey`, một giao dịch — đừng làm bằng tay từng dòng.
3. Đổi vào **giờ thấp điểm**, vì nó đá sạch phiên.
4. Sau khi đổi, **kiểm tay** rằng sao lưu lên R2 còn chạy. **Đừng tin vào việc không thấy lỗi**
   — theo BM-023 thì không thấy lỗi chính là triệu chứng.

### BM-019 — nginx của prod không đặt header bảo mật nào

`docker/nginx.prod.conf` và `docker/nginx.erp.prod.conf` chỉ có `Cache-Control` và
`client_max_body_size`. Thiếu cả bốn: `X-Frame-Options` (hoặc `frame-ancestors`) — nghĩa là
**trang ERP nhúng vào iframe của site bất kỳ được**, đủ để dựng một trang dụ người dùng bấm
nút thật mà không biết; `Strict-Transport-Security`; `X-Content-Type-Options: nosniff`;
`Referrer-Policy`.

Nghịch lý đáng ghi để không ai tưởng là đã làm rồi: **cửa xem tệp đính kèm làm rất kỹ** —
`attachment/controller.py:490` + `:493` đặt `nosniff` và CSP `sandbox; default-src 'none'`,
đúng chuẩn cho tệp người dùng tải lên. Chỉ là **cả ứng dụng** thì không ai đặt.

### BM-020 — trần tần suất nghiệp vụ: khai rồi nhưng chưa bật

`core/limiter.py:16` khai `Limiter(key_func=get_client_ip, default_limits=["300/minute"])`, và
**chính comment ngay trên đó (`:13`) ghi rằng `default_limits` CHƯA có hiệu lực** —
`main.py:115` chỉ gắn `app.state.limiter` + handler chứ không gắn middleware của slowapi.

Toàn hệ vì thế chỉ có **4 endpoint** thực sự bị chặn, đều thuộc `auth`
(`auth/controller.py:138`, `:158`, `:325`, `:346`). Mọi endpoint nghiệp vụ **không có trần
nào**: một tài khoản hợp lệ rút sạch dữ liệu trong phạm vi của mình ở tốc độ tối đa. Phân
quyền vẫn đúng — nó chặn *lấy cái gì*, không chặn *lấy nhanh tới đâu*.

### BM-021 — `/api/uploads` phục vụ tĩnh, không kiểm quyền

`main.py:134` gắn `StaticFiles(directory="uploads")` vào `/api/uploads`. Không đi qua
`require()`, không qua `apply_scope` — thứ gì nằm trong thư mục đó là **công khai**.

Điểm nhẹ: prod dùng R2 nên đường lùi ghi-local của `core/storage.py:53` không chạy, và
`audit/tasks.py:123-131` đã có sẵn chốt chặn gói nhật ký rơi vào đó. Mã nguồn **tự cảnh báo ở
ba chỗ** (`storage.py:53-54`, `file_registry.py:71`, `audit/tasks.py:123`) — tức là người viết
đã biết. Rủi ro thật không phải hôm nay mà là **lần sau**: ai đó thêm một đường ghi mới vào
`uploads/` và không đọc ba dòng cảnh báo đó.

### BM-022 — CORS chưa xác minh trên prod

`main.py:125-131` bật `allow_credentials=True` cùng `allow_methods=["*"]` và
`allow_headers=["*"]`, với `allow_origins` đọc từ `.env` qua `config.py:166`.

Cấu hình này **đúng hay sai hoàn toàn phụ thuộc giá trị `CORS_ORIGINS` thật trên prod**, mà
chưa ai mở ra xem. Nếu ở đó là danh sách tên miền cụ thể thì không có vấn đề gì. Nếu là `*`
thì dòng này lên mức **Cao** — trình duyệt sẽ cho site bất kỳ gọi API kèm cookie/chứng danh
của người đang đăng nhập. Đo trước rồi mới kết luận; xem Việc 5.

### BM-023 — giải mã bí mật hỏng thì im lặng tuyệt đối

Phát hiện khi trả lời câu hỏi của đại ca *"đổi `JWT_SECRET` có ảnh hưởng gì tới prod không"*.

`core/app_settings.py:55-59`:

```python
def _decrypt(s: str) -> str:
    try:
        return _fernet().decrypt(s.encode()).decode()
    except (InvalidToken, Exception):      # nuốt MỌI lỗi
        return ""
```

rồi `get()` ở `:95-100` nhận chuỗi rỗng đó và **lặng lẽ rơi về `.env`**:

```python
if raw not in (None, ""):
    dec = _decrypt(raw)
    if dec:                                 # rỗng thì bỏ qua, không ai biết
        return dec
return getattr(_env, SECRETS[key], "")      # .env trống thì trả ""
```

Ba trạng thái rất khác nhau — *"chưa ai cấu hình"*, *"đã cấu hình nhưng giải mã hỏng"*, và
*"đã cấu hình, đọc tốt"* — bị ép về cùng một kết quả. Không một dòng log nào phân biệt.

**Vì sao đáng lo hơn vẻ ngoài:** ba bí mật đi qua đường này là mật khẩu SMTP và **hai khóa
R2** (`SECRETS` ở `:35-39`). Khóa R2 hỏng nghĩa là **sao lưu CSDL hai lần mỗi ngày im lặng
thất bại**. Mail chết thì có người kêu ngay trong ngày; sao lưu chết thì **không ai kêu cả** —
mình phát hiện đúng vào hôm cần khôi phục, là hôm tệ nhất có thể.

Điều kiện kích hoạt không chỉ có xoay khóa: chép DB prod sang môi trường khác (đúng nếp
`sync data dev→VPS` đang dùng) cũng làm mọi bí mật trong bản chép không giải mã được.

**Hướng vá:** phân biệt ba trạng thái — bắt đúng `InvalidToken` thay vì `Exception`, ghi
`log.error` khi giải mã hỏng, và thêm một chỉ báo ở màn Cấu hình hệ thống nói rõ *"đã cấu hình
nhưng KHÔNG đọc được"*. Kèm một kiểm tra sức khỏe cho sao lưu: lần sao lưu thành công gần nhất
quá N giờ thì báo.

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

### Việc 2 — tách khóa phiên ra khỏi bao-CR-312, làm trước — **XONG trên dev 14/09/2026**

Đã làm đúng theo ý này, thành ba đợt nhỏ: P2 (bao-CR-358, bảng phiên) → P3a (bao-CR-360,
`jti` + đăng xuất đóng phiên) → P3b (bao-CR-395, màn hình + khóa `login_session` + đá phiên /
bắt đăng nhập lại). P2 + P3a đã lên prod 11/09; P3b mới ở local. Cùng đợt: bao-CR-394 vá
BM-012 + BM-014. Đoạn dưới giữ nguyên làm bằng chứng cho lý do tách.

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

### Việc 5 — đợt BM-016…BM-023 (14/09/2026)

Xếp theo **rẻ trước, và đo trước khi vá**.

**5.0 — ĐO TRƯỚC, ngay hôm nay (0 dòng mã).** Hai dòng đang treo ở trạng thái *chưa đo* nên
chưa kết luận được mức: **BM-018** (`JWT_SECRET` trên prod còn là `change_me_please` không) và
**BM-022** (`CORS_ORIGINS` trên prod có phải `*` không). Cả hai nằm trong `.env` của VPS.
⚠️ **Kiểm bằng cách chỉ in ra CÓ/KHÔNG, tuyệt đối không in giá trị** — bí mật in ra một lần là
nó nằm lại trong lịch sử phiên, trong log, trong ảnh chụp màn hình. Đo xong thì sửa mức ở bảng
§2 rồi mới xếp lại thứ tự dưới đây.

**5.1 — Chốt khởi động cho `JWT_SECRET` (BM-018).** Môi trường không phải local mà khóa còn là
mặc định (hoặc quá ngắn) thì app **từ chối chạy**. Vài dòng ở `core/config.py`, rủi ro bằng 0.
⚠️ **KHÔNG xoay khóa** — đọc kỹ mục BM-018 ở §2 trước khi nghĩ tới chuyện đó.

**5.2 — Nói thành lời khi giải mã bí mật hỏng (BM-023).** Bắt đúng `InvalidToken`, ghi
`log.error`, và bày trạng thái *"đã cấu hình nhưng KHÔNG đọc được"* ở màn Cấu hình hệ thống.
Kèm một chốt sức khỏe cho sao lưu: lần sao lưu R2 thành công gần nhất quá N giờ thì báo. Đây là
việc **rẻ nhất mà cứu được nhiều nhất** — nó đổi một hỏng-hóc-im-lặng thành một hỏng-hóc-có-tiếng.

**5.3 — Header bảo mật cho nginx (BM-019).** Bốn dòng `add_header` vào hai tệp
`docker/nginx.prod.conf` và `docker/nginx.erp.prod.conf`. Rủi ro thấp, nhưng **phải thử trên
dev trước** vì `frame-ancestors` đặt chặt tay có thể chặn luôn khung xem tệp đính kèm.

**5.4 — Bật trần tần suất cho endpoint nghiệp vụ (BM-020).** Gắn middleware của slowapi trong
`main.py` cho `default_limits` có hiệu lực, hoặc gắn `@limiter.limit` cho từng nhóm endpoint
nặng. ⚠️ **Đặt trần quá tay là tự chặn người dùng thật** — nhìn số thật trong `tab_request_log`
(P1 đã ghi từ 10/09) rồi lấy đỉnh thật nhân hệ số, đừng bốc một con số cho đẹp.

**5.5 — Che `/api/uploads` (BM-021).** Việc nhỏ nhưng động tới đường phục vụ tệp, nên xếp cuối:
gỡ `StaticFiles` và bắt mọi lối xem tệp đi qua `/api/attachments/{id}/view` (nơi đã có
`require` + CSP). Trước khi gỡ phải rà **hết** những chỗ còn ghi vào `uploads/`.

**5.6 — Deploy 5 bản vá đang nằm ở dev lên prod.** Việc này **không đẻ ra mã mới** nhưng đóng
được nhiều lỗ nhất trong cả danh sách: BM-002, BM-005, BM-012, BM-014, **BM-015**. Nhắc lại cho
rõ mức khẩn: **trên prod hôm nay, đánh dấu một người *Nghỉ việc* KHÔNG khóa tài khoản và KHÔNG
đá phiên của họ.** Không dòng nào ở §2 nguy hơn dòng đó, và nó đã vá xong từ 14/09 — chỉ là vá
chưa tới nơi cần vá.

---

## 4. Sổ này KHÔNG làm gì

- **Không phải bản đánh giá an toàn đầy đủ.** Mười lăm dòng đầu (BM-001…BM-015) là những gì lòi
  ra khi soát quanh **từng ticket**, không phải kết quả của một đợt rà có phương pháp. Ngày
  **14/09/2026** mới có đợt rà đầu tiên đi theo **lớp phòng thủ** thay vì đi theo ticket — nó
  đẻ ra BM-016…BM-023 và lấp đúng hai vùng mà bản cũ của mục này ghi là *"chưa ai nhìn"*:
  **cấu hình** và **lớp mạng / VPS**. Ba vùng vẫn **chưa ai nhìn**, giữ nguyên cảnh báo: khâu
  **tải tệp lên** (kiểu MIME, kích thước, tên tệp), khâu **nhập/xuất dữ liệu** (Excel/CSV), và
  phần **tích hợp ngoài** (Cloudflare tunnel, R2, Brevo, webhook). **Không có dòng nào ở đây
  không có nghĩa là chỗ đó sạch.**
- **Không thay tài liệu thiết kế.** Cách vá nằm ở tệp của từng CR.
- **Không dựng lại được quá khứ.** Mọi thứ trong sổ này chỉ vá được từ lúc vá trở đi.

---

## 5. Kịch bản kiểm thử bảo mật

Viết ngày 14/09/2026, theo yêu cầu *"cần các kịch bản để test các phần bảo mật này"*.

**Luật của mục này — một dòng BM chưa có kịch bản kiểm thì coi như CHƯA vá.** Vá bảo mật khác
vá lỗi nghiệp vụ ở một chỗ: **lỗi nghiệp vụ tự kêu khi tái phát, lỗ bảo mật thì không**. Người
dùng không gọi điện báo *"hôm nay tôi vào được dữ liệu phòng khác"* — họ không biết, hoặc họ
không nói. Bài kiểm chính là cái miệng của lỗ hổng.

Và **bài kiểm phải viết từ phía KẺ TẤN CÔNG**: khẳng định *"người không có quyền thì KHÔNG
làm được"*, chứ không phải *"người có quyền thì làm được"*. Vế sau xanh ngay cả khi chốt chặn
đã bị gỡ sạch.

### 5.1 Bài kiểm tự động — `pytest`

Đặt chung một tệp `test/backend/test_bao_mat_cau_hinh.py`. Chạy đúng tệp đó, đừng quét cả
`test/backend`.

| Dòng | Bài kiểm | Khẳng định |
|---|---|---|
| **BM-018** | `test_chot_khoi_dong_tu_choi_khoa_mac_dinh` | `ENV=production` + `JWT_SECRET="change_me_please"` → hàm chốt **ném lỗi**. Biến thể: khóa ngắn hơn ngưỡng cũng ném; khóa thật thì đi qua; `ENV=local` thì đi qua (đừng làm tắc máy anh em) |
| **BM-023** | `test_giai_ma_hong_thi_bao_thanh_tieng` | Ghi vào `tab_setting` một chuỗi mã bằng khóa **A**, rồi đọc bằng khóa **B** → `get()` **không** trả im lặng chuỗi rỗng: phải có `log.error` (bắt bằng `caplog`) và trạng thái phải phân biệt được *chưa cấu hình* với *cấu hình mà đọc hỏng* |
| **BM-023** | `test_ba_trang_thai_bi_mat_khac_nhau` | Ba ca: chưa có dòng · có dòng đọc tốt · có dòng đọc hỏng → **ba kết quả khác nhau**. Hôm nay cả ba ra `""` |
| **BM-021** | `test_uploads_khong_lo_tep_cho_nguoi_la` | `client.get("/api/uploads/<tên tệp có thật>")` **không kèm token** → phải **401/403/404**, tuyệt đối không phải 200 kèm nội dung |
| **BM-022** | `test_cors_tu_choi_origin_la` | Gửi `Origin: https://ke-xau.example` → phần hồi đáp **không** được có `Access-Control-Allow-Origin` khớp origin đó. Kèm ca ngược: origin thật trong `CORS_ORIGINS` thì được |
| **BM-020** | `test_tran_tan_suat_co_hieu_luc` | Gọi một endpoint nghiệp vụ quá ngưỡng trong một phút → phải có **429**. Đây là bài duy nhất cần `TestClient` thật + đặt lại bộ đếm của limiter giữa các ca, nên tách riêng kẻo làm giòn cả tệp |

⚠️ **Bẫy đã biết, đừng dẫm lại:** `test/backend` chạy **SQLite**, mà SQLite **không** ép độ dài
`VARCHAR` và không có nhiều ràng buộc của MySQL — bài kiểm nào ghi xuống DB rồi khẳng định là
**xanh giả**. Với BM-023 thì kiểm ở tầng **hàm** (`_decrypt` / `get`), đừng kiểm bằng cách tin
vào DB.

### 5.2 Kiểm tay trên hệ đã deploy

Mấy thứ dưới đây **không** pytest nào thấy được, vì chúng sống ở nginx và ở `.env` của VPS.
Chạy sau mỗi lần deploy prod.

**BM-019 — header bảo mật.** Gọi thẳng trang chủ prod và đọc phần đầu hồi đáp. Phải thấy đủ
`X-Frame-Options` (hoặc `Content-Security-Policy: frame-ancestors`), `X-Content-Type-Options`,
`Strict-Transport-Security`, `Referrer-Policy`.
Kiểm cái **thật sự đau**: dựng một tệp HTML tại chỗ, nhúng `<iframe src="https://thumua...">`,
mở bằng trình duyệt — **trang phải KHÔNG hiện**. Vá xong mà iframe vẫn hiện thì header đặt sai
chỗ (đặt ở `location` của API thay vì của trang), không phải "chưa kịp áp dụng".

**BM-022 — CORS.** Gửi một request tiền kiểm (`OPTIONS`) kèm `Origin` của một tên miền bịa ra
và đọc hồi đáp: **không được** có `Access-Control-Allow-Origin` phản chiếu lại origin đó, và
**không được** có `Access-Control-Allow-Credentials: true` đi kèm. Origin thật thì có.

**BM-018 / BM-022 — đọc `.env` của VPS.** ⚠️ **Chỉ in ra CÓ/KHÔNG.** Cần biết đúng hai điều:
`JWT_SECRET` có **khác** `change_me_please` không, và `CORS_ORIGINS` có **khác** `*` không.
Không in giá trị, không `cat` cả tệp, không dán kết quả vào chỗ nào lưu lại được.

**BM-021 — `/api/uploads`.** Liệt kê xem thư mục `uploads` trên prod đang có gì (kỳ vọng: gần
như rỗng vì prod dùng R2). Có tệp thì mở thử đường dẫn đó bằng **cửa sổ ẩn danh** — hiện ra
được là lỗ thật, không phải lý thuyết.

**BM-023 — sao lưu R2 còn sống không.** Đây là bài quan trọng nhất và **không ai nghĩ tới nó
cho tới lúc cần khôi phục**: vào R2 xem **thời điểm tệp sao lưu mới nhất**. Quá 24 giờ là hỏng,
bất kể log có sạch tới đâu. Làm sau **mỗi lần** đổi `JWT_SECRET`, đổi khóa R2, hoặc chép DB
giữa các môi trường.

### 5.3 Kiểm lại các dòng đã vá (hồi quy)

Dòng đã đóng vẫn phải có người canh, vì thứ mở lại một lỗ cũ thường là một CR **không liên
quan gì** tới nó. Ba tệp đang canh, giữ nguyên đừng gộp: `test_nghi_viec_da_phien_cr400.py`
(BM-015) · bộ kiểm của bao-CR-402 (BM-005) · `test_pham_vi_khai_du_b07.py` (44/44 entity —
thêm entity mà quên khai `SCOPE_FIELDS` là suite đỏ ngay, đúng thiết kế).

Và một bài **chưa ai viết, nên viết**: với mỗi endpoint mới đụng dữ liệu nhiều người, một ca
*"tài khoản quyền thấp gọi vào → 403"*. BM-001 tồn tại vì câu đó chưa từng được hỏi.
