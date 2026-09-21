"""Nạp BÙ chỉ mục vector: đối chiếu DB với kho, và chỉ nạp phần còn thiếu (bao-CR-451).

Vì sao có cụm này. Hook nạp chỉ mục bắn từ *service* Trung tâm trợ giúp, còn script seed ghi
thẳng ORM — bài do seed dựng ra không bao giờ vào kho vector, và trước đây không chỗ nào nói
ra. Rà trên máy chủ thử nghiệm ngày 21/09/2026: kho có 55/87 bài, hụt đúng 32 bài của seed.

Không gọi Qdrant/Gemini thật: cắm kho giả bằng `store.set_store`.
"""
import pytest

from app.core.config import settings
from app.modules.assistant.rag import indexer, store, tasks
from app.modules.faq.model import Faq
from app.modules.help_center.model import HelpArticle


class FakeStore:
    """Kho giả: chỉ cần trả đúng tập (nguồn, id) đang có."""

    def __init__(self, refs):
        self._refs = set(refs)

    def source_refs(self):
        return set(self._refs)


@pytest.fixture
def rag_on():
    old = settings.AI_RAG_ENABLED
    settings.AI_RAG_ENABLED = True
    yield
    settings.AI_RAG_ENABLED = old


@pytest.fixture
def noi_dung(db):
    """3 bài HDSD + 2 câu FAQ."""
    articles = [HelpArticle(title=f"Bài {i}", content="noi dung") for i in range(1, 4)]
    faqs = [Faq(question=f"Hỏi {i}", answer="đáp") for i in range(1, 3)]
    db.add_all(articles + faqs)
    db.commit()
    return [a.id for a in articles], [f.id for f in faqs]


@pytest.fixture(autouse=True)
def _tra_kho_ve():
    yield
    store.set_store(None)


def test_thieu_bai_nao_thi_ke_dung_bai_do(db, noi_dung):
    article_ids, faq_ids = noi_dung
    store.set_store(FakeStore([("help_article", article_ids[0]), ("faq", faq_ids[0])]))
    assert indexer.missing_source_refs(db) == [
        ("help_article", article_ids[1]),
        ("help_article", article_ids[2]),
        ("faq", faq_ids[1]),
    ]


def test_kho_trong_thi_thieu_tat_ca(db, noi_dung):
    """Lần đầu bật RAG: nạp bù và dựng lại toàn bộ phải ra cùng một danh sách."""
    store.set_store(FakeStore([]))
    assert indexer.missing_source_refs(db) == indexer.all_source_refs(db)


def test_kho_du_thi_khong_con_gi_de_nap(db, noi_dung):
    store.set_store(FakeStore(indexer.all_source_refs(db)))
    assert indexer.missing_source_refs(db) == []


def test_nguon_da_xoa_duoi_db_khong_bi_dem_la_thieu(db, noi_dung):
    """Bài đã xóa mà kho còn đoạn (mồ côi) KHÔNG được biến thành việc phải nạp lại.

    Nạp lại một id không còn bản ghi thì `reindex_source` chỉ xóa đoạn rồi trả 0 — vô hại
    nhưng là lời gọi thừa, và con số 'còn thiếu' trên màn hình sẽ không bao giờ về 0.
    """
    store.set_store(FakeStore(indexer.all_source_refs(db) + [("help_article", 9999)]))
    assert indexer.missing_source_refs(db) == []
    assert indexer.index_status(db)["orphans"] == 1


def test_so_lieu_doi_chieu_dem_rieng_tung_loai(db, noi_dung):
    article_ids, faq_ids = noi_dung
    store.set_store(FakeStore([("help_article", article_ids[0]), ("faq", faq_ids[0])]))
    stats = indexer.index_status(db)
    assert stats["help_total"] == 3
    assert stats["faq_total"] == 2
    assert stats["help_indexed"] == 1
    assert stats["faq_indexed"] == 1
    assert (stats["missing"], stats["missing_help"], stats["missing_faq"]) == (3, 2, 1)
    assert stats["orphans"] == 0


def test_khong_co_noi_dung_nao_thi_moi_so_deu_0(db):
    store.set_store(FakeStore([]))
    stats = indexer.index_status(db)
    assert stats == {
        "help_total": 0, "faq_total": 0, "help_indexed": 0, "faq_indexed": 0,
        "missing": 0, "missing_help": 0, "missing_faq": 0, "orphans": 0,
    }


def test_task_nap_bu_gac_co_tat():
    settings.AI_RAG_ENABLED = False
    assert tasks.reindex_missing_task.run()["status"] == "skipped"


def test_task_nap_bu_chi_rai_phan_thieu(monkeypatch, rag_on):
    """Rải mỗi nguồn MỘT task, và chỉ rải phần thiếu — đây là cả lý do tồn tại của task này."""
    calls = []
    monkeypatch.setattr(tasks.reindex_source_task, "delay",
                        lambda *a, **k: calls.append(a) or "fake-id")
    monkeypatch.setattr(indexer, "missing_source_refs", lambda db: [("faq", 5)])
    assert tasks.reindex_missing_task.run() == {"status": "queued", "sources": 1}
    assert calls == [("faq", 5)]
