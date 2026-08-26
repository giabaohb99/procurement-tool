"""Bốc nội dung bài HDSD / FAQ ra tệp HTML để sửa ngoài container.

Cặp đôi với `hdsd_load.py`: dump -> sửa tệp (qua editor/agent) -> load lại vào DB.
Sinh ra để phục vụ đợt sửa tài liệu 26/08/2026 (rà soát 58 phát hiện) — giữ lại vì
quy trình dump/sửa/load còn dùng dài dài mỗi lần tài liệu lệch thực tế.

Cách chạy (trong container api):
    python scripts/hdsd_dump.py article 7      -> /app/tmp_docs/article_7.html
    python scripts/hdsd_dump.py faq 2          -> /app/tmp_docs/faq_2.html (chỉ phần answer)
"""
import sys
from pathlib import Path

sys.path.insert(0, "/app")

from app.core.database import SessionLocal  # noqa: E402
from app.modules.faq.model import Faq  # noqa: E402
from app.modules.help_center.model import HelpArticle  # noqa: E402

OUT_DIR = Path("/app/tmp_docs")


def main() -> None:
    kind, obj_id = sys.argv[1], int(sys.argv[2])
    OUT_DIR.mkdir(exist_ok=True)
    db = SessionLocal()
    try:
        if kind == "article":
            row = db.get(HelpArticle, obj_id)
            if not row:
                sys.exit(f"Khong co bai id={obj_id}")
            out = OUT_DIR / f"article_{obj_id}.html"
            out.write_text(row.content or "", encoding="utf-8")
            print(f"OK {out} ({len(row.content or '')} ky tu) — {row.title}")
        elif kind == "faq":
            row = db.get(Faq, obj_id)
            if not row:
                sys.exit(f"Khong co FAQ id={obj_id}")
            out = OUT_DIR / f"faq_{obj_id}.html"
            out.write_text(row.answer or "", encoding="utf-8")
            print(f"OK {out} ({len(row.answer or '')} ky tu) — {row.question}")
        else:
            sys.exit("Dung: hdsd_dump.py article|faq <id>")
    finally:
        db.close()


if __name__ == "__main__":
    main()
