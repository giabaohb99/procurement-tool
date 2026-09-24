"""API HỒ SƠ — `/api/dossiers` (phân hệ Hồ sơ, 16/09/2026).

Dựng bằng `make_crud_router` với khóa quyền `dossier`. Bộ sinh lo list / get /
create / update / delete + nhật ký + xuất CSV, và tự gác **cả hai trục**:
`require("dossier", …)` cho hành động, `apply_scope` cho phạm vi dữ liệu.

⚠️ **`SCOPE_FIELDS["dossier"]` khai bằng CỘT THẬT** (`company_id` ·
`department_id` · `created_by` · `owner_employee_id`), KHÔNG dùng `PUBLIC`. Đây
là điểm khác căn bản so với danh mục *Loại hồ sơ*: một loại giấy tờ là chuyện
chung cả công ty, còn một bộ hồ sơ thì thuộc về một phòng và một người. Khai
`PUBLIC` cho nhanh là ai có `dossier.read` đọc được hồ sơ pháp lý của mọi pháp
nhân — đúng món nợ vô hình đã từ chối ở đợt trước.

⚠️ Hai chốt riêng, cả hai vì cùng một lý do — cột `dossier_type_name` là NHÃN ĐÃ
CHÉP (xem `model.py`):
  * `before_create` / `before_update` chép tên loại + kiểm bộ trường tùy biến;
  * `type_controller.before_update` chép tên mới sang mọi hồ sơ khi loại đổi tên.
"""
from app.core.crud import make_crud_router

from .model import Dossier
from .schema import DossierCreate, DossierResponse, DossierUpdate
from .depends_service import check_depends
from .service import apply_extra_fields, sync_type_label


def _before_create(db, data: DossierCreate) -> None:
    """Bộ sinh trao SCHEMA (không phải dict) ở đường tạo — dựng dict rồi chép lại.

    ⚠️ `dossier_type_name` gửi lên từ máy khách bị GHI ĐÈ ở đây, luôn luôn. Nó có
    mặt trong `DossierCreate` chỉ vì `Model(**data.model_dump())` không nhìn thấy
    trường nào nằm ngoài schema — chứ không phải để ai đó khai tay.
    """
    values = {"dossier_type_id": data.dossier_type_id, "extra_fields": data.extra_fields,
              "custom_fields": data.custom_fields}
    sync_type_label(db, values)
    apply_extra_fields(db, values)
    data.dossier_type_name = values["dossier_type_name"]
    data.extra_fields = values["extra_fields"]
    #  `0` = chưa có id (đang tạo) → chỉ kiểm mấy tờ được trỏ tới là có thật;
    #  chưa tồn tại thì chưa thể nằm trong vòng nào.
    data.depends = check_depends(db, 0, data.depends)


def _before_update(db, obj: Dossier, values: dict) -> None:
    """Đường sửa trao dict các ô ĐƯỢC GỬI (`exclude_unset`) — sửa tại chỗ.

    `obj` còn mang dữ liệu CŨ ở đây, nên `sync_type_label` đối chiếu được «loại
    này có phải loại đang giữ không» để nới cho hồ sơ mang loại đã ngừng dùng.
    """
    sync_type_label(db, values, obj)
    apply_extra_fields(db, values, obj)
    #  ⚠️ Chỉ kiểm khi ô này ĐƯỢC GỬI. `values` là `exclude_unset`, nên `"depends"
    #  in values` phân biệt được «xóa hết tiên quyết» (`[]`) với «đừng đụng vào»
    #  (không có khóa) — hai thứ mà `if values.get("depends")` gộp làm một.
    if "depends" in values:
        values["depends"] = check_depends(db, obj.id, values["depends"] or [])


router = make_crud_router(
    "/api/dossiers", "dossier", Dossier,
    DossierCreate, DossierUpdate, DossierResponse,
    #  ⚠️ Tên nào KHÔNG có ở đây thì bộ lọc gửi lên bị **bỏ qua trong im lặng** —
    #  không lỗi, chỉ là trả nguyên danh sách như chưa lọc. Phải khớp tham số mà
    #  `frontend-v2/.../api/dossier-api.ts` gửi.
    #
    #  KHÔNG có `expiry_state`: nó là trường SUY RA, không phải cột, nên
    #  `apply_filters` không lọc được (`getattr(model, key)` ra `None` → bỏ qua).
    #  Câu hỏi «cái nào sắp hết hạn» trả lời bằng cách SẮP XẾP theo `expiry_date`
    #  — cột đó có chỉ mục và `apply_sort` nhận nó.
    filterable=["code", "name", "dossier_type_id", "status", "owner_employee_id",
                "department_id", "company_id", "storage_location"],
    #  Bỏ trống mã thì máy cấp `HS0001`, `HS0002`… — hồ sơ là chứng từ phát sinh
    #  hằng ngày, bắt nghĩ ra mã trước khi lưu được là dựng rào ngay cửa vào.
    code_prefix="HS",
    unique_field="code",
    #  ⚠️ Hồ sơ VÔ THỜI HẠN (`expiry_date` NULL) phải xuống CUỐI, không lên đầu.
    #  MySQL xếp `NULL` lên đầu khi sắp tăng dần, mà thứ tự mặc định của màn danh
    #  sách là `expiry_date asc` — sinh ra để trả lời «tờ nào sắp hết hạn?».
    #  Không đẩy xuống thì toàn bộ hồ sơ vô thời hạn (phần lớn danh mục hiện tại
    #  mặc định như vậy) chiếm sạch trang đầu và dìm đúng những tờ cần để mắt.
    sort_nulls_last=("expiry_date", "issued_date"),
    csv_headers={"code": "Mã hồ sơ", "name": "Tên hồ sơ",
                 "dossier_type_name": "Loại hồ sơ", "status_label": "Tình trạng",
                 "issued_date": "Ngày cấp", "expiry_date": "Hạn hiệu lực",
                 "owner_name": "Người phụ trách", "department_name": "Bộ phận giữ",
                 "company_name": "Pháp nhân", "storage_location": "Nơi lưu trữ"},
    #  ⚠️ **CHỈ XUẤT, KHÔNG NHẬP.** Bảng cột trên là bảng bày ra tệp Excel nên
    #  quá nửa là trường SUY RA (`status_label`, `owner_name`, `department_name`,
    #  `company_name` — `@property`, không phải cột). Đường nhập của bộ sinh
    #  `setattr` thẳng từng khóa lên bản ghi, gặp `@property` không setter là
    #  **500**; và nó KHÔNG gọi `_before_create`/`_before_update` nên chép nhãn
    #  loại, kiểm ô tùy biến, chặn loại đã ngừng dùng đều bị đi vòng qua hết —
    #  lọt thì đẻ ra hồ sơ `dossier_type_id = 0`, thứ schema cấm thẳng.
    #
    #  Muốn mở lại đường nhập thì phải khai một bảng cột RIÊNG chỉ gồm cột thật,
    #  và dạy bộ sinh gọi hai chốt trước khi gán. Chưa ai cần: giao diện v2
    #  không có nút nhập CSV nào.
    csv_import=False,
    before_create=_before_create,
    before_update=_before_update,
)
