# Phase 05 — Báo cáo Hành chính: Đặt xe · Duyệt đóng dấu · Văn bản · Phê duyệt

## Context links
- Đặt xe: `backend/app/modules/vehicle_booking/model.py:118` (BK_DRAFT=1…BK_RETURNED=8 :21-28, TYPE_CAR=1/TYPE_DELIVERY=2), `vehicle_booking/dashboard_service.py` (`_trend` :76 — đếm từng tháng, KHÔNG dùng lại), scope `scoping.py:107` + nhánh tài xế :519
- Đóng dấu: `seal_request/model.py:42` (SEAL_DRAFT=1…SEAL_RETURNED=7), bảng `tab_seal_request_company`, scope company chỉ thấy APPROVED/COMPLETED (`scoping.py:595-630`), lọc văn thư `tab_seal_clerk`
- Văn bản: `document/model.py:129` (STATUS_DRAFT=1…PENDING_ISSUE=11 :209), `document/query.py:19` (`documents_query`, ép `origin=1`), `document/access_service.py:196` (`visible_condition`), mẫu dùng: `document/dashboard_service._visible`
- Phê duyệt: `approval/instance_model.py` (INSTANCE_RUNNING=1…BLOCKED=6; TASK_WAITING=1…CANCELLED=6), `entity_hooks.register` ở từng `approval_bridge.py`; helper P01 `approval/report_turnaround.py`
- Menu FE: `/vehicle-booking/requests` → `vehicle_booking`; `/approval-seal/requests` → `seal_request`; `/document/documents` KHÔNG entity (phân hệ `document`); `/approval/flows` → `approval_flow`

## Overview
- Priority: P2 · Status: pending · Effort: 9h · Sở hữu: `vehicle_booking/report_*`, `seal_request/report_*`, `document/report_*`, `approval/report_controller.py` + `approval/report_service.py`, `config/report-catalog-admin.ts`, 4 trang FE
- `/overview` hiện có của Đặt xe/Đóng dấu là bảng điều khiển THEO VAI (mine/approve/dispatch…), không lọc đủ theo kỳ, không so sánh → KHÔNG dùng lại; viết `/summary` mới cùng scope với bảng danh sách.

## Key insights
- Nhiều cột ngày của Đặt xe/Đóng dấu là CHUỖI ISO (`start_time`, `approved_at`, `completed_at`) → `range_filter(kind='str')`; `created_at` là DateTime UTC.
- Đóng dấu: người scope `company` (giám đốc, văn thư) CHỈ thấy đề nghị đã duyệt/hoàn tất → số của họ khác số của phòng; đó là đúng luật hiện có, ghi `notes`.
- Đóng dấu nhiều công ty qua bảng nối → chiều "công ty" là nhiều giá trị (khung P01 xử lý, Tổng tính riêng).
- Văn bản: `visible_condition` là biểu thức SQL thuần, dùng thẳng trong truy vấn tổng hợp. Mức mật: chỉ đếm văn bản người xem ĐÃ được thấy → không lộ gì thêm.
- Phê duyệt: instance/task không có `company_id` → scope bằng cách lọc `entity_id` qua truy vấn đã scope của CHÍNH phân hệ chứng từ.

## Báo cáo
### 5.1 Đặt xe
- `GET /api/vehicle-bookings/summary` (+export) · `require('vehicle_booking','read'|'export')` · `apply_scope(VehicleBooking,'vehicle_booking')` · `is_deleted=False` · bỏ `BK_DRAFT`.
- Trường ngày: `start_time` (ngày đi — Q5.1).
- Chỉ số: Yêu cầu, Chuyến hoàn thành (BK_COMPLETED), Tỷ lệ từ chối+hủy % (good down), Tổng km (`distance_km`), Chi phí (`cost`, money), Hành khách, Thời gian duyệt TB (giờ, từ `report_turnaround` entity `vehicle_booking`).
- Xem theo: thời gian · công ty · phòng ban · loại yêu cầu · trạng thái · xe (`assigned_vehicle_id`) · tài xế (`assigned_driver_id`) · người yêu cầu (`requester_id`).
- Breakdowns: theo trạng thái, theo loại.
### 5.2 Duyệt đóng dấu
- `GET /api/seal-requests/summary` (+export) · `require('seal_request',…)` · `apply_scope(SealRequest,'seal_request')` (giữ nguyên luật company/văn thư) · `is_deleted=False` · bỏ SEAL_DRAFT.
- Trường ngày: `created_at` (UTC→VN).
- Chỉ số: Đề nghị, Số bản (`copies`), Đã đóng dấu (SEAL_COMPLETED), Tỷ lệ từ chối % (good down), Thời gian duyệt TB (turnaround), Thời gian duyệt→đóng dấu TB (`approved_at→completed_at`, giờ, good down).
- Xem theo: thời gian · loại dấu (`seal_type_id`) · công ty (bảng nối, nhiều giá trị) · phòng ban · người đề nghị · văn thư (`completed_by`) · trạng thái.
### 5.3 Văn bản
- `GET /api/documents/summary` (+export) · `require('document','read'|'export')` · `documents_query(db).filter(visible_condition(user, profile, 'read'))`.
- Trường ngày: `created_at` (tạo mới); chỉ số "Đã ban hành" dùng `issued_at` trong kỳ (truy vấn phụ cùng điều kiện nhìn thấy) — Q5.2.
- Chỉ số: Tạo mới, Đã ban hành, Chờ duyệt (snapshot SUBMITTED), Hết hạn trong kỳ (`expire_date`), Cần rà soát (snapshot `needs_review`), Thời gian duyệt TB (turnaround entity `document`).
- Xem theo: thời gian · loại văn bản (`doc_type_id`) · nhóm loại (`DocType.group_code`) · công ty ban hành · phòng chủ trì · người soạn (`drafter_employee_id`) · trạng thái · mức khẩn (`urgency`).
- Danh mục FE: entity `document`, `sourcePath=/document/documents` (luật dự phòng P02: mục menu không entity → entity phân hệ). Báo cáo CHẶT hơn nguồn (cần `document.read`) — Q5.3.
### 5.4 Phê duyệt
- `GET /api/approvals/summary` (+export) · `require('approval_flow','read'|'export')` (Q5.4).
- Scope: với mỗi entity đã đăng ký (`document`, `seal_request`, `vehicle_booking`, `leave_request`, `room_booking`) mà người xem `can(entity,'read')`: `instance.entity == e AND instance.entity_id IN (<truy vấn đã scope của e>.with_entities(id))`; văn bản dùng `visible_condition`. Entity không có quyền → loại khỏi phạm vi. Bảng đăng ký nguồn `APPROVAL_REPORT_SOURCES` trong `approval/report_service.py`.
- Trường ngày: `instance.started_at`.
- Chỉ số: Phiên duyệt, Đã duyệt / Từ chối / Trả về / Rút (theo `status`), Đang chờ (snapshot RUNNING+BLOCKED, good down), Thời gian xử lý phiên TB (giờ), Thời gian mỗi bước TB, Tỷ lệ bước quá hạn % (good down).
- Xem theo: thời gian · loại chứng từ (`entity`, nhãn từ `task_notification.ENTITY_LABELS`) · người duyệt (task-level) · bước (`node_name`).
- `sourceIsTable=false` (không có bảng dòng — menu nguồn là cấu hình luồng).

## Related code files
Tạo: `vehicle_booking/report_service.py`, `seal_request/report_service.py`, `document/report_service.py`, `approval/report_service.py`; điền route vào 4 router rỗng P01; `test/backend/test_bao_cao_hanh_chinh.py` (đặt xe + đóng dấu), `test/backend/test_bao_cao_van_ban.py`, `test/backend/test_bao_cao_phe_duyet.py`.
Frontend: `config/report-catalog-admin.ts` (group "Hành chính"), `pages/vehicle-booking-report-page.tsx`, `pages/seal-request-report-page.tsx`, `pages/document-report-page.tsx`, `pages/approval-report-page.tsx`. Route (P02 đã khai): `/report/vehicle-booking`, `/report/seal-request`, `/report/document`, `/report/approval`.

## Implementation steps
1. Mỗi service: `fetch(from,to)` đã scope → `build_report` với spec; nhãn xe/tài xế/loại dấu/loại văn bản tra theo lô.
2. Nối `report_turnaround` bằng subquery id đã scope.
3. `approval/report_service.py`: dựng nguồn theo quyền; test người có `approval_flow.read` nhưng không có `document.read` → không thấy phiên văn bản.
4. FE 4 trang cấu hình + danh mục. 5. Cổng kiểm + pytest 3 tệp mới.

## Test matrix
| Ca | Kỳ vọng |
|---|---|
| Đặt xe scope dept | chỉ phòng mình; tài xế thấy chuyến được giao (nhánh scope có sẵn) |
| Đóng dấu scope company | không đếm DRAFT/PENDING |
| Đóng dấu 2 công ty | mỗi công ty +1, Tổng = 1 |
| Văn bản bị chặn (deny / cá nhân) | không vào bất kỳ số nào |
| Phê duyệt thiếu quyền entity | phiên của entity đó = 0 |
| Bước tuần tự | thời gian bước 2 tính từ lúc bước 1 quyết |

## Success criteria
6 ca trên xanh; `/summary` không bị `/{id}` nuốt; 4 trang hiển thị + Excel.

## Risk assessment
| Rủi ro | K×A | Giảm thiểu |
|---|---|---|
| Lộ văn bản mật qua đếm | TB×Cao | chỉ `visible_condition`; test deny |
| Subquery IN lớn (Phê duyệt) chậm | Thấp×TB | quy mô 20–100 user; trần kỳ 3 năm |
| Chuỗi ngày sai định dạng ở dữ liệu cũ | TB×Thấp | `to_local_date` trả None → bỏ qua, đếm vào `notes` |

## Security considerations
Mọi nguồn dùng đúng chốt của bảng danh sách; Phê duyệt KHÔNG cho xem chứng từ ngoài phạm vi entity gốc.

## Câu hỏi
- Q5.1 Đặt xe tính kỳ theo ngày đi (`start_time`, đề xuất) hay ngày tạo?
- Q5.2 Văn bản: kỳ theo ngày tạo (đề xuất) + chỉ số ban hành theo `issued_at` — đồng ý?
- Q5.3 Người duyệt văn bản không có `document.read` sẽ không thấy báo cáo Văn bản — chấp nhận?
- Q5.4 Báo cáo Phê duyệt gác bằng `approval_flow.read` (thường chỉ quản trị/HCNS) — hay mở cho mọi người có quyền đọc ít nhất một loại chứng từ?
