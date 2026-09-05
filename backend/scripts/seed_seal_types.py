"""Nạp danh mục LOẠI CON DẤU mẫu (Duyệt dấu). Idempotent theo `name` (unique).

Chạy (LOCAL/DEV):  docker compose exec -T api python -m scripts.seed_seal_types
"""
import app.core.all_models  # noqa: F401 — nạp toàn bộ model
from app.core.database import SessionLocal
from app.modules.seal_request.model import SealType

SEAL_TYPES = [
    ("Dấu tròn công ty", "Con dấu pháp nhân (dấu tròn) của công ty"),
    ("Dấu chức danh", "Dấu chức danh của người có thẩm quyền"),
    ("Dấu treo", "Đóng treo trên góc trái văn bản nhiều trang"),
    ("Dấu giáp lai", "Đóng giáp lai giữa các trang của một bộ chứng từ"),
]


def run():
    db = SessionLocal()
    try:
        for name, desc in SEAL_TYPES:
            if db.query(SealType).filter(SealType.name == name).first():
                print(f"  = Đã có: {name}")
                continue
            db.add(SealType(name=name, description=desc, is_active=True))
            print(f"  + Tạo loại con dấu: {name}")
        db.commit()
        print("Xong.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
