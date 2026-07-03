# Runbook — Deploy lên VPS

Kèm cấu hình nginx mẫu ở `docker/nginx.sample.conf`. Xem thêm [Go_Live_Checklist.md](Go_Live_Checklist.md).

---

## 0. Yêu cầu VPS
- Ubuntu 22.04+ (hoặc tương đương), **Docker + Docker Compose plugin**.
- Domain trỏ về IP VPS (VD `thumuatool.degoholding.vn`).
- Mở port 80/443 (nginx). Không public 8000/8080/3306/8081 ra internet.

## 1. Lấy code
```bash
cd /opt
git clone https://github.com/giabaohb99/procurement-tool.git
cd procurement-tool
git checkout bao        # hoặc branch/tag production
```

## 2. Tạo `.env` (KHÔNG commit)
```bash
cp .env.example .env
nano .env
```
Điền bắt buộc:
- `DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD/DB_ROOT_PASSWORD` — MySQL production
  (dùng service `db` trong compose thì `DB_HOST=db`; dùng MySQL ngoài thì điền host thật).
- `JWT_SECRET` — chuỗi ngẫu nhiên **mạnh** (`openssl rand -hex 32`), **BACKUP** (khóa mã hóa secret trong DB).
- `ADMIN_CODE` / `ADMIN_PASSWORD` — admin seed (đổi khỏi demo).
- `CORS_ORIGINS=https://thumuatool.degoholding.vn`
- `FRONTEND_URL=https://thumuatool.degoholding.vn`
- `VITE_API_URL=https://thumuatool.degoholding.vn`  (FE gọi qua reverse proxy `/api`)
> R2/SMTP KHÔNG cần ở `.env` — cấu hình trong app (mục 5).

## 3. Build & chạy
```bash
docker compose up --build -d
docker compose logs -f api    # chờ "alembic upgrade" + "Application startup complete"
```
> Đổi `.env` về sau → `docker compose up -d` (recreate), KHÔNG `restart`.

## 4. Reverse proxy + HTTPS (nginx)
- Copy `docker/nginx.sample.conf` → `/etc/nginx/sites-available/thumua.conf`, sửa `server_name`.
- Bật site + cấp SSL:
```bash
ln -s /etc/nginx/sites-available/thumua.conf /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
apt install certbot python3-certbot-nginx -y
certbot --nginx -d thumuatool.degoholding.vn
```

## 5. Cấu hình trong app (giao diện)
Đăng nhập admin → **Hệ thống → Cấu hình hệ thống**:
- **R2**: endpoint, bucket, public URL, **Access Key ID + Secret Key (khóa MỚI đã rotate)** → "Kiểm tra kết nối R2" phải OK.
- **Email**: bật/tắt tùy nhu cầu; nếu bật để test → đặt tạm *Email test override* = email của bạn, khi chạy thật thì **xóa override**.

## 6. Dữ liệu
- Import master data thật (Công ty, Phòng ban, Nhân sự, NCC, Sản phẩm, Kho, ĐVT, Phân loại).
- Tạo tài khoản nhân sự (username = mã NV).
- **Xóa dữ liệu mẫu/test** (KS0000x, PYC test, thông báo test); khôi phục mật khẩu test.
- Rà **Phân quyền**; tạo vai trò **Admin IT** (quyền `setting`) nếu cần.

## 7. Bảo mật (bắt buộc)
- ☐ **Rotate khóa R2** (khóa cũ đã lộ trong quá trình dev).
- ☐ Đổi `ADMIN_PASSWORD` khỏi demo.
- ☐ `JWT_SECRET` mạnh + backup.
- ☐ Tắt/ẩn Adminer (xóa service `adminer` trong compose hoặc chặn firewall).

## 8. Sao lưu & vận hành
```bash
# backup DB định kỳ (cron)
docker compose exec -T db mysqldump -uroot -p"$DB_ROOT_PASSWORD" procurement > /backup/procurement_$(date +%F).sql
```
- Backup `JWT_SECRET` ngoài server.
- Theo dõi `docker compose logs api`.

## 9. Smoke test sau deploy
- ☐ Đăng nhập admin OK.
- ☐ Tạo PYC → gửi duyệt → duyệt.
- ☐ Upload 1 file đính kèm → mở link được.
- ☐ "Kiểm tra kết nối R2" OK.
- ☐ Chuông hiển thị thông báo/cảnh báo.

## 10. Cập nhật phiên bản mới
```bash
cd /opt/procurement-tool
git pull
docker compose up --build -d   # tự chạy migration mới
```
