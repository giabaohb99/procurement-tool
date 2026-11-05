# CHỐNG TREO PROD — HEALTHCHECK, BỘ TỰ CHỮA, CANH TỪ NGOÀI (bao-CR-735)

| | |
|---|---|
| Bản | 1.0 |
| Ngày | 05/11/2026 |
| Người phụ trách | Agent 4 (A1 Điều phối giao, người chủ gật 05/11) |
| Trạng thái | Mã trên erp-v2, đã thử trên dev; chờ A1 cài lên prod |
| CR liên quan | bao-CR-735 |

## 1. Vấn đề

Prod chạy mọi container với `restart: always`: container **chết** thì 20–30 giây là lên lại (api 17 giây tới
*Application startup complete*, celery 6 giây, nginx 1 giây — A1 đo 05/11). Nhưng container **treo** (còn sống, không
trả lời) thì Docker không biết: trước bản này chỉ `procurement-mysql` có healthcheck, và kể cả có healthcheck thì Docker
cũng **không** tự khởi động lại container `unhealthy`. Chưa có gì canh prod từ ngoài; bộ OPS+HEAL của Agent Hub chỉ chạy ở dev.

## 2. Ba lớp

| Lớp | Ở đâu | Làm gì |
|---|---|---|
| Healthcheck | `docker-compose.production.yml`, `docker-compose.dev.yml`, `docker-compose.agent-hub.yml` + `backend/healthcheck.py` | Docker tự kiểm từng container, hỏng 3 lượt liền thì đánh dấu `unhealthy` |
| Bộ tự chữa | `backend/scripts/ops/autoheal.sh` + `systemd/dego-autoheal.{service,timer}` trên MÁY CHỦ chạy container | Mỗi 30 giây tìm container `unhealthy` có nhãn `dego.autoheal=true` rồi `docker restart` |
| Canh từ ngoài | `backend/scripts/ops/prod_watch.py` + `systemd/dego-prod-watch.{service,timer}` trên VPS 2 | Mỗi phút gọi `https://thumua.degoholding.vn/api/health` qua Cloudflare; hỏng 2 lượt liền thì báo Telegram, hồi lại cũng báo |

Lớp ba bắt cả những thứ hai lớp đầu không thấy: cả máy chủ prod đứng, Cloudflare tunnel rớt, CSDL chết, hoặc bộ tự chữa
đã thôi vì quá trần.

### 2.1 Healthcheck từng container

| Container | Lệnh kiểm | interval / timeout / retries / start_period |
|---|---|---|
| api, agent-api | `python healthcheck.py api` — GET `http://127.0.0.1:8000/api/health`, phải 200 và `"success":true` | 30s / 10s / 3 / 90s |
| celery-worker | `python healthcheck.py celery` — `control.ping` đúng worker `celery@<hostname>` qua Redis | 60s / 20s / 3 / 60s |
| agent-worker | `python healthcheck.py celery agent-worker` — worker `agent-worker@<hostname>` | 60s / 20s / 3 / 60s |
| web, erp, help (nginx) | `wget -q --spider http://127.0.0.1/` — trang tĩnh | 30s / 5s / 3 / 10s |

Các điểm cố ý:

- **api đang migration / seed thì coi là khỏe.** `start.prod.sh` chạy `alembic upgrade head` + `seed_prod` rồi mới
  `exec uvicorn`; chừng nào tiến trình số 1 chưa phải uvicorn thì lượt kiểm trả khỏe. Một migration dài (vài phút) không
  bị bộ tự chữa giết giữa chừng — giết giữa migration nguy hiểm hơn để nó chạy xong.
- **nginx kiểm trang tĩnh, không qua `/api`.** api chết thì đừng kéo nginx chết theo.
- **celery ping chỉ nạp thư viện celery**, không nạp `app.core.celery_app` (đo trên dev: ~0,5 giây, ~30 MB, tiến trình
  tắt ngay). Lệnh ping do tiến trình chính của worker trả lời nên worker bận cả `-c 2` tác vụ dài (dump sao lưu, nạp lô
  50.000 dòng) vẫn trả lời — bận không bị tính là treo.
- **Nới tay**: phải hỏng 3 lượt liền mới `unhealthy` (api ~1,5–2 phút, celery ~3–4 phút), để máy chậm lúc dump sao lưu
  không bị giết oan.
- **Chưa có healthcheck**: celery-beat, agent-beat, agent-poller, redis, qdrant, db-forward, zalo-listener. Beat treo
  thì việc theo lịch không chạy nhưng web vẫn dùng được; muốn canh thì làm CR riêng (vd beat ghi tệp tim mỗi phút).

### 2.2 Bộ tự chữa — vì sao script + systemd timer, không dùng image willfarrell/autoheal

- Image autoheal phải gắn `/var/run/docker.sock` — cầm sock là cầm **quyền root máy chủ**. Thêm một image bên thứ ba
  có quyền đó vào prod là thêm một đường bị chiếm máy (image bị đổi chủ / bị cài mã ở bản sau).
- Script ~70 dòng nằm trong repo, đọc được, log thẳng vào journald (`journalctl -t dego-autoheal`).
- Lan can:
  - Chỉ đụng container có nhãn `dego.autoheal=true`. ERPNext học, bot cũ... trên cùng máy không bị đụng.
  - Trần **3 lần / container / giờ**. Quá trần thì THÔI, báo một lần "cần người xem": lỗi thật (sai cấu hình, CSDL chết)
    mà khởi động lại liên tục chỉ che dấu vết.
  - `docker restart -t 20`: treo thật thì SIGTERM không ai nghe, chờ lâu chỉ thêm giờ đứng.
  - `flock`: hai lượt không chạy chồng.
  - Báo Telegram mỗi lần tự chữa nếu máy có `/etc/dego/alert.env`; không có thì chỉ ghi log.

### 2.3 Canh từ ngoài

- Chạy trên **VPS 2** (máy khác prod) — prod đứng cả máy vẫn có người báo.
- Gọi đúng tên miền người dùng gọi (đi qua Cloudflare). Chú ý: tên miền đúng là `thumua.degoholding.vn`
  (`thumua.degoholding.com` trả 301).
- Hỏng **2 lượt liền** → một tin `[CẢNH BÁO]`. Còn hỏng → nhắc `[VẪN HỎNG]` mỗi 60 phút (`REMIND_MINUTES`, 0 = tắt).
  Trả lời lại → `[ĐÃ HỒI]` kèm số phút đứng. Không gửi lặp mỗi phút.
- Gửi tin hỏng (Telegram chập) thì lượt sau gửi lại, không nuốt tin.
- Chạy bằng `DynamicUser=yes` (người dùng tạm của systemd, không quyền gì), trạng thái ở `/var/lib/dego-prod-watch/`.
- Kênh báo: Telegram, bot + chat lấy từ `AGENT_TELEGRAM_BOT_TOKEN` / `AGENT_TELEGRAM_CHAT_ID` sẵn có. Không có SMTP trên
  VPS 2 nên không dùng email.

## 3. Số đo trên dev (VPS 2, 05/11/2026)

Healthcheck gắn vào container dev đang chạy (tệp override tạm, không dựng lại image); bộ tự chữa chạy vòng 30 giây và bộ
canh chạy vòng 1 phút trong phiên thử, chưa cài systemd (mục 5).

| Lượt thử | Cách giả treo | Kết quả |
|---|---|---|
| 1. api: dừng 2 worker uvicorn | SIGSTOP trong container | uvicorn 0.30.6 tự thay worker treo sau vài giây; container không hề `unhealthy`. Treo **worker** api đã có lớp tự chữa sẵn |
| 2. help-dev (nginx): treo cả container | SIGSTOP mọi tiến trình từ máy chủ, cả tiến trình 1 | `unhealthy` sau **91 giây**; bộ tự chữa `docker restart` ở giây 118 (mất 21 giây: SIGTERM không ai nghe, chờ hết 20 giây rồi SIGKILL); trả trang lại và `healthy` ở giây **139–145**. Log: *Health check exceeded timeout (5s)* |
| 3. api: `docker pause` | pause | Docker báo `unhealthy` ngay (container pause không chạy được lượt kiểm); tự chữa ở giây 28, devthumua trả 200 lại ở giây **43** |
| 4. api: treo cả container, có bộ canh devthumua | SIGSTOP mọi tiến trình từ máy chủ | Bộ canh: lượt hỏng 1 ở phút thứ 1, **tin CẢNH BÁO ở khoảng phút 2** (hai lượt hỏng liền, mỗi lượt chờ 10 giây), không gửi thêm trong 5 phút hỏng tiếp theo, **tin ĐÃ HỒI ở lượt kiểm đầu tiên sau khi hồi** (≤ 1 phút). Phần tự chữa của lượt này không đo được vì đúng lúc đó dev được dựng lại cho việc khác, container mới chưa có healthcheck |

Ước tính cho api treo cả container trên prod: `unhealthy` sau ~1,5–2 phút (3 lượt × 30 giây, mỗi lượt chờ tối đa 10 giây)
+ tối đa 30 giây chờ vòng tự chữa + 20 giây dừng + ~17–20 giây khởi động (migration + seed + uvicorn) = **khoảng 2,5–3
phút** từ lúc treo tới lúc trả lời lại. celery-worker chậm hơn (lượt kiểm 60 giây): ~4–5 phút. Vì bộ canh ngoài báo sau
~2 phút, một lần api treo thường sẽ ra một cặp tin CẢNH BÁO rồi ĐÃ HỒI cách nhau vài phút — đúng ý: người chủ biết prod
vừa đứng bao lâu dù đã tự chữa.

Healthcheck celery (`control.ping`) thử trực tiếp trên worker dev và agent-worker: trả lời ~0,5 giây; tên worker sai thì
báo hỏng sau 8 giây. Chưa giả treo celery-worker dev (worker dùng chung với các Agent khác).

## 4. Cài lên prod (A1 làm tay, sau khi người chủ gật)

**Thứ tự bắt buộc: dựng image MỚI trước, bật bộ tự chữa sau.** Image cũ không có `healthcheck.py`; khai healthcheck mà
chạy image cũ thì container `unhealthy` mãi và bộ tự chữa khởi động lại tới trần.

1. Đẩy mã như mọi đợt (`docker compose -f docker-compose.production.yml up -d --build ...`). Healthcheck nằm trong compose
   nên container dựng lại là có.
2. Chờ 2 phút, kiểm mọi container có nhãn đều `(healthy)`:

   ```bash
   docker ps --filter label=dego.autoheal=true --format '{{.Names}}\t{{.Status}}'
   ```

3. Cài bộ tự chữa:

   ```bash
   cd ~/procurement-tool
   sudo install -m 755 backend/scripts/ops/autoheal.sh /usr/local/bin/dego-autoheal
   sudo install -m 644 backend/scripts/ops/systemd/dego-autoheal.service backend/scripts/ops/systemd/dego-autoheal.timer /etc/systemd/system/
   sudo install -d -m 700 /etc/dego
   echo 'AUTOHEAL_HOST_LABEL="PROD 180.93.2.176"' | sudo tee /etc/dego/autoheal.env >/dev/null
   sudo systemctl daemon-reload && sudo systemctl enable --now dego-autoheal.timer
   systemctl list-timers dego-autoheal.timer
   ```

4. (Tùy chọn) muốn bộ tự chữa prod báo Telegram mỗi lần khởi động lại: tạo `/etc/dego/alert.env` (mục 5), `chmod 600`.
   Không tạo thì vẫn chữa, chỉ ghi journald.
5. Cụm Agent Hub trên prod: dựng lại image `dego-agent-hub` (để có `healthcheck.py`) rồi `up -d` — agent-api,
   agent-worker có nhãn và healthcheck.
6. Xem log: `journalctl -t dego-autoheal --since today`. Tắt: `sudo systemctl disable --now dego-autoheal.timer`.

Không thêm biến nào vào `.env` của app.

## 5. Cài bộ canh trên VPS 2

```bash
cd ~/procurement-tool-dev
sudo install -d -m 755 /usr/local/lib/dego
sudo install -m 755 backend/scripts/ops/prod_watch.py /usr/local/lib/dego/prod_watch.py
sudo install -m 644 backend/scripts/ops/systemd/dego-prod-watch.service backend/scripts/ops/systemd/dego-prod-watch.timer /etc/systemd/system/
sudo install -d -m 700 /etc/dego
sudoedit /etc/dego/alert.env        # hai dòng: TELEGRAM_BOT_TOKEN=... và TELEGRAM_CHAT_ID=... (chép từ .env.dev, KHÔNG in ra)
sudo chmod 600 /etc/dego/alert.env
sudo systemctl daemon-reload
sudo systemd-run --wait --pipe -p DynamicUser=yes -p EnvironmentFile=/etc/dego/alert.env /usr/bin/python3 /usr/local/lib/dego/prod_watch.py --test
sudo systemctl enable --now dego-prod-watch.timer
```

Biến tùy chọn thêm vào cùng tệp: `WATCH_URL`, `WATCH_NAME`, `FAIL_THRESHOLD` (2), `REMIND_MINUTES` (60),
`WATCH_TIMEOUT` (10). Xem log: `journalctl -u dego-prod-watch --since today`.

Bộ tự chữa cho chính dev (tùy chọn, như mục 4 bước 3 với nhãn `"VPS 2 (dev)"`): dev đã có healthcheck trong
`docker-compose.dev.yml` từ bản này.

## 6. Giới hạn còn lại

- VPS 2 đứng thì không ai canh prod (và không ai báo việc đó). Muốn chắc thì thêm một dịch vụ canh bên ngoài (UptimeRobot
  gói miễn phí, 5 phút một lượt) trỏ cùng địa chỉ — việc riêng, cần người chủ gật vì đưa tên miền ra dịch vụ ngoài.
- Bộ tự chữa không cứu được lỗi gốc ngoài container (CSDL chết, hết đĩa, hết RAM cả máy) — khởi động lại tới trần rồi
  báo "cần người xem"; bộ canh ngoài vẫn báo prod đứng.
- celery-beat / agent-poller chưa có healthcheck (mục 2.1).
