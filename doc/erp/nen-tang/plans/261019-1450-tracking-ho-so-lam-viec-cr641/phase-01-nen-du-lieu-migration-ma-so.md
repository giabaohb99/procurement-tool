# Phase 01 — Nền dữ liệu: model, mã số, migration, công tắc

**Ưu tiên:** P1 (chặn mọi phase) · **Effort:** 3h · **Trạng thái:** pending

## Ngữ cảnh
- Luật R2/QĐ-11 (cột kiểu/loại = SMALLINT + IntEnum, nhãn chỉ ở tầng hiển thị) — mẫu `core/report_keys.py`, `core/work_schedule_codes.py`.
- `core/code_sets.py` + `scripts/gen_status_ts.py` sinh `frontend-v2/src/shared/constants/statuses.ts`.
- Bảng nhật ký chỉ-thêm KHÔNG dùng `AuditMixin` (tiền lệ `tab_request_log`, §4.3.1 nhật ký).
- `tab_audit_log` chưa có chỉ mục `created_at` (chỉ entity, entity_id, request_id, session_id) — gom ngày sẽ quét cả phân vùng năm.
- Head hiện tại: `lbrct03`. Memory: autogenerate trôi ~650 dòng → phải gọt tay.

## Quyết định
- **4 bảng mới** (không tách bảng con theo phân hệ — JSON nhỏ có trần trong `tab_usage_daily` đủ cho đọc theo người; YAGNI).
- `module` KHÔNG thành cột: suy từ `route_pattern` ở FE qua `module-registry` (tránh thêm bộ mã phân hệ phải đồng bộ 2 phía).
- `occurred_at` tính ở server = `now − age_ms` (FE gửi tuổi sự kiện, không gửi giờ máy) → không lệch đồng hồ máy khách.

## Lược đồ

`tab_ui_event` (chỉ-thêm, giữ 90 ngày)
| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | BIGINT PK | |
| created_at | DATETIME | server nhận (UTC) |
| occurred_at | DATETIME | `created_at − clamp(age_ms, 0, 600000)` |
| user_id | BIGINT | |
| session_id | BIGINT NULL | `tab_login_session.id` |
| tab_key | INT | số ngẫu nhiên mỗi lần nạp trang — tách đường đi khi mở nhiều tab |
| event_type | SMALLINT | `UiEventType` |
| route_pattern | VARCHAR(120) | `/procurement/purchase-orders/:id`, không query/hash |
| form_key | SMALLINT | `UiForm`, 0 = không phải form |
| duration_ms | INT | 0..86.400.000 |
| result_count | INT NULL | chỉ SEARCH |
| meta | JSON NULL | chỉ CLIENT_ERROR: `{"n": tên≤60, "m": thông điệp≤200}` |
Chỉ mục: `ix_ui_event_occurred_at(occurred_at)`, `ix_ui_event_user_occurred(user_id, occurred_at)`.

`tab_usage_daily` (giữ lâu, ~100 người × 365 ≈ 36k dòng/năm) — UNIQUE `(user_id, day)`, index `(day)`
- định danh: `id, user_id, day DATE, employee_id, company_id, department_id, computed_at`
- lịch: `is_workday BOOL, is_holiday BOOL, work_capacity FLOAT, leave_days FLOAT, active BOOL`
- nhịp: `first_seen_min SMALLINT NULL, last_action_min SMALLINT NULL, work_bursts SMALLINT, active_minutes SMALLINT, logins SMALLINT`
- API: `api_reads INT, api_writes INT, writes_offhours INT, writes_mobile INT, approvals INT, approvals_mobile INT, http_403 INT, http_422 INT, http_5xx INT`
- khác: `exports INT, export_rows INT, deletes INT, max_deletes_10min SMALLINT, new_ip_logins SMALLINT, new_device_logins SMALLINT, max_parallel_ips SMALLINT, on_behalf_received INT, on_behalf_done INT, active_after_resign BOOL`
- UI (P2): `page_views INT, dwell_ms BIGINT, searches INT, searches_empty INT, client_errors INT, first_route VARCHAR(120)`
- JSON có trần (builder cắt, tổng ≤ 16 KB): `hourly` [24 số], `screens` {pattern: [views, dwell_ms, api_calls]} top 40, `docs` {entity: {c,u,s,a,r,t,d}}, `forms` {form_key: [open, submit, abandon, submit_ms]}, `reports` {key: n}, `forbidden_routes` {route: n} top 5.

`tab_user_usage_snapshot` — UNIQUE `(user_id, period_kind, period_start)`, index `(period_kind, period_start)`
`id, user_id, period_kind SMALLINT (1=tuần), period_start DATE (thứ Hai), window_weeks SMALLINT, schema_version SMALLINT, cohort_kind SMALLINT, cohort_key BIGINT, cohort_size SMALLINT, metrics JSON, computed_at`

`tab_user_usage_label` — UNIQUE `(snapshot_id, label)`, index `(period_start, label)`, index `(user_id)`
`id, snapshot_id BIGINT, user_id, period_start DATE, label SMALLINT (UsageStyle), score FLOAT, evidence JSON (≤10 khóa chỉ số)`

Sửa bảng cũ: `tab_notification.read_at DATETIME NULL` + `ix_tab_notification_created_at`; `ix_tab_audit_log_created_at`;
`ix_tab_export_log_created_at`; `ix_approval_task_decided_at`. **Tất cả trong MỘT migration** (luật "index gom 1 migration").

## Mã số (`backend/app/core/usage_codes.py`, thuần stdlib, register vào code_sets)
- `UiEventType`: 1 PAGE_VIEW · 2 PAGE_LEAVE · 3 FORM_OPEN · 4 FORM_SUBMIT · 5 FORM_ABANDON · 6 SEARCH · 7 CLIENT_ERROR
- `UiForm`: 1 YCMH · 2 YCBG · 3 ĐMH · 4 Đơn nghỉ phép · 5 HĐLĐ · 6 Hồ sơ nhân sự
- `UsageStyle` (§4): 1 Làm dồn · 2 Nút thắt duyệt · 3 Dùng Excel song song · 4 Người mới đang vướng · 5 Người thạo · 6 Hay đi lạc · 7 Làm trên điện thoại · 8 Phiếu kém chất lượng · 9 Nhờ làm hộ · 10 Ít dùng
- `CohortKind`: 1 vai trò · 2 pháp nhân · 3 toàn công ty · `UnmeasuredReason`: 1 chưa thu · 2 dưới ngưỡng · 3 không áp dụng
- Số đã cấp KHÔNG đổi, KHÔNG tái dùng (docstring chép luật của `report_keys.py`).

## Công tắc
`core/app_settings.py` REGISTRY: `"usage_tracking_enabled": ("bool", "USAGE_TRACKING_ENABLED")`; `core/config.py` mặc định `False`;
`setting/service.py` FIELDS thêm mục nhóm hệ thống, nhãn «Thu thập cách dùng giao diện (hồ sơ cách làm việc)», hint ghi rõ phải
thông báo nhân viên trước khi bật.

## Tệp
- Tạo: `backend/app/modules/usage_profile/__init__.py`, `model.py`, `route_pattern.py` (hàm thuần `normalize_route`: bỏ host/query/hash,
  đoạn toàn số / uuid / mã phiếu dạng `[A-Z]{2,}\d+` → `:id`, cắt 120 — phase 02 và 03 cùng dùng, đặt ở đây để hai phase song song không giành tệp);
  `backend/app/core/usage_codes.py`;
  `backend/migrations/versions/usgprof01_ho_so_lam_viec_cr641.py`
- Sửa: `core/all_models.py`, `core/code_sets.py`, `core/app_settings.py`, `core/config.py`, `modules/setting/service.py`,
  `modules/notification/model.py` (cột `read_at`), `modules/audit/model.py` + `export_log/model.py` + `approval/instance_model.py` (khai index cho khớp DB),
  `frontend-v2/src/shared/constants/statuses.ts` (SINH, không viết tay)

## Các bước
1. Viết `usage_codes.py` + đăng ký code set; chạy `python scripts/gen_status_ts.py`.
2. Viết model 4 bảng (BigInteger PK, model khai PK 1 cột như tiền lệ để SQLite `create_all` chạy).
3. `alembic upgrade head` → `--autogenerate -m usgprof01` → **gọt về đúng** 4 bảng + 1 cột + 4 index; docstring ghi đã cắt gì. `revision="usgprof01"`, `down_revision="lbrct03"`.
4. `ADD INDEX` trên `tab_audit_log` (bảng phân vùng theo năm): chạy được online; ghi chú canh giờ thấp điểm.
5. downgrade đầy đủ (drop ngược thứ tự).
6. Công tắc + FIELDS.

## Todo
- [ ] usage_codes.py + code_sets + gen_status_ts
- [ ] model.py 4 bảng + all_models
- [ ] read_at + index khai ở model cũ
- [ ] migration usgprof01 gọt tay, upgrade/downgrade chạy được trên MySQL local
- [ ] công tắc usage_tracking_enabled

## Kiểm
`test/backend/test_ho_so_lam_viec_ma_so_cr641.py`: giá trị số cố định từng enum, code set có trong `code_sets`, nhãn tiếng Việt
đủ; `normalize_route`: `/procurement/purchase-orders/129?q=abc#x` → `/procurement/purchase-orders/:id`, uuid, mã `PO2026001`,
chuỗi rỗng → `/`, 500 ký tự → cắt 120, `//a//b/` → `/a/b`.
Chạy: `docker compose exec -T api python -m pytest test/backend/test_ho_so_lam_viec_ma_so_cr641.py -q`.
Thủ công: `alembic upgrade head && alembic downgrade -1 && alembic upgrade head`.

## Rủi ro
| Rủi ro | Khả năng × Tác động | Giảm thiểu |
|---|---|---|
| Autogenerate kéo drift vào migration | Cao × Trung bình | gọt tay, review diff chỉ còn đúng đối tượng của CR |
| `ADD INDEX` trên audit_log khóa bảng lâu | Thấp × Cao | InnoDB online DDL; bảng hiện nhỏ; chạy lúc thấp điểm |
| Hai nhánh song song cùng chạy sau `lbrct03` | Trung bình × Trung bình | kiểm `alembic heads` trước khi merge; có nhánh khác thì đổi `down_revision` |

## Bảo mật
Không cột nào chứa body, từ khóa, id bản ghi. `meta` chỉ cho CLIENT_ERROR, trần 512 byte.
