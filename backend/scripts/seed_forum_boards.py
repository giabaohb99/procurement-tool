# -*- coding: utf-8 -*-
"""Dựng bộ chuyên mục diễn đàn chuẩn — 4 nhóm / 12 box (thiết kế 03/09/2026).

Chạy trong container api:
    docker compose exec -T api python scripts/seed_forum_boards.py

Idempotent theo TÊN: nhóm/box trùng tên thì UPDATE tại chỗ (giữ id — bài đã
đăng trong box không lạc); tên chưa có thì tạo mới; box NGOÀI thiết kế giữ
nguyên không đụng (vd box ẩn thử nghiệm). Icon phải nằm trong BOARD_ICONS của
`frontend-v2/src/modules/forum/components/board-icon.tsx`, tên lạ rơi về icon
mặc định.
"""
import sys

sys.path.insert(0, "/app")

import app.core.all_models  # noqa: F401,E402 — nạp đủ mapper trước khi query
from app.core.database import SessionLocal  # noqa: E402
from app.modules.forum.model import ForumBoard, ForumBoardStatus  # noqa: E402

# (tên nhóm, sort, [(tên box, icon, mô tả)])
DESIGN = [
    ("Thông báo & Chính sách", 0, [
        ("Thông báo công ty", "megaphone",
         "Thông báo chính thức từ Ban lãnh đạo, HR và các phòng ban"),
        ("Nội quy & chính sách", "book",
         "Nội quy, quy định, chính sách và quy trình áp dụng toàn tập đoàn"),
        ("Khen thưởng & vinh danh", "trophy",
         "Vinh danh cá nhân, tập thể xuất sắc; thông báo khen thưởng"),
    ]),
    ("Công việc", 1, [
        ("Trao đổi nghiệp vụ", "briefcase",
         "Bàn việc chung giữa các phòng ban: thu mua, kho, tài chính, sản xuất"),
        ("Hỏi đáp nghiệp vụ", "help-circle",
         "Thắc mắc về quy trình, chứng từ, phân quyền — hỏi là có người đáp"),
        ("Góp ý & sáng kiến", "lightbulb",
         "Đề xuất cải tiến quy trình, công cụ làm việc, sản phẩm"),
        ("Mẹo dùng hệ thống ERP", "cpu",
         "Hướng dẫn, thủ thuật và hỏi đáp khi dùng ERP nội bộ"),
    ]),
    ("Văn hóa & Sự kiện", 2, [
        ("Sự kiện & hoạt động", "camera",
         "Sự kiện công ty, team building, hình ảnh hoạt động nội bộ"),
        ("Chúc mừng & sinh nhật", "heart",
         "Chúc mừng sinh nhật, tin vui, thành viên mới, cột mốc của đồng nghiệp"),
        ("Thể thao & giải trí", "gamepad-2",
         "Kèo thể thao, game và giải trí sau giờ làm"),
    ]),
    ("Đời sống", 3, [
        ("Góc chia sẻ", "coffee",
         "Chuyện trò tự do: cà phê, du lịch, ảnh đẹp, chuyện đời thường"),
        ("Mua bán trao đổi", "shopping-cart",
         "Chợ nội bộ: mua bán, cho tặng, trao đổi đồ dùng giữa đồng nghiệp"),
    ]),
]

# Box đời cũ đổi vai trò: đổi tên TRƯỚC khi khớp thiết kế để giữ id.
RENAME = {"Thông báo chung": "Trao đổi nghiệp vụ"}


def main() -> None:
    db = SessionLocal()
    try:
        by_name: dict[str, ForumBoard] = {}
        for board in db.query(ForumBoard).all():
            name = RENAME.get(board.name, board.name)
            if name != board.name:
                print(f"Đổi tên box id={board.id}: {board.name!r} -> {name!r}")
                board.name = name
            by_name[name] = board

        for group_name, group_sort, boxes in DESIGN:
            group = by_name.get(group_name)
            if group is None:
                group = ForumBoard(name=group_name, parent_id=None)
                db.add(group)
                db.flush()
                print(f"Tạo nhóm mới: {group_name!r} (id={group.id})")
                by_name[group_name] = group
            group.parent_id = None
            group.sort_order = group_sort
            group.status = int(ForumBoardStatus.ACTIVE)
            group.description = ""
            group.icon = ""
            for box_sort, (box_name, icon, description) in enumerate(boxes):
                box = by_name.get(box_name)
                if box is None:
                    box = ForumBoard(name=box_name)
                    db.add(box)
                    db.flush()
                    print(f"Tạo box mới: {box_name!r} (id={box.id})")
                    by_name[box_name] = box
                box.parent_id = group.id
                box.sort_order = box_sort
                box.icon = icon
                box.description = description
                box.status = int(ForumBoardStatus.ACTIVE)

        db.commit()
        print("--- KẾT QUẢ ---")
        groups = (
            db.query(ForumBoard)
            .filter(ForumBoard.parent_id.is_(None))
            .order_by(ForumBoard.sort_order)
            .all()
        )
        for group in groups:
            print(f"[{group.id}] {group.name}")
            children = (
                db.query(ForumBoard)
                .filter(ForumBoard.parent_id == group.id)
                .order_by(ForumBoard.sort_order)
                .all()
            )
            for box in children:
                print(f"    ({box.id}) {box.name} — {box.icon} — status={box.status}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
