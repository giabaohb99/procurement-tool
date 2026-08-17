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


def apply_supersede(db: Session, doc: Document, actor: int) -> int:
    """Ban hành `doc` → đổi trạng thái các văn bản cũ mà nó thay thế / bãi bỏ.

    Nhật ký ghi trên chính VĂN BẢN CŨ chứ không phải văn bản mới: người sáu tháng
    sau mở Quyết định 15 và hỏi "vì sao nó thành bị thay thế" phải thấy câu trả
    lời ngay trong sổ nhật ký của nó.
    """
    from app.core.audit import record

    dem = 0

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
        dem += 1
    return dem


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
