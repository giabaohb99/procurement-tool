from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import success

from . import service

router = APIRouter(prefix="/api/me/preferences", tags=["user_preference"])


class SavePreferencesIn(BaseModel):
    values: dict = {}


#  CỐ Ý KHÔNG dùng `require(entity, action)`: đây là tuỳ chọn hiển thị của CHÍNH
#  người đang đăng nhập, không phải dữ liệu nghiệp vụ. Gác bằng phân quyền thì
#  phải khai thêm một entity vào `ENTITIES` + `SCOPE_FIELDS` (test 44/44 ở
#  `test_pham_vi_khai_du_b07.py`) cho một thứ mà đằng nào ai cũng được sửa phần
#  của mình. `get_current_user` khoá theo `user.id` là đủ và chặt hơn: không có
#  đường nào đọc/ghi tuỳ chọn của người khác vì id lấy từ token, không từ URL.


@router.get("")
def get_my_preferences(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return success(service.get_preferences(db, user.id))


@router.put("")
def save_my_preferences(
    data: SavePreferencesIn,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return success(service.save_preferences(db, user.id, data.values), "Đã lưu tuỳ chọn")
