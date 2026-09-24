# AGENT HUB — DANH SÁCH TÍNH NĂNG CẦN LÀM

**Bản 1.0 · 24/09/2026.** Gom mọi việc còn lại của Đậu Đậu và các trợ lý mới đại ca muốn thêm
(biên bản họp, lịch và nhắc việc, nghiên cứu). Việc đã xong xem `change-log-ai.md`; thiết kế
bot sửa mã xem `01-thiet-ke-ky-thuat.md`; thiết kế biên bản họp gốc (28-29/08, chưa có mã) ở
`meeting-recap/doc/` trên máy.

**Tổng: 29 tính năng** — A 8 · N 5 · T 12 · R 4. Cỡ: **S** = một ngày trở xuống · **M** = hai
đến ba ngày · **L** = từ bốn ngày. Cỡ là ước thô, đo lại sau từng việc (A-01).

## Nguyên tắc chia bot

Chia bot theo **quyền**, không chỉ theo chức năng. Bot nào đọc nội dung lạ (web, tệp người
khác gửi) thì không được giữ khóa nào, vì nội dung đó có thể chứa lệnh cài sẵn.

| Bot | Làm gì | Giữ quyền gì |
|---|---|---|
| **Đậu Đậu** | Sửa mã, gộp, deploy dev | Khóa GitHub, SSH lên VPS |
| **Thư ký** | Biên bản họp, lịch, nhắc việc | Google Drive + Calendar, đọc ERP |
| **Nghiên cứu** | Research, tìm tài liệu, kiểm chứng nội dung | Không giữ khóa nào, chỉ đọc web và kho tài liệu |

Cả ba chạy chung một nền (sổ ghi, khóa Gemini trả phí, bộ hẹn giờ, theo dõi chi phí), mỗi bot
một token Telegram riêng.

## Nhóm A — Đậu Đậu (bot sửa mã), phần còn lại

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| A-01 | Đo thời gian: thẻ kết quả ghi tổng thời gian và thời gian từng bước | S | Sổ đã có giờ bắt đầu/kết thúc từng bước |
| A-02 | Dọn nhánh `bot/*` sau khi gộp | S | Chờ Q3 |
| A-03 | Cổng kiểm cho `frontend/` (bản v1) | S | Chờ Q4. Hiện bot chỉ kiểm được v2 |
| A-04 | Nhận ảnh chụp lỗi gửi kèm yêu cầu sửa, đưa cho bước rà soát và sửa mã | S | Cần N-02 |
| A-05 | Màn quản lý việc của bot trong ERP v2: danh sách, lịch sử, chi phí (AN-006) | M | Nên có trước A-06 |
| A-06 | Phiếu hỗ trợ trong ERP làm nguồn việc, không chỉ Telegram (AN-005) | M | |
| A-07 | Mỗi người tự đăng nhập tài khoản ERP trong Telegram (ai-CR-004) | M | Đại ca dặn để cuối |
| A-08 | Xem thử bản sửa trên máy local qua Cloudflare tunnel (AN-007) | L | Còn 4 câu chờ đại ca |

## Nhóm N — Nền chung cho nhiều bot

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| N-01 | Nhiều bot một nền: mỗi bot một token, sổ ghi rõ tin nào của bot nào | M | |
| N-02 | Tải tệp từ Telegram: ảnh, tin thoại, tệp nhỏ (trần 20 MB của Telegram) | S | Hiện bot bỏ qua mọi thứ không phải chữ |
| N-03 | Kết nối tài khoản Google một lần (Drive + Calendar), khóa lưu mã hóa | M | Chờ Q2 |
| N-04 | Chi phí theo từng bot, từng ngày, có trần ngày | S | |
| N-05 | Cách ly quyền: mỗi bot chỉ thấy khóa của nó | M | Bắt buộc trước khi bật bot Nghiên cứu |

## Nhóm T — Thư ký (biên bản họp, lịch, nhắc việc)

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| T-01 | **Thử trước (M0):** chạy một tệp họp thật qua Gemini ra biên bản, đo chất lượng và chi phí | S | Chốt chặn: không qua thì dừng cụm biên bản. Chờ Q1, Q5 |
| T-02 | Đọc thư mục ghi âm trên Drive, gom nhiều tệp của một cuộc họp thành một phiên | M | Tệp họp dài không gửi qua bot được, phải qua Drive |
| T-03 | Chuẩn hóa và cắt âm thanh dài cho vừa model | M | |
| T-04 | Gỡ băng từng tệp, nối theo thứ tự thời gian | M | |
| T-05 | Mẫu biên bản là dữ liệu (chính thức · gạch đầu dòng · danh sách việc · đầy đủ theo giờ), chọn mẫu bằng chữ | M | Thêm mẫu không phải sửa mã |
| T-06 | Xuất Word theo mẫu DEGO lên Drive, gửi bản tóm tắt ngay trong chat kèm link | M | |
| T-07 | Tin thoại ngắn thành lời nhắc hoặc việc | S | Cần N-02 |
| T-08 | Bản tin 8h sáng: lịch hôm nay, việc đến hạn, phiếu chờ đại ca duyệt | M | Cần N-03 |
| T-09 | Nhắc trước mỗi cuộc họp 15 phút | S | Cần N-03 |
| T-10 | «Nhắc anh 3h gọi nhà cung cấp X»: tạo lời nhắc bằng câu nói | S | Dùng bộ hẹn giờ và phần hiểu giờ sẵn có |
| T-11 | Tạo lịch Google Calendar bằng câu nói, hỏi lại trước khi tạo | S | Cần N-03 |
| T-12 | Việc rút ra từ biên bản thành lời nhắc và việc trong phân hệ Công việc của ERP | M | Chỗ hai cụm cộng lại đáng giá nhất |

## Nhóm R — Nghiên cứu (research, tìm tài liệu, kiểm chứng)

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| R-01 | Research một chủ đề: Gemini tìm Google, trả bản tóm tắt kèm nguồn | S | Cần N-05 |
| R-02 | Kiểm chứng một nhận định: đúng · sai · chưa đủ căn cứ, kèm nguồn | S | |
| R-03 | Tìm tài liệu nội bộ: kho tài liệu đã nạp + thư mục Drive | M | Cần N-03 |
| R-04 | Xuất báo cáo nghiên cứu ra Word lên Drive | S | Dùng lại T-06 |

## Thứ tự đề xuất

| Đợt | Gồm | Vì sao |
|---|---|---|
| 1 | A-01 · A-02 · T-01 | Rẻ; T-01 quyết định cả cụm biên bản có đáng làm không |
| 2 | N-01 · N-02 · N-05 · T-07 · T-10 | Dựng nền nhiều bot; nhắc việc bằng câu nói dùng ngay được |
| 3 | N-03 · T-08 · T-09 · T-11 | Nối Google: lịch và bản tin sáng |
| 4 | T-02 … T-06 · T-12 | Biên bản họp trọn vẹn (chỉ khi T-01 đạt) |
| 5 | N-04 · R-01 … R-04 | Bot Nghiên cứu |
| 6 | A-03 · A-04 · A-05 · A-06 · A-07 · A-08 | Phần còn lại của Đậu Đậu; A-07 cuối cùng |

**Năng lực:** đội làm được khoảng 24 ngày công mỗi tháng và phần lõi ERP còn thiếu 156 ngày
công (số của `meeting-recap/doc/04`). Các trợ lý này là việc cộng thêm, giành giờ với ERP.

## Câu chờ đại ca

| Mã | Câu | Chặn |
|---|---|---|
| Q1 | Biên bản họp làm cho đại ca dùng, hay cho CEO như yêu cầu gốc (bản gốc: chạy trên máy riêng của CEO, chỉ CEO thao tác) | T-01 … T-06 |
| Q2 | Nối tài khoản Google nào: cá nhân hay Google Workspace công ty | N-03 |
| Q3 | Nhánh `bot/*` xóa lúc gộp hay lúc «xong» | A-02 |
| Q4 | Cổng kiểm v1: chỉ chặn lỗi typecheck MỚI (ngoài 4 lỗi cũ) hay chỉ eslint tệp bot sửa | A-03 |
| Q5 | Một tệp ghi âm họp thật để thử (đặt vào thư mục trên máy, không gửi qua chat) | T-01 |
| Q6 | Tên cho bot Thư ký và bot Nghiên cứu | N-01 |
