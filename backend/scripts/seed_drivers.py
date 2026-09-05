# -*- coding: utf-8 -*-
"""Nạp danh sách TÀI XẾ hiện có của DEGO vào danh mục Quản lý tài xế.

Chạy: docker compose exec -T api python -m scripts.seed_drivers
Upsert theo (TÊN, SĐT) nên chạy lại không nhân đôi (hai tài xế thuê ngoài trùng SĐT
vẫn tách được bằng tên). Giá trị B2/C là HẠNG GPLX -> vào cột license_class; số GPLX
thật chưa có nên để trống. KHÔNG đụng user_id của tài xế đã liên kết tài khoản.
"""
import app.core.all_models  # noqa: F401 — nạp toàn bộ model để mapper resolve quan hệ
from app.core.database import SessionLocal
from app.modules.vehicle_booking.model import Driver

# (tên, SĐT, hạng GPLX, thuê ngoài)
DRIVERS = [
    ("Trần Minh Sang", "0773399588", "B2", False),
    ("Lê Minh Thông", "0907507103", "B2", False),
    ("Lưu Nhựt Minh", "0937187336", "B2", False),
    ("Võ Huỳnh Nhật Khoa", "0913007113", "C", False),
    ("Tài xế thuê ngoài", "0971445134", "", True),
    ("Trần Quốc Thái", "0932783785", "C", False),
    ("Lê Tấn Nhựt", "0775959935", "B2", False),
    ("Trần Quang Huy", "0944074191", "B2", False),
    ("Lê Vỹ Khang", "0923992996", "C", False),
    ("Đào Quốc Triệu", "0794964718", "B2", False),
    ("Huỳnh Quang Tín", "0971252340", "B2", False),
    ("Lê Lâm Tùng", "0898087229", "C", False),
    ("Tự lái", "0971445134", "B2", True),
]


def main():
    db = SessionLocal()
    created = updated = 0
    try:
        for name, phone, klass, is_ext in DRIVERS:
            d = db.query(Driver).filter(Driver.name == name, Driver.phone == phone).first()
            if d is None:
                d = Driver(name=name, phone=phone, user_id=None, created_by=0, updated_by=0)
                db.add(d)
                created += 1
            else:
                updated += 1
            d.license_class = klass       # B2/C là HẠNG
            d.license_number = ""          # số GPLX thật chưa có
            d.status = "available"
            d.is_external = is_ext
            d.updated_by = 0
        db.commit()
        print(f"Tài xế: tạo mới {created}, cập nhật {updated} (tổng {len(DRIVERS)}).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
