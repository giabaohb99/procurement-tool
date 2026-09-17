#!/usr/bin/env bash
#
# Gõ tay MỘT sự kiện vào cửa nhận của app đặt xe cũ:
#   POST /api/sync/datxe/events
#
# Dùng để thử đường đồng bộ khi app cũ CHƯA gắn móc bắn tin. Script tự ký HMAC
# nên không phải dán khóa vào dòng lệnh — khóa đọc thẳng từ `.env` ở gốc kho mã
# (tệp đó đã gitignore, đừng chép ra chỗ khác).
#
# Cách chạy (đứng ở gốc kho mã):
#   bash backend/scripts/legacy_sync/send_test_event.sh
#   bash backend/scripts/legacy_sync/send_test_event.sh https://deverp.degoholding.vn req_thu_002
#
# Tham số 1: địa chỉ gốc của ERP   (mặc định http://localhost:8000)
# Tham số 2: khóa phiếu bên app cũ (mặc định req_thu_001)
#
# ⚠️ Chữ ký ký trên NGUYÊN VĂN thân yêu cầu. Sửa `BODY` thì đừng định dạng lại
#    cho đẹp sau khi ký — thừa một dấu cách là 401.
set -euo pipefail

BASE="${1:-http://localhost:8000}"
LEGACY_ID="${2:-req_thu_001}"
PATH_EVENTS="/api/sync/datxe/events"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SECRET="$(grep -E '^SYNC_SHARED_SECRET=' "$ROOT/.env" | head -n 1 | cut -d= -f2- | tr -d '"'"'"'\r')"
if [ -z "$SECRET" ]; then
  echo "Không đọc được SYNC_SHARED_SECRET trong $ROOT/.env" >&2
  exit 1
fi

TS="$(date +%s)"                 # giây; ERP cho lệch tối đa 300 giây
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

#  Một phiếu đặt xe tối giản. `event_id` phải KHÁC nhau mỗi lần gửi: cột đó là
#  khóa duy nhất, gửi lại đúng mã cũ thì ERP trả về kết quả lần trước chứ không
#  xử lại — đúng ý đồ chặn trùng, nhưng lúc thử tay thì dễ tưởng là hỏng.
BODY="{\"event_id\":\"thu-$TS\",\"occurred_at\":\"$NOW\",\"entity\":\"vehicle_booking\",\"action\":\"update\",\"legacy_id\":\"$LEGACY_ID\",\"erp_id\":0,\"data\":{\"type\":\"CAR_BOOKING\",\"createdAt\":${TS}000,\"updatedAt\":${TS}000,\"createdBy\":\"uid_thu\",\"approval\":{\"overallStatus\":\"pending_approval\"},\"details\":{\"purpose\":\"Gọi thử cửa nhận\",\"startLocation\":\"Văn phòng\",\"endLocation\":\"Nhà khách\"}}}"

SIG="$(printf '%s' "$TS.$PATH_EVENTS.$BODY" | openssl dgst -sha256 -hmac "$SECRET" -r | cut -d' ' -f1)"

curl -sS -X POST "$BASE$PATH_EVENTS" \
  -H 'Content-Type: application/json' \
  -H 'X-Sync-Source: datxe' \
  -H "X-Sync-Timestamp: $TS" \
  -H "X-Sync-Signature: $SIG" \
  --data-raw "$BODY"
echo
