"""API VĂN BẢN.

Mỗi endpoint đi qua BA lớp, thiếu lớp nào cũng là một lỗ:

1. `require("document", ...)` — vai trò có được đụng vào loại việc này không;
2. `documents_query()` — ép `origin = 1`, đừng để văn bản pháp luật ngoài lọt vào
   danh sách của phân hệ;
3. `access_service` — phạm vi vai trò **cộng** chia sẻ đích danh **trừ** cấm đích
   danh, tính cho từng văn bản.

Lớp 3 phải áp ở **cả hai chỗ**: `visible_condition()` cho danh sách và
`ensure_can()` cho từng bản ghi. Lọc danh sách mà quên kiểm chi tiết thì gõ
thẳng id lên URL là mở được.

⚠️ Lớp kiểm **mức mật** (`secrecy_level`) vẫn CHƯA có — nó là P5 (cấp mức mật cho
người, chia đặc cách, trình xem Tuyệt mật). Cột đã ghi xuống từ phase này nhưng
chưa ai chặn theo nó, nên chừng nào P5 chưa xong thì không đưa văn bản mật thật
vào hệ thống.
"""
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import get_current_user, get_perm_profile, require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success

from . import access_service, import_service, numbering, serializer, service, version_service
from .model import Document
from .query import documents_query
from .schema import (AccessGrant, AccessRevokeIn, DocumentCreate, DocumentUpdate,
                     RejectIn, VersionContentUpdate, VersionCreate)
from .service import doc_type_or_400

router = APIRouter(prefix="/api/documents", tags=["document"])

FILTERABLE = ["doc_type_id", "company_id", "department_id", "book_id", "status",
              "secrecy_level", "urgency", "owner_employee_id"]


def _load(db: Session, document_id: int, user, action: str = "read") -> Document:
    """Lấy văn bản và kiểm quyền TRÊN CHÍNH nó.

    Mọi endpoint làm việc với một văn bản đều phải qua đây. `ensure_can` trả 404
    (không phải 403) khi không được đọc: nói "có văn bản này nhưng anh không được
    xem" cũng đã là lộ thông tin.
    """
    doc = service.get_or_404(db, document_id)
    access_service.ensure_can(db, doc, user, get_perm_profile(db, user), action)
    return doc


@router.get("")
def list_documents(
    request: Request,
    q: str = Query("", description="Tìm theo tiêu đề, số hiệu, SỐ HIỆU CŨ, từ khóa"),
    effective_from: date | None = Query(None, description="Hiệu lực từ ngày"),
    effective_to: date | None = Query(None, description="Hiệu lực đến ngày"),
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    profile = get_perm_profile(db, user)
    query = apply_filters(documents_query(db), Document, request, FILTERABLE)
    #  Phạm vi vai trò + văn bản được chia đích danh − văn bản bị cấm đích danh.
    visible = access_service.visible_condition(user, profile)
    if visible is not None:
        query = query.filter(visible)

    if q:
        needle = f"%{q.strip()}%"
        #  Tìm chấp nhận cả SỐ HIỆU CŨ của bản giấy (C12): người dùng lâu năm
        #  vẫn tra theo số họ đã thuộc, bắt họ học số mới là bắt sai người.
        query = query.filter(or_(
            Document.title.like(needle),
            Document.doc_code.like(needle),
            Document.issue_number.like(needle),
            Document.legacy_code.like(needle),
            Document.keywords.like(needle),
        ))
    if effective_from:
        query = query.filter(Document.effective_date >= effective_from)
    if effective_to:
        query = query.filter(Document.effective_date <= effective_to)

    total = query.count()
    #  Lọc `?book_id=` là đường mà màn SỔ VĂN BẢN dùng để liệt kê văn bản trong
    #  một quyển; sổ đọc theo số vào sổ tăng dần, khác danh sách chung (mới nhất
    #  trước) nên để màn đó tự sắp lại nếu cần.
    items = (query.order_by(Document.id.desc())
             .offset(pg["offset"]).limit(pg["limit"]).all())
    return success({"total": total, "items": serializer.serialize_many(db, items)})


@router.get("/suggestions")
def list_suggestions(
    doc_type_id: int,
    department_id: int | None = None,
    company_id: int | None = None,
    exclude_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """Văn bản cùng loại cùng phòng đang hiệu lực — hiện ngay trong form soạn (B05)."""
    return success(service.suggestions(db, doc_type_id, department_id, company_id, exclude_id))


@router.get("/number-preview")
def preview_number(
    doc_type_id: int,
    company_id: int,
    department_id: int | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """Số hiệu SẼ cấp — chỉ để xem trước (D08), **không chiếm số**.

    Không có endpoint nào "xin một số" đứng riêng: số phải cấp trong cùng
    transaction với việc ghi bản ghi mang số đó.
    """
    doc_type = doc_type_or_400(db, doc_type_id)
    year = year or date.today().year
    return success({
        "preview": numbering.peek(db, doc_type, company_id, department_id, year),
        "number_when": doc_type.number_when,
        "id_scheme": doc_type.id_scheme,
    })


@router.post("/import/parse")
def parse_import_file(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    """Đọc tệp trên máy người dùng, trả HTML để chèn tại con trỏ.

    Đây là thao tác chuyển đổi không ghi dữ liệu, nhưng vẫn yêu cầu đăng nhập để
    tránh biến API thành dịch vụ xử lý tệp công cộng.
    """
    del user
    filename = (file.filename or "tai-lieu").rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    raw = file.file.read(import_service.MAX_FILE_SIZE + 1)
    try:
        parsed = import_service.parse_document_file(filename, raw)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return success(parsed, "Đã đọc tệp")


@router.get("/{document_id}")
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    #  Tới ngày hiệu lực thì đổi bản đang dùng ngay tại đây — hệ chưa có bộ chạy
    #  định kỳ, xem `service.activate_due_versions`.
    service.activate_due_versions(db, document_id)
    doc = _load(db, document_id, user)
    return success(serializer.serialize(db, doc))


@router.post("")
def create_document(
    data: DocumentCreate,
    db: Session = Depends(get_db),
    user=Depends(require("document", "create")),
):
    doc = service.create_document(db, data, user.id)
    record(db, user.id, "document", doc.id, "create", f"Tạo văn bản {doc.title}")
    return success(serializer.serialize(db, doc), "Đã tạo văn bản", 201)


@router.patch("/{document_id}")
def update_document(
    document_id: int,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
    user=Depends(require("document", "write")),
):
    doc = _load(db, document_id, user, "write")
    doc = service.update_document(db, doc, data, user.id)
    record(db, user.id, "document", doc.id, "update")
    return success(serializer.serialize(db, doc), "Đã cập nhật")


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "delete")),
):
    doc = _load(db, document_id, user, "delete")
    service.delete_document(db, doc)
    record(db, user.id, "document", document_id, "delete")
    return success(None, "Đã xóa văn bản")


# ── Luồng duyệt một bước (TẠM — P3 thay bằng bộ máy chung) ───────────────────
@router.post("/{document_id}/submit")
def submit_document(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "write")),
):
    doc = _load(db, document_id, user, "write")
    doc = service.submit(db, doc, user.id)
    record(db, user.id, "document", doc.id, "update", "Gửi duyệt")
    return success(serializer.serialize(db, doc), "Đã gửi duyệt")


@router.post("/{document_id}/approve")
def approve_document(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "approve")),
):
    doc = _load(db, document_id, user)
    doc = service.approve(db, doc, user.id)
    record(db, user.id, "document", doc.id, "approve",
           f"Ban hành {doc.doc_code or doc.issue_number}")
    return success(serializer.serialize(db, doc), "Đã duyệt và ban hành")


@router.post("/{document_id}/reject")
def reject_document(
    document_id: int,
    data: RejectIn,
    db: Session = Depends(get_db),
    user=Depends(require("document", "approve")),
):
    doc = _load(db, document_id, user)
    doc = service.reject(db, doc, data.reason, user.id)
    record(db, user.id, "document", doc.id, "update", f"Trả lại: {data.reason}")
    return success(serializer.serialize(db, doc), "Đã trả lại bản nháp")


# ── Phiên bản ────────────────────────────────────────────────────────────────
@router.get("/{document_id}/versions")
def list_versions(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    doc = _load(db, document_id, user)
    versions = version_service.list_versions(db, doc)
    return success([serializer.serialize_version(db, v, doc) for v in versions])


@router.get("/{document_id}/versions/{version_id}")
def get_version(
    document_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """Kèm nội dung — chỉ trang soạn thảo gọi, danh sách phiên bản thì không."""
    doc = _load(db, document_id, user)
    version = version_service.get_or_404(db, doc, version_id)
    return success(serializer.serialize_version(db, version, doc, with_content=True))


@router.post("/{document_id}/versions")
def create_version(
    document_id: int,
    data: VersionCreate,
    db: Session = Depends(get_db),
    user=Depends(require("document", "write")),
):
    doc = _load(db, document_id, user, "write")
    version = version_service.open_new_version(db, doc, data, user.id)
    record(db, user.id, "document", doc.id, "update",
           f"Mở phiên bản {version.version_no}: {data.change_summary}")
    return success(serializer.serialize_version(db, version, doc, with_content=True),
                   f"Đã mở phiên bản {version.version_no}", 201)


@router.patch("/{document_id}/versions/{version_id}")
def update_version(
    document_id: int,
    version_id: int,
    data: VersionContentUpdate,
    db: Session = Depends(get_db),
    user=Depends(require("document", "write")),
):
    """Ghi nội dung bản nháp. Bản đã duyệt → 409, kể cả gọi thẳng không qua UI."""
    doc = _load(db, document_id, user, "write")
    version = version_service.get_or_404(db, doc, version_id)
    version = version_service.save_content(db, version, data, user.id)
    return success(serializer.serialize_version(db, version, doc))


# ── Quyền trên từng văn bản ──────────────────────────────────────────────────
@router.get("/{document_id}/access")
def list_access(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """Bảng chia sẻ: đang chia cho ai, hết hạn khi nào, ai đã bị thu hồi.

    Trả **cả dòng đã thu hồi** — thu hồi là đánh dấu chứ không xóa (G19, G20),
    và bảng phải đọc được lịch sử thì mới trả lời được "hồi tháng 7 ai đọc được".
    """
    doc = _load(db, document_id, user)
    return success(serializer.serialize_access(db, access_service.list_access(db, doc)))


@router.post("/{document_id}/access")
def grant_access(
    document_id: int,
    data: AccessGrant,
    db: Session = Depends(get_db),
    user=Depends(require("document", "write")),
):
    """Chia quyền (hoặc cấm) cho một người / phòng ban / pháp nhân / vai trò.

    Cần quyền **sửa** trên chính văn bản đó: ai sửa được văn bản thì mới quyết
    được ai đọc nó.
    """
    doc = _load(db, document_id, user, "write")
    row = access_service.grant(db, doc, data, user.id)
    record(db, user.id, "document", doc.id, "update",
           f"Chia quyền cho đối tượng {row.subject_kind}:{row.subject_id}")
    return success(serializer.serialize_access(db, [row])[0], "Đã lưu quyền truy cập", 201)


@router.post("/{document_id}/access/{access_id}/revoke")
def revoke_access(
    document_id: int,
    access_id: int,
    data: AccessRevokeIn,
    db: Session = Depends(get_db),
    user=Depends(require("document", "write")),
):
    doc = _load(db, document_id, user, "write")
    row = access_service.revoke(db, doc, access_id, data.reason, user.id)
    record(db, user.id, "document", doc.id, "update",
           f"Thu hồi quyền của đối tượng {row.subject_kind}:{row.subject_id}")
    return success(serializer.serialize_access(db, [row])[0], "Đã thu hồi")


@router.get("/{document_id}/permissions")
def my_permissions(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """Tôi được làm gì trên ĐÚNG văn bản này — để giao diện ẩn nút cho đỡ vướng.

    ⚠️ Chỉ là tiện lợi. Chốt chặn thật nằm ở `ensure_can` trong từng endpoint;
    đừng bao giờ coi kết quả này là bảo mật.
    """
    doc = _load(db, document_id, user)
    profile = get_perm_profile(db, user)
    return success({
        action: access_service.can(db, doc, user, profile, action)
        for action in ("read", "write", "delete")
    })


@router.post("/maintenance/activate-due")
def activate_due(
    db: Session = Depends(get_db),
    user=Depends(require("document", "approve")),
):
    """Chuyển các phiên bản đã duyệt sang hiệu lực khi tới ngày, cho TOÀN bảng.

    Có để gọi tay / gắn cron ngoài; đường đọc chi tiết văn bản cũng tự chạy phần
    của riêng nó nên không gọi endpoint này thì hệ vẫn đúng, chỉ là danh sách
    hiển thị chậm một nhịp cho tới khi ai đó mở văn bản ra xem.
    """
    changed = service.activate_due_versions(db)
    return success({"changed": changed}, f"Đã chuyển {changed} phiên bản sang hiệu lực")
