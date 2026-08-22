from fastapi import APIRouter, Depends, HTTPException

from app.core import code_sets  # noqa: F401  (nạp cho đủ sổ đăng ký)
from app.core.auth import get_current_user
from app.core.response import success
from app.core.status_catalog import all_sets

router = APIRouter(prefix="/api/meta", tags=["meta"])


def _out(cs) -> dict:
    return {"name": cs.name, "title": cs.title, "options": cs.full_options}


@router.get("/statuses")
def list_status_sets(user=Depends(get_current_user)):
    """Toàn bộ bộ mã cố định đang khai ở backend (QĐ-9 / B-01).

    Đây là bản để TRA CỨU và để đối chiếu, KHÔNG phải nguồn cho giao diện dựng ô chọn lúc
    chạy. Giao diện đọc tệp TypeScript sinh sẵn từ chính sổ đăng ký này
    (`scripts/gen_status_ts.py` → `frontend-v2/src/shared/constants/statuses.ts`) — cách H2
    ở `doc/erp/06` §5: sinh ra rồi lưu vào mã nguồn, CI so lại. Lấy động qua API thì mỗi màn
    phải chờ thêm một lượt gọi, và lệch phiên bản thì không ai biết.
    """
    return success([_out(cs) for cs in all_sets().values()])


@router.get("/statuses/{name}")
def get_status_set(name: str, user=Depends(get_current_user)):
    sets = all_sets()
    if name not in sets:
        raise HTTPException(404, f"Không có bộ mã '{name}'")
    return success(_out(sets[name]))
