"""Phạm vi dữ liệu cho tệp đính kèm — B-08, trả nợ N-13.

`FILE_POLICY` (`core/file_registry.py`) chỉ nói entity đính kèm ăn theo QUYỀN
VAI TRÒ của chứng từ cha nào. Nó không nói gì về PHẠM VI DỮ LIỆU, nên trước đợt
này ai có `contract.read` phạm vi `company` vẫn tải được đính kèm hợp đồng của
pháp nhân khác miễn đoán đúng id. Lỗ này chung cho cả mười loại chứng từ.

Tệp này bù đúng nửa còn thiếu, theo khuôn hai lớp của `comment/service.resolve_doc`:

  1. quyền vai trò — `user_has_permission`, vẫn nằm ở `attachment/controller._check`;
  2. phạm vi dữ liệu — `ensure_in_scope` ở đây.

Ba chỗ phải cẩn thận:

* **`entity_id` không phải lúc nào cũng là id chứng từ.** Bốn loại treo vào DÒNG
  (`purchase_request_line_image`, `survey_line`, `survey_request_line`,
  `delivery`, `ticket_message`) nên phải tra ngược khóa ngoại mới ra chứng từ cha.
* **Văn bản không dùng `apply_scope` được.** Quyền đọc một văn bản còn tới từ
  chia sẻ đích danh, thành viên sổ, phạm vi áp dụng và việc đang duyệt — những
  nguồn mà `apply_scope` chỉ biết thu hẹp chứ không biết cộng thêm. Nhánh đó đi
  qua `document/access_service.ensure_can`, và giữ nguyên luật 404-khi-không-đọc-được.
* **Entity chưa khai trong `SCOPE_FIELDS` thì đây là hàm rỗng.** `apply_scope`
  không sinh mệnh đề nào cho `product`/`company`/`supplier`. Đó là phần việc của
  B-07 (N-14); khai thêm ở `SCOPE_FIELDS` là đính kèm siết theo, không phải sửa lại đây.
"""
import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, user_has_permission
from app.core.file_registry import policy
from app.core.scoping import apply_scope

#  Nhật ký từ chối. `06` H4(b) dặn: thu nhật ký đủ rồi mới chặn, không thì có
#  người đang dùng hợp lệ mà bị khóa không hiểu vì sao. Ở đây chặn ngay (đợt này
#  chỉ chạy `erp-v2`/dev, prod đứng yên theo QĐ-10) nhưng mỗi lần chặn ghi lại
#  một dòng đủ để tra: ai, tệp nào, chứng từ nào. Đọc log trước khi cắt sang prod.
log = logging.getLogger("app.attachment.scope")


def parent_records(db: Session, entity: str, entity_id: int):
    """(model chứng từ cha, [id cha]) — `(None, [])` nếu entity không nằm trong bộ tra.

    Danh sách id chứ không phải một id: `survey_line` KHÔNG nói rõ đang là dòng
    nhà cung cấp hay dòng sản phẩm, mà hai bảng đánh id riêng nên cùng một số có
    thể có nghĩa ở cả hai. Tra cả hai, và coi là trong phạm vi nếu MỘT trong hai
    phiếu khảo sát tương ứng nằm trong phạm vi — đúng bằng thứ mà lối tải lên
    hiện tại đang cho phép, không rộng hơn.

    Import bên trong hàm để không tạo vòng import với các module nghiệp vụ —
    cùng cách `core/comment_registry.doc_model` làm.
    """
    def _fk(col, parent_model, key_col):
        return parent_model, [i for (i,) in db.query(col).filter(key_col == entity_id)]

    if entity in ("purchase_request", "purchase_request_quote"):
        from app.modules.purchase_request.model import PurchaseRequest
        return PurchaseRequest, [entity_id]
    if entity == "purchase_request_line_image":
        from app.modules.purchase_request.model import (PurchaseRequest,
                                                        PurchaseRequestItem)
        return _fk(PurchaseRequestItem.pr_id, PurchaseRequest, PurchaseRequestItem.id)

    if entity == "survey":
        from app.modules.survey.model import Survey
        return Survey, [entity_id]
    if entity == "survey_line":
        from app.modules.survey.model import (Survey, SurveyProductLine,
                                              SurveySupplierLine)
        ids = [i for (i,) in db.query(SurveySupplierLine.survey_id)
               .filter(SurveySupplierLine.id == entity_id)]
        ids += [i for (i,) in db.query(SurveyProductLine.survey_id)
                .filter(SurveyProductLine.id == entity_id)]
        return Survey, ids

    if entity == "survey_request":
        from app.modules.survey_request.model import SurveyRequest
        return SurveyRequest, [entity_id]
    if entity == "survey_request_line":
        from app.modules.survey_request.model import (SurveyRequest,
                                                      SurveyRequestLine)
        return _fk(SurveyRequestLine.survey_request_id, SurveyRequest, SurveyRequestLine.id)

    if entity == "purchase_order":
        from app.modules.purchase_order.model import PurchaseOrder
        return PurchaseOrder, [entity_id]
    if entity == "delivery":
        from app.modules.purchase_order.model import PODelivery, PurchaseOrder
        return _fk(PODelivery.po_id, PurchaseOrder, PODelivery.id)

    if entity == "contract":
        from app.modules.contract.model import Contract
        return Contract, [entity_id]
    if entity == "payment_request":
        from app.modules.payment_request.model import PaymentRequest
        return PaymentRequest, [entity_id]

    if entity == "ticket":
        from app.modules.ticket.model import Ticket
        return Ticket, [entity_id]
    if entity == "ticket_message":
        from app.modules.ticket.model import Ticket, TicketMessage
        return _fk(TicketMessage.ticket_id, Ticket, TicketMessage.id)

    #  Ba loại dưới đây chưa có mặt trong `SCOPE_FIELDS` nên `apply_scope` không
    #  sinh mệnh đề nào — vẫn khai ở đây để ngày B-07 khai thêm là đính kèm siết
    #  theo, không phải mở lại tệp này.
    if entity == "product":
        from app.modules.product.model import Product
        return Product, [entity_id]
    if entity == "company":
        from app.modules.company.model import Company
        return Company, [entity_id]
    if entity == "supplier":
        from app.modules.supplier.model import Supplier
        return Supplier, [entity_id]
    return None, []


def _ensure_document(db: Session, user, version_id: int, action: str):
    """Đính kèm văn bản: hỏi `access_service`, không hỏi `apply_scope`.

    `visible_condition` gộp cả chia sẻ đích danh lẫn thành viên sổ — hai nguồn
    quyền nằm NGOÀI phạm vi vai trò. Dùng `apply_scope` ở đây là cắt mất đúng
    những người được chia sẻ tay.
    """
    from app.modules.document import access_service
    from app.modules.document.model import Document
    from app.modules.document.version_model import DocumentVersion

    version = db.get(DocumentVersion, version_id)
    doc = db.get(Document, version.document_id) if version else None
    if not doc:
        raise HTTPException(404, "Không tìm thấy văn bản")
    access_service.ensure_can(db, doc, user, get_perm_profile(db, user),
                              "read" if action == "read" else "write")


def _ensure_task_member(db: Session, user, task_id: int, action: str):
    """Đính kèm công việc: hỏi TƯ CÁCH THÀNH VIÊN, không hỏi `apply_scope`.

    `work_task` khai `PUBLIC` ở `core/scoping.SCOPE_FIELDS` vì phạm vi thật của
    nó là "thành viên của danh sách chứa việc" — thứ không diễn đạt được bằng
    cột phòng ban hay pháp nhân. Để nó đi đường `apply_scope` thì không mệnh đề
    nào được thêm vào, tức là chỉ còn lớp vai trò, mà `work_task.read` thì gần
    như ai cũng có: đoán đúng `link_id` là tải được tệp của dự án người khác.

    Cùng lý do và cùng khuôn với `_ensure_document` ngay trên.
    Gỡ/thêm tệp đòi mức MEMBER; xem thì thành viên nào cũng được.
    """
    from app.modules.work.membership_service import (CAN_EDIT, CAN_VIEW,
                                                     require_employee, resolve_actor)
    from app.modules.work.task_service import get_task_or_403

    actor = resolve_actor(db, user)
    require_employee(actor)
    get_task_or_403(db, actor, task_id, CAN_VIEW if action == "read" else CAN_EDIT)


def ensure_in_scope(db: Session, user, entity: str, entity_id: int, mode: str = "read"):
    """Ném 403/404 nếu chứng từ cha của tệp nằm ngoài phạm vi dữ liệu của người này.

    `mode` đi theo `_check`: `read` soi phạm vi hành động `read`; `manage` soi
    `write` HOẶC `create` — đúng cặp mà `_check` đã chấp nhận ở lớp vai trò, nếu
    không thì người chỉ có `create` sẽ gắn được tệp lúc tạo phiếu rồi bị chặn
    ngay ở lần đọc lại.
    """
    parent = (policy(entity) or (None,))[0]
    if not parent or parent == "__self__":
        return
    if parent == "document":
        _ensure_document(db, user, entity_id, mode)
        return
    if parent == "work_task":
        _ensure_task_member(db, user, entity_id, mode)
        return

    model, ids = parent_records(db, entity, entity_id)
    if model is None:
        return
    if not ids:
        raise HTTPException(404, "Chứng từ của tệp không còn tồn tại")

    profile = get_perm_profile(db, user)
    actions = ("read",) if mode == "read" else ("write", "create")
    for action in actions:
        q = apply_scope(db.query(model.id).filter(model.id.in_(ids)), model, parent,
                        user, profile, action)
        if q.first() is not None:
            return
    log.warning("Chan dinh kem ngoai pham vi: user=%s entity=%s entity_id=%s parent=%s mode=%s",
                getattr(user, "id", "?"), entity, entity_id, parent, mode)
    raise HTTPException(403, "Chứng từ của tệp nằm ngoài phạm vi được phép xem")


def reachable_from_scoped_po(db: Session, user, entity: str, entity_id: int) -> bool:
    """Tệp này có nằm trong CHUỖI chứng từ của một đơn mua hàng mình mở được không.

    Đường lùi CHỈ dùng cho lượt tải một tệp. Trang «Chứng từ» liệt kê cả chuỗi
    PO → PYC → PKS → YCKS rồi cho bấm tải từng dòng; những dòng PYC/PKS/YCKS đó
    thường nằm ngoài phạm vi vai trò của người xem đơn, nên siết thẳng là trang
    liệt kê ra tệp mà bấm vào thì 403.

    Không mở thêm gì so với hiện trạng: `GET /api/attachments/chain/zip` đã cho
    tải TRỌN chuỗi cho bất kỳ ai mở được đơn. Đường lùi này chỉ thay nút "tải cả
    gói" bằng "tải từng tệp", cùng một tập tệp.
    """
    from app.modules.purchase_order.model import PurchaseOrder
    from app.modules.survey.model import Survey

    parent = (policy(entity) or (None,))[0]
    if parent not in ("purchase_request", "survey", "survey_request"):
        #  `purchase_order` không cần đường lùi (chính nó là đơn, đã soi ở lớp
        #  trên); hợp đồng / đề nghị thanh toán / phiếu hỗ trợ / văn bản không
        #  nằm trong chuỗi.
        return False
    if not user_has_permission(db, user, "purchase_order", "read"):
        return False

    model, ids = parent_records(db, entity, entity_id)
    if model is None or not ids:
        return False
    codes = [c for (c,) in db.query(model.code).filter(model.id.in_(ids)) if c]
    if not codes:
        return False

    if parent == "purchase_request":
        cond = PurchaseOrder.pr_code.in_(codes)
    elif parent == "survey":
        cond = PurchaseOrder.survey_code.in_(codes)
    else:
        #  YCKS lùi hai chặng: yêu cầu → phiếu khảo sát → đơn.
        sv_codes = [c for (c,) in db.query(Survey.code).filter(Survey.sr_code.in_(codes)) if c]
        if not sv_codes:
            return False
        cond = PurchaseOrder.survey_code.in_(sv_codes)

    q = apply_scope(db.query(PurchaseOrder.id).filter(cond), PurchaseOrder,
                    "purchase_order", user, get_perm_profile(db, user))
    return q.first() is not None
