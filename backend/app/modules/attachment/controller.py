import hashlib
import io
import zipfile
from urllib.parse import quote

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Query,
                     Response, UploadFile)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.attachment_scope import ensure_in_scope, reachable_from_scoped_po
from app.core.auth import (get_current_user, get_perm_profile,
                           user_has_permission)
from app.core.database import get_db
from app.core.document_types import (DOC_TYPE_LABEL, DOC_TYPE_VALUES,
                                      DOCUMENT_TYPES)
from app.core.file_registry import ext_of, is_private, policy
from app.core.response import success
from app.core.scoping import apply_scope
from app.core.storage import (dated_key, delete_key, download_bytes,
                              upload_fileobj)
from app.modules.document.file_access_log import ACTION_TAI, ACTION_XEM

from .model import FileLink, StoredFile
from .service import _delete_file_if_orphan, attach_thumb, make_thumb_for

router = APIRouter(prefix="/api/attachments", tags=["attachment"])


def _link_out(link: FileLink, f: StoredFile) -> dict:
    # id = LINK id (để DELETE tương thích FE cũ); kèm file_id + thông tin file
    #
    #  `url` để RỖNG với entity riêng tư — đó là link đọc thẳng bucket, không qua
    #  kiểm quyền. Bên gọi phải dùng `GET /api/attachments/{id}/download`.
    #  Không xóa hẳn khóa `url` khỏi phong bì vì `frontend/` đang đóng băng đọc
    #  nó cho mọi entity khác; đổi kiểu trả về là làm vỡ màn đang chạy thật.
    return {"id": link.id, "file_id": f.id, "filename": f.filename,
            "url": "" if is_private(link.entity) else f.url,
            "thumb_url": "" if is_private(link.entity) else f.thumb_url,
            "content_type": f.content_type, "size": f.size, "sha256": f.sha256,
            "entity": link.entity, "entity_id": link.entity_id,
            "doc_type": link.doc_type, "sort_order": link.sort_order}


def _file_out(f: StoredFile) -> dict:
    return {"file_id": f.id, "filename": f.filename, "url": f.url,
            "thumb_url": f.thumb_url,
            "content_type": f.content_type, "size": f.size, "sha256": f.sha256}


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


def _check(db: Session, user, entity: str, mode: str, entity_id: int | None = None):
    """mode='read' → cần đọc phiếu cha; mode='manage' → write HOẶC create phiếu cha.

    HAI lớp, đúng khuôn `comment/service.resolve_doc` (B-08 · N-13):
      1. quyền vai trò trên entity cha — `user_has_permission`;
      2. phạm vi dữ liệu của ĐÚNG bản ghi cha — `ensure_in_scope`.

    Thiếu lớp 2 thì `contract.read` phạm vi `company` vẫn tải được đính kèm hợp
    đồng pháp nhân khác chỉ bằng cách đoán id. `entity_id=None` là lối tải tệp
    TẠM (`POST /upload-file`) — tệp chưa gắn vào bản ghi nào nên không có gì để soi.
    """
    parent, exts, max_mb = _policy_or_400(entity)
    if parent == "__self__":
        return exts, max_mb
    if mode == "read":
        ok = user_has_permission(db, user, parent, "read")
    else:
        ok = user_has_permission(db, user, parent, "write") or user_has_permission(db, user, parent, "create")
    if not ok:
        raise HTTPException(403, "Không có quyền thao tác đính kèm cho phần này")
    if entity_id is not None:
        ensure_in_scope(db, user, entity, entity_id, mode)
    return exts, max_mb


def _chan_ban_dang_duyet(db: Session, entity: str, entity_id: int):
    """Đính kèm của VĂN BẢN đang trình duyệt thì khóa (19/08/2026).

    Bộ đính kèm là một phần hồ sơ trình duyệt: thêm hay gỡ một tệp trong lúc
    người duyệt đang đọc cũng là đổi thứ họ sắp ký, y như sửa thân văn bản
    (xem `document/version_service.chan_khi_dang_duyet`).

    Kiểm ở đây chứ không ở tầng `_check` chung: `FILE_POLICY` chỉ biết entity
    cha là `document` nên nó kiểm được QUYỀN, không biết TRẠNG THÁI của đúng
    phiên bản đang bị gắn tệp. Import cục bộ để không tạo vòng import — cùng
    cách `_check_comment` làm với phân hệ bình luận.
    """
    if entity != "document_version":
        return
    from app.modules.document.version_model import DocumentVersion
    from app.modules.document.version_service import chan_khi_dang_duyet

    version = db.get(DocumentVersion, entity_id)
    if version:
        chan_khi_dang_duyet(version)


def _check_comment(db: Session, user, comment_id: int, mode: str):
    """Quyền với đính kèm của MỘT bình luận (CR-033).

    `FILE_POLICY["comment"]` để `__self__` vì bình luận treo được vào nhiều loại chứng từ,
    không có entity cha cố định. Nên ở đây phải hỏi lại đúng chứng từ mà bình luận đang treo:
    `resolve_doc` kiểm cả quyền đọc lẫn phạm vi dữ liệu, y như khi mở trang phiếu.
    Thiếu bước này thì ai đăng nhập cũng tải được file trong bình luận của phiếu người khác.
    """
    from app.modules.comment.model import Comment
    from app.modules.comment.service import resolve_doc

    c = db.get(Comment, comment_id)
    if not c:
        raise HTTPException(404, "Bình luận không tồn tại")
    resolve_doc(db, user, c.entity, c.entity_id)
    if mode == "manage" and c.created_by != user.id:
        raise HTTPException(403, "Chỉ người viết mới gỡ được đính kèm của bình luận")
    return c


def _check_forum(db: Session, user, post_id: int, mode: str):
    """Quyền với ảnh của MỘT bài diễn đàn (F1) — khuôn `_check_comment`.

    `FILE_POLICY["forum_post"]` để `__self__` vì người thường không có grant RBAC
    trên `forum_post` — ai xem được ảnh đi theo LUẬT AUDIENCE của chính bài đó
    (`forum/service.can_view`). Thiếu bước này thì ai đăng nhập cũng tải được
    ảnh trong bài phạm vi phòng ban của phòng khác chỉ bằng cách đoán link_id.
    """
    from app.modules.forum.model import ForumPost
    from app.modules.forum.service import can_view

    p = db.get(ForumPost, post_id)
    if not p:
        raise HTTPException(404, "Bài viết không tồn tại")
    if not can_view(db, user, p):
        raise HTTPException(403, "Bạn không được xem bài viết này")
    if mode == "manage" and p.created_by != user.id:
        raise HTTPException(403, "Chỉ tác giả mới gỡ được ảnh của bài viết")
    return p


def _deny_comment(entity: str):
    """Chặn các lối gắn link chung chung vào bình luận / bài diễn đàn.

    Đính kèm hai loại này CHỈ được gắn khi gửi bài (`file_ids` lúc tạo) — đi cửa
    khác thì bỏ qua kiểm quyền theo chứng từ cha, và sinh ra link treo vào bản ghi không có thật.
    """
    if entity == "comment":
        raise HTTPException(400, "Đính kèm bình luận phải gửi kèm khi tạo bình luận")
    if entity == "forum_post":
        raise HTTPException(400, "Ảnh bài viết phải gửi kèm khi đăng bài (file_ids)")


def _sha256_of(fileobj) -> str:
    """Mã băm nội dung tệp (C06). Đọc theo khối để tệp 30MB không nằm hết trong RAM.

    Trả con trỏ về đầu khi xong — ngay sau đây `upload_fileobj` đọc lại chính
    luồng này; quên `seek(0)` là đẩy lên storage một tệp rỗng.
    """
    h = hashlib.sha256()
    fileobj.seek(0)
    while chunk := fileobj.read(1024 * 1024):
        h.update(chunk)
    fileobj.seek(0)
    return h.hexdigest()


def _store_one(db: Session, f: UploadFile, exts: set, max_mb: int, user_id: int) -> StoredFile:
    """Upload 1 file lên storage + tạo dòng tab_file. Chưa gắn link."""
    ext = ext_of(f.filename or "")
    if ext not in exts:
        raise HTTPException(400, f"Định dạng .{ext or '?'} không được phép (cho phép: {', '.join(sorted(exts))})")
    f.file.seek(0, 2); size = f.file.tell(); f.file.seek(0)
    if size > max_mb * 1024 * 1024:
        raise HTTPException(400, f"File '{f.filename}' vượt {max_mb}MB")
    digest = _sha256_of(f.file)
    # Tạo bản ghi trước (flush lấy id) để đặt key theo cấu trúc {env}/attachment/{năm}/{tháng}/{id}-tên.
    sf = StoredFile(filename=f.filename, file_key="", url="",
                    content_type=f.content_type or "", size=size, sha256=digest,
                    created_by=user_id, updated_by=user_id)
    db.add(sf); db.flush()
    key = dated_key("attachment", f.filename or "file", sf.id)
    # Thumb phải sinh TRƯỚC upload bản gốc — boto3 đóng f.file khi đẩy xong.
    thumb = make_thumb_for(f.filename or "", f.file)
    try:
        url = upload_fileobj(f.file, key, f.content_type or "")
    except RuntimeError as e:
        db.rollback()
        raise HTTPException(400, str(e))
    sf.file_key = key; sf.url = url
    attach_thumb(sf, thumb)
    db.commit(); db.refresh(sf)
    return sf


@router.get("")
def list_attachments(
    entity: str = Query(...), entity_id: int = Query(...),
    db: Session = Depends(get_db), user=Depends(get_current_user),
):
    if entity == "comment":
        _check_comment(db, user, entity_id, "read")
    elif entity == "forum_post":
        _check_forum(db, user, entity_id, "read")
    else:
        _check(db, user, entity, "read", entity_id)
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
    _deny_comment(data.entity)
    _check(db, user, data.entity, "manage", data.entity_id)
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
    _deny_comment(entity)
    exts, max_mb = _check(db, user, entity, "manage", entity_id)
    _chan_ban_dang_duyet(db, entity, entity_id)
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
    _deny_comment(data.entity)
    _check(db, user, data.entity, "manage", data.entity_id)
    _chan_ban_dang_duyet(db, data.entity, data.entity_id)
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
    #  Lớp model tên là `POItem`, không phải `PurchaseOrderItem` — câu import cũ
    #  ném `ImportError` nên CẢ HAI endpoint `/chain` và `/chain/zip` trả 500 từ
    #  ngày CR-007/008 tới nay (trang «Chứng từ» của `frontend/` và nút "Tải tất
    #  cả (.zip)" của `frontend-v2` cùng chết theo). Bắt được lúc làm B-08.
    from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
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
    poi_ids = _ids(POItem.id, POItem.po_id, po.id)
    if poi_ids:
        groups.append(("po_item", poi_ids, "PO", po.code))
        groups.append(("purchase_order_item", poi_ids, "PO", po.code))

    if po.pr_code:
        pr = db.query(PurchaseRequest).filter(PurchaseRequest.code == po.pr_code).first()
        if pr:
            groups.append(("purchase_request", [pr.id], "PYC", pr.code))
            groups.append(("purchase_request_quote", [pr.id], "PYC", pr.code))
            pri_ids = _ids(PurchaseRequestItem.id, PurchaseRequestItem.pr_id, pr.id)
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
            "filename": f.filename,
            #  Chuỗi chứng từ hiện chỉ gom entity của Thu mua (không có entity
            #  riêng tư nào), nhưng vẫn chặn ở đây để sau này thêm loại mới vào
            #  chuỗi không lặng lẽ phát ra link công khai.
            "url": "" if is_private(lk.entity) else f.url,
            "content_type": f.content_type, "size": f.size, "sha256": f.sha256}
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


#  KIỂU TỆP ĐƯỢC PHÉP MỞ TẠI CHỖ.
#
#  ⚠️ Danh sách TRẮNG, không phải danh sách đen — và **SVG cố ý không có mặt**.
#  Trả tệp `inline` từ chính miền của API nghĩa là nội dung tệp chạy trong ngữ
#  cảnh của API: một tệp `.html` hay `.svg` do người dùng tải lên có thể mang mã
#  JavaScript, mở ra là nó đọc được cookie/token của miền đó. Ảnh raster và PDF
#  thì trình duyệt vẽ chứ không chạy.
KIEU_XEM_TAI_CHO = {
    "image/png", "image/jpeg", "image/gif", "image/webp", "image/bmp",
    "application/pdf",
}


@router.get("/{link_id}/view")
def view_one(link_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """XEM TẠI CHỖ — trả `inline` để nhúng thẳng vào trang, không ép tải về.

    Khác `/download` đúng hai điểm: `Content-Disposition: inline` và **chỉ nhận
    kiểu tệp an toàn** (`KIEU_XEM_TAI_CHO`). Kiểu khác vẫn phải đi đường tải về —
    thà bắt tải còn hơn mở một tệp có thể chạy mã ngay trên miền của API.
    """
    lk, f = _lay_file_co_quyen(db, user, link_id, ACTION_XEM)

    kieu = (f.content_type or "").split(";")[0].strip().lower()
    if kieu not in KIEU_XEM_TAI_CHO:
        raise HTTPException(415, "Kiểu tệp này không xem tại chỗ được — tải về để mở.")

    return Response(
        content=download_bytes(f.file_key),
        media_type=kieu,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{quote(f.filename)}",
            #  `nosniff`: cấm trình duyệt tự đoán lại kiểu tệp — đoán sai một
            #  lần là danh sách trắng ở trên thành vô nghĩa.
            "X-Content-Type-Options": "nosniff",
            #  `sandbox`: nội dung chạy như đến từ một gốc khác, không đụng được
            #  cookie/token của miền API. Chốt chặn thứ hai sau danh sách trắng.
            "Content-Security-Policy": "sandbox; default-src 'none'; img-src 'self' data:",
            #  Hạn xem hết là hết — không để bản sao nằm lại trong bộ nhớ đệm
            #  của trình duyệt rồi mở lại được sau đó.
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
        },
    )


@router.get("/{link_id}/preview")
def preview_one(link_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """XEM TẠI CHỖ tệp WORD (và .md/.html) — chuyển sang HTML rồi trả về.

    Word không có trình xem sẵn trong trình duyệt, nên khác ảnh và PDF: không
    nhúng thẳng tệp gốc được mà phải đổi sang HTML trước.

    Dùng lại **đúng bộ chuyển của chức năng nhập tệp** (`parse_document_file`) —
    bộ đó tự đọc OpenXML nên image API không phải kéo theo LibreOffice hàng trăm
    MB, và HTML ra đã đi qua `sanitize_html`. Một bộ chuyển cho cả nhập lẫn xem
    thì thứ người dùng xem trước đúng bằng thứ họ sẽ nhận nếu bấm nhập.

    PDF và ảnh KHÔNG đi đường này — chúng nhúng thẳng qua `/view`, trình duyệt
    vẽ đẹp hơn mọi bản chuyển đổi.
    """
    lk, f = _lay_file_co_quyen(db, user, link_id, ACTION_XEM)

    from app.modules.document.import_service import parse_document_file

    try:
        ket_qua = parse_document_file(f.filename, download_bytes(f.file_key))
    except ValueError as loi:
        #  415 = "hiểu yêu cầu nhưng không xử được kiểu tệp này". Câu của
        #  `parse_document_file` đã nói rõ vì sao (sai đuôi, tệp rỗng, quá lớn).
        raise HTTPException(415, str(loi))

    return success({"filename": f.filename, "html": ket_qua["content_html"]})


@router.get("/{link_id}/download")
def download_one(link_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Tải 1 file (ép attachment, đúng tên gốc). Quyền theo entity cha của link."""
    lk, f = _lay_file_co_quyen(db, user, link_id, ACTION_TAI)
    data = download_bytes(f.file_key)
    return Response(content=data, media_type=f.content_type or "application/octet-stream",
                    headers={"Content-Disposition": _content_disposition(f.filename)})


def _lay_file_co_quyen(db: Session, user, link_id: int,
                       hanh_dong: str) -> tuple[FileLink, StoredFile]:
    """Tra link + kiểm quyền + kiểm HẠN XEM. Dùng chung cho cả xem lẫn tải.

    Gom một chỗ vì hai đường phải chặn y hệt nhau: chặn ở đường xem mà quên
    đường tải thì hạn xem chỉ là một cái nút bị ẩn.
    """
    lk = db.get(FileLink, link_id)
    if not lk:
        raise HTTPException(404, "Không tìm thấy file")
    if lk.entity == "comment":
        _check_comment(db, user, lk.entity_id, "read")
    elif lk.entity == "forum_post":
        _check_forum(db, user, lk.entity_id, "read")
    else:
        try:
            _check(db, user, lk.entity, "read", lk.entity_id)
        except HTTPException as e:
            #  Đường lùi CHỈ cho lượt tải một tệp: trang «Chứng từ» liệt kê cả
            #  chuỗi PO → PYC → PKS → YCKS rồi cho bấm tải từng dòng, mà các
            #  dòng PYC/PKS/YCKS thường nằm ngoài phạm vi vai trò của người xem
            #  đơn. Không nới thêm gì — `chain/zip` đã cho tải trọn chuỗi đó cho
            #  bất kỳ ai mở được đơn; đây chỉ là tải lẻ thay vì tải cả gói.
            if e.status_code != 403 or not reachable_from_scoped_po(db, user, lk.entity, lk.entity_id):
                raise

    #  HẠN XEM xét SAU quyền: hết hạn là 403 «chỉ xem được tới ngày…», khác hẳn
    #  «không có quyền». Đặt trước phần quyền thì người vốn không được xem lại
    #  nhận đúng ngày hết hạn của một tệp họ không được biết là có.
    from app.modules.document.attachment_window import chan_neu_het_han
    chan_neu_het_han(db, lk.entity, lk.entity_id)

    f = db.get(StoredFile, lk.file_id)
    if not f:
        raise HTTPException(404, "File không tồn tại")

    _ghi_nhat_ky_neu_la_van_ban(db, lk, user, f.filename, hanh_dong)
    return lk, f


def _ghi_nhat_ky_neu_la_van_ban(db: Session, lk: FileLink, user, ten_tep: str,
                                hanh_dong: str) -> None:
    """Ghi lượt mở/tải vào nhật ký của VĂN BẢN và báo động nếu bất thường.

    Chỉ đính kèm văn bản mới ghi. Ghi cho mọi entity thì nhật ký phình lên vì
    những lượt xem chẳng ai cần tra (ảnh trong bình luận, chứng từ ĐMH), mà đúng
    thứ cần tìm lại chìm trong đó.

    ⚠️ **Nuốt lỗi.** Người dùng có quyền, tệp có thật, mà bấm vào lại nhận lỗi
    chỉ vì bảng nhật ký trục trặc là đổi một phiền toái nhỏ lấy một sự cố lớn.
    """
    from app.modules.document.attachment_window import van_ban_cua_dinh_kem
    from app.modules.document.file_access_log import ghi_va_canh_bao

    try:
        doc = van_ban_cua_dinh_kem(db, lk.entity, lk.entity_id)
        if doc is not None:
            ghi_va_canh_bao(db, doc, user, hanh_dong, ten_tep)
    except Exception:  # noqa: BLE001 — nhật ký hỏng không được chặn việc mở tệp
        import logging
        logging.getLogger(__name__).exception(
            "Không ghi được nhật ký mở tệp #%s", lk.id)


@router.delete("/{link_id}")
def remove(link_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    lk = db.get(FileLink, link_id)
    if not lk:
        raise HTTPException(404, "Không tìm thấy file")
    if lk.entity == "comment":
        _check_comment(db, user, lk.entity_id, "manage")
    elif lk.entity == "forum_post":
        _check_forum(db, user, lk.entity_id, "manage")
    else:
        _check(db, user, lk.entity, "manage", lk.entity_id)
        _chan_ban_dang_duyet(db, lk.entity, lk.entity_id)
    fid = lk.file_id
    db.delete(lk); db.flush()
    _delete_file_if_orphan(db, fid)      # còn dùng chỗ khác thì giữ file
    db.commit()
    return success(None, "Đã xóa")
