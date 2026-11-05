"""Logic sao lưu CSDL: dump -> nén gzip -> đẩy R2 -> ghi bản ghi -> dọn bản cũ.

Dump bằng `mysqldump` của **MySQL 8.4 thật** (gói `mysql-community-client` của Oracle,
cài trong image, xem docker/Dockerfile.api), kết nối tới DB bằng thông số ở config.
DB nhỏ nên dump gọn trong bộ nhớ.

**Không nhận client MariaDB (phiếu kh-sao-luu-dung, 22/10/2026).** Image cũ cài
`default-mysql-client` — trên Debian đó là MariaDB. `mariadb-dump` ghi cả giá trị
của cột sinh (`tab_approval_instance.running_slot`, `tab_document_version.open_slot`)
vào câu INSERT, nên nạp vào MySQL 8.4 chết ở lỗi 3105 — tức bản sao lưu "thành
công" mà không khôi phục được. Gặp client MariaDB thì `dump_sql` ném lỗi, lượt sao
lưu ghi `failed`, không đẩy bản hỏng lên kho.

**Chặn dọn bản cũ khi bản mới đáng ngờ** (`prune_backups`, dùng chung với DB bot).
Chỉ dọn khi bản vừa tạo thành công VÀ cỡ gzip >= 50% MỐC — trung vị 5 bản thành công
gần nhất KHÔNG bị đánh dấu (chưa có bản nào thì dọn bình thường). Bản bé bất thường
thì giữ nguyên mọi bản thành công cũ, ghi lý do vào `message` (đầu `SUSPECT_NOTE_PREFIX`)
và BÁO CHỦ ĐỘNG (chuông ERP cho người có quyền `backup.read`; bên bot là `alert()`). Bản
mang dấu đó không bao giờ làm mốc, nên lượt bé thứ hai vẫn bị chặn. Dòng failed quá tuổi
vẫn được dọn ngay cả lúc đang chặn. CSDL thu nhỏ thật (hợp lệ) thì quản trị bấm *chấp
nhận cỡ mới* (`accept_new_size`, `POST /api/backups/accept-size`): gỡ dấu cả chuỗi bản
đáng ngờ gần nhất, đánh dấu `ACCEPTED_NOTE_PREFIX`; mốc từ đó chỉ tính tới bản được
chấp nhận mới nhất, không lùi về các bản to trước nó.
`keep_count()` chỉ đếm bản TỐT; dòng failed / running dọn theo tuổi (30 ngày) — chuỗi
lượt hỏng dài không đẩy được bản tốt nào ra. Thiếu R2 thì không sao lưu (không lùi về
`uploads/`, thư mục phục vụ công khai).

**QĐ-C (bao-CR-454, CR-312 P6 đợt 2) — bốn bảng nhật ký KHÔNG đi theo bản sao
lưu hằng đêm.** Chúng đã có đường lưu trữ riêng (gói tháng trên R2, xem
`modules/audit/tasks.py`), nên nằm trong bản dump nữa là lưu hai lần cùng một
thứ: bật ghi nhật ký đầy đủ thì CSDL phình từ 18,7 MB lên ~215 MB, mỗi bản dump
nén từ 1,09 MB lên 8–15 MB, nhân với 30 bản giữ lại là 250–450 MB trên R2 và
mỗi đêm dump lâu thêm, hai lần một ngày.

Đánh đổi đã biết và đã chấp nhận: **phục hồi từ bản sao lưu sẽ ra một hệ thống
trắng nhật ký**. Nhật ký để truy trách nhiệm, không phải để khôi phục dữ liệu;
muốn có lại thì nạp từ gói R2. Khôi phục: `backend/scripts/restore_backup.py`.

**bao-CR-732 — tối ưu (người chủ gật 05/11/2026).** Đo prod 05/11: CSDL ~1.020 MB, mỗi bản nén ~90 MB, và bản dump cũ
nằm trọn trong RAM worker ba lần (bytes thô + gzip + BytesIO). Ba đổi:
1. **Dump luồng** (`dump_main_to` / `dump_customs_to`): stdout của mysqldump đọc từng khúc 1 MB, nén thẳng vào tệp tạm,
   đẩy R2 từ tệp (boto3 tự chia phần) — RAM không còn tỷ lệ với cỡ CSDL. Vẫn hai lượt (`--ignore-table` + `--no-data`).
2. **Bảng nhật ký máy chỉ lấy cấu trúc** (`MACHINE_DATA_TABLES`: sổ đồng bộ, nhật ký nạp tệp, sự kiện giao diện thô) —
   cùng lý với bốn bảng nhật ký ở trên: là vết máy ghi, khôi phục ra rỗng thì hệ vẫn chạy đúng.
3. **Dữ liệu tra cứu thị trường tách bản riêng** (`CUSTOMS_DATA_TABLES`, `part = 'customs'`): bản chính chỉ lấy cấu trúc
   các bảng đó; bản riêng chỉ lấy DỮ LIỆU (`--no-create-info --complete-insert`, nạp được vào cấu trúc của bản chính kể
   cả khi bảng có thêm cột), chụp ở lượt sáng, BỎ QUA nếu dấu vân tay (phiên bản alembic + số dòng / id lớn nhất / lần
   sửa cuối của từng bảng) không đổi, giữ `CUSTOMS_KEEP` bản. Đổi cấu trúc (migration) thì lượt nào cũng chụp lại.
   **Khôi phục = bản chính + bản tra cứu thị trường mới nhất**, đúng thứ tự đó (bản chính dựng lại bảng rỗng).
"""
import gzip
import hashlib
import logging
import os
import statistics
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable

from app.core import app_settings
from app.core.config import settings
from app.core.storage import env_prefix, upload_fileobj, delete_key, is_remote_storage_ready
from app.modules.audit.tasks import ARCHIVE_TABLES

#  ⚠️ MỘT nguồn sự thật cho "bốn bảng nhật ký", và nó cố ý **suy ra** từ
#  `ARCHIVE_TABLES` thay vì chép tay lại tên bảng ở đây. Bản thiết kế §9 nói
#  khai hằng này trong chính tệp này; chép tay thì đúng câu chữ nhưng lại dựng
#  lên đúng thứ câu sau của nó cảnh báo — hai nơi khai cùng một danh sách là
#  hai nơi lệch nhau. Thêm một bảng nhật ký thứ năm vào `ARCHIVE_TABLES` là nó
#  tự ra khỏi bản sao lưu, không phải đi sửa ba chỗ.
LOG_TABLES = tuple(model.__tablename__ for _, model in ARCHIVE_TABLES)

#  Bản mới nhỏ hơn tỷ lệ này so với MỐC thì KHÔNG dọn bản cũ. Mốc = trung vị cỡ của
#  PRUNE_BASELINE_WINDOW bản thành công gần nhất KHÔNG bị đánh dấu đáng ngờ.
PRUNE_MIN_SIZE_RATIO = 0.5
PRUNE_BASELINE_WINDOW = 5
#  Dòng failed / running không giữ theo số bản mà theo tuổi (tính từ started_at).
FAILED_RETENTION_DAYS = 30
#  Đầu `message` của bản bị đánh dấu đáng ngờ. Bản mang dấu này không bao giờ làm mốc
#  so và không được tính vào `keep_count()` — nên lượt bé thứ hai vẫn bị chặn.
SUSPECT_NOTE_PREFIX = "Bỏ qua dọn bản cũ:"
#  Đầu `message` của bản quản trị đã *chấp nhận cỡ mới*: lại được làm mốc, và mốc dừng ở đây.
ACCEPTED_NOTE_PREFIX = "Đã chấp nhận cỡ mới:"
#  Màn Sao lưu ở ERP v2 (frontend-v2 `appRoutes.system.backups`) — đích của chuông báo.
BACKUP_SCREEN_LINK = "/system/backups"

#  bao-CR-732 — bảng nhật ký do máy ghi: mọi bản chỉ lấy CẤU TRÚC. Đo prod 05/11/2026: sổ đồng bộ 173 MB, nhật ký nạp tệp
#  183 MB. Cố ý KHÔNG có `tab_import_change` (ảnh chụp để hoàn tác lô nạp) và bảng số dùng theo ngày / tuần (gom từ nguồn
#  thô đã bị dọn, mất là không dựng lại được).
MACHINE_DATA_TABLES = ("tab_sync_log", "tab_import_log", "tab_ui_event")
#  Dữ liệu tra cứu thị trường nạp từ tệp ngoài, to và ít đổi: dòng hàng 306 MB trên prod. Bảng cấu hình nhỏ do người sửa
#  (bộ lọc lưu, từ đồng nghĩa, văn bản, mã dạng) vẫn ở bản chính để không chịu nhịp một lần mỗi ngày.
CUSTOMS_DATA_TABLES = ("tab_customs_line", "tab_customs_line_change", "tab_customs_party", "tab_customs_tariff",
                       "tab_customs_pesticide", "tab_customs_pesticide_use")
PART_MAIN = "main"
PART_CUSTOMS = "customs"
PART_LABELS = {PART_MAIN: "Bản chính", PART_CUSTOMS: "Tra cứu thị trường"}
CUSTOMS_KEEP = 7
DUMP_CHUNK_BYTES = 1 << 20

log = logging.getLogger(__name__)


def keep_count() -> int:
    """Số bản sao lưu giữ lại (cũ hơn thì xóa), mặc định 30 (~15 ngày với 2 lần/ngày).

    Phải là HÀM chứ không phải hằng số: từ bao-CR-429 con số này sửa được trên
    màn Cấu hình hệ thống, mà hằng số ở đầu tệp thì chốt giá trị ngay lúc nạp
    module — người dùng đổi xong vẫn phải dựng lại dịch vụ mới có tác dụng.
    Sàn 1 để một ô rỗng không biến thành "xóa sạch mọi bản sao lưu".
    """
    return max(1, int(app_settings.get("backup_keep") or 0) or settings.BACKUP_KEEP or 30)


def is_mariadb_client(exe: str) -> bool:
    """Client trong image là MariaDB hay MySQL thật? Đọc từ `<exe> --version`."""
    try:
        r = subprocess.run([exe, "--version"], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=10)
        return b"mariadb" in (r.stdout or b"").lower()
    except Exception:
        return False


def resolve_dump_exe() -> str:
    """Tên chương trình dump. Image chỉ còn `mysqldump` của MySQL; `mariadb-dump` chỉ còn
    để nhận ra image cũ chưa dựng lại (khi đó `dump_sql` từ chối, không dump)."""
    exe = "mysqldump"
    from shutil import which
    if which(exe) is None and which("mariadb-dump"):
        exe = "mariadb-dump"
    return exe


def build_dump_command(exe: str) -> list[str]:
    """Phần dòng lệnh dùng chung cho CẢ HAI lượt dump, chưa gồm tên CSDL.

    `--set-gtid-purged=OFF`: server bật GTID thì mysqldump mặc định chèn
    `SET @@GLOBAL.GTID_PURGED` vào đầu bản dump — nạp vào server khác (hay chính nó
    sau khi đã có GTID) sẽ chết, mà user ứng dụng lại không có quyền đặt biến đó.
    Cờ này chỉ có ở mysqldump của MySQL nên chỉ thêm khi đúng là client MySQL.
    """
    cmd = [
        exe,
        "--single-transaction", "--no-tablespaces", "--skip-lock-tables",
        "--default-character-set=utf8mb4",
    ]
    if not is_mariadb_client(exe):
        cmd.append("--set-gtid-purged=OFF")
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


def dump_sql(db_name: str, log_tables: tuple[str, ...] = ()) -> bytes:
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
    if is_mariadb_client(exe):
        raise RuntimeError(
            f"Client dump là MariaDB ({exe}) — bản dump của nó KHÔNG khôi phục được vào "
            "MySQL 8.4 (lỗi 3105 ở cột sinh). Dựng lại image api để có mysqldump của MySQL "
            "(docker/Dockerfile.api) rồi chạy lại sao lưu.")
    base = build_dump_command(exe)
    ignore = [f"--ignore-table={db_name}.{table}" for table in log_tables]
    data_sql = run_dump_pass(base + ignore + [db_name], exe, "dữ liệu nghiệp vụ")
    if not log_tables:
        #  ai-CR-139: DB bot (agent_hub) không có bảng nhật ký đi đường gói R2 — một lượt là đủ.
        return data_sql
    schema_sql = run_dump_pass(base + ["--no-data", db_name, *log_tables],
                               exe, "cấu trúc bảng nhật ký")
    return data_sql + b"\n" + schema_sql


def stream_dump_pass(cmd: list[str], exe: str, label: str, out) -> int:
    """Chạy một lượt dump, chép stdout từng khúc vào `out` (cắt dòng sandbox ở khúc đầu). Trả số byte thô (bao-CR-732).

    stderr ghi ra tệp tạm chứ không qua PIPE: PIPE đầy (mysqldump báo nhiều cảnh báo) mà không ai đọc thì hai tiến
    trình treo chờ nhau."""
    env = dict(os.environ)
    env["MYSQL_PWD"] = settings.DB_PASSWORD  # tránh lộ mật khẩu trên dòng lệnh
    written = 0
    with tempfile.TemporaryFile() as err:
        proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=err)
        try:
            first = True
            while True:
                chunk = proc.stdout.read(DUMP_CHUNK_BYTES)
                if not chunk:
                    break
                if first:
                    chunk, first = _strip_sandbox_lines(chunk), False
                out.write(chunk)
                written += len(chunk)
        finally:
            proc.stdout.close()
            code = proc.wait()
        if code != 0:
            err.seek(0)
            msg = err.read(500).decode("utf-8", errors="ignore")
            raise RuntimeError(f"{exe} lỗi ở lượt {label} (mã {code}): {msg}")
    if not written:
        raise RuntimeError(f"Dump rỗng ở lượt {label} — không nhận được dữ liệu")
    return written


def _checked_exe() -> str:
    exe = resolve_dump_exe()
    if is_mariadb_client(exe):
        raise RuntimeError(
            f"Client dump là MariaDB ({exe}) — bản dump của nó KHÔNG khôi phục được vào "
            "MySQL 8.4 (lỗi 3105 ở cột sinh). Dựng lại image api để có mysqldump của MySQL "
            "(docker/Dockerfile.api) rồi chạy lại sao lưu.")
    return exe


def main_schema_only_tables() -> tuple[str, ...]:
    """Bảng mà bản CHÍNH chỉ lấy cấu trúc: bốn bảng nhật ký (gói R2), nhật ký máy, dữ liệu tra cứu thị trường."""
    return LOG_TABLES + MACHINE_DATA_TABLES + CUSTOMS_DATA_TABLES


def dump_main_to(out, db_name: str) -> int:
    """Bản CHÍNH, hai lượt nối vào cùng luồng `out` (`dump_sql` giải thích vì sao KHÔNG được bỏ lượt 2)."""
    exe = _checked_exe()
    base = build_dump_command(exe)
    skip = main_schema_only_tables()
    raw = stream_dump_pass(base + [f"--ignore-table={db_name}.{t}" for t in skip] + [db_name], exe,
                           "dữ liệu nghiệp vụ", out)
    out.write(b"\n")
    return raw + 1 + stream_dump_pass(base + ["--no-data", db_name, *skip], exe, "cấu trúc bảng chỉ lấy khung", out)


def dump_customs_to(out, db_name: str) -> int:
    """Bản TRA CỨU THỊ TRƯỜNG: chỉ dữ liệu, câu INSERT ghi rõ tên cột — nạp SAU bản chính, vào bảng bản chính dựng."""
    exe = _checked_exe()
    cmd = build_dump_command(exe) + ["--no-create-info", "--complete-insert", db_name, *CUSTOMS_DATA_TABLES]
    return stream_dump_pass(cmd, exe, "dữ liệu tra cứu thị trường", out)


def dump_to_gzip_file(dump_fn, db_name: str):
    """Chạy `dump_fn(out, db_name)` nén thẳng vào tệp tạm. Trả (tệp đã tua về đầu, cỡ gzip) — bên gọi đóng tệp."""
    tmp = tempfile.TemporaryFile()
    try:
        with gzip.GzipFile(fileobj=tmp, mode="wb", compresslevel=6) as gz:
            dump_fn(gz, db_name)
        size = tmp.tell()
        tmp.seek(0)
        return tmp, size
    except Exception:
        tmp.close()
        raise


def customs_fingerprint(db) -> str:
    """'<phiên bản alembic>:<sha1>' của dữ liệu tra cứu thị trường — đổi khi có dòng thêm / xóa / sửa hoặc có migration.

    Mỗi bảng: số dòng, id lớn nhất, lần sửa cuối (nếu bảng có `updated_at`). Đếm bảng 300 nghìn dòng theo khóa chính
    chỉ mất phần nhỏ giây — rẻ hơn nhiều so với dump lại 300 MB không cần."""
    from sqlalchemy import text

    from app.core.base_model import Base
    try:
        version = db.execute(text("SELECT version_num FROM alembic_version")).scalar() or ""
    except Exception:  # noqa: BLE001 — CSDL bài kiểm không có bảng alembic
        db.rollback()
        version = ""
    parts = []
    for name in CUSTOMS_DATA_TABLES:
        table = Base.metadata.tables.get(name)
        if table is None:
            continue
        upd = ", MAX(updated_at)" if "updated_at" in table.c else ""
        row = db.execute(text(f"SELECT COUNT(*), MAX(id){upd} FROM {name}")).first()
        parts.append(f"{name}={'/'.join(str(v) for v in row)}")
    return f"{version}:{hashlib.sha1(';'.join(parts).encode()).hexdigest()}"


def customs_due(last, fingerprint: str, *, daily: bool) -> str:
    """Lý do phải chụp bản tra cứu thị trường lượt này; chuỗi rỗng = bỏ qua.

    `last`: bản 'customs' thành công gần nhất (hoặc None). `daily`: lượt sáng / bấm tay — lượt chiều chỉ chụp khi đổi
    cấu trúc, để bản chính mới không bao giờ phải đi cùng dữ liệu chụp trên cấu trúc cũ."""
    if last is None:
        return "chưa có bản nào"
    if (last.fingerprint or "") == fingerprint:
        return ""
    if (last.fingerprint or "").split(":", 1)[0] != fingerprint.split(":", 1)[0]:
        return "cấu trúc CSDL đổi (migration)"
    return "dữ liệu đổi" if daily else ""


def _strip_sandbox_lines(sql: bytes) -> bytes:
    """Bỏ dòng '/*!999999\\- enable the sandbox mode */' do mariadb-dump chèn ở đầu file.

    MySQL không hiểu dòng này và sẽ báo lỗi cú pháp khi phục hồi, nên phải cắt bỏ
    ngay lúc dump — nếu không thì bản backup coi như không phục hồi được.
    """
    if b"enable the sandbox mode" not in sql[:512]:
        return sql
    lines = sql.split(b"\n")
    return b"\n".join(d for d in lines if b"enable the sandbox mode" not in d)


@dataclass(frozen=True)
class PruneItem:
    """Một dòng sổ sao lưu, đã quy về dạng chung cho cả ERP (`DbBackup`) lẫn DB bot (`AgentDbBackup`)."""
    row: Any
    succeeded: bool
    size: int
    at: datetime | None
    suspect: bool
    accepted: bool = False


def is_suspect_note(message: str | None) -> bool:
    return (message or "").startswith(SUSPECT_NOTE_PREFIX)


def is_accepted_note(message: str | None) -> bool:
    return (message or "").startswith(ACCEPTED_NOTE_PREFIX)


def to_prune_item(row, succeeded: bool) -> PruneItem:
    """Quy một dòng sổ sao lưu (ERP hay bot — cùng các cột size_bytes / message / started_at)."""
    return PruneItem(row, succeeded, row.size_bytes or 0, row.started_at or row.created_at,
                     is_suspect_note(row.message), is_accepted_note(row.message))


def suspect_reason(new_id: int, new_size: int, baseline_sizes: list[int]) -> str:
    """Lý do coi bản mới là đáng ngờ (chuỗi rỗng = bình thường).

    `baseline_sizes`: cỡ các bản thành công KHÔNG bị đánh dấu, cũ hơn bản mới, mới nhất trước.
    Mốc là trung vị của tối đa PRUNE_BASELINE_WINDOW bản: một bản to lẻ loi không khóa việc dọn
    mãi mãi, mà một lượt bé bị đánh dấu cũng không bao giờ thành mốc để lượt bé sau qua lọt.
    """
    sizes = [s for s in baseline_sizes if s > 0][:PRUNE_BASELINE_WINDOW]
    if not sizes:
        return ""
    baseline = statistics.median(sizes)
    if new_size < baseline * PRUNE_MIN_SIZE_RATIO:
        return (f"bản #{new_id} chỉ {new_size:,} byte, dưới {int(PRUNE_MIN_SIZE_RATIO * 100)}% "
                f"mốc {int(baseline):,} byte (trung vị {len(sizes)} bản thành công gần nhất)")
    return ""


def plan_prune(items: list[PruneItem], *, keep: int, now: datetime,
               include_success: bool = True) -> list[PruneItem]:
    """Chọn các dòng phải xóa. `items` xếp mới nhất trước.

    - Bản thành công (chỉ khi `include_success`): giữ `keep` bản TỐT (thành công, không đáng
      ngờ) mới nhất; mọi bản thành công (kể cả đáng ngờ) cũ hơn bản tốt thứ `keep` thì xóa.
      Dòng failed/running KHÔNG chiếm chỗ trong `keep` — R2 hỏng nhiều ngày rồi một lượt thành
      công không được xóa sạch bản tốt. Sàn `keep` là 1.
    - Dòng failed / running: xóa theo tuổi, quá FAILED_RETENTION_DAYS (kể cả lúc đang chặn).
    """
    keep = max(1, keep)
    out: list[PruneItem] = []
    if include_success:
        good = [i for i in items if i.succeeded and not i.suspect]
        if len(good) > keep:
            boundary_id = good[keep - 1].row.id
            out += [i for i in items if i.succeeded and i.row.id < boundary_id]
    cutoff = now - timedelta(days=FAILED_RETENTION_DAYS)
    out += [i for i in items if not i.succeeded and i.at is not None and i.at < cutoff]
    return out


def baseline_sizes(items: list[PruneItem], new_id: int) -> list[int]:
    """Cỡ các bản làm mốc cho bản `new_id`: bản tốt cũ hơn, mới nhất trước, DỪNG ở bản được
    *chấp nhận cỡ mới* gần nhất — các bản to trước lần chấp nhận không còn được tính."""
    out: list[int] = []
    for i in items:
        if i.row.id >= new_id or not i.succeeded or i.suspect:
            continue
        out.append(i.size)
        if i.accepted:
            break
    return out


def prune_backups(db, new_rec, items: list[PruneItem], *, keep: int, now: datetime,
                  remove_file: Callable[[str], Any],
                  notify: Callable[[str], Any] | None = None) -> int:
    """Chốt rồi dọn — dùng chung cho sao lưu ERP và DB bot. Trả số dòng đã xóa.

    Chỉ dọn bản thành công cũ khi bản vừa tạo thành công VÀ không đáng ngờ (`suspect_reason`).
    Đáng ngờ thì giữ mọi bản thành công, ghi lý do (đầu SUSPECT_NOTE_PREFIX) vào `message` của
    bản đó, gọi `notify` (báo chủ động), và vẫn dọn dòng failed quá tuổi.
    """
    if new_rec is None or not any(i.row is new_rec and i.succeeded for i in items):
        return 0
    reason = suspect_reason(new_rec.id, new_rec.size_bytes or 0, baseline_sizes(items, new_rec.id))
    if reason:
        note = f"{SUSPECT_NOTE_PREFIX} {reason}."
        log.warning("sao lưu: %s", note)
        new_rec.message = note[:1000]
        db.commit()
        if notify is not None:
            try:
                notify(f"{note} Nếu CSDL thu nhỏ thật (hợp lệ), vào màn Sao lưu bấm Chấp nhận cỡ mới; "
                       "nếu không, kiểm lượt dump — bản cũ vẫn được giữ nguyên cho tới khi xử lý.")
            except Exception:  # noqa: BLE001 — báo hỏng không được làm hỏng vòng sao lưu
                db.rollback()
                log.exception("sao lưu: không gửi được báo bản đáng ngờ")
    targets = plan_prune(items, keep=keep, now=now, include_success=not reason)
    for t in targets:
        if t.row.file_key:
            remove_file(t.row.file_key)
        db.delete(t.row)
    if targets:
        db.commit()
    return len(targets)


def accept_suspect_streak(db, items: list[PruneItem], *, actor_id: int, now: datetime) -> int:
    """*Chấp nhận cỡ mới*: gỡ dấu đáng ngờ của CẢ CHUỖI bản đáng ngờ mới nhất (mọi bản thành công
    đáng ngờ mới hơn bản tốt gần nhất), đánh dấu ACCEPTED_NOTE_PREFIX. Trả số bản đã gỡ dấu."""
    streak = []
    for i in items:
        if not i.succeeded:
            continue
        if not i.suspect:
            break
        streak.append(i)
    stamp = f"{ACCEPTED_NOTE_PREFIX} người dùng #{actor_id} lúc {now:%d/%m/%Y %H:%M}"
    for i in streak:
        old = (i.row.message or "")[len(SUSPECT_NOTE_PREFIX):].strip()
        i.row.message = f"{stamp} (trước đó: {old})"[:1000]
    if streak:
        db.commit()
    return len(streak)


def notify_backup_admins(db, text_: str) -> int:
    """Chuông ERP cho mọi tài khoản đang hoạt động có `backup.read`. Trả số người được báo."""
    from app.modules.notification.model import Notification
    from app.modules.role.model import Permission
    from app.modules.user.model import User, UserRole

    role_ids = [p.role_id for p in db.query(Permission).filter(Permission.entity == "backup",
                                                                Permission.can_read.is_(True))]
    if not role_ids:
        return 0
    user_ids = {ur.user_id for ur in db.query(UserRole).filter(UserRole.role_id.in_(role_ids))}
    users = db.query(User.id).filter(User.id.in_(user_ids), User.is_active.is_(True)).all() if user_ids else []
    for (uid,) in users:
        db.add(Notification(user_id=uid, title="Sao lưu CSDL: bản mới bé bất thường",
                            body=text_, link=BACKUP_SCREEN_LINK))
    if users:
        db.commit()
    return len(users)


def _backup_items(db, part: str = PART_MAIN) -> list[PruneItem]:
    """Sổ của MỘT phần (bản chính / tra cứu thị trường) — hai phần dọn và so cỡ riêng, không lấy nhau làm mốc."""
    from .model import DbBackup
    rows = db.query(DbBackup).filter(DbBackup.part == part).order_by(DbBackup.id.desc()).all()
    return [to_prune_item(r, r.status == "success") for r in rows]


def _prune(db, new_rec) -> int:
    """Dọn sổ sao lưu ERP sau một lượt thành công (xem `prune_backups`), riêng từng phần."""
    part = new_rec.part or PART_MAIN
    keep = CUSTOMS_KEEP if part == PART_CUSTOMS else keep_count()
    return prune_backups(db, new_rec, _backup_items(db, part), keep=keep, now=datetime.now(),
                         remove_file=delete_key, notify=lambda t: notify_backup_admins(db, t))


def accept_new_size(db, actor_id: int) -> int:
    """Quản trị xác nhận CSDL thu nhỏ hợp lệ — xem `accept_suspect_streak`. Gỡ dấu cho cả hai phần."""
    now = datetime.now()
    return sum(accept_suspect_streak(db, _backup_items(db, part), actor_id=actor_id, now=now)
               for part in (PART_MAIN, PART_CUSTOMS))


def _run_part(db, *, part: str, actor_id: int, source: str, dump_fn, fingerprint: str = ""):
    """Một lượt sao lưu của MỘT phần: dòng running -> dump luồng ra tệp tạm -> R2 -> success / failed -> dọn."""
    from .model import DbBackup
    started = datetime.now()
    rec = DbBackup(source=source, status="running", started_at=started, created_by=actor_id, part=part,
                   fingerprint=fingerprint)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    try:
        if not is_remote_storage_ready():
            #  Thiếu R2 thì `upload_fileobj` lùi về `uploads/` — thư mục phục vụ CÔNG KHAI qua
            #  /api/uploads. Bản sao lưu CSDL tuyệt đối không được nằm ở đó.
            raise RuntimeError("Chưa cấu hình R2 — bản sao lưu không có chỗ cất an toàn "
                               "(không ghi vào uploads/ vì thư mục đó phục vụ công khai)")
        tmp, size = dump_to_gzip_file(dump_fn, settings.DB_NAME)
        try:
            # {env}/backup/{tên DB}[-customs]-{thời điểm}.sql.gz → prod và dev không lẫn file backup.
            tag = "" if part == PART_MAIN else f"-{part}"
            key = f"{env_prefix()}/backup/{settings.DB_NAME}{tag}-{started.strftime('%Y%m%d-%H%M%S')}.sql.gz"
            upload_fileobj(tmp, key, "application/gzip")
        finally:
            tmp.close()
        rec.file_key = key
        rec.size_bytes = size
        rec.status = "success"
        rec.finished_at = datetime.now()
        db.commit()
    except Exception as e:  # noqa: BLE001
        db.rollback()
        r = db.get(DbBackup, rec.id)
        if r:
            r.status = "failed"
            r.message = str(e)[:1000]
            r.finished_at = datetime.now()
            db.commit()
        raise
    #  Dọn NGOÀI khối trên: bản đã lên R2 mà bước dọn lỗi thì vẫn là bản thành công — ghi nó
    #  thành failed là để chính nó bị dọn theo tuổi về sau.
    try:
        _prune(db, rec)
    except Exception:  # noqa: BLE001
        db.rollback()
        log.exception("sao lưu: dọn bản cũ lỗi, bản #%s vẫn thành công", rec.id)
    db.refresh(rec)
    return rec


def run_customs_backup(db, *, actor_id: int = 0, source: str = "auto", daily: bool = True):
    """Bản tra cứu thị trường nếu tới hạn (`customs_due`); trả DbBackup hoặc None khi bỏ qua."""
    from .model import DbBackup
    fingerprint = customs_fingerprint(db)
    last = (db.query(DbBackup).filter(DbBackup.part == PART_CUSTOMS, DbBackup.status == "success")
            .order_by(DbBackup.id.desc()).first())
    reason = customs_due(last, fingerprint, daily=daily)
    if not reason:
        log.info("sao lưu: bỏ qua bản tra cứu thị trường (không đổi từ bản #%s)", last.id if last else 0)
        return None
    log.info("sao lưu: chụp bản tra cứu thị trường — %s", reason)
    return _run_part(db, part=PART_CUSTOMS, actor_id=actor_id, source=source, dump_fn=dump_customs_to,
                     fingerprint=fingerprint)


def run_backup(db, actor_id: int = 0, source: str = "auto", with_customs: bool = True):
    """Một lần sao lưu: bản chính, rồi bản tra cứu thị trường nếu tới hạn. Trả DbBackup của bản chính.

    `with_customs=False` (lượt chiều): bản tra cứu thị trường chỉ chụp khi cấu trúc đổi. Bản phụ hỏng thì ghi
    `failed` ở dòng của nó, KHÔNG làm hỏng bản chính vừa xong."""
    rec = _run_part(db, part=PART_MAIN, actor_id=actor_id, source=source, dump_fn=dump_main_to)
    try:
        run_customs_backup(db, actor_id=actor_id, source=source, daily=with_customs)
    except Exception:  # noqa: BLE001
        db.rollback()
        log.exception("sao lưu: bản tra cứu thị trường lỗi, bản chính #%s vẫn thành công", rec.id)
    db.refresh(rec)
    return rec


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
