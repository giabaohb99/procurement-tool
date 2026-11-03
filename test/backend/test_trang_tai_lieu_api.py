"""Trang tài liệu API (Swagger) chỉ mở khi bật `API_DOCS_ENABLED` — prod tắt (người chủ chốt 03/11/2026).

Đường nằm dưới `/api/` để đi qua nginx của giao diện như mọi đường API; `/docs` trần thì nginx trả trang SPA.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import build_docs_urls


@pytest.mark.parametrize("enabled, expected", [(True, 200), (False, 404)])
def test_trang_tai_lieu_api_theo_co(enabled, expected):
    client = TestClient(FastAPI(**build_docs_urls(enabled)))
    for path in ("/api/docs", "/api/redoc", "/api/openapi.json"):
        assert client.get(path).status_code == expected, path
    assert client.get("/docs").status_code == 404


def test_mac_dinh_la_tat_de_prod_khong_lo_ban_do_api():
    assert Settings.model_fields["API_DOCS_ENABLED"].default is False
