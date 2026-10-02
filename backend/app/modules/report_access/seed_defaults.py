"""Mặc định CHO PHÉP vai trò 'admin' xem báo cáo MỚI (chưa từng có dòng nào).

Gọi trong `app.seed.run()` và `app.seed_prod.run()` ngay sau `ensure_admin_role`
— không phụ thuộc `SEED_FORCE_SYNC`, chạy mỗi lần khởi động như chính
`ensure_admin_role`.

Hệ quả CỐ Ý (khớp Q3 + "chưa gán = đóng" của plan phân quyền báo cáo):
  - Báo cáo MỚI ra đời (khóa `ReportKey` thêm sau) → admin tự có ngay lần khởi
    động kế tiếp, không ai phải nhớ gán tay.
  - Admin bị THU HỒI dòng của một khóa → seed KHÔNG chèn lại, vì khóa đó đã
    "có ít nhất một dòng" (kể cả dòng thu hồi). Seed không ghi đè việc đại ca
    vừa làm trên UI (cùng luật D-018).
  - Khóa đã có dòng gán cho CHỦ THỂ KHÁC (không phải admin) → cũng không chèn
    thêm cho admin — "có ít nhất một dòng" không phân biệt chủ thể.
"""
from sqlalchemy.orm import Session

from app.core.report_keys import ReportKey
from app.core.subject_match import EFFECT_ALLOW, SUBJECT_ROLE
from app.modules.role.model import Role

from .model import ReportAccess

DEFAULT_REASON = "Mặc định khi ra tính năng phân quyền báo cáo"


def ensure_report_access_defaults(db: Session) -> int:
    """Chèn dòng CHO PHÉP cho vai trò 'admin' với mọi `ReportKey` CHƯA từng có
    dòng nào (kể cả dòng đã thu hồi). Trả số dòng đã chèn; không có vai trò
    'admin' → 0, không chèn gì."""
    admin_role = db.query(Role).filter(Role.code == "admin").first()
    if not admin_role:
        return 0

    keys_with_any_row = {
        row[0] for row in db.query(ReportAccess.report_key).distinct().all()
    }

    n = 0
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
