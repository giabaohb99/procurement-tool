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
**BM-017** (xác thực hai lớp) — đại ca **chấp nhận rủi ro**, lý do ghi tại dòng.
*(Đính chính của bản 1.8: **BM-016 đã bị đảo lại ngay trong ngày** và nay đóng bằng mã —
xem dưới. Chỉ còn **BM-017** là đóng bằng quyết định.)* Một dòng lòi
ra trong lúc trả lời câu hỏi *"đổi `JWT_SECRET` có ảnh hưởng gì tới prod không"*: **BM-023** —
bí mật nằm trong DB mà giải mã hỏng thì **không phát ra tiếng động nào**, và thứ chết trước
tiên là **sao lưu**. Kèm theo: đính chính §4, thêm **Việc 5** ở §3, và thêm hẳn **§5 — kịch bản
kiểm thử bảo mật**, vì một dòng BM không có bài kiểm canh thì lần sau nó hở lại trong im lặng.
**Bản 1.8 — 14/09/2026 (khuya).** **BM-016 ĐẢO LẠI**: từ *"chấp nhận rủi ro"* thành **đã vá**
bằng `bao-CR-405`. Lý do đảo nằm ngay dưới dòng BM-016 và không xóa quyết định cũ — hai điều
mới biết sau khi đếm lại mã nguồn: (1) hệ có **năm** cửa đặt mật khẩu chứ không phải ba như
bản 1.7 ghi, trong đó cửa *đặt lại bằng liên kết* **không kiểm gì cả**; (2) tên đăng nhập
chính là **mã nhân viên**, nên mật khẩu đặt trùng mã nhân viên chỉ cần **một lần đoán** —
`LOGIN_RATE_LIMIT` của BM-004 không đỡ được thứ chỉ cần một lần. Chính sách gom về một chỗ
(`app/core/password_policy.py`) và có **bài kiểm cấu trúc** quét AST: hàm nào gọi
`hash_password` mà không gọi `validate_password` là test đỏ — cửa thứ sáu sẽ lộ ra ở CI chứ
không lộ trên màn hình khách. ⚠️ **Mật khẩu yếu đã tồn tại thì KHÔNG bị đụng tới** — chính
sách chỉ gác lúc ĐẶT.
**Bản 1.9 — 14/09/2026 (khuya).** **Đo BM-018 + BM-022 trên VPS** theo lệnh đại ca — chỉ in
CÓ/KHÔNG, không in giá trị. **Cả hai SẠCH trên prod**: khóa không phải giá trị mặc định và dài
≥ 32 ký tự; `CORS_ORIGINS` đúng một tên miền thật có TLS, không có `*`. Hai dòng vì thế hạ
xuống mức **Thấp**, BM-022 **đóng bằng đo** (không cần mã), BM-018 chỉ còn phần chốt khởi
động. Đo **hai lớp** — tệp `.env` *và* tiến trình đang chạy — vì hai thứ đó trôi khỏi nhau là
chuyện thường. Nhân lần đo lòi ra dòng mới **BM-024**: **prod và dev dùng CHUNG một
`JWT_SECRET`**. Vế *ký vé giả* thì **không hở** — chốt phiên `_check_session` của bao-CR-360
P3a (xác nhận trên chính container prod đang chạy) đòi `jti` phải là một phiên còn sống trong
CSDL prod, nên vé ký từ dev chết ở đó. Vế hở thật là **vai trò Fernet**: cùng khóa đó mã hóa
mật khẩu SMTP + hai khóa R2 trong `tab_setting`, mà prod với dev **chung một máy chủ MySQL** —
vào được dev là đọc được bí mật của prod. Hướng vá: **đổi khóa của DEV** (việc 5.7), tuyệt đối
không đụng khóa prod.
**Bản 2.0 — 14/09/2026 (khuya).** **BM-024 ĐÃ VÁ ngay trong ngày phát hiện** — dev nay có khóa
riêng. Ba bí mật trong `tab_setting` của dev mã hóa lại bằng khóa mới, **3/3 khớp bản gốc**;
đo lại: *prod và dev dùng chung khóa: **KHÔNG***; **prod không restart, không deploy, không
đụng một dòng nào** và vẫn đọc được bí mật của prod. Không có mã nguồn nào đổi — việc hạ tầng,
không cần CR. Hai bẫy ghi lại ở mục BM-024 để lần sau khỏi dẫm: **mã hóa lại TRƯỚC, đổi `.env`
SAU** (ngược lại là mất khóa cũ, và vì BM-023 thì mất **trong im lặng**), và **`docker compose
restart` không nạp lại biến môi trường** — biến nạp lúc *tạo* container, phải `up -d`.
**Bản 2.1 — 14/09/2026 (khuya).** Đợt rà thứ hai, theo lệnh đại ca *"tiếp tục rà bảo mật phần
tải tệp lên"*: soát **khâu tải tệp lên** — đúng một trong ba vùng mà §4 vẫn ghi là *"chưa ai
nhìn"*. Thêm **bảy dòng BM-025 … BM-031**. Dòng nặng nhất là **BM-025**: `/api/attachments/register`
**không hề kiểm tệp đó của ai** — đã chứng minh bằng bài chạy thật, một tài khoản chỉ có
`purchase_request` phạm vi `own` gắn được tệp mật của người khác vào phiếu của mình rồi **tải
về**. Bài học của đợt này: **lỗ không nằm ở module `attachment`** — nó làm khá kỹ (danh sách
trắng kiểu xem trong khung, `nosniff`, CSP `sandbox`, `safe_name` cho khóa lưu trữ) — mà nằm ở
**bốn cửa tải lên đi vòng qua nó**: ảnh đại diện, chữ ký, ảnh bài HDSD. Rà một module rồi kết
luận "khâu tải tệp đã sạch" là cách bỏ sót cả bốn cửa đó; census **12 tệp có `UploadFile`** mới
là cách đúng. Vùng *tải tệp lên* ở §4 nay **đã có người nhìn**, còn hai vùng.
**Bản 2.2 — 15/09/2026.** **Cả bảy dòng BM-025 … BM-031 đã vá** trong một CR duy nhất
(`bao-CR-408`) — chưa commit, chưa deploy. Chốt kiến trúc của đợt vá: **một tệp
`core/upload_guard.py`** làm cả ba việc mà trước đó không cửa nào làm (đọc byte đầu · suy
`content_type` từ nội dung · chặn tên tệp quá dài), cộng **một bảng `DIRECT_FILE_POLICY`** trong
`core/file_registry.py` khai luật cho những cửa **không đi qua `FileLink`**. Hai thứ đợt rà
14/09 chưa thấy, lòi ra lúc vá:
- **Cửa ảnh thứ SÁU** — `employee/controller.py::upload_id_image` (ảnh CCCD hai mặt) mang đúng
  lỗ `startswith("image/")` của BM-027. Sổ ghi *"bốn cửa"*, con số thật là **sáu**. Cách tìm ra
  vẫn là census `UploadFile = File(...)` chứ không phải đọc lại sổ.
- **Cửa gắn tệp thứ HAI** — `ticket/service._register_files` gắn `file_id` vào `FileLink` mà
  không hỏi chủ sở hữu, y hệt BM-025 nhưng ở một module khác. `comment` và `forum` thì có kiểm
  nhưng mỗi nơi chép một bản; cả ba nay dùng chung `attachment/service.select_attachable_ids`.
**Bản 2.3 — 21/09/2026.** Không thêm dòng BM; ghi nhận **một cửa GHI mới vào phân quyền**
mở có chủ ý (`bao-CR-435`, `assistant/tools/account_setup_tool.py` + endpoint
`POST /api/assistant/confirm-account-setup`): trợ lý AI gán vai trò CÓ SẴN + ô loại trừ phòng
ban theo khuôn đề xuất → người bấm Xác nhận. Cửa này đi qua **đúng bộ chốt của màn Phân
quyền** — `user.write` + `role.read` + `employee.read`, `get_scoped(User, write)`, L1
`block_edit_own_permissions`, L2 `block_role_escalation` — và kiểm lại toàn bộ lúc bấm, không
tin đề xuất cũ (vai trò được tick thêm quyền sau lúc đề xuất vẫn bị chặn). Không tạo tài
khoản, không mật khẩu, không tạo vai trò. Lý do ghi vào sổ: lần rà sau phải đếm nó vào census
"đường ghi vào `user_role` / `tab_user_scope`" — trước nay chỉ có màn Phân quyền và seed.

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
| BM-002 | **Cao** | Không có phiên đăng nhập phía máy chủ — token lộ thì không thu hồi được | **ĐÃ ĐÓNG — vá đủ cả dev lẫn PROD (P3a bao-CR-360 + P3b bao-CR-395).** Dev 14/09/2026 (`erp-v2` `00b740b5`), **prod 14/09/2026** (`main` `ea405aa0`, đẩy trong đợt `5abd5dc3`): màn phiên đăng nhập + đá phiên + bắt đăng nhập lại nay đã có trên prod |
| BM-003 | Trung bình | Gia hạn token không để lại dấu vết nào | **Vá một phần (09/09/2026, `main` f023c747 — đã deploy prod; `erp-v2` abff1298 — đã deploy dev).** `/api/auth/refresh` nay ghi `refresh` / `refresh_failed` kèm IP. Còn phần phiên phía máy chủ ở P3. ~~P3 sẽ bỏ chính dòng `refresh` thành công này theo QĐ-A~~ — **QĐ-A đã bị đảo 10/09/2026**, dòng `refresh` thành công GIỮ LẠI, xem BM-009 |
| BM-004 | Trung bình | Giới hạn tần suất đăng nhập dùng chung MỘT xô cho cả công ty | **Đã vá (09/09/2026, `main` f023c747 — đã deploy prod; `erp-v2` abff1298 — đã deploy dev).** Đã kiểm trên hệ thật: dấu vết đăng nhập mang IP công cộng thật (118.71.139.127, 27.64.133.181), không phải `172.x` → `CF-Connecting-IP` tới được api. Kiểm trên dev với header giả `X-Forwarded-For: 6.6.6.6` + `X-Real-IP: 7.7.7.7`: dòng ghi vẫn là IP thật (180.93.2.176), header giả bị bỏ qua |
| BM-005 | Trung bình | Nhật ký không lưu giá trị trước / sau — không chứng minh được đã đổi gì | **ĐÃ ĐÓNG TRÊN PROD (bao-CR-402 = P4 của bao-CR-312, 14/09/2026, `main` `68733348` trong đợt `5abd5dc3`; migration đã chạy, head prod = `d5f7a9c1b3e2`). Commit `erp-v2` `4b51b545` nhưng DEV CHƯA DEPLOY** — dev còn ở `e89ab592`, head alembic `c3e5a7b9d1f2`. `tab_change_log` (migration `d5f7a9c1b3e2`) + `core/change_tracker.py` bám sự kiện ORM, ghi trước/sau **từng cột** cho mọi bảng trừ `NO_LOG_TABLES`. Prod chưa có |
| BM-006 | Thấp | Dấu vết là tùy chọn theo từng lời gọi — quên gọi là mất | Vá một phần (bao-CR-311 + bao-CR-346) — xem BM-010 |
| BM-007 | Thấp | Dòng nhật ký không có IP / trình duyệt / mã lượt gọi | **Vá phần lớn (P1 của bao-CR-312, `erp-v2` 2eba1274 — mới deploy dev).** `tab_request_log` ghi IP + `request_id` + tuyến gọi; `tab_audit_log` có `request_id` / `ip` / `actor_kind`. Còn dấu thiết bị ở bao-CR-346 |
| BM-008 | Trung bình | Giá trị dữ liệu thật bị chép nguyên vào `error_detail` của dòng nhật ký khi câu SQL nổ | **Đã vá + ĐÃ ĐÓNG CẢ HAI PHÍA (bao-CR-346, 10/09/2026) — `erp-v2` 337fa9bb deploy dev; `main` e21023d1 deploy prod chiều 10/09** — `mask_error_detail`, xem chi tiết bên dưới |
| BM-009 | Trung bình | Thao tác **ĐỌC** không để lại dấu vết nào — kể cả tải tệp đính kèm và cả lượt bị chặn 403 | **Đã vá + ĐÃ ĐÓNG CẢ HAI PHÍA (bao-CR-346, 10/09/2026) — `erp-v2` 337fa9bb deploy dev; `main` e21023d1 deploy prod chiều 10/09** — ghi hết mọi GET |
| BM-010 | Trung bình | Đổi phân quyền và đổi tài khoản **không gọi `record()`** — vùng nhạy cảm nhất lại là vùng trắng | **Đã vá + ĐÃ ĐÓNG CẢ HAI PHÍA (bao-CR-346, 10/09/2026) — `erp-v2` 337fa9bb deploy dev; `main` e21023d1 deploy prod chiều 10/09** |
| BM-011 | Trung bình | Nhật ký chỉ có MỘT bản, nằm trên đúng cái máy kẻ tấn công đang đứng | **Đã vá + ĐÃ ĐÓNG CẢ HAI PHÍA (bao-CR-346, 10/09/2026) — `erp-v2` 337fa9bb deploy dev; `main` e21023d1 deploy prod chiều 10/09** — đóng gói ra R2 hàng tháng |
| BM-012 | Thấp | Token hết hạn thì dòng nhật ký ghi `user_id = 0` — không phân biệt được "khách vãng lai" với "người có tài khoản, token vừa hết hạn" | **ĐÃ ĐÓNG — dev + PROD (bao-CR-394, dev `erp-v2` `00b740b5`, prod `main` `ea405aa0` đẩy trong đợt `5abd5dc3` ngày 14/09/2026).** `_peek_user_id` đọc `sub` kể cả khi hết hạn, `tab_request_log.error_code = token_expired` |
| BM-013 | Thấp | `record()` tự `commit()` — giao dịch nghiệp vụ bị rollback vẫn để lại dấu vết ma | **Mở, đã chốt cách xử (bao-CR-402, 14/09/2026): KHÔNG gỡ `db.commit()`.** Lỗ đóng ở **lớp thay đổi** — `tab_change_log` chỉ ghi thứ đã commit thật. Lớp `core/audit.py` giữ nguyên nhịp cũ; đo 273 lời gọi ở 62 tệp tìm ra **hai chỗ hỏng ngay** nếu gỡ, xem dưới |
| BM-014 | Trung bình | `CF-Connecting-IP` được tin **vô điều kiện** — ai gọi thẳng vào api là tự khai IP của mình | **ĐÃ ĐÓNG — dev + PROD (bao-CR-394, dev `erp-v2` `00b740b5`, prod `main` `ea405aa0` đẩy trong đợt `5abd5dc3` ngày 14/09/2026).** Chỉ tin header khi peer TCP nằm trong `TRUSTED_PROXY_CIDRS` |
| BM-015 | **Cao** | Hồ sơ nhân sự chuyển *Nghỉ việc* (hoặc tắt hoạt động) mà **tài khoản đăng nhập vẫn mở, phiên đang sống vẫn dùng tiếp** — HR tưởng đã "cho nghỉ" là xong | **ĐÃ ĐÓNG — dev + PROD (bao-CR-400, dev `erp-v2` `e89ab592`, prod `main` `39176d8c` đẩy trong đợt `5abd5dc3` ngày 14/09/2026).** `update_employee` / `detach_users` khóa mọi tài khoản gắn kèm + `force_relogin` với lý do `EMPLOYEE_RESIGNED = 6`, cùng giao dịch với hồ sơ |
| BM-016 | Trung bình | **Không có bất kỳ chính sách mật khẩu nào** — `password: str` trần ở cả ba cửa (tạo tài khoản · quản trị đặt lại · quên mật khẩu), cửa tự đổi đòi 6 ký tự, cửa hồ sơ nhân sự đòi 4. Đặt mật khẩu `1` là hệ thống nhận | **Đã vá (bao-CR-405, 14/09/2026) — ĐẢO LẠI quyết định "chấp nhận rủi ro" của chính ngày 14/09.** Lý do đảo: rà tới nơi thì thấy census có **NĂM** cửa chứ không phải ba, và lỗ thật không phải "mật khẩu ngắn" mà là **mật khẩu đặt bằng đúng mã nhân viên = tên đăng nhập** — thứ `LOGIN_RATE_LIMIT` không đỡ vì kẻ đoán chỉ cần **một** lần thử. Vá: `core/password_policy.validate_password` gọi ở cả năm cửa. Bằng chứng cũ: `auth/schema.py:20`, `user/schema.py:9` + `:14` |
| BM-017 | Thấp | Không có **xác thực hai lớp**, kể cả cho nhóm tài khoản quản trị đọc được nhật ký toàn hệ | **Chấp nhận rủi ro — đại ca chốt 14/09/2026.** Đây là lớp *tăng cường*, không phải lỗ đang hở; ghi vào sổ để lần rà sau không phải phát hiện lại |
| BM-018 | Thấp *(hạ mức sau khi đo)* | `JWT_SECRET` có giá trị mặc định `change_me_please` và **không có chốt nào chặn app khởi động với nó**. Môi trường nào quên đặt thì bất kỳ ai cũng **tự ký được vé hợp lệ cho bất kỳ tài khoản nào** — mất sạch mọi lớp phòng thủ phía trên | **ĐÃ ĐO 14/09/2026 trên VPS — prod SẠCH:** không phải giá trị mặc định, dài ≥ 32 ký tự, đo cả ở `.env` lẫn trong tiến trình đang chạy; dev cũng không phải mặc định. Điều kiện kích hoạt **không đúng**, nên mức hạ từ *Cao (có điều kiện)* xuống **Thấp**. **Vẫn còn mở phần chốt khởi động** (`core/config.py:13`) — canh cho những lần deploy sau. **KHÔNG xoay khóa** (kéo theo BM-023). ⚠️ Lần đo này lòi ra **BM-024** |
| BM-019 | Trung bình | Hai tệp nginx của prod **không đặt một header bảo mật nào** — trang ERP **nhúng iframe được** vào site bất kỳ (clickjacking), không HSTS, không `nosniff`, không `Referrer-Policy` | **Mở.** Bằng chứng: `docker/nginx.prod.conf` + `docker/nginx.erp.prod.conf` chỉ có `Cache-Control`. Nghịch lý đáng ghi: cửa **xem tệp đính kèm** làm rất kỹ (`attachment/controller.py:490` + `:493` — CSP `sandbox` + `nosniff`), còn cả ứng dụng thì trống |
| BM-020 | Trung bình | Trần tần suất cho endpoint **nghiệp vụ** đã khai nhưng **chưa có hiệu lực** — một tài khoản hợp lệ rút sạch dữ liệu trong phạm vi của mình ở tốc độ tối đa, không lớp nào cản | **Mở.** Bằng chứng: `core/limiter.py:13-16` — `default_limits=["300/minute"]` kèm **chính comment trong mã ghi là CHƯA có hiệu lực**; `main.py:115` chỉ gắn `state.limiter` + handler. Toàn hệ chỉ **4 endpoint** của `auth` có `@limiter.limit` |
| BM-021 | Thấp | `/api/uploads` được gắn bằng `StaticFiles`, **không kiểm quyền** — thứ gì rơi vào thư mục đó là công khai với mọi người | **Mở (rủi ro thấp trên prod).** Bằng chứng: `main.py:134`. Mã nguồn **tự cảnh báo ở ba chỗ**: `core/storage.py:53-54`, `core/file_registry.py:71`, `audit/tasks.py:123-131`. Prod dùng R2 nên đường lùi ghi-local không chạy — rủi ro là *ai đó ghi nhầm vào đó về sau* |
| BM-022 | Thấp *(hạ mức sau khi đo)* | CORS bật `allow_credentials=True` với `allow_origins` đọc từ `.env` — **giá trị thật trên prod chưa ai xác minh** | **ĐÃ ĐO 14/09/2026 trên VPS — prod SẠCH, đóng dòng này.** Không phải `*`, không chứa `*` ở bất kỳ đâu, đúng **1 origin** là tên miền thật, không có `localhost`, không có `http://` trần. Đo cả trong tiến trình đang chạy. Dev cũng không phải `*` |
| BM-023 | Trung bình | Bí mật lưu trong DB (**mật khẩu SMTP, khóa R2**) giải mã hỏng thì **im lặng tuyệt đối**: `_decrypt` nuốt *mọi* lỗi trả chuỗi rỗng, `get()` lặng lẽ rơi về `.env`, `.env` trống thì trả rỗng. Hậu quả nặng nhất không phải mail chết mà là **sao lưu tự động lên R2 chết mà không ai biết** — phát hiện ra đúng vào lúc cần khôi phục | **Mở.** Bằng chứng: `core/app_settings.py:55-59` (`except (InvalidToken, Exception): return ""`) + `:95-100` (nhánh `if dec:` rơi về `.env`). Phát hiện khi trả lời câu hỏi về xoay `JWT_SECRET` |
| BM-024 | Trung bình | **prod và dev dùng CHUNG một `JWT_SECRET`.** Khóa này là **khóa Fernet** mã hóa mật khẩu SMTP + hai khóa R2 trong `tab_setting` và mật khẩu hộp thư — mà prod với dev lại nằm **trên cùng một máy chủ MySQL**. Ai vào được dev thì giải mã được bí mật của prod, dù không mở nổi một phiên đăng nhập nào của prod | **ĐÃ VÁ 14/09/2026 — đổi khóa của DEV, prod không đụng tới.** Đã đo lại sau khi đổi: *prod và dev dùng chung khóa: **KHÔNG***. Ba bí mật trong `tab_setting` của dev đã mã hóa lại bằng khóa mới và **khớp bản gốc**; tiến trình dev đang chạy đọc được cả ba; prod vẫn đọc được bí mật của prod và **không hề restart**. Vế **ký vé giả** vốn đã bị chốt phiên `_check_session` (bao-CR-360 P3a) chặn — xác nhận trên chính container prod đang chạy. **Không có mã nguồn nào đổi** — đây là việc hạ tầng |
| BM-025 | **Cao** | `POST /api/attachments/register` **không kiểm tệp đó của ai.** Nó chỉ kiểm quyền trên **phiếu đích**, rồi gắn thẳng bất kỳ `file_id` nào được gửi lên. `file_id` là số nguyên tăng dần nên dò cạn được. Ai có `create` trên một entity đính kèm bất kỳ — tức gần như **mọi tài khoản**, vì ai cũng lập được yêu cầu mua hàng — thì gắn tệp của người khác vào phiếu nháp của mình rồi tải về: **đọc được mọi tệp trong hệ**, kể cả đính kèm riêng tư của `document_version` | **ĐÃ VÁ (bao-CR-408, 15/09/2026) — chưa commit, chưa deploy.** `register_files` hỏi chủ sở hữu trước: id nào không phải tệp mình tải lên thì **403 cả lượt**, id đã có dây thì bỏ qua im lặng (bấm Lưu hai lần không thành lỗi cứng). Lòi ra **cửa gắn thứ hai cùng lỗ**: `ticket/service._register_files`. Cả ba nơi gắn tệp (`ticket` · `comment` · `forum`) nay gọi chung `attachment/service.select_attachable_ids`. Bằng chứng cũ: vòng `for fid in data.file_ids` chỉ `db.get(StoredFile, fid)` rồi `db.add(FileLink(...))`. **ĐÃ CHỨNG MINH BẰNG BÀI CHẠY THẬT** (14/09/2026): tài khoản chỉ có `purchase_request` phạm vi `own` gắn được tệp `document_version` của người khác rồi đi qua `_get_file_with_permission(..., "download")` trót lọt |
| BM-026 | **Cao** | `/api/auth/avatar` và `/api/employees/{id}/avatar` **không kiểm gì cả** — không đuôi tệp, không kích thước, không nội dung. Bất kỳ tài khoản đăng nhập nào tải lên **bất kỳ thứ gì** tới trần 100MB của nginx và nhận về một URL công khai. Hệ thống thành nơi chứa tệp miễn phí, và nội dung độc hại được phát từ tên miền của công ty | **ĐÃ VÁ (bao-CR-408, 15/09/2026) — chưa commit, chưa deploy.** Bảng `DIRECT_FILE_POLICY` trong `core/file_registry.py` khai luật cho mọi cửa **không đi qua `FileLink`**; `create_stored_file` gọi `upload_guard.guard_upload` nên đuôi + dung lượng + byte đầu đều bị hỏi. Tham số `content_type` đã **bỏ khỏi chữ ký** của `create_stored_file` / `set_user_avatar` — không còn đường nào truyền lời khai vào. Bằng chứng cũ: `auth/controller.py:289-296` + `employee/controller.py:93-118` |
| BM-027 | Trung bình | Ba cửa ảnh chỉ tin **`content_type` do máy khách tự khai**: `/api/auth/signature`, `/api/employees/{id}/signature` kiểm `startswith("image/")` (nên `image/svg+xml` lọt), còn `/api/help/upload-image` **khai thẳng `svg` trong danh sách trắng**. **SVG là tài liệu chạy được JavaScript.** Hôm nay tệp đáp xuống `storage.degoholding.vn` nên chưa lấy được token (token nằm trong `localStorage`, khóa theo origin) — nhưng **ghép với BM-023** thì khóa R2 hỏng trong im lặng, `upload_fileobj` lặng lẽ rơi về `uploads/` và cùng tệp đó được phát từ `/api/uploads/...` — **cùng origin với ứng dụng**, thành XSS lưu trữ đọc sạch token | **ĐÃ VÁ (bao-CR-408, 15/09/2026) — chưa commit, chưa deploy.** `svg` không còn trong bảng chính sách nào (có bài kiểm quét **cả hai** bảng), và đổi đuôi thành `.png` cũng không lọt vì `guard_upload` đọc **byte đầu**. ⚠️ Sổ ghi *"ba cửa"* là **thiếu**: census `UploadFile` ra **cửa thứ sáu** — `employee/controller.py::upload_id_image` (ảnh CCCD) mang đúng lỗ đó, nay dùng `direct_policy("id_image")`. Bằng chứng cũ: `auth/controller.py:302-316`, `employee/controller.py:120-140`, `help_center/controller.py:20` (`IMAGE_EXTS` có `"svg"`) + `:140-158`. Đã đo: prod `r2_public_url = https://storage.degoholding.vn` (tên miền anh em của `thumua`/`erp`), R2 đang sẵn sàng; `grep set_cookie` toàn backend **không ra dòng nào** |
| BM-028 | Thấp | `content_type` do máy khách khai được **lưu nguyên** vào `tab_file.content_type`, đặt làm `ContentType` của đối tượng trên R2, rồi dùng lại làm `media_type` của hồi đáp `/view` và `/download`. Không đối chiếu với đuôi tệp, không đọc mấy byte đầu. Một tệp `.png` khai `text/html` được phục vụ như HTML | **ĐÃ VÁ (bao-CR-408, 15/09/2026) — chưa commit, chưa deploy.** `tab_file.content_type` nay suy từ **đuôi tệp** (`upload_guard.content_type_of`), và đuôi chỉ đứng vững sau khi byte đầu đã khớp. Lời khai của máy khách **không còn được đọc ở bất kỳ cửa nào**. ⚠️ Cố ý chỉ soi byte với **ảnh · PDF · video**: `.doc`/`.xls` đời thật thường là RTF/HTML bên trong, mà chúng không bao giờ hiện trong khung (`INLINE_VIEW_TYPES`). Bằng chứng cũ: `attachment/controller.py::_store_one` (`content_type=f.content_type or ""`) + `view_one`. Giảm nhẹ vẫn giữ: `/view` có `nosniff` + CSP `sandbox` + `INLINE_VIEW_TYPES` cố ý **loại SVG** |
| BM-029 | Thấp | **Zip-slip**: `/api/attachments/chain/zip` dựng đường dẫn trong tệp nén bằng **tên tệp thô của máy khách** — `f"{src}/{doc_type}/{f.filename}"`. Tên chứa `../` thì bộ giải nén nào không tự chống sẽ ghi ra ngoài thư mục đích, trên **máy người dùng** | **ĐÃ VÁ (bao-CR-408, 15/09/2026) — chưa commit, chưa deploy.** `zip_entry_name()` (hàm mức module, để bài kiểm gọi thẳng được) chạy `safe_name()` rồi quy `.`/`..`/rỗng về `"file"`; vòng khử trùng tên cũng tách trên tên **đã sạch**. Bằng chứng cũ: `attachment/controller.py::chain_zip`. Đã chứng minh tên tệp thô sống sót: gửi `'../../../../evil.pdf'` thì `UploadFile.filename` giữ nguyên cả chuỗi; `safe_name()` chỉ làm sạch **khóa lưu trữ**, không đụng tới `tab_file.filename` |
| BM-030 | Thấp | Cụm **độ bền đầu vào** của khâu tải lên, ba thứ: (1) tên tệp dài hơn **255** ký tự rơi thẳng xuống MySQL → **500 chứ không phải 422** (đúng họ `duoc-CR-316`; `tab_file.filename` là `String(255)` mà đường tải lên **không có schema Pydantic nào**); (2) `files: list[UploadFile]` **không có trần số lượng** — một request gửi mấy nghìn tệp; (3) chốt dung lượng chạy **sau khi đã nhận hết thân request**, nên lớp chặn thật duy nhất là `client_max_body_size 100m` của nginx | **VÁ 2/3 (bao-CR-408, 15/09/2026) — chưa commit, chưa deploy.** (1) `ensure_filename_ok` → **422** khi tên rỗng hoặc quá `MAX_FILENAME_LEN = 255`; (2) `ensure_batch_ok` → **422** khi quá `MAX_FILES_PER_REQUEST = 20`. (3) **CÒN MỞ:** chốt dung lượng vẫn chạy sau khi đã nhận hết thân request — chặn trước phải làm ở tầng ASGI/nginx, ngoài phạm vi CR này. Bằng chứng cũ: `attachment/model.py` (`filename: String(255)`), `docker/nginx.prod.conf` + `nginx.erp.prod.conf` (`100m`), `nginx.help.prod.conf` (`35m`). Đã chứng minh: tên tệp **304 ký tự** đi qua `UploadFile` không ai cản |
| BM-031 | Thấp | `POST /api/attachments/upload-file` với `entity=comment` hoặc `entity=forum_post` **không kiểm quyền một chút nào** — `_check` gặp `parent == "__self__"` là trả về sớm trước khi hỏi `user_has_permission`. Thêm nữa, tệp tải lên mà không bao giờ được gắn vào đâu (`/register` không gọi) thì **nằm lại vĩnh viễn**: `_delete_file_if_orphan` chỉ chạy khi có ai xóa một liên kết | **ĐÃ VÁ (bao-CR-408, 15/09/2026) — chưa commit, chưa deploy.** Chốt **không** phải một khóa RBAC: `comment` không có trong `ENTITIES`, còn khóa `forum_post` là quyền **kiểm duyệt** — đòi nó thì người dùng thường hết bình luận được. Chốt thật là **trần tệp-chưa-gắn**: `ensure_orphan_quota` → **429** khi quá `MAX_PENDING_ORPHANS = 50`, cộng việc định kỳ `attachment.purge_orphans` (4h10 hằng ngày) xóa tệp mồ côi quá `ORPHAN_KEEP_DAYS = 7`. ⚠️ Việc dọn lọc theo `file_key LIKE '%/attachment/%'` — ảnh đại diện, tệp trợ lý AI, tệp xuất, ảnh HDSD **vốn không có dây theo thiết kế**, quét cả là xóa nhầm; có bài kiểm canh đúng chỗ đó. Bằng chứng cũ: `attachment/controller.py::_check`, `core/file_registry.py` |

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

### BM-016 — Không có chính sách mật khẩu — ĐÃ VÁ (bao-CR-405)

Ba cửa đặt mật khẩu, không cửa nào kiểm gì: `auth/schema.py:20` (`ResetPasswordInput`),
`user/schema.py:9` (tạo tài khoản), `user/schema.py:14` (quản trị đặt lại). Cả ba khai
`password: str` trần — không `min_length`, không kiểm độ mạnh, không cấm trùng tên đăng nhập.

Hai điều kiện làm nó dễ khai thác hơn vẻ ngoài: tên đăng nhập là **mã nhân viên** (đoán được
từ danh bạ), và tài khoản demo đặt mật khẩu **bằng đúng mã tài khoản**.

**Quyết định 14/09/2026 (đại ca) — lần 1: chấp nhận rủi ro.** Lý do: hệ nội bộ, **không ai tự
đăng ký** — tài khoản do quản trị cấp; và trần tần suất đăng nhập theo IP thật (BM-004 đã vá)
đã chặn được dò tự động, tức là con đường khai thác chính đã đóng.

**Điều kiện đảo lại quyết định** — ghi ra để lần sau khỏi phải cãi: hệ mở cho người ngoài công
ty tự đăng nhập (nhà cung cấp), hoặc mở cổng tự đăng ký, hoặc có một lần rò mật khẩu thật.

#### Vì sao ĐẢO LẠI ngay trong ngày (bao-CR-405, 14/09/2026)

Giữ nguyên hai dòng trên chứ **không xóa** — quyết định cũ có lý của nó, và lý do đảo mới là
thứ đáng đọc. Rà để vá thì lộ ra hai điều mà lần ghi sổ đầu chưa thấy:

1. **Năm cửa, không phải ba.** Census `hash_password` toàn `app/modules` ra thêm
   `auth/controller.py:246` (`/auth/change-password` — **nhận `dict` trần, không có lược đồ
   Pydantic nào**, chỉ đếm đủ 6 ký tự) và `employee/controller.py:236`
   (`/employees/{id}/set-password` — đòi **4** ký tự). Hai cửa này không nằm trong ba cửa đã
   ghi, nên phần "chấp nhận" hôm sáng chấp nhận một bức tranh nhỏ hơn sự thật.
2. **Trần tần suất không đỡ được lỗ thật.** Lý do "đã chặn dò tự động" chỉ đúng với kẻ **thử
   nhiều lần**. Lỗ thật ở đây là mật khẩu đặt **bằng đúng mã nhân viên**, mà mã nhân viên
   chính là tên đăng nhập: kẻ đoán chỉ cần **một** lần thử, `LOGIN_RATE_LIMIT` không bao giờ
   chạm tới. Điều kiện đảo số 3 ("có một lần rò mật khẩu thật") vì thế không cần đợi — nó
   tương đương một lần mở danh bạ.

**Cách vá.** `backend/app/core/password_policy.py` — một hàm `validate_password(raw, *,
username, email)` gọi ở **cả năm** cửa. Luật: ≥ 8 ký tự · có cả chữ lẫn số · ≤ 72 **byte**
(bcrypt cắt âm thầm phần dư, hai mật khẩu khác nhau sẽ đăng nhập được vào nhau) · không
khoảng trắng đầu/cuối · không nằm trong danh sách phổ biến · **không chứa mã nhân viên hoặc
email của chính tài khoản đó** (bỏ dấu + không phân biệt hoa thường).

Luật cố ý **không** đặt trong Pydantic schema: luật mạnh nhất cần biết mã nhân viên + email
của tài khoản đang đặt, mà schema không nhìn thấy hai thứ đó. Và cố ý **không** gọi trong
`hash_password`: các script seed đặt mật khẩu demo bằng mã tài khoản để dựng dữ liệu thử,
siết ở tầng băm là chết seed mà không thêm an toàn nào cho hệ thật.

⚠️ **Tài khoản CŨ không bị động tới.** Mật khẩu yếu đã đặt trước 14/09 vẫn đăng nhập được —
chính sách chỉ gác lúc ĐẶT. Muốn quét sạch thì phải bắt đổi mật khẩu ở lần đăng nhập kế
tiếp, đó là việc riêng, chưa làm.

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

⚠️ **ĐÃ ĐO — điều kiện KHÔNG đúng.** Ngày 14/09/2026, theo lệnh của đại ca, em vào VPS đo, chỉ
in CÓ/KHÔNG:

```
BM-018 | co dong JWT_SECRET trong .env       : CO
BM-018 | JWT_SECRET dang la change_me_please : KHONG
BM-018 | do dai >= 32 ky tu                  : CO
```

Đo **hai lớp**: trong `.env` và trong **tiến trình đang chạy** (`docker exec <api> python -c
"from app.core.config import settings; ..."`). Phải đo cả hai vì `.env` trôi khỏi thứ container
đã nạp là chuyện thường — container khởi động từ một bản `.env` cũ thì tệp trên đĩa nói một
đằng, hệ thật chạy một nẻo. Cả hai lớp đều trả cùng kết quả. Dev cũng không phải giá trị mặc
định.

Nên mức ở bảng hạ từ **Cao** *(có điều kiện)* xuống **Thấp**. Phần **còn mở** là chốt khởi
động ở mục dưới — nó không vá hôm nay, nó canh cho những lần deploy sau.

⚠️ Nhưng lần đo này lòi ra một thứ khác, xem **BM-024**: prod và dev đang dùng **chung một**
khóa.

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

### BM-022 — CORS trên prod — ĐÃ ĐO, SẠCH

`main.py:125-131` bật `allow_credentials=True` cùng `allow_methods=["*"]` và
`allow_headers=["*"]`, với `allow_origins` đọc từ `.env` qua `config.py:166`.

Cấu hình này **đúng hay sai hoàn toàn phụ thuộc giá trị `CORS_ORIGINS` thật trên prod**. Nếu ở
đó là danh sách tên miền cụ thể thì không có vấn đề gì. Nếu là `*` thì dòng này lên mức **Cao**
— trình duyệt sẽ cho site bất kỳ gọi API kèm cookie/chứng danh của người đang đăng nhập.

**Đo ngày 14/09/2026 trên VPS — prod sạch:**

```
BM-022 | CORS_ORIGINS dung dau sao '*'                   : KHONG
BM-022 | co chua ky tu '*' o bat ky dau                  : KHONG
BM-022 | so origin duoc khai bao                         : 1
BM-022 | tien trinh dang chay: allow_credentials         : CO
  co origin cho thumua.degoholding.vn : CO
  co origin cho erp.degoholding.vn    : KHONG
  co origin tro ve localhost          : KHONG
  co origin dung http:// (khong TLS)  : KHONG
```

Đúng một origin, là tên miền thật, có TLS. Dev cũng không phải `*`.

⚠️ **Chỗ trông như lỗ mà không phải lỗ:** danh sách chỉ có `thumua.degoholding.vn`, không có
`erp.degoholding.vn` — tức giao diện v2 *không* nằm trong danh sách cho phép. Nó vẫn chạy được
vì **cả hai giao diện gọi API cùng nguồn (same-origin) qua nginx**, mà same-origin thì trình
duyệt không hỏi CORS. Nghĩa là dòng khai này chỉ ảnh hưởng tới lời gọi từ nguồn khác — và ở đó
nó đang **chặt hơn** mức cần, chứ không lỏng hơn. Để nguyên.

Dòng này **đóng bằng đo**, không cần mã.

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

### BM-024 — prod và dev dùng CHUNG một `JWT_SECRET`

Phát hiện 14/09/2026, **nhân tiện khi đo BM-018** — không phải thứ đi tìm. Cách đo: tính
`sha256` của khóa ở mỗi bên **ngay trên VPS**, so sánh **tại chỗ**, rồi chỉ mang về một chữ:

```
BM-024 | PROD va DEV dung CHUNG mot JWT_SECRET : CO
```

⚠️ Bản băm cũng **không được in ra** và không được mang về máy. Băm không phải là che: cả hai
bên đều là *một* giá trị, nên một bản băm lọt ra ngoài là một mục tiêu để dò.

#### Vế KHÔNG hở: ký vé giả

Điều đầu tiên phải hỏi là *"vậy lấy khóa của dev ký một cái vé `admin` rồi gõ vào prod thì
sao?"*. Câu trả lời là **không vào được**, và lý do là chốt phiên của bao-CR-360 P3a. Em xác
nhận **trên chính container prod đang chạy**, không phải đọc mã nguồn ở máy:

```
=== PROD dang chay co chot phien khong ===
  co ham _check_session                       : CO
  get_current_user co goi _check_session      : CO
  endpoint refresh co goi resolve_session/... : CO
```

`_check_session` đòi **ba** điều cùng lúc: vé phải mang `jti`; `ver` phải khớp
`tab_user.token_version` của prod; và `resolve_session(db, token_id, user.id)` phải tìm thấy
**một dòng phiên còn sống trong CSDL prod**. Vé ký từ dev có chữ ký đúng — nhưng `jti` của nó
là một số chưa từng tồn tại trong `tab_login_session` của prod, nên nó chết ở điều thứ ba.
Đường `refresh` cũng đi qua chốt đó, không có lối vòng.

Đây đúng là thứ đã trả công cho CR-360: nó biến *"khóa ký là đủ"* thành *"khóa ký chưa đủ"*.

#### Vế HỞ THẬT: vai trò Fernet

Khóa này không chỉ ký vé. Nó còn **mã hóa bí mật nằm trong CSDL** (xem bảng bốn vai trò ở
BM-018): mật khẩu SMTP, **hai khóa R2**, mật khẩu hộp thư. Và prod với dev **ở chung một máy
chủ MySQL**.

Ghép hai điều đó lại: ai cầm được khóa ở phía dev thì **giải mã được bí mật của prod**, mà
không cần mở nổi một phiên đăng nhập nào của prod. Trong đó có khóa R2 — tức là **chỗ để sao
lưu CSDL**.

Dev là nơi dễ vào hơn prod theo đúng thiết kế: nó có dữ liệu đầy đủ để thử nghiệm, nhiều người
đụng vào, và không ai canh nó như canh prod. Dùng chung khóa nghĩa là **mức bảo vệ của bí mật
prod bị kéo xuống bằng mức bảo vệ của dev**.

#### ĐÃ VÁ 14/09/2026 — đổi khóa của DEV, không đụng khóa prod

⚠️ **Tuyệt đối không xoay khóa prod** — bốn vai trò, hỏng trong im lặng, thứ chết đầu tiên là
sao lưu (BM-018 + BM-023). Việc làm nằm **hoàn toàn ở phía dev**; prod không restart, không
deploy, không đụng một dòng nào.

**Thứ tự đã chạy** (thứ tự này là bắt buộc, xem lý do ở dưới):

1. **Khảo sát trước** — dev có đúng **3** bí mật trong `tab_setting` (`smtp_password`,
   `r2_access_key_id`, `r2_secret_access_key`), cả ba giải mã tốt bằng khóa cũ; `tab_mailbox`
   **rỗng** nên không có mật khẩu hộp thư nào phải lo.
2. **Sao lưu** `.env.dev` và hai bảng `tab_setting` + `tab_mailbox` của `procurement_dev` vào
   `~/proc_backups/` (`env.dev_truoc_doi_khoa_*.bak` và `dev_setting_mailbox_truoc_doi_khoa_*.sql.gz`,
   quyền `600`).
3. **Mã hóa lại TRƯỚC, đổi `.env` SAU.** Một kịch bản chạy trong container dev *đang còn giữ
   khóa cũ*: giải mã từng bí mật bằng khóa cũ → mã lại bằng khóa mới → ghi xuống. Kịch bản
   **dừng lại** nếu có dòng nào không giải mã được, và tự kiểm lại sau khi ghi: giải mã bằng
   khóa mới phải ra **đúng bản gốc**. Kết quả: `3/3` khớp.
4. **Ghi khóa mới vào `.env.dev`** — bằng một đoạn Python đọc-sửa-ghi, và nó **dừng nếu số dòng
   `JWT_SECRET=` khác 1** (sửa nhầm hai dòng, hoặc không sửa dòng nào, đều là hỏng im lặng).
5. **Dựng lại** `api` + `celery-worker` + `celery-beat` của dev bằng
   `docker compose -f docker-compose.dev.yml --env-file .env.dev up -d`.
6. **Nghiệm thu** — chỉ in CÓ/KHÔNG: tiến trình dev đọc được cả 3 bí mật · *prod và dev dùng
   chung khóa: **KHÔNG*** · khóa dev không phải mặc định và ≥ 32 ký tự · **prod vẫn đọc được bí
   mật của prod** và container prod không hề restart. Log `api` + `celery-worker` dev không một
   dòng lỗi; `/docs` trả 200.
7. **Dọn** tệp khóa tạm (`shred`) và kịch bản, cả trên host lẫn trong container. Giữ lại hai
   bản sao lưu.

⚠️ **Vì sao thứ tự bước 3 trước bước 4 là bắt buộc:** đổi `.env` trước thì khóa cũ mất, mà bí
mật trong DB vẫn đang mã bằng khóa cũ — không còn gì giải mã được chúng nữa. Và vì **BM-023**,
hỏng kiểu đó **không kêu một tiếng nào**: `_decrypt` trả chuỗi rỗng, `get()` lặng lẽ rơi về
`.env`, mọi thứ trông như bình thường cho tới lần cần sao lưu R2.

⚠️ **`docker compose restart` KHÔNG đủ** — biến môi trường được nạp lúc **tạo** container, nên
`restart` chạy lại đúng container cũ với đúng khóa cũ. Phải `up -d` để dựng lại.

**Hệ quả đã biết, chấp nhận:** mọi phiên đăng nhập trên dev bị đá ra (vé cũ ký bằng khóa cũ).
Ở dev thì phiền một lần, không sao.

**Không có mã nguồn nào đổi** — đây là việc hạ tầng, không cần CR, không cần deploy.

---

## 2b. Đợt rà khâu TẢI TỆP LÊN (14/09/2026) — BM-025 … BM-031

> ⚠️ **ĐÃ VÁ NGÀY 15/09/2026 — `bao-CR-408`** (chưa commit, chưa deploy). Bảy mục con dưới đây
> giữ nguyên câu chữ **lúc phát hiện**, kể cả chữ *"Trạng thái: Mở"* — đó là bản ghi hiện
> trường, đừng sửa lại cho khớp hiện tại. Trạng thái hôm nay đọc ở **bảng §2**, cách vá đọc ở
> **Việc 6**. Ba chỗ bản vá đi **khác** với hướng ghi trong §2b, đã giải thích ở Việc 6:
> (1) chính sách cho cửa tải trực tiếp nằm ở bảng **riêng** `DIRECT_FILE_POLICY`, không thêm
> dòng vào `FILE_POLICY`; (2) chốt của BM-031 là **trần tệp-chưa-gắn 429**, không phải một
> khóa RBAC; (3) vế "đo dung lượng trước khi nhận hết thân request" của BM-030 **vẫn còn mở**.

Đợt này soát **một khâu**, không soát một module. Phân biệt đó là điều quan trọng nhất rút ra
được: module `attachment` — chỗ ai cũng nghĩ tới đầu tiên — hóa ra là chỗ **làm kỹ nhất**, còn
lỗ nặng lại nằm ở những cửa tải lên **đi vòng qua nó**.

**Cách rà:** đếm census `UploadFile` trên toàn backend ra **12 tệp**, rồi soát từng cửa theo
sáu câu hỏi cố định — *ai gọi được · tệp gì được nhận · to bao nhiêu được nhận · tên tệp đi về
đâu · tệp đáp xuống origin nào · ai đọc lại được nó*. Ba trong sáu câu đó là những câu mà một
lần rà "đọc mã module `attachment`" không bao giờ đặt ra.

### Kiến trúc đính kèm, nói cho gọn

`tab_file` (**StoredFile** — vật thể thật trên kho) ↔ `tab_file_link` (**FileLink** — dây buộc
tệp vào `entity` + `entity_id`). Một tệp mang nhiều dây; xóa dây chỉ xóa tệp khi nó thành mồ
côi (`_delete_file_if_orphan`). Quyền gác ở **hai lớp** trong `_check`: (1) `user_has_permission`
trên entity cha, (2) `ensure_in_scope` trên **đúng bản ghi cha đó**. `entity_id = None` — đường
tải lên tạm — **bỏ qua lớp 2**.

`FILE_POLICY` ở `core/file_registry.py` khai `entity → (cha, đuôi cho phép, trần MB)`. Entity
không có trong bảng đó thì bị từ chối. **`PRIVATE_ENTITIES = {"document_version"}`** — API trả
`url: ""`, muốn xem phải đi qua `GET /api/attachments/{link_id}/download`.

### Những chốt ĐANG LÀM ĐÚNG — ghi lại để đừng ai "dọn" mất

Bốn thứ dưới đây không phải may mà có; ai refactor khu này mà gỡ chúng là mở lại lỗ:

- **`INLINE_VIEW_TYPES` + ba header ở `/view`** — danh sách trắng kiểu tệp xem-trong-khung
  (**cố ý loại SVG**), kèm `X-Content-Type-Options: nosniff`, `Content-Security-Policy: sandbox;
  default-src 'none'; img-src 'self' data:`, `Cache-Control: no-store`. Đây là chốt tốt nhất
  trong cả khu. Nghịch lý đã ghi ở BM-019: cửa xem một tệp đính kèm gác kỹ hơn cả ứng dụng.
- **`safe_name()` cho khóa lưu trữ** — bỏ đường dẫn, bỏ CR/LF/tab, đổi khoảng trắng. Nó bảo vệ
  **khóa**, và chỉ khóa; `tab_file.filename` vẫn giữ tên thô của máy khách (đó là BM-029/030).
- **Hai lớp của `_check`** — quyền trên entity *và* phạm vi trên đúng bản ghi. Khuôn này đúng,
  vấn đề là `/register` **không đi qua nó đủ xa** (BM-025).
- **Trợ lý AI đọc byte đầu để nhận dạng tệp** thay vì tin `content_type` — cách đúng đã có sẵn
  trong nhà, chỉ là các cửa khác chưa dùng (BM-028).

### BM-025 — `/register` gắn tệp mà không hỏi tệp của ai

**Mức: Cao. Trạng thái: Mở.** Dòng nặng nhất của đợt.

```python
@router.post("/register")
def register_files(data: RegisterIn, db=..., user=...):
    _deny_comment(data.entity)
    _check(db, user, data.entity, "manage", data.entity_id)   # quyền trên PHIẾU ĐÍCH
    ...
    for fid in data.file_ids:
        f = db.get(StoredFile, fid)                            # ← không hỏi tệp của ai
        if not f:
            continue
        lk = FileLink(file_id=fid, entity=data.entity, entity_id=data.entity_id, ...)
```

Mọi câu hỏi về quyền ở đây đều hỏi về **phiếu đích** — thứ kẻ tấn công **tự lập ra**, nên đương
nhiên họ có đủ quyền trên nó. Không câu nào hỏi về **tệp**. `file_id` là số nguyên tự tăng, dò
từ 1 là cạn.

Đường khai thác đủ ba bước, không cần quyền đặc biệt nào:

1. Lập một yêu cầu mua hàng nháp của chính mình (ai cũng có `purchase_request.create`).
2. `POST /api/attachments/register` với `entity=purchase_request`, `entity_id=<phiếu của mình>`,
   `file_ids=[1,2,3,…]`.
3. `GET /api/attachments/{link_id}/download` — vì dây buộc nay trỏ vào **phiếu của mình**, lớp
   kiểm quyền lúc tải về nhìn vào phiếu đó và **cho qua**.

⚠️ **`PRIVATE_ENTITIES` không cứu được gì ở đây.** Nó khóa đường `url` của `document_version`,
nhưng đường `download` thì kiểm theo **dây mới** chứ không theo dây cũ — tệp riêng tư vừa mọc
thêm một dây công khai.

**Đã chứng minh bằng bài chạy thật** (pytest, 14/09/2026, tệp đo đã xóa sau khi đo xong): dựng
một `StoredFile` gắn `document_version`, cấp cho kẻ tấn công **đúng** `purchase_request` phạm vi
`own`, gọi `register_files` → trả về *"Đã gắn file"*, rồi `_get_file_with_permission(..., "download")`
trả về đúng tệp đó. Không phải suy luận từ mã nguồn.

**Hướng vá (chưa làm, chờ lệnh):** trước khi gắn, đòi tệp phải **của chính người gọi**
(`StoredFile.created_by == user.id`) **và chưa có dây nào** — tức chỉ gắn được tệp vừa tải lên ở
đường tạm. Muốn nới cho ca dùng lại tệp cũ thì phải kiểm quyền trên **dây hiện có**, đừng nới
bằng cách bỏ chốt. ⚠️ Vá kiểu này **đụng luồng đang chạy**: phải rà những chỗ hệ thống tự gắn
tệp hộ người dùng (sao chép phiếu, chuyển chứng từ) kẻo chặn nhầm.

### BM-026 — hai cửa ảnh đại diện không kiểm một thứ gì

**Mức: Cao. Trạng thái: Mở.**

```python
@router.post("/avatar")
def update_avatar(file: UploadFile = File(...), user=..., db=...):
    url = set_user_avatar(db, user, fileobj=file.file, filename=file.filename or "avatar",
                          content_type=file.content_type or "", actor_id=user.id)
```

Không đuôi, không dung lượng, không nội dung. Cửa nhân sự (`/api/employees/{id}/avatar`) là bản
chép của đúng đường này. Đặt cạnh `_store_one` — nơi kiểm cả đuôi lẫn trần MB theo `FILE_POLICY`
— thì thấy rõ đây không phải quyết định thiết kế mà là **cửa mọc ra ngoài bảng chính sách**:
`FILE_POLICY` không có dòng nào cho ảnh đại diện, vì đường này không đi qua `attachment`.

Hệ quả gần: bất kỳ tài khoản nào biến hệ thống thành kho chứa tệp tới trần 100MB/lượt, không có
chốt số lượt. Hệ quả xa: nội dung bất kỳ được phát từ tên miền của công ty.

**Hướng vá:** đưa hai cửa này về **cùng một chính sách** với `attachment` — thêm entity
`avatar` vào `FILE_POLICY` (`_IMG`, trần vài MB) và gọi chung một hàm kiểm. Đừng chép luật kiểm
vào từng controller: cửa thứ ba sẽ mọc ra và lại quên.

### BM-027 — `image/*` do máy khách tự khai, và SVG chạy được JavaScript

**Mức: Trung bình. Trạng thái: Mở.**

```python
if not (file.content_type or "").startswith("image/"):
    raise HTTPException(400, "Chữ ký phải là file ảnh (PNG, JPG…).")
```

Câu này kiểm **lời khai của máy khách**, không kiểm tệp. `image/svg+xml` bắt đầu bằng `image/`
nên đi qua, và một tệp SVG là một tài liệu XML **chạy được `<script>`**. Trung tâm HDSD còn
thẳng thắn hơn: `IMAGE_EXTS` ở `help_center/controller.py:20` **khai `svg` trong danh sách
trắng**.

**Đã đo hai thứ quyết định mức độ, không đoán:**

- Prod `r2_public_url = https://storage.degoholding.vn`, R2 đang sẵn sàng — tệp đáp xuống một
  **tên miền anh em** của `thumua` / `erp`, không phải cùng origin.
- **Toàn backend không đặt một cookie nào** (`grep set_cookie` không ra dòng nào); token nằm
  trong `localStorage` (`frontend-v2/src/core/auth/auth-store.ts`), mà `localStorage` **khóa
  theo origin**.

Nên hôm nay đây là chỗ **phát tán nội dung độc hại từ tên miền công ty** (lừa đảo, tệp độc),
chưa phải trộm token. Mức **Trung bình**.

⚠️ **Nhưng nó ghép với BM-023 thành một thứ khác hẳn.** `upload_fileobj` chỉ dùng R2 khi
`_r2_ready()` — cần đủ endpoint + khóa + `public_url`; **thiếu một cái là nó lặng lẽ ghi vào
`uploads/`** và trả về `/api/uploads/<key>`, đường được phục vụ bởi `app.mount("/api/uploads",
StaticFiles(...))` ở `main.py:134` — **cùng origin với ứng dụng, không kiểm quyền** (đó chính là
BM-021). Mà BM-023 nói rằng khóa R2 giải mã hỏng thì `r2_access_key_id` thành `""` **trong im
lặng**. Ghép lại: một lần hỏng khóa không ai biết → cùng tệp SVG đó chuyển từ tên miền anh em
sang **cùng origin** → XSS lưu trữ đọc sạch `localStorage`. Ba dòng BM-021, BM-023, BM-027 mỗi
dòng đứng riêng đều "Thấp/Trung bình"; đứng cùng nhau thì không.

**Hướng vá:** bỏ `svg` khỏi mọi danh sách trắng ảnh, và kiểm bằng **đuôi tệp + byte đầu** thay
vì `content_type`. Nếu nghiệp vụ thật sự cần SVG (logo) thì phải đi qua bộ làm sạch — hệ đã có
`sanitize_html` cho Trung tâm HDSD, nhưng SVG cần bộ riêng.

### BM-028 — `content_type` là lời khai, không phải sự thật

**Mức: Thấp. Trạng thái: Mở.** Chuỗi máy khách gửi lên được lưu nguyên vào `tab_file.content_type`,
đặt làm `ContentType` của đối tượng R2, rồi dùng lại làm `media_type` của hồi đáp `/view` và
`/download`. Không có chỗ nào đối chiếu nó với đuôi tệp, và không có chỗ nào đọc mấy byte đầu.

Mức Thấp **nhờ** hai chốt của `/view` (danh sách trắng + `nosniff` + CSP `sandbox`) đứng chặn ở
cửa nguy hiểm nhất. Nó là **nợ có lãi**: ai nới danh sách trắng đó, hoặc thêm một cửa xem tệp
mới mà quên chép ba header, là dòng này nhảy mức ngay.

### BM-029 — zip-slip ở `/chain/zip`

**Mức: Thấp. Trạng thái: Mở.** Đường dẫn của mỗi mục trong tệp nén dựng từ **tên thô**:

```python
path = f"{src}/{lk.doc_type or 'khac'}/{f.filename}"
zf.writestr(path, download_bytes(f.file_key))
```

Đã chứng minh tên thô sống sót qua `UploadFile`: gửi `'../../../../evil.pdf'` thì
`UploadFile.filename` giữ nguyên cả chuỗi (chỉ **khóa lưu trữ** được `safe_name()` làm sạch, còn
`tab_file.filename` giữ bản gốc). Nạn nhân là **máy người dùng** mở tệp nén, không phải máy chủ
— và bộ giải nén hiện đại phần lớn tự chống. Vá: chạy `safe_name()` thêm một lần khi dựng đường
dẫn trong tệp nén.

### BM-030 — cụm độ bền đầu vào

**Mức: Thấp. Trạng thái: Mở.** Ba thứ cùng họ:

- **Tên tệp > 255 ký tự → 500, không phải 422.** Đúng họ `duoc-CR-316`. Nặng hơn ca nhân sự ở
  một điểm: đường tải lên **không có schema Pydantic nào cả**, `UploadFile` đi thẳng từ HTTP
  xuống `StoredFile.filename` là `String(255)`. Đã chứng minh tên **304 ký tự** đi qua không ai
  cản. ⚠️ `test/backend` chạy SQLite nên bài kiểm nào ghi xuống DB rồi khẳng định là **xanh
  giả** — kiểm ở tầng chặn, đừng tin DB.
- **Không có trần số tệp mỗi lượt.** `files: list[UploadFile]` nhận bao nhiêu cũng được.
- **Chốt dung lượng chạy sau khi đã nhận hết thân request** (`f.file.seek(0, 2)` rồi mới so với
  `max_mb`). Nghĩa là trần `max_mb` bảo vệ **ổ đĩa**, không bảo vệ **băng thông và RAM**; lớp
  chặn thật duy nhất là `client_max_body_size` của nginx (`100m`, riêng Help Center `35m`).

### BM-031 — `__self__` trả về sớm, và tệp mồ côi không ai dọn

**Mức: Thấp. Trạng thái: Mở.** `_check` gặp entity khai cha là `__self__` (`comment`,
`forum_post`) thì **trả về trước khi hỏi quyền**:

```python
if parent == "__self__":
    return exts, max_mb
```

Đây là **cố ý** — hai entity đó có chốt riêng `_check_comment` / `_check_forum` ở cửa **gắn**
tệp. Chỗ thủng là cửa **tải lên trần**: `POST /api/attachments/upload-file` với `entity=comment`
không đi qua chốt riêng nào cả, nên bất kỳ tài khoản đăng nhập nào cũng tải lên được. Ghép thêm:
tệp tải lên mà không bao giờ được `/register` gắn vào đâu thì **nằm lại vĩnh viễn** —
`_delete_file_if_orphan` chỉ chạy khi có ai **xóa một dây**, nên tệp chưa từng có dây thì không
có nhịp nào chạm tới nó.

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

### Việc 5 — đợt BM-016…BM-024 (14/09/2026)

Xếp theo **rẻ trước, và đo trước khi vá**.

**5.0 — ĐO TRƯỚC (0 dòng mã) — XONG 14/09/2026.** Hai dòng treo ở trạng thái *chưa đo* nay đã
đo trên VPS theo lệnh của đại ca, chỉ in CÓ/KHÔNG, không in giá trị:

- **BM-018** — prod **không** dùng khóa mặc định, dài ≥ 32 ký tự, đúng ở cả `.env` lẫn tiến
  trình đang chạy → hạ mức xuống **Thấp**, phần còn mở chỉ là chốt khởi động (5.1).
- **BM-022** — prod **không** phải `*`, đúng 1 origin là tên miền thật có TLS → hạ mức xuống
  **Thấp**, **đóng dòng, không cần mã**.
- ⚠️ Lòi ra **BM-024**: prod và dev dùng **chung một** `JWT_SECRET` → việc mới, mục **5.7**.

⚠️ Giữ nguyên luật đo cho những lần sau: **chỉ in CÓ/KHÔNG, tuyệt đối không in giá trị, và
không in cả bản băm** — bí mật in ra một lần là nó nằm lại trong lịch sử phiên, trong log,
trong ảnh chụp màn hình. So sánh hai bí mật thì băm **trên chính máy đó**, so **tại đó**, chỉ
mang về một chữ CÓ/KHÔNG. Và luôn đo **hai lớp**: tệp `.env` *và* tiến trình đang chạy — hai
thứ đó trôi khỏi nhau là chuyện thường.

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

**5.7 — Cho DEV một `JWT_SECRET` riêng (BM-024) — XONG 14/09/2026.** Làm **hoàn toàn ở phía
dev**, prod không đụng tới. Ba bí mật trong `tab_setting` của dev đã mã hóa lại bằng khóa mới
(3/3 khớp bản gốc), `.env.dev` đã đổi, ba container dev đã dựng lại, đo lại xác nhận **prod và
dev không còn dùng chung khóa** và **prod vẫn đọc được bí mật của prod**. Không đổi một dòng mã
nào. Chi tiết từng bước + hai bẫy (thứ tự bắt buộc, và `restart` không nạp lại biến môi trường)
ghi ở mục **BM-024** trong §2.

### Việc 6 — đợt BM-025…BM-031, khâu tải tệp lên — **XONG 15/09/2026 (`bao-CR-408`)**

Gộp cả bảy dòng vào **một CR** theo lệnh đại ca, chia năm commit. **Mã đã viết xong và xanh;
chưa commit, chưa deploy.** Sáu mục 6.0–6.5 dưới đây giữ nguyên kế hoạch lúc rà, mỗi mục ghi
thêm **bản vá thật đã làm gì** — ba chỗ đi khác kế hoạch, và lý do khác nằm ngay dưới chỗ đó.

**6.0 — Nền: một chốt dùng chung.** Tệp mới `backend/app/core/upload_guard.py` là nơi **duy
nhất** biết luật kiểm một tệp: `guard_upload(filename, fileobj, exts, max_mb)` trả
`(content_type, size)` sau khi đã hỏi đủ đuôi · rỗng · trần MB · **byte đầu**; kèm
`ensure_filename_ok` (422) và `ensure_batch_ok` (422). Mọi cửa gọi nó, không cửa nào tự kiểm.
Bảng luật cho những cửa **không đi qua `FileLink`** là `DIRECT_FILE_POLICY` +
`direct_policy(kind)` trong `core/file_registry.py`.

⚠️ **Vì sao KHÔNG thêm dòng vào `FILE_POLICY` như 6.2 dự tính:** `_policy_or_400` đọc thẳng
bảng đó để quyết định `entity` nào được nhận ở `/upload-file`. Thêm `avatar` vào đấy là mở
thêm một cửa mới (`entity=avatar` tải được tệp qua đường đính kèm), tức vá một lỗ đẻ một lỗ.
Hai bảng nói hai chuyện khác nhau thì phải là hai bảng.

**6.1 — Chốt chủ sở hữu cho `/register` (BM-025).** Việc gấp nhất của cả đợt, vì nó là **đọc
được mọi tệp trong hệ bằng một tài khoản thường**. Vá: đòi `StoredFile.created_by == user.id`
**và** tệp chưa có dây nào, trước khi tạo `FileLink`. ⚠️ **Phải rà luồng đang chạy trước khi
siết** — chỗ nào hệ thống tự gắn tệp hộ người dùng (sao chép phiếu, chuyển chứng từ) mà bị chặn
nhầm thì người dùng mất đính kèm và không ai biết tại sao.

> **Đã làm:** `own_file_ids` · `linked_file_ids` · `select_attachable_ids` ở
> `attachment/service.py`. `/register` **403 cả lượt** khi có id không phải của mình, nhưng
> **bỏ qua im lặng** id đã có dây — bấm Lưu hai lần là chuyện thường ngày, biến nó thành lỗi
> cứng thì người dùng mất phiếu. Rà luồng tự-gắn-hộ như cảnh báo ở trên thì lòi ra **cửa gắn
> thứ hai cùng lỗ**: `ticket/service._register_files`. `comment` và `forum` có kiểm nhưng mỗi
> nơi một bản chép; cả ba nay gọi chung `select_attachable_ids`.

**6.2 — Đưa hai cửa ảnh đại diện về chung chính sách (BM-026).** Thêm entity cho ảnh đại diện /
chữ ký vào `FILE_POLICY` và bắt cả bốn cửa (auth avatar · employee avatar · auth signature ·
employee signature) gọi **cùng một hàm kiểm**. Đừng chép luật kiểm vào từng controller — cửa
thứ năm sẽ mọc ra và lại quên đúng như bốn cửa này đã quên.

> **Đã làm:** `create_stored_file` **bỏ hẳn tham số `content_type`** — không còn đường truyền
> lời khai vào — và tự gọi `direct_policy(kind)` + `guard_upload`. Sáu cửa nay dùng chung:
> `auth` avatar/signature · `employee` avatar/signature · `help_center` ảnh bài ·
> `employee` **ảnh CCCD**. Câu cảnh báo ngay trên đã ứng nghiệm **trong chính đợt vá**: census
> `UploadFile = File(...)` ra **cửa thứ sáu** (`upload_id_image`) mà cả đợt rà 14/09 không thấy,
> vì nó không tên là avatar cũng không tên là signature. Đếm cửa bằng census, đừng đếm bằng trí nhớ.
> ⚠️ `sync_google_avatar` cũng đi qua chốt: ảnh tải từ Google được **nhận dạng bằng byte đầu**
> rồi mới đặt đuôi — trước đó nó tin `Content-Type` của một máy chủ bên ngoài.

**6.3 — Đuổi SVG và kiểm bằng byte đầu (BM-027 + BM-028).** Bỏ `svg` khỏi `IMAGE_EXTS` của Trung
tâm HDSD, đổi `startswith("image/")` thành kiểm **đuôi + byte đầu**. Mượn thẳng cách của
`/api/assistant/uploads` — nó đã làm đúng, không phải viết mới.

> **Đã làm:** `svg` không còn trong bảng nào (bài kiểm quét **cả hai** bảng, để người sau thêm
> lại "cho tiện" thì đỏ ngay). `sniff_family()` mượn đúng bảng byte của
> `assistant/attachments.detect_type`, nối thêm gif · bmp · mp4 · webm.
> ⚠️ **Cố ý chỉ soi byte với ảnh · PDF · video.** `.doc`/`.xls` đời thật rất hay là RTF hoặc
> HTML bên trong — bắt chúng khớp byte là **chặn tệp thật của người dùng** để đổi lấy gần như
> không gì, vì chúng không bao giờ hiện trong khung (`INLINE_VIEW_TYPES`). Rủi ro thật nằm ở
> nhóm **được trình duyệt dựng**, và nhóm đó đã bị soi đủ.

**6.4 — Ba chốt rẻ (BM-029 + BM-030).** `safe_name()` khi dựng đường dẫn trong tệp nén · trần độ
dài tên tệp trả **422** · trần số tệp mỗi lượt. Mỗi thứ vài dòng.

> **Đã làm:** `zip_entry_name()` (tách thành hàm mức module để bài kiểm gọi thẳng, không phải
> dựng cả tệp nén) · `MAX_FILENAME_LEN = 255` · `MAX_FILES_PER_REQUEST = 20`.
> **Vế thứ ba của BM-030 vẫn MỞ**: dung lượng vẫn đo sau khi đã nhận hết thân request. Chặn
> thật phải ở tầng ASGI hoặc nginx, không phải việc của CR này.

**6.5 — Dọn tệp mồ côi + gác cửa `upload-file` (BM-031).** Một việc định kỳ xóa `tab_file`
không dây quá N ngày, và đòi quyền tối thiểu ở cửa tải lên trần.

> **Đã làm:** việc định kỳ `attachment.purge_orphans` (Celery beat, 4h10 hằng ngày) xóa tệp mồ
> côi quá `ORPHAN_KEEP_DAYS = 7`, cộng `ensure_orphan_quota` → **429** ở
> `MAX_PENDING_ORPHANS = 50`.
> ⚠️ **"Đòi quyền tối thiểu" là hướng SAI, đã bỏ.** `comment` không có trong `ENTITIES` nên
> không có khóa nào để đòi; khóa `forum_post` là quyền **kiểm duyệt**, mà bình luận và đăng bài
> là việc mọi người đăng nhập đều làm chính đáng. Đòi một khóa RBAC ở đây là đổi một lỗ nhỏ
> lấy một tính năng chết. Trần tệp-chưa-gắn nói đúng thứ đang lo: **dùng hệ thống làm kho chứa**.
> ⚠️ Việc dọn lọc theo `file_key LIKE '%/attachment/%'`. Ảnh đại diện · tệp trợ lý AI · tệp
> xuất · ảnh HDSD **không có `FileLink` theo đúng thiết kế**, quét cả là xóa mất ảnh đại diện
> của cả công ty sau bảy ngày. Có bài kiểm canh riêng đúng chỗ đó.

⚠️ **Nhắc lại chỗ ghép nguy hiểm nhất của đợt này:** BM-027 hôm nay chỉ là *"phát tán nội dung
độc từ tên miền công ty"* **vì** R2 đang chạy. Ngày nào BM-023 kích hoạt (khóa R2 giải mã hỏng,
im lặng) thì `upload_fileobj` rơi về `uploads/`, tệp đáp xuống **cùng origin**, và nó thành XSS
lưu trữ. Nghĩa là **6.3 rẻ hơn nhiều so với việc chờ 5.2 và 5.5 làm xong** — vá nguồn trước,
đừng trông vào việc hai dòng kia được vá đúng lúc.

---

## 4. Sổ này KHÔNG làm gì

- **Không phải bản đánh giá an toàn đầy đủ.** Mười lăm dòng đầu (BM-001…BM-015) là những gì lòi
  ra khi soát quanh **từng ticket**, không phải kết quả của một đợt rà có phương pháp. Ngày
  **14/09/2026** mới có đợt rà đầu tiên đi theo **lớp phòng thủ** thay vì đi theo ticket — nó
  đẻ ra BM-016…BM-023 và lấp đúng hai vùng mà bản cũ của mục này ghi là *"chưa ai nhìn"*:
  **cấu hình** và **lớp mạng / VPS**. **Khâu tải tệp lên đã rà ngày 14/09/2026** (đợt thứ hai,
  BM-025…BM-031, §2b) — kiểu MIME, kích thước, tên tệp, và cả câu mà lần rà nào cũng quên hỏi:
  *ai đọc lại được tệp đó*. Còn **hai vùng chưa ai nhìn**: khâu **nhập/xuất dữ liệu**
  (Excel/CSV) và phần **tích hợp ngoài** (Cloudflare tunnel, R2, Brevo, webhook). **Không có
  dòng nào ở đây không có nghĩa là chỗ đó sạch.**
- ⚠️ **Và "đã rà" không bằng "đã vá"** — bảy dòng của đợt tải tệp lên đều đang ở trạng thái
  **Mở**. Việc vá xếp ở **Việc 6** của §3.
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
| **BM-024** | `test_ve_ky_dung_khoa_nhung_khong_co_phien_thi_tu_choi` | Tự ký một vé **đúng khóa, đúng `ver`**, `jti` là một chuỗi **không có** trong `tab_login_session` → `get_current_user` phải **401**. Đây là bài canh cho chốt duy nhất chặn được vế ký vé giả khi hai môi trường dùng chung khóa; ai gỡ `_check_session` ra khỏi đường xác thực là test đỏ. Kèm ca ngược: có phiên còn sống thì đi qua |

Đợt tải tệp lên đặt riêng một tệp `test/backend/test_bao_mat_tai_tep.py` — **đã viết xong, 11
bài, xanh** (`bao-CR-408`, 15/09/2026). Chín dòng dự tính dưới đây đều có mặt, cộng hai bài mọc
thêm lúc vá: `test_tran_so_tep_moi_luot` (BM-030) và `test_don_tep_mo_coi_khong_dung_anh_dai_dien`
(BM-031 — canh đúng chỗ việc dọn định kỳ có thể xóa nhầm). Hai chỗ bài kiểm **khác** mô tả dự
tính, cố ý: bài BM-026/027 khẳng định ở **tầng chốt** `guard_upload` chứ không dựng `TestClient`
(cùng một câu khẳng định, rẻ hơn và không giòn), và bài BM-027 quét **cả hai** bảng chính sách
chứ không riêng `IMAGE_EXTS` — hằng số đó đã bị xóa, luật nay nằm ở `DIRECT_FILE_POLICY`.

| Dòng | Bài kiểm | Khẳng định |
|---|---|---|
| **BM-025** | `test_register_tu_choi_tep_cua_nguoi_khac` | Dựng tệp của người A, cấp cho người B **đúng** `purchase_request` phạm vi `own`, B gọi `/register` gắn tệp đó vào phiếu của B → phải **403/404**, và **không** có `FileLink` nào mọc thêm. Kèm ca ngược: tệp của chính B thì gắn được. ⚠️ Bài này đã chạy **xanh theo chiều tấn công** ngày 14/09 (tức lỗ có thật) — viết xong phải thấy nó **đỏ trước khi vá** |
| **BM-025** | `test_khong_tai_duoc_dinh_kem_rieng_tu_qua_day_moi` | Sau khi vá, lặp lại đúng đường ba bước ở §2b rồi khẳng định `_get_file_with_permission(..., "download")` ném lỗi. Đây là bài canh **hậu quả**, không canh **cách vá** — người sau đổi cách vá vẫn phải giữ nó xanh |
| **BM-026** | `test_avatar_tu_choi_duoi_va_kich_thuoc` | Tải `.exe` (hoặc `.html`) lên `/api/auth/avatar` → **400**; tải ảnh vượt trần → **400**; ảnh hợp lệ → qua. Lặp cho `/api/employees/{id}/avatar` |
| **BM-027** | `test_chu_ky_tu_choi_svg_du_khai_image` | Gửi tệp SVG kèm `content_type="image/svg+xml"` → **400**. Đây là bài canh đúng chỗ thủng: khai đúng `image/` mà vẫn phải bị chặn |
| **BM-027** | `test_danh_sach_trang_anh_khong_chua_svg` | Khẳng định cấu trúc: `"svg" not in IMAGE_EXTS` và `"svg"` không nằm trong bộ đuôi ảnh của `FILE_POLICY`. Bài rẻ nhất trong bảng, và là bài duy nhất bắt được người sau thêm lại `svg` cho "tiện" |
| **BM-028** | `test_content_type_lay_tu_noi_dung_khong_lay_tu_loi_khai` | Tải một tệp PNG thật nhưng khai `text/html` → `tab_file.content_type` **không** được là `text/html` |
| **BM-029** | `test_zip_khong_co_duong_dan_di_len` | Dựng `StoredFile.filename = "../../evil.pdf"`, gọi `/chain/zip`, đọc `namelist()` của tệp nén → **không mục nào** chứa `..` |
| **BM-030** | `test_ten_tep_qua_dai_tra_422` | Tên **300 ký tự** → **422**, không phải 500. ⚠️ Kiểm ở **tầng chặn**, đừng ghi xuống DB rồi khẳng định — SQLite không ép `VARCHAR`, xem bẫy ngay dưới |
| **BM-031** | `test_upload_file_doi_quyen_voi_comment` | Tài khoản không quyền gì gọi `/upload-file` với `entity=comment` → phải bị chặn |
| **bao-CR-435** (cửa ghi mới, không phải BM) | `test_assistant_account_setup_tool.py` (22 ca) | Thiếu một trong ba khóa → `denied`; tự sửa mình → L1; vai trò mang quyền người hỏi không có → L2 (cả lúc đề xuất lẫn lúc xác nhận, kể cả khi vai trò được tick thêm quyền SAU lúc đề xuất); tài khoản ngoài phạm vi → "không tìm thấy"; token người khác / token loại `confirm-update` → 403; hết hạn / rác → 400; chạy lại → mọi dòng «không đổi», không ghi gì |

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

**BM-018 / BM-022 — đọc `.env` của VPS — ĐÃ LÀM 14/09/2026, cả hai sạch.** ⚠️ **Chỉ in ra
CÓ/KHÔNG.** Không in giá trị, không `cat` cả tệp, không dán kết quả vào chỗ nào lưu lại được.
Ba điều rút ra từ lần làm thật, áp cho mọi lần sau:

- **Đo hai lớp.** Tệp `.env` nói một đằng, container đã nạp một bản `.env` cũ chạy một nẻo.
  Lớp có thẩm quyền là tiến trình: `docker exec <api> python -c "from app.core.config import
  settings; ..."`.
- **So sánh hai bí mật thì băm ngay tại chỗ.** Tính `sha256` của mỗi bên **trên máy đó**, so
  **tại đó**, mang về đúng một chữ CÓ/KHÔNG. **Bản băm cũng không được in** — cả hai bên là
  một giá trị, nên bản băm lọt ra là một mục tiêu để dò. Đây chính là cách tìm ra BM-024.
- ⚠️ **`docker exec -i` nuốt mất phần còn lại của kịch bản** khi chạy trong một heredoc
  `ssh ... 'bash -s'` — stdin đã là kịch bản rồi. Bỏ `-i` khi exec không tương tác, không thì
  lệnh chạy xong mà **không ra một dòng nào** và trông y hệt như đo hỏng.

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
