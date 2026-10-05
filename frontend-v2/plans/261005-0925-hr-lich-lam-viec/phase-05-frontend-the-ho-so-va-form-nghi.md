# Phase 05 — Frontend: thẻ «Lịch làm việc» trên hồ sơ + chữ ở form nghỉ phép

## Context links
- `modules/hr/pages/employee-detail-page.tsx` (420 dòng — chỉ chèn 1 import + 1 phần tử ở tab `leave`)
- `modules/hr/components/employee-tab-leave.tsx` (khuôn thẻ: `Card` + `SectionHeading`, khổ hẹp `dl` có viền)
- Chữ cứng cần sửa: `components/leave-request-form.tsx:287`, `components/leave-request-lines-editor.tsx:233`,
  `config/leave-type-crud.tsx:322-329`, `types/leave.ts:64-72` (`WORK_HOURS_PER_DAY`, `WORK_DAY_LABEL`)
- API: phase 2 `EffectiveOut`; phase 3 `estimate-days` → `{total_days, schedule_name}`

## Overview
Priority P2 · Status done (06/10/2026, 3 cổng xanh; chưa bấm tay trên trình duyệt) · 3.5h. Hai việc nhỏ: (a) cho người xem hồ sơ biết NV này đang theo lịch nào,
lấy từ đâu; (b) bỏ mọi câu chữ khẳng định «chỉ trừ Chủ nhật / 8 giờ» vì nay sai với người có lịch riêng.

## Key insights
- Thẻ gác bằng chính quyền đọc hồ sơ (`employee.read`, backend `get_scoped`) — KHÔNG cần `work_schedule.read`,
  nên trên prod vai trò cũ thấy ngay mà không phải tick thêm.
- Query key mới ở `query-keys.ts` (`hr.workScheduleEffective(employeeId)`). Không bị invalidate khi HR sửa gán
  (khóa CRUD khác gốc) — chấp nhận: hai màn khác nhau, query refetch khi mount.
- `schedule_name` là trường TÙY CHỌN ở FE (`?:`) → FE chạy được kể cả khi phase 3 chưa deploy.

## Architecture / UI
**`EmployeeWorkScheduleCard`** (đặt dưới `EmployeeTabLeave` trong `TabsContent value="leave"`):
- Tiêu đề «Lịch làm việc»; dòng tên mẫu + badge nguồn: «Gán riêng» / «Theo phòng ban: Kế toán» /
  «Theo pháp nhân: …» / «Toàn công ty» / «Mặc định hệ thống».
- Hiệu lực: «Từ 01/11/2026 · Không thời hạn».
- 7 ô T2..CN (chip): «08:00–17:00», «Sáng», «Nghỉ» + «5,5 ngày công/tuần» (dùng `utils/work-schedule-week.ts` của phase 4).
- `can('work_schedule','write')` → nút «Gán lịch» (link `appRoutes.hr.workScheduleAssignments`). Đang tải → `Skeleton`;
  lỗi → câu ngắn, không toast (thẻ phụ, không chặn hồ sơ).

**Form nghỉ phép**
- Hint theo giờ: «Nghỉ theo giờ quy đổi theo giờ làm của lịch «{schedule_name}», đã trừ giờ nghỉ trưa…»;
  chưa có `schedule_name` → «…theo lịch làm việc áp cho người nghỉ…».
- Lines editor: «…{n} ngày công (đã trừ ngày nghỉ theo lịch làm việc và ngày lễ).»
- Loại nghỉ: nhãn `exclude_holiday` → «Trừ ngày nghỉ theo lịch làm việc và ngày lễ»; hint → «Tắt cho loại nghỉ dài
  liên tục (thai sản) — khi đó đếm cả ngày nghỉ tuần.»
- Xóa `WORK_HOURS_PER_DAY`, `WORK_DAY_LABEL` khỏi `types/leave.ts` (grep: chỉ form dùng).

## Related code files (sở hữu phase 5)
**Create** (`frontend-v2/src/modules/hr/`)
- `api/work-schedule-api.ts` — `getEffectiveWorkSchedule(employeeId, onDate?)` qua `apiGet` (`/api/work-schedules/tools/effective`)
- `hooks/use-effective-work-schedule.ts`
- `components/employee-work-schedule-card.tsx` + `.test.tsx`

**Modify**
- `src/shared/constants/query-keys.ts` (+1 khóa dưới `hr`)
- `src/modules/hr/pages/employee-detail-page.tsx` (tab leave)
- `src/modules/hr/components/leave-request-form.tsx` · `leave-request-lines-editor.tsx`
- `src/modules/hr/config/leave-type-crud.tsx` · `src/modules/hr/types/leave.ts` · `src/modules/hr/api/leave-api.ts` (kiểu trả `schedule_name?: string`)

**Chỉ đọc** (của phase 4): `types/work-schedule.ts`, `utils/work-schedule-week.ts`.

## Implementation steps
1. api + hook + query key.
2. Thẻ + test (mock `@/core/api`).
3. Chèn thẻ vào trang hồ sơ.
4. Sửa 4 chỗ chữ + bỏ 2 hằng; `grep -rn "WORK_DAY_LABEL\|Chủ nhật và ngày lễ\|thứ Bảy vẫn tính" src` → 0.
5. Cổng: typecheck · lint · `npx vitest run src/modules/hr`.

## Test matrix — `employee-work-schedule-card.test.tsx`
| Ca | Kỳ vọng |
|---|---|
| `is_fallback=true` | hiện «Mặc định hệ thống», KHÔNG hiện ngày hiệu lực |
| gán theo phòng ban, `effective_to=null` | «Theo phòng ban: Kế toán», «Không thời hạn» |
| T7 MORNING | chip T7 «Sáng», tổng «5,5» |
| `days` rỗng / thiếu thứ (backend lỗi) | không nổ, chip thiếu hiện «—» |
| API 404 (ngoài phạm vi) | câu báo ngắn, không nút |
| không có `work_schedule.write` | không có nút «Gán lịch» |
| `employeeId = 0` | không gọi API |

## Todo
- [x] api/hook/key  - [x] thẻ + test  - [x] chèn hồ sơ  - [x] sửa chữ form + bỏ hằng  - [x] 3 cổng

## Success criteria
Hồ sơ NV hiện đúng lịch + nguồn; form nghỉ không còn câu «chỉ trừ Chủ nhật»; 3 cổng xanh.

## Risk assessment
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| Đụng `employee-detail-page.tsx` cùng lúc người khác sửa | TB × Thấp | Sửa 2 dòng, `git fetch` trước |
| Bỏ hằng làm vỡ import ở chỗ khác | Thấp × Thấp | typecheck bắt |

## Security
Không dữ liệu nhạy cảm; backend gác phạm vi nhân sự.

## Next steps
Phase 6 tài liệu.
