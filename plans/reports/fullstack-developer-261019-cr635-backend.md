# Báo cáo backend — Hồ sơ cách làm việc (CR đổi số: duoc-CR-641; thư mục plan/migration/report vẫn ghi cr635)

## Trạng thái
Phase 01–05 + phần backend của 08: XONG. Chưa commit. Chưa đụng change-log.md / nhat-ky-task.md / seed.py / document / labor_contract / doc_catalog.

## Migration
- Revision `usgprof01`, down_revision `lbrct03`, tệp `backend/migrations/versions/usgprof01_ho_so_lam_viec_cr635.py` (lead tự đổi tên). `alembic heads` = 1 (`usgprof01`).
- Viết tay (không autogenerate); `alembic check` không lộ drift nào thuộc đối tượng của CR. Đã chạy up/down/up trên MySQL local: OK, các bước tự gác (inspect) nên chạy lại an toàn.
- Nội dung: 4 bảng (`tab_ui_event`, `tab_usage_daily`, `tab_user_usage_snapshot`, `tab_user_usage_label`) + `tab_notification.read_at` + 4 chỉ mục (`tab_notification.created_at`, `tab_audit_log.created_at`, `tab_export_log.created_at`, `tab_approval_task.decided_at`).
- Thêm so với plan: cột `tab_usage_daily.docs_created` (để danh sách cộng được bằng SQL, JSON `docs` không SUM được).
- DB local đã ở `usgprof01`; đã chạy `ensure_report_access_defaults` (chèn khóa 14 cho admin); đã backfill 14 ngày + dựng snapshot tuần 2026-10-12 (276 người) trên DB local để FE thử màn.

## Tệp (tất cả dưới backend/ và test/backend/)
Mới: `app/core/usage_codes.py`; `app/modules/usage_profile/` (28 tệp, mỗi tệp < 200 dòng: model, route_pattern, telemetry_{schema,service,controller}, tasks_{daily,snapshot,cleanup}, backfill, daily_{window,sources,workday,activity,docs,ui,builder}, report_route_keys, snapshot_{sources,metrics_rhythm,metrics_screens,metrics_flow,metrics_misc,paths,builder}, metric_{catalog,stats,partial}, label_{rules,thresholds}, cohort, schema, list_{service,export}, profile_service, cohort_service, controller).
Sửa: `core/{all_models,code_sets,app_settings,config,report_keys,logging_policy,celery_app}.py`, `main.py` (2 router), `modules/setting/service.py` (FIELDS), `modules/auth/controller.py` (`usage_tracking` ở `_me_payload`), `modules/notification/{model,controller}.py` (read_at), `modules/{audit,export_log}/model.py` + `modules/approval/instance_model.py` (khai chỉ mục). Sinh: `frontend-v2/src/shared/constants/statuses.ts` (gen_status_ts.py; +5 bộ mã: ui_event_type, ui_form, usage_style, usage_cohort_kind, usage_unmeasured_reason; `report_key` thêm mục 14).
Docs: `CLAUDE.md` (13→14 báo cáo, 28 đường), `doc/tai-lieu-ky-thuat/tracking-nguoi-dung-ho-so-ca-nhan.md` (v1.1: §8 chốt, §10, §11 lệch thiết kế, §12 thông báo NV bản nháp, §13 vận hành), `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` (+/api/telemetry vào bảng bỏ ghi; ghi chú ui_event 90 ngày không chờ R2).
Test sửa: `test_phan_quyen_bao_cao_{gac_duong,mac_dinh_admin,cau_hinh_api}.py` (13 → `len(ReportKey)`, thêm khóa 14), `test_assistant_report_summary_cr208.py` (khóa 14 CỐ Ý không mở cho công cụ `report_summary` của trợ lý AI).

## Quyết định chủ sản phẩm → cách làm
1. Gác: `require_report(ReportKey.USAGE_PROFILE=14)` + `require("setting","read")` (export dùng `"export"`) trên cả 4 đường. Admin có sẵn qua `ensure_report_access_defaults`. Không "của tôi", không lọc phạm vi.
2. Mục đích tham khảo đánh giá: nêu rõ trong §8 + §12 của doc (bản nháp thông báo tiếng Việt; khuyến nghị pháp chế/HR duyệt trước khi go-live).
3. Công tắc `usage_tracking_enabled`, mặc định BẬT (`USAGE_TRACKING_ENABLED=True` ở config; ô trong Cấu hình hệ thống nhóm «Hệ thống»). Tắt → 204, không ghi.
4. Giữ: `tab_ui_event` 90 ngày; `tab_usage_daily` + snapshot + nhãn 3 năm (`usage.cleanup_ui_events` xóa cả hai).
5. Không lưu từ khóa tìm kiếm; route mẫu không id (server chuẩn hóa lại); `user_id`/`session_id` từ token/ctx, schema `extra=forbid` nên body có `user_id` bị 422.
6. Ngoài giờ theo Lịch làm việc từng người (`load_day_plans_many`, fallback mặc định, ngày lễ), nghỉ phép ĐÃ DUYỆT trừ vào mẫu số.
7. Transport: endpoint nhận JSON lô + Bearer; loại khỏi `tab_request_log` (`SKIP_PATH_PREFIXES += /api/telemetry`); ≤100 sự kiện/lô, thân ≤ 64 KB (413 theo Content-Length), 30 lô/phút theo user.
8. Cohort: vai trò cụ thể nhất có ≥5 người (trừ admin/ADMINISTRATOR), không có → pháp nhân ≥5 → toàn công ty. Nút thắt duyệt: ≥2× trung vị nhóm VÀ ≥8h.

## Endpoint và JSON

### POST /api/telemetry/ui-events  (mọi người đã đăng nhập, Bearer)
Req: `{"events":[{"type":1,"route":"/procurement/purchase-orders/:id","form":0,"duration_ms":0,"result_count":null,"age_ms":1200,"tab_key":81723,"error":null}]}`
- `events` 1..100; `type` ∈ 1..7; `form` ∈ {0,1..6}; `route` 1..120 ký tự khớp `^/[A-Za-z0-9/_:\-.]*$`; `duration_ms` 0..86.400.000; `result_count` 0..1.000.000 (chỉ giữ cho SEARCH=6); `age_ms` ≥0 (>600.000 bị kẹp, không từ chối); `tab_key` 0..2^31-1; `error` chỉ khi type=7: `{"name"≤60,"message"≤200}`; khóa lạ → 422 (extra forbid).
- Resp: bật → 200 `{"success":true,"message":"OK","data":{"accepted":N}}`; **tắt → 204 không thân** (KHÁC plan: plan ghi 200 `{"accepted":0}`) — FE không được `res.json()` bừa trên 204. 413 thân >64KB; 401 chưa đăng nhập; 422 lô sai; 429 quá 30 lô/phút.
- `/api/auth/me` (và payload đăng nhập/refresh) thêm `"usage_tracking": bool`.

### GET /api/usage-profiles/summary  (gác kép; dùng chung bộ kỳ `preset/date_from/date_to` của báo cáo — preset gồm today…last_year|custom, `compare` bị bỏ qua)
Query: `preset` (mặc định this_month) · `date_from`/`date_to` (khi custom) · `company_id` · `department_id` · `role_id` · `label` (1..10) · `q` (≤100, tên/mã NV) · `page` ≥1 · `page_size` 1..100 (20) · `sort` ∈ {full_name, emp_code, active_ratio, active_days, workdays_net, api_writes, docs_created, approvals, exports, http_422_per_100_writes, last_active_day}, tiền tố `-` = giảm dần.
Resp data:
```
{"items":[{"user_id","full_name","emp_code","department_name","company_name",
  "cohort":{"kind","key","size","name"}|null,
  "active_days":int,"workdays_net":float,"active_ratio":float|null,"api_writes":int,"docs_created":int,
  "approvals":int,"exports":int,"http_422_per_100_writes":float|null,
  "labels":[{"code":int,"score":float}],"last_active_day":"YYYY-MM-DD"|null}],
 "total":int,"page":int,"page_size":int,
 "period":{"date_from","date_to"},"label_week":"YYYY-MM-DD"|null,"data_since":"YYYY-MM-DD"|null}
```
`labels`/`cohort` lấy từ snapshot tuần mới nhất ≤ date_to (`label_week`). Truy vấn cố định ≤5.

### GET /api/usage-profiles/summary/export  (`setting.export`)
Cùng tham số trừ `page/page_size`. Trả xlsx; ghi `tab_export_log` (entity `usage_profile`). >5.000 dòng → 400.

### GET /api/usage-profiles/cohorts?week=YYYY-MM-DD  (mặc định tuần mới nhất)
`{"week":"…"|null,"cohorts":[{"cohort_kind":1|2|3,"cohort_key":int,"name":str,"size":int,"medians":{"<metric_key>":number}}]}`

### GET /api/usage-profiles/{user_id}?weeks=8  (1..26; 404 nếu không có user)
```
{"subject":{"user_id","full_name","emp_code","position","department_name","company_name","role_names":[str],"hire_date"|null,"tenure_days"|null},
 "latest":null | {"period_start","schema_version","cohort":{"kind","key","size","name"},"period":{"start","end","window_weeks"},
    "context":{"workdays_net","leave_days","holidays","on_behalf_received","tracking_since"},
    "metrics":{"<key>":{"v":num,"med":num|null,"p75":num|null,"trend":[num|null,x4]}},
    "lists":{"heatmap":[[24 số]x7],"top_screens":[[route,views,dwell_ms,api_calls]],"screens_source":1(UI)|2(API),
             "module_time":[[route,dwell_ms]],"first_screen":[route,n_days,changes],"top_paths":[[a,b,c,n]],
             "reports":[[report_key,n]],"top_403_routes":[[route,n]],"docs":{"<entity>":{"c","u","s","a","r","t","d"}}},
    "counts":{...},"unmeasured":{"<key>":1|2|3},"labels":[{"code","score","evidence":[metric_key]}]},
 "weekly":[{"period_start","cohort_size","metrics":{"<key>":num},"labels":[code]}]   // tối đa `weeks` snapshot gần nhất, tăng dần
 "daily":[{"day","active","is_workday","is_holiday","work_capacity","leave_days","first_seen_min","last_action_min","work_bursts","active_minutes","api_reads","api_writes","writes_offhours","approvals","exports","http_403","http_422","page_views","on_behalf_received"}]   // weeks*7 ngày gần nhất
 "heatmap":[[24]x7],"screens":[{"route","views","dwell_ms","api_calls"}] (top 20),"screens_source":1|2,
 "metric_meta":{"<key>":{"unit","section","phase","direction"}},"deferred_metrics":[str],
 "data_since"|null,"tracking_since"|null}
```
Mã: `unmeasured` 1 chưa thu · 2 dưới ngưỡng · 3 không áp dụng; `labels.code` = UsageStyle 1..10; `cohort.kind` 1 vai trò / 2 pháp nhân / 3 toàn công ty. Chỉ số không đo được KHÔNG có trong `metrics` (không bao giờ ghi 0). Truy vấn cố định ≤6.

## Celery (giờ VN, đã vào `beat_schedule` + `imports`)
`usage.cleanup_ui_events` 04:20 · `usage.aggregate_daily` 04:30 (gom hôm qua) · `usage.build_weekly_snapshots` thứ Hai 05:15 (tuần vừa kết thúc; tự gom bù ngày thiếu). **Cần restart `celery-worker` + `celery-beat`.** Backfill: `docker compose exec api python -m app.modules.usage_profile.backfill --days 90` (đo local: 14 ngày ≈ 28 s trên DB dev ~276 người; snapshot ≈ 1 s).

## Test (chạy trong container, ≤10 tệp/lần)
Mới (8 tệp, hậu tố `_cr641`, plan ghi `_cr635`): ma_so (21), thu_su_kien (28), doc_thong_bao+don_su_kien (3+4), gom_ngay (24), snapshot (20), nhan_kieu (35), api (14) — tất cả xanh.
Đã chạy lại: 3 tệp `test_phan_quyen_bao_cao_*` + `chu_the`, `test_assistant_report_summary_cr208`, `test_pham_vi_khai_du_b07`, `test_bao_cao_phe_duyet`, `test_cau_hinh_*_cr429`, `test_me_payload…`, `test_status_catalog_b01` — xanh. Duy nhất `test_hai_quan_hq1_cr470` đỏ do thiếu module (ModuleNotFoundError), không liên quan.
Kiểm thủ công trên MySQL local: backfill/snapshot/summary/profile/cohorts/export chạy được (đã vá `Decimal` của SUM trên MySQL và thiếu `all_models` trong worker/script — hai lỗi SQLite không thấy); POST telemetry thật trả `{"accepted":1}`, sự kiện lưu `/procurement/purchase-orders/:id`, 0 dòng `tab_request_log` cho `/api/telemetry`; admin DEMOTP (không có khóa 14) gọi summary → 403 đúng.

## Không làm / lưu ý
- Chưa làm: phản hồi «nhận xét sai» của nhân viên; pha 4 AI. Chỉ số HOÃN/BỎ theo metric-definitions (`DEFERRED_METRICS`).
- `top_paths`/`loop_share` chỉ tính từ tuần cuối của cửa sổ; `screen_dwell_avg` = tổng dwell / số PAGE_VIEW (xấp xỉ); `form_submit_p50_ms` = trung vị của trung bình theo ngày; `saved_prefs` đếm mọi dòng `tab_user_preference` (không phân loại khóa); `export_per_list_view` coi màn list = route không chứa `:id` và không kết thúc `/new|/create|/edit`.
- Mốc «tới lượt» của duyệt lần lượt dựa `flow_snapshot` (nếu không đọc được thì tính từ lúc tạo việc).
- Đã vô tình xóa các dòng `tab_ui_event` (3 dòng của FE thử) và 2 dòng `tab_request_log` route `/api/telemetry` (404 lúc router chưa có) trên DB local.
- Sự cố nhỏ giữa chừng: `main.py` import `usage_profile.controller` trước khi có tệp làm dev api sập vài phút (đã có stub, rồi bản thật).
- Bật mặc định + chưa có thông báo NV: nếu deploy prod trước khi HR gửi thông báo sẽ thu thập ngay — xem §13 doc (đặt `USAGE_TRACKING_ENABLED=false` hoặc tắt ở màn Cấu hình).

**Status:** DONE_WITH_CONCERNS
**Summary:** Backend phase 01–05 + docs backend xong, test xanh, migration `usgprof01` chạy up/down/up trên MySQL local, API thật hoạt động.
**Concerns:** (1) telemetry khi tắt trả 204 (khác plan) — FE phải xử lý; (2) công tắc mặc định BẬT cần HR/pháp chế duyệt thông báo trước khi lên prod; (3) cần restart celery-worker/beat; (4) lead đổi tên migration + test `_cr641`↔`_cr635` nếu muốn thống nhất.
