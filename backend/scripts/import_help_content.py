"""Nạp nội dung Trung tâm Hướng dẫn (bài viết + câu hỏi thường gặp) từ file JSON xuất sẵn.

Nguồn: app/seed_data/help-center-content.json (nằm trong image, không cần copy tay).
Nội dung Help Center nằm trong DB chứ không phải file repo, nên soạn ở máy này xong không
tự có ở dev/prod — file JSON là bản mang đi, script này là bản nạp.

Khớp theo TIÊU ĐỀ bài viết (và theo CÂU HỎI với FAQ):
  - Đã có  -> cập nhật nội dung / mô tả / icon / thứ tự / cha.
  - Chưa có -> tạo mới.
  - Bài viết trong DB mà file không có -> GIỮ NGUYÊN, chỉ liệt kê ra để người chạy tự quyết.
Không xóa gì cả.

`parent_id` trong file trỏ tới `id` trong CHÍNH file đó, KHÔNG phải id của môi trường đích,
nên phải tạo cha trước rồi map id cũ -> id mới (file đã sắp sẵn cha trước con).

Chạy thử (mặc định, không ghi gì):
    docker exec -w /app <api> python -m scripts.import_help_content
Nạp thật:
    docker exec -w /app <api> python -m scripts.import_help_content --nap
"""
import json
import os
import sys

import app.core.all_models  # noqa: F401  (đăng ký mapper)
from app.core.database import SessionLocal
from app.modules.faq.model import Faq
from app.modules.help_center.model import HelpArticle
from app.modules.role.model import Role
from app.modules.user.model import UserRole

JSON_PATH = os.environ.get("HELP_JSON", "/app/app/seed_data/help-center-content.json")
NAP = "--nap" in sys.argv


def actor_id(db) -> int:
    """Người thực hiện = một tài khoản quản trị bất kỳ (cột created_by/updated_by)."""
    role = db.query(Role).filter(Role.code == "admin").first()
    ur = db.query(UserRole).filter(UserRole.role_id == role.id).first() if role else None
    return ur.user_id if ur else 1


def main() -> None:
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    db = SessionLocal()
    me = actor_id(db)
    print(f"File: {JSON_PATH} (xuất từ {data.get('exported_from')}) — "
          f"{len(data['articles'])} bài viết, {len(data['faqs'])} câu hỏi")
    print(f"Chế độ: {'NẠP THẬT' if NAP else 'CHẠY THỬ (không ghi gì)'} — người thực hiện: user #{me}")
    print("-" * 78)

    # ---------------------------------------------------------------- bài viết
    ten_cu = {a.title: a for a in db.query(HelpArticle).all()}
    id_map: dict[int, int] = {}          # id trong file -> id thật ở môi trường này
    them = capnhat = 0
    for a in data["articles"]:
        cha = id_map.get(a["parent_id"]) if a.get("parent_id") else None
        obj = ten_cu.get(a["title"])
        if obj:
            capnhat += 1
            print(f"  ~ cập nhật  #{obj.id:<4} {a['title']}")
            if NAP:
                obj.parent_id = cha
                obj.content = a.get("content") or ""
                obj.sort_order = a.get("sort_order") or 0
                obj.summary = a.get("summary")
                obj.icon = a.get("icon")
                obj.updated_by = me
                db.flush()
            id_map[a["id"]] = obj.id
        else:
            them += 1
            print(f"  + thêm mới       {a['title']}")
            if NAP:
                obj = HelpArticle(
                    parent_id=cha, title=a["title"], content=a.get("content") or "",
                    sort_order=a.get("sort_order") or 0, summary=a.get("summary"),
                    icon=a.get("icon"), created_by=me, updated_by=me)
                db.add(obj)
                db.flush()
                id_map[a["id"]] = obj.id
            else:
                id_map[a["id"]] = -a["id"]   # chạy thử: giữ chỗ để map cha-con không vỡ

    du = sorted(set(ten_cu) - {a["title"] for a in data["articles"]})
    if du:
        print(f"\n  Bài viết CÓ trong DB mà file không có ({len(du)}) — giữ nguyên:")
        for t in du:
            print(f"    ? {t}")

    # ------------------------------------------------------------- câu hỏi FAQ
    print("")
    hoi_cu = {q.question: q for q in db.query(Faq).all()}
    f_them = f_capnhat = 0
    for q in data["faqs"]:
        obj = hoi_cu.get(q["question"])
        if obj:
            f_capnhat += 1
            if NAP:
                obj.answer = q.get("answer") or ""
                obj.sort_order = q.get("sort_order") or 0
                obj.is_active = bool(q.get("is_active", True))
                obj.updated_by = me
        else:
            f_them += 1
            if NAP:
                db.add(Faq(question=q["question"], answer=q.get("answer") or "",
                           sort_order=q.get("sort_order") or 0,
                           is_active=bool(q.get("is_active", True)),
                           created_by=me, updated_by=me))
    print(f"  Câu hỏi thường gặp: thêm {f_them}, cập nhật {f_capnhat}")

    if NAP:
        db.commit()
    print("-" * 78)
    print(f"Bài viết: thêm {them}, cập nhật {capnhat}. "
          f"{'ĐÃ GHI VÀO DB.' if NAP else 'Chạy thử — chưa ghi gì.'}")
    print(f"Tổng sau khi chạy: {db.query(HelpArticle).count()} bài viết, "
          f"{db.query(Faq).count()} câu hỏi")
    db.close()


if __name__ == "__main__":
    main()
