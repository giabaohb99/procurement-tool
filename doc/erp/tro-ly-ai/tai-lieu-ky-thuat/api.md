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

> Bảng mục 1 dựng TỰ ĐỘNG ngày 03/11/2026 từ `app.routes` (bao-CR-712): *Mục đích* = dòng đầu docstring (không có thì tên hàm); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* chỉ ghi khi thấy `apply_scope` / `get_scoped` / `scope_condition` ngay trong hàm đường — trống nghĩa là **chưa soát** (có thể lọc ở service). Người phụ trách soát lại và điền cột *Ai gọi*, mục 2–4.

Mã backend: `assistant`, `agent_hub`, `ai_skill`, `ai_plan`, `ai_usage`, `agent_gateway`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/assistant/changes` | Sổ thay đổi của tôi (mới nhất trước), mỗi dòng kèm `can_undo` + `undo_reason`. `all=1` = của mọi người. | `assistant.read` |  | |
| GET | `/api/assistant/changes/{change_id}` | Một dòng sổ kèm ảnh trước / sau. Của người khác (không phải quản lý bot AI) thì 404. | `assistant.read` |  | |
| POST | `/api/assistant/changes/{change_id}/undo` | Hoàn tác một dòng — kiểm lại từ đầu (hạn 24 giờ, chủ sở hữu, quyền, phạm vi, trạng thái, dấu phiếu). | `assistant.read` |  | |
| POST | `/api/assistant/chat` | Gửi một câu hỏi, nhận trả lời + LƯU vào hội thoại (mở mới nếu chưa có id). | `assistant.read` |  | |
| POST | `/api/assistant/confirm-account-setup` | Bước 2 của tool `propose_account_setup` (bao-CR-435): NGƯỜI DÙNG bấm 'Xác nhận' trên | `assistant.read` |  | |
| POST | `/api/assistant/confirm-update` | Bước 2 của tầng GHI có xác nhận (CR-218): NGƯỜI DÙNG bấm 'Xác nhận sửa' trên thẻ | `assistant.read` |  | |
| GET | `/api/assistant/conversations` | Danh sách hội thoại của chính người dùng (mới trước). | `assistant.read` |  | |
| DELETE | `/api/assistant/conversations/{conv_id}` | Xóa hội thoại của chính mình. | `assistant.read` |  | |
| GET | `/api/assistant/conversations/{conv_id}` | Chi tiết hội thoại + toàn bộ tin (chỉ chủ hội thoại xem được). | `assistant.read` |  | |
| GET | `/api/assistant/files/dl/{token}` | ai-CR-207: tải tệp báo cáo bằng đường ký HMAC dùng MỘT lần, 15 phút, KHÔNG cần đăng nhập — cho ứng dụng AI ngoài | — |  | |
| GET | `/api/assistant/files/{file_id}/download` | Tải file báo cáo do tool `export_report_file` sinh ra — CHỈ chủ file tải được. | `assistant.read` |  | |
| GET | `/api/assistant/providers` | Danh sách nhà cung cấp + model mặc định + đã cấu hình key chưa. | `assistant.read` |  | |
| GET | `/api/assistant/rag/index-status` | Đối chiếu số bài HDSD + FAQ dưới DB với số nguồn đang có trong kho vector. | `help_article.write` |  | |
| POST | `/api/assistant/rag/reindex` | Nạp chỉ mục vector loại B (HDSD + FAQ) — đường A, chạy NỀN. | `help_article.write` |  | |
| POST | `/api/assistant/uploads` | Tải MỘT tệp đính kèm chat (CR-204): ảnh JPG/PNG/WebP <= 5MB hoặc PDF <= 10MB. | `assistant.read` |  | |
| GET | `/api/assistant/uploads/{file_id}` | Mở XEM LẠI một tệp đã đính kèm chat (bấm chip trong lịch sử hội thoại). | `assistant.read` |  | |
| GET | `/api/assistant/usage` | Tổng hợp token/số câu theo ngày & theo người — soi chi phí. | `assistant.export` |  | |
| GET | `/api/assistant/usage/mine` | Hạn mức hỏi HÔM NAY của chính người dùng — để giao diện hiện 'còn N câu'. | `assistant.read` |  | |
| GET | `/.well-known/oauth-authorization-server` | as metadata | — |  | |
| GET | `/.well-known/oauth-authorization-server/{rest:path}` | as metadata | — |  | |
| GET | `/.well-known/oauth-protected-resource` | pr metadata | — |  | |
| GET | `/.well-known/oauth-protected-resource/{rest:path}` | pr metadata | — |  | |
| DELETE | `/api/agent-hub/ai-key` | remove my ai key | — |  | |
| GET | `/api/agent-hub/ai-key` | get my ai key | — |  | |
| PUT | `/api/agent-hub/ai-key` | ai-CR-098: nhiều khóa, nhiều hãng. Cùng hãng + cùng ưu tiên = thay khóa; ưu tiên 0 = tự xếp (cùng hãng thì giữ | — |  | |
| GET | `/api/agent-hub/ai-key/company` | get company ai keys | `setting.read` |  | |
| PUT | `/api/agent-hub/ai-key/company` | set company ai key | `setting.write` |  | |
| DELETE | `/api/agent-hub/ai-key/company/{row_id}` | remove company ai key | `setting.write` |  | |
| PATCH | `/api/agent-hub/ai-key/company/{row_id}` | patch company ai key | `setting.write` |  | |
| DELETE | `/api/agent-hub/ai-key/{row_id}` | remove one ai key | — |  | |
| PATCH | `/api/agent-hub/ai-key/{row_id}` | patch my ai key | — |  | |
| GET | `/api/agent-hub/ai-overview` | ai-CR-213 (G1): số liệu màn Tổng quan Kho skill AI / cổng MCP — cùng cổng quyền với nhật ký xem hết. | — |  | |
| GET | `/api/agent-hub/backups` | list db backups | `backup.read` |  | |
| POST | `/api/agent-hub/backups/accept-size` | *Chấp nhận cỡ mới* cho DB bot — cùng nghĩa `/api/backups/accept-size` của ERP. | `backup.delete` |  | |
| POST | `/api/agent-hub/backups/restore-test` | Nạp thử bản mới nhất vào DB tạm rồi xóa — chỉ KIỂM bản sao lưu dùng được, không đụng DB đang chạy. | `backup.create` |  | |
| POST | `/api/agent-hub/backups/run` | run db backup | `backup.create` |  | |
| GET | `/api/agent-hub/backups/{bid}/download` | download db backup | `backup.read` |  | |
| DELETE | `/api/agent-hub/google` | google disconnect | — |  | |
| GET | `/api/agent-hub/google` | my google | — |  | |
| POST | `/api/agent-hub/google/authorize` | google authorize | — |  | |
| GET | `/api/agent-hub/google/callback` | Google gọi về sau màn đồng ý (không có Bearer): danh tính lấy từ `state` đã ký. | — |  | |
| GET | `/api/agent-hub/groups` | list groups | — |  | |
| GET | `/api/agent-hub/groups/meta` | group meta | — |  | |
| GET | `/api/agent-hub/groups/{group_id}` | get group | — |  | |
| PATCH | `/api/agent-hub/groups/{group_id}` | update group | — |  | |
| GET | `/api/agent-hub/groups/{group_id}/files/{message_id}` | Tải tệp gửi trong nhóm (bot tải hộ từ Telegram / Zalo). Tệp chỉ lấy được khi còn trong hạn giữ của kênh. | — |  | |
| GET | `/api/agent-hub/groups/{group_id}/messages` | group messages | — |  | |
| GET | `/api/agent-hub/groups/{group_id}/summaries` | group summaries | — |  | |
| POST | `/api/agent-hub/groups/{group_id}/summarize` | summarize group | — |  | |
| GET | `/api/agent-hub/groups/{group_id}/views` | group views | `agent_group.read` |  | |
| POST | `/api/agent-hub/internal/revoke` | ai-CR-119: ERP (đã tách) báo nhân sự nghỉ — chỉ nhận chữ ký máy-nói-máy, không có người dùng. | — |  | |
| GET | `/api/agent-hub/links` | list my links | — |  | |
| GET | `/api/agent-hub/links/all` | list all links | `agent_group.read` |  | |
| POST | `/api/agent-hub/links/code` | Mã 6 số dùng một lần để nhắn `/dangnhap <mã>` cho bot. Mã cũ chưa dùng bị hủy. | — |  | |
| DELETE | `/api/agent-hub/links/{link_id}` | remove link | — |  | |
| PATCH | `/api/agent-hub/links/{link_id}` | ai-CR-059: mức chuông ERP chuyển sang chat Telegram này — 0 tắt · 1 việc của tôi · 2 tất cả. | — |  | |
| DELETE | `/api/agent-hub/links/{link_id}/admin` | Người quản lý bot AI gỡ liên kết của người khác (nghỉ việc, đổi máy, nối nhầm). | `agent_group.write` |  | |
| GET | `/api/agent-hub/mcp-calls` | list mcp calls | — |  | |
| GET | `/api/agent-hub/mcp-calls/daily` | mcp calls daily | — |  | |
| GET | `/api/agent-hub/mcp-calls/top` | mcp calls top | — |  | |
| POST | `/api/agent-hub/mcp-key-admin/issue` | Phát hộ khóa CHỈ ĐỌC cho một / nhiều người hoặc cả phòng (≤ 50 người một lượt). Người ngoài phạm vi → 403 cả lượt; | — |  | |
| GET | `/api/agent-hub/mcp-key-admin/keys` | key admin list | — |  | |
| GET | `/api/agent-hub/mcp-key-admin/meta` | key admin meta | — |  | |
| POST | `/api/agent-hub/mcp-key-admin/revoke` | Thu hồi: các khóa chỉ định, mọi khóa của một người, hoặc cả một lượt phát. Khóa của người ngoài phạm vi → 403 cả | — |  | |
| GET | `/api/agent-hub/mcp-keys` | list my mcp keys | — |  | |
| POST | `/api/agent-hub/mcp-keys` | create my mcp key | — |  | |
| GET | `/api/agent-hub/mcp-keys/pending` | ai-CR-212: khóa quản trị phát hộ đang chờ mình bấm Nhận. | — |  | |
| DELETE | `/api/agent-hub/mcp-keys/{key_id}` | remove my mcp key | — |  | |
| PATCH | `/api/agent-hub/mcp-keys/{key_id}` | ai-CR-221: bật / tắt tạm khóa của chính mình (cả kết nối OAuth). Tắt thì cổng MCP từ chối với lý do "Khóa đang | — |  | |
| POST | `/api/agent-hub/mcp-keys/{key_id}/claim` | ai-CR-212: nhận khóa phát hộ — khóa thô hiện ĐÚNG một lần; lần sau / khóa của người khác → 404. | — |  | |
| GET | `/api/agent-hub/mcp-keys/{key_id}/last-call` | ai-CR-213 (G8 bước 3 "Kiểm tra kết nối"): lượt gọi gần nhất của MỘT khóa của chính mình. | — |  | |
| GET | `/api/agent-hub/mcp-keys/{key_id}/reveal` | ai-CR-221: CHỦ KHÓA xem lại khóa thô (để chép đoạn cấu hình đã điền khóa). Khóa người khác / đã thu hồi → 404; | — |  | |
| GET | `/api/agent-hub/mcp-settings` | ai-CR-216 (G7): cấu hình cổng MCP — xem cần `agent_group.read`, sửa cần `agent_group.write` (quản lý bot AI, cấp | — |  | |
| PUT | `/api/agent-hub/mcp-settings` | Lưu một phần hay toàn bộ: `{groups?: {mã: bool}, rate_per_key?, rate_per_ip?, bad_key_per_ip?, row_budget_per_min?, | — |  | |
| GET | `/api/agent-hub/mcp-setup` | ai-CR-213 (G8): đoạn cấu hình nối từng ứng dụng AI với ERP; bỏ trống `client` = danh sách ứng dụng. | — |  | |
| GET | `/api/agent-hub/mcp-setup/public` | ai-CR-221 (cho màn công khai /connect-ai của bao-CR-633): cùng nội dung `/mcp-setup` nhưng KHÔNG cần đăng nhập — | — |  | |
| GET | `/api/agent-hub/me/briefs` | my briefs | — |  | |
| PUT | `/api/agent-hub/me/briefs/daily` | set my daily brief | — |  | |
| POST | `/api/agent-hub/me/briefs/topics` | add my topic brief | — |  | |
| DELETE | `/api/agent-hub/me/briefs/{sub_id}` | delete my brief | — |  | |
| PATCH | `/api/agent-hub/me/briefs/{sub_id}` | toggle my brief | — |  | |
| DELETE | `/api/agent-hub/me/memory` | wipe my memory | — |  | |
| GET | `/api/agent-hub/me/memory` | my memory | — |  | |
| PATCH | `/api/agent-hub/me/memory/lines` | edit memory line | — |  | |
| POST | `/api/agent-hub/me/memory/lines` | add memory line | — |  | |
| POST | `/api/agent-hub/me/memory/lines/delete` | delete memory line | — |  | |
| DELETE | `/api/agent-hub/me/memory/notes/{note_id}` | delete memory note | — |  | |
| DELETE | `/api/agent-hub/me/memory/watching/{cand_id}` | drop memory watching | — |  | |
| GET | `/api/agent-hub/oauth-clients` | ai-CR-225 (Agent 1 rà 19/10, mục 3): quản trị xem các ứng dụng AI đã tự đăng ký OAuth — tên tự khai, nơi quay về | — |  | |
| DELETE | `/api/agent-hub/oauth-clients/{client_pk}` | Xóa một ứng dụng OAuth: mọi kết nối của nó bị thu hồi ngay (mã truy cập + mã làm mới chết). | — |  | |
| POST | `/api/agent-hub/oauth/approve` | consent approve | — |  | |
| POST | `/api/agent-hub/oauth/deny` | consent deny | — |  | |
| GET | `/api/agent-hub/oauth/request/{req}` | consent request | — |  | |
| GET | `/api/agent-hub/stats` | Tổng quan: số việc theo trạng thái, chi phí theo ngày và theo bước trong `days` ngày. | `agent_task.read` |  | |
| GET | `/api/agent-hub/tasks` | Việc của bot, mới nhất trước. Lọc theo trạng thái và chữ (mã hoặc tên việc). | `agent_task.read` |  | |
| GET | `/api/agent-hub/tasks/{task_id}` | get task | `agent_task.read` |  | |
| POST | `/api/agent-hub/zalo/login` | zalo login | `agent_group.write` |  | |
| POST | `/api/agent-hub/zalo/logout` | ai-CR-129: ngắt + xóa phiên Zalo công ty (đổi tài khoản). Tin đã ghi giữ nguyên. | `agent_group.write` |  | |
| POST | `/api/agent-hub/zalo/refresh-groups` | zalo refresh groups | `agent_group.write` |  | |
| GET | `/api/agent-hub/zalo/status` | Tình trạng tài khoản Zalo công ty (ai-CR-122). Ảnh QR chỉ trả cho người có `agent_group.write`. | `agent_group.read` |  | |
| DELETE | `/api/mcp` | mcp delete | — |  | |
| GET | `/api/mcp` | mcp get | — |  | |
| POST | `/api/mcp` | mcp endpoint | — |  | |
| GET | `/api/oauth/authorize` | authorize | — |  | |
| POST | `/api/oauth/register` | register client | — |  | |
| POST | `/api/oauth/revoke` | revoke | — |  | |
| POST | `/api/oauth/token` | token | — |  | |
| GET | `/api/ai-skills/access` | list access | `ai_skill.read` |  | |
| POST | `/api/ai-skills/access` | grant access | `ai_skill.write` |  | |
| DELETE | `/api/ai-skills/access/{access_id}` | revoke access | `ai_skill.write` |  | |
| GET | `/api/ai-skills/me` | Skill AI của chính người đang đăng nhập được đọc (đúng thứ cổng MCP sẽ trả). | — |  | |
| GET | `/api/ai-skills/sets` | list sets | `ai_skill.read` |  | |
| POST | `/api/ai-skills/sets` | create set | `ai_skill.create` |  | |
| DELETE | `/api/ai-skills/sets/{set_id}` | delete set | `ai_skill.delete` |  | |
| GET | `/api/ai-skills/sets/{set_id}` | get set | `ai_skill.read` |  | |
| PATCH | `/api/ai-skills/sets/{set_id}` | update set | `ai_skill.write` |  | |
| POST | `/api/ai-skills/sets/{set_id}/import` | Tải gói .zip / .skill. Trùng tên skill trong bộ → THAY GÓI (ghi đè nháp, thay toàn bộ tệp đính kèm). | `ai_skill.write` |  | |
| GET | `/api/ai-skills/sets/{set_id}/skills` | list skills | `ai_skill.read` |  | |
| POST | `/api/ai-skills/sets/{set_id}/skills` | create skill | `ai_skill.write` |  | |
| DELETE | `/api/ai-skills/skills/{skill_id}` | delete skill | `ai_skill.delete` |  | |
| GET | `/api/ai-skills/skills/{skill_id}` | get skill | `ai_skill.read` |  | |
| PATCH | `/api/ai-skills/skills/{skill_id}` | update skill | `ai_skill.write` |  | |
| GET | `/api/ai-skills/skills/{skill_id}/files` | list files | `ai_skill.read` |  | |
| PUT | `/api/ai-skills/skills/{skill_id}/files` | put file | `ai_skill.write` |  | |
| DELETE | `/api/ai-skills/skills/{skill_id}/files/{file_id}` | delete file | `ai_skill.write` |  | |
| POST | `/api/ai-skills/skills/{skill_id}/publish` | publish skill | `ai_skill.approve` |  | |
| GET | `/api/ai-skills/skills/{skill_id}/versions` | list versions | `ai_skill.read` |  | |
| GET | `/api/ai-skills/versions/{version_id}` | get version | `ai_skill.read` |  | |
| GET | `/api/ai-plans` | list ai plans | `work_task.read` |  | |
| GET | `/api/ai-plans/{proposal_id}` | get ai plan | `work_task.read` |  | |
| PUT | `/api/ai-plans/{proposal_id}` | edit ai plan | `work_task.create` |  | |
| POST | `/api/ai-plans/{proposal_id}/approve` | approve ai plan | `work_task.create` |  | |
| POST | `/api/ai-plans/{proposal_id}/reject` | reject ai plan | `work_task.read` |  | |

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
