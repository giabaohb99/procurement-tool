"""bao-CR-582 — màn NHẬT KÝ HỆ THỐNG lọc theo PHƯƠNG THỨC gọi (GET/POST/PUT/PATCH/DELETE).

Đại ca: *"muốn có put coi post thì sao"* — lọc một hay nhiều phương thức một lượt.

Ba thứ canh ở đây:

1. **Nhiều phương thức là HOẶC**, không phải VÀ: `POST,PUT` trả cả lượt POST lẫn PUT.
2. **Giá trị rác bị TỪ CHỐI, không bị bỏ im lặng** — họ lỗi bao-CR-447: tham số sai mà
   backend lờ đi thì bảng ra toàn hệ, người dùng tin là đã lọc.
3. **Bảng và biểu đồ dùng CHUNG bộ lọc** — `/summary` phải nhận đúng tham số của danh
   sách (luật đã ghi ở `controller.read_summary`).
"""
import inspect
import uuid
from datetime import datetime

import pytest

from app.core.logging_codes import SOURCE_API
from app.modules.request_log.model import RequestLog
from app.modules.system_log import controller, service


def _add_request(db, *, method: str, route: str, http_status: int = 200):
    row = RequestLog(
        request_id=uuid.uuid4().bytes, source=SOURCE_API, created_at=datetime(2026, 10, 3, 9, 30),
        user_id=1, session_id=None, ip="10.0.0.1", method=method, path=route, route=route,
        query_string="", http_status=http_status, error_code="", error_detail=None,
        request_body=None, response_body=None, duration_ms=12, audit_count=0, change_count=0)
    db.add(row)
    db.flush()
    return row


def _seed(db):
    _add_request(db, method="GET", route="/get")
    _add_request(db, method="POST", route="/post")
    _add_request(db, method="PUT", route="/put")
    _add_request(db, method="PATCH", route="/patch")
    _add_request(db, method="DELETE", route="/delete", http_status=403)


def _routes(db, **filters):
    q = service.build_query(db, **filters)
    return {r["route"] for r in service.build_page(db, q, 0, 50)}


# ── 1. Đọc chuỗi tham số ────────────────────────────────────────────────────────

@pytest.mark.parametrize("raw, expected", [
    (None, ()),
    ("", ()),
    ("   ", ()),
    ("POST", ("POST",)),
    ("post", ("POST",)),
    (" post , Put ", ("POST", "PUT")),
    ("POST,POST,put", ("POST", "PUT")),
    ("POST,,PUT,", ("POST", "PUT")),
])
def test_parse_methods_chuan_hoa(raw, expected):
    assert service.parse_methods(raw) == expected


@pytest.mark.parametrize("bad", ["GET;DROP", "P0ST", "QUÁDÀI", "ABCDEFGHI", "POST PUT", "*"])
def test_parse_methods_tu_choi_gia_tri_rac(bad):
    with pytest.raises(ValueError):
        service.parse_methods(bad)


def test_parse_methods_chan_danh_sach_qua_dai():
    """Mười phương thức là quá đủ (HTTP chỉ có chín) — dài hơn là ai đó đang nhồi.
    Đếm sau khi bỏ trùng: lặp lại cùng một giá trị không tính là dài."""
    eleven = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE", "CONNECT", "A", "B"]
    with pytest.raises(ValueError):
        service.parse_methods(",".join(eleven))
    assert len(service.parse_methods(",".join(eleven[:10] + ["GET"] * 20))) == 10


# ── 2. Lọc trên bảng ────────────────────────────────────────────────────────────

def test_khong_loc_phuong_thuc_thi_tra_du(db):
    _seed(db)
    assert _routes(db) == {"/get", "/post", "/put", "/patch", "/delete"}
    assert _routes(db, methods=()) == {"/get", "/post", "/put", "/patch", "/delete"}


def test_loc_mot_phuong_thuc(db):
    _seed(db)
    assert _routes(db, methods=("PUT",)) == {"/put"}


def test_nhieu_phuong_thuc_la_HOAC(db):
    _seed(db)
    assert _routes(db, methods=("POST", "PUT")) == {"/post", "/put"}


def test_loc_phuong_thuc_di_cung_bo_loc_khac_la_VA(db):
    _seed(db)
    assert _routes(db, methods=("DELETE", "POST"), status=service.STATUS_BLOCKED) == {"/delete"}


def test_phuong_thuc_khong_co_luot_nao_thi_rong_chu_khong_tra_toan_he(db):
    _seed(db)
    assert _routes(db, methods=("OPTIONS",)) == set()


def test_bieu_do_cung_bo_loc_phuong_thuc(db):
    _seed(db)
    q = service.build_query(db, methods=("POST", "PUT"))
    summary = service.build_summary(db, q)
    assert sum(h["total"] for h in summary["by_hour"]) == 2


# ── 3. Cửa API ──────────────────────────────────────────────────────────────────

def test_ca_danh_sach_lan_bieu_do_deu_nhan_tham_so_method():
    """Quên thêm vào một trong hai cửa là biểu đồ vẽ toàn hệ trong khi bảng đã lọc."""
    assert "method" in inspect.signature(controller.list_logs).parameters
    assert "method" in inspect.signature(controller.read_summary).parameters


def test_cua_api_tra_422_khi_phuong_thuc_rac(db):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as caught:
        controller._parse_methods_or_422("GET;DROP")
    assert caught.value.status_code == 422
