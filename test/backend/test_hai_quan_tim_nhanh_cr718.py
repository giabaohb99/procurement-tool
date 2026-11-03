"""bao-CR-718 — tìm kiếm Tra cứu thị trường nhanh hơn (đo trên bảng thử 328 nghìn dòng, xem tài liệu hai-quan).

Canh bốn chỗ:
  · chỉ mục `ix_customs_line_date` có trên model (trang danh sách đi ngược chỉ mục thay vì quét + sắp);
  · trên MySQL ô tìm dùng LIKE thường (collation `_ci`), không bọc LOWER() — SQLite giữ `ilike`;
  · `list_lines` không dò trang khi tổng = 0 hoặc trang nằm quá tổng;
  · bộ đệm số đếm / ô chọn: chỉ bật trên MySQL, Redis hỏng thì tính thẳng (không bao giờ làm hỏng lời gọi).
"""
from datetime import date
from decimal import Decimal

from sqlalchemy.dialects import mysql, sqlite

from app.modules.customs import read_cache, service
from app.modules.customs.model import CustomsLine
from app.modules.customs.search_service import ci_like

F = {k: "" for k in ("q", "ingredient", "hs_code", "formulation", "origin", "unit", "currency", "incoterm",
                     "price_min", "price_max", "qty_min", "qty_max", "rate_min", "rate_max", "date_from", "date_to")}
F.update({"importer_id": [], "partner_id": [], "batch_id": [], "product_kind": []})


def _line(db, name, d=date(2026, 3, 1)):
    db.add(CustomsLine(reg_date=d, product_name=name, unit_code="KGM", price_usd=Decimal("1"),
                       quantity=Decimal("1"), hs_code="38089319"))


def test_line_table_has_date_index_for_newest_first_paging():
    names = {ix.name: [c.name for c in ix.columns] for ix in CustomsLine.__table__.indexes}
    assert names.get("ix_customs_line_date") == ["reg_date"]


def test_keyword_like_skips_lower_on_mysql_only():
    on_mysql = str(ci_like(CustomsLine.product_name, "%abc%", True).compile(dialect=mysql.dialect())).lower()
    on_sqlite = str(ci_like(CustomsLine.product_name, "%abc%", False).compile(dialect=sqlite.dialect())).lower()
    assert "lower(" not in on_mysql and " like " in on_mysql
    assert "lower(" in on_sqlite


def test_list_lines_returns_total_without_probing_past_the_end(db, monkeypatch):
    _line(db, "ABAMECTIN 3.6EC")
    _line(db, "ABAMECTIN 1.8EC", date(2026, 4, 1))
    _line(db, "GLYPHOSATE 480SL")
    db.commit()
    total, items = service.list_lines(db, {**F, "q": "abamectin"}, 0, 50)
    assert total == 2 and [x["product_name"] for x in items] == ["ABAMECTIN 1.8EC", "ABAMECTIN 3.6EC"]
    total, items = service.list_lines(db, {**F, "q": "abamectin"}, 50, 50)
    assert (total, items) == (2, [])
    total, items = service.list_lines(db, {**F, "q": "khongco"}, 0, 50)
    assert (total, items) == (0, [])


def test_cache_is_off_on_sqlite(db, monkeypatch):
    monkeypatch.setattr(read_cache, "_client", lambda: (_ for _ in ()).throw(AssertionError("không được gọi Redis")))
    calls = []
    assert read_cache.cached(db, "count", F, lambda: calls.append(1) or 7) == 7
    assert read_cache.cached(db, "count", F, lambda: calls.append(1) or 7) == 7
    assert len(calls) == 2


class _FakeRedis:
    def __init__(self):
        self.data = {}

    def get(self, k):
        return self.data.get(k)

    def set(self, k, v, ex=None):
        self.data[k] = v

    def scan_iter(self, match="*", count=None):
        return [k for k in self.data if k.startswith(match.rstrip("*"))]

    def delete(self, *keys):
        for k in keys:
            self.data.pop(k, None)
        return len(keys)


def _as_mysql(db, monkeypatch):
    monkeypatch.setattr(read_cache, "_enabled", lambda _db: True)


def test_cache_hits_until_cleared_or_new_rows(db, monkeypatch):
    _line(db, "ABAMECTIN 3.6EC")
    db.commit()
    fake = _FakeRedis()
    monkeypatch.setattr(read_cache, "_client", lambda: fake)
    _as_mysql(db, monkeypatch)
    calls = []

    def compute():
        calls.append(1)
        return {"n": len(calls)}

    assert read_cache.cached(db, "options", None, compute) == {"n": 1}
    assert read_cache.cached(db, "options", None, compute) == {"n": 1}, "lần hai lấy từ đệm"
    assert read_cache.clear() == 1
    assert read_cache.cached(db, "options", None, compute) == {"n": 2}, "xóa đệm thì tính lại"
    _line(db, "GLYPHOSATE 480SL")
    db.commit()
    assert read_cache.cached(db, "options", None, compute) == {"n": 3}, "lô nạp mới (MAX(id) đổi) thì khóa mới"


def test_cache_fails_open_when_redis_is_down(db, monkeypatch):
    def down():
        raise ConnectionError("redis chết")
    monkeypatch.setattr(read_cache, "_client", down)
    _as_mysql(db, monkeypatch)
    assert read_cache.cached(db, "count", F, lambda: 5) == 5
    assert read_cache.clear() == 0
