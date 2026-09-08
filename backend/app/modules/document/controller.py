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

Ngoại lệ duy nhất của lớp 1: bốn endpoint ĐỌC MỘT văn bản dùng `doc_reader` —
xem ghi chú tại chỗ.

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

from . import (access_service, approval_bridge, duplicate_service, import_service, numbering,
               serializer, service, version_service)
from .model import ORIGIN_INTERNAL, Document
from .version_model import DocumentVersion
from .query import (hide_private_copies_with_visible_source, count_private_copies,
                    documents_query)
from .model import APPLY_MODE_LABELS, STATUS_PENDING_ISSUE
from .schema import (AccessGrant, AccessRevokeIn, ApproveIn, DocumentCreate, DocumentUpdate,
                     ReviewedIn,
                     ManualIssueNumberUpdate, RejectIn, VersionContentUpdate,
                     VersionCreate)
from .service import doc_type_or_400

router = APIRouter(prefix="/api/documents", tags=["document"])

#  Trường mà BỘ LỌC NÂNG CAO của danh sách được phép hỏi. Tên nào không có ở
#  đây thì backend **lặng lẽ bỏ qua** điều kiện đó — nên thêm ô lọc ở giao diện
#  mà quên chỗ này là bộ lọc chạy nhưng không lọc gì.
#
#  Mở rộng ngày 19/08/2026: trước chỉ có mấy khóa tham chiếu, nên màn danh sách
#  chỉ lọc được theo loại và trạng thái. Bộ này thêm đúng những trường người
#  dùng tra thật: trích yếu, các kiểu số hiệu, từ khóa, ngày hiệu lực, năm ban
#  hành và cờ "cần rà soát".
#
#  ⚠️ Whitelist này KHÔNG phải hàng rào quyền: lọc xong vẫn đi qua
#  `access_service.visible_condition`, nên thêm trường vào đây không làm lộ
#  thêm dòng nào.
FILTERABLE = ["doc_type_id", "company_id", "department_id", "book_id", "status",
              "secrecy_level", "urgency", "owner_employee_id",
              "title", "doc_code", "issue_number", "legacy_code", "keywords",
              "storage_location",
              "effective_date", "expire_date", "issue_year", "needs_review",
              #  Hỏi thẳng các BẢN RIÊNG của một bản gốc — đường mà bảng danh
              #  sách dùng khi người dùng bung một dòng ra.
              "source_document_id"]


def doc_reader(user=Depends(get_current_user)):
    """Cổng vào của bốn endpoint ĐỌC MỘT văn bản — chỉ cần đăng nhập.

    Ở đây cố ý BỎ lớp 1 (`require("document", "read")`) và giao toàn bộ việc
    gác cho lớp 3 (`_load` → `ensure_can`), vì lớp 1 hỏi sai câu: nó hỏi "vai
    trò của anh có được đụng vào phân hệ Văn bản không", trong khi người duyệt
    trong luồng thường **không có vai trò nào** ở phân hệ này — bộ máy duyệt
    chỉ hỏi "anh có việc ở phiếu này không".

    Hệ quả của việc hỏi sai câu, đã bắt được thật: người duyệt bấm từ «Việc của
    tôi» sang văn bản thì nhận 404, đành ký mù theo mỗi cái tiêu đề trên dòng
    việc. `access_service.can()` nay mở đúng khe đó và CHỈ mở quyền đọc.

    Không nới thêm endpoint nào khác: danh sách, tìm kiếm, sửa, xóa, ban hành
    vẫn giữ nguyên lớp 1.
    """
    return user


def _load(db: Session, document_id: int, user, action: str = "read") -> Document:
    """Lấy văn bản và kiểm quyền TRÊN CHÍNH nó.

    Mọi endpoint làm việc với một văn bản đều phải qua đây. `ensure_can` trả 404
    (không phải 403) khi không được đọc: nói "có văn bản này nhưng anh không được
    xem" cũng đã là lộ thông tin.
    """
    doc = service.get_or_404(db, document_id)
    access_service.ensure_can(db, doc, user, get_perm_profile(db, user), action)
    return doc


def _list_query(request: Request, db: Session, user, profile: dict,
                     q: str = "", effective_from: date | None = None,
                     effective_to: date | None = None):
    """Truy vấn danh sách văn bản — **một luật lọc duy nhất** cho cả màn danh
    sách lẫn bản xuất Excel.

    Tách ra vì hai đường mà chép luật hai lần thì sớm muộn cũng lệch nhau, và
    lệch ở đây nghĩa là file Excel chứa văn bản người xuất không được phép xem.
    """
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
            #  NƠI LƯU TRỮ CỨNG: gõ "Tủ A2" phải ra mọi văn bản đang nằm trong
            #  tủ đó — đúng lý do cột này tồn tại (đi tìm lại bản giấy).
            Document.storage_location.like(needle),
        ))
    if effective_from:
        query = query.filter(Document.effective_date >= effective_from)
    if effective_to:
        query = query.filter(Document.effective_date <= effective_to)

    #  BẢN RIÊNG nằm DƯỚI bản gốc, không đứng ngang hàng: một văn bản clone cho
    #  mười hai pháp nhân sẽ thành mười ba dòng gần như giống hệt nhau, đọc
    #  danh sách không ra nổi có bao nhiêu văn bản thật.
    #
    #  Chỉ giấu khi người đang xem THẤY ĐƯỢC bản gốc. Người ở pháp nhân con
    #  không xem được bản gốc thì bản riêng của họ chính là văn bản của họ —
    #  giấu đi là danh sách của họ trống trơn.
    #  Hỏi đích danh bản riêng của một bản gốc thì KHÔNG gom nữa — người dùng
    #  vừa bung đúng dòng đó ra, gom lại là trả về rỗng.
    if not request.query_params.get("source_document_id"):
        query = hide_private_copies_with_visible_source(query)

    return query, visible


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
    query, visible = _list_query(request, db, user, profile, q,
                                      effective_from, effective_to)

    total = query.count()
    #  Lọc `?book_id=` là đường mà màn SỔ VĂN BẢN dùng để liệt kê văn bản trong
    #  một quyển; sổ đọc theo số vào sổ tăng dần, khác danh sách chung (mới nhất
    #  trước) nên để màn đó tự sắp lại nếu cần.
    items = (query.order_by(Document.id.desc())
             .offset(pg["offset"]).limit(pg["limit"]).all())
    rows = serializer.serialize_many(db, items)

    #  Đếm trên một truy vấn CHỈ lọc quyền — không kèm bộ lọc/tìm kiếm của
    #  danh sách, nếu không lọc theo trạng thái là số bản riêng tụt theo.
    count_query = documents_query(db)
    if visible is not None:
        count_query = count_query.filter(visible)
    count = count_private_copies(count_query, [doc.id for doc in items])
    for row in rows:
        row["clone_count"] = count.get(row["id"], 0)

    return success({"total": total, "items": rows})


@router.get("/suggestions")
def list_suggestions(
    doc_type_id: int,
    department_id: int | None = None,
    company_id: int | None = None,
    exclude_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """Văn bản cùng loại cùng phòng đang hiệu lực — hiện ngay trong form soạn (B05).

    Lọc theo đúng quyền xem của người đang đăng nhập (xem `service.suggestions`).
    """
    return success(service.suggestions(db, doc_type_id, department_id, company_id,
                                       exclude_id, user=user,
                                       profile=get_perm_profile(db, user)))


@router.get("/storage-locations")
def list_storage_locations(
    q: str = Query("", description="Lọc gợi ý theo chuỗi đang gõ"),
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """Các NƠI LƯU TRỮ CỨNG đã từng nhập — gợi ý cho ô nhập ở form văn bản.

    Ô lưu trữ cứng là chữ tự do (mỗi pháp nhân sắp kho một kiểu), nên thứ giữ
    cho dữ liệu đỡ mỗi người một kiểu chính là danh sách này: gõ "Tủ" là thấy
    ngay "Tủ A2 · Kệ 3" người khác đã dùng, thay vì tự đặt "tu a2" viết thường.

    Chỉ đọc trên những văn bản người này XEM ĐƯỢC: tên ngăn tủ của phòng nhân
    sự cũng là một mẩu thông tin, không phát cho cả công ty.
    """
    query = (
        db.query(Document.storage_location)
        .filter(Document.origin == ORIGIN_INTERNAL, Document.storage_location != "")
    )
    visible = access_service.visible_condition(user, get_perm_profile(db, user))
    if visible is not None:
        query = query.filter(visible)
    if q.strip():
        query = query.filter(Document.storage_location.like(f"%{q.strip()}%"))

    #  `distinct()` ở tầng SQL rồi vẫn gom lại bằng `dict.fromkeys`: MySQL so
    #  chuỗi không phân biệt hoa thường nên hai cách gõ khác nhau vẫn ra hai
    #  dòng, mà gợi ý thì chỉ cần mỗi chỗ một dòng.
    rows = [row[0] for row in query.distinct().limit(200).all()]
    return success(sorted(dict.fromkeys(rows))[:50])


@router.get("/number-preview")
def preview_number(
    doc_type_id: int,
    company_id: int,
    department_id: int | None = None,
    book_id: int | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """Số hiệu SẼ cấp — chỉ để xem trước (D08), **không chiếm số**.

    Không có endpoint nào "xin một số" đứng riêng: số phải cấp trong cùng
    transaction với việc ghi bản ghi mang số đó.
    """
    doc_type = doc_type_or_400(db, doc_type_id)
    today = date.today()
    when = date(year, 1, 1) if year and year != today.year else today
    return success({
        "preview": numbering.peek(db, doc_type, company_id, department_id, when, book_id),
        "number_when": doc_type.number_when,
        "id_scheme": doc_type.id_scheme,
    })


@router.get("/export/xlsx")
def export_xlsx(
    request: Request,
    ids: str = "",
    cols: str = "",
    q: str = Query(""),
    effective_from: date | None = Query(None),
    effective_to: date | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(require("document", "export")),
):
    """Xuất danh sách văn bản ra Excel.

    `ids` = các văn bản người dùng tự tick; bỏ trống thì xuất theo **đúng bộ lọc
    đang đặt trên màn hình**. `cols` = các cột đang hiện, để file ra giống hệt
    cái người dùng đang nhìn.

    ⚠️ Khai TRƯỚC route `/{document_id}` kẻo "export" bị đọc thành id văn bản.
    Lọc quyền dùng chung `_danh_sach_query` với màn danh sách — không viết lại.
    """
    from app.core.export_xlsx import (check_row_limit, parse_ids, pick_columns,
                                      xlsx_response)

    from . import export as ex

    profile = get_perm_profile(db, user)
    query, _ = _list_query(request, db, user, profile, q,
                                effective_from, effective_to)
    id_list = parse_ids(ids)
    if id_list:
        query = query.filter(Document.id.in_(id_list))

    docs = query.order_by(Document.id.desc()).all()
    check_row_limit(len(docs))
    rows = ex.build_rows(db, serializer.serialize_many(db, docs))
    return xlsx_response(ex.FILE_NAME, pick_columns(ex.COLUMNS, cols), rows,
                         ex.SHEET_TITLE)


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
    user=Depends(doc_reader),
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


@router.post("/{document_id}/copy")
def duplicate_document(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "create")),
):
    """Tạo bản nháp độc lập cùng pháp nhân để dựng nhanh dữ liệu thử.

    Đây KHÔNG phải API clone xuống pháp nhân con ở ``clone_controller``.
    """
    source = _load(db, document_id, user)
    copied = duplicate_service.duplicate(db, source, user.id)
    record(db, user.id, "document", copied.id, "create",
           f"Sao chép từ văn bản #{source.id}: {source.title}")
    return success(serializer.serialize(db, copied), "Đã tạo bản sao văn bản", 201)


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


@router.patch("/{document_id}/issue-number")
def update_issue_number(
    document_id: int,
    data: ManualIssueNumberUpdate,
    db: Session = Depends(get_db),
    user=Depends(require("document", "write")),
):
    """Văn thư sửa số khi chính quy tắc đã bật quyền, luôn ghi lý do vào nhật ký."""
    doc = _load(db, document_id, user, "write")
    doc, previous = service.update_issue_number(db, doc, data.issue_number, user.id)
    record(
        db,
        user.id,
        "document",
        doc.id,
        "update",
        f"Sửa số hiệu từ {previous} thành {doc.issue_number}. Lý do: {data.reason}",
    )
    return success(serializer.serialize(db, doc), "Đã cập nhật số hiệu")


@router.delete("/{document_id}/ban-nhap")
def discard_draft(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "create")),
):
    """Nút «Hủy» ở màn Tạo văn bản — dọn bản nháp mà chính mình vừa mở.

    Đi cùng `create` chứ không phải `delete`: xem `service.bo_ban_nhap_cua_minh`.
    """
    doc = _load(db, document_id, user, "read")
    service.discard_own_draft(db, doc, user.id)
    record(db, user.id, "document", document_id, "delete", "Bỏ bản nháp đang soạn dở")
    return success(None, "Đã bỏ bản nháp")


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
    data: ApproveIn | None = None,
    db: Session = Depends(get_db),
    user=Depends(require("document", "approve")),
):
    doc = _load(db, document_id, user)
    #  ĐÃ KÝ ĐỦ, CHỜ BAN HÀNH — nhịp này là của NGƯỜI SOẠN THẢO, không phải của
    #  người có quyền duyệt. Kiểm trước `chan_duong_cu` để câu báo nói đúng
    #  chuyện đang xảy ra thay vì câu chung về luồng nhiều bước.
    if doc.status == STATUS_PENDING_ISSUE:
        service.ensure_can_issue(db, doc, user)
    else:
        approval_bridge.block_legacy_path(db, doc)

    mailbox = _selected_mailbox(db, data, user)
    doc = service.approve(db, doc, user.id,
                          data.apply_mode if data else None,
                          mailbox_id=mailbox.id if mailbox else None)

    #  CR-200 (F12) — người ban hành tích «Đăng thông báo lên diễn đàn» thì clone
    #  thành một bài diễn đàn đã ghim. Chạy SAU khi ban hành xong và nuốt lỗi
    #  cùng luật với kênh chuông/email: diễn đàn hỏng không được biến một văn bản
    #  đã cấp số thành thao tác thất bại.
    forum_posted = False
    if data and data.forum_announce:
        try:
            from .issue_notification import create_forum_announcement
            create_forum_announcement(db, doc, user)
            forum_posted = True
        except Exception:  # noqa: BLE001 — kênh thông báo là best-effort
            import logging
            logging.getLogger(__name__).exception(
                "Không đăng được thông báo diễn đàn cho văn bản #%s", doc.id)

    #  Ghi luôn cơ chế áp dụng vào nhật ký: sáu tháng sau ai hỏi "vì sao văn bản
    #  này không clone xuống công ty con" thì có câu trả lời tại chỗ.
    #  Ghi cả hộp thư đã gửi: "ai đứng tên phát hành" là câu phải trả lời được
    #  từ nhật ký, không phải đi lục bảng thư.
    record(db, user.id, "document", doc.id, "approve",
           f"Ban hành {doc.doc_code or doc.issue_number}"
           f" · {APPLY_MODE_LABELS.get(doc.apply_mode, '')}"
           + (f" · gửi thông báo danh nghĩa {mailbox.email}" if mailbox else "")
           + (" · đăng thông báo lên diễn đàn" if forum_posted else ""))
    return success(serializer.serialize(db, doc), "Đã duyệt và ban hành")


def _selected_mailbox(db: Session, data, user):
    """Hộp thư người dùng chọn trong hộp thoại Ban hành, đã kiểm quyền dùng.

    `None` = không chọn, gửi bằng địa chỉ hệ thống như trước. Kiểm ở tầng API
    chứ không tin ô chọn: `mailbox_id` là một con số trong thân request, giao
    diện chỉ bày hộp thư của mình nhưng ai cũng gõ số khác vào được.
    """
    mailbox_id = getattr(data, "mailbox_id", None) if data else None
    if not mailbox_id:
        return None

    from app.modules.notification import mailbox_service

    return mailbox_service.ensure_can_use(
        db, mailbox_id, getattr(user, "employee_id", None))


@router.get("/{document_id}/mailboxes")
def mailboxes_for_issue(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """Những hộp thư TÔI được gửi danh nghĩa khi ban hành văn bản này.

    Đổ ra ô chọn trong hộp thoại Ban hành. Lọc theo pháp nhân ban hành để hộp
    thư của công ty khác không bày ra cho rối; hộp thư cấp Tập đoàn (không khai
    pháp nhân) thì nơi nào cũng thấy.
    """
    from app.modules.notification import mailbox_service

    doc = _load(db, document_id, user)
    rows = mailbox_service.for_employee(
        db, getattr(user, "employee_id", None), doc.company_id)
    return success([
        {
            "id": row.id,
            "email": row.email,
            "name": row.name,
            "display_name": row.display_name or row.name,
            #  Khai thiếu SMTP thì vẫn bày ra nhưng phải nói rõ, không thì người
            #  dùng chọn xong ban hành xong mới phát hiện thư không đi.
            "ready": mailbox_service.ready_to_send(row),
        }
        for row in rows
    ])


@router.post("/{document_id}/reject")
def reject_document(
    document_id: int,
    data: RejectIn,
    db: Session = Depends(get_db),
    user=Depends(require("document", "approve")),
):
    doc = _load(db, document_id, user)
    approval_bridge.block_legacy_path(db, doc)
    doc = service.send_back(db, doc, data.reason, user.id)
    record(db, user.id, "document", doc.id, "update", f"Trả về: {data.reason}")
    return success(serializer.serialize(db, doc), "Đã trả về cho người soạn")


@router.post("/{document_id}/reviewed")
def confirm_reviewed(
    document_id: int,
    data: ReviewedIn,
    db: Session = Depends(get_db),
    user=Depends(require("document", "write")),
):
    """Xác nhận ĐÃ RÀ SOÁT xong — tắt cờ «cần rà lại».

    Kết luận vào NHẬT KÝ THAO TÁC, không thêm cột: người sau mở nhật ký phải đọc
    được «đã đối chiếu, vẫn đúng» hay «đã sửa theo Chương II» — hai câu đó dẫn
    tới hai hành động khác hẳn nhau nếu về sau có tranh chấp.
    """
    doc = _load(db, document_id, user, "write")
    old_note = doc.needs_review_note
    doc = service.confirm_reviewed(db, doc, data.conclusion, user.id)
    record(db, user.id, "document", doc.id, "update",
           f"Xác nhận đã rà soát: {data.conclusion}"
           + (f" (dấu cũ: {old_note})" if old_note else ""))
    return success(serializer.serialize(db, doc), "Đã ghi nhận rà soát xong")


@router.post("/{document_id}/revoke")
def revoke_document(
    document_id: int,
    data: RejectIn,
    db: Session = Depends(get_db),
    user=Depends(require("document", "cancel")),
):
    """Bãi bỏ văn bản ĐÃ ban hành. Đây là lối thoát duy nhất cho văn bản đã cấp
    số — `DELETE` từ chối những văn bản đó để không thủng sổ."""
    doc = _load(db, document_id, user, "write")
    doc = service.revoke(db, doc, data.reason, user.id)
    record(db, user.id, "document", doc.id, "cancel", f"Bãi bỏ: {data.reason}")
    return success(serializer.serialize(db, doc), "Đã bãi bỏ văn bản")


# ── Phiên bản ────────────────────────────────────────────────────────────────
@router.get("/{document_id}/export/docx")
def export_docx(
    document_id: int,
    version_id: int | None = Query(None, description="Bản cần xuất; bỏ trống = bản đang dùng"),
    db: Session = Depends(get_db),
    user=Depends(doc_reader),
):
    """Xuất một phiên bản văn bản ra tệp Word (.docx).

    Gác bằng `doc_reader` + `_load(..., "read")` như mọi đường ĐỌC nội dung: ai
    mở được văn bản trên màn hình thì tải được đúng thứ đó về máy. Không đòi
    thêm quyền `export` — quyền đó dành cho việc kéo cả DANH SÁCH ra ngoài.
    """
    from fastapi.responses import Response
    from urllib.parse import quote

    from .html_docx import html_to_docx

    doc = _load(db, document_id, user, "read")
    version = (version_service.get_or_404(db, doc, version_id) if version_id
               else db.get(DocumentVersion, doc.current_version_id))
    if version is None:
        raise HTTPException(404, "Văn bản chưa có phiên bản nào để xuất")

    data = html_to_docx(
        version.content_html or "",
        margin_left_mm=version.margin_left_mm,
        margin_right_mm=version.margin_right_mm,
        number_headings=version.auto_heading_number,
        header=(version.header_left, version.header_right),
        footer=(version.footer_left, version.footer_right),
        replacements={
            "{{so_hieu}}": doc.doc_code or doc.issue_number or "",
            "{{ten_van_ban}}": doc.title or "",
            "{{ngay}}": date.today().strftime("%d/%m/%Y"),
        },
    )

    #  Tên tệp lấy theo SỐ HIỆU nếu đã có — người nhận lưu về máy còn tra được.
    name = (doc.doc_code or doc.issue_number or doc.title or "van-ban")
    name = f"{name.replace('/', '-')} - ban {version.version_no}.docx"
    return Response(
        content=data,
        media_type=("application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"),
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"},
    )


@router.get("/{document_id}/versions")
def list_versions(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(doc_reader),
):
    doc = _load(db, document_id, user)
    versions = version_service.list_versions(db, doc)
    return success([serializer.serialize_version(db, v, doc) for v in versions])


@router.get("/{document_id}/versions/{version_id}")
def get_version(
    document_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    user=Depends(doc_reader),
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
    user=Depends(doc_reader),
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
