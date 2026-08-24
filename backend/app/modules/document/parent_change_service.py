"""TÁC ĐỘNG KHI VĂN BẢN CHA THAY ĐỔI (E07, E08).

Hai việc KHÁC NHAU, hai cột cấu hình riêng — đừng gộp:

  - **E07** cha lên phiên bản mới → `rule.on_parent_new_version`
  - **E08** cha bị bãi bỏ         → `rule.on_parent_obsolete`

Nguyên tắc xuyên suốt, tài liệu nhắc hai lần: **hệ thống chỉ liệt kê và đánh
dấu, không tự sửa nội dung văn bản con.** Người rà quyết định, và quyết định đó
đi vào nhật ký thao tác. Tự sửa hộ là sửa một văn bản đã ban hành mà không ai
ký tên chịu trách nhiệm.

Trước tệp này, hai cột trên là **cột chết** — chỉ quan hệ "trích từ" đọc tới
chúng, và đọc bằng giá trị khóa cứng chứ không qua bảng quy tắc.
"""
from sqlalchemy.orm import Session

from app.modules.doc_catalog.link_rule_model import (NEW_VERSION_ASK,
                                                     NEW_VERSION_REVIEW,
                                                     OBSOLETE_EXPIRE,
                                                     OBSOLETE_NOTHING,
                                                     OBSOLETE_REVIEW,
                                                     RELATION_EXCERPT,
                                                     RELATION_LABELS,
                                                     RELATION_REPLACE,
                                                     RELATION_REVOKE,
                                                     DocTypeLinkRule)

from .link_model import DocumentLink
from .model import STATUS_EXPIRED, Document

#  Quan hệ "trích từ" bị khóa cứng ba cột (E11) và thường KHÔNG có dòng quy tắc
#  nào — bản trích do `excerpt_service` sinh ra, không đi qua bảng quy tắc. Nên
#  khi không tìm thấy quy tắc, đây là giá trị áp cho nó.
EXCERPT_FALLBACK = {
    "on_parent_new_version": NEW_VERSION_REVIEW,
    "on_parent_obsolete": OBSOLETE_EXPIRE,
}


#  HAI QUAN HỆ NGƯỢC CHIỀU — trỏ vào cha nhưng KHÔNG phải con.
#
#  «A thay thế B» và «A bãi bỏ B» nghĩa là A **khai tử** B; A là công cụ, không
#  phải kẻ phụ thuộc. Mọi quan hệ còn lại (sửa đổi · bổ sung · hướng dẫn · kèm
#  theo · thuộc về · căn cứ theo · tham chiếu · trích từ) đều mang nghĩa "tôi
#  dựa vào anh", nên cha chết thì con phải rà lại.
#
#  ⚠️ Không loại hai cái này ra thì sinh **báo động tự trỏ vào mình**, dựng lại
#  được trên dữ liệu thật (văn bản #368 «Thông báo bãi bỏ Văn bản nghỉ lễ 02/09»
#  ngày 24/08/2026): ban hành thông báo bãi bỏ → nó bãi bỏ văn bản #339 → E08
#  quét mọi quan hệ trỏ vào #339, gặp luôn quan hệ *bãi bỏ* của chính #368 →
#  đánh dấu #368 «Văn bản cha «…» đã bị bãi bỏ, rà lại đi». Nó vừa bãi bỏ cái
#  đó xong. Và vì MỌI thông báo bãi bỏ đều có đúng quan hệ này nên đây là báo
#  động sai **có hệ thống**, không phải ca hiếm — đúng thứ làm người dùng quen
#  mắt với băng vàng rồi thôi không đọc nữa (xem CR-141).
QUAN_HE_NGUOC_CHIEU = (RELATION_REPLACE, RELATION_REVOKE)


def _children_links(db: Session, parent_id: int) -> list[DocumentLink]:
    """Văn bản con = văn bản TRỎ VÀO cha, TRỪ hai quan hệ ngược chiều.

    "Biểu mẫu thuộc về Quy trình" ghi Biểu mẫu là nguồn, nên con nằm ở chiều đi
    vào — xem `QUAN_HE_NGUOC_CHIEU` cho hai ngoại lệ.
    """
    return (
        db.query(DocumentLink)
        .filter(DocumentLink.target_document_id == parent_id,
                DocumentLink.relation.notin_(QUAN_HE_NGUOC_CHIEU))
        .order_by(DocumentLink.relation.asc(), DocumentLink.id.asc())
        .all()
    )


def _rule_of(db: Session, link: DocumentLink, child: Document,
             parent: Document) -> DocTypeLinkRule | None:
    if link.rule_id:
        return db.get(DocTypeLinkRule, link.rule_id)
    #  Quan hệ khai trước khi có quy tắc, hoặc «tham chiếu» vốn không cần quy
    #  tắc — tra lại theo cặp loại.
    rules = (
        db.query(DocTypeLinkRule)
        .filter(DocTypeLinkRule.source_type_id == child.doc_type_id,
                DocTypeLinkRule.relation == link.relation)
        .all()
    )
    exact = [r for r in rules if r.target_type_id == parent.doc_type_id]
    if exact:
        return exact[0]
    wildcard = [r for r in rules if r.target_type_id is None]
    return wildcard[0] if wildcard else None


def _hanh_dong(db: Session, link: DocumentLink, child: Document, parent: Document,
               cot: str, mac_dinh: int) -> int:
    if link.relation == RELATION_EXCERPT:
        rule = _rule_of(db, link, child, parent)
        #  Kể cả có quy tắc thì ba cột của trích từ đã bị `link_rule_service` ép
        #  lại rồi; không có quy tắc thì dùng giá trị khóa cứng.
        return getattr(rule, cot) if rule else EXCERPT_FALLBACK[cot]
    rule = _rule_of(db, link, child, parent)
    return getattr(rule, cot) if rule else mac_dinh


def impact_of(db: Session, parent: Document, *, obsolete: bool) -> list[dict]:
    """E07 — LIỆT KÊ trước: sửa/bãi bỏ văn bản này thì con nào bị gì.

    Gọi trước khi bấm, để người ban hành nhìn thấy hậu quả rồi mới quyết. Không
    đụng vào dữ liệu.
    """
    cot = "on_parent_obsolete" if obsolete else "on_parent_new_version"
    mac_dinh = OBSOLETE_REVIEW if obsolete else NEW_VERSION_ASK

    ket_qua: list[dict] = []
    for link in _children_links(db, parent.id):
        child = db.get(Document, link.source_document_id)
        if child is None or child.status == STATUS_EXPIRED:
            continue
        hanh_dong = _hanh_dong(db, link, child, parent, cot, mac_dinh)
        ket_qua.append({
            "document_id": child.id,
            "title": child.title,
            "display_code": child.doc_code or child.issue_number or "",
            "status_label": child.status,
            "relation": link.relation,
            "relation_label": RELATION_LABELS.get(link.relation, str(link.relation)),
            "action": hanh_dong,
            "action_label": _nhan_hanh_dong(hanh_dong, obsolete),
        })
    return ket_qua


def _nhan_hanh_dong(hanh_dong: int, obsolete: bool) -> str:
    if obsolete:
        return {
            OBSOLETE_NOTHING: "Không đổi gì",
            OBSOLETE_REVIEW: "Đánh dấu cần rà lại",
            OBSOLETE_EXPIRE: "Hết hiệu lực theo cha",
        }.get(hanh_dong, str(hanh_dong))
    return {
        NEW_VERSION_ASK: "Đánh dấu cần rà lại và ghi nhật ký",
        NEW_VERSION_REVIEW: "Đánh dấu cần rà lại",
    }.get(hanh_dong, "Không đổi gì")


def apply_new_version(db: Session, parent: Document, ly_do: str) -> int:
    """E07 — cha lên phiên bản mới. Trả về số văn bản con bị đánh dấu.

    Giá trị 3 (*hỏi người ban hành rồi ghi nhật ký*) xử lý y như 2 ở tầng dữ
    liệu: **đều chỉ đánh dấu**. Khác biệt nằm ở giao diện — 3 thì bày bảng tác
    động ra hỏi trước, 2 thì làm lặng lẽ. Không có giá trị nào tự sửa nội dung.
    """
    dem = 0
    for muc in impact_of(db, parent, obsolete=False):
        if muc["action"] == NEW_VERSION_ASK or muc["action"] == NEW_VERSION_REVIEW:
            child = db.get(Document, muc["document_id"])
            if child is None:
                continue
            child.needs_review = True
            child.needs_review_note = ly_do
            dem += 1
    return dem


def apply_obsolete(db: Session, parent: Document) -> int:
    """E08 — cha bị bãi bỏ. Trả về số văn bản con bị đụng tới."""
    dem = 0
    for muc in impact_of(db, parent, obsolete=True):
        child = db.get(Document, muc["document_id"])
        if child is None or muc["action"] == OBSOLETE_NOTHING:
            continue

        child.needs_review = True
        child.needs_review_note = f"Văn bản cha «{parent.title}» đã bị bãi bỏ."
        #  Chỉ mức 3 mới kéo con chết theo. Mức 2 giữ con còn hiệu lực — Biểu
        #  mẫu vẫn dùng được dù Quy trình cha đã bỏ, chỉ là phải rà lại.
        if muc["action"] == OBSOLETE_EXPIRE:
            child.status = STATUS_EXPIRED
        dem += 1
    return dem
