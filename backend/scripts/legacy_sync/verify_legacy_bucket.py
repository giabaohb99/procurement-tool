"""Kiểm 1488 tệp `source='datxe'` có đọc được thật từ kho R2 của app cũ không.

Chạy:
    docker compose exec -T -e PYTHONPATH=/app api \
        python -m scripts.legacy_sync.verify_legacy_bucket

Hai chặng, cố ý tách:

1. `head_object` cho TẤT CẢ các dòng — rẻ (không kéo byte), đủ để biết khóa có
   tồn tại và cỡ tệp có khớp cột `size` không. Cỡ lệch là dấu hiệu khóa trúng
   NHẦM một tệp khác, thứ mà phép kiểm "có tồn tại" không bắt được.
2. `get_object` đầy đủ cho một nhúm tệp TÊN XẤU NHẤT (dấu tiếng Việt, khoảng
   trắng, dấu ngoặc) cộng vài tệp nặng nhất. Đây là chỗ ký request S3 dễ gãy,
   và `head_object` đi cùng đường ký nên nếu hỏng thì hỏng từ chặng 1 — chặng 2
   là để chắc phần TRUYỀN cũng xong, không chỉ phần ký.

Không ghi gì xuống DB, không đụng vào kho. Chạy lại bao nhiêu lần cũng được.
"""
from __future__ import annotations

import sys
import unicodedata

from sqlalchemy import text

import app.core.all_models  # noqa: F401  (đăng ký model trước khi mở phiên)
from app.core.database import SessionLocal
from app.core.storage import download_legacy_bytes, legacy_bucket_ready
from app.core.config import settings

#  Số tệp kéo nguyên byte ở chặng 2. Đủ để tin, không đủ để ngồi chờ 5.89 GB.
FULL_READ_SAMPLE = 12


def _client():
    #  Nhập muộn: chỉ chặng kiểm này cần đụng tay vào boto3, mã chạy thật thì
    #  đi qua `storage.download_legacy_bytes`.
    from app.core.storage import _legacy_client
    return _legacy_client()


def _ugliness(key: str) -> int:
    """Điểm 'tên xấu' của một khóa — càng cao càng dễ làm hỏng chữ ký S3."""
    score = sum(1 for ch in key if ord(ch) > 127)          # ký tự ngoài ASCII
    score += key.count(" ") * 2 + key.count("(") * 3
    score += key.count("#") * 5 + key.count("+") * 5 + key.count("%") * 5
    if unicodedata.normalize("NFC", key) != key:
        #  Khóa lưu ở dạng tổ hợp (NFD) — thường do tệp tải lên từ máy Mac.
        score += 50
    return score


def main() -> int:
    if not legacy_bucket_ready():
        print("CHUA CAU HINH: thiếu LEGACY_R2_* trong .env")
        return 2

    print(f"Bucket app cũ: {settings.LEGACY_R2_BUCKET}")
    db = SessionLocal()
    rows = db.execute(text(
        "SELECT id, file_key, filename, size FROM tab_file "
        "WHERE source = 'datxe' ORDER BY id"
    )).fetchall()
    print(f"Số dòng phải kiểm: {len(rows)}")

    s3 = _client()
    bucket = (settings.LEGACY_R2_BUCKET or "").strip()

    missing: list[tuple] = []
    size_mismatch: list[tuple] = []
    errors: list[tuple] = []
    ok = 0

    for i, r in enumerate(rows, 1):
        try:
            head = s3.head_object(Bucket=bucket, Key=r.file_key)
        except Exception as error:
            name = type(error).__name__
            code = getattr(error, "response", {}).get("Error", {}).get("Code", "")
            if code in ("404", "NoSuchKey", "NotFound"):
                missing.append((r.id, r.file_key))
            else:
                errors.append((r.id, f"{name}/{code}", r.file_key))
            continue
        if int(head.get("ContentLength", -1)) != int(r.size or 0):
            size_mismatch.append((r.id, r.size, head.get("ContentLength"), r.file_key))
        else:
            ok += 1
        if i % 200 == 0:
            print(f"  ... {i}/{len(rows)}")

    print("\n--- CHẶNG 1: có mặt + đúng cỡ ---")
    print(f"  khớp hoàn toàn : {ok}")
    print(f"  không tìm thấy : {len(missing)}")
    print(f"  lệch cỡ tệp    : {len(size_mismatch)}")
    print(f"  lỗi khác       : {len(errors)}")
    for row in missing[:10]:
        print(f"    [thiếu] id={row[0]} {row[1]}")
    for row in size_mismatch[:10]:
        print(f"    [lệch cỡ] id={row[0]} DB={row[1]} kho={row[2]} {row[3]}")
    for row in errors[:10]:
        print(f"    [lỗi] id={row[0]} {row[1]} {row[2]}")

    print("\n--- CHẶNG 2: kéo nguyên byte, nhắm tên xấu nhất ---")
    readable = [r for r in rows
                if r.id not in {m[0] for m in missing} | {e[0] for e in errors}]
    ugly = sorted(readable, key=lambda r: _ugliness(r.file_key), reverse=True)
    heavy = sorted(readable, key=lambda r: int(r.size or 0), reverse=True)
    picked, seen = [], set()
    for r in ugly[:FULL_READ_SAMPLE - 3] + heavy[:3]:
        if r.id not in seen:
            seen.add(r.id)
            picked.append(r)

    full_bad = 0
    for r in picked:
        try:
            data = download_legacy_bytes(r.file_key)
        except Exception as error:
            full_bad += 1
            print(f"  HỎNG id={r.id} ({type(error).__name__}) {r.filename}")
            continue
        mark = "OK " if len(data) == int(r.size or 0) else "CỠ LỆCH"
        print(f"  {mark} id={r.id} {len(data):>10} byte  {r.filename[:60]}")

    bad = len(missing) + len(size_mismatch) + len(errors) + full_bad
    print(f"\n{'SACH' if bad == 0 else 'CON ' + str(bad) + ' CHO PHAI XU'}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
