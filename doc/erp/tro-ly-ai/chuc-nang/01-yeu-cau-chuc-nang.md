# YÊU CẦU CHỨC NĂNG — TRỢ LÝ AI

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | Agent 4 |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · ai-CR-063 · bao-CR-620..625 · bao-CR-631 · bao-CR-636 · bao-CR-696 · ai-CR-230 |

Tệp này là **mục lục chức năng**: mỗi dòng tóm tắt ngắn và trỏ tới tài liệu cũ đang giữ chi tiết (luật *một sự thật một
chỗ*). Danh sách từng công cụ (tham số, đầu ra) không chép lại ở đây — đọc
[`02-danh-sach-api-tool.md`](../tai-lieu-ky-thuat/02-danh-sach-api-tool.md). Bộ máy bot (dịch vụ AI, bot Telegram, lõi
hội thoại) đọc ở [`doc/agent-hub/`](../../../agent-hub/README.md).

## 1. Người dùng và vai trò

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Quản trị (`admin`) | Mọi quyền: Trợ lý, soi chi phí, nạp lại chỉ mục, Kho skill, khóa nhân sự, cấu hình nhóm công cụ |
| Quản lý công ty (`company_head`) | Dùng Trợ lý AI web (`assistant.read`, khai tường minh) |
| Quản lý thu mua (`pur_manager`) | Dùng Trợ lý AI web; nhận ngầm cả `assistant.export` nên mở được bảng chi phí toàn hệ ([`01`](../tai-lieu-ky-thuat/01-kien-truc-tro-ly-ai.md) §6.2) |
| Mọi nhân sự | Tạo khóa kết nối, nối ứng dụng AI riêng, đọc skill được gán; công cụ chạy dưới đúng quyền của người đó ([`10`](10-ket-noi-ai-rieng-va-kho-skill.md) §1, §5) |
| Người soạn skill, trưởng phòng (`ai_skill.write` / `approve`) | Soạn, xuất bản, gán quyền đọc bộ skill ([`21`](../tai-lieu-ky-thuat/21-kho-skill-ai-mcp.md) §4.4, §6.2) |
| Người quản lý khóa (`ai_mcp_key_admin`) | Phát khóa hộ, thu hồi khóa nhân sự ([`21`](../tai-lieu-ky-thuat/21-kho-skill-ai-mcp.md) §6.2 G5) |
| Người được giao báo cáo 14 / 16 | Xem hồ sơ cách làm việc, năng lực theo loại việc qua AI ([`22`](../tai-lieu-ky-thuat/22-ai-ke-hoach-phan-viec.md) §6) |

## 2. Danh sách chức năng

Trạng thái: **Có** (đã lên prod) · **Dev** (mới trên dev) · **Đang làm** · **Chưa** · **Bỏ**. *chưa ghi* = tài liệu nguồn
không nói rõ.

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-AI-01 | Hỏi đáp nhiều lượt với Trợ lý AI web — [`01`](../tai-lieu-ky-thuat/01-kien-truc-tro-ly-ai.md) §3, §4 | Người có `assistant.read` | `/assistant`, bong bóng nổi | Có | — |
| CN-AI-02 | Hội thoại: danh sách, mở lại, xóa — chỉ chính chủ — [`01`](../tai-lieu-ky-thuat/01-kien-truc-tro-ly-ai.md) §4 | Như trên | `/assistant` | Có | — |
| CN-AI-03 | Đính kèm ảnh / PDF vào câu hỏi — [`04`](../tai-lieu-ky-thuat/04-bao-mat-va-van-hanh.md) §7 | Như trên | Ô soạn câu hỏi | Có | CR-204 |
| CN-AI-04 | Tra dữ liệu nghiệp vụ bằng công cụ loại A (hợp đồng, giá, lịch sử mua, công nợ, văn bản, phiếu chờ ký...) — [`02`](../tai-lieu-ky-thuat/02-danh-sach-api-tool.md), bảng quyền ở [`04`](../tai-lieu-ky-thuat/04-bao-mat-va-van-hanh.md) §5 | Trợ lý web, bot, ứng dụng AI riêng | Trong câu trả lời | Có | — |
| CN-AI-05 | Soạn nháp phiếu (YCBG, YCMH, nghỉ phép, YCTT, phiếu hỗ trợ) — [`02`](../tai-lieu-ky-thuat/02-danh-sach-api-tool.md) Nhóm 7, 9, 11 | Như trên | Thẻ nháp trong hội thoại | Có | CR-218 · bao-CR-387 |
| CN-AI-06 | Sửa phiếu có xác nhận, sổ thay đổi và hoàn tác trong 24 giờ — [`01`](../tai-lieu-ky-thuat/01-kien-truc-tro-ly-ai.md) §6.4; đường `/api/assistant/changes*` ở [`api.md`](../tai-lieu-ky-thuat/api.md) | Như trên | Thẻ *Xác nhận sửa*; sổ thay đổi | chưa ghi | CR-218 · ai-CR-182 |
| CN-AI-07 | Lập bộ tài khoản thu mua có xác nhận (gán vai trò có sẵn, không tạo tài khoản) — [`02`](../tai-lieu-ky-thuat/02-danh-sach-api-tool.md) Nhóm 19, [`04`](../tai-lieu-ky-thuat/04-bao-mat-va-van-hanh.md) §5 | Quản trị | Thẻ xác nhận trong hội thoại | chưa ghi | bao-CR-435 |
| CN-AI-08 | Xuất báo cáo Word / Excel, chỉ chủ tệp tải được — [`02`](../tai-lieu-ky-thuat/02-danh-sach-api-tool.md) Nhóm 8 | Như trên | Liên kết tải trong hội thoại | Có | CR-205 |
| CN-AI-09 | Tra cứu HDSD bằng RAG và nạp lại chỉ mục — [`01`](../tai-lieu-ky-thuat/01-kien-truc-tro-ly-ai.md) §5.3, [`03`](../plans/03-lo-trinh-phase.md) Phase 3 | Người dùng Trợ lý; quản trị HDSD nạp chỉ mục | Trong câu trả lời | chưa ghi | — |
| CN-AI-10 | Hạn mức câu hỏi mỗi ngày và soi chi phí token — [`03`](../plans/03-lo-trinh-phase.md) Phase 4 (P4-C) | Mọi người (hạn mức của mình); quản trị (chi phí) | `/assistant`; màn chi phí | Có | — |
| CN-AI-11 | Kết nối AI riêng: tạo khóa, nối Claude Desktop / Claude Code / Cursor / Gemini CLI, nối ChatGPT và claude.ai bằng đăng nhập ERP (OAuth), xem lại / tạm tắt khóa — [`10`](10-ket-noi-ai-rieng-va-kho-skill.md) §2–§4b | Mọi nhân sự | `/me?tab=ai-connect`, `/connect-ai` | Có | ai-CR-063 · ai-CR-218..225 · bao-CR-639 |
| CN-AI-12 | Công cụ ERP qua MCP, bật / tắt theo nhóm — [`10`](10-ket-noi-ai-rieng-va-kho-skill.md) §5, [`agent-hub/06`](../../../agent-hub/06-cong-mcp.md) §4 | Quản trị (bật nhóm); mọi người (dùng) | Cấu hình chung | Có | ai-CR-216 |
| CN-AI-13 | Kho skill AI: bộ skill, soạn skill, xuất bản phiên bản, gán ai được đọc theo sơ đồ tổ chức, mức bảo mật — [`10`](10-ket-noi-ai-rieng-va-kho-skill.md) §6, [`21`](../tai-lieu-ky-thuat/21-kho-skill-ai-mcp.md) §4, §6.2 G2–G4 | Người có `ai_skill.*` | Phân hệ AI, nhóm Kho skill | Có | bao-CR-621 · bao-CR-623 |
| CN-AI-14 | Kết nối (khóa nhân sự): phát khóa hộ, thu hồi, xem ai đang nối — [`21`](../tai-lieu-ky-thuat/21-kho-skill-ai-mcp.md) §6.2 G5, [`10`](10-ket-noi-ai-rieng-va-kho-skill.md) §6 | Người quản lý khóa | Phân hệ AI, mục Kết nối | Có | bao-CR-623 · bao-CR-696 |
| CN-AI-15 | Tổng quan và Nhật ký sử dụng (lọc, tìm người / công cụ, cột Chứng từ, xuất CSV) — [`10`](10-ket-noi-ai-rieng-va-kho-skill.md) §7, [`21`](../tai-lieu-ky-thuat/21-kho-skill-ai-mcp.md) §6.2 G1, G6 | Quản trị, trưởng phòng (nhánh mình); mỗi người 20 lượt của mình | Nhóm Giám sát; màn AI của tôi | Có | ai-CR-209 · bao-CR-624 |
| CN-AI-16 | Cấu hình AI: nhóm công cụ, trần tần suất, số ngày giữ nhật ký, câu dặn mặc định — [`21`](../tai-lieu-ky-thuat/21-kho-skill-ai-mcp.md) §6.2 G7 | Quản trị | Nhóm Cấu hình | Có | ai-CR-216 · bao-CR-624 |
| CN-AI-17 | Ứng dụng AI đã kết nối (mục Nâng cao): người đang dùng, lọc còn kết nối / host lạ — [`10`](10-ket-noi-ai-rieng-va-kho-skill.md) §6 | Quản trị | Nhóm Cấu hình, Nâng cao | chưa ghi | bao-CR-635 · bao-CR-696 |
| CN-AI-18 | Quản trị Kho skill và khóa bằng lời qua khóa được ghi (K9) — [`21`](../tai-lieu-ky-thuat/21-kho-skill-ai-mcp.md) §7.2 P7 | Người có `ai_skill.write` / `ai_mcp_key_admin.write` | Ứng dụng AI riêng | Có | bao-CR-634 · bao-CR-637 · bao-CR-638 |
| CN-AI-19 | Một kho tri thức chung cho bot và Trợ lý web (K7) — [`21`](../tai-lieu-ky-thuat/21-kho-skill-ai-mcp.md) §7.2 P8 | Trợ lý web, bot | — | Có | — |
| CN-AI-20 | Đưa hoạt động AI vào hồ sơ cách làm việc (A0) — [`22`](../tai-lieu-ky-thuat/22-ai-ke-hoach-phan-viec.md) §5.1 | Hệ thống; quản trị xem | Báo cáo 14 | Có | ai-CR-230 |
| CN-AI-21 | Năng lực đội cho AI: `team_capacity`, `task_type_stats` (A1) — [`22`](../tai-lieu-ky-thuat/22-ai-ke-hoach-phan-viec.md) §4, §6 | Người có báo cáo 16; trưởng phòng (chỉ thứ tự gợi ý) | Trợ lý web, MCP | chưa ghi | kh-AI1-2 |
| CN-AI-22 | Lập kế hoạch có ước lượng và lý do giao việc, ghi đề xuất và phần người sửa, màn duyệt kế hoạch (A2) — [`22`](../tai-lieu-ky-thuat/22-ai-ke-hoach-phan-viec.md) §4, §5.2 | Trưởng phòng, ban điều hành | Trợ lý web, MCP, màn duyệt kế hoạch | Đang làm | kh-AI1-3 |
| CN-AI-23 | Bot Telegram: nhóm chat, người dùng bot — đóng băng tính năng — [`agent-hub`](../../../agent-hub/README.md) | Quản trị | Nhóm Giám sát, Bot Telegram | Có | — |
| CN-AI-24 | Công cụ cho các phân hệ mọc sau 28/08/2026 (Đặt xe, Duyệt dấu, Diễn đàn, Kho...) — [`03`](../plans/03-lo-trinh-phase.md) Phase 5 | Trợ lý web, MCP | — | Chưa | — |
| CN-AI-25 | RAG toàn hệ có lọc quyền từng bản ghi (AI-2) — [`03`](../plans/03-lo-trinh-phase.md) mục Để sau | — | — | Chưa | — |

Ghi chú trạng thái: CN-AI-01..05, 08, 10 lấy từ dòng *đã code, đang chạy dev + prod* của [`01`](../tai-lieu-ky-thuat/01-kien-truc-tro-ly-ai.md)
và [`04`](../tai-lieu-ky-thuat/04-bao-mat-va-van-hanh.md) (15/09/2026); CN-AI-11..16, 18..20, 23 lấy từ mục *Đã có* §11 của
[kế hoạch theo module](../../../plans/00-ke-hoach-theo-module.md) (prod 19/10 và 20/10/2026). CN-AI-24 có làm một phần
(`erp_read` mới đọc phiếu nhận hàng).

## 3. Chi tiết từng chức năng

### CN-AI-01 — Hỏi đáp với Trợ lý AI web

- **Mục đích:** hỏi bằng tiếng Việt về dữ liệu nghiệp vụ trong phạm vi người hỏi vốn được xem, và về quy trình.
- **Luồng chính:** gửi câu → kiểm cờ `AI_ENABLED`, quyền `assistant.read`, hạn mức ngày → model chọn công cụ → công cụ
  đọc dữ liệu dưới quyền người hỏi → model trả lời, lưu vào hội thoại. Chi tiết: [`01`](../tai-lieu-ky-thuat/01-kien-truc-tro-ly-ai.md) §3.
- **Luật nghiệp vụ:** câu về dữ liệu đi công cụ loại A đọc thẳng CSDL; câu về tài liệu đi RAG loại B; model không được
  bịa số (§2 của `01`).
- **Quyền:** `assistant.read`; `assistant` khai `PUBLIC` trong `SCOPE_FIELDS` vì phạm vi thật nằm ở entity của dữ liệu được tra.
- **Ngoại lệ:** vượt hạn mức ngày trả 429; tắt `AI_ENABLED` thì mọi đường trả 403.

### CN-AI-04 — Công cụ tra cứu loại A

- **Mục đích:** cho model đọc số liệu thật thay vì đoán.
- **Luật nghiệp vụ:** mỗi công cụ có hai lớp quyền (quyền entity `ctx.can` + `apply_scope`), ẩn cột nhạy cảm; mỗi công cụ
  phải được xếp vào một trong bốn bảng (ghi · đọc chứng từ · danh mục dùng chung · cố ý không lọc). Chi tiết:
  [`01`](../tai-lieu-ky-thuat/01-kien-truc-tro-ly-ai.md) §6.3, §7, §8 và [`04`](../tai-lieu-ky-thuat/04-bao-mat-va-van-hanh.md) §4, §5.
- **Liên quan:** thêm công cụ mới theo kỹ năng `.claude/skills/them-cong-cu-mcp/`; công cụ của Tra cứu thị trường ở
  [Hải quan](../../hai-quan/chuc-nang/01-yeu-cau-chuc-nang.md) CN-HQ-21.

### CN-AI-06 — Sửa phiếu có xác nhận

- **Mục đích:** trợ lý đề xuất sửa, người dùng bấm nút mới ghi.
- **Luồng chính:** công cụ `propose_*` trả thẻ đề xuất → người dùng bấm *Xác nhận sửa* → `POST /api/assistant/confirm-update`
  kiểm lại quyền và phạm vi rồi ghi → dòng sổ thay đổi có ảnh trước / sau, hoàn tác được trong 24 giờ.
- **Luật nghiệp vụ:** công cụ có mùi ghi phải khai ở bảng `TOOL_GHI`; tài khoản chỉ có `read` thì mọi công cụ ghi đều bị
  từ chối ([`01`](../tai-lieu-ky-thuat/01-kien-truc-tro-ly-ai.md) §6.4, §6.8). Hoàn tác kiểm lại hạn 24 giờ, chủ sở hữu,
  quyền, phạm vi, trạng thái ([`api.md`](../tai-lieu-ky-thuat/api.md)).

### CN-AI-11 — Kết nối AI riêng

- **Mục đích:** nhân sự dùng ứng dụng AI của chính mình (tự trả tiền model) để đọc ERP dưới đúng tài khoản và quyền.
- **Luồng chính:** cách 1 nối bằng đăng nhập ERP (OAuth, PKCE bắt buộc); cách 2 tạo khóa `dego_mcp_...` (chỉ hiện một lần,
  chọn mức Chỉ đọc / Được ghi, hạn) rồi dán vào ứng dụng. Chi tiết: [`10`](10-ket-noi-ai-rieng-va-kho-skill.md) §2–§4b.
- **Luật nghiệp vụ:** màn hình không dùng chữ *MCP*, *JSON-RPC*; khóa Chỉ đọc không tạo phiếu được; khóa phát hộ phải được
  chủ khóa nhận; tạm tắt / gỡ có hiệu lực tức thì.
- **Ngoại lệ:** bảng lý do từ chối và cách xử ở [`10`](10-ket-noi-ai-rieng-va-kho-skill.md) §7.

### CN-AI-13 — Kho skill AI

- **Mục đích:** cẩm nang công ty soạn một lần, gán theo sơ đồ tổ chức, AI đọc trước khi làm việc nghiệp vụ.
- **Luật nghiệp vụ:** AI chỉ đọc skill đã xuất bản và được gán (`visible_skills` tính lúc gọi); skill không được gán trả
  cùng câu với skill không tồn tại; mức *Bảo vệ* không trả tệp, mức *Khóa* chỉ trả tên và tóm tắt; dòng cấm thắng dòng cho.
  Chi tiết: [`21`](../tai-lieu-ky-thuat/21-kho-skill-ai-mcp.md) §4.2, §4.5 và [`10`](10-ket-noi-ai-rieng-va-kho-skill.md) §5, §6.
- **Quyền:** `ai_skill.read/create/write/delete/approve` (xuất bản cần `approve`).

### CN-AI-22 — AI kế hoạch và phân việc

- **Mục đích:** người nói mục tiêu, AI ra danh sách việc có ước lượng và đề xuất người làm; người quyết.
- **Luật nghiệp vụ:** số do máy tính, AI chỉ viết chữ; hồ sơ hành vi chi tiết chỉ quản trị xem; người khác chỉ thấy kết quả
  đề xuất. Chi tiết: [`22`](../tai-lieu-ky-thuat/22-ai-ke-hoach-phan-viec.md) §2, §4, §6.
- **Liên quan:** bot lập kế hoạch việc vào Dự án ([`agent-hub/18`](../../../agent-hub/18-dieu-phoi-viec-theo-ke-hoach.md)),
  báo cáo 14 / 16 của [Nền tảng](../../nen-tang/chuc-nang/01-yeu-cau-chuc-nang.md) CN-NT-21.

## 4. Luồng trạng thái chứng từ (nếu có)

Khóa kết nối ([`21`](../tai-lieu-ky-thuat/21-kho-skill-ai-mcp.md) §6.2 G5, [`10`](10-ket-noi-ai-rieng-va-kho-skill.md) §7):

```
Chờ nhận (phát hộ) → Đang dùng ⇄ Tạm tắt → Hết hạn / Thu hồi
```

Lượt gọi trong nhật ký MCP: 1 Thành công · 2 Bị từ chối · 3 Lỗi.

## 5. Câu hỏi còn mở

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| 1 | Phòng thử đầu tiên cho AI kế hoạch (đề xuất Thu mua) | Đại ca | chưa có |
| 2 | Ai khai danh mục loại việc cho từng phòng (đề xuất trưởng phòng khai, quản trị duyệt) | Đại ca | chưa có |
| 3 | Kênh thử trước (đề xuất MCP và Trợ lý web) | Đại ca | chưa có |
| 4 | Ký DPA không lưu giữ với Anthropic và Google; danh mục tài liệu tuyệt mật loại khỏi AI | Ban lãnh đạo | chưa có |
| 5 | Khóa model riêng cho prod (đang dùng chung khóa dev) | Đại ca | chưa có |
| 6 | Đóng quyền ngầm `assistant.export` của `pur_manager` (thêm `assistant` vào `_SYS_ENTITIES`) hay giữ | Agent 1 đề xuất, đại ca chốt | chưa có |

Câu 1–5 lấy từ [kế hoạch theo module](../../../plans/00-ke-hoach-theo-module.md) §11 và [`22`](../tai-lieu-ky-thuat/22-ai-ke-hoach-phan-viec.md) §8;
câu 6 từ [`01`](../tai-lieu-ky-thuat/01-kien-truc-tro-ly-ai.md) §6.2.
