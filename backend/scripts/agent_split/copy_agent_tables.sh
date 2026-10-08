#!/usr/bin/env bash
# ai-CR-119 — chép các bảng của dịch vụ AI từ DB ERP sang DB `agent_hub` (một lần, lúc tách S-1).
#
#   bash copy_agent_tables.sh <db_erp> <db_agent>        # chạy TRÊN VPS, cần MYSQL_ROOT_PASSWORD trong môi trường
#   ví dụ: MYSQL_ROOT_PASSWORD=... bash copy_agent_tables.sh procurement_dev agent_hub
#
# Dừng agent-poller / worker của stack cũ TRƯỚC khi chép (kẻo tin tới giữa chừng mất). Chép xong:
#   alembic -c alembic_agent.ini stamp head   (trong container agent-api)
# Bảng cũ ở DB ERP GIỮ NGUYÊN (không xóa) — dọn tay sau khi dịch vụ AI chạy ổn vài ngày.
set -euo pipefail
SRC="${1:?db ERP}"; DST="${2:?db agent}"
CONT="${MYSQL_CONTAINER:-procurement-mysql}"
: "${MYSQL_ROOT_PASSWORD:?cần MYSQL_ROOT_PASSWORD}"

tables=$(docker exec -e MYSQL_PWD="$MYSQL_ROOT_PASSWORD" "$CONT" mysql -N -e \
  "SELECT table_name FROM information_schema.tables WHERE table_schema='$SRC' AND (table_name LIKE 'tab_agent\\_%' OR table_name IN ('tab_ai_key','tab_assistant_conversation','tab_assistant_message'))")
echo "Chép $(wc -w <<<"$tables") bảng: $tables"
# shellcheck disable=SC2086
docker exec -e MYSQL_PWD="$MYSQL_ROOT_PASSWORD" "$CONT" mysqldump --single-transaction --default-character-set=utf8mb4 \
  --add-drop-table "$SRC" $tables \
  | docker exec -i -e MYSQL_PWD="$MYSQL_ROOT_PASSWORD" "$CONT" mysql --default-character-set=utf8mb4 "$DST"
echo "Xong. Kiểm: docker exec $CONT mysql -e 'SELECT count(*) FROM $DST.tab_agent_message'"
