"""API DANH MỤC CHỨC VỤ — `/api/job-positions` (duoc-CR-320).

Danh mục thuần nên dựng bằng `make_crud_router` (khóa quyền riêng
`job_position`), thêm đúng hai chốt mà bộ sinh không tự có:

* `before_update` — đổi tên thì **chép tên mới sang mọi hồ sơ đang giữ**;
* `before_delete` — chức vụ đang có người giữ thì không xóa.

⚠️ Vì sao nằm TRONG module `employee` chứ không thành module riêng: hai chiều
phụ thuộc. Danh mục cần `Employee` để đếm người đang giữ, còn hồ sơ cần
`JobPosition` để lấy nhãn. Tách đôi là hai module `import` lẫn nhau — vòng
`import` chỉ nổ lúc khởi động ở một thứ tự nạp nào đó, tức là trên máy khác chứ
không phải máy người vừa sửa. Cùng lý do `contact_model.py` ở lại đây.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.crud import make_crud_router

from . import position_service
from .position_model import JobPosition
from .position_schema import (JobPositionCreate, JobPositionResponse,
                              JobPositionUpdate)

#  ⚠️ Khóa quyền viết THẲNG vào lời gọi bên dưới, không rút thành hằng: bài
#  kiểm `test_dong_bo_giao_dien_v2` quét mã nguồn để chứng minh mục menu
#  `manage: true` có backend gác thật, và nó chỉ đọc được CHUỖI trong lời gọi
#  `make_crud_router(...)`. Rút thành biến là menu Chức vụ bị coi như không ai
#  gác — đúng thứ bài kiểm đó sinh ra để bắt.
ENTITY = "job_position"


def _propagate_rename(db: Session, obj: JobPosition, values: dict) -> None:
    """Chốt `before_update`: tên đổi thì nhãn trên hồ sơ phải đổi theo.

    Chạy TRƯỚC khi `values` được gán vào `obj`, nên `obj.name` còn là tên CŨ —
    đúng thứ `propagate_rename` cần để so. Bộ sinh CRUD `commit` sau chốt này
    nên hai lệnh đi chung một giao dịch.
    """
    if "name" in values:
        position_service.propagate_rename(db, obj, (values["name"] or "").strip())


def _block_delete_position_in_use(db: Session, obj: JobPosition) -> None:
    """Chốt `before_delete`: còn người giữ chức vụ này thì không xóa.

    Xóa là để lại hồ sơ trỏ vào một `position_id` không còn tồn tại: ô chọn trên
    màn hồ sơ hiện trống, còn cột nhãn vẫn giữ chữ cũ — hai chỗ nói hai điều
    khác nhau về cùng một người. Muốn dẹp một chức vụ thì bỏ tick «Đang dùng»:
    nó biến khỏi ô chọn nhưng hồ sơ cũ vẫn đọc được.
    """
    used = position_service.count_employees(db, obj.id)
    if used:
        #  ⚠️ Nói rõ «toàn công ty»: số này KHÔNG lọc theo phạm vi dữ liệu (chốt
        #  toàn vẹn phải đếm hết), nên nó có thể LỚN HƠN số dòng người dùng vừa
        #  đọc ở tab «Người đang giữ» — thiếu chữ đó thì câu chặn đọc như lỗi.
        raise HTTPException(
            400, f"«{obj.name}» đang có {used} hồ sơ giữ chức vụ này trên toàn công ty "
                 "nên không xóa được. Bỏ tick «Đang dùng» để ẩn khỏi ô chọn thay vì xóa.")


router = make_crud_router(
    "/api/job-positions", "job_position", JobPosition,
    JobPositionCreate, JobPositionUpdate, JobPositionResponse,
    #  ⚠️ Tên nào KHÔNG có ở đây thì bộ lọc nâng cao gửi lên cũng **bị bỏ qua
    #  trong im lặng** — không lỗi, chỉ là trả về nguyên danh sách như chưa lọc.
    #  Nên bốn tên này phải khớp đúng `filterConfig.fields` của
    #  `frontend-v2/.../config/job-position-crud.tsx`.
    filterable=["code", "name", "note", "is_active", "department_id"],
    unique_field="code",
    #  Chữ THƯỜNG cho khớp luật mã của danh mục này (`_code_lowercase` ở
    #  schema) — mã tự sinh mà hoa thì hai nguồn mã trông như hai hệ.
    code_prefix="cv",
    csv_headers={"code": "Mã chức vụ", "name": "Tên chức vụ",
                 "is_active": "Đang dùng", "note": "Ghi chú"},
    before_update=_propagate_rename,
    before_delete=_block_delete_position_in_use,
)
