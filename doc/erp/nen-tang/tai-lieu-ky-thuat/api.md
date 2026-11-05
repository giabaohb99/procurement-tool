# TÀI LIỆU API — NỀN TẢNG DÙNG CHUNG

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (bản dựng tự động từ mã) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

**Tra tham số đầy đủ:** trang `/docs` (Swagger do FastAPI sinh từ mã — dev `https://deverp.degoholding.vn/docs`, prod `https://erp.degoholding.vn/docs`), nhóm (tag) `alert`, `approval`, `approval-delegation`, `approval-flow`, `attachment`, `audit`, `auth`, `backup`, `comment`, `company`, `dashboard`, `department`, `email-exclusion`, `email-template`, `export`, `faq`, `feature-usage`, `help_center`, `import`, `login-session`, `mailbox`, `meta`, `notification`, `push`, `report`, `report_access`, `role`, `setting`, `sync-log`, `system-jobs`, `system-log`, `telemetry`, `ticket`, `usage-profile`, `user`, `user_preference`, `work-capability`.
Tệp này giữ phần Swagger không nói được: **quyền, phạm vi, luật nghiệp vụ, ai gọi**.

**Phong bì chung:** mọi đường trả `{success, message, data}`; lỗi trả `{success: false, error: {code, message, details}}`.

> Bảng mục 1 dựng TỰ ĐỘNG từ `app.routes` bằng `backend/scripts/dung_bang_api.py` (lần cuối 05/11/2026): *Mục đích* = dòng đầu docstring (không có thì tên hàm — sửa docstring trong mã, đừng sửa tay); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* và *Ai gọi* ghi tay được giữ, chữ *tự dò:* là máy dò từ frontend-v2 và cổng MCP. *Phạm vi* trống nghĩa là **chưa soát** (có thể lọc ở service).

Mã backend: `approval`, `notification`, `comment`, `ticket`, `attachment`, `import_tool`, `export_log`, `dashboard`, `meta`, `user_preference`, `push`, `help_center`, `faq`, `alert`, `report`, `report_access`, `setting`, `system_log`, `job_run`, `audit`, `login_session`, `auth`, `user`, `role`, `company`, `department`, `sync_log`, `backup`, `feature_usage`, `usage_profile`, `capability`, `release_info`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/alerts` | list alerts | đăng nhập |  | tự dò: v2 dùng chung |
| GET | `/api/approval-flows` | list flows | `approval_flow.read` | `apply_scope` | tự dò: v2 `approval` |
| POST | `/api/approval-flows` | create flow | `approval_flow.create` |  | tự dò: v2 `approval` |
| GET | `/api/approval-flows/options` | Nhãn tiếng Việt do backend cấp — giao diện không chép cứng. | `approval_flow.read` |  | tự dò: v2 `approval` |
| GET | `/api/approval-flows/permission-approvers` | Ai đang giữ quyền Duyệt trên khóa `entity` — cho cách chọn "Người có quyền duyệt" (duoc-CR-680). | `approval_flow.read` |  | tự dò: v2 `approval` |
| GET | `/api/approval-flows/switches` | list switches | `approval_flow.read` |  | tự dò: v2 `approval` |
| PUT | `/api/approval-flows/switches` | I26 — đường lui của cả phase: tắt là quay về đường duyệt cũ ngay. | `approval_flow.write` |  | tự dò: v2 `approval` |
| GET | `/api/approval-flows/{flow_id}` | get flow | `approval_flow.read` |  | tự dò: v2 `approval` |
| PATCH | `/api/approval-flows/{flow_id}` | update flow | `approval_flow.write` |  | tự dò: v2 `approval` |
| DELETE | `/api/approval-flows/{flow_id}` | delete flow | `approval_flow.delete` |  | tự dò: v2 `approval` |
| POST | `/api/approval-flows/{flow_id}/nodes` | Thêm một bước. | `approval_flow.write` |  | tự dò: v2 `approval` |
| PUT | `/api/approval-flows/{flow_id}/nodes/reorder` | Ghi lại thứ tự sau khi kéo thả trên màn khai luồng. | `approval_flow.write` |  | tự dò: v2 `approval` |
| PATCH | `/api/approval-flows/{flow_id}/nodes/{node_id}` | update node | `approval_flow.write` |  | tự dò: v2 `approval` |
| DELETE | `/api/approval-flows/{flow_id}/nodes/{node_id}` | delete node | `approval_flow.write` |  | tự dò: v2 `approval` |
| POST | `/api/approvals/handover` | I23 — nghỉ việc: chuyển hết việc đang chờ sang người khác trong một lần. | `approval_flow.write` |  | tự dò: v2 `approval` |
| GET | `/api/approvals/my-history` | ĐÃ DUYỆT GẦN ĐÂY — nhìn lại những phiếu chính tôi vừa quyết định. | đăng nhập |  | tự dò: v2 `approval` |
| GET | `/api/approvals/my-tasks` | I17 — mọi thứ đang chờ tôi, của cả văn thư lẫn thu mua, gom một chỗ. | đăng nhập |  | tự dò: v2 `approval` |
| GET | `/api/approvals/of/{entity}/{entity_id}` | Phiên duyệt MỚI NHẤT của một chứng từ — `null` nếu nó chưa vào bộ máy. | đăng nhập |  | tự dò: v2 `approval` |
| GET | `/api/approvals/steps` | LUỒNG DUYỆT DẠNG NGANG cho nhiều chứng từ cùng lúc (CR-260). | đăng nhập |  | tự dò: v2 `hr` |
| GET | `/api/approvals/summary` | approval summary | `báo cáo 12`, `approval_flow.read` |  | tự dò: v2 `report` |
| GET | `/api/approvals/summary/export` | approval summary export | `báo cáo 12`, `approval_flow.export` |  | tự dò: v2 `report` |
| PATCH | `/api/approvals/tasks/{task_id}/reassign` | reassign | `approval_flow.write` |  | tự dò: v2 `approval` |
| GET | `/api/approvals/{instance_id}` | get instance | đăng nhập |  | tự dò: v2 `approval` |
| POST | `/api/approvals/{instance_id}/approve` | Không dùng `require(...)`: quyền ở đây là **có việc đang chờ mình hay không**, chuyện đó do `viec_dang_cho_cua` xét. | đăng nhập |  | tự dò: v2 `approval`, v2 `hr` |
| POST | `/api/approvals/{instance_id}/comment` | I16 — trao đổi ngay trên phiếu, không qua chat riêng. | đăng nhập |  | tự dò: v2 `approval` |
| POST | `/api/approvals/{instance_id}/reject` | reject | đăng nhập |  | tự dò: v2 `approval`, v2 `hr` |
| POST | `/api/approvals/{instance_id}/return` | return | đăng nhập |  | tự dò: v2 `approval`, v2 `hr` |
| GET | `/api/approvals/{instance_id}/trail` | I20 — bản in dấu vết duyệt. | đăng nhập |  | tự dò: v2 `approval` |
| POST | `/api/approvals/{instance_id}/withdraw` | withdraw | đăng nhập |  | tự dò: v2 `approval` |
| GET | `/api/attachments` | list attachments | đăng nhập |  | tự dò: v2 `dossier`, v2 `forum`, v2 `hr`, v2 `procurement`, v2 `support`, v2 `work` |
| POST | `/api/attachments` | Upload + gắn luôn (record đã có id) — tương thích FE cũ. | đăng nhập |  | tự dò: v2 `dossier`, v2 `forum`, v2 `hr`, v2 `procurement`, v2 `support`, v2 `work` |
| GET | `/api/attachments/chain` | Gom TOÀN BỘ chứng từ theo chuỗi của 1 đơn mua hàng (dữ liệu cho trang chi tiết). | đăng nhập |  | tự dò: v2 `procurement` |
| GET | `/api/attachments/chain/zip` | Tải TOÀN BỘ chứng từ chuỗi của 1 đơn dưới dạng .zip, sắp theo thư mục nguồn/loại. | đăng nhập |  | tự dò: v2 `procurement` |
| GET | `/api/attachments/doc-types` | Danh sách loại chứng từ cố định cho FE render selector. | đăng nhập |  | tự dò: v2 `procurement` |
| POST | `/api/attachments/register` | Gắn các file ĐÃ upload (theo file_id) vào 1 record — khi record vừa có id. | đăng nhập |  |  |
| PATCH | `/api/attachments/reorder` | Cập nhật thứ tự hiển thị các đính kèm của 1 record (dùng cho ảnh sản phẩm). | đăng nhập |  |  |
| POST | `/api/attachments/upload-file` | Upload file NGAY → tạo tab_file (chưa gắn link) → trả file_id để gắn khi Lưu record. | đăng nhập |  | tự dò: v2 `forum`, v2 `procurement`, v2 `support`, v2 `work` |
| DELETE | `/api/attachments/{link_id}` | remove | đăng nhập |  | tự dò: v2 `dossier`, v2 `hr`, v2 `procurement`, v2 `work` |
| GET | `/api/attachments/{link_id}/download` | Tải 1 file (ép attachment, đúng tên gốc). | đăng nhập |  | tự dò: v2 `document`, v2 `dossier`, v2 `hr`, v2 `procurement`, v2 `production`, v2 `work`, v2 dùng chung |
| GET | `/api/attachments/{link_id}/preview` | XEM TẠI CHỖ tệp WORD (và .md/.html) — chuyển sang HTML rồi trả về. | đăng nhập |  | tự dò: v2 `document` |
| GET | `/api/attachments/{link_id}/view` | XEM TẠI CHỖ — trả `inline` để nhúng thẳng vào trang, không ép tải về. | đăng nhập |  | tự dò: v2 `document`, v2 `dossier`, v2 `hr`, v2 `procurement`, v2 dùng chung |
| GET | `/api/audit-logs` | list logs | đăng nhập |  | tự dò: v2 `document`, v2 `system`, v2 `work`, v2 dùng chung |
| POST | `/api/auth/avatar` | update avatar | đăng nhập |  | tự dò: v2 dùng chung |
| POST | `/api/auth/change-password` | Người dùng tự đổi mật khẩu (đang đăng nhập). | đăng nhập |  | tự dò: v2 dùng chung |
| POST | `/api/auth/forgot-password` | forgot password | công khai |  | tự dò: v2 dùng chung |
| POST | `/api/auth/google` | login google | công khai |  | tự dò: v2 dùng chung |
| POST | `/api/auth/login` | login | công khai |  | tự dò: v2 dùng chung |
| POST | `/api/auth/logout` | Đăng xuất — bao-CR-360 khiến việc này **có hiệu lực thật** (đóng BM-002). | đăng nhập |  | tự dò: v2 dùng chung |
| GET | `/api/auth/me` | me | đăng nhập |  | tự dò: v2 `procurement`, v2 `system`, v2 dùng chung |
| PUT | `/api/auth/notify-email` | Người dùng tự bật/tắt email thông báo luồng duyệt của chính mình (bao-CR-349). | đăng nhập |  | tự dò: v2 dùng chung |
| POST | `/api/auth/refresh` | refresh | công khai |  |  |
| POST | `/api/auth/reset-password` | reset password | công khai |  | tự dò: v2 dùng chung |
| GET | `/api/auth/sessions` | Phiên của CHÍNH MÌNH, mới nhất trước; phiên đang gọi được đánh dấu `is_current`. | đăng nhập |  | tự dò: v2 `system`, v2 dùng chung |
| GET | `/api/auth/sessions/history` | Lịch sử đăng nhập của CHÍNH MÌNH trong N ngày (bao-CR-400): mọi lần vào (kể cả phiên đã kết thúc) hợp với các lần thất bại nối được về tài khoản này. | đăng nhập |  | tự dò: v2 `system`, v2 dùng chung |
| POST | `/api/auth/sessions/revoke-others` | Đăng xuất mọi thiết bị KHÁC, giữ thiết bị đang bấm nút — cùng cơ chế với đổi mật khẩu (không tăng `token_version`, nên trễ tối đa 60 giây). | đăng nhập |  | tự dò: v2 `system` |
| POST | `/api/auth/sessions/{session_id}/revoke` | Đá MỘT thiết bị của mình. | đăng nhập |  | tự dò: v2 `system` |
| POST | `/api/auth/signature` | Tải ảnh chữ ký cá nhân (PNG nền trong là đẹp nhất). | đăng nhập |  | tự dò: v2 dùng chung |
| DELETE | `/api/auth/signature` | Gỡ chữ ký khỏi hồ sơ. | đăng nhập |  | tự dò: v2 dùng chung |
| GET | `/api/backups` | list | `backup.read` |  | tự dò: v2 `system` |
| POST | `/api/backups/accept-size` | *Chấp nhận cỡ mới*: CSDL thu nhỏ hợp lệ, gỡ dấu đáng ngờ để việc dọn bản cũ chạy lại. | `backup.delete` |  |  |
| POST | `/api/backups/run` | Sao lưu ngay (bấm tay) — đẩy task vào worker, trả về ngay. | `backup.create` |  |  |
| DELETE | `/api/backups/{bid}` | delete | `backup.delete` |  |  |
| GET | `/api/backups/{bid}/download` | Trả URL tải file backup (presigned, hết hạn ngắn). | `backup.read` |  |  |
| GET | `/api/comments` | Một trang bình luận GỐC (cũ → mới) + số phản hồi của từng cái. | đăng nhập |  | tự dò: v2 `forum`, v2 `procurement`, v2 `work` |
| POST | `/api/comments` | create comment | đăng nhập |  | tự dò: v2 `forum`, v2 `procurement`, v2 `work` |
| GET | `/api/comments/mentionable` | Gợi ý người để `@` khi đang gõ bình luận (CR-031). | đăng nhập |  | tự dò: v2 `forum`, v2 `procurement`, v2 `work` |
| DELETE | `/api/comments/{cid}` | delete comment | đăng nhập |  | tự dò: v2 `forum`, v2 `procurement`, v2 `work` |
| POST | `/api/comments/{cid}/like` | Bấm thích / bỏ thích. | đăng nhập |  | tự dò: v2 `forum`, v2 `procurement` |
| GET | `/api/comments/{cid}/likes` | Ai đã thích bình luận này — hiện khi bấm vào con số. | đăng nhập |  |  |
| GET | `/api/comments/{cid}/replies` | list replies | đăng nhập |  | tự dò: v2 `forum`, v2 `procurement` |
| GET | `/api/companies` | list companies | `company.read` | `apply_scope` | tự dò: v2 `dossier`, v2 `hr`, v2 `production`, v2 `work` |
| POST | `/api/companies` | create company | `company.create` |  | tự dò: v2 `dossier`, v2 `hr`, v2 `production`, v2 `work` |
| DELETE | `/api/companies` | bulk delete companies | `company.delete` | `scope_condition` | tự dò: v2 `dossier`, v2 `hr`, v2 `production`, v2 `work` |
| GET | `/api/companies/{cid}` | get company | `company.read` |  | tự dò: v2 `hr` |
| PATCH | `/api/companies/{cid}` | update company | `company.write` |  | tự dò: v2 `hr` |
| DELETE | `/api/companies/{cid}` | delete company | `company.delete` |  | tự dò: v2 `hr` |
| POST | `/api/companies/{cid}/logo` | Cập nhật logo công ty — lưu file thật vào tab_file và gắn link qua tab_file_link. | `company.write` |  | tự dò: v2 `hr` |
| GET | `/api/dashboard/overview` | Tổng hợp trang chủ — LỌC THEO QUYỀN + PHẠM VI. | đăng nhập | `apply_scope` | tự dò: v2 `finance`, v2 `inventory`, v2 `procurement`, v2 `production`, v2 dùng chung |
| GET | `/api/dashboard/production` | Tổng quan phân hệ Sản xuất — danh mục NCC · Sản phẩm · ĐVT · Phân loại · Hợp đồng. | đăng nhập | `apply_scope` | tự dò: v2 `production`, v2 dùng chung |
| GET | `/api/dashboard/stats` | Thống kê nhanh — CÙNG LUẬT VỚI `/overview` (vá 05/09/2026). | đăng nhập | `apply_scope` |  |
| GET | `/api/dashboard/tasks` | Việc CẦN TÔI XỬ LÝ — danh sách chi tiết (đầy đủ, phân trang), lọc theo quyền + phạm vi. | đăng nhập |  | tự dò: v2 `work`, v2 dùng chung |
| POST | `/api/dashboard/tasks/dismiss` | Đánh dấu XONG các việc theo `keys` (hoặc `all: true` = mọi việc chưa ẩn) — ẩn khỏi tab Việc cần làm, chuông cảnh báo và dashboard của TÀI KHOẢN này (CR-215). | đăng nhập |  | tự dò: v2 dùng chung |
| POST | `/api/dashboard/tasks/restore` | Khôi phục việc đã đánh dấu xong. | đăng nhập |  | tự dò: v2 dùng chung |
| GET | `/api/delegations` | list delegations | `approval_flow.read` |  | tự dò: v2 `approval` |
| POST | `/api/delegations` | create delegation | `approval_flow.create` |  | tự dò: v2 `approval` |
| PATCH | `/api/delegations/{delegation_id}` | update delegation | `approval_flow.write` |  | tự dò: v2 `approval` |
| DELETE | `/api/delegations/{delegation_id}` | Ngưng ủy quyền = TẮT, không xóa. | `approval_flow.delete` |  | tự dò: v2 `approval` |
| GET | `/api/departments` | list departments | `department.read` |  | tự dò: v2 `dossier`, v2 `hr`, v2 dùng chung |
| POST | `/api/departments` | create department | `department.create` |  | tự dò: v2 `dossier`, v2 `hr`, v2 dùng chung |
| GET | `/api/departments/by-companies` | Các CẶP (phòng ban × pháp nhân) của những pháp nhân được hỏi. | `department.read` |  | tự dò: v2 `hr` |
| GET | `/api/departments/export/csv` | export departments csv | `department.export` |  |  |
| POST | `/api/departments/import/csv` | duoc-CR-628: Nhập CSV phòng ban đã NGỪNG (ghi thẳng cột, xóa hàng loạt, không chạy thử). | `department.import` |  |  |
| GET | `/api/departments/{did}` | get department | `department.read` |  | tự dò: v2 `document`, v2 `hr` |
| PATCH | `/api/departments/{did}` | update department | `department.write` |  | tự dò: v2 `document`, v2 `hr` |
| DELETE | `/api/departments/{did}` | delete department | `department.delete` |  | tự dò: v2 `document`, v2 `hr` |
| GET | `/api/departments/{did}/companies` | list department companies | `department.read` |  | tự dò: v2 `hr` |
| PUT | `/api/departments/{did}/companies` | replace department companies | `department.write` |  | tự dò: v2 `hr` |
| GET | `/api/email-exclusions` | list exclusions | `setting.read` |  | tự dò: v2 `system` |
| POST | `/api/email-exclusions` | add exclusion | `setting.write` |  | tự dò: v2 `system` |
| DELETE | `/api/email-exclusions/{exclusion_id}` | remove exclusion | `setting.write` |  | tự dò: v2 `system` |
| GET | `/api/email-logs` | Danh sách thư đã ghi, mới nhất trước. | `audit.read` | Không ghi request log (`SKIP_PATH_PREFIXES`) | Màn `/system/email-logs` |
| GET | `/api/email-logs/meta` | Bộ chọn cho ô lọc: sự kiện (danh mục mẫu email + sự kiện lạ đã từng ghi) và trạng thái, kèm nhãn tiếng Việt. | `audit.read` |  | tự dò: v2 `system` |
| GET | `/api/email-logs/stats` | Thẻ đầu màn: số thư theo trạng thái trong N ngày gần đây (mặc định 7). | `audit.read` |  | tự dò: v2 `system` |
| GET | `/api/email-logs/{log_id}` | Một dòng đầy đủ — câu lỗi nguyên văn, không cắt. | `audit.read` |  | tự dò: v2 `system` |
| POST | `/api/email-logs/{log_id}/resend` | Gửi lại y nguyên một thư đã ghi: cùng người nhận, tiêu đề, nội dung, hộp thư gửi danh nghĩa (bao-CR-727). | `audit.write` | Không ghi request log (`SKIP_PATH_PREFIXES`), có audit | Nút Gửi lại trong ngăn chi tiết `/system/email-logs` |
| GET | `/api/email-templates` | list templates | `setting.read` |  | tự dò: v2 `system` |
| GET | `/api/email-templates/{event}` | get template | `setting.read` |  | tự dò: v2 `system` |
| PUT | `/api/email-templates/{event}` | update template | `setting.write` |  | tự dò: v2 `system` |
| POST | `/api/email-templates/{event}/preview` | Render thử bản ĐANG SOẠN (nếu client gửi kèm) hoặc bản đã lưu, với dữ liệu mẫu. | `setting.read` |  | tự dò: v2 `system` |
| POST | `/api/email-templates/{event}/reset` | reset template | `setting.write` |  | tự dò: v2 `system` |
| POST | `/api/email-templates/{event}/test-send` | Gửi thử email của bước này về đúng địa chỉ của người đang bấm. | `setting.write` |  | tự dò: v2 `system` |
| GET | `/api/exports` | list exports | đăng nhập |  | tự dò: v2 `system` |
| GET | `/api/exports/entities` | Các bảng người dùng được phép xuất — đổ vào ô chọn của hộp thoại Xuất. | đăng nhập |  | tự dò: v2 `system` |
| GET | `/api/exports/run` | Xuất một bảng ra CSV/XLSX (theo phạm vi dữ liệu) + ghi nhật ký, trả file tải về. | đăng nhập |  | tự dò: v2 `system` |
| GET | `/api/exports/{bid}` | Chi tiết một lần xuất. | đăng nhập |  | tự dò: v2 `system` |
| GET | `/api/exports/{bid}/file` | Tải lại đúng file đã xuất (ảnh chụp lúc xuất, không sinh lại). | đăng nhập |  | tự dò: v2 `system` |
| GET | `/api/feature-usage/breakdown` | feature breakdown | `báo cáo 15`, `setting.read` |  | tự dò: v2 `report` |
| GET | `/api/feature-usage/summary` | feature summary | `báo cáo 15`, `setting.read` |  | tự dò: v2 `report` |
| GET | `/api/feature-usage/summary/export` | feature summary export | `báo cáo 15`, `setting.export` |  | tự dò: v2 `report` |
| GET | `/api/imports` | list imports | đăng nhập |  | tự dò: v2 `hr`, v2 `system` |
| POST | `/api/imports` | Upload .xlsx/.csv -> lưu file -> tạo batch -> đẩy Celery task (trả batch_id ngay). | đăng nhập |  | tự dò: v2 `hr`, v2 `system` |
| DELETE | `/api/imports/dev/surveys` | DEV-ONLY: xóa phiếu khảo sát theo ids (vd '97,98,99') hoặc toàn bộ phiếu do import tạo (all_imported=true). | đăng nhập |  |  |
| GET | `/api/imports/template` | Tải file .xlsx mẫu (đúng bộ cột) cho một đối tượng danh mục. | đăng nhập |  | tự dò: v2 `system` |
| GET | `/api/imports/{bid}` | get import | đăng nhập |  | tự dò: v2 `system` |
| POST | `/api/imports/{bid}/commit` | Ghi thật từ một bản CHẠY THỬ: tạo batch APPLY dùng lại đúng file, chạy nền. | đăng nhập |  | tự dò: v2 `system` |
| GET | `/api/imports/{bid}/file` | download import file | đăng nhập |  | tự dò: v2 `system` |
| GET | `/api/imports/{bid}/logs` | get import logs | đăng nhập |  | tự dò: v2 `system` |
| POST | `/api/imports/{bid}/revert` | Hoàn tác 1 batch đã ghi: phiếu mới -> xoá, phiếu cũ -> khôi phục snapshot. | đăng nhập |  | tự dò: v2 `system` |
| GET | `/api/login-sessions` | Danh sách phiên, mới nhất trước. | `login_session.read` | `apply_scope` | tự dò: v2 `system` |
| GET | `/api/login-sessions/history` | Lịch sử đăng nhập của MỘT người trong N ngày: mọi dòng phiên (kể cả đã thu hồi) HỢP với các dòng `login_failed` của `tab_audit_log`. | `login_session.read` |  | tự dò: v2 `system` |
| POST | `/api/login-sessions/users/{user_id}/logout-all` | Bắt đăng nhập lại: cắt MỌI thiết bị của một người, hiệu lực tức thì. | `login_session.delete` |  | tự dò: v2 `system` |
| POST | `/api/login-sessions/{session_id}/revoke` | Đá MỘT thiết bị. | `login_session.delete` | `get_scoped` | tự dò: v2 `system` |
| GET | `/api/mailboxes` | Danh sách hộp thư. **Trả thẳng một mảng, KHÔNG phân trang.** | `mailbox.read` | `apply_scope` | tự dò: v2 `system` |
| POST | `/api/mailboxes` | create mailbox | `mailbox.create` |  | tự dò: v2 `system` |
| GET | `/api/mailboxes/cua-toi/danh-sach` | Hộp thư TÔI được gửi danh nghĩa — dùng cho các màn ngoài phân hệ Văn bản. | `document.read` |  |  |
| GET | `/api/mailboxes/{mailbox_id}` | get mailbox | `mailbox.read` |  | tự dò: v2 `system` |
| PATCH | `/api/mailboxes/{mailbox_id}` | update mailbox | `mailbox.write` |  | tự dò: v2 `system` |
| DELETE | `/api/mailboxes/{mailbox_id}` | delete mailbox | `mailbox.delete` |  | tự dò: v2 `system` |
| DELETE | `/api/mailboxes/{mailbox_id}/password` | Xóa mật khẩu ứng dụng — thao tác RIÊNG, có chủ ý. | `mailbox.write` |  | tự dò: v2 `system` |
| GET | `/api/me/preferences` | get my preferences | đăng nhập |  | tự dò: v2 `work`, v2 dùng chung |
| PUT | `/api/me/preferences` | save my preferences | đăng nhập |  | tự dò: v2 `work`, v2 dùng chung |
| GET | `/api/meta/statuses` | Toàn bộ bộ mã cố định đang khai ở backend (QĐ-9 / B-01). | đăng nhập |  |  |
| GET | `/api/meta/statuses/{name}` | get status set | đăng nhập |  |  |
| GET | `/api/notifications` | Thông báo của chính người dùng — phân trang + lọc. | đăng nhập |  | tự dò: v2 dùng chung |
| DELETE | `/api/notifications/read` | Xóa tất cả thông báo ĐÃ ĐỌC của người dùng. | đăng nhập |  | tự dò: v2 dùng chung |
| POST | `/api/notifications/read-all` | mark all read | đăng nhập |  | tự dò: v2 dùng chung |
| DELETE | `/api/notifications/{nid}` | Xóa 1 thông báo của chính người dùng. | đăng nhập |  | tự dò: v2 dùng chung |
| POST | `/api/notifications/{nid}/read` | mark read | đăng nhập |  | tự dò: v2 dùng chung |
| POST | `/api/push/subscribe` | subscribe | đăng nhập |  |  |
| POST | `/api/push/unsubscribe` | unsubscribe | đăng nhập |  |  |
| GET | `/api/push/vapid-public-key` | vapid public key | đăng nhập |  |  |
| GET | `/api/report-access` | 13 báo cáo theo đúng thứ tự khóa, mỗi báo cáo kèm danh sách dòng CÒN SỐNG. | `role.read` |  | tự dò: v2 `system` |
| DELETE | `/api/report-access/grants/{access_id}` | revoke report access | `role.write` |  | tự dò: v2 `system` |
| POST | `/api/report-access/{key}/grants` | grant report access | `role.write` |  | tự dò: v2 `system` |
| GET | `/api/reports/daily` | Chi phí theo NGÀY trong 1 tháng (drill-down khi click cột). | `report.read` |  |  |
| GET | `/api/reports/dept-range` | Đặt hàng & đơn gấp theo Bộ phận trong khoảng NGÀY (date_from, date_to = YYYY-MM-DD). | `report.read` |  | tự dò: v2 `procurement` |
| GET | `/api/reports/export` | Xuất báo cáo mua hàng ra Excel (khớp form thumua1 sheet 12–16). | `report.export` |  |  |
| GET | `/api/reports/ig-range` | Tần suất mua & chi phí theo Loại VTBB/NL trong khoảng NGÀY (date_from, date_to = YYYY-MM-DD). | `report.read` |  | tự dò: v2 `procurement` |
| GET | `/api/reports/import-landed-cost` | Giá vốn lô hàng (bao-CR-347; ba giai đoạn chi phí bao-CR-453) — chọn theo mã đơn hoặc theo khoảng ngày đặt. | `report.read` |  | tự dò: v2 `procurement` |
| GET | `/api/reports/import-landed-cost/export` | Xuất báo cáo giá vốn lô hàng ra Excel — hai sheet, theo lô và theo dòng hàng; nhận cùng bộ tham số `stage` / `include_domestic` với đường đọc. | `report.export` |  |  |
| GET | `/api/reports/matrix` | Báo cáo ma trận (NCC/phân loại/NSPT/bộ phận/vận chuyển) — stale-while-revalidate. | `report.read` |  | tự dò: v2 `production` |
| GET | `/api/reports/nspt-range` | Giao hàng theo NSPT trong khoảng NGÀY (date_from, date_to = YYYY-MM-DD). | `report.read` |  | tự dò: v2 `procurement` |
| GET | `/api/reports/pr-lines` | Báo cáo Yêu cầu mua hàng theo DÒNG hàng (bao-CR-295) — phân trang server (50/trang). | `report.read` |  |  |
| GET | `/api/reports/pr-lines/export` | bao-CR-691: xuất Excel bảng Chi tiết YC mua hàng — cùng bộ lọc với `/pr-lines`, không phân trang, trần `export_xlsx.MAX_ROWS` dòng. | `report.export` |  |  |
| GET | `/api/reports/pr-lines/summary` | Tổng hợp của báo cáo Chi tiết YC mua hàng (theo tiến độ / tháng / bộ phận / nhóm hàng / NSTM) cho màn biểu đồ. | `báo cáo 2`, `report.read` |  | tự dò: v2 `report` |
| GET | `/api/reports/pr-lines/summary/export` | Xuất Excel bản THEO KỲ của báo cáo Chi tiết YC mua hàng (P03) — cùng bộ lọc với `/summary`. | `báo cáo 2`, `report.export` |  | tự dò: v2 `report` |
| GET | `/api/reports/procurement` | procurement | `report.read` |  | tự dò: v2 `procurement` |
| GET | `/api/reports/procurement/summary` | Tổng hợp Báo cáo mua hàng kiểu Haravan — kỳ + so sánh + Xem theo, hợp đồng chuẩn `report_aggregate.build_report`. | `báo cáo 1`, `report.read` |  | tự dò: v2 `report` |
| GET | `/api/reports/procurement/summary/export` | procurement summary export | `báo cáo 1`, `report.export` |  | tự dò: v2 `report` |
| GET | `/api/reports/request-matrix` | Ma trận phòng ban × tháng cho Yêu cầu mua hàng (kind=pyc) / khảo sát (kind=ycks). | `report.read` |  |  |
| GET | `/api/reports/request-range` | Bảng phẳng phòng ban theo khoảng ngày cho PYC/YCKS (có scope). | `report.read` |  | tự dò: v2 `procurement` |
| GET | `/api/reports/shipping-detail` | Chi tiết chi phí vận chuyển theo đơn hàng — phân trang server (page, page_size=50). | `report.read` |  |  |
| GET | `/api/reports/sup-range` | Giao dịch & trễ theo NCC trong khoảng NGÀY (date_from, date_to = YYYY-MM-DD). | `report.read` |  | tự dò: v2 `procurement` |
| GET | `/api/roles` | list roles | `role.read` |  | tự dò: v2 `hr` |
| POST | `/api/roles` | create role | `role.create` |  | tự dò: v2 `hr` |
| GET | `/api/roles/meta` | Danh sách quyền config (đối tượng x hành động) để FE dựng ma trận. | `role.read` |  | tự dò: v2 `hr`, v2 `system` |
| PUT | `/api/roles/order` | Lưu THỨ TỰ HIỆN của danh sách vai trò (kéo thả ở màn Phân quyền). | `role.write` |  | tự dò: v2 `hr` |
| GET | `/api/roles/{rid}` | get role | `role.read` |  | tự dò: v2 `hr` |
| PATCH | `/api/roles/{rid}` | update role | `role.write` |  | tự dò: v2 `hr` |
| DELETE | `/api/roles/{rid}` | delete role | `role.delete` |  | tự dò: v2 `hr` |
| GET | `/api/roles/{rid}/permissions` | get permissions | `role.read` |  | tự dò: v2 `hr` |
| PUT | `/api/roles/{rid}/permissions` | set permissions | `role.write` |  | tự dò: v2 `hr` |
| GET | `/api/settings` | get settings | `setting.read` |  | tự dò: v2 `document`, v2 `hr`, v2 `system` |
| PUT | `/api/settings` | save settings | `setting.write` |  | tự dò: v2 `document`, v2 `hr`, v2 `system` |
| POST | `/api/settings/test-email` | test email | `setting.write` |  | tự dò: v2 `system` |
| POST | `/api/settings/test-storage` | test storage | `setting.write` |  | tự dò: v2 `system` |
| GET | `/api/sync-logs` | Danh sách dòng sổ, mới nhất trước. | `sync_log.read` | `apply_scope` | tự dò: v2 `system` |
| GET | `/api/sync-logs/meta` | Bộ chọn cho các ô lọc: nguồn, đối tượng, mã trạng thái, nhãn cờ. | `sync_log.read` |  | tự dò: v2 `system` |
| GET | `/api/sync-logs/stats` | Thẻ đếm theo trạng thái trong N ngày gần đây. | `sync_log.read` | `apply_scope` | tự dò: v2 `system` |
| GET | `/api/sync-logs/{log_id}` | Một dòng, kèm nguyên cục dữ liệu bên kia gửi sang và câu lỗi nguyên văn. | `sync_log.read` | `get_scoped` | tự dò: v2 `system` |
| POST | `/api/sync-logs/{log_id}/retry` | Chạy lại một dòng hỏng — sinh DÒNG MỚI, không sửa dòng cũ. | `sync_log.write` | `get_scoped` | tự dò: v2 `system` |
| GET | `/api/system-logs` | Danh sách gộp theo `request_id` — mỗi dòng là MỘT lượt gọi. | đăng nhập |  | tự dò: v2 `system` |
| GET | `/api/system-logs/summary` | Số liệu ba biểu đồ. | đăng nhập |  | tự dò: v2 `system` |
| GET | `/api/system-logs/{request_id}` | Gói bốn tab của một lượt gọi: Tổng quan · Request · Thay đổi · Phiên. | đăng nhập |  | tự dò: v2 `system` |
| GET | `/api/system/jobs` | list jobs | `setting.read` |  | tự dò: v2 `system` |
| GET | `/api/system/jobs/{code}/runs` | list runs | `setting.read` |  | tự dò: v2 `system` |
| GET | `/api/system/release-notes` | Các đợt phát hành, mới nhất trước, kèm danh sách phân hệ có trong các mục để màn lọc. | đăng nhập |  | `/whats-new` |
| GET | `/api/system/version` | Phiên bản đang chạy: mục mới nhất của release_notes.json + commit / giờ build bơm lúc build image + môi trường. | đăng nhập | Không gác quyền | chân menu trái, trang Có gì mới |
| POST | `/api/telemetry/ui-events` | post ui events | đăng nhập |  |  |
| GET | `/api/tickets` | list | `ticket.read` | `apply_scope` | tự dò: v2 `support` |
| POST | `/api/tickets` | create | `ticket.create` |  | tự dò: v2 `support` |
| GET | `/api/tickets/{tid}` | get | `ticket.read` | `apply_scope` | tự dò: v2 `support` |
| PATCH | `/api/tickets/{tid}` | update | `ticket.read` |  | tự dò: v2 `support` |
| POST | `/api/tickets/{tid}/assign` | Nhận phiếu / giao phiếu — chỉ nhóm Hỗ trợ. | `ticket.read` |  | tự dò: v2 `support` |
| POST | `/api/tickets/{tid}/messages` | reply | `ticket.read` |  | tự dò: v2 `support` |
| POST | `/api/tickets/{tid}/status` | set status | `ticket.read` |  | tự dò: v2 `support` |
| GET | `/api/usage-profiles/by-app` | usage by app | `báo cáo 14`, `setting.read` |  |  |
| GET | `/api/usage-profiles/cohorts` | usage cohorts | `báo cáo 14`, `setting.read` |  |  |
| GET | `/api/usage-profiles/metrics` | usage metrics | `báo cáo 14`, `setting.read` |  | tự dò: v2 `report` |
| GET | `/api/usage-profiles/summary` | usage summary | `báo cáo 14`, `setting.read` |  | tự dò: v2 `report` |
| GET | `/api/usage-profiles/summary/export` | usage summary export | `báo cáo 14`, `setting.export` |  | tự dò: v2 `report` |
| GET | `/api/usage-profiles/{user_id}` | usage profile | `báo cáo 14`, `setting.read` |  | tự dò: v2 `report` |
| GET | `/api/users` | list users | `user.read` | `scope_condition` | tự dò: v2 `ai-skill`, v2 `hr`, v2 `system`, v2 `vehicle-booking` |
| POST | `/api/users` | provision user | `user.create` |  | tự dò: v2 `ai-skill`, v2 `hr`, v2 `system`, v2 `vehicle-booking` |
| GET | `/api/users/{user_id}` | get user | `user.read` | `get_scoped` | tự dò: v2 `hr` |
| DELETE | `/api/users/{user_id}` | delete user | `user.delete` |  | tự dò: v2 `hr` |
| PUT | `/api/users/{user_id}/active` | set active | `user.write` |  | tự dò: v2 `hr` |
| PUT | `/api/users/{user_id}/notify-email` | Quản trị bật/tắt hộ email thông báo cho một tài khoản (bao-CR-349). | `user.write` |  | tự dò: v2 `hr` |
| POST | `/api/users/{user_id}/reset-password` | reset password | `user.write` |  |  |
| PUT | `/api/users/{user_id}/roles` | assign roles | `user.write` |  | tự dò: v2 `hr` |
| GET | `/api/users/{user_id}/roles/{role_id}/scope` | get scope | `user.read` |  | tự dò: v2 `hr` |
| PUT | `/api/users/{user_id}/roles/{role_id}/scope` | set scope | `user.write` |  | tự dò: v2 `hr` |
| GET | `/api/v1/faq` | Danh sách câu hỏi. | công khai |  |  |
| POST | `/api/v1/faq` | create faq | `help_article.create` |  |  |
| GET | `/api/v1/faq/{faq_id}` | get faq | công khai |  |  |
| PUT | `/api/v1/faq/{faq_id}` | update faq | `help_article.write` |  |  |
| DELETE | `/api/v1/faq/{faq_id}` | delete faq | `help_article.delete` |  |  |
| POST | `/api/v1/help-center` | create help article | `help_article.create` |  |  |
| GET | `/api/v1/help-center/home` | Danh sách 4 khung trang chủ sắp theo sort_order, kèm bài viết đã gắn (nếu có). | công khai |  |  |
| PUT | `/api/v1/help-center/home/items/{item_id}` | update help home item | `help_article.write` |  |  |
| DELETE | `/api/v1/help-center/home/items/{item_id}` | delete help home item | `help_article.write` |  |  |
| PUT | `/api/v1/help-center/home/sections/{section_id}` | update help home section | `help_article.write` |  |  |
| POST | `/api/v1/help-center/home/sections/{section_id}/items` | add help home item | `help_article.write` |  |  |
| POST | `/api/v1/help-center/import` | Nhập bài viết từ file HTML / Markdown — mỗi file thành 1 bài. | `help_article.create` |  |  |
| POST | `/api/v1/help-center/import/parse` | Đọc 1 file → trả {title, summary, content} đã lọc, KHÔNG ghi DB. | `help_article.write` |  |  |
| GET | `/api/v1/help-center/search` | Tìm kiếm bài viết theo tiêu đề HOẶC nội dung, kèm đoạn trích quanh từ khóa. | công khai |  |  |
| PUT | `/api/v1/help-center/slides/{slide_id}` | update article slide | `help_article.write` |  |  |
| DELETE | `/api/v1/help-center/slides/{slide_id}` | delete article slide | `help_article.delete` |  |  |
| GET | `/api/v1/help-center/tree` | Danh sách phẳng bài viết để client dựng cây thư mục. | công khai |  |  |
| POST | `/api/v1/help-center/upload-image` | Upload ảnh (chèn vào trình soạn thảo hoặc làm slide) và trả về URL. | `help_article.write` |  |  |
| GET | `/api/v1/help-center/{article_id}` | Chi tiết 1 bài viết gồm nội dung HTML và danh sách slide. | công khai |  |  |
| PUT | `/api/v1/help-center/{article_id}` | update help article | `help_article.write` |  |  |
| DELETE | `/api/v1/help-center/{article_id}` | delete help article | `help_article.delete` |  |  |
| POST | `/api/v1/help-center/{article_id}/slides` | add article slide | `help_article.write` |  |  |
| GET | `/api/work-capability/load` | Tải đang ôm từng người, tính lúc gọi. | `báo cáo 16`, `setting.read` |  | tự dò: v2 `report` |
| GET | `/api/work-capability/summary` | capability summary | `báo cáo 16`, `setting.read` |  | tự dò: v2 `report` |
| GET | `/api/work-capability/summary/export` | capability summary export | `báo cáo 16`, `setting.export` |  | tự dò: v2 `report` |

## 2. Dữ liệu vào / ra chính

Ghi chú chi tiết từng đường (chuyển từ cột *Mục đích* của bảng mục 1 ngày 05/11/2026, khi cột đó chuyển sang lấy docstring):

- `GET /api/email-logs`: Nhật ký email (bao-CR-721): danh sách thư đã ghi, mới nhất trước, phân trang; lọc `q` (người nhận chứa), `event` (lặp nhiều lần), `status`, `from_date`, `to_date`. Chỉ đọc.
- `GET /api/email-logs/meta`: Bộ chọn ô lọc: sự kiện (danh mục mẫu email + sự kiện lạ đã ghi) và trạng thái, kèm nhãn.
- `GET /api/email-logs/stats`: Số thư theo trạng thái trong `days` ngày (mặc định 7) — thẻ đầu màn.
- `GET /api/email-logs/{log_id}`: Một thư đầy đủ, câu lỗi nguyên văn. Từ bao-CR-727 mọi dòng (cả danh sách) trả thêm `resent_from_id`, `has_body`, `can_resend`, `resend_block_reason`; không trả nội dung thư.
- `POST /api/email-logs/{log_id}/resend`: Gửi lại y nguyên một thư (bao-CR-727): sinh dòng nhật ký MỚI trạng thái chờ (`resent_from_id` = dòng đã bấm, cùng người nhận, tiêu đề, nội dung, `mailbox_id`), gửi nền qua `send_smtp_email` (công tắc email / chặn cứng / override vẫn áp; thư luồng duyệt giữ `force`, không override); ghi audit `email_log` / `resend`. Lỗi: 400 thư không lưu nội dung (thư trước đợt này, thư đặt lại mật khẩu / cấp tài khoản không bao giờ lưu), 429 cùng thư đã gửi lại trong 60 giây, 404.
- `GET /api/system/version`: Phiên bản đang chạy (bao-CR-722): mục mới nhất của release_notes.json + `commit`, `built_at` (biến BUILD_COMMIT / BUILD_TIME bơm lúc build), `environment` (APP_ENV của compose).
- `GET /api/system/release-notes`: Các đợt phát hành mới nhất trước (`limit` tối đa 100), từng mục có module / kind / kind_label / cr / text, kèm `modules` có mục và `kinds`.

## 3. Lỗi riêng của phân hệ

Chưa có.

## 4. Bộ lọc danh sách

Chưa có.

## 5. Thay đổi gần đây

| Ngày | CR | Đổi gì (thêm / sửa / bỏ đường) |
|---|---|---|
| 03/11/2026 | bao-CR-712 | Dựng bản đầu từ mã |
