# Phase 04 + 05 — Frontend «Quá trình công tác»

## Thực thi
- Phase: phase-04-frontend-tab-qua-trinh-cong-tac.md, phase-05-frontend-trang-ca-nhan.md
- Plan: frontend-v2/plans/261003-0837-qua-trinh-lam-viec-nhan-su/plan.md
- Trạng thái: **completed** (code theo hợp đồng API phase 02 — phase 02 chạy song song, chưa xác nhận bằng bấm tay thật)

## Tệp đã tạo (phase 04)
- `hr/types/employee-work-history.ts` (90 dòng) — `EmployeeWorkHistory`, list/save/apply result, `EmployeeWorkHistoryPayload`, `WorkHistoryFile`.
- `hr/api/employee-work-history-api.ts` (86 dòng) — `employeeWorkHistoryApi` (list/listMine/create/update/remove/apply) + hàm tệp (`fetchWorkHistoryFiles`/`uploadWorkHistoryFiles`/`deleteWorkHistoryFile`/url) + `toWorkHistoryPayload` (rỗng → `null` cho `to_date`/`decision_date`, khớp `employee-api.ts::toEmployeePayload`).
- `hr/hooks/use-employee-work-history.ts` (95 dòng) — `useEmployeeWorkHistory`, `useMyWorkHistory`, `useSaveEmployeeWorkHistory`, `useDeleteEmployeeWorkHistory`, `useApplyEmployeeWorkHistory` + dọn cache đúng bảng trong phase (`employeeWorkHistory` luôn; `employee`/`employeeDepartments`/`employees()`/`myEmployee()` khi có `applied_changes`).
- `hr/hooks/use-employee-work-history-files.ts` (48 dòng) — khuôn `use-leave-attachments.ts`.
- `hr/utils/employee-work-history-apply.ts` (98 dòng) + `.test.ts` (173 dòng, **17 bài, xanh**) — `planApplyPrompt` thuần, không gọi API/mở hộp.
- `hr/schemas/employee-work-history-schema.ts` (48 dòng) — zod, refine `to_date ≥ from_date`.
- `hr/config/employee-work-history-columns.tsx` (192 dòng) — `buildEmployeeWorkHistoryColumns({canOpenFiles, onOpenFiles, actions?})`, dùng lại ở phase 05 không `actions`.
- `hr/components/employee-tab-work-history.tsx` (164 dòng) + `.test.tsx` (149 dòng, **5 bài, xanh**).
- `hr/components/employee-work-history-form-dialog.tsx` (242 dòng) + `.test.tsx` (152 dòng, **5 bài đúng tên trong phase, xanh**).
- `hr/components/employee-work-history-files-dialog.tsx` (179 dòng, prop `editable`).
- `hr/components/employee-work-history-resign-confirm-dialog.tsx` (87 dòng) + `.test.tsx` (56 dòng, **4 bài, xanh**).
- **Thêm ngoài danh sách phase** (deviation, xem Concerns): `hr/components/employee-work-history-form-dialog-fields.tsx` (267 dòng) — tách Ô NHẬP khỏi hộp điều phối để mỗi tệp giữ gần ngưỡng `./CLAUDE.md` §"File Size Management" (hộp gốc viết liền sẽ ~345 dòng).

## Tệp đã sửa (phase 04)
- `hr/pages/employee-detail-page.tsx` — +import `History`/`EmployeeTabWorkHistory`, +1 `TabsTrigger` (sau «Chung»), +1 `TabsContent` (~14 dòng, trong hạn "≈12 dòng" của phase).
- `shared/constants/query-keys.ts` — +3 khóa dưới `hr`: `employeeWorkHistory(id)`, `myWorkHistory()`, `workHistoryFiles(historyId)`.

## Tệp đã tạo/sửa (phase 05)
- TẠO `app/components/profile/profile-work-history-card.tsx` (56 dòng) + `.test.tsx` (126 dòng, **4 bài, xanh**).
- SỬA `app/pages/profile-page.tsx` — +import, +1 dòng JSX (`<ProfileWorkHistoryCard />` ngay dưới `<ProfileEmergencyContacts/>`, trong nhánh `{myEmployee && (...)}`).

## Bẫy bắt buộc — đã xử
1. **Bẫy 1 (form lồng form)**: `<form onSubmit>` của hộp thêm/sửa gọi `event.stopPropagation()` TRƯỚC `form.handleSubmit(onSubmit)(event)`. Có bài kiểm riêng xác nhận `onSubmit` của form cha KHÔNG bị gọi khi submit hộp con (`employee-work-history-form-dialog.test.tsx`).
2. Mọi `<Button>` trong các tệp mới đều `type="button"` (nút Lưu duy nhất là `type="submit"`, đúng trong `<form>` của chính hộp đó).
3. Chặn bấm đúp bằng `useRef` ở cả ba nơi: hộp thêm/sửa (`submittingRef`), Áp/Xóa trong tab (`useBusyIds` theo từng id).
4. Enter trong ô của hộp thoại: cùng `stopPropagation` ở bẫy 1 xử luôn (Enter kích submit NATIVE của đúng `<form>` chứa ô đó — hộp con, không phải form cha).
5. Ô hành động trong bảng (`employee-work-history-columns.tsx`): bọc `onClick={(e) => e.stopPropagation()}`.

## Q1–Q4 — đối chiếu triển khai
- **Q1**: `from_date` = ngày hiệu lực, `decision_date` riêng — đúng schema + cột.
- **Q2 (Thôi việc)**: `planApplyPrompt` trả `{kind:'resign', resignDate}` khi tới/ qua ngày hiệu lực và hồ sơ chưa khớp; hộp `EmployeeWorkHistoryResignConfirmDialog` RIÊNG (AlertDialog `destructive`, 2 nút «Chỉ lưu dòng» / «Lưu và chuyển sang nghỉ việc»), KHÔNG dùng `confirm()` chung — có bài kiểm xác nhận `confirm()` không bị gọi ở nhánh này.
- **Q3**: FE không tự đoán "tự sửa" — đọc thẳng cờ `can_edit` từ backend (A9), không ghép `can()` + so `employee_id`.
- **Q4 (tệp)**: cột Tệp đọc `can_open_files`: có quyền → nút kẹp giấy mở `EmployeeWorkHistoryFilesDialog`; không có → chữ tĩnh «Có N tệp đính kèm» (tooltip), KHÔNG nút xem/tải, KHÔNG gọi `/api/attachments` (có bài kiểm xác nhận hộp tệp luôn nhận `open:false` khi không có nút để bấm). `/me` ở phase 05 dùng lại cột với `canOpenFiles:true` cố định và `editable:false` (chỉ xem — không vùng thả, không nút gỡ, nút xem/tải vẫn hiện).

## Tests Status
- Type check: **pass** (`npm run typecheck`, 0 lỗi).
- Lint: **pass** (`npm run lint`, 0 lỗi, **29 cảnh báo — đúng mức nền cũ, không thêm cảnh báo mới**; đã tự sửa 1 cảnh báo `react-refresh/only-export-components` phát sinh lúc đầu bằng cách đổi hàm con `FileCell` trong `employee-work-history-columns.tsx` từ JSX-component sang hàm thường `renderFileCell(...)` gọi trực tiếp).
- Unit tests scoped: `npx vitest run src/modules/hr src/app/pages src/app/components/profile` → **60 tệp / 656 bài, tất cả xanh** (không có tệp test nào khớp `src/app/pages`, không lỗi). Không chạy `npm run check` (full suite) theo đúng chỉ dẫn.

## Issues Encountered / Deviations
1. **Thêm 1 tệp ngoài danh sách phase**: `employee-work-history-form-dialog-fields.tsx`. Hộp thêm/sửa gộp 10 ô + 3 hộp con (hộp tệp, hộp xác nhận thôi việc) sẽ ra ~345 dòng nếu viết liền — vượt xa ngưỡng 200 dòng của `./CLAUDE.md` §"File Size Management" ("nếu file vượt 200 dòng, xem xét module hóa... sau khi module hóa, tiếp tục việc chính"). Tách Ô NHẬP (thuần trình bày, không state/mutation) khỏi hộp điều phối (state, mutation, câu hỏi áp hồ sơ) là ranh giới rõ nhất. Hai tệp còn lại 242 và 267 dòng — vẫn hơi vượt ngưỡng nhưng tách thêm nữa (ví dụ mỗi `FormField` một tệp) sẽ phá KISS nhiều hơn là giúp. Không đụng file nào của phase khác, không xung đột song song với phase 02 (backend).
2. **Nút «Tạo dòng đầu từ hồ sơ»** chỉ hiện khi `can_edit` — phase không nói rõ có cần hiện cho người chỉ-đọc hay không; quyết định: không, vì tạo dòng là hành vi ghi.
3. **Tick «Đóng dòng đang hiệu lực»** chỉ hiện ở chế độ TẠO MỚI (không hiện khi sửa dòng có sẵn) — phase không nói rõ, nhưng logic "đóng dòng KHÁC đang mở" chỉ có ý nghĩa khi dòng đang xử lý là dòng MỚI chèn vào; sửa một dòng có sẵn không nên tự động đóng dòng khác.
4. Câu mô tả thay đổi trong hộp hỏi `confirm()` (loại 1,2,3,5: "Pháp nhân"/"Phòng ban"/"Chức vụ"; loại 4: "Thêm/Gỡ kiêm nhiệm phòng ban này") dùng nhãn CHUNG, không kèm tên pháp nhân/phòng/chức vụ cụ thể — `planApplyPrompt` chỉ nhận id, không có danh mục tên để tra; chấp nhận được vì BE vẫn là chốt chặn cuối và hộp `confirm()` chỉ cần nói ĐÚNG VIỆC sẽ đổi, không cần nhắc lại giá trị (người dùng vừa gõ nó trong form).
5. Hằng số `WORK_HISTORY_FILE_MAX_SIZE_MB`/`WORK_HISTORY_FILE_ACCEPT` xuất từ `employee-work-history-files-dialog.tsx` và dùng lại ở hàng đợi tệp lúc TẠO MỚI (`employee-work-history-form-dialog.tsx`/`-fields.tsx`) — tránh hai nơi lệch trần dung lượng/đuôi tệp (DRY, không phải tệp phase không khai).

## Đối chiếu với backend THẬT (phase 02/03 đã xong lúc viết báo cáo này)
Lúc bắt đầu, phase 02 (backend) còn `pending`/chạy song song nên code theo đúng **hợp đồng** ở
`phase-02-backend-api-ap-ho-so-dinh-kem.md`. Tới lúc hoàn thành phần việc này, `plan.md` đã ghi
phase 02 + 03 **completed** — đã đọc lại mã backend thật để đối chiếu, không chỉ tin vào hợp đồng:
- `work_history_controller.py`: 6 đường API, envelope, thứ tự khai `/me` trước `/{eid}` — **khớp 100%** giả định ở `employee-work-history-api.ts`.
- `work_history_schema.py` (`WorkHistoryOut`/`WorkHistoryIn`/`WorkHistoryUpdate`): tên trường, kiểu, mặc định — **khớp 100%** `types/employee-work-history.ts` và `schemas/employee-work-history-schema.ts`. Chú ý `event_type_label` CỐ Ý không có trong `WorkHistoryOut` (R2/QĐ-11) — đúng với FE tự tra `WORK_EVENT_TYPE`.
- `work_history_access.py` (`can_edit`, `can_open_files`, `check_file`): đúng ngữ nghĩa A9/Q3/Q4 mà FE đang giả định (không tự ghép `can()` + so `employee_id`).
- `file_registry.py`: `employee_work_history` → `(employee, _DOC, 50)` + `PRIVATE_ENTITIES` — đã CHỈNH `ACCEPT` của hộp tệp cho khớp đủ tập đuôi `_DOC` (ban đầu thiếu `txt/csv/xml/msg/eml/cdr`).
**Chưa làm**: bấm tay qua trình duyệt thật (todo cuối của cả hai phase) — ngoài phạm vi gate được giao (`typecheck`/`lint`/`vitest`), và cần tài khoản demo + stack `docker compose up` đang chạy để thao tác tay, không phải việc đọc mã.

## Query keys (đã thêm)
```
hr.employeeWorkHistory(id) = ['hr','employees',id,'work-history']
hr.myWorkHistory()         = ['hr','employees','me','work-history']
hr.workHistoryFiles(hid)   = ['hr','work-history',hid,'files']
```

## Next Steps
- Phase 03 (backend test) và phase 06 (tài liệu) phụ thuộc phase 02 + 04/05 — có thể tiếp tục sau khi phase 02 báo DONE.
- Khi phase 02 lên local: bấm tay cả hai mục "Bấm tay" còn treo ở phase 04 và 05 (đã đánh dấu CHƯA LÀM trong hai tệp phase, kèm lý do).
- Không commit (theo chỉ dẫn).

**Status:** DONE
**Summary:** Hoàn thành phase 04 (tab «Quá trình công tác» ở hồ sơ: cột/tab/hộp thêm-sửa/hộp tệp/hộp xác nhận thôi việc riêng) và phase 05 (thẻ chỉ-đọc ở `/me`, dùng lại cột phase 04). Cả 5 bẫy bắt buộc + Q1–Q4 đã xử đúng tinh thần hợp đồng API, và đã ĐỐI CHIẾU LẠI với mã backend thật (phase 02/03 xong trong lúc làm) — khớp 100% đường API, hình dạng dữ liệu, ngữ nghĩa cờ quyền; đã sửa 1 chỗ lệch nhỏ (tập đuôi tệp chấp nhận ở hộp tệp thiếu vài đuôi so với `FILE_POLICY`). Typecheck 0 lỗi, lint 0 lỗi (không thêm cảnh báo), 656 bài vitest trong phạm vi được giao đều xanh.
**Concerns:** (1) Thêm 1 tệp `-fields.tsx` ngoài danh sách sở hữu của phase để giữ mỗi tệp gần ngưỡng 200 dòng — không đụng file của phase khác. (2) Hai tệp hộp thêm/sửa (242, 267 dòng) vẫn hơi vượt ngưỡng — tách tiếp sẽ phá KISS. (3) Chưa bấm tay qua trình duyệt thật (cần stack chạy + tài khoản demo, ngoài phạm vi gate typecheck/lint/vitest được giao) — đã đối chiếu mã nguồn backend thay cho bấm tay, rủi ro lệch hợp đồng coi như đã loại gần hết.
