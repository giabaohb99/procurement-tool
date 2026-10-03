## Phase Implementation Report

### Executed Phase
- Task: tách tab gộp «Quá trình công tác & Quyết định» thành 2 tab riêng (work-history + decisions)
- Plan: frontend-v2/plans/261003-0837-qua-trinh-lam-viec-nhan-su
- Status: completed

### Files Modified
- `frontend-v2/src/modules/hr/pages/employee-detail-page.tsx` — import `FileCheck2` + `EmployeeTabWorkDecisions`; tách 1 `TabsTrigger`/`TabsContent` cũ thành 2 (`work-history` giữ nguyên giá trị, `decisions` mới); nút nhảy tab truyền `onGoToWorkHistoryClick={() => setTab('work-history')}`. +9 dòng.
- `frontend-v2/src/modules/hr/components/employee-tab-work-history.tsx` — bỏ `EmployeeWorkHistoryDecisionSection` + import, sửa docstring. 149 dòng (trước 153).
- `frontend-v2/src/modules/hr/components/employee-work-history-decision-section.tsx` — thêm prop `onAddInWorkHistoryClick?`, `showAddInWorkHistory`, nút «Thêm ở tab Quá trình công tác» khi rỗng + có quyền. 111 dòng.
- `frontend-v2/src/app/components/profile/profile-work-history-card.tsx` — viết lại dùng `Tabs/TabsList/TabsTrigger/TabsContent` (shadcn) làm 2 tab con cục bộ (`useState`, không URL), mỗi tab con render đúng section cũ, chỉ đọc. 83 dòng.
- `frontend-v2/src/modules/hr/components/employee-tab-work-history.test.tsx` — bỏ describe block "khu Quyết định bổ nhiệm" (3 bài, không còn áp dụng — khu đó không còn render trong component này).
- `frontend-v2/src/modules/hr/components/employee-work-history-decision-section.test.tsx` — +4 bài cho `onAddInWorkHistoryClick` (hiện/ẩn theo rỗng, có prop, đang tải, không rỗng).
- `frontend-v2/src/app/components/profile/profile-work-history-card.test.tsx` — cập nhật 1 bài (QD-20, click sang tab con trước khi assert decisions-only), viết lại bài "không nút Thêm/Sửa/Xóa/Áp ở dạng dòng thời gian" để đi qua cả hai tab con qua `getByRole('tab', ...)`, +1 bài xác nhận 2 tab con + mặc định mở work-history.

### Files Created
- `frontend-v2/src/modules/hr/components/employee-tab-work-decisions.tsx` (61 dòng) — tab «Quyết định bổ nhiệm» mới, dùng CHUNG `useEmployeeWorkHistory(employee.id)` với `employee-tab-work-history.tsx` (TanStack Query cache theo key, staleTime 30s ở `core/api/query-client.ts` — không gọi API hai lần khi chuyển tab trong 30s). Chỉ đọc; files dialog `editable={canEdit}` (chỉ cấm sửa DÒNG, không cấm quản lý tệp).
- `frontend-v2/src/modules/hr/components/employee-tab-work-decisions.test.tsx` (5 bài) — gọi hook đúng id, nút gợi ý hiện/ẩn theo `can_edit`, không nút ghi, `editable` hộp tệp theo `can_edit`.

### Tasks Completed
- [x] Tách tab `work-history` (giữ giá trị cũ, link cũ không gãy) + `decisions` (mới) ngay sau tab Chung, icon lucide riêng (`FileCheck2`).
- [x] Hai tab dùng chung 1 query, không gọi API 2 lần (cache theo key, staleTime 30s).
- [x] Tab Quyết định chỉ xem; rỗng + có quyền sửa → nút nhảy sang tab Quá trình công tác.
- [x] `/me`: 2 tab con trong 1 thẻ (Tabs shadcn), mỗi tab con có toggle Bảng/Dòng thời gian riêng, chỉ đọc.
- [x] Dọn code chết (bỏ DecisionSection khỏi tab gộp cũ), tái dùng component khu sẵn có — không chép.
- [x] Luật cũ giữ nguyên: quyền (`can_edit`/`can_open_files` từ backend), gác file theo quyền, không form lồng mới sinh ra.
- [x] Cập nhật test theo yêu cầu #5.
- [x] Cập nhật đúng 3 đoạn tài liệu: dòng C3 + đoạn "Bổ sung 03/10/2026" ở `doc/erp/hrm/01-ho-so-nhan-su.md`, đoạn tab 2-khu trong mục `duoc-CR-585` ở `doc/tai-lieu-ky-thuat/nhat-ky-task.md` — không đụng chỗ khác của 2 tệp đó.

### Tests Status
- Type check: pass (0 lỗi)
- Lint: pass (0 lỗi, 29 cảnh báo cũ không đổi — không file nào của tôi nằm trong danh sách cảnh báo)
- Unit tests: `npx vitest run src/modules/hr src/app/components/profile src/app/pages` → 66 file, 753 bài xanh (tất cả, không chỉ hr/profile)

### Issues Encountered
- Không có file `employee-detail-page.test.tsx` / `profile-page.test.tsx` từ trước (page có quá nhiều phụ thuộc: useEmployee/useSaveEmployee/useDeleteEmployee/useUploadEmployeeAvatar/departments/colleagues/AuditTimeline/LoginSessionUserCard...). Không dựng test mới ở cấp trang cho việc URL `?tab=work-history`/`?tab=decisions` — xác nhận gián tiếp qua: (a) cơ chế đúng hệt 5 tab cũ khác của trang (không tab nào trong số đó có test URL riêng), (b) 2 component `EmployeeTabWorkHistory`/`EmployeeTabWorkDecisions` có test riêng xác nhận đúng nội dung từng tab. Nêu rõ để đại ca biết đây là lựa chọn phạm vi, không phải sót.
- Nút toggle Bảng/Dòng thời gian của 2 tab dùng 2 URL param riêng (`whView`/`decView`) nên không đụng nhau — không cần sửa `EmployeeWorkHistoryViewToggle`/`EmployeeWorkHistoryTimeline`.

### Next Steps
- Chưa commit (đúng yêu cầu). Khi đại ca duyệt, gộp commit này với các tệp work-history khác (cùng CR-574, chưa commit từ trước).
- Bấm tay qua trình duyệt (`frontend-v2` dev) để xác nhận link `?tab=work-history` cũ còn sống và giao diện 2 tab mới đúng ý — chưa làm trong phiên này (không có quyền truy cập stack chạy).

**Status:** DONE
**Summary:** Tách tab gộp work-history/decisions thành 2 tab riêng ở trang chi tiết + 2 tab con ở /me, dùng chung 1 query, thêm nút nhảy tab khi rỗng, dọn code chết, cập nhật đúng 3 test file + 3 đoạn tài liệu theo yêu cầu. Typecheck/lint/753 test xanh.
**Concerns/Blockers:** Không có test cấp trang (employee-detail-page/profile-page) cho URL tab — quyết định phạm vi có nêu lý do ở trên, nên bàn nếu đại ca muốn thêm.
