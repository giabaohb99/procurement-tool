# ĐỐI CHIẾU TỪNG TRƯỜNG — App đặt xe cũ ↔ ERP

> Đi kèm [README.md](README.md) và [mo-ta-ky-thuat.md](mo-ta-ky-thuat.md).
> Bản 1.0 — 15/09/2026. Dò theo mã nguồn thật, không phải theo trí nhớ.

Nguồn đối chiếu:
- App cũ: `app đặt xe/my-firebase-api/src/types/db.types.ts`, `src/types/enums.ts`, `src/config/request.config.ts`
- ERP: `backend/app/modules/vehicle_booking/model.py`, `backend/app/modules/seal_request/model.py`, `backend/app/modules/attachment/model.py`

Ký hiệu cột "Ghi chú":
- **[=]** khớp thẳng, chỉ đổi kiểu
- **[~]** khớp gần, phải xử lý thêm
- **[!]** **mất dữ liệu** hoặc phải bịa ra giá trị — đọc kỹ
- **[x]** không có chỗ chứa

---

## 1. Hình dạng chung của một phiếu

Bên app cũ, **cả ba loại phiếu nằm chung một nhánh** `requests`, phân biệt bằng trường `type`:

```
requests/<nanoid> = {
  id, createdAt, createdBy,
  type: "CAR_BOOKING" | "DELIVERY" | "SEAL_REQUEST",
  details: { ...khác nhau theo type... },
  approval: { workflowSnapshot, currentLevel, overallStatus, history[], pendingApproverUids[] }
}
```

Bên ERP là **hai bảng khác nhau**: `tab_vehicle_booking` (nhận `CAR_BOOKING` và `DELIVERY`) và `tab_seal_request` (nhận `SEAL_REQUEST`).

| App cũ | ERP | Ghi chú |
|---|---|---|
| `type = "CAR_BOOKING"` | `tab_vehicle_booking.request_type = 1` (TYPE_CAR) | [=] |
| `type = "DELIVERY"` | `tab_vehicle_booking.request_type = 2` (TYPE_DELIVERY) | [=] |
| `type = "SEAL_REQUEST"` | `tab_seal_request` | [~] bảng khác, xem mục 4 |
| `id` (nanoid) | `legacy_id` (cột mới) | [=] |
| — | `code` | [!] ERP **bắt buộc** có mã phiếu, app cũ không có. Sinh mới bằng bộ sinh mã sẵn có (`DX001`…) |
| `createdAt` (mili giây) | `created_at` | [~] đổi sang chuỗi ISO 20 ký tự |
| `createdBy` (UID Firebase) | `requester_id` | [!] UID Firebase **không dùng được**, phải tra qua email — xem mục 6 |
| `approval.overallStatus` | `status` | [~] bảng ánh xạ ở mục 5 |
| `approval.history[]` | `note` hoặc nhật ký dạng chữ | [!] ERP có bộ máy duyệt riêng, **không dựng lại phiên duyệt cũ** |
| `approval.workflowSnapshot` | — | [x] bỏ. Ghi lại thành chữ trong `note` nếu cần tra |
| `approval.currentLevel` | — | [x] bỏ |
| `approval.pendingApproverUids` | — | [x] bỏ |
| — | `is_deleted` | mặc định `false` |
| — | `company_id` | [!] app cũ không có khái niệm pháp nhân. **Bắt buộc khác `0`** (QĐ-G) — tra ba nấc, xem mo-ta-ky-thuat mục 8.3 |

---

## 2. Phiếu đặt xe công tác — `CAR_BOOKING`

Nguồn: `RequestDetailsCarBooking`.

| App cũ (`details.`) | ERP (`tab_vehicle_booking.`) | Ghi chú |
|---|---|---|
| `purpose` | `purpose` | [=] Text |
| `startLocation` | `start_location` | [~] ERP trần **255 ký tự** — phải cắt và ghi cảnh báo nếu dài hơn |
| `endLocation` | `end_location` | [~] trần 255 |
| `startTime` (mili giây) | `start_time` | [~] chuỗi ISO 20 ký tự |
| `endTime` (mili giây) | `end_time` | [~] chuỗi ISO 20 ký tự |
| `passengerCount` | `passenger_count` | [=] |
| `attendees` | `attendees` | [=] Text |
| `contactPhone` | `contact_phone` | [~] ERP trần **20 ký tự** (`sender_phone` lại trần 30 — lệch sẵn trong ERP, không phải lỗi đồng bộ) |
| `isRoundTrip` | `is_round_trip` | [=] |
| `notes` | `note` | [=] Text |
| `intermediateStops[]` | `stops` (Text JSON) | [!] mất một trường, xem mục 3 |
| `firstApproverUid` | `first_approver_id` | [!] UID Firebase → phải tra ra người ERP. Tra không ra thì để `0` |
| `brandId[]` | — | [!] chưa chốt, xem mục 10. Phiếu xe ít dùng thương hiệu hơn phiếu dấu |
| `dispatch.assignedVehicleId` | `assigned_vehicle_id` | [~] phải tra từ `legacy_id` sang mã xe ERP |
| `dispatch.assignedDriverId` | `assigned_driver_id` | [~] tra tương tự |
| `dispatch.dispatchedAt` | `dispatched_at` | [~] ISO |
| `dispatch.dispatchedBy` | `dispatched_by` | [~] tra người qua email |
| `dispatch.driverStatus` | `driver_status` | [~] bảng ánh xạ mục 5.2 |
| `dispatch.actualStartTime` | `actual_start_time` | [~] ISO |
| `dispatch.actualEndTime` | `actual_end_time` | [~] ISO |
| `dispatch.driverActionHistory[]` | — | [x] bỏ, hoặc gộp vào `note` dạng chữ |
| — | `is_self_drive`, `license_number`, `license_class` | [!] app cũ không có khái niệm **tự lái**. Nạp vào là `false` và để trống |
| — | `distance_km`, `cost` | [!] app cũ không ghi. Nạp vào là `0` |
| — | `approved_by`, `approved_at` | [~] moi từ `approval.history` — lấy bản ghi `action = "approved"` **cuối cùng**: `userId` và `timestamp` |
| — | `requester`, `requester_email`, `requester_phone`, `requester_role` | [~] lấy từ hồ sơ `users/<uid>` bên app cũ (`displayName`, `email`, `phone`), `requester_role` ghép từ `role` và tên phòng ban |
| — | `department_id` | [~] xem mo-ta-ky-thuat mục 8.2 |

---

## 3. Điểm dừng trung gian — chỗ mất dữ liệu đầu tiên

App cũ, kiểu `Stop`:

```ts
{ address: string; notes?: string; contactName?: string; contactPhone?: string }
```

ERP, kiểu `StopItem` trong `vehicle_booking/schema.py`:

```python
{ location: str; contact_name: str; contact_phone: str }
```

| App cũ | ERP | Ghi chú |
|---|---|---|
| `address` | `location` | [=] |
| `contactName` | `contact_name` | [=] |
| `contactPhone` | `contact_phone` | [=] |
| `notes` | — | [!] **không có chỗ chứa** |

Ba đường xử lý `notes`, chọn một:

1. **Nối vào `location`** — `"123 Lê Lợi (gọi trước 15 phút)"`. Đơn giản nhất, nhưng làm bẩn ô địa chỉ và không tách lại được.
2. **Gom hết ghi chú điểm dừng, nối vào `note` của phiếu** — `"Ghi chú điểm dừng: (1) gọi trước 15 phút; (2) cổng sau"`. Giữ được chữ, không bẩn ô địa chỉ.
3. **Thêm trường `notes` vào `StopItem`** của ERP. Sạch nhất, nhưng phải sửa schema và màn hình ERP.

Đề nghị **cách 3** nếu đợt này còn sửa được ERP — nó là một trường, chi phí nhỏ; đằng nào cũng hữu ích cho người dùng ERP. Không kịp thì lùi về cách 2.

**Một chỗ lệch nữa trong chính ERP:** comment ở `model.py` dòng 139 viết `stops` là "JSON danh sách chuỗi", nhưng schema thật lại là danh sách đối tượng `StopItem`. Lúc viết mã đọc/ghi phải theo **schema**, đừng theo comment.

---

## 4. Phiếu giao hàng — `DELIVERY`

Nguồn: `RequestDetailsDelivery`. **Lưu ý: tên trường ở đây khác hẳn `CAR_BOOKING`** — dễ chép nhầm.

| App cũ (`details.`) | ERP (`tab_vehicle_booking.`) | Ghi chú |
|---|---|---|
| `purpose` | `purpose` | [=] |
| `pickupLocation` | `start_location` | [~] **đổi tên**, trần 255 |
| `dropoffLocation` | `end_location` | [~] **đổi tên**, trần 255 |
| `startTime` | `start_time` | [~] ISO |
| `endTime` | `end_time` | [~] ISO |
| `itemName` | `goods_name` | [~] **đổi tên**, ERP trần **255** |
| `dimensions` | `goods_size` | [~] **đổi tên**, trần 255 |
| `senderName` | `sender_name` | [=] |
| `senderPhone` | `sender_phone` | [=] trần 30 |
| `recipientName` | `receiver_name` | [~] **recipient → receiver**, chỗ này rất dễ sai |
| `recipientPhone` | `receiver_phone` | [~] như trên |
| `specialInstructions` | `special_instructions` | [=] Text |
| `intermediateStops[]` | `stops` | [!] như mục 3 |
| `brandId[]`, `firstApproverUid`, `dispatch.*` | như mục 2 | |
| `itemWeight` | — | [!] **Có trong bộ kiểm tra hợp lệ** (`request.config.ts`) nhưng **không có trong định nghĩa kiểu**. Dữ liệu thật có thể có. ERP không có cột cân nặng → nối vào `goods_size` |
| — | `passenger_count`, `attendees`, `contact_phone`, `is_round_trip` | không dùng cho phiếu giao hàng, để mặc định |

**Việc phải làm trước khi viết mã:** mở dữ liệu thật trên Firebase, lấy vài chục phiếu `DELIVERY`, liệt kê **tất cả** khóa xuất hiện trong `details`. Định nghĩa kiểu của app cũ đã chứng minh là không đầy đủ (ca `itemWeight`), nên không được tin nó một mình.

---

## 5. Ánh xạ trạng thái

### 5.1. Trạng thái phiếu đặt xe / giao hàng

`RequestStatus` (app cũ) → hằng số `BK_*` (ERP):

| App cũ | ERP | Số | Ghi chú |
|---|---|---|---|
| `pending_approval` | `BK_PENDING` | 2 | [=] |
| `needs_correction` | `BK_RETURNED` | 8 | [=] |
| `fully_approved` | `BK_APPROVED` | 3 | [=] |
| `dispatched` | `BK_DISPATCHED` | 4 | [=] |
| `completed` | `BK_COMPLETED` | 5 | [=] |
| `rejected` | `BK_REJECTED` | 6 | [=] |
| `canceled` | `BK_CANCELLED` | 7 | [=] chú ý chính tả: app cũ một chữ `l`, ERP hai chữ |
| `pending_sealing` | — | — | [x] chỉ dùng cho phiếu đóng dấu |
| `sealed` | — | — | [x] như trên |
| `delivered_to_staff` | — | — | [x] như trên |
| — | `BK_DRAFT` | 1 | [!] app cũ **không có trạng thái nháp** — phiếu tạo ra là đã vào luồng duyệt. Không phiếu cũ nào rơi vào đây |

Ánh xạ này **kín cả hai chiều** cho bảy trạng thái đầu. Chiều ngược (ERP → app cũ) lật ngược đúng bảng trên; riêng `BK_DRAFT` thì **không gửi sang** app cũ.

### 5.2. Trạng thái tài xế

`DriverActionStatus` → `DRV_*`:

| App cũ | ERP | Số |
|---|---|---|
| (không có `dispatch`) | `DRV_NONE` | 0 |
| `pending_acceptance` | `DRV_WAITING` | 1 |
| `accepted` | `DRV_ACCEPTED` | 2 |
| `on_trip` | `DRV_ONGOING` | 3 |
| `completed` | `DRV_COMPLETED` | 4 |
| `rejected` | `DRV_REJECTED` | 5 |

Khớp một-một, không mất gì.

### 5.3. Trạng thái phiếu đóng dấu — QĐ-H

**Luồng thật bên app cũ có HAI nấc văn thư, không phải một:**

```
duyệt xong ──► pending_sealing ──► sealed ──► delivered_to_staff
               hồ sơ nằm chờ      văn thư    văn thư đã TRAO LẠI
               ở bàn văn thư      ĐÃ ĐÓNG    tập hồ sơ cho nhân
                                  DẤU lên    viên — kết thúc thật
                                  giấy
```

Hai nấc sau là hai nút bấm riêng: `POST /v1/admin/requests/:id/seal` ("Xác nhận đóng dấu") và `POST /v1/admin/requests/:id/deliver` ("Bàn giao hồ sơ") — `my-firebase-api/src/services/admin.service.ts:413` và `:451`.

Nói gọn: **`sealed` = dấu đã đóng · `delivered_to_staff` = giấy đã về tay người yêu cầu.**

ERP hiện chỉ có `SEAL_COMPLETED`, mà comment trong `seal_request/model.py:16` ghi rõ nó nghĩa là "Văn thư đã đóng dấu ngoài thực tế" — tức là khớp với `sealed`, **thiếu hẳn nấc bàn giao**.

**Chốt (QĐ-H): thêm `SEAL_DELIVERED = 8` vào ERP**, nhãn "Đã trả hồ sơ". Khi đó ánh xạ kín một-một cả hai chiều:

| App cũ | ERP | Số | Ghi chú |
|---|---|---|---|
| `pending_approval` | `SEAL_PENDING` | 2 | [=] |
| `needs_correction` | `SEAL_RETURNED` | 7 | [=] |
| `fully_approved` | `SEAL_APPROVED` | 3 | [~] xem chú thích dưới |
| `pending_sealing` | `SEAL_APPROVED` | 3 | [~] xem chú thích dưới |
| `sealed` | `SEAL_COMPLETED` | 4 | [=] |
| `delivered_to_staff` | `SEAL_DELIVERED` | 8 | [=] **cột mới theo QĐ-H** |
| `rejected` | `SEAL_REJECTED` | 5 | [=] |
| `canceled` | `SEAL_CANCELLED` | 6 | [=] |
| — | `SEAL_DRAFT` | 1 | [x] app cũ không có |

**Chỗ còn dồn, và vì sao chấp nhận được:** `fully_approved` và `pending_sealing` đều về `SEAL_APPROVED`. Hai trạng thái này bên app cũ thực chất là **cùng một tình huống** — duyệt xong, chờ văn thư — chỉ khác ở chỗ app cũ đánh dấu thêm một nhịp nội bộ. Chiều ngược luôn gửi `pending_sealing` (nấc sau), phiếu không kẹt. Ghi cờ `status_lossy` vào sổ cho những phiếu rơi vào ca này.

**Việc phải làm kèm QĐ-H** (nằm trong pha P7):
1. Thêm `SEAL_DELIVERED = 8` và nhãn vào `seal_request/model.py`;
2. Thêm hai cột `delivered_at`, `delivered_by` — song song với `completed_at`, `completed_by` đã có;
3. Thêm hành động "Bàn giao hồ sơ" cho văn thư trên màn ERP, chỉ bấm được khi phiếu đang ở `SEAL_COMPLETED`;
4. Rà lại các báo cáo và bộ lọc đang coi `SEAL_COMPLETED` là trạng thái cuối — giờ nó **không còn là cuối nữa**.

Điểm 4 là chỗ dễ sót nhất: mọi chỗ trong ERP đang hỏi "phiếu xong chưa" bằng cách so `status == SEAL_COMPLETED` sẽ **bỏ sót phiếu đã trả hồ sơ**. Phải tìm hết và đổi sang so với một bộ trạng thái kết thúc.

### 5.4. Một lỗi sẵn có của app cũ, ảnh hưởng tới đối soát

Bảng thống kê bên app cũ đếm "hoàn thành" **không nhất quán**:

- `admin.service.ts:54` đếm theo `DELIVERED_TO_STAFF`;
- `admin.service.ts:76` đếm theo `COMPLETED` — mà phiếu đóng dấu **không bao giờ vào trạng thái đó**, nên con số này luôn bằng `0`.

Nghĩa là số liệu trên bảng điều khiển cũ đang sai. Lúc làm việc đếm đối chiếu (pha P5) **đừng lấy con số đó làm chuẩn** — phải tự đếm từ dữ liệu gốc.

---

## 6. Phiếu đóng dấu — `SEAL_REQUEST`

Nguồn: `RequestDetailsSeal`.

| App cũ (`details.`) | ERP (`tab_seal_request.`) | Ghi chú |
|---|---|---|
| `purpose` | `purpose` | [=] Text |
| `notes` | `note` | [=] Text |
| `sealTypeId` (nanoid) | `seal_type_id` (số) | [!] **phải nạp trước danh mục loại dấu và dựng bảng tra**, xem mục 6.1 |
| `departmentId` (nanoid) | `department_id` (số) | [~] tra qua tên phòng |
| `firstApproverUid` | `first_approver_id` | [~] tra qua email |
| `attachedFileIds[]` | `tab_file` + `tab_file_link` | [~] xem mục 8 |
| `brandId[]` | `tab_seal_request_company` (nhiều dòng) | [!] **nếu chốt được thương hiệu = công ty thì đây là đường tốt nhất để lấy pháp nhân.** Xem mục 10 |
| `isSkipApproval` | — | [!] **không có chỗ chứa.** ERP có bộ máy duyệt riêng, cờ này vô nghĩa với nó. Ghi vào `note` để giữ dấu vết |
| `skipApprovalToLevel` | — | [!] như trên |
| — | `title` | [!] **ERP bắt buộc có tiêu đề, app cũ không có.** Bịa từ mục đích: lấy 120 ký tự đầu của `purpose` |
| — | `copies` | [!] số bản cần đóng dấu. App cũ không có → mặc định `1` |
| — | `completed_at`, `completed_by` | [!] mốc văn thư. Với phiếu cũ ở trạng thái `sealed`/`delivered_to_staff`, moi từ `approval.history` nếu tìm được; không thì để trống |
| — | `code` | [!] sinh mới, giống mục 1 |
| — | `company_id` + `tab_seal_request_company` | [!] app cũ **không có** pháp nhân. Nạp vào chỉ có **một** công ty (ba nấc theo QĐ-G), bảng nối ghi đúng một dòng. Phiếu dấu có sẵn `details.departmentId` nên **nấc 2 chạy tốt** cho loại phiếu này |
| — | `delivered_at`, `delivered_by` | [!] cột mới theo QĐ-H, cho nấc bàn giao hồ sơ |

### 6.1. Loại con dấu

App cũ có nhánh danh mục riêng cho loại dấu, khóa là `nanoid`. ERP có `tab_seal_type` khóa số. Trước khi nạp phiếu dấu, phải:

1. Đọc danh mục loại dấu bên app cũ;
2. Khớp theo **tên** với `tab_seal_type.name` (cột này `unique`);
3. Tên nào chưa có thì tạo mới trong ERP;
4. Giữ lại bảng tra `nanoid → id` để dùng lúc nạp phiếu.

Không khớp ra thì `seal_type_id = 0` và ghi cảnh báo — **không bỏ phiếu**.

### 6.2. Kết luận cho phiếu dấu

Bảng trên cho thấy phiếu dấu **không khớp gọn** như phiếu xe: bốn trường của app cũ không có chỗ chứa, bốn trường của ERP phải bịa ra. Vì vậy nó tách thành **pha riêng (P7)**, làm sau khi hai chiều của phiếu xe đã chạy êm, và **phải xem dữ liệu thật trước** để biết trong số 4 trường "không có chỗ chứa" kia, thực tế có bao nhiêu phiếu dùng tới.

---

## 7. Danh mục xe và tài xế

### 7.1. Xe

| App cũ (`vehicles/<id>`) | ERP (`tab_vehicle.`) | Ghi chú |
|---|---|---|
| `id` | `legacy_id` (cột mới) | [=] |
| `licensePlate` | `license_plate` | [!] app cũ cho **để trống**, ERP khai `unique` và **không cho trống**. Xe trống biển số phải bịa mã tạm (ví dụ `TAM-<id>`) và ghi cảnh báo |
| `model` | `model` | [=] trần 100 |
| `type` | `type` | [=] chuỗi tự do hai bên, trần 50 |
| `capacity` | `capacity` | [=] app cũ `number`, ERP `Float` — chứa được `2.4` |
| `status` | `status` | [=] hai bên cùng bộ chữ `available` / `on_trip` / `maintenance`. **Đây là cột hiếm hoi khớp nguyên xi** |
| `isExternal` | `is_external` | [=] |
| `externalCompany` | `external_company` | [=] trần 255 |
| — | `supplier_type`, `tax_code`, `tax_address`, `id_number` | [!] app cũ không có. Để mặc định (`SUPPLIER_NONE`, chuỗi rỗng) |

### 7.2. Tài xế

| App cũ (`drivers/<id>`) | ERP (`tab_driver.`) | Ghi chú |
|---|---|---|
| `id` | `legacy_id` (cột mới) | [=] |
| `name` | `name` | [=] |
| `phone` | `phone` | [~] ERP trần **20 ký tự** |
| `licenseNumber` | `license_number` | [=] trần 50 |
| `status` | `status` | [!] app cũ có `on_leave`, ERP khai mặc định `available` và ghi chú `available/on_trip/maintenance`. `on_leave` là **giá trị lạ** với ERP — chốt: đổi thành `maintenance` hoặc mở rộng danh sách bên ERP |
| `isExternal` | `is_external` | [=] |
| `externalCompany` | `external_company` | [=] |
| `userId` (UID Firebase) | `user_id` (số) | [!] tra qua email. Không ra thì để trống |
| — | `email` | [~] lấy từ hồ sơ `users/<userId>` bên app cũ nếu có |
| — | `license_class` (hạng GPLX) | [x] app cũ không có → để trống |
| — | `supplier_type`, `tax_code`, `tax_address`, `id_number` | [!] để mặc định |

### 7.3. Sau đợt nạp đầu tiên

Theo QĐ (README mục 5), **ERP làm chủ hai danh mục này**. App cũ vẫn giữ bản của nó cho các màn hình cũ, nhưng:
- ERP **không** đẩy xe/tài xế mới sang app cũ;
- lúc điều phối, ERP gửi sang **biển số, tên xe, tên tài xế, số điện thoại dạng chữ** (xem mo-ta-ky-thuat mục 5.2);
- nếu về sau nghiệp vụ đòi app cũ tự chọn xe thì mới phải nghĩ lại.

---

## 8. Tệp đính kèm

| App cũ (`files/<id>`) | ERP | Ghi chú |
|---|---|---|
| `id` | `tab_file.external_id` (cột mới) | [=] |
| `fileName` | `tab_file.filename` | [=] |
| `mimeType` | `tab_file.content_type` | [=] |
| `size` | `tab_file.size` | [=] |
| `r2Key` | `tab_file.file_key` | [~] khóa trỏ vào **kho R2 của app cũ**, không phải kho ERP |
| `createdAt` | `tab_file.created_at` | [~] ISO |
| `uploadedBy` | `tab_file.created_by` | [~] tra qua email, không ra thì `0` |
| `relatedRequestId` | `tab_file_link.entity_id` | [~] là mã ERP của phiếu, không phải nanoid |
| `isPublic`, `permissions.read[]` | — | [x] ERP dùng phân quyền riêng của mình |
| — | `tab_file.url` | để **rỗng** — không lưu đường dẫn ký sẵn vì nó hết hạn sau 1 giờ |
| — | `tab_file.sha256`, `thumb_key`, `thumb_url` | [x] để rỗng, vì không cầm tệp thật |
| — | `tab_file.source` (cột mới) | ghi `"datxe"` |
| — | `tab_file_link.entity` | `"seal_request"` hoặc `"vehicle_booking"` |
| — | `tab_file_link.doc_type`, `sort_order`, `purchase_order_id` | để mặc định |

Tệp đính kèm hiện chỉ xuất hiện ở **phiếu đóng dấu** (`attachedFileIds`). Phiếu đặt xe và giao hàng bên app cũ không có trường tệp. Nghĩa là mục này gắn liền với pha P7, trừ khi sau này app cũ thêm tệp cho phiếu xe.

---

## 9. Người dùng và phòng ban — tra chứ không nạp

Theo QĐ-D, **không đồng bộ tài khoản**. Nhưng vẫn cần nạp **bảng tra một lần** để dịch UID Firebase sang người của ERP:

| App cũ | Dùng để làm gì |
|---|---|
| `users/<uid>.email` | Chìa khóa duy nhất nối hai hệ. Chuẩn hóa: cắt khoảng trắng, đổi hết chữ thường |
| `users/<uid>.displayName` | Điền `requester` khi không tra ra người ERP |
| `users/<uid>.phone` | Điền `requester_phone` |
| `users/<uid>.departmentId` → `departments/<id>.name` | Khớp với `tab_department.name` |
| `users/<uid>.role` | **Không** mang sang. Quyền dùng của ERP |
| `users/<uid>.driverId` | Nối `tab_driver.user_id` |
| `users/<uid>.managerId` | Không dùng. ERP có cây quản lý riêng |
| `users/<uid>.fcmTokens` | Không dùng. ERP có kênh thông báo riêng |

Cách làm: dựng một bảng tra tạm trong bộ nhớ lúc chạy nạp (`uid → email → employee_id`), **không tạo bảng mới trong DB**. Đường đồng bộ thường ngày thì tra theo email có sẵn trong gói dữ liệu gửi sang.

---

## 10. Thương hiệu bên app cũ là cái gì bên ERP — H-05

Câu hỏi ban đầu đặt là "thương hiệu ≈ phòng ban?". Dò mã nguồn thì **bằng chứng chỉ sang công ty (pháp nhân)**, không phải phòng ban.

### 10.1. Thương hiệu làm gì trong app cũ

Nó **quyết định ai duyệt pháp lý**. Luồng duyệt phiếu đóng dấu có kiểu người duyệt `CONDITIONAL_BRAND_LEGAL` (`approval.service.ts:56-68`): tới bước đó, hệ đọc `details.brandId`, tra sang `brands/<id>.legalBrandUids` — danh sách thành viên phòng pháp chế **của thương hiệu đó** — và giao phiếu cho họ. Không tra ra thì lùi về danh sách mặc định của bước.

Duyệt xong cấp 1 thì hệ còn báo email cho `brandManagerUid` — người quản lý thương hiệu (`approval.service.ts:187-194`, `:234`).

Tóm lại thương hiệu không phải một nhãn để hiển thị. Nó là **cái định tuyến phiếu tới người ký**.

### 10.2. Vì sao là công ty chứ không phải phòng ban

| Điểm | Thương hiệu (app cũ) | Công ty (ERP) | Phòng ban (ERP) |
|---|---|---|---|
| Định tuyến người ký | `legalBrandUids` — pháp chế riêng | pháp nhân quyết định giám đốc / pháp chế ký | trưởng bộ phận, khác tầng |
| Số lượng trên một phiếu | `brandId` là **mảng** | `tab_seal_request_company` **nhiều-nhiều** | `department_id` chỉ **một** |
| Người đứng đầu | `brandManagerUid` | `legal_representative_id` | `manager_id` |
| Logo | `logoUrl` | `logo` | không có |

Hai dòng đầu là quyết định. Đặc biệt là **số lượng**: `brandId` nhiều, `department_id` một. Nếu coi thương hiệu là phòng ban thì phiếu hai thương hiệu **không có chỗ chứa**.

Thêm một lý lẽ nữa: app cũ **đã có phòng ban riêng rồi** (`departments`, và phiếu dấu có sẵn `details.departmentId`). Nếu thương hiệu cũng là phòng ban thì app cũ đang có hai thứ trùng nhau — không hợp lý.

### 10.3. Chốt thế nào

Chưa chốt được bằng mã nguồn, phải xem dữ liệu thật. Phép thử, làm được trong một buổi:

1. Lấy toàn bộ nhánh `brands` trên Firebase (chỉ cần `id`, `name`);
2. Lấy `tab_company` (`id`, `name`, `short_name`) và `tab_department` (`id`, `name`) của ERP;
3. So tên, đếm xem khớp bên nào nhiều hơn;
4. Đọc `legalBrandUids` của vài thương hiệu, xem những người đó bên ERP thuộc pháp nhân nào.

**Nếu khớp `tab_company`** — đây là kết quả tốt nhất có thể: phiếu dấu cũ có pháp nhân **chính xác ngay từ `brandId`**, không phải đoán qua ba nấc của QĐ-G nữa. Lúc đó thêm một nấc 0 vào quy tắc tra pháp nhân:

```
nấc 0 (chỉ phiếu dấu): brandId → tra bảng thương hiệu → company_id   ← chính xác nhất
nấc 1: hồ sơ nhân sự người tạo
nấc 2: phòng ban
nấc 3: mặc định id 1
```

Và `brandId` nhiều thương hiệu thì đổ thành **nhiều dòng** `tab_seal_request_company` — khớp đúng cấu trúc ERP, không mất gì.

**Nếu khớp `tab_department`** thì dùng nó để điền `department_id`, và pháp nhân vẫn chạy ba nấc như cũ.

**Nếu không khớp bên nào** thì thương hiệu là khái niệm riêng của app cũ, đổ thành chữ vào `note` và chấp nhận mất.

### 10.4. Lấy được một nửa dữ liệu thật — 15/09/2026

Đã lấy được hai danh sách bên ERP (dev). Còn thiếu danh sách `brands` bên Firebase, nên H-05 **vẫn treo**, nhưng đã lộ ra một điều quan trọng: **đại ca đoán "thương hiệu là phòng ban" không sai — bên ERP, phòng ban và pháp nhân đang trùng tên nhau.**

**14 pháp nhân:** DEGO Holding (`id 1`, mã `DEGO`) · IDA Global · ABA · iCare · NPP Dr Xanh · HKD Dr Xanh · Bamboo Việt Nam · N2SBIO · NN DEGO · NN ABA · AGRIPLANT · SAM · AGRICARE · DEGO HOLDING (`id 16`, dòng trùng).

**18 phòng ban:** Xây dựng · Dego Organic · Dego Lab · N2SBIO · Điều phối · ABA Chemical · Thiết kế · Icare · IDA Global · Bamboo · Dr.Xanh · Kế toán · Nhân sự · Lập trình & IT nội bộ · Kiểm soát kế hoạch · Hành chính · Sản xuất - Thu mua · Phòng Demo Thu Mua.

Xếp cạnh nhau thì danh sách phòng ban gồm **hai loại trộn lẫn**:

| Loại | Ví dụ | Có pháp nhân cùng tên không |
|---|---|---|
| Phòng chức năng | Kế toán · Nhân sự · Hành chính · Thiết kế · Điều phối · Kiểm soát kế hoạch · Lập trình & IT · Xây dựng · Sản xuất - Thu mua | Không |
| Đơn vị kinh doanh / thương hiệu | **N2SBIO · ABA Chemical · Icare · IDA Global · Bamboo · Dr.Xanh** | **Có, 6/6 khớp** |
| Thương hiệu chưa có pháp nhân | **Dego Organic · Dego Lab** | Không — nhiều khả năng là thương hiệu của Dego Holding |

Nghĩa là **sáu cái tên vừa là phòng ban vừa là pháp nhân**, và hai cái (Dego Organic, Dego Lab) chỉ tồn tại ở dạng phòng ban. Khi lấy được danh sách `brands` mà nó trùng nhóm này thì cách xử đúng là **đổ về CẢ HAI** chứ không chọn một bên:

- `brandId` → `company_id` (qua bảng tra tên → pháp nhân) — để phiếu chạy đúng giám đốc;
- `brandId` → `department_id` (qua bảng tra tên → phòng ban) — để phiếu nằm đúng nhóm khi xem danh sách.

Thương hiệu nào không có pháp nhân cùng tên (kiểu Dego Lab) thì lấy pháp nhân của **công ty mẹ đang giữ thương hiệu đó** — với dữ liệu hiện tại là Dego Holding `id 1`, nhưng phải hỏi lại chứ đừng đoán.

Bảng tra này **phải là dữ liệu, không phải mã cứng**: một bảng nhỏ (`legacy_brand_id`, `company_id`, `department_id`) để sau này thêm thương hiệu thì sửa dòng chứ không phải sửa mã. Tra không thấy thì ghi cờ cảnh báo vào sổ đồng bộ và lùi về ba nấc cũ.

### 10.5. ĐÓNG H-05 — thương hiệu CHÍNH LÀ pháp nhân, khớp 11/11

Đại ca gửi ảnh ba màn quản trị của **app cũ** ngày 15/09/2026. Màn đó tên là **"Quản lý Công ty — Quản lý thông tin công ty, hộ kinh doanh"**, mà `grep` cả `src/` của app cũ thì **không có collection `companies` nào** — nên màn đó chính là `brands`. Nói cách khác: **bên app cũ, "thương hiệu" và "công ty" là MỘT thứ**, chỉ khác tên gọi trên màn hình. Mấy cột trên màn khớp đúng kiểu `Brand`: *Logo* = `logoUrl` · *Quản lý* = `brandManagerUid` · *Mô tả* = `description` · *Trạng thái Hiện* = `isHidden` · *Văn thư* = `legalBrandUids`.

Và **tên thương hiệu có kèm mã số thuế** ("CÔNG TY TNHH DƯỢC PHẨM ICARE - 0315593265"), nên đối chiếu được chính xác, không phải so tên mờ:

| Thương hiệu app cũ (MST nằm trong tên) | `tab_company` ERP | Khớp bằng |
|---|---|---|
| DƯỢC PHẨM ICARE — 0315593265 | `id 5` ICARE | **mã số thuế** |
| SX & XNK HÓA CHẤT NÔNG NGHIỆP DEGO — 0318430011 | `id 10` NN DEGO | **mã số thuế** |
| HÓA CHẤT NÔNG NGHIỆP ABA — 1801818328 | `id 11` NN ABA | **mã số thuế** |
| N2SBIO VIỆT NAM — 0318776965 | `id 9` N2SBIO | **mã số thuế** |
| PHÂN BÓN NHẬP KHẨU AGRICARE — 0313538685 | `id 14` AGC | **mã số thuế** |
| DEGO HOLDING — 1801722464 | `id 1` DEGO | **mã số thuế** (xem cảnh báo dưới) |
| SẢN XUẤT HÓA CHẤT ABA — 0316342296 | `id 3` ABA | **mã số thuế** |
| XNK IDA GLOBAL — 0314562909 | `id 2` IDA | **mã số thuế** |
| XNK SX TM BAMBOO VIỆT NAM — 0318629897 | `id 8` BAMBOO | **mã số thuế** |
| NHÀ PHÂN PHỐI DR.XANH — ~~8549195602~~ | `id 6` NPP DR.XANH — MST đúng **`578010406`** | **tên** (MST app cũ hỏng, xem QĐ-K) |
| HỘ KINH DOANH DR.XANH — ~~8507408344-001~~ | `id 7` HỘ KD DR.XANH — MST đúng **`578005750`** | **tên** (MST app cũ hỏng, xem QĐ-K) |

**11/11 thương hiệu đều có pháp nhân tương ứng bên ERP.** Chín dòng khớp thẳng bằng mã số thuế, hai dòng Dr.Xanh gắn tay theo tên.

> **ĐÓNG H-09 ngày 16/09/2026 — QĐ-K: ERP là bên đúng.** Đại ca: *"mình tin hệ thống erp nhé, cái kia data bị miss"*. Vậy `578010406` và `578005750` là mã số thuế thật của hai pháp nhân Dr.Xanh; hai chuỗi số nhúng trong tên thương hiệu bên app cũ là **dữ liệu hỏng**, không được dùng để đối chiếu và cũng không được chép ngược sang ERP.

⚠️ **Hệ quả quan trọng hơn hai dòng Dr.Xanh: BẢNG TRA PHẢI KHỚP BẰNG `id`, KHÔNG KHỚP BẰNG TÊN.**

Bảng ở trên là công cụ **đối chiếu một lần bằng mắt**, không phải thuật toán chạy lúc đồng bộ. Ba lý do không được biến nó thành hàm so chuỗi:

1. **Tên bên app cũ nay đã biết là có thể sai.** Mà sai thì có ngày ai đó vào sửa cho đúng — sửa xong là mọi phép so tên trượt sạch, im lặng, và phiếu rơi xuống công ty mặc định `id 1`.
2. **Mã số thuế cũng không dùng làm khóa được**, vì nó nằm *trong* chuỗi tên (`"CÔNG TY TNHH DƯỢC PHẨM ICARE - 0315593265"`) chứ không có ô riêng — phải cắt chuỗi mới lấy ra, mà quy ước viết dấu gạch đó không có gì bảo đảm.
3. ERP có **hai dòng cùng mã số thuế `1801722464`** (`id 1` và `id 16`, xem H-08) — tra bằng mã số thuế ra hai kết quả.

Nên bảng tra chốt là **`brandId` (chuỗi khóa Firebase) → `tab_company.id`**, khai thành một bảng cố định trong mã nguồn (hoặc `tab_company.legacy_brand_id`), lập một lần rồi không đổi theo tên. **Thiếu đúng thứ này:** ba ảnh màn quản trị đại ca gửi chỉ có **tên**, không có `id` — phải kết xuất nhánh `brands` từ Firebase mới lập được bảng. Đó là việc chặn P0, ghi ở [TIEN-DO.md](TIEN-DO.md).

ERP có dư ba dòng: **AGRIPLANT (`id 12`)** và **SAM GROUP (`id 13`)** không có mặt trong app cũ (hai pháp nhân này không dùng app đặt xe — bình thường), cùng dòng **DEGO HOLDING trùng (`id 16`)**.

**Bằng chứng cứng cho H-08:** `id 1` và `id 16` có **cùng mã số thuế `1801722464`**. Không còn là "trùng tên nghi ngờ" nữa — chắc chắn là một pháp nhân bị nhập hai lần. Giữ `id 1` như đã chốt, và `COMPANY_ALIASES` là bắt buộc cho tới ngày dọn.

### 10.6. Cả BA loại phiếu đều mang `brandId` — nấc 0 áp cho tất cả

Bản trước em viết "nấc 0 chỉ dành cho phiếu dấu". **Sai.** Đọc lại `types/db.types.ts` thì cả ba đều có:

| Kiểu phiếu | Dòng | Trường |
|---|---|---|
| `RequestDetailsCarBooking` | 240 | `brandId?: string[]` |
| `RequestDetailsDelivery` | 264 | `brandId?: string[]` |
| `RequestDetailsSeal` | 277 | `brandId?: string[]` + `departmentId` |

Nghĩa là **mọi phiếu bên app cũ đều tự mang pháp nhân của nó**, không cần suy ra từ hồ sơ người tạo. Đây là đường lấy công ty chính xác nhất và nó phủ cả bốn nhóm dữ liệu trong phạm vi.

Hai điều phải cẩn thận:

**(1) `brandId` là MẢNG, mà phiếu xe bên ERP chỉ có một cột `company_id`.** Phiếu dấu thì không sao — đổ thành nhiều dòng `tab_seal_request_company`. Phiếu xe / giao hàng nhiều thương hiệu thì phải chọn một: lấy phần tử đầu, và **ghi cờ cảnh báo `multi_brand` vào sổ đồng bộ** kèm danh sách đầy đủ, để lọc ra xem lại. Đừng im lặng bỏ bớt.

**(2) `brandId` là trường TÙY CHỌN (`?`).** Chưa biết thực tế bao nhiêu phần trăm phiếu có điền. Phải đếm trên dữ liệu thật trước khi bỏ hẳn ba nấc cũ — ba nấc đó vẫn giữ làm đường lùi.

---

### 10.7. ĐÓNG H-10 ngày 16/09/2026 — tạo đủ phòng ban, giữ nguyên tên app cũ (QĐ-L)

Đại ca chốt: *"có thể thêm phòng ban cho đủ với app cũ nhé, bạn cứ tạo như phòng ban trên app cũ nhé, ví dụ như N2AGRO-KT thì để nguyên như vậy."*

Nghĩa là **tạo thêm 8 dòng vào `tab_department`, tên chép đúng từng ký tự như app cũ đang ghi**:

| # | Tên tạo bên ERP | Ghi chú |
|---|---|---|
| 1 | Agricare | trùng tên pháp nhân `id 14` AGRICARE — **vẫn tạo**, xem cảnh báo dưới |
| 2 | N2AGRO | chưa có pháp nhân cùng tên |
| 3 | N2AGRO-KT | **giữ nguyên dấu gạch**, không tách thành "Kế toán N2AGRO" |
| 4 | Mua Hàng | giữ nguyên cách viết hoa của app cũ, không đổi thành "Mua hàng" |
| 5 | Dego Agrochem | chưa có pháp nhân cùng tên |
| 6 | Pháp Lý | app cũ viết hoa chữ L, ERP chưa có phòng này |
| 7 | Dego Holding | trùng tên pháp nhân `id 1` **và** `id 16` |
| 8 | R&D | giữ nguyên ký tự `&` |

`tab_department` bên ERP: **18 → 26 dòng**.

**Luật chép tên, ba điều, cố ý ngặt:**

1. **Chép nguyên văn**, kể cả chỗ viết hoa lạ, dấu gạch, ký tự `&`. Lý do không phải hình thức: tới giai đoạn 2 người dùng mở ERP ra và tìm cái tên họ quen. "Mua Hàng" thành "Mua hàng" thì họ vẫn nhận ra, nhưng "N2AGRO-KT" thành "Kế toán N2AGRO" thì có người chọn nhầm sang phòng Kế toán chung — và không ai phát hiện ra cho tới lúc chạy báo cáo.
2. **Không gộp.** Bốn dòng trùng tên pháp nhân trông rất giống chỗ đáng gộp, nhưng gộp là **phán đoán**, mà phán đoán sai thì im lặng.
3. **Không sửa tên phòng cũ bên ERP cho giống app cũ.** Đây là chiều một: app cũ thiếu gì thì ERP thêm nấy. 18 dòng sẵn có đứng yên.

⚠️ **CẢNH BÁO — bốn dòng trùng tên pháp nhân là một cái bẫy đã giăng sẵn.** Sau đợt này `tab_department` sẽ có **mười** cái tên vừa là tên phòng vừa là tên pháp nhân (6 cái cũ — N2SBIO · ABA Chemical · Icare · IDA Global · Bamboo · Dr.Xanh — cộng 4 cái mới). Rất dễ có người viết một hàm "tra pháp nhân theo tên phòng ban" vì thấy nó khớp tới 10 chỗ. **Cấm.** Pháp nhân lấy ở **nấc 0 từ `brandId`** (QĐ-G + mục 10.6), phòng ban chỉ để hiển thị và gom nhóm. Trùng tên là **trùng tên**, không phải quan hệ.

**Hai chi tiết kỹ thuật em tự quyết, ghi ra đây để đại ca bác nếu thấy sai:**

- **`company_id` của 8 dòng mới để `0`**, giống hệt 18 dòng đang có (đo 15/09: 0/18 dòng có pháp nhân, `tab_department_company` rỗng sạch). Không điền, vì nấc 0 đã lo pháp nhân rồi; điền vào là dựng thêm một nguồn sự thật thứ hai cho cùng một câu hỏi.
- **Mỗi dòng mang `legacy_id`** = khóa Firebase của phòng ban bên app cũ. Không phải để hiển thị, mà để phiếu cũ trỏ được về đúng dòng **kể cả khi sau này ai đó đổi tên phòng**. Đây cũng là lý do phải kết xuất nhánh `departments` — ba ảnh màn quản trị chỉ cho tên, không cho khóa.

**Tạo bằng script, không tạo tay.** Lý do: 8 dòng gõ tay thì gõ sai một ký tự là hỏng đúng thứ vừa đặt luật ở trên, và còn phải chạy hai lần (dev trước, prod sau — H-03). Script chỉ **thêm**, chạy lại được, khớp theo `legacy_id`.

### 10.8. SỐ ĐO THẬT — bản kết xuất toàn bộ Firebase ngày 16/09/2026

Đại ca kết xuất **cả cơ sở dữ liệu** chứ không riêng hai nhánh (9,82 MB, 13 nhánh gốc). Mọi con số dưới đây đo trên bản đó, không phải ước lượng.

| Nhánh | Số bản ghi | Dùng vào việc gì |
|---|---|---|
| `requests` | **1 313** | Toàn bộ phiếu từ ngày mở app |
| `notifications` | 12 856 | Bỏ qua — đại ca dặn, và ERP có bộ thông báo riêng |
| `files` | 1 571 | Tệp đính kèm, nối bằng link (QĐ-E) |
| `users` | 136 | 131 còn hoạt động, 5 đã tắt |
| `departments` | 22 | Dựng `legacy_id` |
| `brands` | 11 | Dựng bảng tra pháp nhân |
| `drivers` / `vehicles` | 13 / 13 | Danh mục xe, tài xế |
| `approval_workflows` | 4 | `wf_car_booking_01` · `wf_delivery_01` · `workflow_seal_v1` · `wf_purchase_01` |

#### A. BẢNG TRA THƯƠNG HIỆU — khóa Firebase, dùng làm nguồn khớp duy nhất (QĐ-K)

| `brandId` (khóa Firebase) | Tên trong app cũ | Số lượt phiếu |
|---|---|---|
| `aFIQKCJMuLaG5geoO9qAy` | CÔNG TY TNHH DEGO HOLDING - 1801722464 | 465 |
| `dFp8B9bCoB-p7cV1hZtxZ` | CÔNG TY TNHH XUẤT NHẬP KHẨU IDA GLOBAL - 0314562909 | 413 |
| `bNWp5G8VCYA96_0L4HrGF` | CÔNG TY TNHH SẢN XUẤT HÓA CHẤT ABA - 0316342296 | 204 |
| `0ih2D3OB1r3QuxHIz4Wtc` | CÔNG TY TNHH DƯỢC PHẨM ICARE - 0315593265 | 145 |
| `oTrZVEVO-y0udrtUvvE6E` | CÔNG TY TNHH XNK SX TM BAMBOO VIỆT NAM - 0318629897 | 94 |
| `VCdzxAf97CslKsN3xyHUL` | CÔNG TY TNHH N2SBIO VIỆT NAM - 0318776965 | 71 |
| `Uq93UP_ftNNIKIJyCRqId` | CÔNG TY TNHH HÓA CHẤT NÔNG NGHIỆP ABA - 1801818328 | 67 |
| `W3d0nCYf0tvE07gDZriAZ` | CÔNG TY TNHH PHÂN BÓN NHẬP KHẨU AGRICARE - 0313538685 | 56 |
| `8OuHN2oYKo8RjvYvAjIM0` | CÔNG TY TNHH SX VÀ XNK HÓA CHẤT NÔNG NGHIỆP DEGO - 0318430011 | 34 |
| `7cbpgbE2ixRnfjMuy_fld` | NHÀ PHÂN PHỐI DR.XANH - ~~8549195602~~ (MST hỏng, QĐ-K) | 28 |
| `lHkjAyl9Qf3e3qWXUuXGG` | HỘ KINH DOANH DR.XANH - ~~8507408344-001~~ (MST hỏng, QĐ-K) | 14 |

Cột trái là thứ mã đồng bộ khớp. Cột giữa **chỉ để người đọc nhận ra**, không được dùng trong mã.

#### B. 22 PHÒNG BAN — khóa Firebase

| `departmentId` | Tên | Bên ERP |
|---|---|---|
| `-GmRqStpzB_mMIyXCuzbl` | N2SBIO | có |
| `0VVUBFa_kKJgrn3ou6mIE` | Nhà Máy Dego Organic | có |
| `4QD0-fGvE3_PJ_-z8k3FP` | Agricare | **tạo mới** |
| `AB_7o-LLqPMVQqAscudjp` | Bamboovietnam | có |
| `B956VINcgQIUC-lHPwZkU` | Dr.Xanh | có |
| `BZRVRaBc9LhaUf-k7pOpB` | Lập Trình & IT Nội Bộ | có |
| `CbS3lW5zVrgaWLYOPJtDe` | N2AGRO-KT | **tạo mới** |
| `GF7IkeBlMQE2mc8rlCC0t` | Hành Chính | có |
| `GGox3WkurI7OiwWJd7WeN` | iCare | có |
| `GrOznia62mMTQTBxerkU3` | Điều Phối | có |
| `JBFJBjnqKatWgF4gZg7bB` | N2AGRO | **tạo mới** |
| `TN7f5_gA2B57LwYURwjhE` | Mua Hàng | **tạo mới** |
| `TR_Mf8x3J1pAespNP0f-G` | Dego Agrochem | **tạo mới** |
| `URhjgJvbpYOIaSlbX1J67` | Thiết Kế | có |
| `dept_ke_toan` | Kế Toán Thuế | có |
| `dept_kinh_doanh` | Pháp Lý | **tạo mới** |
| `dept_ky_thuat` | Sản Xuất | có |
| `hzFUa5BseK9zq15WUzVna` | Dego Holding | **tạo mới** |
| `j_nBJLVUcveZdX3mitV4I` | R&D | **tạo mới** |
| `lw8ywTnkkXyU_uO14TF9v` | ABA Chemical | có |
| `qQH8iMN2OfiyFN-LNrpBz` | IDA Global | có |
| `z6ps_mZ_7e7D4oJuq81FY` | Nhân Sự | có |

⚠️ **Ba dòng cuối bảng có khóa gõ tay** (`dept_ke_toan` · `dept_kinh_doanh` · `dept_ky_thuat`), và **một trong ba đã bị đổi tên**: khóa ghi `kinh_doanh` nhưng tên nay là **Pháp Lý**. Đây là bằng chứng chạy được, không phải suy đoán, cho luật ở mục 10.5: **tên phòng ban trôi, khóa thì không.** `legacy_id` là bắt buộc.

#### C. NĂM PHÁT HIỆN LÀM ĐỔI KẾ HOẠCH

**C-1. KHÔNG CÓ MỘT PHIẾU MUA HÀNG NÀO.** 1 313 phiếu chia đúng ba loại: `SEAL_REQUEST` **946** · `CAR_BOOKING` **321** · `DELIVERY` **46**. Luồng `wf_purchase_01` có khai trong `approval_workflows` nhưng **chưa ai từng nộp một phiếu nào qua nó**. Nghĩa là nghĩa vụ *"kết xuất bản tổng hợp phiếu Mua hàng"* của **QĐ-M tự tiêu** — không có gì để tổng hợp. Bước 6 của P8 bỏ, điều kiện giai đoạn 2 tương ứng bỏ. Ba loại phiếu trong phạm vi đồng bộ **chính là toàn bộ dữ liệu app cũ**.

**C-2. `brandId` LÀ MỘT MẢNG, KHÔNG PHẢI MỘT GIÁ TRỊ.** Đây là chỗ đắt nhất. Phân bố độ dài:

| Số thương hiệu trên một phiếu | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| Số phiếu | 1 190 | 66 | 25 | 5 | 6 | 9 | 7 | 4 | 1 |

**123 phiếu (9,4%) thuộc từ hai pháp nhân trở lên** — 121 phiếu dấu, 2 phiếu giao hàng, 0 phiếu đặt xe. Hợp lý về nghiệp vụ: một lượt đóng dấu có thể đóng cho giấy tờ của nhiều công ty cùng lúc. Nhưng `tab_*.company_id` bên ERP là **một cột số**, và `apply_scope` lọc theo đúng cột đó. Nạp một phiếu 9 thương hiệu vào một cột thì **tám pháp nhân còn lại biến mất**, và người của tám công ty đó không thấy phiếu liên quan tới mình. Nhưng ERP **đã có sẵn** bảng nối `tab_seal_request_company` cho phiếu dấu, và phạm vi lọc theo bảng nối đó — nên 121/123 ca không mất gì. Chỉ còn **2 phiếu giao hàng** phải xử theo cách đã chốt từ trước. Xem mục 10.9.

**C-3. PHIẾU ĐẶT XE VÀ GIAO HÀNG KHÔNG CÓ PHÒNG BAN.** `departmentId` chỉ tồn tại trong `details` của `SEAL_REQUEST` — **946/946**. `CAR_BOOKING` **0/321**, `DELIVERY` **0/46**. QĐ-G nói phiếu bắt buộc có phòng ban, nên 367 phiếu này phải suy ra. Tin tốt: suy được **367/367** qua `createdBy` → `users[uid].departmentId`, vì **cả 136 người dùng đều có `departmentId` hợp lệ** và **1 313/1 313 phiếu có `createdBy` tra ra người thật**. Không phiếu nào rơi xuống giá trị mặc định.

**C-4. DỮ LIỆU THAM CHIẾU SẠCH TUYỆT ĐỐI.** 0 phiếu thiếu `brandId` · 0 tham chiếu thương hiệu chết · 0 `departmentId` rỗng hoặc chết · 0 `createdBy` mồ côi. Nghĩa là **nấc 0 của QĐ-G phủ 100%**, và ba nấc tra dự phòng (phòng ban → hồ sơ người tạo → Dego Holding) trở thành **lưới an toàn cho phiếu MỚI phát sinh**, không phải đường chạy chính của đợt nạp lịch sử. Vẫn giữ, nhưng hạ kỳ vọng xuống đúng vai trò đó.

**C-5. HAI CÂU HỎI KỸ THUẬT TỰ ĐÓNG BẰNG SỐ ĐO.**

- **`StopItem` PHẢI CÓ `notes`.** 44 phiếu có điểm dừng giữa đường, tổng **59 điểm dừng**, trong đó **25 điểm có ghi chú** — và ghi chú là nội dung thật, không phải rác (*"Rước sale"*). Bỏ trường này là mất 25 mẩu thông tin không tái tạo được. Mỗi điểm dừng còn có `address` · `contactName` · `contactPhone`.
- **`driver.status` chỉ có đúng một giá trị: `available` (13/13).** Không có bản ghi nào mang `on_leave` hay trạng thái khác. Nên ánh xạ thế nào cũng **không mất dữ liệu nào** — chọn cách đơn giản nhất và ghi lại, đừng dựng bảng ánh xạ cho một tập một phần tử. Lưu ý 2/13 tài xế là **người ngoài** (`isExternal` + `externalCompany`), 12/13 có `userId` nối về tài khoản.

### 10.9. Một phiếu thuộc nhiều pháp nhân — ĐÃ CÓ LỜI GIẢI, chỉ còn đúng 2 phiếu cần quyết

Số đo C-2 cho ra 123 phiếu thuộc từ 2 tới 9 pháp nhân. Con số đó thoạt nhìn giống một chỗ vỡ kiến trúc, nhưng **không phải** — ERP đã dựng sẵn chỗ chứa từ trước, và mục 5 của chính tệp này lẫn mục 15 của [mo-ta-ky-thuat.md](mo-ta-ky-thuat.md) đã ghi cách xử. Chép lại đây kèm số đo để khỏi ai phải dò:

**Phiếu dấu — 121/123 ca, không mất gì.** ERP có bảng nối `tab_seal_request_company` (nhiều-nhiều), `company_id` chỉ giữ vai **công ty chính**. Quan trọng hơn: `core/scoping.py` nhánh `scope == "company"` cho entity `seal_request` **lọc theo BẢNG NỐI chứ không theo cột** — Văn thư của bất kỳ công ty nào trong danh sách đều thấy phiếu. Tức lo ngại *"tám pháp nhân còn lại không thấy phiếu"* **không xảy ra với phiếu dấu**. Mảng `brandId` đổ thẳng thành nhiều dòng bảng nối.

**Phiếu đặt xe — 0/321 ca.** Không phiếu đặt xe nào có quá một thương hiệu. Vấn đề không tồn tại.

**Phiếu giao hàng — 2/46 ca.** Đây là chỗ duy nhất còn hụt: `tab_delivery_request` chỉ có một cột `company_id`, không có bảng nối. Cách đã chốt từ trước (mục 5 và mục 15.x): **lấy phần tử đầu làm `company_id`, ghi cờ `multi_brand` kèm danh sách đầy đủ vào sổ đồng bộ**, không im lặng bỏ bớt.

**Số đo làm cách đó tốt hơn chứ không xấu đi: đúng HAI phiếu dính cờ.** Hai tờ thì rà tay được — không cần dựng bảng nối thứ hai, không cần đụng `SCOPE_FIELDS`, không cần tách phiếu.

⚠️ **Bài học ghi lại vì suýt đi sai:** đọc số 123/1 313 xong em kết luận ngay là "chặn P0" và dựng ba phương án Đ-1/Đ-2/Đ-3 để hỏi đại ca — trong khi lời giải nằm sẵn ở mục 5 của chính tệp đang viết, và ERP đã có đủ bảng lẫn đủ nhánh phạm vi từ lâu. **Số đo mới phải đối chiếu với thiết kế cũ trước khi kết luận là nó phá thiết kế.** Việc thật sự còn lại nhỏ hơn nhiều: xác nhận 2 phiếu giao hàng kia lúc nạp.

## 11. Tổng hợp các chỗ mất dữ liệu

Danh sách rút gọn để đại ca duyệt — chỗ nào không chấp nhận được thì phải sửa thiết kế trước khi làm.

| # | Mất gì | Ở đâu | Đề nghị |
|---|---|---|---|
| 1 | Ghi chú của điểm dừng (`Stop.notes`) | Cả hai loại phiếu xe | Thêm trường vào `StopItem` của ERP |
| 2 | Cân nặng hàng (`itemWeight`) | Phiếu giao hàng | Nối vào `goods_size` |
| 3 | ~~`sealed` và `delivered_to_staff` dồn làm một~~ | Phiếu đóng dấu | **Đã gỡ** — QĐ-H thêm `SEAL_DELIVERED = 8`. Còn dồn `fully_approved` + `pending_sealing`, chấp nhận được |
| 4 | Cờ bỏ qua duyệt (`isSkipApproval`, `skipApprovalToLevel`) | Phiếu đóng dấu | Ghi vào `note`, chấp nhận mất |
| 5 | Thương hiệu (`brandId`) | Cả ba loại phiếu | **Có thể không mất gì** — nếu thương hiệu = công ty thì đổ thẳng vào `tab_seal_request_company`. Chờ dữ liệu thật, mục 10 |
| 6 | Lịch sử duyệt chi tiết | Cả ba loại phiếu | Đổ thành chữ, không dựng lại phiên duyệt |
| 7 | Lịch sử hành động tài xế | Phiếu xe | Chấp nhận mất, chỉ giữ trạng thái cuối |
| 8 | Tiêu đề phiếu, số bản | Phiếu đóng dấu — ERP phải **bịa** | 120 ký tự đầu của mục đích; số bản mặc định 1 |
| 9 | Pháp nhân | Cả ba loại phiếu — ERP phải **bịa** | QĐ-G: ba nấc hồ sơ nhân sự → phòng ban → Dego Holding. **Cấm để `0`.** Nấc 3 ghi cờ `company_default` để lọc lại |
| 10 | Mã phiếu | Cả ba loại phiếu — ERP phải **sinh mới** | Dùng bộ sinh mã sẵn có |

Bốn dòng cuối là chỗ ERP **bịa ra giá trị** chứ không phải mất — nguy hiểm hơn, vì dữ liệu bịa trông giống dữ liệu thật. Mọi giá trị bịa đều phải ghi lại trong sổ đồng bộ để sau này lọc ra được.
