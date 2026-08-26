"""LUẬT CỦA HỘP THƯ GỬI — ai dùng được cái nào, và mật khẩu cất ra sao.

Tách khỏi controller vì hai chốt dưới đây phải gọi được từ chỗ khác ngoài API:
`document/service.approve()` kiểm quyền dùng hộp thư ngay trong nhịp ban hành,
còn tác vụ gửi thư nền thì cần đường SMTP đã giải mã.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core import app_settings

from .mailbox_model import Mailbox, MailboxMember


def get_or_404(db: Session, mailbox_id: int) -> Mailbox:
    row = db.get(Mailbox, mailbox_id)
    if row is None:
        raise HTTPException(404, "Không tìm thấy hộp thư gửi")
    return row


# ── Mật khẩu ứng dụng ────────────────────────────────────────────────────────

def dat_mat_khau(mailbox: Mailbox, mat_khau: str) -> None:
    """Cất mật khẩu ứng dụng đã mã hóa. Chuỗi rỗng = **không đụng tới** cái cũ.

    ⚠️ Phân biệt "không gửi ô mật khẩu" với "xóa mật khẩu". Màn sửa hộp thư
    không bao giờ nhận lại được giá trị cũ (API không trả), nên nó gửi lên chuỗi
    rỗng ở mọi lần sửa tên/ghi chú. Coi rỗng là xóa thì sửa một cái nhãn cũng đủ
    làm hộp thư ngừng gửi được, mà không dòng nào báo.
    """
    if not (mat_khau or "").strip():
        return
    mailbox.smtp_password_enc = app_settings.encrypt(mat_khau.strip())


def xoa_mat_khau(mailbox: Mailbox) -> None:
    """Xóa hẳn — phải là một thao tác RIÊNG, có chủ ý. Xem `dat_mat_khau`."""
    mailbox.smtp_password_enc = ""


def duong_smtp(mailbox: Mailbox) -> dict:
    """Đường SMTP đã giải mã cho tác vụ gửi thư. **Không lộ ra API.**"""
    from app.core.app_settings import _decrypt

    return {
        "host": mailbox.smtp_host,
        "port": mailbox.smtp_port or 587,
        "user": mailbox.smtp_user or mailbox.email,
        "password": _decrypt(mailbox.smtp_password_enc or ""),
        "use_tls": bool(mailbox.use_tls),
        "from_email": mailbox.email,
        "from_name": mailbox.display_name or mailbox.name,
    }


def san_sang_gui(mailbox: Mailbox) -> bool:
    """Hộp thư đã khai đủ để gửi được chưa."""
    return bool(mailbox.smtp_host and mailbox.smtp_password_enc
                and (mailbox.smtp_user or mailbox.email))


# ── Ai dùng được hộp thư nào ─────────────────────────────────────────────────

def cua_nhan_su(db: Session, employee_id: int | None,
                company_id: int | None = None) -> list[Mailbox]:
    """Những hộp thư nhân sự này được gửi danh nghĩa.

    `company_id` chỉ để LỌC hiển thị theo pháp nhân đang ban hành: hộp thư khai
    pháp nhân khác thì không bày ra cho đỡ rối. Hộp thư không khai pháp nhân
    (cấp Tập đoàn) thì nơi nào cũng thấy.
    """
    if not employee_id:
        return []

    q = (db.query(Mailbox)
         .join(MailboxMember, MailboxMember.mailbox_id == Mailbox.id)
         .filter(MailboxMember.employee_id == employee_id,
                 Mailbox.is_active.is_(True)))
    if company_id:
        q = q.filter((Mailbox.company_id.is_(None))
                     | (Mailbox.company_id == company_id))
    return q.order_by(Mailbox.name.asc()).all()


def duoc_dung(db: Session, mailbox_id: int, employee_id: int | None) -> bool:
    if not employee_id:
        return False
    return (db.query(MailboxMember.id)
            .filter(MailboxMember.mailbox_id == mailbox_id,
                    MailboxMember.employee_id == employee_id)
            .first() is not None)


def ensure_duoc_dung(db: Session, mailbox_id: int,
                     employee_id: int | None) -> Mailbox:
    """Chốt chặn thật, gọi từ nhịp ban hành — không chỉ ẩn nút trên giao diện.

    Gửi thư danh nghĩa cả một phòng ban là thứ mượn được thì phải chặn ở tầng
    dịch vụ: giao diện chỉ bày ra hộp thư của mình, nhưng `mailbox_id` là một số
    trong thân request và ai cũng gõ số khác vào được.
    """
    mailbox = get_or_404(db, mailbox_id)
    if not mailbox.is_active:
        raise HTTPException(400, f"Hộp thư «{mailbox.email}» đã ngừng dùng")
    if not duoc_dung(db, mailbox_id, employee_id):
        raise HTTPException(
            403,
            f"Bạn chưa được cấp quyền gửi thư danh nghĩa «{mailbox.email}». "
            "Đề nghị quản trị thêm bạn vào hộp thư này.",
        )
    if not san_sang_gui(mailbox):
        raise HTTPException(
            400,
            f"Hộp thư «{mailbox.email}» chưa khai đủ đường SMTP (máy chủ và mật "
            "khẩu ứng dụng) nên chưa gửi được.",
        )
    return mailbox


def dat_thanh_vien(db: Session, mailbox: Mailbox, employee_ids: list[int],
                   actor: int) -> int:
    """Đặt LẠI toàn bộ danh sách người được dùng. Trả về số người sau khi đặt."""
    muon = {int(value) for value in employee_ids if value}
    dang_co = {row.employee_id: row for row in db.query(MailboxMember)
               .filter(MailboxMember.mailbox_id == mailbox.id).all()}

    for employee_id, row in dang_co.items():
        if employee_id not in muon:
            db.delete(row)
    for employee_id in muon - set(dang_co):
        db.add(MailboxMember(mailbox_id=mailbox.id, employee_id=employee_id,
                             created_by=actor, updated_by=actor))
    db.flush()
    return len(muon)


def thanh_vien_ids(db: Session, mailbox_id: int) -> list[int]:
    return [row[0] for row in db.query(MailboxMember.employee_id)
            .filter(MailboxMember.mailbox_id == mailbox_id).all()]
