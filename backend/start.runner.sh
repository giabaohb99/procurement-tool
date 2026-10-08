#!/bin/sh
# Khởi động MÁY SỬA MÃ (ai-CR-124). Máy đã tự cập nhật (agent_hub/runner_update.py) thì chạy mã trong
# /worktrees/.runner-code/<sha>/backend — bản khớp vân tay bot trên dev; chưa có, hoặc bản đó hỏng, thì chạy mã đóng
# trong ảnh (/app) như trước. Tắt hẳn bằng AGENT_RUNNER_SELF_UPDATE=false.
set -u

ROOT="${AGENT_WORKTREE_ROOT:-/worktrees}/.runner-code"
CODE=/app

if [ "${AGENT_RUNNER_SELF_UPDATE:-true}" = "true" ] && [ -f "$ROOT/current" ]; then
    SHA=$(cat "$ROOT/current")
    if [ -n "$SHA" ] && [ -d "$ROOT/$SHA/backend/app" ]; then
        CODE="$ROOT/$SHA/backend"
    fi
fi

if [ "$CODE" != /app ]; then
    # Thư viện đổi theo bản mới: cài thêm (lỗi thì quay về mã trong ảnh, không để máy chết).
    if ! cmp -s "$CODE/requirements.txt" /app/requirements.txt; then
        echo "runner: requirements khác bản trong ảnh, cài thêm..."
        pip install --no-cache-dir -q -r "$CODE/requirements.txt" || CODE=/app
    fi
fi

if [ "$CODE" != /app ]; then
    # Bản mới không nạp nổi (lỗi cú pháp, thiếu thư viện) → bỏ dấu `current`, chạy mã trong ảnh.
    if ! (cd "$CODE" && python -c "import app.core.celery_app, app.modules.agent_hub.tasks" >/dev/null 2>&1); then
        echo "runner: bản $CODE không nạp được, quay về mã trong ảnh"
        rm -f "$ROOT/current"
        CODE=/app
    fi
fi

echo "runner: chạy mã ở $CODE"
cd "$CODE" || exit 1
exec celery -A app.core.celery_app worker -l info -c 1 \
    -Q "agent_code.${AGENT_RUNNER_NAME}" -n "${AGENT_RUNNER_NAME}@%h"
