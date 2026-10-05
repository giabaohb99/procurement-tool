# Phase 04 — Frontend: màn «Mẫu lịch tuần» + «Gán lịch»

## Context links
- `frontend-v2/.claude/rules/*.md` (components, styling, icons, naming, typescript, testing)
- Mẫu: `modules/hr/config/holiday-crud.tsx`, `pages/holiday-{list,detail}-page.tsx`, `config/leave-type-crud.tsx`
- Khung: `shared/crud/types.ts` (`type:'custom'` + `render({control,name,disabled})`, `formFields` dạng HÀM,
  `openFormOnRowClick`, `createRoute`), mẫu ô custom: `modules/dossier/utils/dossier-form-fields.ts`
- Gác route theo tiền tố: `app/router/module-visibility.ts canAccessRoute` (memory: route thiếu mục menu = MỞ)
- Hợp đồng API: phase 2 §API. Bộ mã: `shared/constants/statuses.ts` (`WORK_DAY_KIND`, `WORK_SCHEDULE_LEVEL` — sinh ở phase 1)

## Overview
Priority P2 · Status done (06/10/2026, 3 cổng xanh; chưa bấm tay trên trình duyệt) · 9h. Hai màn danh mục dựng trên `shared/crud`, KHÔNG viết api/hook riêng
(khóa cache `['crud', apiPath]` của lớp CRUD lo invalidation).

## Key insights
- `routes.tsx` đã 379 dòng → tách mục menu + route lịch làm việc ra `config/work-schedule-module-entries.tsx`,
  `routes.tsx` chỉ thêm 1 import + 2 dấu spread.
- Đường gán `/hr/work-schedule-assignments` KHÔNG là con tiền tố của `/hr/work-schedules` → hai mục menu gác độc lập.
- Đổi «Cấp áp dụng» mà giữ `target_id` cũ = gán nhầm đích (NV #12 thành pháp nhân #12). Ô đích là ô CUSTOM
  tự xóa giá trị khi cấp đổi; backend vẫn kiểm đích có thật.
- Giờ từ backend dạng `"08:00:00"`; `<Input type="time">` cần `"HH:MM"` → chuẩn hóa ở util.
- Số nguyên bộ mã cho NHÁNH logic khai hằng nhỏ ở `types/work-schedule.ts`; NHÃN/OPTIONS lấy từ `statuses.ts`
  (không gõ tay danh sách nhãn). Test chốt hằng khớp `statuses.ts`.

## Architecture / UI
**Menu** (nhóm «Danh mục», sau «Nghỉ phép»): «Lịch làm việc» (icon `CalendarClock`, `entities:['work_schedule']`,
`manage: true`) với 2 con: «Mẫu lịch tuần» → `/hr/work-schedules`, «Gán lịch» → `/hr/work-schedule-assignments`
(cả hai `entity:'work_schedule', manage:true`). Người chỉ có read không thấy menu (cùng luật «Chức vụ»).

**Mẫu lịch tuần** — `WORK_SCHEDULE_CRUD_CONFIG` (apiPath `/api/work-schedules`, `createRoute` trang riêng vì form dài)
- Cột: Tên · Tóm tắt tuần (`summarizeWeek`: «T2–T6 08:00–17:00 · T7 sáng · CN nghỉ») · Công/tuần (5,5) · Đang gán (n nơi) · Trạng thái.
- Form: `name`, `note` (textarea), `is_active` (switch), `days` (`type:'custom'`, fullWidth) → `WorkScheduleWeekEditor`.
- `deleteWarning`; hint trên ô `days` khi `assignment_count>0`: «Mẫu đang gán n nơi — sửa giờ sẽ đổi số ngày GỢI Ý
  của mọi đơn nhập sau, kể cả đơn lùi ngày. Đổi lịch từ một ngày cụ thể thì tạo mẫu mới rồi gán kèm ngày hiệu lực.»

**Bảng 7 ngày** — `WorkScheduleWeekEditor` (`useController` trên `days`, KHÔNG giữ state riêng)
- 7 hàng T2..CN: Thứ · Loại ngày (Select từ `WORK_DAY_KIND`) · Giờ vào · Giờ ra · Nghỉ trưa từ · đến · Công (1 / 0,5 / 0).
- OFF → ẩn/khóa 4 ô giờ và xóa giá trị; MORNING/AFTERNOON → khóa ô trưa và xóa giá trị; đổi sang FULL từ OFF → điền 08:00–17:00 / 12:00–13:00.
- Nút phụ «Chép T2 xuống T3–T6». Dòng cuối: «Tổng: 5,5 ngày công/tuần». Khổ hẹp: mỗi ngày một thẻ (không bảng ngang).
- `disabled` → mọi ô chỉ xem. Lỗi backend 422 hiện toast chung của khung CRUD (luật thật ở backend).

**Gán lịch** — `WORK_SCHEDULE_ASSIGNMENT_CRUD_CONFIG` (apiPath `/api/work-schedule-assignments`, hộp thoại, `openFormOnRowClick: true`)
- Cột: Cấp áp dụng · Đối tượng (`target_name`; SYSTEM → «Toàn công ty») · Mẫu lịch · Từ ngày · Đến ngày («Không thời hạn») · Đang hiệu lực (badge) · Ghi chú.
- Lọc nhanh: Cấp áp dụng, Mẫu lịch.
- Form: `target_level` (select từ `WORK_SCHEDULE_LEVEL`) · `target_id` (`type:'custom'` → `WorkScheduleTargetField`:
  SYSTEM → ẩn + ép 0; COMPANY → `/api/companies`; DEPARTMENT → `/api/departments`; EMPLOYEE → `SearchSelect` `/api/employees`;
  `useWatch(target_level)` + reset khi đổi) · `schedule_id` (select `/api/work-schedules?is_active=true`) ·
  `effective_from` (date, required) · `effective_to` (date, `nullWhenEmpty`) · `note`.
- Hint dưới khung: «Hẹp thắng rộng: Nhân sự > Phòng ban > Pháp nhân > Toàn công ty. Chưa gán gì → T2–T7, 08:00–17:00.»

## Related code files (sở hữu phase 4 — phase 5 không đụng)
**Create** (`frontend-v2/src/modules/hr/`)
- `types/work-schedule.ts` — `WorkScheduleDay`, `WorkSchedule`, `WorkScheduleAssignment`, `EffectiveWorkSchedule`, hằng `WORK_DAY_KIND_CODE`, `WORK_SCHEDULE_LEVEL_CODE`
- `utils/work-schedule-week.ts` + `.test.ts` — `buildDefaultWeek`, `normalizeDayOnKindChange`, `toTimeInput`, `dayCredit`, `sumWeeklyWorkdays`, `summarizeWeek`
- `components/work-schedule-week-editor.tsx` + `work-schedule-week-editor-row.tsx` + `work-schedule-week-editor.test.tsx`
- `components/work-schedule-target-field.tsx` + `.test.tsx`
- `config/work-schedule-crud.tsx` · `config/work-schedule-assignment-crud.tsx`
- `config/work-schedule-module-entries.tsx` — export `workScheduleNavItem`, `workScheduleRoutes`
- `pages/work-schedule-list-page.tsx` · `pages/work-schedule-detail-page.tsx` · `pages/work-schedule-assignment-list-page.tsx`

**Modify**
- `src/modules/hr/routes.tsx` (import + spread)
- `src/shared/constants/app-routes.ts` (`workSchedules`, `workScheduleNew`, `workScheduleDetail(id)`, `workScheduleAssignments`)
- `src/modules/system/config/permission-groups.ts` (`'work_schedule'` vào nhóm `hr`)
- `src/app/router/module-visibility.test.ts` (ca gác mới)

## Implementation steps
1. Types + util + test util (hàm thuần trước — rẻ, chỗ sai âm thầm).
2. Week editor (+row) + test; target field + test.
3. Hai CrudConfig + 3 trang; app-routes; module-entries; nối routes.tsx; permission-groups.
4. Ca gác trong `module-visibility.test.ts`.
5. Cổng: `npm run typecheck` · `npm run lint` · `npx vitest run src/modules/hr src/app/router src/modules/system/config`.
6. Bấm thử trên `http://localhost:8083` (khổ máy tính + khổ điện thoại bằng emulate, không resize — memory).

## Test matrix (vitest, khẳng định theo vai trò/nội dung)
| Tệp | Ca cực đoan |
|---|---|
| `work-schedule-week.test.ts` | `summarizeWeek` gom T2–T6 liền nhau nhưng KHÔNG gom T2,T4 cách quãng; giờ khác nhau cắt nhóm; toàn OFF → «Nghỉ cả tuần»; mảng rỗng / thiếu ngày / thứ tự xáo trộn; `toTimeInput` với `"08:00:00"`, `"8:00"`, `null`, `""`; `sumWeeklyWorkdays` 5.5, 0, 7; `normalizeDayOnKindChange` OFF xóa giờ, MORNING xóa trưa; hằng `*_CODE` khớp `statuses.ts` |
| `work-schedule-week-editor.test.tsx` | chọn «Nghỉ» → ô giờ biến mất/khóa và giá trị gửi lên là null; «Chỉ buổi sáng» → ô trưa khóa; tổng công cập nhật 6 → 5,5; `disabled` → không ô nào sửa được; «Chép T2» không đè CN |
| `work-schedule-target-field.test.tsx` | đổi cấp EMPLOYEE→COMPANY → `target_id` về rỗng (lỗi «gán nhầm đích»); SYSTEM → không có ô chọn, giá trị 0; nguồn API rỗng (mock `@/core/api`) → hiện trạng thái rỗng, không nổ |
| `module-visibility.test.ts` | `/hr/work-schedules`, `/hr/work-schedules/new`, `/hr/work-schedules/5`, `/hr/work-schedule-assignments`: `write` → vào; chỉ `read` → không; `{}` → không; quyền `holiday` → không |

## Todo
- [x] types + util + test  - [x] editor + target field + test  - [x] crud configs + pages + routes  - [x] gác + 3 cổng

## Success criteria
3 cổng xanh; HR tạo mẫu T2–T6 + sáng T7 hiển thị «5,5»; gán theo phòng ban hiện tên phòng; người chỉ read không thấy menu.

## Risk assessment
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| `CrudDetailPage` không truyền mảng `days` đúng dạng khi sửa | TB × TB | Test editor nhận `defaultValue` từ bản ghi; `buildPayload` chỉ chuẩn hóa giờ "HH:MM" |
| Ô chọn NV 1000 dòng chậm | Thấp × Thấp | ~100 NV; dùng `SearchSelect` |
| `routes.tsx` vượt 400 dòng | Cao nếu chép thẳng | Tách module-entries |

## Security
Gác hiển thị bằng `manage: true`; chốt thật ở backend `require`.

## Next steps
Phase 5 dùng `types/work-schedule.ts` + `utils/work-schedule-week.ts` (chỉ đọc).

## Câu hỏi mở
- Có cần hiển thị lịch (T7 nửa ngày) lên màn «Lịch nghỉ» (`calendar-grid.isWeekend` đang chỉ tô CN)? Plan: CHƯA làm.
