# TÀI LIỆU API — TRỢ LÝ AI

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (bản dựng tự động từ mã) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

**Tra tham số đầy đủ:** trang `/docs` (Swagger do FastAPI sinh từ mã — dev `https://deverp.degoholding.vn/docs`, prod `https://erp.degoholding.vn/docs`), nhóm (tag) `agent-hub`, `ai-plan`, `ai_skill`, `assistant`, `mcp`, `mcp-oauth`.
Tệp này giữ phần Swagger không nói được: **quyền, phạm vi, luật nghiệp vụ, ai gọi**.

**Phong bì chung:** mọi đường trả `{success, message, data}`; lỗi trả `{success: false, error: {code, message, details}}`.

> Bảng mục 1 dựng TỰ ĐỘNG từ `app.routes` bằng `backend/scripts/dung_bang_api.py` (lần cuối 05/11/2026): *Mục đích* = dòng đầu docstring (không có thì tên hàm — sửa docstring trong mã, đừng sửa tay); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* và *Ai gọi* ghi tay được giữ, chữ *tự dò:* là máy dò từ frontend-v2 và cổng MCP. *Phạm vi* trống nghĩa là **chưa soát** (có thể lọc ở service).

Mã backend: `assistant`, `agent_hub`, `ai_skill`, `ai_plan`, `ai_usage`, `agent_gateway`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/.well-known/oauth-authorization-server` | as metadata | công khai |  |  |
| GET | `/.well-known/oauth-authorization-server/{rest:path}` | as metadata | công khai |  |  |
| GET | `/.well-known/oauth-protected-resource` | pr metadata | công khai |  |  |
| GET | `/.well-known/oauth-protected-resource/{rest:path}` | pr metadata | công khai |  |  |
| GET | `/api/agent-hub/ai-key` | get my ai key | đăng nhập |  | tự dò: v2 `system` |
| PUT | `/api/agent-hub/ai-key` | ai-CR-098: nhiều khóa, nhiều hãng. | đăng nhập |  | tự dò: v2 `system` |
| DELETE | `/api/agent-hub/ai-key` | remove my ai key | đăng nhập |  | tự dò: v2 `system` |
| GET | `/api/agent-hub/ai-key/company` | get company ai keys | `setting.read` |  | tự dò: v2 `system` |
| PUT | `/api/agent-hub/ai-key/company` | set company ai key | `setting.write` |  | tự dò: v2 `system` |
| PATCH | `/api/agent-hub/ai-key/company/{row_id}` | patch company ai key | `setting.write` |  | tự dò: v2 `system` |
| DELETE | `/api/agent-hub/ai-key/company/{row_id}` | remove company ai key | `setting.write` |  | tự dò: v2 `system` |
| PATCH | `/api/agent-hub/ai-key/{row_id}` | patch my ai key | đăng nhập |  | tự dò: v2 `system` |
| DELETE | `/api/agent-hub/ai-key/{row_id}` | remove one ai key | đăng nhập |  | tự dò: v2 `system` |
| GET | `/api/agent-hub/ai-overview` | ai-CR-213 (G1): số liệu màn Tổng quan Kho skill AI / cổng MCP — cùng cổng quyền với nhật ký xem hết. | đăng nhập |  | tự dò: v2 `ai-skill` |
| GET | `/api/agent-hub/backups` | list db backups | `backup.read` |  | tự dò: v2 `system` |
| POST | `/api/agent-hub/backups/accept-size` | *Chấp nhận cỡ mới* cho DB bot — cùng nghĩa `/api/backups/accept-size` của ERP. | `backup.delete` |  |  |
| POST | `/api/agent-hub/backups/restore-test` | Nạp thử bản mới nhất vào DB tạm rồi xóa — chỉ KIỂM bản sao lưu dùng được, không đụng DB đang chạy. | `backup.create` |  |  |
| POST | `/api/agent-hub/backups/run` | run db backup | `backup.create` |  |  |
| GET | `/api/agent-hub/backups/{bid}/download` | download db backup | `backup.read` |  |  |
| GET | `/api/agent-hub/google` | my google | đăng nhập |  | tự dò: v2 `system` |
| DELETE | `/api/agent-hub/google` | google disconnect | đăng nhập |  | tự dò: v2 `system` |
| POST | `/api/agent-hub/google/authorize` | google authorize | đăng nhập |  | tự dò: v2 `system` |
| GET | `/api/agent-hub/google/callback` | Google gọi về sau màn đồng ý (không có Bearer): danh tính lấy từ `state` đã ký. | công khai |  |  |
| GET | `/api/agent-hub/groups` | list groups | đăng nhập |  | tự dò: v2 `assistant` |
| GET | `/api/agent-hub/groups/meta` | group meta | đăng nhập |  | tự dò: v2 `assistant` |
| GET | `/api/agent-hub/groups/{group_id}` | get group | đăng nhập |  | tự dò: v2 `assistant` |
| PATCH | `/api/agent-hub/groups/{group_id}` | update group | đăng nhập |  | tự dò: v2 `assistant` |
| GET | `/api/agent-hub/groups/{group_id}/files/{message_id}` | Tải tệp gửi trong nhóm (bot tải hộ từ Telegram / Zalo). | đăng nhập |  | tự dò: v2 `assistant` |
| GET | `/api/agent-hub/groups/{group_id}/messages` | group messages | đăng nhập |  | tự dò: v2 `assistant` |
| GET | `/api/agent-hub/groups/{group_id}/summaries` | group summaries | đăng nhập |  | tự dò: v2 `assistant` |
| POST | `/api/agent-hub/groups/{group_id}/summarize` | summarize group | đăng nhập |  | tự dò: v2 `assistant` |
| GET | `/api/agent-hub/groups/{group_id}/views` | group views | `agent_group.read` |  | tự dò: v2 `assistant` |
| POST | `/api/agent-hub/internal/revoke` | ai-CR-119: ERP (đã tách) báo nhân sự nghỉ — chỉ nhận chữ ký máy-nói-máy, không có người dùng. | công khai |  |  |
| GET | `/api/agent-hub/links` | list my links | đăng nhập |  | tự dò: v2 `system` |
| GET | `/api/agent-hub/links/all` | list all links | `agent_group.read` |  | tự dò: v2 `assistant` |
| POST | `/api/agent-hub/links/code` | Mã 6 số dùng một lần để nhắn `/dangnhap <mã>` cho bot. | đăng nhập |  | tự dò: v2 `system` |
| PATCH | `/api/agent-hub/links/{link_id}` | ai-CR-059: mức chuông ERP chuyển sang chat Telegram này — 0 tắt · 1 việc của tôi · 2 tất cả. | đăng nhập |  | tự dò: v2 `system` |
| DELETE | `/api/agent-hub/links/{link_id}` | remove link | đăng nhập |  | tự dò: v2 `system` |
| DELETE | `/api/agent-hub/links/{link_id}/admin` | Người quản lý bot AI gỡ liên kết của người khác (nghỉ việc, đổi máy, nối nhầm). | `agent_group.write` |  | tự dò: v2 `assistant` |
| GET | `/api/agent-hub/mcp-calls` | list mcp calls | đăng nhập |  | tự dò: v2 `ai-skill` |
| GET | `/api/agent-hub/mcp-calls/daily` | mcp calls daily | đăng nhập |  |  |
| GET | `/api/agent-hub/mcp-calls/top` | mcp calls top | đăng nhập |  |  |
| POST | `/api/agent-hub/mcp-key-admin/issue` | Phát hộ khóa CHỈ ĐỌC cho một / nhiều người hoặc cả phòng (≤ 50 người một lượt). | đăng nhập |  | tự dò: v2 `ai-skill` |
| GET | `/api/agent-hub/mcp-key-admin/keys` | key admin list | đăng nhập |  | tự dò: v2 `ai-skill` |
| GET | `/api/agent-hub/mcp-key-admin/meta` | key admin meta | đăng nhập |  | tự dò: v2 `ai-skill` |
| POST | `/api/agent-hub/mcp-key-admin/revoke` | Thu hồi: các khóa chỉ định, mọi khóa của một người, hoặc cả một lượt phát. | đăng nhập |  | tự dò: v2 `ai-skill` |
| GET | `/api/agent-hub/mcp-keys` | list my mcp keys | đăng nhập |  | tự dò: v2 `ai-skill`, v2 `system` |
| POST | `/api/agent-hub/mcp-keys` | create my mcp key | đăng nhập |  | tự dò: v2 `ai-skill`, v2 `system` |
| GET | `/api/agent-hub/mcp-keys/pending` | ai-CR-212: khóa quản trị phát hộ đang chờ mình bấm Nhận. | đăng nhập |  | tự dò: v2 `ai-skill` |
| PATCH | `/api/agent-hub/mcp-keys/{key_id}` | ai-CR-221: bật / tắt tạm khóa của chính mình (cả kết nối OAuth). | đăng nhập |  | tự dò: v2 `ai-skill`, v2 `system` |
| DELETE | `/api/agent-hub/mcp-keys/{key_id}` | remove my mcp key | đăng nhập |  | tự dò: v2 `ai-skill`, v2 `system` |
| POST | `/api/agent-hub/mcp-keys/{key_id}/claim` | ai-CR-212: nhận khóa phát hộ — khóa thô hiện ĐÚNG một lần; lần sau / khóa của người khác → 404. | đăng nhập |  | tự dò: v2 `ai-skill` |
| GET | `/api/agent-hub/mcp-keys/{key_id}/last-call` | ai-CR-213 (G8 bước 3 "Kiểm tra kết nối"): lượt gọi gần nhất của MỘT khóa của chính mình. | đăng nhập |  | tự dò: v2 `ai-skill` |
| GET | `/api/agent-hub/mcp-keys/{key_id}/reveal` | ai-CR-221: CHỦ KHÓA xem lại khóa thô (để chép đoạn cấu hình đã điền khóa). | đăng nhập |  | tự dò: v2 `ai-skill` |
| GET | `/api/agent-hub/mcp-settings` | ai-CR-216 (G7): cấu hình cổng MCP — xem cần `agent_group.read`, sửa cần `agent_group.write` (quản lý bot AI, cấp hệ thống; KHÔNG dùng `ai_skill.write` vì vai trò Biên tập skill phòng ban cũng có quyền đó mà cấu hình… | đăng nhập |  | tự dò: v2 `ai-skill` |
| PUT | `/api/agent-hub/mcp-settings` | Lưu một phần hay toàn bộ: `{groups?: {mã: bool}, rate_per_key?, rate_per_ip?, bad_key_per_ip?, row_budget_per_min?, log_retention_days?, extra_instructions?}`. | đăng nhập |  | tự dò: v2 `ai-skill` |
| GET | `/api/agent-hub/mcp-setup` | ai-CR-213 (G8): đoạn cấu hình nối từng ứng dụng AI với ERP; bỏ trống `client` = danh sách ứng dụng. | đăng nhập |  | tự dò: v2 `ai-skill` |
| GET | `/api/agent-hub/mcp-setup/public` | ai-CR-221 (cho màn công khai /connect-ai của bao-CR-633): cùng nội dung `/mcp-setup` nhưng KHÔNG cần đăng nhập — chỉ địa chỉ cổng + hướng dẫn tĩnh, đoạn cấu hình mang chỗ giữ khóa `placeholder`, không bao giờ có khóa… | công khai |  | tự dò: v2 `ai-skill` |
| GET | `/api/agent-hub/me/briefs` | my briefs | đăng nhập |  | tự dò: v2 `system` |
| PUT | `/api/agent-hub/me/briefs/daily` | set my daily brief | đăng nhập |  | tự dò: v2 `system` |
| POST | `/api/agent-hub/me/briefs/topics` | add my topic brief | đăng nhập |  | tự dò: v2 `system` |
| PATCH | `/api/agent-hub/me/briefs/{sub_id}` | toggle my brief | đăng nhập |  | tự dò: v2 `system` |
| DELETE | `/api/agent-hub/me/briefs/{sub_id}` | delete my brief | đăng nhập |  | tự dò: v2 `system` |
| GET | `/api/agent-hub/me/memory` | my memory | đăng nhập |  | tự dò: v2 `system` |
| DELETE | `/api/agent-hub/me/memory` | wipe my memory | đăng nhập |  | tự dò: v2 `system` |
| POST | `/api/agent-hub/me/memory/lines` | add memory line | đăng nhập |  | tự dò: v2 `system` |
| PATCH | `/api/agent-hub/me/memory/lines` | edit memory line | đăng nhập |  | tự dò: v2 `system` |
| POST | `/api/agent-hub/me/memory/lines/delete` | delete memory line | đăng nhập |  | tự dò: v2 `system` |
| DELETE | `/api/agent-hub/me/memory/notes/{note_id}` | delete memory note | đăng nhập |  | tự dò: v2 `system` |
| DELETE | `/api/agent-hub/me/memory/watching/{cand_id}` | drop memory watching | đăng nhập |  | tự dò: v2 `system` |
| GET | `/api/agent-hub/oauth-clients` | ai-CR-225 (Agent 1 rà 19/10, mục 3): quản trị xem các ứng dụng AI đã tự đăng ký OAuth — tên tự khai, nơi quay về (hostname), có thuộc ứng dụng quen không, số kết nối còn sống. | đăng nhập |  | tự dò: v2 `ai-skill` |
| DELETE | `/api/agent-hub/oauth-clients/{client_pk}` | Xóa một ứng dụng OAuth: mọi kết nối của nó bị thu hồi ngay (mã truy cập + mã làm mới chết). | đăng nhập |  | tự dò: v2 `ai-skill` |
| POST | `/api/agent-hub/oauth/approve` | consent approve | đăng nhập |  |  |
| POST | `/api/agent-hub/oauth/deny` | consent deny | đăng nhập |  |  |
| GET | `/api/agent-hub/oauth/request/{req}` | consent request | đăng nhập |  | tự dò: v2 dùng chung |
| GET | `/api/agent-hub/stats` | Tổng quan: số việc theo trạng thái, chi phí theo ngày và theo bước trong `days` ngày. | `agent_task.read` |  | tự dò: v2 `system` |
| GET | `/api/agent-hub/tasks` | Việc của bot, mới nhất trước. | `agent_task.read` |  | tự dò: v2 `system` |
| GET | `/api/agent-hub/tasks/{task_id}` | get task | `agent_task.read` |  | tự dò: v2 `system` |
| POST | `/api/agent-hub/zalo/login` | zalo login | `agent_group.write` |  | tự dò: v2 `assistant` |
| POST | `/api/agent-hub/zalo/logout` | ai-CR-129: ngắt + xóa phiên Zalo công ty (đổi tài khoản). | `agent_group.write` |  | tự dò: v2 `assistant` |
| POST | `/api/agent-hub/zalo/refresh-groups` | zalo refresh groups | `agent_group.write` |  | tự dò: v2 `assistant` |
| GET | `/api/agent-hub/zalo/status` | Tình trạng tài khoản Zalo công ty (ai-CR-122). | `agent_group.read` |  | tự dò: v2 `assistant` |
| GET | `/api/ai-plans` | list ai plans | `work_task.read` |  | tự dò: v2 `work` |
| GET | `/api/ai-plans/{proposal_id}` | get ai plan | `work_task.read` |  | tự dò: v2 `work` |
| PUT | `/api/ai-plans/{proposal_id}` | edit ai plan | `work_task.create` |  | tự dò: v2 `work` |
| POST | `/api/ai-plans/{proposal_id}/approve` | approve ai plan | `work_task.create` |  | tự dò: v2 `work` |
| POST | `/api/ai-plans/{proposal_id}/reject` | reject ai plan | `work_task.read` |  | tự dò: v2 `work` |
| GET | `/api/ai-skills/access` | list access | `ai_skill.read` |  | tự dò: v2 `ai-skill` |
| POST | `/api/ai-skills/access` | grant access | `ai_skill.write` |  | tự dò: v2 `ai-skill` |
| DELETE | `/api/ai-skills/access/{access_id}` | revoke access | `ai_skill.write` |  | tự dò: v2 `ai-skill` |
| GET | `/api/ai-skills/me` | Skill AI của chính người đang đăng nhập được đọc (đúng thứ cổng MCP sẽ trả). | đăng nhập |  | tự dò: v2 `ai-skill` |
| GET | `/api/ai-skills/sets` | list sets | `ai_skill.read` |  | tự dò: v2 `ai-skill` |
| POST | `/api/ai-skills/sets` | create set | `ai_skill.create` |  | tự dò: v2 `ai-skill` |
| GET | `/api/ai-skills/sets/{set_id}` | get set | `ai_skill.read` |  | tự dò: v2 `ai-skill` |
| PATCH | `/api/ai-skills/sets/{set_id}` | update set | `ai_skill.write` |  | tự dò: v2 `ai-skill` |
| DELETE | `/api/ai-skills/sets/{set_id}` | delete set | `ai_skill.delete` |  | tự dò: v2 `ai-skill` |
| POST | `/api/ai-skills/sets/{set_id}/import` | Tải gói .zip / .skill. | `ai_skill.write` |  | tự dò: v2 `ai-skill` |
| GET | `/api/ai-skills/sets/{set_id}/skills` | list skills | `ai_skill.read` |  | tự dò: v2 `ai-skill` |
| POST | `/api/ai-skills/sets/{set_id}/skills` | create skill | `ai_skill.write` |  | tự dò: v2 `ai-skill` |
| GET | `/api/ai-skills/skills/{skill_id}` | get skill | `ai_skill.read` |  | tự dò: v2 `ai-skill` |
| PATCH | `/api/ai-skills/skills/{skill_id}` | update skill | `ai_skill.write` |  | tự dò: v2 `ai-skill` |
| DELETE | `/api/ai-skills/skills/{skill_id}` | delete skill | `ai_skill.delete` |  | tự dò: v2 `ai-skill` |
| GET | `/api/ai-skills/skills/{skill_id}/files` | list files | `ai_skill.read` |  | tự dò: v2 `ai-skill` |
| PUT | `/api/ai-skills/skills/{skill_id}/files` | put file | `ai_skill.write` |  | tự dò: v2 `ai-skill` |
| DELETE | `/api/ai-skills/skills/{skill_id}/files/{file_id}` | delete file | `ai_skill.write` |  | tự dò: v2 `ai-skill` |
| POST | `/api/ai-skills/skills/{skill_id}/publish` | publish skill | `ai_skill.approve` |  | tự dò: v2 `ai-skill` |
| GET | `/api/ai-skills/skills/{skill_id}/versions` | list versions | `ai_skill.read` |  | tự dò: v2 `ai-skill` |
| GET | `/api/ai-skills/versions/{version_id}` | get version | `ai_skill.read` |  | tự dò: v2 `ai-skill` |
| GET | `/api/assistant/changes` | Sổ thay đổi của tôi (mới nhất trước), mỗi dòng kèm `can_undo` + `undo_reason`. | `assistant.read` |  | tự dò: v2 `system` |
| GET | `/api/assistant/changes/{change_id}` | Một dòng sổ kèm ảnh trước / sau. | `assistant.read` |  | tự dò: v2 `system` |
| POST | `/api/assistant/changes/{change_id}/undo` | Hoàn tác một dòng — kiểm lại từ đầu (hạn 24 giờ, chủ sở hữu, quyền, phạm vi, trạng thái, dấu phiếu). | `assistant.read` |  | tự dò: v2 `system` |
| POST | `/api/assistant/chat` | Gửi một câu hỏi, nhận trả lời + LƯU vào hội thoại (mở mới nếu chưa có id). | `assistant.read` |  | tự dò: v2 `assistant` |
| POST | `/api/assistant/confirm-account-setup` | Bước 2 của tool `propose_account_setup` (bao-CR-435): NGƯỜI DÙNG bấm 'Xác nhận' trên thẻ đề xuất lập bộ tài khoản thu mua. | `assistant.read` |  | tự dò: v2 `assistant` |
| POST | `/api/assistant/confirm-update` | Bước 2 của tầng GHI có xác nhận (CR-218): NGƯỜI DÙNG bấm 'Xác nhận sửa' trên thẻ đề xuất do tool `propose_document_update` sinh ra. | `assistant.read` |  | tự dò: v2 `assistant` |
| GET | `/api/assistant/conversations` | Danh sách hội thoại của chính người dùng (mới trước). | `assistant.read` |  | tự dò: v2 `assistant` |
| GET | `/api/assistant/conversations/{conv_id}` | Chi tiết hội thoại + toàn bộ tin (chỉ chủ hội thoại xem được). | `assistant.read` |  | tự dò: v2 `assistant` |
| DELETE | `/api/assistant/conversations/{conv_id}` | Xóa hội thoại của chính mình. | `assistant.read` |  | tự dò: v2 `assistant` |
| GET | `/api/assistant/files/dl/{token}` | ai-CR-207: tải tệp báo cáo bằng đường ký HMAC dùng MỘT lần, 15 phút, KHÔNG cần đăng nhập — cho ứng dụng AI ngoài (Claude Desktop qua cổng MCP) không có JWT web. | công khai |  |  |
| GET | `/api/assistant/files/{file_id}/download` | Tải file báo cáo do tool `export_report_file` sinh ra — CHỈ chủ file tải được. | `assistant.read` |  | tự dò: cổng MCP |
| GET | `/api/assistant/providers` | Danh sách nhà cung cấp + model mặc định + đã cấu hình key chưa. | `assistant.read` |  | tự dò: v2 `assistant` |
| GET | `/api/assistant/rag/index-status` | Đối chiếu số bài HDSD + FAQ dưới DB với số nguồn đang có trong kho vector. | `help_article.write` |  | tự dò: v2 `system` |
| POST | `/api/assistant/rag/reindex` | Nạp chỉ mục vector loại B (HDSD + FAQ) — đường A, chạy NỀN. | `help_article.write` |  | tự dò: v2 `system` |
| POST | `/api/assistant/uploads` | Tải MỘT tệp đính kèm chat (CR-204): ảnh JPG/PNG/WebP <= 5MB hoặc PDF <= 10MB. | `assistant.read` |  | tự dò: v2 `assistant` |
| GET | `/api/assistant/uploads/{file_id}` | Mở XEM LẠI một tệp đã đính kèm chat (bấm chip trong lịch sử hội thoại). | `assistant.read` |  | tự dò: v2 `assistant` |
| GET | `/api/assistant/usage` | Tổng hợp token/số câu theo ngày & theo người — soi chi phí. | `assistant.export` |  |  |
| GET | `/api/assistant/usage/mine` | Hạn mức hỏi HÔM NAY của chính người dùng — để giao diện hiện 'còn N câu'. | `assistant.read` |  |  |
| GET | `/api/mcp` | mcp get | công khai |  | tự dò: cổng MCP |
| POST | `/api/mcp` | mcp endpoint | công khai |  | tự dò: cổng MCP |
| DELETE | `/api/mcp` | mcp delete | công khai |  | tự dò: cổng MCP |
| GET | `/api/oauth/authorize` | authorize | công khai |  | tự dò: v2 dùng chung |
| POST | `/api/oauth/register` | register client | công khai |  |  |
| POST | `/api/oauth/revoke` | revoke | công khai |  |  |
| POST | `/api/oauth/token` | token | công khai |  |  |

## 2. Dữ liệu vào / ra chính

Chưa có — người phụ trách điền các trường mang luật nghiệp vụ.

## 3. Lỗi riêng của phân hệ

Chưa có.

## 4. Bộ lọc danh sách

Chưa có.

## 5. Thay đổi gần đây

| Ngày | CR | Đổi gì (thêm / sửa / bỏ đường) |
|---|---|---|
| 03/11/2026 | bao-CR-712 | Dựng bản đầu từ mã |
