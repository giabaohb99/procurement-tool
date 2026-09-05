# Duyệt dấu (Yêu cầu đóng dấu)

## Mục đích

Số hóa việc **xin đóng dấu** trong nội bộ DEGO: nhân sự tạo **yêu cầu đóng dấu** kèm **ảnh/PDF chứng
từ có chữ ký sống**, trưởng bộ phận **duyệt**, **văn thư** tiếp nhận — đối chiếu chứng từ và **đóng dấu
ngoài thực tế** rồi bấm **Hoàn thành**. **Giám đốc** công ty cần đóng dấu được **thông báo** khi phiếu
được duyệt. Phân hệ kèm một **danh mục nền**: Loại con dấu.

Đường dẫn (chỉ có trên `frontend-v2/`, cổng 8083):
- Yêu cầu đóng dấu: `/approval-seal` (danh sách), `/approval-seal/:id` (chi tiết), `/approval-seal/new` (tạo), `/approval-seal/:id/edit` (sửa).
- Loại con dấu: `/approval-seal/seal-types` · `/seal-types/new` · `/seal-types/:id`.

> **Rule R2 (QĐ-11).** Cột nghĩa *trạng thái* lưu **`SMALLINT` + hằng số nguyên** (IntEnum-style), API
> trả **số kèm nhãn**, tiếng Việt chỉ ở tầng hiển thị. Áp cho `status` — xem hằng số ở
> `backend/app/modules/seal_request/model.py`. Mọi endpoint trả phong bì `{success, message, data}`;
> gác quyền bằng `require(entity, action)`, bó phạm vi bằng `apply_scope`/`get_scoped`; ghi vết bằng `audit`.

## Vai trò tham gia

- **Người tạo / Nhân sự** (`seal_request:create`, `:read`): tạo & gửi duyệt yêu cầu của mình; sửa khi
  phiếu còn *Nháp* hoặc bị *Yêu cầu chỉnh sửa*; **upload ảnh/PDF chứng từ có chữ ký sống**.
- **Người duyệt — Trưởng bộ phận** (`seal_request:approve`): Duyệt · Yêu cầu chỉnh sửa · Từ chối phiếu
  *Chờ duyệt*.
- **Văn thư** (`seal_clerk`, `seal_request:write` phạm vi `company`): trên phiếu *Đã duyệt* — **Hoàn
  thành** (sau khi đóng dấu ngoài thực tế) · Yêu cầu chỉnh sửa · Từ chối. Đối chiếu **chứng từ chữ ký
  sống** trước khi đóng.
- **Giám đốc công ty** (`seal_request:read` phạm vi `company`): **được thông báo** khi phiếu của công
  ty mình được duyệt (bên liên quan). *(Có thêm cổng phê duyệt cho Giám đốc hay không — xem quyết định
  còn mở A trong `doc/duyet-dau/README.md`.)*
- **Quản trị con dấu** (`seal_admin`): quản **Danh mục Loại con dấu** (`seal_type` create/write/delete)
  + xem mọi phiếu.

> **Phạm vi dữ liệu.** `seal_request` lọc theo `company_id` / `department_id` / `created_by`
> (`core/scoping.py`). `company_id` = **công ty của con dấu** (người tạo chọn) — Văn thư/Giám đốc phạm
> vi `company` thấy đúng phiếu của công ty mình. `seal_type` khai **PUBLIC** (danh mục dùng chung).

## Vòng đời trạng thái phiếu (`status`)

| Mã (SMALLINT) | Tên hiển thị | Ý nghĩa | Nút thao tác hiển thị |
|---|---|---|---|
| `1` | Nháp | Đang soạn, chưa gửi duyệt | Lưu nháp · Gửi duyệt · Sửa · Xóa |
| `2` | Chờ duyệt | Đã gửi, đợi Trưởng bộ phận | **Duyệt · Yêu cầu chỉnh sửa · Từ chối** (nếu có `approve`) |
| `3` | Đã duyệt | Đã duyệt, chờ Văn thư đóng dấu | **Hoàn thành · Yêu cầu chỉnh sửa · Từ chối** (nếu có `write`) |
| `4` | Hoàn thành | Văn thư đã đóng dấu | (chỉ xem) |
| `5` | Từ chối | Người duyệt / Văn thư từ chối — khóa | (chỉ xem) |
| `6` | Đã hủy | Đã hủy — kết thúc | (chỉ xem) |
| `7` | Yêu cầu chỉnh sửa | Trả người tạo sửa rồi gửi lại | Lưu · Gửi duyệt lại · Sửa |

**Điều kiện chuyển trạng thái** (backend `service.py`, kiểm quyền + trạng thái nguồn):

- `Nháp` / `Yêu cầu chỉnh sửa` → `Chờ duyệt`: người tạo (hoặc `write`) bấm **Gửi duyệt**; pass
  `validate()` — có **Mục đích**, **Loại con dấu**, **Công ty**, và **≥ 1 tệp chứng từ chữ ký sống**.
  Lưu nháp thì không kiểm.
- `Chờ duyệt` → `Đã duyệt`: người có `approve` bấm **Duyệt** (`POST /{id}/approve`) → **bắn thông báo
  NSYC + Văn thư + Giám đốc**.
- `Chờ duyệt` → `Yêu cầu chỉnh sửa`: **Yêu cầu chỉnh sửa** + lý do (`/{id}/return`); lý do ghi vào ghi chú.
- `Chờ duyệt` → `Từ chối`: **Từ chối** + lý do (`/{id}/reject`).
- `Đã duyệt` → `Hoàn thành`: Văn thư bấm **Hoàn thành** (`/{id}/complete`, kèm số bản / ghi chú đóng
  dấu) → **thông báo NSYC**.
- `Đã duyệt` → `Yêu cầu chỉnh sửa`: Văn thư **Yêu cầu chỉnh sửa** + lý do (`/{id}/return`) — VD chụp
  lại chữ ký rõ hơn. Gửi lại → quay về `Chờ duyệt` *(mặc định — xem quyết định còn mở B)*.
- `Đã duyệt` → `Từ chối`: Văn thư **Từ chối** + lý do (`/{id}/reject`).

Chỉ trạng thái **Nháp** và **Yêu cầu chỉnh sửa** cho sửa nội dung phiếu (`EDITABLE_STATUSES`); sau khi
vào luồng thì khóa.

> **Lưu ý — luồng duyệt.** Ban đầu các bước Duyệt/Trả/Từ chối là **chuyển trạng thái trực tiếp theo
> quyền `approve`** (như Đặt xe PHA 3); bản **nối runtime engine đa-bước** (`approval_flow` +
> `entity_hooks` + `ApprovalSwitch`) là PHA 5 — xem `doc/duyet-dau/phase-5-runtime-duyet-va-test.md`.

---

## A. Thông tin chung của phiếu (header)

### 1. Mã phiếu (`code`)
- Kiểu nhập: Tự động
- Mặc định: hệ thống sinh `DD{seq:03d}` khi tạo (không sửa)
- Nguồn / liên kết: `_next_seal_code(db)` (chỉ đếm mã `DD\d+`, max+1 — tránh lỗi trùng như Đặt xe từng gặp)
- Người sửa: Hệ thống

### 2. Loại yêu cầu (cố định)
- Hiển thị nhãn **"Phê duyệt dấu"** (không có cột — phân hệ chỉ 1 loại phiếu).

### 3. Mục đích sử dụng (`purpose`)
- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: **Có** (kiểm khi gửi duyệt: "Vui lòng nhập mục đích sử dụng")
- Logic: là **tiêu đề hiển thị** của phiếu (chi tiết / danh sách / bản in). VD "Duyệt dấu Hợp đồng Hồ Gia - Dego".
- Người sửa: Người tạo / `write`, khi phiếu sửa được

### 4. Tên chứng từ (`title`)
- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không (tiêu đề phụ / tên văn bản cần đóng dấu)

### 5. Loại con dấu (`seal_type_id`)
- Kiểu nhập: Chọn (từ danh mục Loại con dấu đang dùng)
- Mặc định: trống
- Bắt buộc: **Có**
- Nguồn / liên kết: `tab_seal_type` (`is_active=True`)

### 6. Công ty cần đóng dấu (`company_id`)
- Kiểu nhập: Chọn (danh mục Công ty — hiện kèm **MST**)
- Mặc định: công ty của người tạo (cho đổi)
- Bắt buộc: **Có**
- Logic: **quyết định phạm vi** Văn thư/Giám đốc và **người nhận thông báo**. VD "CÔNG TY TNHH DEGO
  HOLDING - 1801722464".

### 7. Số bản cần đóng dấu (`copies`)
- Kiểu nhập: Nhập số
- Mặc định: 1
- Bắt buộc: Không (≥ 1)
- Logic: Văn thư đối chiếu số bản khi đóng dấu ("Đóng dấu 2 bản").

### 8. Ghi chú (`note`)
- Kiểu nhập: Nhập nhiều dòng — **cho phép đính kèm ảnh** (`doc_type="note"`, xem mục H)
- Mặc định: trống
- Bắt buộc: Không
- Logic: các lý do *Yêu cầu chỉnh sửa / Từ chối* được **ghi thêm** một dòng có nhãn vào ô này.

### 9. Trưởng bộ phận phê duyệt (`first_approver_id`)
- Kiểu nhập: Chọn / Tự động (theo phòng ban người tạo)
- Bắt buộc: **Có** khi gửi duyệt
- Logic: người sẽ Duyệt ở cổng 1. VD "Phạm Khánh Ngân".

### 10. Người tạo & phạm vi (`requester`, `requester_id`, `department_id`, `company_id`)
- Kiểu nhập: Tự động (chụp từ hồ sơ nhân sự lúc tạo; `company_id` mặc định = công ty người tạo nhưng cho đổi)
- Người sửa: Hệ thống
- Hiển thị chi tiết: **Tên · Email · SĐT · Vai trò** (serialize nối hồ sơ nhân sự).

---

## B. Tệp chứng từ chữ ký sống (yêu cầu cốt lõi)

| Việc | Chi tiết |
|---|---|
| Upload | NSYC tải **ảnh (jpg/png)** hoặc **PDF** chứng từ **có chữ ký sống**; nhiều tệp; `doc_type="signed_doc"` |
| Bắt buộc | **≥ 1 tệp** khi **Gửi duyệt** (không chặn lúc lưu nháp) |
| Xem | 3 nút mỗi tệp: **Mở ở tab mới** · **Xem trực tiếp** (inline trên phiếu) · **Tải về** |
| Lưu trữ | Hệ `attachment` dùng chung: `tab_file` + `tab_file_link` `(entity="seal_request", entity_id)`; kho `core/storage.py` (R2 hoặc đĩa cục bộ) |
| Giới hạn | Theo `FILE_POLICY["seal_request"]` — đuôi cho phép (pdf/ảnh) + dung lượng tối đa (chứng từ có thể ~17 MB) |

Endpoint xem/mở/tải nối vào `/api/attachments/{link_id}/view|preview|download` (đã có sẵn). Quyền xem
tệp **kế thừa quyền phiếu** (`seal_request` read + `ensure_in_scope`).

---

## C. Đóng dấu & hoàn thành (chỉ xem trên chi tiết; điền qua thao tác)

| Trường | Nguồn | Ghi khi |
|---|---|---|
| Người/Thời gian duyệt (audit) | tài khoản TBP | Duyệt |
| Người/Thời gian đóng dấu (audit) | tài khoản Văn thư | Hoàn thành |
| Số bản đã đóng / Ghi chú đóng dấu | Văn thư nhập khi Hoàn thành | Hoàn thành |

Lịch sử đầy đủ (ai — làm gì — lúc nào — lý do) lấy từ **`audit`** và hiển thị bằng **`AuditTimeline`**
(như khối "Lịch sử" của bản cũ: *Tạo yêu cầu → Phê duyệt → Đóng dấu*).

---

## D. Danh mục Loại con dấu (`/api/seal-types`, entity `seal_type`)

CRUD chuẩn qua `make_crud_router` (khóa tự nhiên **tên**, chặn trùng). Bảng: `tab_seal_type`.

| # | Trường | Kiểu nhập | Bắt buộc | Ghi chú |
|---|---|---|---|---|
| 1 | Tên (`name`) | Nhập tay | **Có** (unique) | VD Dấu tròn công ty · Dấu chức danh · Dấu treo · Dấu giáp lai |
| 2 | Mô tả (`description`) | Nhập tay | Không | |
| 3 | Đang dùng (`is_active`) | Chọn (Bật/Tắt) | Có | Tắt thì không hiện ở ô chọn Loại con dấu |

---

## H. Ghi chú đính kèm ảnh

Ô **Ghi chú** cho phép **đính kèm ảnh minh họa** (`doc_type="note"`) qua cùng hệ `attachment`. Ảnh ghi
chú hiển thị inline ở khối Ghi chú trên trang chi tiết; **không bắt buộc**, tách khỏi **chứng từ chữ ký
sống** (`doc_type="signed_doc"`) để Văn thư không nhầm hai loại.

---

## Giao diện dùng chung (2 màn)

- **Badge trạng thái dạng "pill"** theo `po_badges_design.md`: Hoàn thành = xanh lá · Chờ duyệt/Đã duyệt
  = vàng/xanh dương · Từ chối = đỏ · Đã hủy = xám.
- **Thêm & Sửa mở TRANG riêng** (không popup) — case UI **C-02**; trang sửa có nút **Xóa** + khối
  **Lịch sử thao tác** (`AuditTimeline`). **Thao tác nhanh** (Duyệt / nhập lý do / Hoàn thành) vẫn **popup**.
- **Header** có nút **back** + tiêu đề = **Mục đích sử dụng** + badge trạng thái bên phải (mẫu
  `booking-page-header.tsx`).
- **Sắp xếp theo cột** (server-side, whitelist cột thật) ở cả 2 bảng.
- **Nhân bản** phiếu: bấm biểu tượng ở dòng → mở trang tạo mới đã chép nội dung (`/new?from=<id>`;
  **không** chép tệp đính kèm).

## Phân quyền

| Vai trò (mã) | Quyền chính | Phạm vi |
|---|---|---|
| Văn thư (`seal_clerk`) | `seal_request` read/write · `seal_type` read | `company` |
| Quản trị con dấu (`seal_admin`) | `seal_request` read + `seal_type` create/write/delete | `all` |
| Trưởng bộ phận (vai trò sẵn có) | `seal_request` read/approve | `dept` |
| Nhân viên (vai trò sẵn có) | `seal_request` read/create/write | `own` |

Chi tiết thiết kế phân quyền hai trục: `doc/phan-quyen/Thiet_Ke_Phan_Quyen.md`.

## Liên quan

- Kế hoạch & tiến độ theo phase: `doc/duyet-dau/` (`README.md` + `TIEN-DO.md` + `phase-0…5`).
- Khuôn tham chiếu: phân hệ **Đặt xe** (`doc/tai-lieu-chuc-nang/16-dat-xe.md`, `doc/dat-xe-duyet-dau/`).
- Case thiết kế giao diện đã chốt: skill `ui` (C-01 popup thao tác nhanh, **C-02** trang Thêm/Sửa).
