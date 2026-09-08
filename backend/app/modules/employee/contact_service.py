"""Đọc / đặt lại hai bảng con của hồ sơ nhân sự.

Cả hai bảng đặt lại **một lượt** (xóa hết rồi ghi lại theo đúng thứ tự client
gửi), giống `department_service.set_extra_departments`. Không sửa từng dòng: đây
là bảng ba–bốn dòng nằm trong một tab của màn hồ sơ, người dùng bấm Lưu của cả
hồ sơ chứ không bấm Lưu của từng dòng.

⚠️ **Không hàm nào ở đây xét quyền.** Chốt nằm ở controller — phạm vi lấy từ hồ
sơ CHA (`get_scoped(Employee, "employee", ...)`) và nội dung gác bằng
`employee_sensitive.read`. Lý lẽ đầy đủ ở `sensitive.py`.
"""
from sqlalchemy.orm import Session

from .contact_model import EmployeeContact, EmployeeFamily


def _rows_of(db: Session, model, employee_id: int) -> list:
    return (db.query(model)
            .filter(model.employee_id == employee_id)
            .order_by(model.sort_order, model.id)
            .all())


def list_contacts(db: Session, employee_id: int) -> list[EmployeeContact]:
    return _rows_of(db, EmployeeContact, employee_id)


def list_families(db: Session, employee_id: int) -> list[EmployeeFamily]:
    return _rows_of(db, EmployeeFamily, employee_id)


def _replace_rows(db: Session, model, employee_id: int, items: list, fields: tuple[str, ...],
                  user_id: int) -> list:
    """Xóa sạch rồi ghi lại — KHÔNG commit, để nơi gọi gộp chung transaction.

    Bỏ qua dòng RỖNG HỌ TÊN: giao diện dựng sẵn một dòng trống cho người dùng gõ
    vào, và dòng đó vẫn được gửi lên khi họ không gõ gì. Lưu nó là mỗi lần mở
    hồ sơ ra lại đẻ thêm một người báo tin không tên.

    `sort_order` lấy theo ĐÚNG thứ tự client gửi, không tự sắp lại: người dùng
    kéo cha lên trên mẹ thì đó là một quyết định, không phải ngẫu nhiên. Nhưng
    đánh số theo SỐ DÒNG ĐÃ LƯU chứ không theo chỉ số đầu vào — dòng trống bị bỏ
    ở giữa sẽ để lại lỗ hổng (0, 2, 5…) khiến người đọc dữ liệu tưởng có dòng đã
    bị xóa mất.
    """
    db.query(model).filter(model.employee_id == employee_id).delete(synchronize_session=False)
    saved = []
    for item in items:
        data = item.model_dump()
        if not (data.get("full_name") or "").strip():
            continue
        row = model(employee_id=employee_id, sort_order=len(saved),
                    created_by=user_id, updated_by=user_id,
                    **{f: data[f] for f in fields})
        db.add(row)
        saved.append(row)
    db.flush()
    return saved


_CONTACT_FIELDS = ("full_name", "relation", "address", "phone")
_FAMILY_FIELDS = ("full_name", "relation", "gender", "date_of_birth", "phone", "id_number")


def set_contacts(db: Session, employee_id: int, items: list, user_id: int) -> list[EmployeeContact]:
    return _replace_rows(db, EmployeeContact, employee_id, items, _CONTACT_FIELDS, user_id)


def set_families(db: Session, employee_id: int, items: list, user_id: int) -> list[EmployeeFamily]:
    return _replace_rows(db, EmployeeFamily, employee_id, items, _FAMILY_FIELDS, user_id)


def delete_all_of(db: Session, employee_id: int) -> None:
    """Xóa hai bảng con khi xóa hồ sơ cha.

    Bảng đã khai `ondelete="CASCADE"` ở tầng FK, nhưng SQLAlchemy `db.delete(obj)`
    trên MySQL vẫn để database tự lo — còn bộ test chạy SQLite, nơi ràng buộc
    khóa ngoại **mặc định TẮT**. Nghĩa là ca "xóa nhân sự xong bảng con còn rác"
    không thể kiểm được nếu chỉ trông vào CASCADE. Xóa tường minh ở đây để hai
    môi trường hành xử giống nhau.
    """
    for model in (EmployeeContact, EmployeeFamily):
        db.query(model).filter(model.employee_id == employee_id).delete(synchronize_session=False)
