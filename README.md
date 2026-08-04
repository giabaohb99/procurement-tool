# Mini Tool Quản lý Thu Mua — DEGO Holding

Web nội bộ (~20–100 user) số hóa toàn bộ quy trình Thu mua của DEGO Holding:

> **Yêu cầu mua (PYC) → Khảo sát giá (NCC/SP) → Đơn mua hàng (PO) → Nhận hàng (GR) → Công nợ → Yêu cầu thanh toán**

Kèm hệ thống **phân quyền RBAC + phạm vi dữ liệu (data scope)**, báo cáo, và dashboard theo quyền.

---

## 1. Tính năng chính

| Nhóm | Module | Mô tả |
|---|---|---|
| **Mua hàng** | Yêu cầu mua (`purchase_request`) | Lập PYC, duyệt nhiều cấp, phân bổ NSTM, trạng thái theo từng dòng hàng |
| | Khảo sát (`survey`) | Khảo sát NCC & khảo sát Sản phẩm/giá, duyệt |
| | Đơn mua hàng (`purchase_order`) | PO + nhiều lần giao hàng (deliveries) trong popup, in A4 ngang |
| | Nhận hàng (`goods_receipt`) | Ghi nhận nhận hàng ngầm khi cập nhật lần giao → tự cộng tồn kho |
| **Kho / Tài chính** | Tồn kho (`inventory`) | Xem tồn, điều chỉnh tồn (+/−) theo bình quân gia quyền |
| | Công nợ (`payable`) | Tự sinh từ PO (hàng hóa + vận chuyển), tuổi nợ (aging) |
| | Yêu cầu thanh toán (`payment_request`) | Gom nhiều khoản nợ cùng NCC thành 1 phiếu, in được |
| **Danh mục** | NCC, Hợp đồng, Sản phẩm, Kho, ĐVT, Phân loại, Công ty, Phòng ban, Nhân sự | CRUD danh mục dùng chung |
| **Quản trị** | Phân quyền (`role`/`user`) | Ma trận quyền theo vai trò + phạm vi dữ liệu theo từng user |
| | Báo cáo (`report`) · Dashboard | Số liệu & biểu đồ theo phạm vi quyền của người xem |
| | Thông báo (`notification`/`alert`) | Thông báo trong app + email (gửi nền) |

---

## 2. Kiến trúc & công nghệ

| Lớp | Công nghệ |
|---|---|
| **Backend** | FastAPI 0.115 · SQLAlchemy 2.0 · Pydantic v2 · PyMySQL |
| **Database** | MySQL 8.0 · **Alembic** (migration) |
| **Frontend** | React 18 · Vite 5 · TypeScript · React Router 6 · react-select · axios |
| **Auth** | JWT (access + refresh) · bcrypt · Google OAuth (tùy chọn) |
| **File đính kèm** | Cloudflare R2 (S3-compatible, qua boto3) |
| **Rate limit** | slowapi |
| **Chạy** | Docker Compose (db · api · web · help · adminer) |

Backend theo mô-đun: mỗi feature là 1 thư mục `app/modules/<feature>/` gồm `model.py` (SQLAlchemy) · `schema.py` (Pydantic) · `service.py` (nghiệp vụ) · `controller.py` (route).

---

## 3. Cấu trúc thư mục

```
procurement-tool/
├─ backend/
│  ├─ app/
│  │  ├─ core/          # config, database, auth (RBAC), scoping, response, audit...
│  │  ├─ modules/       # từng feature (model/schema/service/controller)
│  │  ├─ seed.py        # nạp dữ liệu mẫu + tài khoản + vai trò chuẩn
│  │  └─ main.py        # khởi tạo FastAPI, gắn router
│  ├─ migrations/       # Alembic (versions/)
│  ├─ start.sh          # đợi DB → alembic upgrade → seed → uvicorn --reload
│  └─ requirements.txt
├─ frontend/
│  └─ src/
│     ├─ pages/         # màn hình chi tiết (PYC, PO, Khảo sát, Công nợ...)
│     ├─ components/    # CrudList / CrudDetail (cấu hình hóa), FilterBar, Pagination
│     ├─ config/cruds.tsx  # khai báo các màn CRUD theo cấu hình
│     ├─ auth/          # AuthContext (can(entity, action))
│     └─ App.tsx        # định tuyến
├─ help-center/         # app Hướng dẫn sử dụng (React riêng, dùng chung API) — xem help-center/README.md
├─ doc/                 # tài liệu yêu cầu, thiết kế, phân quyền (xem doc/README.md)
├─ docker/              # Dockerfile.api, Dockerfile.web, Dockerfile.help
├─ docker-compose.yml
├─ .env.example
└─ TASKS.md             # checklist tiến độ
```

---

## 4. Chạy nhanh (Docker)

```bash
cp .env.example .env          # rồi điền giá trị thật (DB, R2, JWT...)
docker compose up --build
```

| Dịch vụ | URL | Ghi chú |
|---|---|---|
| **Web** | http://localhost:8080 | Giao diện chính |
| **Hướng dẫn sử dụng** | http://localhost:8082 | App tài liệu HDSD (dùng chung tài khoản) |
| **API** | http://localhost:8000/api/health | Swagger docs: `/docs` |
| **Adminer** | http://localhost:8081 | Xem/sửa DB trực quan |

Khi khởi động, `api` tự: đợi DB sẵn sàng → **chạy Alembic** (`alembic upgrade head`) → **seed** dữ liệu & tài khoản → chạy uvicorn (hot reload).

### Adminer (xem database)
System **MySQL** · Server **db** · Username/Password theo `.env` (`DB_USER`/`DB_PASSWORD`) · Database **procurement**.

---

## 5. Cấu hình (`.env`)

| Biến | Ý nghĩa |
|---|---|
| `DB_*` | Kết nối MySQL (host/port/name/user/password/root) |
| `JWT_SECRET`, `ACCESS_EXPIRE_MIN`, `REFRESH_EXPIRE_DAYS` | JWT |
| `CORS_ORIGINS` | Origin FE được phép gọi API |
| `LOGIN_RATE_LIMIT` | Giới hạn đăng nhập (mặc định `10/minute`) |
| `ADMIN_CODE`, `ADMIN_PASSWORD` | Tài khoản admin seed |
| `HELP_ADMIN_PASSWORD` | Mật khẩu tài khoản quản trị HDSD (`helpadmin`) |
| `R2_*` | Cloudflare R2 cho file đính kèm |
| `VITE_API_URL`, `VITE_GOOGLE_CLIENT_ID` | FE (Vite đọc lúc dev) |
| `VITE_HELP_URL` | URL app HDSD — menu trong app Thu mua trỏ sang (mặc định `http://localhost:8082`) |

> ⚠️ **Không commit `.env`** (đã nằm trong `.gitignore`). Khóa/secret R2, JWT chỉ để trong `.env`, tuyệt đối không hard-code vào source. Nếu secret từng lộ, **rotate** ngay trên Cloudflare.

---

## 6. Tài khoản & đăng nhập

- **Đăng nhập bằng Email HOẶC Mã nhân viên** + mật khẩu.
- Mọi nhân sự đều có tài khoản: mặc định **username = mật khẩu = mã nhân viên** (đổi mật khẩu sau).
- **Admin mặc định:** mã `degoadmin` · mật khẩu theo `ADMIN_PASSWORD` trong `.env` (mẫu: `dego2026`).
- **Quản trị Hướng dẫn sử dụng:** `helpadmin` (hoặc mã `HDSD0001`) · mật khẩu theo `HELP_ADMIN_PASSWORD` (mẫu: `helpadmin`) — chỉ quản trị tài liệu ở http://localhost:8082.

---

## 7. Hệ thống phân quyền (RBAC + Data Scope)

Hai trục độc lập:

1. **Hành động thuộc về VAI TRÒ** — ma trận `(entity × action)`.
   `ACTIONS = read · create · write · delete · approve · cancel · print · export`.
2. **Phạm vi dữ liệu thuộc về USER** — mỗi lần gán (user × vai trò) mang một **scope** riêng.
   `SCOPES = own · assigned · dept · company · all`, kèm chọn cụ thể / loại trừ theo Công ty / Phòng ban / Nhân sự.

- **Backend:** `require(entity, action)` chặn theo hành động; `apply_scope(query, model, entity, user, profile)` lọc dữ liệu theo phạm vi (HỢP các grant). Hồ sơ quyền cache in-process 60s.
- **Frontend:** `AuthContext.can(entity, action)` để ẩn menu và nút hành động; field bị khóa khi không có quyền ghi.
- **Vai trò chuẩn** (seed): Nhân sự cơ bản · Trưởng phòng · Quản lý công ty · NV thu mua · Quản lý thu mua · Admin thu mua · Quản trị Hướng dẫn sử dụng · Admin hệ thống.

Chi tiết thiết kế: [`doc/phan-quyen/Thiet_Ke_Phan_Quyen.md`](doc/phan-quyen/Thiet_Ke_Phan_Quyen.md).

---

## 8. Cơ sở dữ liệu & Migration (Alembic)

Dự án **dùng Alembic**. `start.sh` tự chạy `alembic upgrade head` mỗi lần container `api` khởi động.

Khi thay đổi model (thêm/sửa cột):

```bash
# 1. Sửa app/modules/<feature>/model.py
# 2. Sinh migration tự động
docker compose exec api alembic revision --autogenerate -m "mo_ta_thay_doi"
# 3. Kiểm tra file trong backend/migrations/versions/ rồi áp
docker compose exec api alembic upgrade head
```

> ⚠️ **Không** chạy `ALTER TABLE` / `INSERT` chứa **tiếng Việt** trực tiếp qua CLI (vd `docker compose exec db mysql -e "..."`) — sẽ gây lỗi double-encoding (mojibake: `Chính thức` → `ChÃnh thá»©c`). Luôn thao tác qua migration hoặc script Python (SQLAlchemy) để đảm bảo UTF-8.

---

## 9. Quy trình phát triển (Dev)

- **Hot reload:** code `backend/` và `frontend/` được mount vào container → sửa là tự nạp lại.
- **Thêm dependency FE** (sửa `package.json`): cài lại + restart:
  ```bash
  docker compose exec web npm install
  docker compose restart web
  ```
- **Thêm dependency BE** (sửa `requirements.txt`): `docker compose up --build api`.
- **Seed lại dữ liệu/quyền:** `docker compose exec api python -m app.seed` (idempotent).

---

## 10. Tài liệu

Toàn bộ tài liệu nằm trong `doc/` — mục lục: [`doc/README.md`](doc/README.md).

| Chủ đề | Đường dẫn |
|---|---|
| Yêu cầu tổng thể | [`doc/yeu-cau/Requirement_Mini_Tool_Thu_Mua.md`](doc/yeu-cau/Requirement_Mini_Tool_Thu_Mua.md) |
| Yêu cầu Yêu cầu mua (chi tiết) | [`doc/yeu-cau/Requirement_YeuCauMua_ChiTiet.md`](doc/yeu-cau/Requirement_YeuCauMua_ChiTiet.md) |
| Thiết kế phân quyền | [`doc/phan-quyen/Thiet_Ke_Phan_Quyen.md`](doc/phan-quyen/Thiet_Ke_Phan_Quyen.md) |
| Quy ước đặt tên | [`doc/chung/NAMING_CONVENTIONS.md`](doc/chung/NAMING_CONVENTIONS.md) |
| Thiết kế giao diện / Dashboard | [`doc/thiet-ke/`](doc/thiet-ke/) |

---

## 11. Lộ trình còn lại (tham khảo `TASKS.md`)

- Worker nền (Celery + Redis) cho email/thông báo thay cho background task.
- Chuông thông báo trên FE (đếm chưa đọc, danh sách).
- Duyệt PO theo ngưỡng giá trị.
- Quy đổi đơn vị tính (Sheet 5).
