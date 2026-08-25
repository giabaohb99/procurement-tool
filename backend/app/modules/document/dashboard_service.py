"""SỐ LIỆU TRANG TỔNG QUAN VĂN THƯ.

Mọi câu đếm ở đây đều đi qua **cùng một bộ lọc phạm vi** với danh sách văn bản
(`access_service.visible_condition`). Đếm không lọc thì trang tổng quan nói một
con số mà bấm vào danh sách lại ra con số khác — và người dùng sẽ tin con số
lớn hơn.

Một lần gọi trả về đủ cả trang: KPI, biểu đồ, việc cần xử lý, văn bản gần đây.
Tách nhiều endpoint thì mỗi lần mở trang là năm lượt gọi, mà chúng đọc chung
một bảng.
"""
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.modules.doc_catalog.model import DocType

from . import access_service, serializer
from .model import (STATUS_APPROVED, STATUS_DRAFT, STATUS_EFFECTIVE,
                    STATUS_RETURNED, STATUS_SUBMITTED, Document)
from .query import documents_query

#  Văn bản hết hiệu lực trong bao nhiêu ngày tới thì coi là "sắp hết".
SAP_HET_HAN_NGAY = 30
#  Nháp nằm im quá lâu — nhiều khả năng bị bỏ quên chứ không phải đang soạn.
NHAP_TREO_NGAY = 30
#  Từ mức này trở lên coi là KHẨN CẤP (2 Khẩn · 3 Hỏa tốc). Mức 1 Thường thì không.
KHAN_TU_MUC = 2


@dataclass(frozen=True)
class DashboardFilters:
    """Bộ lọc của thanh trên cùng trang tổng quan.

    Khoảng ngày lọc theo **`created_at` (ngày lập)** chứ không phải ngày hiệu
    lực: người dùng chọn "30 ngày qua" là đang hỏi *"kỳ vừa rồi phát sinh những
    gì"*, mà văn bản lập trong kỳ có thể chưa tới ngày hiệu lực — lọc theo hiệu
    lực thì đúng những thứ mới nhất lại biến mất.
    """
    company_id: int | None = None
    department_id: int | None = None
    from_date: date | None = None
    to_date: date | None = None


def _visible(db: Session, user, profile, filters: DashboardFilters | None = None,
             theo_ngay: bool = True):
    """Truy vấn nền: chỉ văn bản nội bộ, chỉ phần người này được xem, đã lọc.

    `theo_ngay=False` bỏ qua khoảng ngày — dành cho biểu đồ 12 tháng, thứ tự nó
    đã tự khai một cửa sổ thời gian. Lọc chồng hai khoảng lên nhau thì cột của
    những tháng ngoài khoảng rỗng trơn, và biểu đồ đọc ra một câu chuyện sai.
    """
    query = documents_query(db)
    dieu_kien = access_service.visible_condition(user, profile)
    if dieu_kien is not None:
        query = query.filter(dieu_kien)

    if not filters:
        return query
    if filters.company_id:
        query = query.filter(Document.company_id == filters.company_id)
    if filters.department_id:
        query = query.filter(Document.department_id == filters.department_id)
    if theo_ngay and filters.from_date:
        query = query.filter(Document.created_at >= filters.from_date)
    if theo_ngay and filters.to_date:
        #  `created_at` là DATETIME: so với `to_date` trần thì mọi văn bản lập
        #  trong chính ngày đó (giờ > 00:00) bị loại. Cộng một ngày rồi so "<".
        query = query.filter(Document.created_at < filters.to_date + timedelta(days=1))
    return query


def overview(db: Session, user, profile, filters: DashboardFilters | None = None) -> dict:
    hom_nay = date.today()
    filters = filters or DashboardFilters()
    nen = _visible(db, user, profile, filters)

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
        "issued_12m": _ban_hanh_12_thang(db, user, profile, hom_nay, filters),
        "by_type": _co_cau_theo_loai(db, user, profile, filters),
        "priority_matrix": _ma_tran_uu_tien(db, user, profile, filters),
        "todo": _viec_can_xu_ly(db, user, profile, hom_nay, filters),
        "recent": serializer.serialize_many(
            db, nen.order_by(Document.id.desc()).limit(8).all()
        ),
        "year": hom_nay.year,
    }


def _ban_hanh_12_thang(db: Session, user, profile, hom_nay: date,
                       filters: DashboardFilters) -> list[dict]:
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
        _visible(db, user, profile, filters, theo_ngay=False)
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


def _co_cau_theo_loai(db: Session, user, profile, filters: DashboardFilters) -> list[dict]:
    """Văn bản còn hiệu lực chia theo loại, nhiều nhất lên trước."""
    rows = (
        _visible(db, user, profile, filters)
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


def _ma_tran_uu_tien(db: Session, user, profile, filters: DashboardFilters) -> dict:
    """MA TRẬN ƯU TIÊN — văn bản còn hiệu lực chia bốn ô *quan trọng × khẩn cấp*.

    Hai trục lấy từ hai chỗ khác nhau, và đó là điều phải nhớ khi đọc con số:

    - **Khẩn cấp** đọc từ `urgency` của TỪNG văn bản (2 Khẩn · 3 Hỏa tốc).
    - **Quan trọng** đọc từ CỜ CỦA LOẠI — loại nào bắt buộc qua duyệt hoặc bắt
      buộc kèm Quyết định ban hành thì cả loại là quan trọng. Bảng `tab_document`
      không có cột "quan trọng" nào, và thêm một cột như vậy nghĩa là mọi văn
      bản cũ về ô "không quan trọng" cho tới khi có người ngồi tick lại từng cái
      (chốt 18/08/2026).

    Hệ quả cần biết: hai văn bản CÙNG LOẠI luôn nằm cùng một nửa trục quan
    trọng. Muốn phân biệt tới từng văn bản thì phải thêm cột thật.
    """
    quan_trong = {
        row[0] for row in
        db.query(DocType.id)
        .filter(or_(DocType.needs_approval.is_(True), DocType.needs_decision.is_(True)))
        .all()
    }

    rows = (
        _visible(db, user, profile, filters)
        .filter(Document.status == STATUS_EFFECTIVE)
        .with_entities(Document.doc_type_id, Document.urgency, func.count(Document.id))
        .group_by(Document.doc_type_id, Document.urgency)
        .all()
    )

    o = {
        "important_urgent": 0,
        "important_normal": 0,
        "normal_urgent": 0,
        "normal_normal": 0,
    }
    for doc_type_id, urgency, so in rows:
        khoa = "important" if doc_type_id in quan_trong else "normal"
        #  `urgency` có thể rỗng ở dữ liệu nhập từ bản giấy — coi như Thường.
        khoa += "_urgent" if (urgency or 1) >= KHAN_TU_MUC else "_normal"
        o[khoa] += so
    return o


def _viec_can_xu_ly(db: Session, user, profile, hom_nay: date,
                    filters: DashboardFilters) -> list[dict]:
    """Ba nhóm việc đang treo, mỗi nhóm một dòng kèm đường dẫn tới danh sách."""
    nen = _visible(db, user, profile, filters)

    can_ra_lai = nen.filter(Document.needs_review.is_(True)).count()
    cho_duyet = nen.filter(Document.status == STATUS_SUBMITTED).count()
    #  Bị trả về là việc CỦA NGƯỜI SOẠN và có hạn ngầm: người duyệt đang chờ bản
    #  sửa. Không nêu ra đây thì nó lẫn vào đống nháp và nằm im.
    bi_tra_ve = nen.filter(Document.status == STATUS_RETURNED).count()
    nhap_treo = nen.filter(
        Document.status == STATUS_DRAFT,
        Document.created_at <= hom_nay - timedelta(days=NHAP_TREO_NGAY),
    ).count()

    viec = [
        {"key": "needs_review", "label": "Văn bản cần rà lại",
         "hint": "Văn bản cha đã đổi hoặc bị bãi bỏ", "count": can_ra_lai,
         "tone": "warning"},
        {"key": "returned", "label": "Bị trả về, chờ sửa lại",
         "hint": "Người duyệt đã trả về — sửa rồi gửi duyệt lại",
         "count": bi_tra_ve, "tone": "warning"},
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
