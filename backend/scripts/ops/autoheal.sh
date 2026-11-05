#!/usr/bin/env bash
# bao-CR-735 — BỘ TỰ CHỮA container treo, chạy trên MÁY CHỦ (systemd timer dego-autoheal.timer, mỗi 30 giây).
#
# Docker có `restart: always` nhưng chỉ khởi động lại container ĐÃ CHẾT; container treo (còn sống mà không trả lời)
# chỉ bị đánh dấu `unhealthy` rồi để nguyên. Script này tìm container `unhealthy` CÓ NHÃN dego.autoheal=true (khai
# trong docker-compose cạnh `healthcheck:`) rồi `docker restart`. Container không nhãn (ERPNext học, bot cũ...) không đụng.
#
# Lan can:
#   - Trần AUTOHEAL_MAX_PER_HOUR lần / container / giờ (mặc định 3). Quá trần thì THÔI khởi động lại, báo một lần
#     "cần người xem" — lỗi thật (hỏng cấu hình, CSDL chết) thì khởi động lại liên tục chỉ che mất dấu vết.
#   - flock: hai lượt không chạy chồng nhau.
#   - Báo Telegram nếu có /etc/dego/alert.env (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID; chmod 600, chủ root). Không có
#     tệp thì chỉ ghi log. Khóa không bao giờ ra log hay dòng lệnh (`ps`) — curl đọc URL từ stdin.
#
# Chọn script + timer thay vì image willfarrell/autoheal: không thêm image lạ cầm docker.sock (cầm sock = quyền root
# máy chủ), mã ngắn đọc được trong repo, log ra journald cùng chỗ với mọi thứ khác.
# Xem log: journalctl -t dego-autoheal --since today
set -u

LABEL="${AUTOHEAL_LABEL:-dego.autoheal=true}"
MAX_PER_HOUR="${AUTOHEAL_MAX_PER_HOUR:-3}"
STOP_TIMEOUT="${AUTOHEAL_STOP_TIMEOUT:-20}"   # treo thật thì SIGTERM không ai nghe — chờ lâu chỉ thêm giờ đứng
STATE="${AUTOHEAL_STATE:-/var/lib/dego-autoheal/restarts.log}"
ALERT_ENV="${DEGO_ALERT_ENV:-/etc/dego/alert.env}"
HOST_LABEL="${AUTOHEAL_HOST_LABEL:-$(hostname)}"
DOCKER="${DOCKER:-docker}"

log() {
  logger -t dego-autoheal -- "$*" 2>/dev/null || true
  echo "$(date '+%F %T') $*"
}

notify() {
  (
    # Biến có thể đến từ tệp (chạy tay) hoặc từ EnvironmentFile= của systemd.
    # shellcheck disable=SC1090
    if [ -r "$ALERT_ENV" ]; then . "$ALERT_ENV"; fi
    [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ] || exit 0
    printf 'url = "https://api.telegram.org/bot%s/sendMessage"\n' "$TELEGRAM_BOT_TOKEN" \
      | curl -s -m 15 -o /dev/null -f -K - \
          --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" --data-urlencode "text=$1"
  ) || log "không gửi được tin báo Telegram"
}

exec 9>"${AUTOHEAL_LOCK:-/run/dego-autoheal.lock}"
flock -n 9 || exit 0

mkdir -p "$(dirname "$STATE")"
touch "$STATE"
now=$(date +%s)
# Chỉ giữ một giờ gần nhất. Dòng: "<epoch> <container>" (đã khởi động lại) hoặc "<epoch> <container> giveup".
awk -v t=$((now - 3600)) '$1 >= t' "$STATE" >"$STATE.tmp" && mv "$STATE.tmp" "$STATE"

"$DOCKER" ps --filter "label=$LABEL" --filter health=unhealthy --format '{{.Names}}' | while read -r name; do
  [ -n "$name" ] || continue
  done_count=$(awk -v c="$name" '$2 == c && NF == 2' "$STATE" | wc -l)
  gave_up=$(awk -v c="$name" '$2 == c && $3 == "giveup"' "$STATE" | wc -l)
  # lượt kiểm HỎNG gần nhất (container bị pause thì không có lượt hỏng nào — để trống)
  reason=$("$DOCKER" inspect --format '{{if .State.Health}}{{range .State.Health.Log}}{{if ne .ExitCode 0}}{{println .Output}}{{end}}{{end}}{{end}}' "$name" 2>/dev/null \
    | tr -s '\n' | tail -n 1 | cut -c1-200)

  if [ "$done_count" -ge "$MAX_PER_HOUR" ]; then
    if [ "$gave_up" -eq 0 ]; then
      echo "$now $name giveup" >>"$STATE"
      log "$name unhealthy nhưng đã khởi động lại $done_count lần trong 1 giờ — THÔI, cần người xem. Lỗi: $reason"
      notify "[CẦN NGƯỜI XEM] $HOST_LABEL: $name vẫn treo sau $done_count lần tự khởi động lại trong 1 giờ. Bộ tự chữa tạm dừng với container này. Lỗi gần nhất: $reason"
    fi
    continue
  fi

  started=$(date +%s)
  echo "$now $name" >>"$STATE"   # tính cả lần hỏng vào trần — không báo lặp mỗi 30 giây
  if "$DOCKER" restart -t "$STOP_TIMEOUT" "$name" >/dev/null 2>&1; then
    log "$name unhealthy → đã docker restart ($(( $(date +%s) - started )) giây, lần $((done_count + 1))/$MAX_PER_HOUR trong 1 giờ). Lỗi: $reason"
    notify "[TỰ CHỮA] $HOST_LABEL: $name bị treo, đã tự khởi động lại (lần $((done_count + 1)) trong 1 giờ). Lỗi healthcheck: $reason"
  else
    log "$name unhealthy — docker restart THẤT BẠI"
    notify "[LỖI] $HOST_LABEL: $name bị treo, tự khởi động lại THẤT BẠI. Cần người xem."
  fi
done
