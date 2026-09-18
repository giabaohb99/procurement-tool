"""Script phục hồi CSDL từ bản sao lưu R2 (ví dụ #72) và chạy lại đồng bộ dữ liệu sạch.

Chạy:
  docker compose -f docker-compose.dev.yml --env-file .env.dev exec api python -m scripts.restore_backup --id 72
"""
import argparse
import gzip
import os
import shutil
import subprocess
import sys

from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine, SessionLocal
from app.core.storage import download_bytes
from app.modules.backup.model import DbBackup
from app.modules.legacy_datxe.tasks import pull_updated


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


def main():
    parser = argparse.ArgumentParser(description="Phục hồi CSDL từ bản sao lưu R2")
    parser.add_argument("--id", type=int, default=72, help="ID bản sao lưu (mặc định 72)")
    parser.add_argument("--sync", action="store_true", default=True, help="Chạy lại pull_updated sau restore")
    args = parser.parse_args()

    db = SessionLocal()
    rec = db.get(DbBackup, args.id)
    if not rec:
        print(f"❌ Không tìm thấy bản sao lưu #{args.id} trong CSDL!")
        sys.exit(1)

    print(f"1. Đang tải tệp sao lưu #{rec.id} ({rec.file_key}) từ Cloudflare R2...")
    try:
        gz_data = download_bytes(rec.file_key)
        sql = gzip.decompress(gz_data)
        print(f"   --> Đã giải nén tệp SQL ({len(sql):,} bytes)")
    except Exception as e:
        print(f"❌ Lỗi tải tệp từ R2: {e}")
        sys.exit(1)

    tmp_path = "/tmp/restore_target.sql"
    with open(tmp_path, "wb") as f:
        f.write(sql)

    db.close()

    print("2. Đóng kết nối cũ & phục hồi dữ liệu vào MySQL...")
    kill_other_connections()

    exe = shutil.which("mysql") or shutil.which("mariadb") or "mysql"
    cmd = [
        exe,
        "-f",
        "-h", settings.DB_HOST,
        "-P", str(settings.DB_PORT),
        "-u", settings.DB_USER,
        settings.DB_NAME,
    ]
    env = dict(os.environ)
    env["MYSQL_PWD"] = settings.DB_PASSWORD

    with open(tmp_path, "rb") as f_in:
        p = subprocess.run(cmd, env=env, stdin=f_in, capture_output=True, text=True)

    if os.path.exists(tmp_path):
        os.remove(tmp_path)

    if p.returncode != 0:
        print(f"❌ Phục hồi CSDL thất bại (code {p.returncode}):\n{p.stderr}")
        sys.exit(1)

    print("✅ SUCCESS: Phục hồi CSDL về bản sao lưu #72 thành công!")

    if args.sync:
        print("3. Đang tự động chạy đồng bộ lại dữ liệu Datxe / Duyệt dấu mới nhất...")
        db_sync = SessionLocal()
        try:
            res = pull_updated(db_sync, start_at=0)
            print(f"✅ SUCCESS: Đã đồng bộ hoàn tất dữ liệu mới! Kết quả: {res}")
        finally:
            db_sync.close()


if __name__ == "__main__":
    main()
