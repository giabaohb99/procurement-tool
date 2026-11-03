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

> Bảng mục 1 dựng TỰ ĐỘNG ngày 03/11/2026 từ `app.routes` (bao-CR-712): *Mục đích* = dòng đầu docstring (không có thì tên hàm); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* chỉ ghi khi thấy `apply_scope` / `get_scoped` / `scope_condition` ngay trong hàm đường — trống nghĩa là **chưa soát** (có thể lọc ở service). Người phụ trách soát lại và điền cột *Ai gọi*, mục 2–4.

Mã backend: `approval`, `notification`, `comment`, `ticket`, `attachment`, `import_tool`, `export_log`, `dashboard`, `meta`, `user_preference`, `push`, `help_center`, `faq`, `alert`, `report`, `report_access`, `setting`, `system_log`, `job_run`, `audit`, `login_session`, `auth`, `user`, `role`, `company`, `department`, `sync_log`, `backup`, `feature_usage`, `usage_profile`, `capability`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/approval-flows` | list flows | `approval_flow.read` | `apply_scope` | |
| POST | `/api/approval-flows` | create flow | `approval_flow.create` | `get_scoped` | |
| GET | `/api/approval-flows/options` | Nhãn tiếng Việt do backend cấp — giao diện không chép cứng. | `approval_flow.read` |  | |
| GET | `/api/approval-flows/permission-approvers` | Ai đang giữ quyền Duyệt trên khóa `entity` — cho cách chọn "Người có quyền duyệt" (duoc-CR-680). | `approval_flow.read` |  | |
| GET | `/api/approval-flows/switches` | list switches | `approval_flow.read` |  | |
| PUT | `/api/approval-flows/switches` | I26 — đường lui của cả phase: tắt là quay về đường duyệt cũ ngay. | `approval_flow.write` | `get_scoped` | |
| DELETE | `/api/approval-flows/{flow_id}` | delete flow | `approval_flow.delete` |  | |
| GET | `/api/approval-flows/{flow_id}` | get flow | `approval_flow.read` |  | |
| PATCH | `/api/approval-flows/{flow_id}` | update flow | `approval_flow.write` |  | |
| POST | `/api/approval-flows/{flow_id}/nodes` | Thêm một bước. `as_branch=true` = nhánh song song của chặng đó, mặc định | `approval_flow.write` |  | |
| PUT | `/api/approval-flows/{flow_id}/nodes/reorder` | Ghi lại thứ tự sau khi kéo thả trên màn khai luồng. | `approval_flow.write` |  | |
| DELETE | `/api/approval-flows/{flow_id}/nodes/{node_id}` | delete node | `approval_flow.write` |  | |
| PATCH | `/api/approval-flows/{flow_id}/nodes/{node_id}` | update node | `approval_flow.write` |  | |
| POST | `/api/approvals/handover` | I23 — nghỉ việc: chuyển hết việc đang chờ sang người khác trong một lần. | `approval_flow.write` |  | |
| GET | `/api/approvals/my-history` | ĐÃ DUYỆT GẦN ĐÂY — nhìn lại những phiếu chính tôi vừa quyết định. | — |  | |
| GET | `/api/approvals/my-tasks` | I17 — mọi thứ đang chờ tôi, của cả văn thư lẫn thu mua, gom một chỗ. | — |  | |
| GET | `/api/approvals/of/{entity}/{entity_id}` | Phiên duyệt MỚI NHẤT của một chứng từ — `null` nếu nó chưa vào bộ máy. | — |  | |
| GET | `/api/approvals/steps` | LUỒNG DUYỆT DẠNG NGANG cho nhiều chứng từ cùng lúc (CR-260). | — |  | |
| GET | `/api/approvals/summary` | approval summary | `approval_flow.read`, `báo cáo 12` |  | |
| GET | `/api/approvals/summary/export` | approval summary export | `approval_flow.export`, `báo cáo 12` |  | |
| PATCH | `/api/approvals/tasks/{task_id}/reassign` | reassign | `approval_flow.write` |  | |
| GET | `/api/approvals/{instance_id}` | get instance | — |  | |
| POST | `/api/approvals/{instance_id}/approve` | Không dùng `require(...)`: quyền ở đây là **có việc đang chờ mình hay | — |  | |
| POST | `/api/approvals/{instance_id}/comment` | I16 — trao đổi ngay trên phiếu, không qua chat riêng. | — |  | |
| POST | `/api/approvals/{instance_id}/reject` | reject | — |  | |
| POST | `/api/approvals/{instance_id}/return` | return  | — |  | |
| GET | `/api/approvals/{instance_id}/trail` | I20 — bản in dấu vết duyệt. | — |  | |
| POST | `/api/approvals/{instance_id}/withdraw` | withdraw | — |  | |
| GET | `/api/delegations` | list delegations | `approval_flow.read` |  | |
| POST | `/api/delegations` | create delegation | `approval_flow.create` |  | |
| DELETE | `/api/delegations/{delegation_id}` | Ngưng ủy quyền = TẮT, không xóa. | `approval_flow.delete` |  | |
| PATCH | `/api/delegations/{delegation_id}` | update delegation | `approval_flow.write` |  | |
| GET | `/api/email-exclusions` | list exclusions | `setting.read` |  | |
| POST | `/api/email-exclusions` | add exclusion | `setting.write` |  | |
| DELETE | `/api/email-exclusions/{exclusion_id}` | remove exclusion | `setting.write` |  | |
| GET | `/api/email-templates` | list templates | `setting.read` |  | |
| GET | `/api/email-templates/{event}` | get template | `setting.read` |  | |
| PUT | `/api/email-templates/{event}` | update template | `setting.write` |  | |
| POST | `/api/email-templates/{event}/preview` | Render thử bản ĐANG SOẠN (nếu client gửi kèm) hoặc bản đã lưu, với dữ liệu mẫu. | `setting.read` |  | |
| POST | `/api/email-templates/{event}/reset` | reset template | `setting.write` |  | |
| GET | `/api/email-logs` | Nhật ký email (bao-CR-721): danh sách thư đã ghi, mới nhất trước, phân trang; lọc `q` (người nhận chứa), `event` (lặp nhiều lần), `status`, `from_date`, `to_date`. Chỉ đọc. | `audit.read` | Không ghi request log (`SKIP_PATH_PREFIXES`) | Màn `/system/email-logs` |
| GET | `/api/email-logs/meta` | Bộ chọn ô lọc: sự kiện (danh mục mẫu email + sự kiện lạ đã ghi) và trạng thái, kèm nhãn. | `audit.read` |  | |
| GET | `/api/email-logs/stats` | Số thư theo trạng thái trong `days` ngày (mặc định 7) — thẻ đầu màn. | `audit.read` |  | |
| GET | `/api/email-logs/{log_id}` | Một thư đầy đủ, câu lỗi nguyên văn. | `audit.read` |  | |
| POST | `/api/email-templates/{event}/test-send` | Gửi thử email của bước này về đúng địa chỉ của người đang bấm. | `setting.write` |  | |
| GET | `/api/mailboxes` | Danh sách hộp thư. **Trả thẳng một mảng, KHÔNG phân trang.** | `mailbox.read` | `apply_scope` | |
| POST | `/api/mailboxes` | create mailbox | `mailbox.create` |  | |
| GET | `/api/mailboxes/cua-toi/danh-sach` | Hộp thư TÔI được gửi danh nghĩa — dùng cho các màn ngoài phân hệ Văn bản. | `document.read` |  | |
| DELETE | `/api/mailboxes/{mailbox_id}` | delete mailbox | `mailbox.delete` |  | |
| GET | `/api/mailboxes/{mailbox_id}` | get mailbox | `mailbox.read` |  | |
| PATCH | `/api/mailboxes/{mailbox_id}` | update mailbox | `mailbox.write` |  | |
| DELETE | `/api/mailboxes/{mailbox_id}/password` | Xóa mật khẩu ứng dụng — thao tác RIÊNG, có chủ ý. Xem `dat_mat_khau`. | `mailbox.write` |  | |
| GET | `/api/notifications` | Thông báo của chính người dùng — phân trang + lọc. | — |  | |
| DELETE | `/api/notifications/read` | Xóa tất cả thông báo ĐÃ ĐỌC của người dùng. | — |  | |
| POST | `/api/notifications/read-all` | mark all read | — |  | |
| DELETE | `/api/notifications/{nid}` | Xóa 1 thông báo của chính người dùng. | — |  | |
| POST | `/api/notifications/{nid}/read` | mark read | — |  | |
| GET | `/api/comments` | Một trang bình luận GỐC (cũ → mới) + số phản hồi của từng cái. | — |  | |
| POST | `/api/comments` | create comment | — |  | |
| GET | `/api/comments/mentionable` | Gợi ý người để `@` khi đang gõ bình luận (CR-031). | — |  | |
| DELETE | `/api/comments/{cid}` | delete comment | — |  | |
| POST | `/api/comments/{cid}/like` | Bấm thích / bỏ thích. Cố ý KHÔNG sinh thông báo — nếu không chuông sẽ rất ồn. | — |  | |
| GET | `/api/comments/{cid}/likes` | Ai đã thích bình luận này — hiện khi bấm vào con số. | — |  | |
| GET | `/api/comments/{cid}/replies` | list replies | — |  | |
| GET | `/api/tickets` | list  | `ticket.read` | `apply_scope` | |
| POST | `/api/tickets` | create  | `ticket.create` |  | |
| GET | `/api/tickets/{tid}` | get  | `ticket.read` | `apply_scope` | |
| PATCH | `/api/tickets/{tid}` | update  | `ticket.read` |  | |
| POST | `/api/tickets/{tid}/assign` | Nhận phiếu / giao phiếu — chỉ nhóm Hỗ trợ. | `ticket.read` |  | |
| POST | `/api/tickets/{tid}/messages` | reply  | `ticket.read` |  | |
| POST | `/api/tickets/{tid}/status` | set status  | `ticket.read` |  | |
| GET | `/api/attachments` | list attachments | — |  | |
| POST | `/api/attachments` | Upload + gắn luôn (record đã có id) — tương thích FE cũ. | — |  | |
| GET | `/api/attachments/chain` | Gom TOÀN BỘ chứng từ theo chuỗi của 1 đơn mua hàng (dữ liệu cho trang chi tiết). | — |  | |
| GET | `/api/attachments/chain/zip` | Tải TOÀN BỘ chứng từ chuỗi của 1 đơn dưới dạng .zip, sắp theo thư mục nguồn/loại. | — |  | |
| GET | `/api/attachments/doc-types` | Danh sách loại chứng từ cố định cho FE render selector. | — |  | |
| POST | `/api/attachments/register` | Gắn các file ĐÃ upload (theo file_id) vào 1 record — khi record vừa có id. | — |  | |
| PATCH | `/api/attachments/reorder` | Cập nhật thứ tự hiển thị các đính kèm của 1 record (dùng cho ảnh sản phẩm). | — |  | |
| POST | `/api/attachments/upload-file` | Upload file NGAY → tạo tab_file (chưa gắn link) → trả file_id để gắn khi Lưu record. | — |  | |
| DELETE | `/api/attachments/{link_id}` | remove | — |  | |
| GET | `/api/attachments/{link_id}/download` | Tải 1 file (ép attachment, đúng tên gốc). Quyền theo entity cha của link. | — |  | |
| GET | `/api/attachments/{link_id}/preview` | XEM TẠI CHỖ tệp WORD (và .md/.html) — chuyển sang HTML rồi trả về. | — |  | |
| GET | `/api/attachments/{link_id}/view` | XEM TẠI CHỖ — trả `inline` để nhúng thẳng vào trang, không ép tải về. | — |  | |
| GET | `/api/imports` | list imports | — |  | |
| POST | `/api/imports` | Upload .xlsx/.csv -> lưu file -> tạo batch -> đẩy Celery task (trả batch_id ngay). | — |  | |
| DELETE | `/api/imports/dev/surveys` | DEV-ONLY: xóa phiếu khảo sát theo ids (vd '97,98,99') hoặc toàn bộ phiếu do import tạo | — |  | |
| GET | `/api/imports/template` | Tải file .xlsx mẫu (đúng bộ cột) cho một đối tượng danh mục. Đặt TRƯỚC /{bid} | — |  | |
| GET | `/api/imports/{bid}` | get import | — |  | |
| POST | `/api/imports/{bid}/commit` | Ghi thật từ một bản CHẠY THỬ: tạo batch APPLY dùng lại đúng file, chạy nền. | — |  | |
| GET | `/api/imports/{bid}/file` | download import file | — |  | |
| GET | `/api/imports/{bid}/logs` | get import logs | — |  | |
| POST | `/api/imports/{bid}/revert` | Hoàn tác 1 batch đã ghi: phiếu mới -> xoá, phiếu cũ -> khôi phục snapshot. | — |  | |
| GET | `/api/exports` | list exports | — |  | |
| GET | `/api/exports/entities` | Các bảng người dùng được phép xuất — đổ vào ô chọn của hộp thoại Xuất. | — |  | |
| GET | `/api/exports/run` | Xuất một bảng ra CSV/XLSX (theo phạm vi dữ liệu) + ghi nhật ký, trả file tải về. | — |  | |
| GET | `/api/exports/{bid}` | Chi tiết một lần xuất. Đặt SAU /entities và /run để không nuốt hai path đó. | — |  | |
| GET | `/api/exports/{bid}/file` | Tải lại đúng file đã xuất (ảnh chụp lúc xuất, không sinh lại). | — |  | |
| GET | `/api/dashboard/overview` | Tổng hợp trang chủ — LỌC THEO QUYỀN + PHẠM VI. Khối nào user không có quyền Xem | — | `apply_scope` | |
| GET | `/api/dashboard/production` | Tổng quan phân hệ Sản xuất — danh mục NCC · Sản phẩm · ĐVT · Phân loại · Hợp đồng. | — | `apply_scope` | |
| GET | `/api/dashboard/stats` | Thống kê nhanh — CÙNG LUẬT VỚI `/overview` (vá 05/09/2026). | — | `apply_scope` | |
| GET | `/api/dashboard/tasks` | Việc CẦN TÔI XỬ LÝ — danh sách chi tiết (đầy đủ, phân trang), lọc theo quyền + phạm vi. | — |  | |
| POST | `/api/dashboard/tasks/dismiss` | Đánh dấu XONG các việc theo `keys` (hoặc `all: true` = mọi việc chưa ẩn) — | — |  | |
| POST | `/api/dashboard/tasks/restore` | Khôi phục việc đã đánh dấu xong. Body: `keys` (danh sách) hoặc `all: true`. | — |  | |
| GET | `/api/meta/statuses` | Toàn bộ bộ mã cố định đang khai ở backend (QĐ-9 / B-01). | — |  | |
| GET | `/api/meta/statuses/{name}` | get status set | — |  | |
| GET | `/api/me/preferences` | get my preferences | — |  | |
| PUT | `/api/me/preferences` | save my preferences | — |  | |
| POST | `/api/push/subscribe` | subscribe | — |  | |
| POST | `/api/push/unsubscribe` | unsubscribe | — |  | |
| GET | `/api/push/vapid-public-key` | vapid public key | — |  | |
| POST | `/api/v1/help-center` | create help article | `help_article.create` |  | |
| GET | `/api/v1/help-center/home` | Danh sách 4 khung trang chủ sắp theo sort_order, kèm bài viết đã gắn (nếu có). | — |  | |
| DELETE | `/api/v1/help-center/home/items/{item_id}` | delete help home item | `help_article.write` |  | |
| PUT | `/api/v1/help-center/home/items/{item_id}` | update help home item | `help_article.write` |  | |
| PUT | `/api/v1/help-center/home/sections/{section_id}` | update help home section | `help_article.write` |  | |
| POST | `/api/v1/help-center/home/sections/{section_id}/items` | add help home item | `help_article.write` |  | |
| POST | `/api/v1/help-center/import` | Nhập bài viết từ file HTML / Markdown — mỗi file thành 1 bài. | `help_article.create` |  | |
| POST | `/api/v1/help-center/import/parse` | Đọc 1 file → trả {title, summary, content} đã lọc, KHÔNG ghi DB. | `help_article.write` |  | |
| GET | `/api/v1/help-center/search` | Tìm kiếm bài viết theo tiêu đề HOẶC nội dung, kèm đoạn trích quanh từ khóa. | — |  | |
| DELETE | `/api/v1/help-center/slides/{slide_id}` | delete article slide | `help_article.delete` |  | |
| PUT | `/api/v1/help-center/slides/{slide_id}` | update article slide | `help_article.write` |  | |
| GET | `/api/v1/help-center/tree` | Danh sách phẳng bài viết để client dựng cây thư mục. | — |  | |
| POST | `/api/v1/help-center/upload-image` | Upload ảnh (chèn vào trình soạn thảo hoặc làm slide) và trả về URL. | `help_article.write` |  | |
| DELETE | `/api/v1/help-center/{article_id}` | delete help article | `help_article.delete` |  | |
| GET | `/api/v1/help-center/{article_id}` | Chi tiết 1 bài viết gồm nội dung HTML và danh sách slide. | — |  | |
| PUT | `/api/v1/help-center/{article_id}` | update help article | `help_article.write` |  | |
| POST | `/api/v1/help-center/{article_id}/slides` | add article slide | `help_article.write` |  | |
| GET | `/api/v1/faq` | Danh sách câu hỏi. Trang người dùng gọi với active_only=true để bỏ câu đang ẩn. | — |  | |
| POST | `/api/v1/faq` | create faq | `help_article.create` |  | |
| DELETE | `/api/v1/faq/{faq_id}` | delete faq | `help_article.delete` |  | |
| GET | `/api/v1/faq/{faq_id}` | get faq | — |  | |
| PUT | `/api/v1/faq/{faq_id}` | update faq | `help_article.write` |  | |
| GET | `/api/alerts` | list alerts | — |  | |
| GET | `/api/reports/daily` | Chi phí theo NGÀY trong 1 tháng (drill-down khi click cột). Nhẹ: lọc theo tháng rồi gom theo ngày. | `report.read` |  | |
| GET | `/api/reports/dept-range` | Đặt hàng & đơn gấp theo Bộ phận trong khoảng NGÀY (date_from, date_to = YYYY-MM-DD). Tính realtime. | `report.read` |  | |
| GET | `/api/reports/export` | Xuất báo cáo mua hàng ra Excel (khớp form thumua1 sheet 12–16). | `report.export` |  | |
| GET | `/api/reports/ig-range` | Tần suất mua & chi phí theo Loại VTBB/NL trong khoảng NGÀY (date_from, date_to = YYYY-MM-DD). Tính realtime. | `report.read` |  | |
| GET | `/api/reports/import-landed-cost` | Giá vốn lô hàng (bao-CR-347; ba giai đoạn chi phí bao-CR-453) — chọn theo mã đơn | `report.read` |  | |
| GET | `/api/reports/import-landed-cost/export` | Xuất báo cáo giá vốn lô hàng ra Excel — hai sheet, theo lô và theo dòng hàng; nhận | `report.export` |  | |
| GET | `/api/reports/matrix` | Báo cáo ma trận (NCC/phân loại/NSPT/bộ phận/vận chuyển) — stale-while-revalidate. | `report.read` |  | |
| GET | `/api/reports/nspt-range` | Giao hàng theo NSPT trong khoảng NGÀY (date_from, date_to = YYYY-MM-DD). Tính realtime. | `report.read` |  | |
| GET | `/api/reports/pr-lines` | Báo cáo Yêu cầu mua hàng theo DÒNG hàng (bao-CR-295) — phân trang server (50/trang). | `report.read` |  | |
| GET | `/api/reports/pr-lines/export` | bao-CR-691: xuất Excel bảng Chi tiết YC mua hàng — cùng bộ lọc với `/pr-lines`, không phân trang, trần | `report.export` |  | |
| GET | `/api/reports/pr-lines/summary` | Tổng hợp của báo cáo Chi tiết YC mua hàng (theo tiến độ / tháng / bộ phận / nhóm hàng / | `báo cáo 2`, `report.read` |  | |
| GET | `/api/reports/pr-lines/summary/export` | Xuất Excel bản THEO KỲ của báo cáo Chi tiết YC mua hàng (P03) — cùng bộ lọc với `/summary`. | `báo cáo 2`, `report.export` |  | |
| GET | `/api/reports/procurement` | procurement | `report.read` |  | |
| GET | `/api/reports/procurement/summary` | Tổng hợp Báo cáo mua hàng kiểu Haravan — kỳ + so sánh + Xem theo, hợp đồng chuẩn | `báo cáo 1`, `report.read` |  | |
| GET | `/api/reports/procurement/summary/export` | procurement summary export | `báo cáo 1`, `report.export` |  | |
| GET | `/api/reports/request-matrix` | Ma trận phòng ban × tháng cho Yêu cầu mua hàng (kind=pyc) / khảo sát (kind=ycks). Có apply_scope theo user. | `report.read` | `apply_scope` | |
| GET | `/api/reports/request-range` | Bảng phẳng phòng ban theo khoảng ngày cho PYC/YCKS (có scope). | `report.read` |  | |
| GET | `/api/reports/shipping-detail` | Chi tiết chi phí vận chuyển theo đơn hàng — phân trang server (page, page_size=50). | `report.read` |  | |
| GET | `/api/reports/sup-range` | Giao dịch & trễ theo NCC trong khoảng NGÀY (date_from, date_to = YYYY-MM-DD). Tính realtime. | `report.read` |  | |
| GET | `/api/report-access` | 13 báo cáo theo đúng thứ tự khóa, mỗi báo cáo kèm danh sách dòng CÒN SỐNG. | `role.read` |  | |
| DELETE | `/api/report-access/grants/{access_id}` | revoke report access | `role.write` |  | |
| POST | `/api/report-access/{key}/grants` | grant report access | `role.write` |  | |
| GET | `/api/settings` | get settings | `setting.read` |  | |
| PUT | `/api/settings` | save settings | `setting.write` |  | |
| POST | `/api/settings/test-email` | test email | `setting.write` |  | |
| POST | `/api/settings/test-storage` | test storage | `setting.write` |  | |
| GET | `/api/system-logs` | Danh sách gộp theo `request_id` — mỗi dòng là MỘT lượt gọi. | — |  | |
| GET | `/api/system-logs/summary` | Số liệu ba biểu đồ. | — |  | |
| GET | `/api/system-logs/{request_id}` | Gói bốn tab của một lượt gọi: Tổng quan · Request · Thay đổi · Phiên. | — |  | |
| GET | `/api/system/jobs` | list jobs | `setting.read` |  | |
| GET | `/api/system/jobs/{code}/runs` | list runs | `setting.read` |  | |
| GET | `/api/audit-logs` | list logs | — |  | |
| GET | `/api/login-sessions` | Danh sách phiên, mới nhất trước. `active_only` = chưa thu hồi (mặc định); | `login_session.read` | `apply_scope` | |
| GET | `/api/login-sessions/history` | Lịch sử đăng nhập của MỘT người trong N ngày: mọi dòng phiên (kể cả đã thu | `login_session.read` |  | |
| POST | `/api/login-sessions/users/{user_id}/logout-all` | Bắt đăng nhập lại: cắt MỌI thiết bị của một người, hiệu lực tức thì. | `login_session.delete` |  | |
| POST | `/api/login-sessions/{session_id}/revoke` | Đá MỘT thiết bị. Hiệu lực tối đa 60 giây (đệm tra phiên). | `login_session.delete` | `get_scoped` | |
| POST | `/api/auth/avatar` | update avatar | — |  | |
| POST | `/api/auth/change-password` | Người dùng tự đổi mật khẩu (đang đăng nhập). Body: {old_password, new_password}. | — |  | |
| POST | `/api/auth/forgot-password` | forgot password | — |  | |
| POST | `/api/auth/google` | login google | — |  | |
| POST | `/api/auth/login` | login | — |  | |
| POST | `/api/auth/logout` | Đăng xuất — bao-CR-360 khiến việc này **có hiệu lực thật** (đóng BM-002). | — |  | |
| GET | `/api/auth/me` | me | — |  | |
| PUT | `/api/auth/notify-email` | Người dùng tự bật/tắt email thông báo luồng duyệt của chính mình (bao-CR-349). | — |  | |
| POST | `/api/auth/refresh` | refresh | — |  | |
| POST | `/api/auth/reset-password` | reset password | — |  | |
| GET | `/api/auth/sessions` | Phiên của CHÍNH MÌNH, mới nhất trước; phiên đang gọi được đánh dấu `is_current`. | — |  | |
| GET | `/api/auth/sessions/history` | Lịch sử đăng nhập của CHÍNH MÌNH trong N ngày (bao-CR-400): mọi lần vào | — |  | |
| POST | `/api/auth/sessions/revoke-others` | Đăng xuất mọi thiết bị KHÁC, giữ thiết bị đang bấm nút — cùng cơ chế với | — |  | |
| POST | `/api/auth/sessions/{session_id}/revoke` | Đá MỘT thiết bị của mình. Phiên của người khác → 404 như không tồn tại. | — |  | |
| DELETE | `/api/auth/signature` | Gỡ chữ ký khỏi hồ sơ. Chỉ xóa liên kết, file trên storage giữ nguyên (không phá phiếu đã in). | — |  | |
| POST | `/api/auth/signature` | Tải ảnh chữ ký cá nhân (PNG nền trong là đẹp nhất). Mỗi lần tải ghi đè URL cũ. | — |  | |
| GET | `/api/users` | list users | `user.read` | `scope_condition` | |
| POST | `/api/users` | provision user | `user.create` |  | |
| DELETE | `/api/users/{user_id}` | delete user | `user.delete` |  | |
| GET | `/api/users/{user_id}` | get user | `user.read` | `get_scoped` | |
| PUT | `/api/users/{user_id}/active` | set active | `user.write` |  | |
| PUT | `/api/users/{user_id}/notify-email` | Quản trị bật/tắt hộ email thông báo cho một tài khoản (bao-CR-349). | `user.write` |  | |
| POST | `/api/users/{user_id}/reset-password` | reset password | `user.write` |  | |
| PUT | `/api/users/{user_id}/roles` | assign roles | `user.write` |  | |
| GET | `/api/users/{user_id}/roles/{role_id}/scope` | get scope | `user.read` |  | |
| PUT | `/api/users/{user_id}/roles/{role_id}/scope` | set scope | `user.write` |  | |
| GET | `/api/roles` | list roles | `role.read` |  | |
| POST | `/api/roles` | create role | `role.create` |  | |
| GET | `/api/roles/meta` | Danh sách quyền config (đối tượng x hành động) để FE dựng ma trận. | `role.read` |  | |
| PUT | `/api/roles/order` | Lưu THỨ TỰ HIỆN của danh sách vai trò (kéo thả ở màn Phân quyền). | `role.write` |  | |
| DELETE | `/api/roles/{rid}` | delete role | `role.delete` |  | |
| GET | `/api/roles/{rid}` | get role | `role.read` |  | |
| PATCH | `/api/roles/{rid}` | update role | `role.write` |  | |
| GET | `/api/roles/{rid}/permissions` | get permissions | `role.read` |  | |
| PUT | `/api/roles/{rid}/permissions` | set permissions | `role.write` |  | |
| DELETE | `/api/companies` | bulk delete companies | `company.delete` | `scope_condition` | |
| GET | `/api/companies` | list companies | `company.read` | `apply_scope` | |
| POST | `/api/companies` | create company | `company.create` |  | |
| DELETE | `/api/companies/{cid}` | delete company | `company.delete` |  | |
| GET | `/api/companies/{cid}` | get company | `company.read` |  | |
| PATCH | `/api/companies/{cid}` | update company | `company.write` |  | |
| POST | `/api/companies/{cid}/logo` | Cập nhật logo công ty — lưu file thật vào tab_file và gắn link qua tab_file_link. | `company.write` |  | |
| GET | `/api/departments` | list departments | `department.read` |  | |
| POST | `/api/departments` | create department | `department.create` |  | |
| GET | `/api/departments/by-companies` | Các CẶP (phòng ban × pháp nhân) của những pháp nhân được hỏi. | `department.read` |  | |
| GET | `/api/departments/export/csv` | export departments csv | `department.export` |  | |
| POST | `/api/departments/import/csv` | duoc-CR-628: Nhập CSV phòng ban đã NGỪNG (ghi thẳng cột, xóa hàng loạt, không chạy thử). | `department.import` |  | |
| DELETE | `/api/departments/{did}` | delete department | `department.delete` |  | |
| GET | `/api/departments/{did}` | get department | `department.read` |  | |
| PATCH | `/api/departments/{did}` | update department | `department.write` |  | |
| GET | `/api/departments/{did}/companies` | list department companies | `department.read` |  | |
| PUT | `/api/departments/{did}/companies` | replace department companies | `department.write` |  | |
| GET | `/api/sync-logs` | Danh sách dòng sổ, mới nhất trước. Không trả `payload` (xem `schema.py`). | `sync_log.read` | `apply_scope` | |
| GET | `/api/sync-logs/meta` | Bộ chọn cho các ô lọc: nguồn, đối tượng, mã trạng thái, nhãn cờ. | `sync_log.read` |  | |
| GET | `/api/sync-logs/stats` | Thẻ đếm theo trạng thái trong N ngày gần đây. | `sync_log.read` | `apply_scope` | |
| GET | `/api/sync-logs/{log_id}` | Một dòng, kèm nguyên cục dữ liệu bên kia gửi sang và câu lỗi nguyên văn. | `sync_log.read` | `get_scoped` | |
| POST | `/api/sync-logs/{log_id}/retry` | Chạy lại một dòng hỏng — sinh DÒNG MỚI, không sửa dòng cũ. | `sync_log.write` | `get_scoped` | |
| GET | `/api/backups` | list  | `backup.read` |  | |
| POST | `/api/backups/accept-size` | *Chấp nhận cỡ mới*: CSDL thu nhỏ hợp lệ, gỡ dấu đáng ngờ để việc dọn bản cũ chạy lại. | `backup.delete` |  | |
| POST | `/api/backups/run` | Sao lưu ngay (bấm tay) — đẩy task vào worker, trả về ngay. | `backup.create` |  | |
| DELETE | `/api/backups/{bid}` | delete  | `backup.delete` |  | |
| GET | `/api/backups/{bid}/download` | Trả URL tải file backup (presigned, hết hạn ngắn). Bucket private nên không link công khai. | `backup.read` |  | |
| GET | `/api/feature-usage/breakdown` | feature breakdown | `báo cáo 15`, `setting.read` |  | |
| GET | `/api/feature-usage/summary` | feature summary | `báo cáo 15`, `setting.read` |  | |
| GET | `/api/feature-usage/summary/export` | feature summary export | `báo cáo 15`, `setting.export` |  | |
| POST | `/api/telemetry/ui-events` | post ui events | — |  | |
| GET | `/api/usage-profiles/by-app` | usage by app | `báo cáo 14`, `setting.read` |  | |
| GET | `/api/usage-profiles/cohorts` | usage cohorts | `báo cáo 14`, `setting.read` |  | |
| GET | `/api/usage-profiles/metrics` | usage metrics | `báo cáo 14`, `setting.read` |  | |
| GET | `/api/usage-profiles/summary` | usage summary | `báo cáo 14`, `setting.read` |  | |
| GET | `/api/usage-profiles/summary/export` | usage summary export | `báo cáo 14`, `setting.export` |  | |
| GET | `/api/usage-profiles/{user_id}` | usage profile | `báo cáo 14`, `setting.read` |  | |
| GET | `/api/work-capability/load` | Tải đang ôm từng người, tính lúc gọi. Phải truyền ít nhất một trong `company_id` / `department_id` / `employee_id`. | `báo cáo 16`, `setting.read` |  | |
| GET | `/api/work-capability/summary` | capability summary | `báo cáo 16`, `setting.read` |  | |
| GET | `/api/work-capability/summary/export` | capability summary export | `báo cáo 16`, `setting.export` |  | |

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
