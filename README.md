# Procurement Tool — Mini Tool Quản lý Thu Mua

Web nội bộ (~20 user) số hóa quy trình Thu mua: Khảo sát → Mua hàng → Nhận hàng (GR) → Công nợ.

## Stack
- **Backend:** FastAPI + SQLAlchemy + MySQL
- **Frontend:** React + Vite + TypeScript
- **Async (Phase 3+):** Celery + Redis
- **File:** Cloudflare R2 (S3-compatible)
- **Chạy:** Docker Compose

## Thư mục
```
procurement-tool/
├─ doc/        # tài liệu mô tả + quy ước đặt tên
├─ backend/    # FastAPI API
├─ frontend/   # React + Vite
├─ docker-compose.yml
├─ .env.example
└─ TASKS.md    # checklist tiến độ (làm tới đâu tick tới đó)
```

## Chạy nhanh (Docker)
```bash
cp .env.example .env          # rồi điền giá trị thật (DB, R2, JWT...)
docker compose up --build
# API:      http://localhost:8000/api/health   (docs: /docs)
# Web:      http://localhost:8080
# Adminer:  http://localhost:8081   (xem DB)
```

### Adminer (xem database)
Mở http://localhost:8081 và đăng nhập:
- System: **MySQL** · Server: **db** · Username/Password: theo `.env` (`DB_USER`/`DB_PASSWORD`) · Database: **procurement**
Khi khởi động, API tự tạo bảng + seed tài khoản admin.

## Tài khoản mặc định
- Mã đăng nhập: `degoadmin`
- Mật khẩu: `dego2026`
- Vai trò: **Admin (full quyền)**

> Đăng nhập hiện dùng **mã nhân viên + mật khẩu** (nội bộ). Google OAuth làm sau.

## Quy ước
Xem `doc/NAMING_CONVENTIONS.md` và `doc/Requirement_Mini_Tool_Thu_Mua.md`.

## Quy tắc an toàn dữ liệu (Data Safety Rules)
**CẢNH BÁO: DỰ ÁN HIỆN TẠI CHƯA SỬ DỤNG ALEMBIC MIGRATION.**
Do đó, khi cập nhật code có liên quan đến cấu trúc cơ sở dữ liệu (thêm/sửa cột, thay đổi model SQLAlchemy), **TUYỆT ĐỐI KHÔNG ĐƯỢC BỎ QUA** bước cập nhật trực tiếp vào MySQL.
- Bất kỳ thay đổi nào trong `model.py` phải đi kèm với việc cập nhật cấu trúc bảng (`ALTER TABLE`) trực tiếp trong cơ sở dữ liệu.
- Viết file script Python (sử dụng SQLAlchemy) hoặc `.sql` để chạy lệnh `ALTER TABLE` khi deploy.
- **KHÔNG** thao tác `ALTER TABLE` hoặc `INSERT/UPDATE` chứa chuỗi tiếng Việt trực tiếp qua Command Line / PowerShell (vd: `docker compose exec db mysql -e "..."`). Việc này sẽ gây lỗi mã hóa kép (Unicode double-encoding mojibake), biến chữ `Chính thức` thành `ChÃnh thá»©c` trong database.
- Luôn chạy script qua file `.py` hoặc mount file `.sql` vào container để đảm bảo đúng định dạng `UTF-8`.
- Nếu thiếu bước cập nhật schema, API sẽ báo lỗi 500 do thiếu cột, khiến toàn bộ dữ liệu bảng bị ẩn/mất khỏi giao diện, gây gián đoạn hệ thống nghiêm trọng.
