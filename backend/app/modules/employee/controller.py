from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.core.auth import get_perm_profile, hash_password, require
from app.core.base_controller import apply_filters, apply_sort_from_request, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_scoped

from . import (contact_service, department_service, position_service, sensitive,
               service)
from .schema import (EmployeeContactOut, EmployeeContactsIn, EmployeeCreate,
                     EmployeeDetailOut, EmployeeFamiliesIn, EmployeeFamilyOut,
                     EmployeeOut, EmployeeUpdate)

router = APIRouter(prefix="/api/employees", tags=["employee"])


@router.get("")
def list_employees(
    request: Request,
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("employee", "read")),
):
    query = apply_filters(db.query(service.Employee), service.Employee, request, service.FILTERABLE)
    query = service.apply_keyword_search(query, request.query_params.get("search"))
    query = apply_scope(query, service.Employee, "employee", user, get_perm_profile(db, user))
    query = apply_sort_from_request(query, service.Employee, request)
    total, items = service.list_employees(db, query, pg)
    rows = [EmployeeOut.model_validate(i).model_dump() for i in items]
    #  Che nhóm nhạy cảm NGAY Ở ĐÂY, không để tầng giao diện tự ẩn — danh sách
    #  này còn đi ra qua trợ lý AI và qua mọi client gọi thẳng API.
    return success({
        "total": total,
        "items": sensitive.mask_many(rows, get_perm_profile(db, user)),
    })


@router.get("/{eid}")
def get_employee(eid: int, db: Session = Depends(get_db), user=Depends(require("employee", "read"))):
    obj = service.get_employee(db, eid)
    data = EmployeeDetailOut.model_validate(obj).model_dump()
    profile = get_perm_profile(db, user)
    return success(sensitive.mask(data, sensitive.can_read_sensitive(profile, obj.id)))


@router.post("/{eid}/avatar")
def update_employee_avatar(eid: int, file: UploadFile = File(...), db: Session = Depends(get_db),
                           user=Depends(require("employee", "write"))):
    """Đổi ảnh đại diện của nhân sự. Ảnh lưu vào TÀI KHOẢN đăng nhập của nhân sự đó
    (tab_user.avatar) — cùng chỗ với ảnh người dùng tự đổi ở Trang cá nhân, tránh 2 nguồn lệch nhau.
    Nhân sự chưa có tài khoản thì chưa có chỗ lưu ảnh → yêu cầu tạo tài khoản trước."""
    from app.modules.user.model import User
    from app.modules.user.service import set_user_avatar

    emp = service.get_employee(db, eid)
    u = db.query(User).filter(User.employee_id == eid).first()
    if not u:
        raise HTTPException(400, "Nhân sự chưa có tài khoản đăng nhập — hãy tạo tài khoản trước khi đặt ảnh đại diện")
    try:
        url = set_user_avatar(db, u, fileobj=file.file, filename=file.filename or "avatar",
                              content_type=file.content_type or "", actor_id=user.id)
    except Exception as e:
        raise HTTPException(400, f"Lỗi tải ảnh: {str(e)}")
    audit_record(db, user.id, "employee", eid, "update", f"Đổi ảnh đại diện nhân sự {emp.code}")
    return success({"avatar": url}, "Đã cập nhật ảnh đại diện")


@router.post("/{eid}/signature")
def update_employee_signature(eid: int, file: UploadFile = File(...), db: Session = Depends(get_db),
                              user=Depends(require("employee", "write"))):
    """Đặt ảnh chữ ký cho nhân sự (HR làm hộ). Lưu vào TÀI KHOẢN đăng nhập của nhân
    sự (tab_user.signature) — cùng chỗ với chữ ký người dùng tự đặt ở Trang cá nhân.
    Nhân sự chưa có tài khoản thì chưa có chỗ lưu → yêu cầu tạo tài khoản trước."""
    import uuid
    from app.core.storage import env_prefix, safe_name, upload_fileobj
    from app.modules.user.model import User

    emp = service.get_employee(db, eid)
    u = db.query(User).filter(User.employee_id == eid).first()
    if not u:
        raise HTTPException(400, "Nhân sự chưa có tài khoản đăng nhập — hãy tạo tài khoản trước khi đặt chữ ký")
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(400, "Chữ ký phải là file ảnh (PNG, JPG…).")
    try:
        key = f"{env_prefix()}/signature/{u.id}/{uuid.uuid4().hex[:12]}-{safe_name(file.filename or 'signature')}"
        url = upload_fileobj(file.file, key, file.content_type or "")
        u.signature = url
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Lỗi tải ảnh chữ ký: {str(e)}")
    audit_record(db, user.id, "employee", eid, "update", f"Cập nhật chữ ký nhân sự {emp.code}")
    return success({"signature": url}, "Đã cập nhật chữ ký")


@router.delete("/{eid}/signature")
def delete_employee_signature(eid: int, db: Session = Depends(get_db),
                              user=Depends(require("employee", "write"))):
    """Gỡ chữ ký của nhân sự. Chỉ xóa liên kết (tab_user.signature=""), file trên
    storage giữ nguyên để không phá phiếu đã in."""
    from app.modules.user.model import User

    emp = service.get_employee(db, eid)
    u = db.query(User).filter(User.employee_id == eid).first()
    if u:
        u.signature = ""
        db.commit()
    audit_record(db, user.id, "employee", eid, "update", f"Gỡ chữ ký nhân sự {emp.code}")
    return success({"signature": ""}, "Đã gỡ chữ ký")


def _status_code(raw: str) -> str:
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
    for code, label in EMPLOYEE_STATUS.labels.items():
        if norm(label) == can:
            return code
    return ""


class SetPasswordIn(BaseModel):
    password: str


def _block_set_password_out_of_scope(db: Session, eid: int, actor) -> None:
    """Nhân sự #eid phải nằm trong phạm vi GHI của người đang thao tác.

    Đặt lại mật khẩu của người khác **không phải sửa một ô hồ sơ** — nó là trao
    quyền đăng nhập bằng danh nghĩa người đó. Cửa song sinh
    `POST /users/{id}/reset-password` đã hiểu vậy và gọi `_block_out_of_scope`
    (`user/controller.py:75`); cửa này thì trước 05/09/2026 chỉ có
    `require("employee", "write")` — tức là kiểm **có quyền hay không**, không
    kiểm **trên ai**. Hệ quả: `employee.write` phạm vi *own*, phạm vi hẹp nhất
    tồn tại, vẫn đặt được mật khẩu tài khoản quản trị rồi đăng nhập bằng nó.

    Đường đó đi vòng qua cả CR-158 lẫn ba chốt của CR-167: chúng canh việc bạn
    nâng quyền cho **chính mình**, còn đây là mượn tài khoản người khác — không
    có dòng phân quyền nào thay đổi để mà chặn.

    ⚠️ Còn một tầng NỮA chưa gắn, và cố ý chưa gắn ở đây: người có
    `employee.write` phạm vi *tất cả* (hành chính) vẫn đặt được mật khẩu của
    người mang quyền cao hơn mình. Luật L2 của `core/privilege_escalation.py`
    diễn đạt đúng thứ cần chặn, nhưng gắn vào đây mà không gắn vào cửa song
    sinh thì hai cửa cùng làm một việc lại chặt lỏng khác nhau — và nó cắt luôn
    việc hành chính đặt lại mật khẩu hộ người phòng khác, một việc có thật hằng
    ngày. Đó là câu hỏi CHÍNH SÁCH cho cả hai cửa, không phải bản vá của riêng
    cửa này.
    """
    if get_scoped(db, service.Employee, "employee", eid, actor,
                  get_perm_profile(db, actor), "write") is None:
        raise HTTPException(404, "Không tìm thấy nhân sự")


@router.post("/{eid}/set-password")
def set_password(eid: int, data: SetPasswordIn, db: Session = Depends(get_db),
                 user=Depends(require("employee", "write"))):
    """Đặt mật khẩu tài khoản của nhân sự. Nếu nhân sự CHƯA có tài khoản đăng nhập
    thì TỰ TẠO tài khoản (email + vai trò của nhân sự) rồi đặt luôn mật khẩu này."""
    from app.modules.user.model import User
    if not (data.password or "").strip() or len(data.password) < 4:
        raise HTTPException(400, "Mật khẩu tối thiểu 4 ký tự")
    _block_set_password_out_of_scope(db, eid, user)
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
    return success(_masked(db, obj, user), "Đã tạo nhân viên", 201)


@router.patch("/{eid}")
def update_employee(
    eid: int, data: EmployeeUpdate, db: Session = Depends(get_db),
    user=Depends(require("employee", "write")),
):
    #  ⚠️ Đổi ô «Phòng ban» của hồ sơ CŨNG là đổi phạm vi dữ liệu người đó nhìn
    #  thấy — y hệt thêm một phòng kiêm nhiệm. Trước CR-167 cửa này không có chốt
    #  nào: vai trò `employee.write` phạm vi *own* là có thật, nên tự đổi phòng
    #  của mình sang phòng khác là đọc được dữ liệu phòng đó, không cần đụng tới
    #  màn Phân quyền. Hai cửa cùng đổi một thứ thì phải cùng một luật.
    if data.department_id is not None:
        profile = get_perm_profile(db, user)
        department_service.block_edit_own_department(db, eid, user)
        department_service.block_out_of_scope_departments(db, [data.department_id], user, profile)

    obj = service.update_employee(db, eid, data, user.id)
    return success(_masked(db, obj, user), "Đã cập nhật")


def _masked(db: Session, obj, user) -> dict:
    """Bản `EmployeeOut` đã che nhóm nhạy cảm cho đúng người đang gọi.

    ⚠️ Cửa GHI cũng phải che. `employee.write` mà không có `employee_sensitive.read`
    là một tổ hợp có thật (hành chính sửa số điện thoại); không che thì họ PATCH
    một ô vô hại rồi đọc số tài khoản ngân hàng trong chính câu trả lời — một
    đường vòng không cần biết gõ gì đặc biệt.
    """
    data = EmployeeOut.model_validate(obj).model_dump()
    allowed = sensitive.can_read_sensitive(get_perm_profile(db, user), obj.id)
    return sensitive.mask(data, allowed)


def _employee_in_scope(db, eid: int, user, profile, action: str = "read"):
    """Hồ sơ nhân sự NẰM TRONG phạm vi của người đang thao tác, không thì 404.

    ⚠️ `GET /api/employees/{eid}` cũ dùng `service.get_employee` — **không xét
    phạm vi**. Hai cửa dưới đây là cửa GHI (đổi phòng ban = đổi tầm nhìn dữ
    liệu) nên phải xét: lọc ở danh sách bao nhiêu cũng vô nghĩa nếu gõ thẳng id
    lên URL là sửa được hồ sơ ngoài phạm vi.

    404 chứ không 403, cùng lý lẽ với `document.ensure_can`: nói "có hồ sơ này
    nhưng anh không được xem" thì chính câu đó đã lộ thứ cần giấu.
    """
    from app.core.scoping import get_scoped

    from .model import Employee

    obj = get_scoped(db, Employee, "employee", eid, user, profile, action)
    if obj is None:
        raise HTTPException(404, "Không tìm thấy nhân viên")
    return obj


class ExtraDepartmentsIn(BaseModel):
    """Đặt lại danh sách phòng KIÊM NHIỆM. Phòng chính KHÔNG đi qua đây."""

    extra_department_ids: list[int] = []


@router.get("/{eid}/departments")
def list_employee_departments(
    eid: int, db: Session = Depends(get_db), user=Depends(require("employee", "read")),
):
    """Phòng chính + phòng kiêm nhiệm, TÁCH BẠCH hai khóa.

    Không gộp thành một danh sách rồi quy ước «phần tử đầu là phòng chính»: đó
    là một luật ngầm mà người dùng không có cách nào biết, và nó làm ô «Phòng
    ban» của hồ sơ thành thừa.
    """
    emp = _employee_in_scope(db, eid, user, get_perm_profile(db, user))
    return success({"primary_department_id": emp.department_id or 0,
                    "extra_department_ids": department_service.extra_departments_of(db, emp.id)})


@router.put("/{eid}/departments")
def set_employee_departments(
    eid: int, data: ExtraDepartmentsIn, db: Session = Depends(get_db),
    user=Depends(require("employee", "write")),
):
    """KIÊM NHIỆM — đặt lại các phòng phụ trách THÊM. Phòng chính giữ nguyên.

    Phòng chính đổi ở ô «Phòng ban» của hồ sơ (`PATCH /employees/{id}`) — hai
    thao tác khác nhau thì hai cửa khác nhau. Cả hai cửa đều qua đúng ba chốt
    chống vượt quyền dưới đây, vì cả hai đều đổi phạm vi dữ liệu người đó nhìn
    thấy. Lý lẽ đầy đủ ở `employee/department_service.py`.
    """
    profile = get_perm_profile(db, user)
    emp = _employee_in_scope(db, eid, user, profile, "write")

    department_service.block_edit_own_department(db, emp.id, user)
    department_service.block_out_of_scope_departments(db, data.extra_department_ids, user, profile)
    ids = department_service.set_extra_departments(db, emp, data.extra_department_ids, user.id)
    db.commit()

    audit_record(db, user.id, "employee", emp.id, "update",
                 f"Đặt lại phòng kiêm nhiệm: {ids}")
    return success({"primary_department_id": emp.department_id or 0,
                    "extra_department_ids": ids}, "Đã cập nhật phòng kiêm nhiệm")


# ── Hai bảng con của hồ sơ ──────────────────────────────────────────────────
#  Chốt của chúng là chốt của HỒ SƠ CHA — hai lớp, cả hai đều phải qua:
#    1. `_employee_in_scope(...)` — hồ sơ này có nằm trong phạm vi dữ liệu của
#       người gọi không (nếu không: 404, không phải 403);
#    2. `employee_sensitive.read` — có được xem NỘI DUNG không.
#  Hai bảng cố ý KHÔNG có khóa phân quyền riêng; lý lẽ ở `sensitive.py`.

def _block_sensitive(db: Session, user, employee_id: int) -> None:
    """Chặn khi không được xem nhóm nhạy cảm. 403 chứ KHÔNG phải 404.

    Khác `_employee_in_scope`: ở đó giấu cả sự tồn tại của hồ sơ, còn ở đây người
    gọi ĐÃ biết hồ sơ tồn tại (họ vừa mở nó). Trả 404 lúc này chỉ làm giao diện
    hiểu nhầm là hồ sơ vừa bị xóa và đá người dùng về danh sách.
    """
    if not sensitive.can_read_sensitive(get_perm_profile(db, user), employee_id):
        raise HTTPException(403, "Bạn không có quyền xem thông tin nhạy cảm của hồ sơ nhân sự")


@router.get("/{eid}/contacts")
def list_employee_contacts(
    eid: int, db: Session = Depends(get_db), user=Depends(require("employee", "read")),
):
    """Người báo tin trong trường hợp cần thiết."""
    emp = _employee_in_scope(db, eid, user, get_perm_profile(db, user))
    _block_sensitive(db, user, emp.id)
    rows = contact_service.list_contacts(db, emp.id)
    return success([EmployeeContactOut.model_validate(r).model_dump() for r in rows])


@router.put("/{eid}/contacts")
def set_employee_contacts(
    eid: int, data: EmployeeContactsIn, db: Session = Depends(get_db),
    user=Depends(require("employee", "write")),
):
    profile = get_perm_profile(db, user)
    emp = _employee_in_scope(db, eid, user, profile, "write")
    _block_sensitive(db, user, emp.id)
    rows = contact_service.set_contacts(db, emp.id, data.items, user.id)
    db.commit()
    audit_record(db, user.id, "employee", emp.id, "update",
                 f"Cập nhật người báo tin ({len(rows)} người)")
    return success([EmployeeContactOut.model_validate(r).model_dump() for r in rows],
                   "Đã cập nhật người báo tin")


@router.get("/{eid}/families")
def list_employee_families(
    eid: int, db: Session = Depends(get_db), user=Depends(require("employee", "read")),
):
    """Thành viên hộ gia đình — phục vụ kê khai BHXH."""
    emp = _employee_in_scope(db, eid, user, get_perm_profile(db, user))
    _block_sensitive(db, user, emp.id)
    rows = contact_service.list_families(db, emp.id)
    return success([EmployeeFamilyOut.model_validate(r).model_dump() for r in rows])


@router.put("/{eid}/families")
def set_employee_families(
    eid: int, data: EmployeeFamiliesIn, db: Session = Depends(get_db),
    user=Depends(require("employee", "write")),
):
    profile = get_perm_profile(db, user)
    emp = _employee_in_scope(db, eid, user, profile, "write")
    _block_sensitive(db, user, emp.id)
    rows = contact_service.set_families(db, emp.id, data.items, user.id)
    db.commit()
    audit_record(db, user.id, "employee", emp.id, "update",
                 f"Cập nhật thành viên hộ gia đình ({len(rows)} người)")
    return success([EmployeeFamilyOut.model_validate(r).model_dump() for r in rows],
                   "Đã cập nhật thành viên hộ gia đình")


#  Hai ô ảnh CCCD chỉ đặt được qua cửa này — `EmployeeUpdate` cố ý không khai
#  chúng. Nhận chuỗi đường dẫn từ client là để người ta trỏ ô ảnh vào một URL
#  bất kỳ, rồi màn hồ sơ và bản in sẽ tải nó về hộ.
_ID_IMAGE_SIDES = {"front": "id_front_image", "back": "id_back_image"}


@router.post("/{eid}/id-image/{side}")
def upload_id_image(
    eid: int, side: str, file: UploadFile = File(...), db: Session = Depends(get_db),
    user=Depends(require("employee", "write")),
):
    """Tải ảnh CCCD mặt trước / mặt sau. `side` = `front` | `back`."""
    import uuid

    from app.core.storage import env_prefix, safe_name, upload_fileobj

    col = _ID_IMAGE_SIDES.get((side or "").lower())
    if not col:
        raise HTTPException(400, "Mặt ảnh chỉ nhận 'front' (mặt trước) hoặc 'back' (mặt sau)")
    profile = get_perm_profile(db, user)
    emp = _employee_in_scope(db, eid, user, profile, "write")
    #  ⚠️ Ảnh CCCD thuộc nhóm nhạy cảm nên GHI cũng phải có khóa đó, không chỉ
    #  ĐỌC: ghi đè được ảnh CCCD của người khác là thay giấy tờ tùy thân của họ
    #  trong hồ sơ mà người đọc hồ sơ không có cách nào biết.
    _block_sensitive(db, user, emp.id)
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(400, "Ảnh CCCD phải là file ảnh (PNG, JPG…).")
    try:
        key = (f"{env_prefix()}/employee-id/{emp.id}/{side}-"
               f"{uuid.uuid4().hex[:12]}-{safe_name(file.filename or 'cccd')}")
        url = upload_fileobj(file.file, key, file.content_type or "")
        setattr(emp, col, url)
        emp.updated_by = user.id
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Lỗi tải ảnh CCCD: {str(e)}")
    audit_record(db, user.id, "employee", emp.id, "update",
                 f"Cập nhật ảnh CCCD mặt {'trước' if side == 'front' else 'sau'}")
    return success({col: url}, "Đã cập nhật ảnh CCCD")


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
    query = service.apply_keyword_search(query, request.query_params.get("search"))
    # Đ-13b: xuất CSV cũng phải bó theo phạm vi dữ liệu như màn danh sách — trước đây
    # thiếu dòng này nên người phạm vi hẹp bấm Xuất là kéo được TOÀN BỘ nhân sự.
    query = apply_scope(query, Employee, "employee", user, get_perm_profile(db, user))
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


@router.get("/export/xlsx")
def export_employees_xlsx(
    ids: str | None = Query(None),
    request: Request = None,
    db: Session = Depends(get_db),
    user=Depends(require("employee", "export")),
):
    """Xuất Nhân sự ra .xlsx theo đúng bộ lọc đang áp + phạm vi dữ liệu (Đ-13b).

    Endpoint MỚI nên gác thẳng bằng action `export` (QĐ-I4). Bản CSV cũ tạm giữ gác
    `read` để không gãy màn cũ; sẽ chuẩn hoá về `export` ở Pha C."""
    from app.core.export_xlsx import Col, check_row_limit, parse_ids, xlsx_response
    from .model import Employee

    query = apply_filters(db.query(Employee), Employee, request, service.FILTERABLE)
    query = apply_scope(query, Employee, "employee", user, get_perm_profile(db, user))
    id_list = parse_ids(ids)
    if id_list:
        query = query.filter(Employee.id.in_(id_list))
    items = query.order_by(Employee.id.desc()).all()
    check_row_limit(len(items))

    cols = [
        Col("code", "Mã NV", width=16),
        Col("full_name", "Họ tên", width=28),
        Col("email", "Email", width=24),
        Col("phone", "Số điện thoại", width=16),
        Col("department_name", "Phòng ban", width=22),
        Col("company_name", "Công ty", width=22),
        Col("position", "Vị trí", width=18),
        Col("status_label", "Trạng thái NS", width=16),
    ]
    rows = [{c.key: getattr(it, c.key, "") for c in cols} for it in items]
    return xlsx_response("nhan-su", cols, rows, "Nhan su")

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
    # bao-CR-368: nhập CSV cũng là một cửa tạo nhân sự — phải chặn trùng email y như màn nhập tay,
    # nếu không thì vá một cửa vẫn còn cửa kia. Dòng trùng bị BỎ QUA chứ không huỷ cả tệp, rồi báo
    # số lượng ở câu kết để người nhập biết mà sửa lại.
    skipped_duplicate_email: list[str] = []
    for line_no, row in enumerate(reader, start=2):   # 2 = dòng đầu tiên sau hàng tiêu đề
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
        status = _status_code(status_raw) or ("official" if not status_raw else "")
        if not status:
            valid = " / ".join(EMPLOYEE_STATUS.labels.values())
            raise HTTPException(
                400, f"Dòng {line_no}: trạng thái nhân sự {status_raw!r} không hợp lệ. "
                     f"Giá trị nhận: {valid}.")


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

        #  Chức vụ trong tệp là CHỮ; khớp được vào danh mục thì gắn luôn khóa
        #  (duoc-CR-320). Không khớp → giữ chữ, `position_id = 0`: tệp CSV cũ
        #  vẫn nhập được như trước, chỉ là hồ sơ đó chưa nối vào danh mục.
        matched_position = position_service.resolve_by_name(db, position)
        position_id = matched_position.id if matched_position else 0
        if matched_position:
            position = matched_position.name      # chuẩn hóa hoa thường theo danh mục

        existing = db.query(Employee).filter(Employee.code == code).first() if code else None
        if email and action not in ["xóa", "delete"]:
            from sqlalchemy import func as sa_func
            duplicate = (db.query(Employee)
                         .filter(sa_func.lower(Employee.email) == email.lower(),
                                 Employee.id != (existing.id if existing else 0))
                         .first())
            if duplicate:
                skipped_duplicate_email.append(
                    f"{code or full_name} (email đã thuộc {duplicate.code})")
                continue

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
                existing.position_id = position_id
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
                department_id=department_id, position=position,
                position_id=position_id, status=status,
                is_active=is_active, created_by=user.id, updated_by=user.id
            )
            db.add(new_obj)
            db.flush()
            created += 1
            
    db.commit()
    msg = f"Nhập file thành công. Thêm mới {created}, cập nhật {updated}, ẩn {deleted}."
    if skipped_duplicate_email:
        msg += (f" Bỏ qua {len(skipped_duplicate_email)} dòng trùng email: "
                + ", ".join(skipped_duplicate_email[:5])
                + ("…" if len(skipped_duplicate_email) > 5 else ""))
    return success(None, msg)
