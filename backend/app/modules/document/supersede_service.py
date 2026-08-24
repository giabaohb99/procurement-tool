"""NHÃN "ĐÃ BỊ SỬA ĐỔI" và ba tác động tự động của quan hệ (J10).

Ba biến thể của quan hệ, tác động lên văn bản CŨ khác hẳn nhau (`van-thu` mục
"Ba biến thể của quan hệ"):

| Quan hệ | Tác động lên văn bản cũ |
|---|---|
| 2 sửa đổi  | **KHÔNG đổi trạng thái** — phần không bị sửa vẫn có hiệu lực |
| 1 thay thế | Văn bản cũ chuyển `status = 5` bị thay thế |
| 9 bãi bỏ   | Văn bản cũ chuyển `status = 7` bãi bỏ |

Hệ thống làm ba việc này **tự động khi văn bản mới được ban hành**, dựa vào cột
`relation`. Người dùng không phải nhớ đi đổi trạng thái văn bản cũ bằng tay —
và cũng **không được phép** đổi bằng tay.

**Vì sao cái nhãn là bắt buộc, không phải tùy chọn.** Dòng "sửa đổi" ở trên
KHÔNG đổi trạng thái, nên Quyết định 15 bị sửa Điều 5 vẫn hiện "Có hiệu lực"
trên màn hình. Người mở nó đọc Điều 5 cũ rồi làm sai — và **không ai phát hiện
ra**, vì mọi thứ trông vẫn đúng. Đây là chỗ nguy hiểm nhất của cả nhóm J.
"""
from datetime import date

from sqlalchemy.orm import Session

from app.modules.doc_catalog.link_rule_model import (RELATION_AMEND,
                                                     RELATION_LABELS,
                                                     RELATION_REPLACE,
                                                     RELATION_REVOKE,
                                                     RELATION_SUPPLEMENT)

from .link_model import DocumentLink
from .model import (ALIVE_STATUSES, STATUS_REPLACED, STATUS_REVOKED,
                    STATUS_LABELS, Document)

#  Quan hệ nào làm văn bản cũ đổi trạng thái, và đổi sang cái gì.
#  «Sửa đổi» và «bổ sung» CỐ Ý không có mặt: chúng chỉ đụng một phần nội dung,
#  phần còn lại vẫn có hiệu lực.
SUPERSEDE_EFFECT = {
    RELATION_REPLACE: STATUS_REPLACED,
    RELATION_REVOKE: STATUS_REVOKED,
}

#  Quan hệ nào sinh ra nhãn cảnh báo trên văn bản cũ. Rộng hơn bảng trên: kể cả
#  loại không đổi trạng thái vẫn phải gắn nhãn — thật ra ĐÓ mới là loại nguy
#  hiểm, vì văn bản vẫn hiện "có hiệu lực".
AMENDED_BY_RELATIONS = (
    RELATION_REPLACE, RELATION_AMEND, RELATION_SUPPLEMENT, RELATION_REVOKE,
)


def apply_supersede(db: Session, doc: Document, actor: int) -> list[Document]:
    """Ban hành `doc` → đổi trạng thái các văn bản cũ mà nó thay thế / bãi bỏ.

    Nhật ký ghi trên chính VĂN BẢN CŨ chứ không phải văn bản mới: người sáu tháng
    sau mở Quyết định 15 và hỏi "vì sao nó thành bị thay thế" phải thấy câu trả
    lời ngay trong sổ nhật ký của nó.

    Trả về **danh sách văn bản vừa bị BÃI BỎ** để chỗ gọi gửi thông báo cho pháp
    nhân con SAU KHI commit. Không tự gửi ở đây: hàm này chạy giữa transaction
    ban hành, mà gửi thư thì phải commit trước (`EmailLog` phải tồn tại trước khi
    tác vụ nền đọc tới) — commit ở đây là chốt nửa chừng một việc chưa xong.

    ⚠️ **Đường này phải cho ra cùng kết quả với `service.revoke`.** Trước
    24/08/2026 nó chỉ đổi mỗi `status`: không đóng `expire_date`, không chạy
    `apply_obsolete`, không báo ai — nên cùng một chuyện *"văn bản bị bãi bỏ"* mà
    đi hai đường khác nhau lại ra hai kết quả khác nhau.
    """
    from app.core.audit import record

    from .parent_change_service import apply_obsolete

    bi_bai_bo: list[Document] = []

    links = (
        db.query(DocumentLink)
        .filter(DocumentLink.source_document_id == doc.id,
                DocumentLink.relation.in_(tuple(SUPERSEDE_EFFECT)))
        .all()
    )
    for link in links:
        cu = db.get(Document, link.target_document_id)
        if cu is None:
            continue
        moi = SUPERSEDE_EFFECT[link.relation]
        #  Chỉ đụng văn bản CÒN SỐNG. Văn bản đã bãi bỏ từ trước thì để nguyên —
        #  ghi đè là xóa mất lý do bãi bỏ thật của nó.
        if cu.status not in ALIVE_STATUSES or cu.status == moi:
            continue
        cu.status = moi
        record(db, actor, "document", cu.id, "update",
               f"{RELATION_LABELS.get(link.relation, '')} bởi "
               f"{doc.doc_code or doc.issue_number or doc.title}"
               f" → {STATUS_LABELS.get(moi, '')}")

        if moi == STATUS_REVOKED:
            #  Ngày bãi bỏ = ngày hết hiệu lực, y như `service.revoke`.
            cu.expire_date = date.today()
            #  ⚠️ PHẢI ghi `updated_by`. Luật quyền xem sau khi bãi bỏ coi cột
            #  này là "người bãi bỏ" (`revoke_access.py`); không ghi thì nó vẫn
            #  là người SỬA CUỐI CÙNG trước đó — và người đó giữ nguyên quyền xem
            #  một văn bản lẽ ra đã bị giấu khỏi họ. Dựng lại được: văn bản 339
            #  do admin tạo, DEMO_MANAGER sửa lần cuối; bãi bỏ theo quan hệ xong
            #  DEMO_MANAGER vẫn `can_read=True`.
            cu.updated_by = actor
            #  E08 — văn bản con xử lý theo cột `on_parent_obsolete`. Thiếu dòng
            #  này thì bãi bỏ bằng quan hệ không kéo con theo, còn bãi bỏ bằng
            #  nút bấm thì có.
            apply_obsolete(db, cu)
            bi_bai_bo.append(cu)

    return bi_bai_bo


def amended_by(db: Session, document_id: int) -> list[dict]:
    """J10 — những văn bản ĐÃ BAN HÀNH đang sửa đổi / thay thế / bãi bỏ văn bản này.

    Chỉ tính văn bản đã ban hành: một dự thảo sửa đổi còn nằm trong ngăn kéo thì
    chưa đổi gì cả, gắn nhãn sớm là dọa người đọc bằng một thứ chưa có hiệu lực.
    """
    links = (
        db.query(DocumentLink)
        .filter(DocumentLink.target_document_id == document_id,
                DocumentLink.relation.in_(AMENDED_BY_RELATIONS))
        .order_by(DocumentLink.id.asc())
        .all()
    )

    ket_qua: list[dict] = []
    for link in links:
        moi = db.get(Document, link.source_document_id)
        if moi is None or moi.status not in ALIVE_STATUSES:
            continue
        ket_qua.append({
            "document_id": moi.id,
            "title": moi.title,
            "display_code": moi.doc_code or moi.issue_number or "",
            "relation": link.relation,
            "relation_label": RELATION_LABELS.get(link.relation, str(link.relation)),
            "effective_date": moi.effective_date,
            "status_label": STATUS_LABELS.get(moi.status, str(moi.status)),
        })
    return ket_qua
