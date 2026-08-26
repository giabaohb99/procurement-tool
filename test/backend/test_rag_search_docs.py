"""Tool loại B `search_docs` (Phase 3): gác cờ AI_RAG_ENABLED + lọc ngưỡng + hình dạng kết quả.

Cắm embedder + store GIẢ để không gọi Gemini/Qdrant thật (mạng). CHỈ kiểm phần vừa làm:
tầng `rag/search.py` + đăng ký tool ở `tools/__init__.py`. Việc nhúng/nạp thật verify tay.
"""
import pytest

from app.core.config import settings
from app.modules.assistant import tools as T
from app.modules.assistant.rag import search as search_mod
from app.modules.assistant.rag.embedder import set_embedder
from app.modules.assistant.rag.store import set_store


class _FakeEmbedder:
    dim = 3

    def embed(self, texts, *, is_query=False):
        # Vector không quan trọng: store giả bỏ qua nó. Chỉ cần đúng số lượng.
        return [[0.1, 0.2, 0.3] for _ in texts]


class _FakeStore:
    """Trả cố định 2 đoạn: một trên ngưỡng, một dưới ngưỡng để kiểm bộ lọc."""

    def __init__(self, hits):
        self._hits = hits

    def search(self, vector, limit, *, only_active=True):
        return self._hits[:limit]


@pytest.fixture
def rag_on():
    """Bật cờ RAG cho một test rồi trả lại nguyên trạng + dọn singleton embedder/store."""
    old = settings.AI_RAG_ENABLED
    settings.AI_RAG_ENABLED = True
    yield
    settings.AI_RAG_ENABLED = old
    set_embedder(None)
    set_store(None)


def test_tool_an_khi_tat_co(db, seed):
    """RAG tắt -> tool không có trong allowlist, gọi thẳng trả lỗi 'không có công cụ'."""
    settings.AI_RAG_ENABLED = False
    from app.modules.user.model import User
    user = db.get(User, seed.u_req_id)
    names = [d.name for d in T.tool_defs()]
    assert "search_docs" not in names
    out = T.run_tool(db, user, "search_docs", {"query": "cách tạo phiếu"})
    assert out.get("error")


def test_tool_hien_khi_bat_co(rag_on):
    """RAG bật -> tool xuất hiện cho provider."""
    names = [d.name for d in T.tool_defs()]
    assert "search_docs" in names


def test_loc_nguong_va_hinh_dang_ket_qua(db, seed, rag_on):
    """Đoạn dưới MIN_SCORE bị loại; đoạn trên ngưỡng trả đủ text/nguồn/link/điểm."""
    set_embedder(_FakeEmbedder())
    set_store(_FakeStore([
        {"text": "Vào menu Yêu cầu mua hàng rồi bấm Tạo mới.", "source": "help_article",
         "title": "Tạo YCMH", "url": "/articles/12", "score": 0.87},
        {"text": "Đoạn lạc đề điểm thấp.", "source": "faq",
         "title": "Khác", "url": "/faq", "score": 0.20},   # dưới MIN_SCORE=0.5
    ]))
    from app.modules.user.model import User
    user = db.get(User, seed.u_req_id)

    out = T.run_tool(db, user, "search_docs", {"query": "làm sao tạo yêu cầu mua hàng"})
    assert out["total"] == 1
    item = out["items"][0]
    assert item["source"] == "help_article"
    assert item["url"] == "/articles/12"
    assert item["title"] == "Tạo YCMH"
    assert item["score"] == 0.87


def test_cau_hoi_rong_tra_rong(db, seed, rag_on):
    """Query rỗng -> không gọi store, trả tổng 0 (không nổ)."""
    set_embedder(_FakeEmbedder())
    set_store(_FakeStore([{"text": "x", "source": "faq", "score": 0.9}]))
    from app.modules.user.model import User
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "search_docs", {"query": "   "})
    assert out == {"items": [], "total": 0}


def test_search_docs_ham_thuan_lay_dung_nguong(rag_on):
    """Gọi thẳng hàm search_docs (không qua tool): xác nhận MIN_SCORE cắt đúng."""
    set_embedder(_FakeEmbedder())
    set_store(_FakeStore([
        {"text": "trên ngưỡng", "source": "faq", "title": "", "url": "/faq", "score": 0.55},
        {"text": "dưới ngưỡng", "source": "faq", "title": "", "url": "/faq", "score": 0.49},
    ]))
    out = search_mod.search_docs("bất kỳ")
    assert len(out) == 1
    assert out[0]["text"] == "trên ngưỡng"
