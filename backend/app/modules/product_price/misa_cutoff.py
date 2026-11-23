"""Mốc cắt sổ Misa của sổ giá (duoc-CR-784): nguồn 3 (sổ chi tiết mua hàng Misa) và nguồn 1 / 2 KHÔNG được đếm trùng.

Chủ dự án chốt tạm: dữ liệu báo cáo Misa là đúng cho tới ngày `misa_price_cutoff` (= ngày lớn nhất của dòng Misa nạp vào).
Từ đó mọi phép tính giá (cũ / mới, hai lần mua gần nhất, min / max, số lần mua, lịch sử, ma trận giá gần nhất, tác động) xét:

  * dòng nguồn 3 (Misa) có ngày  <= mốc;
  * dòng ĐƠN MUA HÀNG THẬT có ngày  > mốc: nguồn 2 (dòng ĐMH) hoặc nguồn 1 mà lịch sử mua hàng là `source = 'system'` (sổ giá
    ghi `doc_id` = id ĐMH > 0);
  * dòng lịch sử CŨ (`source = 'legacy'`, nạp từ Excel, `doc_id = 0`, nhiều dòng sai ngày tương lai) BỊ BỎ HẲN khi mốc đang bật.

Chưa có mốc (chưa nạp Misa, hoặc đã `--purge`) thì điều kiện luôn đúng — hành vi y hệt khi chưa có nguồn Misa.

Điều kiện là MỘT biểu thức SQL có truy vấn con vô hướng đọc `tab_setting` (không phụ thuộc bảng sổ giá nên MySQL tính một lần),
nhờ đó KHÔNG thêm lượt truy vấn nào: số truy vấn cố định của các màn giá giữ nguyên. Dùng `DATE(...)` ở cả hai bên để so ngày với
chuỗi `YYYY-MM-DD` giống nhau trên MySQL (thật) và SQLite (bài kiểm). `source_type` và `doc_id` đều nằm trong chỉ mục phủ `ix_ppl_code_latest`.
"""
from datetime import date

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.core.packaging_price_codes import PriceSourceType
from app.modules.setting.model import Setting

from .model import ProductPriceLedger as L

CUTOFF_SETTING_KEY = "misa_price_cutoff"
MISA = int(PriceSourceType.MISA)
PO_LINE = int(PriceSourceType.PO_LINE)


def cutoff_value_subquery():
    """Truy vấn con vô hướng: ngày mốc (kiểu DATE), NULL khi chưa đặt."""
    return func.date(select(Setting.svalue).where(Setting.skey == CUTOFF_SETTING_KEY).scalar_subquery())


def misa_cutoff_condition() -> ColumnElement:
    """Điều kiện dựng trên `ProductPriceLedger`: đúng với mọi dòng khi chưa có mốc; có mốc thì Misa <= mốc, còn sau mốc chỉ nhận
    dòng ĐMH thật (nguồn 2 hoặc `doc_id > 0`) — dòng lịch sử cũ không ĐMH bị loại."""
    cutoff = cutoff_value_subquery()
    return or_(cutoff.is_(None),
               and_(L.source_type == MISA, L.price_date <= cutoff),
               and_(L.source_type != MISA, L.price_date > cutoff,
                    or_(L.source_type == PO_LINE, L.doc_id > 0)))


def with_misa_cutoff(scope_cond=None) -> ColumnElement:
    """Gộp điều kiện phạm vi pháp nhân (có thể None) với điều kiện mốc sổ Misa."""
    cond = misa_cutoff_condition()
    return cond if scope_cond is None else and_(scope_cond, cond)


def get_misa_cutoff(db: Session) -> date | None:
    """Mốc đang đặt (None = chưa có / giá trị hỏng — coi như chưa có)."""
    raw = db.query(Setting.svalue).filter(Setting.skey == CUTOFF_SETTING_KEY).scalar()
    try:
        return date.fromisoformat((raw or "").strip()) if raw else None
    except ValueError:
        return None


def set_misa_cutoff(db: Session, value: date | None) -> None:
    """Đặt mốc (tạo dòng `tab_setting` nếu chưa có); `None` = xóa mốc. Không commit — nơi gọi tự commit."""
    row = db.query(Setting).filter(Setting.skey == CUTOFF_SETTING_KEY).first()
    if value is None:
        if row is not None:
            db.delete(row)
    elif row is None:
        db.add(Setting(skey=CUTOFF_SETTING_KEY, svalue=value.isoformat(), created_by=0, updated_by=0))
    else:
        row.svalue = value.isoformat()
    db.flush()
