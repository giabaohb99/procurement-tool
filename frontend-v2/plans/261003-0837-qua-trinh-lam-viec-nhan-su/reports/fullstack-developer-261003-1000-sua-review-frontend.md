# Sửa review FRONTEND v2 — Quá trình công tác nhân sự

## Thực thi
- Plan: frontend-v2/plans/261003-0837-qua-trinh-lam-viec-nhan-su/plan.md
- Phạm vi: finding H1, M4, M5, M6, Low FE, Low (tách tệp) — chỉ frontend-v2/, không đụng backend/, không đụng frontend/ (v1)
- Trạng thái: **completed**
- Cách làm: viết test ĐỎ trước (chạy xác nhận fail) rồi sửa code tới khi xanh, cho từng finding.

## H1 — nút ▶ «Áp vào hồ sơ» phải hỏi trước khi gọi API
- `employee-tab-work-history.tsx` giờ gọi `useEmployeeWorkHistoryRowApply` (hook mới) thay vì gọi thẳng `applyMutation.mutate`.
- Dòng Thôi việc (nhận biết qua `planApplyPrompt` trả `kind:'resign'`, **không gõ số cứng** — dùng lại đúng một bộ hằng số `RESIGN_TYPE`/`POSITION_TRACK`/`MAIN_TRACK` xuất từ `utils/employee-work-history-apply.ts`) → mở lại `EmployeeWorkHistoryResignConfirmDialog` với `cancelLabel="Hủy"` / `confirmLabel="Chuyển sang nghỉ việc"` (đỏ, destructive sẵn có) — dialog này giờ generic hoá thêm `onCancel` riêng để "Hủy" ở ngữ cảnh này KHÔNG gọi gì cả (khác ngữ cảnh Lưu dòng, nơi "Chỉ lưu dòng" vẫn phải lưu).
- Loại khác → `confirm()` chung, liệt kê thay đổi CŨ → MỚI (tái dùng `planApplyPrompt`, dữ liệu lấy thẳng từ `row.company_name/department_name/position_label` — không cần tra danh mục).
- Test: `employee-tab-work-history.test.tsx` — 5 bài mới (dòng Thôi việc chưa gọi API lúc mở hộp, Hủy không gọi, Chuyển sang nghỉ việc mới gọi đúng id; loại khác xác nhận `confirm()` nhận đúng `cancelLabel/confirmLabel`, Hủy không gọi).

## M4 — ẩn vùng tệp khi `can_open_files=false`
- Thêm prop `canOpenFiles` xuyên suốt `EmployeeTabWorkHistory → EmployeeWorkHistoryFormDialog → …Fields → …FileField`.
- `false` → KHÔNG vùng thả tệp (tạo mới), KHÔNG nút «Quản lý tệp» (sửa); sửa thêm: khi không có gì để báo (tạo mới, hoặc sửa dòng 0 tệp) thì bỏ hẳn luôn nhãn «Tệp QĐ» (tránh nhãn trống hoác không nội dung — lỗi nhỏ tự phát hiện lúc viết test).
- Có tệp sẵn (sửa, `file_count>0`) vẫn báo chữ tĩnh "Có N tệp đính kèm…", không nút, không gọi `/api/attachments`.
- Test: 4 bài trong `employee-work-history-form-dialog.test.tsx` (tạo mới + sửa, cả hai chiều `canOpenFiles`, cộng case sửa dòng 0 tệp).

## M5 — nạp lại danh sách sau khi tải tệp
- `useEmployeeWorkHistoryFormSubmit.save()`: sau khi `uploadWorkHistoryFiles` thành công → `queryClient.invalidateQueries({queryKey: queryKeys.hr.employeeWorkHistory(employeeId)})` (khóa có sẵn, chỉ thiếu lệnh gọi).
- Test: dựng `QueryClientProvider` thật, giả lập chọn 1 tệp qua input ẩn của `FileDropzone`, xác nhận `uploadWorkHistoryFiles(123, [file])` rồi `invalidateQueries` đúng khóa.

## M6 — câu hỏi áp hồ sơ khi lưu (loại không phải thôi việc)
- `confirm()` giờ nhận `confirmLabel="Lưu và cập nhật hồ sơ"` / `cancelLabel="Chỉ lưu dòng"` (API đã có sẵn ở `shared/ui/confirm-dialog.tsx`, chỉ thiếu truyền).
- Nêu giá trị CŨ → MỚI: `planApplyPrompt` nhận thêm `company_label/department_label/position_label` (nhãn MỚI, bên gọi tra từ danh mục đã nạp) và tự lấy nhãn CŨ từ `employee.company_name/department_name/position` (đã có sẵn, không cần tra thêm) → câu dạng `"Phòng ban: Phòng cũ → Phòng mới"`. Kiêm nhiệm cũng nêu tên phòng khi có, giữ nguyên câu cũ "phòng ban này" khi không có nhãn (không hồi quy câu cũ).
- Nhập bù lịch sử cũ không bị hỏi: `planApplyPrompt` nhận thêm `existingRows` + `editingId`, có dòng CHÍNH (`MAIN_TRACK`) khác hiệu lực MUỘN HƠN dòng đang lưu → bỏ câu hỏi (áp dụng cho nhóm chính + kiêm nhiệm; **cố ý KHÔNG áp dụng cho Thôi việc** — hệ quả khóa tài khoản nặng hơn, giữ nguyên hành vi luôn hỏi kể cả nhập bù, có test chốt riêng).
- Esc/đóng hộp: chọn phương án "nói rõ trong câu" (giữ `confirm()` chung, không đổi hành vi Esc=Hủy) — thêm câu `"Đóng hộp này (hoặc nhấn Esc) sẽ CHỈ lưu dòng, không cập nhật hồ sơ."` vào message. Xem mục "Quyết định/giả định" cuối báo cáo.
- Ngày «hôm nay»: dùng `toDateInputValue(new Date())` — đúng quy ước sẵn có của repo (test ép `TZ=Asia/Ho_Chi_Minh` toàn cục ở `vitest.config.ts`); không có helper "ngày VN" riêng ở frontend để gọi thêm (đã grep).
- Test: `employee-work-history-apply.test.ts` thêm ~15 bài (nhãn cũ→mới, nhập bù không hỏi cho nhóm chính/kiêm nhiệm, nhập bù VẪN hỏi cho Thôi việc, `editingId` tự loại dòng đang sửa khỏi `existingRows`, `workHistoryRowToApplyValues`); `employee-work-history-form-dialog.test.tsx` thêm 2 bài (nhãn + câu Esc; nhập bù không mở `confirm()`).

## Low FE
- Câu "của chính bạn do người khác cập nhật" giờ chỉ hiện khi `!isLoading && !isError && !canEdit && isOwnProfile` (`isOwnProfile = user?.employee_id === employee.id`, đọc từ `useAuth()`). Trước đó hiện cho MỌI người thiếu quyền sửa, kể cả đang xem hồ sơ NGƯỜI KHÁC.
- Áp hồ sơ CHÍNH MÌNH (chỉ xảy ra khi quản trị hệ thống tự sửa, A9/Q3) → `invalidateAfterChange` (dùng chung cho cả LƯU và nút ▶ ÁP) giờ gọi thêm `refreshOwnProfileIfSelf`: so `useAuthStore.getState().user?.employee_id` với hồ sơ vừa đổi, khớp thì `invalidateQueries(myWorkHistory())` + gọi lại `authService.me()` rồi `setUser` (best-effort, lỗi thì bỏ qua, không chặn luồng áp hồ sơ).
- "sau áp hồ sơ invalidate hồ sơ nhân sự + danh sách" — đã đúng từ trước (không phải lỗi), giữ nguyên.
- Test: `employee-tab-work-history.test.tsx` 3 bài (hiện đúng/không hiện khi là người khác/không hiện khi đang tải); `use-employee-work-history.test.tsx` (tệp MỚI) 4 bài cho cả `useSaveEmployeeWorkHistory` và `useApplyEmployeeWorkHistory`.

## Low — tách tệp xuống dưới 200 dòng
Không chỉ 2 tệp phase nêu — `employee-tab-work-history.tsx` cũng vượt 200 dòng sau khi thêm H1, tách luôn cho nhất quán với CLAUDE.md §"File Size Management":
- `employee-work-history-form-dialog.tsx` 257→**197** dòng: chuyển state/mutation/`onSubmit`/câu hỏi áp hồ sơ sang hook mới `hooks/use-employee-work-history-form-submit.ts` (151 dòng); `buildDefaultValues` sang `utils/employee-work-history-form-defaults.ts` (42 dòng, hàm thuần).
- `employee-work-history-form-dialog-fields.tsx` 272→**164** dòng: tách ô Pháp nhân/Phòng ban/Chức vụ + Số QĐ/Ngày ký QĐ/Ghi chú sang `-form-dialog-detail-fields.tsx` (127 dòng) và ô Tệp QĐ sang `-form-dialog-file-field.tsx` (72 dòng).
- `employee-tab-work-history.tsx` 164→236 (sau H1)→**167** dòng: tách câu hỏi áp dòng (H1) + `useBusyIds` sang `hooks/use-employee-work-history-row-apply.ts` (88 dòng).
- Tất cả tệp ≤200 dòng sau khi tách; không tệp nào của phase khác bị đụng.

## Dọn trùng/DRY nhân tiện
- `RESIGN_TYPE`/`POSITION_TRACK`/`CONCURRENT_TYPE`/`MAIN_TRACK` giờ khai MỘT chỗ (`utils/employee-work-history-apply.ts`, export), ba nơi trước đó khai riêng (`form-dialog.tsx`, `-fields.tsx`, `tab-work-history.tsx` cũ) nay import lại — tránh lệch số khi backend đổi mã (dù không khả năng, nhưng đỡ phải nhớ sửa ba chỗ).

## Tests Status
- Type check: **pass** (`npm run typecheck`, 0 lỗi).
- Lint: **pass** (`npm run lint`, 0 lỗi, **29 cảnh báo — đúng baseline cũ, không thêm cảnh báo mới**). Có sửa 1 lỗi mới tự gây ra (`@typescript-eslint/consistent-type-imports` ở cách mock `importOriginal` trong test) — đổi sang khuôn `import type * as Module from '...'` đúng quy ước đã dùng ở các test khác trong repo (`folder-documents-table.test.tsx`).
- Unit tests phạm vi được giao: `npx vitest run src/modules/hr src/app/components/profile src/app/pages` → **61 tệp / 690 bài, tất cả xanh**. Riêng các tệp đụng trong lượt sửa này: 112 bài (apply.ts 27, form-dialog 14, tab-work-history 13, resign-dialog 7, use-employee-work-history hook 4 — còn lại là các tệp đã có sẵn từ trước, không đổi).
- Không chạy `npm run check` (full suite), không `npm run format`, không commit — đúng chỉ dẫn.

## Files Modified / Created
Sửa (đã có từ phase 04/05):
- `src/modules/hr/components/employee-tab-work-history.tsx` (167 dòng)
- `src/modules/hr/components/employee-tab-work-history.test.tsx`
- `src/modules/hr/components/employee-work-history-form-dialog.tsx` (197 dòng)
- `src/modules/hr/components/employee-work-history-form-dialog.test.tsx`
- `src/modules/hr/components/employee-work-history-form-dialog-fields.tsx` (164 dòng)
- `src/modules/hr/components/employee-work-history-resign-confirm-dialog.tsx` (105 dòng)
- `src/modules/hr/components/employee-work-history-resign-confirm-dialog.test.tsx`
- `src/modules/hr/hooks/use-employee-work-history.ts` (120 dòng)
- `src/modules/hr/utils/employee-work-history-apply.ts` (165 dòng)
- `src/modules/hr/utils/employee-work-history-apply.test.ts`

Tạo mới (để tách theo giới hạn 200 dòng + encapsulate finding):
- `src/modules/hr/hooks/use-employee-work-history-form-submit.ts` (151 dòng)
- `src/modules/hr/hooks/use-employee-work-history-row-apply.ts` (88 dòng)
- `src/modules/hr/hooks/use-employee-work-history.test.tsx` (mới hoàn toàn — hook này trước đây chưa có test riêng)
- `src/modules/hr/utils/employee-work-history-form-defaults.ts` (42 dòng)
- `src/modules/hr/components/employee-work-history-form-dialog-detail-fields.tsx` (127 dòng)
- `src/modules/hr/components/employee-work-history-form-dialog-file-field.tsx` (72 dòng)

Xóa:
- `src/modules/hr/components/employee-work-history-form-dialog-identity-fields.tsx` (tạo rồi xóa trong cùng lượt sửa — gộp vào `-detail-fields.tsx` để đủ cắt giảm dòng cho tệp orchestrator).

## Quyết định/giả định (không hỏi lại được trong lượt review)
1. **M6 — Esc/đóng hộp**: chọn phương án "nói rõ trong câu" (giữ `confirm()` chung, Esc vẫn tương đương Hủy = chỉ lưu dòng) thay vì đổi hành vi để Esc không lưu gì. Lý do: đổi hành vi Esc cần tách thành hộp xác nhận riêng (như hộp Thôi việc) — phạm vi lớn hơn cho một câu hỏi ít nguy hiểm hơn (không khóa tài khoản). Nếu đại ca muốn nhất quán 100% với hộp Thôi việc (Esc không lưu gì), cần làm thêm một hộp riêng cho nhánh này.
2. **Nhập bù lịch sử cũ (M6) không áp dụng cho Thôi việc** — đọc đúng phạm vi câu chữ gốc ("khi lưu, loại không phải thôi việc"); Thôi việc vẫn luôn hỏi kể cả nhập bù quá khứ, giữ đúng test cũ của phase 04.
3. **H1, loại khác không có thay đổi thực** (ví dụ áp dòng Kiêm nhiệm đã có sẵn trong danh sách) — vẫn mở `confirm()` với câu chung "Dòng này sẽ được áp vào hồ sơ." thay vì gọi thẳng API, để giữ đúng tinh thần "luôn hỏi trước khi gọi API" của H1.
4. **Tách thêm `employee-tab-work-history.tsx`** dù phase/review không nêu tên tệp này — vì chính lượt sửa H1 làm nó vượt 200 dòng; xử luôn theo CLAUDE.md §"File Size Management" cho nhất quán, không đợi review lần sau.

## Concerns
- Không có pending/blocker. Cổng đầy đủ (typecheck/lint/vitest phạm vi giao) xanh.

**Status:** DONE
**Summary:** Sửa đủ 6 nhóm finding FE (H1/M4/M5/M6/Low FE/Low tách tệp) theo đúng luồng viết test đỏ → sửa code → xanh cho từng nhóm; dọn trùng 1 bộ hằng số mã sự kiện ra một nguồn duy nhất; tách thêm 1 tệp ngoài danh sách review (tab-work-history.tsx) vì chính H1 làm nó vượt ngưỡng. Typecheck 0 lỗi, lint 0 lỗi/29 cảnh báo nền cũ, 690 bài vitest trong phạm vi giao đều xanh.
**Concerns:** Mục "Quyết định/giả định" #1 (Esc của hộp hỏi áp hồ sơ khi lưu) là lựa chọn giữa hai phương án hợp lệ nêu trong đề bài — đã chọn phương án ít thay đổi kiến trúc hơn, nêu rõ ở trên để đại ca duyệt lại nếu muốn phương án kia.
