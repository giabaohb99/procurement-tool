# Phase 04 — FE tab Kiêm nhiệm trên hồ sơ nhân sự

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 12/11/2026 | giao-dien-v2 | Nháp | duoc-CR-755 |

## Context links
- [plan.md](plan.md); API ở [phase-01](phase-01-be-du-lieu-migration-api.md) mục Architecture; tham số
  `end_old_company_concurrent` ở [phase-03](phase-03-be-qua-trinh-doi-phap-nhan-nhap-excel.md).
- Hiện có: `frontend-v2/src/modules/hr/pages/employee-detail-page.tsx:343-411` (tab, `?tab=`, thẻ kiêm nhiệm trong tab Chung),
  `components/employee-department-card.tsx` (+ test), `components/employee-keep-old-department-dialog.tsx` (+ test),
  `hooks/use-employees.ts:75-91`, `api/employee-api.ts:101-110`, `utils/employee-work-history-apply.ts:120-145`,
  `components/employee-tab-work-history.tsx`, `components/employee-tab-work-decisions.tsx` (đọc `useEmployeeDepartments`).
- Khuôn bảng + hộp thoại có tệp: tab Quá trình công tác (`employee-work-history-form-dialog*.tsx`,
  `employee-work-history-files-dialog*.tsx`). Luật: `frontend-v2/.claude/rules/*.md`, `.claude/rules/frontend-v2-ui-conventions.md`,
  `frontend-v2/docs/ui/table.md`.

## Overview
P2. Thêm tab **Kiêm nhiệm** (giữa *Quyết định bổ nhiệm* và *Liên hệ & Ngân hàng*), bỏ thẻ kiêm nhiệm khỏi tab Chung, hộp
thêm/sửa dòng có tệp QĐ, nhãn trạng thái, hộp hỏi khi đổi pháp nhân, câu xác nhận Áp QTCT mới.

## Key insights
- Bẫy 4 của QTCT: hộp thoại có `<form>` trong trang hồ sơ phải `e.stopPropagation()` trước `handleSubmit`.
- Nhãn trạng thái đọc từ tệp sinh `gen_status_ts.py` (`ConcurrentStatus`) — không gõ tay danh sách.
- Bảng nạp đủ mọi dòng (≤ 30) → xếp ở trình duyệt được (luật §8); mặc định: Đang hiệu lực → Sắp tới → Đã hết, rồi từ ngày giảm.
- Chỉ người có `employee.write` + không phải chính mình mới thấy nút (cờ `can_edit` do backend trả, không tự suy).

## Requirements
- Tab hiện với mọi ai mở được hồ sơ. Bảng: Công ty · Phòng ban · Chức vụ · Từ ngày · Đến ngày · Trạng thái (huy hiệu) · Tính
  phạm vi (Có/Không) · Số QĐ · Tệp (số đếm, bấm mở hộp tệp khi `can_open_files`) · Thao tác (Sửa / Xóa). Khổ điện thoại: thẻ.
- Hộp thêm/sửa: ô chọn Công ty → ô chọn Phòng ban lọc theo phòng phục vụ công ty đó (phòng `company_id` = công ty, phòng dùng
  chung, phòng có dòng `tab_department_company`) → Chức vụ (`tab_job_position`, `sort_by=name`) → Từ ngày (bắt buộc) → Đến ngày
  → Số QĐ (≤ 50) → Ngày QĐ → Ghi chú (≤ 500) → công tắc **Tính vào phạm vi quyền** kèm một dòng giải thích *Bật: người này
  thấy dữ liệu đúng phòng này ở công ty này theo vai trò đang có* → khu tệp QĐ (dùng lại thành phần tải tệp của QTCT với entity
  `employee_concurrent`).
- Lỗi 403/409/400 hiện đúng câu backend (L1, L2, chồng giai đoạn, trần, trùng phòng chính).
- Đổi pháp nhân trong tab Chung: mở rộng `employee-keep-old-department-dialog` thêm ô **Kết thúc N dòng kiêm nhiệm ở công ty
  cũ** (mặc định tick) khi có dòng hiệu lực / sắp tới ở công ty cũ; gửi `end_old_company_concurrent`.
- Áp QTCT loại Kiêm nhiệm: câu xác nhận *Cập nhật dòng kiêm nhiệm: phòng X — công ty B, từ ... đến ...* (thay cho *Thêm/Gỡ kiêm
  nhiệm phòng ban*); so theo `work_history_id` thay vì danh sách phòng.
- Đổi kiêm nhiệm → nạp lại nhánh `queryKeys.hr.all` (phạm vi đổi).

## Architecture
```
employee-detail-page ─ Tabs: ... | decisions | concurrent (mới) | contact ...
  └ EmployeeTabConcurrent ─ useEmployeeConcurrents(eid) ── GET  /api/employees/{eid}/concurrents
       ├ EmployeeConcurrentTable / rows-mobile
       ├ EmployeeConcurrentFormDialog ─ useSaveEmployeeConcurrent ── POST/PATCH
       └ xóa ─ useDeleteEmployeeConcurrent ── DELETE
```

## Related code files
Tạo (kebab-case, mỗi tệp < 200 dòng): `modules/hr/types/employee-concurrent.ts`, `api/employee-concurrent-api.ts`,
`hooks/use-employee-concurrents.ts`, `components/employee-tab-concurrent.tsx`, `components/employee-concurrent-table.tsx`,
`components/employee-concurrent-rows-mobile.tsx`, `components/employee-concurrent-form-dialog.tsx`,
`components/employee-concurrent-form-fields.tsx`, `schemas/employee-concurrent-schema.ts`, `utils/concurrent-department-options.ts`
+ bài kiểm cạnh mỗi tệp có logic.
Sửa: `pages/employee-detail-page.tsx`, `components/employee-keep-old-department-dialog.tsx` (+ test),
`utils/employee-work-history-apply.ts` (+ test nếu có), `components/employee-tab-work-history.tsx`,
`components/employee-tab-work-decisions.tsx` (+ test), `hooks/use-employees.ts` (gỡ `useSaveEmployeeDepartments`),
`api/employee-api.ts` (gỡ `setDepartments`), `core/query-keys` nếu khai khóa ở đó.
Xóa: `components/employee-department-card.tsx`, `components/employee-department-card.test.tsx`.
KHÔNG đụng (phase 05): `org-chart-*`, `department-members-table.tsx`, `department-detail-page.tsx`,
`app/components/profile/*`, `modules/system/components/user-scope-dialog*`, `core/auth/auth-types.ts`.

## Implementation steps
1. Kiểu + API + hook (bước 1 là thứ phase 05 có thể đọc; xong trước).
2. Bảng + thẻ điện thoại + nhãn trạng thái từ bộ mã sinh.
3. Hộp thêm/sửa + lược đồ zod (giới hạn khớp backend) + `stopPropagation`; ô phòng lọc theo công ty.
4. Gắn tab, nhớ `?tab=concurrent`; gỡ thẻ cũ khỏi tab Chung.
5. Hộp đổi pháp nhân + câu xác nhận Áp QTCT.
6. Gỡ hook/API cũ; grep `extra_department_ids` trong `modules/hr` còn ai đọc.
7. Cổng: `cd frontend-v2 && npx tsc --noEmit` (host), `docker compose exec -T erp npm run lint`,
   `docker compose exec -T erp npx vitest run src/modules/hr`.

## Todo
- [x] Kiểu, API, hook
- [x] Bảng + thẻ điện thoại
- [x] Hộp thêm/sửa + tệp QĐ
- [x] Tab + gỡ thẻ cũ
- [x] Hộp đổi pháp nhân, câu Áp QTCT
- [x] Gỡ mã cũ, chạy ba cổng

## Success criteria
- typecheck 0 lỗi, lint 0 lỗi (không thêm cảnh báo), vitest `src/modules/hr` xanh.
- Vitest phủ: lưu hộp không submit form hồ sơ cha; ô phòng đổi theo công ty; chính mình không thấy nút; `can_open_files = false`
  → không mở tệp; nhãn trạng thái đúng ba mã; hộp đổi pháp nhân gửi đúng cờ.
- Kiểm tay (dev local, khổ 1280 và điện thoại bằng emulate, không resize): thêm dòng khác công ty, đính tệp, sửa ngày thành hôm
  qua → huy hiệu Đã hết.

## Risks
| Rủi ro | Khả năng × Tác động | Giảm thiểu |
|---|---|---|
| Dải tab thêm một mục tràn ngang khổ 390px | Cao × Thấp | `ScrollableTabsList` đã tự cuộn; kiểm emulate |
| Ô phòng lọc sai (phòng dùng chung bị bỏ) | Trung × Trung | Hàm thuần `concurrent-department-options.ts` có bài kiểm |
| Đọc nhầm cờ quyền phía trình duyệt | Thấp × Trung | Dùng `can_edit`/`can_open_files` backend trả |

## Security
- Không tự che/mở theo quyền ở giao diện; backend là chốt. Tệp QĐ chỉ qua `GET /api/attachments/{id}/download`.

## Next steps
Phase 06 chụp màn cho HDSD.
