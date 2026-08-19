"""Tính AI THUỘC PHẠM VI áp dụng của văn bản (F01–F05).

Ba quy tắc, thứ tự quan trọng:

1. Các dòng **bao gồm** cộng dồn.
2. **Loại trừ luôn thắng** — dù trùng chiều nào.
3. **Không có dòng nào = áp cho TOÀN BỘ PHÁP NHÂN BAN HÀNH** — mọi phòng ban,
   mọi nhân sự của chính công ty đứng tên văn bản, và chỉ công ty đó.

Quy tắc 3 đổi ngày 19/08/2026. Trước đó "không khai gì = không ai thuộc phạm
vi": an toàn về lý thuyết nhưng sai với việc thật — phần lớn văn bản chỉ lưu
hành trong đúng công ty làm ra nó, mà vẫn bắt người soạn khai tay một dòng
"pháp nhân = công ty mình" thì ai cũng quên, và văn bản ban hành xong không tới
ai. Mặc định mới không làm rò văn bản sang công ty khác: nó dừng đúng ở pháp
nhân ban hành, muốn đi xa hơn vẫn phải khai tay.

Mặc định này chỉ tính cho văn bản **còn sống** (đã duyệt / có hiệu lực) — bản
nháp trong công ty không phải thứ nằm trong mục "Văn bản áp dụng cho tôi".

⚠️ **`include_children` đang là phép xấp xỉ.** `tab_company` chỉ có cột `level`
(1 Tập đoàn · 2 công ty con · 3 …), KHÔNG có cột cha, nên "gồm đơn vị con" hiện
được hiểu là *mọi pháp nhân có `level` lớn hơn*. Đúng với cây một tầng đang có,
sai ngay khi xuất hiện tầng thứ ba thuộc hai nhánh khác nhau. Muốn đúng hẳn thì
phải thêm `parent_id` vào `tab_company` — xem câu hỏi cuối `task-process.md`.
"""
from sqlalchemy.orm import Session

from app.modules.company.model import Company
from app.modules.employee.model import Employee

from .model import ALIVE_STATUSES, Document
from .scope_model import (DIM_COMPANY, DIM_DEPARTMENT, DIM_EMPLOYEE,
                          MODE_EXCLUDE, MODE_INCLUDE, DocumentScope)


def scopes_of(db: Session, document_id: int) -> list[DocumentScope]:
    return (
        db.query(DocumentScope)
        .filter(DocumentScope.document_id == document_id)
        #  Loại trừ hiện SAU bao gồm trên màn hình — đọc theo thứ tự đó là hiểu
        #  ngay "áp cho ai, trừ ai".
        .order_by(DocumentScope.mode.asc(), DocumentScope.dim.asc(),
                  DocumentScope.id.asc())
        .all()
    )


def _child_company_ids(db: Session, company: Company | None) -> set[int]:
    """Pháp nhân "con" của một pháp nhân. Xem cảnh báo ở đầu tệp."""
    if company is None:
        return set()
    rows = db.query(Company.id).filter(Company.level > company.level).all()
    return {row[0] for row in rows}


def _match(db: Session, row: DocumentScope, employee: Employee) -> bool:
    """Một dòng phạm vi có trúng nhân sự này không."""
    if row.dim == DIM_EMPLOYEE:
        return row.employee_id == employee.id

    if row.dim == DIM_DEPARTMENT:
        #  Ràng buộc dữ liệu đã ép `company_id` khác rỗng ở chiều này, nên so cả
        #  hai là đúng ý người khai: "phòng Kế toán CỦA pháp nhân này".
        return (row.department_id == employee.department_id
                and row.company_id == employee.company_id)

    if row.company_id == employee.company_id:
        return True
    if row.include_children:
        return employee.company_id in _child_company_ids(db, db.get(Company, row.company_id))
    return False


def mac_dinh_theo_phap_nhan(doc: Document | None, employee: Employee) -> bool:
    """Quy tắc 3 — văn bản không khai dòng nào thì áp trong đúng pháp nhân của nó."""
    if doc is None:
        return False
    if doc.status not in ALIVE_STATUSES:
        return False
    return doc.company_id == employee.company_id


def applies_to(db: Session, document_id: int, employee: Employee) -> bool:
    """Nhân sự này có thuộc phạm vi áp dụng của văn bản không."""
    rows = scopes_of(db, document_id)
    if not rows:
        return mac_dinh_theo_phap_nhan(db.get(Document, document_id), employee)

    #  Quy tắc 2 — loại trừ thắng, nên xét trước và thoát ngay.
    for row in rows:
        if row.mode == MODE_EXCLUDE and _match(db, row, employee):
            return False

    return any(row.mode == MODE_INCLUDE and _match(db, row, employee) for row in rows)


def document_ids_for(db: Session, employee: Employee) -> list[int]:
    """F05 — mọi văn bản đang áp dụng cho một người.

    Lọc thô ở tầng truy vấn rồi lọc tinh bằng `applies_to`: phần "gồm đơn vị con"
    và luật loại-trừ-thắng không viết gọn thành một câu SQL được, mà số văn bản
    có khai phạm vi thì nhỏ hơn hẳn tổng số văn bản.
    """
    co_khai = {row[0] for row in db.query(DocumentScope.document_id).distinct().all()}
    #  Quy tắc 3 — văn bản còn sống của chính công ty người này, không khai dòng
    #  phạm vi nào, thì mặc định áp cho họ. Lọc luôn ở SQL cho khỏi kéo cả bảng.
    ngam_dinh = {
        row[0]
        for row in db.query(Document.id)
        .filter(
            Document.company_id == employee.company_id,
            Document.status.in_(ALIVE_STATUSES),
            Document.id.notin_(co_khai or {0}),
        )
        .all()
    }
    ung_vien = co_khai | ngam_dinh
    return sorted(doc_id for doc_id in ung_vien if applies_to(db, doc_id, employee))


def serialize(db: Session, row: DocumentScope) -> dict:
    from app.modules.department.model import Department

    company = db.get(Company, row.company_id) if row.company_id else None
    department = db.get(Department, row.department_id) if row.department_id else None
    employee = db.get(Employee, row.employee_id) if row.employee_id else None

    return {
        "id": row.id,
        "document_id": row.document_id,
        "dim": row.dim,
        "mode": row.mode,
        "company_id": row.company_id,
        "company_name": company.name if company else "",
        "department_id": row.department_id,
        "department_name": department.name if department else "",
        "employee_id": row.employee_id,
        "employee_name": employee.full_name if employee else "",
        "include_children": row.include_children,
    }
