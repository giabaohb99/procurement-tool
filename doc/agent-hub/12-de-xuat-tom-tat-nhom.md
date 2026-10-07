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

## 3. Câu chờ đại ca

| Mã | Câu | Em đề xuất |
|---|---|---|
| Z1 | Zalo đi hướng nào (A / B / C ở §2)? | A ngay; B chỉ khi chấp nhận rủi ro |
| Z2 | Nếu B: dùng số Zalo nào làm bot (số riêng, không phải số cá nhân của ai)? | Số riêng |
| G3 | Bản tổng hợp nhóm tự động mỗi ngày: có làm, mấy giờ? | Có, 17:30, người dùng tự bật |
