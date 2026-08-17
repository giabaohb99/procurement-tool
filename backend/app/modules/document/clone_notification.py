"""THƯ BÁO KÈM BẢN NHÁP ĐÃ CLONE (F09).

*"Mỗi pháp nhân nhận một thư: có bản gốc, có bản nháp đã clone, có hạn xử lý."*

Gửi **hai đường**, cố ý:

  * **chuông trong ứng dụng** — luôn ghi được, nằm trong cùng transaction, và là
    thứ bài kiểm canh được;
  * **thư điện tử** — chỉ chạy khi `EMAIL_WORKFLOW_ENABLED` bật, và có hỏng thì
    cũng không được làm hỏng việc clone.

Vì sao không chỉ gửi thư: thư phụ thuộc SMTP, cấu hình môi trường và hộp thư của
người nhận. Clone xong mà thư rớt thì pháp nhân con không biết có việc — mà bản
nháp thì đã nằm đó rồi. Chuông không rớt.
"""
from sqlalchemy.orm import Session

from app.modules.employee.model import Employee
from app.modules.notification.model import Notification
from app.modules.user.model import User

from .model import Document


def _users_of_company(db: Session, company_id: int,
                      assignee_employee_id: int | None) -> list[User]:
    """Ai ở pháp nhân nhận cần biết. Có người phụ trách thì gửi đúng người đó."""
    if assignee_employee_id:
        user = (
            db.query(User).filter(User.employee_id == assignee_employee_id).first()
        )
        return [user] if user else []

    #  Chưa chỉ định người phụ trách thì gửi cho mọi tài khoản của pháp nhân đó.
    #  Thà nhiều người nhận còn hơn không ai nhận — bản nháp đã nằm sẵn ở đó rồi.
    employee_ids = [
        row[0] for row in
        db.query(Employee.id).filter(Employee.company_id == company_id,
                                     Employee.is_active.is_(True)).all()
    ]
    if not employee_ids:
        return []
    return db.query(User).filter(User.employee_id.in_(employee_ids),
                                 User.is_active.is_(True)).all()


def notify_clone_created(db: Session, source: Document, clone: Document) -> int:
    """Báo cho pháp nhân nhận: có bản nháp mới cần xử lý. Trả về số người đã báo."""
    recipients = _users_of_company(db, clone.company_id, clone.clone_assignee_employee_id)
    if not recipients:
        return 0

    han = f" Hạn xử lý {clone.clone_due_date:%d/%m/%Y}." if clone.clone_due_date else ""
    goc = source.doc_code or source.issue_number or source.title

    for user in recipients:
        db.add(Notification(
            user_id=user.id,
            title=f"Bản nháp cần xử lý: {clone.title}",
            #  Thân thư nêu đủ ba thứ F09 đòi: bản gốc, bản nháp, hạn xử lý.
            body=(
                f"Pháp nhân của bạn nhận một bản nháp được clone từ văn bản «{goc}». "
                f"Để nguyên nếu dùng được, hoặc soạn lại cho đúng pháp nhân mình.{han}"
            ),
            link=f"/document/documents/{clone.id}",
            created_by=clone.cloned_by or 0,
        ))
    return len(recipients)


def notify_clones_stale(db: Session, source: Document, clones: list[Document]) -> int:
    """Điều kiện 3 của clone — gốc lên phiên bản mới thì người phụ trách phải BIẾT.

    Đánh dấu *cần rà lại* mà không báo cho ai thì cái dấu đó nằm im tới lúc có
    người tình cờ mở văn bản ra xem.
    """
    dem = 0
    goc = source.doc_code or source.issue_number or source.title

    for clone in clones:
        for user in _users_of_company(db, clone.company_id, clone.clone_assignee_employee_id):
            db.add(Notification(
                user_id=user.id,
                title=f"Cần rà lại: {clone.title}",
                body=(
                    f"Văn bản gốc «{goc}» đã lên phiên bản mới. Rà lại bản của pháp "
                    "nhân mình xem còn đúng không."
                ),
                link=f"/document/documents/{clone.id}",
                created_by=0,
            ))
            dem += 1
    return dem
