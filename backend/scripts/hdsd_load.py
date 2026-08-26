"""Nạp lại tệp HTML đã sửa vào bài HDSD / FAQ, qua sanitize_html + queue reindex vector.

Cặp đôi với `hdsd_dump.py`. Nội dung LUÔN đi qua sanitize_html trước khi ghi DB —
đây là hàng rào bắt buộc cho mọi HTML sinh ngoài hệ thống (đã từng dính lỗ srcdoc).
Ghi DB thẳng nên hook tự reindex của tầng service KHÔNG chạy — script tự queue
`reindex_source_task` để chỉ mục vector của trợ lý AI không lệch nội dung mới.

Cách chạy (trong container api):
    python scripts/hdsd_load.py article 7
    python scripts/hdsd_load.py faq 2
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "/app")

from app.core.database import SessionLocal  # noqa: E402
from app.modules.faq.model import Faq  # noqa: E402
from app.modules.help_center.import_service import sanitize_html  # noqa: E402
from app.modules.help_center.model import HelpArticle  # noqa: E402

IN_DIR = Path("/app/tmp_docs")


def _queue_reindex(source: str, source_id: int) -> None:
    try:
        from app.modules.assistant.rag.tasks import reindex_source_task

        reindex_source_task.delay(source, source_id)
        print(f"Da queue reindex {source}#{source_id}")
    except Exception as e:  # broker tắt thì vẫn phải ghi được nội dung
        print(f"CANH BAO: khong queue duoc reindex ({e}) — chay lai reindex thu cong sau")


def main() -> None:
    kind, obj_id = sys.argv[1], int(sys.argv[2])
    db = SessionLocal()
    try:
        if kind == "article":
            path = IN_DIR / f"article_{obj_id}.html"
            row = db.get(HelpArticle, obj_id)
        elif kind == "faq":
            path = IN_DIR / f"faq_{obj_id}.html"
            row = db.get(Faq, obj_id)
        else:
            sys.exit("Dung: hdsd_load.py article|faq <id>")
        if not row:
            sys.exit(f"Khong co {kind} id={obj_id}")
        if not path.exists():
            sys.exit(f"Chua co tep {path} — chay hdsd_dump.py truoc")

        raw = path.read_text(encoding="utf-8")
        clean = sanitize_html(raw)
        before = len((row.content if kind == "article" else row.answer) or "")
        if kind == "article":
            row.content = clean
        else:
            row.answer = clean
        row.updated_at = datetime.utcnow()
        db.commit()
        print(f"OK {kind}#{obj_id}: {before} -> {len(clean)} ky tu")
        _queue_reindex("help_article" if kind == "article" else "faq", obj_id)
    finally:
        db.close()


if __name__ == "__main__":
    main()
