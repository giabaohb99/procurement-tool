"""Mặc định CHO PHÉP vai trò quản trị hệ thống xem báo cáo MỚI (chưa từng có dòng nào).

Gọi trong `app.seed.run()` và `app.seed_prod.run()` ngay sau `ensure_admin_role`
— không phụ thuộc `SEED_FORCE_SYNC`, chạy mỗi lần khởi động như chính
`ensure_admin_role`.

M5 (code review): chèn cho CẢ vai trò `admin` (đời mới) lẫn `ADMINISTRATOR` (đời cũ) nếu
tồn tại — cùng danh sách hai mã `seed.ensure_admin_role`/`force_resync_roles` coi là MỘT
("vai trò quản trị"). Trước bản vá này chỉ chèn cho `admin`, nên một DB còn giữ
`ADMINISTRATOR` (chưa dọn/đổi tên) sẽ có người quản trị KHÔNG xem được báo cáo nào.

Hệ quả CỐ Ý (khớp Q3 + "chưa gán = đóng" của plan phân quyền báo cáo):
  - Báo cáo MỚI ra đời (khóa `ReportKey` thêm sau) → cả hai vai trò quản trị tự có ngay
    lần khởi động kế tiếp, không ai phải nhớ gán tay.
  - Một vai trò quản trị bị THU HỒI dòng của một khóa → seed KHÔNG chèn lại, vì khóa đó đã
    "có ít nhất một dòng" (kể cả dòng thu hồi). Seed không ghi đè việc đại ca vừa làm trên
    UI (cùng luật D-018).
  - Khóa đã có dòng gán cho CHỦ THỂ KHÁC (không phải admin/ADMINISTRATOR) → cũng không
    chèn thêm — "có ít nhất một dòng" không phân biệt chủ thể.
  - `admin` VÀ `ADMINISTRATOR` cùng tồn tại ở lần khởi động ĐẦU TIÊN (bảng trống) → cả hai
    đều được chèn 13 dòng: trạng thái "khóa nào đã có dòng" được chốt MỘT LẦN trước khi
    chèn cho vai trò nào, round đầu không bị lệch vì thứ tự xử lý vai trò.
"""
from sqlalchemy.orm import Session

from app.core.report_keys import ReportKey
from app.core.subject_match import EFFECT_ALLOW, SUBJECT_ROLE
from app.modules.role.model import Role

from .model import ReportAccess

DEFAULT_REASON = "Mặc định khi ra tính năng phân quyền báo cáo"

#  Cùng danh sách `app.seed.ensure_admin_role`/`force_resync_roles` dùng để coi hai mã này
#  là MỘT vai trò quản trị (đời cũ `ADMINISTRATOR` + đời mới `admin`).
_ADMIN_ROLE_CODES = ("admin", "ADMINISTRATOR")


def ensure_report_access_defaults(db: Session) -> int:
    """Chèn dòng CHO PHÉP cho MỌI vai trò quản trị (`admin`, `ADMINISTRATOR`) với mọi
    `ReportKey` CHƯA từng có dòng nào (kể cả dòng đã thu hồi). Trả số dòng đã chèn; không
    có vai trò quản trị nào → 0, không chèn gì."""
    admin_roles = db.query(Role).filter(Role.code.in_(_ADMIN_ROLE_CODES)).all()
    if not admin_roles:
        return 0

    #  Chốt trạng thái "khóa nào đã có dòng" TRƯỚC khi chèn cho vai trò nào — nếu đọc lại
    #  giữa hai vòng (vd sau khi chèn xong cho `admin`), vai trò `ADMINISTRATOR` ở vòng sau
    #  sẽ thấy các khóa đó đã "có dòng" (do chính `admin` vừa thêm) và bị SKIP — hai vai trò
    #  quản trị lẽ ra phải cùng được chèn ở lần khởi động đầu tiên lại lệch nhau.
    keys_with_any_row = {
        row[0] for row in db.query(ReportAccess.report_key).distinct().all()
    }

    n = 0
    for admin_role in admin_roles:
        for key in ReportKey:
            if int(key) in keys_with_any_row:
                continue
            db.add(ReportAccess(
                report_key=int(key),
                subject_kind=SUBJECT_ROLE,
                subject_id=admin_role.id,
                effect=EFFECT_ALLOW,
                reason=DEFAULT_REASON,
                created_by=0,
                updated_by=0,
            ))
            n += 1
    if n:
        db.commit()
    return n
