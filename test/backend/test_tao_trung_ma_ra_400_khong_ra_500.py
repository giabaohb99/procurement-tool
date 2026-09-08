"""TẠO TRÙNG MÃ PHẢI RA 400 ĐỌC ĐƯỢC, KHÔNG PHẢI 500.

⚠️ LỖI ĐÃ XẢY RA (04/09/2026, trang *Thêm loại nghỉ*). Bộ CRUD chung kiểm trùng
bằng một câu `SELECT` rồi mới `INSERT`. Bấm nút Tạo ba lần liên tiếp thì ba lệnh
bay đi gần như cùng lúc, cả ba đều thấy "chưa có" ở câu SELECT, rồi hai lệnh
chậm chân đâm vào ràng buộc duy nhất của DB. `IntegrityError` không có ai bắt nên
rơi ra `unhandled_exception_handler` thành **500 kèm mã sự cố**: người dùng tạo
xong nhận một toast xanh rồi hai toast đỏ *"Hệ thống gặp lỗi không lường trước"*.

Giao diện nay cũng chặn bấm trùng (`useSingleFlight`), nhưng đó chỉ lo được một
tab trình duyệt — hai người bấm cùng lúc thì chốt còn lại nằm ở đây.
"""
import pytest
from fastapi import HTTPException

from app.core.crud import commit_or_conflict
from app.modules.leave.catalog_model import LeaveType


def _them(db, code: str) -> LeaveType:
    obj = LeaveType(code=code, name=f"Loại {code}")
    db.add(obj)
    return obj


def test_trung_rang_buoc_duy_nhat_thanh_loi_400(db):
    _them(db, "annual")
    commit_or_conflict(db, "code đã tồn tại")

    _them(db, "annual")  # kẻ chậm chân trong cuộc đua
    with pytest.raises(HTTPException) as loi:
        commit_or_conflict(db, "code đã tồn tại")

    assert loi.value.status_code == 400
    assert "đã tồn tại" in loi.value.detail


def test_phien_lam_viec_con_dung_duoc_sau_khi_hong(db):
    """Không `rollback` thì phiên kẹt ở trạng thái hỏng, mọi câu sau đều nổ theo."""
    _them(db, "sick")
    commit_or_conflict(db, "code đã tồn tại")

    _them(db, "sick")
    with pytest.raises(HTTPException):
        commit_or_conflict(db, "code đã tồn tại")

    #  Ghi được tiếp bằng mã khác = phiên đã sạch.
    _them(db, "unpaid")
    commit_or_conflict(db, "code đã tồn tại")
    assert db.query(LeaveType).count() == 2


def test_khong_trung_thi_luu_binh_thuong(db):
    _them(db, "wedding")
    commit_or_conflict(db, "code đã tồn tại")
    assert db.query(LeaveType).filter(LeaveType.code == "wedding").first() is not None


def test_khong_nuot_loi_khac(db):
    """Chỉ bắt vi phạm ràng buộc — lỗi khác phải bay lên nguyên vẹn để còn thấy."""
    class LoiKhac(Exception):
        pass

    class PhienGia:
        def commit(self):
            raise LoiKhac("mất kết nối")

        def rollback(self):  # pragma: no cover — không được gọi tới
            raise AssertionError("không được rollback khi lỗi không phải ràng buộc")

    with pytest.raises(LoiKhac):
        commit_or_conflict(PhienGia(), "code đã tồn tại")
