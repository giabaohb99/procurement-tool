# Kế hoạch: Phân hệ DUYỆT DẤU (Yêu cầu đóng dấu)

> **Trạng thái tổng quát (05/09/2026):** MỚI BẮT ĐẦU. Backend hiện chỉ có **stub** — `model.py` +
> `schema.py` cho `seal_request` / `seal_type`, bảng đã migrate, entity + phạm vi quyền đã đăng ký,
> **NHƯNG chưa có `service.py` / `controller.py` / router**, chưa nối thông báo, chưa có giao diện
> (frontend-v2 chỉ là trang "Sắp có", `enabled: false`). Kế hoạch này là **làm mới toàn bộ nghiệp vụ
> trên nền stub sẵn có**, bám đúng khuôn phân hệ **Đặt xe** (`vehicle_booking`). Log ở [TIEN-DO.md](TIEN-DO.md).

Nhánh làm việc: **`pltgiang`** (frontend-v2 + backend). Phân hệ chạy ở menu **Duyệt dấu**
(`/approval-seal`), gồm 2 màn chính: **Yêu cầu đóng dấu · Danh mục Loại con dấu**.

## Mục lục (theo thứ tự làm)

| Tài liệu | Nội dung |
|---|---|
| **README.md** *(file này)* | Tổng quan · mô hình dữ liệu · chi tiết chức năng · quyết định đã chốt |
| [TIEN-DO.md](TIEN-DO.md) | Log tick từng đầu việc theo PHA 0→5 + lệnh chạy local |
| [phase-0-nen-mo-hinh.md](phase-0-nen-mo-hinh.md) | Nền: `status` String→SMALLINT (R2), FILE_POLICY, vai trò seed, đăng ký luồng duyệt |
| [phase-1-mvp-phieu-va-upload.md](phase-1-mvp-phieu-va-upload.md) | MVP phiếu + **upload chứng từ chữ ký sống** + Danh mục Loại con dấu |
| [phase-2-luong-duyet-2-cong.md](phase-2-luong-duyet-2-cong.md) | Luồng duyệt 2 cổng: TBP duyệt · Văn thư đóng dấu (hoàn thành/trả/từ chối) |
| [phase-3-thong-bao-va-email.md](phase-3-thong-bao-va-email.md) | Thông báo & email theo bước (NSYC · Văn thư · Giám đốc công ty) |
| [phase-4-dong-bo-ui-va-ban-in.md](phase-4-dong-bo-ui-va-ban-in.md) | Đồng bộ UI/UX + bản in + nhân bản + ghi chú đính kèm ảnh |
| [phase-5-runtime-duyet-va-test.md](phase-5-runtime-duyet-va-test.md) | Nối runtime luồng duyệt (bridge) + test tổng thể + kịch bản phân quyền |
| [../tai-lieu-chuc-nang/17-duyet-dau.md](../tai-lieu-chuc-nang/17-duyet-dau.md) | **Tài liệu chức năng** (đặc tả trường, vòng đời trạng thái, phân quyền) cho người dùng/BA |

> Mỗi phase một file chi tiết theo khung 7 mục — giống bộ [dat-xe-duyet-dau](../dat-xe-duyet-dau/) /
> [ke-hoach-celery](../ke-hoach-celery/). Tất cả PHA đều là **kế hoạch phía trước** (chưa làm) — dùng
> `[ ]` trong TIEN-DO. §2–§4 dưới đây là bản tóm gọn xuyên suốt các phase.

## Quy ước chung (mọi phase tuân theo)
- **Tiếng Việt**, bám đúng code thật (tên file/hàm/cột) — **nguồn sự thật là `model.py`**; tài liệu
  lệch code thì sửa tài liệu trong cùng đợt CR.
- **Rule R2 (QĐ-11):** cột nghĩa **trạng thái/loại** lưu **SMALLINT + hằng số nguyên** (IntEnum-style),
  API trả **số kèm nhãn**, tiếng Việt chỉ ở tầng hiển thị. ⚠️ Stub hiện để `status String(30)="draft"` —
  PHA 0 **đổi sang SMALLINT** cho khớp Đặt xe (bảng chưa có dữ liệu nên đổi an toàn).
- Backend: gác quyền `require(entity, action)`, bó phạm vi `apply_scope`/`get_scoped`, ghi vết `audit`,
  phong bì `{success, message, data}`. Lấy 1 phiếu theo id **phải** qua `get_scoped`, không `db.get`.
- Frontend: danh sách dùng `DataTable`; Thêm/Sửa là **TRANG riêng** (case UI **C-02**); màu qua token
  semantic; badge "pill" theo `po_badges_design.md`.
- **Tái dùng, không dựng mới:** hệ **đính kèm tệp** (`core/storage.py` + module `attachment`) và hệ
  **thông báo** (`notification/*` + `notify.py` mẫu của Đặt xe) đã có sẵn — chỉ khai thêm cấu hình.
- **Khung mỗi file phase:** *Mục tiêu · Phạm vi & việc cụ thể (checklist) · Thiết kế kỹ thuật · Cấu
  hình/migration · Chống trùng/Idempotent · Kiểm thử & tiêu chí · Rủi ro & lưu ý.*

---

## 0. Mục tiêu & phạm vi

Số hóa việc **xin đóng dấu** của DEGO: nhân sự tạo **yêu cầu đóng dấu** (mục đích + loại con dấu +
công ty cần đóng dấu + **ảnh/PDF chứng từ có chữ ký sống**), **trưởng bộ phận duyệt**, **văn thư** tiếp
nhận, kiểm chứng từ và **đóng dấu ngoài thực tế** rồi bấm **Hoàn thành**. **Giám đốc** công ty cần đóng
dấu được **thông báo** khi phiếu được duyệt. Kèm một danh mục nền **Loại con dấu**.

Ngoài phạm vi (chưa làm): chữ ký số / con dấu điện tử, ký duyệt trên thiết bị di động chuyên biệt,
theo dõi tồn kho con dấu vật lý.

---

## 1. Kiến trúc & vị trí mã

| Lớp | Đường dẫn | Hiện trạng |
|---|---|---|
| Backend module | `backend/app/modules/seal_request/` (`model.py · schema.py` → thêm `service.py · controller.py · catalog_controller.py`) | **stub** (model+schema) |
| Router | `backend/app/main.py` (`include_router`, prefix `/api/seal-requests`, `/api/seal-types`) | **chưa nối** |
| Phạm vi quyền | `backend/app/core/scoping.py` (`seal_request` company/dept/owner; `seal_type` PUBLIC) | ✅ đã khai |
| Entity + nhãn | `backend/app/core/permissions.py` (`seal_request`, `seal_type`) | ✅ đã đăng ký |
| Chính sách tệp | `backend/app/core/file_registry.py` (`FILE_POLICY["seal_request"]`) | **chưa khai** |
| Vai trò seed | `backend/app/seed.py` (`seal_clerk · seal_admin` + cấp `seal_request:approve` cho TBP) | **chưa có** |
| Frontend module | `frontend-v2/src/modules/approval-seal/` (`routes.tsx` + `pages/` → thêm `api/ · hooks/ · components/ · config/ · types/`) | **stub** (`enabled:false`) |

**Khuôn tham chiếu 1-1: phân hệ Đặt xe** (`backend/app/modules/vehicle_booking/` +
`frontend-v2/src/modules/vehicle-booking/`). Nghiệp vụ phiếu **hand-write controller**; danh mục Loại
con dấu dùng **`make_crud_router`**. Form Thêm/Sửa là **TRANG riêng** (C-02); dialog thao tác nhanh
(duyệt/nhập lý do/hoàn thành) vẫn **popup** (C-01).

---

## 2. Mô hình dữ liệu

**Rule R2:** `status` lưu **SMALLINT + hằng số**, tiếng Việt chỉ ở tầng hiển thị.

### `tab_seal_type` — Loại con dấu (danh mục nền, đã có bảng)
`name` (unique) · `description` · `is_active`. Entity `seal_type` = **PUBLIC** (dùng chung mọi pháp
nhân). CRUD qua `make_crud_router`. Seed sẵn: *Dấu tròn công ty · Dấu chức danh · Dấu treo · Dấu giáp lai*.

### `tab_seal_request` — Yêu cầu đóng dấu (đã có bảng, mở rộng ở PHA 0)
Cột **đã có** (stub): `code` (DD###, unique) · `title` · `purpose` · `seal_type_id` · `department_id` ·
`company_id` · `requester` · `requester_id` · `first_approver_id` · `status` · `note` · `is_deleted`
+ `AuditMixin` (`created_at/by`, `updated_at/by`).

Cột **thêm ở PHA 0:**
- **`status`** đổi kiểu `String→SmallInteger` (bộ mã bên dưới).
- `copies` `SmallInteger` default 1 — **Số bản cần đóng dấu** (VD "Đóng dấu 2 bản").

**Tệp đính kèm** KHÔNG lưu cột trên phiếu — dùng hệ **attachment** dùng chung: bảng `tab_file` +
`tab_file_link` nối theo `(entity="seal_request", entity_id=<id phiếu>)`, phân biệt bằng `doc_type`:
- `doc_type="signed_doc"` — **chứng từ có chữ ký sống** (NSYC upload; **bắt buộc ≥ 1** khi gửi duyệt).
- `doc_type="note"` — **ảnh minh họa cho ghi chú** (không bắt buộc).

**Bộ mã trạng thái phiếu (`status`):** `1` Nháp · `2` Chờ duyệt · `3` Đã duyệt (chờ đóng dấu) ·
`4` Hoàn thành (đã đóng dấu) · `5` Từ chối · `6` Đã hủy · `7` Yêu cầu chỉnh sửa.
`EDITABLE_STATUSES = (1, 7)` — chỉ sửa nội dung khi *Nháp* hoặc bị *Yêu cầu chỉnh sửa*.

> **Khác Đặt xe:** không có `driver_status`; chỉ 1 loại phiếu (bỏ `request_type`, nhãn cố định "Phê
> duyệt dấu"). `company_id` = **công ty của con dấu** (người tạo CHỌN — có thể khác công ty phòng ban
> của họ), quyết định phạm vi Văn thư/Giám đốc và người nhận thông báo.

Migration liên quan (mới): `seal1status01` (status→SMALLINT + `copies`). Bảng gốc tạo ở
`020dab131963_add_vehicle_and_seal_models.py` (đã có).

---

## 3. Chi tiết chức năng

### 3.1 Yêu cầu đóng dấu (`/approval-seal`)
- **Danh sách:** lọc theo trạng thái / loại con dấu / công ty / tìm nhanh, **sắp xếp theo cột** (mã,
  mục đích, loại dấu, công ty, người tạo, trạng thái), badge trạng thái "pill", nút **Nhân bản** mỗi dòng.
- **Tạo / Sửa:** **TRANG riêng** (`/new`, `/:id/edit`, nhân bản `/new?from=<id>`) — mục đích, loại con
  dấu, **công ty cần đóng dấu**, số bản, ghi chú (đính kèm được ảnh), **upload chứng từ chữ ký sống**,
  **Lưu nháp / Gửi duyệt**. Chỉ sửa khi *Nháp* / *Yêu cầu chỉnh sửa*.
- **Chi tiết** (`/:id`): xem đầy đủ + **khối tệp đính kèm** (mở tab mới · xem trực tiếp · tải về) +
  **cụm nút theo vai trò** + **Lịch sử thao tác** (`AuditTimeline`).

### 3.2 Danh mục Loại con dấu (`/approval-seal/seal-types`)
- CRUD qua `make_crud_router` (khóa tự nhiên **tên**, chặn trùng). Thêm/Sửa **TRANG riêng**, có **Xóa** +
  **Lịch sử thao tác**. Trường: Tên · Mô tả · Đang dùng.

### 3.3 Luồng nghiệp vụ 2 cổng (trên trang chi tiết phiếu)
- **Trưởng bộ phận** (`seal_request:approve`): **Duyệt** · **Yêu cầu chỉnh sửa** (lý do) · **Từ chối** (lý do).
- **Văn thư** (`seal_request:write`): trên phiếu *Đã duyệt* → **Hoàn thành** (đã đóng dấu, ghi số bản/ghi
  chú) · **Yêu cầu chỉnh sửa** (VD chụp lại chữ ký rõ hơn) · **Từ chối**.
- Chốt chặn thật ở backend: `require` + kiểm trạng thái nguồn + `get_scoped`. Lý do Trả/Từ chối **ghi
  thêm dòng có nhãn** vào `note` (như `_append_note` của Đặt xe).

### 3.4 Tệp chứng từ chữ ký sống (yêu cầu cốt lõi)
- NSYC **upload ảnh/PDF** chứng từ **có chữ ký sống** để Văn thư đối chiếu trước khi đóng dấu; **bắt
  buộc ≥ 1 tệp** khi gửi duyệt.
- Mỗi tệp có 3 nút: **Mở ở tab mới** · **Xem trực tiếp** (trên phiếu) · **Tải về** — nối endpoint
  `/api/attachments/{link_id}/view|preview|download`. Ảnh xem inline; PDF mở tab mới.

### 3.5 Thông báo & phân quyền
- **Duyệt xong → chuông + email** tới **NSYC + Văn thư (theo công ty) + Giám đốc công ty**. Các mốc
  khác: gửi duyệt → TBP; trả/từ chối → NSYC; hoàn thành (đóng dấu) → NSYC.
- Vai trò seed: **Văn thư** (`seal_clerk`) · **Quản trị con dấu** (`seal_admin`); TBP dùng cơ chế
  duyệt sẵn có (`seal_request:approve`, phạm vi `dept`).

### 3.6 Đồng bộ UI/UX (dùng chung)
- Badge "pill" (`status-pill.tsx`), hộp xác nhận toàn cục (`shared/ui/confirm-dialog.tsx`), header có
  nút **back** + tiêu đề = **Mục đích** + badge trạng thái (mẫu `booking-page-header.tsx`), icon
  `Stamp` (lucide) cho menu + thẻ phân hệ.

---

## 4. Các quyết định (chốt & còn mở)

**Đã chốt:**
1. **1 loại phiếu** ("Phê duyệt dấu") — bỏ `request_type`; `company_id` là **công ty cần đóng dấu** do
   người tạo chọn.
2. **`status` = SMALLINT** (R2), đổi từ stub String (bảng chưa có dữ liệu nên đổi an toàn).
3. **Chứng từ chữ ký sống bắt buộc ≥ 1** khi gửi duyệt; tái dùng hệ `attachment` (không lưu cột tệp
   trên phiếu). Ghi chú cho phép **đính kèm ảnh** (`doc_type="note"`).
4. Thêm/Sửa = **TRANG riêng** (C-02); thao tác nhanh (duyệt/lý do/hoàn thành) **popup** (C-01).
5. **Văn thư** hoàn thành sau khi đóng dấu **ngoài thực tế** — hệ thống không sinh dấu điện tử.

**Còn mở (Bản = `?`, cần khách chốt):**
- **A.** Giám đốc công ty là **người nhận thông báo** hay **thêm 1 cổng phê duyệt** sau TBP? Mặc định
  kế hoạch: **chỉ thông báo**. (Bản cũ có 2 dòng "Phê duyệt" trong lịch sử — có thể là TBP + Văn thư,
  không nhất thiết Giám đốc ký.)
- **B.** Văn thư "Yêu cầu chỉnh sửa" → NSYC sửa xong gửi lại thì quay về **TBP duyệt lại** (mặc định,
  an toàn) hay **về thẳng Văn thư** (bỏ qua TBP)? Mặc định: **về TBP**.
- **C.** Có cần cột **"NSYC không thuộc phòng ban của TBP"** (chọn TBP thủ công) không, hay luôn auto
  theo phòng ban người tạo? Mặc định: auto + cho chọn `first_approver_id` như Đặt xe.

---

## 5. Các phase & tiến độ

| Phase | Nội dung | Trạng thái |
|---|---|---|
| **PHA 0** | Nền & mô hình (status→SMALLINT, `copies`, FILE_POLICY, vai trò seed, đăng ký luồng duyệt) | [ ] Chưa — [phase-0](phase-0-nen-mo-hinh.md) |
| **PHA 1** | MVP phiếu + upload chứng từ chữ ký sống + Danh mục Loại con dấu | [ ] Chưa — [phase-1](phase-1-mvp-phieu-va-upload.md) |
| **PHA 2** | Luồng duyệt 2 cổng (TBP duyệt · Văn thư đóng dấu) | [ ] Chưa — [phase-2](phase-2-luong-duyet-2-cong.md) |
| **PHA 3** | Thông báo & email theo bước (NSYC · Văn thư · Giám đốc) | [ ] Chưa — [phase-3](phase-3-thong-bao-va-email.md) |
| **PHA 4** | Đồng bộ UI/UX + bản in + nhân bản + ghi chú đính kèm ảnh | [ ] Chưa — [phase-4](phase-4-dong-bo-ui-va-ban-in.md) |
| **PHA 5** | Runtime luồng duyệt (bridge) + test tổng thể + phân quyền | [ ] Chưa — [phase-5](phase-5-runtime-duyet-va-test.md) |

Chi tiết từng đầu việc + log: **[TIEN-DO.md](TIEN-DO.md)** · Tài liệu chức năng:
**[../tai-lieu-chuc-nang/17-duyet-dau.md](../tai-lieu-chuc-nang/17-duyet-dau.md)**.
