# Phase 03 — FE tab Kiêm nhiệm hai loại, đổi pháp nhân, trang công ty, sơ đồ, phạm vi

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 13/11/2026 | giao-dien-v2 | Xong (chờ rà mã) | duoc-CR-756 (sửa duoc-CR-755 phase 04, 05) |

## Context links
- [plan.md](plan.md) hợp đồng tóm tắt; hợp đồng đủ: [phase-01](phase-01-be-du-lieu-luong-ghi-l2.md) mục Architecture; danh sách người
  kiêm nhiệm: [phase-02](phase-02-be-pham-vi-doc-hien-thi.md) yêu cầu 6-8.
- Luật: `frontend-v2/.claude/rules/*.md`, `.claude/rules/frontend-v2-ui-conventions.md`, `frontend-v2/docs/ui/table.md`.
- Báo cáo CR-755 giao diện: `plans/reports/giao-dien-v2-261112-1550-cr755-phase04.md`.

## Overview
Ưu tiên P1. Hộp thêm / sửa chọn **Loại** trước; bảng có cột **Loại**; hộp đổi pháp nhân còn một câu hỏi; trang chi tiết công ty
(`pages/company-detail-page.tsx`, ĐÃ CÓ — trang biểu mẫu, chưa có tab) thêm khối **Kiêm nhiệm tại công ty này**; sơ đồ tổ chức gom dòng
loại Công ty theo công ty; `/me`, popup phạm vi hiện đúng hai loại.

## Key insights
- `CONCURRENT_KIND` lấy từ `shared/constants/statuses.ts` (SINH bởi `gen_status_ts.py`, phase 01 bước 1). Không gõ tay danh sách.
- Ô phòng loại Phòng ban = `buildConcurrentDepartmentOptions(departments, servedPairs, primaryCompanyId, primary, keepId)` — hàm
  sẵn có, chỉ cố định `companyId` = công ty chính; không còn ô chọn công ty cho loại này (hiện chỉ đọc tên công ty hiện tại).
- Ô công ty loại Công ty: danh mục công ty trừ công ty chính (giữ công ty của dòng đang sửa để không hiện trống).
- Hồ sơ chưa gắn pháp nhân: nút Thêm tắt + dòng giải thích (backend 400 cả hai loại).
- Trang công ty dài 474 dòng: khối mới là tệp riêng, trang chỉ thêm một dòng gọi (khuôn trang phòng ban dòng 362-364).
- Cột che theo quyền không có ở đây; bảng nạp đủ dòng → xếp ở trình duyệt (luật §8); Loại xếp theo số mã.

## Requirements
1. Kiểu: `EmployeeConcurrent` + `kind`, `kind_label`; payload `kind` + đúng ô theo loại (loại 1 không gửi `company_id`, loại 2 không gửi
   `department_id`; PATCH không gửi `kind`); `ConcurrentMember` + `kind`, `kind_label`; `auth-types.ts` `concurrents[]` + `kind`.
2. Hộp thêm / sửa: ô **Loại** (Phòng ban | Công ty) đầu hộp, mặc định Phòng ban; khi sửa thì chỉ đọc. Lược đồ zod
   (`employee-concurrent-schema.ts`) bắt buộc phòng (loại 1) / công ty (loại 2). Câu lỗi 400/403/409 của máy chủ hiện nguyên văn.
3. Bảng + thẻ điện thoại: cột **Loại** · **Nơi kiêm nhiệm** (tên phòng với loại 1, tên công ty với loại 2) thay hai cột công ty / phòng.
4. Hộp đổi pháp nhân (`employee-company-change-concurrent-dialog.tsx`): liệt kê dòng sẽ kết thúc (loại 1 ở công ty cũ + loại 2 trùng
   công ty mới), MỘT ô tick **Vẫn kiêm nhiệm ở công ty cũ (thêm dòng loại Công ty từ hôm nay)**; gửi `keep_old_company_concurrent`.
   `use-employee-profile-save-flow.ts`: đổi cả pháp nhân lẫn phòng → bỏ hộp **giữ phòng cũ** (gộp vào ô tick trên); chỉ đổi phòng → hộp
   giữ phòng cũ như cũ. Bỏ `keep_concurrent_ids` / `end_old_company_concurrent` khỏi `employee-schema.ts` + `company-change-concurrent-choice.ts`.
5. Trang phòng ban: `DepartmentConcurrentMembersTable` gọi `kind=1`. Trang công ty: MỚI `company-concurrent-members-table.tsx` gọi
   `?company_id=&kind=2`, cột Mã · Họ tên · Chức vụ kiêm nhiệm · Thời hạn · Trạng thái · Nơi làm chính; gác `can('employee','read')`;
   `can_open` = có liên kết hồ sơ; dùng `DataTable`.
6. Sơ đồ tổ chức (`utils/org-chart-forest.ts`, `org-chart-concurrent-section.tsx`): nhóm loại 2 theo công ty (*Kiêm nhiệm tại công ty B*).
7. `/me` (`profile-info-card.tsx`) hiện câu backend trả; popup phạm vi (`scope-summary.ts` `listScopeConcurrentPairs` → đổi tên
   `listScopeConcurrentPlaces`, `account-scope-summary-panel.tsx`, `user-scope-dialog.tsx`): *Phòng X* / *Công ty B (cả công ty theo bậc
   vai trò)*, chỉ dòng Đang hiệu lực + bật công tắc.
8. Hộp QTCT loại Kiêm nhiệm (`employee-work-history-form-dialog.tsx` / `utils/employee-work-history-apply.ts`): chú thích một dòng
   *Công ty khác công ty chính: Áp ghi kiêm nhiệm loại Công ty, bỏ phòng ban*.

## Architecture
`useEmployeeConcurrents(eid)` → bảng; hộp → `employee-concurrent-api.ts` (POST/PATCH theo hợp đồng) → làm mới query key cũ.
`useConcurrentMembers({departmentId?, companyId?, kind})` → `concurrent-members-api.ts` (`GET /api/employee-concurrents`) — query key
thêm `companyId`, `kind` (`shared/constants/query-keys.ts`).

## Related code files
Sửa (`frontend-v2/src/`): `modules/hr/types/{employee-concurrent,concurrent-member,org-chart}.ts`, `modules/hr/api/{employee-concurrent-api,
concurrent-members-api}.ts`, `modules/hr/hooks/{use-employee-concurrents,use-concurrent-members,use-employee-profile-save-flow}.ts`,
`modules/hr/schemas/{employee-concurrent-schema,employee-schema}.ts`, `modules/hr/components/employee-concurrent-{form-dialog,form-fields,
table,mobile-card}.tsx`, `employee-tab-concurrent.tsx`, `employee-company-change-concurrent-dialog.tsx`, `department-concurrent-members-table.tsx`,
`org-chart-concurrent-section.tsx`, `employee-work-history-form-dialog.tsx`, `modules/hr/config/employee-concurrent-columns.tsx`,
`modules/hr/utils/{concurrent-department-options,company-change-concurrent-choice,concurrent-member-display,employee-concurrent-display,
org-chart-forest,employee-work-history-apply}.ts`, `modules/hr/pages/company-detail-page.tsx`, `core/auth/auth-types.ts`,
`app/components/profile/profile-info-card.tsx`, `modules/system/utils/scope-summary.ts`, `modules/system/components/{account-scope-summary-panel,
user-scope-dialog}.tsx`, `shared/constants/query-keys.ts`; bài kiểm `.test.ts(x)` cạnh mỗi tệp trên.
Tạo: `modules/hr/components/company-concurrent-members-table.tsx` (+ `.test.tsx`).
KHÔNG sửa: `shared/constants/statuses.ts` (phase 01 sinh), mọi tệp `backend/`.

## Implementation steps
1. Chờ `statuses.ts` có `CONCURRENT_KIND`; `merge origin/erp-v2`. 2. Kiểu + API + query key. 3. Lược đồ + hộp + ô Loại.
4. Bảng / thẻ / cột. 5. Hộp đổi pháp nhân + luồng lưu hồ sơ. 6. Bảng trang phòng ban (kind) + bảng trang công ty mới.
7. Sơ đồ, `/me`, popup phạm vi, chú thích QTCT. 8. Bài kiểm; `typecheck` + `lint` cả cây; `vitest run src/modules/hr src/modules/system
   src/app/components/profile`. 9. Kiểm tay trên `localhost:8083` khổ 1440 và 390 (emulate, không resize) — ảnh vào `plans/reports/`.

## Todo
- [x] Kiểu + API · [x] hộp hai loại · [x] bảng cột Loại · [x] hộp đổi pháp nhân · [x] trang công ty · [x] sơ đồ · [x] /me + popup
- [x] vitest: hộp loại 1 không gửi `company_id`, loại 2 không gửi `department_id`, sửa không gửi `kind`, đổi loại xóa ô của loại kia;
  ô phòng chỉ phòng của công ty hiện tại (phòng riêng công ty khác không có, phòng dùng chung + phòng qua `tab_department_company` có);
  ô công ty không có công ty chính; hồ sơ không pháp nhân → nút Thêm tắt; hộp đổi pháp nhân gửi đúng `keep_old_company_concurrent`;
  bảng trang công ty gọi `kind=2`; popup phạm vi hai câu; sơ đồ nhóm theo công ty.

## Success criteria
`typecheck` 0 lỗi; `lint` 0 lỗi (không thêm cảnh báo); vitest ba khu trên xanh; ảnh 1440 + 390 của tab, hộp, trang công ty.

## Risks
| Rủi ro | Khả năng × Tác động | Giảm thiểu |
|---|---|---|
| Phase 01/02 đổi hợp đồng giữa chừng | Thấp × Trung | Hợp đồng ở plan.md; đổi phải báo |
| Gộp hộp **giữ phòng cũ** khi đổi pháp nhân làm người dùng tưởng mất lựa chọn | Trung × Thấp | Câu ô tick nói rõ; HDSD phase 04 |
| Trang công ty phình quá 474 dòng | Chắc × Thấp | Khối là tệp riêng, trang thêm 2 dòng |

## Security
Ẩn ô không thay chốt máy chủ — L1/L2/L3 ở backend. Không hiện điện thoại / email người kiêm nhiệm (API đã không trả).

## Next
Báo phase 04 danh sách nhãn / câu chữ cuối cùng. Báo cáo `plans/reports/giao-dien-v2-261113-HHMM-cr756-phase03.md`.
