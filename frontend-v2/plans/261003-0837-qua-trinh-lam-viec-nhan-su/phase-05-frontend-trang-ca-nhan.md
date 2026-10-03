# Phase 05 — Frontend: thẻ «Quá trình công tác» ở Trang cá nhân `/me`

**Ưu tiên:** P2 · **Effort:** 2h · **Trạng thái:** pending · **Phụ thuộc:** 04 (cột, api, hook, hộp tệp)

## Bối cảnh
- `src/app/pages/profile-page.tsx` (333 dòng) — tab «Thông tin cá nhân», khối `myEmployee && (<ProfileHrDetails/> + <ProfileEmergencyContacts/>)` ~dòng 273.
- Khuôn thẻ: `app/components/profile/profile-emergency-contacts.tsx` (+ test), `profile-leave-card.tsx`.
- `app/` được import từ `@/modules/hr/**` (đang làm vậy với `useMyEmployee`, `EmployeePeopleEditor`) — không phải module-nhập-module.

## Thiết kế
- **Thẻ, không phải tab mới**: đặt ngay dưới `ProfileEmergencyContacts` trong tab «Thông tin cá nhân». Lý do: chuỗi đọc `?tab=` của trang đã dài 9 nhánh; quá trình công tác là một phần của hồ sơ, đứng cạnh hồ sơ thì người dùng tìm thấy.
- Chỉ dựng khi `myEmployee` có (tài khoản chưa gắn hồ sơ → không dựng).
- `DataTable` dùng lại `buildEmployeeWorkHistoryColumns()` của phase 04 **không có** cột Thao tác, `storageKey="me.work-history"`. Không nút Thêm/Sửa/Xóa/Áp.
- Cột Tệp: `/me` luôn trả `can_open_files=true` (Q4 — chính chủ luôn mở được tệp của mình, không cần `employee.read` hay `employee_sensitive.read`); bấm mở `EmployeeWorkHistoryFilesDialog` ở chế độ **chỉ xem** (`editable={false}`): xem qua `/view`, tải qua `downloadFile`.
- Dòng Thôi việc hiện như mọi dòng; không có hộp xác nhận nào ở đây (chỉ đọc).
- Rỗng: «Chưa có quá trình công tác nào được ghi. Phòng Nhân sự cập nhật mục này.»
- Dữ liệu: `useMyWorkHistory()` → `GET /api/employees/me/work-history`, khóa `hr.myWorkHistory()`. **Không** gọi `/{eid}/work-history` (người không có `employee.read` sẽ ăn 403).

## Tệp

| Tạo | Sửa |
|---|---|
| `app/components/profile/profile-work-history-card.tsx` | `app/pages/profile-page.tsx` (+import, +1 dòng JSX) |
| `app/components/profile/profile-work-history-card.test.tsx` | |

(`useMyWorkHistory` nằm trong `hr/hooks/use-employee-work-history.ts` — tạo ở phase 04.)

## Test
- Gọi đúng đường `/me/work-history` (mock `@/core/api`), không có id nào trong URL.
- Không có nút Thêm/Sửa/Xóa/Áp vào hồ sơ dù người dùng có `employee.write`.
- Hộp tệp mở ở chế độ chỉ xem: không có vùng thả, không có nút xóa; nút xem/tải CÓ hiện dù người dùng không có `employee_sensitive.read`.
- Danh sách rỗng → câu «Phòng Nhân sự cập nhật mục này».

```bash
docker compose exec -T erp npm run typecheck
docker compose exec -T erp npm run lint
docker compose exec -T erp npx vitest run profile-work-history-card
```

## Todo
- [x] thẻ + gắn vào trang
- [x] test xanh; typecheck + lint 0 lỗi
- [ ] bấm tay: tài khoản DEMONV (không `employee.read`, không sensitive) mở `/me` thấy dòng + mở được tệp QĐ của mình — CHƯA LÀM: đã đối chiếu mã backend thật (phase 02/03 xong) khớp hợp đồng, nhưng chưa bấm qua trình duyệt; xem Concerns trong report

## Thành công khi
Tài khoản không có `employee.read` xem được quá trình + tệp của chính mình; đổi URL/tham số không xem được của người khác (đã khóa ở backend, phase 03).

## Rủi ro / Rollback
Thấp. Gỡ 1 dòng JSX ở `profile-page.tsx` là tắt.
