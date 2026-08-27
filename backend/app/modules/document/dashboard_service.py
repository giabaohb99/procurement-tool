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
EXPIRING_SOON_DAYS = 30
#  Nháp nằm im quá lâu — nhiều khả năng bị bỏ quên chứ không phải đang soạn.
STALE_DRAFT_DAYS = 30
#  Từ mức này trở lên coi là KHẨN CẤP (2 Khẩn · 3 Hỏa tốc). Mức 1 Thường thì không.
URGENT_FROM_LEVEL = 2


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
             by_day: bool = True):
    """Truy vấn nền: chỉ văn bản nội bộ, chỉ phần người này được xem, đã lọc.

    `theo_ngay=False` bỏ qua khoảng ngày — dành cho biểu đồ 12 tháng, thứ tự nó
    đã tự khai một cửa sổ thời gian. Lọc chồng hai khoảng lên nhau thì cột của
    những tháng ngoài khoảng rỗng trơn, và biểu đồ đọc ra một câu chuyện sai.
    """
    query = documents_query(db)
    condition = access_service.visible_condition(user, profile)
    if condition is not None:
        query = query.filter(condition)

    if not filters:
        return query
    if filters.company_id:
        query = query.filter(Document.company_id == filters.company_id)
    if filters.department_id:
        query = query.filter(Document.department_id == filters.department_id)
    if by_day and filters.from_date:
        query = query.filter(Document.created_at >= filters.from_date)
    if by_day and filters.to_date:
        #  `created_at` là DATETIME: so với `to_date` trần thì mọi văn bản lập
        #  trong chính ngày đó (giờ > 00:00) bị loại. Cộng một ngày rồi so "<".
        query = query.filter(Document.created_at < filters.to_date + timedelta(days=1))
    return query


def overview(db: Session, user, profile, filters: DashboardFilters | None = None) -> dict:
    today = date.today()
    filters = filters or DashboardFilters()
    base = _visible(db, user, profile, filters)

    def count(*condition) -> int:
        return base.filter(*condition).count()

    expiring_soon = count(
        Document.status == STATUS_EFFECTIVE,
        Document.expire_date.isnot(None),
        Document.expire_date >= today,
        Document.expire_date <= today + timedelta(days=EXPIRING_SOON_DAYS),
    )

    return {
        "kpi": {
            "effective": count(Document.status == STATUS_EFFECTIVE),
            "submitted": count(Document.status == STATUS_SUBMITTED),
            #  Cờ do E07/E08/F11 bật — văn bản cha đổi thì con phải rà lại.
            "needs_review": count(Document.needs_review.is_(True)),
            "expiring": expiring_soon,
            "draft": count(Document.status == STATUS_DRAFT),
        },
        "issued_12m": _issued_12_months(db, user, profile, today, filters),
        "by_type": _breakdown_by_type(db, user, profile, filters),
        "priority_matrix": _priority_matrix(db, user, profile, filters),
        "todo": _todo_items(db, user, profile, today, filters),
        "recent": serializer.serialize_many(
            db, base.order_by(Document.id.desc()).limit(8).all()
        ),
        "year": today.year,
    }


def _issued_12_months(db: Session, user, profile, today: date,
                       filters: DashboardFilters) -> list[dict]:
    """Số văn bản ban hành theo tháng, 12 tháng gần nhất kể cả tháng rỗng.

    Dựng đủ 12 ô TRƯỚC rồi mới đổ số vào: để cơ sở dữ liệu tự sinh nhãn tháng
    thì tháng nào không có văn bản sẽ biến mất khỏi trục, và biểu đồ đọc ra một
    câu chuyện sai — nhìn như tháng đó không tồn tại.
    """
    start = (today.replace(day=1) - timedelta(days=334)).replace(day=1)

    buckets: dict[str, int] = {}
    year, month = start.year, start.month
    for _ in range(12):
        buckets[f"{month:02d}/{year}"] = 0
        month += 1
        if month > 12:
            month, year = 1, year + 1

    rows = (
        _visible(db, user, profile, filters, by_day=False)
        .filter(Document.status.in_((STATUS_EFFECTIVE, STATUS_APPROVED)),
                Document.effective_date.isnot(None),
                Document.effective_date >= start)
        .with_entities(Document.effective_date)
        .all()
    )
    for (when,) in rows:
        label = f"{when.month:02d}/{when.year}"
        if label in buckets:
            buckets[label] += 1

    return [{"label": label, "value": value} for label, value in buckets.items()]


def _breakdown_by_type(db: Session, user, profile, filters: DashboardFilters) -> list[dict]:
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

    labels = {
        row[0]: row[1] for row in
        db.query(DocType.id, DocType.name)
        .filter(DocType.id.in_([r[0] for r in rows if r[0]])).all()
    }
    result = [
        {"name": labels.get(doc_type_id, "Chưa phân loại"), "value": value}
        for doc_type_id, value in rows
    ]
    return sorted(result, key=lambda item: item["value"], reverse=True)


def _priority_matrix(db: Session, user, profile, filters: DashboardFilters) -> dict:
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
    important = {
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
    for doc_type_id, urgency, value in rows:
        key = "important" if doc_type_id in important else "normal"
        #  `urgency` có thể rỗng ở dữ liệu nhập từ bản giấy — coi như Thường.
        key += "_urgent" if (urgency or 1) >= URGENT_FROM_LEVEL else "_normal"
        o[key] += value
    return o


def _todo_items(db: Session, user, profile, today: date,
                    filters: DashboardFilters) -> list[dict]:
    """Ba nhóm việc đang treo, mỗi nhóm một dòng kèm đường dẫn tới danh sách."""
    base = _visible(db, user, profile, filters)

    needs_review_count = base.filter(Document.needs_review.is_(True)).count()
    submitted_count = base.filter(Document.status == STATUS_SUBMITTED).count()
    #  Bị trả về là việc CỦA NGƯỜI SOẠN và có hạn ngầm: người duyệt đang chờ bản
    #  sửa. Không nêu ra đây thì nó lẫn vào đống nháp và nằm im.
    returned_count = base.filter(Document.status == STATUS_RETURNED).count()
    stale_drafts = base.filter(
        Document.status == STATUS_DRAFT,
        Document.created_at <= today - timedelta(days=STALE_DRAFT_DAYS),
    ).count()

    task = [
        {"key": "needs_review", "label": "Văn bản cần rà lại",
         "hint": "Văn bản cha đã đổi hoặc bị bãi bỏ", "count": needs_review_count,
         "tone": "warning"},
        {"key": "returned", "label": "Bị trả về, chờ sửa lại",
         "hint": "Người duyệt đã trả về — sửa rồi gửi duyệt lại",
         "count": returned_count, "tone": "warning"},
        {"key": "submitted", "label": "Đang chờ duyệt",
         "hint": "Chờ người có quyền phê duyệt", "count": submitted_count,
         "tone": "default"},
        {"key": "stale_draft", "label": f"Nháp treo quá {STALE_DRAFT_DAYS} ngày",
         "hint": "Nhiều khả năng bị bỏ quên", "count": stale_drafts,
         "tone": "default"},
    ]
    #  Nhóm rỗng bỏ hẳn: một danh sách toàn số 0 làm loãng đúng dòng đang cần
    #  người xử lý.
    return [item for item in task if item["count"] > 0]
