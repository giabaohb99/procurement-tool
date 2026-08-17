"""SỐ LIỆU TRANG TỔNG QUAN VĂN THƯ.

Mọi câu đếm ở đây đều đi qua **cùng một bộ lọc phạm vi** với danh sách văn bản
(`access_service.visible_condition`). Đếm không lọc thì trang tổng quan nói một
con số mà bấm vào danh sách lại ra con số khác — và người dùng sẽ tin con số
lớn hơn.

Một lần gọi trả về đủ cả trang: KPI, biểu đồ, việc cần xử lý, văn bản gần đây.
Tách nhiều endpoint thì mỗi lần mở trang là năm lượt gọi, mà chúng đọc chung
một bảng.
"""
from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.doc_catalog.model import DocType

from . import access_service, serializer
from .model import (STATUS_APPROVED, STATUS_DRAFT, STATUS_EFFECTIVE,
                    STATUS_SUBMITTED, Document)
from .query import documents_query

#  Văn bản hết hiệu lực trong bao nhiêu ngày tới thì coi là "sắp hết".
SAP_HET_HAN_NGAY = 30
#  Nháp nằm im quá lâu — nhiều khả năng bị bỏ quên chứ không phải đang soạn.
NHAP_TREO_NGAY = 30


def _visible(db: Session, user, profile):
    """Truy vấn nền: chỉ văn bản nội bộ và chỉ phần người này được xem."""
    query = documents_query(db)
    dieu_kien = access_service.visible_condition(user, profile)
    return query.filter(dieu_kien) if dieu_kien is not None else query


def overview(db: Session, user, profile) -> dict:
    hom_nay = date.today()
    nen = _visible(db, user, profile)

    def dem(*dieu_kien) -> int:
        return nen.filter(*dieu_kien).count()

    sap_het_han = dem(
        Document.status == STATUS_EFFECTIVE,
        Document.expire_date.isnot(None),
        Document.expire_date >= hom_nay,
        Document.expire_date <= hom_nay + timedelta(days=SAP_HET_HAN_NGAY),
    )

    return {
        "kpi": {
            "effective": dem(Document.status == STATUS_EFFECTIVE),
            "submitted": dem(Document.status == STATUS_SUBMITTED),
            #  Cờ do E07/E08/F11 bật — văn bản cha đổi thì con phải rà lại.
            "needs_review": dem(Document.needs_review.is_(True)),
            "expiring": sap_het_han,
            "draft": dem(Document.status == STATUS_DRAFT),
        },
        "issued_12m": _ban_hanh_12_thang(db, user, profile, hom_nay),
        "by_type": _co_cau_theo_loai(db, user, profile),
        "todo": _viec_can_xu_ly(db, user, profile, hom_nay),
        "recent": serializer.serialize_many(
            db, nen.order_by(Document.id.desc()).limit(8).all()
        ),
        "year": hom_nay.year,
    }


def _ban_hanh_12_thang(db: Session, user, profile, hom_nay: date) -> list[dict]:
    """Số văn bản ban hành theo tháng, 12 tháng gần nhất kể cả tháng rỗng.

    Dựng đủ 12 ô TRƯỚC rồi mới đổ số vào: để cơ sở dữ liệu tự sinh nhãn tháng
    thì tháng nào không có văn bản sẽ biến mất khỏi trục, và biểu đồ đọc ra một
    câu chuyện sai — nhìn như tháng đó không tồn tại.
    """
    dau = (hom_nay.replace(day=1) - timedelta(days=334)).replace(day=1)

    o_trong: dict[str, int] = {}
    nam, thang = dau.year, dau.month
    for _ in range(12):
        o_trong[f"{thang:02d}/{nam}"] = 0
        thang += 1
        if thang > 12:
            thang, nam = 1, nam + 1

    rows = (
        _visible(db, user, profile)
        .filter(Document.status.in_((STATUS_EFFECTIVE, STATUS_APPROVED)),
                Document.effective_date.isnot(None),
                Document.effective_date >= dau)
        .with_entities(Document.effective_date)
        .all()
    )
    for (ngay,) in rows:
        nhan = f"{ngay.month:02d}/{ngay.year}"
        if nhan in o_trong:
            o_trong[nhan] += 1

    return [{"label": nhan, "value": so} for nhan, so in o_trong.items()]


def _co_cau_theo_loai(db: Session, user, profile) -> list[dict]:
    """Văn bản còn hiệu lực chia theo loại, nhiều nhất lên trước."""
    rows = (
        _visible(db, user, profile)
        .filter(Document.status == STATUS_EFFECTIVE)
        .with_entities(Document.doc_type_id, func.count(Document.id))
        .group_by(Document.doc_type_id)
        .all()
    )
    if not rows:
        return []

    ten = {
        row[0]: row[1] for row in
        db.query(DocType.id, DocType.name)
        .filter(DocType.id.in_([r[0] for r in rows if r[0]])).all()
    }
    ket_qua = [
        {"name": ten.get(doc_type_id, "Chưa phân loại"), "value": so}
        for doc_type_id, so in rows
    ]
    return sorted(ket_qua, key=lambda item: item["value"], reverse=True)


def _viec_can_xu_ly(db: Session, user, profile, hom_nay: date) -> list[dict]:
    """Ba nhóm việc đang treo, mỗi nhóm một dòng kèm đường dẫn tới danh sách."""
    nen = _visible(db, user, profile)

    can_ra_lai = nen.filter(Document.needs_review.is_(True)).count()
    cho_duyet = nen.filter(Document.status == STATUS_SUBMITTED).count()
    nhap_treo = nen.filter(
        Document.status == STATUS_DRAFT,
        Document.created_at <= hom_nay - timedelta(days=NHAP_TREO_NGAY),
    ).count()

    viec = [
        {"key": "needs_review", "label": "Văn bản cần rà lại",
         "hint": "Văn bản cha đã đổi hoặc bị bãi bỏ", "count": can_ra_lai,
         "tone": "warning"},
        {"key": "submitted", "label": "Đang chờ duyệt",
         "hint": "Chờ người có quyền phê duyệt", "count": cho_duyet,
         "tone": "default"},
        {"key": "stale_draft", "label": f"Nháp treo quá {NHAP_TREO_NGAY} ngày",
         "hint": "Nhiều khả năng bị bỏ quên", "count": nhap_treo,
         "tone": "default"},
    ]
    #  Nhóm rỗng bỏ hẳn: một danh sách toàn số 0 làm loãng đúng dòng đang cần
    #  người xử lý.
    return [item for item in viec if item["count"] > 0]
