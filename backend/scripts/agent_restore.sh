#!/usr/bin/env bash
# Quay lại DB của DỊCH VỤ AI (agent_hub) từ một bản sao lưu — ai-CR-139. Chạy TRÊN VPS, ngoài container.
#
#   agent_restore.sh <tệp .sql.gz> --full
#       Quay lại TOÀN BỘ về bản đó: dừng stack bot → dump bản hiện tại (để quay ngược) → nạp bản vào DB tạm, kiểm →
#       thay vào agent_hub → khởi động (agent-api tự chạy alembic lên head) → kiểm health.
#       MẤT mọi thay đổi sau giờ của bản sao lưu.
#
#   agent_restore.sh <tệp .sql.gz> --table <bảng> --where "<điều kiện>"
#       Lấy lại MỘT PHẦN (vd trí nhớ / lịch sử một người bị xóa nhầm): nạp bản vào DB tạm, chép đúng các dòng khớp sang
#       agent_hub bằng REPLACE (dòng còn thì ghi đè đúng dòng đó, dòng khác không đụng). KHÔNG dừng stack.
#
# Bước xác nhận: phải gõ đúng cụm in ra màn hình, hoặc truyền --yes (chỉ dùng khi đã được duyệt, vd qua thẻ duyệt
# thao tác VPS). Chưa xác nhận thì thoát mã 3 TRƯỚC khi đụng docker hay DB.
#
# Biến môi trường (mặc định theo dev 09/10/2026):
#   MYSQL_CONTAINER  procurement-mysql          container MySQL (dùng mật khẩu root trong env của chính nó)
#   AGENT_DB         agent_hub
#   STACK_DIR        $HOME/agent-hub            thư mục compose của stack bot
#   COMPOSE_ARGS     ""                         thêm cờ cho `docker compose` (vd -f docker-compose.agent.yml)
#   SERVICES         "agent-api agent-worker agent-beat agent-poller zalo-listener"
#   HEALTH_URL       ""                         để trống thì bỏ bước kiểm health
#   SAFETY_DIR       $STACK_DIR/restore-safety  nơi cất bản dump «trước khi quay lại»
set -euo pipefail

usage() {
  sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
}

FILE="${1:-}"
[ -n "$FILE" ] || usage
shift || true
MODE=""
TABLE=""
WHERE=""
YES=0
while [ $# -gt 0 ]; do
  case "$1" in
    --full) MODE="full" ;;
    --table) MODE="part"; TABLE="${2:-}"; shift ;;
    --where) WHERE="${2:-}"; shift ;;
    --yes) YES=1 ;;
    *) echo "Tham số lạ: $1" >&2; usage ;;
  esac
  shift
done

[ -f "$FILE" ] || { echo "Không thấy tệp: $FILE" >&2; exit 2; }
case "$FILE" in *.sql.gz) ;; *) echo "Tệp phải là .sql.gz (bản sao lưu của màn Sao lưu)" >&2; exit 2 ;; esac
[ -n "$MODE" ] || { echo "Chọn --full hoặc --table <bảng> --where \"<điều kiện>\"" >&2; exit 2; }
if [ "$MODE" = "part" ]; then
  [[ "$TABLE" =~ ^tab_[a-z0-9_]+$ ]] || { echo "Tên bảng không hợp lệ: '$TABLE'" >&2; exit 2; }
  [ -n "$WHERE" ] || { echo "Lấy lại một phần phải có --where (không chép cả bảng bằng đường này)" >&2; exit 2; }
fi

MYSQL_CONTAINER="${MYSQL_CONTAINER:-procurement-mysql}"
AGENT_DB="${AGENT_DB:-agent_hub}"
STACK_DIR="${STACK_DIR:-$HOME/agent-hub}"
COMPOSE_ARGS="${COMPOSE_ARGS:-}"
SERVICES="${SERVICES:-agent-api agent-worker agent-beat agent-poller zalo-listener}"
HEALTH_URL="${HEALTH_URL:-}"
SAFETY_DIR="${SAFETY_DIR:-$STACK_DIR/restore-safety}"
TMP_DB="${AGENT_DB}_restore_tmp"
STAMP="$(date +%Y%m%d-%H%M%S)"

echo "================ QUAY LẠI DB BOT ================"
echo "Bản sao lưu : $FILE"
echo "DB đích     : $AGENT_DB (container $MYSQL_CONTAINER), DB tạm $TMP_DB"
if [ "$MODE" = "full" ]; then
  PHRASE="QUAY LAI TOAN BO $AGENT_DB"
  echo "Kiểu        : TOÀN BỘ — dừng [$SERVICES], dump bản hiện tại vào $SAFETY_DIR, thay hết dữ liệu."
  echo "              MẤT mọi thay đổi sau giờ của bản sao lưu."
else
  PHRASE="LAY LAI $TABLE"
  echo "Kiểu        : MỘT PHẦN — bảng $TABLE, điều kiện: $WHERE (REPLACE theo khóa chính, không dừng stack)."
fi
echo "================================================="

if [ "$YES" -ne 1 ]; then
  printf 'Gõ đúng «%s» để chạy: ' "$PHRASE"
  ANSWER=""
  read -r ANSWER || true
  if [ "$ANSWER" != "$PHRASE" ]; then
    echo "Chưa xác nhận — không làm gì." >&2
    exit 3
  fi
fi

mysql_root() {
  docker exec -i "$MYSQL_CONTAINER" sh -c 'exec mysql --default-character-set=utf8mb4 -uroot -p"$MYSQL_ROOT_PASSWORD" "$@"' -- "$@"
}
mysqldump_root() {
  docker exec -i "$MYSQL_CONTAINER" sh -c 'exec mysqldump --default-character-set=utf8mb4 --single-transaction -uroot -p"$MYSQL_ROOT_PASSWORD" "$@"' -- "$@"
}
compose() {
  # shellcheck disable=SC2086
  (cd "$STACK_DIR" && docker compose $COMPOSE_ARGS "$@")
}

load_tmp() {
  echo "-> Nạp bản sao lưu vào DB tạm $TMP_DB"
  mysql_root -e "DROP DATABASE IF EXISTS \`$TMP_DB\`; CREATE DATABASE \`$TMP_DB\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
  gunzip -c "$FILE" | mysql_root "$TMP_DB"
  local ver tables
  ver="$(mysql_root -N -B -e "SELECT version_num FROM \`$TMP_DB\`.alembic_version LIMIT 1" || true)"
  tables="$(mysql_root -N -B -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$TMP_DB'")"
  echo "   alembic_version=$ver, số bảng=$tables"
  if [ -z "$ver" ] || [ "${tables:-0}" -lt 5 ]; then
    echo "Bản nạp thử không đạt (thiếu alembic_version hoặc quá ít bảng) — dừng, DB đang chạy chưa bị đụng." >&2
    mysql_root -e "DROP DATABASE IF EXISTS \`$TMP_DB\`"
    exit 4
  fi
}

cleanup_tmp() {
  mysql_root -e "DROP DATABASE IF EXISTS \`$TMP_DB\`" || echo "Không xóa được DB tạm $TMP_DB — xóa tay." >&2
}

if [ "$MODE" = "part" ]; then
  load_tmp
  trap cleanup_tmp EXIT
  n="$(mysql_root -N -B -e "SELECT COUNT(*) FROM \`$TMP_DB\`.\`$TABLE\` WHERE $WHERE")"
  echo "-> Bản sao lưu có $n dòng khớp; chép sang $AGENT_DB.$TABLE (REPLACE)"
  mysqldump_root --no-create-info --replace --skip-triggers --where="$WHERE" "$TMP_DB" "$TABLE" | mysql_root "$AGENT_DB"
  echo "Xong. Kiểm lại trên màn / bot; trí nhớ cá nhân nạp lại sau tối đa 10 phút (bộ đệm lõi)."
  exit 0
fi

mkdir -p "$SAFETY_DIR"
SAFETY="$SAFETY_DIR/${AGENT_DB}-truoc-khi-quay-lai-$STAMP.sql.gz"
echo "-> Dừng stack bot: $SERVICES"
# shellcheck disable=SC2086
compose stop $SERVICES
echo "-> Dump bản HIỆN TẠI để quay ngược: $SAFETY"
mysqldump_root "$AGENT_DB" | gzip > "$SAFETY"
load_tmp
echo "-> Thay $AGENT_DB bằng bản sao lưu"
mysql_root -e "DROP DATABASE IF EXISTS \`$AGENT_DB\`; CREATE DATABASE \`$AGENT_DB\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
gunzip -c "$FILE" | mysql_root "$AGENT_DB"
cleanup_tmp
echo "-> Khởi động lại stack bot (agent-api tự chạy alembic lên head)"
# shellcheck disable=SC2086
compose start $SERVICES
if [ -n "$HEALTH_URL" ]; then
  for i in $(seq 1 30); do
    if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then echo "Health xanh sau ${i}x5 giây."; break; fi
    sleep 5
    [ "$i" -eq 30 ] && { echo "Health CHƯA xanh sau 150 giây — xem log agent-api. Bản trước khi quay lại: $SAFETY" >&2; exit 5; }
  done
fi
echo "Xong. Bản trước khi quay lại (để quay ngược nếu cần): $SAFETY"
