# Mục lục quy định: luật, skill, agent

| | |
|---|---|
| Bản | 1.0 |
| Ngày | 03/11/2026 |
| Người phụ trách | A1 Điều phối (chạy bài kiểm, nhắc); người thêm luật / skill tự thêm dòng |
| Trạng thái | Hiệu lực |
| CR liên quan | bao-CR-712 (đề xuất [`de-xuat-to-chuc-lai-tai-lieu.md`](../de-xuat-to-chuc-lai-tai-lieu.md) mục 2.2) |

Luật, skill và định nghĩa agent phải nằm ở chỗ công cụ (Claude Code, Codex) đọc thẳng nên **không dời vào `doc/`**.
Tệp này chỉ là MỤC LỤC trỏ tới tệp thật — không chép nội dung. **Thêm luật / skill / agent mới thì thêm một dòng ở đây
trong cùng commit**; `backend/scripts/kiem_tai_lieu.py` chặn (exit 1) khi thiếu.

## 1. Luật chung (luôn áp dụng)

| Tên | Khi nào nạp | Ai giữ | Nội dung |
|---|---|---|---|
| [`CLAUDE.md`](../../../CLAUDE.md) | luôn (cốt lõi kiến trúc, lệnh, phân quyền) | A1 Điều phối | Kiến trúc backend / frontend, hai trục phân quyền, lệnh Docker, luật trạng thái R2 |
| [`chung-dat-ten-va-quy-uoc.md`](../../../.claude/rules/chung-dat-ten-va-quy-uoc.md) | luôn (không khai `paths:`) | A1 Điều phối | Đặt tên hàm / biến / tệp, ngôn ngữ chuỗi / chú thích, không emoji, trạng thái, commit, bài kiểm |
| [`chung-tai-lieu.md`](../../../.claude/rules/chung-tai-lieu.md) | khi sửa `doc/**` | A1 Điều phối | Khuôn thư mục tài liệu, 10 luật, chỗ ghi kế hoạch |
| [`AGENTS.md`](../../../AGENTS.md) | Codex đọc | A1 Điều phối | Chỉ trỏ sang `CLAUDE.md` và `.claude/rules/` |

## 2. Luật theo khu (nạp khi sửa đúng thư mục ở dòng `paths:`)

| Tên | Khi nào nạp | Ai giữ | Nội dung |
|---|---|---|---|
| [`backend-input-limits.md`](../../../.claude/rules/backend-input-limits.md) | `backend/app/**`, `test/backend/**` | Agent backend | Cột `String(n)` phải có `max_length`, trần JSON / ngày / số dòng |
| [`document-folders-search.md`](../../../.claude/rules/document-folders-search.md) | `document/`, `doc_catalog/`, migrations | Agent văn thư | Thư mục văn bản, chỉ mục tìm toàn văn, bẫy FULLTEXT |
| [`frontend-v1-frozen.md`](../../../.claude/rules/frontend-v1-frozen.md) | `frontend/`, `help-center/` | A1 Điều phối | Bản V1 đóng băng: CRUD khai báo, `can()`, Help Center |
| [`frontend-v2-migration-status.md`](../../../.claude/rules/frontend-v2-migration-status.md) | `frontend/`, `frontend-v2/` | A3 Giao diện | Tiến độ dời màn V1 → V2 (Đ-01…Đ-15) |
| [`frontend-v2-ui-conventions.md`](../../../.claude/rules/frontend-v2-ui-conventions.md) | `frontend-v2/src/**` | A3 Giao diện | `LinesTable`, ô chỉ xem, trường bắt buộc, bẫy biểu mẫu / bảng |
| [`hr-employee-profile.md`](../../../.claude/rules/hr-employee-profile.md) | `employee/`, `hr/`, seed | Anh Dược | Hồ sơ nhân sự mở rộng, `employee_sensitive`, Chức vụ |
| [`hr-labor-contract-variables.md`](../../../.claude/rules/hr-labor-contract-variables.md) | `labor_contract/`, `hr/`, test `*hdld*` | Anh Dược | Biến mẫu HĐLĐ động |
| [`hr-leave.md`](../../../.claude/rules/hr-leave.md) | `leave/`, `approval/`, `hr/` | Anh Dược | Nghỉ phép: quyền, quỹ, đơn nhiều loại |
| [`backend/.claude/rules/naming.md`](../../../backend/.claude/rules/naming.md) | khi mở phiên trong `backend/` | A1 Điều phối | Chỉ trỏ sang luật chung |
| [`frontend-v2/.claude/rules/components.md`](../../../frontend-v2/.claude/rules/components.md) | `frontend-v2/` | A3 Giao diện | Cách dựng component |
| [`frontend-v2/.claude/rules/icons.md`](../../../frontend-v2/.claude/rules/icons.md) | `frontend-v2/` | A3 Giao diện | Bộ icon, cách dùng |
| [`frontend-v2/.claude/rules/naming.md`](../../../frontend-v2/.claude/rules/naming.md) | `frontend-v2/` | A3 Giao diện | Tệp kebab-case, thư mục phân hệ, query key, barrel (phần riêng v2) |
| [`frontend-v2/.claude/rules/styling.md`](../../../frontend-v2/.claude/rules/styling.md) | `frontend-v2/` | A3 Giao diện | Tailwind, màu, khoảng cách |
| [`frontend-v2/.claude/rules/testing.md`](../../../frontend-v2/.claude/rules/testing.md) | `frontend-v2/` | A3 Giao diện | Vitest, ba cổng kiểm, chạy theo thư mục |
| [`frontend-v2/.claude/rules/typescript.md`](../../../frontend-v2/.claude/rules/typescript.md) | `frontend-v2/` | A3 Giao diện | Kiểu TypeScript, cấm `any` |
| [`frontend-v2/.claude/rules/ui.md`](../../../frontend-v2/.claude/rules/ui.md) | `frontend-v2/` | A3 Giao diện | Quy ước giao diện chung |

## 3. Skill và agent

### 3.1. Skill của dự án (`.claude/skills/`)

| Tên | Khi nào dùng | Ai giữ |
|---|---|---|
| [`ba-che-do-agent`](../../../.claude/skills/ba-che-do-agent/SKILL.md) | Sửa agent_hub / assistant / ai_skill / agent_gateway; tính năng chạy local mà hỏng dev / prod | Agent 4 (AI) |
| [`he-agent-bao-cao-xong-viec`](../../../.claude/skills/he-agent-bao-cao-xong-viec/SKILL.md) | Xong một việc: báo 3–4 dòng, cập nhật Dự án | A1 Điều phối |
| [`he-agent-cai-tien`](../../../.claude/skills/he-agent-cai-tien/SKILL.md) | Hằng tuần: học từ sổ quyết định, đề xuất mức tự quyết | A1 Điều phối |
| [`he-agent-nam-tinh-hinh`](../../../.claude/skills/he-agent-nam-tinh-hinh/SKILL.md) | Đầu phiên điều phối, khi hỏi "làm tới đâu rồi" | A1 Điều phối |
| [`he-agent-ra-ma-doc-lap`](../../../.claude/skills/he-agent-ra-ma-doc-lap/SKILL.md) | Agent rà mã trước khi gộp erp-v2 | A1 Điều phối |
| [`he-agent-truoc-khi-hoi`](../../../.claude/skills/he-agent-truoc-khi-hoi/SKILL.md) | Mỗi lần định hỏi người chủ | A1 Điều phối |
| [`he-agent-viec-chen-ngang`](../../../.claude/skills/he-agent-viec-chen-ngang/SKILL.md) | Việc mới chen ngang việc đang làm | A1 Điều phối |
| [`recap-hom-qua`](../../../.claude/skills/recap-hom-qua/SKILL.md) | "Hôm qua có gì mới", recap theo người | A1 Điều phối |
| [`soat-man-dev`](../../../.claude/skills/soat-man-dev/SKILL.md) | Soát màn mới trên dev trước khi gộp / lên prod | Agent tài liệu - kiểm thử |
| [`them-cong-cu-mcp`](../../../.claude/skills/them-cong-cu-mcp/SKILL.md) | Thêm / đổi công cụ cho MCP, Trợ lý web, bot | Agent 4 (AI) |
| [`them-entity-moi`](../../../.claude/skills/them-entity-moi/SKILL.md) | Thêm khóa phân quyền mới (bảy sổ đăng ký) | Agent backend |
| [`them-man-v2`](../../../.claude/skills/them-man-v2/SKILL.md) | Thêm màn / phân hệ ở frontend-v2 | A3 Giao diện |
| [`viet-hdsd`](../../../.claude/skills/viet-hdsd/SKILL.md) | Viết / sửa bài HDSD (`seed_help_*.py`) + tài liệu chức năng | Agent tài liệu - kiểm thử |

### 3.2. Skill toàn máy (`~/.claude/skills/`, không nằm trong repo)

Cài máy mới thì chép đủ bộ này (bản tham khảo ở `~/.claude/references`).

| Tên | Mục đích |
|---|---|
| `code-review-and-quality` | Rà mã nhiều trục trước khi gộp |
| `code-simplification` | Làm gọn mã không đổi hành vi |
| `debugging-and-error-recovery` | Gỡ lỗi tìm nguyên nhân gốc |
| `documentation-and-adrs` | Ghi quyết định kiến trúc, tài liệu API |
| `graphify` | Dựng đồ thị tri thức từ mã / tài liệu (`/graphify`) |
| `planning-and-task-breakdown` | Chia việc lớn thành bước — kế hoạch ghi vào `doc/erp/<phan-he>/plans/` |
| `ponytail`, `ponytail-audit`, `ponytail-debt`, `ponytail-gain`, `ponytail-help`, `ponytail-review` | Chống làm quá: giải pháp gọn nhất, rà mã thừa |
| `security-and-hardening` | Rà bảo mật đầu vào, xác thực, dữ liệu cá nhân |
| `spec-driven-development` | Viết đặc tả trước khi làm |
| `test-driven-development` | Đỏ → xanh → làm gọn |

### 3.3. Định nghĩa agent (`.claude/agents/`)

| Tên | Khi nào dùng | Ai giữ |
|---|---|---|
| [`ai-mcp`](../../../.claude/agents/ai-mcp.md) | Dịch vụ AI: cổng MCP, Kho skill, Trợ lý web, bot, cổng B | Agent 4 (AI) |
| [`dieu-phoi`](../../../.claude/agents/dieu-phoi.md) | Chia việc, gộp nhánh, dựng dev, phát hành prod, cấp số CR | A1 Điều phối |
| [`giao-dien-v2`](../../../.claude/agents/giao-dien-v2.md) | Màn, phân hệ, hộp thoại, bảng ở frontend-v2 | A3 Giao diện |
| [`tai-lieu-kiem-thu`](../../../.claude/agents/tai-lieu-kiem-thu.md) | Bài HDSD, tài liệu chức năng, soát màn dev | Agent tài liệu - kiểm thử |

## 4. Khuôn mẫu tài liệu phân hệ

Bốn tệp bắt buộc của mỗi `doc/erp/<phan-he>/` (luật ở `chung-tai-lieu.md`, người chủ chốt 03/11/2026). Chép khuôn rồi điền.

| Khuôn | Tạo thành | Nội dung |
|---|---|---|
| [`mau-readme-phan-he.md`](mau/mau-readme-phan-he.md) | `README.md` | Phân hệ là gì, tới đâu, đọc gì trước, mục lục, mã nguồn |
| [`mau-yeu-cau-chuc-nang.md`](mau/mau-yeu-cau-chuc-nang.md) | `chuc-nang/01-yeu-cau-chuc-nang.md` | Vai trò, danh sách chức năng mã `CN-*`, chi tiết từng chức năng, luồng trạng thái, câu hỏi mở |
| [`mau-yeu-cau-phi-chuc-nang.md`](mau/mau-yeu-cau-phi-chuc-nang.md) | `chuc-nang/02-yeu-cau-phi-chuc-nang.md` | 12 nhóm yêu cầu mã `PCN-*`: hiệu năng, phân quyền, dữ liệu nhạy cảm, giới hạn đầu vào, nhật ký, lưu trữ, sao lưu, đồng thời, tích hợp, thiết bị, pháp lý, vận hành — mỗi dòng có mức đo và cách kiểm |
| [`mau-tai-lieu-api.md`](mau/mau-tai-lieu-api.md) | `tai-lieu-ky-thuat/api.md` | Bảng đường API: quyền, phạm vi, ai gọi; trường mang luật; lỗi riêng; bộ lọc. Tham số đầy đủ tra trang `/api/docs` (chỉ dev và local, prod tắt) |
