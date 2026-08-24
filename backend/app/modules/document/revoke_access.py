"""AI CÒN XEM ĐƯỢC VĂN BẢN ĐÃ BÃI BỎ.

Bãi bỏ **là một thay đổi về quyền xem**, không chỉ là đổi nhãn trạng thái. Trước
ngày 24/08/2026 nó chỉ đổi `status` và không hàm phân quyền nào đọc tới cột đó,
nên ai đọc được văn bản trước khi bãi bỏ thì sau vẫn đọc, vẫn mở chi tiết, vẫn
xuất Word — người trong phạm vi áp dụng tiếp tục làm theo một văn bản đã chết.

Luật mới, chốt cùng khách 24/08/2026:

  Văn bản đã bãi bỏ **chỉ còn bốn nhóm** xem được —
  1. người TẠO ra nó (`created_by`),
  2. người CHỊU TRÁCH NHIỆM nội dung (`owner_employee_id`),
  3. người vừa BÃI BỎ nó (`updated_by` — bãi bỏ là bước cuối của vòng đời nên
     cột này không bị nhịp sửa nào ghi đè sau đó),
     ⚠️ Cột này chỉ đúng nghĩa "người bãi bỏ" **nếu mọi đường bãi bỏ đều ghi
     nó**. Có hai đường: nút «Bãi bỏ» (`service.revoke`) và ban hành văn bản
     mang quan hệ *bãi bỏ* (`supersede_service.apply_supersede`). Đường thứ hai
     ban đầu quên ghi, và hậu quả đúng bằng lỗ hổng: người SỬA CUỐI CÙNG trước
     đó giữ nguyên quyền xem. Thêm đường bãi bỏ thứ ba thì phải ghi cột này.
  4. người có quyền đọc văn bản ở **phạm vi công ty hoặc toàn hệ** — quản trị và
     văn thư.

Nhóm 4 là chỗ khác với câu chữ *"ngoài người tạo thì không ai xem được"*, và cố
ý: **Sổ văn bản phải tra ra được**. Văn bản đã cấp số mà biến mất khỏi sổ với cả
người giữ sổ thì đó là một lỗ trong sổ đăng ký — đúng thứ mà luật *"bản cũ không
xóa, không ẩn — xóa là mất bằng chứng"* (`doc/erp/van-thu/05-vong-doi-phien-ban.md`)
cấm. Người phải tuân theo văn bản thì hết thấy; người phải lưu hồ sơ thì vẫn thấy.
"""
from sqlalchemy import or_

from .model import STATUS_REVOKED, Document

#  Hai phạm vi được coi là "giữ sổ": thấy toàn bộ văn bản của một pháp nhân trở
#  lên. Tên phạm vi lấy từ `core/scoping.py`.
PHAM_VI_GIU_SO = ("company", "all")


def giu_so(profile: dict, action: str = "read") -> bool:
    """Người này có quyền `action` trên văn bản ở phạm vi công ty / toàn hệ không.

    Đọc thẳng từng GRANT chứ không dùng `perms_union`: hợp nhất quyền làm mất
    thông tin phạm vi, mà ở đây phạm vi mới là thứ quyết định.
    """
    for grant in profile.get("grants") or []:
        quyen = (grant.get("perms") or {}).get("document") or {}
        if quyen.get(action) and quyen.get("scope") in PHAM_VI_GIU_SO:
            return True
    return False


def dieu_kien_loc(user, profile: dict):
    """Điều kiện SQL cộng thêm vào bộ lọc danh sách. `None` = không phải lọc gì."""
    if giu_so(profile):
        return None

    ve = [
        Document.status != STATUS_REVOKED,
        Document.created_by == user.id,
        Document.updated_by == user.id,
    ]
    employee_id = getattr(user, "employee_id", None) or 0
    if employee_id:
        ve.append(Document.owner_employee_id == employee_id)
    return or_(*ve)


def con_xem_duoc(doc: Document, user, profile: dict) -> bool:
    """Bản ghi CỤ THỂ này người đang đăng nhập còn xem được không.

    Trả `True` cho mọi văn bản chưa bãi bỏ — chỗ gọi chỉ cần hỏi một câu, không
    phải tự kiểm trạng thái trước.
    """
    if doc.status != STATUS_REVOKED:
        return True
    if giu_so(profile):
        return True

    employee_id = getattr(user, "employee_id", None) or 0
    return (
        doc.created_by == user.id
        or doc.updated_by == user.id
        or bool(employee_id and doc.owner_employee_id == employee_id)
    )
