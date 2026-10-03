## Phase Implementation Report

### Executed Phase
- Task: nâng «Quá trình công tác» + «Quyết định bổ nhiệm» ở `/me` từ tab con lồng trong thẻ cuối tab «Thông tin cá nhân» lên thành 2 TAB CHÍNH của trang.
- Plan: frontend-v2/plans/261003-0837-qua-trinh-lam-viec-nhan-su
- Status: completed

### Files Modified
- `frontend-v2/src/app/pages/profile-page.tsx` (338 → 391 dòng, +53). Đổi:
  - Import `FileCheck2` thêm vào nhóm lucide; đổi import `ProfileWorkHistoryCard` → `ProfileWorkHistoryTab` + `ProfileWorkDecisionsTab`.
  - Đưa `useMyEmployee()` lên ĐẦU hàm (trước tính `activeTab`) + biến `hasEmployeeProfile = Boolean(myEmployee)` — vì `activeTab` nay cần gác theo cờ này.
  - `activeTab`: thêm 2 nhánh `work-history`/`decisions` **đầu** chuỗi ternary, cả hai đều `&& hasEmployeeProfile` — mở thẳng `?tab=work-history` khi chưa gắn hồ sơ thì rơi về `info`, giống khuôn `rawTab === 'tickets' && canReadTickets` đã có.
  - `TabsTrigger`: thêm 2 tab (icon `History`/`FileCheck2`, đúng icon dùng ở `employee-detail-page.tsx`) ngay sau «Thông tin cá nhân», bọc `{hasEmployeeProfile && (...)}`.
  - `TabsContent`: thêm 2 block tương ứng (`ProfileWorkHistoryTab`/`ProfileWorkDecisionsTab`), cũng bọc `{hasEmployeeProfile && (...)}` — gác 2 lớp (ẩn trigger + chặn giá trị `activeTab`) cho chắc.
  - Xóa `<ProfileWorkHistoryCard />` khỏi cuối khối `{myEmployee && (...)}` trong tab «Thông tin cá nhân» — không còn trùng 2 chỗ.
  - Bỏ khai trùng `const { data: myEmployee } = useMyEmployee()` ở vị trí cũ (chỉ còn 1 lần gọi).

### Files Created
- `frontend-v2/src/app/components/profile/profile-work-history-tab.tsx` (58 dòng) — nội dung TAB CHÍNH «Quá trình công tác», tách trực tiếp từ `profile-work-history-card.tsx` cũ (bỏ lớp `Tabs` con, chỉ còn `EmployeeWorkHistoryMainSection` + `EmployeeWorkHistoryFilesDialog`, cùng props/hành vi cũ — chỉ đọc, dùng `useMyWorkHistory`).
- `frontend-v2/src/app/components/profile/profile-work-decisions-tab.tsx` (54 dòng) — nội dung TAB CHÍNH «Quyết định bổ nhiệm», cùng khuôn, dùng `EmployeeWorkHistoryDecisionSection`, KHÔNG truyền `onAddInWorkHistoryClick` (ở `/me` giờ cả hai tab đều chỉ đọc, không có lối "nhảy sang tab ghi" như ở `employee-detail-page.tsx`).
- `frontend-v2/src/app/components/profile/profile-work-history-tab.test.tsx` (5 bài, chuyển gần như nguyên từ test cũ của card: đúng đường API không id, không nút ghi, rỗng → câu nhắc, hộp tệp chỉ xem, không nút ghi ở dạng Dòng thời gian).
- `frontend-v2/src/app/components/profile/profile-work-decisions-tab.test.tsx` (3 bài: chỉ hiện dòng có `decision_no` + dùng chung 1 lần gọi API, rỗng → câu nhắc KHÔNG có nút nhảy tab, không nút ghi ở cả Bảng/Dòng thời gian).
- `frontend-v2/src/app/pages/profile-page.test.tsx` (MỚI — trang này trước đó chưa có test nào) — 5 bài tập trung đúng phần vừa đổi: 2 tab chính đứng thứ 2/3 (sau «Thông tin cá nhân»), tab «Quá trình công tác» hiện đúng khu + không nút ghi, tab «Quyết định bổ nhiệm» lọc đúng + không nút ghi/không nút nhảy tab, ẨN cả hai khi `employee_id = 0` (cả mặc định và khi cố mở thẳng `?tab=work-history` — rơi về `info`). Mẹo giữ test nhẹ: không resolve `/api/auth/me` (giữ `null`) nên tab «Thông tin cá nhân» chỉ dựng Skeleton, tránh phải mock cả chuỗi phụ thuộc `ProfileInfoCard`/`SignatureCard`/`EmailNotificationCard`; Radix `TabsContent` không mount tab ẩn nên việc này không ảnh hưởng 2 tab mới.

### Files Deleted
- `frontend-v2/src/app/components/profile/profile-work-history-card.tsx` — không còn ai import (grep xác nhận), thay bằng 2 tab trên.
- `frontend-v2/src/app/components/profile/profile-work-history-card.test.tsx` — tách thành 2 test file trên.

### Tasks Completed
- [x] 2 tab chính ngay sau «Thông tin cá nhân», khuôn tab hiện có (icon lucide `History`/`FileCheck2`, `TAB_TRIGGER_UNDERLINE`, lưu trên URL `?tab=work-history`/`?tab=decisions` khớp giá trị dùng ở màn hồ sơ nhân sự).
- [x] Mỗi tab 1 khu đúng (`EmployeeWorkHistoryMainSection`/`EmployeeWorkHistoryDecisionSection`), nút Bảng/Dòng thời gian riêng (2 `useUrlParamState` khác khóa `whView`/`decView`, không đụng nhau), CHỈ ĐỌC, dùng chung `useMyWorkHistory` (TanStack Query cache theo key — 2 tab test xác nhận chỉ 1 lần gọi `/api/employees/me/work-history`; 2 tab cũng không mount cùng lúc vì Radix Tabs lazy-mount).
- [x] Bỏ thẻ tab-con cũ khỏi cuối tab «Thông tin cá nhân» — không trùng 2 chỗ, không code chết (xóa cả file cũ).
- [x] Ẩn 2 tab khi `employee_id = 0` — gác 2 lớp: ẩn `TabsTrigger` (giống `canReadTickets`) VÀ chặn giá trị trong `activeTab` (mở thẳng link `?tab=work-history` không lọt).
- [x] Không đụng `src/modules/hr/**` — chỉ IMPORT `EmployeeWorkHistoryMainSection`/`EmployeeWorkHistoryDecisionSection`/`EmployeeWorkHistoryFilesDialog`/`useMyWorkHistory` (đều đã có sẵn từ trước, không sửa file nào trong đó).

### Tests Status
- Type check: pass (0 lỗi) — `docker compose exec -T erp npm run typecheck`.
- Lint: pass (0 lỗi, 29 cảnh báo cũ không đổi — không file nào của tôi trong danh sách).
- Unit tests: `npx vitest run src/app/pages src/app/components/profile` → 11 file, **62 bài xanh** (gồm 5 bài page mới + 5 + 3 bài 2 tab mới).

### Issues Encountered
Không có. Lựa chọn đáng nêu: gác ẨN dùng `Boolean(myEmployee)` — `useMyEmployee()` là query async, nên có một nhịp ngắn lúc đang tải mà 2 tab chưa hiện dù tài khoản có hồ sơ (giống hệt hành vi cũ của `ProfileLeaveCard`/`ProfileEmergencyContacts`/thẻ work-history cũ, không phải hồi quy mới).

### Next Steps
Chưa commit (đúng yêu cầu). Gộp cùng các tệp work-history khác (CR-574) khi đại ca duyệt.

**Status:** DONE
**Summary:** Tách 2 khu quá trình công tác/quyết định bổ nhiệm từ tab con ẩn trong «Thông tin cá nhân» thành 2 tab chính độc lập ở `/me`, ẨN khi chưa gắn hồ sơ nhân sự, dùng chung component + query với tab hồ sơ, không nút ghi. Xóa code chết (`profile-work-history-card.*`). Typecheck/lint/62 test xanh.
**Concerns/Blockers:** Không có.
