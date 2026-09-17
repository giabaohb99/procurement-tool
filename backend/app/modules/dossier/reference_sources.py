"""DANH MỤC mà một ô «Chọn từ danh mục» được phép trỏ tới.

Trường tùy biến kiểu `reference` lưu **ID** của một dòng trong danh mục có sẵn,
thay vì một chuỗi người dùng tự gõ. Chữa đúng chỗ tệ nhất của ô chọn tự gõ: mỗi
người gõ một kiểu, không ai sửa tập trung được, và «Nhân sự thực hiện» thì gõ
tên xong đổi tên nhân sự là dữ liệu trôi.

⚠️ **DANH SÁCH TRẮNG theo KHÓA, tuyệt đối không nhận URL từ máy khách.** Cho
khai URL nghĩa là bất kỳ ai sửa được bộ trường đều bắt máy chủ đi đọc một đường
dẫn tùy ý, và biến ô chọn thành cửa dò mọi endpoint của hệ. Khóa lạ thì chặn.

⚠️ Đây là danh sách **cố ý hẹp**. Thêm một danh mục vào đây là mở nó cho mọi
người sửa được bộ trường, nên mỗi dòng phải trả lời được: *ai đọc được danh mục
này?* Quyền vẫn do chính endpoint của nó gác (ô chọn gọi API bằng token của
người dùng), nhưng đừng trông vào đó mà thêm bừa.
"""

#  khóa → (đường dẫn module, tên lớp). Import bên trong hàm để không dựng vòng
#  import với các module nghiệp vụ — cùng khuôn `core/entity_models.py`.
REFERENCE_MODELS: dict[str, tuple[str, str]] = {
    "employee": ("app.modules.employee.model", "Employee"),
    "department": ("app.modules.department.model", "Department"),
    "company": ("app.modules.company.model", "Company"),
    "supplier": ("app.modules.supplier.model", "Supplier"),
    "product": ("app.modules.product.model", "Product"),
}

#  Nhãn tiếng Việt — bản TypeScript ở
#  `frontend-v2/src/modules/dossier/types/dossier-reference-sources.ts` phải
#  khớp từng khóa. Lệch một khóa thì người dùng khai được một danh mục mà
#  backend chặn, hoặc ngược lại.
REFERENCE_LABELS: dict[str, str] = {
    "employee": "Nhân sự",
    "department": "Phòng ban",
    "company": "Pháp nhân",
    "supplier": "Nhà cung cấp",
    "product": "Sản phẩm / Vật tư",
}


def is_known(source: str) -> bool:
    return source in REFERENCE_MODELS


def model_of(source: str):
    """Model của một danh mục. `None` nếu khóa lạ."""
    entry = REFERENCE_MODELS.get(source)
    if not entry:
        return None
    from importlib import import_module

    module, name = entry
    return getattr(import_module(module), name)


def exists(db, source: str, row_id: int) -> bool:
    """Dòng được trỏ tới còn tồn tại không?

    ⚠️ Kiểm thật chứ không tin máy khách, và lý do rất cụ thể: ô này lưu **ID**,
    mà ID trỏ vào hư không thì màn hình hiện **trống trơn** — nhìn y hệt ô chưa
    ai nhập. Không lỗi, không cảnh báo, không cách nào biết hồ sơ đang mất dữ
    liệu. Một câu 422 lúc lưu rẻ hơn nhiều so với việc đó.

    ⚠️ CỐ Ý không lọc theo phạm vi dữ liệu người gọi: đây là câu hỏi «dòng này
    có thật không», không phải «anh có được xem nó không». Cửa API của chính
    danh mục đó mới là chỗ trả lời câu thứ hai, và ô chọn gọi nó bằng token của
    người dùng.
    """
    model = model_of(source)
    if model is None:
        return False
    return db.get(model, row_id) is not None
