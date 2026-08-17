"""API QUAN HỆ VĂN BẢN, CÂY TÀI LIỆU và BẢN TRÍCH (E03–E06, C19, E11).

Router riêng nhưng **cùng prefix** `/api/documents` với `controller.py`: đây vẫn
là việc của văn bản, tách tệp chỉ để không dồn tất cả vào một chỗ.

Quyền dùng chung `_load()` của `controller.py` — ba lớp kiểm y hệt, trong đó
`ensure_can` trả 404 chứ không 403 khi không được đọc.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.database import get_db
from app.core.response import success
from app.modules.doc_catalog.link_rule_model import RELATION_LABELS

from . import (excerpt_service, issue_service, link_serializer, link_service,
               parent_change_service, supersede_service)
from .controller import _load
from .link_serializer import summary_of

router = APIRouter(prefix="/api/documents", tags=["document-link"])


def _ten_loai(db: Session, doc_type_id: int | None) -> str:
    """Rỗng = loại nào cũng được — nói thẳng ra thay vì để trống."""
    from app.modules.doc_catalog.model import DocType

    doc_type = db.get(DocType, doc_type_id) if doc_type_id else None
    return doc_type.name if doc_type else "Loại bất kỳ"


class LinkCreate(BaseModel):
    relation: int = Field(ge=1, le=10)
    target_document_id: int
    note: str = ""


class ExcerptCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    content_html: str
    secrecy_level: int = Field(ge=1, le=4)
    note: str = ""


@router.get("/{document_id}/links")
def list_links(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """Quan hệ hai chiều của một văn bản, cộng phần khai còn thiếu để gửi duyệt."""
    doc = _load(db, document_id, user)

    outgoing = [link_serializer.serialize_link(db, link, viewed_from=doc.id)
                for link in link_service.links_of(db, doc.id)]
    incoming = [link_serializer.serialize_link(db, link, viewed_from=doc.id)
                for link in link_service.links_to(db, doc.id)]

    return success({
        "outgoing": outgoing,
        "incoming": incoming,
        #  E04 — nói TRƯỚC còn thiếu gì, đừng để người dùng bấm gửi duyệt rồi
        #  mới biết. Backend vẫn chặn lần nữa lúc gửi.
        "missing_required": link_service.missing_required(db, doc),
    })


@router.get("/{document_id}/link-slots")
def list_link_slots(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """E03 — các ô quan hệ form phải tự hiện cho loại của văn bản này.

    Kèm luôn danh sách văn bản chọn được cho từng ô: đã lọc đúng loại đích cho
    phép và chỉ văn bản đang còn hiệu lực, nên người soạn không phải nhớ quy tắc.
    """
    doc = _load(db, document_id, user)

    slots = []
    for rule in link_service.rules_for_type(db, doc.doc_type_id):
        targets = link_service.allowed_targets(db, rule, exclude_document_id=doc.id)
        slots.append({
            "rule_id": rule.id,
            "relation": rule.relation,
            "relation_label": RELATION_LABELS.get(rule.relation, str(rule.relation)),
            "target_type_id": rule.target_type_id,
            #  Hai dòng cùng quan hệ khác đích thì nhãn phải nói ra đích, nếu
            #  không màn hình hiện hai ô "Thuộc về" y hệt nhau.
            "target_type_name": _ten_loai(db, rule.target_type_id),
            "is_required": rule.is_required,
            "min_count": rule.min_count,
            "max_count": rule.max_count,
            "options": [summary_of(db, target) for target in targets],
        })
    return success(slots)


@router.get("/{document_id}/issue-preview")
def issue_preview(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """J04 — mọi thứ sắp xảy ra khi bấm Ban hành. Chỉ đọc, không đụng gì.

    Ban hành không lùi được: số cấp ra là cấp vĩnh viễn, phiên bản khóa là khóa
    một chiều, văn bản cũ bị thay thế thì đổi trạng thái ngay.
    """
    doc = _load(db, document_id, user)
    return success(issue_service.preview(db, doc))


@router.get("/{document_id}/amended-by")
def amended_by(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """J10 — văn bản này đã bị sửa đổi / thay thế / bãi bỏ bởi những văn bản nào.

    **Bắt buộc hiện trên màn hình, không phải tùy chọn.** Quan hệ *sửa đổi* không
    đổi trạng thái, nên Quyết định 15 bị sửa Điều 5 vẫn hiện "Có hiệu lực" — người
    mở nó đọc Điều 5 cũ rồi làm sai, và không ai phát hiện ra vì mọi thứ trông
    vẫn đúng.
    """
    doc = _load(db, document_id, user)
    return success(supersede_service.amended_by(db, doc.id))


@router.get("/{document_id}/tree")
def document_tree(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """E06 — mở một Quy trình thấy ngay Hướng dẫn công việc và Biểu mẫu thuộc nó."""
    doc = _load(db, document_id, user)
    return success(link_serializer.build_tree(db, doc))


@router.get("/{document_id}/impact")
def parent_change_impact(
    document_id: int,
    obsolete: bool = False,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """E07 — LIỆT KÊ trước khi bấm: sửa/bãi bỏ văn bản này thì con nào bị gì.

    `obsolete=false` hỏi cho việc lên phiên bản mới, `true` hỏi cho việc bãi bỏ.
    Hai việc khác nhau, hai cột cấu hình riêng — hỏi chung một câu là trả lời sai
    một trong hai.

    Chỉ ĐỌC. Hệ thống liệt kê để người ban hành quyết, không tự sửa gì.
    """
    doc = _load(db, document_id, user)
    return success(parent_change_service.impact_of(db, doc, obsolete=obsolete))


@router.post("/{document_id}/links")
def add_link(
    document_id: int,
    data: LinkCreate,
    db: Session = Depends(get_db),
    user=Depends(require("document", "write")),
):
    doc = _load(db, document_id, user, "write")
    link = link_service.add_link(
        db, doc, data.relation, data.target_document_id, data.note, user.id,
    )
    record(db, user.id, "document", doc.id, "update")
    return success(
        link_serializer.serialize_link(db, link, viewed_from=doc.id),
        "Đã khai quan hệ", 201,
    )


@router.delete("/{document_id}/links/{link_id}")
def delete_link(
    document_id: int,
    link_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "write")),
):
    doc = _load(db, document_id, user, "write")
    link_service.delete_link(db, doc, link_id)
    record(db, user.id, "document", doc.id, "update")
    return success(None, "Đã gỡ quan hệ")


@router.post("/{document_id}/excerpts")
def create_excerpt(
    document_id: int,
    data: ExcerptCreate,
    db: Session = Depends(get_db),
    user=Depends(require("document", "create")),
):
    """C19 — tách một phần nội dung bản gốc thành văn bản riêng mức mật thấp hơn.

    Cần quyền ĐỌC bản gốc (không phải quyền sửa): người được chia một quy chế
    mật vẫn có thể cần tách phần việc của mình xuống nhà máy.
    """
    source = _load(db, document_id, user)
    excerpt = excerpt_service.create_excerpt(
        db, source, data.title, data.content_html, data.secrecy_level, data.note, user.id,
    )
    record(db, user.id, "document", excerpt.id, "create")
    return success(summary_of(db, excerpt), "Đã tạo bản trích nội bộ", 201)


@router.get("/{document_id}/excerpts")
def list_excerpts(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    doc = _load(db, document_id, user)
    return success([
        link_serializer.serialize_link(db, link, viewed_from=doc.id)
        for link in excerpt_service.excerpts_of(db, doc.id)
    ])
