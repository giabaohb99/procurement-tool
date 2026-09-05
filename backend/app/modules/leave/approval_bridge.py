"""NỐI ĐƠN NGHỈ PHÉP VÀO BỘ MÁY DUYỆT DÙNG CHUNG (P-05).

Đây là đợt mà QĐ-NP5 nói tới: đơn duyệt xong thì **trừ quỹ** và **sinh giấy
GNP** vào sổ văn thư. Đơn là chứng từ nghiệp vụ, giấy là hồ sơ; giữ cả hai và
nối lại bằng `LeaveRequest.document_id`.

Bốn kết cục của bộ máy đều phải có mặt ở đây — thiếu một cái là quỹ lệch:

    approved  →  chuyển giữ chỗ sang đã dùng, sinh giấy GNP
    rejected  →  trả lại giữ chỗ, đơn khóa
    returned  →  trả lại giữ chỗ, đơn về «Trả về» để sửa rồi gửi lại
    withdrawn →  trả lại giữ chỗ, đơn về «Nháp»

⚠️ Ba kết cục sau đều **trả lại giữ chỗ**. Quên một cái thì số ngày đó treo vĩnh
viễn trong `pending_days` và người ta mất phép mà không hiểu vì sao — mà lỗi này
không có triệu chứng nào cho tới khi ai đó cộng tay lại sổ.

**Chưa khai luồng thì vẫn chạy được.** `instance_service.start()` trả `None` khi
không luồng nào áp; lúc đó đơn vẫn vào *Chờ duyệt* với `approval_instance_id = 0`
và người có quyền `leave_request.approve` bấm duyệt thẳng. Không có đường lùi này
thì cài mới xong là không ai nộp nổi đơn cho tới khi quản trị khai xong luồng.

**Và cả cái cờ nữa** (`ApprovalSwitch` cho entity `leave_request`, màn «Bật bộ máy
duyệt»). Trước đây nghỉ phép trình thẳng vào bộ máy không hỏi cờ, nên dòng công
tắc của nó bày ra cũng chỉ là nút giả. Nay `start_approval` hỏi cờ trước: TẮT thì
đi đúng đường lùi ở đoạn trên. Đó là điểm khác biệt so với "chưa khai luồng" —
đường lùi kia là *tình cờ chưa có luồng*, còn cái này là *cố ý tắt để quay về*.
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.approval import entity_hooks, flow_service, instance_service

from . import balance_service
from .constants import (LR_APPROVED, LR_DRAFT, LR_PENDING, LR_REJECTED,
                        LR_RETURNED, SESSION_TO_DOC_CODE)
from .request_model import LeaveRequest

ENTITY = "leave_request"


def entity_context(obj: LeaveRequest) -> dict:
    """Bối cảnh để chọn người duyệt và xét điều kiện rẽ nhánh.

    Chỉ những ô THẬT SỰ dùng để rẽ nhánh. Đổ cả bản ghi vào đây thì người khai
    luồng thấy hai chục tên cột và không biết chọn cái nào.

    `department_id` là của NGƯỜI NGHỈ (chép lúc lập đơn), nên bước «trưởng bộ
    phận của phòng chủ trì» trỏ đúng vào sếp trực tiếp của họ chứ không phải sếp
    của người lập hộ.
    """
    return {
        "id": obj.id,
        "employee_id": obj.employee_id,
        "leave_type_id": obj.leave_type_id,
        "company_id": obj.company_id,
        "department_id": obj.department_id,
        "total_days": obj.total_days,
    }


def is_enabled(db: Session) -> bool:
    """Bộ máy duyệt nhiều bước có đang bật cho nghỉ phép không (màn «Bật bộ máy duyệt»)."""
    return flow_service.is_enabled(db, ENTITY)


def running_instance(db: Session, request_id: int):
    return instance_service.running_instance(db, ENTITY, request_id)


def block_legacy_path(db: Session, obj: LeaveRequest) -> None:
    """Đơn đang có phiên duyệt chạy thì KHÔNG cho bấm duyệt thẳng.

    Không có chốt này thì nút duyệt một bước thành đường tắt đi vòng qua cả
    luồng — đúng lỗ hổng đã phải vá cho văn bản (xem `document/approval_bridge`).

    ⚠️ CHỈ áp cho *duyệt* và *từ chối*. **Đừng gọi nó ở đường HỦY** — hủy đơn của
    chính mình không phải là đi vòng qua luồng, và chặn ở đó thì người xin nghỉ
    đổi ý không còn cách nào rút lại (đã dựng lại được lúc chạy thử 03/09/2026:
    gửi duyệt xong bấm Hủy ăn đúng câu "đừng bấm duyệt thẳng ở đây", vô nghĩa
    với thao tác họ vừa làm). Đường hủy dùng `withdraw_running_approval` dưới đây.
    """
    if running_instance(db, obj.id) is not None:
        raise HTTPException(
            400, "Đơn này đang chạy trong luồng phê duyệt nhiều bước. "
                 "Duyệt ở màn Phê duyệt, đừng bấm duyệt thẳng ở đây.")


def withdraw_running_approval(db: Session, obj: LeaveRequest, user,
                              reason: str = "") -> None:
    """RÚT phiên duyệt đang chạy, để đơn hủy được. Không có phiên thì không làm gì.

    Người xin nghỉ đổi ý là chuyện thường, và tờ đơn lúc đó đang nằm trong luồng.
    Không rút phiên thì hủy đơn xong phiên duyệt vẫn chạy: người duyệt vẫn thấy
    việc chờ mình, ký xong thì hook `on_approved` trừ quỹ cho một tờ đơn đã hủy.

    Dùng lại `action_service.withdraw` chứ không tự đặt trạng thái phiên — luật
    "đã có người ký thì không rút được" và phần ghi dấu vết nằm ở đó. Hai luật
    của nó vọng ra tới đây, và cả hai đều đúng với nghỉ phép:

    * **chỉ người trình mới rút được** — Nhân sự muốn dẹp đơn của người khác thì
      dùng *Trả lại* / *Từ chối* ở màn Phê duyệt, nơi có ô ghi lý do;
    * **đã có người ký thì không rút** — chữ ký đã đặt không được biến mất.

    Cả hai đều ném `HTTPException` với câu đã soạn sẵn cho người dùng, nên ở đây
    không bọc lại: bọc là mất câu nói rõ vì sao.
    """
    instance = running_instance(db, obj.id)
    if instance is None:
        return

    from app.modules.approval import action_service

    #  Lý do NGƯỜI DÙNG gõ đi thẳng vào dấu vết phiên duyệt. Ghi câu chung
    #  "Người nộp hủy đơn nghỉ phép" thì dòng thời gian nói được ai và lúc nào,
    #  nhưng không nói được VÌ SAO — mà đó là câu duy nhất người đọc lại cần.
    note = (reason or "").strip()
    action_service.withdraw(
        db, instance, getattr(user, "employee_id", 0) or 0, user.id,
        f"Hủy đơn nghỉ phép: {note}" if note else "Người nộp hủy đơn nghỉ phép")


def cancel_request(db: Session, obj: LeaveRequest, reason: str, user) -> LeaveRequest:
    """HỦY đơn: rút phiên duyệt (nếu còn chạy) rồi hủy và trả quỹ.

    Đặt ở đây chứ không ở controller: đây là NGHIỆP VỤ hai bước phải đi liền
    nhau, và để ở controller thì không có bài kiểm nào chạm tới được — mà đúng
    thứ tự hai bước này là chỗ đã sai một lần (xem `block_legacy_path`).

    `withdraw` chạy hook `on_withdrawn`: quỹ đã trả lại và đơn về Nháp. `cancel`
    bên dưới chỉ trả quỹ cho đơn ở *Chờ duyệt* / *Đã duyệt* nên không trả hai
    lần — đọc `request_service.cancel` trước khi đổi thứ tự.
    """
    from . import request_service

    withdraw_running_approval(db, obj, user, reason)
    db.refresh(obj)
    return request_service.cancel(db, obj, reason, user.id)


def start_approval(db: Session, obj: LeaveRequest, user) -> int:
    """Trình đơn vào bộ máy. Trả id phiên, hoặc `0` khi cờ TẮT / không luồng nào áp.

    Hỏi cờ TRƯỚC khi mở phiên, không phải sau: `instance_service.start()` đã ghi
    bản chụp luồng và sinh việc cho người duyệt rồi thì hủy đi là vứt luôn mấy
    dòng dấu vết vừa tạo.
    """
    if not is_enabled(db):
        return 0

    instance = instance_service.start(
        db, ENTITY, obj.id, entity_context(obj),
        submitter_employee_id=obj.employee_id, actor=user.id,
        entity_code=obj.code,
        entity_title=f"Đơn nghỉ phép {obj.code} — {obj.total_days} ngày",
    )
    return instance.id if instance is not None else 0


# ── Bốn kết cục ────────────────────────────────────────────────────────────────

def _get(db: Session, request_id: int) -> LeaveRequest | None:
    obj = db.get(LeaveRequest, request_id)
    return obj if obj is not None and not obj.is_deleted else None


def _reason(instance, default: str) -> str:
    return (getattr(instance, "finish_reason", "") or default)[:500]


def _on_approved(db: Session, request_id: int, instance) -> None:
    """Ký hết các bước: trừ quỹ thật rồi sinh giấy GNP.

    Thứ tự có chủ ý — **trừ quỹ trước, sinh giấy sau**. Trừ quỹ là phần bắt buộc
    đúng; sinh giấy là phần lưu hồ sơ, và nó gọi sang cả một phân hệ khác nên
    khả năng hỏng cao hơn nhiều (thiếu loại văn bản GNP, thiếu sổ, thiếu quyền).
    Sinh giấy hỏng thì `entity_hooks.fire` ghi lý do lên phiếu duyệt và người ta
    thấy ngay; quỹ thì đã đúng rồi.
    """
    obj = _get(db, request_id)
    if obj is None or obj.status == LR_APPROVED:
        return

    balance_service.consume(db, obj.employee_id, obj.from_date.year,
                            obj.leave_type_id, obj.total_days,
                            instance.updated_by or 0)
    obj.status = LR_APPROVED
    obj.decided_at = datetime.now()
    obj.decision_note = ""
    obj.updated_by = instance.updated_by or 0
    db.flush()

    create_leave_document(db, obj, instance.updated_by or 0)


def _release_and_set(db: Session, request_id: int, instance, status: int,
                     default_reason: str) -> None:
    """Ba kết cục KHÔNG duyệt: trả lại giữ chỗ rồi đặt trạng thái.

    Gộp một hàm vì cả ba làm đúng một việc với quỹ — tách ra ba bản chép thì
    sớm muộn có một bản quên dòng `release`.
    """
    obj = _get(db, request_id)
    if obj is None or obj.status != LR_PENDING:
        return
    actor = instance.updated_by or 0
    balance_service.release(db, obj.employee_id, obj.from_date.year,
                            obj.leave_type_id, obj.total_days, actor)
    obj.status = status
    obj.decision_note = _reason(instance, default_reason)
    obj.decided_at = datetime.now()
    obj.updated_by = actor
    db.flush()


def _on_rejected(db: Session, request_id: int, instance) -> None:
    """Từ chối → đơn khóa. Muốn nghỉ nữa thì lập đơn khác, không sửa đơn cũ."""
    _release_and_set(db, request_id, instance, LR_REJECTED, "Bị từ chối")


def _on_returned(db: Session, request_id: int, instance) -> None:
    """Trả về người nộp → sửa được và gửi duyệt LẠI được.

    Khác «từ chối» đúng ở chỗ đó, và phải khác: người soạn mở đơn ra mà chỉ thấy
    «Nháp» thì không biết mình vừa bị dẹp hay đang được mời sửa lại (bài học
    24/08/2026 của phân hệ Văn thư).
    """
    _release_and_set(db, request_id, instance, LR_RETURNED, "Trả về chỉnh sửa")


def _on_withdrawn(db: Session, request_id: int, instance) -> None:
    """Người nộp tự rút → về **Nháp**, không phải «Trả về»: không ai trả gì cho họ cả."""
    _release_and_set(db, request_id, instance, LR_DRAFT, "")


entity_hooks.register(
    ENTITY,
    on_approved=_on_approved,
    on_rejected=_on_rejected,
    on_returned=_on_returned,
    on_withdrawn=_on_withdrawn,
)


def _context_by_id(db: Session, request_id: int) -> dict:
    """Dựng lại bối cảnh từ id — cho lúc SỬA LUỒNG phải tính lại người duyệt."""
    obj = _get(db, request_id)
    return entity_context(obj) if obj else {}


entity_hooks.register_subject(ENTITY, _context_by_id)


def can_read_request(db: Session, request_id: int, user) -> bool:
    """Ai được xem tờ đơn này: **trong phạm vi dữ liệu, HOẶC đang phải ký nó**.

    Vế đầu là luật cũ — dùng lại đúng phạm vi của đơn. Không có nó thì bộ máy
    trả `True` cho mọi người, và `/api/approvals/of/leave_request/<id>` phơi ra
    tên người nghỉ + lý do nghỉ cho bất kỳ ai đăng nhập (lỗ hổng đã dựng lại
    được với văn bản 25/08/2026).

    Vế sau thêm ở CR-260, và không có nó thì tính năng duyệt ngay trong màn Nghỉ
    phép không chạy được: người duyệt chặng 2 thường là Trưởng phòng Nhân sự,
    mà phạm vi dữ liệu của họ không với tới đơn của nhân viên phòng khác. Kết
    quả là bộ máy giao việc cho họ, gửi thông báo cho họ, rồi chặn họ mở tờ đơn
    ra đọc — họ phải ký một thứ không được phép nhìn.

    ⚠️ Nới đúng **lúc đang có việc treo**, không nới cho người «đã từng ký».
    Ký xong là quyền đọc thêm đó đóng lại; xem lại phiếu mình đã ký thì vào khối
    «Tôi đã duyệt gần đây», nơi dữ liệu vốn đã lọc theo chính họ. Nới rộng hơn
    thì mỗi lượt ký lại thêm vĩnh viễn một tờ vào tầm nhìn của một người, và
    phạm vi dữ liệu phình dần theo thời gian mà không ai rà lại được.
    """
    from app.core.auth import get_perm_profile
    from app.core.scoping import get_scoped
    from app.modules.approval import steps_service

    if get_scoped(db, LeaveRequest, ENTITY, request_id, user,
                  get_perm_profile(db, user)) is not None:
        return True

    return steps_service.has_pending_task(
        db, ENTITY, request_id, getattr(user, "employee_id", 0) or 0)


def _can_read(db: Session, request_id: int, user) -> bool:
    return can_read_request(db, request_id, user)


entity_hooks.register_reader(ENTITY, _can_read)


# ── Sinh giấy nghỉ phép (GNP) ──────────────────────────────────────────────────

def create_leave_document(db: Session, obj: LeaveRequest, actor: int) -> int:
    """Sinh văn bản GNP từ đơn ĐÃ DUYỆT — QĐ-NP5. Trả id văn bản, `0` nếu bỏ qua.

    Bỏ qua **im lặng** khi môi trường chưa khai loại văn bản `GNP`: phân hệ Văn
    thư là tùy chọn, và bắt mọi nơi phải có nó mới nộp được đơn nghỉ là buộc hai
    phân hệ vào nhau không cần thiết. Còn khai rồi mà sinh hỏng thì để lỗi bay
    lên — `entity_hooks.fire` bắt và ghi lý do lên phiếu duyệt.

    Giấy sinh ra ở trạng thái **Nháp** và KHÔNG tự gửi duyệt: nó đã được duyệt
    rồi, ở chính tờ đơn này. Đẩy nó vào luồng `document` lần nữa là bắt cùng một
    việc ký hai lượt.
    """
    from app.modules.doc_catalog.model import DocType
    from app.modules.document import service as doc_service
    from app.modules.document.schema import DocumentCreate
    from app.modules.document.type_metadata import LEAVE_DOC_TYPE

    if obj.document_id:
        return obj.document_id

    doc_type = (db.query(DocType)
                .filter(DocType.code == LEAVE_DOC_TYPE, DocType.is_active.is_(True))
                .first())
    if doc_type is None:
        return 0

    from .catalog_model import LeaveType

    leave_type = db.get(LeaveType, obj.leave_type_id)
    payload = DocumentCreate(
        doc_type_id=doc_type.id,
        company_id=obj.company_id,
        #  Phòng chủ trì BẮT BUỘC ở `DocumentCreate` — bước đầu luồng văn bản là
        #  «trưởng bộ phận của phòng chủ trì», thiếu là phiếu kẹt ngay khi gửi.
        department_id=obj.department_id,
        owner_employee_id=obj.employee_id,
        title=f"Giấy nghỉ phép {obj.code} — {obj.total_days} ngày",
        summary=(obj.reason or "")[:500],
        metadata={
            "employee_id": obj.employee_id,
            #  Mã CHUỖI của loại nghỉ — đây chính là mối nối giữa bảng cấu hình
            #  và ô JSON của giấy. Xem đầu `leave/constants.py`.
            "leave_type": (leave_type.code if leave_type else "annual"),
            "from_date": obj.from_date.isoformat(),
            "to_date": obj.to_date.isoformat(),
            "from_session": SESSION_TO_DOC_CODE.get(obj.from_session, "full"),
            "to_session": SESSION_TO_DOC_CODE.get(obj.to_session, "full"),
            "total_days": obj.total_days,
            "reason": obj.reason or "",
            #  Giấy GNP chỉ có MỘT ô người bàn giao (di sản CR-159). Lấy người
            #  đầu tiên; danh sách đầy đủ nằm ở `tab_leave_handover` của đơn.
            "handover_employee_id": (obj.handovers[0].employee_id
                                     if obj.handovers else 0),
            "contact_phone": obj.contact_phone or "",
        },
    )
    doc = doc_service.create_document(db, payload, actor)
    obj.document_id = doc.id
    db.flush()
    return doc.id
