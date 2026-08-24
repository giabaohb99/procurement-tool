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


def boi_canh(doc: Document) -> dict:
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


def dang_bat(db: Session) -> bool:
    return flow_service.is_enabled(db, ENTITY)


def phien_dang_chay(db: Session, document_id: int):
    """Phiên duyệt nhiều bước còn mở của văn bản này, `None` nếu không có."""
    return instance_service.phien_dang_chay(db, ENTITY, document_id)


def chan_duong_cu(db: Session, doc: Document) -> None:
    """Khóa hai nút duyệt MỘT BƯỚC khi phiếu đang chạy trong bộ máy nhiều bước.

    Không có chốt này thì bất kỳ ai có quyền `document.approve` cũng ban hành
    được một văn bản đang nằm ở chặng 1 — đã bắt được đúng ca đó: văn bản được
    cấp số và chuyển hiệu lực trong khi phiên duyệt vẫn chờ trưởng bộ phận ký,
    còn phiên thì tiếp tục chạy trên một văn bản đã ban hành.

    Chốt đặt ở controller chứ không ở `service.approve()`: chính bộ máy nhiều
    bước gọi `service.approve()` khi duyệt xong, đặt ở đó là nó tự chặn mình.
    """
    phien = phien_dang_chay(db, doc.id)
    if phien is None:
        return
    raise HTTPException(
        400,
        "Văn bản này đang chạy trong luồng duyệt nhiều bước — xử lý ở màn "
        "«Việc của tôi» chứ không ban hành thẳng ở đây.",
    )


def _nhan_su_cua_tai_khoan(db: Session, actor: int) -> int | None:
    """Tài khoản đang bấm là nhân sự nào. `None` khi tài khoản chưa gắn hồ sơ."""
    from app.modules.user.model import User

    if not actor:
        return None
    row = db.query(User.employee_id).filter(User.id == actor).first()
    return row[0] if row and row[0] else None


def trinh_duyet(db: Session, doc: Document, actor: int):
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
    return instance_service.bat_dau(
        db, ENTITY, doc.id, boi_canh(doc),
        submitter_employee_id=(
            _nhan_su_cua_tai_khoan(db, actor)
            or doc.drafter_employee_id
            or doc.owner_employee_id
        ),
        actor=actor,
        entity_code=doc.doc_code or doc.issue_number or "",
        entity_title=doc.title or "",
        #  Bản clone là văn bản pháp lý riêng của nơi nhận. Không có luồng riêng
        #  thì phải chặn từ trước bằng `dam_bao_co_luong_rieng()`, tuyệt đối
        #  không rơi về luồng dùng chung của bản gốc.
        chi_luong_phap_nhan=bool(doc.source_document_id),
    )


def dam_bao_co_luong_rieng(db: Session, doc: Document) -> None:
    """Bản clone phải có luồng khớp ĐÚNG pháp nhân trước khi đổi trạng thái.

    Gọi trước `service.submit()` commit. Chặn sau commit thì API báo lỗi nhưng
    văn bản đã thành «Đang duyệt» mà không có phiên nào — tình trạng không màn
    hình nào sửa được.
    """
    if not doc.source_document_id:
        return
    if flow_service.chon_luong(
            db, ENTITY, boi_canh(doc), chi_phap_nhan=True) is not None:
        return

    from app.modules.company.model import Company

    company = db.get(Company, doc.company_id) if doc.company_id else None
    ten = company.name if company else f"#{doc.company_id}"
    raise HTTPException(
        400,
        f"Pháp nhân «{ten}» chưa có luồng duyệt Văn bản riêng. "
        "Hãy tạo luồng và chọn đúng «Pháp nhân áp dụng» trước khi gửi duyệt.",
    )


# ── Hàm chạy khi phiên duyệt kết thúc ───────────────────────────────────────

def _khi_duyet_xong(db: Session, document_id: int, instance) -> None:
    """Duyệt hết các bước = ban hành: cấp số, khóa phiên bản, chuyển hiệu lực.

    Dùng lại đúng `service.approve()` chứ không viết lại luật ban hành ở đây —
    viết lại là hai đường ban hành khác nhau, và một trong hai sẽ quên cấp số
    hoặc quên khóa phiên bản.
    """
    from . import service

    doc = db.get(Document, document_id)
    if doc is not None:
        service.approve(db, doc, instance.updated_by or 0)


def _khi_tu_choi(db: Session, document_id: int, instance) -> None:
    """Từ chối → văn bản **Đã từ chối**: khóa sửa, làm lại thì sao chép.

    Từ 24/08/2026 đây KHÔNG còn cùng đường với «trả lại». Trước đó cả hai đều đổ
    về Nháp, nên người soạn mở văn bản ra chỉ thấy «Nháp» và không cách nào biết
    nó vừa bị dẹp hay đang được mời sửa lại.
    """
    from . import service

    doc = db.get(Document, document_id)
    if doc is not None:
        service.tu_choi(db, doc, instance.finish_reason or "Bị từ chối",
                        instance.updated_by or 0)


def _khi_tra_lai(db: Session, document_id: int, instance) -> None:
    """Trả lại → văn bản **Trả về**: sửa được và gửi duyệt lại được.

    Chỉ chạy khi phiếu trả về TẬN người nộp (`INSTANCE_RETURNED`). Trả về một
    bước phía trước thì phiên vẫn chạy, bộ máy không gọi hook nào — đúng vậy, văn
    bản phải giữ nguyên «Đang duyệt» vì nó vẫn đang trong luồng.
    """
    from . import service

    doc = db.get(Document, document_id)
    if doc is not None:
        service.tra_lai(db, doc, instance.finish_reason or "Bị trả về",
                        instance.updated_by or 0)


def _khi_rut_lai(db: Session, document_id: int, instance) -> None:
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
        service.rut_phieu(db, doc, instance.finish_reason or "", instance.updated_by or 0)


entity_hooks.register(
    ENTITY,
    on_approved=_khi_duyet_xong,
    on_rejected=_khi_tu_choi,
    on_returned=_khi_tra_lai,
    on_withdrawn=_khi_rut_lai,
)


def _boi_canh_theo_id(db: Session, document_id: int) -> dict:
    """Dựng lại bối cảnh từ id — cho lúc SỬA LUỒNG phải tính lại người duyệt.

    Khác `boi_canh(doc)` ở trên đúng một chỗ: ở đây bộ máy chỉ cầm cái id, vì
    người quản trị đang đứng ở màn Luồng duyệt chứ không mở văn bản nào.
    """
    doc = db.get(Document, document_id)
    return boi_canh(doc) if doc else {}


entity_hooks.register_subject(ENTITY, _boi_canh_theo_id)
