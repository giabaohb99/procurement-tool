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

## Skill nghề (đưa vào kho mã 22/10/2026, commit e09e7650)

Sáu skill theo nghề, nằm ở `.claude/skills/<tên>/SKILL.md`. Bộ `he-agent-*` lo *cách làm việc cùng người chủ*; bộ này lo *làm đúng một loại việc kỹ thuật hay vấp*. Claude Code tự nạp skill khi việc đang làm khớp phần mô tả; muốn gọi thẳng thì gõ `/<tên skill>`.

| Skill | Dùng khi | Nó giúp gì |
|---|---|---|
| `them-man-v2` | Thêm màn, route hay phân hệ mới ở `frontend-v2/` | Liệt kê sáu nơi phải khai cùng lúc (sổ phân hệ, route, menu, quyền...), bài kiểm đồng bộ, các bẫy biểu mẫu, ba cổng kiểm (typecheck, lint, vitest theo thư mục) và cách commit an toàn ở cây git dùng chung |
| `them-entity-moi` | Phân hệ mới cần khóa quyền riêng, hoặc tách quyền khỏi entity cũ | Bảy sổ đăng ký phải khai cùng lúc ở backend (`ENTITIES`, `SCOPE_FIELDS`, `FILE_POLICY`...), seed vai trò và giao diện v2, để các bài kiểm canh phạm vi không đỏ |
| `them-cong-cu-mcp` | Tạo hoặc đổi công cụ cho cổng MCP, Trợ lý web hay bot | Đủ mọi chỗ phải khai: sổ công cụ, cổng MCP, nhóm cấu hình G7, bộ lọc công cụ, nhãn ý định, cổng B, bài kiểm canh cửa |
| `ba-che-do-agent` | Sửa `agent_hub`, `assistant`, `ai_skill`, `agent_gateway`; tính năng AI chạy ở local nhưng hỏng ở dev / prod | Giải thích ba chế độ chạy dịch vụ AI (nhúng / service / erp): mã nào chạy ở tiến trình nào, đọc DB nào, biến môi trường nào, các bẫy đã gặp và cách thử cả ba trước khi đẩy |
| `viet-hdsd` | Có tính năng mới lên dev mà chưa có bài hướng dẫn, hoặc màn đổi làm bài cũ sai | Viết bài trên Trung tâm trợ giúp (`seed_help_*.py`) kèm tài liệu chức năng song song, chạy seed và nạp lại chỉ mục tìm kiếm trên dev |
| `soat-man-dev` | Trước khi gộp main hoặc trước giờ đóng băng lên prod | Soát màn mới trên dev bằng khung trình duyệt người chủ đã đăng nhập sẵn, đối chiếu bài hướng dẫn và hợp đồng API, xếp lỗi chặn / lỗi nhỏ, báo đúng chủ khu |

## Định nghĩa agent (`.claude/agents/`)

Bốn vai dựng sẵn, gọi như subagent hoặc dùng làm tên vai cho một phiên riêng. Mỗi tệp ghi khu được sửa, vùng cấm và skill nạp sẵn.

| Agent | Vai | Không làm |
|---|---|---|
| `dieu-phoi` | Chia việc, gộp nhánh, dựng dev, phát hành prod, cấp số CR, trả lời câu hỏi cách làm của agent khác | Lên prod khi người chủ chưa ra lệnh; in bí mật |
| `ai-mcp` | Cổng MCP, Kho skill AI, Trợ lý web, bot (lõi core_v2), cổng B | Chạy bộ mẫu tốn tiền khi chưa duyệt; xoay khóa prod |
| `giao-dien-v2` | Màn, hộp thoại, bảng, hook gọi API, bài kiểm vitest ở `frontend-v2/` | Sửa backend |
| `tai-lieu-kiem-thu` | Bài hướng dẫn, tài liệu chức năng, soát màn dev, đối chiếu màn / bài / tài liệu | Gõ mật khẩu vào trang ngoài localhost; chép khóa thật vào tài liệu |

Các tệp này viết theo hệ của đại ca (nhắc *đại ca*, *Agent 1*). Người khác dùng thì đọc thay bằng người chủ và người điều phối của mình; phần riêng từng người vẫn để ở `03`.
