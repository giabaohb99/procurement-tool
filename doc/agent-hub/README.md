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
| Hướng dẫn bật Google cá nhân cho Trợ lý trên dev (lịch, Drive, bản tin sáng) | [10-huong-dan-noi-google.md](10-huong-dan-noi-google.md) |
| Quy định hỏi và làm: khi nào bot làm luôn, khi nào hỏi một lần, khi nào không làm; sửa dữ liệu bằng lời (ai-CR-073) | [09-quy-dinh-hoi-va-lam.md](09-quy-dinh-hoi-va-lam.md) |
| Vận hành VPS qua bot: sổ môi trường, `deploy.sh`, thao tác có duyệt + sao lưu + hoàn tác, tự vận hành (ai-CR-067..069) | [08-van-hanh-vps.md](08-van-hanh-vps.md) |
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
- `11-ke-hoach-bien-ban-hop.md` — phase 10: biên bản họp từ ghi âm / video (mp3, m4a, mp4 qua Drive), lộ trình 10.0–10.4 + câu chờ chốt.
- `12-de-xuat-tom-tat-nhom.md` — đề xuất bot trong nhóm Telegram / Zalo tóm tắt tin nhắn và tệp; câu chờ chốt G1–G6.
- `17-tri-nho-va-y-dinh.md` — **toàn bộ lôgic nhớ của bot** (09/10, ai-CR-137): năm lớp nhớ (lõi · kho · tóm tắt cuộc · sổ ý định · điểm tự rút), sổ ý định không nguyên văn câu hỏi, nhãn con theo công cụ, tự rút ghi nhớ (≥ 3 lần trên ≥ 2 ngày, bia mộ khi «quên», không đọc nhóm), riêng tư, bảng thứ tự nạp mỗi lượt gọi model.
- `14-cong-erp-api.md` — hợp đồng cổng B ERP ↔ dịch vụ AI, ba chế độ `AGENT_MODE`, cách dựng dịch vụ AI tách riêng trên dev, deploy đích `agent`, runbook S-5/S-6 (ai-CR-119).
- `13-lo-trinh.md` — **lộ trình tổng** (08/10): trạng thái theo phase, bộ 44 chức năng của một trợ lý cá nhân đối chiếu bot IDA, kiến trúc đích A2A bốn nút (bot cá nhân · cổng ERP · bot code · kho tin nhắn), tầng lưu trữ, việc kế tiếp. Thay bảng phase cuối doc 04.
