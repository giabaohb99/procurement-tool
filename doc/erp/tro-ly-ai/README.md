# TRỢ LÝ AI (AI)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | Agent 4 |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · ai-CR-063 (cổng MCP) · bao-CR-620..625 (Kho skill) · bao-CR-631, bao-CR-636 (tài liệu và bài HDSD) · bao-CR-696 (gom một phân hệ AI) · ai-CR-230 (đợt A0) |

## Phân hệ này là gì

Mọi thứ AI nằm trong ERP: **Trợ lý AI web** hỏi đáp tiếng Việt trên dữ liệu người hỏi vốn được xem (trang `/assistant`
và bong bóng nổi), **Kết nối AI riêng** để nhân sự dùng Claude / ChatGPT / Cursor / Gemini CLI của mình đọc ERP qua cổng
MCP (Trang cá nhân, tab *Trợ lý AI của tôi*), **Kho skill AI** là cẩm nang công ty viết cho AI đọc, và **AI kế hoạch và
phân việc**. Từ bao-CR-696 (30/10/2026) gom thành một phân hệ **AI** trên giao diện v2 với các nhóm menu Trợ lý AI ·
Kết nối · Kho skill · Giám sát · Cấu hình. Bộ máy bot (dịch vụ AI, bot Telegram, lõi hội thoại, máy sửa mã) có bộ tài
liệu riêng ở [`doc/agent-hub/`](../../agent-hub/README.md) — ở đây chỉ liên kết, không chép.

## Tới đâu rồi

| Mảng | Trạng thái | Ghi chú |
|---|---|---|
| Trợ lý AI web, công cụ tra cứu loại A, soạn nháp, sửa phiếu có xác nhận | Đã lên prod | [`01`](tai-lieu-ky-thuat/01-kien-truc-tro-ly-ai.md) ghi *đã code, đang chạy dev + prod* (15/09/2026) |
| Kho skill P0–P8, cổng MCP có khóa và OAuth (ChatGPT, claude.ai), K7, K9 | Đã lên prod | Prod 19/10/2026 theo [kế hoạch theo module](../../plans/00-ke-hoach-theo-module.md) §11 |
| Hoạt động AI vào hồ sơ cách làm việc (A0) | Đã lên prod | Prod 20/10/2026, ai-CR-230 |
| AI kế hoạch và phân việc (A1, A2) | Đang làm | A2 máy chủ xong, màn duyệt kế hoạch đã lên `erp-v2` 23/10/2026 ([kế hoạch theo module](../../plans/00-ke-hoach-theo-module.md) AI1-3); A1 kế hoạch 22/10 ghi chưa gắn công cụ, nay mã đã có `assistant/tools/capability_tool.py` (kh-AI1-2) nhưng tài liệu chưa ghi trạng thái lên môi trường |
| Tra cứu HDSD bằng RAG | chưa ghi | Prod chạy với `AI_RAG_ENABLED=false` theo [`03`](plans/03-lo-trinh-phase.md) Phase 5 |
| Công cụ cho phân hệ mọc sau 28/08/2026 (Phase 5) | Chưa làm | Làm một phần: `erp_read` mới có phiếu nhận hàng |
| Bot Telegram | Đã lên prod | Đóng băng tính năng từ 17/10/2026; MCP là đường chính |

## Đọc gì trước

| Muốn biết | Đọc |
|---|---|
| Làm được gì | [`chuc-nang/01-yeu-cau-chuc-nang.md`](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Chạy tốt cỡ nào, ai được xem gì | [`chuc-nang/02-yeu-cau-phi-chuc-nang.md`](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [`tai-lieu-ky-thuat/api.md`](tai-lieu-ky-thuat/api.md) · nhóm `assistant`, `ai_skill`, `ai-plan`, `agent-hub`, `mcp`, `mcp-oauth` trên `/docs` |
| Thiết kế, bảng dữ liệu, bẫy | [`tai-lieu-ky-thuat/`](tai-lieu-ky-thuat/) · cổng MCP: [`agent-hub/06-cong-mcp.md`](../../agent-hub/06-cong-mcp.md) |
| So sánh, khảo sát, câu hỏi chờ chốt | chưa có thư mục `nghien-cuu/`; câu chờ quyết ở [`21`](tai-lieu-ky-thuat/21-kho-skill-ai-mcp.md) §9, [`22`](tai-lieu-ky-thuat/22-ai-ke-hoach-phan-viec.md) §8, [kế hoạch theo module](../../plans/00-ke-hoach-theo-module.md) §11 |
| Kế hoạch đang làm / đã xong | [`plans/`](plans/) |
| Kịch bản kiểm thử tay | [`kiem-thu/`](kiem-thu/) |
| Hướng dẫn người dùng | Trung tâm trợ giúp: bài *Trợ lý AI* ([`seed_help_tro_ly_ai.py`](../../../backend/scripts/seed_help_tro_ly_ai.py)), cụm *Hướng dẫn sử dụng Kết nối AI riêng và Kho skill AI* ([`seed_help_ket_noi_ai_mcp.py`](../../../backend/scripts/seed_help_ket_noi_ai_mcp.py), [`seed_help_ket_noi_ai_cach_1.py`](../../../backend/scripts/seed_help_ket_noi_ai_cach_1.py), [`seed_help_ai_rieng_lam_duoc_gi.py`](../../../backend/scripts/seed_help_ai_rieng_lam_duoc_gi.py)) |

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [`chuc-nang/01-yeu-cau-chuc-nang.md`](chuc-nang/01-yeu-cau-chuc-nang.md) | Danh sách chức năng CN-AI-NN, tóm tắt và liên kết | Nháp |
| [`chuc-nang/02-yeu-cau-phi-chuc-nang.md`](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng PCN-AI-01..12 | Nháp |
| [`chuc-nang/10-ket-noi-ai-rieng-va-kho-skill.md`](chuc-nang/10-ket-noi-ai-rieng-va-kho-skill.md) | Kết nối AI riêng (khóa, OAuth), công cụ và skill, quản trị Kho skill, nhật ký và lỗi thường gặp; khớp bài HDSD | chưa ghi (bản 1.4, 30/10/2026) |
| [`kiem-thu/21a-kich-ban-thu-mcp-dev.md`](kiem-thu/21a-kich-ban-thu-mcp-dev.md) | Kịch bản thử Kho skill và cổng MCP trên dev | chưa ghi (bản 1.0, 17/10/2026) |
| [`plans/03-lo-trinh-phase.md`](plans/03-lo-trinh-phase.md) | Lộ trình phase 0–5 của Trợ lý AI, các quyết định đổi hướng | chưa ghi (25/08/2026) |
| [`tai-lieu-ky-thuat/01-kien-truc-tro-ly-ai.md`](tai-lieu-ky-thuat/01-kien-truc-tro-ly-ai.md) | Chức năng và phân quyền Trợ lý AI, luồng một lượt hỏi, còn nợ, việc khi thêm công cụ | Đã code, chạy dev + prod (15/09/2026) |
| [`tai-lieu-ky-thuat/02-danh-sach-api-tool.md`](tai-lieu-ky-thuat/02-danh-sach-api-tool.md) | Từng công cụ loại A: tham số, đầu ra, nguồn dữ liệu | Đã code 37 công cụ (21/09/2026) |
| [`tai-lieu-ky-thuat/04-bao-mat-va-van-hanh.md`](tai-lieu-ky-thuat/04-bao-mat-va-van-hanh.md) | Bảy tầng bảo vệ, bảng quyền từng công cụ, giới hạn còn lại, bài kiểm | Đã code, chạy dev + prod (15/09/2026) |
| [`tai-lieu-ky-thuat/21-kho-skill-ai-mcp.md`](tai-lieu-ky-thuat/21-kho-skill-ai-mcp.md) | Thiết kế Kho skill AI qua MCP: dữ liệu, quyền, cổng, giao diện, lộ trình | P0 · P1 · P1b · P2 · P4 xong trên dev, lên prod 19/10/2026 |
| [`tai-lieu-ky-thuat/22-ai-ke-hoach-phan-viec.md`](tai-lieu-ky-thuat/22-ai-ke-hoach-phan-viec.md) | AI kế hoạch và phân việc: công cụ, dữ liệu, quyền riêng tư, lộ trình | chưa ghi (bản 0.2, 20/10/2026) |
| [`tai-lieu-ky-thuat/api.md`](tai-lieu-ky-thuat/api.md) | Bảng đường API của Trợ lý, Kho skill, AI kế hoạch, dịch vụ AI, cổng MCP (dựng tự động từ mã) | Nháp |

## Mã nguồn

- Backend: `backend/app/modules/assistant/` (Trợ lý, công cụ ở `assistant/tools/`), `ai_skill/`, `ai_plan/`, `ai_usage/`,
  `agent_hub/` (cổng MCP `mcp.py`, khóa `mcp_keys.py`, bước nối ứng dụng `mcp_setup.py`), `agent_gateway/`.
- Giao diện v2: `frontend-v2/src/modules/ai/` (khung phân hệ AI), `assistant/`, `ai-skill/`.
- Kỹ năng cho người viết mã: `.claude/skills/them-cong-cu-mcp/`, `.claude/skills/ba-che-do-agent/`.
