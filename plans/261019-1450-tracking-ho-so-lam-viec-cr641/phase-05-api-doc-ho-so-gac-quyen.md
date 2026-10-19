# Phase 05 — API đọc hồ sơ + `ReportKey` 14 + gác quyền

**Ưu tiên:** P1 · **Effort:** 5h · **Phụ thuộc:** 04 · **Trạng thái:** pending · ⚠️ cùng PR với phase 07

## Ngữ cảnh
- Luật thêm báo cáo (CLAUDE.md, duoc-CR-562): `ReportKey` mới (số tiếp theo, không tái dùng) → `gen_status_ts.py` → `key` ở `report-catalog-*.ts`
  → `require_report` trên CẢ `/summary` và `/summary/export`. `test_phan_quyen_bao_cao_gac_duong.py` đếm đúng 2 đường/khóa.
- `report_access/seed_defaults.ensure_report_access_defaults` tự chèn dòng CHO PHÉP cho `admin` + `ADMINISTRATOR` với khóa CHƯA có dòng nào,
  chạy ở `seed.py` + `seed_prod.py` mỗi lần khởi động → **không cần chèn trong migration** (DRY).
- `report_cache.ReportSummaryCacheMiddleware` cache GET `/summary` theo (path, query, token) 60 s — chấp nhận được.
- Memory "API báo cáo nhanh nhất": gom SQL, số truy vấn cố định, test đếm truy vấn.

## Quyết định gác quyền
- Gác KÉP như 13 báo cáo cũ: `user=Depends(require("setting", "read"))` + `dependencies=[Depends(require_report(ReportKey.USAGE_PROFILE))]`.
  Chọn `setting` (không phải `audit`) vì mục danh mục FE phải có `sourcePath` khớp mục menu gốc cùng khóa — mục gốc là
  «Nhật ký hệ thống» `/system/logs`, khóa gác thực tế của nó trong test là `setting` (khóa phân hệ Quản trị). Không thêm entity mới
  (khỏi đụng `ENTITIES`, `SCOPE_FIELDS`, bài 44/44).
- Admin xem TẤT CẢ người, không `apply_scope` (khóa `setting` không có bảng để lọc). KHÔNG có đường "hồ sơ của tôi", không mở cho quản lý.
- Gán khóa 14 cho người khác ở tab «Báo cáo» của Phân quyền là hành động chủ ý của admin — xem câu hỏi mở Q1.

## Đường API (`usage_profile/controller.py`, prefix `/api/usage-profiles`)
| Đường | Trả | Truy vấn (trần) |
|---|---|---|
| `GET /summary?preset&from&to&company_id&department_id&role_id&label&q&page&page_size&sort` | `{items[], total, period, data_since}`; mỗi dòng: user_id, họ tên, mã NV, phòng, nhóm so sánh, active_days, workdays_net, active_ratio, api_writes, docs_created, approvals, exports, http_422_per_100_writes, labels[] (tuần gần nhất ≤ `to`), last_active_day | ≤ 5: đếm · trang (GROUP BY user trên `tab_usage_daily` ⨝ user/employee/department) · nhãn theo lô · tên vai trò nhóm theo lô · `MIN(day)` |
| `GET /summary/export` (cùng tham số) | xlsx qua `core/export_xlsx`, ghi `tab_export_log` (entity `usage_profile`) | ≤ 5 + ghi log |
| `GET /{user_id}?weeks=8` (1..26) | `subject` (họ tên, mã, phòng, vai trò nhóm, thâm niên) · `latest` = snapshot mới nhất (metrics, cohort, labels, unmeasured) · `weekly[]` các chỉ số chính · `daily[]` (day, active, is_workday, leave_days, first/last, writes) · `heatmap` · `screens[]` (gộp `screens` JSON các ngày, cờ nguồn API/UI) · `metric_meta` từ `metric_catalog` | ≤ 7: user+employee · vai trò · snapshot N tuần · nhãn · daily cửa sổ · (không vòng lặp theo ngày) |
| `GET /cohorts?week=YYYY-MM-DD` | `[{cohort_kind, cohort_key, name, size, medians{}}]` đọc từ snapshot của tuần (trung vị đã lưu trong `metrics.*.med`) | ≤ 3 |
404 khi user không tồn tại; `weeks`/`page_size` ngoài dải → 422 (Query `ge/le`).
Dữ liệu đọc: chỉ từ `tab_usage_daily` + snapshot + nhãn — KHÔNG đọc request_log/ui_event lúc mở màn (nhanh, và đúng §7.7).

## Tệp
- Tạo: `usage_profile/schema.py`, `list_service.py`, `list_export.py`, `profile_service.py`, `cohort_service.py`, `controller.py`
- Sửa: `core/report_keys.py` (`USAGE_PROFILE = 14`, `REPORT_META[14] = ("Hồ sơ cách làm việc", "Quản trị")`), `main.py` (router),
  `export_log/registry.py` nếu cần khai entity xuất, `frontend-v2/src/shared/constants/statuses.ts` (sinh lại)
- Sửa test cũ: `test_phan_quyen_bao_cao_gac_duong.py` (GATED + ROUTE_SPECS thêm khóa 14, entity `setting`),
  `test_phan_quyen_bao_cao_mac_dinh_admin.py` + `test_phan_quyen_bao_cao_cau_hinh_api.py` (đổi số cứng `13` → `len(ReportKey)`)
- Tạo test: `test/backend/test_ho_so_lam_viec_api_cr641.py`

## Các bước
1. Thêm `ReportKey.USAGE_PROFILE = 14` + nhãn; chạy `gen_status_ts.py`.
2. Service danh sách: một câu GROUP BY có phân trang ở SQL; lọc nhãn bằng `EXISTS` trên `tab_user_usage_label` của tuần gần nhất.
3. Service hồ sơ + nhóm; tách tệp < 200 dòng.
4. Controller gác kép; xuất xlsx.
5. Cập nhật 3 test cũ + viết test mới.

## Todo
- [ ] ReportKey 14 + gen_status_ts
- [ ] list_service + export
- [ ] profile_service + cohort_service
- [ ] controller gác kép, đăng ký main.py
- [ ] sửa 3 test báo cáo cũ
- [ ] test API + đếm truy vấn

## Kiểm (`test_ho_so_lam_viec_api_cr641.py`, đi qua `TestClient` — gác ở `dependencies=[...]` không chạy khi gọi hàm trực tiếp; mỗi client 1 token giả duy nhất, xem chú thích fixture `client_as` của test gác đường)
- Không `setting.read` → 403 cả 4 đường; có `setting.read` nhưng chưa gán khóa 14 → 403; vai trò admin sau `ensure_report_access_defaults` → 200.
- Nhân viên thường gọi `/{chính_mình}` → 403 (không có đường "của tôi").
- Lọc phòng ban / nhãn / q đúng; trang 2 đúng; `weeks=27` → 422; user 999999 → 404.
- Hồ sơ không chứa trường văn bản tự do ngoài tên/mã/phòng/vai trò.
- **Đếm truy vấn**: danh sách 2 vs 15 người bằng nhau (≤ 5); hồ sơ `weeks=4` vs `weeks=12` bằng nhau (≤ 7).
Chạy: `docker compose exec -T api python -m pytest test/backend/test_ho_so_lam_viec_api_cr641.py test/backend/test_phan_quyen_bao_cao_gac_duong.py test/backend/test_phan_quyen_bao_cao_mac_dinh_admin.py test/backend/test_phan_quyen_bao_cao_cau_hinh_api.py -q`

## Rủi ro
| Rủi ro | K × T | Giảm thiểu |
|---|---|---|
| Đỏ FE `report-catalog.test.ts` giữa 05 và 07 | Chắc chắn × Thấp | cùng PR; không deploy giữa chừng |
| Admin gán khóa 14 cho người khác → lộ hồ sơ | Thấp × Cao | cần thêm `setting.read`; Q1 hỏi có khóa cứng vai trò quản trị không |
| Xuất xlsx = dữ liệu cá nhân rời hệ thống | Trung bình × Trung bình | ghi `tab_export_log`; request_log vẫn ghi GET; chỉ admin |

## Bảo mật
Mỗi lần admin mở hồ sơ người khác để lại dòng `tab_request_log` (GET không bị loại) — đủ trả lời "ai đã xem hồ sơ ai".
