"""Nối DANH MỤC CHỨC VỤ với HỒ SƠ NHÂN SỰ (duoc-CR-320).

⚠️ **Hai cột, một sự thật.** `tab_employee.position_id` là khóa trỏ vào danh
mục — đó là sự thật; `tab_employee.position` là **nhãn đã chép sẵn**. Giữ cả
hai là có chủ ý, không phải quên dọn:

* mười chỗ đang đọc thẳng `emp.position` để in phiếu, xuất Excel, dựng hồ sơ cho
  trợ lý AI và ghi tiêu đề YCMH/YCBG (`purchase_request/service.py`,
  `survey_request/service.py`, `core/audit.py`, `export_log/registry.py`…). Đổi
  hết sang `join` chỉ để lấy một chuỗi là mười chỗ có thể sót một;
* **hồ sơ cũ chưa map** vẫn giữ nguyên chữ người ta đã gõ. Ép hết vào danh mục
  ngay là hoặc mất dữ liệu, hoặc đẻ ra vài chục dòng danh mục rác từ những lỗi
  gõ cũ.

Cái giá của việc chép nhãn là nó **trôi** nếu không ai đồng bộ. Nên toàn hệ chỉ
có ĐÚNG HAI đường ghi vào `position`, cả hai nằm trong tệp này:

1. `sync_label` — lưu hồ sơ và có đụng `position_id`;
2. `propagate_rename` — đổi tên một dòng danh mục.

Thêm đường thứ ba ở chỗ khác là mở lại đúng mớ dữ liệu mà đợt này đang dọn.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .model import Employee
from .position_model import JobPosition


def get_position(db: Session, position_id: int) -> JobPosition | None:
    """Đọc một dòng danh mục. `0` (chưa gán) trả `None`, không nổ."""
    return db.get(JobPosition, position_id) if position_id else None


def check_assignable(db: Session, position_id: int) -> JobPosition | None:
    """Chức vụ gán được cho hồ sơ không — chặn id chết và chức vụ đã ngừng dùng.

    ⚠️ Chặn id KHÔNG TỒN TẠI vì cột này không có khóa ngoại cứng (cùng quy ước
    với `department_id`, `manager_id` của module này): không kiểm ở tầng dịch vụ
    thì `position_id = 99999` ghi xuống êm ru, và hồ sơ đó hiện chức vụ rỗng mãi
    mãi mà không ai truy được vì sao.

    ⚠️ Chặn chức vụ **đã ngừng dùng** vì ô chọn trên giao diện chỉ đổ dòng đang
    dùng; gán được một dòng không có trong ô chọn nghĩa là mở hồ sơ ra sửa ô
    khác rồi bấm Lưu là giao diện tự đổi chức vụ sang giá trị đầu danh sách.
    Ngoại lệ: hồ sơ ĐANG giữ chức vụ đó thì giữ nguyên được — xem `sync_label`.
    """
    if not position_id:
        return None
    obj = get_position(db, position_id)
    if obj is None:
        raise HTTPException(400, "Chức vụ không tồn tại")
    if not obj.is_active:
        raise HTTPException(
            400, f"Chức vụ «{obj.name}» đã ngừng dùng nên không gán mới được. "
                 "Bật lại ở danh mục Chức vụ, hoặc chọn chức vụ khác.")
    return obj


def sync_label(db: Session, obj: Employee, fields: dict, old_position_id: int = 0) -> None:
    """Chép tên chức vụ sang `Employee.position` sau khi `position_id` đổi.

    Gọi ở CẢ hai đường ghi hồ sơ (tạo mới và cập nhật), ngay trước `commit`.

    Ba nước, theo đúng thứ tự:

    * lần lưu này KHÔNG gửi `position_id` → không đụng gì. Quan trọng: màn hồ sơ
      gửi `PATCH` một phần, nên đụng vào đây là mọi lần lưu ô khác cũng ghi đè
      chức vụ;
    * gửi `position_id = 0` → **xóa cả nhãn**. "Bỏ chọn chức vụ" mà vẫn để lại
      chữ cũ trên phiếu in là thứ tệ nhất trong ba nước: người dùng thấy ô trống
      trên màn hình và tin rằng phiếu in cũng trống;
    * gửi một id thật → nhãn = tên trong danh mục.

    ⚠️ `old_position_id` không phải để tối ưu. Màn hồ sơ gửi LẠI mọi ô mỗi lần
    lưu, kể cả ô không đổi — nên hồ sơ đang giữ một chức vụ vừa bị Nhân sự cho
    ngừng dùng sẽ **không sửa nổi ô nào khác** (mỗi lần Lưu đều ăn câu «chức vụ
    đã ngừng dùng») cho tới khi có người đi đổi chức vụ của họ. Giữ nguyên giá
    trị cũ thì luôn hợp lệ; chốt `check_assignable` chỉ áp cho việc gán MỚI.
    """
    if "position_id" not in fields:
        return
    new_id = fields["position_id"] or 0
    if new_id and new_id == (old_position_id or 0):
        position = get_position(db, new_id)
    else:
        position = check_assignable(db, new_id)
    obj.position = position.name if position else ""


def propagate_rename(db: Session, position: JobPosition, new_name: str) -> int:
    """Đổi tên chức vụ → cập nhật nhãn của MỌI hồ sơ đang giữ nó.

    ⚠️ Thiếu nhịp này thì sửa lỗi chính tả trong danh mục xong, màn hình hiện
    tên mới (nó đọc theo id) còn **bản in và tệp Excel vẫn ra tên cũ** — sai
    lệch chỉ lộ ra ở tờ giấy đưa cho khách, tức là muộn nhất có thể.

    Trả về số hồ sơ đã chạm để chỗ gọi ghi vào nhật ký. Chạy trong CÙNG giao
    dịch với lệnh sửa danh mục (bộ sinh CRUD `commit` sau `before_update`), nên
    hoặc cả hai cùng vào, hoặc cả hai cùng không.
    """
    if not new_name or new_name == position.name:
        return 0
    return (db.query(Employee)
            .filter(Employee.position_id == position.id)
            .update({Employee.position: new_name}, synchronize_session=False))


def resolve_by_name(db: Session, name: str) -> JobPosition | None:
    """Tìm dòng danh mục theo TÊN — cho đường nhập CSV, nơi người ta gõ chữ.

    So không phân biệt hoa thường và bỏ khoảng trắng thừa, đúng luật mà
    migration `c5e2a8b31d47` đã dùng để gom dữ liệu cũ: tệp CSV người dùng sửa
    trong Excel thì «Trưởng phòng» và «Trưởng Phòng » là cùng một chức vụ.

    ⚠️ Không khớp thì trả `None` và chỗ gọi giữ nguyên CHỮ, `position_id = 0` —
    **cố ý không tự tạo dòng danh mục mới**. Tự tạo thì mỗi lỗi gõ trong một tệp
    CSV đẻ ra một chức vụ, và danh mục vừa dọn xong lại đầy rác sau một lần nhập.
    """
    text = " ".join((name or "").split())
    if not text:
        return None
    for row in db.query(JobPosition).filter(JobPosition.is_active.is_(True)).all():
        if " ".join((row.name or "").split()).casefold() == text.casefold():
            return row
    return None


def count_employees(db: Session, position_id: int) -> int:
    """Số hồ sơ đang giữ chức vụ này — dùng cho chốt chặn xóa.

    ⚠️ **KHÔNG lọc theo phạm vi dữ liệu**, cố ý: đây là chốt TOÀN VẸN dữ liệu,
    không phải một con số để đọc. Lọc theo phạm vi thì người chỉ thấy phòng mình
    xóa được một chức vụ mà phòng khác đang giữ.
    """
    return db.query(Employee).filter(Employee.position_id == position_id).count()
