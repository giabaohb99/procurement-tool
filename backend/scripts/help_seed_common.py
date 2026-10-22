# -*- coding: utf-8 -*-
"""Phần dùng chung của các script seed Trung tâm trợ giúp MỚI (Công việc, Nhân sự — duoc-CR-670).

Các script seed cũ (nghỉ phép, diễn đàn, văn bản…) mỗi cái chép riêng bộ hàm này; script mới import từ đây
cho khỏi chép lần thứ N. Chạy dạng `python scripts/<tên>.py` nên thư mục scripts đã nằm trong sys.path.

Khuôn: xóa nguyên cây con của thẻ gốc cùng tiêu đề (con trước, cha sau — FK tự tham chiếu không cascade)
rồi dựng lại ở ĐÚNG vị trí cũ; gắn thẻ gốc vào khung «Các Phân hệ» ở trang chủ nếu chưa có.
"""
import re
import sys
import unicodedata

sys.path.insert(0, "/app")

from sqlalchemy import text  # noqa: E402

import app.core.all_models  # noqa: F401,E402 — nạp đủ mapper trước khi query
from app.core.database import SessionLocal  # noqa: E402
from app.modules.help_center.model import HelpArticle, HelpHomeItem, HelpHomeSection  # noqa: E402


def slugify(value: str) -> str:
    """Sinh slug y hệt `slugify()` của help-center (help-slug.tsx); lệch một ký tự là liên kết chết."""
    value = value.replace("đ", "d").replace("Đ", "D")
    value = "".join(c for c in unicodedata.normalize("NFD", value) if unicodedata.category(c) != "Mn")
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9]+", "-", value.lower()))


def ref(target_title: str, label: str) -> str:
    return (f'<a href="/{slugify(target_title)}" '
            f'style="color:var(--primary,#2563eb);font-weight:600;text-decoration:underline">{label}</a>')


def _descendants(db, root_id):
    found, frontier = [(root_id, 0)], [(root_id, 0)]
    while frontier:
        nid, depth = frontier.pop()
        for (cid,) in db.query(HelpArticle.id).filter(HelpArticle.parent_id == nid).all():
            found.append((cid, depth + 1))
            frontier.append((cid, depth + 1))
    return found


def _delete_subtree(db, root_id):
    nodes = _descendants(db, root_id)
    for nid, _ in sorted(nodes, key=lambda x: x[1], reverse=True):
        for table, col in (("tab_help_home_item", "article_id"), ("tab_help_article_slide", "article_id")):
            db.execute(text(f"DELETE FROM {table} WHERE {col} = :id"), {"id": nid})
        db.execute(text("DELETE FROM tab_help_article WHERE id = :id"), {"id": nid})
    db.flush()
    return len(nodes)


def _insert_node(db, node, parent_id, order):
    art = HelpArticle(parent_id=parent_id, title=node["title"], content=node.get("content", ""),
                      summary=node.get("summary"), icon=node.get("icon"), sort_order=order)
    db.add(art)
    db.flush()
    count = 1
    for i, child in enumerate(node.get("children", [])):
        count += _insert_node(db, child, art.id, i)[0]
    return count, art.id


def _attach_home_card(db, article_id):
    section = db.query(HelpHomeSection).filter(HelpHomeSection.key == "categories").first()
    if section is None:
        print("Không thấy khung categories — bỏ qua gắn thẻ trang chủ.")
        return
    last = (db.query(HelpHomeItem.sort_order).filter(HelpHomeItem.section_id == section.id)
            .order_by(HelpHomeItem.sort_order.desc()).first())
    order = (last[0] + 1) if last and last[0] is not None else 0
    db.add(HelpHomeItem(section_id=section.id, article_id=article_id, sort_order=order))
    print(f"Đã gắn thẻ phân hệ vào trang chủ (sort_order={order}).")


def rebuild_tree(tree: dict) -> None:
    """Dựng lại cây `tree` (dict lồng `children`); idempotent theo tiêu đề gốc."""
    db = SessionLocal()
    try:
        old = (db.query(HelpArticle)
               .filter(HelpArticle.title == tree["title"], HelpArticle.parent_id.is_(None)).first())
        order = None
        if old is not None:
            order = old.sort_order
            print(f"Đã xóa cây cũ «{tree['title']}»: {_delete_subtree(db, old.id)} bài (gốc id={old.id}).")
        if order is None:
            last = (db.query(HelpArticle.sort_order).filter(HelpArticle.parent_id.is_(None))
                    .order_by(HelpArticle.sort_order.desc()).first())
            order = (last[0] + 1) if last and last[0] is not None else 0
        total, root_id = _insert_node(db, tree, None, order)
        _attach_home_card(db, root_id)
        db.commit()
        print(f"Đã dựng cây «{tree['title']}»: {total} bài (gốc id={root_id}, sort_order={order}).")
        print("Tiếp theo: docker compose exec -T api python scripts/reindex_help_rag.py")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Bài lẻ dưới thẻ DỰNG TAY (Thu mua, Bắt đầu, Quản trị Hệ thống…) ──────────────────────────────
#  Các cây này không có script sở hữu nên KHÔNG được xóa/dựng lại như `rebuild_tree`: chỉ thêm hoặc
#  ghi đè đúng bài cùng tiêu đề dưới thẻ cha tìm theo TIÊU ĐỀ (id local/dev/prod khác nhau), rồi nạp
#  luôn kho vector cho đúng các bài đó. Bài người dùng tự viết không bao giờ bị đụng; chạy lại vô hại.

def _root(db, title: str):
    return db.query(HelpArticle).filter(HelpArticle.parent_id.is_(None), HelpArticle.title == title).first()


def upsert_articles(articles, dry_run: bool) -> list[int]:
    """`articles` = [(tiêu đề thẻ cha, tiêu đề bài, tóm tắt, HTML)] → id các bài đã ghi."""
    db = SessionLocal()
    touched = []
    try:
        for parent_title, title, summary, content in articles:
            parent = _root(db, parent_title)
            if parent is None:
                print(f"  BỎ QUA «{title}»: không có thẻ cha «{parent_title}» trên hệ này")
                continue
            row = (db.query(HelpArticle)
                   .filter(HelpArticle.parent_id == parent.id, HelpArticle.title == title).first())
            print(f"  {'cập nhật' if row else 'thêm'}: «{title}» (dưới «{parent_title}»)")
            if dry_run:
                continue
            if row is None:
                orders = [a.sort_order or 0 for a in db.query(HelpArticle).filter(HelpArticle.parent_id == parent.id)]
                row = HelpArticle(parent_id=parent.id, title=title, sort_order=max(orders or [0]) + 1)
                db.add(row)
            row.summary, row.content = summary, content
            db.flush()
            touched.append(row.id)
        if not dry_run:
            db.commit()
        return touched
    finally:
        db.close()


def reindex_articles(ids: list[int]) -> None:
    """Nạp kho vector cho đúng các bài vừa ghi; RAG tắt thì bỏ qua (seed ghi ORM nên hook không chạy)."""
    from app.core.config import settings
    if not ids:
        return
    if not settings.AI_RAG_ENABLED:
        print("  RAG đang tắt (AI_RAG_ENABLED=false) — bỏ qua bước nạp kho vector")
        return
    from app.modules.assistant.rag import indexer
    db = SessionLocal()
    try:
        for aid in ids:
            try:
                print(f"  nạp kho vector bài #{aid}: {indexer.reindex_source(db, indexer.SRC_HELP, aid)} đoạn")
            except Exception as exc:  # why: lỗi nạp (429, Qdrant tắt) không làm hỏng bài đã ghi; chạy lại là bù
                print(f"  LỖI nạp bài #{aid}: {type(exc).__name__}: {exc} — chạy lại script để nạp bù")
    finally:
        db.close()


def run_article_upsert(articles, description: str) -> None:
    """`main()` chung của các script bài lẻ: `--dry-run` chỉ in, không ghi."""
    import argparse
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--dry-run", action="store_true", help="chỉ in sẽ làm gì, không ghi")
    args = p.parse_args()
    ids = upsert_articles(articles, args.dry_run)
    if not args.dry_run:
        reindex_articles(ids)
    print("Thử xong, chưa ghi gì." if args.dry_run else "Xong.")
