"""SEED PHÒNG HỌP — chạy TAY, cố ý không nằm trong `app/seed.py`.

    docker compose exec api python -m app.seed_dat_phong_hop

Cùng lẽ với `seed_nghi_phep`: danh mục phòng là thứ mỗi công ty tự khai theo
toà nhà của mình, nạp tự động ở mỗi lần khởi động là áp phòng tưởng tượng lên
dữ liệu thật. Chỉ THÊM phòng còn thiếu (so theo `code`), chạy lại được, không
ghi đè phòng người dùng đã sửa.
"""
from app.core.database import SessionLocal
from app.modules.meeting_room.model import MeetingRoom

#  Bộ phòng mẫu. `company_id = 0` = dùng chung mọi pháp nhân — đúng thực tế toà
#  nhà chung, và cũng để thử đúng nhánh "phòng dùng chung" của `list_availability`.
ROOMS = [
    {"code": "P301", "name": "Phòng họp 301", "location": "Tầng 3", "capacity": 8,
     "equipment": "TV 55 inch, bảng trắng", "sort_order": 10},
    {"code": "P302", "name": "Phòng họp 302", "location": "Tầng 3", "capacity": 12,
     "equipment": "Máy chiếu, bảng trắng", "sort_order": 20},
    {"code": "P501", "name": "Hội trường 501", "location": "Tầng 5", "capacity": 60,
     "equipment": "Máy chiếu, âm thanh, micro", "sort_order": 30},
    {"code": "PHOP-NHO", "name": "Phòng trao đổi nhanh", "location": "Tầng 2",
     "capacity": 4, "equipment": "", "sort_order": 40},
]


def seed_rooms() -> int:
    db = SessionLocal()
    added = 0
    try:
        existing = {r[0] for r in db.query(MeetingRoom.code).all()}
        for values in ROOMS:
            if values["code"] in existing:
                continue
            db.add(MeetingRoom(**values, company_id=0, is_active=True,
                               created_by=1, updated_by=1))
            added += 1
        db.commit()
    finally:
        db.close()
    return added


if __name__ == "__main__":
    count = seed_rooms()
    print(f"Đã thêm {count} phòng họp (bỏ qua phòng đã có).")
