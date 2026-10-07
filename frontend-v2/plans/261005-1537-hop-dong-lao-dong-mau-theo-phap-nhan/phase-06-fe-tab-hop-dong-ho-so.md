# Phase 06 — FE tab «Hợp đồng» trong hồ sơ nhân sự

## Context Links
- `src/modules/hr/pages/employee-detail-page.tsx` (424 dòng, `useUrlParamState('tab')`, `ScrollableTabsList`)
- Khuôn: `components/employee-tab-work-history.tsx`, `employee-work-history-form-dialog*.tsx`, `employee-work-history-files-dialog.tsx`, `hooks/use-employee-work-history*.ts`
- `.claude/rules/hr-employee-profile.md` bẫy #4: hộp có `<form>` trong trang hồ sơ phải `e.stopPropagation()` ở `onSubmit`
- Dùng lại: `@/shared/ui/number-input`, `@/shared/ui/date-picker`, `@/shared/ui/file-dropzone`, `@/shared/utils/format-money`, `labelOf` + `LABOR_CONTRACT_TYPE/STATUS`

## Overview
Priority P2. Status done (05/10/2026). Tab `labor-contracts` «Hợp đồng» (icon `FileSignature`), chỉ dựng khi `can('labor_contract','read')`.

## Requirements
- Bảng (DataTable, không phân trang — vài dòng/người): Số HĐ · Loại · Hiệu lực (bắt đầu – kết thúc) · Chức danh · Lương cơ bản · Trạng thái (badge theo `effective_status`, EXPIRED tô cảnh báo) · Tệp (đã sinh / bản ký) · Hành động.
- Nút «Lập hợp đồng» khi `can_create` (backend trả).
- Hộp lập/sửa (DRAFT): Loại HĐ → nạp mẫu `GET /employees/{eid}/labor-contract-templates?contract_type=` (rỗng → câu «Pháp nhân {X} chưa có mẫu cho loại này» + link sang màn Mẫu nếu có quyền); Số HĐ (gợi ý để trống = mã hệ thống); Ngày ký/bắt đầu/kết thúc (ẩn kết thúc khi INDEFINITE); Chức danh, Địa điểm (điền sẵn từ hồ sơ); Lương cơ bản, Lương đóng BH, Phụ cấp, Ghi chú phụ cấp; Ghi chú. Pháp nhân hiển thị CHỈ ĐỌC (snapshot).
- Hành động dòng (theo cờ backend): Sinh/Sinh lại tệp (chọn mẫu) · Tải .docx (`can('labor_contract','print')`) · Tải lên/Xem bản đã ký · Chuyển trạng thái (Ký / Hủy / Chấm dứt — hộp hỏi ngày + lý do) · Xóa.
- Lỗi backend hiện nguyên câu tiếng Việt.

## Related Code Files
- Create: `src/modules/hr/schemas/labor-contract-schema.ts` (+ `.test.ts`), `hooks/use-employee-labor-contracts.ts` (list + mutations, invalidate `hr.employeeLaborContracts(id)`), `config/employee-labor-contract-columns.tsx`, `components/employee-tab-labor-contracts.tsx`, `components/labor-contract-form-dialog.tsx`, `components/labor-contract-form-dialog-fields.tsx`, `components/labor-contract-row-actions.tsx`, `components/labor-contract-transition-dialog.tsx`, `components/labor-contract-generate-dialog.tsx`, `components/labor-contract-status-badge.tsx`, test cạnh tệp
- Modify: `src/modules/hr/pages/employee-detail-page.tsx` (thêm 1 `TabsTrigger` + 1 `TabsContent`, gác `can`) — chỉ phase này đụng
- Read-only: types/api/query-keys từ phase 05

## Implementation Steps
1. Zod schema mirror luật backend (end bắt buộc theo loại, end ≥ start, tiền ≥ 0) + chuyển payload (ngày rỗng → `null`). Backend vẫn là chuẩn.
2. Hook list/mutations.
3. Cột + badge + tab.
4. Hộp form (`stopPropagation`), hộp sinh tệp, hộp chuyển trạng thái, tải lên bản ký.
5. Gắn tab vào trang chi tiết; tab không quyền → không dựng (tránh 403 toast khi mount).
6. Vitest: schema (INDEFINITE + end_date → lỗi; FIXED_TERM thiếu end → lỗi; end < start; tiền âm; chuỗi rỗng); hộp form KHÔNG submit form hồ sơ cha; tab ẩn khi thiếu quyền; hành động theo cờ (DRAFT có Sinh, SIGNED không Sửa); danh sách mẫu rỗng hiện câu hướng dẫn; EXPIRED hiện badge «Hết hạn».

## Todo
- [x] schema + test · [x] hook · [x] cột/badge/tab · [x] 3 hộp thoại (form, sinh tệp, chuyển trạng thái; tải bản ký là nút chọn tệp) · [x] gắn vào trang · [x] vitest (chưa bấm tay trên trình duyệt)

## Success Criteria
typecheck/lint 0 lỗi; `npx vitest run src/modules/hr` xanh; thao tác tay đủ vòng: lập → sinh → tải → tải bản ký → ký → chấm dứt.

## Risk Assessment
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| Submit lồng làm lưu đè hồ sơ | Trung×Cao | `stopPropagation` + test |
| `employee-detail-page.tsx` phình | Cao×Thấp | chỉ thêm ~10 dòng, logic ở component tab |
| Khổ 390px tràn | Trung×Thấp | `ScrollableTabsList` sẵn; kiểm bằng emulate (memory) |

## Security
Ẩn tab/nút chỉ là tiện; lương không render nếu không có `labor_contract.read` (component không mount).

## Next
Phase 07.
