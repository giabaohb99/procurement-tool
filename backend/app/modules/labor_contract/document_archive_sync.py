"""Cầu nối HĐLĐ -> bản LƯU TRỮ ở phân hệ Văn bản (duoc-CR-629).

Một điểm vào duy nhất, IDEMPOTENT và BEST-EFFORT: `archive_sync` chạy SAU khi nghiệp vụ HĐ đã
commit, mọi lỗi chỉ ghi log (HĐ vẫn lập / ký / xóa bình thường), và sự kiện sau tự lành.
KHÔNG đổi luật HĐLĐ nào. Luật ĐỌC bản lưu trữ nằm ở
`document/labor_contract_archive_access.py` (chỉ `labor_contract.read` trong phạm vi).

Mọi đường GHI HĐ mới (lập, sửa, sinh tệp, tải bản ký, chuyển trạng thái, xóa) PHẢI gọi
`archive_sync(db, contract_id, actor_id)` sau commit.

Ánh xạ trạng thái (ghi thẳng cột, không qua luồng duyệt; không dùng STATUS_REVOKED vì nó kéo theo
luật bãi bỏ `revoke_access`):

    Nháp -> Nháp · Đã ký -> Có hiệu lực · Đã chấm dứt -> Hết hiệu lực
    Đã hủy / HĐ xóa mềm -> Lưu trữ · hồ sơ nhân sự xóa cứng -> văn bản xóa mềm
"""
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.base_model import mark_deleted
from app.core.labor_contract_codes import (LABOR_CONTRACT_STATUS_LABELS, LABOR_CONTRACT_TYPE_LABELS,
                                           LaborContractStatus as S, LaborContractType)
from app.modules.doc_catalog.model import DocType
from app.modules.document import model as doc_model
from app.modules.document.schema import DocumentCreate
from app.modules.document.type_metadata import LABOR_CONTRACT_DOC_TYPE
from app.modules.employee.model import Employee

from . import document_archive_files
from .model import LaborContract

log = logging.getLogger("app.labor_contract")


def _fmt(d) -> str:
    return d.strftime("%d/%m/%Y") if d else "…"


def _title(lc: LaborContract, emp: Employee | None) -> str:
    #  ⚠️ Chỉ số HĐ + tên người: KHÔNG lương, phụ cấp, CCCD, số tài khoản.
    name = emp.full_name if emp else ""
    return (f"HĐLĐ {lc.contract_no or lc.code} — {name}" if name else f"HĐLĐ {lc.contract_no or lc.code}")[:500]


def _summary(lc: LaborContract) -> str:
    try:
        type_label = LABOR_CONTRACT_TYPE_LABELS[LaborContractType(int(lc.contract_type))]
    except ValueError:
        type_label = ""
    parts = [type_label, f"hiệu lực từ {_fmt(lc.start_date)} đến {_fmt(lc.end_date)}"]
    if lc.is_deleted:
        parts.append(f"Hợp đồng đã xóa ở phân hệ Nhân sự ngày {_fmt(lc.deleted_at)}")
    elif int(lc.status) == int(S.CANCELLED):
        parts.append(f"Đã hủy: {lc.terminate_reason}".rstrip(": "))
    else:
        label = LABOR_CONTRACT_STATUS_LABELS.get(S(int(lc.status)), "")
        parts.append(label)
        if int(lc.status) == int(S.TERMINATED) and lc.terminate_reason:
            parts.append(f"Lý do: {lc.terminate_reason}")
    return " · ".join(p for p in parts if p)[:500]


def _doc_status_and_dates(lc: LaborContract) -> tuple[int, object, object]:
    status = int(lc.status)
    if lc.is_deleted or status == int(S.CANCELLED):
        return doc_model.STATUS_ARCHIVED, lc.start_date, lc.end_date
    if status == int(S.SIGNED):
        return doc_model.STATUS_EFFECTIVE, lc.start_date, lc.end_date
    if status == int(S.TERMINATED):
        return doc_model.STATUS_EXPIRED, lc.start_date, lc.terminated_date or lc.end_date
    return doc_model.STATUS_DRAFT, lc.start_date, lc.end_date


def _active_doc_type(db: Session) -> DocType | None:
    return (db.query(DocType).filter(DocType.code == LABOR_CONTRACT_DOC_TYPE,
                                     DocType.is_active.is_(True)).first())


def _unlinked_marked(db: Session, lc: LaborContract, marker: str):
    """Văn bản loại HDLD, còn sống, mang dấu `marker` và CHƯA gắn với HĐ nào (kể cả HĐ khác) — tập duy nhất được nhận
    lại / dọn dư. Sửa tay `keywords` bị chặn ở PATCH; dù có lọt, văn bản đã gắn HĐ khác không bao giờ lọt vào đây."""
    linked_elsewhere = select(LaborContract.document_id).where(LaborContract.document_id > 0)
    return (db.query(doc_model.Document)
            .filter(doc_model.Document.doc_type_id.in_(select(DocType.id).where(DocType.code == LABOR_CONTRACT_DOC_TYPE)),
                    doc_model.Document.keywords == marker,
                    doc_model.Document.is_deleted == False,  # noqa: E712
                    ~doc_model.Document.id.in_(linked_elsewhere)))


def _ensure_document(db: Session, lc: LaborContract, actor_id: int) -> doc_model.Document | None:
    """Văn bản của HĐ; chưa có (hoặc đã bị xóa cứng) thì tạo. `None` nếu loại HDLD thiếu / tắt."""
    from app.modules.document import service as doc_service

    marker = f"hdld:{lc.id}"
    if lc.document_id:
        doc = db.get(doc_model.Document, lc.document_id)
        if doc is not None:
            if doc.is_deleted:
                return None
            #  Đã có văn bản chính thức: bản dư (do chạy đua) xóa mềm — CHỈ văn bản loại HDLD mà KHÔNG HĐ nào trỏ tới.
            #  `keywords` là dấu nhận văn bản mồ côi chứ không phải danh tính: văn bản đã gắn với một HĐ (kể cả HĐ khác)
            #  hay văn bản thường mang cùng chuỗi đều KHÔNG bị đụng.
            for extra in _unlinked_marked(db, lc, marker).all():
                if extra.id != doc.id:
                    mark_deleted(extra, actor_id)
            return doc
    doc_type = _active_doc_type(db)
    if doc_type is None:
        log.warning("CR-629: thiếu loại văn bản HDLD hoặc đang tắt — HĐLĐ #%s không sinh được bản lưu trữ", lc.id)
        return None
    #  Tự lành văn bản MỒ CÔI (review M1): lần tạo trước commit văn bản rồi chết trước khi ghi liên kết.
    #  Nhận lại bằng dấu `hdld:{id HĐ}` ở `keywords`; bản dư (do chạy đua) thì xóa mềm.
    orphans = _unlinked_marked(db, lc, marker).order_by(doc_model.Document.id).with_for_update().all()
    if orphans:
        keep, extras = orphans[0], orphans[1:]
        for extra in extras:
            mark_deleted(extra, actor_id)
        lc.document_id = keep.id
        db.commit()
        return keep
    emp = db.get(Employee, lc.employee_id)
    payload = DocumentCreate(
        doc_type_id=doc_type.id, company_id=lc.company_id or 0, department_id=lc.department_id or 0,
        #  KHÔNG gán người lao động làm chủ văn bản: chủ / người tạo mở đường đọc theo `is_personal`.
        owner_employee_id=0, title=_title(lc, emp), summary=_summary(lc),
        content_mode=doc_model.CONTENT_MODE_FILES,
        keywords=marker,
    )
    #  Tạo văn bản và ghi liên kết trong CÙNG MỘT giao dịch (review L1): không còn khe «văn bản chưa có liên kết».
    doc = doc_service.create_document(db, payload, actor_id, commit=False)
    lc.document_id = doc.id
    db.commit()
    return doc


def archive_sync(db: Session, contract_id: int, actor_id: int) -> int:
    """Đồng bộ văn bản lưu trữ của HĐ; trả `document_id` (0 nếu bỏ qua / lỗi). Không bao giờ ném lỗi."""
    try:
        lc = (db.query(LaborContract).filter(LaborContract.id == contract_id)
              .with_for_update().populate_existing().first())
        if lc is None:
            return 0
        doc = _ensure_document(db, lc, actor_id)
        if doc is None:
            return 0
        status, effective, expire = _doc_status_and_dates(lc)
        emp = db.get(Employee, lc.employee_id)
        doc.title, doc.summary = _title(lc, emp), _summary(lc)
        doc.status, doc.effective_date, doc.expire_date = status, effective, expire
        doc.updated_by = actor_id
        db.commit()
        document_archive_files.mirror(db, lc, doc, actor_id)
        return doc.id
    except Exception:   # why: bản lưu trữ là phụ — không để làm hỏng nghiệp vụ HĐ đã commit
        db.rollback()
        log.exception("CR-629: đồng bộ bản lưu trữ HĐLĐ #%s lỗi", contract_id)
        return 0


def soft_delete_archive_of(db: Session, lc: LaborContract, user_id: int) -> None:
    """Hồ sơ nhân sự bị xóa CỨNG -> bản lưu trữ xóa MỀM (HĐ sắp mất nên liên kết cũng mất). KHÔNG commit."""
    if not lc.document_id:
        return
    doc = db.get(doc_model.Document, lc.document_id)
    if doc is not None and not doc.is_deleted:
        mark_deleted(doc, user_id)
