## Phase Implementation Report

### Executed Phase
- Task: gom thanh điều khiển «Quá trình công tác» / «Quyết định bổ nhiệm» về một hàng
- Plan: frontend-v2/plans/261003-0837-qua-trinh-lam-viec-nhan-su
- Status: completed

### Files Modified
- `src/shared/data-table/data-table.tsx` (+~15 dòng) — thêm prop `toolbarEnd?: ReactNode`, render SAU menu «Cột» trong cụm `ml-auto`; sửa điều kiện hiện hàng công cụ để `toolbarEnd` một mình (không `toolbar`, mọi cột `hideable:false`) vẫn dựng được hàng
- `src/shared/data-table/data-table.test.tsx` (+~50 dòng) — 3 bài mới cho `toolbarEnd` (đứng sau Cột, bỏ trống không đổi gì, một mình vẫn dựng hàng)
- `docs/ui/table.md` (+1 dòng) — khai `toolbarEnd` vào bảng Prop của `DataTable`
- `src/modules/hr/components/employee-work-history-toolbar.tsx` (mới, 94 dòng) — `EmployeeWorkHistoryToolbarTitle` (tiêu đề + toggle gộp một ô `flex-1 justify-between`, dùng làm `toolbar` của `DataTable` ở chế độ Bảng) và `EmployeeWorkHistoryTimelineToolbar` (hàng công cụ tự dựng cho chế độ Dòng thời gian, vì `DataTable` không mount lúc đó — lặp đúng class dải công cụ của `data-table.tsx` để đổi chế độ không nhảy hình)
- `src/modules/hr/components/employee-work-history-view-toggle.tsx` — bỏ `size="sm"` (h-8) → mặc định `"default"` (h-9), khớp chiều cao nút Tải lại/Cột đứng cạnh
- `src/modules/hr/components/employee-work-history-main-section.tsx` — bỏ hàng tiêu đề riêng; tiêu đề+toggle qua `toolbar`, «Thêm dòng» qua `toolbarEnd` (chế độ Bảng) hoặc `addButton` của `EmployeeWorkHistoryTimelineToolbar` (chế độ Dòng thời gian); thêm `onRefresh?` pass-through; `filtersActive={false}` để tránh `FilterResetButton` tự suy nhầm từ `whView`; bỏ `size="sm"` ở nút Thêm dòng cho đồng cỡ
- `src/modules/hr/components/employee-work-history-decision-section.tsx` — tương tự, KHÔNG có `toolbarEnd`/addButton (khu chỉ đọc)
- Test mới trong `employee-work-history-main-section.test.tsx` (+4 bài) và `employee-work-history-decision-section.test.tsx` (+2 bài): Tải lại/Cột/Thêm dòng đúng chỗ ở cả hai chế độ, Thêm dòng đứng SAU Cột, không có «Xóa lọc» lố, `onRefresh` được gọi đúng ở chế độ Dòng thời gian

### Tasks Completed
- [x] Một hàng duy nhất: tiêu đề trái, `[Bảng|Dòng thời gian][Tải lại][Cột][+Thêm dòng]` phải, Thêm dòng ngoài cùng
- [x] Chế độ Dòng thời gian: cùng hàng, có Tải lại, KHÔNG có Cột
- [x] Khu Quyết định: như Quá trình công tác nhưng không có Thêm dòng
- [x] Kích cỡ nút đồng đều (ToggleGroup đổi sang h-9 khớp nút outline cạnh nó)
- [x] Màn hẹp: dùng `flex-wrap` sẵn có của `DataTable`, không thêm hack riêng
- [x] Chặn regression «Xóa lọc» lố (do `whView`/`decView` nằm trên URL, không phải bộ lọc thật) bằng `filtersActive={false}`
- [x] `toolbarEnd` giữ tương thích ngược (optional, mặc định `undefined`, không đổi hành vi cũ), có test, có dòng docs

### Tests Status
- Type check: pass (0 lỗi)
- Lint: pass (0 lỗi, 29 cảnh báo — ĐÃ CÓ TRƯỚC khi sửa, xác nhận bằng `git stash` đối chiếu, không thêm cảnh báo mới)
- Unit tests: pass — `npx vitest run src/modules/hr src/app/components/profile src/app/pages src/shared/data-table` → 84 file, 901 bài; chạy riêng 3 file vừa sửa/thêm → 53 bài (28+13+12), tất cả xanh

### Issues Encountered
- Kỹ thuật gộp: tiêu đề+toggle đặt trong MỘT ô `flex-1 justify-between` làm `toolbar` — ô này nuốt hết khoảng trống còn lại của dải công cụ (cùng kỹ thuật ô tìm kiếm `flex-1` ở các màn khác, xem `docs/ui/table.md` §3) nên `ml-auto` của cụm Tải lại/Cột/Thêm dòng không còn gì để kéo, hai cụm dính liền thành một hàng đúng thứ tự yêu cầu — không cần thêm prop nào khác ngoài `toolbarEnd`.
- Vì `DataTable` KHÔNG mount ở chế độ Dòng thời gian, hàng công cụ của chế độ đó không thể đi qua `toolbar`/`toolbarEnd` — phải dựng `EmployeeWorkHistoryTimelineToolbar` riêng, tự quản lý cờ `refreshing` giống `handleRefresh` của `DataTable` (copy có chủ đích, không export logic đó ra khỏi `data-table.tsx` vì nó gắn chặt với state nội bộ của bảng).
- data-table.tsx đã 777 dòng từ trước (vượt ngưỡng 200 dòng của luật modularize) — KHÔNG đụng vào việc tách file đó, ngoài phạm vi task này; chỉ cộng thêm đúng phần `toolbarEnd`.

### Next Steps
- Không có phụ thuộc nào bị chặn. Gợi ý theo dõi: nếu sau này có màn khác cũng cần tiêu đề+toggle gộp vào `toolbar` của `DataTable`, xem lại `EmployeeWorkHistoryToolbarTitle` có nên nâng lên `shared/` không (hiện để ở `modules/hr/components/` vì chỉ hai khu này dùng, đúng luật "component riêng của phân hệ không để ở shared/" cho tới khi có nơi dùng thứ hai).

**Status:** DONE
**Summary:** Gộp hai hàng điều khiển thành một cho cả hai khu, thêm `toolbarEnd` cho `DataTable` (tương thích ngược, có test, có docs), đồng bộ chiều cao nút, chặn luôn một lỗi "Xóa lọc" lố mà đổi `toolbar` từ rỗng sang có-giá-trị sẽ gây ra nếu không khai `filtersActive={false}`. Build + lint + test đều xanh.
**Concerns/Blockers:** Không.
