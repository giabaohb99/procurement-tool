# Bảng định nghĩa chỉ số — §3 của thiết kế → nguồn · công thức · pha · trạng thái

Quy ước: **D** = ngày VN (UTC 17:00 hôm trước → 17:00 hôm đó; mọi `created_at` lưu UTC naive, cộng `VN_OFFSET`).
**W** = cửa sổ snapshot 4 tuần kết thúc Chủ nhật. **Ngày làm việc ròng** = Σ(`work_capacity` − `leave_days`) trên các ngày
`is_workday` (Lịch làm việc qua `resolver_many`, mặc định T2–T7 08–17; trừ lễ `holiday_names_many`; trừ đơn nghỉ
`LR_APPROVED` theo `roster_leave.leave_mask_on`). Ô "Daily" = cột/JSON của `tab_usage_daily`; "Snap" = tính lúc dựng
snapshot. Pha: P1 = gom từ bảng có sẵn · P2 = cần `tab_ui_event`/`read_at` · P3 = nhãn/xu hướng.
Khóa chỉ số (cột 2) là khóa CỐ ĐỊNH trong `usage_profile/metric_catalog.py` — đổi tên là gãy snapshot cũ + pha 4.

## 3.1 Nhịp làm việc

| Chỉ số | Khóa | Nguồn → công thức | Pha | Trạng thái |
|---|---|---|---|---|
| Giờ vào đầu / thao tác cuối | `first_seen_p50_min`, `last_action_p50_min` | Daily `first_seen_min`/`last_action_min` = min/max (request_log ∪ ui_event) phút-trong-ngày VN; Snap = trung vị ngày active | P1 | GIỮ |
| Bản đồ nhiệt giờ × thứ | `heatmap` (7×24) | Daily `hourly[24]` = số lượt request_log theo giờ VN; Snap cộng theo thứ | P1 | GIỮ |
| Ngày có vào / ngày làm việc | `active_ratio`, `active_workdays`, `workdays_net` | Daily `active` ∧ `is_workday`; ratio = active_workdays / workdays_net (≤ 1) | P1 | GIỮ |
| Số phiên/ngày, thời lượng | `bursts_per_day`, `active_minutes_p50`, `logins` | ⚠️ ĐỔI ĐỊNH NGHĨA: phiên đăng nhập sống 7 ngày (refresh) nên không phản ánh "vào ra". Phiên làm việc = chuỗi lượt (request_log ∪ ui_event) ngắt khi nghỉ > 30 phút → Daily `work_bursts`, `active_minutes`; `logins` = số dòng login_session tạo trong D | P1 | GIỮ (định nghĩa mới) |
| Thao tác ngoài giờ, cuối tuần | `offhours_write_share` | Daily `writes_offhours` = lượt GHI (POST/PATCH/PUT/DELETE, trừ `/api/auth/*`) ngoài [start, end] của DaySpec, hoặc ngày OFF/lễ; giờ trưa tính trong giờ | P1 | GIỮ |
| Tỷ lệ điện thoại theo loại thao tác | `mobile_write_share`, `mobile_approve_share` | request_log.session_id ⨝ login_session.device_type=2 → Daily `writes_mobile`; audit nhóm DUYỆT ⨝ session → `approvals_mobile` | P1 | GIỮ |

## 3.2 Trang truy cập

| Chỉ số | Khóa | Nguồn → công thức | Pha | Trạng thái |
|---|---|---|---|---|
| Top 10 màn | `top_screens` | P2: Daily `screens{pattern:[views,dwell_ms,api_calls]}` từ PAGE_VIEW. P1 ước lượng: `referer` của request_log → bỏ host/query, số/uuid → `:id` → `api_calls` | P1+P2 | GIỮ (cờ `source`) |
| % thời gian theo phân hệ | `module_time_share` | Σ dwell_ms theo pattern; FE ánh xạ pattern → phân hệ qua `module-registry` | P2 | GIỮ |
| Ở lại TB từng màn | `screen_dwell_avg` | dwell_ms / số PAGE_LEAVE của pattern (chỉ thời gian tab đang hiện) | P2 | GIỮ |
| Màn mở đầu ngày | `first_screen_mode` | Daily `first_route` = PAGE_VIEW sớm nhất; Snap = giá trị hay gặp nhất + số lần đổi | P2 | GIỮ |
| Đường đi A→B→C | `top_paths`, `loop_share` | Snap từ `tab_ui_event` thô (còn trong 90 ngày): chuỗi PAGE_VIEW theo (session_id, tab_key), top 5 bộ ba; vòng = A→B→A | P2 | GIỮ (chỉ trong 90 ngày) |
| Số màn khác nhau 30 ngày | `distinct_screens_30d` | đếm khóa `screens` (views>0) trong 30 ngày | P2 | GIỮ |
| Báo cáo hay mở | `reports_opened` | GET `/summary` → `ReportKey` tra từ `app.routes` (dependency có `report_key`) → Daily `reports{key:n}` | P1 | GIỮ |
| Bị chặn quyền 403 | `http_403`, `top_403_routes` | request_log `http_status=403` → Daily `http_403`, `forbidden_routes` (top 5 route mẫu) | P1 | GIỮ |

## 3.3 Cách làm task (theo `entity` trong `TRACKED_DOC_ENTITIES`)

`TRACKED_DOC_ENTITIES` = purchase_request, survey_request, purchase_order, goods_receipt, payment_request, document,
leave_request, vehicle_booking, seal_request, labor_contract. Động từ từ `audit.action` qua bảng `TASK_VERB_BY_ACTION`
(create · update · submit/submitted · approve/approved · reject/rejected · return/returned · delete).

| Chỉ số | Khóa | Nguồn → công thức | Pha | Trạng thái |
|---|---|---|---|---|
| Lập / gửi / duyệt / từ chối | `docs.{entity}.{c,s,a,r}` | audit `actor_kind=1` theo created_by × entity × động từ → Daily `docs` JSON | P1 | GIỮ |
| Thời gian lập một phiếu | `form_submit_p50_ms` | FORM_SUBMIT.duration_ms theo `form_key` (6 form có móc) | P2 | GIỮ (chỉ 6 form) |
| Lưu nháp trước khi gửi | `drafts_before_submit_p50` | Snap: phiếu gửi lần đầu trong W → đếm `update` của chính người tạo trước `submit` đầu | P1 | GIỮ |
| Sửa sau khi gửi | `edits_after_submit_share` | Snap: phiếu có `update` của người tạo sau `submit` đầu / số phiếu đã gửi | P1 | GIỮ |
| Bị trả về / từ chối | `returned_rate` | Snap: phiếu người này tạo có `return`/`reject` bởi người khác / số phiếu đã gửi | P1 | GIỮ |
| Mở form rồi bỏ | `form_abandon_rate` | FORM_ABANDON / FORM_OPEN theo form_key | P2 | GIỮ |
| Tới lượt → xử lý (p50, p90) | `approval_wait_p50_h`, `approval_wait_p90_h`, `pending_now` | Snap: `tab_approval_task` (assignee_employee_id → user) `decided_at − created_at` (giờ lịch). ⚠️ việc "lần lượt" có thể được tạo trước lúc tới lượt — implementer kiểm `task_service`; nếu vậy lấy `decided_at` của việc trước cùng instance làm mốc | P1 | GIỮ cho phiếu qua bộ máy duyệt; YCMH/ĐMH duyệt ngoài bộ máy → **HOÃN** (không có mốc "tới lượt" tin được) |
| Xử lý theo lô | `batch_approval_share` | Snap: lượt duyệt nằm trong cụm ≥ 5 quyết định / 10 phút ÷ tổng | P1 | GIỮ |
| Phiếu tạo 3 ngày cuối tháng | `month_end_create_share` | Daily `docs.*.c` của ngày ≥ (cuối tháng − 2), cửa sổ 3 tháng | P1 | GIỮ |
| Bấm hộ / được bấm hộ | `on_behalf_received`, `on_behalf_done` | ⚠️ ĐỔI NGUỒN: `audit.on_behalf_of` hiện KHÔNG lời gọi nào điền (luôn 0). Dùng: (a) phiếu mà người đề nghị ≠ người tạo — leave_request.employee_id, purchase_request.requester_id, seal_request.requester_id so với created_by→employee; (b) `tab_approval_action.on_behalf_of_id` (duyệt thay theo ủy quyền) | P1 | GIỮ (nguồn mới) |
| Nhập tay hay nhập file, % dòng lỗi | `imports`, `import_error_rate` | `tab_import_batch` created_by: Σ error_count / Σ total_rows | P1 | GIỮ |
| Việc dự án đúng hạn / quá hạn | `work_on_time_rate`, `work_overdue_open` | `tab_work_task_assignee` ⨝ `tab_work_task` (due_date, completed_at) theo employee | P1 | GIỮ |

## 3.4 Phản hồi và phối hợp

| Chỉ số | Khóa | Nguồn → công thức | Pha | Trạng thái |
|---|---|---|---|---|
| Tỷ lệ đọc thông báo | `notif_read_rate` | Snap: `tab_notification` tạo trong W: is_read / tổng | P1 | GIỮ |
| Gửi → đọc mất bao lâu | `notif_read_p50_min` | `read_at − created_at` (cột mới, chỉ từ ngày deploy, không bù) | P2 | GIỮ |
| Nhắc tên → trả lời | `mention_reply_p50_h` | `tab_comment_mention` (user_id) ⨝ bình luận đầu tiên của người được nhắc cùng `entity/entity_id` sau mốc nhắc | P1 | GIỮ (best-effort) |
| Bình luận trên phiếu mình / người khác | `comments` | `tab_comment` theo created_by → tổng số | P1 | GIỮ tổng; tách mình/khác **HOÃN** (cần tra chủ phiếu từng entity) |
| Hỏi trợ lý AI | `assistant_questions`, `assistant_changes` | `tab_assistant_message` (vai người dùng) + `tab_assistant_change` | P1 | GIỮ số đếm; "chủ đề hay hỏi" **BỎ** (là văn bản tự do, trái §7.4) |

## 3.5 Mức thành thạo

| Chỉ số | Khóa | Nguồn → công thức | Pha | Trạng thái |
|---|---|---|---|---|
| Lưu bộ lọc, tùy chỉnh cột | `saved_prefs` | `tab_user_preference` đếm theo user (pref_key nhóm lọc/cột) | P1 | GIỮ |
| Lỗi 422 / 100 lần lưu | `http_422_per_100_writes` | Daily `http_422` / `api_writes` × 100 | P1 | GIỮ mức route; mức TRƯỜNG («Ngày giao») **HOÃN** (phải bóc `response_body.details`) |
| Tìm không ra kết quả | `search_empty_rate` | SEARCH result_count=0 / SEARCH — KHÔNG từ khóa | P2 | GIỮ |
| Xem hướng dẫn / FAQ, yêu cầu hỗ trợ | `help_views`, `tickets` | PAGE_VIEW pattern `/help%` + `tab_ticket.requester_id` | P2 + P1 | GIỮ |
| Xuất Excel so với xem màn | `exports`, `export_per_list_view` | `tab_export_log` theo created_by; chia PAGE_VIEW màn danh sách | P1 + P2 | GIỮ |
| Xu hướng 4–8 tuần | `trend[]` | mỗi chỉ số trong snapshot mang 4 giá trị tuần (đọc từ snapshot trước) | P3 | GIỮ |

## 3.6 An toàn tài khoản

| Chỉ số | Khóa | Nguồn → công thức | Pha | Trạng thái |
|---|---|---|---|---|
| IP / thiết bị chưa từng thấy | `new_ip_logins`, `new_device_logins` | login_session trong D so với 90 ngày trước của cùng user (IP nguyên văn; thiết bị = device_type\|os\|browser) | P1 | GIỮ |
| Nhiều nơi cùng lúc | `max_parallel_ips` | request_log: số IP khác nhau tối đa trong một khung 10 phút | P1 | GIỮ |
| Xuất vượt mức thường | `export_rows_spike` | Snap: export_rows tuần > 3 × p95 tuần của chính người đó 12 tuần trước (≥ 1.000 dòng) | P1 | GIỮ |
| Xóa hàng loạt | `max_deletes_10min` | audit nhóm XÓA, cửa sổ trượt 10 phút | P1 | GIỮ |
| Quyền 90 ngày không dùng | — | — | — | **HOÃN**: đọc (GET) không ánh xạ được route → entity; chỉ làm được nửa phần ghi, dễ kết luận sai "quyền thừa" |
| Nghỉ việc vẫn hoạt động | `active_after_resign` | employee.resign_date < D (hoặc status nghỉ việc) ∧ Daily `active` | P1 | GIỮ |

## 3.8 Dùng AI (duoc-CR-655) — pha 3: cần `tab_ai_usage_daily` (ai-CR-230)

Chưa có số dùng AI (bảng trống / chưa tồn tại / mốc thu sau cửa sổ) → cả 8 khóa ở `unmeasured` = `NOT_COLLECTED`. Đã thu mà người này
không dùng → 0 (đo được thật). Chỉ số đếm và mã, không nội dung câu hỏi. Kênh / ứng dụng / nhóm công cụ chính là MÃ nên nằm ở `lists`
(`ai_channels`, `ai_clients`, `ai_tool_groups`), không thành khóa số (trung vị của mã vô nghĩa).

| Chỉ số | Khóa | Nguồn → công thức | Pha | Trạng thái |
|---|---|---|---|---|
| Lượt dùng AI | `ai_uses` | Σ `turns` của người trong cửa sổ (web/Telegram/Zalo = câu hỏi, MCP = lượt gọi công cụ) | P3 | GIỮ |
| Ngày có dùng AI | `ai_active_days` | số ngày có `turns`+`tool_calls` > 0 | P3 | GIỮ |
| Dùng qua ứng dụng ngoài | `ai_mcp_share` | `turns` kênh MCP / `ai_uses` (0 lượt → chưa đo được) | P3 | GIỮ |
| Nhóm việc nhờ AI | `ai_tool_groups_used` | số khóa khác nhau trong `tool_groups` | P3 | GIỮ |
| AI bị từ chối quyền | `ai_denied` | Σ `denied` | P3 | GIỮ |
| Nháp AI đã xác nhận | `ai_drafts_confirmed` | Σ `drafts_confirmed` | P3 | GIỮ |
| Phiếu do AI soạn | `ai_docs_drafted` | `tab_audit_log` action `create`, entity ∈ `TRACKED_DOC_ENTITIES`, `ai_channel` > 0; DISTINCT (entity, entity_id) | P3 | GIỮ |
| Phiếu AI soạn / phiếu lập | `ai_docs_share` | `ai_docs_drafted` / `docs_created`, trần 100% (0 phiếu lập → chưa đo được) | P3 | GIỮ |
| Câu hỏi trợ lý AI (3.4) | `assistant_questions` | giữ khóa; lấy số lớn hơn giữa tin nhắn trợ lý (DB ERP) và `turns` kênh web | P1 | ĐỔI NGUỒN |

## Đánh dấu "chưa đo được" (`unmeasured`) — bắt buộc cho pha 4

Mỗi khóa không có giá trị mang mã lý do `UnmeasuredReason`: `1` chưa bật thu sự kiện / trước ngày bật · `2` dưới ngưỡng dữ
liệu (vd < 5 phiếu) · `3` không áp dụng (vd không có việc duyệt nào). Không bao giờ ghi 0 thay cho "không đo được".
