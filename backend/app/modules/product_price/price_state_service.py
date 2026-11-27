"""Trạng thái giá theo mã hàng: giá cũ / mới, 2 lần mua gần nhất, báo giá, min / max (duoc-CR-784, phase 04).

Ngưỡng sàn / trần đã BỎ (migration `cleanup784`, chủ dự án chốt C6): không còn truy vấn ngưỡng, `PriceState` không có `floor` / `ceiling`.

Hàm lõi `get_price_states` chạy TỐI ĐA 4 truy vấn (3 khi mọi mã cùng một tầng) bất kể số mã (luật "API báo cáo phải nhanh nhất"):
  1. sổ giá — `latest_priced_query.latest_priced_by_code` (một câu mỗi tầng: tầng đủ số gộp + tầng nhẹ cho mã không cần min / max),
     MỘT câu cho cả hai việc: số gộp theo mã (đếm MỌI dòng kể cả giá 0,
     ngày mua cuối, min / max giá trong `[date_from, date_to]` — khoảng ngày CHỈ áp cho min / max, KHÔNG áp cho cũ / mới) và
     hai lần mua có giá (`price > 0`) gần nhất → lần mua gần nhất + lần trước đó. Không dùng hàm cửa sổ (xem module đó);
  2. báo giá mới nhất theo mã — kể cả `valid_from` ở tương lai (Q2 đã chốt 20/11: báo giá sắp áp dụng tính ngay là giá mới
     để xem trước tác động);
  3. `tab_product` (tên, nhóm, ĐVT).

Thứ tự "gần nhất": ngày mua giảm, rồi `doc_id` (id ĐMH) giảm, rồi id dòng sổ giảm. Trước `srcmerge784` `doc_id` phải đứng TRƯỚC id vì dòng
nguồn 2 (dòng ĐMH) bị xóa rồi nguồn 1 (lịch sử) chèn lại với id MỚI hơn; nay dòng ĐMH giữ id suốt đời nên lý do đó hết, nhưng thứ tự
này GIỮ NGUYÊN (đổi thì phải đổi chỉ mục phủ `ix_ppl_code_latest` và kết quả lần 1 / lần 2 của hai ĐMH cùng ngày đổi chỗ).

Luật cũ / mới (đúng `build()` của bản mẫu): có báo giá → mới = báo giá, cũ = lần mua có giá gần nhất (không có lần mua thì cũ =
mới); không báo giá → mới = lần mua gần nhất, cũ = lần trước đó (chỉ một lần mua thì cũ = mới). Phạm vi dữ liệu: `scope_cond`
là điều kiện phạm vi của khóa màn đang gọi (`packaging_*`, bao-CR-792) trên sổ giá — giá chỉ tính trên các dòng người xem được thấy.

Mốc sổ Misa (`misa_cutoff.py`) được áp BÊN TRONG `latest_priced_by_code` — mọi số của hàm này (cũ / mới, p1 / p2, số lần mua,
ngày cuối, min / max) chỉ xét dòng còn hiệu lực: Misa tới mốc, dòng ĐMH (nguồn 2) sau mốc. Chưa có mốc = như cũ.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.modules.product.model import Product

from .latest_priced_query import LedgerRow, latest_priced_by_code
from .model import ProductPriceLedger as L
from .model import ProductPriceQuote


@dataclass
class PricePoint:
    """Một lần mua trong sổ giá."""
    price: Decimal
    date: date
    supplier_code: str = ""
    unit: str = ""
    source_type: int = 0
    doc_id: int = 0
    supplier_name: str = ""      # tên nhà cung cấp chép theo dòng sổ (nguồn Misa); trống = tra `tab_supplier` theo mã
    line_stage: int = 0          # LedgerLineStage của dòng sổ (đang mở / đã chốt)


@dataclass
class QuotePoint:
    price: Decimal
    valid_from: date
    supplier_code: str = ""


@dataclass
class PriceState:
    code: str
    name: str = ""
    group: str = ""
    unit: str = ""                       # ĐVT danh mục (`tab_product.unit`); trống thì ĐVT lần mua có giá gần nhất
    old: Decimal | None = None
    new: Decimal | None = None
    p1: PricePoint | None = None
    p2: PricePoint | None = None
    quote: QuotePoint | None = None
    purchase_count: int = 0
    last_date: date | None = None
    min: Decimal | None = None
    max: Decimal | None = None


def derive_old_new(p1: PricePoint | None, p2: PricePoint | None, quote: QuotePoint | None):
    """Luật cũ / mới của một mã. Trả `(old, new)`; cả hai None nếu chưa có giá nào."""
    if quote is not None:
        return (p1.price if p1 else quote.price), quote.price
    if p1 is not None:
        return (p2.price if p2 else p1.price), p1.price
    return None, None


def _point(r: LedgerRow) -> PricePoint:
    return PricePoint(price=r.price, date=r.price_date, supplier_code=r.supplier_code, unit=r.unit,
                      source_type=r.source_type, doc_id=r.doc_id, supplier_name=r.supplier_name,
                      line_stage=r.line_stage)


def get_price_states(db: Session, codes: set[str] | None, *, as_of: date | None = None, date_from: date | None = None,
                     date_to: date | None = None, scope_cond=None, also: set[str] | None = None,
                     new_only: bool = False, stats_codes: set[str] | None = None) -> dict[str, PriceState]:
    """`{mã: PriceState}` — tối đa 4 truy vấn.

    `codes=None` = mọi mã có dữ liệu (sổ giá / báo giá). `also` = mã phải có mặt dù chưa có dữ liệu giá nào (vd mã
    thành phần của định mức) — chúng vẫn có tên / nhóm / ĐVT và `old = new = None`. `as_of` (mặc định None = không lọc) loại
    dòng sổ giá có ngày SAU mốc đó khỏi cũ / mới / số lần / min / max — công tắc cho Q5 (ngày dòng cũ ở tương lai).

    `new_only=True` = chế độ NHẸ chỉ để lấy `new` (ô chọn mã): chỉ lần mua gần nhất, KHÔNG số gộp (đếm / min / max / ngày cuối
    không có nghĩa) và `old` luôn None — bỏ hẳn lượt quét toàn sổ nên rẻ hơn nhiều khi sổ giá lớn.

    `stats_codes` (tập con của `codes`) = chỉ các mã này được tính SỐ GỘP (số lần mua, ngày cuối, min / max); mã còn lại chỉ có
    cũ / mới / hai lần mua (đủ để tính chi phí) — tiết kiệm lượt quét toàn bộ dòng của các mã thành phần mà màn không hiện min / max.
    Mặc định `None` = mọi mã đều có số gộp. Chỉ dùng được khi `codes` không phải `None`.
    """
    also = set(also or ())
    # điều kiện chung của mọi dòng sổ được xét (phạm vi pháp nhân, mốc ngày); `codes` do bảng dẫn của truy vấn gộp lo
    base = [c for c in (scope_cond, L.price_date <= as_of if as_of is not None else None) if c is not None]

    # 1) sổ giá: số lần mua (kể cả giá 0), ngày cuối, min / max trong khoảng ngày + hai lần mua có giá gần nhất — mỗi tầng MỘT câu
    in_range = [L.price > 0]
    if date_from is not None:
        in_range.append(L.price_date >= date_from)
    if date_to is not None:
        in_range.append(L.price_date <= date_to)
    ranged = case((and_(*in_range), L.price))
    rank_conds = [L.price > 0, *base]
    agg_cols = [func.count(L.id), func.max(L.price_date), func.min(ranged), func.max(ranged)]
    if new_only:
        ledger = latest_priced_by_code(db, 1, codes=codes, rank_conds=rank_conds)
    else:
        full, light = (codes, set()) if stats_codes is None or codes is None else (stats_codes & codes, codes - stats_codes)
        ledger: dict = {}
        if full is None or full:
            ledger = latest_priced_by_code(db, 2, codes=full, rank_conds=rank_conds, agg_conds=base, agg_cols=agg_cols)
        if light:
            ledger |= latest_priced_by_code(db, 2, codes=light, rank_conds=rank_conds)

    # 2) báo giá mới nhất theo mã (kể cả hiệu lực ở tương lai)
    q_rn = func.row_number().over(partition_by=ProductPriceQuote.product_code,
                                  order_by=(ProductPriceQuote.valid_from.desc(), ProductPriceQuote.id.desc())).label("rn")
    q_inner = select(ProductPriceQuote.product_code, ProductPriceQuote.price, ProductPriceQuote.valid_from,
                     ProductPriceQuote.supplier_code, q_rn)
    if codes is not None:
        q_inner = q_inner.where(ProductPriceQuote.product_code.in_(codes or {""}))
    q_inner = q_inner.subquery()
    quotes = db.execute(select(q_inner).where(q_inner.c.rn == 1)).all()

    states: dict[str, PriceState] = {}

    def state(code: str) -> PriceState:
        return states.setdefault(code, PriceState(code=code))

    for code, entry in ledger.items():
        st = state(code)
        if entry.stats:
            count, last, lo, hi = entry.stats
            st.purchase_count, st.last_date, st.min, st.max = int(count or 0), last, lo, hi
        if entry.rows:
            st.p1 = _point(entry.rows[0])
        if len(entry.rows) > 1:
            st.p2 = _point(entry.rows[1])
    for r in quotes:
        state(r.product_code).quote = QuotePoint(r.price, r.valid_from, r.supplier_code or "")
    for code in also:
        state(code)
    for st in states.values():
        st.old, st.new = derive_old_new(st.p1, st.p2, st.quote)
        if new_only:
            st.old = None

    # 3) tên / nhóm / ĐVT danh mục
    info = {c: (n or "", g or "", u or "") for c, n, g, u in
            db.query(Product.code, Product.name, Product.item_group, Product.unit).filter(Product.code.in_(set(states) or {""})).all()}
    for code, st in states.items():
        st.name, st.group, st.unit = info.get(code, ("", "", ""))
        #  ĐVT danh mục thường để trống: lấy ĐVT của lần mua có giá gần nhất có ghi ĐVT (đã nằm sẵn trong truy vấn xếp hạng,
        #  không thêm truy vấn) — cùng luật với "Giá mua gần nhất" (duoc-CR-784, 26/11/2026).
        if not st.unit:
            st.unit = next((pt.unit for pt in (st.p1, st.p2) if pt is not None and pt.unit), "")
    return states
