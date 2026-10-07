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
| Giữ tin nhóm | 30 ngày (`AGENT_GROUP_RETENTION_DAYS`), dọn lúc 03:20 mỗi đêm |

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
| Z-3 | Kênh B: tiến trình phụ (Node, thư viện tài khoản cá nhân) chỉ ghi lặng tin nhóm → API nội bộ của backend → bảng nhóm chung; tự báo khi bị đá phiên | 3 ngày |
| Z-4 | Đọc nhóm Zalo qua cùng 3 công cụ nhóm (`list_my_groups`…), quyền đọc = người đã thêm tài khoản B vào nhóm | 1 ngày |

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
