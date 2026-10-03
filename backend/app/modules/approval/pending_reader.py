"""Người ĐANG được giao duyệt một chứng từ thì được ĐỌC chứng từ đó (bao-CR-584).

Bộ máy duyệt giao việc theo luồng cấu hình — trưởng bộ phận của người nộp, một vai
trò (Pháp lý, Quản lý điều phối…), một người cụ thể. Người được giao rất hay nằm
NGOÀI phạm vi dữ liệu của chứng từ: Pháp lý kiểm tra dấu của mọi phòng, trưởng bộ
phận được người tạo chọn ở phòng khác. Không nới thì chuỗi hậu quả là: chuông báo
«chờ bạn duyệt» → bấm vào trang chi tiết 404 → không thấy nút Duyệt → phiếu kẹt,
không chỗ nào đỏ lên. Kể cả mở được phiếu mà không mở được TỆP CHỨNG TỪ thì người
kiểm vẫn không kiểm được gì.

Luật một chỗ, dùng ở ba cửa: trang chi tiết phiếu, tệp đính kèm, ô Trao đổi.

⚠️ Chỉ nới khi việc **đang treo** (`has_pending_task`). Duyệt xong là đóng lại —
không thì mỗi lượt ký lại thêm vĩnh viễn một phiếu vào tầm nhìn của một người.
⚠️ Chỉ áp cho loại chứng từ khai trong `APPROVER_READABLE`. Mở cho «mọi entity»
là một quyết định khác hẳn, phải rà từng loại trước.
"""
from sqlalchemy.orm import Session

#: Loại chứng từ áp luật «đang được giao duyệt thì đọc được».
APPROVER_READABLE = frozenset({"vehicle_booking", "seal_request"})


def is_pending_approver(db: Session, entity: str, entity_id: int | None, user) -> bool:
    """Người này có đang giữ một việc duyệt CÒN TREO trên chứng từ này không."""
    if entity not in APPROVER_READABLE or not entity_id:
        return False
    employee_id = getattr(user, "employee_id", 0) or 0
    if not employee_id:
        return False
    from .steps_service import has_pending_task

    return has_pending_task(db, entity, int(entity_id), employee_id)
