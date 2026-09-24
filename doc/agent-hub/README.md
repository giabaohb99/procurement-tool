# AGENT HUB — Bộ máy tự động hóa bằng AI

Cụm tài liệu cho hệ thống nhận ticket, cho AI tóm tắt và đề xuất, đại ca duyệt qua Telegram,
rồi giao cho một con bot code thực hiện, kiểm thử, đưa lên dev và cuối cùng lên prod.

**Trạng thái: MỚI CÓ THIẾT KẾ, CHƯA VIẾT MỘT DÒNG MÃ NÀO.** Mọi thứ trong đây là bản vẽ.

| Đọc gì | Tệp |
|---|---|
| Xây bằng cách nào — kiến trúc, dữ liệu, luồng, cấu hình, lộ trình | [01-thiet-ke-ky-thuat.md](01-thiet-ke-ky-thuat.md) |
| Bot được phép và bị cấm làm gì — lằn ranh an toàn | [02-bo-quy-tac-bot.md](02-bo-quy-tac-bot.md) |
| Quyết định quen thuộc của đại ca, bot tra trước khi hỏi (ai-CR-015) | [03-so-quyet-dinh.md](03-so-quyet-dinh.md) |
| Danh sách tính năng còn phải làm: Đậu Đậu + nền nhiều bot + Thư ký + Nghiên cứu (ai-CR-031) | [04-danh-sach-tinh-nang.md](04-danh-sach-tinh-nang.md) |
| Ai đổi gì, khi nào (sổ CR riêng của mảng AI) | [../tai-lieu-ky-thuat/change-log-ai.md](../tai-lieu-ky-thuat/change-log-ai.md) |

## Tóm tắt một đoạn

Ticket đến từ hai nguồn (phân hệ Phiếu hỗ trợ có sẵn của ERP, và tin nhắn Telegram của đại ca) —
đó là đích đến; **bậc 1 chỉ chạy nguồn Telegram**, xem §12 của bản thiết kế.
Một **bot quản lý** chạy bằng **Gemini** gom các ticket cùng loại, tóm tắt dựa trên trí nhớ lấy
từ chính kho tài liệu của dự án, rồi viết một bản đề xuất cách sửa và nhắn qua Telegram. Đại ca
duyệt hoặc sửa. Duyệt xong, một **bot code** chạy bằng **Claude Code CLI ngay trên máy đại ca**
(dùng subscription, không tốn API key) sẽ sửa mã, viết bài kiểm, chạy cổng kiểm, mở PR. GitHub
Actions chạy lại cổng trên máy sạch rồi đưa lên **dev**. Bot quản lý tổng hợp kết quả nhắn về
Telegram. Đại ca ra lệnh thì mới **lên prod**.

## Ba điều quan trọng nhất, nếu chỉ đọc được ba dòng

1. **Mỗi mũi tên sang Telegram là một điểm dừng thật.** Task nằm im trong cơ sở dữ liệu chờ
   đại ca, không có đường nào tự chạy tiếp sau khi hết giờ.
2. **Bot code không bao giờ có chìa khóa prod.** Nó chạy trong hộp kín, chỉ thấy đúng bản sao
   mã nguồn của việc nó đang làm.
3. **Làm theo bốn bậc, bậc 4 là cổng prod và làm sau cùng.** Bậc 1 không đụng một dòng mã nào
   của hệ thống mà vẫn trả lời được câu hỏi đắt nhất: con bot quản lý có đủ khôn không.
