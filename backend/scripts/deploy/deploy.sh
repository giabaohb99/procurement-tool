#!/usr/bin/env bash
# deploy.sh — đưa ĐÚNG MỘT COMMIT đã kiểm lên một môi trường (ai-CR-067, V-02 của doc/agent-hub/04).
#
#   deploy.sh <đích> <commit|latest> [service ...]
#     đích    : dev | prod | tên khác (khi đó phải khai DEPLOY_DIR, DEPLOY_COMPOSE, DEPLOY_BRANCH)
#     commit  : sha, hoặc «latest» = origin/<nhánh của đích>
#     service : bỏ trống = tự chọn theo tệp đổi giữa bản đang chạy và bản mới
#
# Chạy TRÊN máy chủ đích. Bot code gửi tệp này qua `ssh … bash -s -- <đích> <commit> …` (tệp đi qua
# stdin, không cần có sẵn trên máy chủ); người cũng chạy tay được y như vậy:
#   ssh vps 'bash -s -- dev latest' < backend/scripts/deploy/deploy.sh
#
# Biến môi trường (sổ môi trường của bot truyền vào; thiếu thì lấy mặc định của dev / prod):
#   DEPLOY_DIR, DEPLOY_COMPOSE, DEPLOY_BRANCH, DEPLOY_HEALTH,
#   DEPLOY_ROLLBACK=1 (mặc định: health hỏng thì tự quay về bản trước), DEPLOY_LOG_DIR
#
# In ra các dòng máy đọc được: PREV= · HEAD= · SERVICES= · HEALTH= · RESULT=ok|fail|rolled_back|busy · ERR=
# Mỗi lần chạy ghi một tệp nhật ký ở $DEPLOY_LOG_DIR (mặc định ~/agent-deploy-logs).
#
# Luật cứng: commit phải NẰM TRÊN origin/<nhánh của đích> (dev = erp-v2, prod = main). Không deploy
# được bản lạ chưa vào nhánh chung. Không có --force, không xóa dữ liệu.

main() {
  set -uo pipefail
  local target="${1:-}" commit="${2:-}"
  if [ -z "$target" ] || [ -z "$commit" ]; then
    echo "ERR=thiếu tham số: deploy.sh <đích> <commit|latest> [service ...]"; echo "RESULT=fail"; return 2
  fi
  shift 2
  local services=("$@")

  case "$target" in
    dev)
      : "${DEPLOY_DIR:=$HOME/procurement-tool-dev}"
      : "${DEPLOY_COMPOSE:=--env-file .env.dev -f docker-compose.dev.yml}"
      : "${DEPLOY_BRANCH:=erp-v2}"
      : "${DEPLOY_HEALTH:=https://devthumua.degoholding.vn/api/health}" ;;
    prod)
      : "${DEPLOY_DIR:=$HOME/procurement-tool}"
      : "${DEPLOY_COMPOSE:=-f docker-compose.production.yml}"
      : "${DEPLOY_BRANCH:=main}"
      : "${DEPLOY_HEALTH:=https://thumua.degoholding.vn/api/health}" ;;
    *)
      if [ -z "${DEPLOY_DIR:-}" ] || [ -z "${DEPLOY_COMPOSE:-}" ] || [ -z "${DEPLOY_BRANCH:-}" ]; then
        echo "ERR=đích lạ «$target»: phải khai DEPLOY_DIR, DEPLOY_COMPOSE, DEPLOY_BRANCH"; echo "RESULT=fail"; return 2
      fi ;;
  esac
  : "${DEPLOY_HEALTH:=}"
  DEPLOY_DIR="${DEPLOY_DIR/#\~/$HOME}"   # sổ môi trường ghi «~/…»: biến trong ngoặc kép không tự nở dấu ~
  : "${DEPLOY_ROLLBACK:=1}"
  : "${DEPLOY_LOG_DIR:=$HOME/agent-deploy-logs}"
  DEPLOY_LOG_DIR="${DEPLOY_LOG_DIR/#\~/$HOME}"
  : "${DEPLOY_HEALTH_TRIES:=12}"
  : "${DEPLOY_HEALTH_DELAY:=10}"

  mkdir -p "$DEPLOY_LOG_DIR"
  local log="$DEPLOY_LOG_DIR/$(date +%Y%m%d-%H%M%S)-$target-$$.log"
  exec > >(tee -a "$log") 2>&1
  echo "LOG=$log"

  # Một lượt deploy một lúc cho mỗi đích.
  exec 9>"/tmp/agent-deploy-$target.lock"
  if ! flock -n 9; then
    echo "ERR=đang có lượt deploy khác trên $target"; echo "RESULT=busy"; return 3
  fi

  cd "$DEPLOY_DIR" || { echo "ERR=không vào được $DEPLOY_DIR"; echo "RESULT=fail"; return 2; }
  local prev; prev="$(git rev-parse HEAD)"
  echo "PREV=$prev"
  git fetch origin --quiet || { echo "ERR=git fetch hỏng"; echo "RESULT=fail"; return 2; }
  [ "$commit" = "latest" ] && commit="origin/$DEPLOY_BRANCH"
  local sha
  sha="$(git rev-parse --verify --quiet "${commit}^{commit}")" || {
    echo "ERR=không có commit $commit"; echo "RESULT=fail"; return 2; }
  if ! git merge-base --is-ancestor "$sha" "origin/$DEPLOY_BRANCH"; then
    echo "ERR=commit ${sha:0:10} không nằm trên origin/$DEPLOY_BRANCH"; echo "RESULT=fail"; return 2
  fi

  if [ "${#services[@]}" -eq 0 ]; then
    mapfile -t services < <(pick_services "$prev" "$sha")
  fi
  # ai-CR-081: bỏ service không có trong compose của đích (vd agent-poller trên prod, hoặc dev chưa bật profile bot)
  # thay vì để `up` hỏng cả lượt.
  if [ "${#services[@]}" -gt 0 ]; then
    local known kept=() s
    # shellcheck disable=SC2086
    known="$(docker compose $DEPLOY_COMPOSE config --services 2>/dev/null)"
    if [ -n "$known" ]; then
      for s in "${services[@]}"; do
        if grep -qx "$s" <<<"$known"; then kept+=("$s"); else echo "Bỏ qua service không có ở $target: $s"; fi
      done
      services=("${kept[@]}")
    fi
  fi
  echo "SERVICES=${services[*]:-}"

  git reset --hard "$sha" >/dev/null && echo "HEAD=$sha"
  if [ "${#services[@]}" -gt 0 ]; then
    # shellcheck disable=SC2086
    docker compose $DEPLOY_COMPOSE up -d --build "${services[@]}" || {
      echo "ERR=docker compose up hỏng"; rollback "$prev" "$sha" "${services[@]}"; return 1; }
  else
    echo "Không có service nào cần dựng lại (chỉ đổi tài liệu / bài kiểm)."
  fi

  local code; code="$(health)"
  echo "HEALTH=$code"
  if [ -n "$DEPLOY_HEALTH" ] && [ "$code" != "200" ]; then
    rollback "$prev" "$sha" "${services[@]}"; return 1
  fi
  echo "RESULT=ok"
  return 0
}

# Đổi thư mục nào thì dựng lại service đó (cùng bảng với coder.deploy_services_for).
pick_services() {
  local prev="$1" sha="$2" paths
  paths="$(git diff --name-only "$prev" "$sha")"
  local out=()
  if grep -q '^backend/' <<<"$paths"; then
    out+=(api celery-worker celery-beat)
    # shellcheck disable=SC2086
    if docker compose $DEPLOY_COMPOSE config --services 2>/dev/null | grep -qx agent-poller; then out+=(agent-poller); fi
  fi
  grep -q '^frontend-v2/' <<<"$paths" && out+=(erp)
  grep -q '^frontend/' <<<"$paths" && out+=(web)
  grep -q '^help-center/' <<<"$paths" && out+=(help)
  printf '%s\n' "${out[@]}"
}

health() {
  [ -z "$DEPLOY_HEALTH" ] && { echo "-1"; return; }
  local i code=0
  for ((i = 0; i < DEPLOY_HEALTH_TRIES; i++)); do
    code="$(curl -s -o /dev/null -m 10 -w '%{http_code}' "$DEPLOY_HEALTH" || echo 0)"
    [ "$code" = "200" ] && break
    sleep "$DEPLOY_HEALTH_DELAY"
  done
  echo "$code"
}

rollback() {
  local prev="$1" sha="$2"; shift 2
  if [ "$DEPLOY_ROLLBACK" != "1" ] || [ "$prev" = "$sha" ]; then
    echo "RESULT=fail"; return
  fi
  echo "Bản mới hỏng, quay về $prev"
  git reset --hard "$prev" >/dev/null && echo "HEAD=$prev"
  if [ "$#" -gt 0 ]; then
    # shellcheck disable=SC2086
    docker compose $DEPLOY_COMPOSE up -d --build "$@" || true
  fi
  echo "HEALTH_AFTER_ROLLBACK=$(health)"
  echo "RESULT=rolled_back"
}

# Gọi main SAU khi bash đã đọc hết các hàm: chạy qua `bash -s` thì tệp này đi trên stdin, lệnh con nào
# lỡ đọc stdin sẽ nuốt mất phần còn lại của tệp — nên stdin của main là /dev/null.
main "$@" </dev/null
