---
name: he-agent-viec-chen-ngang
description: Chạy khi có việc mới chen vào giữa lúc đang làm việc khác (người chủ nhắn giữa chừng, sự cố, bot giám sát báo). Xếp mức khẩn / gấp / thường, cất việc dở an toàn kèm ghi chỗ dừng, báo agent liên quan, làm việc chen, rồi mở lại việc cũ không mất gì.
---

# Việc chen ngang

## Xếp mức

| Mức | Dấu hiệu | Làm gì |
|---|---|---|
| **Khẩn** | Prod lỗi / không vào được; người dùng không làm được việc; lỗ bảo mật; dữ liệu sai; người chủ ghi *khẩn* | Dừng ngay việc đang làm |
| **Gấp** | Người chủ cần trong ngày, không có gì đang hỏng; người chủ ghi *gấp* | Xong **bước** đang dở (không bỏ nửa chừng) rồi làm |
| **Thường** | Việc mới, không cần ngay | Chấm điểm, đưa vào kế hoạch `00` + Dự án, báo *sẽ làm khi nào* |

Không chắc mức nào → coi là **gấp** và hỏi một câu trong báo cáo, không đoán là khẩn.

## Các bước khi dừng việc đang làm

1. **Cất việc dở an toàn:** không commit nửa chừng lên nhánh chung. Mã đang sửa → commit vào nhánh tạm `tam-dung/<mã việc>` trên bản sạch của mình (hoặc nhánh dự phòng như `du-phong/...`). Không dùng `git stash` ở cây chung — người khác có thể lấy nhầm.
2. **Ghi chỗ dừng** vào mục việc trong sổ task (và Dự án qua đồng bộ): *tạm dừng vì <việc chen>, dừng ở bước <...>, làm tiếp từ <...>, nhánh tạm <...>*.
3. **Báo agent đang chạy song song** nếu việc chen đụng khu của họ (cùng tệp, cần đóng băng để deploy). Không đụng thì để họ làm tiếp.
4. **Làm việc chen.** Sự cố thì **tìm nguyên nhân gốc trước khi kết luận** — sự cố #4 ngày 22/10: bot báo *prod không kết nối được* nhưng thật ra prod sống, lỗi ở DNS vùng .vn; kiểm bằng cách gọi thẳng địa chỉ Cloudflare (`curl --resolve`) và xem container / log trước khi báo *sập*.
5. **Báo xong** theo `he-agent-bao-cao-xong-viec`.
6. **Mở lại việc cũ** từ ghi chỗ dừng; xóa nhánh tạm khi đã gộp.
7. **Ghi sổ quyết định:** việc chen thuộc mức nào, người chủ có đồng ý mức đó không — để lần sau xếp đúng mà không hỏi.

## Kiểm đã làm đúng

- Không có việc nào bị bỏ dở mà không có ghi chỗ dừng.
- Không có commit nửa chừng trên erp-v2 / main vì bị cắt ngang.
