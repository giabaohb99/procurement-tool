# Rà mã phần trợ lý không lộ lương (duoc-CR-757)

| | |
|---|---|
| Ngày | 13/11/2026 |
| Kết luận | Trả lại |

## Chặn

- **C1.** `search_chat_history` (`agent_hub/personal_memory.py:470-505`, mở trên MCP qua nhóm `mine`) trả lại câu bot đã
  trả lời ở mọi chat, kể cả câu `my_salary` trả lương ở chat riêng → lương của chính chủ ra MCP. Sửa: lọc dòng có
  lương / phụ cấp / thu nhập khi kênh không riêng (hoặc gắn cờ lượt có gọi `my_salary`), thêm bài kiểm MCP.

## Nên sửa

- **N1.** Cờ kênh riêng/chung đọc từ `args._conversation` (`tools/__init__.py:167-175`, `salary_privacy.py:43-45`); chỉ
  `core_v2._answer` ghi đè. Đường `/hoi` (`agent_hub/service.answer_question` → `assistant/service.py:417/428`) để model
  tự điền. Sửa: ContextVar gắn cùng `ai_channel_scope(...)` (`service.py:404`) + header đã ký ở cổng B; bỏ đọc từ `args`.
  Kèm lỗi chức năng: `/hoi lương của tôi` ở chat riêng bị từ chối oan.
- **N2.** `INSTRUCTIONS` của MCP (`mcp.py:34`) chưa có luật lương; công cụ trả chữ tự do (`document_read`, `drive_read`,
  `read_group_messages`, `read_group_file`) có thể đọc nguyên văn quyết định lương. Thêm câu luật + mẫu `core_eval`.
- **N3.** Tài liệu: `.claude/rules/hr-employee-profile.md:297`, `doc/erp/tro-ly-ai/tai-lieu-ky-thuat/02-danh-sach-api-tool.md`,
  `04-bao-mat-va-van-hanh.md`, `doc/agent-hub/06-cong-mcp.md`; sau deploy chạy `backend/scripts/publish_handbook_update.py`.

## Gợi ý

- G1 `_SECRET_RE` (`personal_memory.py:56`) thêm lương / phụ cấp / thu nhập để không tự rút vào sổ nhớ.
- G2 `leave_encashment_tool.py:35` trả `decision_note` chữ tự do (có thể ghi đơn giá) — bỏ hoặc gác kênh riêng.
- G3 `User.employee_id` không UNIQUE: người có `user.write` gắn tài khoản mình vào hồ sơ người khác là đọc được lương
  (ngoài CR này).
- G4 Chat chưa liên kết lùi về `AGENT_ASSISTANT_USER` (`service.py:4061`) → `my_salary` phải đòi liên kết thật.
- G5 `\bluong\b` (`tool_router.py:84`) khớp cả "luồng" sau khi bỏ dấu.

## Đã kiểm, đạt

`my_salary` không có tham số chọn người, chặn `employee_id = 0`, qua `sensitive.mask` + `is_self`; tiền YCTT thanh toán
nghỉ phép giấu ở `payment_request_read`, `pending_procurement_approvals`, `dataset_query`, `_fetch_by_code`; hộp duyệt
chỉ có số ngày; `report_summary` không mở Quỹ lương; `employee_lookup` có `NEVER_FIELDS`; nhật ký không giữ số.
