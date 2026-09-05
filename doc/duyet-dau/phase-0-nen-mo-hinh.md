# PHA 0 — Nền & mô hình dữ liệu

> Tổng quan: [README.md](README.md) · Log: [TIEN-DO.md](TIEN-DO.md). Trạng thái: **CHƯA LÀM**.
> Nền cho mọi phase sau: chuẩn hóa bảng theo R2, mở chính sách tệp, seed vai trò.

## Mục tiêu
Đưa **stub** `seal_request` / `seal_type` (chỉ model+schema) về đúng khuôn nền của Đặt xe: `status`
là **SMALLINT + hằng số**, khai **chính sách tệp đính kèm**, **seed vai trò** Văn thư/Quản trị con dấu,
và **đăng ký entity** vào màn cấu hình luồng duyệt. Không đụng nghiệp vụ (để PHA 1+).

## Phạm vi & việc cụ thể
- [ ] `model.py`: đổi `status: Mapped[str] String(30)="draft"` → **`Mapped[int] SmallInteger` default `SEAL_DRAFT`**; thêm bộ hằng số `SEAL_*` + dict nhãn (khuôn `vehicle_booking.model`).
- [ ] `model.py`: thêm cột **`copies: SmallInteger default 1`** (số bản cần đóng dấu).
- [ ] Migration **`seal1status01`**: `ALTER` `status` VARCHAR→SMALLINT (map "draft"→1 nếu có, mặc định 1), `ADD copies`.
- [ ] `core/file_registry.py`: thêm **`FILE_POLICY["seal_request"] = ("seal_request", <đuôi pdf+ảnh>, <MB>)`**.
- [ ] Xác nhận `core/scoping.py` đã có `seal_request` (company/dept/owner) + `seal_type` PUBLIC — **không sửa** (đã khai).
- [ ] `seed.py`: thêm vai trò **`seal_clerk`** (Văn thư) + **`seal_admin`** (Quản trị con dấu); cấp **`seal_request:approve`** cho vai trò Trưởng bộ phận.
- [ ] frontend-v2: đăng ký `seal_request` vào bản đồ entity của `/approval/flows` (`entity-link.ts`: ENTITY_LABELS + ROUTES).

## Thiết kế kỹ thuật
Bộ mã trạng thái (khai trong `seal_request/model.py`):
```python
SEAL_DRAFT = 1      # Nháp
SEAL_PENDING = 2    # Chờ duyệt (TBP)
SEAL_APPROVED = 3   # Đã duyệt — chờ Văn thư đóng dấu
SEAL_COMPLETED = 4  # Hoàn thành — đã đóng dấu
SEAL_REJECTED = 5   # Từ chối — khóa
SEAL_CANCELLED = 6  # Đã hủy
SEAL_RETURNED = 7   # Yêu cầu chỉnh sửa — trả người tạo
SEAL_STATUS_LABELS = {1:"Nháp", 2:"Chờ duyệt", 3:"Đã duyệt", 4:"Hoàn thành",
                      5:"Từ chối", 6:"Đã hủy", 7:"Yêu cầu chỉnh sửa"}
EDITABLE_STATUSES = (SEAL_DRAFT, SEAL_RETURNED)
```
Vai trò seed (khuôn `STD_ROLES`):
| Mã | Tên | Quyền | Phạm vi |
|---|---|---|---|
| `seal_clerk` | Văn thư | `seal_request` read/write · `seal_type` read | `company` |
| `seal_admin` | Quản trị con dấu | `seal_request` read · `seal_type` read/create/write/delete | `all` |
| *(TBP sẵn có)* | Trưởng bộ phận | + `seal_request` read/approve | `dept` |

Chính sách tệp: `_DOC` (pdf + ảnh, ~50 MB — chứng từ có thể ~17 MB). Nếu URL không được lộ công khai,
thêm `seal_request` vào `PRIVATE_ENTITIES` (`file_registry.py`).

## Cấu hình / migration
```bash
docker compose exec api alembic revision -m "seal1status01_status_smallint_copies"   # rồi sửa tay
docker compose exec api alembic upgrade head
docker compose exec -T api python -m app.seed        # nạp vai trò seal_clerk/seal_admin (LOCAL)
```
⚠️ `status` là cột **đổi kiểu** — viết migration TAY (autogenerate hay bỏ sót đổi kiểu). Bảng
`tab_seal_request` **chưa có dữ liệu** (chưa từng có controller) nên `ALTER` an toàn.

## Chống trùng / Idempotent
- Seed vai trò idempotent (khuôn `STD_ROLES`); chạy lại không đẻ trùng. Prod đổi vai trò cần `SEED_FORCE_SYNC=true` một lần (xem CLAUDE.md).
- Migration một chiều: `downgrade` trả `status` về VARCHAR + drop `copies`.

## Kiểm thử & tiêu chí
- `alembic upgrade head` sạch; `\d tab_seal_request` thấy `status SMALLINT`, có `copies`.
- `python -m app.seed` tạo `seal_clerk`/`seal_admin`; đăng nhập user gán vai trò → `get_perm_profile` có grant `seal_request`.
- `test_pham_vi_khai_du_b07.py` vẫn xanh (entity `seal_request`/`seal_type` đã khai đủ SCOPE_FIELDS).

## Rủi ro & lưu ý
- **Đừng để status vừa String vừa SMALLINT giữa hai môi trường** — deploy migration trước khi bật controller.
- `company_id` là **công ty con dấu** (người tạo chọn), KHÔNG luôn = công ty phòng ban người tạo → chớ auto-fill đè khi người dùng đã chọn (xử lý ở PHA 1 `create`).
- Chưa seed dữ liệu mẫu ở phase này (chưa có service tạo phiếu) — để PHA 1.
