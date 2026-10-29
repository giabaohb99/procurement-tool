"""Tool HỒ SƠ NHÂN SỰ của trợ lý AI (T45 `employee_lookup`).

Trả lời «anh Nam phòng nào», «ai là quản lý trực tiếp của tôi», «cho xin email
của chị Hà bên Kế toán» — tức phần DANH BẠ của hồ sơ nhân sự.

⚠️ **Đây là tool ĐẦU TIÊN đọc hồ sơ của NGƯỜI KHÁC.** Mọi tool trước đó chỉ đọc
chứng từ; hồ sơ nhân sự thì ngoài chức danh còn có ngày sinh, số CCCD, địa chỉ
nhà và số tài khoản ngân hàng. Ba lớp chặn, cả ba đều cần:

1. **Khóa `employee.read`** — ai không có thì không tra được ai.
2. **`apply_scope`** — người chỉ được khai phạm vi phòng ban thì chỉ thấy phòng
   mình, đúng như màn Nhân sự.
3. **Danh sách trường TRẮNG** — chỉ trả đúng 13 trường danh bạ liệt kê ở
   `_OUT_FIELDS` (+ `extra_phones`, dựng riêng), và vẫn chạy qua
   `sensitive.mask_many` một lượt nữa. Bộ 15 trường nhạy cảm khai ở
   `modules/employee/sensitive.py` **không** nằm trong danh sách trắng, nên lượt
   che đó hôm nay là vô hiệu — giữ nó làm chốt cho ngày ai đó thêm một trường
   vào đây mà quên rằng trợ lý AI cũng là một đường ra dữ liệu (đúng bài học ghi
   ở đầu `sensitive.py`).

⚠️ **LƯƠNG (`salary_monthly`, `allowance_monthly`, duoc-CR-693) KHÔNG BAO GIỜ ra
khỏi tool này — kể cả khi người hỏi là chính chủ.** Chủ trương: trợ lý AI không
đọc lương; chính chủ xem ở Trang cá nhân. Cũng không có tham số lọc / sắp xếp nào
chạm tới lương (thứ tự cũng là thông tin). Bài kiểm `test_assistant_nhan_su_cr693_694.py`
đỏ nếu hai trường đó lọt vào `_OUT_FIELDS`.

Nhãn số chính (`phone_label`) và số điện thoại khác (`extra_phones`, duoc-CR-694)
cùng mức với `phone` (không thuộc nhóm nhạy cảm) nên trả kèm, mỗi số phụ
`{number, label}`; tìm theo số phụ
dùng cùng luật với ô tìm nhanh của màn Nhân sự (`employee.service.apply_keyword_search`).

⚠️ `Employee.avatar` và `User.avatar` là `@property`, không phải cột — đừng đưa
vào `with_entities`, sẽ `ArgumentError` lúc chạy. Ở đây không trả ảnh.
"""
import re

from sqlalchemy import String, cast, or_
from sqlalchemy.orm import joinedload

from app.core.scoping import apply_scope
from app.modules.employee.model import Employee
from app.modules.employee.sensitive import mask_many

from .base import ToolContext, ToolSpec, denied

MAX_ROWS = 30

#  DANH SÁCH TRẮNG các trường được phép ra khỏi tool này. Đọc chú thích đầu tệp
#  trước khi thêm một dòng vào đây.
_OUT_FIELDS = ("id", "code", "full_name", "position", "job_level_label", "department_name",
               "company_name", "email", "phone", "phone_label", "direct_manager_name", "status_label",
               "is_active")
#  Trường CẤM tuyệt đối với tool này (CR-693) — bài kiểm soi giao với `_OUT_FIELDS` phải rỗng.
NEVER_FIELDS = ("salary_monthly", "allowance_monthly", "salary_set", "salary_updated_at")
#  Từ khóa trông như số điện thoại (toàn chữ số / ký tự phân cách, ≥ 3 chữ số) mới quét số phụ — KHỚP luật
#  `employee.service.apply_keyword_search`, kẻo chữ «number» / «label» trong chính JSON khớp từ khóa chữ bất kỳ.
_PHONE_LIKE = re.compile(r"[0-9\s+.\-()]+")

_PARAMS = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Từ khóa tìm: họ tên, mã nhân viên, email công việc, số điện "
                           "thoại (cả số chính lẫn số khác) hoặc chức vụ. Bỏ trống = liệt kê "
                           "theo phòng ban.",
        },
        "department_id": {
            "type": "integer",
            "description": "Chỉ lấy nhân sự thuộc phòng ban này. Chỉ dùng khi đã biết ID "
                           "phòng ban; không biết thì tìm bằng `query` theo tên người.",
        },
        "active_only": {
            "type": "boolean",
            "description": "Chỉ lấy người ĐANG làm việc (mặc định true). Đặt false khi cần "
                           "tra cả người đã nghỉ.",
        },
        "limit": {
            "type": "integer",
            "description": f"Số dòng tối đa (mặc định 10, trần {MAX_ROWS}).",
        },
    },
}

_DESC = (
    "Tra DANH BẠ NHÂN SỰ: họ tên, mã nhân viên, chức vụ, cấp bậc, phòng ban, công ty, email "
    "và điện thoại công việc (phone = số chính, phone_label = nhãn của nó; extra_phones = các "
    "số khác, mỗi số kèm nhãn như Công việc / Zalo), người quản lý trực tiếp, tình trạng làm "
    "việc. Gọi khi người "
    "dùng hỏi 'anh/chị X làm ở phòng nào', 'ai là quản lý trực tiếp của tôi', 'cho xin email "
    "của ...', 'phòng Kế toán có những ai'. CHỈ trả thông tin liên hệ công việc — KHÔNG có "
    "ngày sinh, CCCD, địa chỉ nhà, tài khoản ngân hàng hay lương; ai hỏi những thứ đó thì "
    "trả lời là phải vào màn Hồ sơ nhân sự và cần quyền riêng. Lương thì kể cả của chính "
    "người hỏi trợ lý cũng không đọc — chính chủ xem ở Trang cá nhân. Kết quả đã lọc theo phạm vi "
    "dữ liệu của người hỏi, nên rỗng có thể nghĩa là ngoài phạm vi chứ không phải không tồn "
    "tại — nói rõ điều đó thay vì khẳng định công ty không có người này."
)


def _clamp(value, default: int, hi: int = MAX_ROWS) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(n, hi))


def _dump(emp: Employee) -> dict:
    """Dựng dòng kết quả THEO danh sách trắng, không `model_dump()` cả hồ sơ.

    Chép cả hồ sơ rồi xóa bớt là khuôn ngược: thêm cột mới ở `model.py` là nó tự
    lọt ra trợ lý AI, im lặng.
    """
    out: dict = {}
    for f in _OUT_FIELDS:
        v = getattr(emp, f, None)
        out[f] = v if isinstance(v, (int, bool)) else (v or "")
    out["extra_phones"] = _extra_phones(getattr(emp, "extra_phones", None))
    return out


def _extra_phones(raw) -> list[dict]:
    """Chỉ chép hai khóa `number` / `label` của từng số phụ — JSON lạ (dữ liệu cũ, nhập tay) không kéo theo khóa khác."""
    out = []
    for e in raw if isinstance(raw, list) else []:
        if isinstance(e, dict) and str(e.get("number") or "").strip():
            out.append({"number": str(e["number"]).strip(), "label": str(e.get("label") or "").strip()})
    return out


def _run(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("employee"):
        return denied("hồ sơ nhân sự (employee.read)")

    limit = _clamp(args.get("limit"), 10)
    q = ctx.db.query(Employee).options(
        #  Nạp kèm 3 quan hệ: `department_name` / `company_name` /
        #  `direct_manager_name` là property đọc qua quan hệ, không nạp trước thì
        #  mỗi dòng thêm 3 truy vấn.
        joinedload(Employee.department),
        joinedload(Employee.company),
        joinedload(Employee.direct_manager),
    )

    kw = str(args.get("query") or "").strip()
    if kw:
        like = f"%{kw}%"
        conds = [Employee.full_name.like(like), Employee.code.like(like), Employee.email.like(like),
                 Employee.phone.like(like), Employee.position.like(like)]
        if _PHONE_LIKE.fullmatch(kw) and sum(c.isdigit() for c in kw) >= 3:
            conds.append(cast(Employee.extra_phones, String).like(like))
        q = q.filter(or_(*conds))

    dept = args.get("department_id")
    if isinstance(dept, (int, float)) and int(dept) >= 0:
        #  `0` là GIÁ TRỊ THẬT (chưa gắn phòng ban), không phải "tất cả" — nên
        #  điều kiện lọc là `>= 0`, và "tất cả" là không truyền tham số.
        q = q.filter(Employee.department_id == int(dept))

    if args.get("active_only") is not False:
        q = q.filter(Employee.is_active.is_(True))

    q = apply_scope(q, Employee, "employee", ctx.user, ctx.profile)
    rows = q.order_by(Employee.full_name).limit(limit).all()

    items = [_dump(r) for r in rows]
    #  Chốt dự phòng — xem chú thích đầu tệp. Hôm nay không che gì vì danh sách
    #  trắng đã loại hết trường nhạy cảm.
    mask_many(items, ctx.profile)
    return {"items": items, "total": len(items),
            "note": "Danh sách đã lọc theo phạm vi dữ liệu của người hỏi."}


EMPLOYEE_LOOKUP_SPEC = ToolSpec(
    name="employee_lookup",
    description=_DESC,
    parameters=_PARAMS,
    handler=_run,
)
