"""Nạp chỉ mục loại B chạy NỀN (Phase 3): hook chỉ XẾP HÀNG, task gác cờ.

CHỈ kiểm phần vừa đổi: `rag/hooks.py` (dispatch .delay) + `rag/tasks.py` (gác AI_RAG_ENABLED).
Không gọi Redis/Gemini/Qdrant thật — thay .delay bằng hàm giả, và task chạy khi cờ tắt trả
'skipped' nên không đụng DB.
"""
import pytest

from app.core.config import settings
from app.modules.assistant.rag import hooks, tasks


@pytest.fixture
def rag_on():
    old = settings.AI_RAG_ENABLED
    settings.AI_RAG_ENABLED = True
    yield
    settings.AI_RAG_ENABLED = old


def _capture(monkeypatch, task, calls):
    """Thay .delay của một task bằng hàm chỉ ghi lại tham số (không chạm broker)."""
    monkeypatch.setattr(task, "delay", lambda *a, **k: calls.append((a, k)) or "fake-id")


def test_hook_tat_co_khong_xep_hang(monkeypatch):
    """RAG tắt -> không gọi .delay (môi trường không Qdrant vẫn lưu bài bình thường)."""
    settings.AI_RAG_ENABLED = False
    calls = []
    _capture(monkeypatch, tasks.reindex_source_task, calls)
    hooks.on_source_saved(None, "faq", 7)
    assert calls == []


def test_hook_bat_co_xep_hang_dung_tham_so(monkeypatch, rag_on):
    """RAG bật -> xếp hàng đúng (source, source_id) cho worker."""
    calls = []
    _capture(monkeypatch, tasks.reindex_source_task, calls)
    hooks.on_source_saved(None, "help_article", 12)
    assert calls == [(("help_article", 12), {})]


def test_hook_xoa_xep_hang(monkeypatch, rag_on):
    calls = []
    _capture(monkeypatch, tasks.remove_source_task, calls)
    hooks.on_source_deleted("faq", 3)
    assert calls == [(("faq", 3), {})]


def test_hook_nuot_loi_broker(monkeypatch, rag_on):
    """Broker chập lúc xếp hàng -> KHÔNG được nổi lỗi ra (không làm vỡ việc lưu bài)."""
    def _boom(*a, **k):
        raise RuntimeError("redis down")
    monkeypatch.setattr(tasks.reindex_source_task, "delay", _boom)
    hooks.on_source_saved(None, "faq", 1)  # không raise là đạt


def test_task_gac_co_tat(monkeypatch):
    """Task chạy khi cờ tắt -> trả 'skipped', không đụng DB/Qdrant."""
    settings.AI_RAG_ENABLED = False
    assert tasks.reindex_source_task.run("faq", 1)["status"] == "skipped"
    assert tasks.remove_source_task.run("faq", 1)["status"] == "skipped"
    assert tasks.rebuild_all_task.run()["status"] == "skipped"
