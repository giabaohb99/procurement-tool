"""PHẦN THI HÀNH trên VPS: thao tác qua cổng duyệt, sao lưu, hoàn tác, chẩn đoán, tự chữa, báo tài nguyên.

ai-CR-068 (V-02, V-03, V-06) + ai-CR-069/070 (O-02 … O-06). Chạy TRONG máy sửa mã (runner) — chỉ máy có khóa
SSH lên VPS (cờ «được deploy») mới nhận vé `agent.run_op` / `agent.diagnose_incident` / `agent.resource_report`.
Phần nhận lệnh + cổng duyệt nằm ở `ops.py` (chạy ở bot); tệp này KHÔNG tự quyết được gì — chỉ chạy dòng sổ
`tab_agent_op` đã ở trạng thái «chờ máy» (đã duyệt, hoặc loại chỉ đọc trên dev, hoặc tự chữa dev trong trần).

Luật thi hành:
  - Kịch bản dựng TỪ SỔ (thư mục, đuôi compose, tên DB) + tham số đã kiểm mẫu; chữ tự do duy nhất đi xuống VPS
    là câu SQL / lệnh shell đại ca gõ — đã qua `guardrails` ở bot và qua lại lần nữa ở đây.
  - SQL chạy qua `python` trong container api của chính môi trường đó (SQLAlchemy, không qua mysql CLI — luật
    chống lỗi mã hóa tiếng Việt), câu SQL đi dạng base64 nên không có chuyện thoát chuỗi.
  - Sửa dữ liệu = sao lưu ĐÚNG các bảng bị đụng trước (mysqldump, nén) — sao lưu hỏng thì KHÔNG chạy.
  - Deploy prod = sao lưu cả DB prod trước. Hoàn tác deploy = deploy lại commit trước đó.
  - Kết quả qua `guardrails.mask_secrets` trước khi vào sổ hay lên Telegram.
"""
from __future__ import annotations

import base64
import json
import logging
import re
import subprocess
import time
from datetime import timedelta
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings

from . import coder, guardrails, telegram
from .constants import (
    ACT_OPS,
    ENV_PROD,
    HEAL_ACTIONS,
    INC_HEALING,
    INC_RESOLVED,
    INC_WAITING,
    OP_ACTION,
    OP_DATA_PLAN,
    OP_DEPLOY,
    OP_KIND_LABELS,
    OP_RESTORE,
    OP_BOT_DB_RESTORE,
    OP_SHELL_READ,
    OP_SHELL_WRITE,
    OP_SQL_READ,
    OP_SQL_WRITE,
    OP_VIEW,
    OPS_FAILED,
    OPS_OK,
    OPS_RUNNING,
)
from .timeutil import now_local, now_utc
from .model import AgentEnv, AgentIncident, AgentOp

log = logging.getLogger("app.agent_hub.ops_runner")

OUTPUT_KEEP = 3500
CARD_OUTPUT = 1800
VIEW_TIMEOUT = 180
SQL_TIMEOUT = 600
BACKUP_TIMEOUT = 1800
DIAG_TIMEOUT = 300
HEAL_HEALTH_TRIES = 12
HEAL_HEALTH_DELAY = 10

_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
_COMPOSE = re.compile(r"^[A-Za-z0-9_.\-/= ]{0,255}$")
_DIR = re.compile(r"^[A-Za-z0-9_.\-/~]{1,255}$")
_BACKUP_FILE = re.compile(r"^op\d+-[a-z0-9-]+-\d{8}-\d{6}(-[a-z]+)?\.sql\.gz$")


BOT_RESTORE_TIMEOUT = 1800       # ai-CR-141: tải bản sao lưu + quay lại DB bot


class OpsError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Mảnh kịch bản dựng từ sổ môi trường
# ---------------------------------------------------------------------------
def _q(value: str) -> str:
    return coder._sh_quote(value)


def _path_expr(path: str) -> str:
    """«~/x» → "$HOME"/'x' (dấu ~ trong ngoặc đơn không nở); đường tuyệt đối → '…'."""
    path = path or ""
    if path == "~":
        return '"$HOME"'
    if path.startswith("~/"):
        return '"$HOME"/' + _q(path[2:])
    return _q(path)


def _check_env(env: AgentEnv) -> None:
    if not env.dir or not _COMPOSE.match(env.compose_args or "") or not _DIR.match(env.dir):
        raise OpsError(f"sổ môi trường «{env.name}» thiếu thư mục hoặc đuôi compose lạ")


def _compose(env: AgentEnv) -> str:
    _check_env(env)
    return f"docker compose {env.compose_args}".rstrip()


def _cd(env: AgentEnv) -> str:
    _check_env(env)
    return f"cd {_path_expr(env.dir)}"


def _services(names: list[str] | None) -> list[str]:
    out = [s for s in (names or []) if _NAME.match(str(s))]
    if len(out) != len(names or []):
        raise OpsError("tên service lạ")
    return out


def env_vars(env: AgentEnv) -> dict:
    """Biến DEPLOY_* cho deploy.sh — lấy nguyên từ sổ môi trường."""
    return {"DEPLOY_DIR": env.dir, "DEPLOY_COMPOSE": env.compose_args, "DEPLOY_BRANCH": env.branch,
            "DEPLOY_HEALTH": env.health_url}


def _backup_dir() -> str:
    return settings.AGENT_OPS_BACKUP_DIR or "~/agent-backups"


def _db_container() -> str:
    name = settings.AGENT_OPS_DB_CONTAINER or "procurement-mysql"
    if not _NAME.match(name):
        raise OpsError("tên container DB lạ")
    return name


def _dump_cmd(db_name: str, tables: list[str]) -> str:
    """mysqldump chạy TRONG container MySQL; mật khẩu root nở ra bên trong container, không qua dòng lệnh
    của VPS, không lên output. Chỉ tên đã kiểm mẫu được ghép vào."""
    if not _NAME.match(db_name or "") or any(not _NAME.match(t) for t in tables):
        raise OpsError("tên DB / bảng lạ")
    inner = ("MYSQL_PWD=\"$MYSQL_ROOT_PASSWORD\" exec mysqldump --single-transaction --default-character-set=utf8mb4 "
             f"--skip-lock-tables -uroot {db_name} {' '.join(tables)}").strip()
    return f"docker exec {_db_container()} sh -c {_q(inner)}"


def backup_script(op_id: int, env: AgentEnv, tables: list[str], *, tag: str = "") -> str:
    """Sao lưu bảng (hoặc cả DB khi `tables` rỗng) ra tệp nén trong thư mục sao lưu. In `BACKUP=<đường dẫn>`."""
    stamp = now_utc().strftime("%Y%m%d-%H%M%S")
    name = f"op{op_id}-{re.sub(r'[^a-z0-9-]', '-', env.name.lower())}-{stamp}{('-' + tag) if tag else ''}.sql.gz"
    keep = max(1, int(settings.AGENT_OPS_BACKUP_KEEP_DAYS or 14))
    return "\n".join([
        "set -euo pipefail",
        f"D={_path_expr(_backup_dir())}",
        'mkdir -p "$D"',
        f"find \"$D\" -maxdepth 1 -name 'op*.sql.gz' -mtime +{keep} -delete || true",
        f'F="$D"/{_q(name)}',
        f'{_dump_cmd(env.db_name, tables)} | gzip > "$F"',
        'test -s "$F"',
        'echo "BACKUP=$F"',
        'echo "BACKUP_SIZE=$(du -h "$F" | cut -f1)"',
    ]) + "\n"


def restore_script(env: AgentEnv, path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    if not _BACKUP_FILE.match(name):
        raise OpsError("tệp sao lưu lạ — chỉ nạp lại tệp do bot tạo")
    if not _NAME.match(env.db_name or ""):
        raise OpsError("tên DB lạ")
    inner = ("MYSQL_PWD=\"$MYSQL_ROOT_PASSWORD\" exec mysql --default-character-set=utf8mb4 "
             f"-uroot {env.db_name}")
    return "\n".join([
        "set -euo pipefail",
        f"F={_path_expr(_backup_dir())}/{_q(name)}",
        'test -s "$F"',
        f'gunzip -c "$F" | docker exec -i {_db_container()} sh -c {_q(inner)}',
        'echo "RESTORED=$F"',
    ]) + "\n"


_SQL_PY = """
import base64, json, sys
from app.core.database import engine
sql = base64.b64decode("{b64}").decode("utf-8")
write = {write}
with engine.connect() as c:
    c.execution_options(no_parameters=True)   # dấu % trong LIKE không bị hiểu là chỗ tham số
    if not write:
        c.exec_driver_sql("SET SESSION TRANSACTION READ ONLY")
    r = c.exec_driver_sql(sql)
    if r.returns_rows:
        cols = list(r.keys())
        rows = r.fetchmany(51)
        print("COLS=" + json.dumps(cols, ensure_ascii=False))
        for row in rows[:50]:
            print(json.dumps([None if v is None else str(v) for v in row], ensure_ascii=False))
        if len(rows) > 50:
            print("(còn nữa — chỉ in 50 dòng đầu)")
    else:
        print("ROWCOUNT=" + str(r.rowcount))
    if write:
        c.commit()
    else:
        c.rollback()
"""


def sql_script(env: AgentEnv, sql: str, *, write: bool) -> str:
    """Câu SQL chạy bằng SQLAlchemy TRONG container api của môi trường (đúng DB, đúng tài khoản của app)."""
    kind, reason, _ = guardrails.classify_sql(sql)
    if kind == guardrails.SQL_DENIED or (kind == guardrails.SQL_WRITE and not write) \
            or (kind == guardrails.SQL_READ and write):
        raise OpsError(f"câu SQL không qua được lan can: {reason or kind}")
    b64 = base64.b64encode(sql.strip().rstrip(";").encode("utf-8")).decode("ascii")
    py = _SQL_PY.format(b64=b64, write="True" if write else "False")
    return "\n".join([
        "set -euo pipefail",
        _cd(env),
        f"{_compose(env)} exec -T api python - <<'AGENT_PY'",
        py.strip(),
        "AGENT_PY",
    ]) + "\n"


def shell_script(env: AgentEnv, cmd: str, *, write: bool) -> str:
    kind, reason = guardrails.classify_shell(cmd)
    if kind == guardrails.SHELL_DENIED or (kind == guardrails.SHELL_WRITE and not write):
        raise OpsError(f"lệnh không qua được lan can: {reason or kind}")
    return "\n".join([_cd(env), "export LANG=C.UTF-8", cmd.strip()]) + "\n"


def action_script(env: AgentEnv, action: str, services: list[str]) -> str:
    svcs = " ".join(_services(services))
    c = _compose(env)
    body = {
        "restart_services": f"{c} restart {svcs}",
        "up_services": f"{c} up -d {svcs}",
        "build_services": f"{c} up -d --build {svcs}",
        #  Chỉ bộ đệm build + ảnh treo (dangling) quá 24 giờ. Không volume, không ảnh đang dùng.
        "prune_build_cache": "docker builder prune -f --filter until=24h && docker image prune -f --filter until=24h",
    }.get(action)
    if body is None:
        raise OpsError(f"thao tác lạ: {action}")
    if action in ("restart_services", "up_services", "build_services") and not svcs:
        raise OpsError("thiếu tên service")
    return "\n".join(["set -euo pipefail", _cd(env), body, f"{c} ps --format 'table {{{{.Service}}}}\\t{{{{.State}}}}\\t{{{{.Status}}}}'"]) + "\n"


def status_script(env: AgentEnv) -> str:
    c = _compose(env)
    return "\n".join([
        _cd(env),
        'echo "HEAD=$(git rev-parse --short HEAD) $(git log -1 --format=%s | cut -c1-80)"',
        f"{c} ps -a --format 'table {{{{.Service}}}}\\t{{{{.State}}}}\\t{{{{.Status}}}}'",
    ]) + "\n"


def logs_script(env: AgentEnv, service: str, lines: int) -> str:
    svc = _services([service])[0]
    n = max(10, min(int(lines or 80), 400))
    return "\n".join([_cd(env), f"{_compose(env)} logs --no-color --tail {n} {svc} 2>&1"]) + "\n"


RESOURCE_SCRIPT = r"""
echo "HOST=$(hostname)"
echo "CPUS=$(nproc)"
echo "LOAD=$(cut -d' ' -f1-3 /proc/loadavg)"
free -m | awk '/^Mem:/{print "MEM_TOTAL="$2; print "MEM_USED="$3; print "MEM_AVAIL="$7} /^Swap:/{print "SWAP_TOTAL="$2; print "SWAP_USED="$3}'
df -P / | awk 'NR==2{print "DISK_TOTAL_KB="$2; print "DISK_USED_KB="$3; print "DISK_PCT="$5}'
echo "TOP:"
docker stats --no-stream --format '{{.Name}} {{.CPUPerc}} {{.MemUsage}}' 2>/dev/null | sort -t' ' -k2 -rn | head -8
echo "DOCKER_DF:"
docker system df --format '{{.Type}}: {{.Size}} (thu hồi được {{.Reclaimable}})' 2>/dev/null
"""


def diag_script(env: AgentEnv) -> str:
    """Gom đủ thứ để chẩn đoán (O-02), CHỈ ĐỌC: container, log đuôi, commit, migration, tài nguyên, health."""
    c = _compose(env)
    health = f"curl -s -o /dev/null -m 10 -w '%{{http_code}}' {_q(env.health_url)} || echo 0" if env.health_url else "echo -1"
    return "\n".join([
        _cd(env),
        'echo "== COMMIT"; git log -3 --format="%h %cr %s" | cut -c1-120',
        f"echo \"== HEALTH=$({health})\"",
        f"echo '== CONTAINER'; {c} ps -a --format 'table {{{{.Service}}}}\\t{{{{.State}}}}\\t{{{{.Status}}}}'",
        f"for s in $({c} ps -a --format '{{{{.Service}}}} {{{{.State}}}}' | awk '$2!=\"running\"{{print $1}}'); do "
        f"echo \"== LOG $s (không chạy)\"; {c} logs --no-color --tail 60 \"$s\" 2>&1 | tail -60; done",
        f"echo '== LOG api'; {c} logs --no-color --tail 80 api 2>&1 | tail -80",
        f"echo '== MIGRATION'; timeout 25 {c} exec -T api alembic current 2>&1 | tail -3 || true",
        "echo '== MAY'", RESOURCE_SCRIPT.strip(),
    ]) + "\n"


def parse_resources(out: str) -> dict:
    info: dict = {}
    for key in ("HOST", "CPUS", "LOAD", "MEM_TOTAL", "MEM_USED", "MEM_AVAIL", "SWAP_TOTAL", "SWAP_USED",
                "DISK_TOTAL_KB", "DISK_USED_KB", "DISK_PCT"):
        m = re.search(rf"^{key}=(.*)$", out, re.MULTILINE)
        if m:
            info[key.lower()] = m.group(1).strip()
    top = re.search(r"^TOP:\n(.*?)(?:^DOCKER_DF:|\Z)", out, re.MULTILINE | re.DOTALL)
    info["top"] = [ln for ln in (top.group(1).splitlines() if top else []) if ln.strip()][:8]
    ddf = re.search(r"^DOCKER_DF:\n(.*)\Z", out, re.MULTILINE | re.DOTALL)
    info["docker_df"] = [ln for ln in (ddf.group(1).splitlines() if ddf else []) if ln.strip()][:4]
    return info


def resource_text(env_names: list[str], info: dict) -> str:
    esc = telegram.esc

    def gb(mb: str) -> str:
        try:
            return f"{int(mb) / 1024:.1f}"
        except (TypeError, ValueError):
            return "?"

    def gb_kb(kb: str) -> str:
        try:
            return f"{int(kb) / 1024 / 1024:.0f}"
        except (TypeError, ValueError):
            return "?"

    lines = [f"<b>Máy {esc(info.get('host') or '?')}</b> ({esc(', '.join(env_names))})",
             f"CPU {esc(info.get('cpus') or '?')} lõi · tải {esc(info.get('load') or '?')}",
             f"RAM dùng {gb(info.get('mem_used'))}/{gb(info.get('mem_total'))} GB, còn {gb(info.get('mem_avail'))} GB"
             + (f" · swap {gb(info.get('swap_used'))}/{gb(info.get('swap_total'))} GB" if info.get("swap_total") not in (None, "0") else ""),
             f"Đĩa dùng {esc(info.get('disk_pct') or '?')} ({gb_kb(info.get('disk_used_kb'))}/{gb_kb(info.get('disk_total_kb'))} GB)"]
    if info.get("top"):
        lines.append("Container ăn nhiều nhất:")
        lines += [f"• {esc(t)}" for t in info["top"][:5]]
    if info.get("docker_df"):
        lines.append("Docker: " + esc(" · ".join(info["docker_df"])))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Chạy một dòng sổ thao tác
# ---------------------------------------------------------------------------
def _ssh(script: str, env: AgentEnv, *, timeout: int, check: bool = True) -> str:
    return coder.run_ssh(script, timeout=timeout, target=env, check=check)


def _run_backup(db: Session, op: AgentOp, env: AgentEnv, tables: list[str], *, tag: str = "") -> str:
    out = _ssh(backup_script(op.id, env, tables, tag=tag), env, timeout=BACKUP_TIMEOUT)
    m = re.search(r"^BACKUP=(\S+)\s*$", out, re.MULTILINE)
    if not m:
        raise OpsError("sao lưu không ra tệp — em KHÔNG chạy thao tác")
    return m.group(1)


def bot_restore_script(p: dict) -> str:
    """ai-CR-141: tải bản sao lưu DB bot từ link R2 ký sẵn về tệp tạm trên VPS, chạy `agent_restore.sh --yes`, xóa tệp.
    Script đi qua stdin của ssh — `</dev/null` để `docker exec -i` bên trong không nuốt phần còn lại của script."""
    mode = str(p.get("mode") or "")
    url = str(p.get("url") or "")
    if mode not in ("full", "part") or not url.startswith("https://"):
        raise OpsError("thẻ quay lại DB bot thiếu link tải hoặc kiểu")
    script = settings.AGENT_RESTORE_SCRIPT or "~/agent-hub/backend/scripts/agent_restore.sh"
    stack = settings.AGENT_RESTORE_STACK_DIR or "~/agent-hub"
    if not _DIR.match(script) or not _DIR.match(stack):
        raise OpsError("đường dẫn script / stack lạ")
    args = ["--full"] if mode == "full" else ["--table", str(p.get("table") or ""), "--where", str(p.get("where") or "")]
    if mode == "part" and not re.fullmatch(r"tab_[a-z0-9_]+", args[1]):
        raise OpsError("tên bảng lạ")
    env_vars = f"STACK_DIR={_path_expr(stack)} MYSQL_CONTAINER={_q(_db_container())}"
    if settings.AGENT_RESTORE_HEALTH_URL:
        env_vars += f" HEALTH_URL={_q(settings.AGENT_RESTORE_HEALTH_URL)}"
    return "\n".join([
        "set -euo pipefail",
        'F="$(mktemp --suffix=.sql.gz /tmp/agent_hub-restore-XXXXXX)"',
        "trap 'rm -f \"$F\"' EXIT",
        f'curl -fsS --max-time 900 -o "$F" {_q(url)}',
        'test -s "$F"',
        f'{env_vars} bash {_path_expr(script)} "$F" {" ".join(_q(a) for a in args)} --yes </dev/null',
    ]) + "\n"


def _after_full_bot_restore(snapshot: dict, status: int, out: str, error: str) -> None:
    """DB bot vừa bị THAY bằng bản sao lưu: dòng sổ thao tác này không còn (bản sao lưu có trước nó), kết nối cũ trỏ vào
    DB đã xóa. Bỏ hết kết nối, mở phiên mới, ghi LẠI một dòng sổ cho lượt này rồi báo."""
    from app.core.database import SessionLocal, engine

    engine.dispose()
    db2 = SessionLocal()
    try:
        env = db2.get(AgentEnv, snapshot["env_id"])
        params = {k: v for k, v in (snapshot.get("params") or {}).items() if k != "url"}
        params["rewritten"] = True
        new = AgentOp(env_id=snapshot["env_id"], kind=OP_BOT_DB_RESTORE, status=status, title=snapshot["title"],
                      command=snapshot["command"], params=params, undo_params={}, chat_id=snapshot["chat_id"],
                      auto=False, incident_id=0, approved_at=snapshot.get("approved_at"),
                      started_at=snapshot.get("started_at"), finished_at=now_utc(),
                      output=guardrails.mask_secrets(out or "")[-OUTPUT_KEEP:], error=guardrails.mask_secrets(error)[:1000],
                      backup_ref="", created_by=0, updated_by=0)
        db2.add(new)
        db2.commit()
        send_result(db2, new, env)
    finally:
        db2.close()


def execute(db: Session, op: AgentOp) -> dict:
    """Chạy MỘT dòng sổ đã ở trạng thái chờ máy. Không ném lỗi nghiệp vụ: mọi lỗi thành `OPS_FAILED` + tin báo."""
    env = db.get(AgentEnv, op.env_id)
    op.status = OPS_RUNNING
    op.started_at = now_utc()
    db.commit()
    p = dict(op.params or {})
    out = ""
    try:
        if env is None or env.revoked_at is not None:
            raise OpsError("môi trường đã bị gỡ khỏi sổ")
        if op.kind == OP_VIEW:
            out = _view(env, p)
        elif op.kind == OP_SQL_READ:
            out = _ssh(sql_script(env, op.command, write=False), env, timeout=SQL_TIMEOUT)
        elif op.kind == OP_SQL_WRITE:
            _, _, tables = guardrails.classify_sql(op.command)
            path = _run_backup(db, op, env, tables)
            op.backup_ref = path[-255:]
            op.undo_params = {"kind": OP_RESTORE, "path": path, "tables": tables}
            db.commit()
            out = _ssh(sql_script(env, op.command, write=True), env, timeout=SQL_TIMEOUT)
        elif op.kind == OP_RESTORE:
            tables = list(p.get("tables") or [])
            #  Nạp lại cũng là sửa dữ liệu: sao lưu trạng thái HIỆN TẠI trước, để hoàn tác được cả lượt hoàn tác.
            cur = _run_backup(db, op, env, tables, tag="truoc") if tables else ""
            op.backup_ref = cur[-255:]
            if cur:
                op.undo_params = {"kind": OP_RESTORE, "path": cur, "tables": tables}
            db.commit()
            out = _ssh(restore_script(env, str(p.get("path") or "")), env, timeout=BACKUP_TIMEOUT)
        elif op.kind in (OP_SHELL_READ, OP_SHELL_WRITE):
            out = _ssh(shell_script(env, op.command, write=op.kind == OP_SHELL_WRITE), env, timeout=VIEW_TIMEOUT,
                       check=False)
        elif op.kind == OP_ACTION:
            action = str(p.get("action") or "")
            if action == "rollback_last_deploy":
                out = _rollback(db, op, env)
            else:
                out = _ssh(action_script(env, action, list(p.get("services") or [])), env, timeout=coder.DEPLOY_TIMEOUT_SEC)
        elif op.kind == OP_DEPLOY:
            out = _deploy(db, op, env, p)
        elif op.kind == OP_DATA_PLAN:
            out = plan_data(db, op, env)
        elif op.kind == OP_BOT_DB_RESTORE:
            if p.get("mode") == "full":
                snapshot = {"env_id": op.env_id, "title": op.title, "command": op.command, "params": dict(p),
                            "chat_id": op.chat_id, "approved_at": op.approved_at, "started_at": op.started_at}
                db.commit()
                try:
                    out = _ssh(bot_restore_script(p), env, timeout=BOT_RESTORE_TIMEOUT)
                except (OpsError, coder.CoderError, subprocess.TimeoutExpired, OSError) as e:
                    err = str(e) if not isinstance(e, subprocess.TimeoutExpired) else "quá giờ chờ — có thể còn chạy dở"
                    db.rollback()
                    _after_full_bot_restore(snapshot, OPS_FAILED, str(getattr(e, "output", "") or ""), err)
                    return {"status": "error", "op": 0, "error": err[:300]}
                db.rollback()
                _after_full_bot_restore(snapshot, OPS_OK, out, "")
                return {"status": "ok", "op": 0, "error": ""}
            out = _ssh(bot_restore_script(p), env, timeout=BOT_RESTORE_TIMEOUT)
            op.params = {k: v for k, v in p.items() if k != "url"}      # link tải xong việc thì bỏ khỏi sổ
        else:
            raise OpsError(f"loại thao tác lạ {op.kind}")
        if op.kind in (OP_SHELL_READ, OP_SHELL_WRITE) and re.search(r"^RC=(\d+)\s*$", out, re.MULTILINE):
            rc = re.findall(r"^RC=(\d+)\s*$", out, re.MULTILINE)[-1]
            op.error = f"lệnh thoát mã {rc}"
        op.status = OPS_OK
    except (OpsError, coder.CoderError, subprocess.TimeoutExpired, OSError) as e:
        err = str(e) if not isinstance(e, subprocess.TimeoutExpired) else "quá giờ chờ — thao tác có thể còn chạy dở trên VPS"
        op.status = OPS_FAILED
        op.error = guardrails.mask_secrets(err)[:1000]
        out = out or str(getattr(e, "output", "") or "")
    op.output = guardrails.mask_secrets(out or "")[-OUTPUT_KEEP:]
    op.finished_at = now_utc()
    db.commit()
    #  Lượt soạn lệnh sửa dữ liệu tự gửi thẻ duyệt / câu trả lời rồi — chỉ báo thêm khi HỎNG.
    if op.status == OPS_FAILED or not (op.auto or op.kind == OP_DATA_PLAN):
        send_result(db, op, env)
    return {"status": "ok" if op.status == OPS_OK else "error", "op": op.id, "error": op.error}


def _view(env: AgentEnv, p: dict) -> str:
    what = p.get("what")
    if what == "status":
        return _ssh(status_script(env), env, timeout=VIEW_TIMEOUT)
    if what == "logs":
        return _ssh(logs_script(env, str(p.get("service") or "api"), int(p.get("lines") or 80)), env, timeout=VIEW_TIMEOUT)
    if what == "resources":
        return _ssh(RESOURCE_SCRIPT, env, timeout=VIEW_TIMEOUT)
    if what == "diagnose":
        raw = guardrails.mask_secrets(_ssh(diag_script(env), env, timeout=VIEW_TIMEOUT, check=False))
        diag = diagnose(env, raw, question=str(p.get("question") or ""))
        return format_diagnosis(diag) + "\n\n--- dữ liệu gom được ---\n" + raw[-1500:]
    raise OpsError(f"kiểu xem lạ: {what}")


def _deploy(db: Session, op: AgentOp, env: AgentEnv, p: dict) -> str:
    commit = str(p.get("commit") or "latest")
    services = _services(list(p.get("services") or []))
    if env.kind == ENV_PROD:
        #  Prod: sao lưu CẢ DB trước — migration đi cùng bản mới không hoàn tác được bằng cách deploy lại.
        path = _run_backup(db, op, env, [], tag="db")
        op.backup_ref = path[-255:]
        db.commit()
    target = env.name if _NAME.match(env.name) else "custom"
    out = _ssh(coder.deploy_script(services, commit=commit, target=target, env_vars=env_vars(env)), env,
               timeout=coder.DEPLOY_TIMEOUT_SEC, check=False)
    info = coder.parse_deploy_output(out)
    prev = info.get("prev") or ""
    if prev and re.fullmatch(r"[0-9a-f]{7,40}", prev):
        used = [s for s in (info.get("services") or "").split() if _NAME.match(s)]
        op.undo_params = {"kind": OP_DEPLOY, "commit": prev, "services": used}
    p.update(prev=prev, head=info.get("head", ""), result=info.get("result", ""), health=info.get("health", ""),
             log=info.get("log", ""))
    op.params = p
    db.commit()
    if info.get("result") != "ok":
        coder_msg = {"rolled_back": "health hỏng sau deploy — VPS đã TỰ QUAY VỀ bản trước",
                     "busy": "đang có lượt deploy khác trên môi trường này"}.get(info.get("result", ""))
        raise _with_output(OpsError(coder_msg or f"deploy hỏng: {info.get('err') or 'xem log'}"), out)
    return out


def _with_output(e: Exception, out: str) -> Exception:
    e.output = out  # type: ignore[attr-defined]
    return e


def last_ok_deploy(db: Session, env: AgentEnv, *, within: timedelta | None = None) -> AgentOp | None:
    q = select(AgentOp).where(AgentOp.env_id == env.id, AgentOp.kind == OP_DEPLOY, AgentOp.status == OPS_OK)
    if within is not None:
        q = q.where(AgentOp.finished_at >= now_utc() - within)
    return db.scalar(q.order_by(AgentOp.id.desc()).limit(1))


def _rollback(db: Session, op: AgentOp, env: AgentEnv) -> str:
    """Quay về commit trước lần deploy THÀNH CÔNG gần nhất do bot chạy (tự chữa: chỉ khi lần đó trong 2 giờ)."""
    last = last_ok_deploy(db, env, within=timedelta(hours=2) if op.auto else None)
    prev = str(((last.undo_params or {}).get("commit") if last else "") or "")
    if not prev:
        raise OpsError("không có lần deploy nào của bot (gần đây) để quay về")
    p = {"commit": prev, "services": list((last.undo_params or {}).get("services") or [])}
    op.params = {**(op.params or {}), **p}
    db.commit()
    return _deploy(db, op, env, p)


# ---------------------------------------------------------------------------
# Tin báo kết quả
# ---------------------------------------------------------------------------
def _owner_chat(op: AgentOp | None = None) -> str:
    return (op.chat_id if op is not None and op.chat_id else "") or settings.AGENT_TELEGRAM_CHAT_ID


def _reply(db: Session, chat_id: str, text: str) -> None:
    from . import service

    service.reply(db, chat_id, text, action=ACT_OPS)
    db.commit()


def send_result(db: Session, op: AgentOp, env: AgentEnv | None) -> None:
    """Tin báo kết quả một thao tác (ai-CR-075: tiêu đề đậm · nhãn đậm · ghi chú nghiêng · cách dòng giữa phần)."""
    esc = telegram.esc
    secs = int((op.finished_at - op.started_at).total_seconds()) if op.finished_at and op.started_at else 0
    ok = op.status == OPS_OK
    undo = (f"<i>Muốn trả lại như cũ: «hoàn tác thao tác #{op.id}».</i>"
            if ok and op.undo_params and not op.undone_by_op_id else "")
    if (op.params or {}).get("plain") or op.kind == OP_DATA_PLAN:
        #  ai-CR-073: lệnh sửa dữ liệu bằng lời báo bằng câu thường, không bày output SQL.
        if ok:
            m = re.findall(r"^ROWCOUNT=(-?\d+)\s*$", op.output or "", re.MULTILINE)
            blocks = [f"<b>XONG</b> · thao tác #{op.id}", esc(op.title)]
            if m:
                blocks.append(f"<b>Đã đổi:</b> {m[-1]} dòng")
        else:
            blocks = [f"<b>KHÔNG LÀM ĐƯỢC</b> · thao tác #{op.id}", esc(op.title),
                      f"<b>Lý do:</b> {esc(op.error[:500] or 'lỗi không rõ')}"]
        if undo:
            blocks.append(undo)
        _reply(db, _owner_chat(op), "\n\n".join(blocks))
        return
    where = f" trên <b>{esc(env.name)}</b>" if env else ""
    blocks = [("<b>XONG</b>" if ok else "<b>HỎNG</b>") + f" · {esc(OP_KIND_LABELS.get(op.kind, 'thao tác'))}{where} · "
              f"thao tác #{op.id} · {secs} giây",
              esc(op.title)]
    if op.error:
        blocks.append(f"<b>{'Lưu ý' if ok else 'Lỗi'}:</b> {esc(op.error[:500])}")
    if op.output:
        blocks.append(f"<b>Kết quả:</b>\n<pre>{esc(op.output[-CARD_OUTPUT:])}</pre>")
    if op.backup_ref:
        blocks.append(f"<b>Sao lưu trước khi chạy:</b> <code>{esc(op.backup_ref)}</code>")
    if undo:
        blocks.append(undo)
    _reply(db, _owner_chat(op), "\n\n".join(blocks))


# ---------------------------------------------------------------------------
# Báo tài nguyên (V-06)
# ---------------------------------------------------------------------------
def hosts(db: Session) -> dict[str, list[AgentEnv]]:
    """Gom môi trường theo máy (dev + prod hiện chung một VPS → báo một lần)."""
    groups: dict[str, list[AgentEnv]] = {}
    for env in db.scalars(select(AgentEnv).where(AgentEnv.revoked_at.is_(None)).order_by(AgentEnv.id)):
        key = f"{env.host or settings.AGENT_VPS_HOST}:{env.port or settings.AGENT_VPS_PORT}"
        groups.setdefault(key, []).append(env)
    return groups


def resource_report(db: Session, *, chat_id: str = "") -> str:
    from . import ops

    parts = []
    for envs in hosts(db).values():
        try:
            out = _ssh(RESOURCE_SCRIPT, envs[0], timeout=VIEW_TIMEOUT)
            parts.append(resource_text([e.name for e in envs], parse_resources(out)))
        except (OpsError, coder.CoderError, subprocess.TimeoutExpired, OSError) as e:
            parts.append(f"<b>Máy của {telegram.esc(', '.join(e2.name for e2 in envs))}</b>: không đọc được "
                         f"({telegram.esc(str(e)[:200])})")
    parts.append(ops.activity_text(db))
    text = "<b>Tình hình máy</b> " + now_local().strftime("%d/%m %H:%M") + "\n\n" + "\n\n".join(parts)
    _reply(db, chat_id or settings.AGENT_TELEGRAM_CHAT_ID, text)
    return text


# ---------------------------------------------------------------------------
# Chẩn đoán (O-02)
# ---------------------------------------------------------------------------
_DIAG_BRIEF = """\
Bạn là kỹ sư vận hành của hệ thống ERP DEGO (FastAPI + MySQL + Redis + Celery + React, chạy Docker Compose).
Môi trường «{env}» ({kind}) đang có vấn đề: {symptom}
{question}
Dưới đây là dữ liệu đã gom trên VPS (CHỈ ĐỌC; bí mật đã che). Đọc và chẩn đoán. KHÔNG dùng công cụ nào, chỉ
trả lời bằng chữ.

Trả lời ĐÚNG một khối JSON (không chữ nào ngoài khối), các khóa:
  "summary": 1–2 câu tiếng Việt: chuyện gì đang xảy ra,
  "cause": nguyên nhân khả dĩ nhất, ngắn (≤ 12 chữ, tiếng Việt, không số liệu thay đổi theo lần — dùng để gom sự cố lặp),
  "action": MỘT trong {actions},
  "services": danh sách service compose cần thao tác (rỗng nếu không cần),
  "confidence": số 0..1,
  "fix_hint": nếu lỗi nằm ở MÃ NGUỒN (exception lặp lại, migration hỏng…) thì 1 câu gợi ý sửa gốc rễ, không thì "".

Chọn action theo luật: container dừng/thoát → "up_services"; container chạy mà treo/không trả lời → "restart_services";
lỗi bắt đầu ngay sau commit mới nhất và log chỉ ra lỗi mã → "rollback_last_deploy"; đĩa > 90% do bộ đệm build →
"prune_build_cache"; DB / mạng ngoài / không rõ → "none". KHÔNG bao giờ đề xuất xóa dữ liệu.

=== DỮ LIỆU ===
{data}
"""


def _ops_workdir() -> str:
    path = Path(settings.AGENT_WORKTREE_ROOT) / "ops"
    path.mkdir(parents=True, exist_ok=True)
    try:
        coder._chown_runner(path)
    except Exception:  # noqa: BLE001 — không có user runner (chạy thử) thì thôi
        pass
    return str(path)


def heuristic_diagnosis(raw: str) -> dict:
    """Chẩn đoán dự phòng khi Claude không trả lời được: chỉ dựa vào trạng thái container và đĩa."""
    stopped = []
    block = re.search(r"== CONTAINER\n(.*?)(?:\n== |\Z)", raw, re.DOTALL)
    for ln in (block.group(1).splitlines() if block else [])[1:]:
        cols = ln.split()
        if len(cols) >= 2 and cols[1] not in ("running", "State") and _NAME.match(cols[0]):
            stopped.append(cols[0])
    pct = re.search(r"^DISK_PCT=(\d+)%", raw, re.MULTILINE)
    if stopped:
        return {"summary": f"Container không chạy: {', '.join(stopped)}.", "cause": "container dừng",
                "action": "up_services", "services": stopped, "confidence": 0.6, "fix_hint": ""}
    if pct and int(pct.group(1)) >= 92:
        return {"summary": f"Đĩa đầy {pct.group(1)}%.", "cause": "đĩa đầy", "action": "prune_build_cache",
                "services": [], "confidence": 0.6, "fix_hint": ""}
    return {"summary": "Không đọc ra nguyên nhân từ trạng thái container / đĩa.", "cause": "không rõ",
            "action": "none", "services": [], "confidence": 0.2, "fix_hint": ""}


def diagnose(env: AgentEnv, raw: str, *, symptom: str = "", question: str = "") -> dict:
    brief = _DIAG_BRIEF.format(env=env.name, kind="PROD" if env.kind == ENV_PROD else "dev/preview",
                               symptom=symptom or "đại ca hỏi tình trạng",
                               question=f"Câu hỏi của đại ca: {question}" if question else "",
                               actions=" | ".join(f'"{a}"' for a in HEAL_ACTIONS), data=raw[-12000:])
    cmd = [settings.AGENT_CODER_CMD, "-p", *coder.model_args(), "--output-format", "json", "--max-turns", "2"]
    try:
        data = coder._run_cli(cmd, brief, _ops_workdir(), DIAG_TIMEOUT)
        text = str(data.get("result") or "")
        m = re.search(r"\{.*\}", text, re.DOTALL)
        diag = json.loads(m.group(0)) if m else {}
    except (coder.CoderError, subprocess.TimeoutExpired, OSError, ValueError) as e:
        log.warning("agent_hub.ops: chẩn đoán bằng Claude hỏng (%s) — dùng luật dự phòng", e)
        diag = {}
    if not isinstance(diag, dict) or diag.get("action") not in HEAL_ACTIONS:
        fallback = heuristic_diagnosis(raw)
        fallback["summary"] = (str(diag.get("summary") or "") if isinstance(diag, dict) else "") or fallback["summary"]
        diag = fallback
    diag["services"] = [s for s in (diag.get("services") or []) if isinstance(s, str) and _NAME.match(s)][:6]
    return diag


def format_diagnosis(diag: dict) -> str:
    lines = [f"Chẩn đoán: {diag.get('summary') or '?'}", f"Nguyên nhân khả dĩ: {diag.get('cause') or '?'}"]
    action = diag.get("action") or "none"
    if action != "none":
        lines.append(f"Đề xuất: {action}" + (f" ({', '.join(diag.get('services') or [])})" if diag.get("services") else ""))
    if diag.get("fix_hint"):
        lines.append(f"Gốc rễ trong mã: {diag['fix_hint']}")
    return "\n".join(lines)


def signature_for(env: AgentEnv, cause: str) -> str:
    from .runners import slug

    return f"{env.name}:{slug(cause or 'khong-ro')[:60]}"[:120]


# ---------------------------------------------------------------------------
# Sự cố: chẩn đoán → tự chữa dev / đề xuất prod (O-02 … O-06)
# ---------------------------------------------------------------------------
def heal_count(db: Session, env: AgentEnv) -> int:
    since = now_utc() - timedelta(hours=1)
    return int(db.scalar(select(func.count(AgentOp.id)).where(
        AgentOp.env_id == env.id, AgentOp.auto.is_(True), AgentOp.incident_id != 0,
        AgentOp.created_at >= since)) or 0)


def wait_health(env: AgentEnv, *, tries: int = HEAL_HEALTH_TRIES, delay: int = HEAL_HEALTH_DELAY) -> int:
    if not env.health_url:
        return -1
    import requests

    code = 0
    for _ in range(tries):
        try:
            code = requests.get(env.health_url, timeout=10).status_code
        except requests.RequestException:
            code = 0
        if code == 200:
            return code
        time.sleep(delay)
    return code


def _heal_op(db: Session, env: AgentEnv, incident: AgentIncident, diag: dict, *, auto: bool) -> AgentOp:
    from . import ops

    action = diag["action"]
    services = list(diag.get("services") or [])
    if action in ("restart_services", "up_services") and not services:
        services = ["api"]
    title = f"Chữa sự cố #{incident.id}: {action}" + (f" {' '.join(services)}" if services else "")
    return ops.new_op(db, env, OP_ACTION, title=title, command=ops.describe_action(env, action, services),
                      params={"action": action, "services": services}, chat_id=settings.AGENT_TELEGRAM_CHAT_ID,
                      auto=auto, incident_id=incident.id)


def handle_incident(db: Session, incident: AgentIncident) -> dict:
    """Một sự cố vừa mở: gom → chẩn đoán → dev tự chữa (trong trần) / prod đề xuất chờ «đúng» → sổ + tin báo."""
    from . import ops

    env = db.get(AgentEnv, incident.env_id)
    if env is None:
        return {"status": "skipped"}
    esc = telegram.esc
    try:
        raw = guardrails.mask_secrets(_ssh(diag_script(env), env, timeout=VIEW_TIMEOUT, check=False))
    except (OpsError, coder.CoderError, subprocess.TimeoutExpired, OSError) as e:
        raw = f"(không SSH được vào VPS: {e})"
    diag = diagnose(env, raw, symptom=incident.symptom)
    incident.diagnosis = (format_diagnosis(diag) + "\n\n" + raw[-3000:])[:60000]
    incident.cause = str(diag.get("cause") or "")[:255]
    incident.action = str(diag.get("action") or "none")[:40]
    incident.signature = signature_for(env, incident.cause)
    db.commit()
    head = f"<b>Sự cố #{incident.id}</b> trên <b>{esc(env.name)}</b>: {esc(incident.symptom)}\n{esc(format_diagnosis(diag))}"

    task_note = ops.maybe_root_cause_task(db, incident, diag)
    if task_note:
        head += "\n" + task_note

    if incident.action == "none":
        incident.status = INC_WAITING
        db.commit()
        _reply(db, settings.AGENT_TELEGRAM_CHAT_ID, head + "\nKhông có thao tác an toàn nào em tự làm được — cần đại ca xem.")
        return {"status": "waiting", "incident": incident.id}

    can_auto = (settings.AGENT_HEAL_ENABLED and env.auto_heal and env.kind != ENV_PROD)
    if not can_auto:
        op = _heal_op(db, env, incident, diag, auto=False)
        incident.status = INC_WAITING
        incident.heal_op_id = op.id
        db.commit()
        why = "prod chỉ đề xuất" if env.kind == ENV_PROD else "tự chữa đang tắt"
        ops.ask_approval(db, settings.AGENT_TELEGRAM_CHAT_ID, op, env, lead=head + f"\n({why})")
        return {"status": "proposed", "incident": incident.id, "op": op.id}

    if heal_count(db, env) >= max(1, settings.AGENT_HEAL_MAX_PER_HOUR):
        incident.status = INC_WAITING
        db.commit()
        _reply(db, settings.AGENT_TELEGRAM_CHAT_ID, head + f"\nĐã tự chữa {settings.AGENT_HEAL_MAX_PER_HOUR} lần trong một giờ "
               "trên môi trường này — em DỪNG, cần đại ca xem.")
        return {"status": "capped", "incident": incident.id}

    op = _heal_op(db, env, incident, diag, auto=True)
    incident.status = INC_HEALING
    incident.heal_op_id = op.id
    db.commit()
    _reply(db, settings.AGENT_TELEGRAM_CHAT_ID, head + f"\nEm tự chữa trên dev: thao tác #{op.id}.")
    execute(db, op)
    code = wait_health(env) if op.status == OPS_OK else 0
    if code == 200:
        incident.status = INC_RESOLVED
        incident.resolved_at = now_utc()
        env.fail_streak = 0
        env.last_health_code = 200
        db.commit()
        mins = int((incident.resolved_at - (incident.started_at or incident.resolved_at)).total_seconds() // 60)
        _reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
               f"Sự cố #{incident.id} trên <b>{esc(env.name)}</b> đã hết sau tự chữa (gián đoạn ~{mins} phút).")
        return {"status": "healed", "incident": incident.id, "op": op.id}
    incident.status = INC_WAITING
    db.commit()
    _reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
           f"Tự chữa sự cố #{incident.id} trên <b>{esc(env.name)}</b> KHÔNG ăn (health {code}). Cần đại ca xem; "
           f"«thao tác #{op.id}» để xem kết quả.")
    return {"status": "heal_failed", "incident": incident.id, "op": op.id}


# ---------------------------------------------------------------------------
# Sửa dữ liệu bằng lời (ai-CR-073)
# ---------------------------------------------------------------------------
#  Đại ca nói bằng lời («gán chức vụ Nhân viên (Demo) cho các nhân sự có (CR-414) trong tên»). Claude Code đọc mô hình
#  dữ liệu trong mã nguồn (/app của runner, chỉ Read/Glob/Grep), xin TRA dữ liệu thật bằng các câu SELECT — runner
#  chạy giúp qua đường chỉ đọc có lan can rồi đưa kết quả lại — tối đa DATA_ROUNDS lượt, rồi trả MỘT câu lệnh sửa.
#  Runner kiểm lại bằng lan can + quy định (bảng cấm, trần số dòng), đếm số dòng thật, rồi đẻ ra một thao tác
#  OP_SQL_WRITE «chờ duyệt» với thẻ tiếng Việt. Claude không bao giờ tự chạy lệnh nào trên máy chủ.
DATA_ROUNDS = 4
DATA_LOOKUPS_PER_ROUND = 5
DATA_TIMEOUT = 600

_DATA_BRIEF = """\
Bạn là kỹ sư dữ liệu của hệ thống ERP DEGO (FastAPI + SQLAlchemy + MySQL 8). Thư mục hiện tại là mã nguồn backend:
mô hình bảng ở app/modules/*/model.py (và các tệp *_model.py), luật nghiệp vụ ở *service.py. Đọc chúng để biết bảng,
cột, và cách hệ thống tự ghi dữ liệu (ví dụ một giá trị phải ghi cùng lúc vào hai cột: cột id và cột nhãn chép).

Đại ca (người quản lý) nhờ, trên môi trường «{env}»:
«{request}»

Việc của bạn: soạn MỘT câu lệnh SQL làm đúng điều đại ca nhờ, ĐÚNG như hệ thống tự làm khi sửa qua màn hình.
Bạn KHÔNG chạy được gì. Muốn xem dữ liệu thật (id của danh mục, số dòng khớp, giá trị hiện tại) thì xin tra.

Mỗi lượt trả lời ĐÚNG một khối JSON, không chữ nào ngoài khối, theo MỘT trong ba dạng:
1. Xin tra (tối đa {per_round} câu, chỉ SELECT, không chọn cột mật khẩu / token / khóa):
   {{"lookups": ["SELECT ...", "..."]}}
2. Lệnh cuối:
   {{"summary": "MỘT câu ngắn (dưới 140 ký tự) bằng lời nghiệp vụ: đổi gì cho ai. KHÔNG tên bảng, tên cột, id, tên hàm",
     "sql": "MỘT câu UPDATE / INSERT / DELETE, có WHERE, không chú thích, chuỗi tiếng Việt viết đúng dấu",
     "count_sql": "SELECT COUNT(*) ... cùng điều kiện, đếm số dòng sẽ bị đổi",
     "preview_sql": "SELECT 2-3 cột người đọc hiểu (mã, tên, giá trị HIỆN TẠI của thứ sẽ đổi), đặt bí danh tiếng Việt
                     bằng dấu huyền (vd `Mã`, `Họ tên`, `Chức vụ hiện tại`), KHÔNG cột id, cùng điều kiện, LIMIT 10",
     "assumptions": ["tối đa 2 giả định QUAN TRỌNG đại ca cần biết, bằng lời nghiệp vụ, không tên bảng / cột / hàm"]}}
   Chi tiết kỹ thuật (bảng, cột, vì sao ghi hai cột…) để trong câu sql — đại ca xem được bằng «thao tác #n».
3. Không làm được an toàn bằng một câu SQL (cần đổi cấu trúc bảng, cần nhiều bước có điều kiện, đụng tài khoản /
   phân quyền / mật khẩu, yêu cầu vô nghĩa):
   {{"cannot": "lý do ngắn bằng tiếng Việt, và nên làm cách nào"}}

Luật: KHÔNG hỏi lại đại ca — yêu cầu mơ hồ thì chọn cách hợp lý nhất và ghi vào assumptions. Không DDL, không
TRUNCATE/DROP. Không đụng bảng tài khoản, vai trò, phân quyền, nhật ký, cấu hình hệ thống, bảng tab_agent_*.
Khớp chuỗi theo đúng chữ đại ca đưa (LIKE với % hai đầu khi đại ca nói «có trong tên»). Tối đa {max_rows} dòng.
"""


def _data_cmd(session_id: str, *, resume: bool) -> list[str]:
    return [settings.AGENT_CODER_CMD, "-p", *coder.model_args(), "--output-format", "json",
            "--allowedTools", "Read,Glob,Grep", "--max-turns", "12",
            "--resume" if resume else "--session-id", session_id]


def _data_workdir() -> str:
    """Claude đọc mô hình dữ liệu từ chính mã backend trong runner (/app); không có thì thư mục trống."""
    return "/app" if Path("/app/app/modules").is_dir() else _ops_workdir()


def short_text(text: str, limit: int) -> str:
    """Cắt ở ranh giới câu / chữ rồi thêm «…» — không cụt giữa chữ như «Qu» (thẻ đầu tiên 05/10)."""
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = max(cut.rfind(". "), cut.rfind("; "))
    if end >= limit // 2:
        return cut[:end + 1]
    return cut.rsplit(" ", 1)[0].rstrip(",;:") + "…"


def _json_block(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not m:
        return {}
    try:
        out = json.loads(m.group(0))
    except ValueError:
        return {}
    return out if isinstance(out, dict) else {}


def _run_lookups(env: AgentEnv, queries: list) -> str:
    parts = []
    for q in [str(x) for x in queries if str(x).strip()][:DATA_LOOKUPS_PER_ROUND]:
        kind, reason, _ = guardrails.classify_sql(q)
        if kind != guardrails.SQL_READ:
            parts.append(f"SQL: {q}\nBỊ CHẶN: {reason or 'không phải câu đọc'}")
            continue
        try:
            out = _ssh(sql_script(env, q, write=False), env, timeout=SQL_TIMEOUT, check=False)
        except (OpsError, coder.CoderError, subprocess.TimeoutExpired, OSError) as e:
            out = f"LỖI: {e}"
        parts.append(f"SQL: {q}\nKẾT QUẢ:\n{guardrails.mask_secrets(out)[-3000:]}")
    return "\n\n".join(parts) or "(không có câu tra hợp lệ)"


def _count_rows(env: AgentEnv, count_sql: str) -> int:
    kind, reason, _ = guardrails.classify_sql(count_sql)
    if kind != guardrails.SQL_READ:
        raise OpsError(f"câu đếm không hợp lệ: {reason or 'không phải câu đọc'}")
    out = _ssh(sql_script(env, count_sql, write=False), env, timeout=SQL_TIMEOUT)
    rows = [ln for ln in out.splitlines() if ln.strip().startswith("[")]
    try:
        return int(json.loads(rows[0])[0])
    except (IndexError, ValueError, TypeError):
        raise OpsError("không đếm được số dòng sẽ đổi") from None


def plan_data(db: Session, op: AgentOp, env: AgentEnv) -> str:
    """Soạn lệnh sửa dữ liệu từ lời đại ca → thao tác OP_SQL_WRITE chờ «đúng». Trả đoạn nhật ký cho dòng sổ."""
    from uuid import uuid4

    from . import ops, policy

    request = str((op.params or {}).get("request") or op.command)
    session = str(uuid4())
    msg = _DATA_BRIEF.format(env=env.name, request=request, per_round=DATA_LOOKUPS_PER_ROUND,
                             max_rows=policy.DATA_MAX_ROWS)
    from app.modules.assistant import glossary

    if terms := glossary.prompt_block(db, request):
        msg += "\n" + terms + "\n"          # ai-CR-077: «nhà máy» = phòng nào — đại ca đã dạy thì dùng luôn
    log_lines: list[str] = []
    plan: dict = {}
    for i in range(DATA_ROUNDS):
        data = coder._run_cli(_data_cmd(session, resume=i > 0), msg, _data_workdir(), DATA_TIMEOUT)
        plan = _json_block(str(data.get("result") or ""))
        if plan.get("lookups") and i < DATA_ROUNDS - 1:
            found = _run_lookups(env, plan["lookups"])
            log_lines.append(f"--- tra lượt {i + 1}\n{found[-1500:]}")
            msg = ("Kết quả tra trên VPS:\n\n" + found + "\n\nTiếp tục: xin tra thêm, hoặc trả lệnh cuối, hoặc cannot. "
                   "Chỉ một khối JSON.")
            continue
        break
    chat = op.chat_id or settings.AGENT_TELEGRAM_CHAT_ID
    if plan.get("cannot"):
        _reply(db, chat, f"Em không soạn được lệnh cho yêu cầu này: {telegram.esc(str(plan['cannot'])[:600])}")
        return "\n".join(log_lines + [f"cannot: {plan['cannot']}"])
    sql = str(plan.get("sql") or "").strip()
    if not sql:
        raise OpsError("máy sửa mã không soạn ra được lệnh sau nhiều lượt tra")
    kind, reason, tables = guardrails.classify_sql(sql)
    if kind != guardrails.SQL_WRITE:
        raise OpsError(f"lệnh soạn ra không qua lan can: {reason or 'không phải lệnh sửa'}")
    denied = [t for t in tables if policy.data_table_denied(t)]
    if denied:
        _reply(db, chat, f"Yêu cầu này đụng bảng {telegram.esc(', '.join(denied))} (tài khoản / phân quyền / nhật ký / "
               "cấu hình). Quy định không cho sửa thẳng bằng lệnh dữ liệu — đại ca sửa trên màn hình, hoặc giao thành "
               "việc sửa mã.")
        return "\n".join(log_lines + [f"từ chối: bảng cấm {denied}"])
    rows = _count_rows(env, str(plan.get("count_sql") or ""))
    if rows <= 0:
        _reply(db, chat, f"Không có bản ghi nào khớp yêu cầu trên <b>{telegram.esc(env.name)}</b> — em không đổi gì.")
        return "\n".join(log_lines + ["0 dòng khớp"])
    if rows > policy.DATA_MAX_ROWS:
        _reply(db, chat, f"Yêu cầu này đổi {rows} dòng, quá trần {policy.DATA_MAX_ROWS} dòng một lệnh. Đại ca chia nhỏ "
               "điều kiện, hoặc giao thành việc sửa mã.")
        return "\n".join(log_lines + [f"quá trần: {rows} dòng"])
    sample: list[str] = []
    preview_sql = str(plan.get("preview_sql") or "")
    if guardrails.classify_sql(preview_sql)[0] == guardrails.SQL_READ:
        try:
            sample = ops.format_rows(guardrails.mask_secrets(
                _ssh(sql_script(env, preview_sql, write=False), env, timeout=SQL_TIMEOUT)), limit=5)
        except (OpsError, coder.CoderError, subprocess.TimeoutExpired, OSError):
            sample = []
    summary = short_text(str(plan.get("summary") or request), 200)
    write = ops.new_op(db, env, OP_SQL_WRITE, title=summary, command=sql, chat_id=chat,
                       params={"plain": True, "rows": rows, "sample": sample, "request": request[:1000],
                               "assumptions": [short_text(str(a), 160) for a in (plan.get("assumptions") or [])][:2],
                               "plan_op": op.id})
    ops.ask_approval(db, chat, write, env)
    return "\n".join(log_lines + [f"đã soạn thao tác #{write.id}: {rows} dòng", sql])
