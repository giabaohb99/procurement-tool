# Quy trình nhánh & Deploy

> Tệp này là **luật**, không phải ghi chú. Đọc trước mỗi lần đụng vào `main` hoặc vào VPS.
> Viết ngày 22/08/2026, sau sự cố `erp-v2` lọt vào `main` (mục A.4).

---

## 0. Bản đồ một trang

| | **PROD** | **DEV** |
|---|---|---|
| Nhánh git | **`main`** | **`erp-v2`** |
| Thư mục trên VPS | `~/procurement-tool` | `~/procurement-tool-dev` |
| Thư mục ở máy local | `D:\New folder\thuthapykien\procurement-main` | `D:\New folder\thuthapykien\procurement-tool` |
| File compose | `docker-compose.production.yml` | `docker-compose.dev.yml` + `--env-file .env.dev` |
| Tên project compose | `procurement-tool` | `procurement-tool-dev` |
| Database (MySQL 8.4 chung) | `procurement` | `procurement_dev` |
| Giao diện Thu mua (bản cũ) | https://thumua.degoholding.vn | https://devthumua.degoholding.vn |
| Giao diện ERP v2 | *(chưa có ở prod)* | https://deverp.degoholding.vn |
| Trung tâm HDSD | https://help.degoholding.vn | https://devhelp.degoholding.vn |

Cả hai thư mục trên VPS là **hai worktree của CÙNG một repo git**. Ở máy local cũng vậy.
Vì dùng chung một kho ref, **bắt buộc mỗi worktree giữ một nhánh khác nhau** — nếu để chung
nhánh thì deploy bên này sẽ dời ref của bên kia, bên kia báo "Already up to date" rồi lặng lẽ
build lại code CŨ.

---

## A. LUẬT NHÁNH

### A.1. Sửa cái gì thì đi nhánh nào

| Sửa thư mục | Nhánh | Vì sao |
|---|---|---|
| `backend/` | **`main`** | Prod đang chạy backend này. Sửa xong merge sang `erp-v2`. |
| `frontend/` | **`main`** | Đây là giao diện **đang chạy thật** cho người dùng. Đã đóng băng: chỉ vá lỗi. |
| `help-center/` | **`main`** | Đang chạy thật ở `help.degoholding.vn`. |
| `frontend-v2/` | **`erp-v2`** | Giao diện ERP mới, prod chưa bật. **Tuyệt đối không đưa sang `main`.** |
| `doc/erp/`, `ke-hoach/` | **`erp-v2`** | Tài liệu của việc đang làm dở. |
| `doc/tai-lieu-ky-thuat/` | theo commit đi kèm | change-log đi cùng commit sửa mã. |

Tính năng mới của giao diện → `frontend-v2/` trên `erp-v2`.
Vá lỗi màn đang chạy thật → `frontend/` trên `main`.

### A.2. Chiều merge — MỘT CHIỀU

```
main  ──────►  erp-v2        ĐƯỢC (đưa bản vá prod sang dev)
main  ◄──────  erp-v2        CẤM  (kéo 34 migration văn thư + đa pháp nhân vào prod)
```

Muốn đưa một commit từ `erp-v2` về `main` thì **cherry-pick đúng commit đó**, không merge:

```bash
cd "D:/New folder/thuthapykien/procurement-main"
git cherry-pick <sha>
```

Chỉ cherry-pick commit **chỉ đụng `backend/` hoặc `frontend/`**. Kiểm trước bằng
`git show --stat <sha>` — thấy `frontend-v2/` hay `backend/migrations/` lạ thì dừng.

### A.3. Bốn việc bắt buộc trước mỗi lần push

```bash
git status --short          # 1. phải RỖNG (hoặc chỉ còn thứ mình cố ý sửa)
git rev-parse --abbrev-ref HEAD   # 2. đúng nhánh mình định đẩy chưa
git fetch origin            # 3. người khác cũng đẩy lên main và erp-v2
git log --oneline origin/main..main   # 4. ĐẾM commit — nhiều hơn dự kiến là có chuyện
```

Bước 4 là chốt chặn quan trọng nhất. Nếu định đẩy 1 commit mà nó liệt kê 40 dòng lạ → **dừng**,
xem mục A.4.

### A.4. BẪY: `git merge erp-v2` lúc đang đứng ở `main` KHÔNG hỏi gì cả

Ngày 22/08/2026, `main` nuốt trọn `erp-v2`: **948 tệp, +117.144 dòng**, trong đó **34 migration**
văn thư / đa pháp nhân. Code đó đã lên tới thư mục prod trên VPS — chỉ cần một lệnh
`up -d --build api` là 34 migration chạy thẳng vào database thật.

**Vì sao không ai thấy:** trước đó `main` đã được merge VÀO `erp-v2`, nên `main` là **tổ tiên**
của `erp-v2`. Git xử lý bằng **fast-forward**: không đẻ commit merge, không mở editor, không
báo gì. `git log` sau đó trông hoàn toàn bình thường.

**Chặn gốc:** luôn giữ **hai worktree**. Khi mỗi nhánh có thư mục riêng thì không còn nhu cầu
`git checkout` qua lại, và không ai gõ `git merge` nhầm chỗ. Nếu thư mục `procurement-main`
biến mất, dựng lại:

```bash
cd "D:/New folder/thuthapykien/procurement-tool" && git worktree add "../procurement-main" main
```

**Cách cứu nếu lỡ tay lần nữa:**

```bash
git reflog show main                    # tìm dòng "merge erp-v2: Fast-forward"
```

Commit ở dòng **ngay DƯỚI** nó chính là `main` sạch cuối cùng. Rồi:

```bash
git tag backup/main-truoc-khi-go-merge-$(date +%Y%m%d)   # thắt dây an toàn
git reset --hard <sha-sạch>
git cherry-pick <sha>                   # nhặt lại commit backend lỡ làm ở erp-v2
MSYS_NO_PATHCONV=1 GIT_SSH_COMMAND="C:/Windows/System32/OpenSSH/ssh.exe -i D:/pem/id_ed25519_github -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" \
  git push --force-with-lease=refs/heads/main:<sha-đang-ở-origin> origin main
```

Xong **phải reset luôn thư mục prod trên VPS** (mục B.2) — nếu không, cây làm việc ở đó vẫn
đang giữ code bẩn và lần build sau sẽ chạy migration vào database thật.

### A.5. Đẩy code lên GitHub (máy này chặn HTTPS)

```bash
MSYS_NO_PATHCONV=1 GIT_SSH_COMMAND="C:/Windows/System32/OpenSSH/ssh.exe -i D:/pem/id_ed25519_github -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" git push origin main
```

---

## B. DEPLOY PROD (nhánh `main`)

Vào VPS: `python D:\vps_deploy\vps_ssh.py '<lệnh bash>'`
(hoặc `ssh -i D:\pem\id_ed25519_vps -p 51251 degosysadmin@180.93.2.176`).

### B.1. Kiểm trước khi deploy — 3 câu hỏi

```bash
cd ~/procurement-tool
git rev-parse --abbrev-ref HEAD     # phải là: main
git status --short                  # phải RỖNG
git log --oneline -3
```

Và ở máy local, xem migration sắp mang lên là những cái nào:

```bash
git log --oneline --stat <sha-prod-đang-chạy>..main -- backend/migrations/
```

Thấy migration lạ (văn thư, đa pháp nhân, approval, vehicle, seal) → **dừng, kiểm lại A.4**.

### B.2. Kéo code

**Luôn `fetch` + `reset --hard`, TUYỆT ĐỐI không `git pull`** (hai worktree chung ref, `pull`
sẽ báo "Already up to date" trong khi file không đổi):

```bash
cd ~/procurement-tool && git fetch origin && git reset --hard origin/main && git status --short && git log --oneline -1
```

`git status --short` phải rỗng trước khi sang bước build.

### B.3. Build — đổi gì thì build cái đó

Prod **bake code vào image** (`start.prod.sh`, không bind-mount), nên **không rebuild = không đổi gì**.

| Đã sửa | Phải build lại |
|---|---|
| `backend/` | `api` **và** `celery-worker` **và** `celery-beat` (ba service chung một image) |
| `frontend/` | `web` |
| `help-center/` | `help` |
| `docker/nginx.prod.conf` | `web` (file được COPY vào image lúc build) |

```bash
cd ~/procurement-tool
docker compose -f docker-compose.production.yml build api celery-worker celery-beat > /tmp/build.log 2>&1; tail -20 /tmp/build.log
docker compose -f docker-compose.production.yml up -d api celery-worker celery-beat
```

Một lệnh gọn (build + up):

```bash
cd ~/procurement-tool && docker compose -f docker-compose.production.yml up -d --build api celery-worker celery-beat
```

> **BẮT BUỘC có `-f docker-compose.production.yml`.** Thiếu nó, compose lấy
> `docker-compose.yml` (bản LOCAL: có service `db` riêng, bind-mount, thiếu network `dego-db`)
> → api không nối được MySQL → Exited(1) → Cloudflare trả **502 origin_bad_gateway**.
> Lỡ dính thì chạy lại đúng lệnh có `-f`, rồi `docker network rm procurement-tool_default`.

> **KHÔNG truyền `-p`.** Project prod là `procurement-tool` (tên mặc định theo thư mục).

### B.4. Lệnh cho từng loại thay đổi

```bash
# Sửa backend
cd ~/procurement-tool && docker compose -f docker-compose.production.yml up -d --build api celery-worker celery-beat

# Sửa frontend/ (giao diện Thu mua đang chạy thật)
cd ~/procurement-tool && docker compose -f docker-compose.production.yml up -d --build web

# Sửa help-center/
cd ~/procurement-tool && docker compose -f docker-compose.production.yml up -d --build help
```

Prod **không có service `erp`** — `frontend-v2/` chưa lên prod. Gõ `build erp` ở đây sẽ báo
service không tồn tại; đó là đúng, không phải lỗi.

### B.5. Migration chạy lúc nào

`start.prod.sh` tự chạy `alembic upgrade head` rồi `python -m app.seed_prod` mỗi lần `api` khởi
động. Nghĩa là **migration chạy ngay lúc `up -d`**, không phải lệnh riêng. Đó chính là lý do
bước B.1 phải soi danh sách migration trước.

`seed_prod.py` **không ghi đè** phân quyền đã sửa trên UI. Muốn ép áp lại `STD_ROLES` thì đặt
`SEED_FORCE_SYNC=true` trong `.env`, restart `api` một lần, rồi trả về `false`.

---

## C. DEPLOY DEV (nhánh `erp-v2`)

```bash
cd ~/procurement-tool-dev
git fetch origin && git reset --hard origin/erp-v2 && git status --short && git log --oneline -1
docker compose --env-file .env.dev -f docker-compose.dev.yml up -d --build api celery-worker erp
```

| Đã sửa | Build lại |
|---|---|
| `backend/` | `api` + `celery-worker` (dev **không có** `celery-beat`) |
| `frontend-v2/` | `erp` |
| `frontend/` | `web` |
| `help-center/` | `help` |

> **KHÔNG truyền `-p procurement-dev`.** Stack dev thật nằm dưới project **`procurement-tool-dev`**
> (tên mặc định theo thư mục). Thêm `-p procurement-dev` là compose tưởng đây là stack khác, đẻ ra
> một bộ container song song rồi chết ở `Conflict. The container name "/erp-dev" is already in use`.
> Kiểm nhanh: `docker ps --format '{{.Names}}\t{{.Label "com.docker.compose.project"}}'`.
>
> *(Dòng chú thích ở đầu `docker-compose.dev.yml` còn ghi `-p procurement-dev` — đó là dòng CŨ, sai.)*

Dev dùng database **`procurement_dev`** riêng, `EMAIL_HARD_OFF` bật và `STORAGE_PREFIX` riêng để
không đụng vào dữ liệu/hộp thư/tệp của prod.

---

## D. XÁC MINH SAU DEPLOY

### D.1. Container sống và HTTP 200

```bash
docker compose -f docker-compose.production.yml ps
for d in thumua help devthumua deverp devhelp; do printf "%-10s %s\n" "$d" "$(curl -s -o /dev/null -w "%{http_code}" https://$d.degoholding.vn/)"; done
curl -s -o /dev/null -w "%{http_code}\n" https://thumua.degoholding.vn/api/health
```

### D.2. Alembic khớp

```bash
cd ~/procurement-tool && docker compose -f docker-compose.production.yml exec -T api alembic current
```

Phải in ra đúng head của nhánh và có chữ `(head)`. Kiểm head ở local **phải dùng `alembic heads`** —
đừng regex quét thư mục `versions/`, nó bỏ sót dạng `revision: str = ...`.

Hai nhánh chạy song song mà mỗi bên thêm migration sẽ để lại **2 head**, `start.prod.sh` chết lúc
deploy. Nối bằng:

```bash
docker compose exec api alembic merge -m "noi hai nhanh" <head1> <head2>
```

### D.3. Kiểm image có thật sự "ăn" code mới không

Đây là cách **duy nhất đáng tin**. Đừng nhìn ngày tạo image/container (image build lại nhưng
container vẫn cũ là chuyện thường), và **đừng grep chuỗi tiếng Việt trong bundle đã minify** —
trình nén gộp chuỗi trùng nên số lần xuất hiện không khớp mã nguồn, dễ kết luận sai.

So **hash blob git** của một tệp vừa sửa, giữa container và commit:

```bash
# Trong container (backend/ ánh xạ thành /app)
docker exec procurement-tool-api-1 python -c "
import hashlib
d = open('/app/app/modules/payable/service.py','rb').read()
print(hashlib.sha1(b'blob %d\0' % len(d) + d).hexdigest())"
```

```bash
# Ở local, cùng tệp, cùng commit
git rev-parse main:backend/app/modules/payable/service.py
```

Hai chuỗi trùng nhau = image đúng commit đó. Khác nhau = build chưa ăn, phải build lại.

Với `web` / `erp` (bundle đã build) thì tìm **hình dạng mã đã minify**, ví dụ
`[{v:!1,t:"Mẫu thường"},{v:!0,t:"Mẫu thuế"}]`, chứ không tìm chuỗi nhãn trần.

### D.4. Celery

```bash
docker logs --tail 20 procurement-tool-celery-worker-1   # tìm dòng "ready"
docker logs --tail 20 procurement-tool-celery-beat-1
```

Celery ở prod **đang chạy thật** (sao lưu R2 hai lần mỗi ngày). Deploy backend mà quên build
`celery-worker` / `celery-beat` là hai con đó tiếp tục chạy code cũ.

---

## E. CẤM ĐỤNG TRÊN VPS

VPS này chạy chung nhiều hệ thống. **Chỉ thao tác trong hai project `procurement-tool` và
`procurement-tool-dev`.**

| Không đụng | Là gì |
|---|---|
| `procurement-mysql`, `procurement-adminer` | project `procurement-db` — CSDL của cả prod lẫn dev |
| `cloudflare_tunnel` | project `ingress` — tắt là mất toàn bộ domain |
| `dego-ketoan-backend`, `dego-ketoan-web` | hệ thống kế toán |
| `dego-pm-app`, `dego-pm-postgres` | công cụ Quản lý dự án |
| `netbird-*` | VPN nội bộ |
| `n8n`, `portainer` | hạ tầng chung |

**Tuyệt đối không `docker volume prune` / `docker system prune -a`.**

Danh sách container của mình (để đối chiếu khi `docker ps`):

- prod (`procurement-tool`): `procurement-tool-api-1`, `procurement-tool-celery-worker-1`,
  `procurement-tool-celery-beat-1`, `procurement-tool-redis-1`, `procurement-web`,
  `procurement-help`, `procurement-db-forward`
- dev (`procurement-tool-dev`): `procurement-tool-dev-api-1`, `procurement-tool-dev-celery-worker-1`,
  `procurement-tool-dev-redis-1`, `procurement-web-dev`, `procurement-help-dev`, `erp-dev`

Vài luật nhỏ nhưng đã dính:

- **Không** `ALTER TABLE` / `INSERT` text tiếng Việt qua `mysql -e` → mojibake. Đi bằng Alembic
  hoặc script Python/SQLAlchemy utf8mb4.
- **Không** chạy `npm install` trong container `erp` khi Vite dev server đang chạy → hỏng
  `node_modules/.vite`.
- Không đẩy binary / JSON lớn qua `vps_ssh.py` (bị cắt ngắn) — ghi ra file log rồi `tail`.
- Lệnh docker có đường dẫn `/app` thì thêm `MSYS_NO_PATHCONV=1` (Git Bash trên Windows).

---

## F. Sổ tay 30 giây

```bash
# --- PROD: sửa backend, đẩy lên và deploy ---
cd "D:/New folder/thuthapykien/procurement-main"
git status --short && git fetch origin && git log --oneline origin/main..main
MSYS_NO_PATHCONV=1 GIT_SSH_COMMAND="C:/Windows/System32/OpenSSH/ssh.exe -i D:/pem/id_ed25519_github -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" git push origin main
# rồi trên VPS:
cd ~/procurement-tool && git fetch origin && git reset --hard origin/main && git status --short
docker compose -f docker-compose.production.yml up -d --build api celery-worker celery-beat
docker compose -f docker-compose.production.yml exec -T api alembic current
curl -s -o /dev/null -w "%{http_code}\n" https://thumua.degoholding.vn/api/health

# --- DEV: sửa frontend-v2, deploy ---
cd ~/procurement-tool-dev && git fetch origin && git reset --hard origin/erp-v2 && git status --short
docker compose --env-file .env.dev -f docker-compose.dev.yml up -d --build erp
curl -s -o /dev/null -w "%{http_code}\n" https://deverp.degoholding.vn/
```

Ba câu tự hỏi trước khi gõ Enter ở prod:

1. Tôi đang ở nhánh **`main`** chứ?
2. `git log --oneline origin/main..main` có đúng số commit tôi định đẩy không?
3. Lệnh docker của tôi có **`-f docker-compose.production.yml`** chưa?
