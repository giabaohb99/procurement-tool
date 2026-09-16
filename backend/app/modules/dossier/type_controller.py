"""API DANH MỤC LOẠI HỒ SƠ — `/api/dossier-types` (phân hệ Hồ sơ, 16/09/2026).

Danh mục thuần: dựng bằng `make_crud_router` với khóa quyền riêng
`dossier_type`. Bộ sinh lo list / get / create / update / delete + nhật ký +
nhập-xuất CSV, và tự gác cả hai trục (`require` + `apply_scope`).

⚠️ **Chưa có chốt `before_delete`**, và đó là điều đúng lúc này: bảng hồ sơ
(`tab_dossier`) chưa tồn tại nên không có gì trỏ tới một loại — xóa không để lại
dữ liệu mồ côi. Dựng bảng hồ sơ thì **phải** thêm ngay hai chốt, theo đúng khuôn
`employee/position_controller.py`:

  * `before_delete` — loại đang có hồ sơ dùng thì chặn, câu chặn nói rõ «trên
    toàn công ty» vì số đó KHÔNG lọc theo phạm vi người gọi;
  * `before_update` — đổi tên thì chép tên mới sang mọi hồ sơ đang mang tên cũ.

Cùng lúc đó mới thêm endpoint `/stats` đếm ngược (đếm trong serializer là N+1 —
xem duoc-CR-322), và **phải đăng ký TRƯỚC** `make_crud_router` vì bộ sinh có
`/{oid}`: FastAPI khớp theo thứ tự, để sau thì `/stats` rơi vào `{oid}` và trả
422 khi ép «stats» thành số.
"""
from app.core.crud import make_crud_router

from .type_model import DossierType
from .type_schema import (DossierTypeCreate, DossierTypeResponse,
                          DossierTypeUpdate)

#  ⚠️ Khóa quyền viết THẲNG vào lời gọi, không rút thành hằng: bài kiểm
#  `test_dong_bo_giao_dien_v2` quét mã nguồn để chứng minh mục menu `manage:
#  true` có backend gác thật, và nó chỉ đọc được CHUỖI nằm ngay trong lời gọi
#  `make_crud_router(...)`. Rút thành biến là menu «Loại hồ sơ» bị coi như không
#  ai gác — đúng thứ bài kiểm đó sinh ra để bắt.
router = make_crud_router(
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
                 "default_valid_months": "Hạn mặc định (tháng)"},
)
