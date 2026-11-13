# Phase 02 — BE phạm vi đọc theo bậc, chủ thể công ty, hiển thị, /me, trợ lý AI

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 13/11/2026 | backend B | Đã làm xong mã + bài kiểm (chưa commit) | duoc-CR-756 (sửa duoc-CR-755 phase 02, 05) |

## Context links
- [plan.md](plan.md); [phase-01](phase-01-be-du-lieu-luong-ghi-l2.md) (cột `kind`, hợp đồng `ConcurrentOut`).
- `core/auth.py:246-298` (dựng `dept_ids`, `concurrent_pairs`); `core/scoping.py`: `_company_cond_for` 401, `_concurrent_pairs_of` 416,
  `_pair_conds` 421, `holds_handling_dept` 462, `_role_scope_cond` 535 (nhánh `dept_proc` 570-688, `own` 691, `dept` 722, `company` 740,
  duyệt dấu Giám đốc 778-783), `scope_condition` 912, `_concurrent_row_as_employee` 940, `concurrent_row_scope_condition` 961,
  `_or_concurrent_exists` 973; `core/subject_match.py:27-56`; `doc_catalog/folder_access_service.company_reach` 51.
- `employee/concurrent_members_service.py`, `concurrent_members_controller.py`, `org_chart_controller.py:92-138`,
  `auth/controller.py:86-120`, `assistant/tools/employee_tool.py:85-175`.
- Bảng đường thấy / không thấy cũ: `doc/tai-lieu-ky-thuat/phan-quyen/thiet-ke-phan-quyen.md` §4c.

## Overview
Ưu tiên P1. Thay cặp tự do `concurrent_pairs` bằng danh sách `concurrent_companies` và cộng vào ĐÚNG bậc; viết lại nhánh Q1 (đọc hồ
sơ người kiêm nhiệm) cho hai loại; chủ thể công ty B ở ACL; danh sách người kiêm nhiệm theo phòng (loại 1) và theo công ty (loại 2).

## Key insights
- Bậc `dept` hiện là `công ty == chính AND phòng IN dept_ids` (+ cặp). Mô hình mới: `công ty IN (chính, *B) AND phòng IN dept_ids` —
  gọn hơn cũ, đúng ý "phòng của họ ở công ty B", một mệnh đề `IN` thay vì N mệnh đề cặp.
- `dept_proc`, `_narrow_to_dept`, `_handler_match`, `holds_handling_dept`, nhánh `dept_proc` rơi về `dept` của entity không phải
  chứng từ thu mua: KHÔNG ràng công ty (bao-CR-434) → `dept_ids` đã phủ "phòng của họ ở mọi công ty"; công ty kiêm nhiệm không thêm
  gì. Bỏ hết `_pair_conds` ở đó — không đổi hành vi với người không kiêm nhiệm.
- `own` của entity không có cột chủ / `self` rơi về `scope = "company"` (dòng 720). Để giữ "own giữ nguyên", nhánh rơi đó chỉ dùng
  công ty CHÍNH (cờ cục bộ `own_fallback`).
- Bậc company không phình ngoài công ty kiêm nhiệm: danh sách lấy từ dòng hiệu lực + bật công tắc của CHÍNH người đó.
- Dòng loại 2 có `department_id = 0` → bí danh "dòng ngồi như hồ sơ" của CR-755 sai cho loại 2; phải ghép phòng của người đó.

## Requirements
1. `get_perm_profile`: cùng MỘT truy vấn `active_concurrent_rows(counts_scope_only=True)`; loại 1 có `company_id ∈ {chính, 0}` → `dept_ids`;
   loại 1 lệch công ty (dữ liệu trôi) → bỏ qua + log WARNING `app.scoping`; loại 2 có `company_id ∉ {0, chính}` → `concurrent_companies`
   (sắp xếp, không trùng). Bỏ khóa `concurrent_pairs`. Bản cache cũ còn khóa cũ trong 60 giây → mã mới không đọc nó (đóng, không mở).
2. `_role_scope_cond`: `_own_companies(profile)`; `_company_in_cond(model, f, ids)` (một id → `==` như cũ để SQL người không kiêm nhiệm
   không đổi; nhiều id → `IN`; kèm `company_alt`). Nhánh `dept`, `company` dùng nó; duyệt dấu Giám đốc (chỉ `read`) `_SRC.company_id IN`;
   Văn thư (bảng `tab_seal_clerk`) KHÔNG đổi. `company_id = 0` + có công ty kiêm nhiệm: bậc `company` dùng danh sách kiêm nhiệm (không
   `_chan`); không có gì → `_chan` như cũ. Phase 01 chặn tạo dòng cho hồ sơ không pháp nhân nên ca này chỉ từ dữ liệu cũ.
3. Q1 — `concurrent_row_visible_condition(R, employee_dept_col, user, profile, action)` trên bí danh dòng `R`:
   - `R.kind == 1`: phạm vi `employee` áp lên chỗ ngồi (`R.department_id`, `R.company_id`);
   - `R.kind == 2`: chỗ ngồi (`Employee.department_id` của người đó, `R.company_id`) OR `EXISTS` dòng loại 1 hiệu lực + bật `D` của cùng
     người với chỗ ngồi (`D.department_id`, `R.company_id`).
   Bí danh chỗ ngồi = lớp nhỏ mang `company_id` / `department_id` / `id` (khuôn `_concurrent_row_as_employee`, dựng lười, cache theo tổ hợp).
   `_or_concurrent_exists` = `cond OR EXISTS(R hiệu lực + bật + visible)`. Vẫn một câu SQL, không thêm truy vấn.
4. `subject_pairs`: bỏ vòng `concurrent_pairs`; thêm `(SUBJECT_COMPANY, B)` cho mỗi B trong `concurrent_companies`.
5. `company_reach`: cộng `concurrent_companies` cho grant bậc `company` / `dept` / `dept_proc` (câu hỏi mở 2, mặc định có).
6. `list_visible_members(..., department_id=None, company_id=None, kind=None)`: lọc theo tham số; quyền thấy dòng = yêu cầu 3 (không xét
   hiệu lực / công tắc của dòng như cũ); bỏ điều kiện "trùng chỗ chính" cho loại 2 (loại 2 không bao giờ trùng). Item + `kind`, `kind_label`.
   `describe_concurrent(kind, ...)`: loại 1 *Phòng X (Chức vụ)*; loại 2 *Công ty B (Chức vụ)*. `effective_roles_of` + `kind`.
7. `GET /api/employee-concurrents`: `department_id` thành tùy chọn, thêm `kind` (1|2), cần ít nhất một trong `department_id` / `company_id`
   (422 kèm câu tiếng Việt). Docstring + `api.md` (phase 04 ghi tài liệu, docstring ở đây).
8. `/api/org-chart` `concurrents`: dòng loại 1 như cũ; dòng loại 2 kèm `kind` (giao diện gom theo công ty); `company_ids` vẫn gồm công ty
   dòng. `/api/auth/me` `concurrents[]` + `kind`, `kind_label`; `kiem_nhiem` = câu mới. Trợ lý `employee_lookup`: mô tả công cụ đổi câu
   (loại Phòng ban / Công ty), `concurrent_roles` lấy câu mới.

## Architecture
```
tab_employee_concurrent (hiệu lực + bật) ──1 truy vấn──> get_perm_profile
   loại 1 ─> dept_ids            loại 2 ─> concurrent_companies
                │                               │
  _role_scope_cond: dept = công ty IN (chính,*B) AND phòng IN dept_ids
                    company = công ty IN (chính,*B)   own/all/dept_proc = như cũ
  subject_pairs: + (COMPANY, B)       company_reach: + B (company/dept/dept_proc)
Q1/members: R loại 1 → chỗ (R.phòng, R.công ty); R loại 2 → chỗ (phòng chính | phòng loại 1, R.công ty)
```

## Related code files
Sửa: `backend/app/core/auth.py`, `backend/app/core/scoping.py`, `backend/app/core/subject_match.py`,
`backend/app/modules/doc_catalog/folder_access_service.py`, `employee/concurrent_members_service.py`,
`employee/concurrent_members_controller.py`, `employee/org_chart_controller.py`, `auth/controller.py`,
`assistant/tools/employee_tool.py`.
Tạo: `test/backend/test_kiem_nhiem_doc_lap_cr756.py`.
Sửa bài kiểm: `test_kiem_nhiem_pham_vi_cap_cr755.py`, `test_kiem_nhiem_hien_thi_cr755.py`, `test_me_payload_vai_tro_kiem_nhiem.py`;
bài sổ công cụ AI nếu câu mô tả `employee_lookup` bị so chuỗi.
Không đụng (phase 01): `concurrent_{model,schema,service,transition}*`, `department_service.py`, `employee/service.py`.

## Implementation steps
1. Chờ phase 01 bước 1-3 (cột `kind`). `merge origin/erp-v2`.
2. `auth.py` (yêu cầu 1). 3. `scoping.py`: `_own_companies`, `_company_in_cond`, nhánh `dept` / `company` / `own_fallback` / duyệt dấu;
   gỡ `_concurrent_pairs_of`, `_pair_conds` và mọi lời gọi (dept_proc, PO handler, fallback, `holds_handling_dept`).
4. Q1: `concurrent_row_visible_condition` + `_or_concurrent_exists`; giữ tên `concurrent_row_scope_condition` làm vỏ gọi hàm mới (ít
   nơi gọi phải sửa) hoặc đổi tên và sửa hết nơi gọi — chọn một, grep sạch. 5. `subject_match.py`. 6. `company_reach`.
7. Members service / controller / org chart / `/me` / AI. 8. Bài kiểm; chạy `test_pham_vi_*` từng tệp (`test_pham_vi_cap_bac_ma_tran.py` riêng).

## Todo
- [x] B2 auth · [x] B3 scoping bậc · [x] B4 Q1 · [x] B5 chủ thể · [x] B6 company_reach · [x] B7 hiển thị + /me + AI
- [x] `test_kiem_nhiem_doc_lap_cr756.py`: P (chính A, phòng X dùng chung) kiêm nhiệm công ty B —
  bậc `company`: thấy MỌI hồ sơ / phiếu của B (YCMH, văn bản, đơn nghỉ), không thấy C; bậc `dept`: thấy (X, B), không thấy (Y, B);
  phòng loại 1 Z (của A) → thấy (Z, A) và (Z, B); `own` không đổi (kể cả entity `own` rơi về `company`); `all` không đổi; `dept_proc`
  YCMH không đổi so với người không kiêm nhiệm; tắt công tắc / `to_date` hôm qua / `from_date` mai → mất B; loại trừ công ty B ở
  ô phạm vi → mất B; cache: sửa dòng + `clear_perm_cache_of` → thấy ngay.
- [x] Q1: V bậc `company` ở B đọc hồ sơ P (chi tiết, tệp QTCT có `employee_sensitive`); V bậc `dept` (X, B) đọc được, V (Y, B) 404;
  V (Z, B) đọc được khi P có loại 1 Z; danh sách `/api/employees` của V KHÔNG có P (Q5 giữ); V không ghi được hồ sơ P qua Q1.
- [x] Chủ thể: văn bản / thư mục / báo cáo (`tab_report_access`) / skill AI chia cho công ty B → P thấy; tắt công tắc → không.
- [x] Đếm truy vấn `get_perm_profile` bằng đúng số cũ (0, 1, 5 dòng kiêm nhiệm); `/api/employee-concurrents?company_id=B&kind=2` số
  truy vấn cố định; `?kind=1&department_id=X` không ra dòng loại 2; thiếu cả hai id → 422.
- [x] `grep -rn "concurrent_pairs" backend/app` = 0.

## Success criteria
`test_kiem_nhiem_doc_lap_cr756.py` + 3 tệp sửa + `test_pham_vi_*` từng tệp + `test_tai_lieu_van_ban_*`/`test_*report_access*` liên quan
(chạy theo grep `subject_match`) xanh; ruff 0 lỗi; số truy vấn hồ sơ quyền không tăng (bài đếm).

## Risks
| Rủi ro | Khả năng × Tác động | Giảm thiểu |
|---|---|---|
| Đổi `==` thành `IN` làm đỏ bài so SQL / làm chậm truy vấn | Trung × Thấp | Một id giữ `==`; nhiều id mới `IN` |
| Bậc `company` ở B mở cả GHI / DUYỆT toàn B (mọi phân hệ) | Chắc × Cao | Đúng chốt 2 + Q6 cũ; công tắc từng dòng là chốt; L2 loại 2 chỉ bậc toàn công ty; bài kiểm ghi rõ |
| Bỏ `_pair_conds` ở `dept_proc` làm mất phiếu của người đã có cặp CR-755 | Thấp × Thấp | Chưa lên dev/prod; dữ liệu cặp đã thành loại 2 |
| Q1 lồng `EXISTS` hai tầng chậm ở danh sách lớn | Thấp × Trung | Chỉ bật ở đường đọc MỘT hồ sơ + tập id nhỏ (`can_open`); chỉ mục `employee_id` sẵn |
| Chủ thể công ty B mở ACL rộng hơn ý người chia | Trung × Trung | Đúng chốt Q3; ghi rõ ở §4c + HDSD |

## Security
Không entity / khóa quyền mới. Không mở `include_concurrent` ở danh sách, xuất tệp, báo cáo, truy vấn gốc sơ đồ, đường ghi. Members API
giữ danh sách trắng trường (không điện thoại, email, ngày sinh). Log WARNING cho dòng loại 1 lệch công ty.

## Next
Báo phase 03 khi `GET /api/employee-concurrents` mới chạy. Báo cáo `plans/reports/fullstack-developer-261113-HHMM-cr756-phase02.md`.
