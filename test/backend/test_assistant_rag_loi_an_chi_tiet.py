"""N-009 (change-log.md): câu lỗi 502 của `rag/index-status` và `rag/reindex` KHÔNG được
bày nội dung lỗi gốc của thư viện (Qdrant/Celery) cho người dùng — chỉ một câu tiếng Việt
cố định; chi tiết thật ghi qua `logger.exception` cho quản trị tra log.

Gọi thẳng hàm controller, bỏ qua lớp `Depends`: monkeypatch `app_settings.get` để `_guard()`
luôn cho qua, và `settings.AI_RAG_ENABLED = True` để không rớt sớm về nhánh tắt RAG.
"""
import logging
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core import app_settings
from app.core.config import settings
from app.modules.assistant import controller


@pytest.fixture(autouse=True)
def _bat_ai_va_rag(monkeypatch):
    monkeypatch.setattr(app_settings, "get", lambda *a, **k: True)
    monkeypatch.setattr(settings, "AI_RAG_ENABLED", True)


def _user():
    return SimpleNamespace(id=1)


def test_index_status_che_loi_goc_ghi_log(db, monkeypatch, caplog):
    """`indexer.index_status` ném RuntimeError -> 502 với câu cố định, không lộ 'boom-secret';
    log ở mức ERROR giữ nguyên chi tiết."""
    from app.modules.assistant.rag import indexer

    def _no(db):
        raise RuntimeError("boom-secret")

    monkeypatch.setattr(indexer, "index_status", _no)

    with caplog.at_level(logging.ERROR, logger="app.modules.assistant.controller"):
        with pytest.raises(HTTPException) as exc:
            controller.rag_index_status(user=_user(), db=db)

    assert exc.value.status_code == 502
    assert "boom-secret" not in exc.value.detail
    assert any(r.levelno == logging.ERROR for r in caplog.records)
    assert "boom-secret" in caplog.text


def test_reindex_che_loi_goc_ghi_log(monkeypatch, caplog):
    """`task.delay()` ném RuntimeError (broker sập) -> 502 với câu cố định, không lộ
    'boom-secret'; log ở mức ERROR giữ nguyên chi tiết."""
    from app.modules.assistant.rag import tasks as rag_tasks

    def _no(*a, **k):
        raise RuntimeError("boom-secret")

    monkeypatch.setattr(rag_tasks.rebuild_all_task, "delay", _no)

    with caplog.at_level(logging.ERROR, logger="app.modules.assistant.controller"):
        with pytest.raises(HTTPException) as exc:
            controller.rag_reindex(mode="all", user=_user())

    assert exc.value.status_code == 502
    assert "boom-secret" not in exc.value.detail
    assert any(r.levelno == logging.ERROR for r in caplog.records)
    assert "boom-secret" in caplog.text


def test_reindex_mode_sai_van_400_nhu_cu():
    """Ca phủ định: `mode` không hợp lệ vẫn chặn ở 400 như trước khi sửa, không đụng nhánh
    che lỗi 502 vừa thêm."""
    with pytest.raises(HTTPException) as exc:
        controller.rag_reindex(mode="khong-hop-le", user=_user())

    assert exc.value.status_code == 400
