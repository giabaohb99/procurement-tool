"""Tool tra LUỒNG PHÊ DUYỆT + VĂN BẢN cho Trợ lý AI — chỉ đọc, không ghi.

- `approval_flow_lookup`: "đơn nghỉ phép do ai duyệt", "người phê duyệt của tôi là ai".
  Tìm loại văn bản trong danh mục rồi chọn luồng bằng ĐÚNG bộ máy chọn của phân hệ duyệt
  (`flow_service.chon_luong`) — không tự chọn lại, kẻo tool nói một đằng phiếu chạy một
  nẻo. Mỗi bước trả kèm hai tầng: QUY TẮC khai trong luồng ("Trưởng bộ phận người nộp")
  và TÊN NGƯỜI cụ thể nếu chính người hỏi nộp phiếu (`approver_resolver`).
- `my_documents`: "văn bản nào đang áp dụng lên tôi". Tái dùng phép tính phạm vi của văn
  thư (`scope_service.document_ids_for`) + lọc quyền đọc — y hệt màn «Áp dụng cho tôi»,
  để chat và màn hình không bao giờ trả hai danh sách khác nhau.
- `document_search`: tìm văn bản theo từ khóa — đi đúng luật lọc của MÀN DANH SÁCH
  (`documents_query` + `visible_condition` + giấu bản riêng khi thấy bản gốc), nên chat
  không bao giờ kể ra văn bản mà người hỏi mở danh sách không thấy.
- `document_read`: đọc NỘI DUNG một văn bản để trả lời câu hỏi về nội dung. Cổng vào
  giống bốn endpoint đọc-một-văn-bản (`doc_reader`): không đòi vai trò văn thư, quyền
  kiểm trên CHÍNH văn bản bằng `access_service.can` — người duyệt trong luồng không có
  vai trò nào ở phân hệ vẫn hỏi được văn bản mình đang duyệt.
"""
import re
from html import unescape

from sqlalchemy import and_, or_

from app.modules.approval import approver_resolver, flow_service, serializer
from app.modules.approval.flow_model import (APPROVER_FIELD, APPROVER_LEVEL_UP,
                                             APPROVER_ROLE)
from app.modules.doc_catalog.model import DocType
from app.modules.document.model import STATUS_LABELS, Document
from app.modules.document import access_service, scope_service
from app.modules.document.query import (an_ban_rieng_co_goc_xem_duoc,
                                        documents_query)
from app.modules.document.version_model import DocumentVersion
from app.modules.employee.model import Employee

from .base import ToolContext, ToolSpec, denied

MAX_FLOWS = 10
MAX_DOCS = 30
#  Đường dẫn chi tiết văn bản bên frontend-v2 (`appRoutes.document.documentDetail`) — trả
#  kèm để câu trả lời gắn link Markdown mở thẳng văn bản, người dùng khỏi tự đi tìm.
_DUONG_DAN_VAN_BAN = "/document/documents/{id}"
#  Mỗi phần nội dung trả cho model — văn bản dài đọc theo từng phần (tham số `part`)
#  thay vì nhồi cả quy chế vài chục trang vào một lượt.
MAX_CONTENT_CHARS = 8000


# ── approval_flow_lookup ────────────────────────────────────────────────────────────────

def _run_flow_lookup(ctx: ToolContext, args: dict) -> dict:
    doc_type_query = str(args.get("doc_type") or "").strip()
    entity = str(args.get("entity") or "").strip()

    if doc_type_query:
        return _luong_van_ban(ctx, doc_type_query)
    if entity:
        return _luong_chung_tu(ctx, entity)
    return {"error": "Cho biết loại văn bản (vd 'nghỉ phép') hoặc mã loại chứng từ cần tra."}


def _tim_loai_van_ban(db, query: str) -> list[DocType]:
    """Tìm loại văn bản theo mã rồi theo tên.

    Người hỏi hay nói "đơn nghỉ phép" trong khi danh mục ghi "Giấy nghỉ phép" — LIKE cả
    câu sẽ trượt vì chữ "đơn". Nên nếu cả câu không ra, bỏ dần từ ĐẦU câu rồi thử lại
    ("đơn nghỉ phép" -> "nghỉ phép"): phần lõi tên loại thường nằm ở cuối.
    """
    exact = (db.query(DocType)
             .filter(DocType.is_active.is_(True), DocType.code == query.upper())
             .first())
    if exact:
        return [exact]

    tu = query.split()
    for bat_dau in range(len(tu)):
        cum = " ".join(tu[bat_dau:])
        if len(cum) < 3:
            break
        rows = (db.query(DocType)
                .filter(DocType.is_active.is_(True), DocType.name.like(f"%{cum}%"))
                .order_by(DocType.sort_order.asc(), DocType.id.asc())
                .limit(6).all())
        if rows:
            return rows
    return []


def _boi_canh_cua_toi(db, user) -> tuple[dict, int | None]:
    """Bối cảnh giả định CHÍNH NGƯỜI HỎI là người nộp phiếu — để giải ra tên người duyệt
    cụ thể ("người phê duyệt nghỉ phép CỦA TÔI là ai")."""
    emp = db.get(Employee, user.employee_id) if getattr(user, "employee_id", None) else None
    subject = {
        "company_id": emp.company_id if emp else None,
        "department_id": emp.department_id if emp else None,
    }
    return subject, (emp.id if emp else None)


def _ten_nhan_su(db, employee_ids: list[int]) -> list[str]:
    if not employee_ids:
        return []
    theo_id = {row.id: row.full_name for row in
               db.query(Employee).filter(Employee.id.in_(employee_ids)).all()}
    return [theo_id[i] for i in employee_ids if i in theo_id]


def _mo_ta_buoc(db, node, subject: dict, submitter_id: int | None) -> dict:
    """Một bước duyệt, hai tầng thông tin: quy tắc khai + tên người giải ra cho người hỏi."""
    data = serializer.node_out(db, node)

    quy_tac = data["approver_kind_label"]
    ref = (node.approver_ref or "").strip()
    if data["approver_names"]:
        quy_tac += f": {data['approver_names']}"
    elif node.approver_kind == APPROVER_ROLE and ref:
        from app.modules.role.model import Role
        codes = [phan.strip() for phan in ref.split(",") if phan.strip()]
        ten_vai = [row.name for row in db.query(Role).filter(Role.code.in_(codes)).all()]
        quy_tac += ": " + ", ".join(ten_vai or codes)
    elif node.approver_kind == APPROVER_LEVEL_UP and ref:
        quy_tac += f" ({ref} cấp)"
    elif node.approver_kind == APPROVER_FIELD and ref:
        quy_tac += f" (ô '{ref}' trên phiếu)"

    buoc = {
        "seq": node.seq,
        "name": node.name or data["node_kind_label"],
        "node_kind": data["node_kind_label"],
        "approver_rule": quy_tac,
        #  Tên NGƯỜI THẬT nếu chính người hỏi nộp phiếu này. Rỗng = chưa tính được
        #  (thiếu trưởng bộ phận, vai trò chưa gán ai...) — nói thẳng, đừng bịa.
        "approvers_for_me": _ten_nhan_su(
            db, approver_resolver.resolve(db, node, subject, submitter_id)),
    }
    if node.branch_key:
        buoc["branch"] = node.branch_key
    if (node.condition or "").strip():
        buoc["condition"] = node.condition
    if data["multi_mode_label"] and node.multi_mode != 1:
        buoc["multi_mode"] = data["multi_mode_label"]
    return buoc


#  Khi bộ máy luồng nhiều bước chưa chạy (cờ tắt, hoặc bật mà chưa khai luồng) thì văn bản
#  duyệt MỘT BƯỚC: người có quyền duyệt văn bản bấm Duyệt/Từ chối trên trang chi tiết.
_DUYET_MOT_BUOC = ("Hiện phê duyệt MỘT BƯỚC: người có quyền duyệt văn bản "
                   "xem xét và bấm Duyệt/Từ chối trên trang chi tiết.")


def _luong_van_ban(ctx: ToolContext, query: str) -> dict:
    """Luồng duyệt của một LOẠI VĂN BẢN — ai hỏi cũng được trả lời: đây chính là thông tin
    người nộp thấy khi gửi duyệt phiếu của mình, không phải cấu hình mật."""
    db, user = ctx.db, ctx.user

    matches = _tim_loai_van_ban(db, query)
    if not matches:
        vai_loai = [row.name for row in
                    db.query(DocType).filter(DocType.is_active.is_(True))
                    .order_by(DocType.sort_order.asc()).limit(10).all()]
        return {"error": f"Không tìm thấy loại văn bản nào khớp '{query}'.",
                "available_types": vai_loai,
                "reminder": "Hỏi lại người dùng xem họ muốn loại văn bản nào."}
    if len(matches) > 1:
        return {"status": "ambiguous",
                "matches": [{"code": t.code, "name": t.name} for t in matches],
                "reminder": "Nhiều loại văn bản cùng khớp — hỏi lại người dùng chọn một."}

    loai = matches[0]
    subject, submitter_id = _boi_canh_cua_toi(db, user)
    subject["doc_type_id"] = loai.id

    ket_qua = {
        "doc_type": {"code": loai.code, "name": loai.name,
                     "is_personal": loai.is_personal,
                     "needs_approval": loai.needs_approval},
        "engine_enabled": flow_service.is_enabled(db, "document"),
    }

    if not loai.needs_approval:
        ket_qua.update(status="no_approval", total=0,
                       message=f"Loại văn bản «{loai.name}» KHÔNG cần phê duyệt.")
        return ket_qua

    flow = flow_service.chon_luong(db, "document", subject) if ket_qua["engine_enabled"] else None
    if flow is None:
        ket_qua.update(status="one_step", total=0, message=(
            ("Bộ máy luồng nhiều bước đang TẮT cho văn bản. " if not ket_qua["engine_enabled"]
             else f"Chưa khai luồng phê duyệt nào áp cho «{loai.name}». ") + _DUYET_MOT_BUOC))
        return ket_qua

    steps = [_mo_ta_buoc(db, node, subject, submitter_id)
             for node in flow_service.nodes_of(db, flow.id)]
    ket_qua.update(
        status="flow", total=len(steps),
        flow={"name": flow.name, "description": flow.description},
        steps=steps,
        note=("`approver_rule` là quy tắc khai trong luồng; `approvers_for_me` là tên "
              "người duyệt CỤ THỂ nếu chính người hỏi nộp phiếu. Danh sách rỗng nghĩa là "
              "chưa tính được (vd phòng chưa có trưởng bộ phận) — nói rõ, đừng đoán tên."),
    )
    return ket_qua


def _luong_chung_tu(ctx: ToolContext, entity: str) -> dict:
    """Luồng của một loại CHỨNG TỪ bất kỳ (purchase_request...) — đây là màn cấu hình
    luồng nên gác đúng quyền của màn đó."""
    if not ctx.can("approval_flow"):
        return denied("cấu hình luồng phê duyệt")

    db = ctx.db
    subject, submitter_id = _boi_canh_cua_toi(db, ctx.user)

    from app.modules.approval.flow_model import ApprovalFlow
    flows = (db.query(ApprovalFlow)
             .filter(ApprovalFlow.entity == entity, ApprovalFlow.is_active.is_(True))
             .order_by(ApprovalFlow.priority.desc(), ApprovalFlow.id.asc())
             .limit(MAX_FLOWS).all())

    ket_qua = {"entity": entity,
               "engine_enabled": flow_service.is_enabled(db, entity),
               "total": len(flows)}
    if not flows:
        ket_qua["message"] = f"Chưa khai luồng phê duyệt nào cho loại chứng từ '{entity}'."
        return ket_qua

    ket_qua["flows"] = [{
        "name": flow.name,
        "company_name": (serializer.flow_out(db, flow)["company_name"] or "Dùng chung"),
        "priority": flow.priority,
        "condition": flow.condition or "",
        "steps": [_mo_ta_buoc(db, node, subject, submitter_id)
                  for node in flow_service.nodes_of(db, flow.id)],
    } for flow in flows]
    return ket_qua


APPROVAL_FLOW_LOOKUP_SPEC = ToolSpec(
    name="approval_flow_lookup",
    description=(
        "Tra LUỒNG PHÊ DUYỆT: một loại văn bản do ai duyệt, qua những bước nào, và người "
        "duyệt cụ thể của chính người hỏi là ai (vd 'đơn nghỉ phép do ai phê duyệt', "
        "'người phê duyệt nghỉ phép của tôi là ai'). Truyền `doc_type` cho văn bản; chỉ "
        "dùng `entity` khi hỏi về luồng của chứng từ khác (cần quyền cấu hình luồng)."
    ),
    parameters={
        "type": "object",
        "properties": {
            "doc_type": {
                "type": "string",
                "description": ("Tên hoặc mã loại văn bản (vd 'nghỉ phép', 'quyết định', "
                                "'GNP'). Bỏ các từ đơn/giấy/văn bản nếu tra không ra."),
            },
            "entity": {
                "type": "string",
                "description": ("Mã loại chứng từ KHÔNG phải văn bản, vd 'purchase_request'. "
                                "Đừng điền khi đã có doc_type."),
            },
        },
    },
    handler=_run_flow_lookup,
)


# ── my_documents ────────────────────────────────────────────────────────────────────────

def _run_my_documents(ctx: ToolContext, args: dict) -> dict:
    """Văn bản đang áp dụng cho CHÍNH người hỏi — không cần quyền gì thêm ngoài đăng nhập,
    giống endpoint `/api/documents/applies-to-me` (màn ai cũng mở được)."""
    db, user = ctx.db, ctx.user
    keyword = str(args.get("keyword") or "").strip()
    limit = args.get("limit")
    limit = max(1, min(int(limit), MAX_DOCS)) if isinstance(limit, (int, float)) else 20

    emp = db.get(Employee, user.employee_id) if getattr(user, "employee_id", None) else None
    if emp is None:
        return {"error": "Tài khoản chưa gắn hồ sơ nhân sự nên không tính được phạm vi áp dụng."}

    ids = scope_service.document_ids_for(db, emp)
    if not ids:
        return {"total": 0, "items": []}

    query = db.query(Document).filter(Document.id.in_(ids))
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(Document.title.like(like)
                             | Document.issue_number.like(like)
                             | Document.keywords.like(like))
    docs = query.all()

    #  Cùng cái bẫy §4.6 của kịch bản test văn thư: phạm vi áp dụng RỘNG HƠN quyền đọc
    #  (dòng cấm đích danh nằm ở tab_document_access). Lọc lại bằng chính `can()` để chat
    #  không kể ra văn bản mà người hỏi bấm vào sẽ ăn 404.
    docs = [d for d in docs if access_service.can(db, d, user, ctx.profile, "read")]
    docs.sort(key=lambda d: (d.effective_date is None, d.effective_date), reverse=True)

    loai_theo_id = {row.id: row.name for row in
                    db.query(DocType).filter(
                        DocType.id.in_({d.doc_type_id for d in docs if d.doc_type_id}))}
    return {
        "total": len(docs),
        "items": [{
            "issue_number": d.issue_number,
            "title": d.title,
            "doc_type": loai_theo_id.get(d.doc_type_id, ""),
            "status": STATUS_LABELS.get(d.status, ""),
            "effective_date": d.effective_date.isoformat() if d.effective_date else "",
            "expire_date": d.expire_date.isoformat() if d.expire_date else "",
            "url": _DUONG_DAN_VAN_BAN.format(id=d.id),
        } for d in docs[:limit]],
    }


MY_DOCUMENTS_SPEC = ToolSpec(
    name="my_documents",
    description=(
        "Danh sách VĂN BẢN đang áp dụng cho chính người hỏi (quy chế, quy định, thông "
        "báo... trong phạm vi áp dụng của họ). Dùng cho câu 'văn bản nào áp dụng lên "
        "tôi', 'tôi phải theo quy định nào'."
    ),
    parameters={
        "type": "object",
        "properties": {
            "keyword": {"type": "string",
                        "description": "Lọc theo tiêu đề / số hiệu / từ khóa (tùy chọn)."},
            "limit": {"type": "integer",
                      "description": f"Số dòng tối đa, mặc định 20, trần {MAX_DOCS}."},
        },
    },
    handler=_run_my_documents,
)


# ── document_search ─────────────────────────────────────────────────────────────────────

def _dieu_kien_tu_khoa(keyword: str):
    """AND theo TỪNG TỪ, mỗi từ OR trên các cột tìm của màn danh sách.

    LIKE cả câu thì "quy định công tác phí" trượt tiêu đề "Quy định về chế độ công tác
    phí" chỉ vì thiếu chữ "về". Tách từ rồi bắt mỗi từ khớp Ở ĐÂU ĐÓ (tiêu đề, số hiệu,
    số hiệu cũ, từ khóa, nơi lưu trữ) là đủ hẹp mà không bắt người hỏi thuộc nguyên văn."""
    cot = (Document.title, Document.doc_code, Document.issue_number,
           Document.legacy_code, Document.keywords, Document.storage_location)
    return and_(*[or_(*[c.like(f"%{tu}%") for c in cot]) for tu in keyword.split()])


def _dong_van_ban(d: Document, loai_theo_id: dict) -> dict:
    return {
        "document_id": d.id,
        "issue_number": d.issue_number,
        "legacy_code": d.legacy_code or "",
        "title": d.title,
        "doc_type": loai_theo_id.get(d.doc_type_id, ""),
        "status": STATUS_LABELS.get(d.status, ""),
        "effective_date": d.effective_date.isoformat() if d.effective_date else "",
        "expire_date": d.expire_date.isoformat() if d.expire_date else "",
        "summary": (d.summary or "")[:200],
        "url": _DUONG_DAN_VAN_BAN.format(id=d.id),
    }


def _run_document_search(ctx: ToolContext, args: dict) -> dict:
    #  Cùng cổng với màn danh sách (`require("document", "read")`) — my_documents và
    #  document_read cố ý KHÔNG gác vì chúng trả lời phạm vi hẹp hơn, còn tìm kiếm là
    #  quét cả kho văn bản.
    if not ctx.can("document"):
        return denied("kho văn bản (cần quyền đọc phân hệ Văn bản)")

    keyword = str(args.get("keyword") or "").strip()
    if not keyword:
        return {"error": "Cho biết từ khóa cần tìm (tên văn bản, số hiệu, chủ đề...)."}
    limit = args.get("limit")
    limit = max(1, min(int(limit), MAX_DOCS)) if isinstance(limit, (int, float)) else 20

    db = ctx.db
    query = documents_query(db)
    visible = access_service.visible_condition(ctx.user, ctx.profile)
    if visible is not None:
        query = query.filter(visible)
    query = query.filter(_dieu_kien_tu_khoa(keyword))

    out: dict = {}
    loai_hoi = str(args.get("doc_type") or "").strip()
    if loai_hoi:
        loai = _tim_loai_van_ban(db, loai_hoi)
        if loai:
            query = query.filter(Document.doc_type_id.in_([r.id for r in loai]))
        else:
            #  Tên loại gõ sai thì bỏ bộ lọc chứ đừng chặn cả cuộc tìm — nhưng phải NÓI,
            #  im lặng là model tưởng kết quả đã lọc đúng loại.
            out["note"] = f"Không thấy loại văn bản '{loai_hoi}' — kết quả chưa lọc theo loại."

    query = an_ban_rieng_co_goc_xem_duoc(query)
    total = query.count()
    docs = query.order_by(Document.id.desc()).limit(limit).all()

    loai_theo_id = {row.id: row.name for row in
                    db.query(DocType).filter(
                        DocType.id.in_({d.doc_type_id for d in docs if d.doc_type_id}))}
    out.update(total=total, items=[_dong_van_ban(d, loai_theo_id) for d in docs])
    if total:
        out["reminder"] = ("Danh sách chỉ có tiêu đề/tóm tắt. Câu hỏi về NỘI DUNG văn bản "
                           "thì gọi tiếp document_read với document_id tương ứng.")
    return out


DOCUMENT_SEARCH_SPEC = ToolSpec(
    name="document_search",
    description=(
        "TÌM VĂN BẢN nội bộ (quy chế, quy định, quyết định, thông báo...) theo từ khóa — "
        "khớp trên tiêu đề, số hiệu (cả số hiệu cũ bản giấy), từ khóa và nơi lưu trữ; kết "
        "quả đã lọc đúng quyền xem của người hỏi. Dùng cho câu 'tìm văn bản/quy định về "
        "X', 'văn bản số Y là văn bản nào', 'có quy định nào về Z không'. Tool chỉ trả "
        "DANH SÁCH; muốn trả lời nội dung bên trong thì gọi tiếp document_read. Khác "
        "my_documents: my_documents chỉ liệt kê văn bản áp dụng lên chính người hỏi."
    ),
    parameters={
        "type": "object",
        "properties": {
            "keyword": {"type": "string",
                        "description": "Từ khóa cần tìm — bắt buộc. Vd 'công tác phí', '01/QC'."},
            "doc_type": {"type": "string",
                         "description": "Lọc theo loại văn bản (tên hoặc mã), vd 'quyết định'. Tùy chọn."},
            "limit": {"type": "integer",
                      "description": f"Số dòng tối đa, mặc định 20, trần {MAX_DOCS}."},
        },
        "required": ["keyword"],
    },
    handler=_run_document_search,
)


# ── document_read ───────────────────────────────────────────────────────────────────────

def _html_thanh_van_ban(html: str) -> str:
    """Bóc HTML của trình soạn thảo thành văn bản thuần cho model đọc.

    Không cần render đẹp — chỉ cần giữ ranh giới đoạn/dòng và ô bảng (` | `) để câu chữ
    không dính liền nhau làm model đọc sai điều khoản."""
    if not html:
        return ""
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?i)</t[dh]>", " | ", text)
    text = re.sub(r"(?i)<br\s*/?>|</(p|div|li|tr|h[1-6]|table|ul|ol|blockquote)>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


#  MỘT câu cho cả "không tồn tại" lẫn "không có quyền" — như màn chi tiết trả 404 chứ
#  không 403: nói "có văn bản này nhưng anh không được xem" cũng đã là lộ thông tin.
_KHONG_THAY = ("Không tìm thấy văn bản khớp (hoặc bạn không có quyền xem). "
               "Thử document_search để tra đúng số hiệu / document_id trước.")


def _run_document_read(ctx: ToolContext, args: dict) -> dict:
    db, user = ctx.db, ctx.user
    so_hieu = str(args.get("issue_number") or "").strip()
    try:
        document_id = int(args.get("document_id") or 0)
    except (TypeError, ValueError):
        document_id = 0

    if document_id > 0:
        docs = documents_query(db).filter(Document.id == document_id).all()
    elif so_hieu:
        docs = documents_query(db).filter(Document.issue_number == so_hieu).all()
        if not docs:
            #  Người dùng hay gõ một khúc số hiệu ("15/QĐ") hoặc số hiệu CŨ bản giấy.
            like = f"%{so_hieu}%"
            docs = (documents_query(db)
                    .filter(or_(Document.issue_number.like(like),
                                Document.legacy_code.like(like)))
                    .order_by(Document.id.desc()).limit(6).all())
    else:
        return {"error": "Cho biết document_id (lấy từ document_search) hoặc số hiệu văn bản."}

    docs = [d for d in docs if access_service.can(db, d, user, ctx.profile, "read")]
    if not docs:
        return {"error": _KHONG_THAY}
    if len(docs) > 1:
        return {"error": "Nhiều văn bản khớp số hiệu đó — gọi lại với document_id của đúng bản cần đọc.",
                "matches": [{"document_id": d.id, "issue_number": d.issue_number,
                             "title": d.title} for d in docs]}

    doc = docs[0]
    version = db.get(DocumentVersion, doc.current_version_id) if doc.current_version_id else None
    text = _html_thanh_van_ban(version.content_html if version else "")

    part = args.get("part")
    part = max(1, int(part)) if isinstance(part, (int, float)) else 1
    tong_phan = max(1, -(-len(text) // MAX_CONTENT_CHARS))
    part = min(part, tong_phan)

    loai = db.get(DocType, doc.doc_type_id) if doc.doc_type_id else None
    out = {
        "document": {
            "document_id": doc.id,
            "issue_number": doc.issue_number,
            "legacy_code": doc.legacy_code or "",
            "title": doc.title,
            "doc_type": loai.name if loai else "",
            "status": STATUS_LABELS.get(doc.status, ""),
            "effective_date": doc.effective_date.isoformat() if doc.effective_date else "",
            "expire_date": doc.expire_date.isoformat() if doc.expire_date else "",
            "summary": doc.summary or "",
            "url": _DUONG_DAN_VAN_BAN.format(id=doc.id),
        },
        "part": part,
        "total_parts": tong_phan,
        "content": text[(part - 1) * MAX_CONTENT_CHARS: part * MAX_CONTENT_CHARS],
    }
    if not text:
        out["note"] = ("Văn bản chưa có nội dung soạn trên hệ thống (có thể chỉ có file "
                       "đính kèm) — trả lời theo tiêu đề/tóm tắt và nói rõ giới hạn này.")
    elif part < tong_phan:
        out["note"] = (f"Nội dung dài, đây là phần {part}/{tong_phan} — cần đọc tiếp thì "
                       f"gọi lại với part={part + 1}. Đừng suy đoán phần chưa đọc.")
    return out


DOCUMENT_READ_SPEC = ToolSpec(
    name="document_read",
    description=(
        "ĐỌC NỘI DUNG (toàn văn, đã bóc định dạng) một văn bản nội bộ mà người hỏi có "
        "quyền xem — dùng để trả lời câu hỏi về nội dung: 'quy định X nói gì về Y', "
        "'điều kiện/mức chi trong văn bản Z'. Truyền document_id (ưu tiên, lấy từ "
        "document_search hoặc my_documents) hoặc số hiệu. Văn bản dài chia thành nhiều "
        "phần — truyền part để đọc tiếp. Khi trả lời phải bám nội dung tool trả về, nêu "
        "số hiệu văn bản, và lưu ý người dùng nếu văn bản không ở trạng thái Có hiệu lực."
    ),
    parameters={
        "type": "object",
        "properties": {
            "document_id": {"type": "integer",
                            "description": "Id văn bản — lấy từ kết quả document_search."},
            "issue_number": {"type": "string",
                             "description": "Số hiệu văn bản (chấp nhận cả số hiệu cũ), vd '15/QĐ-DEGO'."},
            "part": {"type": "integer",
                     "description": "Phần nội dung cần đọc (1-based), mặc định 1. Dùng khi total_parts > 1."},
        },
    },
    handler=_run_document_read,
)
