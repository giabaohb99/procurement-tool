#!/bin/sh
# Đường hầm SSH lên server dev cho máy sửa mã tách rời (ai-CR-055, D-04).
#
# Mở hai cổng chuyển tiếp trong KHÔNG GIAN MẠNG của container này (agent-runner dùng chung):
#   127.0.0.1:3306 -> <VPS>:127.0.0.1:${AGENT_TUNNEL_DB_PORT}     (socat db-forward -> MySQL dev)
#   127.0.0.1:6379 -> <VPS>:127.0.0.1:${AGENT_TUNNEL_REDIS_PORT}  (socat redis-dev-forward -> Redis dev)
# Khóa `/root/tunnel_key` mount chỉ đọc; chép ra bản 0600 vì ssh từ chối khóa có quyền rộng.
# Phía VPS, dòng authorized_keys của khóa này chỉ cho mở cổng (`restrict,port-forwarding,
# permitopen=...`), không mở shell — xem doc/agent-hub/05-may-sua-ma.md.
# Đứt thì nối lại sau 5 giây; ssh tự thoát khi không mở được cổng (ExitOnForwardFailure).
set -u

: "${AGENT_TUNNEL_HOST:?AGENT_TUNNEL_HOST chưa khai trong .env.runner}"
: "${AGENT_TUNNEL_USER:?AGENT_TUNNEL_USER chưa khai trong .env.runner}"
AGENT_TUNNEL_PORT="${AGENT_TUNNEL_PORT:-22}"
AGENT_TUNNEL_DB_PORT="${AGENT_TUNNEL_DB_PORT:-13306}"
AGENT_TUNNEL_REDIS_PORT="${AGENT_TUNNEL_REDIS_PORT:-16379}"

if [ ! -s /root/tunnel_key ] || grep -q "placeholder" /root/tunnel_key 2>/dev/null; then
  echo "tunnel: chưa mount khóa SSH đường hầm (AGENT_TUNNEL_SSH_KEY_FILE) — không nối được lên dev" >&2
  sleep 3600
  exit 1
fi
mkdir -p /root/.ssh
cp /root/tunnel_key /root/.ssh/tunnel_key
chmod 600 /root/.ssh/tunnel_key

while true; do
  echo "tunnel: nối ${AGENT_TUNNEL_USER}@${AGENT_TUNNEL_HOST}:${AGENT_TUNNEL_PORT} (db ${AGENT_TUNNEL_DB_PORT}, redis ${AGENT_TUNNEL_REDIS_PORT})"
  ssh -N \
    -i /root/.ssh/tunnel_key \
    -p "${AGENT_TUNNEL_PORT}" \
    -o BatchMode=yes \
    -o StrictHostKeyChecking=accept-new \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -L "127.0.0.1:3306:127.0.0.1:${AGENT_TUNNEL_DB_PORT}" \
    -L "127.0.0.1:6379:127.0.0.1:${AGENT_TUNNEL_REDIS_PORT}" \
    "${AGENT_TUNNEL_USER}@${AGENT_TUNNEL_HOST}"
  echo "tunnel: đứt (mã $?), nối lại sau 5 giây" >&2
  sleep 5
done
