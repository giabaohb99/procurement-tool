"""LỊCH NGÀY LỄ — tách khỏi `workday_service.py` cho gọn (cắt-dán, không đổi logic).

`workday_service` import lại các tên này nên `workday_service.MAX_RANGE_DAYS`,
`workday_service.holiday_dates` vẫn tồn tại cho người gọi cũ (draft_tool, request_service).
"""
from datetime import date, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from .catalog_model import Holiday

#  Trần bảo hiểm cho vòng lặp ngày. Thai sản 6 tháng là ~180 ngày; đơn dài hơn
#  một năm là dữ liệu hỏng hoặc gõ nhầm năm, và ta không muốn một ô nhập sai kéo
#  theo một vòng lặp mười nghìn lượt.
MAX_RANGE_DAYS = 400


def holiday_dates(db: Session, company_id: int, from_date: date, to_date: date) -> set[date]:
    """Tập ngày lễ áp cho pháp nhân này, trong khoảng đã cho.

    Gộp HAI nguồn: dòng dùng chung (`company_id = 0`) và dòng riêng của pháp
    nhân. Đây chính là phép gộp mà khuôn một-cột của `apply_scope` không diễn
    đạt được — lý do `holiday` khai `PUBLIC` ở `SCOPE_FIELDS`.

    Ngày lễ LẶP hằng năm (`is_recurring`) khớp theo ngày/tháng, bất kể năm lưu
    trong bảng — nhập «01/01» một lần là năm nào cũng nhận. Tết Âm lịch thì
    không lặp được vì trôi theo lịch âm, mỗi năm phải nhập một lần.
    """
    return set(holiday_names_many(db, [company_id], from_date, to_date).get(company_id, {}))


def holiday_names_many(db: Session, company_ids, from_date: date,
                       to_date: date) -> dict[int, dict[date, str]]:
    """`{company_id: {ngày lễ: tên}}` cho NHIỀU pháp nhân bằng ĐÚNG MỘT truy vấn.

    Cùng luật với `holiday_dates` (dòng chung `company_id = 0` + dòng riêng, lặp hằng
    năm khớp theo ngày/tháng) — `holiday_dates` nay gọi lại hàm này nên không lệch.
    Dòng riêng của pháp nhân thắng dòng chung khi trùng ngày (lấy tên riêng).
    """
    wanted = {int(c or 0) for c in company_ids}
    rows = (db.query(Holiday)
            .filter(Holiday.is_active.is_(True),
                    or_(Holiday.company_id == 0, Holiday.company_id.in_(wanted)))
            .all())
    days = list(date_range(from_date, to_date))   # trải ngày lặp trong đúng khoảng đang hỏi
    out: dict[int, dict[date, str]] = {}
    for cid in wanted:
        mine: dict[date, str] = {}
        for r in sorted(rows, key=lambda x: x.company_id == cid):   # riêng ghi đè chung
            if r.company_id not in (0, cid) or not r.date:
                continue
            if r.is_recurring:
                for d in days:
                    if (d.month, d.day) == (r.date.month, r.date.day):
                        mine[d] = r.name or ""
            elif from_date <= r.date <= to_date:
                mine[r.date] = r.name or ""
        out[cid] = mine
    return out


def date_range(from_date: date, to_date: date):
    """Sinh từng ngày trong khoảng, bao gồm cả hai đầu. Chặn ở `MAX_RANGE_DAYS`."""
    day, guard = from_date, 0
    while day <= to_date and guard < MAX_RANGE_DAYS:
        yield day
        day += timedelta(days=1)
        guard += 1
