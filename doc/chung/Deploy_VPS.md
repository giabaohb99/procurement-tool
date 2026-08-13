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

VPS hiện chạy **2 môi trường trên cùng một máy**, mỗi môi trường một thư mục và một nhánh:

| Môi trường | Thư mục | Nhánh | Lệnh compose |
|---|---|---|---|
| **prod** | `~/procurement-tool` | `main` | `docker compose -f docker-compose.production.yml …` |
| **dev (UAT)** | `~/procurement-tool-dev` | `bao` | `docker compose -p procurement-dev --env-file .env.dev -f docker-compose.dev.yml …` |

```bash
cd ~/procurement-tool
git fetch origin && git reset --hard origin/main
git status --short          # PHẢI rỗng mới build
docker compose -f docker-compose.production.yml up --build -d api web
docker compose -f docker-compose.production.yml logs -f api    # chờ "alembic upgrade" + "startup complete"
```

Ba cái dễ sai, sai là mất buổi:

- **KHÔNG `git pull`** trên VPS — có file sinh ra lúc chạy sẽ kẹt merge; luôn `fetch` + `reset --hard` về đúng nhánh.
- **Prod bắt buộc `-f docker-compose.production.yml`.** Thiếu cờ này là compose lấy file mặc định (bản dev) → web chạy vite dev server, nginx trả **502**.
- **Sao lưu DB trước khi có migration** (từ 2026-08-11 CSDL là **MySQL 8.4**, container `procurement-mysql`, định nghĩa ở `~/procurement-db/` — **ngoài repo**, cố ý tách để deploy app không bao giờ đụng tới CSDL):
  ```bash
  docker exec procurement-mysql mysqldump -uroot -p"$DB_ROOT_PASSWORD"       --single-transaction --routines procurement | gzip > ~/proc_backups/prod_truoc_<ma CR>_$(date +%Y%m%d).sql.gz
  ```
  Mật khẩu ở `~/procurement-db/.env` (khoá `DB_ROOT_PASSWORD`) — **khác** mật khẩu MariaDB cũ. Vào Adminer: `ssh -p 51251 -L 18080:127.0.0.1:18080 degosysadmin@180.93.2.176` rồi mở `http://localhost:18080`, server = `procurement-mysql`.
- **App nối CSDL bằng TÊN CONTAINER trên mạng `dego-db`**, không qua cổng máy chủ — nên chuyển CSDL chỉ là đổi `DB_HOST` trong `.env` rồi khởi động lại `api` + `celery`, quay lại cũng vậy. Đổi cổng không đổi được app nối vào đâu.
- **Đổi gì thì build lại cái đó**: sửa FE → build lại `web`; sửa backend → `api`; sửa Trung tâm Hướng dẫn (`help-center/`) → `help`. Cả `web` và `help` đều build tĩnh nên **restart không ăn thua, phải `--build`**.

Sau khi lên, ghi **1 dòng vào [Nhật ký deploy](../tai-lieu-ky-thuat/change-log.md#nhật-ký-deploy-môi-trường-thật)**: đẩy gì, migration tới head nào, file sao lưu tên gì, hành vi nào người dùng thấy đổi ngay.

### 10.1. Nội dung Trung tâm Hướng dẫn sử dụng

Bài hướng dẫn **nằm trong CSDL của từng môi trường**, không đi theo code. Soạn ở local xong, xuất ra `backend/app/seed_data/help-center-content.json`, rồi nạp ở môi trường đích:

```bash
docker exec -w /app <container api> python -m scripts.import_help_content          # chạy thử, không ghi gì
docker exec -w /app <container api> python -m scripts.import_help_content --nap    # ghi thật
```

Khớp bài theo **tiêu đề**, FAQ theo **câu hỏi** — có thì cập nhật, chưa có thì tạo, **không xóa bài nào**; bài chỉ có trong DB mà file không có sẽ được liệt kê ra để tự quyết.
