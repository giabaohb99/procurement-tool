# -*- coding: utf-8 -*-
"""Seed nội dung Trung tâm trợ giúp cho phân hệ VĂN BẢN (bản 2, 23/09/2026).

Dựng cây: 1 thẻ phân hệ «Hướng dẫn sử dụng Văn bản» (hiện ngoài trang chủ "Các Phân hệ")
-> 7 bài con theo 7 phần của tài liệu HDSD: làm quen · soạn và gửi duyệt · duyệt · ban hành
và sau ban hành · sổ, số hiệu và thiết lập · phân quyền · câu hỏi thường gặp. Bài có ảnh chụp
màn hình đánh dấu số và sơ đồ luồng.

⚠️ Nội dung KHÔNG viết ở đây. Nguồn là `doc/huong-dan-su-dung/van-ban/huong-dan-su-dung-van-ban.md`
(+ `gioi-thieu-nhanh-van-ban.md` cho bài gốc). Thư mục `doc/` không có trong container, nên
nội dung được đóng gói sẵn vào `scripts/help_van_ban/` bằng
`doc/huong-dan-su-dung/van-ban/dong-goi-hdsd-cho-seed.py`. Sửa tài liệu thì chạy lại script
đóng gói, commit thư mục gói, rồi chạy lại seed này.

THAY bộ HDSD văn thư cũ: cây «Hướng dẫn sử dụng công cụ văn thư» (seed_help_van_thu.py, chia
theo vai trò) bị xóa nếu còn — không để người dùng thấy hai bộ hướng dẫn cho cùng phân hệ.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_van_ban.py
    # rồi nạp bài mới vào kho tìm kiếm của trợ lý AI (seed ghi thẳng ORM nên hook không bắn):
    docker compose exec -T api python scripts/reindex_help_rag.py

Idempotent:
  - Cây cũ (cùng tiêu đề gốc) bị xóa nguyên cây con rồi dựng lại, GIỮ vị trí gốc cũ.
  - Ảnh tải lên kho với key CỐ ĐỊNH `{env}/help_center/van-ban/<tên tệp>` — chạy lại là ghi
    đè đúng chỗ, không sinh bản sao.
"""
import json
import os
import sys

sys.path.insert(0, "/app")

from sqlalchemy import text  # noqa: E402

import app.core.all_models  # noqa: F401,E402 — nạp đủ mapper trước khi query
from app.core.database import SessionLocal  # noqa: E402
from app.core.storage import env_prefix, upload_fileobj  # noqa: E402
from app.modules.help_center.model import (  # noqa: E402
    HelpArticle,
    HelpHomeItem,
    HelpHomeSection,
)

BUNDLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "help_van_ban")
IMG_PLACEHOLDER = "__HINH__"
# Các cây bị thay thế: tiêu đề gốc của bộ cũ + chính bộ này (để chạy lại được).
OLD_ROOT_TITLES = ("Hướng dẫn sử dụng công cụ văn thư",)


def upload_images() -> dict[str, str]:
    """Tải mọi ảnh trong gói lên kho, trả {tên tệp: URL}."""
    urls = {}
    folder = os.path.join(BUNDLE, "hinh")
    for name in sorted(os.listdir(folder)):
        key = f"{env_prefix()}/help_center/van-ban/{name}"
        ctype = "image/webp" if name.endswith(".webp") else "image/png"
        with open(os.path.join(folder, name), "rb") as f:
            urls[name] = upload_fileobj(f, key, ctype)
    print(f"Đã tải {len(urls)} ảnh lên kho.")
    return urls


def fill_images(html: str, urls: dict[str, str]) -> str:
    for name, url in urls.items():
        html = html.replace(f"{IMG_PLACEHOLDER}/{name}", url)
    if IMG_PLACEHOLDER in html:
        raise RuntimeError("Còn ảnh trong bài mà gói không có — chạy lại script đóng gói.")
    return html


def collect_descendants(db, root_id):
    """Trả [(id, độ sâu)] của cả cây, gồm chính gốc."""
    found = [(root_id, 0)]
    frontier = [(root_id, 0)]
    while frontier:
        nid, depth = frontier.pop()
        for (cid,) in db.query(HelpArticle.id).filter(HelpArticle.parent_id == nid).all():
            found.append((cid, depth + 1))
            frontier.append((cid, depth + 1))
    return found


def delete_subtree(db, root_id):
    nodes = collect_descendants(db, root_id)
    #  Xóa RAW theo thứ tự sâu-trước: FK tự tham chiếu parent_id KHÔNG cascade.
    for nid, _ in sorted(nodes, key=lambda x: x[1], reverse=True):
        db.execute(text("DELETE FROM tab_help_home_item WHERE article_id = :id"), {"id": nid})
        db.execute(text("DELETE FROM tab_help_article_slide WHERE article_id = :id"), {"id": nid})
        db.execute(text("DELETE FROM tab_help_article WHERE id = :id"), {"id": nid})
    db.flush()
    return len(nodes)


def insert_node(db, node, parent_id, order, urls):
    art = HelpArticle(
        parent_id=parent_id,
        title=node["title"],
        content=fill_images(node.get("content", ""), urls),
        summary=node.get("summary"),
        icon=node.get("icon"),
        sort_order=order,
    )
    db.add(art)
    db.flush()
    count = 1
    for i, child in enumerate(node.get("children", []), start=1):
        count += insert_node(db, child, art.id, i, urls)[0]
    return count, art.id


def attach_home_card(db, article_id):
    """Gắn thẻ phân hệ vào khung "Các Phân hệ" trang chủ nếu chưa có."""
    section = db.query(HelpHomeSection).filter(HelpHomeSection.key == "categories").first()
    if section is None:
        print("Không thấy khung categories — bỏ qua gắn thẻ trang chủ.")
        return
    max_order = (
        db.query(HelpHomeItem.sort_order)
        .filter(HelpHomeItem.section_id == section.id)
        .order_by(HelpHomeItem.sort_order.desc())
        .first()
    )
    next_order = (max_order[0] + 1) if max_order and max_order[0] is not None else 0
    db.add(HelpHomeItem(section_id=section.id, article_id=article_id, sort_order=next_order))
    print(f"Đã gắn thẻ phân hệ vào trang chủ (sort_order={next_order}).")


def main():
    with open(os.path.join(BUNDLE, "bai-viet.json"), encoding="utf-8") as f:
        tree = json.load(f)

    db = SessionLocal()
    try:
        # Giữ vị trí của cây cũ (nếu có) để bộ mới đứng đúng chỗ bộ cũ trong danh mục.
        keep_order = None
        for title in (tree["title"], *OLD_ROOT_TITLES):
            old = (db.query(HelpArticle)
                   .filter(HelpArticle.title == title, HelpArticle.parent_id.is_(None)).first())
            if old is not None:
                keep_order = old.sort_order if keep_order is None else keep_order
                removed = delete_subtree(db, old.id)
                print(f"Đã xóa cây «{title}»: {removed} bài (gốc id={old.id}).")

        if keep_order is None:
            max_order = (
                db.query(HelpArticle.sort_order)
                .filter(HelpArticle.parent_id.is_(None))
                .order_by(HelpArticle.sort_order.desc())
                .first()
            )
            keep_order = (max_order[0] + 1) if max_order and max_order[0] is not None else 0

        urls = upload_images()
        total, root_id = insert_node(db, tree, None, keep_order, urls)
        attach_home_card(db, root_id)
        db.commit()
        print(f"Đã dựng cây Văn bản: {total} bài (gốc id={root_id}, sort_order={keep_order}).")
        print("Tiếp theo: docker compose exec -T api python scripts/reindex_help_rag.py")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
