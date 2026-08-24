from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import apply_filters, apply_sort_from_request, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_perm_profile, get_scoped, scope_condition

from . import service
from .schema import CompanyCreate, CompanyOut, CompanyUpdate

router = APIRouter(prefix="/api/companies", tags=["company"])


def _format_company(c: service.Company, logo_url: str = "") -> dict:
    d = CompanyOut.model_validate(c).model_dump()
    d["logo"] = logo_url
    return d


def _cong_ty_trong_pham_vi(db, cid: int, user, action: str):
    """Lấy công ty #cid nếu nó nằm trong phạm vi của user, không thì 404 — B-07.

    Chiều phạm vi của chính bảng công ty là `id` (xem `SCOPE_FIELDS["company"]`), nên
    người đặt phạm vi `company` chỉ đụng được đúng pháp nhân của mình. Trước B-07 mọi
    endpoint ở đây đi thẳng `service.get_company(db, cid)` nên ai có `company.write`
    là sửa được hồ sơ của MỌI pháp nhân.
    """
    obj = get_scoped(db, service.Company, "company", cid, user, get_perm_profile(db, user), action)
    if not obj:
        raise HTTPException(404, "Không tìm thấy công ty")
    return obj


@router.get("")
def list_companies(
    request: Request,
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("company", "read")),
):
    from sqlalchemy.orm import joinedload
    query = apply_filters(db.query(service.Company), service.Company, request, service.FILTERABLE)
    query = query.options(joinedload(service.Company.legal_rep))
    query = apply_scope(query, service.Company, "company", user, get_perm_profile(db, user))
    query = apply_sort_from_request(query, service.Company, request)
    total, items = service.list_companies(db, query, pg)

    cids = [c.id for c in items]
    logos = service.get_company_logo_map(db, cids)

    return success({
        "total": total,
        "items": [_format_company(c, logos.get(c.id, "")) for c in items],
    })


@router.get("/{cid}")
def get_company(cid: int, db: Session = Depends(get_db), user=Depends(require("company", "read"))):
    comp = _cong_ty_trong_pham_vi(db, cid, user, "read")
    logo_map = service.get_company_logo_map(db, [cid])
    return success(_format_company(comp, logo_map.get(cid, "")))


@router.post("")
def create_company(
    data: CompanyCreate, db: Session = Depends(get_db), user=Depends(require("company", "create"))
):
    obj = service.create_company(db, data, user.id)
    return success(_format_company(obj), "Đã tạo công ty", 201)


@router.patch("/{cid}")
def update_company(
    cid: int, data: CompanyUpdate, db: Session = Depends(get_db),
    user=Depends(require("company", "write")),
):
    _cong_ty_trong_pham_vi(db, cid, user, "write")
    obj = service.update_company(db, cid, data, user.id)
    logo_map = service.get_company_logo_map(db, [cid])
    return success(_format_company(obj, logo_map.get(cid, "")), "Đã cập nhật")


@router.post("/{cid}/logo")
def update_company_logo(
    cid: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require("company", "write")),
):
    """Cập nhật logo công ty — lưu file thật vào tab_file và gắn link qua tab_file_link."""
    from app.core.audit import record as audit_record
    from app.core.file_registry import policy
    from app.modules.attachment.controller import _store_one
    from app.modules.attachment.model import FileLink

    company = _cong_ty_trong_pham_vi(db, cid, user, "write")
    _, exts, max_mb = policy("company")
    sf = _store_one(db, file, exts, max_mb, user.id)

    # Tìm link logo cũ nếu có để cập nhật file_id, hoặc tạo link mới
    existing_link = (
        db.query(FileLink)
        .filter(FileLink.entity == "company", FileLink.entity_id == cid, FileLink.doc_type == "logo")
        .first()
    )
    if existing_link:
        existing_link.file_id = sf.id
        existing_link.updated_by = user.id
        db.commit()
    else:
        lk = FileLink(
            file_id=sf.id,
            entity="company",
            entity_id=cid,
            doc_type="logo",
            created_by=user.id,
            updated_by=user.id,
        )
        db.add(lk)
        db.commit()

    audit_record(db, user.id, "company", cid, "update", f"Cập nhật logo công ty #{cid}")
    return success({"logo": sf.url}, "Đã cập nhật logo công ty thành công")


@router.delete("/{cid}")
def delete_company(cid: int, db: Session = Depends(get_db), user=Depends(require("company", "delete"))):
    _cong_ty_trong_pham_vi(db, cid, user, "delete")
    service.delete_company(db, cid, user.id)
    return success(None, "Đã xóa")


@router.delete("")
def bulk_delete_companies(ids: str, db: Session = Depends(get_db), user=Depends(require("company", "delete"))):
    id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    if not id_list:
        raise HTTPException(400, "Không có ID hợp lệ")
    from .model import Company
    # Xóa hàng loạt là đường vòng dễ quên nhất: một câu DELETE ... IN (...) không đi qua
    # bất kỳ chốt nào. Chặn phạm vi NGAY TRONG câu lệnh, rồi báo lại số thật sự xóa được
    # thay vì `len(id_list)` — trước đây báo thừa cả những dòng không có quyền đụng.
    q = db.query(Company).filter(Company.id.in_(id_list))
    cond = scope_condition(Company, "company", user, get_perm_profile(db, user), "delete")
    if cond is not None:
        q = q.filter(cond)
    xoa_duoc = [i for (i,) in q.with_entities(Company.id).all()]
    if not xoa_duoc:
        raise HTTPException(404, "Không tìm thấy công ty nào trong phạm vi của bạn")
    db.query(Company).filter(Company.id.in_(xoa_duoc)).delete(synchronize_session=False)
    db.commit()
    from app.core.audit import record
    for cid in xoa_duoc:
        record(db, user.id, service.ENTITY, cid, "delete")
    return success(None, f"Đã xóa {len(xoa_duoc)} công ty")
