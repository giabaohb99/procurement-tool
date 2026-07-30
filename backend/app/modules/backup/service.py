"""Logic sao lưu CSDL: dump -> nén gzip -> đẩy R2 -> ghi bản ghi -> dọn bản cũ.

Dump bằng mysqldump/mariadb-dump (client cài trong image, xem docker/Dockerfile.api),
kết nối tới DB bằng thông số ở config. DB nhỏ nên dump gọn trong bộ nhớ.
"""
import gzip
import io
import os
import subprocess
from datetime import datetime

from app.core.config import settings
from app.core.storage import upload_fileobj, delete_key

# Số bản backup giữ lại (cũ hơn -> xóa). Đọc từ .env, mặc định 30 (~15 ngày với 2 lần/ngày).
KEEP = getattr(settings, "BACKUP_KEEP", 30)


def _dump_sql() -> bytes:
    """Chạy mysqldump và trả về nội dung .sql (bytes). Ném lỗi nếu dump thất bại."""
    # Ưu tiên mysqldump; image dùng mariadb-client (có symlink mysqldump). Fallback mariadb-dump.
    exe = "mysqldump"
    from shutil import which
    if which(exe) is None and which("mariadb-dump"):
        exe = "mariadb-dump"
    cmd = [
        exe,
        "--single-transaction", "--no-tablespaces", "--skip-lock-tables",
        "--default-character-set=utf8mb4",
        "-h", settings.DB_HOST, "-P", str(settings.DB_PORT),
        "-u", settings.DB_USER, settings.DB_NAME,
    ]
    env = dict(os.environ)
    env["MYSQL_PWD"] = settings.DB_PASSWORD  # tránh lộ mật khẩu trên dòng lệnh
    p = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        err = (p.stderr or b"").decode("utf-8", errors="ignore")[:500]
        raise RuntimeError(f"{exe} lỗi (mã {p.returncode}): {err}")
    if not p.stdout:
        raise RuntimeError("Dump rỗng — không nhận được dữ liệu")
    return p.stdout


def _prune(db) -> int:
    """Giữ KEEP bản mới nhất, xóa phần cũ hơn (cả file R2 lẫn dòng DB). Trả số bản đã xóa."""
    from .model import DbBackup
    olds = db.query(DbBackup).order_by(DbBackup.id.desc()).offset(KEEP).all()
    n = 0
    for o in olds:
        if o.file_key:
            delete_key(o.file_key)
        db.delete(o)
        n += 1
    if n:
        db.commit()
    return n


def run_backup(db, actor_id: int = 0, source: str = "auto"):
    """Thực hiện 1 lần sao lưu. Ghi bản ghi running -> success/failed. Trả về DbBackup."""
    from .model import DbBackup
    started = datetime.now()
    rec = DbBackup(source=source, status="running", started_at=started, created_by=actor_id)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    try:
        raw = _dump_sql()
        gz = gzip.compress(raw, compresslevel=6)
        key = f"backups/procurement-{started.strftime('%Y%m%d-%H%M%S')}.sql.gz"
        upload_fileobj(io.BytesIO(gz), key, "application/gzip")
        rec.file_key = key
        rec.size_bytes = len(gz)
        rec.status = "success"
        rec.finished_at = datetime.now()
        db.commit()
        _prune(db)
        db.refresh(rec)
        return rec
    except Exception as e:  # noqa: BLE001
        db.rollback()
        r = db.get(DbBackup, rec.id)
        if r:
            r.status = "failed"
            r.message = str(e)[:1000]
            r.finished_at = datetime.now()
            db.commit()
        raise


def delete_backup(db, bid: int) -> bool:
    """Xóa 1 bản backup (file R2 + dòng DB). Trả True nếu có xóa."""
    from .model import DbBackup
    rec = db.get(DbBackup, bid)
    if not rec:
        return False
    if rec.file_key:
        delete_key(rec.file_key)
    db.delete(rec)
    db.commit()
    return True
