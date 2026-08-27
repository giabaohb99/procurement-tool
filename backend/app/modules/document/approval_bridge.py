"""NỐI VĂN BẢN VÀO BỘ MÁY DUYỆT DÙNG CHUNG (task CHUYỂN của phase 3).

Trước đây văn bản chạy bằng ba nút cứng `submit → approve/reject` — đúng bằng
"luồng một bước viết tay tạm thời" mà tài liệu xếp vào phase 2. Ở đây nó được
nối vào bộ máy nhiều bước, **sau một cái cờ**.

Ba điều giữ nguyên khi cờ TẮT hoặc chưa khai luồng nào:
  · `service.submit()` vẫn chạy y như cũ;
  · trang chi tiết vẫn có ba nút cũ;
  · không bảng nào của văn bản đổi cấu trúc.

Cờ bật mà chưa khai luồng cho `document` thì `bat_dau()` trả `None` và đường cũ
vẫn chạy — không có khe nào để văn bản rơi vào khoảng không.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.approval import entity_hooks, flow_service, instance_service

from .model import Document

ENTITY = "document"


def entity_context(doc: Document) -> dict:
    """Bối cảnh phiếu cho điều kiện rẽ nhánh và cách chọn người duyệt «lấy từ ô».

    Chỉ đưa ra những ô thật sự có nghĩa để rẽ nhánh. Đổ cả bản ghi vào đây thì
    người khai luồng thấy sáu chục tên cột và không biết chọn cái nào.
    """
    return {
        #  `id` để khai được luồng riêng cho MỘT văn bản cụ thể — bộ chọn "Áp
        #  dụng cho" ở giao diện sinh điều kiện `id in [...]`. Thiếu ô này thì
        #  lựa chọn đó không bao giờ khớp và luồng lặng lẽ không chạy.
        "id": doc.id,
        "doc_type_id": doc.doc_type_id,
        "company_id": doc.company_id,
        "department_id": doc.department_id,
        "secrecy_level": doc.secrecy_level,
        "urgency": doc.urgency,
        "owner_employee_id": doc.owner_employee_id,
        "drafter_employee_id": doc.drafter_employee_id,
        "signer_employee_id": doc.signer_employee_id,
    }


def is_enabled(db: Session) -> bool:
    return flow_service.is_enabled(db, ENTITY)


def running_instance(db: Session, document_id: int):
    """Phiên duyệt nhiều bước còn mở của văn bản này, `None` nếu không có."""
    return instance_service.running_instance(db, ENTITY, document_id)


def latest_instance(db: Session, document_id: int):
    """Phiên duyệt GẦN NHẤT của văn bản, kể cả phiên đã kết thúc.

    Khác `phien_dang_chay`: dùng để GIẢI THÍCH, không để chặn — xem
    `chan_duong_cu`.
    """
    from app.modules.approval.instance_model import ApprovalInstance

    return (db.query(ApprovalInstance)
            .filter(ApprovalInstance.entity == ENTITY,
                    ApprovalInstance.entity_id == document_id)
            .order_by(ApprovalInstance.id.desc())
            .first())


def block_legacy_path(db: Session, doc: Document) -> None:
    """Khóa hai nút duyệt MỘT BƯỚC khi phiếu đang chạy trong bộ máy nhiều bước.

    Không có chốt này thì bất kỳ ai có quyền `document.approve` cũng ban hành
    được một văn bản đang nằm ở chặng 1 — đã bắt được đúng ca đó: văn bản được
    cấp số và chuyển hiệu lực trong khi phiên duyệt vẫn chờ trưởng bộ phận ký,
    còn phiên thì tiếp tục chạy trên một văn bản đã ban hành.

    Chốt đặt ở controller chứ không ở `service.approve()`: chính bộ máy nhiều
    bước gọi `service.approve()` khi duyệt xong, đặt ở đó là nó tự chặn mình.
    """
    instance = running_instance(db, doc.id)
    if instance is not None:
        raise HTTPException(
            400,
            "Văn bản này đang chạy trong luồng duyệt nhiều bước — xử lý ở màn "
            "«Việc của tôi» chứ không ban hành thẳng ở đây.",
        )
    _clarify_instance_finished(db, doc)


def _clarify_instance_finished(db: Session, doc: Document) -> None:
    """Nói RÕ vì sao không ban hành được, thay câu «Không có bản nào đang chờ duyệt».

    Ca người dùng gặp (24/08/2026): người duyệt bấm *Trả lại*, rồi ai đó bấm
    *Duyệt và ban hành* và nhận đúng một dòng đỏ **«Không có bản nào đang chờ
    duyệt»** — câu này đọc như hệ hỏng, trong khi sự thật là phiên duyệt vừa kết
    thúc bằng *Trả lại* nên chẳng còn gì để ban hành.

    ⚠️ **Không chặn thêm bất cứ đường nào.** Chỉ nói lại cho tử tế đúng cái lỗi
    mà `service.approve()` / `service.tu_choi()` sắp ném ra: chốt duy nhất là
    "bản đang mở KHÔNG ở trạng thái chờ duyệt", tức đường cũ vốn đã hỏng dù có
    hàm này hay không. Chờ duyệt thật thì hàm này im lặng — kể cả khi văn bản có
    một phiên duyệt cũ đã đóng (bị trả về, sửa xong rồi gửi duyệt lại bằng đường
    một bước vì luồng nhiều bước không còn khớp).
    """
    from .service import open_version
    from .version_model import VERSION_SUBMITTED

    version = open_version(db, doc)
    if version is not None and version.status == VERSION_SUBMITTED:
        return

    from app.modules.approval.instance_model import (INSTANCE_REJECTED,
                                                     INSTANCE_RETURNED,
                                                     INSTANCE_STATUS_LABELS,
                                                     INSTANCE_WITHDRAWN)

    instance = latest_instance(db, doc.id)
    #  CHỈ ba kết cục «không đi tiếp được» mới cần giải thích. Phiên **đã duyệt**
    #  thì im lặng: văn bản đã ban hành rồi, và chốt cũ có một bài kiểm giữ đúng
    #  điều đó — hết phiên là đường một bước dùng lại được bình thường
    #  (`test_van_ban_dang_duyet_khong_di_tat.py`).
    if instance is None or instance.status not in (
            INSTANCE_RETURNED, INSTANCE_REJECTED, INSTANCE_WITHDRAWN):
        return

    label = INSTANCE_STATUS_LABELS.get(instance.status, "đã kết thúc")
    days = instance.finished_at.strftime("%d/%m/%Y %H:%M") if instance.finished_at else ""
    reason = f" — lý do: {instance.finish_reason}" if instance.finish_reason else ""
    raise HTTPException(
        400,
        f"Không ban hành được: phiên duyệt của văn bản này đã kết thúc ở trạng thái "
        f"«{label}»{f' lúc {days}' if days else ''}{reason}. "
        "Người soạn sửa lại rồi gửi duyệt lần nữa thì mới có bản để ban hành.",
    )


def _employee_id_of_user(db: Session, actor: int) -> int | None:
    """Tài khoản đang bấm là nhân sự nào. `None` khi tài khoản chưa gắn hồ sơ."""
    from app.modules.user.model import User

    if not actor:
        return None
    row = db.query(User.employee_id).filter(User.id == actor).first()
    return row[0] if row and row[0] else None


def submit_for_approval(db: Session, doc: Document, actor: int):
    """Trình văn bản vào bộ máy mới. `None` = chưa khai luồng, gọi đường cũ.

    **Người nộp = người BẤM GỬI DUYỆT**, không phải người ghi trên phiếu.

    ⚠️ Trước 20/08/2026 chỗ này lấy `drafter_employee_id or owner_employee_id`,
    và nó chặn đứng luồng clone: bản clone chép hai ô đó **từ bản gốc**, tức
    người của Tập đoàn. Văn thư SAM bấm gửi duyệt bản của SAM thì bộ máy lại đi
    tìm trưởng bộ phận của người bên Tập đoàn — không ra ai, `on_no_approver` của
    luồng mặc định là *dừng phiếu*, nên **phiếu kẹt và pháp nhân con không ban
    hành được văn bản của mình**. Dựng lại được trên Chrome với tài khoản `VTSAM`.

    Lấy người bấm cũng đúng với ý đã ghi ở `approver_resolver._phong_cua_nguoi_nop`:
    *"thu mua lập phiếu hộ bộ phận khác thì trưởng bộ phận người nộp phải là
    trưởng của thu mua, không phải trưởng phòng ghi trên phiếu"*. Hai chỗ giờ mới
    nói cùng một câu.

    Vẫn lùi về ô trên phiếu khi tài khoản chưa gắn hồ sơ nhân sự (tài khoản hệ
    thống, tác vụ nền) — thà định tuyến theo phiếu còn hơn không định tuyến được.
    """
    return instance_service.start(
        db, ENTITY, doc.id, entity_context(doc),
        submitter_employee_id=(
            _employee_id_of_user(db, actor)
            or doc.drafter_employee_id
            or doc.owner_employee_id
        ),
        actor=actor,
        entity_code=doc.doc_code or doc.issue_number or "",
        entity_title=doc.title or "",
        #  Bản clone là văn bản pháp lý riêng của nơi nhận. Không có luồng riêng
        #  thì phải chặn từ trước bằng `dam_bao_co_luong_rieng()`, tuyệt đối
        #  không rơi về luồng dùng chung của bản gốc.
        company_flow_only=bool(doc.source_document_id),
    )


def ensure_dedicated_flow(db: Session, doc: Document) -> None:
    """Bản clone phải có luồng khớp ĐÚNG pháp nhân trước khi đổi trạng thái.

    Gọi trước `service.submit()` commit. Chặn sau commit thì API báo lỗi nhưng
    văn bản đã thành «Đang duyệt» mà không có phiên nào — tình trạng không màn
    hình nào sửa được.
    """
    if not doc.source_document_id:
        return
    if flow_service.pick_flow(
            db, ENTITY, entity_context(doc), company_only=True) is not None:
        return

    from app.modules.company.model import Company

    company = db.get(Company, doc.company_id) if doc.company_id else None
    name = company.name if company else f"#{doc.company_id}"
    raise HTTPException(
        400,
        f"Pháp nhân «{name}» chưa có luồng duyệt Văn bản riêng. "
        "Hãy tạo luồng và chọn đúng «Pháp nhân áp dụng» trước khi gửi duyệt.",
    )


# ── Hàm chạy khi phiên duyệt kết thúc ───────────────────────────────────────

def _write_log(db: Session, document_id: int, instance, action: str, message: str) -> None:
    """Ghi kết cục vào NHẬT KÝ THAO TÁC của chính văn bản.

    ⚠️ Thiếu nhịp này thì thẻ *Lịch sử thao tác* của văn bản dừng lại ở dòng
    «Gửi duyệt»: người soạn mở ra thấy trạng thái đã thành «Trả về» mà không có
    một dòng nào nói ai trả, lúc nào, vì sao (lỗi khách báo 24/08/2026). Dấu vết
    phiên duyệt có ghi, nhưng đó là thẻ khác — và nó biến mất khỏi tầm mắt ngay
    khi người ta gửi duyệt lại lần sau.

    Đặt ở đây chứ không ở `service`: đường ĐI QUA CONTROLLER (luồng một bước) đã
    tự ghi nhật ký rồi, còn đường qua bộ máy nhiều bước thì không đi qua
    controller nào của văn bản cả.
    """
    from app.core.audit import record

    record(db, instance.updated_by or 0, ENTITY, document_id, action, message)


def _reason(instance, default: str) -> str:
    return (instance.finish_reason or "").strip() or default


def _on_approved(db: Session, document_id: int, instance) -> None:
    """Ký hết các bước. Ban hành LUÔN hay DỪNG LẠI chờ người soạn bấm?

    Câu trả lời nằm ở cột `auto_issue_after_approval` của **loại văn bản**:

    * bật (mặc định, mọi loại đang chạy) → ban hành luôn như trước: cấp số, khóa
      phiên bản, chuyển hiệu lực;
    * tắt → văn bản dừng ở **Chờ ban hành**. Người soạn thảo mở ra, chọn hộp thư
      gửi thông báo rồi bấm *Ban hành* (26/08/2026).

    Dùng lại đúng `service.approve()` ở nhánh trên chứ không viết lại luật ban
    hành ở đây — viết lại là hai đường ban hành khác nhau, và một trong hai sẽ
    quên cấp số hoặc quên khóa phiên bản.
    """
    from . import service

    doc = db.get(Document, document_id)
    if doc is None:
        return

    if not _auto_issue(db, doc):
        service.mark_pending_issue(db, doc, instance.updated_by or 0)
        _write_log(db, document_id, instance, "approved",
                     "Xong hết các bước của luồng — chờ người soạn bấm Ban hành")
        return

    service.approve(db, doc, instance.updated_by or 0)
    #  Câu ghi KHÔNG lặp lại nhãn hành động: giao diện đã in "Duyệt: …" nên
    #  ghi thêm chữ "duyệt" nữa thành "Duyệt: Duyệt xong…".
    _write_log(db, document_id, instance, "approved",
                 "Xong hết các bước của luồng — ban hành")


def _auto_issue(db: Session, doc: Document) -> bool:
    """Loại của văn bản này có cho duyệt xong ban hành luôn không.

    Loại đã bị xóa khỏi danh mục thì trả `True` — giữ đúng hành vi cũ. Dừng một
    văn bản ở «Chờ ban hành» vì lý do không đọc được cấu hình là để nó kẹt mà
    không ai hiểu vì sao.
    """
    from app.modules.doc_catalog.model import DocType

    kind = db.get(DocType, doc.doc_type_id) if doc.doc_type_id else None
    return True if kind is None else bool(kind.auto_issue_after_approval)


def _on_rejected(db: Session, document_id: int, instance) -> None:
    """Từ chối → văn bản **Đã từ chối**: khóa sửa, làm lại thì sao chép.

    Từ 24/08/2026 đây KHÔNG còn cùng đường với «trả lại». Trước đó cả hai đều đổ
    về Nháp, nên người soạn mở văn bản ra chỉ thấy «Nháp» và không cách nào biết
    nó vừa bị dẹp hay đang được mời sửa lại.
    """
    from . import service

    doc = db.get(Document, document_id)
    if doc is not None:
        reason = _reason(instance, "Bị từ chối")
        service.reject(db, doc, reason, instance.updated_by or 0)
        _write_log(db, document_id, instance, "rejected", reason)


def _on_returned(db: Session, document_id: int, instance) -> None:
    """Trả lại → văn bản **Trả về**: sửa được và gửi duyệt lại được.

    Chỉ chạy khi phiếu trả về TẬN người nộp (`INSTANCE_RETURNED`). Trả về một
    bước phía trước thì phiên vẫn chạy, bộ máy không gọi hook nào — đúng vậy, văn
    bản phải giữ nguyên «Đang duyệt» vì nó vẫn đang trong luồng.
    """
    from . import service

    doc = db.get(Document, document_id)
    if doc is not None:
        reason = _reason(instance, "Bị trả về")
        service.send_back(db, doc, reason, instance.updated_by or 0)
        _write_log(db, document_id, instance, "returned", reason)


def _on_withdrawn(db: Session, document_id: int, instance) -> None:
    """Người nộp tự rút phiếu → văn bản VỀ NHÁP, sửa rồi gửi duyệt lại từ đầu.

    Phải có nhịp này, không thì rút xong văn bản kẹt ở *đang duyệt*: gửi duyệt
    lại không được (đường gửi chỉ nhận bản nháp), mà nút ban hành MỘT BƯỚC lại
    mở ra vì `chan_duong_cu` chỉ khóa khi phiên còn đang chạy — thành đường tắt
    ban hành không ai ký. Dùng lại `service.rut_phieu()` chứ không tự đặt trạng
    thái: luật "bản đầu đổi trạng thái, bản thứ hai giữ nguyên vì bản trước còn
    hiệu lực" nằm ở đó, chép ra đây là sớm muộn hai bên lệch nhau.

    Về **Nháp** chứ không phải «Trả về»: chính người nộp rút, không ai trả gì cho
    họ cả.
    """
    from . import service

    doc = db.get(Document, document_id)
    if doc is not None:
        reason = _reason(instance, "")
        service.withdraw_document(db, doc, reason, instance.updated_by or 0)
        _write_log(db, document_id, instance, "withdrawn", reason or "Người nộp tự rút")


entity_hooks.register(
    ENTITY,
    on_approved=_on_approved,
    on_rejected=_on_rejected,
    on_returned=_on_returned,
    on_withdrawn=_on_withdrawn,
)


def _context_by_id(db: Session, document_id: int) -> dict:
    """Dựng lại bối cảnh từ id — cho lúc SỬA LUỒNG phải tính lại người duyệt.

    Khác `boi_canh(doc)` ở trên đúng một chỗ: ở đây bộ máy chỉ cầm cái id, vì
    người quản trị đang đứng ở màn Luồng duyệt chứ không mở văn bản nào.
    """
    doc = db.get(Document, document_id)
    return entity_context(doc) if doc else {}


entity_hooks.register_subject(ENTITY, _context_by_id)


def _can_read_document(db: Session, document_id: int, user) -> bool:
    """Người này có đọc được văn bản của phiếu duyệt đó không.

    Bộ máy duyệt hỏi qua đây để biết ai được xem phiếu và ai được ghi ý kiến —
    xem `entity_hooks._READERS`. Dùng lại đúng luật đọc của văn bản
    (`access_service.can`), không chép một bản luật thứ hai.
    """
    from app.core.auth import get_perm_profile

    from . import access_service

    doc = db.get(Document, document_id)
    if doc is None:
        return False
    return access_service.can(db, doc, user, get_perm_profile(db, user), "read")


entity_hooks.register_reader(ENTITY, _can_read_document)
