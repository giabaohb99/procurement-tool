# PHA 6 — Còn lại (nâng cấp Đặt xe)

> Tổng quan & PHA 0→5: [README.md](README.md) · Log tick từng việc: [TIEN-DO.md](TIEN-DO.md).
> Nhánh: **`pltgiang`**. Mọi việc dưới đây **KHÔNG chặn dùng hằng ngày** — 3 màn + luồng thao tác
> theo vai trò đã chạy. Đây là phần tự động hóa duyệt, thông báo và ràng buộc lịch.

Mỗi mục theo **khung phase chuẩn** của bộ này (xem [../ke-hoach-celery/README.md](../ke-hoach-celery/README.md)):
*Mục tiêu · Phạm vi & việc cụ thể · Thiết kế kỹ thuật · Cấu hình · Chống trùng · Kiểm thử · Rủi ro*.

Thứ tự làm đề nghị: **6.1 (lõi) → 6.2 → 6.3 → 6.4 → 6.5**; 6.6–6.8 là phụ, làm khi có nhu cầu thật.

---

## 6.1 — Nối RUNTIME luồng duyệt (⭐ lõi) ✅ BACKEND ĐÃ LÀM (04/09/2026)

> **Đã triển khai & verify** (pytest xanh: `test/backend/test_dat_xe_luong_duyet_runtime.py`):
> - `vehicle_booking/approval_bridge.py` — `entity_hooks.register` 4 kết cục + `register_subject`
>   + `register_reader`; `submit_for_approval` (mở phiên qua `instance_service.start`); `block_legacy_path`.
> - `service._after_submit`: gửi duyệt → nếu `flow_service.is_enabled("vehicle_booking")` và có luồng
>   khớp thì mở phiên; cờ TẮT / chưa khai luồng → giữ ĐƯỜNG CŨ (báo `dx_submitted`). **Tương thích
>   ngược 100%** — mặc định cờ tắt, hành vi cũ không đổi (test khẳng định).
> - Controller `approve/return/reject` gọi `block_legacy_path` — đang chạy phiên nhiều bước thì chặn
>   duyệt thẳng (tránh hai đường đổi trạng thái). Bridge đăng ký ở `main.py` như `document`.
> - Kết cục engine → trạng thái phiếu: approved→Đã duyệt (+báo Điều phối viên) · rejected→Từ chối ·
>   returned→Yêu cầu chỉnh sửa · withdrawn→Nháp.
>
> **Frontend ✅ (04/09/2026):** `components/booking-approval-panel.tsx` trên trang chi tiết —
> lấy phiên bằng `approvalApi.ofEntity`, tìm lượt của mình bằng `useMyTasks`, **Duyệt/Trả/Từ chối
> ngay bằng `ApprovalActionDialog`** + dấu vết `ApprovalTrailCard`. Ba nút duyệt cũ TỰ ẨN khi
> `approval_running` (backend set ở API chi tiết, `booking-workflow-actions.tsx`). *(Codebase này KHÔNG
> còn hộp "Việc của tôi" chung — duyệt engine thao tác NGAY trên chứng từ, nên panel này là cần thiết,
> không chỉ là polish.)*

### Mục tiêu
Cho "Gửi duyệt" chạy qua **engine đa-bước `approval_flow`** (đã có sẵn, đang dùng cho Văn thư) thay vì
**chuyển trạng thái trực tiếp theo quyền `approve`** như hiện tại. Khi bật, phiếu đi qua đúng các bước
cấu hình ở `/approval/flows` ("Duyệt yêu cầu đặt xe" — 2 bước đã tạo); duyệt xong engine **gọi ngược**
về phiếu để đổi trạng thái.

### Phạm vi & việc cụ thể
- [ ] Tạo `backend/app/modules/vehicle_booking/approval_bridge.py` **theo đúng khuôn**
  `app/modules/document/approval_bridge.py` (bản mẫu duy nhất đang chạy).
- [ ] Đăng ký 4 kết cục + subject + reader cho entity `vehicle_booking`.
- [ ] "Gửi duyệt": nếu `ApprovalSwitch(entity="vehicle_booking").enabled` → **mở phiên duyệt**
  (`instance_service`) thay vì set thẳng `status = Chờ duyệt`; nếu tắt → giữ đường cũ (fallback).
- [ ] Bật công tắc: bản ghi `ApprovalSwitch` cho `vehicle_booking` (qua UI `/approval/flows` hoặc seed).
- [ ] Import `approval_bridge` một lần lúc nạp app (để `register(...)` chạy) — thêm vào nơi module
  được import sẵn (giống document).

### Thiết kế kỹ thuật
`entity_hooks.register(entity, on_approved=, on_rejected=, on_returned=, on_withdrawn=)` — **bốn** kết
cục (thiếu `on_withdrawn` thì rút phiếu xong phiếu kẹt ở *đang duyệt*, xem cảnh báo trong
`entity_hooks.py`). Mỗi hàm nhận `(db, entity_id, instance)`:

| Kết cục | Phiếu chuyển sang | Ghi chú |
|---|---|---|
| `on_approved` | `Đã duyệt` (3) | Sẵn sàng điều phối. *(Cân nhắc:* tự mở bước điều phối.) |
| `on_rejected` | `Từ chối` (6) | Ghi `instance.finish_reason` vào `note` phiếu |
| `on_returned` | `Yêu cầu chỉnh sửa` (8) | Người tạo sửa & gửi lại |
| `on_withdrawn` | `Nháp` (1) | Người nộp tự rút |

Thêm `entity_hooks.register_subject("vehicle_booking", ...)` (trả bối cảnh phiếu cho
`approver_resolver` — người tạo/phòng ban/công ty để phân bước "theo vai trò"/"theo cấp trên") và
`register_reader(...)` (ai được xem phiên duyệt — bám `apply_scope` của `vehicle_booking`).

⚠️ `entity_hooks.fire` **nuốt lỗi có chủ ý** (phiên đã ghi chữ ký, để lỗi bay lên thì rã cả giao dịch)
— nhưng ghi lý do vào `instance.finish_reason`. Hàm hook phải **idempotent** (bấm lại không hỏng thêm).

### Cấu hình
- Không thêm ENV. Chỉ cần bản ghi `ApprovalSwitch` bật cho `vehicle_booking`.
- Luồng "Duyệt yêu cầu đặt xe" đã seed ở PHA 3 — kiểm lại 2 bước còn đúng.

### Chống trùng
- Đang có phiên `đang chạy` thì **không** mở phiên mới cho cùng phiếu (engine đã chặn; kiểm lại).
- Công tắc tắt giữa chừng: phiếu đã có phiên vẫn chạy hết theo engine; phiếu mới đi đường trực tiếp.

### Kiểm thử & tiêu chí hoàn thành
- Bật switch → tạo phiếu → Gửi duyệt: sinh phiên 2 bước; duyệt đủ 2 bước → phiếu `Đã duyệt`.
- Từ chối / Trả / Rút ở từng bước → phiếu về đúng trạng thái bảng trên; `note`/`finish_reason` có lý do.
- Tắt switch → Gửi duyệt vẫn chạy đường trực tiếp (không vỡ).
- Test: thêm `test/backend/test_dat_xe_duyet_runtime.py` (mô phỏng như test bridge của document).

### Rủi ro & lưu ý
- Nhân đôi "nút duyệt": khi bật engine, **ẩn** cụm Duyệt/Trả/Từ chối trực tiếp trên trang chi tiết
  (nếu không, có 2 đường đổi trạng thái — đúng lỗi "đường tắt đi vòng qua luồng" ghi ở `action_service.py`).
- `approve`-theo-quyền và engine **không được chạy song song** trên cùng phiếu.

---

## 6.2 — Màn "Chuyến của tôi" cho tài xế ✅ ĐÃ LÀM (04/09/2026)

> `filter_my_trips` (lọc `?mine=1` — chỉ chuyến mình là tài xế được phân, khác phạm vi `assigned`) +
> trang `my-trips-page.tsx` (`/vehicle-booking/my-trips`, nhóm theo bước, tái dùng `BookingWorkflowActions`)
> + nav "Chuyến của tôi". Test `test/backend/test_dat_xe_chuyen_cua_toi.py`.

### Mục tiêu
Tài xế có một màn gọn chỉ liệt kê **chuyến được phân cho chính mình**, thao tác Chấp nhận / Bắt đầu /
Hoàn tất ngay, không phải lọc trong danh sách chung.

### Phạm vi & việc cụ thể
- [ ] Route `/vehicle-booking/my-trips` (chỉ hiện với vai trò `booking_driver`).
- [ ] Danh sách phiếu `status = Điều phối` + `assigned_driver_id` = tài xế đang đăng nhập, nhóm theo
  `driver_status` (Chờ nhận · Đã nhận · Đang đi).
- [ ] Cụm nút thao tác nhanh ngay trên thẻ (tái dùng `booking-workflow-actions.tsx`).

### Thiết kế kỹ thuật
- **Không cần API mới**: phạm vi `assigned` đã lọc đúng (nối `Driver.user_id`). Gọi
  `/api/vehicle-bookings?status=4` — `apply_scope` tự bó về chuyến của tài xế.
- Frontend: trang mới trong `modules/vehicle-booking/pages/`, dùng `DataTable` hoặc thẻ.

### Kiểm thử & tiêu chí
- Đăng nhập tài xế A: chỉ thấy chuyến của A; tài xế B không thấy chuyến của A.
- Thao tác từ màn này đổi `driver_status` đúng như trên trang chi tiết.

### Rủi ro
- Đừng để lộ nút cho người không phải tài xế được phân (backend `_ensure_can_drive` vẫn chặn thật).

---

## 6.3 — Chống trùng giờ khi điều phối ✅ ĐÃ LÀM (04/09/2026)

> Đã cài `_find_time_conflict` trong `dispatch_booking` (`service.py`) + test
> `test/backend/test_dat_xe_thong_bao_va_chong_trung.py` (chồng xe / chồng tài xế / giáp ranh).

### Mục tiêu
Một **xe** hoặc một **tài xế** không bị phân 2 chuyến chồng khung giờ.

### Phạm vi & việc cụ thể
- [ ] Khi `dispatch_booking`: kiểm xe/tài xế được chọn có chuyến khác **giao khoảng**
  `[start_time, end_time]` ở trạng thái còn hiệu lực (Điều phối/đang chạy) không.
- [ ] Trùng → trả lỗi rõ ("Xe X đã có chuyến DX045 từ 08:00–10:00"); **chặn ở service**, không chỉ ẩn nút.

### Thiết kế kỹ thuật
- Điều kiện giao khoảng: `existing.start_time < new.end_time AND existing.end_time > new.start_time`,
  cùng `assigned_vehicle_id` (hoặc `assigned_driver_id`), loại trừ chính phiếu đang sửa, chỉ xét
  `status = Điều phối` và `driver_status ∈ {Chờ nhận, Đã nhận, Đang đi}`.
- Trả `error(...)` theo phong bì; frontend hiện toast.

### Chống trùng / biên
- Chuyến khứ hồi, chuyến chưa có `end_time` (không nên có — `end_time` bắt buộc). Cho phép **giáp
  ranh** (kết thúc == bắt đầu) không tính là trùng.

### Kiểm thử & tiêu chí
- Phân xe cho 2 phiếu trùng giờ → phiếu thứ 2 bị chặn; lệch giờ → cho qua.
- Test service `test_dat_xe_chong_trung_gio.py`.

### Rủi ro
- Giờ thực tế (`actual_*`) lệch kế hoạch — mục này chặn theo **giờ kế hoạch** khi điều phối, đủ dùng.

---

## 6.4 — Lọc nguồn tài xế theo vai trò khi điều phối ✅ ĐÃ LÀM (04/09/2026)

> Endpoint `GET /api/dispatch/drivers` (`catalog_controller.dispatch_router`, gác `vehicle_booking.write`) +
> `service.drivers_for_dispatch`: thuê ngoài + nội bộ giữ vai trò `booking_driver`; ẩn hồ sơ nội bộ không
> vai trò. Frontend `dispatchOptionsApi.drivers` trỏ sang endpoint này. Test `test_dat_xe_loc_tai_xe_dieu_phoi.py`.

### Mục tiêu
Ô chọn tài xế lúc điều phối chỉ hiện **người thật sự giữ vai trò Tài xế** (`booking_driver`), không hiện
mọi bản ghi trong `tab_driver`.

### Phạm vi & việc cụ thể
- [ ] Tùy chọn `?role=driver` (hoặc endpoint riêng) cho danh sách tài xế khi điều phối: lọc bản ghi
  `tab_driver` có `user_id` gắn tài khoản mang vai trò `booking_driver` (nội bộ); tài xế thuê ngoài
  vẫn hiện (không có tài khoản).
- [ ] Frontend ô chọn tài xế ở dialog điều phối gọi danh sách đã lọc.

### Thiết kế kỹ thuật
- Join `tab_driver.user_id` → grant vai trò `booking_driver`. Quyết định rõ: thuê ngoài (không
  `user_id`) **luôn hiện** vì họ là tài xế theo định nghĩa.

### Kiểm thử & tiêu chí
- Nhân sự không có vai trò Tài xế nhưng lỡ tạo bản ghi driver nội bộ → **không** hiện trong ô điều phối.

### Rủi ro
- Đừng lọc luôn ở màn Danh mục tài xế (ở đó phải thấy hết để quản lý) — chỉ lọc ở **ô điều phối**.

---

## 6.5 — Thông báo & Email theo bước (+ cài đặt bật/tắt & sửa template HTML) ✅ ĐÃ LÀM (04/09/2026)

> **Đã triển khai & verify** (backend suite + `npm run check` xanh):
> - Model `tab_email_template` (`notification/email_template_model.py`) + migration `dxmail01` (đã upgrade).
> - `email_template_service.py` (mặc định trong code + đè DB; render/preview/send) + `email_template_controller.py`
>   (list/get/put/reset/preview/test-send) đăng ký ở `main.py`.
> - `vehicle_booking/notify.py` bắn **chuông + email** tại các mốc `service.py`; ca **TBP duyệt → Điều phối viên**
>   (`dx_approved`) đã chạy, có test.
> - Frontend **`EmailTemplatePanel`** nhúng vào `/system/settings` (dưới nhóm Email): bật/tắt từng bước,
>   sửa HTML, chèn biến, xem trước (iframe), gửi thử, khôi phục mặc định.
> - ⚠️ **Khác plan một điểm:** gác quyền dùng entity **`setting`** (không đẻ entity `email_template` mới) —
>   vì đây là một mục của Cấu hình hệ thống; đỡ phải sửa `permissions.py`/`scoping.py`/seed.

### Mục tiêu
Mỗi mốc chuyển trạng thái của phiếu **gửi chuông + email** tới đúng **người liên quan**. Ví dụ trục:
**TBP duyệt → email tới vai trò Điều phối viên**: *"Bạn có chuyến xe cần điều phối"*. Ngoài ra dựng một
**trang cài đặt**: **bật/tắt email cho từng bước** và **sửa template email dạng HTML** ngay trên trang đó.

### Phạm vi & việc cụ thể
- [ ] Thêm các event `dx_*` vào `trigger_notification` + gọi tại các mốc trong `vehicle_booking/service.py`.
- [ ] **Bổ sung người nhận theo vai trò**: khi **duyệt** (`dx_approved`), gửi thêm cho **mọi tài khoản
  giữ vai trò `booking_dispatcher` / `booking_manager`** (`recipient_ids`) — nội dung "có chuyến cần điều phối".
- [ ] Bảng **`tab_email_template`**: mỗi event một dòng (công tắc bật/tắt email + subject + thân HTML).
- [ ] **Gộp vào `/system/settings`** (không trang riêng): thêm mục "Mẫu email theo bước" — liệt kê từng
  bước, **switch bật/tắt email**, nút **Sửa template** mở **trình soạn HTML**.
- [ ] `trigger_notification` **đọc template từ DB trước**, không có/không bật thì **fallback template code**.

### Thiết kế kỹ thuật

**A. Tái dùng nguyên hạ tầng đang chạy** (không dựng lại):
| Có sẵn | Vai trò |
|---|---|
| `notification/service.py → trigger_notification(...)` | Bắn **chuông + email** trong một lời gọi (email chạy nền qua `background_tasks`) |
| `notification/service.py → render_template(html, context)` | Engine regex: `{{ var }}`, `{{var}}`, `{% if cond %}…{% endif %}` |
| `notification/email_templates.py → HTML_LAYOUT` | Khung HTML chuẩn DEGO (header/logo/nút) — làm **fallback** & khung bọc |
| `core/app_settings` (`get`/`set`, Fernet) | Công tắc `email_enabled` + cấu hình SMTP đã có |
| `send_smtp_email(...)` | Gửi thật; đã tôn trọng `email_enabled` |

**B. Bảng ca thông báo (người nhận thật — chỉ tài khoản hệ thống):**
**MỖI EVENT = MỘT nhóm người nhận** (để mỗi nhóm một mẫu email riêng). Hai mốc "Duyệt" và
"Hoàn tất" tách làm hai event vì Điều phối viên và Người tạo cần nội dung khác nhau:

| Event | Mốc | Người nhận | Nội dung mẫu |
|---|---|---|---|
| `dx_submitted` | Gửi duyệt | Người duyệt (TBP theo bước/vai trò) | "YCĐX {{ code }} chờ bạn duyệt" |
| **`dx_approved_dispatcher`** | **Duyệt** | **Điều phối viên** | **"Bạn có chuyến xe cần điều phối: {{ code }}"** |
| `dx_approved_creator` | Duyệt | Người tạo | "Yêu cầu đặt xe {{ code }} đã được duyệt" |
| `dx_returned` / `dx_rejected` | Trả / Từ chối | Người tạo | "YCĐX {{ code }} bị trả/từ chối: {{ reason }}" |
| `dx_dispatched` | Điều phối | Tài xế được phân (**nội bộ**) | "Bạn được phân chuyến {{ code }}, khởi hành {{ start_time }}" |
| `dx_driver_accepted` / `dx_driver_rejected` | Tài xế nhận / từ chối | Điều phối viên | "Tài xế đã {{ trạng thái }} chuyến {{ code }}" |
| `dx_completed_dispatcher` | Hoàn tất | Điều phối viên | "Chuyến {{ code }} đã hoàn tất" |
| `dx_completed_creator` | Hoàn tất | Người tạo | "Yêu cầu đặt xe {{ code }} đã hoàn tất" |

Bắn theo nhóm: `notify_approved` / `notify_completed` (`notify.py`) gọi 2 event một lần. Màn cài đặt có
cột **Tên bước · Tiêu đề · Người nhận · Email** (`recipient` trong `get_effective`).

**Bổ sung 04/09/2026:**
- **Prettify HTML** ở trang sửa mẫu (nút "Định dạng HTML") — dùng `js-beautify` (đúng thứ Sublime
  HTML-CSS-JS Prettify dùng); trang sửa là 2 cột soạn/xem trước canh đều.
- **Loại trừ email** theo cá nhân / phòng ban / công ty (`tab_email_exclusion`, migration `dxmail02`),
  **áp cho TẤT CẢ mẫu hoặc TỪNG mẫu** (cột `event`, migration `dxmail03`): `filter_recipients(db,
  recipients, event)` gọi trong `send_event_email` — gộp luật áp mọi mẫu (`event=""`) + luật riêng
  event (chỉ chặn EMAIL, chuông vẫn gửi). Panel `email-exclusion-panel.tsx` có ô "Áp cho mẫu".
  Test `test_email_loai_tru.py`.

> ⚠️ **Ai** nhận (recipient) là **luật nghiệp vụ nằm ở code** — không cho sửa trên UI (tránh gửi nhầm).
> UI chỉ chỉnh **bật/tắt** và **nội dung template**. Tài xế thuê ngoài / người gửi-nhận / người liên
> hệ điểm dừng **không** có tài khoản → không nhận kênh này (muốn báo phải SMS/Zalo — ngoài phạm vi).

**C. Cài đặt bật/tắt + sửa template (phần MỚI người dùng yêu cầu):**
- **Bảng** `tab_email_template` (module `notification`, thêm vào `all_models.py`):
  `event` *(unique, vd `dx_approved`)* · `label` *(nhãn bước, hiển thị)* · `enabled` *(bool — công tắc
  email của bước)* · `subject` *(chuỗi, cho phép `{{ var }}`)* · `body_html` *(Text — thân HTML sửa được)* ·
  kế thừa `AuditMixin`. Bật/tắt = cột `enabled`; sửa template = `subject` + `body_html`.
- **Backend** (entity quyền mới `email_template`, gác bằng `require`):
  `GET /api/email-templates` (liệt kê + trạng thái) · `GET /api/email-templates/{event}` ·
  `PUT /api/email-templates/{event}` (sửa `enabled`/`subject`/`body_html`) ·
  `POST /api/email-templates/{event}/preview` (render thử với context mẫu) ·
  `POST /api/email-templates/{event}/test-send` (gửi thử tới email người bấm).
- **`trigger_notification` đổi nhẹ:** trước khi vào chuỗi if/elif hardcode, **tra `tab_email_template`
  theo `event`**: có dòng & `enabled=True` → dùng `subject`/`body_html` của DB (render qua
  `render_template`, bọc trong `HTML_LAYOUT`); **không có / `enabled=False`** → **bỏ gửi email**, giữ
  template code làm fallback khi thiếu. *(Chuông in-app vẫn tạo — công tắc này chỉ chi phối EMAIL, đúng
  chữ "cài đặt email thông báo".)*
- **Frontend — GỘP vào Cấu hình hệ thống `/system/settings`** *(quyết định: không dựng trang riêng
  trong phân hệ Đặt xe)*. Trang này ở `modules/system/pages/setting-page.tsx`, hiện có mảng `GROUPS =`
  `workflow · email (SMTP) · storage` (vẽ theo trường backend, gác `setting.write`). Thêm **một mục
  mới** — vd nhóm **"Mẫu email theo bước"** — đặt **ngay dưới nhóm _Email (SMTP)_**.
  - ⚠️ Mục này **KHÔNG phải field-row khai báo** như 3 nhóm cũ (chúng chỉ vẽ theo `type`); nó là **panel
    riêng** — theo đúng khuôn các panel "nặng" đã có (`approval/components/flow-settings-panel.tsx`,
    `document/pages/document-settings-page.tsx`). Đặt component ở `modules/system/components/
    email-template-panel.tsx` (gọi API `email_template`), **không** nhét vào `modules/vehicle-booking/`.
  - Nội dung panel: **bảng từng bước** — cột *Bước · Người nhận (chỉ đọc) · Bật email (switch) · Sửa*.
    Nút **Sửa** mở **trình soạn template**:
    - Ô `subject` + **vùng soạn HTML** cho `body_html` (textarea/editor mã, KHÔNG `<Input disabled>`).
    - **Bảng biến chèn được** (bấm để chèn) — xem mục D.
    - **Xem trước** (gọi endpoint preview, render iframe) + **Gửi thử** về email của mình.
    - Nút **Khôi phục mặc định** (xóa dòng DB → quay lại template code).
  - Gác quyền: dùng chung `setting.write` của trang Cấu hình (không tạo quyền UI mới); backend endpoint
    vẫn gác bằng entity `email_template` như mục B.

**D. Biến chèn được vào template** (đưa vào `context` khi render — bám `trigger_notification` hiện có):
`{{ code }}` (mã phiếu) · `{{ doc_type_label }}` · `{{ creator_name }}` · `{{ reason }}` ·
`{{ approve_note }}` · `{{ link }}` (link mở phiếu) · `{{ start_time }}` · `{{ end_location }}` ·
`{{ driver_name }}` · `{{ vehicle_label }}` · `{% if is_urgent %}…{% endif %}`. Trang cài đặt hiện
**đúng danh sách biến hợp lệ cho từng event** để người soạn không gõ biến không có dữ liệu.

### Cấu hình
- Không thêm ENV mới. Dùng công tắc chung `email_enabled` + SMTP trong `app_settings` (đã có màn cấu hình).
- Seed sẵn một dòng `tab_email_template` cho mỗi event `dx_*` (enabled mặc định + subject/body từ code)
  để trang cài đặt có nội dung sửa ngay; seed idempotent.
- (Nếu có Celery — [../ke-hoach-celery](../ke-hoach-celery/README.md)) email đẩy qua worker; chưa có thì
  `background_tasks` đồng bộ (fallback), **không bắt buộc Redis**.

### Chống trùng / Idempotent
- Đánh dấu đã gửi theo `(booking_id, event)` để retry không bắn email trùng.
- `event` **unique** trong `tab_email_template` (một bước một template).

### Kiểm thử & tiêu chí hoàn thành
- TBP duyệt phiếu → **mọi Điều phối viên** nhận chuông + email "có chuyến cần điều phối"; người tạo nhận "đã duyệt".
- Tắt switch một bước → bước đó **không gửi email** (chuông vẫn có); bật lại → gửi.
- Sửa `body_html` một event → email thực tế đổi theo; **Xem trước** & **Gửi thử** khớp.
- `email_enabled=false` (công tắc chung) → không email nào ra, kể cả bước đang bật.
- Test: `test/backend/test_dat_xe_email_template.py` (tra DB template, fallback code, tôn trọng `enabled`).

### Rủi ro & lưu ý
- **Không cho sửa người nhận trên UI** — chỉ bật/tắt + nội dung; recipient là luật ở code.
- **Chèn HTML tự do** = rủi ro hỏng layout/XSS trong mail client: bọc bắt buộc trong `HTML_LAYOUT`,
  escape biến (render_template đang thay chuỗi thô — cân nhắc escape `{{ reason }}` do người dùng nhập).
- Không spam: gộp khi 1 phiếu đổi nhiều bước liên tiếp trong thời gian ngắn.
- ⚠️ Template sửa trên UI **sống ở DB** — prod chạy lại seed **không** được ghi đè (giống phân quyền/
  danh mục người dùng đã sửa): seed chỉ chèn khi **thiếu** dòng, đừng `SEED_FORCE_SYNC` đè template.

---

## 6.6 — (Cân nhắc) Đưa dialog thao tác nhanh lên trang
Hiện **điều phối / nhập lý do / hoàn tất** vẫn là **popup** (case C-01) vì là thao tác nhanh, giữ ngữ
cảnh danh sách. Chỉ chuyển lên trang nếu người dùng yêu cầu — khi đó ghi case UI mới, không tự đổi.

## 6.7 — (Nếu cần) Cấp ID/PW cho tài xế thuê ngoài
Đã **tạm bỏ** (quyết định §4.3 ở README). Cần backend provisioning tài khoản đăng nhập riêng cho tài
xế ngoài + gắn vai trò `booking_driver` + phát ID/PW. Làm khi có nhu cầu tài xế ngoài tự thao tác.

## 6.8 — Bản in phiếu đặt xe ✅ ĐÃ LÀM (04/09/2026)
`pages/vehicle-booking-print-page.tsx` (khổ A4, thanh thao tác `print:hidden`, `window.print()`), route
`/print/vehicle-booking/:id` đăng ở `app-router.tsx` (ngoài khung, như các bản in khác) + nút **In phiếu**
ở trang chi tiết. Ba cụm A/B/C + ô ký.

## 6.9 — Kịch bản 6 bước ✅ (integration) · ⏳ (E2E trình duyệt)
`test/backend/test_dat_xe_luong_6_buoc.py` chạy đầy đủ **tạo → duyệt → điều phối → nhận → bắt đầu →
hoàn tất** + nhánh trả/từ chối/tài xế-từ-chối, ở tầng service (verify ngay). **Còn lại:** E2E trình
duyệt (Playwright) cần cả stack + tài khoản demo cho 3 vai trò Đặt xe — chạy trên host, đặt ở `test/e2e/`.

---

## Việc "quét dọn" tài liệu đi kèm CR này
- [ ] `doc/erp/tai-lieu-ky-thuat/05e-du-lieu-cong-tac-ho-tro.md` **Cụm H** đang tả **schema chuỗi cũ**
  (status VARCHAR) — **đã lệch** so với module đã ship (SMALLINT R2 + ~20 cột mới: `stops` JSON, khối
  giao hàng, `supplier_type`/`tax_*`, `license_class`, `capacity` Float). Cập nhật 3 bảng
  `tab_vehicle · tab_driver · tab_vehicle_booking` theo `model.py` **trong cùng đợt CR** (nguồn sự
  thật là `model.py`; mã đúng, từ điển sai).
- [ ] `doc/erp/tai-lieu-ky-thuat/02-danh-muc-module.md`: dòng frontend `vehicle-booking` đang ghi
  *"Sắp có"* — đổi thành **Đang chạy** (đã bật ở `module-registry.ts`).
