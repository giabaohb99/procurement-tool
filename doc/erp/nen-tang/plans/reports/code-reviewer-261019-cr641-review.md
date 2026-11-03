# Review duoc-CR-641 «Hồ sơ cách làm việc» (uncommitted, erp-v2) — 19/10/2026

## Scope
- BE: `backend/app/modules/usage_profile/**` (37 tệp ~3.3k LOC), `core/usage_codes.py`, migration `usgprof01`, sửa ở core/*, auth, notification, approval/audit/export_log model, setting.
- FE: `core/telemetry/**`, `protected-route.tsx`, 6 trang form + list (móc), `modules/report/**` (usage-profile), statuses/app-routes/query-keys.
- Kiểm đã chạy:
  - `alembic heads` → `usgprof01 (head)` duy nhất; `alembic current` = usgprof01.
  - pytest 5 tệp CR-641 (api, thu_su_kien, gom_ngay, snapshot, don_su_kien) → **90 passed**.
  - vitest `src/core/telemetry` + `report/config|utils` + list page → **24 files / 167 passed**.
  - `scripts.gen_status_ts --check` (host) → khớp, 29 bộ mã.
  - So schema DB thật vs model 4 bảng mới → khớp cột/null/index/unique.
  - `report_route_keys()` nạp được ngoài app (14 khóa, ~4.5 s lần đầu).

## Overall
Khung tốt: gác kép đủ 4 đường, user_id lấy từ token, insert lô 1 câu, số truy vấn cố định có test, migration tự gác, không lưu từ khóa. Nhưng có 1 lỗi đếm sai dữ liệu chắc chắn (bấm hộ ở phiếu đóng dấu), 1 lệch hợp đồng FE↔BE (lọc kiểu làm việc), 1 đường ghi đè mất số gom lịch sử, và rủi ro riêng tư do công tắc mặc định BẬT trong khi pháp chế chưa duyệt.

---

## Critical
Không có lỗ hổng bảo mật / auth bypass. (Gác `require("setting",…)` + `require_report(14)` có trên cả 4 đường; test 403 phủ đủ.)

## High

### H1. Phiếu đóng dấu luôn bị đếm là «bấm hộ», và có thể ghi «được bấm hộ» nhầm người
- `backend/app/modules/usage_profile/daily_sources.py:131` lấy `(SealRequest.created_by, SealRequest.requester_id)`, nhưng `seal_request/service.py:254` ghi `requester_id = user.id` (ID TÀI KHOẢN), không phải id nhân sự như `PurchaseRequest.requester_id`.
- `daily_docs.py:64` so sánh `requester_emp (thật ra là user id) != creator_emp (employee id)` → gần như luôn khác.
- Đã chạy lại bằng `proxy_columns([(5,5)], …, user_emp={5:12})` → `done {5: 1}`: người tự lập phiếu đóng dấu của chính mình bị tính 1 lượt «đã bấm hộ».
  Nếu có nhân sự mang id = user id đó, người dùng của nhân sự ấy còn bị cộng `on_behalf_received`.
- Ảnh hưởng: sai `on_behalf_done/received` → sai `proxy_share`, `proxied_days_ratio`, nhãn PROXY_DEPENDENT, cột «bấm hộ» trong context snapshot. Không test nào phủ proxy.
- Sửa: với seal, quy `requester_id` ra employee (join `User.employee_id`) hoặc bỏ hẳn (seal luôn `created_by == requester_id`, không có lập hộ). Thêm test proxy cho cả ba nguồn.

### H2. Lọc «Kiểu làm việc» nhiều giá trị: FE gửi mảng, BE chỉ nhận một số, nên lọc sai mà không báo lỗi
- FE `pages/usage-profile-list-page.tsx:46` gửi `label=['2','5']` → `label=2&label=5` (test FE còn khẳng định hành vi này).
- BE `controller.py:39,50` khai `label: int | None = Query(None)`. Starlette trả GIÁ TRỊ CUỐI, nên chỉ lọc theo 5 và bỏ qua 2, không 422.
- Ảnh hưởng: chọn ≥ 2 kiểu thì danh sách và file Excel ra sai.
- Sửa: BE `label: list[int] | None = Query(None, max_length=10)`, validate từng phần tử, rồi `UserUsageLabel.label.in_(labels)`; thêm test API 2 nhãn.
  Hoặc FE khóa chọn một giá trị.

### H3. Gom lại một ngày cũ hơn hạn giữ nguồn sẽ GHI ĐÈ số gom tốt bằng số thiếu
- `daily_builder.py:93-104`: `write_rows` = DELETE ngày rồi INSERT lại từ nguồn thô. Nguồn thô bị dọn: request_log GET sau 90 ngày (`logging_policy.GET_RETENTION_DAYS`), `tab_ui_event` sau 90 ngày.
- Ba đường chạy được cho ngày cũ:
  - `backfill.py:25` nhận `--from` tùy ý; chỉ chặn số ngày, không chặn độ cũ;
  - `usage.aggregate_daily(day="…")` chạy tay;
  - `--days 90` chạm đúng ngày D-90, khi cleanup 04:20 đã xóa một phần sự kiện UI của ngày đó.
- Ảnh hưởng: `api_reads`, `first_seen_min`, `hourly`, `screens`, `reports`, `page_views`, `dwell_ms`… của ngày cũ về 0/None. Bản giữ 3 năm mất vĩnh viễn, không báo lỗi.
- Sửa: trong `aggregate_day` từ chối (hoặc cần `force=True`) khi `day < vn_today() - 89`. Backfill clamp `start ≥ vn_today() - 89`. Ghi rõ ở docstring.

### H4. Riêng tư: công tắc mặc định BẬT, nên deploy là thu thập ngay, trong khi pháp chế chưa duyệt
- `core/config.py:149` `USAGE_TRACKING_ENABLED: bool = True`.
- Plan phase-01 ghi mặc định `False`; phase-08 §28 ghi «để TẮT, chỉ bật SAU KHI HR đã gửi thông báo»; hint ở Cấu hình (`setting/service.py`) cũng ghi «Phải thông báo nhân viên trước khi bật».
- Tài liệu `tracking-nguoi-dung-ho-so-ca-nhan.md` mục 4 vẫn «CÒN MỞ — cần pháp chế / nhân sự duyệt», mục 13 tự nêu rủi ro.
- Ngoài ra, gom ngày từ request_log/audit/login **chạy bất kể công tắc**: hồ sơ hành vi từng người vẫn được dựng kể cả khi tắt.
- Sửa (chặn deploy):
  - đặt `USAGE_TRACKING_ENABLED=false` trong `.env` prod TRƯỚC khi deploy, hoặc đổi mặc định về `False` theo plan;
  - cân nhắc cho công tắc gác luôn 2 job gom/snapshot (hoặc thêm công tắc thứ hai);
  - xác nhận lại với chủ sản phẩm (xem Câu hỏi 1).

## Medium

### M1. Thông điệp lỗi phía client lưu nguyên văn, server không làm sạch
- `telemetry_service.py:34-36` chỉ cắt độ dài.
- Làm sạch chỉ ở FE (`install-global-error-capture.ts:10`: thay dãy ≥6 chữ số). Email, họ tên trong thông điệp nghiệp vụ (`logger.error('Route lỗi', error)` với lỗi API chứa tên người/mã phiếu), URL có `?q=` thì vẫn lọt.
- Route đã được chuẩn hóa lại ở server ("FE lỗi cũng không để lọt id"), còn `meta.m` thì không.
- Sửa: ở server áp lại cùng luật + xóa email (`\S+@\S+`), URL/query (`https?://\S+`, `\?\S*`). Nhỏ hơn nữa: chỉ giữ `name` + mã băm thông điệp.

### M2. Chặn 64 KB không chặn được gì thật
- `telemetry_controller.py:39-48`: chặn theo header `Content-Length`.
  - Thân chunked (không có header) đi qua.
  - FastAPI đọc và `json.loads` TOÀN BỘ thân TRƯỚC khi chạy `dependencies` và trước khi slowapi đếm lượt (limiter chỉ là decorator, không có middleware). Trần thật là nginx 100 MB.
- Ảnh hưởng: tài khoản đã đăng nhập gửi được thân lớn tùy ý, mỗi lượt bị parse vào RAM. Rủi ro thấp vì phải có token, nhưng docstring đang hứa sai.
- Sửa: middleware ASGI nhỏ cho riêng `/api/telemetry`, đếm byte từ `receive()` và cắt ở 64 KB; hoặc `location /api/telemetry { client_max_body_size 64k; }` ở nginx.

### M3. `active_after_resign` báo động giả khi gom lại ngày cũ
- `daily_builder.py:76`: `(resign_date and resign_date < day) or emp_status == RESIGNED`. `status` là trạng thái HIỆN TẠI.
- Backfill hoặc tự lành một ngày TRƯỚC khi nghỉ của người đã nghỉ, có hoạt động, sẽ bị cờ «hoạt động sau nghỉ việc». Đây là chỉ số an ninh, báo sai gây hiểu lầm.
- Sửa: có `resign_date` thì chỉ dùng ngày; `status` chỉ là phương án dự phòng khi không có ngày. Dùng `EMPLOYEE_STATUS` thay hằng `RESIGNED` chép tay.

### M4. «Lượt ghi» gồm cả POST không phải nghiệp vụ
- `daily_activity.py:14,68`: mọi POST/PUT/PATCH/DELETE trừ `/api/auth/*` đều là «ghi», gồm đánh dấu đã đọc thông báo, lưu tùy chỉnh, chat trợ lý AI…
- Hệ quả: `offhours_write_share`, `mobile_write_share`, `http_422_per_100_writes` và nhãn MOBILE_FIRST bị nhiễu, ví dụ đọc thông báo trên điện thoại buổi tối.
- Sửa: danh sách loại trừ (`/api/notifications`, `/api/user-preferences`, `/api/assistant`…) hoặc chỉ đếm route có audit nghiệp vụ.

### M5. Hàng đợi FE: `inFlight` bị keepalive xóa cờ sai lúc
- `telemetry-queue.ts:167`: `finally { inFlight = false }` chạy cả cho nhánh keepalive.
- Ví dụ: flush thường đang bay → tab ẩn → flush keepalive kết thúc trước → đặt `inFlight=false` → nhịp 30 s kế tiếp chạy song song flush thứ hai.
- Ảnh hưởng nhỏ: không nhân đôi sự kiện vì `takeBatches` đã rút bộ đệm, nhưng thứ tự lô 401 trả lại bộ đệm có thể đảo.
- Sửa: chỉ reset khi `!keepalive`.

### M6. Mã UI viết tay ở TS (R2)
- `core/telemetry/ui-event-codes.ts:7-26` chép tay `UI_EVENT`/`UI_FORM`, trùng tên `UI_FORM` với bản sinh trong `shared/constants/statuses.ts` (khác kiểu: object số vs `StatusOption[]`). Tên khóa cũng lệch: `SURVEY_REQUEST`/`EMPLOYEE` vs backend `QUOTE_REQUEST`/`EMPLOYEE_PROFILE`.
- Có test canh khớp số, nhưng trái luật «không viết tay bộ mã ở TS», và trùng tên dễ import nhầm.
- Sửa: cho `gen_status_ts.py` sinh thêm hằng số kiểu `UI_EVENT_TYPE_CODE`, hoặc đổi tên bản local (`UI_EVENT_CODE`, `UI_FORM_CODE`) và dẫn từ bản sinh.

## Low
- **L1** `snapshot_metrics_flow.py:162`: `completed.date()` là ngày UTC so với `due` (ngày VN). Việc xong 00:00–06:59 VN ngày D+1 bị tính «đúng hạn». Dùng `vn_date(completed)`. `work_overdue_open` (dòng 169) dùng `today` thật thay vì cuối cửa sổ, nên dựng lại tuần cũ ra số khác.
- **L2** Một sự kiện sai mẫu route → cả lô 100 sự kiện bị 422 và FE bỏ lô. Có thể cân nhắc bỏ từng sự kiện lỗi ở server thay vì từ chối cả lô.
- **L3** `model.py:23` `ix_ui_event_user_occurred` chưa có truy vấn nào dùng (gom ngày và snapshot lọc theo `occurred_at` / `event_type`), chỉ tốn ghi. `latest_label_week_and_since` và `min(day) where page_views>0` quét toàn bảng (nhỏ, ~100k dòng/3 năm — chấp nhận được).
- **L4** `report_route_keys()` dùng `lru_cache`. Lần đầu worker không import được `app.main` thì `{}` bị nhớ cho cả vòng đời worker, chỉ số «báo cáo hay mở» âm thầm rỗng. Đề xuất không cache khi rỗng và `log.warning`.
- **L5** `chain_audits` (`snapshot_sources.py`) lọc `entity_id IN (…)` không kèm entity, cũng không chặn `created_at`, nên nạp thừa audit của entity khác trùng id và quét mọi phân vùng năm. Kết quả vẫn đúng nhờ kiểm submit-trong-W; chỉ tốn I/O.
- **L6** `approvals` đếm cả `line_approve` theo dòng: duyệt 1 YCBG 30 dòng = 30 lượt duyệt, nên `batch_approval_share` / BATCH_WORKER bị đẩy lên.
- **L7** Sự kiện giữ lại do 401 qua đêm sẽ mang `occurred_at = now − 10′` khi gửi lại, rơi nhầm ngày. Đây là đánh đổi có chủ đích; nên ghi rõ trong tài liệu.
- **L8** Plan `plan.md` vẫn ghi tiêu đề `duoc-CR-635`, tên report `…cr635…`, còn code/test/change-log dùng CR-641. Nên thống nhất trước commit.

## Edge cases scouted (đã kiểm, OK)
- Telemetry:
  - `user_id`/`session_id` lấy từ token + ctx, không lấy từ body;
  - `extra="forbid"`, mọi chuỗi có `max_length`;
  - `age_ms` bị kẹp; rate key `u{uid}` (`_peek_user_id` có kiểm chữ ký);
  - `/api/telemetry` nằm trong `SKIP_PATH_PREFIXES`; không có trường từ khóa;
  - route chuẩn hóa lại ở server.
- Gác: 4 đường đều `GUARD` + `require(setting, read|export)`; `/summary`, `/cohorts` khai trước `/{user_id}`; trợ lý AI cố ý loại khóa 14 (test cr208).
- Giờ VN: `vn_day_bounds`, `minute_of_day`, `vn_today` dùng đúng; celery `Asia/Ho_Chi_Minh`, `enable_utc=False`.
- Ngày lễ gộp dòng chung + riêng; nghỉ phép chỉ tính đơn ĐÃ DUYỆT, không xóa; `leave_days` cắt theo `work_mask`.
- Decimal MySQL: `decorate` ép `float/int`; `rnd()` ép `float`; `ratio(Decimal, Decimal)` an toàn.
- Idempotent: daily DELETE+INSERT theo ngày; snapshot xóa nhãn → snapshot → INSERT; UNIQUE chặn nhân đôi.
- Cleanup: chỉ `occurred_at < now-90d` và `day/period_start < today-3y`, xóa theo lô id, có trần, có `dry_run`.
- Migration: khớp model (đã so trên DB thật), một head, tự gác `inspect`, downgrade drop ngược thứ tự, không đụng dữ liệu nghiệp vụ; ADD INDEX trên `tab_audit_log` phân vùng là online DDL.
- N+1: list ≤5, profile ≤7 truy vấn có test 2 vs 15 người / 4 vs 12 tuần; gom ngày ~14 truy vấn cố định; insert lô 1 câu.
- FE:
  - 401 giữ lô; 204 / `accepted=0` thì tắt; keepalive cộng dồn ≤ 60 KB;
  - `pagehide` chạy hook PAGE_LEAVE/FORM_ABANDON trước khi flush;
  - tìm kiếm theo `debouncedValue` + chờ `isFetching`, nên không bắn theo từng phím;
  - hook dọn listener;
  - đăng xuất → `setEnabled(false)` xóa bộ đệm, không lẫn sang người sau;
  - chỉ số `unmeasured` hiện «Chưa đo được — lý do», không hiện 0.
- R2: các cột mới là SMALLINT + IntEnum, đăng ký `code_sets`, TS sinh khớp. Không entity mới nên không cần SCOPE_FIELDS. ReportKey 14 đi đủ chuỗi: `report_keys.py` → gen TS → catalog `key: 14` → `require_report` trên `/summary` + `/summary/export`.

## Recommended actions (thứ tự)
1. H4: chốt mặc định công tắc / `.env` prod = false trước deploy; quyết có gác cả job gom không.
2. H1: sửa nguồn bấm hộ của seal + test.
3. H2: BE nhận `list[int]` cho `label` + test.
4. H3: chặn gom lại ngày ngoài hạn giữ nguồn.
5. M1–M4, rồi M5/M6.
6. Low: gom vào commit dọn sau.

## Metrics
- Backend tests CR-641 (5/8 tệp chạy): 90 pass. FE: 167 pass. Typecheck/lint: chưa chạy cả cây (máy hạn chế).
- Alembic heads: 1 (`usgprof01`).

**Status:** DONE_WITH_CONCERNS
**Summary:** Gác quyền và ống thu sự kiện chắc chắn. Có 3 lỗi đúng/sai dữ liệu cần sửa trước commit: seal bị tính bấm hộ, lọc nhiều nhãn chỉ áp nhãn cuối, gom lại ngày cũ ghi đè mất số. Thêm 1 rủi ro riêng tư khi deploy: công tắc mặc định BẬT.

## Unresolved questions
1. Chủ sản phẩm chốt «mặc định BẬT» có biết là deploy prod sẽ thu thập ngay khi pháp chế chưa duyệt không? Công tắc có nên gác luôn cả phần gom từ nhật ký sẵn có không?
2. Viết trong giờ nghỉ phép đã duyệt có tính «ngoài giờ» không? (Hiện: không, vì chỉ theo DaySpec.)
3. `tab_request_log.query_string` vẫn lưu `?q=` từ khóa tìm kiếm của mọi màn danh sách (có sẵn từ trước). Tiêu chí 6 «không bảng nào chứa từ khóa tìm kiếm» có tính bảng này không?
