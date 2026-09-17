"""API DANH MỤC LOẠI HỒ SƠ — `/api/dossier-types` (phân hệ Hồ sơ, 16/09/2026).

Danh mục thuần: dựng bằng `make_crud_router` với khóa quyền riêng
`dossier_type`. Bộ sinh lo list / get / create / update / delete + nhật ký +
nhập-xuất CSV, và tự gác cả hai trục (`require` + `apply_scope`).

Hai chốt riêng, cả hai vì `tab_dossier.dossier_type_name` là NHÃN ĐÃ CHÉP (xem
`model.py`):

* `before_update` — đổi tên loại thì chép tên mới sang mọi hồ sơ đang mang tên
  cũ. Thiếu nó thì màn hình hiện tên mới còn bản in đưa cho cơ quan nhà nước ra
  tên cũ.
* `before_delete` — loại đang có hồ sơ dùng thì chặn xóa.

⚠️ Loại hồ sơ còn là **khuôn biểu mẫu** (`field_schema`), nên xóa một loại không
chỉ làm hồ sơ mất phân loại — nó làm mất luôn lời giải nghĩa cho mọi giá trị
đang nằm trong `tab_dossier.extra_fields` của những hồ sơ ấy: các khóa còn đó
nhưng không ai biết `so_gp` từng là ô gì.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.crud import make_crud_router
from app.core.database import get_db
from app.core.response import success

from . import service
from .type_model import DossierType
from .type_schema import (DossierTypeCreate, DossierTypeResponse,
                          DossierTypeUpdate)


def _propagate_rename(db: Session, obj: DossierType, values: dict) -> None:
    """Chốt `before_update`: tên đổi thì nhãn trên hồ sơ phải đổi theo.

    Chạy TRƯỚC khi `values` được gán vào `obj`, và bộ sinh `commit` sau chốt này
    nên hai lệnh đi chung một giao dịch — không có cửa sổ nào mà danh mục đã đổi
    tên còn hồ sơ thì chưa.
    """
    if "name" in values:
        service.propagate_type_rename(db, obj.id, (values["name"] or "").strip())


def _block_delete_type_in_use(db: Session, obj: DossierType) -> None:
    """Chốt `before_delete`: còn hồ sơ mang loại này thì không xóa."""
    used = service.count_by_type(db, obj.id)
    if used:
        #  ⚠️ Nói rõ «toàn công ty»: số này KHÔNG lọc theo phạm vi dữ liệu (chốt
        #  toàn vẹn phải đếm hết), nên nó có thể LỚN HƠN con số người dùng vừa
        #  đọc ở cột «Hồ sơ đang dùng» — thiếu chữ đó thì câu chặn đọc như lỗi.
        raise HTTPException(
            400, f"«{obj.name}» đang có {used} hồ sơ dùng trên toàn công ty nên không "
                 "xóa được. Bỏ tick «Còn dùng» để ẩn khỏi ô chọn thay vì xóa — hồ sơ cũ "
                 "vẫn đọc được loại của chúng.")


#  ⚠️ `/stats` phải đăng ký TRƯỚC bộ sinh CRUD, vì bộ sinh có `/{oid}`: FastAPI
#  khớp theo thứ tự đăng ký, để sau thì «stats» rơi vào `{oid}` và trả 422 khi
#  ép thành số. Vì thế mới có router bọc ngoài này (cùng khuôn
#  `employee/position_controller.py`).
router = APIRouter()


@router.get("/api/dossier-types/stats")
def get_type_stats(db: Session = Depends(get_db),
                   user=Depends(require("dossier_type", "read"))):
    """Đếm NGƯỢC: mỗi loại có bao nhiêu hồ sơ đang dùng.

    Tách thành endpoint riêng thay vì thêm `dossier_count` vào
    `DossierTypeResponse`: serializer chạy cho TỪNG dòng nên đếm ở đó là một
    truy vấn mỗi dòng (N+1, bài học duoc-CR-322), và nó chạy cả ở những chỗ chỉ
    cần tên loại để đổ ô chọn.

    ⚠️ Số ở đây **lọc theo phạm vi dữ liệu** của người gọi trên entity
    `dossier`, nên nó có thể NHỎ HƠN con số mà chốt chặn xóa dùng — hai luật
    ngược nhau, cố ý: số bày cho người xem thì lọc, chốt toàn vẹn thì đếm hết.

    ⚠️ Thiếu quyền `dossier.read` thì `apply_scope` trả "chặn tất" và kết quả
    rỗng — **không phải 403**. Giao diện phải tự tắt cột, không thì mọi dòng
    hiện 0 và người đọc tin là chưa hồ sơ nào dùng loại nào.
    """
    from sqlalchemy import func

    from app.core.auth import get_perm_profile
    from app.core.scoping import apply_scope

    from .model import Dossier

    q = db.query(Dossier.dossier_type_id, func.count(Dossier.id))
    q = apply_scope(q, Dossier, "dossier", user, get_perm_profile(db, user))
    #  MỘT truy vấn gộp nhóm cho cả trang, bất kể bao nhiêu loại — đừng đổi
    #  thành vòng lặp `count()` theo từng dòng.
    rows = q.group_by(Dossier.dossier_type_id).all()
    return success({"items": [{"type_id": tid, "total": total} for tid, total in rows]})


#  ⚠️ Khóa quyền viết THẲNG vào lời gọi, không rút thành hằng: bài kiểm
#  `test_dong_bo_giao_dien_v2` quét mã nguồn để chứng minh mục menu `manage:
#  true` có backend gác thật, và nó chỉ đọc được CHUỖI nằm ngay trong lời gọi
#  `make_crud_router(...)`. Rút thành biến là menu «Loại hồ sơ» bị coi như không
#  ai gác — đúng thứ bài kiểm đó sinh ra để bắt.
router.include_router(make_crud_router(
    "/api/dossier-types", "dossier_type", DossierType,
    DossierTypeCreate, DossierTypeUpdate, DossierTypeResponse,
    #  ⚠️ Tên nào KHÔNG có ở đây thì bộ lọc gửi lên cũng **bị bỏ qua trong im
    #  lặng** — không lỗi, chỉ là trả nguyên danh sách như chưa lọc. Bốn tên này
    #  phải khớp tham số mà `frontend-v2/.../api/dossier-type-api.ts` gửi.
    filterable=["code", "name", "description", "is_active"],
    #  ⚠️ Trùng mã thì bộ sinh trả câu **«code đã tồn tại»** — nửa Anh nửa Việt,
    #  không nói mã nào. Câu đó dựng từ tên cột trong `core/crud.py` và dùng
    #  chung cho hơn hai chục danh mục, nên KHÔNG vá riêng ở đây: thử thêm
    #  `before_create` để nói câu tử tế hơn là công cốc — chốt `unique_field`
    #  chạy TRƯỚC `before_create`, và `commit_or_conflict` cũng lặp lại câu ấy
    #  làm lưới cuối. Muốn sửa thì sửa một lần ở bộ sinh, cho cả hệ.
    unique_field="code",
    csv_headers={"code": "Mã loại", "name": "Tên loại",
                 "description": "Mô tả", "is_active": "Còn dùng",
                 "default_valid_months": "Hạn mặc định (tháng)",
                 "field_count": "Số ô tùy biến"},
    before_update=_propagate_rename,
    before_delete=_block_delete_type_in_use,
))
