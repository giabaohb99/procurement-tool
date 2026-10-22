# 02 — BỘ SKILL CỦA HỆ AGENT

**Bản 0.1 — 22/10/2026.** Sáu skill dùng chung cho mọi người chủ. Skill đặt trong kho mã ở `.claude/skills/he-agent-*/SKILL.md` để ai kéo code về là có. Phần riêng của từng người (sổ quyết định, hạn mức, tên danh sách theo dõi) đọc từ **tệp cấu hình của người chủ** (`03`), skill không ghi cứng tên ai.

| Skill | Ai dùng | Khi nào | Đầu vào | Đầu ra |
|---|---|---|---|---|
| `he-agent-nam-tinh-hinh` | Điều phối | Đầu phiên; khi người chủ hỏi *làm tới đâu*; trước khi chọn việc | git (erp-v2, main), sổ task, Dự án, kế hoạch `00`, kết quả kiểm | Bảng tình hình ngắn: đang làm gì / của ai / tới đâu / việc đứng yên / chưa lên prod; danh sách việc chấm điểm *Làm ngay / Lên lịch / Gác / Bỏ* |
| `he-agent-truoc-khi-hoi` | Mọi agent | Mỗi lần định hỏi người chủ | Sổ quyết định, bảng hạn mức | Hoặc **tự làm theo tiền lệ / hạn mức** (ghi *đã tự làm theo tiền lệ X*), hoặc **một câu hỏi gọn kèm đề nghị A/B**; sau khi có trả lời thì **ghi sổ** |
| `he-agent-bao-cao-xong-viec` | Mọi agent | Xong một nghiệp vụ | Việc vừa xong, kết quả kiểm và rà | Báo cáo 3–4 dòng theo mẫu; cập nhật Dự án, kế hoạch `00`, sổ task |
| `he-agent-viec-chen-ngang` | Điều phối | Có việc mới chen giữa lúc đang làm | Việc mới, việc đang dở | Xếp mức *khẩn / gấp / thường*; cất việc dở + ghi chỗ dừng; báo agent liên quan; mở lại sau |
| `he-agent-ra-ma-doc-lap` | Người rà (Agent 2) | Trước khi gộp mọi thay đổi | Diff, mã việc, điều kiện xong | Biên bản rà: lỗi mức *chặn / nên sửa / gợi ý*, mỗi lỗi có chỗ, lý do, cách sửa; kết luận *được gộp / trả lại* |
| `he-agent-cai-tien` | Điều phối | Mỗi tuần, hoặc khi người chủ bảo | Sổ quyết định, số liệu tuần, lỗi lọt | Đề xuất nâng / hạ mức từng loại việc; bài học gom thành luật hoặc bài kiểm; gọn lại tệp hướng dẫn |

## Luật viết skill (giữ cho bộ dùng chung được)

- Viết **quy trình từng bước**, không viết kiến thức chung. Mỗi bước có cách kiểm *đã làm đúng chưa*.
- **Không ghi cứng** tên người, mã nhân sự, tên danh sách: đọc từ tệp cấu hình của người chủ.
- Ghi rõ **vùng cấm** và **sàn luôn hỏi** ở mọi skill có thể dẫn tới hành động ra ngoài.
- Skill viết từ chỗ đã vấp: mỗi bẫy có ví dụ thật (ngày, mã CR) để người đọc hiểu vì sao.
- Tiếng Việt, câu ngắn, không emoji, không « ».

## Skill chuyên môn đã có (giữ nguyên, ngoài bộ này)

`them-cong-cu-mcp`, `ba-che-do-agent`, `them-man-v2`, `them-entity-moi`, `viet-hdsd`, `soat-man-dev` — skill theo nghề của từng người viết. Bộ `he-agent-*` lo phần *cách làm việc cùng người chủ*, không thay các skill nghề.
