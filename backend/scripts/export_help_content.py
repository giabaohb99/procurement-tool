"""Xuất nội dung Trung tâm Hướng dẫn (bài viết + câu hỏi thường gặp) ra file JSON.

Đối xứng với `import_help_content.py`. Nội dung Help Center nằm trong DB chứ không phải
file repo, nên soạn ở môi trường nào chỉ có ở đó — muốn mang từ dev sang prod thì xuất ở
bên này rồi nạp ở bên kia. File xuất ra đúng định dạng mà script nạp đang đọc.

CHA TRƯỚC CON: script nạp map `parent_id` trong file sang id thật của môi trường đích theo
thứ tự đọc, nên bài cha bắt buộc phải đứng trước bài con trong danh sách. Ở đây sắp bằng
cách duyệt cây theo chiều sâu, không phải sắp theo id — id ở 2 môi trường không liên quan
gì tới nhau.

KHÔNG xuất `tab_help_article_slide` (ảnh minh hoạ từng bước): ảnh gắn theo id bài viết mà
id 2 bên khác nhau, và bộ ảnh hiện tại là dữ liệu mẫu seed sẵn giống nhau ở mọi môi trường.
Khi nào có ảnh soạn thật thì mở rộng thêm, đừng đoán bừa ở đây.

Chạy TRONG container api:
    docker exec -w /app <api> python -m scripts.export_help_content            # ra /app/help-export.json
    docker exec -w /app <api> python -m scripts.export_help_content /app/x.json
"""
import json
import os
import sys

import app.core.all_models  # noqa: F401  (đăng ký mapper)
from app.core.database import SessionLocal
from app.modules.faq.model import Faq
from app.modules.help_center.model import HelpArticle

OUT = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "/app/help-export.json"
NOTE = ("Nội dung Trung tâm Hướng dẫn sử dụng (bài viết + câu hỏi thường gặp). parent_id tham "
        "chiếu tới id trong CHÍNH file này — script nạp phải map lại sang id thật của môi "
        "trường đích, không dùng thẳng.")


def main() -> None:
    db = SessionLocal()
    rows = db.query(HelpArticle).all()
    con: dict[int | None, list] = {}
    for a in rows:
        con.setdefault(a.parent_id, []).append(a)
    for ds in con.values():
        ds.sort(key=lambda a: (a.sort_order or 0, a.id))

    articles: list[dict] = []

    def di(cha: int | None) -> None:
        for a in con.get(cha, []):
            articles.append({
                "id": a.id, "parent_id": a.parent_id, "title": a.title,
                "sort_order": a.sort_order or 0, "summary": a.summary, "icon": a.icon,
                "content": a.content or "",
            })
            di(a.id)

    di(None)
    if len(articles) != len(rows):
        # Bài có parent_id trỏ tới bài đã xoá thì không nằm trong cây -> vét nốt, để cuối.
        thieu = {a.id for a in rows} - {a["id"] for a in articles}
        print(f"CẢNH BÁO: {len(thieu)} bài mồ côi (parent_id trỏ tới bài không còn) — xuất kèm, "
              f"nạp sang sẽ thành bài gốc: {sorted(thieu)}")
        for a in rows:
            if a.id in thieu:
                articles.append({
                    "id": a.id, "parent_id": None, "title": a.title,
                    "sort_order": a.sort_order or 0, "summary": a.summary, "icon": a.icon,
                    "content": a.content or "",
                })

    faqs = [{"id": q.id, "question": q.question, "answer": q.answer or "",
             "sort_order": q.sort_order or 0, "is_active": bool(q.is_active)}
            for q in db.query(Faq).order_by(Faq.sort_order, Faq.id).all()]

    data = {"version": 1, "exported_from": os.environ.get("DB_NAME", "?"),
            "note": NOTE, "articles": articles, "faqs": faqs}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    goc = sum(1 for a in articles if not a["parent_id"])
    chu = sum(len(a["content"]) for a in articles)
    print(f"Đã xuất {len(articles)} bài viết ({goc} mục gốc, {chu:,} ký tự nội dung) "
          f"và {len(faqs)} câu hỏi ra {OUT}")
    db.close()


if __name__ == "__main__":
    main()
