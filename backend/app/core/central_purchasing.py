"""Phòng thu mua MẶC ĐỊNH (thu mua trung tâm) — bao-CR-524, khách chốt 30/09/2026.

Trước CR này, số `0` ở các cột phòng của chứng từ thu mua mang nghĩa «Thu mua chung» — một
phòng ẢO không có trong danh mục (bao-CR-414/480/484/486/488):
  · `handler_dept_id = 0` trên YCMH (`tab_purchase_request`) · YCBG (`tab_survey_request`) ·
    ĐMH (`tab_purchase_order`);
  · `department_id = 0` trên công nợ (`tab_payable`, khoản nợ có đơn) và YCTT
    (`tab_payment_request`, phiếu gom nợ của đơn thu mua chung);
  · `department_id = 0` trên bảng phân công (`tab_category_assignee`) = bộ «Thu mua chung».

Khách bỏ phòng ảo đó: phòng thu mua mặc định là một PHÒNG THẬT trong danh mục — mã
`PBA017` «Sản xuất -Thu mua». Đây là NƠI DUY NHẤT tra mã → id phòng. KHÔNG gõ cứng id (id
local / dev / prod khác nhau); mã đổi được ở màn Cấu hình hệ thống (khóa
`central_purchasing_dept_code`).

Tương thích ngược: `0` còn sót (phiếu cũ chưa chạy `scripts/backfill_central_purchasing_dept.py`)
vẫn được coi là phòng thu mua mặc định ở MỌI chỗ đọc — trước và sau khi chạy script, không chỗ
nào gãy. Chỉ giao diện là thôi mời chọn «Thu mua chung».
Danh mục chưa có phòng mang mã đã cấu hình thì mọi hàm ở đây trả `0` = quay về đúng hành vi cũ.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

SETTING_KEY = "central_purchasing_dept_code"
DEFAULT_CODE = "PBA017"

#  Giá trị cũ của phòng ảo «Thu mua chung» — chỉ còn để ĐỌC dữ liệu chưa backfill.
LEGACY_CENTRAL_ID = 0


def get_central_dept_code() -> str:
    """Mã phòng thu mua mặc định đang cấu hình (rỗng → mặc định `PBA017`)."""
    from app.core import app_settings
    return (str(app_settings.get(SETTING_KEY) or "").strip() or DEFAULT_CODE)


def get_central_dept(db: Session):
    """Bản ghi `Department` của phòng thu mua mặc định; None nếu danh mục chưa có mã đó."""
    from app.modules.department.model import Department
    return db.query(Department).filter(Department.code == get_central_dept_code()).first()


def get_central_dept_id(db: Session) -> int:
    """Id phòng thu mua mặc định; 0 nếu danh mục chưa có phòng mang mã đã cấu hình.

    Nhớ tạm trong `db.info` theo mã (một phiên = một request / một script) để vòng lặp gọi nhiều
    lần không bắn nhiều câu truy vấn. Không nhớ kết quả 0 — phòng có thể vừa được tạo trong phiên.
    """
    code = get_central_dept_code()
    cache = db.info.setdefault("central_purchasing_dept", {})
    if cache.get(code):
        return cache[code]
    dep = get_central_dept(db)
    dept_id = int(dep.id) if dep else 0
    if dept_id:
        cache[code] = dept_id
    return dept_id


def central_dept_id_subquery():
    """Id phòng thu mua mặc định dưới dạng câu truy vấn con — cho chỗ dựng điều kiện SQL mà không
    cầm phiên DB (`core/scoping`). Danh mục chưa có mã → NULL, mọi so sánh với nó ra sai."""
    from app.modules.department.model import Department
    return select(Department.id).where(Department.code == get_central_dept_code()).scalar_subquery()


def is_central_dept(db: Session, dept_id) -> bool:
    """Phòng này có phải phòng thu mua mặc định không — `0` cũ (chưa backfill) cũng tính."""
    value = int(dept_id or 0)
    if value == LEGACY_CENTRAL_ID:
        return True
    return value == get_central_dept_id(db)


def normalize_handler_dept_id(db: Session, dept_id) -> int:
    """Giá trị GHI xuống cột phòng xử lý: `0` (không nhờ phòng nào / «Thu mua chung» cũ) →
    id phòng thu mua mặc định. Danh mục chưa có phòng đó thì giữ `0` như trước."""
    value = int(dept_id or 0)
    return value or get_central_dept_id(db)


def central_dept_ids(db: Session) -> set[int]:
    """Mọi giá trị mang nghĩa «phòng thu mua mặc định» trên dữ liệu: `{0, id thật}`."""
    ids = {LEGACY_CENTRAL_ID}
    central = get_central_dept_id(db)
    if central:
        ids.add(central)
    return ids
