"""Khớp CHỦ THỂ (người · phòng ban · pháp nhân · vai trò) + tính HIỆU LỰC (còn
hạn, chưa thu hồi) — dùng CHUNG cho mọi bảng kiểu "ai được/bị áp dụng gì lên
một đối tượng": `tab_document_access` (đã có, `document/access_service.py`) và
`tab_doc_folder_access` (phase 04, duoc-CR-475, `doc_catalog/folder_access_service.py`).

Tách ra khỏi `document/access_service.py` để thư mục dùng LẠI đúng luật khớp
chủ thể + luật hiệu lực, thay vì chép sang một bản mới rồi hai bản trôi dần xa
nhau (`plan.md` phase 04, bước 1: "Tách hàm khớp chủ thể; test ACL văn bản cũ
phải xanh nguyên").

Hằng SUBJECT_*/EFFECT_* GỐC vẫn khai ở `document/access_model.py` (bảng
`tab_document_access` ra đời trước, nhiều nơi đã `from .access_model import
SUBJECT_EMPLOYEE`) — ở đây IMPORT LẠI đúng bốn+hai con số đó, không định nghĩa
hai lần. `core/` được phép import từ `app/modules/` (xem `core/auth.py`,
`core/scoping.py` đã làm vậy), nên chiều import này không mới.
"""
from datetime import date

from sqlalchemy import and_, or_

from app.modules.document.access_model import (EFFECT_ALLOW, EFFECT_DENY,  # noqa: F401 — re-export
                                                EFFECT_LABELS, SUBJECT_COMPANY,
                                                SUBJECT_DEPARTMENT, SUBJECT_EMPLOYEE,
                                                SUBJECT_LABELS, SUBJECT_ROLE)


def subject_pairs(profile: dict) -> list[tuple[int, int]]:
    """Người đang đăng nhập ứng với những (loại đối tượng, id) nào.

    Một người khớp nhiều dòng cùng lúc: bản thân họ, MỌI phòng KIÊM NHIỆM
    (CR-167 — lùi về phòng chính khi hồ sơ quyền chưa có danh sách), pháp nhân
    của họ, và từng vai trò họ mang. Bản DÙNG CHUNG, chuyển nguyên logic từ
    `document/access_service.py` (bản gốc giữ nguyên tên hàm, gọi qua đây).
    """
    pairs: list[tuple[int, int]] = []
    if profile.get("employee_id"):
        pairs.append((SUBJECT_EMPLOYEE, profile["employee_id"]))
    for department_id in (profile.get("dept_ids")
                          or ([profile["dept_id"]] if profile.get("dept_id") else [])):
        if department_id:
            pairs.append((SUBJECT_DEPARTMENT, department_id))
    if profile.get("company_id"):
        pairs.append((SUBJECT_COMPANY, profile["company_id"]))
    for grant in profile.get("grants", []):
        if grant.get("role_id"):
            pairs.append((SUBJECT_ROLE, grant["role_id"]))
    return pairs


def subject_match_condition(model, profile: dict):
    """Điều kiện SQL "dòng này khớp người đang đăng nhập" cho một bảng có hai
    cột `subject_kind`/`subject_id` (đúng hình dạng `tab_document_access` và
    `tab_doc_folder_access`). `None` = người này không có gì để khớp (chưa gắn
    hồ sơ nhân sự, chưa mang vai trò nào)."""
    pairs = subject_pairs(profile)
    if not pairs:
        return None
    return or_(*[
        and_(model.subject_kind == kind, model.subject_id == sid) for kind, sid in pairs
    ])


def still_live_condition(model, today: date | None = None):
    """Điều kiện "dòng còn hiệu lực": chưa thu hồi (`revoked_at IS NULL`) và
    đang trong hạn (`valid_from`/`valid_to`, trống = không hạn)."""
    today = today or date.today()
    return and_(
        model.revoked_at.is_(None),
        or_(model.valid_from.is_(None), model.valid_from <= today),
        or_(model.valid_to.is_(None), model.valid_to >= today),
    )
