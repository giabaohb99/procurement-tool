# Phase 02 — Gom ngày (`tab_usage_daily`) từ bảng sẵn có + sự kiện UI, backfill

**Ưu tiên:** P1 · **Effort:** 7h · **Phụ thuộc:** 01 · **Trạng thái:** pending

## Ngữ cảnh
- Công thức từng chỉ số: [`metric-definitions.md`](metric-definitions.md) cột "Daily".
- Lịch làm việc gom nhiều người: `work_schedule/resolver_many.load_day_plans_many` (3 truy vấn cố định), `day_rules.work_mask/day_capacity`, `FALLBACK_WEEK`.
- Ngày lễ: `leave/holiday_calendar.holiday_names_many` (1 truy vấn). Nghỉ phép: `LeaveRequest.status == LR_APPROVED` + `work_schedule/roster_leave.leave_mask_on`.
- Giờ VN: `core/vn_time.py`, `VN_OFFSET` (container + DB lưu UTC naive).
- Đếm truy vấn: `test/backend/lich_lam_viec_factory.count_queries(db, fn)`.

## Kiến trúc (`backend/app/modules/usage_profile/`, mỗi tệp < 200 dòng)
```
daily_window.py      ngày VN → [utc_from, utc_to); phút-trong-ngày; referer → path rồi gọi route_pattern.normalize_route (phase 01)
daily_sources.py     ĐÚNG các truy vấn của 1 ngày (tất cả người dùng một lượt):
                     Q1 request_log (user_id>0, source=API): user_id, created_at, method, http_status, session_id, route, referer, ip
                     Q2 login_session: dòng tạo trong D + dòng có id ∈ session của Q1 (device_type, ip, os, browser)
                     Q3 login_session 90 ngày trước D của người có đăng nhập D (ip, chữ ký thiết bị) — so "chưa từng thấy"
                     Q4 audit_log actor_kind=1 trong D: created_by, entity, entity_id, action, action_group, session_id, created_at
                     Q5 export_log trong D: created_by, row_count
                     Q6 ui_event trong D (theo occurred_at)
                     Q7 người dùng active + employee (company, department, status, resign_date)
                     Q8–10 load_day_plans_many · Q11 holiday_names_many · Q12 đơn nghỉ LR_APPROVED chồng D
                     Q13 bấm hộ: leave_request/purchase_request/seal_request tạo trong D có người đề nghị ≠ người tạo
                     Q14 tab_approval_action trong D có on_behalf_of_id
daily_workday.py     is_workday / is_holiday / work_capacity / leave_days / ngoài giờ (thuần, nhận DaySpec)
daily_activity.py    hourly, bursts (> 30 phút = phiên mới), first/last, offhours, mobile, 403/422/5xx, parallel IP 10', reports, screens(api_calls)
daily_docs.py        TASK_VERB_BY_ACTION, TRACKED_DOC_ENTITIES → docs JSON, deletes + cửa sổ trượt 10', approvals
daily_ui.py          page_views, dwell, first_route, screens(views/dwell), forms, searches, client_errors
daily_builder.py     ghép → list[dict] dòng; cắt JSON theo trần; ghi: DELETE dòng của D rồi bulk INSERT (idempotent)
report_route_keys.py {route_path: ReportKey} dựng MỘT lần từ app.routes (dependency có `report_key`, chỉ đường `/summary`) — DRY với gác quyền
tasks_daily.py       Celery `usage.aggregate_daily(day=None)` → mặc định hôm qua VN
backfill.py          `python -m app.modules.usage_profile.backfill --days 90 [--from YYYY-MM-DD]` — lặp tuần tự, commit mỗi ngày
```

## Luật
1. Có dòng cho **mọi người dùng active có hồ sơ nhân sự** mỗi ngày (kể cả không vào) — thiếu thì "ngày làm việc ròng" sai.
   Tài khoản không có nhân sự (admin máy) vẫn có dòng nếu có hoạt động, lịch = `FALLBACK_WEEK`, công ty 0.
2. `leave_days` = phần nửa buổi nghỉ ∩ nửa buổi phải làm, tối đa `work_capacity`; chỉ đơn ĐÃ DUYỆT.
3. Ngoài giờ: giờ VN của lượt GHI < `spec.start` hoặc ≥ `spec.end`, hoặc ngày OFF/lễ. Bỏ `/api/auth/*`.
4. Referer: chỉ lấy path; rỗng → bỏ qua; pattern dài > 120 → cắt.
5. Số truy vấn KHÔNG phụ thuộc số người/số dòng (không vòng lặp gọi DB theo người).
6. Lỗi một ngày không làm hỏng ngày khác (backfill): bắt lỗi, log, đi tiếp, trả danh sách ngày lỗi.

## Tệp
- Tạo: 9 tệp trên + `test/backend/test_ho_so_lam_viec_gom_ngay_cr641.py` (+ factory `test/backend/ho_so_lam_viec_factory.py` nếu cần)
- KHÔNG sửa `core/celery_app.py` ở phase này (phase 04 đăng ký cả 3 job).

## Các bước
1. `daily_window.py` + test thuần (biên ngày VN: 23:30 VN thuộc D, 06:30 VN hôm sau không thuộc D; chuẩn hóa `/procurement/purchase-orders/129?x=1` → `/procurement/purchase-orders/:id`).
2. `daily_sources.py`: `with_entities` đúng cột, lọc trong SQL, KHÔNG ORM object đầy đủ.
3. Các bộ tính thuần (workday/activity/docs/ui) — nhận list tuple, trả dict theo user_id.
4. `daily_builder.py` + ghi idempotent.
5. `tasks_daily.py`, `backfill.py` (ngủ 0,2 s giữa các ngày để không chiếm DB).
6. Đo trên dữ liệu local cỡ prod (seed 10k request_log/ngày): < 10 s/ngày.

## Todo
- [ ] daily_window + chuẩn hóa pattern
- [ ] daily_sources (14 truy vấn cố định)
- [ ] workday / activity / docs / ui tính thuần
- [ ] builder + ghi idempotent + trần JSON
- [ ] task Celery + backfill
- [ ] test + đếm truy vấn

## Kiểm (`test_ho_so_lam_viec_gom_ngay_cr641.py`)
- Lịch riêng (T2–T6 07:30–16:30) → lượt ghi 17:00 là ngoài giờ; mặc định → 17:00 cũng ngoài giờ, 16:59 trong giờ; CN/lễ → ngoài giờ.
- Nghỉ phép đã duyệt nửa buổi → `leave_days=0.5`; đơn chờ duyệt/bị từ chối → 0; ngày lễ → `is_workday=False`.
- Người không vào vẫn có dòng `active=False`; chạy lại cùng ngày → không nhân đôi.
- Phiên làm việc: 3 lượt cách 10' + 1 lượt sau 45' → `work_bursts=2`.
- Thiết bị: lượt ghi qua phiên `device_type=2` → `writes_mobile`.
- Docs: create/update/submit/approve/return đúng ô; entity ngoài whitelist bị bỏ.
- Bấm hộ: đơn nghỉ employee A do user B tạo → B `on_behalf_done=1`, A `on_behalf_received=1`.
- UI: PAGE_VIEW/LEAVE → views, dwell; FORM_* → forms; SEARCH n=0 → searches_empty; first_route đúng.
- Nghỉ việc (resign_date < D) mà có request → `active_after_resign=True`.
- **Đếm truy vấn**: 2 người vs 12 người (mỗi người vài chục dòng) → số truy vấn bằng nhau.
Chạy: `docker compose exec -T api python -m pytest test/backend/test_ho_so_lam_viec_gom_ngay_cr641.py -q`.

## Rủi ro
| Rủi ro | K × T | Giảm thiểu |
|---|---|---|
| Q1 kéo ~10k dòng/ngày vào RAM | Thấp × Thấp | cột hẹp; ~1–2 MB; job đêm |
| Backfill 90 ngày dồn tải DB | Trung bình × Trung bình | chạy tay ngoài giờ, tuần tự, ngủ giữa ngày |
| GET đã bị dọn > 90 ngày → backfill xa hơn thiếu dữ liệu đọc | Chắc chắn × Thấp | backfill giới hạn 90 ngày; ghi chú ở màn "dữ liệu từ ngày …" |
| v1 (thumua) dùng chung DB → referer pattern của v1 không khớp menu v2 | Cao × Thấp | FE hiện pattern thô kèm nhãn "giao diện cũ" |
| Đổi tên action trong ACTION_CATALOG làm rơi động từ | Thấp × Trung bình | test khẳng định mọi khóa của `TASK_VERB_BY_ACTION` có trong `ACTION_CATALOG` |

## Bảo mật
Đọc `referer` chỉ lấy PATH, bỏ query (query có thể chứa `q=` từ khóa). Không đọc `query_string`, `request_body`, `response_body`.
