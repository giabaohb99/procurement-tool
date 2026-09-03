# GIỚI HẠN TÀI NGUYÊN DOCKER CHO MÁY LẬP TRÌNH

**Bản hiện hành:** 03/09/2026 · Áp cho **stack local**, không áp cho VPS.

Tài liệu này dành cho cả người lẫn trợ lý AI làm việc trên repo. Đọc trước khi than
"máy đơ khi chạy test" hoặc trước khi định gỡ mấy dòng `mem_limit` trong `docker-compose.yml`.

---

## 1. Triệu chứng và nguyên nhân

**Triệu chứng.** Mỗi lần chạy `pytest`, `npm run check`, hoặc `docker compose up --build`,
Docker vọt lên hơn 90% CPU và 10–20 GB RAM. Máy đứng hình vài chục giây, ứng dụng đang mở
(IDE, trình duyệt, Claude Code) tự thoát.

**Nguyên nhân — không phải do test nặng, mà do chưa ai đặt trần.** Hai tầng đều bỏ ngỏ:

| Tầng | Mặc định khi không cấu hình | Hậu quả |
|---|---|---|
| Máy ảo WSL2 (chứa toàn bộ Docker) | Lấy **50% RAM** và **toàn bộ số lõi CPU** | Docker chiếm sạch lõi, Windows không còn lõi để vẽ giao diện |
| Từng container | **Không giới hạn** | Một container phình là kéo sập cả stack |

Chỗ chết là **lõi CPU**, không phải RAM. Hết RAM thì máy chậm dần và còn cứu được; hết lõi
thì hệ điều hành không kịp xử lý cả sự kiện chuột, nên nó **đứng**, rồi trình quản lý cửa sổ
kết luận ứng dụng "không phản hồi" và tắt đi.

**Yếu tố làm nặng thêm: stack local có 11 container.** `db` · `adminer` · `api` · `web` ·
`help` · `erp` · `redis` · `qdrant` · `redisinsight` · `celery-worker` · `celery-beat`.
Đa số phiên làm việc chỉ cần 4–5 cái.

---

## 2. Hai tầng chặn — phải làm cả hai

### 2.1 Tầng máy ảo — `%USERPROFILE%\.wslconfig`

**Đây là tầng quan trọng nhất, và là tầng duy nhất chống được đơ máy.**

Tệp này nằm ở thư mục người dùng của Windows, **không nằm trong repo** và **không commit
được** — vì con số phụ thuộc cấu hình từng máy. Mẫu kèm hướng dẫn ở
[`docker/wslconfig.example`](../../docker/wslconfig.example).

```bash
# 1) Chép mẫu về thư mục người dùng (chạy trong Git Bash)
cp docker/wslconfig.example "$USERPROFILE/.wslconfig"
```

Sửa hai con số cho khớp máy — nguyên tắc: **cho Docker khoảng 1/3 RAM và 1/3 số lõi**.

| Máy | `memory` | `processors` | `swap` |
|---|---|---|---|
| 16 GB / 8 lõi | `6GB` | `4` | `2GB` |
| 32 GB / 16 lõi | `10GB` | `6` | `4GB` |
| 32 GB / 22 lõi | `10GB` | `8` | `4GB` |
| 64 GB / 24 lõi | `16GB` | `10` | `4GB` |

Áp dụng — lệnh này **tắt hết container đang chạy**, lưu việc trước khi bấm:

```bash
wsl --shutdown
```

Đợi khoảng 15 giây, mở lại Docker Desktop, rồi `docker compose up -d`. Kiểm lại:

```bash
docker info --format "{{.NCPU}} cpus / {{.MemTotal}} bytes"
```

Phải ra đúng số lõi vừa đặt. Còn ra 22 lõi (hay số lõi thật của máy) nghĩa là tệp chưa ăn —
kiểm lại đường dẫn, tệp phải nằm ở `C:\Users\<tên>\.wslconfig` chứ không phải trong repo.

⚠️ **Không đặt `networkingMode=mirrored`.** Nó hay làm hỏng ánh xạ cổng của Docker Desktop,
mất luôn `localhost:8000` / `:8080` / `:8083`, mà không giúp gì cho việc chặn tài nguyên.

### 2.2 Tầng container — `docker-compose.yml`

Trần từng service đã nằm sẵn trong [`docker-compose.yml`](../../docker-compose.yml), commit
theo repo nên cả đội dùng chung. Không phải làm gì thêm.

| Service | RAM | CPU | Ghi chú |
|---|---|---|---|
| `db` | 1 GB | 2 | Kèm `--innodb-buffer-pool-size=256M` — MySQL mặc định tự phình theo RAM nhìn thấy |
| `api` | 2 GB | 3 | Rộng hơn các service khác vì `pytest` chạy trong chính container này |
| `erp` | 3 GB | 2 | Cây mã `frontend-v2` lớn nhất; đo thực tế **~1,8 GB lúc rảnh** |
| `web` | 1500 MB | 1.5 | |
| `help` | 1 GB | 1 | |
| `celery-worker` | 1 GB | 1 | Local hạ xuống `-c 1`; VPS vẫn `-c 2` |
| `celery-beat` | 384 MB | 0.5 | |
| `redis` | 384 MB | 0.5 | |
| `qdrant` | 1 GB | 1 | |
| `adminer` | 256 MB | 0.5 | |
| `redisinsight` | 384 MB | 0.5 | |

Trần là **trần**, không phải phần đặt trước — container không dùng thì không chiếm. Tổng
trần cố ý cao hơn mức `.wslconfig` một chút, vì không bao giờ có chuyện mọi container cùng
chạm trần một lúc.

Ba service Vite (`web`, `help`, `erp`) còn được ghim `NODE_OPTIONS=--max-old-space-size` để
đống nhớ của Node không phình dần theo thời gian chạy.

---

## 3. Máy mình yếu hơn thì làm sao

**Đừng sửa `docker-compose.yml`** — tệp đó dùng chung cả đội. Tạo
`docker-compose.override.yml` ở thư mục gốc; `docker compose up` **tự gộp** nó đè lên tệp
chính mà không cần cờ `-f`, và tệp này đã được `.gitignore` bỏ qua nên không lọt lên repo.

```yaml
# docker-compose.override.yml — riêng của máy tôi, không commit
services:
  erp:
    mem_limit: 2g
    cpus: 1
  api:
    mem_limit: 1g
    cpus: 2
```

⚠️ Override **chỉ tự gộp khi KHÔNG truyền `-f`**. Deploy dev/prod đều có `-f` nên hoàn toàn
không bị ảnh hưởng — xem [`quy-trinh-nhanh-va-deploy.md`](quy-trinh-nhanh-va-deploy.md).

---

## 4. Cách rẻ nhất: tắt bớt container

Không phải sửa gì, và giảm được nhiều hơn mọi cách chỉnh trần:

```bash
docker compose stop adminer redisinsight    # công cụ soi, cần thì bật lại
docker compose stop qdrant                  # nếu không đụng tới Trợ lý AI
docker compose stop web help                # nếu đang chỉ làm frontend-v2 (erp)
docker compose stop erp help                # nếu đang chỉ làm giao diện cũ (web)
```

Chỉ chạy `db` + `api` + một bản giao diện là đủ cho phần lớn công việc.

Xem cái gì đang ăn tài nguyên:

```bash
docker stats --no-stream --format "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

---

## 5. Vì sao `erp` ngốn CPU cả khi không ai đụng

Bind-mount trên Windows **không phát sự kiện hệ tệp** sang container Linux, nên Vite buộc
phải dò lại cây mã theo chu kỳ. Cấu hình hiện tại ở
[`frontend-v2/vite.config.ts`](../../frontend-v2/vite.config.ts):

```ts
watch: { usePolling: true, interval: 1000, binaryInterval: 2000 }
```

Đo thực tế: `erp` chiếm **17,76% CPU và 1,82 GB RAM khi hoàn toàn rảnh**, trong khi `web` và
`help` cùng loại chỉ khoảng 80 MB. Bỏ `usePolling` thì mất HMR trên Windows nên **không bỏ
được**; nâng `interval` lên `3000` sẽ giảm rõ, đổi lại lưu tệp xong phải chờ lâu hơn mới thấy
trang tự tải lại. Chưa đổi vì đây là tệp dùng chung — ai muốn đổi thì bàn trước.

---

## 6. Luật cho trợ lý AI làm việc trên repo này

1. **Chỉ chạy test của phần vừa sửa.** Quét cả `test/backend` là một trong những nguyên nhân
   chính làm máy đơ, và gần như không bao giờ cần thiết.
   Đúng: `docker compose exec -T api python -m pytest test/backend/test_process.py -q`
   Sai: `docker compose exec -T api python -m pytest test/backend -q`
2. **Không tự ý gỡ `mem_limit` / `cpus`** trong `docker-compose.yml`. Thấy container bị giết
   vì hết bộ nhớ thì báo lại và đề xuất số mới, đừng lặng lẽ bỏ trần.
3. **Không chạy `docker compose up --build`** khi chỉ cần khởi động lại. Code đã bind-mount
   nên `docker compose restart <service>` là đủ; chỉ build lại khi đổi `requirements.txt`,
   `package.json`, hoặc `Dockerfile.*`.
4. **Không tự chạy `wsl --shutdown`** — lệnh này giết mọi container đang chạy. Đề xuất cho
   người dùng tự bấm.
5. **Đụng vào `docker-compose.dev.yml` hay `docker-compose.production.yml` thì đọc
   [`quy-trinh-nhanh-va-deploy.md`](quy-trinh-nhanh-va-deploy.md) trước.** Trần trong tài
   liệu này **chỉ áp cho local**; VPS có cấu hình riêng và không đặt trần vì máy chủ ở đó
   không phải chạy giao diện đồ họa cho ai cả.

---

## 7. Số đo tham chiếu

Đo ngày 03/09/2026 trên máy 31,4 GB RAM / 22 lõi, 11 container **đang rảnh**, trước khi đặt trần:

| Container | CPU | RAM |
|---|---|---|
| `erp` | **17,76%** | **1,82 GB** |
| `api` | 4,65% | 254 MB |
| `web` | 1,62% | 77 MB |
| `help` | 1,24% | 85 MB |
| `db` | 0,44% | 452 MB |
| `celery-worker` | 0,15% | 269 MB |
| `qdrant` | 0,25% | 177 MB |
| `redisinsight` | 0,00% | 120 MB |
| `celery-beat` | 0,00% | 100 MB |
| `redis` | 0,14% | 8 MB |
| `adminer` | 0,00% | 9 MB |

Trần máy ảo lúc đó: **15,34 GB RAM / 22 lõi** — tức là bằng đúng mặc định của WSL2, chưa hề
bị chặn. Con số này là lý do có tài liệu này.
