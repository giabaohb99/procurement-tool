"""N lần mua có giá gần nhất của từng mã + số gộp theo mã, trong MỘT câu SQL (duoc-CR-784, hiệu năng khi sổ giá lớn).

Lý do tồn tại: bản đầu xếp hạng bằng `ROW_NUMBER() OVER (PARTITION BY product_code ORDER BY ...)` rồi lọc `rn <= n`. MySQL
không đẩy `rn <= n` xuống nên phải xếp CẢ sổ giá (650 nghìn dòng = 5 – 20 giây). Cách làm ở đây không dùng hàm cửa sổ:

  1. Bảng dẫn `t` = MỘT dòng mỗi mã (GROUP BY `product_code`, kèm các số gộp của người gọi) + cột `thr` = NGÀY của lần mua thứ n
     (truy vấn con tương quan, `ORDER BY ... LIMIT 1 OFFSET n-1`, đọc chỉ mục phủ `ix_ppl_code_latest`).
  2. LEFT JOIN sổ giá với `price_date >= thr` (mã có ít hơn n lần mua thì `thr` rỗng → lấy hết) — chỉ đọc đoạn cuối của mã.
  3. Python xếp lại `(ngày, doc_id, id)` giảm dần rồi cắt đúng n (cùng ngày với `thr` có thể thừa vài dòng).

Chỉ dùng phép chuẩn (truy vấn con vô hướng, OFFSET, LEFT JOIN) nên chạy giống nhau trên MySQL (thật) và SQLite (bài kiểm).
Chỉ mục phủ `(product_code, price_date, doc_id, id, price, company_id)` trả lời được mọi điều kiện (giá > 0, pháp nhân) mà
không chạm bảng. Thứ tự "gần nhất" giữ đúng luật cũ: ngày giảm, rồi `doc_id` giảm, rồi id dòng giảm (xem `price_state_service`).

Điều kiện phạm vi pháp nhân (`scope_cond`) do người gọi dựng trên `ProductPriceLedger`; hàm này tự chuyển nó sang các bí danh.
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy import and_, func, inspect, select, true
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql.util import ClauseAdapter

from .misa_cutoff import misa_cutoff_condition
from .model import ProductPriceLedger as L

#  Mốc "xa nhất" thay cho `thr` rỗng — luôn nhỏ hơn mọi ngày hợp lệ (schema chặn năm < MIN_YEAR).
FAR_PAST = date(1000, 1, 1)


@dataclass
class LedgerRow:
    """Một lần mua trong sổ giá (chỉ các cột màn giá cần)."""
    id: int
    price: Decimal
    qty: Decimal
    unit: str
    price_date: date
    supplier_code: str
    source_type: int
    doc_id: int
    supplier_name: str = ""     # tên nhà cung cấp chép theo dòng (nguồn Misa); trống = tra `tab_supplier` theo mã


@dataclass
class CodeLatest:
    """Kết quả của một mã: `stats` = các số gộp người gọi xin (theo thứ tự `agg_cols`), `rows` = tối đa n lần mua, mới nhất trước."""
    stats: tuple = ()
    rows: list[LedgerRow] = field(default_factory=list)


def _retarget(alias, cond):
    """Chuyển điều kiện dựng trên `ProductPriceLedger` sang một bí danh của nó."""
    return ClauseAdapter(inspect(alias).selectable).traverse(cond)


def uses_lateral(db: Session) -> bool:
    """MySQL 8.0.14+ có `LATERAL` (truy vấn con tương quan trong FROM) — cách nhanh nhất; còn lại dùng cách chuẩn dưới đây."""
    dialect = db.connection().dialect      # lấy kết nối trước: phiên bản máy chủ chỉ có sau lần nối đầu tiên của engine
    return dialect.name == "mysql" and not getattr(dialect, "is_mariadb", False) and (dialect.server_version_info or (0,)) >= (8, 0, 14)


def _detail_columns(outer):
    return [outer.id.label("l_id"), outer.price.label("l_price"), outer.qty.label("l_qty"), outer.unit.label("l_unit"),
            outer.price_date.label("l_date"), outer.supplier_code.label("l_supplier"), outer.source_type.label("l_source"),
            outer.doc_id.label("l_doc"), outer.supplier_name.label("l_supplier_name")]


def _lateral_statement(n: int, where: list, rank_conds: list, agg_cols: list | None, agg_conds: list | None):
    """Cách MySQL 8: bảng dẫn = danh sách mã (quét chỉ mục bỏ qua; `IN` chỉ lọc vài nghìn mã chứ không lọc từng dòng sổ), rồi
    MỖI mã dò chỉ mục hai lần bằng LATERAL — n id mới nhất, và (khi cần) các số gộp — cuối cùng nối khóa chính lấy chi tiết."""
    inner, outer = aliased(L), aliased(L)
    codes_table = select(L.product_code).where(*where).distinct().subquery("t")
    top = (select(inner.id).where(inner.product_code == codes_table.c.product_code, *[_retarget(inner, c) for c in rank_conds])
           .order_by(inner.price_date.desc(), inner.doc_id.desc(), inner.id.desc()).limit(n).lateral("top"))
    source = codes_table.outerjoin(top, true()).outerjoin(outer, outer.id == top.c.id)
    stat_cols, keep = [], []
    if agg_cols:
        gathered = aliased(L)
        agg = (select(func.count(gathered.id).label("agg_rows"),
                      *[_retarget(gathered, col).label(f"agg_{i}") for i, col in enumerate(agg_cols)])
               .where(gathered.product_code == codes_table.c.product_code, *[_retarget(gathered, c) for c in (agg_conds or [])])
               .lateral("agg"))
        source = source.outerjoin(agg, true())
        stat_cols = [agg.c[f"agg_{i}"] for i in range(len(agg_cols))]
        keep = [agg.c.agg_rows > 0]      # truy vấn gộp không GROUP BY luôn trả một dòng: mã không có dòng nào thỏa thì bỏ
    return select(codes_table.c.product_code, *stat_cols, *_detail_columns(outer)).select_from(source).where(*keep), len(stat_cols)


def _portable_statement(n: int, where: list, rank_conds: list, agg_cols: list | None, agg_conds: list | None):
    """Cách chuẩn (SQLite, MariaDB, MySQL cũ): `thr` = NGÀY của lần mua thứ n (truy vấn con vô hướng tương quan trong bảng dẫn
    GROUP BY), rồi nối sổ giá với `price_date >= thr`."""
    inner, outer = aliased(L), aliased(L)
    thr = (select(inner.price_date).where(inner.product_code == L.product_code, *[_retarget(inner, c) for c in rank_conds])
           .order_by(inner.price_date.desc(), inner.doc_id.desc(), inner.id.desc()).limit(1).offset(n - 1)
           .correlate(L).scalar_subquery().label("thr"))
    agg_labels = [col.label(f"agg_{i}") for i, col in enumerate(agg_cols or [])]
    t = select(L.product_code, *agg_labels, thr).where(*where, *(agg_conds or [])).group_by(L.product_code).subquery("t")
    source = t.outerjoin(outer, and_(outer.product_code == t.c.product_code, *[_retarget(outer, c) for c in rank_conds],
                                     outer.price_date >= func.coalesce(t.c.thr, FAR_PAST)))
    return select(t.c.product_code, *[t.c[lbl.name] for lbl in agg_labels], *_detail_columns(outer)).select_from(source), \
        len(agg_labels)


def latest_priced_by_code(db: Session, n: int, *, codes: set[str] | None, rank_conds: list, agg_cols: list | None = None,
                          agg_conds: list | None = None, strategy: str | None = None) -> dict[str, CodeLatest]:
    """`{mã: CodeLatest}` — đúng MỘT câu SQL bất kể số mã / số dòng sổ giá.

    * `codes` — giới hạn mã (`None` = mọi mã trong sổ).
    * `rank_conds` — điều kiện của dòng ĐƯỢC XẾP HẠNG (thường `price > 0`, phạm vi pháp nhân, khoảng ngày) — dựng trên `L`.
    * `agg_cols` — cột gộp theo mã (`func.count(L.id)`, ...) tính trên các dòng thỏa `agg_conds`; `None` = không cần số gộp
      (chế độ nhẹ: chỉ cần danh sách mã + n lần mua, rẻ nhất).
    * `strategy` — `"lateral"` / `"portable"`; mặc định tự chọn theo CSDL (`uses_lateral`). Hai cách cho CÙNG kết quả (bài kiểm
      đối chiếu); chỉ ép khi kiểm hoặc đo.
    Mã chỉ có mặt khi có dòng sổ thỏa `agg_conds` (hoặc bất kỳ dòng nào ở chế độ nhẹ); `rows` rỗng nếu không dòng nào được xếp hạng.
    """
    if n < 1:
        raise ValueError("n phải >= 1")
    # Mốc sổ Misa (`misa_cutoff.py`): MỘT chỗ duy nhất áp cho mọi đường tính giá — mã, hạng và số gộp đều chỉ thấy dòng còn hiệu lực.
    cut = misa_cutoff_condition()
    rank_conds = [*rank_conds, cut]
    agg_conds = [*(agg_conds or []), cut]
    build = _lateral_statement if (strategy == "lateral" if strategy else uses_lateral(db)) else _portable_statement
    where = [L.product_code.in_(codes or {""})] if codes is not None else []
    where.append(cut)
    stmt, stat_count = build(n, where, rank_conds, agg_cols, agg_conds)

    result: dict[str, CodeLatest] = {}
    for r in db.execute(stmt):
        m = r._mapping
        entry = result.get(m["product_code"])
        if entry is None:
            entry = result[m["product_code"]] = CodeLatest(stats=tuple(r[1:1 + stat_count]))
        if m["l_id"] is not None:
            entry.rows.append(LedgerRow(id=int(m["l_id"]), price=m["l_price"], qty=m["l_qty"], unit=m["l_unit"] or "",
                                        price_date=m["l_date"], supplier_code=m["l_supplier"] or "",
                                        source_type=int(m["l_source"]), doc_id=int(m["l_doc"] or 0),
                                        supplier_name=m["l_supplier_name"] or ""))
    for entry in result.values():
        entry.rows.sort(key=lambda row: (row.price_date, row.doc_id, row.id), reverse=True)
        del entry.rows[n:]
    return result
