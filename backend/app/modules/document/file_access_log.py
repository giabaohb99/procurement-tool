"""NHẬT KÝ MỞ / TẢI TỆP ĐÍNH KÈM VĂN BẢN + cảnh báo khi bất thường.

Không có cách nào chặn người xem chụp lại màn hình (xem `attachment-viewer-dialog.tsx`).
Thứ thay thế được là **biết ai đã mở cái gì, lúc nào** — và khi một người mở/tải
dồn dập bất thường thì báo ngay cho người quản lý, đừng đợi tới lúc tài liệu đã
nằm ngoài công ty mới đi dựng lại.

Ba phần, cố ý tách rời:

  1. **Ghi** — mỗi lượt mở/tải một dòng `tab_audit_log` trên chính VĂN BẢN, nên
     nó hiện thẳng trong sổ nhật ký của văn bản đó, không phải đi tra bảng khác.
  2. **Đếm** — bao nhiêu lượt của cùng một người trong cửa sổ vừa qua.
  3. **Báo** — vượt ngưỡng thì gửi chuông cho người được chỉ định.

⚠️ Ghi nhật ký **không được làm hỏng việc mở tệp**. Người dùng có quyền, tệp có
thật, mà bấm vào lại báo lỗi chỉ vì bảng nhật ký trục trặc là đổi một phiền toái
nhỏ lấy một sự cố lớn. Nên toàn bộ phần này chạy trong `try/except` ở chỗ gọi.
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.app_settings import get as setting
from app.core.audit import record, resolve_actor
from app.modules.notification.model import Notification

from .model import Document

LOGGER = logging.getLogger(__name__)

ACTION_XEM = "view_file"
ACTION_TAI = "download_file"
#  Dòng đánh dấu "đã báo rồi" — dùng luôn nhật ký làm chỗ nhớ, khỏi đẻ bảng mới
#  chỉ để chống gửi trùng.
ACTION_CANH_BAO = "file_alert"

NHAN_HANH_DONG = {ACTION_XEM: "Mở xem", ACTION_TAI: "Tải về"}


def ghi_va_canh_bao(db: Session, doc: Document, user, hanh_dong: str, ten_tep: str) -> None:
    """Ghi một lượt mở/tải, rồi báo nếu người này đang mở dồn dập bất thường."""
    record(db, user.id, "document", doc.id, hanh_dong,
           f"{NHAN_HANH_DONG.get(hanh_dong, hanh_dong)} tệp «{ten_tep}»")

    nguong = int(setting("doc_file_alert_threshold") or 0)
    if nguong <= 0:  # 0 = tắt hẳn phần cảnh báo
        return

    phut = int(setting("doc_file_alert_window_min") or 10)
    tu_luc = _moc_cua_so(db, phut)
    so_luot = _dem_luot(db, user.id, tu_luc)
    if so_luot < nguong:
        return
    if _da_bao_trong_cua_so(db, user.id, tu_luc):
        #  Đã báo một lần trong cửa sổ này rồi. Không báo lại mỗi lượt tiếp theo:
        #  người nhận sẽ tắt tiếng chuông, và lần sau có chuyện thật thì không ai
        #  nhìn nữa.
        return

    _bao_dong(db, doc, user, so_luot, phut)


def _moc_cua_so(db: Session, phut: int) -> datetime:
    """Mốc đầu cửa sổ, đo bằng ĐỒNG HỒ CỦA CSDL.

    ⚠️ KHÔNG dùng `datetime.utcnow()` của Python. `created_at` do CSDL ghi
    (`server_default=func.now()` ở `core/base_model.py`), nên nếu máy chủ CSDL
    chạy giờ Việt Nam mà đây lấy giờ UTC thì cửa sổ lệch **7 tiếng** — và lệch
    đúng chiều gây **báo động giả**: bảy tiếng hoạt động bị đếm như thể xảy ra
    trong mười phút. Ở máy lập trình hai đồng hồ tình cờ trùng nhau (container
    chạy UTC) nên lỗi này không lộ ra khi thử.

    Hỏi thẳng CSDL thì hai vế của phép so luôn cùng một đồng hồ, khỏi phụ thuộc
    cấu hình múi giờ của từng môi trường.
    """
    bay_gio = db.execute(select(func.now())).scalar()
    if isinstance(bay_gio, str):  # SQLite trả chuỗi
        bay_gio = datetime.fromisoformat(bay_gio)
    return (bay_gio or datetime.now()) - timedelta(minutes=phut)


def _dem_luot(db: Session, user_id: int, tu_luc: datetime) -> int:
    from app.modules.audit.model import AuditLog

    return (db.query(AuditLog)
            .filter(AuditLog.entity == "document",
                    AuditLog.action.in_((ACTION_XEM, ACTION_TAI)),
                    AuditLog.created_by == user_id,
                    AuditLog.created_at >= tu_luc)
            .count())


def _da_bao_trong_cua_so(db: Session, user_id: int, tu_luc: datetime) -> bool:
    from app.modules.audit.model import AuditLog

    return (db.query(AuditLog.id)
            .filter(AuditLog.entity == "document",
                    AuditLog.action == ACTION_CANH_BAO,
                    AuditLog.entity_id == user_id,
                    AuditLog.created_at >= tu_luc)
            .first()) is not None


def _bao_dong(db: Session, doc: Document, user, so_luot: int, phut: int) -> None:
    ten = resolve_actor(db, user.id)
    tieu_de = f"Bất thường: {ten} mở {so_luot} tệp trong {phut} phút"
    than = (
        f"{ten} vừa mở hoặc tải {so_luot} tệp đính kèm văn bản trong {phut} phút gần đây. "
        f"Tệp gần nhất thuộc văn bản «{doc.doc_code or doc.issue_number or doc.title}». "
        f"Mở sổ nhật ký của văn bản để xem chi tiết."
    )

    nguoi_nhan = nguoi_nhan_canh_bao(db)
    for uid in nguoi_nhan:
        #  Không tự báo cho chính người đang thao tác: cảnh báo là để người khác
        #  biết, còn họ thì đã biết mình vừa làm gì.
        if uid == user.id:
            continue
        db.add(Notification(user_id=uid, title=tieu_de, body=than,
                            link=f"/document/documents/{doc.id}", created_by=0))

    #  `entity_id` = id NGƯỜI bị cảnh báo (không phải id văn bản): chống gửi trùng
    #  tra theo người, mà một người thì mở nhiều văn bản khác nhau.
    record(db, 0, "document", user.id, ACTION_CANH_BAO,
           f"{tieu_de} — đã báo cho {len(nguoi_nhan)} người")


def nguoi_nhan_canh_bao(db: Session) -> list[int]:
    """Ai nhận cảnh báo.

    Ưu tiên danh sách khai tay ở Cấu hình hệ thống (`doc_file_alert_recipients`,
    ngăn cách bằng dấu phẩy, nhận email hoặc mã nhân viên). Bỏ trống thì tự suy:
    **mọi tài khoản có quyền ĐỌC văn bản ở phạm vi toàn hệ** — tức quản trị và
    văn thư cấp tập đoàn, cùng nhóm "giữ sổ" ở `revoke_access.py`.

    Vì sao có đường tự suy: khai tay mà quên khai thì cảnh báo rơi vào hư không
    và không ai biết là nó đang không chạy.
    """
    khai_tay = (setting("doc_file_alert_recipients") or "").strip()
    if khai_tay:
        return _theo_danh_sach(db, khai_tay)
    return _theo_quyen_toan_he(db)


def _theo_danh_sach(db: Session, chuoi: str) -> list[int]:
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    khoa = [phan.strip() for phan in chuoi.split(",") if phan.strip()]
    if not khoa:
        return []
    rows = (db.query(User.id)
            .outerjoin(Employee, Employee.id == User.employee_id)
            .filter(User.is_active.is_(True),
                    User.email.in_(khoa) | Employee.code.in_(khoa))
            .all())
    return [row[0] for row in rows]


def _theo_quyen_toan_he(db: Session) -> list[int]:
    from app.modules.role.model import Permission
    from app.modules.user.model import User, UserRole

    role_ids = [row[0] for row in
                db.query(Permission.role_id)
                .filter(Permission.entity == "document",
                        Permission.can_read.is_(True),
                        Permission.scope == "all")
                .all()]
    if not role_ids:
        return []
    rows = (db.query(User.id)
            .join(UserRole, UserRole.user_id == User.id)
            .filter(UserRole.role_id.in_(role_ids), User.is_active.is_(True))
            .distinct()
            .all())
    return [row[0] for row in rows]
