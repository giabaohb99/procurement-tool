"""API QUẢN TRỊ HỘP THƯ GỬI (26/08/2026).

Không dùng `make_crud_router` vì hai chỗ lệch hẳn khỏi CRUD chung: mật khẩu ứng
dụng **không bao giờ trả ngược** (chỉ trả cờ đã cấu hình hay chưa), và danh sách
người được dùng là một bảng con đặt lại theo lô.

Gác bằng entity `mailbox` — quyền cấp cho ai gửi được thư danh nghĩa cả phòng
ban là việc của quản trị, không đi ké quyền của phân hệ Văn bản.
"""
import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_perm_profile

from . import mailbox_service
from .mailbox_model import Mailbox

router = APIRouter(prefix="/api/mailboxes", tags=["mailbox"])

#  Kiểm địa chỉ bằng regex chứ không dùng `EmailStr`: cả hệ chưa cài
#  `email-validator`, mà thêm một phụ thuộc cho đúng một ô nhập là không đáng.
#  Đây là ô của quản trị, gõ sai thì SMTP báo ngay ở lần gửi thử.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class MailboxIn(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=255)
    display_name: str = ""

    @field_validator("email")
    @classmethod
    def _dung_dinh_dang(cls, value: str) -> str:
        value = (value or "").strip().lower()
        if not _EMAIL_RE.match(value):
            raise ValueError("Địa chỉ email không hợp lệ")
        return value
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_user: str = ""
    #  Mật khẩu ứng dụng. Rỗng = GIỮ NGUYÊN cái đang có, không phải xóa —
    #  xem `mailbox_service.dat_mat_khau`.
    smtp_password: str = ""
    use_tls: bool = True
    company_id: int | None = None
    note: str = ""
    is_active: bool = True
    employee_ids: list[int] = []


def _ra_json(db: Session, row: Mailbox) -> dict:
    return {
        "id": row.id,
        "code": row.code,
        "name": row.name,
        "email": row.email,
        "display_name": row.display_name,
        "smtp_host": row.smtp_host,
        "smtp_port": row.smtp_port,
        "smtp_user": row.smtp_user,
        #  KHÔNG trả mật khẩu, chỉ trả "đã có hay chưa" — cùng quy ước với
        #  `smtp_password` ở màn Cấu hình hệ thống.
        "has_password": bool(row.smtp_password_enc),
        "ready": mailbox_service.san_sang_gui(row),
        "use_tls": row.use_tls,
        "company_id": row.company_id,
        "note": row.note,
        "is_active": row.is_active,
        "employee_ids": mailbox_service.thanh_vien_ids(db, row.id),
    }


@router.get("")
def list_mailboxes(
    db: Session = Depends(get_db),
    user=Depends(require("mailbox", "read")),
    q: str = "",
    is_active: bool | None = None,
):
    """Danh sách hộp thư. **Trả thẳng một mảng, KHÔNG phân trang.**

    Cố ý không đi qua `apply_filters` / `pagination` như các màn danh sách lớn:
    bảng này là danh mục quản trị cỡ vài dòng (mỗi phòng ban đứng tên phát hành
    một hộp thư là cùng). Bọc thêm phong bì phân trang cho nó chỉ tạo ra một hình
    dạng phản hồi thứ hai mà tầng gọi phải bóc, trong khi màn hình vốn nạp một
    phát rồi lọc tại chỗ.
    """
    query = apply_scope(db.query(Mailbox), Mailbox, "mailbox", user,
                        get_perm_profile(db, user))
    if is_active is not None:
        query = query.filter(Mailbox.is_active.is_(is_active))
    if (q or "").strip():
        needle = f"%{q.strip()}%"
        query = query.filter(Mailbox.code.like(needle)
                             | Mailbox.name.like(needle)
                             | Mailbox.email.like(needle))
    rows = query.order_by(Mailbox.name.asc()).all()
    return success([_ra_json(db, row) for row in rows])


@router.get("/{mailbox_id}")
def get_mailbox(
    mailbox_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("mailbox", "read")),
):
    return success(_ra_json(db, mailbox_service.get_or_404(db, mailbox_id)))


@router.post("")
def create_mailbox(
    data: MailboxIn,
    db: Session = Depends(get_db),
    user=Depends(require("mailbox", "create")),
):
    values = data.model_dump(exclude={"smtp_password", "employee_ids"})
    values["email"] = str(values["email"]).strip().lower()
    row = Mailbox(**values, created_by=user.id, updated_by=user.id)
    mailbox_service.dat_mat_khau(row, data.smtp_password)
    db.add(row)
    db.flush()
    mailbox_service.dat_thanh_vien(db, row, data.employee_ids, user.id)
    record(db, user.id, "mailbox", row.id, "create",
           f"Tạo hộp thư gửi {row.email}")
    db.commit()
    return success(_ra_json(db, row), "Đã tạo hộp thư gửi")


@router.patch("/{mailbox_id}")
def update_mailbox(
    mailbox_id: int,
    data: MailboxIn,
    db: Session = Depends(get_db),
    user=Depends(require("mailbox", "write")),
):
    row = mailbox_service.get_or_404(db, mailbox_id)
    for field, value in data.model_dump(
            exclude={"smtp_password", "employee_ids"}).items():
        setattr(row, field, str(value).strip().lower() if field == "email" else value)
    mailbox_service.dat_mat_khau(row, data.smtp_password)
    row.updated_by = user.id
    so_nguoi = mailbox_service.dat_thanh_vien(db, row, data.employee_ids, user.id)
    record(db, user.id, "mailbox", row.id, "update",
           f"Sửa hộp thư {row.email} · {so_nguoi} người được dùng")
    db.commit()
    return success(_ra_json(db, row), "Đã lưu hộp thư gửi")


@router.delete("/{mailbox_id}/password")
def clear_password(
    mailbox_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("mailbox", "write")),
):
    """Xóa mật khẩu ứng dụng — thao tác RIÊNG, có chủ ý. Xem `dat_mat_khau`."""
    row = mailbox_service.get_or_404(db, mailbox_id)
    mailbox_service.xoa_mat_khau(row)
    row.updated_by = user.id
    record(db, user.id, "mailbox", row.id, "update",
           f"Xóa mật khẩu ứng dụng của {row.email}")
    db.commit()
    return success(_ra_json(db, row), "Đã xóa mật khẩu ứng dụng")


@router.delete("/{mailbox_id}")
def delete_mailbox(
    mailbox_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("mailbox", "delete")),
):
    row = mailbox_service.get_or_404(db, mailbox_id)
    #  Ngừng dùng chứ không xóa hẳn: nhật ký thư cũ còn trỏ vào đây, và câu "thư
    #  đó gửi danh nghĩa ai" phải trả lời được mãi về sau.
    row.is_active = False
    row.updated_by = user.id
    record(db, user.id, "mailbox", row.id, "delete",
           f"Ngừng dùng hộp thư {row.email}")
    db.commit()
    return success(_ra_json(db, row), "Đã ngừng dùng hộp thư")


@router.get("/cua-toi/danh-sach")
def my_mailboxes(
    company_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """Hộp thư TÔI được gửi danh nghĩa — dùng cho các màn ngoài phân hệ Văn bản."""
    rows = mailbox_service.cua_nhan_su(
        db, getattr(user, "employee_id", None), company_id)
    return success([
        {"id": row.id, "email": row.email, "name": row.name,
         "display_name": row.display_name or row.name,
         "ready": mailbox_service.san_sang_gui(row)}
        for row in rows
    ])
