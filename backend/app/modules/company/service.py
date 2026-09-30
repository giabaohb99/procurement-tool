from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.utils import generate_code

from .model import Company
from .schema import CompanyCreate, CompanyUpdate

FILTERABLE = ["code", "name", "issue_code", "tax_code", "level", "is_active"]
ENTITY = "company"


def get_company_logo_map(db: Session, company_ids: list[int]) -> dict[int, str]:
    if not company_ids:
        return {}
    from app.modules.attachment.model import FileLink, StoredFile

    rows = (
        db.query(FileLink.entity_id, StoredFile.url)
        .join(StoredFile, StoredFile.id == FileLink.file_id)
        .filter(
            FileLink.entity == "company",
            FileLink.entity_id.in_(company_ids),
            FileLink.doc_type == "logo",
        )
        .order_by(FileLink.id.desc())
        .all()
    )
    res: dict[int, str] = {}
    for cid, url in rows:
        if cid not in res:
            res[cid] = url or ""
    return res


def list_companies(db: Session, base_query, pg: dict):
    total = base_query.count()
    items = base_query.order_by(Company.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def get_company(db: Session, cid: int) -> Company:
    obj = db.get(Company, cid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy công ty")
    return obj


def _tax_key(value: str | None) -> str:
    """Khóa so trùng mã số thuế: bỏ mọi khoảng trắng, không phân biệt hoa thường.

    Cố ý GIỮ dấu gạch: ``0301234567-001`` là mã của CHI NHÁNH, khác hẳn mã công ty mẹ
    ``0301234567`` — hai pháp nhân đó được phép cùng tồn tại.
    """
    return "".join((value or "").split()).upper()


def ensure_tax_code_free(db: Session, tax_code: str | None, exclude_id: int = 0) -> None:
    """bao-CR-534: mỗi mã số thuế chỉ thuộc MỘT công ty — trùng là chặn hẳn (đại ca chốt 30/09).

    Sinh ra sau bao-CR-532: hệ từng có hai dòng «DEGO Holding» cùng mã số thuế, chứng từ chia
    đôi giữa hai dòng (~1.340 dòng trên prod) và phải viết script gộp. Hệ chỉ chặn trùng ``code``,
    mà ``code`` thì ai cũng tự đặt được, nên đó không phải cái chốt đúng.

    MST để trống thì cho qua — chưa biết mã chưa phải là trùng.
    """
    key = _tax_key(tax_code)
    if not key:
        return
    normalized = func.replace(func.upper(func.trim(func.coalesce(Company.tax_code, ""))), " ", "")
    other = (db.query(Company.name, Company.code)
             .filter(normalized == key, Company.id != exclude_id).first())
    if other:
        raise HTTPException(
            400,
            f"Mã số thuế {tax_code.strip()} đã thuộc công ty «{other.name}» (mã {other.code}). "
            "Mỗi pháp nhân chỉ có một mã số thuế — hãy sửa công ty đó thay vì tạo thêm.",
        )


def create_company(db: Session, data: CompanyCreate, user_id: int) -> Company:
    if not data.code:
        data.code = generate_code(db, Company, "CTY")
    elif db.query(Company).filter(Company.code == data.code).first():
        raise HTTPException(400, "Mã công ty đã tồn tại")
    if data.issue_code and db.query(Company).filter(Company.issue_code == data.issue_code).first():
        raise HTTPException(400, "Mã số hiệu pháp nhân đã tồn tại")
    data.tax_code = (data.tax_code or "").strip()
    ensure_tax_code_free(db, data.tax_code)
    obj = Company(**data.model_dump(), created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "create")

    #  Thư mục gốc của phân hệ Văn thư KHÔNG còn tạo ngay ở đây (rà soát
    #  24/09/2026, duoc-CR-475): gốc chỉ là chỗ chứa mặc định, sinh LAZY đúng
    #  lúc văn bản đầu tiên của pháp nhân này cần nó (xem
    #  `doc_catalog/folder_link_service._company_root_id`) — tạo trước ở đây
    #  làm gốc "tự mọc lại" theo cách khác với việc bị xóa tay.
    return obj


def update_company(db: Session, cid: int, data: CompanyUpdate, user_id: int) -> Company:
    obj = get_company(db, cid)
    values = data.model_dump(exclude_unset=True)
    #  bao-CR-531: gửi `null` cho loại hình = không đổi (cột NOT NULL, ghi None là 500).
    if values.get("company_type", 0) is None:
        values.pop("company_type")

    if "issue_code" in values:
        from app.modules.doc_catalog.issue_code_guard import ensure_company_issue_code_free
        ensure_company_issue_code_free(db, obj.issue_code, values["issue_code"])
        duplicate = (
            db.query(Company.id)
            .filter(Company.issue_code == values["issue_code"], Company.id != obj.id)
            .first()
        ) if values["issue_code"] else None
        if duplicate:
            raise HTTPException(400, "Mã số hiệu pháp nhân đã tồn tại")

    #  Chỉ kiểm khi MST THẬT SỰ đổi. Màn sửa gửi lại mọi ô mỗi lần lưu; nếu đâu đó còn sót một
    #  cặp trùng từ trước (dữ liệu cũ, nạp tay) thì chặn cả lúc MST không đổi là khóa luôn việc
    #  sửa địa chỉ hay email của cả hai công ty đó — cùng bài học chức vụ ngừng dùng (duoc-CR-320).
    if values.get("tax_code") is not None:
        values["tax_code"] = values["tax_code"].strip()
        if _tax_key(values["tax_code"]) != _tax_key(obj.tax_code):
            ensure_tax_code_free(db, values["tax_code"], exclude_id=obj.id)

    for key, value in values.items():
        setattr(obj, key, value)
    obj.updated_by = user_id
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "update")
    return obj


def delete_company(db: Session, cid: int, user_id: int):
    obj = get_company(db, cid)
    db.delete(obj)
    db.commit()
    record(db, user_id, ENTITY, cid, "delete")
