# Review fixes FE — duoc-CR-717 (03/11/2026)

Gates: host `npm run typecheck` 0 lỗi · host `eslint` trên 83 tệp đã đổi/thêm: 0 lỗi, 0 cảnh báo · container
`vitest run src/modules/hr src/modules/report src/shared/crud src/app/router`: 213 tệp, 2200 bài, 2199 xanh + 1 bài
hết giờ 5s vì máy tải nặng (`report-catalog-hr.test.ts` › nạp component báo cáo đợt 4, chạy riêng thì xanh 17/17).
Chạy lại phần hr/crud/router/report-components sau lượt sửa cuối: 92 tệp / 1124 bài xanh.
Không đụng backend, doc, change-log, nhật ký, `.claude/rules`. Chưa commit.

## Tóm tắt review (người rà không ghi được tệp)
| Mã | Chỗ | Lỗi |
|---|---|---|
| M1 | `leave-balance-policy-note.tsx` | Luôn tra phân bổ HÔM NAY bất kể `balance.year` → giải thích nhầm năm; lỗi API rơi về **không có chính sách** |
| M2 | cùng tệp | Link sang gói hiện với `leave_type.read` nhưng route gói gác quyền quản lý → 403 |
| M3 | `leave-policy-lines-card.tsx` | `<Input type=number>` + `Number('')`=0 → thêm dòng 0 ngày; **12,5** thành rỗng |
| M4 | `shared/crud` bố cục phẳng | Nút Lưu đầu trang chết ở tab khác **Thông tin**; nháp của thẻ dòng mất khi đổi tab |
| M5 | hộp Cấp quỹ + trang hàng loạt | Lọc phòng ban theo `company_id` → rỗng (phòng ban dùng chung) |
| Menu | `routes.tsx` | **Phân bổ chính sách** hiện cho mọi nhân viên (seed cấp `leave_balance.read`) |
| L1 | `use-leave-policy.ts` | Dọn cache không trúng khóa xem trước |
| L2 | `holiday-work-report-filters.tsx` | `?day_kind` sai gửi nguyên lên backend (422) |
| L3 | `leave-policy-assign-dialog.tsx` | `max-h/overflow` trùng với lớp phủ tự cuộn |
| L4 | `leave-policy-assign-preview.tsx` | Lỗi xem trước báo **không tìm thấy nhân sự** |
| L5 | 3 nơi | Chép `FilterSelect` + `toFilterId` |
| L6 | 5 tệp | Tệp > 200 dòng |
| L7 | gói CRUD | Đổi tên / ngừng gói không dọn cache phân bổ |
| L8 | ma trận | **Tổng còn lại** trôi giữa bảng khi đã lưu bố cục |
| L9 | màn Quỹ phép | Hai chủ cho `?q=` |

## Đã sửa
- **M1** `LeaveBalancePolicyNote` nhận `year`; chỉ dựng khi `year` = năm hiện tại theo giờ VN (`todayInVietnamISO`),
  câu **Chính sách đang áp hôm nay: …**; năm khác / đang tải / lỗi API → không dựng gì, không gọi API. `active_on` cũng theo giờ VN.
- **M2** Link chỉ khi `canManageEntity('leave_type', can)`, còn lại chữ đậm.
- **M3** Ô chữ `inputMode=decimal`; `parsePolicyDays` (utils/leave-policy-display) nhận **12,5** / **12.5**, rỗng/rác → **Nhập số ngày (VD 12 hoặc 12,5).**; khoảng 0–366 + bước 0,5 giữ ở `upsertPolicyLine`; gõ lại thì xóa câu lỗi cũ.
- **M4** `CrudDetailFlatLayout` chỉ dựng nút Lưu/Xóa khi tab đầu đang mở (cả link sâu `?tab=`). Nháp tab con:
  `CrudTabDraftProvider` (bọc `CrudDetailPage`, `key` theo `:id`) + `useCrudTabDraft(key)` (ngoài provider rơi về state cục bộ).
  Thẻ dòng gói và thẻ Hạn mức theo nhóm của loại nghỉ (`leave-type-quota-card.tsx`) dùng nó, kèm dấu **Có thay đổi chưa lưu** cạnh nút Lưu riêng.
- **M5** Bỏ `company_id` khi đọc phòng ban ở cả hai nơi; bỏ luôn **đổi pháp nhân thì xóa phòng ban**.
- **Menu** Mục **Phân bổ chính sách** gác `leave_balance` + `action: 'write'` (hàng rào route theo mục); `module-visibility.test.ts` cập nhật
  (chỉ đọc → không thấy, có write → thấy). Tab **Đang phân bổ** của gói chỉ cho bấm dòng khi có `write`.
- **Backend mới**: `PolicyConflict` thêm `'scope'`; hộp một người hiện riêng câu lý do (không vẽ **chính sách hiện tại**), nút Phân bổ khóa;
  bảng hàng loạt khóa ô chọn, tên rỗng → **Nhân sự #id**. `skipped.reason` hiện nguyên. Dòng của chính người đăng nhập
  (`user.employee_id`) không có nút Kết thúc/Xóa, thay bằng **Của bạn — nhờ người khác sửa** (khóa thừa cả admin vì FE không biết ai là admin
  nếu không nạp danh mục vai trò). 403/404 khác: toast lỗi chung của http client hiện câu backend.
- **L1** Khóa gốc `queryKeys.hr.leavePolicyAssignmentsRoot`, dọn bằng nó. **L2** `day_kind` sai → hiện mặc định và gỡ khỏi URL.
  **L3** bỏ `max-h/overflow`. **L4** `isError` → **Không tính thử được…**. **L5** `EmployeeFilterSelect` + `utils/employee-filter-id.ts`
  (`FILTER_ANY`, `toFilterId`); `BULK_ANY` bỏ. **L7** `CrudConfig.alsoInvalidate` nhận thêm khóa query thô (mảng); gói khai gốc phân bổ.
  **L8** cột Tổng `stickyRight`. **L9** màn cha giữ `useUrlSearchParam`, truyền `search` xuống hai thẻ.
- **L6** `leave-balance-page.tsx` 444 → 103 (+ `leave-balance-rows-table.tsx`, `leave-balance-page-actions.tsx`); matrix 205 → 154
  (+ `leave-balance-matrix-filters.tsx`, `utils/leave-balance-matrix-filters.ts`); assign dialog 222 → 154 (+ `leave-policy-assign-fields.tsx`);
  list page 201 → 163 (+ `leave-policy-assignment-list-toolbar.tsx`, `-row-actions.tsx`, `utils/leave-policy-assignment-filters.ts`);
  allocate dialog 208 → 164. `routes.tsx` để nguyên.

## Bài kiểm mới / sửa
policy-note (năm khác, lỗi API, giờ VN 31/12, link theo quyền quản lý) · lines-card (rỗng, **12,5**, nháp sống qua unmount) ·
leave-policy-display (`parsePolicyDays`) · employee-filter-id · allocate dialog (phòng ban sau khi chọn pháp nhân) ·
crud-detail-page (bố cục phẳng ẩn nút đầu trang) · matrix (Tổng cuối dù bố cục lưu) · list page (dòng của mình) ·
holiday-work filters (gỡ `day_kind` sai) · module-visibility.

## Trình duyệt (localhost:8083, admin, 1440 + 390)
Tạo gói thử → tab **Loại nghỉ & số ngày**: không có Lưu/Xóa đầu trang; thêm **12,5** → sang **Thông tin** (Lưu/Xóa hiện) → quay lại còn dòng
12,5 + **Có thay đổi chưa lưu**; ô rỗng → **Nhập số ngày**; Lưu số ngày xong dấu tắt. Hộp Cấp quỹ: chọn pháp nhân → phòng ban 18 mục.
Ma trận: Tổng còn lại cột cuối; `?q=` giữ khi đổi thẻ. 390px màn Quỹ phép năm hiển thị đúng. Gói thử đã xóa.

## Còn hở
- Bố cục CRUD cũ (không phẳng) vẫn có nút Lưu đầu trang chết ở tab con — ngoài phạm vi quyết định (chỉ flat).
- Dòng của chính mình khóa cả với quản trị hệ thống (FE không biết admin) — admin muốn tự sửa phải nhờ người khác.
- `day_kind` sai vẫn có thể bắn MỘT lượt 422 trước khi effect gỡ URL.

**Status:** DONE_WITH_CONCERNS
**Summary:** Sửa đủ M1–M5, menu, L1–L9 và khớp hành vi backend mới (`conflict:"scope"`, chặn tự sửa); typecheck/lint 0 lỗi, vitest xanh (1 bài hết giờ do tải, chạy riêng xanh).
