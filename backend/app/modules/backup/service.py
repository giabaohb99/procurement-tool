"""Logic sao lưu CSDL: dump -> nén gzip -> đẩy R2 -> ghi bản ghi -> dọn bản cũ.

Dump bằng mysqldump/mariadb-dump (client cài trong image, xem docker/Dockerfile.api),
kết nối tới DB bằng thông số ở config. DB nhỏ nên dump gọn trong bộ nhớ.

**QĐ-C (bao-CR-454, CR-312 P6 đợt 2) — bốn bảng nhật ký KHÔNG đi theo bản sao
lưu hằng đêm.** Chúng đã có đường lưu trữ riêng (gói tháng trên R2, xem
`modules/audit/tasks.py`), nên nằm trong bản dump nữa là lưu hai lần cùng một
thứ: bật ghi nhật ký đầy đủ thì CSDL phình từ 18,7 MB lên ~215 MB, mỗi bản dump
nén từ 1,09 MB lên 8–15 MB, nhân với 30 bản giữ lại là 250–450 MB trên R2 và
mỗi đêm dump lâu thêm, hai lần một ngày.

Đánh đổi đã biết và đã chấp nhận: **phục hồi từ bản sao lưu sẽ ra một hệ thống
trắng nhật ký**. Nhật ký để truy trách nhiệm, không phải để khôi phục dữ liệu;
muốn có lại thì nạp từ gói R2.
"""
import gzip
import io
import os
import subprocess
from datetime import datetime

from app.core import app_settings
from app.core.config import settings
from app.core.storage import env_prefix, upload_fileobj, delete_key
from app.modules.audit.tasks import ARCHIVE_TABLES

#  ⚠️ MỘT nguồn sự thật cho «bốn bảng nhật ký», và nó cố ý **suy ra** từ
#  `ARCHIVE_TABLES` thay vì chép tay lại tên bảng ở đây. Bản thiết kế §9 nói
#  khai hằng này trong chính tệp này; chép tay thì đúng câu chữ nhưng lại dựng
#  lên đúng thứ câu sau của nó cảnh báo — hai nơi khai cùng một danh sách là
#  hai nơi lệch nhau. Thêm một bảng nhật ký thứ năm vào `ARCHIVE_TABLES` là nó
#  tự ra khỏi bản sao lưu, không phải đi sửa ba chỗ.
LOG_TABLES = tuple(model.__tablename__ for _, model in ARCHIVE_TABLES)


def keep_count() -> int:
    """Số bản sao lưu giữ lại (cũ hơn thì xóa), mặc định 30 (~15 ngày với 2 lần/ngày).

    Phải là HÀM chứ không phải hằng số: từ bao-CR-429 con số này sửa được trên
    màn Cấu hình hệ thống, mà hằng số ở đầu tệp thì chốt giá trị ngay lúc nạp
    module — người dùng đổi xong vẫn phải dựng lại dịch vụ mới có tác dụng.
    Sàn 1 để một ô rỗng không biến thành «xóa sạch mọi bản sao lưu».
    """
    return max(1, int(app_settings.get("backup_keep") or 0) or settings.BACKUP_KEEP or 30)


def _la_client_mariadb(exe: str) -> bool:
    """Client trong image là MariaDB hay MySQL thật? Quyết định cờ SSL dùng được."""
    try:
        r = subprocess.run([exe, "--version"], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=10)
        return b"mariadb" in (r.stdout or b"").lower()
    except Exception:
        return False


def resolve_dump_exe() -> str:
    """Ưu tiên mysqldump; image dùng mariadb-client (có symlink). Lùi về mariadb-dump."""
    exe = "mysqldump"
    from shutil import which
    if which(exe) is None and which("mariadb-dump"):
        exe = "mariadb-dump"
    return exe


def build_dump_command(exe: str) -> list[str]:
    """Phần dòng lệnh dùng chung cho CẢ HAI lượt dump, chưa gồm tên CSDL."""
    cmd = [
        exe,
        "--single-transaction", "--no-tablespaces", "--skip-lock-tables",
        "--default-character-set=utf8mb4",
    ]
    # Server MySQL 8 bật TLS sẵn với chứng chỉ tự ký; client MariaDB mặc định lại đòi
    # xác thực chứng chỉ nên dump chết với "self-signed certificate in certificate chain".
    # Tắt phần XÁC THỰC (kết nối vẫn mã hoá), và chỉ thêm khi đúng là client MariaDB
    # vì MySQL 8 đã bỏ cờ này.
    if _la_client_mariadb(exe):
        cmd.append("--ssl-verify-server-cert=0")
    cmd += ["-h", settings.DB_HOST, "-P", str(settings.DB_PORT), "-u", settings.DB_USER]
    return cmd


def run_dump_pass(cmd: list[str], exe: str, label: str) -> bytes:
    """Chạy một lượt dump, trả nội dung .sql đã cắt dòng sandbox. Hỏng thì ném lỗi."""
    env = dict(os.environ)
    env["MYSQL_PWD"] = settings.DB_PASSWORD  # tránh lộ mật khẩu trên dòng lệnh
    p = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        err = (p.stderr or b"").decode("utf-8", errors="ignore")[:500]
        raise RuntimeError(f"{exe} lỗi ở lượt {label} (mã {p.returncode}): {err}")
    if not p.stdout:
        raise RuntimeError(f"Dump rỗng ở lượt {label} — không nhận được dữ liệu")
    return _strip_sandbox_lines(p.stdout)


def _dump_sql() -> bytes:
    """Dump HAI LƯỢT rồi nối lại thành một tệp .sql (QĐ-C).

    Lượt 1: cả CSDL, bỏ dữ liệu bốn bảng nhật ký bằng `--ignore-table`.
    Lượt 2: `--no-data` đúng bốn bảng đó — chỉ lấy `CREATE TABLE`.

    ⚠️ **KHÔNG ĐƯỢC BỎ LƯỢT 2.** `--ignore-table` không chỉ bỏ dữ liệu, nó bỏ
    luôn cả `CREATE TABLE`. Phục hồi xong thì bảng **không tồn tại**, mà
    `alembic_version` trong chính bản dump đó lại đang ở head — nên
    `alembic upgrade head` lúc khởi động coi như không còn gì phải làm và không
    dựng lại bảng nào. Hệ thống lên xanh, rồi chết ở truy vấn đầu tiên chạm
    nhật ký: tức là ở middleware, tức là ở **mọi** lượt gọi API.

    Lượt `--no-data` cũng là chỗ giữ lại mệnh đề `PARTITION BY RANGE` của
    bao-CR-454, nên bảng phục hồi ra đúng hình, chỉ rỗng ruột.
    """
    exe = resolve_dump_exe()
    base = build_dump_command(exe)
    ignore = [f"--ignore-table={settings.DB_NAME}.{table}" for table in LOG_TABLES]
    data_sql = run_dump_pass(base + ignore + [settings.DB_NAME], exe, "dữ liệu nghiệp vụ")
    schema_sql = run_dump_pass(base + ["--no-data", settings.DB_NAME, *LOG_TABLES],
                               exe, "cấu trúc bảng nhật ký")
    return data_sql + b"\n" + schema_sql


def _strip_sandbox_lines(sql: bytes) -> bytes:
    """Bỏ dòng '/*!999999\\- enable the sandbox mode */' do mariadb-dump chèn ở đầu file.

    MySQL không hiểu dòng này và sẽ báo lỗi cú pháp khi phục hồi, nên phải cắt bỏ
    ngay lúc dump — nếu không thì bản backup coi như không phục hồi được.
    """
    if b"enable the sandbox mode" not in sql[:512]:
        return sql
    lines = sql.split(b"\n")
    return b"\n".join(d for d in lines if b"enable the sandbox mode" not in d)


def _prune(db) -> int:
    """Giữ `keep_count()` bản mới nhất, xóa phần cũ hơn (cả file R2 lẫn dòng DB). Trả số bản đã xóa."""
    from .model import DbBackup
    olds = db.query(DbBackup).order_by(DbBackup.id.desc()).offset(keep_count()).all()
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
        # {env}/backup/{tên DB}-{thời điểm}.sql.gz → prod và dev không lẫn file backup.
        key = f"{env_prefix()}/backup/{settings.DB_NAME}-{started.strftime('%Y%m%d-%H%M%S')}.sql.gz"
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
