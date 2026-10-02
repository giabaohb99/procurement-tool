"""Chặn bấm dồn `scope=all` của mục Xuất Excel Thuốc BVTV (M1, review 02/10/2026).

Chỉ áp cho `scope=all` (quét hết danh mục, có thể chậm; `scope=page` chỉ một trang, nhẹ, không
cần khóa). HAI lớp:

  · `EXPORTING_ALL` — set TRONG TIẾN TRÌNH, lớp chặn NHANH, nhưng mỗi tiến trình uvicorn có bộ
    nhớ RIÊNG — hai yêu cầu của CÙNG một người rơi vào HAI tiến trình khác nhau (`--workers 2`
    trên prod) sẽ không thấy nhau nếu chỉ có lớp này.
  · Khóa CÓ TÊN của MySQL (`pesticide_export_<uid>`, không chờ — `GET_LOCK(.., 0)`) trên KẾT NỐI
    RIÊNG — đứng vững qua NHIỀU tiến trình, cùng lý do với `pesticide_service._import_lock`:
    khóa gắn với kết nối, kết nối của `db` có thể trả về pool giữa chừng. SQLite (bộ test)
    không có khóa có tên — bỏ qua nhánh này, chỉ còn lớp trong-tiến-trình (đủ cho bộ test, chạy
    một tiến trình).
"""
from contextlib import contextmanager

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

BUSY_MESSAGE = "Bạn đang xuất toàn bộ danh mục Thuốc BVTV — chờ xuất xong rồi thử lại"

#  Người đang xuất TOÀN BỘ danh mục — chặn CHÍNH NGƯỜI ĐÓ bấm lần hai trong lúc lần đầu còn chạy.
EXPORTING_ALL: set[int] = set()


@contextmanager
def export_lock(db: Session, user_id: int):
    if user_id in EXPORTING_ALL:
        raise HTTPException(429, BUSY_MESSAGE)
    EXPORTING_ALL.add(user_id)
    try:
        bind = db.get_bind()
        if bind.dialect.name != "mysql":
            yield
            return
        name = f"pesticide_export_{user_id}"
        with bind.connect() as conn:
            if conn.execute(text("SELECT GET_LOCK(:n, 0)"), {"n": name}).scalar() != 1:
                raise HTTPException(429, BUSY_MESSAGE)
            try:
                yield
            finally:
                conn.execute(text("SELECT RELEASE_LOCK(:n)"), {"n": name})
    finally:
        EXPORTING_ALL.discard(user_id)
