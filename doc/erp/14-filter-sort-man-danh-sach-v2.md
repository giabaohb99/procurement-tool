# Thiết kế Bộ lọc & Sắp xếp cho màn danh sách — Thu mua & Sản xuất (ERP v2)

Trạng thái: BẢN THIẾT KẾ (chờ duyệt) · Ngày: 21/08/2026 · Phạm vi đợt này: phân hệ
**Thu mua** (4 màn) + **Sản xuất** (5 màn). Các phân hệ khác làm sau.

Mục tiêu: đứng ở vai trò một **nhân viên thu mua**, mở màn danh sách ra là lọc/sắp
xếp được ngay những chiều họ dùng hằng ngày — không phải mở "bộ lọc nâng cao" gõ
điều kiện cho từng lần. Hiện các màn đang thiếu phần lọc nhanh bên ngoài và **chưa
màn nào có sắp xếp (sort)**.

---

## 0. Nguyên tắc thiết kế

**Hai tầng lọc, tách vai trò rõ ràng:**

1. **Thanh lọc nhanh (bên ngoài)** — nằm ngay trên bảng, hiện sẵn, một chạm. Chỉ để
   3–6 chiều DÙNG NHIỀU NHẤT của màn đó. Không nhồi hết field ra đây.
2. **Bộ lọc nâng cao** (`ConditionalFilter` đã có) — cho điều kiện phức tạp, ghép
   nhiều điều kiện, operator lạ (khác, chứa, trong khoảng…). Giữ nguyên cơ chế, chỉ
   bổ sung field còn thiếu.

**Quy tắc vàng:** một field chỉ nên xuất hiện ở MỘT tầng. Cái nào đưa ra thanh nhanh
thì bỏ khỏi bộ lọc nâng cao (đỡ trùng, đỡ rối), trừ khi ở nâng cao cần operator khác
(ví dụ trạng thái: ngoài là chọn nhanh 1 giá trị, nâng cao cho "thuộc nhiều trạng thái").

**Chip nhanh theo vai trò** — vài nút bật/tắt đặt đầu thanh, gói sẵn điều kiện hay
dùng: "Đơn của tôi", "Gấp", "Chờ xử lý", "Tháng này". Bấm một cái là ra, không phải
chọn từng ô.

**Ràng buộc kỹ thuật (bắt buộc tôn trọng):**

- Field chỉ lọc được nếu nằm trong `FILTERABLE` của controller (hoặc là tham số lọc
  đặc biệt đã cài). Field chỉ sort được nếu là **cột vật lý** của bảng chính — cột
  tính toán (`total`, `amount`, `expiry`, `thumbnail_url`) KHÔNG sort ở backend được.
- Ô tham chiếu (NCC, nhân sự, bộ phận) dùng **combobox có fetch**, lọc theo **id**
  (`is`/`is_not`), không lọc theo tên — trừ vài chỗ dữ liệu cũ chưa có id (ghi rõ bên dưới).
- Sort truyền lên bằng `sort_by=<cột>` + `sort_dir=asc|desc`.

---

## 1. Bộ "dạng lọc" chuẩn dùng trong tài liệu này

| Ký hiệu | Dạng | Mô tả | Ví dụ |
|---|---|---|---|
| **Tìm** | ô text (debounce) | Gõ tự do, backend LIKE `%...%` | Tìm mã ĐMH |
| **Chọn** | select đơn | Một giá trị từ danh sách cố định | Trạng thái, Vai trò NCC |
| **ChọnN** | multi-select | Nhiều giá trị (operator `in`) — thường ở bộ lọc nâng cao | Nhiều trạng thái |
| **Tham chiếu** | combobox + fetch | Gõ để tìm, chọn 1; lọc theo id | NCC, NSPT, Bộ phận |
| **Khoảng ngày** | date-range + preset | Từ–đến, kèm nút nhanh Hôm nay / Tuần này / Tháng này / Quý | Ngày đặt, Ngày cần hàng |
| **Chip** | nút bật/tắt boolean | Bật là thêm điều kiện, tắt là bỏ | Gấp, Đã ký |
| **Hiệu lực** | select tính theo ngày | Còn hạn / Sắp hết hạn / Hết hạn (tính từ `end_date`) | Hợp đồng |

**Điều khiển Sắp xếp:** một nút **"Sắp xếp"** cạnh bộ lọc — chọn *trường* + *hướng*
(↑ tăng / ↓ giảm). Mặc định mỗi màn ghi trong phần riêng. (Bổ trợ: cho bấm tiêu đề
cột để sort — xem mục 5, việc chung của `DataTable`.)

---

## 2. PHÂN HỆ THU MUA

### 2.1 Yêu cầu mua hàng (PYC) — `purchase-request-list-page.tsx`

Vai trò thu mua: nhận PYC từ các bộ phận, ưu tiên xử lý cái **gấp** và cái **sắp tới
hạn cần hàng**.

**Chip nhanh:** `[Gấp]` (`is_urgent=true`) · `[Tháng này]` (ngày tạo trong tháng) ·
`[Sắp tới hạn]` (`need_date` trong 7 ngày tới).

**Thanh lọc nhanh đề xuất:**

| Chiều lọc | Dạng | Param | Nguồn | Ghi chú |
|---|---|---|---|---|
| Tìm mã PYC | Tìm | `code` | — | Đã có |
| Công ty | Chọn | `company_id` | `useCompanies` | Đã có |
| Trạng thái | Chọn | `status` | `PR_STATUS_LABELS` | Đã có |
| Bộ phận yêu cầu | Tham chiếu | `department_id` | `fetchDepartmentOptions` | **Thêm** |
| Ngày cần hàng | Khoảng ngày | `need_date_from/to` | — | **Thêm** (backend đã có range) |
| Gấp | Chip | `is_urgent` | — | **Thêm** (đưa ra ngoài dạng chip) |

**Bộ lọc nâng cao (giữ + tinh chỉnh):** người yêu cầu (`requester_id`), ngày tạo
(`request_date`), nhóm hàng (`item_group` — lọc qua dòng hàng, **thêm**), người phụ
trách dòng (`assignee` — **thêm**), trạng thái nhiều giá trị.

**Sắp xếp:**

| Nhãn | Cột | Hướng mặc định | Ý nghĩa nghiệp vụ |
|---|---|---|---|
| Mới nhất (mặc định) | `id` (≈ ngày tạo) | ↓ | Việc mới lên đầu |
| Ngày cần hàng | `need_date` | ↑ | Gần hạn xử lý trước — **hữu ích nhất với thu mua** |
| Ngày tạo | `request_date` | ↓/↑ | |

> `total` (tổng tiền) là cột tính toán → **không sort backend được**. Nếu muốn sắp theo
> tiền phải sort trong trang hiện tại, ghi chú rõ để không hiểu nhầm là sort toàn bộ.

### 2.2 Đơn mua hàng (ĐMH) — `purchase-order-list-page.tsx`

Vai trò thu mua: theo dõi đơn mình phụ trách, đòi **hồ sơ chứng từ** còn thiếu, xem
đơn theo **nhà cung cấp**.

**Chip nhanh:** `[Đơn của tôi]` (`nspt_id` = người đăng nhập) · `[Gấp]` ·
`[Thiếu chứng từ]` (`document_status` = chưa đủ) · `[Tháng này]`.

**Thanh lọc nhanh đề xuất:**

| Chiều lọc | Dạng | Param | Nguồn | Ghi chú |
|---|---|---|---|---|
| Tìm mã ĐMH | Tìm | `code` | — | Đã có |
| Công ty | Chọn | `company_id` | `useCompanies` | Đã có |
| Trạng thái | Chọn | `status` | `PO_STATUS_LABELS` | Đã có |
| Nhà cung cấp | Tham chiếu | `supplier_code` | fetch `/api/suppliers` | **Thêm** (hiện chỉ có ô text mã trong nâng cao) |
| NSPT phụ trách | Tham chiếu | `nspt_id` | `fetchEmployeeOptions` | **Thêm** |
| Hồ sơ chứng từ | Chọn | `document_status` | `DOCUMENT_STATUSES` | **Thêm** |
| Ngày đặt | Khoảng ngày | `order_date_from/to` | — | **Thêm** (backend đã có range) |

**Bộ lọc nâng cao (giữ):** mã PYC (`pr_code`), mã MISA (`misa_code`), bộ phận
(`department_id`), số hóa đơn (`invoice_no` — lọc qua bảng con, **thêm vào UI** vì
hiện param có nhưng không có ô nào nhập), nhóm hàng (`item_group`), gấp nhiều điều kiện.

**Sắp xếp:**

| Nhãn | Cột | Hướng | Ghi chú |
|---|---|---|---|
| Mới nhất (mặc định) | `id` | ↓ | |
| Ngày đặt | `order_date` | ↓/↑ | |

> `amount` (tiền hàng) computed → không sort backend. Xử lý như PYC.

### 2.3 Yêu cầu báo giá (YCBG) — `survey-request-list-page.tsx`

**Chip nhanh:** `[Tháng này]` · `[Chờ xử lý]` (trạng thái đang mở).

**Thanh lọc nhanh đề xuất:**

| Chiều lọc | Dạng | Param | Nguồn | Ghi chú |
|---|---|---|---|---|
| Tìm mã phiếu | Tìm | `code` | — | Đã có |
| Công ty | Chọn | `company_id` | `useCompanies` | Đã có |
| Trạng thái | Chọn | `status` | `SR_STATUS_LABELS` | Đã có |
| Bộ phận | Tham chiếu | `department_id` | `fetchDepartmentOptions` | **Thêm** |
| Ngày tạo | Khoảng ngày | `request_date_from/to` | — | **Thêm** |

**Bộ lọc nâng cao (giữ):** người yêu cầu (`requester_id`), nhóm hàng / người phụ
trách dòng (`item_group`, `assignee` — **thêm**).

**Sắp xếp:** Mới nhất (`id` ↓, mặc định) · Ngày tạo (`request_date`). Màn này sort
chạy **end-to-end sạch nhất** (service không ghi đè).

### 2.4 Phiếu khảo sát — `survey-list-page.tsx`

**Chip nhanh:** `[Khảo sát NCC]` / `[Khảo sát SP]` (`survey_type`) · `[Chờ xử lý]`.

**Thanh lọc nhanh đề xuất:**

| Chiều lọc | Dạng | Param | Nguồn | Ghi chú |
|---|---|---|---|---|
| Tìm mã phiếu | Tìm | `code` | — | Đã có |
| Trạng thái | Chọn | `status` | `SURVEY_STATUS_LABELS` | Đã có |
| Loại khảo sát | Chọn | `survey_type` | `SURVEY_TYPE_LABELS` | **Thêm** (cần bổ sung vào FILTERABLE) |
| Nhóm hàng | Tìm/Chọn | `item_group` | — | **Thêm** |
| NSPT | Tìm | `nspt` | — | **Thêm** (lọc theo TÊN — phiếu chưa có `nspt_id`) |

**Bộ lọc nâng cao (giữ):** mã YCBG (`sr_code`), mã PYC (`pr_code`), nội dung chính
(`main_content`), mã hàng (`item_code`).

**Sắp xếp:** Mới nhất (`id` ↓, mặc định).

> Lưu ý dữ liệu: `nspt` phiếu khảo sát lọc theo **tên** (chưa có cột id), đổi sang id
> backend lặng lẽ bỏ điều kiện. `survey_type` hiện KHÔNG nằm trong `FILTERABLE` → phải
> thêm vào backend thì mới lọc được (xem mục 5).

---

## 3. PHÂN HỆ SẢN XUẤT

Cả 5 màn đang dùng `CrudListPage`: toolbar chỉ có **1 ô tìm + nút bộ lọc nâng cao**.
Cần bổ sung thanh lọc nhanh. `CrudListPage` cần được nâng để nhận thêm "ô lọc nhanh"
tuỳ biến (xem mục 5).

### 3.1 Hợp đồng — `contract-list-page.tsx`

Chiều dùng nhiều nhất của hợp đồng là **hiệu lực / hạn** (để gia hạn kịp) và **loại
hợp đồng / đối tác**.

**Chip nhanh:** `[Sắp hết hạn]` (`expiry=Sắp hết hạn`) · `[Còn hạn]` · `[Chưa ký]`
(`signed=false`).

**Thanh lọc nhanh đề xuất:**

| Chiều lọc | Dạng | Param | Nguồn | Ghi chú |
|---|---|---|---|---|
| Tìm mã/tên HĐ | Tìm | `title` (+ `code`) | — | Đã có (nên tìm cả `code`, hiện chỉ `title`) |
| Loại hợp đồng | Chọn | `contract_type` | 7 mã (CR-118) | **Thêm** |
| Bên ký kết | Chọn | `party_type` | NCC/Khách hàng/Khác | **Thêm** |
| Nhà cung cấp | Tham chiếu | `party_code` | fetch `/api/suppliers` | **Thêm** |
| Hiệu lực | Hiệu lực | `expiry` | Còn hạn/Sắp hết/Hết hạn | **Thêm** |
| Ngày hết hạn | Khoảng ngày | `end_date_from/to` | — | **Thêm** (backend đã có) |

**Bộ lọc nâng cao (giữ):** trạng thái (`status`), đã ký (`signed`), ngày ký
(`start_date`), tên đối tác (`party_name`).

**Sắp xếp:**

| Nhãn | Cột | Hướng | Ghi chú |
|---|---|---|---|
| Mới nhất (mặc định) | `id` | ↓ | |
| Ngày hết hạn | `end_date` | ↑ | Sắp hết hạn lên đầu — **hữu ích nhất** |
| Ngày ký | `start_date` | ↓ | |

> `expiry` là cột tính toán → không sort được; muốn "sắp hết hạn trước" thì sort theo
> `end_date` ↑. Sort backend của Hợp đồng **chạy được** (`apply_sort_from_request`).

### 3.2 Nhà cung cấp — `supplier-list-page.tsx`

**Thanh lọc nhanh đề xuất:**

| Chiều lọc | Dạng | Param | Nguồn | Ghi chú |
|---|---|---|---|---|
| Tìm tên/mã/MST | Tìm | `name` | — | Đã có (chỉ `name`; nên mở rộng OR sang `code`, `tax_code`) |
| Vai trò | Chọn | `supplier_type` | goods/transport | **Thêm** |
| Trạng thái | Chọn | `is_active` | Đang GD / Ngừng | **Thêm** |

**Bộ lọc nâng cao (giữ):** mã (`code`), MST (`tax_code`).

**Sắp xếp:** Tên A→Z (`name` ↑) · Mã (`code` ↑) · Mới nhất (`id` ↓, mặc định).

> **Cần sửa backend:** `service.list_suppliers` đang `order_by(Supplier.id.desc())`
> đè lên sort từ request → sort KHÔNG ăn. Phải bỏ order_by cứng, để
> `apply_sort_from_request` quyết (xem mục 5).

### 3.3 Sản phẩm & Vật tư — `product-list-page.tsx`

**Thanh lọc nhanh đề xuất:**

| Chiều lọc | Dạng | Param | Nguồn | Ghi chú |
|---|---|---|---|---|
| Tìm (mã/tên/mã HH) | Tìm | `search` | — | Đã có (OR 4 cột) |
| Phân loại (nhóm hàng) | Tham chiếu | `item_group` | fetch `/api/item-groups` | **Thêm** (đổi từ text thành combobox) |
| ĐVT | Chọn | `unit` | fetch `/api/units` | **Thêm** |
| Trạng thái | Chọn | `is_active` | Đang dùng / Ngừng | **Thêm** |

**Sắp xếp:** Mã (`code` ↑) · Tên (`name` ↑) · Mới nhất (`id` ↓, mặc định).

> **Cần sửa backend:** giống NCC — `service.list_products` đè `order_by(Product.id.desc())`.
> `item_group`/`unit` lưu là **chuỗi** (không phải FK) nên combobox chỉ để chọn giá trị
> chuỗi cho gọn, backend vẫn lọc LIKE.

### 3.4 Nhóm hàng — `item-group-list-page.tsx`

**Thanh lọc nhanh:** Tìm (`name`, đã có) · Trạng thái (`is_active`, **thêm**).
**Sắp xếp:** Mã · Tên · Mới nhất (mặc định). Sort backend chạy được (`apply_sort`).

### 3.5 Đơn vị tính — `unit-list-page.tsx`

**Thanh lọc nhanh:** Tìm (mở rộng `name` + `code`) · Trạng thái (`is_active`, **thêm**).
**Sắp xếp:** Mã · Tên · Mới nhất (mặc định). Sort backend chạy được.

---

## 4. Bảng tổng hợp "thêm gì ở mỗi màn"

| Màn | Lọc nhanh thêm | Sort thêm | Cần sửa backend? |
|---|---|---|---|
| PYC | Bộ phận, Ngày cần hàng, chip Gấp | need_date | Không |
| ĐMH | NCC, NSPT, Hồ sơ CT, Ngày đặt, chip Của tôi | order_date | Không |
| YCBG | Bộ phận, Ngày tạo | request_date | Không |
| Khảo sát | Loại KS, Nhóm hàng, NSPT | — | **Thêm `survey_type` vào FILTERABLE** |
| Hợp đồng | Loại HĐ, Bên ký, NCC, Hiệu lực, Ngày hết hạn | end_date, start_date | Không (search nên thêm `code`) |
| NCC | Vai trò, Trạng thái | name, code | **Bỏ order_by cứng ở service** |
| Sản phẩm | Nhóm hàng, ĐVT, Trạng thái | code, name | **Bỏ order_by cứng ở service** |
| Nhóm hàng | Trạng thái | code, name | Không |
| ĐVT | Trạng thái | code, name | Không |

---

## 5. Việc nền cần làm trước (dùng chung mọi màn)

1. **`DataTable` + `CrudListPage` chưa có sort.** Cần: thêm `sortable?` cho cột +
   trạng thái sort (cột đang sort, hướng) + nút "Sắp xếp"; `CrudListPage` và các page
   thu mua truyền `sort_by`/`sort_dir` vào `ListParams`. Không có bước này thì mọi mục
   "Sắp xếp" ở trên chưa chạy được.
2. **Ô lọc nhanh cho `CrudListPage`.** Hiện khung chỉ render 1 ô tìm; cần cho khai một
   mảng "ô lọc nhanh" (select/combobox/date-range) để 5 màn Sản xuất có thanh lọc ngoài.
3. **Control "Khoảng ngày + preset".** Một component dùng chung (Hôm nay/Tuần/Tháng/Quý)
   để PYC, ĐMH, YCBG, Hợp đồng đều xài.
4. **Backend — bỏ order_by cứng** trong `service.list_suppliers` và `service.list_products`
   để `apply_sort_from_request` có tác dụng (nếu không, sort NCC/Sản phẩm vô hiệu).
5. **Backend — thêm `survey_type` vào `FILTERABLE`** của module `survey` để lọc theo
   loại khảo sát.
6. **Chip nhanh "Đơn của tôi"** cần biết nhân sự của người đăng nhập (`assignee_id`/
   `nspt_id`) — lấy từ hồ sơ đăng nhập, map sang `nspt_id`.

---

## 6. Ghi chú phạm vi

- Tài liệu này CHỈ thiết kế, chưa code. Sau khi đại ca duyệt sẽ tách thành các CR nhỏ
  (nền sort/lọc nhanh trước, rồi từng màn) và ghi vào `change-log.md`.
- Không đụng phân hệ khác (Nhân sự, Tài chính, Kho, Hệ thống) trong đợt này.
- Cột tính toán không sort được là ràng buộc kỹ thuật, không phải thiếu sót — nêu rõ
  để lúc làm không hứa nhầm với người dùng.
