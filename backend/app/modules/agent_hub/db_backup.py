"""Sao lưu DB của DỊCH VỤ AI (ai-CR-139, đại ca duyệt 09/10/2026 qua Agent 1).

Vì sao cần: khi bot chạy TÁCH DB (`AGENT_MODE=service`, DB `agent_hub`), `celery_app.py` chỉ giữ lịch tên `agent-*` và
chỉ nạp task của agent_hub — nên `backup.run` của ERP bị lọc mất, DB bot không có bản nào (72 giờ trên dev không chạy
lần nào). Mất DB là mất lịch sử chat, trí nhớ, sổ ý định, sổ việc AI-xxxx, liên kết Telegram / Zalo. Qdrant không sao lưu
vì dựng lại được từ DB + HDSD. Chế độ nhúng (`embedded`) thì bảng bot nằm trong DB ERP, bản sao lưu ERP đã gồm.

Bốn việc:
  · `run`          — mysqldump (dùng lại `backup.service`) → gzip → R2 `<env>/backup/<DB>-YYYYmmdd-HHMMSS.sql.gz` → ghi
                     `tab_agent_db_backup` → giữ `keep_count()` bản mới nhất. Hỏng thì báo ngay.
  · `watch`        — mỗi giờ: quá STALE_HOURS không có bản thành công thì báo (một lần mỗi 24 giờ; mới dựng thì chờ đủ
                     STALE_HOURS mới tính).
  · `restore_test` — mỗi tuần: nạp bản mới nhất vào DB tạm `<DB>_restore_test`, kiểm `alembic_version` + số bảng + đếm dòng
                     vài bảng chính so với DB đang chạy, rồi XÓA DB tạm (kể cả khi hỏng). Hỏng thì báo.
  · Báo = tin vận hành vào chat chủ bot, tự chép cho người có quyền `agent_ops` (`service.reply(..., action=ACT_OPS)`).

KHÔNG có đường khôi phục trên web. Quay lại DB: `backend/scripts/agent_restore.sh` (runbook ở doc/agent-hub/08 §sao lưu).
"""
from __future__ import annotations

import gzip
import io
import logging
import os
import subprocess
from datetime import datetime, timedelta
from enum import IntEnum

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import settings

from .model import AgentCursor, AgentDbBackup
from .timeutil import now_utc

log = logging.getLogger("app.agent_hub.db_backup")

STALE_HOURS = 26
ALERT_EVERY = timedelta(hours=24)
KEY_TABLES = ("alembic_version", "tab_agent_message", "tab_agent_task", "tab_agent_chat_link", "tab_agent_memory")
CURSOR_WATCH_SINCE = "agent_backup_watch_since"
CURSOR_STALE_ALERT = "agent_backup_stale_alert"
_EPOCH = datetime(1970, 1, 1)


def _epoch(dt: datetime) -> int:
    """Giờ UTC không múi → số giây (không dùng hàm timestamp của datetime: nó coi giờ không múi là giờ máy)."""
    return int((dt - _EPOCH).total_seconds())


def _from_epoch(v: int) -> datetime:
    return _EPOCH + timedelta(seconds=int(v))


class Kind(IntEnum):
    BACKUP = 1
    RESTORE_TEST = 2


class Source(IntEnum):
    AUTO = 1
    MANUAL = 2


class Status(IntEnum):
    RUNNING = 1
    SUCCESS = 2
    FAILED = 3


#  Mã chữ cho giao diện — cùng hình với `/api/backups` của ERP để màn Sao lưu dùng chung bảng.
STATUS_CODES = {Status.RUNNING: "running", Status.SUCCESS: "success", Status.FAILED: "failed"}
SOURCE_CODES = {Source.AUTO: "auto", Source.MANUAL: "manual"}
KIND_CODES = {Kind.BACKUP: "backup", Kind.RESTORE_TEST: "restore_test"}


def enabled() -> bool:
    """Chỉ chế độ dịch vụ AI tách DB mới có DB riêng để sao lưu."""
    return bool(settings.agent_is_service)


def db_name() -> str:
    return settings.DB_NAME


def restore_db_name() -> str:
    return f"{settings.DB_NAME}_restore_test"


def keep_count() -> int:
    from app.modules.backup.service import keep_count as erp_keep

    return erp_keep()


def object_key(started: datetime) -> str:
    from app.core.storage import env_prefix

    return f"{env_prefix()}/backup/{db_name()}-{started:%Y%m%d-%H%M%S}.sql.gz"


# ---------------------------------------------------------------------------
# Báo
# ---------------------------------------------------------------------------
def alert(db: Session, text_: str) -> None:
    """Tin vận hành: chat chủ bot + bản sao cho người có quyền agent_ops. Không có chat chủ thì chỉ ghi log."""
    log.warning("agent_hub: %s", text_)
    owner = str(settings.AGENT_TELEGRAM_CHAT_ID or "")
    if not owner:
        return
    try:
        from . import service
        from .constants import ACT_OPS

        service.reply(db, owner, text_, action=ACT_OPS)
        db.commit()
    except Exception:  # noqa: BLE001 — báo hỏng không được làm hỏng vòng sao lưu
        db.rollback()
        log.exception("agent_hub: không gửi được tin báo sao lưu")


def _cursor(db: Session, name: str) -> AgentCursor:
    row = db.scalar(select(AgentCursor).where(AgentCursor.name == name))
    if row is None:
        row = AgentCursor(name=name, value=0)
        db.add(row)
        db.flush()
    return row


# ---------------------------------------------------------------------------
# Sao lưu
# ---------------------------------------------------------------------------
def _prune(db: Session) -> int:
    from app.core.storage import delete_key

    olds = db.scalars(select(AgentDbBackup).where(AgentDbBackup.kind == Kind.BACKUP)
                      .order_by(AgentDbBackup.id.desc()).offset(keep_count())).all()
    for o in olds:
        if o.file_key:
            delete_key(o.file_key)
        db.delete(o)
    if olds:
        db.commit()
    return len(olds)


def run(db: Session, *, source: Source = Source.AUTO, actor_id: int = 0) -> AgentDbBackup:
    """Một lượt sao lưu DB bot. Hỏng thì ghi `failed` + báo, rồi ném lỗi cho task ghi kết quả."""
    from app.core.storage import is_remote_storage_ready, upload_fileobj
    from app.modules.backup.service import dump_sql

    started = now_utc()
    rec = AgentDbBackup(kind=Kind.BACKUP, source=int(source), status=Status.RUNNING, started_at=started, message="",
                        detail={}, created_by=actor_id, updated_by=actor_id)
    db.add(rec)
    db.commit()
    try:
        if not enabled():
            raise RuntimeError("bot đang chạy chung DB ERP — bản sao lưu ERP đã gồm bảng bot")
        if not is_remote_storage_ready():
            #  `upload_fileobj` thiếu R2 thì lùi về `uploads/` — thư mục phục vụ CÔNG KHAI. Sao lưu tuyệt đối không lùi.
            raise RuntimeError("chưa khai R2 cho dịch vụ AI — bản sao lưu không có chỗ cất")
        gz = gzip.compress(dump_sql(db_name()), compresslevel=6)
        key = object_key(started)
        upload_fileobj(io.BytesIO(gz), key, "application/gzip")
        rec.file_key, rec.size_bytes, rec.status, rec.finished_at = key, len(gz), Status.SUCCESS, now_utc()
        db.commit()
        _prune(db)
        return rec
    except Exception as e:
        db.rollback()
        r = db.get(AgentDbBackup, rec.id)
        if r is not None:
            r.status, r.message, r.finished_at = Status.FAILED, str(e)[:1000], now_utc()
            db.commit()
        alert(db, f"Sao lưu DB bot ({db_name()}) LỖI: {str(e)[:300]}")
        raise


def last_success(db: Session) -> AgentDbBackup | None:
    return db.scalar(select(AgentDbBackup).where(AgentDbBackup.kind == Kind.BACKUP, AgentDbBackup.status == Status.SUCCESS)
                     .order_by(AgentDbBackup.id.desc()).limit(1))


def watch(db: Session, *, now: datetime | None = None) -> dict:
    """Quá STALE_HOURS không có bản thành công → báo, tối đa một lần mỗi ALERT_EVERY."""
    if not enabled():
        return {"ok": True, "reason": "không tách DB"}
    now = now or now_utc()
    since = _cursor(db, CURSOR_WATCH_SINCE)
    if not since.value:
        since.value = _epoch(now)
        db.commit()
    ok = last_success(db)
    stale_from = (ok.finished_at or ok.started_at) if ok is not None else _from_epoch(since.value)
    if now - stale_from <= timedelta(hours=STALE_HOURS):
        return {"ok": True}
    sent = _cursor(db, CURSOR_STALE_ALERT)
    if sent.value and now - _from_epoch(sent.value) < ALERT_EVERY:
        return {"ok": False, "alerted": False}
    sent.value = _epoch(now)
    db.commit()
    hours = int((now - stale_from).total_seconds() // 3600)
    what = f"bản thành công gần nhất cách đây {hours} giờ" if ok is not None else "chưa có bản thành công nào"
    alert(db, f"Sao lưu DB bot ({db_name()}): đã quá {STALE_HOURS} giờ, {what}. Xem màn Sao lưu › DB bot.")
    return {"ok": False, "alerted": True}


# ---------------------------------------------------------------------------
# Khôi phục thử
# ---------------------------------------------------------------------------
def _mysql(sql: str = "", *, database: str = "", stdin: bytes | None = None) -> str:
    """Gọi client mysql/mariadb bằng thông số DB của dịch vụ. Mật khẩu qua biến môi trường, không lên dòng lệnh."""
    from shutil import which

    from app.modules.backup.service import _la_client_mariadb

    exe = "mysql" if which("mysql") else "mariadb"
    cmd = [exe, "--default-character-set=utf8mb4", "-N", "-B"]
    if _la_client_mariadb(exe):
        cmd.append("--ssl-verify-server-cert=0")
    cmd += ["-h", settings.DB_HOST, "-P", str(settings.DB_PORT), "-u", settings.DB_USER]
    if database:
        cmd.append(database)
    if sql:
        cmd += ["-e", sql]
    env = dict(os.environ)
    env["MYSQL_PWD"] = settings.DB_PASSWORD
    p = subprocess.run(cmd, env=env, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1800)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or b"").decode("utf-8", errors="ignore")[:400] or f"{exe} lỗi mã {p.returncode}")
    return (p.stdout or b"").decode("utf-8", errors="ignore").strip()


def _live_counts(db: Session) -> dict:
    out: dict = {"tables": int(db.execute(text(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = :s"), {"s": db_name()}).scalar() or 0)}
    for t in KEY_TABLES[1:]:
        try:
            out[t] = int(db.execute(text(f"SELECT COUNT(*) FROM `{t}`")).scalar() or 0)
        except Exception:  # noqa: BLE001
            db.rollback()
            out[t] = None
    try:
        out["alembic_version"] = str(db.execute(text("SELECT version_num FROM alembic_version")).scalar() or "")
    except Exception:  # noqa: BLE001
        db.rollback()
        out["alembic_version"] = ""
    return out


def check_restored(restored: dict, live: dict) -> list[str]:
    """So bản nạp thử với DB đang chạy. Trả danh sách lỗi (rỗng = đạt)."""
    errs = []
    if not restored.get("alembic_version"):
        errs.append("bản nạp không có alembic_version")
    if restored.get("tables", 0) < max(5, int(live.get("tables", 0) * 0.9)):
        errs.append(f"thiếu bảng: nạp được {restored.get('tables', 0)}, DB đang chạy có {live.get('tables', 0)}")
    for t in KEY_TABLES[1:]:
        r, l_ = restored.get(t), live.get(t)
        if r is None:
            errs.append(f"không có bảng {t}")
        elif l_ and r == 0:
            errs.append(f"bảng {t} rỗng trong khi DB đang chạy có {l_} dòng")
    return errs


def restore_test(db: Session, *, actor_id: int = 0) -> AgentDbBackup:
    """Nạp bản mới nhất vào DB tạm, kiểm, rồi xóa DB tạm (luôn luôn). Hỏng thì báo."""
    from app.core.storage import download_bytes

    rec = AgentDbBackup(kind=Kind.RESTORE_TEST, source=Source.AUTO if not actor_id else Source.MANUAL,
                        status=Status.RUNNING, started_at=now_utc(), message="", detail={}, created_by=actor_id,
                        updated_by=actor_id)
    db.add(rec)
    db.commit()
    tmp = restore_db_name()
    created = False
    try:
        if not enabled():
            raise RuntimeError("bot đang chạy chung DB ERP — không có DB riêng để khôi phục thử")
        src = last_success(db)
        if src is None or not src.file_key:
            raise RuntimeError("chưa có bản sao lưu thành công nào để nạp thử")
        sql = gzip.decompress(download_bytes(src.file_key))
        _mysql(f"DROP DATABASE IF EXISTS `{tmp}`; CREATE DATABASE `{tmp}` CHARACTER SET utf8mb4 "
               "COLLATE utf8mb4_unicode_ci")
        created = True
        _mysql(database=tmp, stdin=sql)
        restored: dict = {"tables": int(_mysql(
            f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '{tmp}'") or 0)}
        restored["alembic_version"] = _mysql("SELECT version_num FROM alembic_version LIMIT 1", database=tmp)
        for t in KEY_TABLES[1:]:
            try:
                restored[t] = int(_mysql(f"SELECT COUNT(*) FROM `{t}`", database=tmp) or 0)
            except RuntimeError:
                restored[t] = None
        live = _live_counts(db)
        errs = check_restored(restored, live)
        rec.file_key, rec.size_bytes = src.file_key, src.size_bytes
        rec.detail = {"source_id": src.id, "restored": restored, "live": live}
        if errs:
            raise RuntimeError("; ".join(errs))
        rec.status, rec.finished_at = Status.SUCCESS, now_utc()
        rec.message = f"Nạp được {restored['tables']} bảng, alembic {restored['alembic_version']}"
        db.commit()
        return rec
    except Exception as e:
        db.rollback()
        r = db.get(AgentDbBackup, rec.id)
        if r is not None:
            r.status, r.message, r.finished_at = Status.FAILED, str(e)[:1000], now_utc()
            db.commit()
        alert(db, f"Khôi phục thử DB bot ({db_name()}) LỖI: {str(e)[:300]}")
        raise
    finally:
        if created:
            try:
                _mysql(f"DROP DATABASE IF EXISTS `{tmp}`")
            except Exception:  # noqa: BLE001
                log.exception("agent_hub: không xóa được DB tạm %s", tmp)
                alert(db, f"Khôi phục thử: không xóa được DB tạm {tmp} — xóa tay giúp em.")


# ---------------------------------------------------------------------------
# Cho màn Sao lưu
# ---------------------------------------------------------------------------
def serialize(r: AgentDbBackup) -> dict:
    def iso(d):
        return d.isoformat() if d else None

    return {"id": r.id, "kind": KIND_CODES.get(Kind(r.kind), "backup"),
            "source": SOURCE_CODES.get(Source(r.source), "auto"), "status": STATUS_CODES.get(Status(r.status), "failed"),
            "file_key": r.file_key, "size_bytes": int(r.size_bytes or 0), "message": r.message or "",
            "detail": r.detail or {}, "started_at": iso(r.started_at), "finished_at": iso(r.finished_at),
            "created_at": iso(r.created_at), "created_by": r.created_by,
            "created_by_name": "" if not r.created_by else f"Người dùng #{r.created_by}"}


def _names(db: Session, ids: set[int]) -> dict[int, str]:
    from . import erp

    out = {}
    for uid in ids:
        try:
            out[uid] = erp.describe(db, erp.user_by_id(db, uid))[0]
        except Exception:  # noqa: BLE001 — tên người bấm chỉ để hiển thị
            out[uid] = f"Người dùng #{uid}"
    return out


def page(db: Session, *, offset: int, limit: int) -> dict:
    total = int(db.scalar(select(func.count(AgentDbBackup.id))) or 0)
    rows = list(db.scalars(select(AgentDbBackup).order_by(AgentDbBackup.id.desc()).offset(offset).limit(limit)))
    names = _names(db, {int(r.created_by) for r in rows if r.created_by})
    items = []
    for r in rows:
        item = serialize(r)
        item["created_by_name"] = names.get(int(r.created_by or 0), "") if r.created_by else ""
        items.append(item)
    return {"total": total, "items": items, "keep": keep_count(), "enabled": enabled(),
            "db_name": db_name(), "stale_hours": STALE_HOURS}
