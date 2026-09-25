"""Guard TỪ DỪNG của chỉ mục FULLTEXT (M9, rà soát code-reviewer 23/09/2026) —
`backend/scripts/reindex_documents.py::check_stopwords_disabled`.

Script nằm NGOÀI package `app` (quy ước script chạy tay của repo, xem docstring
đầu tệp đó) nên phải tự thêm `backend/scripts` vào `sys.path` trước khi import
— không đi qua `sys.path.insert(0, "/app")` của chính script (đường đó chỉ
đúng TRONG container, bài kiểm này chạy trong CÙNG container nên `/app` cũng
đúng, nhưng thêm thư mục script cho rõ ràng, không phụ thuộc side-effect đó).

Nhánh MySQL thật (chèn dòng thử vào `tab_document_search`, tra `MATCH AGAINST`)
đã kiểm TAY trên MySQL local (xem ghi chú trong migration `83679db84fd1` và
docstring của script) — bộ pytest chạy SQLite, chỉ kiểm được nhánh "không phải
MySQL thì bỏ qua, không phải lỗi".
"""
import sys
from types import SimpleNamespace

if "/app/scripts" not in sys.path:
    sys.path.insert(0, "/app/scripts")

import reindex_documents  # noqa: E402 — path đã chỉnh ở trên


def _fake_db(dialect_name: str):
    return SimpleNamespace(bind=SimpleNamespace(dialect=SimpleNamespace(name=dialect_name)))


def test_dialect_khac_mysql_bo_qua_tra_true():
    """SQLite (bộ test/dev) không có FULLTEXT ngram của MySQL để kiểm — trả
    `True` (không báo hỏng), KHÔNG được coi là lỗi."""
    assert reindex_documents.check_stopwords_disabled(_fake_db("sqlite")) is True


def test_dialect_khac_mysql_khong_dung_toi_db_that():
    """`db` giả KHÔNG có `.execute`/`.query` nào — nếu hàm lỡ chạm tới (quên
    kiểm dialect trước) sẽ nổ `AttributeError` ngay, bài kiểm này tự bắt được."""
    fake = SimpleNamespace(bind=SimpleNamespace(dialect=SimpleNamespace(name="sqlite")))
    assert reindex_documents.check_stopwords_disabled(fake) is True


def test_probe_id_khong_trung_id_van_ban_that():
    """`document_id` PK của `tab_document_search` KHÔNG tự sinh — nó CHÍNH LÀ
    `tab_document.id` (AUTO_INCREMENT từ 1, luôn dương). Probe phải âm để
    không bao giờ trùng một văn bản thật."""
    assert reindex_documents._STOPWORD_PROBE_ID < 0
