# ĐẶT PHÒNG HỌP — duoc-CR-279

Bản 1.0 · 04/09/2026 · nhánh `erp-v2`

## Chốt trước khi làm (khách trả lời 04/09)

| Câu | Chốt |
|---|---|
| Có duyệt không | **Có** — chạy qua bộ máy duyệt dùng chung, như Đặt xe / Nghỉ phép |
| Nằm ở đâu | **Phân hệ Nhân sự**, một mục menu riêng (khuôn `LeaveSectionTabs`) |
| Phạm vi đợt này | **Backend + giao diện đầy đủ** (danh mục phòng · lịch đặt · phiếu đặt) |
| Lấy thêm | **Mời người tham dự** (kèm thông báo). KHÔNG làm: đặt lặp hằng tuần, thiết bị kèm phòng |

## Vì sao không có tài liệu yêu cầu

Rà cả `doc/` ngày 04/09: không có bản đặc tả nào cho đặt phòng họp. Chỗ duy nhất
nhắc tới là `doc/erp/tham-khao-hrm/07-workspace-tai-san.md` §WS2 — khảo sát HRM
đối thủ, ở đó đặt phòng **gộp vào form Lịch biểu** (một thao tác tạo lịch họp có
luôn phòng + người dự + nhắc trước). Bản này **tách phiếu đặt phòng riêng**, vì:

- phòng là **tài nguyên có hạn** nên phải có chốt chặn trùng và người duyệt;
  lịch họp cá nhân thì không cần cả hai;
- ta chưa có phân hệ Lịch biểu, dựng nó chỉ để đặt phòng là làm ngược thứ tự.

Mời người tham dự vẫn giữ (khách chọn) nhưng chỉ là **danh sách + thông báo**,
không phải lịch biểu có xác nhận tham dự.

## Khuôn bám theo

| Việc | Bám tệp nào |
|---|---|
| Bộ mã số (R2/QĐ-11) | `leave/constants.py`, `vehicle_booking/model.py` |
| Nối bộ máy duyệt (4 kết cục) | `leave/approval_bridge.py` |
| Bảng con nhiều người | `leave/request_model.LeaveHandover` |
| Controller hai trục quyền | `leave/request_controller.py` |
| Danh mục khai báo (FE) | `CrudConfig` + `createRoute` (duoc-CR-277) |
| Lịch ngày/tuần (FE) | `hr/utils/calendar-grid.ts` (duoc-CR-278) |
| Thanh tab của cụm màn (FE) | `hr/components/leave-section-tabs.tsx` |

## Luật lõi — CHẶN TRÙNG

Một phòng, hai phiếu **giao nhau về thời gian** (`start < other.end AND end >
other.start`) mà cả hai còn sống thì phòng bị đặt đôi. "Còn sống" =
`BLOCKING_STATUSES = (Chờ duyệt, Đã duyệt)` — **phải tính cả phiếu chờ duyệt**,
không thì hai người cùng gửi duyệt một khung giờ và người duyệt mới là người
phát hiện ra.

Kiểm ở **ba** chỗ, cố ý không gộp:

1. **Gửi duyệt** — chốt chính, báo rõ ai đang giữ và khung giờ nào.
2. **Trước khi hook `on_approved` chốt** — phòng vệ cho trường hợp dữ liệu bị
   sửa tay hoặc phiếu cũ được khôi phục.
3. **Lưu nháp: KHÔNG chặn**, chỉ trả cảnh báo mềm trong `availability`. Nháp
   chưa giữ phòng; chặn ở đây là bắt người ta phải đặt xong trong một lần gõ.

## Phase

| Phase | Nội dung | Tệp chính |
|---|---|---|
| [01](./phase-01-backend.md) | Model + migration + bộ mã + service chặn trùng + controller + cầu nối duyệt + quyền + seed + test | `backend/app/modules/meeting_room/**` |
| [02](./phase-02-frontend-phieu.md) | Types/api/hooks · danh mục phòng · danh sách phiếu (Của tôi / Cần tôi duyệt) · chi tiết + duyệt | `frontend-v2/src/modules/hr/**` |
| [03](./phase-03-frontend-lich.md) | Lịch đặt phòng theo ngày/tuần (cột = phòng) · mời người tham dự + thông báo | nt |

## Khóa quyền mới (2)

- `room_booking` — phiếu đặt: ai cũng đặt được, trưởng phòng/hành chính duyệt.
- `meeting_room` — danh mục phòng: việc quản trị, tách khỏi phiếu vì cho quyền
  sửa danh mục ≠ cho quyền đặt phòng.

Khai đủ **ba** chỗ: `ENTITIES` · `ENTITY_LABELS` · `SCOPE_FIELDS` (thiếu chỗ ba
là chặn sạch — có test canh). Vai trò cũ trên hệ đang chạy **không tự có** hai
khóa này (seed không ghi đè, D-018): phải tick ở màn Phân quyền.

## Rủi ro đã lường

| Rủi ro | Cách chặn |
|---|---|
| Hai phiếu cùng gửi duyệt một khung giờ | `BLOCKING_STATUSES` gồm cả *Chờ duyệt* |
| Sửa phiếu đã duyệt sang giờ khác, đè phòng người khác | Chỉ sửa được ở *Nháp* / *Trả về* (`EDITABLE_STATUSES`) |
| Hủy phiếu đang chờ ký mà phiên duyệt vẫn chạy | `withdraw_running_approval` trước khi hủy (bài học nghỉ phép) |
| Người duyệt không thuộc phạm vi dữ liệu của phiếu | Nới đọc khi **đang có việc treo** (`has_pending_task`), không nới cho "đã từng ký" |
| Thông báo gửi mà bấm vào không đi đâu | Khai `ENTITY_LABELS` + `ENTITY_LINKS` trong `approval/task_notification.py` |
