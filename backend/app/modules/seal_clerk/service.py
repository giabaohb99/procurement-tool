from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record

from .model import CLERK_ACTIVE, CLERK_STATUS_LABELS, SealClerk
from .schema import SealClerkCreate, SealClerkUpdate

#  Entity dùng để ghi nhật ký (không phải khóa phân quyền — quyền quản lý dùng
#  chung `seal_type`, xem controller). Chỉ là nhãn nguồn cho `tab_audit_log`.
_AUDIT_ENTITY = "seal_clerk"


def get(db: Session, cid: int) -> SealClerk:
    obj = db.get(SealClerk, cid)
    if obj is None:
        raise HTTPException(404, "Không tìm thấy phân công văn thư")
    return obj


def _exists(db: Session, employee_id: int, company_id: int, is_head: bool) -> bool:
    return db.query(SealClerk).filter(
        SealClerk.employee_id == employee_id,
        SealClerk.company_id == company_id,
        SealClerk.is_head.is_(is_head),
    ).first() is not None


def create(db: Session, data: SealClerkCreate, user_id: int) -> SealClerk:
    company_id = 0 if data.is_head else data.company_id
    if _exists(db, data.employee_id, company_id, data.is_head):
        raise HTTPException(400, "Văn thư này đã được phân công cho công ty đó")
    obj = SealClerk(employee_id=data.employee_id, company_id=company_id,
                    is_head=data.is_head, created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    audit_record(db, user_id, _AUDIT_ENTITY, obj.id, "create", "Phân công văn thư")
    return obj


def bulk_upsert(db: Session, employee_id: int, company_ids: list[int],
                is_head: bool, user_id: int) -> int:
    """Gán một văn thư cho nhiều công ty (mỗi công ty một dòng, bỏ qua dòng đã có).
    `is_head=True` thì thêm một dòng VĂN THƯ TỔNG (company_id=0)."""
    count = 0
    for cid in dict.fromkeys(c for c in company_ids if c):  # khử trùng, giữ thứ tự
        if _exists(db, employee_id, cid, False):
            continue
        db.add(SealClerk(employee_id=employee_id, company_id=cid, is_head=False,
                         created_by=user_id, updated_by=user_id))
        count += 1
    if is_head and not _exists(db, employee_id, 0, True):
        db.add(SealClerk(employee_id=employee_id, company_id=0, is_head=True,
                         created_by=user_id, updated_by=user_id))
        count += 1
    if count:
        db.commit()
        audit_record(db, user_id, _AUDIT_ENTITY, employee_id, "create",
                     f"Phân công văn thư cho {count} công ty/vai trò")
    return count


def update(db: Session, cid: int, data: SealClerkUpdate, user_id: int) -> SealClerk:
    obj = get(db, cid)
    if data.is_head is not None:
        obj.is_head = data.is_head
        if data.is_head:
            obj.company_id = 0
    if data.company_id is not None and not obj.is_head:
        obj.company_id = data.company_id
    obj.updated_by = user_id
    db.commit()
    db.refresh(obj)
    audit_record(db, user_id, _AUDIT_ENTITY, obj.id, "write", "Sửa phân công văn thư")
    return obj


#  Ưu tiên "DEGO HOLDING" đứng đầu danh sách công ty của mỗi văn thư (khớp theo tên).
_HOLDING_KW = "DEGO HOLDING"


def _order_companies(companies: list[dict]) -> list[dict]:
    return sorted(companies,
                  key=lambda c: (0 if _HOLDING_KW in (c["name"] or "").upper() else 1,
                                 (c["name"] or "").lower()))


def list_grouped(db: Session, search: str = "", offset: int = 0, limit: int = 50,
                 sort_by: str = "employee_name", sort_dir: str = "asc",
                 company_id: int = 0) -> tuple[int, list[dict]]:
    """Danh sách GỘP THEO VĂN THƯ — mỗi người MỘT dòng (kèm công ty + logo + cờ tổng).

    Bảng phân công nhỏ (dữ liệu cấu hình) nên gộp/tìm/lọc/sắp/phân trang trong Python
    cho gọn. `company_id` > 0: chỉ giữ văn thư phụ trách công ty đó.
    """
    from app.modules.company.model import Company
    from app.modules.company.service import get_company_logo_map
    from app.modules.employee.model import Employee

    grouped: dict[int, dict] = {}
    for row in db.query(SealClerk).all():
        g = grouped.setdefault(row.employee_id, {
            "employee_id": row.employee_id, "anchor_id": row.id,
            "company_ids": [], "is_head": False, "status": row.status})
        g["anchor_id"] = min(g["anchor_id"], row.id)
        #  Cả nhóm bình thường cùng một trạng thái. Nếu lệch (dữ liệu cũ), "Đang hoạt
        #  động thắng": chỉ cần MỘT dòng còn hoạt động là văn thư vẫn nhận phiếu → min
        #  (ACTIVE=1 < PAUSED=2).
        g["status"] = min(g["status"], row.status)
        if row.is_head:
            g["is_head"] = True
        elif row.company_id:
            g["company_ids"].append(row.company_id)

    if company_id:  # chỉ giữ văn thư phụ trách công ty được lọc
        grouped = {eid: g for eid, g in grouped.items() if company_id in g["company_ids"]}

    emp_ids = list(grouped)
    emps = ({e.id: e for e in db.query(Employee).filter(Employee.id.in_(emp_ids)).all()}
            if emp_ids else {})
    all_cids = {c for g in grouped.values() for c in g["company_ids"]}
    names = (dict(db.query(Company.id, Company.name).filter(Company.id.in_(all_cids)).all())
             if all_cids else {})
    logos = get_company_logo_map(db, list(all_cids)) if all_cids else {}

    items = []
    for g in grouped.values():
        emp = emps.get(g["employee_id"])
        companies = _order_companies([
            {"id": c, "name": names.get(c, f"#{c}"), "logo": logos.get(c, "")}
            for c in g["company_ids"]])
        items.append({
            "employee_id": g["employee_id"],
            "anchor_id": g["anchor_id"],
            "employee_name": emp.full_name if emp else None,
            "employee_code": emp.code if emp else None,
            "company_count": len(g["company_ids"]),
            "companies": companies,
            "is_head": g["is_head"],
            "status": g["status"],
            "status_label": CLERK_STATUS_LABELS.get(g["status"], str(g["status"])),
        })

    kw = (search or "").strip().lower()
    if kw:
        items = [it for it in items
                 if kw in (it["employee_name"] or "").lower()
                 or kw in (it["employee_code"] or "").lower()
                 or any(kw in (c["name"] or "").lower() for c in it["companies"])]

    reverse = sort_dir == "desc"
    if sort_by == "company_count":
        items.sort(key=lambda it: it["company_count"], reverse=reverse)
    else:
        items.sort(key=lambda it: (it["employee_name"] or "").lower(), reverse=reverse)

    return len(items), items[offset:offset + limit]


def list_for_employee(db: Session, employee_id: int) -> dict:
    """Gộp phân công của MỘT văn thư: danh sách công ty + có phải văn thư tổng."""
    rows = db.query(SealClerk).filter(SealClerk.employee_id == employee_id).all()
    #  "Đang hoạt động thắng": min (ACTIVE=1 < PAUSED=2); rỗng thì mặc định hoạt động.
    status = min((r.status for r in rows), default=CLERK_ACTIVE)
    return {
        "employee_id": employee_id,
        "company_ids": [r.company_id for r in rows if not r.is_head and r.company_id],
        "is_head": any(r.is_head for r in rows),
        "status": status,
    }


def sync(db: Session, employee_id: int, company_ids: list[int], is_head: bool,
         user_id: int, anchor_id: int = 0, status: int | None = None) -> int:
    """Đặt LẠI toàn bộ phân công của một văn thư = đúng `company_ids` (+ cờ tổng).
    Thêm công ty mới, xóa công ty bị bỏ chọn, bật/tắt văn thư tổng.

    `status` là của TỪNG VĂN THƯ nên áp cho MỌI dòng của người đó: `None` = giữ
    nguyên (để công tắc "Đa pháp nhân" ở danh sách không lỡ bật lại), có giá trị =
    đặt cả nhóm sang trạng thái đó. Dòng mới lấy `status` (mặc định Đang hoạt động)."""
    target = list(dict.fromkeys(c for c in company_ids if c))
    new_row_status = status if status is not None else CLERK_ACTIVE
    rows = db.query(SealClerk).filter(SealClerk.employee_id == employee_id).all()
    non_head = {r.company_id: r for r in rows if not r.is_head}
    head_rows = [r for r in rows if r.is_head]
    changed = 0

    for cid in target:
        if cid not in non_head:
            db.add(SealClerk(employee_id=employee_id, company_id=cid, is_head=False,
                             status=new_row_status, created_by=user_id, updated_by=user_id))
            changed += 1
    for cid, row in non_head.items():
        if cid not in target:
            db.delete(row)
            changed += 1
    if is_head and not head_rows:
        db.add(SealClerk(employee_id=employee_id, company_id=0, is_head=True,
                         status=new_row_status, created_by=user_id, updated_by=user_id))
        changed += 1
    elif not is_head and head_rows:
        for row in head_rows:
            db.delete(row)
            changed += 1

    #  Trạng thái áp cho MỌI dòng CÒN LẠI của văn thư (giữ đồng bộ một trạng thái).
    if status is not None:
        for row in rows:
            stays = (not row.is_head and row.company_id in target) or (row.is_head and is_head)
            if stays and row.status != status:
                row.status = status
                row.updated_by = user_id
                changed += 1

    if changed:
        db.commit()
        note = f"Cập nhật phân công văn thư — {len(target)} công ty"
        if is_head:
            note += " + văn thư tổng"
        if status is not None:
            note += f" · {CLERK_STATUS_LABELS.get(status, status)}"
        audit_record(db, user_id, _AUDIT_ENTITY, anchor_id or employee_id, "write", note)
    return changed


def delete(db: Session, cid: int, user_id: int) -> None:
    obj = get(db, cid)
    db.delete(obj)
    db.commit()
    audit_record(db, user_id, _AUDIT_ENTITY, cid, "delete", "Xóa phân công văn thư")
