"""VÒNG ĐỜI BẢN CLONE — sinh tự động lúc ban hành, và giữ cột theo dõi nói đúng.

Tách khỏi `clone_service.py` (đã 357 dòng) vì đây là hai mối lo khác nhau: bên
kia lo *tạo ra* bản clone, bên này lo *thời điểm* tạo và *trạng thái* của nó về
sau.

Hai việc:

**1. Sinh tự động khi ban hành** (chốt 20/08/2026). Trước đó phải vào thẻ Quan hệ
bấm tay, lý do ghi trong mã là *"mỗi bản clone là một văn bản thật mang số hiệu
vĩnh viễn, nên đó phải là một lần bấm có chủ ý"*. Yêu cầu nghiệp vụ đảo lại: ban
hành xuống thì pháp nhân phải **có sẵn bản nháp trong tay**, không phải chờ ai đó
nhớ bấm thêm một nút. Rủi ro cũ vẫn còn thật, nên chặn ở chỗ khác: hộp Ban hành
gọi tên từng pháp nhân sắp nhận bản riêng trước khi cho bấm.

**2. Cột theo dõi đổi theo văn bản.** `clone_status` từng chỉ đổi qua một API mà
**không màn hình nào gọi** — bản clone đã ban hành xong, có số hiệu, có hiệu lực,
mà bảng theo dõi ở văn bản gốc vẫn ghi "Đã gửi". Cột đó chính là câu *"ai đã ban
hành"*, câu quan trọng nhất của bảng, và nó nói sai suốt.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from .clone_service import (CLONE_DRAFTING, CLONE_ISSUED, CLONE_REJECTED,
                            CLONE_SUBMITTED, clones_of, create_clones)
from .model import (ALIVE_STATUSES, STATUS_DRAFT, STATUS_REJECTED,
                    STATUS_RETURNED, STATUS_SUBMITTED, Document)
from .scope_model import DIM_COMPANY, MODE_INCLUDE, DocumentScope


def clone_targets(db: Session, source: Document) -> list[int]:
    """Pháp nhân nào nhận bản riêng — suy thẳng từ các dòng PHẠM VI ÁP DỤNG.

    Bản sao chính xác của `cloneTargetsFromScopes` bên frontend, cố ý: hộp Ban
    hành gọi tên các pháp nhân sắp nhận bản riêng, và cái tên nó gọi phải đúng
    bằng cái mà backend sắp tạo ra. Hai bên tính khác nhau thì người bấm thấy một
    danh sách, hệ thống sinh một danh sách khác.

    Ba luật lọc, mỗi luật một lý do:
      * chỉ dòng **bao gồm** — dòng loại trừ nói nơi đó KHÔNG áp dụng, clone về
        đó là tạo văn bản cho nơi vừa bị loại ra;
      * chỉ chiều **pháp nhân** — clone tách theo pháp nhân, dòng phòng ban hay
        cá nhân không nói được nên tách cho ai;
      * bỏ **pháp nhân ban hành** — bản gốc đã nằm ở đó rồi.

    `include_children` cố ý KHÔNG bung ra thành các công ty con: danh sách con
    còn đổi, mà clone thì đẻ ra văn bản thật mang số hiệu vĩnh viễn — không sinh
    theo một danh sách đang trôi.
    """
    rows = (
        db.query(DocumentScope)
        .filter(DocumentScope.document_id == source.id,
                DocumentScope.dim == DIM_COMPANY,
                DocumentScope.mode == MODE_INCLUDE)
        .order_by(DocumentScope.company_id.asc())
        .all()
    )
    ids: list[int] = []
    for row in rows:
        if not row.company_id or row.company_id == source.company_id:
            continue
        if row.company_id not in ids:
            ids.append(row.company_id)
    return ids


def auto_clone_after_issue(db: Session, source: Document, actor: int) -> list[Document]:
    """Ban hành xong thì mỗi pháp nhân trong phạm vi có ngay một bản nháp.

    Gọi SAU khi việc ban hành đã commit. Lý do: bản clone là văn bản thật, ghi nó
    trong cùng transaction với việc ban hành nghĩa là clone hỏng thì kéo đổ luôn
    cả việc ban hành — mà số hiệu thì đã cấp ra rồi.

    Cũng vì thế mà hàm này **không được ném lỗi lên trên**: văn bản gốc đã ban
    hành xong và đúng. Clone hỏng thì để nguyên đó, thẻ «Bản clone ở pháp nhân
    con» vẫn còn nút bấm tay và vẫn liệt kê những nơi chưa nhận.

    Không có phạm vi pháp nhân nào ngoài nơi ban hành → trả rỗng, không làm gì.
    """
    if source.status not in ALIVE_STATUSES or not source.current_version_id:
        return []

    #  Nơi đã có bản clone thì bỏ qua — ban hành phiên bản 2.0 không được đẻ thêm
    #  một bản thứ hai cho cùng pháp nhân. `create_clones` cũng chặn bằng cách ném
    #  lỗi, nhưng ở đây ném lỗi là hỏng cả mẻ vì một nơi trùng.
    da_co = {clone.company_id for clone in clones_of(db, source.id)}
    can_clone = [cid for cid in clone_targets(db, source) if cid not in da_co]
    if not can_clone:
        return []

    try:
        return create_clones(db, source, can_clone, None, "", actor)
    except Exception:
        #  Nuốt lỗi có chủ ý — xem lý do ở phần mô tả. Bỏ dở giữa chừng thì gỡ
        #  hết phần chưa commit, để lần bấm tay sau chạy trên nền sạch.
        db.rollback()
        return []


# ── Cột theo dõi đổi theo trạng thái văn bản ─────────────────────────────────

def _trang_thai_tuong_ung(doc: Document) -> int | None:
    """Bản clone đang ở đâu trong vòng đời của chính nó."""
    if doc.status in ALIVE_STATUSES:
        return CLONE_ISSUED
    if doc.status == STATUS_SUBMITTED:
        return CLONE_SUBMITTED
    #  Bị trả về vẫn là "đang soạn" dưới mắt pháp nhân mẹ: nơi nhận còn đang làm,
    #  chỉ là vòng thứ hai. Cột này trả lời "bản của công ty đó tới đâu rồi", chứ
    #  không kể lại từng nhịp trong nội bộ họ.
    if doc.status in (STATUS_DRAFT, STATUS_RETURNED):
        return CLONE_DRAFTING
    #  Từ chối thì đúng nghĩa cột: pháp nhân con KHÔNG áp dụng bản này.
    if doc.status == STATUS_REJECTED:
        return CLONE_REJECTED
    #  Bị thay thế / hết hiệu lực / bãi bỏ: đó vẫn là một bản ĐÃ TỪNG ban hành,
    #  đừng kéo ngược về "đang soạn".
    return None


def dong_bo_trang_thai(doc: Document, actor: int) -> bool:
    """Kéo `clone_status` theo trạng thái thật của bản clone. Trả về có đổi không.

    Gọi ở đúng ba nhịp bản clone **tự nó** đi tới: gửi duyệt · ban hành · bị trả
    lại. Không gọi ở nơi khác — nhất là không gọi trên đường đọc, vì cờ *cần rà
    lại* (`CLONE_STALE`) cũng nằm chung cột này và sẽ bị xóa mất.

    Không commit: người gọi đang ở giữa một transaction của mình.
    """
    if not doc.source_document_id:
        return False

    moi = _trang_thai_tuong_ung(doc)
    if moi is None or moi == doc.clone_status:
        return False

    doc.clone_status = moi
    #  Mốc "xử lý xong" chỉ ghi MỘT LẦN, ở lần ban hành đầu tiên. Bản clone lên
    #  phiên bản 2.0 không phải là lần pháp nhân đó xử lý bản gốc.
    if moi == CLONE_ISSUED and doc.clone_handled_at is None:
        doc.clone_handled_at = datetime.now()
    doc.updated_by = actor
    return True
