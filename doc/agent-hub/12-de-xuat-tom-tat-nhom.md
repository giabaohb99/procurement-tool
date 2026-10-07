# 12 — Đề xuất: bot trong nhóm tóm tắt tin nhắn và tệp (Telegram + Zalo)

> Bản 0.1 — 07/10/2026, ý của đại ca: «cài bot vào nhóm thì tóm tắt được tin nhắn của nhóm, rồi gợi ý tóm tắt luôn
> các tệp gửi trong nhóm», cho cả bot Telegram và bot Zalo. Chưa làm, chờ chốt các câu ở §4.

## 1. Đánh giá nhanh

Ý hay và hợp với hướng trợ lý cá nhân: nhóm công việc là chỗ thông tin trôi nhanh nhất, người vắng nửa ngày phải đọc
lại hàng trăm tin. Phần lớn nền đã có: kho ghi chú, tóm tắt buổi (ai-CR-102), đọc tệp pdf / Word / Excel của Trợ lý,
biên bản họp từ ghi âm (ai-CR-104), khóa AI từng người (ai-CR-098).

| Kênh | Đọc tin nhóm | Lịch sử cũ | Tệp | Rủi ro |
|---|---|---|---|---|
| **Telegram** | Được, phải TẮT chế độ riêng tư của bot (BotFather → `/setprivacy` → Disable) hoặc cho bot làm quản trị nhóm | Chỉ từ lúc bot vào nhóm (Bot API không đọc tin cũ) | Tải được tệp ≤ 20 MB | Thấp — API chính thức |
| **Zalo** | Bot IDA đã đọc tin nhóm (tài khoản cá nhân qua `zca-js`), đã lưu tin + ảnh vào kho của nó | Đo 02/10: chỉ khoảng 2 tuần qua bookmarklet Zalo Web | Đã tải tệp đính kèm | Cao hơn — không phải API chính thức, có thể bị khóa tài khoản; Zalo OA không vào được nhóm |

## 2. Cách làm đề xuất

1. **Lưu tin nhóm** (Telegram): bảng tin nhóm riêng, giữ 30 ngày, chỉ nhóm do người đã đăng nhập ERP thêm bot vào.
2. **Tóm tắt khi được hỏi**: trong nhóm gọi «@bot tóm tắt hôm nay» / «tóm tắt từ sáng» → bot gửi bản tóm tắt
   **vào tin riêng** của người hỏi (không làm ồn nhóm); người hỏi phải là thành viên nhóm đó.
3. **Bản tổng hợp định kỳ** (tùy chọn): 17:30 mỗi ngày gửi riêng cho chủ bot: ý chính, việc được giao, câu hỏi còn treo,
   **danh sách tệp mới** kèm số thứ tự.
4. **Gợi ý tóm tắt tệp**: không tự nhắn vào nhóm mỗi khi có tệp; tệp mới nằm trong bản tổng hợp, người dùng nhắn
   «tóm tắt tệp 2» thì bot đọc tệp đó (pdf / Word / Excel / ảnh; ghi âm / video thì đi đường biên bản họp).
5. **Zalo**: không viết lại phần đọc nhóm — bot IDA đã có. Hai cách: (a) làm tóm tắt ngay trong IDA (đội IDA, kế hoạch
   doc/02 của IDA đã có mục brief / báo cáo); (b) IDA chuyển tin nhóm sang Agent Hub qua một đường API, một lõi tóm tắt
   dùng chung cho cả hai kênh. Em nghiêng (b) về lâu dài, (a) nếu cần nhanh.

Ước: Telegram 3–4 ngày công; nối Zalo theo cách (b) thêm 2–3 ngày phía Agent Hub + phần việc bên IDA.

## 3. Thứ tự đề xuất

Làm sau bước 10.2 của biên bản họp (khi đã thử tệp họp thật), hoặc chen trước nếu đại ca cần gấp — hai việc độc lập.

## 4. Câu chờ đại ca chốt

| Mã | Câu | Em đề xuất |
|---|---|---|
| G1 | Ai được nhờ tóm tắt nhóm: mọi thành viên, hay chỉ người đã thêm bot vào? | Mọi thành viên đã đăng nhập ERP, chạy bằng khóa AI của họ |
| G2 | Bản tóm tắt gửi đâu: vào nhóm hay tin riêng người hỏi? | Tin riêng; chỉ gửi vào nhóm khi nói rõ «gửi vào nhóm» |
| G3 | Có bản tổng hợp tự động mỗi ngày không, mấy giờ, gửi cho ai? | Có, 17:30, gửi riêng người đã bật |
| G4 | Giữ tin nhóm bao lâu? | 30 ngày |
| G5 | Zalo: làm trong IDA, hay nối IDA vào lõi Agent Hub? | Nối vào lõi Agent Hub (một nơi tóm tắt, một nơi giữ khóa) |
| G6 | Tắt chế độ riêng tư của bot Telegram (đại ca thao tác trong BotFather, em hướng dẫn) | — |
