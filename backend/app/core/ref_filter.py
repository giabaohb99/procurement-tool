"""Lọc danh sách theo Ô THAM CHIẾU (phòng ban / nhân sự) bằng ID — CR-088.

Nối tiếp CR-086/087. Chứng từ đã neo `department_id` / `nspt_id` / `head_of_dept_id`, nhưng
bộ lọc trên các màn vẫn gửi CHUỖI TÊN và `apply_filters` so bằng `LIKE %tên%` — mang y nguyên
căn bệnh vừa chữa, thậm chí nặng hơn một bậc:

```
đổi tên phòng          →  bộ lọc cũ trượt sạch, danh sách rỗng mà không báo gì
hai người trùng tên    →  lọc một người ra đơn của cả hai
LIKE là khớp CHUỖI CON →  lọc "Hân" ra luôn mọi người có chữ "Hân" trong tên
```

Thời kỳ quá độ: **id là nguồn sự thật, dòng chưa điền lùi được id (`= 0`) mới so TÊN** — cùng
khuôn `scoping._dept_match` / `_emp_match`, và tên ở đây so BẰNG chứ không `LIKE`. Bỏ nhánh
tên ở N-008 thì hàm này rút lại còn đúng một điều kiện.

Vì sao phải có nhánh lùi: dev đang có 77/126 ĐMH `nspt_id = 0` (nhập lịch sử bằng biệt danh).
Lọc thuần theo id là mấy dòng đó biến mất khỏi màn hình — người dùng không hiểu vì sao.
"""
from sqlalchemy import and_, or_

# {cột id: cột tên} — ô tham chiếu có ĐỦ CẢ HAI cột trên cùng một bảng.
# Bảng chỉ có cột id (vd `tab_document.department_id`) không nằm ở đây và cũng không cần:
# nó lọc thẳng bằng `apply_filters` như một khóa ngoại bình thường.
REF_PAIRS = {
    "department_id": "department",
    "nspt_id": "nspt",
    "head_of_dept_id": "head_of_dept",
    "requester_id": "requester",
}

# Cột id nào tra tên ở bảng nào. Cả hệ chỉ có hai loại tham chiếu.
_EMP_REFS = ("nspt_id", "head_of_dept_id", "requester_id")


def owns(model, col_id: str) -> bool:
    """`apply_filters` có phải nhường cột này cho `apply_ref_filters` không?

    Chỉ nhường khi model có ĐỦ cặp id + tên. Thiếu cột tên nghĩa là bảng đó neo bằng id ngay
    từ đầu, không có nợ nào để trả — cứ để `apply_filters` so khớp chính xác như cũ.
    """
    twin = REF_PAIRS.get(col_id)
    return bool(twin) and getattr(model, col_id, None) is not None \
        and getattr(model, twin, None) is not None


def ref_name(db, col_id: str, rid: int) -> str:
    """Tên hiện hành của bản ghi được trỏ tới — chỉ dùng để dựng nhánh lùi cho dòng id = 0."""
    if col_id in _EMP_REFS:
        from app.modules.employee.model import Employee
        emp = db.get(Employee, rid)
        return (emp.full_name or "") if emp else ""
    from app.modules.department.model import Department
    dep = db.get(Department, rid)
    return (dep.name or "") if dep else ""


def ref_cond(db, model, col_id: str, rid: int):
    """Điều kiện "ô tham chiếu này trỏ tới bản ghi `rid`". `rid` không hợp lệ -> None."""
    if not rid or not owns(model, col_id):
        return None
    cond = getattr(model, col_id) == rid
    name = ref_name(db, col_id, rid)
    if not name:
        return cond
    return or_(cond, and_(getattr(model, col_id) == 0,
                          getattr(model, REF_PAIRS[col_id]) == name))


def apply_ref_filters(query, model, request, db):
    """Áp mọi param trần dạng `<ô tham chiếu>_id=<id>` có trên model. Nối bằng AND."""
    for col_id in REF_PAIRS:
        raw = (request.query_params.get(col_id) or "").strip()
        if not raw.isdigit():
            continue
        cond = ref_cond(db, model, col_id, int(raw))
        if cond is not None:
            query = query.filter(cond)
    return query
