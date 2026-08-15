"""BÀI KIỂM 100 KẾT NỐI — chạy trên MySQL THẬT, không phải SQLite.

    docker compose exec -T api python -m test.backend.check_number_sequence_concurrency

Vì sao tách khỏi pytest: bộ kiểm thử backend chạy SQLite in-memory, mà SQLite
khóa cả tệp nên không mô phỏng được hai transaction tranh nhau một dòng. Thứ cần
chứng minh ở đây — `SELECT ... FOR UPDATE` bắt người thứ hai xếp hàng — chỉ đúng
trên MySQL.

ĐẠT khi: 100 luồng cùng xin cấp số cho CÙNG một sổ → nhận về **đúng 100 số liên
tiếp, không trùng, không nhảy cóc**.

Đây là điều kiện nghiệm thu bắt buộc trước khi mở cấp số trên prod. Không được
bỏ qua vì "chắc là ổn": lỗi này chỉ lộ ra khi có hai người bấm cùng lúc, và lúc
đó thì hai văn bản trùng số đã phát ra ngoài rồi.
"""
import sys
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import text

from app.core.database import SessionLocal
from app.modules.doc_catalog.number_service import next_number

THREADS = 100
SCOPE_KEY = "book:__CHECK_CONCURRENCY__:2026"
YEAR = 2026


def cap_mot_so(_: int) -> int:
    """Một "người dùng": mở transaction riêng, xin số, commit."""
    db = SessionLocal()
    try:
        seq = next_number(db, SCOPE_KEY, YEAR)
        db.commit()
        return seq
    finally:
        db.close()


def main() -> int:
    cleanup = SessionLocal()
    cleanup.execute(text("DELETE FROM tab_number_sequence WHERE scope_key = :k"),
                    {"k": SCOPE_KEY})
    cleanup.commit()
    cleanup.close()

    with ThreadPoolExecutor(max_workers=THREADS) as pool:
        numbers = list(pool.map(cap_mot_so, range(THREADS)))

    ok = sorted(numbers) == list(range(1, THREADS + 1))
    trung = len(numbers) - len(set(numbers))

    print(f"Đã cấp     : {len(numbers)} số")
    print(f"Nhỏ nhất   : {min(numbers)} · lớn nhất: {max(numbers)}")
    print(f"Trùng      : {trung}")
    print(f"Thiếu số   : {sorted(set(range(1, THREADS + 1)) - set(numbers)) or 'không'}")
    print("KẾT QUẢ    :", "ĐẠT" if ok else "KHÔNG ĐẠT")

    final = SessionLocal()
    final.execute(text("DELETE FROM tab_number_sequence WHERE scope_key = :k"),
                  {"k": SCOPE_KEY})
    final.commit()
    final.close()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
