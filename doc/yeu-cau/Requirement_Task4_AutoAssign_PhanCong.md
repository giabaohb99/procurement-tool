# Requirement — Task 4: Tự động phân bổ nhân sự thu mua (NSTM) theo phân loại khi duyệt PYC

**Phiên bản:** 1.0  
**Ngày:** 2026-07-04  
**Trạng thái:** Chốt — sẵn sàng triển khai  
**Tham chiếu:** `doc/yeu-cau/Plan_CapNhat_Flow_KhaoSat_v2.md` — mục Task 4

---

## 1. Mục tiêu & phạm vi

### 1.1 Mục tiêu

Khi Trưởng phòng duyệt một Yêu cầu mua hàng (PYC), hệ thống tự động điền nhân sự thu mua (NSTM) phụ trách vào từng **dòng hàng** dựa trên **phân loại VTBB/NL** (`item_group`) của dòng đó — thay vì để AdminTM phân công tay từng dòng sau khi duyệt.

**Đây KHÔNG phải auto-duyệt.** Quyết định duyệt/từ chối vẫn hoàn toàn do Trưởng phòng thực hiện.

### 1.2 Phạm vi

| Trong phạm vi | Ngoài phạm vi |
|---|---|
| Bảng cấu hình phân công theo phân loại | Tự động duyệt PYC |
| Màn cấu hình "Phân công phụ trách theo phân loại" | Phân bổ NSTM cho Phiếu khảo sát (task 5, tái dùng logic) |
| Logic tự gán khi endpoint `approve` được gọi | Thay đổi quy trình duyệt PYC |
| Override tay của AdminTM ở màn chi tiết PYC | Gán theo kho hoặc theo phòng ban |
| Reset phân công khi phiếu bị trả về (đã có sẵn) | |

### 1.3 Lợi ích

- Giảm thao tác thủ công: AdminTM không cần phân công dòng nào nữa trong trường hợp cấu hình đúng.
- Liên tục không bị gián đoạn khi NSTM nghỉ: cơ chế dự phòng tự xử lý.
- Minh bạch: dòng hàng nào thiếu cấu hình phân loại sẽ hiển thị rõ để AdminTM xử lý.

---

## 2. Data model

### 2.1 Bảng mới: `tab_category_assignee`

Bảng cấu hình ánh xạ **1 phân loại → 1 NSTM chính + 1 NSTM dự phòng**.

| Cột | Kiểu (SQLAlchemy) | Nullable | Mô tả |
|---|---|---|---|
| `id` | `BigInteger`, PK, autoincrement | NO | Khóa chính (kế thừa `Base`) |
| `item_group_id` | `BigInteger` | NO | FK → `tab_item_group.id` |
| `primary_employee_id` | `BigInteger` | NO | FK → `tab_employee.id` — NSTM chính |
| `backup_employee_id` | `BigInteger` | YES (default 0) | FK → `tab_employee.id` — NSTM dự phòng; 0 = chưa đặt |
| `created_by` | `BigInteger` | NO | (kế thừa `AuditMixin`) |
| `updated_by` | `BigInteger` | NO | (kế thừa `AuditMixin`) |
| `created_at` | `DateTime` | NO | (kế thừa `AuditMixin`) |
| `updated_at` | `DateTime` | NO | (kế thừa `AuditMixin`) |

**Ràng buộc:**
- `item_group_id` phải là `UNIQUE` — mỗi phân loại chỉ có 1 bản ghi cấu hình.
- `primary_employee_id != backup_employee_id` (kiểm tra ở service, không ở DB constraint).
- `primary_employee_id` bắt buộc; `backup_employee_id` tùy chọn.

**Quan hệ:**

```
tab_item_group (1) ──────────── (0..1) tab_category_assignee
tab_employee   (1) ──────────── (0..*) tab_category_assignee [primary_employee_id]
tab_employee   (1) ──────────── (0..*) tab_category_assignee [backup_employee_id]
```

**SQLAlchemy model (sketch):**

```python
class CategoryAssignee(Base, AuditMixin):
    __tablename__ = "tab_category_assignee"

    item_group_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    primary_employee_id: Mapped[int] = mapped_column(BigInteger)
    backup_employee_id: Mapped[int] = mapped_column(BigInteger, default=0)
```

### 2.2 Bảng liên quan — không thay đổi schema

| Bảng | Cột liên quan | Ghi chú |
|---|---|---|
| `tab_purchase_request_item` | `item_group` (String 100), `assignee` (String 100) | `item_group` = tên phân loại (khớp với `tab_item_group.name`); `assignee` = mã nhân viên (`tab_employee.code`) |
| `tab_purchase_request` | `assignee_id` (BigInteger) | NSTM chính toàn phiếu — **không thay đổi** trong task này |
| `tab_item_group` | `id`, `name`, `is_active` | Nguồn lookup phân loại |
| `tab_employee` | `id`, `code`, `full_name`, `is_active` | Nguồn lookup nhân sự |

> **Lưu ý quan trọng:** `PurchaseRequestItem.assignee` lưu **mã nhân viên** (`Employee.code`, kiểu String), không phải `employee_id`. Logic gán cần đọc `Employee.code` từ bản ghi `Employee` tìm được.

---

## 3. Màn hình cấu hình "Phân công phụ trách theo phân loại"

### 3.1 Vị trí & điều hướng

- Menu: **Danh mục → Phân công phụ trách** (hoặc đặt trong nhóm "Cấu hình thu mua").
- Route đề xuất: `/category-assignees`
- Entity name (permission): `category_assignee`

### 3.2 Mô tả UI — màn danh sách

Hiển thị bảng liệt kê tất cả cấu hình hiện có:

| Cột | Dữ liệu |
|---|---|
| Phân loại | Tên phân loại (`tab_item_group.name`) |
| NSTM chính | Tên đầy đủ + mã nhân viên |
| NSTM dự phòng | Tên đầy đủ + mã nhân viên (hoặc "—" nếu chưa đặt) |
| Trạng thái NSTM chính | Badge: "Đang làm" (is_active=true) / "Không hoạt động" (is_active=false) |
| Thao tác | Nút Sửa / Xóa |

Bộ lọc: theo tên phân loại (tìm kiếm text).

Nút **"+ Thêm cấu hình"** ở góc trên phải.

**Các phân loại chưa có cấu hình** nên được hiển thị nổi bật (badge "Chưa cấu hình") hoặc liệt kê riêng ở phần dưới để nhắc AdminTM cấu hình đủ.

### 3.3 Mô tả UI — form thêm/sửa

Form modal hoặc trang riêng với các trường:

| Trường | Loại input | Bắt buộc | Ghi chú |
|---|---|---|---|
| Phân loại | Select (dropdown tìm kiếm) | CÓ | Chỉ chọn từ `tab_item_group` có `is_active=true`; khi THÊM: lọc ra phân loại chưa có cấu hình |
| NSTM chính | Select (dropdown tìm kiếm) | CÓ | Danh sách từ `tab_employee` có `is_active=true` |
| NSTM dự phòng | Select (dropdown tìm kiếm) | KHÔNG | Danh sách từ `tab_employee` có `is_active=true`; không được chọn trùng NSTM chính |

**Validation:**
- Phân loại bắt buộc; khi tạo mới phải unique.
- NSTM chính bắt buộc.
- NSTM dự phòng ≠ NSTM chính (nếu có chọn).
- Thông báo lỗi rõ ràng bằng tiếng Việt.

### 3.4 Phân quyền màn cấu hình

| Role | Quyền |
|---|---|
| `pur_admin` (Admin thu mua) | Xem + Thêm + Sửa + Xóa |
| `pur_manager` (Quản lý thu mua) | Xem (read-only) |
| Các role khác | Không truy cập |

> Seed thêm entity `category_assignee` vào `STD_ROLES` trong `seed.py`:
> - `pur_admin`: `["read", "create", "write", "delete"]`, scope `"all"`
> - `pur_manager`: `["read"]`, scope `"all"`

---

## 4. API endpoints

### 4.1 Module mới: `category_assignee`

Router prefix: `/api/category-assignees`

#### `GET /api/category-assignees`
- **Mô tả:** Danh sách cấu hình phân công, join thông tin phân loại + nhân viên.
- **Quyền:** `category_assignee.read`
- **Query params:** `page`, `limit`, `item_group_name` (filter text)
- **Response:**
```json
{
  "data": {
    "total": 10,
    "items": [
      {
        "id": 1,
        "item_group_id": 3,
        "item_group_name": "Thùng",
        "primary_employee_id": 12,
        "primary_employee_code": "NV001",
        "primary_employee_name": "Nguyễn Văn A",
        "primary_is_active": true,
        "backup_employee_id": 15,
        "backup_employee_code": "NV002",
        "backup_employee_name": "Trần Thị B",
        "backup_is_active": true
      }
    ]
  }
}
```

#### `POST /api/category-assignees`
- **Mô tả:** Tạo cấu hình mới cho 1 phân loại.
- **Quyền:** `category_assignee.create`
- **Body:**
```json
{
  "item_group_id": 3,
  "primary_employee_id": 12,
  "backup_employee_id": 15
}
```
- **Lỗi:** 400 nếu `item_group_id` đã có cấu hình; 400 nếu `primary == backup`.

#### `PATCH /api/category-assignees/{id}`
- **Mô tả:** Cập nhật NSTM chính/dự phòng cho 1 phân loại.
- **Quyền:** `category_assignee.write`
- **Body:** Các trường cần cập nhật (partial update).

#### `DELETE /api/category-assignees/{id}`
- **Mô tả:** Xóa cấu hình (không ảnh hưởng dữ liệu lịch sử — `assignee` trên PYC item đã gán vẫn giữ nguyên).
- **Quyền:** `category_assignee.delete`

### 4.2 Thay đổi endpoint hiện có: `POST /api/purchase-requests/{pid}/approve`

**Trước (hiện tại):**
```python
@router.post("/{pid}/approve")
def approve_pr(pid, data: ApproveIn, ...):
    pr = service.set_status(db, pid, "approved", user.id)
    if data.assignee_id:
        pr.assignee_id = data.assignee_id
        db.commit()
    ...
```

**Sau (bổ sung):** Sau khi `set_status("approved")`, gọi thêm `service.auto_assign_items(db, pr)` trước khi commit và trigger notification.

```python
@router.post("/{pid}/approve")
def approve_pr(pid, data: ApproveIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "approve"))):
    pr = service.set_status(db, pid, "approved", user.id)
    if data.assignee_id:
        pr.assignee_id = data.assignee_id
        db.commit()
    # [MỚI] Tự gán NSTM theo phân loại
    service.auto_assign_items(db, pr)
    trigger_notification(...)
    return success(_out(db, pr), "Đã duyệt")
```

### 4.3 Endpoint gán tay hiện có (giữ nguyên, không đổi)

`PATCH /api/purchase-requests/{pid}/assign` — AdminTM dùng để override gán từng dòng. Đã hoạt động, không cần sửa logic; chỉ cần FE hiển thị đúng cột NSTM và cho phép chỉnh sửa.

---

## 5. Logic tự gán khi duyệt

### 5.1 Hàm `auto_assign_items(db, pr)`

Đặt trong `backend/app/modules/purchase_request/service.py`.

**Thuật toán từng bước:**

```
ĐẦU VÀO: pr (PurchaseRequest đã set status="approved")

1. Lấy danh sách dòng hàng: items = items_of(db, pr.id)

2. Với mỗi dòng item trong items:

   a. Đọc item.item_group (String — tên phân loại)

   b. Nếu item.item_group == "" hoặc None:
      → Bỏ qua (không gán); item.assignee giữ nguyên giá trị cũ (thường = "")
      → Ghi nhận vào danh sách "dòng không có phân loại" để log/cảnh báo

   c. Tìm ItemGroup: ig = db.query(ItemGroup).filter(ItemGroup.name == item.item_group, ItemGroup.is_active == True).first()
      Nếu ig is None:
      → Bỏ qua (không gán); ghi nhận "phân loại không tìm thấy hoặc đã ngưng"

   d. Tìm cấu hình: cfg = db.query(CategoryAssignee).filter(CategoryAssignee.item_group_id == ig.id).first()
      Nếu cfg is None:
      → Bỏ qua (không gán); ghi nhận "phân loại chưa cấu hình NSTM"

   e. Chọn NSTM:
      primary = db.get(Employee, cfg.primary_employee_id)
      Nếu primary và primary.is_active == True:
          assignee_emp = primary
      Else nếu cfg.backup_employee_id > 0:
          backup = db.get(Employee, cfg.backup_employee_id)
          Nếu backup và backup.is_active == True:
              assignee_emp = backup
          Else:
              assignee_emp = None  # cả 2 đều không active
      Else:
          assignee_emp = None  # không có dự phòng, người chính không active

   f. Nếu assignee_emp is not None:
          item.assignee = assignee_emp.code
      Else:
          item.assignee = ""   # để trống; AdminTM phải gán tay

3. db.commit()

4. Ghi audit log: record(db, pr.updated_by, "purchase_request", pr.id, "auto_assign",
   f"Tự động gán NSTM theo phân loại khi duyệt")
```

### 5.2 Bảng quyết định gán

| Trạng thái NSTM chính | Trạng thái dự phòng | Kết quả gán |
|---|---|---|
| `is_active = true` | Bất kỳ | Gán NSTM chính |
| `is_active = false` | `is_active = true` | Gán NSTM dự phòng |
| `is_active = false` | `is_active = false` | Không gán (để trống) |
| `is_active = false` | Chưa đặt (backup_employee_id = 0) | Không gán (để trống) |

### 5.3 Xử lý override tay (AdminTM)

- Sau khi `auto_assign_items` chạy, AdminTM vào màn chi tiết PYC và có thể gọi `PATCH /api/purchase-requests/{pid}/assign` để ghi đè từng dòng bất kỳ.
- Ghi đè **không bị chặn** bởi logic tự động — bất kỳ mã nhân viên nào đều có thể gán.
- Logic `auto_assign_items` **chỉ chạy 1 lần tại thời điểm duyệt**. Nếu AdminTM gán tay sau đó, kết quả gán tay là cuối cùng.
- Nếu phiếu bị **trả về (return)**: hàm `return_pr` đã sẵn có logic xóa `item.assignee = ""` và `pr.assignee_id = 0` — không cần thay đổi.
- Khi phiếu được **gửi duyệt lại** và được duyệt lần 2: `auto_assign_items` chạy lại, ghi đè toàn bộ — kể cả những dòng AdminTM đã gán tay. Đây là hành vi chấp nhận được (khi trả về + sửa + duyệt lại, NSTM reset về mặc định).

---

## 6. Phân quyền

### 6.1 Ai được cấu hình phân công?

| Hành động | Role được phép |
|---|---|
| Xem danh sách cấu hình | `pur_admin`, `pur_manager` |
| Thêm cấu hình mới | `pur_admin` |
| Sửa cấu hình | `pur_admin` |
| Xóa cấu hình | `pur_admin` |

`pur_manager` (Quản lý thu mua) chỉ được **xem** để nắm thông tin phân bổ, không chỉnh sửa.

### 6.2 Ai được gán tay NSTM trên dòng PYC?

| Hành động | Role được phép | Phạm vi |
|---|---|---|
| Gán tay từng dòng (override) | `pur_admin` | Bất kỳ nhân sự nào |
| Xem kết quả gán (cột NSTM) | `pur_admin`, `pur_manager`, `dept_head` (người duyệt), người tạo phiếu | — |
| NSTM tự cập nhật trạng thái dòng hàng của mình | `pur_staff` | Chỉ dòng được gán cho mình (`item.assignee == emp_code`) |

**Lưu ý scope hiện tại:**
- `pur_staff` có scope `proc` trên `purchase_request`: thấy phiếu của mình + phiếu đã approved + phiếu được phân bổ.
- `pur_admin` có scope `proc` trên `purchase_request` + quyền `approve` → gọi được endpoint `/assign`.
- Endpoint `/assign` hiện yêu cầu `require("purchase_request", "approve")` — `pur_admin` và `pur_manager` đều có quyền này.

---

## 7. Tác động tới màn chi tiết PYC

### 7.1 Bảng dòng hàng

Sau khi duyệt, màn chi tiết PYC (trang `/purchase-requests/{id}`) hiển thị thêm (hoặc đảm bảo hiển thị) cột:

| Cột | Hiển thị | Sửa được? |
|---|---|---|
| NSTM phụ trách | Tên nhân viên (hoặc mã nếu không tra được tên) | Chỉ `pur_admin` |
| Trạng thái NSTM | "Đã gán" / "Chưa gán" (badge màu) | Không |

**Logic hiển thị tên từ mã:** Frontend (hoặc API `_out`) cần join tên nhân viên từ `item.assignee` (mã) → `tab_employee.code` → `tab_employee.full_name`. Cách đơn giản: backend trả thêm field `assignee_name` trong danh sách items của `_out`.

### 7.2 Thay đổi `_out` / `items_of` (backend)

Bổ sung `assignee_name` vào dict items trong hàm `_out` của `controller.py`:

```python
# Trong _out(), phần items:
from app.modules.employee.model import Employee

emp_map = {}  # cache mã → tên để tránh query N+1
items_raw = service.items_of(db, pr.id)
# Collect all assignee codes
codes = {i.assignee for i in items_raw if i.assignee}
if codes:
    emps = db.query(Employee).filter(Employee.code.in_(codes)).all()
    emp_map = {e.code: e.full_name for e in emps}

d["items"] = [
    {
        ...,
        "assignee": i.assignee,
        "assignee_name": emp_map.get(i.assignee, ""),
        ...
    }
    for i in items_raw
]
```

### 7.3 Hành vi gán tay (FE)

Khi `pur_admin` nhấn nút chỉnh sửa NSTM trên 1 dòng:
- Mở dropdown chọn nhân viên (danh sách `tab_employee` `is_active=true`).
- Sau khi chọn, gọi `PATCH /api/purchase-requests/{pid}/assign` với body:
```json
{
  "items": [{"id": <item_id>, "assignee": "<emp_code>"}]
}
```
- Không cần gửi `assignee_id` header (chỉ gửi nếu muốn đổi NSTM header phiếu).

---

## 8. Tiêu chí nghiệm thu (Acceptance Criteria)

### AC-01: Tự gán khi duyệt — trường hợp bình thường

**Given** phân loại "Thùng" đã được cấu hình NSTM chính = NV001 (is_active=true), dự phòng = NV002  
**When** Trưởng phòng gọi `POST /api/purchase-requests/{id}/approve`  
**Then** mọi dòng hàng có `item_group = "Thùng"` được gán `assignee = "NV001"` tự động

---

### AC-02: Fallback sang dự phòng khi NSTM chính nghỉ

**Given** phân loại "Nguyên liệu" có NSTM chính = NV003 (is_active=**false**), dự phòng = NV004 (is_active=true)  
**When** Trưởng phòng duyệt PYC có dòng phân loại "Nguyên liệu"  
**Then** dòng đó được gán `assignee = "NV004"` (dự phòng)

---

### AC-03: Không gán khi cả 2 đều nghỉ

**Given** NSTM chính NV003 (is_active=false), NSTM dự phòng NV004 (is_active=false)  
**When** Trưởng phòng duyệt PYC có dòng phân loại đó  
**Then** `item.assignee = ""` (dòng hiển thị "Chưa gán"); hệ thống không báo lỗi, phiếu vẫn được duyệt bình thường

---

### AC-04: Không gán khi dòng thiếu phân loại

**Given** một dòng hàng có `item_group = ""`  
**When** PYC được duyệt  
**Then** `item.assignee` không thay đổi (vẫn = ""); không có lỗi exception

---

### AC-05: Không gán khi phân loại chưa cấu hình NSTM

**Given** phân loại "Bao bì" tồn tại trong `tab_item_group` nhưng chưa có bản ghi trong `tab_category_assignee`  
**When** PYC có dòng phân loại "Bao bì" được duyệt  
**Then** `item.assignee = ""` (không gán); phiếu vẫn duyệt thành công

---

### AC-06: AdminTM ghi đè sau tự gán

**Given** sau khi phiếu được duyệt, dòng đã tự gán `assignee = "NV001"`  
**When** AdminTM gọi `PATCH /api/purchase-requests/{id}/assign` với `{"items": [{"id": X, "assignee": "NV005"}]}`  
**Then** `item.assignee = "NV005"`; kết quả override được lưu; không bị rollback

---

### AC-07: NSTM chỉ thấy dòng được gán cho mình

**Given** người dùng có role `pur_staff`, mã nhân viên = "NV001"  
**When** gọi `GET /api/purchase-requests/{id}` trên phiếu đã duyệt  
**Then** chỉ thấy các dòng có `assignee = "NV001"` (scope `proc` + filter `_see_all_items`)

---

### AC-08: Cấu hình phân công — thêm mới

**Given** AdminTM đang ở màn "Phân công phụ trách theo phân loại"  
**When** thêm cấu hình mới cho phân loại chưa có: chọn phân loại + NSTM chính + lưu  
**Then** bản ghi mới xuất hiện trong danh sách; API `GET /api/category-assignees` trả về bản ghi đó

---

### AC-09: Validation — không cho trùng phân loại

**Given** phân loại "Thùng" đã có cấu hình  
**When** AdminTM thử tạo thêm 1 cấu hình nữa cho "Thùng"  
**Then** API trả lỗi 400 "Phân loại này đã có cấu hình NSTM"

---

### AC-10: Validation — NSTM chính ≠ dự phòng

**Given** AdminTM chọn cùng 1 người cho cả NSTM chính và dự phòng  
**When** lưu  
**Then** API trả lỗi 400 "NSTM dự phòng không được trùng NSTM chính"

---

### AC-11: Màn chi tiết PYC hiển thị tên NSTM

**Given** phiếu đã duyệt, dòng có `assignee = "NV001"`  
**When** bất kỳ người dùng có quyền xem mở chi tiết PYC  
**Then** cột NSTM hiển thị tên đầy đủ của NV001 (không chỉ mã)

---

### AC-12: Phiếu trả về — reset NSTM

**Given** phiếu đã duyệt và đã tự gán NSTM trên các dòng  
**When** Trưởng phòng/AdminTM gọi `POST /api/purchase-requests/{id}/return`  
**Then** tất cả `item.assignee = ""` và `pr.assignee_id = 0` (logic hiện có trong `return_pr`)

---

## 9. Edge cases & lưu ý

### 9.1 PYC có nhiều dòng, nhiều phân loại khác nhau
Mỗi dòng tra cấu hình độc lập → 1 phiếu có thể có nhiều NSTM khác nhau (mỗi người phụ trách phân loại của mình). Đây là hành vi đúng theo yêu cầu.

### 9.2 Phân loại trong `item_group` (String) vs `tab_item_group.name`
Hiện tại `PurchaseRequestItem.item_group` lưu **tên** (không phải ID), phải join qua `name`. Cần đảm bảo tên phân loại nhất quán (case-sensitive). Gợi ý: khi người dùng chọn phân loại khi tạo PYC, frontend gửi đúng `name` từ dropdown danh mục.

### 9.3 Phân loại bị đổi tên sau khi đã cấu hình
Nếu tên `tab_item_group.name` bị sửa, các dòng PYC cũ giữ tên cũ → sẽ không tra được cấu hình nữa. Sau khi triển khai task này, nên hạn chế đổi tên phân loại (hoặc thêm cảnh báo khi sửa ItemGroup).

### 9.4 N+1 query khi auto-assign
Tránh query Employee cho từng dòng. Gợi ý: collect tất cả `primary_employee_id` + `backup_employee_id` từ configs trước, query 1 lần bằng `Employee.id.in_(ids)`.

### 9.5 Concurrency: 2 admin duyệt cùng lúc
Khó xảy ra (phiếu chỉ có 1 trạng thái), nhưng nếu xảy ra: `set_status` sẽ chạy 2 lần → `auto_assign_items` chạy 2 lần → kết quả cuối là gán của lần sau. Không gây corrupt data. Chấp nhận.

### 9.6 NSTM header (`pr.assignee_id`) vs NSTM dòng (`item.assignee`)
- `pr.assignee_id` = ID nhân viên được giao **toàn phiếu** (trường cũ, vẫn giữ nguyên).
- `item.assignee` = mã nhân viên từng dòng (task này tự động điền).
- Task 4 chỉ điền `item.assignee`; `pr.assignee_id` vẫn do người duyệt truyền vào qua `data.assignee_id` (không thay đổi).

### 9.7 Không ảnh hưởng đến khảo sát (task 5)
Logic `auto_assign_items` sẽ được **tái sử dụng** khi task 5 triển khai Yêu cầu khảo sát. Lúc đó chỉ cần gọi hàm tương tự với entity khác. Thiết kế hàm service nên tách rõ phần "tra cấu hình theo item_group → trả về emp_code" thành helper riêng.

---

## 10. Câu hỏi mở

Tất cả các quyết định thiết kế đã được chốt. Không còn câu hỏi mở chặn triển khai.

Các điểm có thể cân nhắc thêm (không bắt buộc trước khi code):

| Điểm | Mô tả | Đề xuất |
|---|---|---|
| Notification khi dòng không được gán | Có nên gửi thông báo cho AdminTM khi có dòng hàng không gán được NSTM? | Giai đoạn 2; hiện tại chỉ để trống `assignee` |
| Hiển thị cảnh báo "dòng chưa gán" trên UI | Badge/icon ở màn danh sách PYC? | Giai đoạn 2 |
| Lịch sử thay đổi NSTM trên dòng hàng | Ghi lại audit khi override tay? | Logic `record()` trong `assign()` đã có ghi `"Phân bổ NSTM"` ở mức phiếu |

---

## Phụ lục: Checklist triển khai

- [ ] **Backend:** Tạo `backend/app/modules/category_assignee/model.py` (`CategoryAssignee`)
- [ ] **Backend:** Tạo `backend/app/modules/category_assignee/schema.py` (Pydantic schemas)
- [ ] **Backend:** Tạo `backend/app/modules/category_assignee/service.py` (CRUD + validation)
- [ ] **Backend:** Tạo `backend/app/modules/category_assignee/controller.py` (router `/api/category-assignees`)
- [ ] **Backend:** Thêm `auto_assign_items()` vào `purchase_request/service.py`
- [ ] **Backend:** Sửa `purchase_request/controller.py` — endpoint `approve_pr` gọi `auto_assign_items`
- [ ] **Backend:** Sửa `_out()` trong `controller.py` — thêm `assignee_name` vào items
- [ ] **Backend:** Thêm entity `category_assignee` vào `app/core/permissions.py` (ENTITIES list)
- [ ] **Backend:** Seed quyền `category_assignee` cho `pur_admin` + `pur_manager` trong `seed.py`
- [ ] **Backend:** Migration Alembic — tạo bảng `tab_category_assignee`
- [ ] **Backend:** Đăng ký router trong `main.py` (hoặc router tổng)
- [ ] **Frontend:** Màn `/category-assignees` (list + form thêm/sửa)
- [ ] **Frontend:** Cột NSTM + tên NSTM trong bảng dòng hàng màn chi tiết PYC
- [ ] **Frontend:** Dropdown chỉnh NSTM từng dòng cho `pur_admin` (gọi `/assign`)
- [ ] **Test:** Verify AC-01 đến AC-12
