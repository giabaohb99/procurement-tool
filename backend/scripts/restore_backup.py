"""Script phục hồi CSDL từ bản sao lưu R2 (ví dụ #72) và chạy lại đồng bộ dữ liệu sạch.

Chạy:
  docker compose -f docker-compose.dev.yml --env-file .env.dev exec api python -m scripts.restore_backup --id 72

**Dừng ngay ở lỗi đầu tiên (phiếu kh-sao-luu-dung, 22/10/2026).** Bản cũ chạy client
với `-f` (bỏ qua lỗi, nạp tiếp) rồi in SUCCESS: bản dump hỏng ở cột sinh (lỗi 3105)
vẫn «thành công», ra một CSDL thiếu dòng mà không ai biết. Nay client chạy KHÔNG có
`-f`, mã thoát khác 0 thì in lỗi và thoát mã 1, không chạy bước nào phía sau.

**Chỉ mục tìm văn bản (bẫy từ dừng FULLTEXT ngram, migration `83679db84fd1`).**
Bản dump dựng lại 4 chỉ mục FULLTEXT của `tab_document_search` ngay ở câu
CREATE TABLE, đọc `innodb_ft_enable_stopword` từ SESSION đang nạp — mặc định là BẬT,
tức tìm «văn», «bản», «toàn» sẽ ra rỗng. Nên phiên nạp đặt sẵn
`SET SESSION innodb_ft_enable_stopword = 0` qua `--init-command`, và nạp xong thì
kiểm lại bằng chính `reindex_documents.check_stopwords_disabled` (hỏng thì
`fix_stopwords` dựng lại 4 chỉ mục).
"""
import argparse
import gzip
import os
import re
import shutil
import subprocess
import sys

from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine, SessionLocal
from app.core.storage import download_bytes
from app.modules.backup.model import DbBackup
from app.modules.legacy_datxe.tasks import pull_updated

#  Đặt cho riêng phiên nạp: chỉ mục FULLTEXT dựng ở CREATE TABLE đọc biến này từ SESSION.
RESTORE_INIT_SQL = "SET SESSION innodb_ft_enable_stopword = 0"


def kill_other_connections():
    """Hủy các kết nối đang mở tới database để giải phóng Metadata Locks (MDL)."""
    with engine.connect() as conn:
        try:
            # Tìm tất cả process_id của db này trừ kết nối hiện tại
            res = conn.execute(text(
                "SELECT id FROM information_schema.processlist "
                "WHERE db = :dbname AND id != CONNECTION_ID()"
            ), {"dbname": settings.DB_NAME})
            pids = [row[0] for row in res.fetchall()]
            for pid in pids:
                try:
                    conn.execute(text(f"KILL {pid}"))
                except Exception:
                    pass
            print(f"--> Đã đóng {len(pids)} kết nối đang chờ tới CSDL '{settings.DB_NAME}'")
        except Exception as e:
            print(f"--> Không thể ngắt kết nối cũ: {e}")


def build_restore_command(exe: str) -> list[str]:
    """Dòng lệnh nạp bản dump. CỐ Ý không có `-f`/`--force`: lỗi đầu tiên là dừng."""
    return [
        exe,
        "--default-character-set=utf8mb4",
        f"--init-command={RESTORE_INIT_SQL}",
        "-h", settings.DB_HOST,
        "-P", str(settings.DB_PORT),
        "-u", settings.DB_USER,
        settings.DB_NAME,
    ]


#  Neo ĐẦU DÒNG (re.M): mysqldump thoát ký tự xuống dòng trong dữ liệu thành `\n`, nên một chuỗi
#  y hệt nằm trong câu INSERT không bao giờ đứng ở đầu dòng — không bị đếm nhầm.
_DUMP_HEADER = re.compile(rb"^-- MySQL dump ", re.MULTILINE)
_MARIADB_HEADER = re.compile(rb"^-- MariaDB dump ", re.MULTILINE)
_DUMP_FOOTER = re.compile(rb"^-- Dump completed", re.MULTILINE)
_CREATE_TABLE = re.compile(rb"^CREATE TABLE `([^`]+)`", re.MULTILINE)


def check_dump_complete(sql: bytes) -> str:
    """Bản dump có trọn vẹn không? Trả lý do hỏng (chuỗi rỗng = đủ).

    mysqldump ghi `-- Dump completed on ...` ở dòng cuối mỗi lượt. Bản sao lưu ERP nối HAI
    lượt (QĐ-C) nên mỗi dòng đầu `-- MySQL dump` phải có một dòng kết, và dòng kết cuối cùng
    phải là phần cuối tệp (chỉ còn khoảng trắng phía sau).
    """
    if _MARIADB_HEADER.search(sql):
        return ("đây là bản dump của MariaDB (mariadb-dump, image api cũ) — KHÔNG nạp được vào "
                "MySQL 8.4 (lỗi 3105 ở cột sinh); dùng bản sao lưu tạo sau khi dựng lại image")
    headers = len(_DUMP_HEADER.findall(sql))
    footers = list(_DUMP_FOOTER.finditer(sql))
    if not headers:
        return "không thấy dòng đầu '-- MySQL dump' — không phải bản dump của mysqldump"
    if len(footers) < headers:
        return f"bản dump cụt: {headers} lượt dump nhưng chỉ {len(footers)} dòng '-- Dump completed'"
    tail = sql[footers[-1].start():]
    if b"\n" in tail.rstrip():
        return "bản dump cụt: tệp không kết bằng dòng '-- Dump completed'"
    return ""


def dump_table_names(sql: bytes) -> set[str]:
    """Tên mọi bảng bản dump sẽ tạo (kể cả bảng giữ chỗ của view)."""
    return {m.decode("utf-8", errors="replace") for m in _CREATE_TABLE.findall(sql)}


def live_table_names() -> set[str]:
    """Tên mọi bảng / view đang có trong CSDL đích sau khi nạp."""
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT table_name FROM information_schema.tables "
                                 "WHERE table_schema = :s"), {"s": settings.DB_NAME}).all()
    return {r[0] for r in rows}


def ensure_fulltext_stopwords_off() -> None:
    """Nạp xong: chỉ mục tìm văn bản phải tra được chữ «văn»; không thì dựng lại 4 chỉ mục.

    Bản sao lưu cũ (trước duoc-CR-477) không có `tab_document_search` thì bỏ qua —
    `alembic upgrade head` lúc khởi động sẽ tạo bảng đúng cách.
    """
    from scripts.reindex_documents import check_stopwords_disabled, fix_stopwords

    db = SessionLocal()
    try:
        has_table = db.execute(text(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = :s AND table_name = 'tab_document_search'"
        ), {"s": settings.DB_NAME}).scalar()
        if not has_table:
            print("   --> Không có bảng tab_document_search, bỏ qua kiểm chỉ mục tìm văn bản.")
            return
        if check_stopwords_disabled(db):
            print("   --> Chỉ mục tìm văn bản đạt (không lọc từ dừng).")
            return
        print("   --> Chỉ mục tìm văn bản đang lọc từ dừng, dựng lại với từ dừng tắt...")
        fix_stopwords(db)
        if not check_stopwords_disabled(db):
            raise RuntimeError("dựng lại xong vẫn lọc từ dừng — chạy tay "
                               "scripts/reindex_documents.py --fix-stopwords và kiểm lại")
        print("   --> Đã dựng lại chỉ mục tìm văn bản.")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Phục hồi CSDL từ bản sao lưu R2")
    parser.add_argument("--id", type=int, default=72, help="ID bản sao lưu (mặc định 72)")
    parser.add_argument("--sync", action="store_true", default=True, help="Chạy lại pull_updated sau restore")
    args = parser.parse_args()

    db = SessionLocal()
    rec = db.get(DbBackup, args.id)
    if not rec:
        print(f"LỖI: Không tìm thấy bản sao lưu #{args.id} trong CSDL!")
        sys.exit(1)
    if rec.status != "success" or not rec.file_key:
        print(f"LỖI: Bản sao lưu #{rec.id} không ở trạng thái thành công (status={rec.status!r}), không nạp.")
        sys.exit(1)

    print(f"1. Đang tải tệp sao lưu #{rec.id} ({rec.file_key}) từ Cloudflare R2...")
    try:
        gz_data = download_bytes(rec.file_key)
        sql = gzip.decompress(gz_data)
        print(f"   --> Đã giải nén tệp SQL ({len(sql):,} bytes)")
    except Exception as e:
        print(f"LỖI: Không tải/giải nén được tệp từ R2: {e}")
        sys.exit(1)

    #  Kiểm TRƯỚC khi ngắt kết nối / nạp: bản cụt thì CSDL đang chạy còn nguyên.
    broken = check_dump_complete(sql)
    if broken:
        print(f"LỖI: Bản sao lưu #{rec.id} không nạp được — {broken}. CSDL chưa bị đụng tới.")
        sys.exit(1)
    expected_tables = dump_table_names(sql)
    print(f"   --> Bản dump đủ, sẽ tạo {len(expected_tables)} bảng")

    tmp_path = "/tmp/restore_target.sql"
    with open(tmp_path, "wb") as f:
        f.write(sql)

    db.close()

    print("2. Đóng kết nối cũ & phục hồi dữ liệu vào MySQL (dừng ngay ở lỗi đầu tiên)...")
    kill_other_connections()

    exe = shutil.which("mysql") or shutil.which("mariadb") or "mysql"
    cmd = build_restore_command(exe)
    env = dict(os.environ)
    env["MYSQL_PWD"] = settings.DB_PASSWORD

    try:
        with open(tmp_path, "rb") as f_in:
            p = subprocess.run(cmd, env=env, stdin=f_in, capture_output=True, text=True)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    if p.returncode != 0:
        print(f"LỖI: Phục hồi CSDL THẤT BẠI (mã {p.returncode}) — CSDL có thể đang nạp dở, "
              f"KHÔNG dùng cho tới khi nạp lại được:\n{p.stderr}")
        sys.exit(1)
    if p.stderr and p.stderr.strip():
        print(f"   --> Client báo (không phải lỗi):\n{p.stderr.strip()}")

    missing = sorted(expected_tables - live_table_names())
    if missing:
        print(f"LỖI: Nạp xong nhưng thiếu {len(missing)}/{len(expected_tables)} bảng có trong bản dump: "
              f"{', '.join(missing[:20])}")
        sys.exit(1)
    print(f"   --> Đủ {len(expected_tables)} bảng của bản dump")

    print("3. Kiểm chỉ mục tìm văn bản (từ dừng FULLTEXT)...")
    try:
        ensure_fulltext_stopwords_off()
    except Exception as e:  # noqa: BLE001
        print(f"LỖI: Đã nạp dữ liệu nhưng chỉ mục tìm văn bản hỏng: {e}")
        sys.exit(1)

    print(f"XONG: Phục hồi CSDL về bản sao lưu #{rec.id}.")

    if args.sync:
        print("4. Đang tự động chạy đồng bộ lại dữ liệu Datxe / Duyệt dấu mới nhất...")
        db_sync = SessionLocal()
        try:
            res = pull_updated(db_sync, start_at=0)
            print(f"XONG: Đã đồng bộ hoàn tất dữ liệu mới! Kết quả: {res}")
        finally:
            db_sync.close()


if __name__ == "__main__":
    main()
