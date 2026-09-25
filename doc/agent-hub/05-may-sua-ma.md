# AGENT HUB — MÁY SỬA MÃ TÁCH RỜI: cài, đăng ký, vận hành

**Bản 1.0 · 25/09/2026 · ai-CR-054 + ai-CR-055 (D-03 … D-05 của [`04`](./04-danh-sach-tinh-nang.md)).**
Đi cùng thiết kế [`01` §13](./01-thiet-ke-ky-thuat.md).

Từ phase 2, Đậu Đậu chạy **trên server dev** cho mọi người. Phần chạy Claude Code tách ra thành
**máy sửa mã** (runner): máy đại ca là máy số 1, đại ca thêm máy khác bằng một câu nhắn. Bot chỉ
xếp việc vào hàng đợi của từng máy; máy tự nối lên dev, kéo việc về làm, ghi kết quả ngược lên.
Máy tắt thì việc nằm chờ trong hàng đợi, không mất.

```
[Telegram] → bot trên dev → Redis dev: hàng đợi agent_code.<tên máy>
                                   ↑ đường hầm SSH (khóa riêng của máy, chỉ mở cổng)
                             runner trên máy: Claude Code (gói của chủ máy) · git · PAT GitHub của chủ máy
                                   ↓ ghi kết quả vào các bảng tab_agent_* bằng tài khoản MySQL riêng
```

## 0. Đưa bot lên dev lần đầu (D-06, ai-CR-056) — các lệnh, theo thứ tự

Mã đã sẵn trên nhánh `agent-hub-bac-1` (đã gộp `origin/erp-v2` ngày 25/09/2026, migration gộp head
`e6b1d4f8a2c7`). Còn lại là bốn bước chạm vào nhánh dev dùng chung và VPS:

```bash
# 1. Đẩy nhánh bot thành erp-v2 (fast-forward, erp-v2 không có commit nào ngoài nhánh bot)
git fetch origin && git push origin agent-hub-bac-1:erp-v2

# 2. Trên VPS: lấy mã + khai bot trong .env.dev (token bot DÁN TAY, không gửi qua chat)
ssh <vps> 'cd ~/procurement-tool-dev && git fetch origin && git reset --hard origin/erp-v2'
ssh <vps> 'cat >> ~/procurement-tool-dev/.env.dev <<EOF
# ---- Đậu Đậu trên dev (ai-CR-056) ----
COMPOSE_PROFILES=bot
AGENT_HUB_ENABLED=true
AGENT_TELEGRAM_BOT_TOKEN=<token bot MỚI tạo ở BotFather cho dev>
AGENT_TELEGRAM_BOT_USERNAME=<tên bot không có @>
AGENT_TELEGRAM_CHAT_ID=<id chat đại ca, cùng số với máy đại ca>
AGENT_LINK_ENABLED=true
AGENT_ERP_URL=https://deverp.degoholding.vn
AGENT_CODER_ENABLED=true
AGENT_DEPLOY_ENABLED=false
AGENT_DEFAULT_RUNNER=may-dai-ca
AGENT_GEMINI_API_KEY=
AGENT_ASSISTANT_USER=
EOF'

# 3. Dựng lại (backend + giao diện v2 đổi; migration chạy trong start.prod.sh của api)
ssh <vps> 'cd ~/procurement-tool-dev && docker compose --env-file .env.dev -f docker-compose.dev.yml \
  up -d --build api celery-worker celery-beat erp agent-poller redis-dev-forward'
ssh <vps> 'cd ~/procurement-tool-dev && docker compose --env-file .env.dev -f docker-compose.dev.yml \
  exec -T api alembic current'      # phải là e6b1d4f8a2c7

# 4. Mục 1.2 (tài khoản MySQL agent_runner) + 1.3 (authorized_keys cho may-dai-ca) bên dưới
```

**Tình trạng 25/09/2026:** bước 2 và 3 ĐÃ CHẠY (bot Lạc Lạc `@laclacdethuong_bot` sống trên dev, migration
`e6b1d4f8a2c7`, `redis-dev-forward` 127.0.0.1:16379, dòng `authorized_keys` cho `may-dai-ca` đã thêm). Dev đang
chạy mã của `origin/agent-hub-bac-1`; bước 1 (đẩy `erp-v2`) và bước 4 (tài khoản MySQL) do đại ca chạy tay —
bộ lọc quyền của phiên trợ lý không cho đụng bí mật và nhánh dùng chung:

```bash
# (1) đẩy erp-v2 để lần deploy dev sau của người khác không mất bot
git -C "D:/New folder/thuthapykien/procurement-agent-hub" push origin agent-hub-bac-1:erp-v2
# (4a) trên VPS — tài khoản MySQL agent_runner, database dev là procurement_dev; tự đặt <mật khẩu>
ssh <vps>  # rồi:
docker exec -i -e MYSQL_PWD="$(grep ^DB_ROOT_PASSWORD= ~/procurement-tool/.env | cut -d= -f2)" procurement-mysql mysql -uroot <<'SQL'
CREATE USER IF NOT EXISTS 'agent_runner'@'%' IDENTIFIED BY '<mật khẩu>';
GRANT SELECT, INSERT, UPDATE ON `procurement_dev`.`tab_agent_task` TO 'agent_runner'@'%';
GRANT SELECT, INSERT, UPDATE ON `procurement_dev`.`tab_agent_task_item` TO 'agent_runner'@'%';
GRANT SELECT, INSERT, UPDATE ON `procurement_dev`.`tab_agent_run` TO 'agent_runner'@'%';
GRANT SELECT, INSERT, UPDATE ON `procurement_dev`.`tab_agent_message` TO 'agent_runner'@'%';
GRANT SELECT, UPDATE ON `procurement_dev`.`tab_agent_runner` TO 'agent_runner'@'%';
GRANT SELECT ON `procurement_dev`.`tab_agent_grant` TO 'agent_runner'@'%';
GRANT SELECT ON `procurement_dev`.`tab_agent_chat_link` TO 'agent_runner'@'%';
GRANT SELECT ON `procurement_dev`.`tab_agent_user_key` TO 'agent_runner'@'%';
GRANT SELECT ON `procurement_dev`.`tab_setting` TO 'agent_runner'@'%';
GRANT SELECT ON `procurement_dev`.`alembic_version` TO 'agent_runner'@'%';
FLUSH PRIVILEGES;
SQL
# (4b) nhắn Lạc Lạc: «thêm máy may-dai-ca» → «đúng» → chép AGENT_RUNNER_TOKEN; rồi «cho máy may-dai-ca được deploy»
# (4c) máy đại ca: điền 3 dòng còn trống trong procurement-agent-hub/.env.runner
#      (AGENT_RUNNER_TOKEN, DB_PASSWORD = <mật khẩu> ở trên, JWT_SECRET = giá trị trong .env.dev trên VPS),
#      kiểm REDIS_URL cùng số ngăn với REDIS_URL trong .env.dev, rồi:
docker compose -p agentrunner -f docker-compose.runner.yml up -d --build
```

Sau đó: đại ca mở deverp → Trang cá nhân → «Telegram» lấy mã, nhắn `/dangnhap <mã>` cho bot dev; vào
«Khóa AI» dán khóa Gemini; nhắn «thêm máy của anh» → lấy `AGENT_RUNNER_TOKEN` dán vào `.env.runner`
trên máy (đã điền sẵn phần còn lại), điền `DB_NAME` + `DB_PASSWORD` của `agent_runner`, rồi
`docker compose -p agentrunner -f docker-compose.runner.yml up -d --build`. Stack `agenthub` cũ trên
máy đại ca tắt đi (`docker compose down`) để không có hai bot.

## 1. Chuẩn bị MỘT LẦN trên VPS dev (đại ca hoặc người có SSH quản trị)

Ba thứ, làm sau khi stack bot đã lên dev (D-06) vì tài khoản MySQL cấp quyền theo TÊN BẢNG.

### 1.1 Cổng chuyển tiếp Redis dev (MySQL đã có sẵn `procurement-db-forward` 127.0.0.1:13306)

Thêm vào compose của stack bot trên dev một service socat, chỉ nghe trên `127.0.0.1` của VPS:

```yaml
  redis-dev-forward:
    image: alpine/socat
    container_name: procurement-redis-dev-forward
    restart: always
    command: TCP-LISTEN:6379,fork,reuseaddr TCP:redis:6379
    ports:
      - "127.0.0.1:16379:6379"
```

Không mở ra Internet: hai cổng 13306 và 16379 chỉ tới được qua đường hầm SSH.

### 1.2 Tài khoản MySQL riêng cho máy sửa mã

Chạy bằng tài khoản quản trị MySQL (đi qua `docker exec … mysql`, KHÔNG có tiếng Việt nên không
lo lỗi mã hóa). Thay `<db>` bằng tên database dev và `<mật khẩu>` bằng mật khẩu sinh ngẫu nhiên:

```sql
CREATE USER IF NOT EXISTS 'agent_runner'@'%' IDENTIFIED BY '<mật khẩu>';
GRANT SELECT, INSERT, UPDATE ON `<db>`.`tab_agent_task`      TO 'agent_runner'@'%';
GRANT SELECT, INSERT, UPDATE ON `<db>`.`tab_agent_task_item` TO 'agent_runner'@'%';
GRANT SELECT, INSERT, UPDATE ON `<db>`.`tab_agent_run`       TO 'agent_runner'@'%';
GRANT SELECT, INSERT, UPDATE ON `<db>`.`tab_agent_message`   TO 'agent_runner'@'%';
GRANT SELECT, UPDATE         ON `<db>`.`tab_agent_runner`    TO 'agent_runner'@'%';
GRANT SELECT                 ON `<db>`.`tab_agent_grant`     TO 'agent_runner'@'%';
GRANT SELECT                 ON `<db>`.`tab_setting`         TO 'agent_runner'@'%';
GRANT SELECT                 ON `<db>`.`alembic_version`     TO 'agent_runner'@'%';
FLUSH PRIVILEGES;
```

Tài khoản này KHÔNG đọc được `tab_user`, `tab_employee` hay bất kỳ bảng nghiệp vụ nào: máy sửa mã
bị chiếm thì kẻ chiếm cũng chỉ thấy sổ của bot. Cần thêm bảng nào thì thêm dòng GRANT, không mở
cả database.

### 1.3 Dòng `authorized_keys` cho từng máy — chỉ mở cổng, không mở shell

Mỗi máy một cặp khóa riêng (mục 2.2). Dán khóa công khai vào `~/.ssh/authorized_keys` của tài
khoản SSH trên VPS, **đứng trước là phần giới hạn**:

```
restrict,port-forwarding,permitopen="127.0.0.1:13306",permitopen="127.0.0.1:16379" ssh-ed25519 AAAA… agent-tunnel-may-duoc
```

`restrict` tắt hết (pty, X11, agent, lệnh); `port-forwarding` + hai `permitopen` mở lại đúng hai cổng.
Gỡ máy = xóa dòng này (và «tắt máy …» với bot, mục 4).

## 2. Cài trên máy sửa mã (chủ máy tự làm)

Cần: Docker Desktop, Git, một tài khoản GitHub có quyền đẩy vào kho, gói Claude Code của chính mình.

### 2.1 Lấy mã máy từ bot

Đại ca nhắn cho bot **«thêm máy của anh Được»** → bot hỏi lại → **«đúng»** → bot trả hai dòng
`AGENT_RUNNER_NAME=…` và `AGENT_RUNNER_TOKEN=…` **đúng một lần**; chép xong xóa tin đó trong Telegram.

### 2.2 Khóa SSH đường hầm của máy

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/agent_tunnel_may-duoc -C agent-tunnel-may-duoc
```

Gửi đại ca nội dung tệp `.pub` (KHÔNG gửi tệp không đuôi) để thêm vào VPS theo mục 1.3.

### 2.3 Khóa GitHub và Claude Code của chủ máy

- GitHub → Settings → Developer settings → Fine-grained token: đúng kho `procurement-tool`, quyền
  *Contents: Read and write* (+ *Pull requests: Read and write* nếu muốn bot mở PR). Đây là PAT của
  **chủ máy**, không mượn của đại ca.
- Claude Code: trên máy chạy `claude setup-token`, chép chuỗi bắt đầu bằng `sk-ant-oat…`.

### 2.4 Tệp `.env.runner` và bật

```bash
git clone git@github.com:giabaohb99/procurement-tool.git
cd procurement-tool && git checkout erp-v2
cp .env.runner.example .env.runner        # điền theo chú thích trong tệp
docker compose -p agentrunner -f docker-compose.runner.yml up -d --build
docker compose -p agentrunner -f docker-compose.runner.yml logs -f
```

Nhật ký `tunnel` phải thấy dòng `nối …` rồi im (không lặp «đứt»); nhật ký `agent-runner` phải thấy
`celery@may-duoc ready`. Sau 30 giây đại ca hỏi bot **«máy nào đang bật»** phải thấy máy này *đang bật*.

Các giá trị KHÔNG được có trên máy này: token Telegram của bot, khóa Gemini, PAT GitHub của đại ca,
khóa SSH VPS của đại ca. Tệp `.env.runner` nằm trong `.gitignore`.

## 3. Bot chia việc thế nào (D-05)

| Tình huống | Bot làm |
|---|---|
| Việc mới, có máy đang bật | Giao máy đang bật ít việc nhất; ghi máy vào việc (dính từ đây) |
| Việc mới, không máy nào bật | Giao `AGENT_DEFAULT_RUNNER` (thường là máy đại ca), không khai thì máy liên lạc gần nhất; nhắn «đang chờ máy X bật»; vé nằm trong Redis tới khi máy nối vào |
| Làm tiếp · hỏi thêm · sửa cho xanh · gộp · deploy của việc đã có máy | Luôn về đúng máy đó (worktree + phiên Claude Code chỉ có ở đó) |
| Máy tắt giữa lượt `claude` | Vòng nhặt việc kẹt (ai-CR-016) báo sau 15 phút; máy bật lại thì «làm tiếp» nối phiên |
| Đại ca «AI-0012 cho máy anh Được làm» | Đổi máy nếu việc không đang chạy dở; máy mới làm lại từ kế hoạch (bản vá dở không mang theo) |
| Máy bị «tắt máy …» | Nhịp tim và mọi vé kế bị từ chối; việc đang dính máy đó chờ tới khi đại ca giao máy khác |
| Deploy dev | Chỉ máy có cờ deploy («cho máy X được deploy»); máy mới mặc định KHÔNG |
| Chưa đăng ký máy nào | Y như phase 0/1: hàng đợi `agent_code`, bot và runner cùng máy |

## 4. Câu nhắn của đại ca

- «thêm máy của anh Được» · «đăng ký máy cho Bảo» — hỏi lại, «đúng» → phát mã máy
- «tắt máy của anh Được» · «gỡ máy may-duoc» — hỏi lại, «đúng» → gỡ
- «máy nào đang bật» · «danh sách máy sửa mã»
- «AI-0012 cho máy anh Được làm»
- «cho máy may-duoc được deploy dev» · «cấm máy may-duoc deploy»
- «AI-0012 xong chưa» — dòng tình trạng ghi thêm «Máy X (đang bật/tắt)»

## 5. Vì sao thiết kế như vậy

- **Máy tự nối LÊN, dev không gọi xuống**: máy ở nhà/công ty nằm sau NAT, không có địa chỉ công khai.
- **Hàng đợi theo máy thay vì một hàng đợi chung**: worktree và phiên Claude Code là trạng thái cục
  bộ; một vé rơi nhầm máy là mất mạch «làm tiếp». Vé nằm trong Redis nên máy tắt không mất việc.
- **Tin Telegram gửi hộ**: máy không giữ token bot (ai-CR-054); mất máy không mất bot.
- **Tài khoản MySQL theo bảng + `authorized_keys` chỉ mở cổng**: mỗi máy chỉ với tới đúng thứ nó cần.
- **Việc dính máy**: đơn giản hơn di chuyển worktree giữa máy; đổi máy thì làm lại từ kế hoạch, bot nói rõ.
- Để sau (D-07): thay đường hầm bằng gọi API ERP có khóa riêng, máy không chạm DB.
