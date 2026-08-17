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


def trinh_duyet(db: Session, doc: Document, actor: int):
    """Trình văn bản vào bộ máy mới. `None` = chưa khai luồng, gọi đường cũ."""
    return instance_service.bat_dau(
        db, ENTITY, doc.id, boi_canh(doc),
        submitter_employee_id=doc.drafter_employee_id or doc.owner_employee_id,
        actor=actor,
        entity_code=doc.doc_code or doc.issue_number or "",
        entity_title=doc.title or "",
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
    from . import service

    doc = db.get(Document, document_id)
    if doc is not None:
        service.reject(db, doc, instance.finish_reason or "Bị từ chối", instance.updated_by or 0)


def _khi_tra_lai(db: Session, document_id: int, instance) -> None:
    """Trả lại cũng đưa bản nháp về trạng thái sửa được — cùng đường với từ chối
    ở phía văn bản, khác nhau ở chỗ phiếu duyệt còn gửi lại được."""
    _khi_tu_choi(db, document_id, instance)


entity_hooks.register(
    ENTITY,
    on_approved=_khi_duyet_xong,
    on_rejected=_khi_tu_choi,
    on_returned=_khi_tra_lai,
)
