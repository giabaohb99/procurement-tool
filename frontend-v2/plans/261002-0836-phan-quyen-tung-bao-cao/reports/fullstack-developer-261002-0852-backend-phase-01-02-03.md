# Backend phase 01-03 — phân quyền xem từng báo cáo

Plan: `frontend-v2/plans/261002-0836-phan-quyen-tung-bao-cao/`. Phạm vi: phase 01 (khóa/bảng/migration/seed),
phase 02 (gác 26 đường + `/auth/me` + API cấu hình), phase 03 (test). Không commit.

## Hợp đồng API cho FE (đọc trước khi làm phase 04-06)

### 1. `report_keys` trong `/api/auth/me` (KHÔNG có `/api/report-access/me` riêng — đúng Q1)
`GET /api/auth/me`, `POST /api/auth/login`, `POST /api/auth/google`, `POST /api/auth/refresh` đều
trả qua `_me_payload` — field mới:
```json
{ "report_keys": [1, 3, 11] }
```
Mảng `int` đã `sorted()`, rỗng khi chưa được gán báo cáo nào (= đóng, đúng chốt "chưa gán = đóng").

### 2. Hằng số sinh ra ở `statuses.ts`
`REPORT_KEY: readonly StatusOption[]` (13 phần tử, `value` là CHUỖI SỐ `"1".."13"`, `label` khớp
catalog FE, `sort_order` = chính con số khóa). Cũng có trong `STATUS_SETS.report_key`. Map số ↔ tên
khóa dùng `ReportKey` TypeScript riêng (nếu phase 05 cần enum thay vì số trần) — số ở đây KHÔNG đổi:
PURCHASE_REPORT=1, PR_LINES=2, SURVEY_PROGRESS=3, PURCHASE_PROGRESS=4, SURVEY_REPORT=5,
HR_HEADCOUNT=6, LEAVE_USAGE=7, LEAVE_BALANCE=8, VEHICLE_BOOKING=9, SEAL_REQUEST=10, DOCUMENT=11,
APPROVAL=12, WORK=13.

### 3. 26 đường `/summary`+`/summary/export` gác thêm 403
Mất quyền báo cáo → `403 {"success":false,"error":{"code":"403","message":"Chưa được giao xem báo cáo: <nhãn>"}}`.
Gác KÉP — `require(entity,...)`/`apply_scope` cũ GIỮ NGUYÊN, không đổi path/tham số/response khi
ĐÃ có quyền. FE không cần sửa gì ở 13 trang biểu đồ hiện có TRỪ xử lý 403 mới (đã có pattern xử lý
403 chung, chỉ là lý do 403 nay có thêm một nguồn).

### 4. `GET/POST/DELETE /api/report-access` (gác `role.read`/`role.write`)

`GET /api/report-access` → `data`: mảng 13 mục, ĐÚNG thứ tự khóa 1..13:
```json
[{ "key": 11, "label": "Báo cáo văn bản", "group": "Hành chính",
  "grants": [{ "id": 5, "subject_kind": 4, "subject_kind_label": "Vai trò", "subject_id": 7,
              "subject_name": "Quản trị hệ thống", "effect": 1, "reason": "", "valid_from": null,
              "valid_to": null, "created_at": "2026-10-02T10:00:00" }] }]
```
`subject_kind`: 1 người (NHÂN SỰ) · 2 phòng ban · 3 pháp nhân · 4 vai trò. `effect`: 1 cho phép · 2
cấm. Chỉ dòng CÒN SỐNG (chưa thu hồi) — khớp Q6.

`POST /api/report-access/{key}/grants` — `key` là số (404 nếu ngoài 1..13):
```json
// request
{ "subjects": [{ "subject_kind": 4, "subject_id": 7 }],   // 1..200 phần tử
 "effect": 1, "reason": "", "valid_from": null, "valid_to": null }   // valid_* optional (Q2)
// response data
{ "created": 1, "updated": 0, "skipped": [] }
// skipped khi chủ thể không tồn tại:
"skipped": [{ "subject_kind": 1, "subject_id": 999999, "reason": "Không tìm thấy đối tượng" }]
```
Trùng (key, subject_kind, subject_id, effect) còn sống → SỬA dòng đó (updated), không đẻ dòng mới.
Không chặn tự gán cho chính mình/vai trò mình (Q5) — gán rộng tay không mở rộng dữ liệu vì gác kép.

`DELETE /api/report-access/grants/{access_id}` body `{ "reason": "" }` → thu hồi (đánh dấu
`revoked_at`, không xóa dòng); gọi lần 2 trên dòng đã thu hồi → 400.

Validate: `reason` ≤ 500 ký tự, `subjects` 1..200 phần tử, `subject_kind` ∈ {1,2,3,4}, `effect` ∈
{1,2} — sai → 422.

## Quyết định thiết kế đáng chú ý
- Khóa `ReportKey` (SMALLINT + IntEnum, R2) khai ở `backend/app/core/report_keys.py` — thuần
  stdlib, gộp CẢ enum + nhãn + đăng ký `CodeSet` một tệp (khác forum vì model `report_access` không
  cần chính `ReportKey` để khai cột).
- Bảng `tab_report_access` cùng hình dạng `tab_doc_folder_access`/`tab_document_access` — dùng lại
  `core/subject_match.py`. Nâng `subject_names()` dùng chung lên đó (trước ở
  `doc_catalog/folder_access_view_service.py`, giờ tệp đó gọi lại hàm chung — hành vi giữ nguyên).
- Migration `rptacc01` viết tay, danh sách 13 khóa ĐÓNG BĂNG trong migration (không import
  `ReportKey`). Đã kiểm `alembic upgrade head → downgrade -1 → upgrade head` sạch trên local, 1 head
  duy nhất (`rptacc01`).
- `ensure_report_access_defaults` gọi trong `seed.run()` VÀ `seed_prod.run()` ngay sau
  `ensure_admin_role` — đã kiểm chạy 2 lần không nhân đôi dòng (idempotent).
- Gác bằng `dependencies=[Depends(require_report(ReportKey.X))]` trên decorator của CẢ 26 đường —
  không đụng `user=Depends(require(...))` sẵn có. Đã soi `app.routes`: đúng 26 đường có khóa, 4
  đường còn lại (`/api/payables/summary`, `/api/system-logs/summary`,
  `/api/customs/imports/{bid}/rows/summary`, `/api/leave-balances/tools/summary`) không gác khóa
  nào — khớp bảng loại trừ của phase-02.

## Phát hiện ngoài kế hoạch — bẫy cache Redis làm test HTTP ăn 403/200 SAI
`core/report_cache.ReportSummaryCacheMiddleware` (gói A2, tính năng khác, đã có trước) cache GET
`/summary` qua REDIS THẬT, khóa = `sha256(path + query + sha256(Bearer token))`. Test dùng
`app.dependency_overrides` để giả `get_current_user` KHÔNG set header `Authorization`, nên MỌI
request test tới cùng path+query chia đúng MỘT khóa cache (token rỗng) — một test trả 200 (cache
HIT) làm test SAU đó (mong 403 vì chưa gán quyền) nhận lại nguyên response cũ, bỏ qua HẲN
`require_report`/`require(entity,...)`. Không flaky theo code — flaky theo THỜI GIAN (TTL 60s) và
THỨ TỰ test chạy, tái hiện được 100% khi 2 test đụng cùng path trong cùng 60s.

Vá bằng cách gắn **Bearer token giả nhưng DUY NHẤT mỗi lần build TestClient**
(`TestClient(app, headers={"Authorization": f"Bearer test-{uuid4().hex}"})`) ở MỌI fixture
`client_as`/`_client_as` chạm 1 trong 13 đường `/summary` có `preset` — áp cho cả 4 tệp test cũ
(`test_bao_cao_van_ban.py`, `test_bao_cao_phe_duyet.py`, `test_bao_cao_cong_viec.py`,
`test_bao_cao_hanh_chinh.py`) + 1 test inline (`test_bao_cao_nhan_su.py`) + tệp mới
`test_phan_quyen_bao_cao_gac_duong.py`. Giá trị token không ảnh hưởng xác thực (đã giả hẳn
`get_current_user`), chỉ cần khác nhau giữa các lượt gọi. Ngoài phạm vi sửa `report_cache.py` (không
thuộc file ownership của phase này) — chỉ sửa phía test.

## File đã tạo / sửa
Tạo: `backend/app/core/report_keys.py`; `backend/app/modules/report_access/{__init__,model,service,
guard,schema,grant_service,controller,seed_defaults}.py`; migration
`backend/migrations/versions/rptacc01_phan_quyen_tung_bao_cao.py`; 4 tệp test
`test/backend/test_phan_quyen_bao_cao_{gac_duong,chu_the,cau_hinh_api,mac_dinh_admin}.py`.

Sửa: `backend/app/core/{code_sets,all_models,subject_match}.py`, `backend/app/main.py`,
`backend/app/{seed,seed_prod}.py`, `backend/app/modules/auth/controller.py`,
`backend/app/modules/doc_catalog/folder_access_view_service.py`, 13 controller (26 route — xem
bảng phase-02), `frontend-v2/src/shared/constants/statuses.ts` (SINH lại, không gõ tay),
`test/backend/conftest.py` (+ fixture `gan_bao_cao`), 6 tệp test HTTP cũ,
`test/backend/test_pham_vi_luat_bat_bien.py` (+1 dòng `BB4_CONTROLLER_MIEN_TRU`).

## Test
Lệnh gate của phase-03 — chạy 2 lần liên tiếp, ổn định cả hai lần:
```
docker compose exec -T api python -m pytest -q test/backend/test_phan_quyen_bao_cao_*.py \
  test/backend/test_bao_cao_*.py test/backend/test_pham_vi_luat_bat_bien.py \
  test/backend/test_status_catalog_b01.py test/backend/test_van_ban_thu_muc_quyen*.py \
  test/backend/test_van_ban_thu_muc.py
# 497 passed, 1 skipped, 1 failed (PRE-EXISTING, không do phase này — xem dưới)
```
Đã thử "bỏ 1 decorator → test soi route đỏ ngay → gắn lại → xanh" (tiêu chí xong của phase-03).

## Concern — 1 test đỏ CÓ SẴN TRƯỚC khi tôi bắt đầu (không do phase 01-03)
`test_pham_vi_luat_bat_bien.py::test_bb4_controller_khong_loc_pham_vi_phai_co_ten_kem_ly_do` đỏ vì 6
controller (`approval/report_controller.py`, `document/report_controller.py`,
`employee/report_controller.py`, `leave/balance_report_controller.py`, `leave/report_controller.py`,
`work/report_controller.py`) chưa khai lý do miễn trừ BB-4. Đã xác nhận qua `git stash` — đỏ CẢ KHI
không có bất kỳ thay đổi nào của tôi, thuộc nợ kỹ thuật của một đợt trước (phase 05/06 báo cáo kiểu
Haravan). Không thuộc file ownership của phase 01-03 plan này nên không tự sửa; chỉ thêm đúng 1 dòng
cho `report_access/controller.py` (controller MỚI của chính phase này).

**Status:** DONE
**Summary:** Phase 01-03 backend xong — khóa/bảng/migration/seed (01), gác 26 đường +
`report_keys` ở `/auth/me` + API cấu hình `role.read/write` (02), 4 tệp test mới + vá 6 tệp cũ +
BB-4 (03). Gate xanh 2 lần liên tiếp, không flaky (phát hiện và vá bẫy cache Redis làm test HTTP
auth sai). Phase 04-06 (frontend) dùng hợp đồng ở đầu báo cáo này.
**Concerns:** 1 test BB-4 đỏ CÓ SẴN trước phiên này (6 controller thiếu lý do miễn trừ, nợ kỹ thuật
đợt trước) — ngoài phạm vi phase 01-03, cần một phiên riêng để soát + khai lý do hoặc thêm
`apply_scope`.
