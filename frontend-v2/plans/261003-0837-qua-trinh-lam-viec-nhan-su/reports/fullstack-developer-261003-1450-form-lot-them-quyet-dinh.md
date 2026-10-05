## Phase Implementation Report

### Executed Phase
- Task: 3 việc «Quá trình công tác & Quyết định bổ nhiệm» — (1) lỗi form lồng ở hộp tệp/xem trước, (2) mốc «Hiệu lực…» khi không có ngày ký, (3) nút «+ Thêm quyết định»
- Plan: frontend-v2/plans/261003-0837-qua-trinh-lam-viec-nhan-su
- Status: completed

### Việc 1 — LỖI form lồng: nút nào thực sự gây submit?
**Kết luận sau khi dựng lại bằng jsdom (3 lớp Portal thật: Sửa → Tệp quyết định → Xem trước) VÀ 2 bài kiểm tay bằng `createPortal` trần: KHÔNG nút nào trong chuỗi mô tả (Quản lý tệp/Xem trước/Tải về/Mở tab mới/Close) có thể submit form cha theo cơ chế HTML — vì mỗi `DialogContent` của Radix portal RA `document.body`, tách khỏi DOM của `<form>` trang; nút `type="submit"` không có `<form>` làm chủ (form owner) thì click không phát sinh event `submit` nào cả (đúng chuẩn, kiểm chứng bằng bài test base-case + raw-portal-case, cả hai đúng dự đoán).**

Rà toàn bộ nút trong chuỗi — TẤT CẢ đã có `type="button"` TRƯỚC khi tôi sửa (do đợt "sửa review frontend" 1000 đã vá): Sửa (pencil), Áp, Xóa-trigger (`ConfirmIconButton`), Quản lý tệp, Xem trước, Tải về (hộp tệp), Gỡ tệp-trigger. CHỈ 2 nút thật sự thiếu `type="button"`: **«Mở tab mới» và «Tải về» trong `shared/attachments/attachment-preview-dialog.tsx`** (component DÙNG CHUNG, không riêng nhân sự) — mặc định HTML là `submit`. Đã sửa (a). Dù phân tích + test cho thấy 2 nút này KHÔNG thể gây bug (bản thân portal detach), sửa `type="button"` là đúng quy ước "bẫy 3" của repo và an toàn tuyệt đối cho MỌI nơi dùng component chung này sau này (vd nếu ai render nó không qua Dialog).

Làm thêm (b) theo đúng yêu cầu — bọc `onSubmit` chặn-lan ở ranh giới `AttachmentPreviewDialog` VÀ `EmployeeWorkHistoryFilesDialog` (dùng `className="contents"` để không đổi layout `flex-col`/`grid` của `DialogContent` cha) — không có `<form>` nào trong 2 hộp này hôm nay nên đây là **phòng ngừa**, không phải vá một lỗ đã xác nhận.

**Không tìm được bằng chứng mã nguồn cho mốc submit thật** mà báo cáo tay nêu (PATCH lúc 11:32:43). Khả năng cao nhất không phải code bug của 2 hộp này: hoặc (i) người test bấm nhầm đúng nút «Lưu» thật ở đầu trang (`employee-detail-page.tsx`, luôn `type="submit"`) ngay lúc overlay vừa tắt — các hộp Dialog che kín `fixed inset-0` nên "Lưu" không bấm được TRONG LÚC hộp mở, chỉ có nguy cơ ngay khoảnh khắc hộp cuối vừa đóng animation; hoặc (ii) một mốc tôi chưa dựng lại được. Đã sửa đủ theo yêu cầu (a)+(b) và thêm lớp chặn thứ ba (xem dưới) — nêu rõ để đại ca cân nhắc kiểm tay lại trên Chrome thật nếu còn gặp.

### Việc 2 — mốc «Hiệu lực …» khi không có ngày ký
`employee-work-history-display.ts::workHistoryTimelineDateLabel` — dòng không `decision_date` giờ hiện `Hiệu lực ${from_date}` thay vì `—`. Bảng (cột «Ngày ký QĐ») GIỮ NGUYÊN, không đụng.

### Việc 3 — nút «+ Thêm quyết định»
- Hook mới `use-employee-work-history-editor-dialog.ts` (điều phối `open/editRow/seed/requireDecisionNo/createTitle` + `openCreate`/`openEdit`) — NÂNG lên chỗ chung, cả `employee-tab-work-history.tsx` và `employee-tab-work-decisions.tsx` tự gọi MỘT LẦN, không chép logic chuyển trạng thái.
- `EmployeeWorkHistoryFormDialog` thêm 2 prop tùy chọn: `requireDecisionNo` (đổi resolver sang `employeeWorkHistoryDecisionSchema` — Số QĐ bắt buộc, lỗi hiện tại `FormMessage` sẵn có) và `createTitle` (đè tiêu đề lúc TẠO MỚI, không đụng lúc SỬA).
- `EmployeeTabWorkDecisions` gọi `editor.openCreate({event_type: APPOINT_TYPE}, {requireDecisionNo:true, createTitle:'Thêm quyết định bổ nhiệm'})`, tự mount `EmployeeWorkHistoryFormDialog` của riêng nó (allRows/extraDeptIds lấy đúng như tab kia).
- `EmployeeWorkHistoryDecisionSection`: đổi `onAddInWorkHistoryClick` (nhảy tab) → `onAddClick` (mở thẳng hộp), hiện ở `toolbarEnd` (bảng) / `addButton` của `EmployeeWorkHistoryTimelineToolbar` (dòng thời gian) VÀ nút gợi ý giữa khu lúc rỗng — cả hai gọi chung `onAddClick`. Ẩn hoàn toàn khi không truyền (thẻ `/me`).
- Lưu dùng chung `useEmployeeWorkHistory(employee.id)`/`invalidateAfterChange` đã có sẵn → dòng mới hiện ở CẢ HAI tab không cần sửa gì thêm.

### Files Modified
- `src/shared/attachments/attachment-preview-dialog.tsx` (+9 dòng) — `type="button"` 2 nút, bọc `onSubmit` chặn-lan.
- `src/modules/hr/components/employee-work-history-files-dialog.tsx` (198→137 dòng, TÁCH) — bọc `onSubmit` chặn-lan; danh sách tệp tách sang file mới.
- `src/modules/hr/components/employee-work-history-files-dialog-list.tsx` (MỚI, 112 dòng) — thuần trình bày, nhận hàm xử lý từ cha.
- `src/modules/hr/utils/employee-work-history-display.ts` — fallback «Hiệu lực …».
- `src/modules/hr/utils/employee-work-history-apply.ts` — thêm `APPOINT_TYPE = 3`.
- `src/modules/hr/schemas/employee-work-history-schema.ts` — thêm `employeeWorkHistoryDecisionSchema`.
- `src/modules/hr/hooks/use-employee-work-history-editor-dialog.ts` (MỚI, 56 dòng).
- `src/modules/hr/components/employee-work-history-form-dialog.tsx` (199→209 dòng, hơi vượt 200 — xem Concerns) — `requireDecisionNo`/`createTitle`.
- `src/modules/hr/components/employee-work-history-form-dialog-fields.tsx`, `-detail-fields.tsx` — thread `requireDecisionNo`, nhãn «Số QĐ *».
- `src/modules/hr/components/employee-tab-work-history.tsx` — dùng hook chung thay state cục bộ.
- `src/modules/hr/components/employee-tab-work-decisions.tsx` — dùng hook chung, mount `EmployeeWorkHistoryFormDialog`, bỏ prop `onGoToWorkHistoryClick`.
- `src/modules/hr/components/employee-work-history-decision-section.tsx` — `onAddClick` thay `onAddInWorkHistoryClick`, toolbarEnd/addButton.
- `src/modules/hr/pages/employee-detail-page.tsx` — bỏ truyền `onGoToWorkHistoryClick`.
- `src/app/components/profile/profile-work-decisions-tab.tsx` — sửa comment (không đổi hành vi, `/me` vẫn không `onAddClick`).

### Tests
Mới: `attachment-preview-dialog.test.tsx` (3), `employee-work-history-files-dialog.test.tsx` (5, gồm 3 bài bẫy form lồng), `use-employee-work-history-editor-dialog.test.ts` (5). Sửa/thêm bài trong: `employee-work-history-form-dialog.test.tsx` (+7, gồm bẫy 1 mở rộng qua cả 3 hộp + createTitle/requireDecisionNo), `employee-work-history-display.test.ts` (mốc Hiệu lực), `employee-tab-work-decisions.test.tsx` (viết lại theo hành vi mới), `employee-work-history-decision-section.test.tsx` (viết lại nhóm nút), `profile-work-decisions-tab.test.tsx` + `profile-page.test.tsx` (câu rỗng/nút đổi tên).

- Type check: pass (0 lỗi).
- Lint: pass (0 lỗi, 29 cảnh báo nền cũ — không thêm mới; 1 lỗi tự gây lúc đầu do `import()` type annotation trong test, đã sửa về khuôn `import type * as X from '...'`).
- Vitest theo yêu cầu: `src/modules/hr src/app/components/profile src/shared/attachments` → 87 tệp / 928 bài xanh. `src/app/pages` → 5 bài xanh.

### Issues Encountered
- `employee-work-history-form-dialog.tsx` còn 209 dòng (vượt ngưỡng 200 "nên xem xét" ~9 dòng) sau khi thêm 2 prop + docstring — đã tối giản comment hết mức hợp lý; không tách thêm vì phần còn lại (orchestration state/effect/hook gọi) là một khối logic liền, tách nữa sẽ làm khó đọc hơn là lợi.
- Không dựng lại được mốc gây `PATCH` thật trên jsdom dù đã thử 2 cấu trúc portal (qua component thật + `createPortal` trần) — xem phần "Kết luận" Việc 1. Đã vá đủ theo yêu cầu + thêm lớp chặn phòng ngừa, nhưng KHÔNG dám khẳng định 100% đây là root cause gốc nếu bug còn tái hiện trên Chrome thật.

### Next Steps
- Nếu đại ca còn thấy PATCH lạ trên Chrome thật sau bản vá này: kiểm tra lại CHÍNH XÁC click cuối cùng trước khi PATCH bắn (devtools "Event Listeners" hoặc ghi màn hình chậm) — nghi vấn còn lại là click-through vào nút «Lưu» thật ở đầu trang ngay lúc overlay cuối cùng vừa tắt, không phải nút trong 3 hộp lồng.

**Status:** DONE
**Summary:** Vá đủ (a)+(b) cho hộp tệp/xem trước theo yêu cầu dù không dựng lại được cơ chế submit thật qua jsdom (2 nút thiếu type=button chỉ ở `attachment-preview-dialog.tsx`, các nút khác đã an toàn từ đợt sửa trước); fix mốc «Hiệu lực…»; thêm nút «+ Thêm quyết định» dùng chung đúng hộp cũ qua hook điều phối mới, Số QĐ bắt buộc validate ở form. Typecheck/lint sạch, 928+5 bài vitest xanh trong phạm vi giao.
**Concerns/Blockers:** Chưa xác định được 100% nút/sự kiện gây PATCH thật trên Chrome — nêu rõ nghi vấn còn lại (click-through vào nút Lưu đầu trang) ở trên.
