"""Bộ đệm ngắn cho phần ĐỌC nặng của Tra cứu thị trường — bao-CR-718.

Hai thứ tốn nhất khi mở / lật trang màn tra cứu (đo trên bảng thử 328 nghìn dòng, cỡ prod 03/11/2026):
  · ĐẾM tổng theo bộ lọc có từ khóa — phải dò hết ~61 MB tên hàng (LIKE '%…%' không dùng được chỉ mục, bảng chia
    phân vùng nên không đặt được FULLTEXT): ~0,5 giây mỗi lần, mà lật sang trang 2, 3… lại đếm lại y hệt.
  · `/options` — bảy câu GROUP BY trên cả bảng cho các ô chọn: ~1,1 giây mỗi lần mở màn.

Cả hai chỉ đổi khi dữ liệu đổi. Khóa đệm gắn với `MAX(id)` của bảng (lô nạp mới → id mới → khóa mới, tự bỏ bản
cũ) và hết hạn sau `TTL` giây — sửa / xóa tay một dòng hay gắn lại nhãn thì số đếm có thể lệch tối đa `TTL` giây.
Tra cứu thị trường không có phạm vi theo người (chỉ quyền `customs_price.read`) nên đệm dùng CHUNG mọi người.

Chỉ bật trên MySQL: SQLite của bộ test dùng lại id giữa các bài, đệm chung Redis sẽ trả số của bài trước.
Redis chết / chậm (timeout 0,2 giây) → tính thẳng, không bao giờ làm hỏng lời gọi.
"""
import hashlib
import json
import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings

from .model import CustomsLine

log = logging.getLogger("app.customs.read_cache")

TTL = 300
_TIMEOUT = 0.2
_PREFIX = "customs_read:"


def _client():
    import redis
    return redis.Redis.from_url(settings.REDIS_URL, socket_timeout=_TIMEOUT, socket_connect_timeout=_TIMEOUT,
                                decode_responses=True)


def _key(db: Session, kind: str, params: dict | None) -> str:
    stamp = db.query(func.max(CustomsLine.id)).scalar() or 0
    raw = json.dumps(params or {}, sort_keys=True, ensure_ascii=False, default=str)
    return f"{_PREFIX}{kind}:{stamp}:{hashlib.sha1(raw.encode()).hexdigest()}"


def _enabled(db: Session) -> bool:
    return db.get_bind().dialect.name == "mysql"


def cached(db: Session, kind: str, params: dict | None, compute):
    """`compute()` qua đệm; `params` là mọi thứ quyết định kết quả (bộ lọc)."""
    if not _enabled(db):
        return compute()
    key = _key(db, kind, params)
    client = None
    try:
        client = _client()
        hit = client.get(key)
        if hit is not None:
            return json.loads(hit)
    except Exception:  # noqa: BLE001 — Redis hỏng kiểu gì cũng là "không đọc được", tính thẳng
        log.warning("Redis không đọc được khóa %s — tính thẳng", key)
        client = None
    value = compute()
    if client is not None:
        try:
            client.set(key, json.dumps(value, ensure_ascii=False, default=str), ex=TTL)
        except Exception:  # noqa: BLE001
            log.warning("Redis không ghi được khóa %s — bỏ qua", key)
    return value


def clear() -> int:
    """Xóa mọi khóa đệm — gọi sau thao tác BỚT / ĐỔI dòng mà `MAX(id)` không đổi: gộp dòng trùng, sửa / xóa tay,
    hoàn tác lô. Redis hỏng thì thôi (đệm tự hết hạn sau `TTL`)."""
    try:
        client = _client()
        keys = list(client.scan_iter(match=_PREFIX + "*", count=500))
        return client.delete(*keys) if keys else 0
    except Exception:  # noqa: BLE001
        log.warning("Redis không xóa được đệm tra cứu thị trường — để tự hết hạn")
        return 0
