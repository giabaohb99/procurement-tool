# 12 — Trợ lý cá nhân đọc nhóm: tóm tắt tin nhắn, tệp, đọc và viết báo cáo (Telegram + Zalo)

> Bản 1.0 — 07/10/2026. Đại ca chốt: **trợ lý của từng người**; ai thêm bot vào nhóm nào thì **nhắn riêng** cho bot
> để nó tổng hợp, **không cần gọi @bot trong nhóm**; tin gửi riêng cho bot cũng được tóm tắt, ghi nhận; đọc báo cáo,
> viết báo cáo; làm cho **Telegram và Zalo**; trước mắt nội bộ, khách hàng để sau. **Không liên quan bot IDA** — chỉ
> mượn ý, không đụng kho `ida-zalo-assistant`.

## 1. Telegram — XONG đợt 1 (ai-CR-105)

| Việc | Cách chạy |
|---|---|
| Ghi tin nhóm | Bot ở trong nhóm ghi lặng mọi tin + siêu dữ liệu tệp (chưa tải). **Không nói gì trong nhóm** |
| Chủ nhóm | Người thêm bot vào nhóm (update `my_chat_member`) = chủ, nếu chat riêng của họ đã đăng nhập ERP |
| Ai đọc được | Chủ nhóm, hoặc người đã đăng nhập ERP mà Telegram xác nhận đang là thành viên nhóm (`getChatMember`) |
| Hỏi | Nhắn riêng: «nhóm Kế toán hôm nay bàn gì», «tổng hợp nhóm X tuần này», «bot đang ở nhóm nào» |
| Tệp trong nhóm | Bản tóm tắt liệt kê tệp kèm số thứ tự; «tóm tắt tệp số 2» → đọc pdf / Word / Excel / văn bản; ghi âm / video → biên bản họp gửi riêng |
| Đọc báo cáo gửi riêng | Gửi tệp pdf / Word / Excel / txt vào chat riêng, chú thích là câu hỏi (trống = tóm tắt) |
| Viết báo cáo | «viết báo cáo tuần từ nhóm X ra Word» → công cụ xuất Word sẵn có |
| Tin gửi riêng | Đã có: tóm tắt cuối buổi vào kho (ai-CR-102), tìm lại hội thoại cũ, sổ ghi nhớ |
| Giữ tin nhóm | **90 ngày** từ ai-CR-122 (đại ca chốt 08/10; trước đó 30), `AGENT_GROUP_RETENTION_DAYS`, dọn lúc 03:20 mỗi đêm |

**Việc tay của đại ca (một lần):** BotFather → `/setprivacy` → chọn bot → **Disable**. Không tắt thì trong nhóm bot chỉ
thấy lệnh `/…` và tin trả lời bot. Sau khi tắt, **mời bot ra rồi thêm lại** vào các nhóm đã có để Telegram áp chế độ mới.
Bot chỉ đọc được tin **từ lúc vào nhóm**, không lấy được tin cũ.

Còn lại (đợt 2): bản tổng hợp tự động mỗi ngày gửi riêng (giờ do từng người bật), màn web xem nhóm.

## 2. Zalo — CẦN ĐẠI CA CHỐT HƯỚNG

Đã tra tài liệu chính thức Zalo Bot Platform (`docs.zaloplatforms.com`, 07/10/2026):

- Bot Zalo chính thức **vào được nhóm** nhưng tính năng đang **«thử nghiệm nội bộ, sẽ ra mắt»**.
- Trong nhóm, bot chính thức **chỉ nhận tin trả lời bot hoặc tin @nhắc tên bot** — **không đọc được toàn bộ tin nhóm**.
  Tức là **không tóm tắt nhóm được** bằng đường chính thức.
- Zalo OA (tài khoản doanh nghiệp) không vào được nhóm.

Ba hướng:

| Hướng | Được | Mất |
|---|---|---|
| **A. Bot Zalo chính thức** | Đúng luật Zalo, ổn định | Không đọc được tin nhóm → chỉ làm được trợ lý chat riêng (hỏi đáp, đọc tệp gửi riêng, biên bản họp, sổ nhớ) |
| **B. Tài khoản Zalo cá nhân làm bot** (thư viện không chính thức kiểu `zca-js`, tự dựng phía mình) | Đọc được toàn bộ tin nhóm như Telegram | Không phải cách Zalo cho phép, **có thể bị khóa tài khoản**; Zalo đổi giao thức là gãy; cần một tài khoản Zalo riêng cho bot |
| **C. Chờ Zalo mở nhóm cho bot chính thức** | Đường chính thức | Chưa biết bao giờ, và có thể vẫn chỉ nhận @nhắc tên |

Em đề xuất: làm **A ngay** (cùng lõi với Telegram, 3–4 ngày công: kênh Zalo vào cùng bộ xử lý tin, đăng nhập bằng mã như
Telegram) để người dùng Zalo có trợ lý riêng; phần **tóm tắt nhóm Zalo** chỉ làm theo **B** nếu đại ca chấp nhận rủi ro
khóa tài khoản và dùng một số Zalo riêng cho bot.

## 3. Đã chốt (đại ca 07/10/2026)

- **Không làm** bản tổng hợp nhóm tự động cuối ngày — chỉ tổng hợp khi người dùng nhắn hỏi.
- **Zalo làm cả A và B**:
  - **A — bot Zalo chính thức** (Zalo Bot Platform): trợ lý chat riêng y như Telegram — hỏi đáp ERP, sổ nhớ, thẻ cá
    nhân, đọc tệp, biên bản họp. Nhận tin bằng polling (`getUpdates`) như Telegram nên không cần mở webhook. Cần: đại
    ca tạo bot trong mini app «Zalo Bot Creator» và đưa token qua tệp (không dán vào chat).
  - **B — một tài khoản Zalo riêng làm «bot» đọc nhóm** (thư viện không chính thức, dựng phía mình, KHÔNG dùng mã IDA):
    chỉ để GHI LẶNG tin + tệp các nhóm Zalo mà tài khoản đó được thêm vào, đổ vào cùng bảng nhóm như Telegram; người
    dùng hỏi qua bot A hoặc Telegram. Cần: một số điện thoại / tài khoản Zalo riêng (không phải số cá nhân của ai), đại
    ca quét QR đăng nhập một lần; chấp nhận rủi ro bị khóa tài khoản.
- **Xưng hô**: mỗi người theo sổ ghi nhớ riêng; mặc định «anh/chị» (ai-CR-106).

## 4. Lộ trình Zalo

| Bước | Việc | Cỡ |
|---|---|---|
| Z-1 | Tách lớp «kênh» khỏi mã Telegram: gửi / nhận / tải tệp / mã chat có tiền tố kênh (Telegram giữ số cũ, Zalo `zl:`), đăng nhập bằng mã dùng chung | **Xong mã — ai-CR-111** |
| Z-2 | Kênh A: bộ nối Zalo Bot API (polling, gửi tin, tải tệp), luồng nhận tin Zalo trong `agent-poller` | **Xong mã — ai-CR-111**, chờ token để bật |
| Z-3 | Kênh B: tiến trình phụ `zalo-listener` (Node, zca-js) ghi lặng tin nhóm + chat riêng với tài khoản công ty; tự báo khi bị đá phiên | **Xong mã — ai-CR-122** (08/10) |
| Z-4 | Đọc nhóm Zalo qua cùng 3 công cụ nhóm, quyền đọc = tài khoản Zalo đã đăng nhập ERP có tên trong danh sách thành viên | **Xong mã — ai-CR-122** (08/10) |

## 5. Còn chờ đại ca

| Mã | Việc | Ghi chú |
|---|---|---|
| Z1 | Token bot Zalo chính thức (mini app Zalo Bot Creator → tạo bot → lấy token), lưu vào một tệp trên máy rồi báo em đường dẫn. **Đừng đặt webhook** cho bot (Zalo không cho kéo tin khi đã có webhook) | Em đưa vào `.env.dev` thành `AGENT_ZALO_BOT_TOKEN`, xong xóa tệp, khởi động lại `agent-poller` |
| Z2 | Một tài khoản Zalo riêng cho kênh B + lúc rảnh để quét QR | Rủi ro bị khóa — đừng dùng số cá nhân |

## 6. Kênh Zalo A đã dựng (ai-CR-111, 07/10/2026)

| Việc | Cách chạy trên Zalo |
|---|---|
| Đăng nhập | Nhắn `/dangnhap <mã>` (mã lấy ở Trang cá nhân trên ERP, cùng mã với Telegram) |
| Hỏi đáp, sổ ghi nhớ, thẻ cá nhân, khóa AI, chuông ERP | Y hệt Telegram — cùng một lõi |
| Ảnh kèm chú thích, tin thoại | Có (tin thoại chép thành chữ rồi trả lời như tin chữ) |
| Nút bấm | Zalo không có → bot liệt kê lựa chọn, người dùng nhắn lại bằng chữ |
| Gửi tệp Word / Excel | Zalo Bot chưa có API gửi tệp → bot báo lấy qua Telegram hoặc web |
| Tin dài | Cắt tối đa 5 mẩu, mỗi mẩu ≤ 1900 ký tự |
| Nhóm Zalo | Bot chính thức chỉ nhận tin trả lời bot / tin nhắc tên bot → ghi lặng; người đăng nhập nói đầu tiên là chủ; chỉ người từng nhắn trong nhóm đọc được. Đọc TOÀN BỘ nhóm phải chờ hướng B (Z-3) |

## 7. Kênh Zalo B đã dựng (ai-CR-122, 08/10/2026)

Đại ca chốt 08/10: **một tài khoản Zalo riêng của công ty làm «bot»** · **chỉ trả lời riêng** như hiện tại · **giữ tin 3
tháng**.

| Việc | Cách chạy |
|---|---|
| Tiến trình | Service `zalo-listener` (Node 20 + zca-js 2.2.0) trong stack agent-hub, chỉ mạng nội bộ, 256 MB. Giữ phiên MỘT tài khoản. Không có nghiệp vụ: chỉ ghi sự kiện vào hàng đợi, gửi tin khi được gọi |
| Đăng nhập | Đại ca nhắn bot Telegram `/zalo dangnhap` → ảnh QR về chat đại ca → quét bằng điện thoại **giữ số Zalo công ty**. Phiên lưu mã hóa (AES-256-GCM) ở volume `zalo_session`; khởi động lại không phải quét lại |
| Văng phiên | Zalo đá phiên (mở Zalo Web / PC cùng tài khoản ở nơi khác, đứt mạng lâu) → bot báo đại ca, tự thử nối lại 10 phút một lần; không được thì `/zalo dangnhap` quét lại. `zalo-listener` im quá 5 phút → báo một lần |
| Nhận tin | `agent-poller` kéo `GET /updates` có con trỏ (như Telegram). Mọi lượt gọi ký HMAC bằng `AGENT_SERVICE_SECRET` |
| Nhóm | Tin + tệp mọi nhóm có tài khoản công ty → kho nhóm chung (`zg:<id>`). Bot **không nói gì trong nhóm** (chặn cứng ở hàm gửi). Tên nhóm + danh sách thành viên quét lại 6 giờ/lần và mỗi khi có người vào / ra |
| Ai đọc được nhóm | Người đã nhắn riêng tài khoản công ty `/dangnhap <mã>` (mã ở Trang cá nhân ERP) VÀ có tên trong danh sách thành viên nhóm đó. Người thêm tài khoản công ty vào nhóm ghi là chủ |
| Chat riêng | Nhắn riêng tài khoản công ty = dùng bot y như Telegram (hỏi ERP, sổ nhớ, biên bản họp, đọc tệp, chuông). Khác bot Zalo chính thức: **gửi được tệp** Word / Excel. Không có nút bấm (liệt kê lựa chọn), không sửa tin đã gửi |
| Nhịp gửi | Một hàng, cách nhau 1,5–2,2 giây (`ZALO_SEND_GAP_MS`) — giảm rủi ro Zalo khóa số |
| Lệnh chủ bot | `/zalo` tình trạng · `/zalo dangnhap` lấy QR · `/zalo nhom` đồng bộ lại nhóm |

**Luật vận hành:** không mở Zalo Web / Zalo PC bằng tài khoản công ty trên máy nào khác (sẽ đá phiên của bot); điện
thoại giữ số vẫn dùng bình thường. Người muốn bot đọc nhóm Zalo nào thì **thêm tài khoản công ty vào nhóm đó**; bot chỉ
thấy tin **từ lúc vào**.

## 8. Đánh giá hạ tầng (đại ca hỏi 08/10)

### 8.1 Nếu mỗi người tự quét QR bằng Zalo cá nhân (phương án b)

| Mặt | Tài khoản công ty (đang làm) | Mỗi người một QR (100 người) |
|---|---|---|
| Phiên giữ thường trực | 1 kết nối | 100 kết nối, mỗi cái ~40–60 MB RAM → **4–6 GB RAM** riêng cho phần này (gom nhiều tài khoản / tiến trình thì ~2–3 GB). CPU thấp (kết nối nằm chờ) |
| Số nhóm bị ghi | Chỉ nhóm có thêm tài khoản công ty (vài chục) | **Mọi nhóm** của 100 người, gồm nhóm gia đình, nhóm riêng tư — vài nghìn nhóm (nhóm chung nhiều người chỉ lưu một lần) |
| Lượng tin, giữ 90 ngày | ~5–20 nghìn tin / ngày → 0,5–2 triệu dòng, **1–3 GB** — MySQL hiện tại chịu được | ~100–300 nghìn tin / ngày → 9–27 triệu dòng, **10–30 GB** + tệp. Phải làm tầng lưu trữ đã ghi ở doc 13 §4 (chia bảng theo tháng, tệp lên R2) và tách kho tin (S-6) |
| Rủi ro khóa số | Dồn vào MỘT số của công ty | Khóa đúng **Zalo cá nhân** của nhân viên |
| Đá phiên | Không ai dùng Zalo Web / PC bằng số công ty → hiếm | Người nào đang dùng Zalo PC / Web thì bot và họ đá nhau liên tục — gần như chắc chắn xảy ra hằng ngày |
| Riêng tư | Chỉ nhóm công việc người ta chủ động thêm bot | Bot đọc cả tin riêng tư; cần sự đồng ý bằng văn bản của từng người (dữ liệu cá nhân theo Nghị định 13/2023) |

**Kết luận:** máy móc không phình nhiều (thêm một VPS 4–8 GB là đủ), nhưng **dữ liệu phình 10–15 lần**, và hai cái khó
thật nằm ở **đá phiên** (người dùng Zalo PC) và **khóa số cá nhân**. Em đề xuất giữ tài khoản công ty; nếu sau này cần thì
chỉ mở QR cá nhân cho **vài người tự nguyện** (quản lý), mỗi người chọn **danh sách nhóm được ghi** thay vì ghi tất cả.

### 8.2 Nếu cho bot trả lời trong nhóm khi được gọi (@bot) — Telegram và Zalo

**Mã phải đổi (khoảng 3–4 ngày):**

| Việc | Ghi chú |
|---|---|
| Nhận ra «được gọi» | Telegram: tin có `@tên_bot` hoặc trả lời tin của bot. Zalo B: danh sách `mentions` có id tài khoản công ty, hoặc trích tin của nó. Zalo A: bot chính thức vốn chỉ nhận tin kiểu này |
| Trả lời dưới quyền ai | Người gọi phải đã đăng nhập ERP (nhắn riêng `/dangnhap` trước); dùng khóa AI của người gọi. Người chưa đăng nhập → im hoặc một câu nhắc ngắn |
| **Chống lộ số liệu ERP** — chỗ quan trọng nhất | Câu trả lời trong nhóm ai cũng thấy. Đề xuất: trong nhóm chỉ trả lời câu chung (tóm tắt nhóm, tra mạng, giải thích); câu đụng số liệu ERP thì nhắn kết quả **riêng** cho người gọi và trong nhóm chỉ báo «em đã nhắn riêng». Chủ nhóm có thể bật «nhóm nội bộ, được trả lời số liệu» |
| Ngữ cảnh | Dùng luôn kho tin nhóm: «@bot tóm tắt từ sáng tới giờ», «@bot ai hứa gửi báo giá» |
| Chống loạn | Trần ~10 câu trả lời / giờ / nhóm, bỏ qua tin của bot khác, câu trả lời ngắn, không nút bấm (Telegram: nút trong nhóm ai cũng bấm được → nút phải kiểm người bấm = người gọi) |
| Gỡ chốt chặn | Hàm gửi Zalo B đang chặn cứng tin vào nhóm; đổi thành theo cờ cấu hình từng nhóm |

**Hạ tầng: không cần đánh giá lại** ở quy mô hiện tại. Kho tin không đổi (đằng nào cũng đã ghi hết tin nhóm). Số lượt gọi
AI tăng ít vì chỉ trả lời khi được gọi. Một việc nên làm cùng lúc: **đẩy phần trả lời sang hàng đợi worker** (hiện trả lời
chạy ngay trong `agent-poller` — một câu dài 30 giây làm tin nhóm khác ghi chậm theo; tin không mất vì có hàng đợi, nhưng
nhóm đông sẽ dồn) — đúng hàng «chat / heavy» đã ghi ở doc 13 §7. Thêm bộ đếm trần theo nhóm trong Redis sẵn có.

**Rủi ro riêng Zalo B:** tài khoản cá nhân **nói** trong nhóm (nhất là nhóm đông, nhiều người lạ) dễ bị Zalo đánh dấu
hơn chỉ đọc. Nếu bật, em đề xuất Telegram trước, Zalo B sau một hai tuần chạy ổn, và giới hạn nhóm được phép nói.

