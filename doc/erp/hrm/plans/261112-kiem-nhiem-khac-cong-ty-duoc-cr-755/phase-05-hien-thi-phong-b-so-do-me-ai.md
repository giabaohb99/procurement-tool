# Phase 05 — Hiển thị ở phòng B: chi tiết phòng ban, sơ đồ tổ chức, /me, popup phạm vi, trợ lý AI

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 12/11/2026 | fullstack-developer | Nháp | duoc-CR-755 |

## Context links
- [plan.md](plan.md) quyết định 4, Q1, Q5; [phase-02](phase-02-be-pham-vi-theo-cap.md) `concurrent_row_scope_condition`.
- `employee/org_chart_controller.py:52-120`, `auth/controller.py:85-122` (`kiem_nhiem`), `assistant/tools/employee_tool.py:50`
  (`_OUT_FIELDS`), `frontend-v2/src/modules/hr/components/department-members-table.tsx`, `pages/department-detail-page.tsx:361`,
  `components/org-chart-*.tsx`, `pages/org-chart-page.tsx`, `app/components/profile/profile-info-card.tsx`,
  `modules/system/components/user-scope-dialog.tsx` (+ test), `core/auth/auth-types.ts`.

## Overview
P2. Trưởng phòng / người xem phòng ở công ty B thấy người kiêm nhiệm của phòng mình, gắn nhãn **Kiêm nhiệm**, ở trang chi tiết
phòng ban và sơ đồ tổ chức. Báo cáo không đổi. Trang cá nhân + popup phạm vi + trợ lý AI nói đúng phòng và công ty kiêm nhiệm.

## Key insights
- Ai thấy dòng nào = `concurrent_row_scope_condition` (phase 02): phạm vi `employee.read` của người xem áp lên (phòng, công ty)
  của dòng. Không cần khóa quyền mới, không đổi phạm vi đọc HỒ SƠ.
- Chốt Q1 = CÓ: người xem có phạm vi `dept`/`company` phủ cặp của dòng hiệu lực + bật công tắc mở được HỒ SƠ ĐẦY ĐỦ. Cách làm:
  bật `include_concurrent=True` (phase 02) ở MỌI đường ĐỌC hồ sơ `/api/employees/{eid}` và các tab con của nó; danh sách
  `/api/employees`, xuất tệp, báo cáo, truy vấn gốc sơ đồ giữ TẮT (Q5 + không đếm trùng). Hai tab mang khóa quyền khác
  (Hợp đồng = `labor_contract`, Quỹ phép = `leave_balance`) vẫn theo phạm vi riêng của chúng — không mở theo Q1.
- Bảng kiêm nhiệm ở trang phòng ban vẫn là dòng tóm tắt (mã, họ tên, chức vụ kiêm nhiệm, từ/đến ngày, trạng thái, công ty +
  phòng chính; không điện thoại, email, ngày sinh); `can_open` = hồ sơ đọc được theo phạm vi CÓ nhánh Q1 (một truy vấn
  `apply_scope(..., include_concurrent=True)` trên tập id) → dòng bật công tắc thường mở được, dòng tắt công tắc chỉ xem tên.
- Bảng thành viên phòng phân trang ở máy chủ — KHÔNG trộn người kiêm nhiệm vào cùng trang (xếp lại một trang là nói dối thứ tự,
  luật §8). Làm bảng thứ hai **Kiêm nhiệm tại phòng này** ngay dưới, nạp đủ (≤ 200 dòng, trần ở backend).
- Báo cáo quân số / quỹ lương / cơ cấu đọc `Employee.company_id/department_id` → không đếm trùng; chỉ thêm bài canh.

## Requirements
Backend:
- Đường đọc hồ sơ bật `include_concurrent=True` (chỉ `read`): `employee/controller.py` (`get_employee`, `_employee_in_scope`
  khi `action == "read"`, `pending-work`, `contacts`, `families`, `departments`), `work_history_access.employee_in_scope`
  (đọc QTCT, quyết định, tệp QĐ chế độ đọc), `concurrent_controller.py` (GET danh sách kiêm nhiệm), đọc ảnh CCCD nếu đi qua
  `get_scoped`. Đường ghi, `set-password`, ảnh đại diện / chữ ký (ghi) KHÔNG bật. Liệt kê đủ bằng grep `get_scoped(` +
  `_employee_in_scope(` trong `modules/employee/`.
- `GET /api/employee-concurrents?department_id=&company_id=&include_ended=0` (`employee.read`; `department_id` bắt buộc;
  `company_id` tùy chọn — trang phòng dùng chung gửi kèm khi đang lọc theo công ty). Trả dòng hiệu lực (+ sắp tới) của nhân sự
  đang làm, lọc `concurrent_row_scope_condition`, trần 200, xếp theo họ tên + id. Đặt đường riêng (không lồng
  `/api/employees/...`) để khỏi đụng thứ tự route `/{eid}`.
- `GET /api/org-chart`: thêm khóa `concurrents` = `[{employee_id, code, full_name, department_id, company_id, position_label}]`
  dòng hiệu lực, cùng bộ lọc trên, chỉ nhân sự đang làm; phòng của dòng được thêm vào tập phòng cần vẽ (kèm chuỗi phòng cha).
  Thêm đúng một truy vấn, không theo số phòng.
- `/api/auth/me`: `kiem_nhiem` thành chuỗi *Phòng X — Công ty B (Chức vụ)* cho dòng hiệu lực (cả cùng và khác công ty); thêm
  `concurrents` có cấu trúc `{department_id, company_id, department_name, company_name, position_label, counts_scope}` cho popup.
- Trợ lý AI `employee_lookup`: thêm trường `concurrent_roles` (chuỗi như `/me`) vào bản ghi đã được phép xem; KHÔNG đổi bộ lọc
  (vẫn theo phạm vi hồ sơ). Kiểm sổ công cụ AI / bài canh `_OUT_FIELDS` (trường mới không nhạy cảm).
Frontend:
- `department-detail-page`: dưới `DepartmentMembersTable` thêm `DepartmentConcurrentMembersTable` (Mã · Họ tên + huy hiệu
  **Kiêm nhiệm** · Chức vụ kiêm nhiệm · Công ty kiêm nhiệm · Từ – đến · Thuộc phòng chính); tên chỉ là liên kết khi `can_open`.
  Ẩn cả khối khi rỗng.
- Sơ đồ tổ chức: thẻ người kiêm nhiệm trong nút phòng, viền nét đứt + huy hiệu **Kiêm nhiệm**, popover ghi phòng + công ty chính;
  không vẽ cạnh quản lý trực tiếp cho thẻ kiêm nhiệm (cạnh đó thuộc vị trí chính).
- Trang cá nhân: hiện danh sách kiêm nhiệm mới. Popup phạm vi (`user-scope-dialog`, bao-CR-430): liệt kê cặp có **Tính phạm vi**
  dạng *Phòng X (Công ty B)*, dòng tắt công tắc không liệt kê.

## Architecture
```
DepartmentDetailPage ─ DepartmentMembersTable (cũ, primary)        GET /api/employees?department_id=X
                     └ DepartmentConcurrentMembersTable (mới)      GET /api/employee-concurrents?department_id=X
OrgChartPage ─ /api/org-chart {departments, employees, concurrents(mới)}
ProfileInfoCard, UserScopeDialog ─ /api/auth/me {kiem_nhiem, concurrents(mới)}
```

## Related code files
Backend tạo: `backend/app/modules/employee/concurrent_members_controller.py`; sửa: `employee/org_chart_controller.py`,
`employee/controller.py` (chỉ bật cờ ở đường đọc), `employee/work_history_access.py`, `employee/concurrent_controller.py`
(GET), `employee/contact_service.py` nếu tự gọi `get_scoped`, `auth/controller.py`, `assistant/tools/employee_tool.py`, `main.py` (gắn router), bài kiểm
`test/backend/test_me_payload_vai_tro_kiem_nhiem.py`; tạo `test/backend/test_kiem_nhiem_khac_cong_ty_hien_thi_cr755.py`.
Frontend tạo: `modules/hr/api/concurrent-members-api.ts`, `hooks/use-concurrent-members.ts`,
`components/department-concurrent-members-table.tsx` (+ test), sửa: `pages/department-detail-page.tsx`, `pages/org-chart-page.tsx`,
`components/org-chart-*.tsx` (đúng tệp cần), `app/components/profile/profile-info-card.tsx`, `core/auth/auth-types.ts`,
`modules/system/components/user-scope-dialog.tsx` (+ test), kiểu sơ đồ tổ chức trong `modules/hr/types/`.
Đọc, không sửa: `modules/hr/types/employee-concurrent.ts` (phase 04).

## Implementation steps
1. Backend đường danh sách + org chart + `/me` + AI; bài kiểm.
2. Frontend bảng phòng ban, sơ đồ, trang cá nhân, popup; vitest.
3. Cổng backend đúng tệp; frontend `npx tsc --noEmit` (host), lint, `npx vitest run src/modules/hr src/modules/system src/app/components/profile`.

## Todo
- [x] `GET /api/employee-concurrents` + trần + xếp
- [x] `concurrents` trong org chart
- [x] `/me` + AI `concurrent_roles`
- [x] Bảng kiêm nhiệm ở trang phòng ban
- [x] Thẻ kiêm nhiệm ở sơ đồ
- [x] Trang cá nhân + popup phạm vi
- [x] Bài kiểm hai phía

## Success criteria
`pytest test/backend/test_kiem_nhiem_khac_cong_ty_hien_thi_cr755.py test/backend/test_me_payload_vai_tro_kiem_nhiem.py
-q --timeout=120` + bài báo cáo nhân sự liên quan (`-k "headcount or quan_so or quy_luong or co_cau"`) xanh. Phủ:
trưởng phòng (X, B) thấy A trong danh sách kiêm nhiệm, `can_open = true` khi dòng bật công tắc, `false` khi tắt; người (Y, B)
không thấy; **canh Q1**: với trưởng phòng (X, B), gọi lần lượt mọi đường `GET /api/employees/{A}/...` đọc hồ sơ (soi
`app.routes`, bỏ đường ghi) → 200; tắt công tắc / dòng hết hạn → 404 hết; `PATCH /api/employees/{A}` → 404; `GET
/api/employees` (không lọc và lọc `department_id=X`) KHÔNG có A; nhạy cảm che khi thiếu `employee_sensitive.read`, lương luôn che;
dòng hết hạn không hiện; phản hồi không chứa điện thoại/email/ngày sinh; sơ đồ có A ở nút X với `concurrents`, số truy vấn sơ
đồ cố định; báo cáo quân số phòng X ở B KHÔNG đếm A, phòng chính của A vẫn đếm A đúng một lần; `/me` liệt kê cặp khác công ty.
Frontend: typecheck/lint 0 lỗi, vitest các thư mục trên xanh.

## Risks
| Rủi ro | Khả năng × Tác động | Giảm thiểu |
|---|---|---|
| Lộ thông tin liên lạc người công ty khác | Trung × Trung | Danh sách trắng trường ở serializer; bài kiểm soi khóa |
| Sơ đồ vẽ trùng người (chính + kiêm nhiệm cùng nút) | Thấp × Thấp | Bỏ dòng kiêm nhiệm trùng phòng chính + công ty chính |
| Sót một đường đọc tab hồ sơ chưa bật cờ | Trung × Thấp | Bài canh soi `app.routes` (thiếu quyền, không lộ) |
| Bật nhầm cờ ở đường ghi / danh sách | Thấp × Trung | Phase 02 bỏ qua cờ khi `action != read`; bài canh PATCH + danh sách |

## Security
- Q1 mở ĐỌC hồ sơ đầy đủ đúng cặp, không mở sửa; danh sách / báo cáo / xuất không đổi. Nhạy cảm theo `employee_sensitive`,
  lương chỉ chính chủ. Đường mới gác `employee.read` + điều kiện phạm vi trên từng dòng.
- `org_chart_visible_to_all` TẮT → vẫn 403 như cũ trước khi tới phần kiêm nhiệm.

## Next steps
Phase 06.
