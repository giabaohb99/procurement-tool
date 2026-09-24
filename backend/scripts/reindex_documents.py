# -*- coding: utf-8 -*-
"""Dựng chỉ mục TÌM KIẾM TOÀN VĂN văn bản — CHẠY TAY, ngay trong tiến trình,
không qua Celery (phase 07, duoc-CR-477).

Cùng lý do `scripts/reindex_help_rag.py` tồn tại: dựng lần đầu sau khi bảng
`tab_document_search` vừa được migration tạo ra (bảng trống, mọi văn bản đang
có phải nạp một lượt), và chữa cháy khi nghi có hook bị bỏ sót (Rủi ro § của
phase 07: "chỉ mục cũ khi hook bị bỏ sót").

⚠️ ĐÂY LÀ ĐƯỜNG DẪN THẬT — đặc tả phase 07 viết `python -m app.scripts.
reindex_documents`, nhưng mọi script chạy tay khác của repo này đều nằm ở
`backend/scripts/` (xem `reindex_help_rag.py`, `sync_task_journal.py`...),
không phải `backend/app/scripts/`. Theo đúng cấu trúc đang có, không dựng
thêm một quy ước script thứ hai.

Chạy trong container api:
    # nạp bù MỌI văn bản chưa có chỉ mục hoặc đã sửa từ lúc nạp trước
    docker compose exec -T api python scripts/reindex_documents.py
    # dựng lại TOÀN BỘ, kể cả văn bản chưa đổi gì (đo giờ, đối chiếu số liệu)
    docker compose exec -T api python scripts/reindex_documents.py --all
    # chỉ những văn bản sửa từ một mốc thời gian trở đi (vá chỗ hook bị bỏ sót)
    docker compose exec -T api python scripts/reindex_documents.py --since 2026-09-01

`--all` và mặc định (không cờ) đều gọi `reindex()` cho MỌI văn bản còn tồn tại
— khác nhau đúng một chỗ: `reindex()` tự bỏ qua (không ghi lại) khi băm nguồn
không đổi, nên chạy lại vô hại và rẻ ở lần nạp bù thứ hai trở đi. `--all` chỉ
khác ở CÂU IN ra màn hình (đếm luôn cả phần bị bỏ qua vào "đã kiểm").

⚠️ GUARD TỪ DỪNG (M9, rà soát 23/09/2026 — bổ sung sau migration `83679db84fd1`).
Migration đó đã chứng minh: cờ `innodb_ft_enable_stopword` chỉ có tác dụng
NGAY TẠI câu `CREATE/ALTER ... FULLTEXT INDEX`, không bền theo thời gian —
`mysqldump`/khôi phục bản sao lưu, `OPTIMIZE TABLE`, hay một `ALTER TABLE`
COPY nào đó sau này đều dựng lại chỉ mục bằng session MẶC ĐỊNH (lọc BẬT lại),
và MySQL không có cách tra "chỉ mục X có đang lọc từ dừng không" sau khi đã
dựng — chỉ kiểm được bằng TRUY VẤN THỬ. `--check-stopwords` chèn một dòng THỬ
vào CHÍNH `tab_document_search` (`document_id=-1`, xóa ngay sau khi kiểm), tra
chữ "văn" (đúng âm tiết đã gây lỗi gốc) qua chỉ mục THẬT đang phục vụ tìm
kiếm, và báo hỏng nếu tra không ra — chạy được như một bước ops định kỳ/lúc
khởi động, độc lập với việc reindex văn bản thật. `--fix-stopwords` dựng lại
4 chỉ mục thật với
`SET SESSION innodb_ft_enable_stopword = 0` (giống hệt migration, không cần
viết migration mới mỗi lần cần vá lại).
"""
import argparse
import sys
import time
from datetime import datetime

sys.path.insert(0, "/app")

import app.core.all_models  # noqa: E402,F401 — đăng ký mapper trước khi mở session
from app.core.database import SessionLocal  # noqa: E402
from app.modules.document import search_index_service  # noqa: E402
from app.modules.document.model import Document  # noqa: E402

#  Khớp ĐÚNG `_FULLTEXT_INDEXES` của migration `83679db84fd1` — tên + cột.
_FULLTEXT_INDEXES = (
    ("ft_document_search_all", "meta_text, body_text, file_text"),
    ("ft_document_search_meta", "meta_text"),
    ("ft_document_search_body", "body_text"),
    ("ft_document_search_file", "file_text"),
)


#  Id KHÔNG BAO GIỜ trùng văn bản thật — `tab_document.id` luôn dương
#  (AUTO_INCREMENT từ 1). Không FK (`search_model.py`) nên chèn/xóa dòng này
#  an toàn, không đụng văn bản nào.
_STOPWORD_PROBE_ID = -1


def check_stopwords_disabled(db) -> bool:
    """`True` nếu CHỈ MỤC FULLTEXT THẬT (`tab_document_search`) đang tra được
    chữ "văn" — tức từ dừng đang TẮT đúng như migration `83679db84fd1` đã đặt.
    Dialect khác MySQL (SQLite bộ test) không có gì để kiểm — trả `True` luôn.

    ⚠️ Kiểm trên CHÍNH bảng/chỉ mục thật đang phục vụ tìm kiếm, không dựng một
    chỉ mục THỬ riêng — MySQL không lộ "chỉ mục X có đang lọc từ dừng không"
    qua `INFORMATION_SCHEMA` (chỉ đọc được tại đúng câu DDL dựng nó), nên câu
    trả lời duy nhất đáng tin là chạy thật một `MATCH AGAINST` trên bảng đang
    dùng. Chèn một dòng THỬ (`document_id = -1`, không đụng văn bản thật nào)
    rồi xóa ngay trong `finally` — kể cả khi lỗi giữa chừng."""
    if db.bind.dialect.name != "mysql":
        return True
    from sqlalchemy import text

    from app.core.text_fold import fold

    probe_text = fold("văn bản")  # dạng đã gập dấu — đúng thứ CỘT THẬT lưu
    db.execute(text("DELETE FROM tab_document_search WHERE document_id = :id"),
              {"id": _STOPWORD_PROBE_ID})
    try:
        db.execute(text(
            "INSERT INTO tab_document_search "
            "(document_id, meta_text, body_text, file_text, file_text_raw, "
            "file_names, file_fingerprint, source_hash, indexed_at) "
            "VALUES (:id, :meta, '', '', '', '[]', '', '', NOW())"
        ), {"id": _STOPWORD_PROBE_ID, "meta": probe_text})
        #  ⚠️ BẮT BUỘC `commit()` trước khi `MATCH AGAINST` — InnoDB FULLTEXT
        #  chỉ phản ánh dòng đã COMMIT (bắt được lúc kiểm tay: cùng một câu,
        #  chưa commit ra `False`, commit xong ra `True`), khác các cột
        #  thường vẫn đọc lại được ngay trong transaction đang mở.
        db.commit()
        found = db.execute(text(
            "SELECT COUNT(*) FROM tab_document_search WHERE document_id = :id "
            "AND MATCH(meta_text, body_text, file_text) AGAINST ('+\"van\"' IN BOOLEAN MODE)"
        ), {"id": _STOPWORD_PROBE_ID}).scalar()
        return bool(found)
    finally:
        db.execute(text("DELETE FROM tab_document_search WHERE document_id = :id"),
                  {"id": _STOPWORD_PROBE_ID})
        db.commit()


def fix_stopwords(db) -> None:
    """Dựng lại 4 chỉ mục FULLTEXT thật với từ dừng TẮT — cùng thao tác với
    migration `83679db84fd1`, không cần viết migration mới mỗi lần cần vá."""
    from sqlalchemy import text

    db.execute(text("SET SESSION innodb_ft_enable_stopword = 0"))
    for name, _cols in _FULLTEXT_INDEXES:
        db.execute(text(f"ALTER TABLE tab_document_search DROP INDEX {name}"))
    for name, cols in _FULLTEXT_INDEXES:
        db.execute(text(
            f"ALTER TABLE tab_document_search ADD FULLTEXT INDEX {name} ({cols}) "
            "WITH PARSER ngram"))
    db.execute(text("SET SESSION innodb_ft_enable_stopword = DEFAULT"))
    db.commit()


def parse_args():
    p = argparse.ArgumentParser(description="Dựng chỉ mục tìm kiếm toàn văn văn bản (chạy tay)")
    p.add_argument("--all", action="store_true",
                   help="Nói rõ ý định dựng lại toàn bộ (hành vi thực tế giống mặc định — "
                        "`reindex()` tự bỏ qua khi băm nguồn không đổi)")
    p.add_argument("--since", type=str, default="",
                   help="Chỉ văn bản sửa (`updated_at`) từ ngày này trở đi, dạng YYYY-MM-DD")
    p.add_argument("--sleep-every", type=int, default=200,
                   help="Nghỉ 1 giây sau mỗi N văn bản — bớt tải CPU container api lúc đang có "
                        "người dùng thật (mặc định 200, đặt 0 để tắt)")
    p.add_argument("--check-stopwords", action="store_true",
                   help="CHỈ kiểm chỉ mục FULLTEXT có đang lọc từ dừng không rồi thoát, "
                        "không reindex văn bản nào (dùng cho ops/health-check định kỳ)")
    p.add_argument("--fix-stopwords", action="store_true",
                   help="Dựng lại chỉ mục FULLTEXT với từ dừng tắt trước khi reindex "
                        "(dùng khi --check-stopwords báo hỏng)")
    return p.parse_args()


def main():
    args = parse_args()
    #  `args.all` cố ý KHÔNG đọc tới — chỉ để câu lệnh dễ hiểu, hành vi thực tế
    #  giống hệt mặc định (xem docstring).

    db = SessionLocal()
    try:
        if args.check_stopwords:
            ok = check_stopwords_disabled(db)
            print("OK — chỉ mục FULLTEXT không lọc từ dừng." if ok else
                  "HỎNG — chỉ mục FULLTEXT đang lọc từ dừng (tìm \"văn\"/\"bản\"/\"toàn\"... "
                  "sẽ ra rỗng). Chạy lại với --fix-stopwords để vá.")
            return 0 if ok else 1

        if args.fix_stopwords:
            fix_stopwords(db)
            print("Đã dựng lại chỉ mục FULLTEXT với từ dừng tắt.")

        query = db.query(Document.id)
        if args.since:
            try:
                since = datetime.strptime(args.since, "%Y-%m-%d")
            except ValueError:
                print(f"--since sai định dạng: {args.since!r} (cần YYYY-MM-DD)")
                return 1
            query = query.filter(Document.updated_at >= since)
        ids = [row[0] for row in query.order_by(Document.id.asc()).all()]

        print(f"Sẽ kiểm {len(ids)} văn bản.")
        indexed = skipped = failed = 0
        for i, doc_id in enumerate(ids, start=1):
            try:
                row = search_index_service.reindex(db, doc_id)
                if row is None:
                    skipped += 1
                else:
                    indexed += 1
            except Exception as e:  # noqa: BLE001 — một văn bản hỏng không được làm đứt cả mẻ
                failed += 1
                print(f"  [{i}/{len(ids)}] văn bản #{doc_id}: LỖI {e}")
            if args.sleep_every and i % args.sleep_every == 0:
                print(f"  [{i}/{len(ids)}] đã kiểm...")
                time.sleep(1)

        print(f"Xong: {indexed} văn bản có chỉ mục, {skipped} bị xóa/không có gì để trích, "
              f"{failed} lỗi.")
        return 1 if failed else 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
