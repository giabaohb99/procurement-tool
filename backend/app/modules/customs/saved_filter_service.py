"""Bộ lọc đã lưu của màn Tra cứu giá hải quan — bao-CR-496 (F07).

Riêng từng TÀI KHOẢN: mọi hàm nhận `user_id` và chỉ thấy / sửa / xóa dòng của đúng người đó;
dòng của người khác coi như KHÔNG TỒN TẠI (404, không phải 403 — không để lộ có bộ lọc ấy).
`is_shared` chưa dùng: `list_for` đã chừa nhánh đọc thêm bộ lọc chung để sau mở không phải đổi API.
"""
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .model import CustomsSavedFilter

MAX_PER_USER = 50


def list_for(db: Session, user_id: int, include_shared: bool = False) -> list[CustomsSavedFilter]:
    cond = CustomsSavedFilter.user_id == user_id
    if include_shared:
        cond = or_(cond, CustomsSavedFilter.is_shared.is_(True))
    return (db.query(CustomsSavedFilter).filter(cond)
            .order_by(CustomsSavedFilter.name.asc(), CustomsSavedFilter.id.asc()).all())


def get_own(db: Session, user_id: int, fid: int) -> CustomsSavedFilter:
    """Dòng của CHÍNH người gọi; của người khác → 404 như không có."""
    obj = db.get(CustomsSavedFilter, fid)
    if not obj or obj.user_id != user_id:
        raise HTTPException(404, "Không tìm thấy bộ lọc đã lưu")
    return obj


def create(db: Session, user_id: int, name: str, params: str) -> CustomsSavedFilter:
    count = db.query(CustomsSavedFilter).filter(CustomsSavedFilter.user_id == user_id).count()
    if count >= MAX_PER_USER:
        raise HTTPException(400, f"Mỗi người lưu tối đa {MAX_PER_USER} bộ lọc — xóa bớt bộ cũ rồi lưu lại")
    dup = (db.query(CustomsSavedFilter)
           .filter(CustomsSavedFilter.user_id == user_id, CustomsSavedFilter.name == name).first())
    if dup:
        raise HTTPException(400, f"Bạn đã có bộ lọc tên «{name}» — chọn tên khác hoặc bấm Cập nhật bộ đó")
    obj = CustomsSavedFilter(user_id=user_id, name=name, params=params or "", is_shared=False,
                             created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, user_id: int, fid: int, name: str | None, params: str | None) -> CustomsSavedFilter:
    obj = get_own(db, user_id, fid)
    if name is not None and name != obj.name:
        dup = (db.query(CustomsSavedFilter)
               .filter(CustomsSavedFilter.user_id == user_id, CustomsSavedFilter.name == name,
                       CustomsSavedFilter.id != fid).first())
        if dup:
            raise HTTPException(400, f"Bạn đã có bộ lọc tên «{name}»")
        obj.name = name
    if params is not None:
        obj.params = params
    obj.updated_by = user_id
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, user_id: int, fid: int) -> None:
    obj = get_own(db, user_id, fid)
    db.delete(obj)
    db.commit()
