"""Nạp lại tệp HTML đã sửa vào bài HDSD / FAQ, qua sanitize_html + queue reindex vector.

Cặp đôi với `hdsd_dump.py`. Nội dung LUÔN đi qua sanitize_html trước khi ghi DB —
đây là hàng rào bắt buộc cho mọi HTML sinh ngoài hệ thống (đã từng dính lỗ srcdoc).
Ghi DB thẳng nên hook tự reindex của tầng service KHÔNG chạy — script tự queue
`reindex_source_task` để chỉ mục vector của trợ lý AI không lệch nội dung mới.

⚠️ **sanitize_html gỡ luôn `srcdoc` + `sandbox` của iframe**, mà nhiều bài HDSD có sẵn khối
nhúng guideflow hợp lệ do CHÍNH trình soạn của Trung tâm HDSD sinh ra (bài 39 dài 6287 ký tự,
sanitize xong còn 5135 — mất trắng khối nhúng, không báo gì). Nên dump → sửa → load một bài
có khối nhúng là im lặng xóa nó. Từ 07/09/2026 script **dừng lại** khi phát hiện chuyện đó;
cố ý bỏ khối nhúng thì thêm cờ `--bo-embed`.

Cách chạy (trong container api):
    python scripts/hdsd_load.py article 7
    python scripts/hdsd_load.py faq 2
    python scripts/hdsd_load.py article 39 --bo-embed   # chấp nhận mất khối nhúng
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
        if "srcdoc=" in raw and "srcdoc=" not in clean and "--bo-embed" not in sys.argv:
            sys.exit(
                f"DUNG LAI: sanitize_html da go khoi nhung (srcdoc) khoi {kind}#{obj_id} — "
                f"{len(raw)} -> {len(clean)} ky tu. Khoi nhung guideflow do trinh soan HDSD "
                f"sinh ra la hop le, ghi de la mat han. Giu lai thi sua tep roi chay lai; "
                f"co y bo that thi them co --bo-embed."
            )
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
