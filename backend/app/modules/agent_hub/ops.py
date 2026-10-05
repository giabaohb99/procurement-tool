"""SỔ MÔI TRƯỜNG + CỔNG DUYỆT THAO TÁC VPS + THEO DÕI SỨC KHỎE — phần chạy ở BOT (ai-CR-067..070).

Phase 6 (nhóm V) + phase 7 (nhóm O) của `doc/agent-hub/04`. Đại ca chốt 05/10/2026:
  - Bot code được vào VPS 1 xem và sửa, NHƯNG qua cổng: xem dev tự do · xem prod cần «đúng» · sửa dev cần «đúng»
    + sao lưu trước + nhật ký + lệnh hoàn tác · sửa prod cần «đúng» (+ OTP — TẠM BỎ QUA theo lệnh đại ca, V-04).
  - Sổ môi trường khai bằng câu nhắn; thêm VPS = thêm dòng.
  - Theo dõi health mỗi phút; hỏng liên tiếp → mở sự cố → máy sửa mã chẩn đoán → dev tự chữa trong danh sách thao
    tác an toàn (trần 3 lần/giờ), prod chỉ đề xuất chờ «đúng»; sự cố lặp lại → mở việc sửa gốc rễ.

Tệp này CHỈ nhận lệnh, kiểm lan can, ghi sổ, hỏi «đúng» và giao vé cho máy sửa mã (`agent.run_op`); phần chạy
thật trên VPS ở `ops_runner.py`. Cả hai tệp nằm trong danh sách cấm của bot code (V-05).
Chỉ CHAT CỦA ĐẠI CA (`telegram.is_allowed_chat`) ra lệnh được; công tắc tổng `AGENT_OPS_ENABLED`.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings

from . import guardrails, runners, telegram
from .constants import (
    ACT_COMMAND,
    ACT_GLOSS_WAIT,
    ACT_GRANT_WAIT,
    ACT_OP_DONE,
    ACT_OP_DROPPED,
    ACT_OP_WAIT,
    ACT_OPS,
    ACT_RUNNER_WAIT,
    CLOSED_STATUSES,
    DIR_OUT,
    ENV_KIND_LABELS,
    ENV_PREVIEW,
    ENV_PROD,
    INC_DIAGNOSING,
    INC_HEALING,
    INC_RESOLVED,
    INC_STATUS_LABELS,
    INC_WAITING,
    OP_ACTION,
    OP_DATA_PLAN,
    OP_DEPLOY,
    OP_KIND_LABELS,
    OP_READ_KINDS,
    OP_RESTORE,
    OP_SHELL_READ,
    OP_SHELL_WRITE,
    OP_SQL_READ,
    OP_SQL_WRITE,
    OP_STATUS_LABELS,
    OP_VIEW,
    OPS_CANCELLED,
    OPS_FAILED,
    OPS_OK,
    OPS_QUEUED,
    OPS_WAITING,
    RISK_MEDIUM,
    RUN_RUNNING,
    SRC_INCIDENT,
    ST_TRIAGE,
)
from .timeutil import now_utc
from .model import AgentEnv, AgentIncident, AgentMessage, AgentOp, AgentRun, AgentTask

log = logging.getLogger("app.agent_hub.ops")

CONFIRM_WINDOW = timedelta(minutes=15)
OP_EXPIRE = timedelta(hours=24)
REPEAT_WINDOW = timedelta(days=7)
REPEAT_MIN = 3
_ENV_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
_SERVICE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,63}$")
_PATHLIKE = re.compile(r"^[A-Za-z0-9_.\-/~]{1,255}$")
_COMPOSE_ARGS = re.compile(r"^[A-Za-z0-9_.\-/= ]{0,255}$")


def enabled() -> bool:
    return bool(settings.AGENT_OPS_ENABLED)


# ---------------------------------------------------------------------------
# Sổ môi trường (V-01)
# ---------------------------------------------------------------------------
def active_envs(db: Session) -> list[AgentEnv]:
    return list(db.scalars(select(AgentEnv).where(AgentEnv.revoked_at.is_(None)).order_by(AgentEnv.id)))


def env_by_name(db: Session, name: str) -> AgentEnv | None:
    return db.scalar(select(AgentEnv).where(AgentEnv.name == (name or "").strip().lower(),
                                            AgentEnv.revoked_at.is_(None)))


def is_prod(env: AgentEnv) -> bool:
    return int(env.kind or 0) == ENV_PROD


def env_listing(db: Session) -> str:
    esc = telegram.esc
    rows = active_envs(db)
    if not rows:
        return "Sổ môi trường trống. Thêm: «thêm môi trường staging: dir=~/x compose=\"-f a.yml\" branch=erp-v2 health=https://…»."
    lines = ["<b>Sổ môi trường:</b>"]
    for e in rows:
        health = ("chưa đo" if not e.last_health_at else
                  f"health {e.last_health_code}" + (f", hỏng {e.fail_streak} lượt liền" if e.fail_streak else ""))
        lines.append(
            f"• <b>{esc(e.name)}</b> ({esc(ENV_KIND_LABELS.get(e.kind, '?'))}) — máy {esc(e.host or 'mặc định')}, "
            f"<code>{esc(e.dir)}</code>, nhánh <code>{esc(e.branch)}</code>, DB <code>{esc(e.db_name or '-')}</code>, "
            f"{health}, tự chữa: {'bật' if e.auto_heal and not is_prod(e) else 'tắt'}")
    return "\n".join(lines)


_ENV_KEYS = {"dir": "dir", "compose": "compose_args", "branch": "branch", "nhanh": "branch", "nhánh": "branch",
             "health": "health_url", "db": "db_name", "kind": "kind", "loai": "kind", "loại": "kind",
             "host": "host", "port": "port", "user": "ssh_user", "heal": "auto_heal", "note": "note"}
_FIELD = re.compile(r"([A-Za-zÀ-ỹ_]+)\s*=\s*(\"([^\"]*)\"|'([^']*)'|\S+)")


def parse_env_fields(rest: str) -> tuple[dict, str]:
    """`dir=~/x compose="-f a.yml" branch=erp-v2 health=https://… db=x kind=preview heal=on` → (cột, lỗi)."""
    out: dict = {}
    for m in _FIELD.finditer(rest or ""):
        key = _ENV_KEYS.get(m.group(1).lower())
        if key is None:
            return {}, f"không hiểu khóa «{m.group(1)}» (dùng: dir, compose, branch, health, db, kind, host, port, user, heal, note)"
        val = m.group(3) if m.group(3) is not None else (m.group(4) if m.group(4) is not None else m.group(2))
        out[key] = val.strip()
    if "kind" in out:
        kinds = {v: k for k, v in ENV_KIND_LABELS.items()}
        if out["kind"].lower() not in kinds:
            return {}, "kind chỉ nhận dev / prod / preview"
        out["kind"] = kinds[out["kind"].lower()]
    if "auto_heal" in out:
        out["auto_heal"] = out["auto_heal"].lower() in ("on", "bat", "bật", "1", "true", "co", "có")
    if "port" in out:
        if not out["port"].isdigit():
            return {}, "port phải là số"
        out["port"] = int(out["port"])
    for key in ("dir",):
        if key in out and not _PATHLIKE.match(out[key]):
            return {}, f"{key} có ký tự lạ"
    if "compose_args" in out and not _COMPOSE_ARGS.match(out["compose_args"]):
        return {}, "compose có ký tự lạ (chỉ chữ, số, - _ . / = và dấu cách)"
    if "branch" in out and not re.match(r"^[A-Za-z0-9._/-]{1,80}$", out["branch"]):
        return {}, "branch có ký tự lạ"
    if "db_name" in out and not re.match(r"^[A-Za-z0-9_]{1,64}$", out["db_name"]):
        return {}, "db có ký tự lạ"
    if "host" in out and not re.match(r"^[A-Za-z0-9.-]{1,255}$", out["host"]):
        return {}, "host có ký tự lạ"
    if "ssh_user" in out and not re.match(r"^[a-z_][a-z0-9_-]{0,31}$", out["ssh_user"]):
        return {}, "user có ký tự lạ"
    if "health_url" in out and not re.match(r"^https?://[^\s'\"]{3,250}$", out["health_url"]):
        return {}, "health phải là địa chỉ http(s)"
    return out, ""


def add_env(db: Session, name: str, fields: dict) -> AgentEnv:
    name = (name or "").strip().lower()
    if not _ENV_NAME.match(name):
        raise ValueError("tên môi trường chỉ gồm chữ thường không dấu, số, gạch nối")
    if env_by_name(db, name) is not None:
        raise ValueError(f"đã có môi trường «{name}»")
    if not fields.get("dir") or not fields.get("branch"):
        raise ValueError("thiếu dir hoặc branch")
    row = AgentEnv(name=name, kind=int(fields.get("kind") or ENV_PREVIEW), created_by=0, updated_by=0,
                   **{k: v for k, v in fields.items() if k != "kind"})
    db.add(row)
    db.commit()
    return row


# ---------------------------------------------------------------------------
# Thao tác (V-02, V-03)
# ---------------------------------------------------------------------------
def needs_approval(env: AgentEnv, kind: int) -> bool:
    """Luật đại ca chốt 05/10, đọc từ `policy.py`: xem dev tự do; xem prod / sửa bất kỳ đâu = «đúng».
    Bước tra để soạn lệnh sửa dữ liệu (OP_DATA_PLAN) làm luôn ở mọi môi trường (policy.DATA_PLAN_READ)."""
    from . import policy

    if kind == OP_DATA_PLAN:
        return policy.DATA_PLAN_READ != policy.ACT
    rw = "read" if kind in OP_READ_KINDS else "write"
    return policy.ops_rule(rw, ENV_KIND_LABELS.get(int(env.kind or 0), "prod")) != policy.ACT


def describe_action(env: AgentEnv, action: str, services: list[str]) -> str:
    svcs = " ".join(services)
    c = f"docker compose {env.compose_args}".rstrip()
    return {
        "restart_services": f"{c} restart {svcs}",
        "up_services": f"{c} up -d {svcs}",
        "build_services": f"{c} up -d --build {svcs}",
        "prune_build_cache": "docker builder prune -f --filter until=24h && docker image prune -f --filter until=24h",
        "rollback_last_deploy": "deploy.sh về commit trước lần deploy gần nhất của bot",
    }.get(action, action)


def new_op(db: Session, env: AgentEnv, kind: int, *, title: str, command: str, params: dict | None = None,
           chat_id: str = "", auto: bool = False, incident_id: int = 0) -> AgentOp:
    """Ghi sổ TRƯỚC khi chạy. Tự chữa (auto) và loại chỉ đọc trên dev vào thẳng «chờ máy»; còn lại «chờ duyệt»."""
    queued = auto or not needs_approval(env, kind)
    op = AgentOp(env_id=env.id, kind=kind, status=OPS_QUEUED if queued else OPS_WAITING, title=title[:255],
                 command=command or "", params=params or {}, undo_params={}, chat_id=str(chat_id or "")[:50],
                 auto=bool(auto), incident_id=incident_id, approved_at=now_utc() if queued else None,
                 output="", error="", backup_ref="", created_by=0, updated_by=0)
    db.add(op)
    db.commit()
    return op


def ops_queue(db: Session) -> str | None:
    """Hàng đợi của máy được thao tác VPS: máy có cờ deploy (có khóa SSH), ưu tiên máy đang bật.
    Sổ máy trống (bot + runner chung máy) → hàng đợi cũ. Có máy mà không máy nào được deploy → None."""
    rows = runners.active(db)
    if not rows:
        return runners.LEGACY_QUEUE
    able = [r for r in rows if r.can_deploy]
    if not able:
        return None
    online = [r for r in able if runners.is_online(r)]
    return runners.queue_name((online or able)[0].name)


def _send_task(db: Session, name: str, args: list) -> bool:
    queue = ops_queue(db)
    if queue is None:
        return False
    from app.core.celery_app import celery_app

    celery_app.send_task(name, args=args, queue=queue)
    return True


def dispatch_op(db: Session, op: AgentOp) -> bool:
    if not _send_task(db, "agent.run_op", [op.id]):
        op.status = OPS_FAILED
        op.error = "không có máy sửa mã nào được deploy (có khóa SSH lên VPS)"
        op.finished_at = now_utc()
        db.commit()
        return False
    return True


def format_rows(out: str, *, limit: int = 5) -> list[str]:
    """Kết quả SQL đọc (dòng `COLS=[...]` + mỗi dòng một mảng JSON) → vài dòng chữ «cột: giá trị · …»."""
    cols: list = []
    rows: list[str] = []
    for line in (out or "").splitlines():
        line = line.strip()
        if line.startswith("COLS="):
            try:
                cols = json.loads(line[5:])
            except ValueError:
                cols = []
            continue
        if cols and line.startswith("["):
            try:
                vals = json.loads(line)
            except ValueError:
                continue
            rows.append(" · ".join(f"{c}: {'' if v is None else v}" for c, v in zip(cols, vals)))
    return rows[:limit]


def start_data_change(db: Session, chat_id: str, text: str, env_name: str = "") -> str:
    """Đại ca nhờ sửa dữ liệu bằng lời → ghi sổ một lượt soạn lệnh (chỉ đọc, làm luôn) và giao máy sửa mã."""
    env = env_by_name(db, env_name or "dev") or env_by_name(db, "dev")
    if env is None:
        return "Sổ môi trường chưa có dev."
    op = new_op(db, env, OP_DATA_PLAN, title=f"Soạn lệnh: {text[:200]}", command=text,
                params={"request": text[:2000]}, chat_id=chat_id)
    if not dispatch_op(db, op):
        return f"Không giao được cho máy sửa mã: {op.error}."
    return (f"Dạ, em tra dữ liệu trên <b>{telegram.esc(env.name)}</b> để soạn lệnh · thao tác #{op.id}\n"
            "<i>Vài phút em gửi thẻ ghi rõ sẽ đổi gì, bao nhiêu dòng để đại ca duyệt.</i>")


def _env_badge(env: AgentEnv) -> str:
    return "<b>PROD</b> (dữ liệu thật)" if is_prod(env) else f"<b>{telegram.esc(env.name)}</b>"


def _answer_line(op: AgentOp) -> str:
    return (f"Nhắn <b>đúng</b> để chạy · <b>thôi</b> để bỏ\n"
            f"<i>Quá 15 phút thì nhắn «chạy thao tác #{op.id}».</i>")


def _plain_card(op: AgentOp, env: AgentEnv) -> str:
    """Thẻ duyệt cho lệnh sửa dữ liệu bằng lời (ai-CR-073/075): tiếng Việt, nhãn đậm, KHÔNG bày câu SQL
    (xem bằng «thao tác #n»). Bố cục: tiêu đề · sẽ làm · số dòng · ví dụ · giả định · an toàn · cách trả lời."""
    esc = telegram.esc
    p = op.params or {}
    blocks = [f"<b>SỬA DỮ LIỆU</b> trên {_env_badge(env)} · thao tác #{op.id}",
              f"<b>Sẽ làm:</b> {esc(op.title)}\n<b>Số dòng đổi:</b> {int(p.get('rows') or 0)}"]
    sample = [r for r in (p.get("sample") or []) if r]
    if sample:
        blocks.append("<b>Ví dụ đang là:</b>\n" + "\n".join(f"• {esc(r[:160])}" for r in sample[:3]))
    notes = [str(a) for a in (p.get("assumptions") or [])[:2] if str(a).strip()]
    if notes:
        blocks.append("\n".join(f"<i>Em hiểu là: {esc(a[:200])}</i>" for a in notes))
    blocks.append(f"<b>An toàn:</b> sao lưu phần dữ liệu này trước khi chạy.\n"
                  f"<i>Muốn trả lại như cũ: «hoàn tác thao tác #{op.id}».</i>")
    if is_prod(env):
        blocks.append("<i>OTP cho prod tạm bỏ qua theo lệnh đại ca 05/10.</i>")
    blocks.append(_answer_line(op))
    return "\n\n".join(blocks)


def _card(op: AgentOp, env: AgentEnv) -> str:
    if (op.params or {}).get("plain"):
        return _plain_card(op, env)
    esc = telegram.esc
    blocks = [f"<b>{esc(OP_KIND_LABELS.get(op.kind, 'thao tác').upper())}</b> trên {_env_badge(env)} · thao tác #{op.id}",
              f"<b>Sẽ làm:</b> {esc(op.title)}",
              f"<b>Lệnh:</b>\n<pre>{esc(op.command[:1500])}</pre>"]
    safety = ""
    if op.kind == OP_SQL_WRITE:
        _, _, tables = guardrails.classify_sql(op.command)
        safety = (f"<b>An toàn:</b> sao lưu bảng <code>{esc(', '.join(tables))}</code> trước khi chạy.\n"
                  f"<i>Hoàn tác «hoàn tác thao tác #{op.id}» nạp lại bản sao lưu — thay đổi khác lên các bảng này sau "
                  "lúc sao lưu cũng mất.</i>")
    elif op.kind == OP_RESTORE:
        safety = "<b>An toàn:</b> sao lưu trạng thái hiện tại trước khi nạp lại, để hoàn tác được cả lượt này."
    elif op.kind == OP_DEPLOY:
        safety = ("<b>An toàn:</b> một lượt một lúc · commit phải nằm trên nhánh của môi trường · health hỏng thì tự quay "
                  "về bản trước" + (" · sao lưu CẢ DB prod trước" if is_prod(env) else "") + ".\n"
                  f"<i>Hoàn tác: «hoàn tác thao tác #{op.id}» deploy lại commit trước.</i>")
    elif op.kind == OP_SHELL_WRITE:
        safety = "<b>Lưu ý:</b> lệnh tự do — <i>không có cách hoàn tác tự động</i>, em chỉ ghi nhật ký kết quả."
    if safety:
        blocks.append(safety)
    if is_prod(env):
        blocks.append("<i>OTP cho prod tạm bỏ qua theo lệnh đại ca 05/10.</i>")
    blocks.append(_answer_line(op))
    return "\n\n".join(blocks)


def ask_approval(db: Session, chat_id: str, op: AgentOp, env: AgentEnv, *, lead: str = "") -> None:
    from . import service

    service.reply(db, chat_id, (lead + "\n\n" if lead else "") + _card(op, env), action=ACT_OPS)
    service.log_message(db, DIR_OUT, chat_id, 0, json.dumps({"op_id": op.id}), action=ACT_OP_WAIT)
    db.commit()


def approve(db: Session, op: AgentOp, chat_id: str) -> str:
    if op.status != OPS_WAITING:
        return f"Thao tác #{op.id} đang ở trạng thái «{OP_STATUS_LABELS.get(op.status, '?')}», không chạy lại được."
    if op.created_at and now_utc() - op.created_at > OP_EXPIRE:
        op.status = OPS_CANCELLED
        op.error = "quá 24 giờ chưa duyệt"
        db.commit()
        return f"Thao tác #{op.id} quá 24 giờ rồi, em bỏ. Ra lệnh lại giúp em."
    op.status = OPS_QUEUED
    op.approved_at = now_utc()
    op.chat_id = op.chat_id or chat_id
    db.commit()
    if not dispatch_op(db, op):
        return f"Thao tác #{op.id}: {op.error}."
    return f"Dạ, em chạy thao tác #{op.id}. Xong em báo."


def cancel(db: Session, op: AgentOp) -> str:
    if op.status != OPS_WAITING:
        return f"Thao tác #{op.id} không còn chờ duyệt."
    op.status = OPS_CANCELLED
    op.finished_at = now_utc()
    db.commit()
    return f"Dạ, bỏ thao tác #{op.id}."


def undo(db: Session, op: AgentOp, chat_id: str) -> tuple[AgentOp | None, str]:
    """Hoàn tác = một dòng MỚI theo `undo_params` của dòng cũ, cũng qua cổng «đúng»."""
    env = db.get(AgentEnv, op.env_id)
    up = dict(op.undo_params or {})
    if env is None:
        return None, "Môi trường của thao tác đó không còn trong sổ."
    if op.status != OPS_OK or not up:
        return None, f"Thao tác #{op.id} không có gì để hoàn tác (chưa chạy xong, hoặc loại thao tác không hoàn tác được)."
    if op.undone_by_op_id:
        return None, f"Thao tác #{op.id} đã được hoàn tác bằng #{op.undone_by_op_id} rồi."
    kind = int(up.get("kind") or 0)
    if kind == OP_RESTORE:
        new = AgentOp(env_id=env.id, kind=OP_RESTORE, status=OPS_WAITING, title=f"Hoàn tác #{op.id}: nạp lại bản sao lưu",
                      command=f"nạp lại {up.get('path')} vào DB {env.db_name} (bảng {', '.join(up.get('tables') or [])})",
                      params={"path": up.get("path"), "tables": up.get("tables") or []}, undo_params={},
                      undo_of_op_id=op.id, chat_id=chat_id, output="", error="", backup_ref="", created_by=0, updated_by=0)
    elif kind == OP_DEPLOY:
        commit = str(up.get("commit") or "")
        svcs = [s for s in (up.get("services") or []) if _SERVICE.match(s)]
        new = AgentOp(env_id=env.id, kind=OP_DEPLOY, status=OPS_WAITING, title=f"Hoàn tác #{op.id}: deploy lại {commit[:10]}",
                      command=f"deploy.sh {env.name} {commit} {' '.join(svcs)}".strip(),
                      params={"commit": commit, "services": svcs}, undo_params={}, undo_of_op_id=op.id, chat_id=chat_id,
                      output="", error="", backup_ref="", created_by=0, updated_by=0)
    else:
        return None, f"Thao tác #{op.id} không hoàn tác tự động được."
    db.add(new)
    db.flush()
    op.undone_by_op_id = new.id
    db.commit()
    return new, ""


def _fmt_time(dt: datetime | None) -> str:
    from .timeutil import LOCAL_OFFSET

    return (dt + LOCAL_OFFSET).strftime("%d/%m %H:%M") if dt else "-"


def op_listing(db: Session, env: AgentEnv | None = None, *, deploy_only: bool = False, limit: int = 10) -> str:
    esc = telegram.esc
    q = select(AgentOp)
    if env is not None:
        q = q.where(AgentOp.env_id == env.id)
    if deploy_only:
        q = q.where(AgentOp.kind == OP_DEPLOY)
    rows = list(db.scalars(q.order_by(AgentOp.id.desc()).limit(limit)))
    if not rows:
        return "Chưa có thao tác nào trong sổ."
    names = {e.id: e.name for e in db.scalars(select(AgentEnv))}
    lines = ["<b>" + ("Lịch sử deploy" if deploy_only else "Lịch sử thao tác") + "</b> (mới nhất trước):"]
    for o in rows:
        extra = ""
        if o.kind == OP_DEPLOY:
            p = o.params or {}
            extra = f" {str(p.get('prev') or '')[:7]}→{str(p.get('head') or p.get('commit') or '')[:7]}"
        lines.append(f"• #{o.id} {_fmt_time(o.created_at)} <b>{esc(names.get(o.env_id, '?'))}</b> "
                     f"{esc(OP_KIND_LABELS.get(o.kind, '?'))}: {esc(o.title[:70])}{esc(extra)} — "
                     f"{esc(OP_STATUS_LABELS.get(o.status, '?'))}" + (" (tự chạy)" if o.auto else "")
                     + (f" · đã hoàn tác bằng #{o.undone_by_op_id}" if o.undone_by_op_id else ""))
    lines.append("Xem chi tiết: «thao tác #n».")
    return "\n".join(lines)


def op_detail(db: Session, op: AgentOp) -> str:
    esc = telegram.esc
    env = db.get(AgentEnv, op.env_id)
    lines = [f"<b>Thao tác #{op.id}</b> trên <b>{esc(env.name if env else '?')}</b> "
             f"({esc(OP_KIND_LABELS.get(op.kind, '?'))}) — {esc(OP_STATUS_LABELS.get(op.status, '?'))}",
             esc(op.title), f"<pre>{esc(op.command[:800])}</pre>",
             f"Tạo {_fmt_time(op.created_at)} · duyệt {_fmt_time(op.approved_at)} · xong {_fmt_time(op.finished_at)}"
             + (" · bot tự chạy" if op.auto else "")]
    if op.backup_ref:
        lines.append(f"Sao lưu: <code>{esc(op.backup_ref)}</code>")
    if op.error:
        lines.append("Lỗi: " + esc(op.error[:400]))
    if op.output:
        lines.append(f"<pre>{esc(op.output[-1500:])}</pre>")
    if op.undo_params and op.status == OPS_OK and not op.undone_by_op_id:
        lines.append(f"Hoàn tác: «hoàn tác thao tác #{op.id}».")
    return "\n".join(lines)


def incident_listing(db: Session, env: AgentEnv | None = None, *, limit: int = 10) -> str:
    esc = telegram.esc
    q = select(AgentIncident)
    if env is not None:
        q = q.where(AgentIncident.env_id == env.id)
    rows = list(db.scalars(q.order_by(AgentIncident.id.desc()).limit(limit)))
    if not rows:
        return "Chưa có sự cố nào trong sổ."
    names = {e.id: e.name for e in db.scalars(select(AgentEnv))}
    lines = ["<b>Sổ sự cố</b> (mới nhất trước):"]
    for i in rows:
        dur = ""
        if i.resolved_at and i.started_at:
            dur = f", gián đoạn ~{int((i.resolved_at - i.started_at).total_seconds() // 60)} phút"
        lines.append(f"• #{i.id} {_fmt_time(i.started_at)} <b>{esc(names.get(i.env_id, '?'))}</b>: {esc(i.symptom)} — "
                     f"{esc(INC_STATUS_LABELS.get(i.status, '?'))}{dur}"
                     + (f"; nguyên nhân: {esc(i.cause)}" if i.cause else "")
                     + (f"; đã làm: {esc(i.action)}" if i.action and i.action != "none" else "")
                     + (f"; thao tác #{i.heal_op_id}" if i.heal_op_id else ""))
    return "\n".join(lines)


def activity_text(db: Session) -> str:
    """Phần «việc của bot» trong báo tài nguyên (V-06)."""
    since = now_utc() - timedelta(hours=24)
    open_tasks = int(db.scalar(select(func.count(AgentTask.id)).where(AgentTask.status.notin_(CLOSED_STATUSES))) or 0)
    new_tasks = int(db.scalar(select(func.count(AgentTask.id)).where(AgentTask.created_at >= since)) or 0)
    claude = int(db.scalar(select(func.count(AgentRun.id)).where(AgentRun.started_at >= since,
                                                                 AgentRun.provider == "claude_code")) or 0)
    gemini = int(db.scalar(select(func.count(AgentRun.id)).where(AgentRun.started_at >= since,
                                                                 AgentRun.provider != "claude_code")) or 0)
    stuck = int(db.scalar(select(func.count(AgentRun.id)).where(
        AgentRun.status == RUN_RUNNING, AgentRun.started_at < now_utc() - timedelta(hours=2))) or 0)
    ops_n = int(db.scalar(select(func.count(AgentOp.id)).where(AgentOp.created_at >= since)) or 0)
    inc_open = int(db.scalar(select(func.count(AgentIncident.id)).where(AgentIncident.status != INC_RESOLVED)) or 0)
    inc_day = int(db.scalar(select(func.count(AgentIncident.id)).where(AgentIncident.started_at >= since)) or 0)
    online = sum(1 for r in runners.active(db) if runners.is_online(r))
    return ("<b>Việc của bot (24 giờ qua)</b>\n"
            f"Việc đang mở {open_tasks} · việc mới {new_tasks} · lượt Claude {claude} · lượt Gemini {gemini}"
            + (f" · <b>{stuck} lượt kẹt quá 2 giờ</b>" if stuck else "") + "\n"
            f"Thao tác VPS {ops_n} · sự cố mới {inc_day} · sự cố chưa hết {inc_open} · máy sửa mã đang bật {online}")


# ---------------------------------------------------------------------------
# Sự cố lặp lại → việc sửa gốc rễ (O-06)
# ---------------------------------------------------------------------------
def maybe_root_cause_task(db: Session, incident: AgentIncident, diag: dict) -> str:
    if not incident.signature or (incident.cause or "").strip().lower() in ("", "không rõ", "khong ro"):
        return ""
    since = now_utc() - REPEAT_WINDOW
    same = list(db.scalars(select(AgentIncident).where(AgentIncident.signature == incident.signature,
                                                        AgentIncident.started_at >= since)))
    if len(same) < REPEAT_MIN:
        return ""
    existing = next((i.task_id for i in same if i.task_id), 0)
    if existing:
        task = db.get(AgentTask, existing)
        if task is not None and task.status not in CLOSED_STATUSES:
            incident.task_id = existing
            db.commit()
            return f"Sự cố này lặp lại {len(same)} lần trong 7 ngày; việc sửa gốc rễ <b>{telegram.esc(task.code)}</b> đang mở."
    from . import service

    if service._quota_left(db) <= 0:
        return f"Sự cố này lặp lại {len(same)} lần trong 7 ngày; chạm trần việc/ngày nên em chưa mở việc sửa gốc rễ."
    env = db.get(AgentEnv, incident.env_id)
    summary = "\n".join([
        f"Sự cố lặp lại {len(same)} lần trong 7 ngày trên môi trường {env.name if env else '?'} "
        f"(các sự cố #{', #'.join(str(i.id) for i in same)}).",
        f"Triệu chứng: {incident.symptom}.",
        f"Nguyên nhân khả dĩ: {incident.cause}.",
        f"Gợi ý gốc rễ: {diag.get('fix_hint') or 'chưa có — rà soát mã để tìm'}.",
        "Mỗi lần bot đã tự chữa tạm (khởi động lại / quay về bản trước). Việc này là sửa GỐC RỄ trong mã để sự cố không lặp lại.",
        "",
        "Chẩn đoán lần gần nhất:",
        (incident.diagnosis or "")[:3000],
    ])
    task = AgentTask(code=service.next_code(db), title=f"Sự cố lặp lại: {incident.cause}"[:255], source=SRC_INCIDENT,
                     status=ST_TRIAGE, summary=summary, risk_level=RISK_MEDIUM, created_by=0, updated_by=0)
    db.add(task)
    db.flush()
    for i in same:
        i.task_id = task.id
    db.commit()
    try:
        service.start_scan(db, task)
        db.commit()
    except Exception:  # noqa: BLE001 — mở việc được là đủ, rà soát lỗi thì đại ca giao lại
        log.exception("agent_hub.ops: giao rà soát việc sửa gốc rễ hỏng")
    return (f"Sự cố này lặp lại {len(same)} lần trong 7 ngày — em mở việc <b>{telegram.esc(task.code)}</b> để sửa gốc rễ "
            "(đi đường thường: rà soát → kế hoạch → đại ca duyệt).")


# ---------------------------------------------------------------------------
# Theo dõi sức khỏe (O-01) — vòng beat mỗi phút ở worker của bot
# ---------------------------------------------------------------------------
def _fetch_code(url: str) -> int:
    import requests

    try:
        return requests.get(url, timeout=10).status_code
    except requests.RequestException:
        return 0


def open_incident(db: Session, env: AgentEnv) -> AgentIncident | None:
    return db.scalar(select(AgentIncident).where(AgentIncident.env_id == env.id, AgentIncident.status != INC_RESOLVED)
                     .order_by(AgentIncident.id.desc()).limit(1))


def check_health(db: Session, *, fetch=None, now: datetime | None = None) -> dict:
    from . import service

    fetch = fetch or _fetch_code
    now = now or now_utc()
    streak = max(1, int(settings.AGENT_HEALTH_FAIL_STREAK or 3))
    esc = telegram.esc
    opened = resolved = 0
    for env in active_envs(db):
        if not env.health_url:
            continue
        code = int(fetch(env.health_url) or 0)
        env.last_health_code = code
        env.last_health_at = now
        cur = open_incident(db, env)
        if code == 200:
            env.fail_streak = 0
            #  Đang tự chữa thì để máy sửa mã tự đóng (nó báo kèm kết quả thao tác) — trừ khi kẹt quá 30 phút.
            healing = cur is not None and cur.status == INC_HEALING and \
                (now - (cur.started_at or now)) < timedelta(minutes=30)
            if cur is not None and not healing:
                cur.status = INC_RESOLVED
                cur.resolved_at = now
                resolved += 1
                mins = int((now - (cur.started_at or now)).total_seconds() // 60)
                service.reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
                              f"Sự cố #{cur.id} trên <b>{esc(env.name)}</b> đã hết: health 200 trở lại "
                              f"(gián đoạn ~{mins} phút).", action=ACT_OPS)
            continue
        env.fail_streak = int(env.fail_streak or 0) + 1
        if env.fail_streak < streak or cur is not None:
            continue
        symptom = f"health {code}" if code else "health không kết nối được"
        inc = AgentIncident(env_id=env.id, status=INC_DIAGNOSING, symptom=f"{symptom} ({streak} phút liền)",
                            signature="", started_at=now - timedelta(minutes=streak - 1), diagnosis="", cause="",
                            action="", created_by=0, updated_by=0)
        db.add(inc)
        db.flush()
        opened += 1
        sent = _send_task(db, "agent.diagnose_incident", [inc.id])
        if not sent:
            inc.status = INC_WAITING
        service.reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
                      f"<b>Sự cố #{inc.id}</b>: <b>{esc(env.name)}</b> {esc(inc.symptom)}. "
                      + ("Em đang gom log để chẩn đoán." if sent else
                         "Không có máy sửa mã nào được thao tác VPS để chẩn đoán — cần đại ca xem."), action=ACT_OPS)
    db.commit()
    return {"opened": opened, "resolved": resolved}


STUCK_AFTER = timedelta(minutes=5)
STUCK_NOTE = "máy sửa mã chưa nhận sau 5 phút"


def remind_stuck_ops(db: Session, *, now: datetime | None = None) -> int:
    """Thao tác đã duyệt mà nằm «chờ máy» quá 5 phút → báo đại ca MỘT lần (05/10: máy sửa mã thiếu quyền DB
    nên nhận vé rồi chết lặng, đại ca chờ mà không ai báo). Dấu đã báo = `error` ghi STUCK_NOTE."""
    from . import service

    now = now or now_utc()
    rows = list(db.scalars(select(AgentOp).where(AgentOp.status == OPS_QUEUED, AgentOp.error == "",
                                                 AgentOp.approved_at < now - STUCK_AFTER)))
    for op in rows:
        op.error = STUCK_NOTE
        service.reply(db, op.chat_id or settings.AGENT_TELEGRAM_CHAT_ID,
                      f"Thao tác <b>#{op.id}</b> ({telegram.esc(op.title[:80])}) đã duyệt hơn 5 phút mà máy sửa mã chưa "
                      "nhận hoặc nhận rồi hỏng trước khi ghi được kết quả. Máy có thể đang tắt, mất đường hầm, hoặc thiếu "
                      "quyền DB — em đang chờ; «máy nào đang bật» để xem máy.", action=ACT_OPS)
    if rows:
        db.commit()
    return len(rows)


def dispatch_resource_report(db: Session, chat_id: str = "") -> bool:
    return _send_task(db, "agent.resource_report", [chat_id])


# ---------------------------------------------------------------------------
# Câu nhắn của đại ca
# ---------------------------------------------------------------------------
_TAIL = r"(\s+(nhé|nha|đi|luôn|giúp em|giúp anh|giùm))*[.!?]*"
_P = {
    "env_list": re.compile(rf"^(sổ môi trường|danh sách môi trường|các môi trường|môi trường nào|môi trường){_TAIL}$"),
    "env_add": re.compile(r"^thêm môi trường\s+(?P<name>[a-z0-9-]+)\s*:?\s*(?P<rest>.*)$", re.DOTALL),
    "env_remove": re.compile(rf"^(gỡ|xóa|bỏ) môi trường\s+(?P<name>[a-z0-9-]+){_TAIL}$"),
    "heal": re.compile(rf"^(?P<on>bật|tắt) tự chữa\s+(?P<env>[a-z0-9-]+){_TAIL}$"),
    "resources": re.compile(rf"^(tình hình máy|tình hình vps|tài nguyên( máy)?|báo tài nguyên){_TAIL}$"),
    "status": re.compile(rf"^(trạng thái|tình trạng)\s+(?P<env>[a-z0-9-]+){_TAIL}$"),
    "logs": re.compile(rf"^(xem\s+)?log\s+(?P<svc>[a-z0-9_.-]+)(\s+(trên|của)?\s*(?P<env>[a-z0-9-]+))?(\s+(?P<n>\d+)(\s+dòng)?)?{_TAIL}$"),
    "restart": re.compile(rf"^(khởi động lại|restart)\s+(?P<svcs>[a-z0-9_. -]+?)\s+(trên\s+)?(?P<env>[a-z0-9-]+){_TAIL}$"),
    "build": re.compile(rf"^(dựng lại|build lại|rebuild)\s+(?P<svcs>[a-z0-9_. -]+?)\s+(trên\s+)?(?P<env>[a-z0-9-]+){_TAIL}$"),
    "prune": re.compile(rf"^dọn bộ đệm( build)?\s+(trên\s+)?(?P<env>[a-z0-9-]+){_TAIL}$"),
    "deploy": re.compile(rf"^deploy\s+(?P<env>[a-z0-9-]+)\s+(?P<commit>[0-9a-f]{{7,40}}|latest|bản mới nhất|mới nhất)"
                         rf"(\s+(?P<svcs>[a-z0-9_. -]+?))?{_TAIL}$"),
    "rollback": re.compile(rf"^(quay về bản trước|rollback)\s+(?P<env>[a-z0-9-]+){_TAIL}$"),
    "diagnose": re.compile(r"^(chẩn đoán|kiểm tra)\s+(?P<env>[a-z0-9-]+)\s*(:\s*(?P<q>.+))?$", re.DOTALL),
    "history": re.compile(rf"^lịch sử (?P<what>thao tác|deploy)(\s+(?P<env>[a-z0-9-]+))?{_TAIL}$"),
    "detail": re.compile(rf"^(xem\s+)?thao tác\s+#?(?P<n>\d+){_TAIL}$"),
    "undo": re.compile(rf"^hoàn tác(\s+thao tác)?\s+#?(?P<n>\d+){_TAIL}$"),
    "approve_id": re.compile(rf"^(đúng|chạy|duyệt)\s+thao tác\s+#?(?P<n>\d+){_TAIL}$"),
    "cancel_id": re.compile(rf"^(bỏ|hủy|thôi)\s+thao tác\s+#?(?P<n>\d+){_TAIL}$"),
    "incidents": re.compile(rf"^(sổ sự cố|các sự cố|lịch sử sự cố|sự cố)(\s+(?P<env>[a-z0-9-]+))?{_TAIL}$"),
}
#  SQL / shell giữ NGUYÊN chữ hoa-thường của đại ca, nên khớp trên chữ gốc (không hạ chữ).
_SQL = re.compile(r"^\s*sql\s+(?P<env>[A-Za-z0-9-]+)\s*:\s*(?P<body>.+)$", re.DOTALL | re.IGNORECASE)
_SHELL = re.compile(r"^\s*(chạy|shell)\s+(?P<env>[A-Za-z0-9-]+)\s*:\s*(?P<body>.+)$", re.DOTALL | re.IGNORECASE)


def parse(text: str) -> dict | None:
    raw = (text or "").strip()
    if m := _SQL.match(raw):
        return {"op": "sql", "env": m.group("env").lower(), "body": m.group("body").strip()}
    if m := _SHELL.match(raw):
        return {"op": "shell", "env": m.group("env").lower(), "body": m.group("body").strip()}
    low = re.sub(r"\s+", " ", raw.lower())
    if re.search(r"\bai[-\s]?\d+\b", low):
        return None      # lệnh trên một VIỆC («deploy dev AI-0007») — để đường cũ xử
    for op, pat in _P.items():
        m = pat.match(low)
        if m:
            d = {k: v for k, v in m.groupdict().items() if v is not None}
            if op == "env_add":
                rest_m = re.match(r"^\s*thêm môi trường\s+[A-Za-z0-9-]+\s*:?\s*(.*)$", raw, re.DOTALL | re.IGNORECASE)
                d["rest"] = rest_m.group(1) if rest_m else d.get("rest", "")
            if op == "diagnose" and "q" in d:
                q_m = re.match(r"^[^:]*:\s*(.+)$", raw, re.DOTALL)
                d["q"] = q_m.group(1).strip() if q_m else d["q"]
            return {"op": op, **d}
    return None


_WAITS = (ACT_OP_WAIT, ACT_RUNNER_WAIT, ACT_GRANT_WAIT, ACT_GLOSS_WAIT)


def _pending(db: Session, chat_id: str, row: AgentMessage) -> AgentMessage | None:
    """Thẻ «đúng» thao tác còn sống, và là thẻ chờ MỚI NHẤT của chat (thẻ máy / cấp quyền mới hơn thì nhường)."""
    last = db.scalar(select(AgentMessage).where(AgentMessage.chat_id == chat_id, AgentMessage.action.in_(_WAITS),
                                                AgentMessage.id < row.id).order_by(AgentMessage.id.desc()).limit(1))
    if last is None or last.action != ACT_OP_WAIT:
        return None
    if row.created_at and last.created_at and row.created_at - last.created_at > CONFIRM_WINDOW:
        return None
    return last


def _split_services(raw: str) -> list[str]:
    return [s for s in re.split(r"[\s,]+|\bvà\b", raw or "") if s]


def handle_text(db: Session, chat_id: str, row: AgentMessage, text: str) -> bool:
    """Chat đại ca: lệnh sổ môi trường / thao tác VPS / sự cố. Trả True khi đã xử (tin đóng dấu lệnh)."""
    from . import service

    if not telegram.is_allowed_chat(chat_id):
        return False
    low = (text or "").strip().lower()
    pending = _pending(db, chat_id, row)
    if pending is not None and (service._YES.match(low) or service._NO.match(low)):
        row.action = ACT_COMMAND
        try:
            op_id = int(json.loads(pending.body or "{}").get("op_id") or 0)
        except ValueError:
            op_id = 0
        op = db.get(AgentOp, op_id)
        if op is None:
            pending.action = ACT_OP_DROPPED
            db.commit()
            return False
        yes = bool(service._YES.match(low))
        pending.action = ACT_OP_DONE if yes else ACT_OP_DROPPED
        db.commit()
        service.reply(db, chat_id, telegram.esc(approve(db, op, chat_id) if yes else cancel(db, op)), action=ACT_OPS)
        db.commit()
        return True

    parsed = parse(text)
    if parsed is None:
        return False
    op_name = parsed["op"]
    #  «hỏi/kiểm tra <tên lạ>», «log <x>» … mà tên môi trường không có trong sổ thì có thể là câu thường — trả lại.
    env_name = parsed.get("env") or ("dev" if op_name in ("logs",) else "")
    env = env_by_name(db, env_name) if env_name else None
    if op_name in ("diagnose", "logs", "status", "incidents", "history") and env_name and env is None:
        return False
    row.action = ACT_COMMAND
    esc = telegram.esc

    def say(msg: str) -> bool:
        service.reply(db, chat_id, msg, action=ACT_OPS)
        db.commit()
        return True

    if not enabled():
        return say("Thao tác VPS đang tắt (<code>AGENT_OPS_ENABLED=false</code> trong .env của bot).")

    if op_name == "env_list":
        return say(env_listing(db))
    if op_name == "env_add":
        fields, err = parse_env_fields(parsed.get("rest", ""))
        if err:
            return say(esc(err))
        try:
            new = add_env(db, parsed["name"], fields)
        except ValueError as e:
            return say(esc(str(e)))
        return say(f"Đã thêm môi trường <b>{esc(new.name)}</b> ({esc(ENV_KIND_LABELS.get(new.kind, '?'))}). "
                   "Kiểm thử: «trạng thái " + esc(new.name) + "».")
    if op_name == "env_remove":
        if env is None:
            return say(f"Không có môi trường <b>{esc(parsed['name'])}</b>.")
        if env.name in ("dev", "prod"):
            return say("dev và prod là hai môi trường gốc, em không gỡ bằng câu nhắn.")
        env.revoked_at = now_utc()
        db.commit()
        return say(f"Đã gỡ môi trường <b>{esc(env.name)}</b> khỏi sổ.")
    if op_name == "resources":
        ok = dispatch_resource_report(db, chat_id)
        return say("Dạ, em đang đọc tài nguyên các máy." if ok else
                   "Không có máy sửa mã nào được thao tác VPS (cờ deploy) để đọc tài nguyên.")
    if op_name == "history":
        return say(op_listing(db, env, deploy_only=parsed.get("what") == "deploy"))
    if op_name == "incidents":
        return say(incident_listing(db, env))
    if op_name in ("detail", "undo", "approve_id", "cancel_id"):
        op = db.get(AgentOp, int(parsed["n"]))
        if op is None:
            return say(f"Không có thao tác #{parsed['n']}.")
        if op_name == "detail":
            return say(op_detail(db, op))
        if op_name == "approve_id":
            return say(esc(approve(db, op, chat_id)))
        if op_name == "cancel_id":
            return say(esc(cancel(db, op)))
        new, err = undo(db, op, chat_id)
        if new is None:
            return say(esc(err))
        ask_approval(db, chat_id, new, db.get(AgentEnv, new.env_id))
        return True

    if env is None:
        return say(f"Không có môi trường <b>{esc(env_name or '?')}</b> trong sổ. Xem «môi trường».")

    if op_name == "heal":
        on = parsed["on"] == "bật"
        if on and is_prod(env):
            return say("Prod không bao giờ tự chữa — chỉ đề xuất chờ «đúng».")
        env.auto_heal = on
        db.commit()
        tail = "" if settings.AGENT_HEAL_ENABLED else " (công tắc tổng <code>AGENT_HEAL_ENABLED</code> đang tắt nên chưa chạy)"
        return say(f"Tự chữa trên <b>{esc(env.name)}</b>: {'BẬT' if on else 'TẮT'}{tail}.")

    if op_name == "status":
        op = new_op(db, env, OP_VIEW, title="Trạng thái container", command=f"docker compose {env.compose_args} ps -a",
                    params={"what": "status"}, chat_id=chat_id)
    elif op_name == "logs":
        svc = parsed["svc"]
        if not _SERVICE.match(svc):
            return say("Tên service lạ.")
        n = int(parsed.get("n") or 80)
        op = new_op(db, env, OP_VIEW, title=f"Log {svc} ({n} dòng)",
                    command=f"docker compose {env.compose_args} logs --tail {n} {svc}",
                    params={"what": "logs", "service": svc, "lines": n}, chat_id=chat_id)
    elif op_name == "diagnose":
        op = new_op(db, env, OP_VIEW, title="Chẩn đoán" + (f": {parsed.get('q', '')[:200]}" if parsed.get("q") else ""),
                    command="gom container / log / commit / migration / tài nguyên (chỉ đọc) → Claude chẩn đoán",
                    params={"what": "diagnose", "question": parsed.get("q", "")[:1000]}, chat_id=chat_id)
    elif op_name in ("restart", "build"):
        svcs = _split_services(parsed["svcs"])
        if not svcs or any(not _SERVICE.match(s) for s in svcs):
            return say("Tên service lạ.")
        action = "restart_services" if op_name == "restart" else "build_services"
        op = new_op(db, env, OP_ACTION, title=f"{'Khởi động lại' if op_name == 'restart' else 'Dựng lại'} {' '.join(svcs)}",
                    command=describe_action(env, action, svcs), params={"action": action, "services": svcs}, chat_id=chat_id)
    elif op_name == "prune":
        op = new_op(db, env, OP_ACTION, title="Dọn bộ đệm build", command=describe_action(env, "prune_build_cache", []),
                    params={"action": "prune_build_cache", "services": []}, chat_id=chat_id)
    elif op_name == "deploy":
        commit = parsed["commit"]
        commit = "latest" if commit in ("latest", "bản mới nhất", "mới nhất") else commit
        svcs = _split_services(parsed.get("svcs", ""))
        if any(not _SERVICE.match(s) for s in svcs):
            return say("Tên service lạ.")
        op = new_op(db, env, OP_DEPLOY, title=f"Deploy {commit[:10]}" + (f" ({' '.join(svcs)})" if svcs else ""),
                    command=f"deploy.sh {env.name} {commit} {' '.join(svcs)}".strip(),
                    params={"commit": commit, "services": svcs}, chat_id=chat_id)
    elif op_name == "rollback":
        op = new_op(db, env, OP_ACTION, title="Quay về bản trước lần deploy gần nhất của bot",
                    command=describe_action(env, "rollback_last_deploy", []),
                    params={"action": "rollback_last_deploy", "services": []}, chat_id=chat_id)
    elif op_name == "sql":
        kind, reason, _ = guardrails.classify_sql(parsed["body"])
        if kind == guardrails.SQL_DENIED:
            return say("Em không chạy câu này: " + esc(reason) + ".")
        op = new_op(db, env, OP_SQL_READ if kind == guardrails.SQL_READ else OP_SQL_WRITE,
                    title="SQL " + ("đọc" if kind == guardrails.SQL_READ else "sửa dữ liệu"), command=parsed["body"],
                    chat_id=chat_id)
    elif op_name == "shell":
        kind, reason = guardrails.classify_shell(parsed["body"])
        if kind == guardrails.SHELL_DENIED:
            return say("Em không chạy lệnh này: " + esc(reason) + ".")
        op = new_op(db, env, OP_SHELL_READ if kind == guardrails.SHELL_READ else OP_SHELL_WRITE,
                    title="Lệnh shell " + ("chỉ đọc" if kind == guardrails.SHELL_READ else f"có sửa ({reason})"),
                    command=parsed["body"], chat_id=chat_id)
    else:
        return False

    if op.status == OPS_WAITING:
        ask_approval(db, chat_id, op, env)
        return True
    if not dispatch_op(db, op):
        return say(f"Thao tác #{op.id}: {esc(op.error)}.")
    return say(f"Dạ, em xem <b>{esc(env.name)}</b> (thao tác #{op.id}), có kết quả em gửi liền.")
