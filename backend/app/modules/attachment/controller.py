import io
import zipfile
from urllib.parse import quote

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Query,
                     Response, UploadFile)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import (get_current_user, get_perm_profile,
                           user_has_permission)
from app.core.database import get_db
from app.core.document_types import (DOC_TYPE_LABEL, DOC_TYPE_VALUES,
                                      DOCUMENT_TYPES)
from app.core.file_registry import ext_of, policy
from app.core.response import success
from app.core.scoping import apply_scope
from app.core.storage import (dated_key, delete_key, download_bytes,
                              upload_fileobj)

from .model import FileLink, StoredFile
from .service import _delete_file_if_orphan

router = APIRouter(prefix="/api/attachments", tags=["attachment"])


def _link_out(link: FileLink, f: StoredFile) -> dict:
    # id = LINK id (để DELETE tương thích FE cũ); kèm file_id + thông tin file
    return {"id": link.id, "file_id": f.id, "filename": f.filename, "url": f.url,
            "content_type": f.content_type, "size": f.size,
            "entity": link.entity, "entity_id": link.entity_id,
            "doc_type": link.doc_type, "sort_order": link.sort_order}


def _file_out(f: StoredFile) -> dict:
    return {"file_id": f.id, "filename": f.filename, "url": f.url,
            "content_type": f.content_type, "size": f.size}


def _valid_doc_type(doc_type: str) -> str:
    """Loại rỗng cho phép (tương thích upload cũ); loại lạ → 400."""
    if doc_type and doc_type not in DOC_TYPE_VALUES:
        raise HTTPException(400, f"Loại chứng từ không hợp lệ: {doc_type}")
    return doc_type


def _policy_or_400(entity: str):
    pol = policy(entity)
    if not pol:
        raise HTTPException(400, f"Loại đính kèm không hợp lệ: {entity}")
    return pol


def _check(db: Session, user, entity: str, mode: str):
    """mode='read' → cần đọc phiếu cha; mode='manage' → write HOẶC create phiếu cha."""
    parent, exts, max_mb = _policy_or_400(entity)
    if parent == "__self__":
        return exts, max_mb
    if mode == "read":
        ok = user_has_permission(db, user, parent, "read")
    else:
        ok = user_has_permission(db, user, parent, "write") or user_has_permission(db, user, parent, "create")
    if not ok:
        raise HTTPException(403, "Không có quyền thao tác đính kèm cho phần này")
    return exts, max_mb


def _store_one(db: Session, f: UploadFile, exts: set, max_mb: int, user_id: int) -> StoredFile:
    """Upload 1 file lên storage + tạo dòng tab_file. Chưa gắn link."""
    ext = ext_of(f.filename or "")
    if ext not in exts:
        raise HTTPException(400, f"Định dạng .{ext or '?'} không được phép (cho phép: {', '.join(sorted(exts))})")
    f.file.seek(0, 2); size = f.file.tell(); f.file.seek(0)
    if size > max_mb * 1024 * 1024:
        raise HTTPException(400, f"File '{f.filename}' vượt {max_mb}MB")
    # Tạo bản ghi trước (flush lấy id) để đặt key theo cấu trúc {env}/attachment/{năm}/{tháng}/{id}-tên.
    sf = StoredFile(filename=f.filename, file_key="", url="",
                    content_type=f.content_type or "", size=size,
                    created_by=user_id, updated_by=user_id)
    db.add(sf); db.flush()
    key = dated_key("attachment", f.filename or "file", sf.id)
    try:
        url = upload_fileobj(f.file, key, f.content_type or "")
    except RuntimeError as e:
        db.rollback()
        raise HTTPException(400, str(e))
    sf.file_key = key; sf.url = url
    db.commit(); db.refresh(sf)
    return sf


@router.get("")
def list_attachments(
    entity: str = Query(...), entity_id: int = Query(...),
    db: Session = Depends(get_db), user=Depends(get_current_user),
):
    _check(db, user, entity, "read")
    rows = (db.query(FileLink, StoredFile)
            .join(StoredFile, StoredFile.id == FileLink.file_id)
            .filter(FileLink.entity == entity, FileLink.entity_id == entity_id)
            .order_by(FileLink.sort_order.asc(), FileLink.id.desc()).all())
    return success([_link_out(lk, f) for lk, f in rows])


class ReorderIn(BaseModel):
    entity: str
    entity_id: int
    ordered_link_ids: list[int] = []   # thứ tự mong muốn (index = sort_order)


@router.patch("/reorder")
def reorder(data: ReorderIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Cập nhật thứ tự hiển thị các đính kèm của 1 record (dùng cho ảnh sản phẩm)."""
    _check(db, user, data.entity, "manage")
    for idx, lid in enumerate(data.ordered_link_ids):
        lk = db.get(FileLink, lid)
        if lk and lk.entity == data.entity and lk.entity_id == data.entity_id:
            lk.sort_order = idx
    db.commit()
    return success(None, "Đã cập nhật thứ tự")


@router.post("")
def upload(
    entity: str = Form(...), entity_id: int = Form(...),
    purchase_order_id: int = Form(0),
    doc_type: str = Form(""),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db), user=Depends(get_current_user),
):
    """Upload + gắn luôn (record đã có id) — tương thích FE cũ."""
    exts, max_mb = _check(db, user, entity, "manage")
    _valid_doc_type(doc_type)
    out = []
    for f in files:
        sf = _store_one(db, f, exts, max_mb, user.id)
        lk = FileLink(file_id=sf.id, entity=entity, entity_id=entity_id,
                      purchase_order_id=purchase_order_id, doc_type=doc_type,
                      created_by=user.id, updated_by=user.id)
        db.add(lk); db.commit(); db.refresh(lk)
        out.append(_link_out(lk, sf))
    return success(out, "Đã tải lên", 201)


@router.post("/upload-file")
def upload_file_only(
    entity: str = Form(...),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db), user=Depends(get_current_user),
):
    """Upload file NGAY → tạo tab_file (chưa gắn link) → trả file_id để gắn khi Lưu record."""
    exts, max_mb = _check(db, user, entity, "manage")
    out = [_file_out(_store_one(db, f, exts, max_mb, user.id)) for f in files]
    return success(out, "Đã tải lên", 201)


class RegisterIn(BaseModel):
    entity: str
    entity_id: int
    purchase_order_id: int = 0
    doc_type: str = ""
    file_ids: list[int] = []


@router.post("/register")
def register_files(data: RegisterIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Gắn các file ĐÃ upload (theo file_id) vào 1 record — khi record vừa có id."""
    _check(db, user, data.entity, "manage")
    _valid_doc_type(data.doc_type)
    out = []
    for fid in data.file_ids:
        f = db.get(StoredFile, fid)
        if not f:
            continue
        lk = FileLink(file_id=fid, entity=data.entity, entity_id=data.entity_id,
                      purchase_order_id=data.purchase_order_id, doc_type=data.doc_type,
                      created_by=user.id, updated_by=user.id)
        db.add(lk); db.commit(); db.refresh(lk)
        out.append(_link_out(lk, f))
    return success(out, "Đã gắn file", 201)


@router.get("/doc-types")
def list_doc_types(user=Depends(get_current_user)):
    """Danh sách loại chứng từ cố định cho FE render selector."""
    return success(DOCUMENT_TYPES)


def _resolve_chain(db: Session, user, entity: str, entity_id: int):
    """Resolve chuỗi chứng từ của 1 đơn → (po, groups). groups = list (entity, [ids], src, scode).
    Chuỗi: PO(+delivery) → PYC purchase_request(+quote) → PKS survey → YCKS survey_request(+line),
    resolve theo MÃ (pr_code, survey_code, sr_code); mã rỗng/không thấy → bỏ nhánh.
    Raise 400 nếu entity != purchase_order; 403 nếu thiếu quyền / ngoài scope."""
    if entity != "purchase_order":
        raise HTTPException(400, "Chuỗi chứng từ chỉ hỗ trợ đơn mua hàng")
    if not user_has_permission(db, user, "purchase_order", "read"):
        raise HTTPException(403, "Không có quyền xem chứng từ")

    # import trong hàm để tránh circular import với các module nghiệp vụ
    from app.modules.purchase_order.model import PODelivery, PurchaseOrder, PurchaseOrderItem
    from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
    from app.modules.survey.model import Survey, SurveySupplierLine, SurveyProductLine
    from app.modules.survey_request.model import (SurveyRequest,
                                                  SurveyRequestLine)

    # Chặn theo data-scope y như trang chi tiết đơn (không để xem chứng từ đơn ngoài phạm vi)
    po = apply_scope(db.query(PurchaseOrder).filter(PurchaseOrder.id == entity_id),
                     PurchaseOrder, "purchase_order", user, get_perm_profile(db, user)).first()
    if not po:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")

    def _ids(col, key_col, key_val):
        return [i for (i,) in db.query(col).filter(key_col == key_val)]

    # (entity, [entity_ids], source_label, source_code)
    groups: list[tuple[str, list[int], str, str]] = [("purchase_order", [po.id], "PO", po.code)]
    del_ids = _ids(PODelivery.id, PODelivery.po_id, po.id)
    if del_ids:
        groups.append(("delivery", del_ids, "PO", po.code))
    poi_ids = _ids(PurchaseOrderItem.id, PurchaseOrderItem.purchase_order_id, po.id)
    if poi_ids:
        groups.append(("po_item", poi_ids, "PO", po.code))
        groups.append(("purchase_order_item", poi_ids, "PO", po.code))

    if po.pr_code:
        pr = db.query(PurchaseRequest).filter(PurchaseRequest.code == po.pr_code).first()
        if pr:
            groups.append(("purchase_request", [pr.id], "PYC", pr.code))
            groups.append(("purchase_request_quote", [pr.id], "PYC", pr.code))
            pri_ids = _ids(PurchaseRequestItem.id, PurchaseRequestItem.purchase_request_id, pr.id)
            if pri_ids:
                groups.append(("purchase_request_item", pri_ids, "PYC", pr.code))

    if po.survey_code:
        sv = db.query(Survey).filter(Survey.code == po.survey_code).first()
        if sv:
            groups.append(("survey", [sv.id], "PKS", sv.code))
            ssl_ids = _ids(SurveySupplierLine.id, SurveySupplierLine.survey_id, sv.id)
            if ssl_ids:
                groups.append(("survey_supplier_line", ssl_ids, "PKS", sv.code))
                groups.append(("survey_line", ssl_ids, "PKS", sv.code))
            spl_ids = _ids(SurveyProductLine.id, SurveyProductLine.survey_id, sv.id)
            if spl_ids:
                groups.append(("survey_product_line", spl_ids, "PKS", sv.code))
                groups.append(("survey_line", spl_ids, "PKS", sv.code))
            if sv.sr_code:
                sr = db.query(SurveyRequest).filter(SurveyRequest.code == sv.sr_code).first()
                if sr:
                    groups.append(("survey_request", [sr.id], "YCKS", sr.code))
                    srl_ids = _ids(SurveyRequestLine.id, SurveyRequestLine.survey_request_id, sr.id)
                    if srl_ids:
                        groups.append(("survey_request_line", srl_ids, "YCKS", sr.code))
    return po, groups


def _chain_rows(db: Session, groups):
    """Trả list (lk, f, src, scode) — mọi FileLink+StoredFile theo groups."""
    rows = []
    for ent, ids, src, scode in groups:
        for lk, f in (db.query(FileLink, StoredFile)
                      .join(StoredFile, StoredFile.id == FileLink.file_id)
                      .filter(FileLink.entity == ent, FileLink.entity_id.in_(ids))
                      .order_by(FileLink.id.desc()).all()):
            rows.append((lk, f, src, scode))
    return rows


def _content_disposition(filename: str) -> str:
    """Content-Disposition attachment an toàn cho tên file có dấu tiếng Việt (RFC 5987)."""
    ascii_name = filename.encode("ascii", "ignore").decode() or "download"
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"


@router.get("/chain")
def chain(entity: str = Query(...), entity_id: int = Query(...),
          db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Gom TOÀN BỘ chứng từ theo chuỗi của 1 đơn mua hàng (dữ liệu cho trang chi tiết)."""
    po, groups = _resolve_chain(db, user, entity, entity_id)
    out = [{"link_id": lk.id, "source": src, "source_code": scode,
            "entity": lk.entity, "entity_id": lk.entity_id, "doc_type": lk.doc_type,
            "doc_type_label": DOC_TYPE_LABEL.get(lk.doc_type, lk.doc_type or "—"),
            "filename": f.filename, "url": f.url,
            "content_type": f.content_type, "size": f.size}
           for lk, f, src, scode in _chain_rows(db, groups)]
    return success(out)


@router.get("/chain/zip")
def chain_zip(entity: str = Query(...), entity_id: int = Query(...),
              db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Tải TOÀN BỘ chứng từ chuỗi của 1 đơn dưới dạng .zip, sắp theo thư mục nguồn/loại."""
    po, groups = _resolve_chain(db, user, entity, entity_id)
    rows = _chain_rows(db, groups)
    if not rows:
        raise HTTPException(404, "Đơn chưa có chứng từ nào để tải")

    buf = io.BytesIO()
    seen: set[str] = set()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for lk, f, src, scode in rows:
            folder = f"{src}/{lk.doc_type or 'khac'}"
            path = f"{folder}/{f.filename}"
            # chống trùng tên trong cùng thư mục
            n = 1
            while path in seen:
                stem, dot, ext = f.filename.rpartition(".")
                base = stem if dot else f.filename
                suffix = f".{ext}" if dot else ""
                path = f"{folder}/{base}_{n}{suffix}"
                n += 1
            seen.add(path)
            try:
                zf.writestr(path, download_bytes(f.file_key))
            except Exception:
                # 1 file lỗi không làm hỏng cả gói — bỏ qua file đó
                continue
    buf.seek(0)
    fname = f"chung-tu-{po.code or entity_id}.zip"
    return Response(content=buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": _content_disposition(fname)})


@router.get("/{link_id}/download")
def download_one(link_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Tải 1 file (ép attachment, đúng tên gốc). Quyền theo entity cha của link."""
    lk = db.get(FileLink, link_id)
    if not lk:
        raise HTTPException(404, "Không tìm thấy file")
    _check(db, user, lk.entity, "read")
    f = db.get(StoredFile, lk.file_id)
    if not f:
        raise HTTPException(404, "File không tồn tại")
    data = download_bytes(f.file_key)
    return Response(content=data, media_type=f.content_type or "application/octet-stream",
                    headers={"Content-Disposition": _content_disposition(f.filename)})


@router.delete("/{link_id}")
def remove(link_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    lk = db.get(FileLink, link_id)
    if not lk:
        raise HTTPException(404, "Không tìm thấy file")
    _check(db, user, lk.entity, "manage")
    fid = lk.file_id
    db.delete(lk); db.flush()
    _delete_file_if_orphan(db, fid)      # còn dùng chỗ khác thì giữ file
    db.commit()
    return success(None, "Đã xóa")
