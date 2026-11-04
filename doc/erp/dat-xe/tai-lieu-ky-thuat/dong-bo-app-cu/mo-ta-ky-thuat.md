# MÔ TẢ KỸ THUẬT — Đồng bộ app đặt xe cũ ↔ ERP

> Đi kèm [README.md](README.md). Đối chiếu từng trường ở [doi-chieu-truong.md](doi-chieu-truong.md).
> Bản 1.0 — 15/09/2026.

---

## 1. Hình dạng tổng thể

```
        APP CŨ (Cloudflare Worker + Firebase RTDB)              ERP (FastAPI + MySQL)
        ┌──────────────────────────────────────┐               ┌────────────────────────────────┐
        │  người dùng tạo/sửa phiếu            │               │  điều phối viên duyệt, gán xe  │
        │            │                          │               │            │                   │
        │            ▼                          │   (1) chuông  │            ▼                   │
        │  service ghi RTDB  ──►  ghi SỔ  ──────┼──────────────►│  nhận ──► ghi SỔ ──► ghi phiếu │
        │                                       │               │                                │
        │  nhận ◄── ghi SỔ ◄────────────────────┼───────────────┤  ghi SỔ ──► gửi (2) chuông     │
        │            │                          │               │                                │
        │            ▼                          │               │                                │
        │  cập nhật phiếu (không báo ngược)     │               │                                │
        └──────────────────────────────────────┘               └────────────────────────────────┘
                     ▲                                                        │
                     └──────────── (3) đối soát ban đêm ──────────────────────┘
                              ERP quét lại theo `updatedAt`, so và vá chỗ lệch
```

Ba đường, không phải một:

1. **Chuông xuôi** — app cũ có thay đổi thì gọi sang ERP.
2. **Chuông ngược** — ERP có thay đổi thì gọi sang app cũ.
3. **Lưới an toàn** — mỗi đêm ERP tự quét lại, vá những gì chuông làm rơi.

Đường 3 không phải phần thừa. Webhook chắc chắn rơi sự kiện (bên kia bảo trì, mạng đứt, deploy giữa chừng), và nếu không có đường 3 thì chỗ rơi đó **không ai biết** cho tới khi có người đi tìm một phiếu cụ thể.

---

## 2. Khóa đối chiếu — làm sao biết phiếu này bên kia là cái nào

### 2.1. Phía ERP — thêm cột `legacy_id`

Thêm vào bốn bảng: `tab_vehicle_booking`, `tab_seal_request`, `tab_vehicle`, `tab_driver`.

```
legacy_id : String(64), mặc định "", có index UNIQUE (cho phép nhiều dòng rỗng)
```

Phiếu do ERP tự tạo thì cột này rỗng. Phiếu nhận từ app cũ thì mang mã `nanoid` của bên kia.

Lưu ý khi viết migration: MySQL cho phép **nhiều dòng NULL** trong khóa unique nhưng **không cho nhiều dòng chuỗi rỗng**. Vậy hai cách, chọn một và ghi rõ trong migration:
- để `nullable=True`, phiếu ERP tự tạo thì để `NULL` — hợp với unique nhưng lệch nếp "không dùng NULL" của repo;
- hoặc bỏ unique ở tầng DB, chặn trùng ở tầng mã nguồn (tra trước khi ghi) và đặt index thường.

Đề nghị chọn **cách một** (`nullable=True` + unique), vì chống trùng ở tầng DB là chốt cuối, tầng mã nguồn có thể bị vòng lặp gọi song song lách qua.

### 2.2. Phía app cũ — thêm ba trường

Thêm vào mỗi bản ghi `requests`, `vehicles`, `drivers`:

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `updatedAt` | number (mili giây) | Ghi lại **mỗi lần sửa bất cứ thứ gì**. Hiện app cũ hoàn toàn không có trường này — grep cả `src/` không ra dòng nào |
| `erpId` | number | Phiếu này bên ERP là số mấy. Để trống nếu chưa sang được |
| `syncStatus` | string | Trạng thái đồng bộ gần nhất, để hiện ngay trên màn hình quản trị của app cũ |

Kèm theo phải khai `.indexOn: ["updatedAt"]` trong **Rules của Realtime Database** cho nhánh `requests`. Không khai thì truy vấn `orderBy="updatedAt"` vẫn chạy nhưng Firebase **kéo toàn bộ nhánh về rồi lọc ở máy khách** — với vài nghìn phiếu là mỗi lần quét tải về vài chục MB.

---

## 3. Sổ đồng bộ phía ERP — bảng `tab_sync_log`

Đây là trái tim của cả thiết kế. Module mới: `backend/app/modules/sync_log/`.

### 3.1. Các cột

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id`, `created_at`, `created_by`, `updated_at`, `updated_by` | — | Cột chuẩn, kế thừa `AuditMixin` |
| `source` | String(20) | Hệ nguồn. Lần này luôn là `"datxe"`. Để sẵn cho sau này có hệ khác |
| `direction` | SmallInteger | 1 = nhận về · 2 = gửi đi |
| `entity` | String(50) | `vehicle_booking` · `seal_request` · `vehicle` · `driver` · `file` |
| `action` | SmallInteger | 1 = tạo · 2 = cập nhật · 3 = đổi trạng thái · 4 = xóa |
| `legacy_id` | String(64), index | Mã bên app cũ, ví dụ `abcf` |
| `local_id` | BigInteger, index, mặc định 0 | Mã bên ERP. Bằng 0 khi chưa tạo được |
| `status` | SmallInteger, index | 1 chờ · 2 đang chạy · 3 thành công · 4 lỗi · 5 bỏ qua (không có gì đổi) |
| `message` | Text | **Nguyên văn** câu trả lời hoặc câu lỗi của bên kia. Thành công thì ngắn; lỗi thì đây là chỗ đọc để hiểu |
| `payload` | Text (MEDIUMTEXT) | **Nguyên cục JSON bên kia gửi sang**, giữ nguyên không cắt gọt |
| `content_hash` | String(64) | Mã băm của phần dữ liệu nghiệp vụ, để biết "có thật sự đổi gì không" |
| `event_id` | String(64), UNIQUE | Mã sự kiện do bên gửi sinh ra. Nhận lại lần hai thì nhận ra ngay |
| `attempt_count` | SmallInteger, mặc định 0 | Đã thử mấy lần |
| `last_tried_at` | String(20) | Lần thử gần nhất, chuỗi ISO |
| `warnings` | String(255), mặc định "" | **Danh sách cờ cảnh báo**, ngăn bằng dấu phẩy. Dòng thành công vẫn có thể mang cờ |

Bộ cờ trong `warnings` — khai thành hằng số, đừng gõ chuỗi rải rác:

| Cờ | Nghĩa |
|---|---|
| `no_employee` | Không tra ra người tạo theo email |
| `no_department` | Không tra ra phòng ban |
| `company_by_dept` | Pháp nhân lấy ở nấc 2 (theo phòng ban) |
| `company_default` | Pháp nhân lấy ở nấc 3 (**giá trị bịa**) |
| `truncated` | Có chuỗi bị cắt vì vượt trần độ dài |
| `no_plate` | Xe không có biển số, đã bịa mã tạm |
| `title_generated` | Tiêu đề phiếu dấu bịa từ mục đích |
| `status_lossy` | Trạng thái ánh xạ không kín |

Cờ là thứ cho phép **lọc ra mọi phiếu có dữ liệu bịa** sau này. Thiếu nó thì dữ liệu bịa trộn lẫn với dữ liệu thật và không tách lại được.

Trạng thái và loại đều là **SMALLINT kèm hằng số** theo luật R2/QĐ-11 của repo (xem `CLAUDE.md`), không lưu chữ tiếng Việt. Nhãn tiếng Việt khai trong `constants.py` của module và chỉ dùng ở tầng hiển thị.

### 3.2. Ba luật bắt buộc của quyển sổ

**Ghi trước khi làm, không phải ghi sau.** Nhận được tín hiệu thì việc đầu tiên là chèn một dòng trạng thái *chờ*, rồi mới xử lý. Ghi sau thì lúc tiến trình chết giữa chừng sẽ không còn dấu vết nào.

**Một dòng sổ = một sự kiện, không ghi đè lịch sử.** Phiếu `abcf` đổi trạng thái năm lần thì có năm dòng sổ. Nhìn vào sổ phải dựng lại được câu chuyện.

**Không bao giờ xóa dòng lỗi.** Dọn sổ thì chỉ dọn dòng *thành công* cũ hơn sáu tháng, bằng một việc chạy nền riêng, và phải ghi lại là đã dọn bao nhiêu dòng.

### 3.3. Quyền

Thêm entity `sync_log` vào `ENTITIES` trong `core/permissions.py` — kéo theo **ba việc bắt buộc**, thiếu một là hỏng:

1. Khai trong `SCOPE_FIELDS` của `core/scoping.py`, dùng mốc `PUBLIC` (sổ này không lọc theo phòng ban). **Không khai là chặn sạch và có test bắt đỏ.**
2. Cân nhắc `_SYS_ENTITIES` trong `seed.py`: quyền vận hành hệ thống, **không** nên rơi vào bộ quyền mặc định của Quản lý thu mua.
3. Trên hệ đang chạy, vai trò cũ **không tự có** khóa mới — phải tick tay ở màn Phân quyền, hoặc chạy `SEED_FORCE_SYNC=true` đúng một lần rồi trả về `false`.

Ai được xem sổ: nhóm quản trị hệ thống. Nút "Chạy lại" đòi quyền ghi.

---

## 4. Sổ đồng bộ phía app cũ

Thêm nhánh `sync_logs` trong Realtime Database, mỗi dòng một khóa `nanoid`:

```
sync_logs/<id> = {
  eventId, direction, entity, action,
  legacyId, erpId,
  status,          // pending | running | success | failed | skipped
  message,         // nguyên văn phản hồi của ERP
  payload,         // cục dữ liệu đã gửi đi
  attemptCount,
  createdAt, lastTriedAt
}
```

Vì sao phải có sổ ở **cả hai** đầu: khi hỏng thì thường là một bên không nhìn thấy bên kia. Chỉ nhìn một quyển sổ thì không biết tín hiệu chưa bắn đi, hay bắn rồi mà bên kia không nhận, hay bên kia nhận rồi mà câu trả lời rớt trên đường về.

Kèm một màn hình nhỏ trong phần quản trị của app cũ để lọc theo trạng thái và bấm gửi lại.

---

## 5. Hợp đồng webhook

### 5.1. Chiều app cũ → ERP

```
POST  {ERP_BASE}/api/sync/datxe/events
```

Header:

| Header | Nội dung |
|---|---|
| `X-Sync-Source` | `datxe` |
| `X-Sync-Event` | mã sự kiện, duy nhất, do bên gửi sinh |
| `X-Sync-Timestamp` | thời điểm gửi, giây |
| `X-Sync-Signature` | chữ ký, xem mục 6 |

Thân:

```json
{
  "event_id":   "evt_xxx",
  "occurred_at": 1757900000000,
  "entity":     "vehicle_booking",
  "action":     "create",
  "legacy_id":  "abcf",
  "erp_id":     0,
  "data":       { ...nguyên cục bản ghi bên app cũ... }
}
```

Trả về, theo đúng phong bì chuẩn của ERP (`{success, message, data}`):

```json
{ "success": true, "message": "Đã nhận", "data": { "erp_id": 123, "status": "success", "sync_log_id": 45 } }
```

App cũ nhận `erp_id` thì ghi ngược vào bản ghi của mình và đóng dòng sổ.

⚠️ **`erp_id` luôn là id THẬT, kể cả khi `status` là `skipped`** (vá 17/09, tìm ra bằng
một cú gọi tay). Ba nhánh bỏ qua — trùng `event_id` · nội dung không đổi ô nào của ERP ·
phiếu đã chốt bên ERP — đều nói "không có gì phải làm", **không** nói "chưa có hàng nào
bên ERP". Trả `0` ở đó là bảo app cũ xóa trắng `erpId` của đúng phiếu vừa nhận xong.
Bên app cũ vẫn nên tự thủ thêm một lớp: **chỉ ghi `erpId` khi giá trị nhận về lớn hơn 0.**

### 5.2. Chiều ERP → app cũ

```
POST  {LEGACY_API}/api/v1/sync/erp-events
```

Cùng bộ header và cùng hình dạng thân, chỉ khác `X-Sync-Source: erp`. Trường `data` mang **trạng thái mới và thông tin điều phối đã dịch sẵn thành chữ**:

```json
{
  "status": "dispatched",
  "vehicle": { "license_plate": "51A-12345", "model": "Ford Transit", "type": "xe khách 16 chỗ" },
  "driver":  { "name": "Nguyễn Văn A", "phone": "0901234567" },
  "approved_at": "2026-09-15T10:22:00",
  "note": "..."
}
```

Gửi kèm chữ như vậy thì app cũ **không cần đồng bộ danh mục xe và tài xế** — nó chỉ hiển thị lại. Đây là chỗ cắt được nhiều việc nhất trong cả thiết kế.

### 5.3. ERP không gọi thẳng vào Firebase

Chiều ngược **phải đi qua API của Worker**, không ghi thẳng Realtime Database. Ghi thẳng thì mất hết phần nghiệp vụ của app cũ (thông báo đẩy, kiểm tra hợp lệ, ghi lịch sử), và mai kia app cũ đổi cấu trúc dữ liệu là ERP hỏng theo mà không ai biết.

### 5.4. Trả lời nhanh, xử lý ngay

Khối lượng thực tế nhỏ (vài chục phiếu mỗi ngày), nên **xử lý luôn trong lượt gọi** cho đơn giản, không đẩy sang hàng đợi: ghi sổ *chờ* → xử → cập nhật sổ → trả lời. Nếu xử hỏng thì dòng sổ ở trạng thái *lỗi* và việc chạy nền sẽ gọi lại sau.

Riêng chiều **ERP → app cũ** thì **không gọi HTTP ngay trong lượt xử lý của người dùng**: ghi dòng sổ *chờ* rồi để Celery đẩy đi. Lý do: nếu gọi thẳng, app cũ chết là điều phối viên bấm nút "Duyệt" trên ERP phải ngồi chờ hết thời gian chờ mạng. Celery đã chạy thật ở prod (đang làm sao lưu R2 hai lần mỗi ngày), có sẵn chỗ cắm.

---

## 6. Xác thực — làm sao biết tín hiệu là thật

Hai bên giữ chung một **khóa bí mật** đặt trong biến môi trường (`SYNC_SHARED_SECRET`). Bên gửi ký lên phần thân cộng với thời điểm gửi; bên nhận ký lại và so.

Ba luật:
- Thời điểm gửi lệch quá **5 phút** thì từ chối — chặn trò bắt lại gói cũ gửi lại.
- So chữ ký bằng hàm so sánh **thời gian cố định** (`hmac.compare_digest`), không so bằng `==`.
- Khóa để trong `.env` hai bên, **không commit**, và **khác nhau giữa dev và prod**.

Không dùng token đăng nhập Firebase cho đường này: đây là máy gọi máy, không có người nào đứng sau. App Check cũng không áp — nó là cái gác dành cho trình duyệt.

---

## 7. Chống lặp và chống trùng

### 7.1. Chống lặp vô hạn

Kịch bản hỏng: ERP báo sang app cũ "phiếu đã duyệt" → app cũ ghi xuống → app cũ thấy có thay đổi nên báo ngược sang ERP → ERP ghi xuống → lại báo sang... chạy mãi.

Chặn ở **cả hai đầu**:

- **Phía app cũ:** lượt ghi nào đến từ đường `/sync/erp-events` thì **không bắn chuông**. Trong mã nguồn là một cờ truyền xuống tầng service.
- **Phía ERP:** dùng một biến ngữ cảnh (`contextvar`) kiểu `sync_in_progress`; khi nó đang bật thì tầng phát sự kiện **không ghi dòng sổ gửi đi**. Cùng khuôn với cách `tab_change_log` chặn ghi chồng.

Không dựa vào một cơ chế duy nhất. Một tầng hỏng thì tầng kia còn đỡ, và vòng lặp vô hạn là loại lỗi phá nhanh nhất: mỗi vòng đều ghi sổ nên trong vài phút có thể sinh hàng trăm nghìn dòng.

### 7.2. Chống xử lý trùng một sự kiện

- `event_id` khai **UNIQUE**. Nhận lại lần hai thì tra thấy ngay, trả về kết quả cũ, không làm gì thêm.
- Trước khi tạo phiếu luôn tra `legacy_id`. Có rồi thì cập nhật, không tạo mới.
- So `content_hash`: giống hệt bản đang có thì ghi sổ trạng thái *bỏ qua* và dừng. Vừa tiết kiệm, vừa là chốt chặn thứ ba của mục 7.1.

---

## 8. Khớp người, phòng ban, công ty

### 8.1. Người tạo phiếu

Đường đi: lấy `email` trong phiếu bên app cũ → chuẩn hóa (bỏ khoảng trắng, đổi hết về chữ thường) → tìm trong `tab_user.email` → từ tài khoản lần ra hồ sơ nhân sự.

Tìm không thấy thì **vẫn nhận phiếu**, và:
- `requester_id = 0`;
- `requester`, `requester_email`, `requester_phone` giữ nguyên chữ mà app cũ gửi sang — mấy cột này vốn được thiết kế để **chụp lại** thông tin lúc tạo phiếu, đúng việc;
- ghi dòng sổ ở trạng thái thành công nhưng có ghi chú "chưa gắn được người", để lọc ra mà gắn tay sau.

**Không** được vì không tìm thấy người mà từ chối phiếu. Mất phiếu nặng hơn thiếu một liên kết.

### 8.2. Phòng ban

Khớp theo **tên phòng** (nhánh `departments` bên app cũ có `name`) với `tab_department.name`. Không thấy thì `department_id = 0`.

Có một đường tốt hơn: nếu đã tìm ra hồ sơ nhân sự ở bước 8.1 thì **lấy phòng ban theo hồ sơ nhân sự của ERP**, chính xác hơn hẳn so với khớp chữ. Chỉ khi không tìm ra người mới lùi về khớp tên phòng.

### 8.3. Công ty (pháp nhân) — QĐ-G

App cũ không có khái niệm công ty — nó có `brands` (thương hiệu), là thứ khác. Mà `company_id` bên ERP làm **hai việc nặng**:

- quyết định **ai nhìn thấy phiếu** (phạm vi dữ liệu);
- quyết định **đơn chạy tới giám đốc nào**.

Nên luật là: **phiếu bắt buộc có công ty, cấm `company_id = 0`.** Phiếu để `0` sẽ rơi ra ngoài phạm vi của mọi người, **không ai nhìn thấy**, kể cả người tạo — và cũng không tới được giám đốc nào.

**Tra theo bốn nấc, dừng ở nấc đầu tiên ra kết quả:**

| Nấc | Đường tra | Ghi vào sổ |
|---|---|---|
| **0** | **`details.brandId` → bảng tra thương hiệu → `company_id`** | `company_source = 0` — **chính xác nhất, chính phiếu khai ra** |
| 1 | Hồ sơ nhân sự của người tạo → `company_id`, nếu khác `0` | `company_source = 1` |
| 2 | Phòng ban của phiếu → `tab_department.company_id` | `company_source = 2` |
| 3 | Công ty mặc định `SYNC_DEFAULT_COMPANY_ID` = **`1`** (Dego Holding, mã `DEGO`) | `company_source = 3` — **giá trị bịa**, phải lọc ra được |

**Nấc 0 thêm ngày 15/09/2026** sau khi đối chiếu dữ liệu thật (xem [doi-chieu-truong.md](doi-chieu-truong.md) mục 10.5 và 10.6). Hai điều làm nó thành nấc chính chứ không phải nấc phụ:

- **Thương hiệu bên app cũ chính là pháp nhân** — màn quản trị của app cũ gọi thẳng là "Quản lý Công ty", tên có kèm mã số thuế, và **11/11 thương hiệu khớp `tab_company`** của ERP (9 khớp bằng mã số thuế, 2 dòng Dr.Xanh khớp bằng tên).
- **Cả ba loại phiếu đều mang `brandId`**, không riêng phiếu dấu (`db.types.ts` dòng 240 · 264 · 277).

Nghĩa là phiếu **tự khai pháp nhân của nó**, không phải suy ra từ hồ sơ người tạo. Ba nấc còn lại vẫn giữ làm đường lùi, vì `brandId` là trường tùy chọn — chưa đếm được thực tế bao nhiêu phần trăm phiếu có điền.

`brandId` là **mảng**: phiếu dấu đổ thành nhiều dòng `tab_seal_request_company`; phiếu xe / giao hàng chỉ có một cột `company_id` nên lấy phần tử đầu và **ghi cờ `multi_brand`** kèm danh sách đầy đủ vào sổ.

Bảng tra thương hiệu là **dữ liệu, không phải mã cứng** — một bảng `legacy_brand_id` → (`company_id`, `department_id`), nạp một lần rồi sửa được trên màn hình. Nạp tự động bằng **mã số thuế**, hai dòng Dr.Xanh gắn tay (hai bên đang ghi hai mã thuế khác nhau, cần đại ca xác nhận mã nào đúng).

Nấc nào dùng cũng phải ghi lại trong sổ đồng bộ. Phiếu ở nấc 3 gom thành một bộ lọc riêng trên màn hình sổ, để người vận hành gắn tay lại cho đúng.

**Vì sao phải có nấc 2 — hai chỗ hỏng đã tìm thấy trong dữ liệu thật:**

*Một.* `tab_company` có **hai dòng cùng tên "CÔNG TY TNHH DEGO HOLDING"**: `id 1` mã `DEGO` và `id 16` mã `DEGO HOLDING`. Ghi rõ ở `backend/app/modules/work/membership_service.py:80`. Hai người cùng một công ty thật vẫn đang mang hai số khác nhau.

**Đã chốt 15/09/2026: công ty mặc định là `id 1`.** Dòng `id 16` **chưa dọn** và vẫn đang có dữ liệu gắn vào — gộp nó là một đợt dọn riêng, ngoài phạm vi việc này (câu hỏi H-08). Trong lúc chờ, mã đồng bộ phải coi `1` và `16` là **cùng một công ty thật**: chỗ nào so sánh pháp nhân hoặc đếm đối chiếu thì gom hai số này lại, đừng coi là hai công ty khác nhau. Khai thành một hằng số `COMPANY_ALIASES` một chỗ, để ngày dọn xong thì xóa đúng một dòng.

*Hai.* **237/262 nhân sự đang để `company_id = 0`.** Nghĩa là nấc 1 gần như luôn trượt.

### 8.3.1. ĐO THẬT trên dev ngày 15/09/2026 — nấc 2 cũng đang chết

Bản đầu của mục này viết "nấc 2 đỡ được vì `tab_department.company_id` điền tốt hơn". **Đo thật thì sai.** Số lấy từ `deverp.degoholding.vn` (dữ liệu chép từ prod):

| Đo | Kết quả |
|---|---|
| Nhân sự | **262** người (255 chính thức, 6 nghỉ việc, 1 thai sản) |
| Nhân sự có `company_id` khác 0 | **25/262** — 90% trống |
| Nhân sự có `department_id` khác 0 | **241/262** — **92% ĐÃ ĐIỀN** |
| Phòng ban | 18 phòng |
| Phòng ban có `company_id` khác 0 | **0/18** — trống sạch |
| Dòng trong `tab_department_company` | **0** — bảng rỗng hoàn toàn |
| Công ty | 14 pháp nhân (`id` 1,2,3,5..14,16 — **không có `id 4` và `id 15`**) |

Ba điều rút ra:

**(a) Hôm nay cả nấc 1 lẫn nấc 2 đều trượt, 100% phiếu rơi xuống nấc 3.** Tức là mọi đơn chạy tới giám đốc Dego Holding — đúng thứ QĐ-G muốn tránh. Không phải lỗi mã, là dữ liệu chưa ai điền.

**(b) Chỗ cần điền là 18 DÒNG PHÒNG BAN, không phải 237 hồ sơ nhân sự** — nếu vẫn phải đi đường suy luận. Điền `company_id` cho 18 phòng ban thì nấc 2 hứng được **241/262 người (92%)**; điền 237 hồ sơ nhân sự ra kết quả tương tự nhưng tốn gấp 13 lần công, và mỗi lần có người mới vào lại phải nhớ điền.

> **ĐÃ HẾT HIỆU LỰC từ chiều 15/09/2026 — H-07 ĐÓNG.** Có **nấc 0** rồi thì không cần suy luận nữa: phiếu tự mang `brandId`, và thương hiệu khớp 11/11 với pháp nhân ERP. Đại ca chốt: *"nhân viên có công ty hay không thì có vấn đề gì đâu, nhân viên có thuộc phòng ban hoặc thương hiệu nào thì có"* — đúng, và dữ liệu ủng hộ. **Không cần đợt điền pháp nhân nào trước khi nạp lịch sử.** Nấc 1 và nấc 2 tụt xuống thành đường lùi cho những phiếu cũ không có `brandId`; nếu đếm ra số phiếu thiếu `brandId` là nhỏ thì bỏ luôn cũng được, đi thẳng xuống nấc 3.

**(c) Có một tham chiếu chết:** 1 nhân sự đang mang `company_id = 15`, mà `tab_company` không có `id 15` (gọi API trả 404). Không sập gì cả — nó im lặng thành "không thuộc công ty nào". Lúc nạp lịch sử phải kiểm tra công ty tra ra **có thật sự tồn tại không**, chứ không chỉ kiểm khác `0`; không thì phiếu mang một pháp nhân ma và lại rơi ra ngoài tầm nhìn của mọi người.

**Sửa lại luật tra cho khớp thực tế:** mỗi nấc trả ra một số thì phải **kiểm số đó có dòng trong `tab_company` và đang `is_active`**; không đạt thì coi như nấc đó trượt, đi tiếp nấc sau.

### 8.4. Phòng ban của phiếu đi kèm công ty

Vì nấc 2 ở trên dựa vào phòng ban, nên **phòng ban phải tra trước công ty**, không phải ngược lại. Thứ tự trong mã: tra người → tra phòng ban → tra công ty.

Phiếu đóng dấu bên app cũ có sẵn `details.departmentId` (phòng ban của phiếu, có thể khác phòng của người tạo). Ưu tiên dùng trường đó. Phiếu xe không có, lấy theo phòng của người tạo.

---

## 9. Quy tắc nhận phiếu

Khi ERP nhận một phiếu từ app cũ:

1. Tra `legacy_id`. Chưa có → tạo mới. Có rồi → sang bước 4.
2. Tạo mới: sinh mã phiếu theo đúng bộ sinh mã sẵn có (`DX001`, `DX002`... cho đặt xe). **Không tự đặt định dạng mã khác** — bộ sinh mã hiện tại quét các mã dạng `DX<số>` để lấy số lớn nhất, chen mã lạ vào là nó tính sai.
3. Ghi `legacy_id`, ghi các trường nội dung, tính `content_hash`, lưu.
4. Cập nhật: **ghi đè hết, trừ ghi rỗng đè lên đang có** (đại ca chốt 17/09/2026, xem khung dưới).
5. Phiếu ở trạng thái đã chốt (Hoàn thành, Từ chối, Đã hủy) thì **không nhận cập nhật nội dung nữa**, ghi sổ trạng thái *bỏ qua* kèm lý do.

Điểm 4 và 5 là chỗ dễ sai nhất trong toàn bộ thiết kế. Nên viết thành một danh sách trường tường minh trong mã nguồn, một chỗ duy nhất, chứ đừng để mỗi hàm tự nhớ.

### 9.4 bis — vì sao đổi từ "cấm sáu ô" sang "ghi đè hết"

Bản đầu mục 4 viết: *tuyệt đối không đụng `status`, `assigned_vehicle_id`, `assigned_driver_id`, `driver_status`, `distance_km`, `cost`*. Câu đó **giả định điều phối viên bấm gán xe bên ERP**. Giai đoạn này chưa đúng: chiều ERP → app cũ chưa làm, người ta vẫn gán xe bên app cũ, ERP mới chỉ là cái gương. Cấm ghi đè lúc này thì gương đứng hình ngay lần đầu, phiếu mãi mãi không có xe.

Luật thay thế, một câu: **ghi đè hết, trừ ghi rỗng đè lên đang có.** Ô nào bộ dựng trả ra `""` / `0` / `None` mà dưới ERP đang có dữ liệu thì giữ nguyên và đếm vào sổ đồng bộ.

Vế "trừ" không phải phòng xa. `assigned_vehicle_id` không chép thẳng — nó là `vehicle_index.get(khóa, 0)`. Hôm nào đội xe mua xe mới, app cũ gán liền, ERP chưa kịp đóng dấu `legacy_id` cho xe đó thì bộ dựng trả 0, ghi đè thẳng là **xóa xe khỏi một chuyến đã chạy xong** — mất dữ liệu vì tra không ra, không phải vì ai bỏ, và không một dòng lỗi nào. Đo trên kho Firebase dev ngày 17/09 thì 0/9 thương hiệu, 0/3 tài xế, 3/37 người khớp dấu `legacy_id`, nên bật đồng bộ dev mà thiếu luật này là mất sạch xe với tài xế ngay nhịp đầu.

Riêng `False` **không** tính là rỗng: bỏ tick "khứ hồi" là một ý định thật, khác hẳn "không biết".

Bảy ô không bao giờ mở, gom ở hằng số `LEGACY_READONLY_FIELDS` trong `app/modules/legacy_datxe/builder.py`: `id`, `code`, `legacy_id`, `created_at`, `created_by` (đổi `code` là mọi bản in và email đã gửi trỏ sai; `created_at` là mốc đối soát; hai dấu kia là dây nối giữa hai hệ) cộng `updated_at`, `updated_by` — hai ô này không phải cấm, mà do người gọi tự đóng dấu.

**Ngày nào điều phối chuyển hẳn sang ERP thì thêm sáu tên ở đoạn đầu mục này vào đúng hằng số đó.** Một chỗ duy nhất, không phải đi lục lại mã. Bài kiểm canh luật nằm ở `test/backend/test_dong_bo_datxe_ghi_de.py`.

### 9.6 — tra danh mục ba nấc, và cái gì được phép tự tạo

Hệ quả của 9.4 bis: ô trống thì giữ được dữ liệu cũ, nhưng **phiếu mới** vẫn thiếu. Nên bộ tra danh mục (xe, tài xế, phòng ban, con người) đi ba nấc, gom trong một hàm, không rải mỗi chỗ một kiểu:

1. Tra dấu `legacy_id`. Ra thì trả về. Nấc này ăn 100% ca hiện có — 1313 phiếu đã nạp không trượt ca nào.
2. Không ra thì tra theo **đặc điểm tự nhiên**: xe theo biển số, tài xế theo số điện thoại rồi tới tên, phòng ban theo tên đã chuẩn hóa, con người theo **email** (đúng QĐ-D: hai bên nối nhau bằng email). Khớp thì **đóng dấu `legacy_id` vào hàng có sẵn** rồi trả về, lần sau nấc 1 ăn luôn.
3. Vẫn không ra mới tính tạo — và **không tạo đồng đều mọi loại**:

| Loại | Tự tạo? | Vì sao |
|---|---|---|
| Xe, tài xế | **Có** nhưng mặc định TẮT (`SYNC_DATXE_AUTO_CREATE`), và mỗi hàng đẻ ra đóng cờ `auto_created` lên dòng sổ đồng bộ | Danh mục vận hành, trùng thì gộp lại được, không dính tiền hay quyền |
| Phòng ban | **Không** | Dính phân quyền theo phạm vi — đẻ phòng mới là đẻ một vùng dữ liệu không ai được gán vào |
| Công ty | **Không** | Pháp nhân có mã số thuế, dính hợp đồng, công nợ, báo cáo. Một công ty rác là báo cáo lệch |
| Nhân sự, tài khoản, phân quyền | **Tuyệt đối không** | Đây là cửa máy-gọi-máy từ ngoài vào. Cho app cũ tự đẻ tài khoản ERP là mở đường leo thang quyền. Không khớp email thì phiếu vẫn nhận, `requester_id = 0`, tên và email người tạo vẫn chụp vào phiếu nên bản in không mất chữ nào — ba phiếu đang ở tình trạng đó, chạy bình thường |

**Hàng đợi soát nằm ở đâu (đính chính 17/09/2026).** Bản đầu của mục này viết là hàng tự tạo sẽ mang `is_active = False`; **`tab_vehicle` và `tab_driver` không có cột đó**, mà mượn `Vehicle.status` thì hỏng nghĩa — cột ấy nói tình trạng vận hành của xe, không nói "ERP chưa soát dòng này". Chốt lại: dấu hiệu duy nhất là **cờ `auto_created` trên dòng sổ đồng bộ**, và bộ lọc *chỉ dòng có cảnh báo* của màn Nhật ký đồng bộ **chính là** hàng đợi soát. Hai cờ anh em đi cùng nó: `stamped_by_name` (ghép theo đặc điểm tự nhiên, nấc 2) và `unresolved_catalog` (tra không ra, ô để trống).

Vì sao không cho tự tạo tất: bảng khai tay tồn tại chính vì mấy cặp ghép cần **người** quyết. `"Tự lái"` bên app cũ là một hồ sơ tài xế còn bên ERP là cờ `is_self_drive`; bốn phòng ban được gộp tay; ba UID Firebase cùng một con người. Bộ tự tạo không sai về kỹ thuật — nó chỉ không biết **cái gì đã tồn tại dưới một cái tên khác**.

---

## 10. Tệp đính kèm

ERP **không chép nội dung tệp**. Với mỗi tệp bên app cũ, tạo:

- một dòng `tab_file`: `filename` lấy tên gốc, `content_type`, `size` chép nguyên; `file_key` ghi khóa R2 bên app cũ; `url` để **rỗng**;
- một dòng `tab_file_link`: `entity` là `seal_request` hoặc `vehicle_booking`, `entity_id` là mã phiếu bên ERP.

Thêm hai cột nhẹ vào `tab_file` để phân biệt tệp ở xa:

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `source` | String(20), mặc định "" | Rỗng = tệp của ERP. `"datxe"` = tệp nằm bên app cũ |
| `external_id` | String(64), mặc định "" | Mã tệp bên app cũ |

### 10.1. Xem tệp thế nào

**Không** lưu đường dẫn ký sẵn (presigned URL) vào cột `url`: app cũ ký URL chỉ sống **một giờ**, lưu xuống thì hôm sau bấm vào là hỏng.

Đường đúng: người dùng bấm xem → ERP thấy `source = "datxe"` → ERP gọi sang app cũ bằng khóa dịch vụ để **xin một đường dẫn mới**, hoặc kéo nội dung về rồi trả thẳng cho trình duyệt. Người dùng không thấy khác gì tệp thường.

Kéo theo: cần một đường ở app cũ cho ERP gọi vào, dạng `GET /api/v1/sync/files/{id}/url`, có xác thực như mục 6.

### 10.2. Điều phải nhớ

Ngày tắt app cũ là ngày mọi tệp này chết. Trước lúc đó phải có một đợt chép tệp thật sang kho ERP — lúc đó chỉ cần đọc `tab_file` lọc theo `source = "datxe"`, tải về, đẩy lên R2 của ERP, ghi lại `file_key` và xóa cờ `source`. Thiết kế này để dành sẵn đường cho đợt đó.

---

## 11. Đối soát ban đêm

Một việc chạy nền lúc 01:00 (Celery beat), làm ba việc:

**Một — quét theo thời gian cập nhật.** Hỏi app cũ những phiếu có `updatedAt` mới hơn mốc đồng bộ gần nhất, so `content_hash` với bên ERP, lệch thì nạp lại. Đây chính là chỗ cần trường `updatedAt` ở mục 2.2.

**Hai — đếm đối chiếu.** Đếm số phiếu theo tháng và theo trạng thái ở hai bên. Lệch thì ghi một dòng cảnh báo, kèm danh sách mã phiếu chênh nhau.

**Ba — gọi lại việc hỏng.** Lấy các dòng sổ đang *lỗi*, thử lại, giãn dần khoảng cách giữa các lần thử (1 phút, 5 phút, 30 phút, 2 giờ, 12 giờ). Quá **10 lần** vẫn hỏng thì dừng tự động, để nguyên trong sổ chờ người xem — đừng thử mãi, vì lỗi dữ liệu thì thử nghìn lần vẫn hỏng, chỉ tổ làm đầy sổ.

Kết quả mỗi đêm ghi thành một dòng tổng kết: quét bao nhiêu, vá bao nhiêu, còn lệch bao nhiêu.

### 11.1 — bản đã dựng (17/09/2026)

Hai việc chạy nền ở `backend/app/modules/legacy_datxe/tasks.py`, lịch khai trong `core/celery_app.py`. Việc **hai** (đếm đối chiếu) **chưa làm** — để lại cho đợt sau, vì nó cần đếm được bên app cũ chứ không chỉ đọc từng nhánh.

| Task | Lịch | Làm gì |
|---|---|---|
| `datxe.pull_updated` | mỗi `SYNC_DATXE_PULL_MINUTES` phút | Hỏi Firebase phiếu có `updatedAt` từ con trỏ trở đi, đẩy qua đúng `apply_legacy_record` mà cái móc đang dùng |
| `datxe.retry_pending` | phút 3, 13, 23… mỗi giờ | Chạy lại dòng sổ đang *chờ* hoặc *lỗi*, tối đa **3 lần thử** một dòng |

Bốn điều chốt khác bản vẽ ban đầu, đều có lý do:

- **Con trỏ là mốc BAO GỒM**, lưu ở `cursor_to` của dòng lượt chạy thành công gần nhất. Cộng thêm một mili-giây thì hai phiếu sửa trong cùng một mili-giây sẽ mất một; nhìn lại phiếu ở ranh giới thì `is_unchanged` chặn ngay, không tốn dòng sổ nào.
- **Lượt đầu tiên chỉ nhìn lại 24 giờ.** Sổ chưa có con trỏ mà quét cả nhánh thì 1313 phiếu cũ — vốn đã nạp một lần hồi P1 — đổ vào sổ ngay lần chạy đầu.
- **Con trỏ vẫn tiến kể cả khi vài phiếu hỏng.** Mỗi phiếu hỏng đã có dòng sổ *lỗi* của riêng nó và `datxe.retry_pending` nhặt lại; neo con trỏ vì một phiếu hỏng vĩnh viễn thì cứ năm phút lại kéo nguyên đám đó về, mãi mãi.
- **Chạy lại tự động là chạy TẠI CHỖ** (tăng `attempt_count`), không đẻ dòng mới — cùng `event_id`, cùng `payload`, vẫn là một sự kiện. Nút **Chạy lại** của người dùng thì khác: đó là một quyết định mới nên `clone_for_retry` sinh hẳn dòng riêng, và dòng đó rơi vào vòng này ở lần thử đầu. Trần **3 lần** thay cho thang giãn 1 phút → 12 giờ của bản vẽ: lỗi dữ liệu thì thử mấy cũng hỏng, và mỗi lần thử đều thấy được trong sổ.

⚠️ **Firebase Rules phải khai chỉ mục** cho nhánh `requests` ở **cả hai dự án** (dev và prod):

```json
"requests": { ".indexOn": ["updatedAt"] }
```

Thiếu chỉ mục thì Firebase trả 400, `read_node` nuốt lỗi thành `None`, và triệu chứng là "vòng quét chẳng kéo được phiếu nào" chứ không có gì đỏ lên.

---

## 12. Màn hình sổ đồng bộ

Trong ERP, nằm ở nhóm Quản trị: `/system/sync-log`.

- Bảng danh sách, lọc theo **trạng thái**, **loại**, **chiều**, khoảng ngày, và ô tìm theo mã bên cũ.
- Bấm vào một dòng thì xem được **nguyên cục JSON** bên kia gửi sang và **nguyên văn** câu lỗi.
- Nút **Chạy lại** cho dòng lỗi (đòi quyền ghi). Chạy lại an toàn nhờ mục 7.2.
- Thẻ đếm ở đầu trang: hôm nay nhận bao nhiêu, gửi bao nhiêu, đang lỗi bao nhiêu.
- Bộ lọc riêng "**chưa gắn được người**" cho trường hợp ở mục 8.1.

Dựng bằng khung CRUD khai báo sẵn có của `frontend-v2` (`shared/crud`), không tự ghép bảng.

---

## 13. Cấu hình

**Phía ERP** (`.env`):

| Biến | Ý nghĩa |
|---|---|
| `SYNC_DATXE_ENABLED` | Bật/tắt toàn bộ việc đồng bộ. Mặc định **tắt** |
| `SYNC_SHARED_SECRET` | Khóa ký chung, khác nhau giữa dev và prod |
| `SYNC_LEGACY_API_BASE` | `https://api.degoholding.vn` hoặc bản dev |
| `SYNC_DEFAULT_COMPANY_ID` | Công ty mặc định khi không tra ra (mục 8.3). **Chốt `1`** — Dego Holding, mã `DEGO` |
| `SYNC_NOTIFY_ON_IMPORT` | Có bắn thông báo khi nhận phiếu không. Lúc nạp lịch sử phải để **tắt** |
| `LEGACY_FIREBASE_DB_URL` | Kho Firebase app cũ, chỉ vòng quét lưới an toàn dùng (mục 6) |
| `LEGACY_FIREBASE_SECRET` | Khóa đọc kho trên. **Theo từng dự án**, đổi URL là phải đổi luôn |
| `SYNC_DATXE_PULL_MINUTES` | Nhịp quét, phút |

**HAI DỰ ÁN FIREBASE RIÊNG, ĐỪNG LẪN** (đại ca xác nhận 17/09/2026):

| | Tên kho | Dùng cho |
|---|---|---|
| Dev | `api-degoholding-default-rtdb` | worker `my-firebase-api-dev`, tên miền `dev-api.degoholding.vn` |
| Prod | `api-degoholding-com-default-rtdb` | worker `my-firebase-api`, tên miền `api.degoholding.vn` — đây là kho đã sinh ra 1313 phiếu nạp ở P1 |

Dữ liệu hai kho **không trùng nhau**: đối chiếu 17/09 thấy 0/9 thương hiệu, 0/3 tài xế, 3/37 người và 0/480 phiếu bên dev có mặt trong dấu `legacy_id` dưới ERP. Hệ quả cần nhớ khi test: phiếu đẩy từ bản dev sẽ **thiếu công ty, thiếu người tạo, thiếu xe** — đó là do hai kho khác dữ liệu, KHÔNG phải lỗi bảng tra. Test trên dev chỉ chứng minh được đường ống (chữ ký, cửa nhận, sổ đồng bộ, luật ô được phép ghi đè); phép tra danh mục đã được 1313 phiếu prod chứng minh rồi.

Cũng vì thế **không nên** chạy `sync_master_data` / `sync_users` / `sync_fleet` trên bản kết xuất dev để "cho khớp": cột `legacy_id` chỉ đeo được MỘT khóa, nên làm vậy sẽ đẻ ra bản sao thứ hai của từng công ty, phòng ban, xe, người.

**Phía app cũ** (`wrangler secret`):

| Biến | Ý nghĩa |
|---|---|
| `SYNC_ENABLED` | Bật/tắt bắn chuông |
| `SYNC_SHARED_SECRET` | Giống khóa bên ERP |
| `SYNC_ERP_BASE` | Đường tới ERP |

Cả hai đầu đều có công tắc tắt. Khi có sự cố thì tắt một cái là dừng hẳn, không phải đi gỡ mã.

---

## 14. Những chỗ sẽ đau, ghi trước cho đỡ mất thời gian

**Thời gian.** App cũ lưu **số mili giây**; ERP lưu **chuỗi ISO dài đúng 20 ký tự** (`2026-09-15T10:22:00`). Đổi qua lại phải cố định múi giờ `Asia/Ho_Chi_Minh`, và phải cắt đúng 20 ký tự, dài hơn là MySQL cắt cụt âm thầm.

**Cột chuỗi không khai độ dài tối đa ở tầng kiểm tra thì thành lỗi 500, không phải lỗi 422.** Luật này repo đã trả giá rồi (rà hồ sơ nhân sự ra 12 ca). Dữ liệu từ app cũ là dữ liệu **bên ngoài**, không có gì bảo đảm nó ngắn — mọi trường nhận về đều phải khai trần độ dài, và kiểm ở tầng schema chứ không phải trông chờ DB.

**Bài kiểm chạy trên SQLite mà SQLite không ép độ dài chuỗi.** Nên bài kiểm nào ghi xuống DB rồi khẳng định là **xanh giả**. Kiểm trần độ dài phải kiểm ở tầng schema.

**Điểm dừng trung gian lệch tên trường.** App cũ có `address`, `notes`, `contactName`, `contactPhone`; ERP có `location`, `contact_name`, `contact_phone` — **không có** chỗ chứa `notes`. Xem [doi-chieu-truong.md](doi-chieu-truong.md) mục 5.

**Vòng lặp sinh sổ.** Nếu mục 7.1 hỏng, trong vài phút sổ có thể phình lên hàng trăm nghìn dòng. Nên đặt một cái van: một phiếu sinh quá **20 dòng sổ trong một giờ** thì tự dừng đồng bộ phiếu đó và cảnh báo.

**Nạp lịch sử đừng bắn thông báo.** Nạp 2000 phiếu mà quên tắt là 2000 cái chuông cộng 2000 lá thư. Đây là câu hỏi H-02 trong README.

**Alembic.** Model mới phải được thêm vào `backend/app/core/all_models.py`, nếu không lệnh sinh migration tự động sẽ **không thấy bảng mới**.

---

## 15. Đồng bộ trạng thái duyệt khi HAI bộ máy cùng chạy (QĐ-I)

Đại ca chốt 15/09: *"2 app vẫn hoạt động, nhưng có đường đồng bộ qua lại thôi, không
thay đổi gì ở luồng được — cứ cái đang hoạt động bình thường, kiểu đổi thì ai đâu mà
đổi liền được."* Mục này là cách làm cho đúng trong ràng buộc đó.

### 15.1. Nguyên tắc gốc — đồng bộ KẾT CỤC, không đồng bộ TIẾN TRÌNH

Hai bên có cấu trúc luồng duyệt giống nhau đến bất ngờ:

| App cũ (`ApprovalState`, nhúng trong phiếu) | ERP (`tab_approval_instance`) |
|---|---|
| `workflowSnapshot` | `flow_snapshot` |
| `currentLevel` | `current_seq` |
| `history[]` | `tab_approval_action` |
| `pendingApproverUids[]` | `tab_approval_task` |
| `overallStatus` | `status` |

Giống cấu trúc **không có nghĩa là map được từng chặng**. Số chặng, tên chặng, người ký
mỗi chặng do hai bên tự khai và **được phép khác nhau** — đó chính là điều QĐ-I bảo vệ.
Nên luật cứng:

> **Phiếu đang chạy giữa chừng thì KHÔNG đẩy gì sang bên kia.**
> Chỉ khi ra **kết cục** mới đẩy.

Bốn kết cục cả hai bên đều hiểu: **đã duyệt · từ chối · trả về sửa · đã hủy**.
Chặng 1 sang chặng 2 là chuyện nội bộ, bên kia không cần biết và **không được** biết —
biết rồi lại sinh nhu cầu diễn giải chặng của nhau, đúng thứ QĐ-I tránh.

### 15.2. Bên nhận đóng phiên thế nào — cấm ký khống

Bên nhận **không** giả vờ có người ký từng chặng. Nó đóng phiên duyệt của mình bằng
**một hành động hệ thống có ghi rõ nguồn**:

- **Phía ERP:** đóng `ApprovalInstance` và ghi `finish_reason`:
  `"Duyệt trên app đặt xe bởi Nguyễn Văn A (a@dego.vn) lúc 15/09/2026 10:22"`.
  Mọi `ApprovalTask` còn `TASK_PENDING` chuyển sang trạng thái **hủy việc**, kèm lý do
  y hệt — người đang có việc treo phải thấy việc đó biến mất **có lời giải thích**,
  chứ không phải biến mất im lặng.
  `ApprovalAction` ghi **một** dòng duy nhất với `actor_employee_id` = người khớp theo
  email (mục 8), `node_seq = 0` nghĩa là "không thuộc chặng nào", `comment` ghi nguồn.
  ⚠️ **Tuyệt đối không tạo một `ApprovalAction` cho mỗi chặng.** Ghi khống chữ ký trên
  phiếu đóng dấu là chuyện pháp lý, không phải chuyện kỹ thuật.
- **Phía app cũ:** `approval.overallStatus` đặt thẳng, `currentLevel` nhảy tới cuối, và
  thêm **một** `ApprovalHistoryEntry` với `action` tương ứng, `userName` = tên người ký
  bên ERP, `comment` = `"Xử lý trên ERP"`. Không đụng `workflowSnapshot`.

Nhờ vậy đọc lịch sử phiếu ở bất kỳ bên nào cũng thấy đúng một câu chuyện: *"chặng nội bộ
chạy tới đâu, rồi bên kia kết luận, và kết luận đó do ai"*.

### 15.3. Đụng độ — CÚ SAU GHI ĐÈ (QĐ-J)

Đại ca chốt 15/09, và chốt này dựa trên một thứ quan trọng hơn cả luật xử đụng độ:
**không có giai đoạn nào hai bên cùng thao tác** (xem QĐ-J ở README mục 3). Giai đoạn 1
người dùng ở app cũ, giai đoạn 2 người dùng ở ERP. Nên đụng độ không phải chuyện *"sẽ
xảy ra"* mà là *"gần như không xảy ra"* — và khi nó lỡ xảy ra thì:

> **Cú sau ghi đè. Lấy cú sau.**

Bản đầu của mục này dựng luật giành quyền bốn điều (ai thắng, cú thua báo gì, trùng khít
xử sao, lệch đồng hồ xử sao). **Bỏ hết.** Không có hai người thao tác song song thì đó là
bộ máy canh một chuyện không tới, mà mỗi nhánh của nó lại là một chỗ để sai.

Chỉ giữ đúng **một** điều kiện kỹ thuật, vì không có nó thì "cú sau" ra sai người:

⚠️ **"Sau" là sau theo GIỜ BẤM, không phải theo giờ tín hiệu tới.**
Webhook đi qua mạng, có hàng đợi, có lần thử lại — **tới lệch thứ tự là chuyện thường**.
Cứ lấy cú tới sau mà đè thì một tín hiệu bị chậm 30 giây sẽ đè lên kết quả mới hơn, và
lần đối soát đêm chỉ thấy hai bên "đã khớp nhau" ở giá trị cũ. Nên mỗi tín hiệu **bắt buộc
mang theo dấu thời gian lúc người ta bấm ở bên bấm**, và bên nhận so bằng dấu đó: tới
mà cũ hơn cái đang có thì **bỏ qua**, ghi một dòng sổ `stale_skipped` rồi thôi.

Việc này rẻ (một trường trong gói tin, một phép so) nên không có lý do bỏ.

Không cần `decision_owner`, không cần luật trùng khít, không cần cảnh báo lệch đồng hồ.
Đồng hồ hai máy lệch vài giây cũng không sao — cửa sổ mà sai số đó gây hại chỉ rộng bằng
đúng khoảng thời gian hai người bấm cách nhau vài giây ở hai app khác nhau, tức là bằng
không theo QĐ-J.

### 15.4. Ba giới hạn còn lại, nói trước cho khỏi bất ngờ

QĐ-J làm tan gần hết nhóm giới hạn của bản đầu (chúng đều sinh ra từ giả định hai bên
thao tác song song). Còn lại ba, đều nhẹ:

1. **Báo cáo "ai ký chặng mấy" chỉ đúng ở bên người ta thực bấm.** Bên kia chỉ có một
   dòng "xử lý bên <tên app>". Giai đoạn 1 nghĩa là báo cáo chi tiết luồng duyệt nằm ở
   app cũ, ERP chỉ có kết cục; giai đoạn 2 thì ngược lại. Báo cáo hiệu suất duyệt phải
   nói rõ nó đếm trên bên nào, và **số liệu vắt qua hai giai đoạn thì không so được**.
2. **Có cửa sổ vài giây tới vài phút bên không-thao-tác hiện trạng thái cũ.** Webhook rơi
   thì cửa sổ đó kéo tới lần đối soát đêm. Không tránh được, chỉ rút ngắn. Vì chỉ một bên
   thao tác nên cửa sổ này **không gây quyết định sai**, chỉ gây nhìn thấy số cũ.
3. **Phiếu đang giữa chừng thì bên kia chỉ thấy "chờ duyệt"**, không thấy đang ở chặng
   mấy, ai đang cầm. Hệ quả cố ý của 15.1.

> Giới hạn thứ tư của bản đầu — *"người có quyền duyệt bên cũ mà bên ERP không có vẫn
> duyệt được"* — vẫn đúng về mặt kỹ thuật nhưng **không còn là rủi ro**: giai đoạn 1 mọi
> người vốn đã duyệt ở app cũ theo đúng quyền của app cũ. Nó chỉ trở lại thành việc phải
> làm ở **mốc chuyển giai đoạn**, và lúc đó là việc rà quyền một lần, không phải việc
> canh thường trực. Đã ghi thành một dòng trong `TIEN-DO.md`.

### 15.5. Ca nguy nhất — trả về sửa sau khi bên kia đã duyệt

`needs_correction` bên app cũ cho người tạo **sửa nội dung rồi gửi lại**. Nếu lúc đó ERP
đã duyệt xong thì không còn là lệch trạng thái nữa, mà là **ERP đã duyệt một nội dung
không còn tồn tại**.

Luật: **phiếu đã có kết cục ở một bên thì bên kia không được tự mở lại.** Tín hiệu mở lại
đến sau một kết cục thì **không áp**, mà ghi vào sổ với trạng thái `cần người xử` và hiện
lên màn hình quản trị (mục 12). Người xử quyết định: hoặc hủy phiếu cũ và lập phiếu mới,
hoặc chấp nhận nội dung mới rồi duyệt lại tay ở cả hai bên.

Đây là chỗ duy nhất trong cả bộ tài liệu mà máy **cố ý không tự quyết**. Bài học cùng họ
đã có trong repo: phân hệ nghỉ phép, hủy đơn mà không rút phiên duyệt thì người duyệt ký
xong hook vẫn trừ quỹ cho tờ đơn đã hủy (xem `CLAUDE.md`, mục Nghỉ phép).

### 15.6. Chống vọng lại

ERP nhận tin → đóng phiên → hook `entity_hooks` của ERP bắn webhook ngược về app cũ →
app cũ nhận → ... Vòng lặp kinh điển. Áp đúng **nguyên tắc Bốn** của README: bản ghi nào
vừa đổi **vì lệnh của bên kia** thì mang cờ `sync_origin` và **không** bắn ngược lại.
Cờ này đặt trong cùng một giao dịch với cú ghi, không đặt bằng biến toàn cục.
Van an toàn ở mục 14 (một phiếu quá 20 dòng sổ trong một giờ thì tự dừng) là lưới đỡ cuối.
