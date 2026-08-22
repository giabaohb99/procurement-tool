import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.core.auth import get_perm_profile, hash_password, require
from app.core.base_controller import apply_filters, apply_sort_from_request, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope

from . import service
from .schema import EmployeeCreate, EmployeeDetailOut, EmployeeOut, EmployeeUpdate

router = APIRouter(prefix="/api/employees", tags=["employee"])


@router.get("")
def list_employees(
    request: Request,
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("employee", "read")),
):
    query = apply_filters(db.query(service.Employee), service.Employee, request, service.FILTERABLE)
    query = apply_scope(query, service.Employee, "employee", user, get_perm_profile(db, user))
    query = apply_sort_from_request(query, service.Employee, request)
    total, items = service.list_employees(db, query, pg)
    return success({
        "total": total,
        "items": [EmployeeOut.model_validate(i).model_dump() for i in items],
    })


@router.get("/{eid}")
def get_employee(eid: int, db: Session = Depends(get_db), user=Depends(require("employee", "read"))):
    return success(EmployeeDetailOut.model_validate(service.get_employee(db, eid)).model_dump())


@router.post("/{eid}/avatar")
def update_employee_avatar(eid: int, file: UploadFile = File(...), db: Session = Depends(get_db),
                           user=Depends(require("employee", "write"))):
    """Đổi ảnh đại diện của nhân sự. Ảnh lưu vào TÀI KHOẢN đăng nhập của nhân sự đó
    (tab_user.avatar) — cùng chỗ với ảnh người dùng tự đổi ở Trang cá nhân, tránh 2 nguồn lệch nhau.
    Nhân sự chưa có tài khoản thì chưa có chỗ lưu ảnh → yêu cầu tạo tài khoản trước."""
    from app.core.storage import env_prefix, safe_name, upload_fileobj
    from app.modules.user.model import User

    emp = service.get_employee(db, eid)
    u = db.query(User).filter(User.employee_id == eid).first()
    if not u:
        raise HTTPException(400, "Nhân sự chưa có tài khoản đăng nhập — hãy tạo tài khoản trước khi đặt ảnh đại diện")
    try:
        key = f"{env_prefix()}/avatar/{u.id}/{uuid.uuid4().hex[:12]}-{safe_name(file.filename or 'avatar')}"
        url = upload_fileobj(file.file, key, file.content_type or "")
    except Exception as e:
        raise HTTPException(400, f"Lỗi tải ảnh: {str(e)}")
    u.avatar = url
    db.commit()
    audit_record(db, user.id, "employee", eid, "update", f"Đổi ảnh đại diện nhân sự {emp.code}")
    return success({"avatar": url}, "Đã cập nhật ảnh đại diện")


def _ma_trang_thai(raw: str) -> str:
    """Đổi ô "Trạng thái NS" trong tệp CSV thành MÃ (B-03).

    Đây là NGOẠI LỆ có chủ đích của luật "không tự dịch nhãn thành mã": tệp CSV do người
    dùng gõ tay trong Excel, không phải giao diện mình viết ra — bắt họ gõ `maternity_leave`
    là vô lý, mà chặn 422 giữa chừng thì hỏng cả lần nhập. Ở tầng API thì vẫn chặn thẳng.

    Nhận cả ba dạng: mã sẵn (`official`), nhãn đúng (`Nghỉ thai sản`) và nhãn gõ lệch dấu /
    lệch hoa thường (`nghi thai san`). Không nhận ra thì trả rỗng để nơi gọi tự quyết —
    KHÔNG đoán bừa thành "Chính thức", vì đoán sai ở đây là ghi đè trạng thái thật của
    một con người.
    """
    import unicodedata

    from app.core.status_codes import EMPLOYEE_STATUS

    v = (raw or "").strip()
    if not v:
        return ""
    if v in EMPLOYEE_STATUS.values:
        return v

    def norm(s: str) -> str:
        s = unicodedata.normalize("NFD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        return " ".join(s.replace("đ", "d").replace("Đ", "D").lower().split())

    can = norm(v)
    for ma, nhan in EMPLOYEE_STATUS.labels.items():
        if norm(nhan) == can:
            return ma
    return ""


class SetPasswordIn(BaseModel):
    password: str


@router.post("/{eid}/set-password")
def set_password(eid: int, data: SetPasswordIn, db: Session = Depends(get_db),
                 user=Depends(require("employee", "write"))):
    """Đặt mật khẩu tài khoản của nhân sự. Nếu nhân sự CHƯA có tài khoản đăng nhập
    thì TỰ TẠO tài khoản (email + vai trò của nhân sự) rồi đặt luôn mật khẩu này."""
    from app.modules.user.model import User
    if not (data.password or "").strip() or len(data.password) < 4:
        raise HTTPException(400, "Mật khẩu tối thiểu 4 ký tự")
    u = db.query(User).filter(User.employee_id == eid).first()
    if u:
        u.password_hash = hash_password(data.password)
        db.commit()
        return success(None, "Đã đặt lại mật khẩu")

    # Chưa có tài khoản → tự tạo từ nhân sự rồi đặt mật khẩu
    emp = db.get(service.Employee, eid)
    if not emp:
        raise HTTPException(404, "Không tìm thấy nhân sự")
    if not (emp.email or "").strip():
        raise HTTPException(400, "Nhân sự chưa có email — hãy nhập email trước để tạo tài khoản đăng nhập")
    if db.query(User).filter(User.email == emp.email).first():
        raise HTTPException(400, f"Email {emp.email} đã được dùng cho tài khoản khác")
    from app.modules.user import service as user_service
    from app.modules.user.schema import UserProvision
    # CR-022: quyền KHÔNG lấy theo ô "Vai trò" của hồ sơ nhân sự (ô đó nay là "Vị trí / Chức vụ",
    # chỉ là chữ). CR-037: nhưng để trắng vai trò thì người mới đăng nhập vào không thấy gì —
    # provision_user tự gán vai trò mặc định 'Nhân sự'; quyền cao hơn admin vẫn gán tay.
    user_service.provision_user(
        db, UserProvision(employee_id=eid, email=emp.email, password=data.password, role_ids=[]), user.id)
    return success(None, "Đã tạo tài khoản đăng nhập (vai trò mặc định: Nhân sự). "
                         "Vào Phân quyền tài khoản để cấp thêm quyền.")


@router.post("")
def create_employee(
    data: EmployeeCreate, db: Session = Depends(get_db),
    user=Depends(require("employee", "create")),
):
    obj = service.create_employee(db, data, user.id)
    return success(EmployeeOut.model_validate(obj).model_dump(), "Đã tạo nhân viên", 201)


@router.patch("/{eid}")
def update_employee(
    eid: int, data: EmployeeUpdate, db: Session = Depends(get_db),
    user=Depends(require("employee", "write")),
):
    obj = service.update_employee(db, eid, data, user.id)
    return success(EmployeeOut.model_validate(obj).model_dump(), "Đã cập nhật")


@router.delete("/{eid}")
def delete_employee(
    eid: int, db: Session = Depends(get_db), user=Depends(require("employee", "delete"))
):
    locked = service.delete_employee(db, eid, user.id)
    msg = "Đã xóa" if not locked else f"Đã xóa. Đã khoá {locked} tài khoản đăng nhập của nhân sự này."
    return success(None, msg)

@router.get("/export/csv")
def export_employees_csv(
    ids: str | None = Query(None),
    request: Request = None,
    db: Session = Depends(get_db),
    user=Depends(require("employee", "read")),
):
    from app.core.csv_utils import export_csv_response
    from .model import Employee
    
    query = apply_filters(db.query(Employee), Employee, request, service.FILTERABLE)
    if ids:
        id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
        if id_list:
            query = query.filter(Employee.id.in_(id_list))
            
    items = query.order_by(Employee.id.desc()).all()
    headers_map = {
        "code": "Mã NV",
        "full_name": "Họ tên",
        "email": "Email",
        "phone": "Số điện thoại",
        "department_name": "Phòng ban",
        "position": "Vị trí",          # CR-022: chức danh hiển thị, KHÔNG phải phân quyền
        # B-03: xuất NHÃN chứ không xuất mã. Cột này người dùng mở bằng Excel để đọc và
        # để sửa rồi nhập ngược lại — đổ `official` ra đó là biến một tệp đang đọc được
        # thành tệp phải tra cứu. Đường nhập vẫn hiểu cả nhãn lẫn mã (xem `_ma_trang_thai`).
        "status_label": "Trạng thái NS",
    }
    return export_csv_response(items, headers_map, "employees")

@router.post("/import/csv")
def import_employees_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require("employee", "write")),
):
    import csv
    from io import StringIO
    from fastapi import HTTPException
    from app.core.utils import generate_code
    from .model import Employee
    
    try:
        content = file.file.read().decode("utf-8-sig").replace("\r\n", "\n")
        if content.lower().startswith("sep="):
            content = content.split("\n", 1)[-1]
    except UnicodeDecodeError:
        raise HTTPException(400, "Lỗi định dạng file. Vui lòng lưu file CSV với encoding UTF-8.")
        
    reader = csv.DictReader(StringIO(content))
    if not reader.fieldnames:
        raise HTTPException(400, "File CSV trống")
        
    from app.core.status_codes import EMPLOYEE_STATUS

    created, updated, deleted = 0, 0, 0
    for dong, row in enumerate(reader, start=2):   # 2 = dòng đầu tiên sau hàng tiêu đề
        action = (row.get("Hành động") or "").strip().lower()
        is_active = action not in ["xóa", "delete", "ngừng"]
        
        code = (row.get("Mã NV") or row.get("ID") or "").strip()
        full_name = (row.get("Họ tên") or "").strip()
        email = (row.get("Email") or "").strip()
        phone = (row.get("Số điện thoại") or row.get("SĐT") or "").strip()
        department_name = (row.get("Phòng ban") or "").strip()
        # CR-022: cột "Vai trò" cũ nay là "Vị trí" (chức danh). Vẫn đọc tên cột cũ để file CSV
        # xuất trước đây import lại được, nhưng đổ vào `position` — KHÔNG cấp quyền cho tài khoản.
        position = (row.get("Vị trí") or row.get("Chức vụ") or row.get("Vai trò") or "").strip()
        # B-03: ô này chứa NHÃN tiếng Việt (đúng cái bản xuất CSV đổ ra) hoặc mã. Bỏ trống
        # thì mặc định Chính thức như trước. Gõ sai thì dừng cả lần nhập và nói rõ dòng nào
        # — im lặng cho qua là một hồ sơ nhân sự mang trạng thái không ai chọn được nữa.
        status_raw = (row.get("Trạng thái NS") or row.get("Trạng thái") or "").strip()
        status = _ma_trang_thai(status_raw) or ("official" if not status_raw else "")
        if not status:
            hop_le = " / ".join(EMPLOYEE_STATUS.labels.values())
            raise HTTPException(
                400, f"Dòng {dong}: trạng thái nhân sự {status_raw!r} không hợp lệ. "
                     f"Giá trị nhận: {hop_le}.")


        if not code and not full_name:
            continue
            
        # Try mapping department_name to department_id
        department_id = 0
        if department_name:
            from .model import Employee
            from app.modules.department.model import Department
            dept = db.query(Department).filter(Department.name.like(f"%{department_name}%")).first()
            if dept:
                department_id = dept.id

        existing = db.query(Employee).filter(Employee.code == code).first() if code else None
        if existing:
            if action in ["xóa", "delete"]:
                service.detach_users(db, existing.id, user.id)   # CR-023: khoá tài khoản kèm theo
                db.delete(existing)
                deleted += 1
            else:
                if full_name: existing.full_name = full_name
                existing.email = email
                existing.phone = phone
                if department_id: existing.department_id = department_id
                existing.position = position
                existing.status = status
                existing.is_active = is_active
                existing.updated_by = user.id
                if not is_active: deleted += 1
                else: updated += 1
        else:
            if not is_active or not full_name: continue
            if not code: code = generate_code(db, Employee, "NSU")
            new_obj = Employee(
                code=code, full_name=full_name, email=email, phone=phone,
                department_id=department_id, position=position, status=status,
                is_active=is_active, created_by=user.id, updated_by=user.id
            )
            db.add(new_obj)
            db.flush()
            created += 1
            
    db.commit()
    return success(None, f"Nhập file thành công. Thêm mới {created}, cập nhật {updated}, ẩn {deleted}.")
