# -*- coding: utf-8 -*-
"""Nạp danh sách XE hiện có của DEGO vào danh mục Quản lý xe (/vehicle-booking/vehicles).

Chạy: docker compose exec -T api python -m scripts.seed_vehicles
Upsert theo `license_plate` (khóa duy nhất) nên chạy lại KHÔNG nhân đôi — xe đã có thì
cập nhật loại/tải cho khớp. Xe THUÊ NGOÀI không có biển: tên gọi để ở cột license_plate.
"""
import app.core.all_models  # noqa: F401 — nạp toàn bộ model để mapper resolve quan hệ
from app.core.database import SessionLocal
from app.modules.vehicle_booking.model import Vehicle

# (biển-số-hoặc-tên, mẫu xe, loại xe, tải người/tấn, thuê ngoài)
VEHICLES = [
    ("51L-423.31", "BMW", "Xe con", 4, False),
    ("51M-15735", "Vinfast Limo Green", "Xe con", 7, False),
    ("65C-172.76", "Toyota Hilux", "Xe bán tải", 5, False),
    ("51D-465.49", "MAZDA BT50", "Xe bán tải", 5, False),
    ("51D-668.25", "Mazda BT50", "Xe bán tải", 5, False),
    ("51D-629.48", "MAZDA BT50", "Xe bán tải", 5, False),
    ("51D-982.44", "Toyota Hilux", "Xe bán tải", 5, False),
    ("65A-096.81", "Toyota Vios", "Xe con", 5, False),
    ("51D-895.00", "ISUZU", "Xe tải", 2.4, False),
    ("51D-853.97", "HYUNDAI", "Xe tải", 6.8, False),
    # Thuê ngoài — không biển số, tên gọi để ở cột biển số.
    ("Xe 4 chỗ thuê", "", "Xe con", 4, True),
    ("Xe tải thuê", "", "Xe tải", 2.4, True),
    ("Xe 7 chỗ thuê", "", "Xe con", 7, True),
]


def main():
    db = SessionLocal()
    created = updated = 0
    try:
        for plate, model, vtype, cap, is_ext in VEHICLES:
            v = db.query(Vehicle).filter(Vehicle.license_plate == plate).first()
            if v is None:
                v = Vehicle(license_plate=plate, created_by=0, updated_by=0)
                db.add(v)
                created += 1
            else:
                updated += 1
            v.model = model
            v.type = vtype
            v.capacity = cap
            v.status = "available"
            v.is_external = is_ext
            v.updated_by = 0
        db.commit()
        print(f"Xe: tạo mới {created}, cập nhật {updated} (tổng {len(VEHICLES)}).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
