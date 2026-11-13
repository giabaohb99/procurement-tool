# Phase 01 — BE dữ liệu, API tab, luồng ghi, chốt L2

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 13/11/2026 | backend A | Nháp | duoc-CR-756 (sửa duoc-CR-755) |

## Context links
- [plan.md](plan.md) (luật cốt lõi, hợp đồng tóm tắt); kế hoạch cũ `../261112-kiem-nhiem-khac-cong-ty-duoc-cr-755/plan.md` + phase-01, 03.
- Mã hiện tại: `employee/concurrent_{model,schema,serializer,service,transition_service,access,controller}.py`,
  `employee/department_service.py` (`pair_in_write_scope` 96, `block_out_of_scope_primary_department` 155,
  `block_out_of_scope_pair` 182), `employee/service.py` (`_sync_primary_department` 270, `update_employee_core` 404),
  `employee/schema.py` 290-299, `employee/work_history_apply_service.py` 77, `import_tool/employee_import_revert.py` 149-219,
  `core/hr_concurrent_codes.py`, `core/code_sets.py`, migration `kn755a_bang_kiem_nhiem.py`.
- Rà mã CR-755: `plans/reports/code-reviewer-261112-1645-cr755-kiem-nhiem.md`; sửa theo rà: `...-1658-cr755-sua-theo-review.md`.

## Overview
Ưu tiên P1. Đưa cột `kind` vào bảng, đổi CRUD tab + mọi đường ghi tự động (đổi phòng chính giữ phòng cũ, đổi pháp nhân,
Áp QTCT loại 4, hoàn tác nhập Excel) sang hai loại dòng, viết lại L2 theo loại. Bước 1-3 phải xong + đẩy vào cây trước để
phase 02 (cần `EmployeeConcurrent.kind`) và phase 03 (cần `CONCURRENT_KIND` trong `statuses.ts`) bắt đầu.

## Key insights
- `kn755a` đã đẩy lên `erp-v2` → KHÔNG sửa; viết `kn756a` (`down_revision = "kn755a"`, viết tay, không autogenerate).
- Dev/prod chưa có `kn755a`: dòng chép từ `is_primary = 0` đều mang công ty chính → toàn loại 1. Dòng khác công ty chỉ có ở DB local.
- Lưu `company_id` = công ty chính cho loại 1 để `end_rows_at_company` (lọc `company_id == cũ`), chỉ mục `(department_id, company_id)`,
  `describe_concurrent`, `company/references.py` chạy nguyên. Dòng cũ mang `company_id = 0` → migration chuẩn hóa về công ty chính.
- L2 hiện tại đọc `concurrent_pairs`; khóa này bị phase 02 bỏ. Phase 01 đọc khóa MỚI `concurrent_companies` theo hợp đồng
  (bài kiểm tự dựng `profile` dict, không phụ thuộc `auth.py` của phase 02).
- Bao-CR-709 giữ phòng cũ KHÔNG qua L2 (phòng vốn là phòng chính). Giữ nguyên cho loại 1 cùng công ty; nhánh tạo loại 2 (đổi
  pháp nhân) PHẢI qua L2 loại 2 — mọi đường tạo dòng Công ty một luật.

## Requirements
Chức năng:
1. `ConcurrentKind(IntEnum)`: `DEPARTMENT = 1` "Phòng ban", `COMPANY = 2` "Công ty"; `register(CodeSet("concurrent_kind",
   "Loại kiêm nhiệm", ...))` trong `hr_concurrent_codes.py` (khuôn `CONCURRENT_STATUS_SET`); chạy `gen_status_ts.py` → `CONCURRENT_KIND`.
2. Loại 1: phòng phục vụ CÔNG TY CHÍNH (`check_concurrent_target(db, emp.company_id, dept)`); ≠ phòng chính; chồng giai đoạn theo
   (nhân sự, loại 1, phòng). Loại 2: công ty tồn tại, ≠ công ty chính, `department_id = 0`; chồng theo (nhân sự, loại 2, công ty).
3. Hồ sơ chưa gắn pháp nhân chính (`company_id = 0`): 400 cả hai loại (câu hỏi mở 1, mặc định chặn).
4. Trần 30 dòng / người giữ nguyên (đếm cả hai loại, cả dòng đã hết).
5. `kind` không đổi qua PATCH tab (đổi loại = xóa + thêm). Áp QTCT được đổi loại TẠI CHỖ (cùng một dòng QTCT, đo L2 cả cũ lẫn mới).
6. Đổi pháp nhân A → C (`end_rows_at_company` mở rộng): kết thúc / xóa (chưa bắt đầu) dòng loại 1 có `company_id == A` VÀ dòng loại 2
   có `company_id == C`; nhập Excel: dòng chưa bắt đầu → lỗi dòng như cũ. `keep_old_company_concurrent = True` (hoặc
   `keep_old_department = True` khi pháp nhân cũng đổi) → tạo MỘT dòng loại 2 (A) từ hôm nay, ghi chú
   `Giữ kiêm nhiệm khi đổi pháp nhân`, bỏ qua nếu đã có dòng loại 2 (A) còn hiệu lực / sắp tới; qua L2 loại 2.
7. Đổi phòng chính trong CÙNG công ty + giữ phòng cũ → dòng loại 1 (phòng cũ, công ty chính) như bao-CR-709.
8. Áp QTCT loại 4: `company = wh.company_id or emp.company_id`; cùng công ty chính → loại 1 (cần `wh.department_id`, trùng phòng
   chính → bỏ qua); khác → loại 2 (bỏ phòng của QTCT, QTCT giữ nguyên). Câu thay đổi: `Kiêm nhiệm — thêm công ty "B"`.
9. Hoàn tác lô Excel: `restore_ended` / `revert_problems` đo L2 + chồng giai đoạn theo loại; khóa `_concurrent_ended` không đổi hình.
10. `same_company_department_ids` (GET `/departments` cũ) chỉ lấy loại 1.

Phi chức năng: sửa tại chỗ (id bền, tệp QĐ không mồ côi); `lock_employee_row` trước kiểm chồng / trần ở mọi đường ghi; mọi
lỗi tiếng Việt; docstring đường API tiếng Việt cập nhật theo loại.

## Architecture
Dữ liệu vào → biến đổi → ra: payload tab → `ConcurrentIn` (kiểm hình theo loại) → `concurrent_service.create_concurrent`
(L1 → khóa hàng → trần → kiểm hồ sơ có pháp nhân → L3 theo loại → L2 theo loại → trùng chính → chồng theo loại → ghi) →
`serialize_one` (+ `kind`, `kind_label`).

Hợp đồng API (phase 03 dựa vào đây, đổi phải báo phase 03):
```
ConcurrentIn  (POST /api/employees/{eid}/concurrents, extra=forbid)
  kind: 1|2 (bắt buộc)
  department_id: int = 0   # loại 1: > 0 bắt buộc; loại 2: phải 0/vắng → 422
  company_id: int = 0      # loại 1: phải 0/vắng (máy chủ điền công ty chính) → 422; loại 2: > 0 bắt buộc
  position_id, from_date (bắt buộc), to_date|null, decision_no, decision_date|null, note, counts_scope  (như cũ)
ConcurrentPatch (PATCH .../{cid}): như cũ, KHÔNG có kind; loại 1 chỉ nhận department_id, loại 2 chỉ nhận company_id
  (gửi ô của loại kia → 400 "Dòng loại Phòng ban không chọn công ty" / "Dòng loại Công ty không chọn phòng ban")
ConcurrentOut: như cũ + kind: int, kind_label: str; loại 2: department_id 0, department_name ""
Lỗi mới: 400 "Công ty kiêm nhiệm trùng công ty chính", 400 "Phòng ban ... không phục vụ công ty hiện tại",
  400 "Hồ sơ chưa gắn pháp nhân chính", 409 chồng giai đoạn ("cùng phòng ban" | "cùng công ty"),
  403 L2 loại 2 "Không gán được kiêm nhiệm ở công ty mà bạn không có phạm vi ghi toàn công ty: <tên>"
EmployeeUpdate (PATCH /api/employees/{id}): BỎ keep_concurrent_ids; THÊM keep_old_company_concurrent: bool | None;
  end_old_company_concurrent giữ làm cờ NỘI BỘ (hoàn tác lô gửi False), giao diện thôi gửi.
```
L2 (department_service, đọc `profile["concurrent_companies"]`):
- `_actor_companies(profile)` = {công ty chính} ∪ `concurrent_companies` (bỏ 0).
- `pair_in_write_scope(profile, dept, company)` (loại 1 + đổi phòng chính): theo TỪNG grant `employee.write`: `all` → có;
  `company` → `company ∈ _actor_companies`; bậc hẹp hơn → `company ∈ _actor_companies` VÀ (`dept ∈ dept_ids`, hoặc ô
  "Phòng ban được xem" khi `company` = công ty chính). `company = 0` coi như công ty chính người thao tác (như cũ).
- MỚI `company_in_write_scope(profile, company)` (loại 2): grant `all`, hoặc grant `company` có `company ∈ _actor_companies`.
- `block_out_of_scope_concurrent(db, specs, profile)` thay `block_out_of_scope_pair`; `specs = [(kind, company, dept), ...]`.

## Related code files
Sửa: `backend/app/core/hr_concurrent_codes.py`, `backend/app/core/code_sets.py` (nếu cần đăng ký), `backend/scripts/gen_status_ts.py`
(chỉ chạy) → `frontend-v2/src/shared/constants/statuses.ts` (tệp SINH, phase 01 sở hữu), `employee/concurrent_model.py`,
`concurrent_schema.py`, `concurrent_serializer.py`, `concurrent_service.py`, `concurrent_transition_service.py`,
`concurrent_access.py`, `concurrent_controller.py` (docstring), `department_service.py`, `employee/service.py`, `employee/schema.py`,
`employee/controller.py` (`/departments` cũ, nếu cần), `work_history_apply_service.py`, `import_tool/employee_import_revert.py`
(kiểm; `employee_import.py` chỉ đọc).
Tạo: `backend/migrations/versions/kn756a_kiem_nhiem_loai_phong_cong_ty.py`, `test/backend/test_kiem_nhiem_doc_lap_ghi_cr756.py`.
Sửa bài kiểm: `test_kiem_nhiem_khac_cong_ty_du_lieu_cr755.py`, `test_kiem_nhiem_migration_cr755.py`, `test_kiem_nhiem_luong_ghi_cr755.py`,
`test_kiem_nhiem_sua_theo_review_cr755.py`, `test_kiem_nhiem_phong_ban.py`, `test_doi_phap_nhan_nhan_su.py`.
Không đụng (phase 02): `core/auth.py`, `core/scoping.py`, `core/subject_match.py`, `concurrent_members_*`, `org_chart_controller.py`.

## Implementation steps
1. Mã loại + đăng ký + chạy `gen_status_ts.py` (đẩy ngay `statuses.ts` cho phase 03).
2. Model: `kind: Mapped[int] = mapped_column(SmallInteger, default=1)`; chú thích đầu tệp viết lại theo hai loại.
3. Migration `kn756a`: (a) `add_column kind SMALLINT NOT NULL server_default '1'`; (b) `UPDATE ... JOIN tab_employee e SET kind = 2,
   department_id = 0 WHERE c.company_id <> 0 AND c.company_id <> COALESCE(e.company_id, 0)`; (c) loại 1 có `company_id = 0` →
   `company_id = e.company_id`; (d) chỉ mục `ix_employee_concurrent_company_kind (company_id, kind)` cho trang công ty; (e) in số dòng
   loại 2 bị bỏ phòng + số cặp loại 2 chồng nhau (để nguyên, chỉ local). Chạy lại được (kiểm cột / chỉ mục đã có). downgrade: bỏ chỉ
   mục + cột; dòng loại 2 ở lại với phòng 0. Đẩy bước 1-3 trước rồi báo phase 02, 03.
4. Schema: `ConcurrentIn` + `kind` + validator `mode="after"` kiểm hình theo loại; `ConcurrentPatch` giữ `extra=forbid` (không `kind`);
   `ConcurrentOut` + `kind`, `kind_label`. Bài kiểm ở tầng schema (`pytest.raises(ValidationError)`).
5. Service: `require_primary_company(emp)`; `check_concurrent_target` theo loại; `block_primary_duplicate` theo loại;
   `block_overlap(db, eid, kind, company, dept, ...)` lọc theo loại; `create/update/delete` gọi `block_out_of_scope_concurrent`.
   Update: ô của loại kia → 400; đổi phòng (loại 1) / công ty (loại 2) đo L2 cả cũ lẫn mới.
6. `department_service`: `_actor_companies`, viết lại `pair_in_write_scope`, thêm `company_in_write_scope`,
   `block_out_of_scope_concurrent`, `_pair_label` cho loại 2 chỉ tên công ty; bỏ mọi chỗ đọc `concurrent_pairs`.
7. `concurrent_access.check_file` (ghi tệp): L2 theo loại của dòng.
8. Transition: `end_rows_at_company(db, emp, old_company, new_company, ...)` (thêm tham số công ty mới, lọc hai nhóm ở yêu cầu 6;
   `keep_ids` bỏ); MỚI `keep_company_seat(db, emp, old_company, actor, profile)` (tạo loại 2 A, L2); `create_from_kept_department`
   chỉ khi cùng công ty → loại 1; `upsert_from_work_history` theo yêu cầu 8; `restore_ended` / `revert_problems` theo loại.
   Tệp đang 269 dòng: tách `concurrent_company_change_service.py` (đổi pháp nhân + giữ ghế công ty cũ + hoàn tác) cho dưới 200.
9. `employee/service.update_employee_core`: bóc `keep_old_company_concurrent`; truyền công ty mới; `keep_old_department` + đổi pháp
   nhân → gọi `keep_company_seat` thay `create_from_kept_department`; cần `actor`/`profile` cho L2 → thêm tham số `profile`
   (tùy chọn; `None` = đường nội bộ hoàn tác / nhập Excel, không tạo ghế). Bỏ `keep_concurrent_ids` khỏi `EmployeeUpdate`.
10. Bài kiểm (mục Todo), ruff, `alembic upgrade head && downgrade -1 && upgrade head` trên local.

## Todo
- [x] B1 mã loại + `statuses.ts` · [x] B2 model · [x] B3 `kn756a` (lên, xuống, lên lại) · [x] B4 schema · [x] B5 service
- [x] B6 L2 · [x] B7 tệp QĐ · [x] B8 transition (tách tệp) · [x] B9 `update_employee_core` + `EmployeeUpdate`
- [x] `test_kiem_nhiem_doc_lap_ghi_cr756.py`: migration (khác công ty → loại 2 phòng 0; cùng công ty → loại 1; công ty 0 chuẩn hóa;
  chạy lại không đổi); schema hai loại (8 ca hình sai → 422); L3 loại 1 phòng công ty khác → 400, phòng dùng chung + phòng qua
  `tab_department_company` → được; loại 2 trùng công ty chính → 400; hồ sơ không pháp nhân → 400; chồng giai đoạn theo loại (loại 1 cùng
  phòng 409, loại 2 cùng công ty 409, loại 1 + loại 2 khác nhau không 409); L2 loại 2: bậc `company` A gán B → 403, bậc `company` có
  công ty kiêm nhiệm B → được, `all` → được, bậc `dept` → 403; L2 loại 1 bậc `dept` ngoài phòng → 403; L1 tự sửa → 403 (kể cả admin);
  PATCH đổi `kind` → 422; đổi pháp nhân A→C: loại 1 (A) kết thúc, loại 2 (C) kết thúc, loại 2 (D khác) không đụng, giữ ghế → một dòng
  loại 2 (A), giữ ghế thiếu L2 → 403 + không đổi gì; Áp QTCT cùng công ty → loại 1, khác công ty → loại 2 phòng 0, Áp lại đổi công ty
  → đổi loại tại chỗ cùng id; hoàn tác lô khôi phục `to_date` cả dòng loại 2 (C).
- [x] Sửa 6 tệp bài kiểm cũ theo mô hình mới (cặp (X, B) → loại 2 B; `keep_concurrent_ids` → `keep_old_company_concurrent`).

## Success criteria
- Các tệp ở mục Related code files (bài kiểm) xanh với `--timeout=120`; thêm `test_nhap_excel_nhan_su*`, `test_qua_trinh_cong_tac_*`
  từng tệp xanh. `ruff check app` 0 lỗi. Migration lên / xuống / lên lại trên local OK, `alembic heads` một đầu `kn756a`.
- `grep concurrent_pairs backend/app` chỉ còn ở phase 02 (tới khi phase 02 xong thì 0).

## Risks
| Rủi ro | Khả năng × Tác động | Giảm thiểu |
|---|---|---|
| Phase 02 đổi tên khóa hồ sơ quyền khác hợp đồng | Thấp × Cao | Tên `concurrent_companies` chốt ở plan.md; bài kiểm dựng dict |
| Bỏ `keep_concurrent_ids` làm vỡ giao diện trước khi phase 03 xong | Cao × Thấp | Không deploy giữa chừng; commit một lượt |
| Nhập Excel đổi pháp nhân sang C mà còn dòng loại 2 (C) chưa bắt đầu | Trung × Thấp | Lỗi dòng như luật cũ (`IMPORT_UNSTARTED_ERROR`) |
| Migration chạy trên DB local có dòng loại 2 chồng nhau | Thấp × Thấp | Để nguyên, in số; sửa ở tab (409 khi sửa) |

## Security
L1 không đổi (kể cả quản trị). L2 loại 2 chặt hơn loại 1: chỉ bậc toàn công ty — gán dòng Công ty mở cả công ty B cho người khác.
Tệp QĐ vẫn gác `employee_sensitive.read`. Mọi đường ghi xóa cache quyền (`clear_perm_cache_of`).

## Next
Báo phase 02 + 03 sau bước 3. Xong phase: báo cáo `plans/reports/fullstack-developer-261113-HHMM-cr756-phase01.md`.
