"""API tab Giá mua gần nhất (ma trận 3 / 5 / 10 lần mua mỗi mã VTBB) của màn Giá bao bì (duoc-CR-784).

Router con, gắn vào `impact_controller.router` (cùng tiền tố `/api/packaging-cost`) nên không phải sửa `main.py`.
Phạm vi dữ liệu theo PHÁP NHÂN đo trên sổ giá — cùng luật với Tác động giá / Bảng giá.

bao-CR-792 (27/11/2026): mỗi màn của cụm một khóa quyền; màn này gác `packaging_last_price`. `view_scope` nhận khóa của màn
gọi; `shared_view_scope` dành cho đường dùng chung nhiều màn.
"""
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import StringConstraints
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.permissions import PACKAGING_ENTITIES
from app.core.response import success
from app.core.scoping import PUBLIC, SCOPE_FIELDS, get_perm_profile, scope_condition
from app.modules.product_price.model import ProductPriceLedger

from . import export_columns as xl
from .last_prices_service import DEFAULT_N, MAX_N, build_last_prices

ENTITY = "packaging_last_price"
MAX_PAGE_SIZE = 500
MAX_GROUPS = 200     #  số nhóm tối đa trong một lần gọi (ô chọn nhiều nhóm, 27/11/2026: prod có khoảng 42 nhóm nên trần 50 quá sát)
GroupValue = Annotated[str, StringConstraints(max_length=50)]    #  độ dài từng tên nhóm (cột item_group dài 50)
router = APIRouter()


def view_scope(db: Session, user, entity: str, action: str = "read"):
    """Điều kiện phạm vi pháp nhân của người xem trên sổ giá theo khóa `entity` của màn đang gọi (None = thấy hết)."""
    return scope_condition(ProductPriceLedger, entity, user, get_perm_profile(db, user), action)


def shared_view_scope(db: Session, user, action: str = "read"):
    """Phạm vi trên sổ giá cho đường DÙNG CHUNG nhiều màn (bao-CR-792) = HỢP phạm vi các khóa người xem giữ.

    Chỉ tính các khóa đo trên sổ giá; `packaging_bom` (danh mục dùng chung, không có giá) không góp phạm vi nào — người chỉ
    có khóa đó vẫn gọi được đường dùng chung nhưng không thấy giá. None = thấy hết.
    """
    profile = get_perm_profile(db, user)
    conds = [scope_condition(ProductPriceLedger, entity, user, profile, action)
             for entity in PACKAGING_ENTITIES if SCOPE_FIELDS[entity] is not PUBLIC]
    return None if any(cond is None for cond in conds) else or_(*conds)


def last_price_filters(
    n: int = Query(DEFAULT_N, ge=2, le=MAX_N), q: str = Query("", max_length=100),
    group: list[GroupValue] = Query([], max_length=MAX_GROUPS),
    supplier: list[str] = Query([], max_length=50), date_from: date | None = None, date_to: date | None = None,
    trend: str = Query("all", pattern="^(all|up|down|flat)$"), min_pct: float | None = Query(None, ge=0, le=100000),
    only_priced: bool = True, bom_only: bool = False, scope: str = Query("bom", pattern="^(bom|all)$"),
    sort_by: str = Query("code", max_length=30), sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
) -> dict:
    """Bộ tham số lọc + xếp dùng chung cho danh sách và Xuất Excel (cùng thứ tự)."""
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "Từ ngày không được sau Đến ngày")
    return {"n": n, "q": q, "groups": group, "suppliers": supplier, "date_from": date_from, "date_to": date_to,
            "trend": trend, "min_pct": min_pct, "only_priced": only_priced, "bom_only": bom_only, "scope": scope,
            "sort_by": sort_by, "sort_dir": sort_dir}


@router.get("/last-prices")
def last_prices(filters: dict = Depends(last_price_filters), page: int = Query(1, ge=1),
                page_size: int = Query(50, ge=1, le=MAX_PAGE_SIZE), db: Session = Depends(get_db),
                user=Depends(require(ENTITY, "read"))):
    """Giá mua gần nhất: mỗi mã VTBB một dòng (ngày, nhà cung cấp, số lượng, đơn giá n lần mua, biến động, giá trung bình).

    `n` = số lần hiển thị (2–10, mặc định 5). Lần 1 là lần mua có giá (> 0) gần nhất; `purchases` xếp từ gần nhất tới xa
    nhất. `v12` / `v1n` là tỷ số biến động lần 1 so lần 2 / lần n (0,05 = +5%). Bộ lọc: `q` (mã, tên, nhóm, nhà cung cấp),
    `group` (lặp được, `group=Chai&group=Nắp` = nhóm Chai HOẶC Nắp; tối đa 200 nhóm, mỗi tên <= 50 ký tự; chỉ một giá trị vẫn
    nhận như cũ), `supplier` (lặp được — giữ mã có nhà cung cấp đó trong n lần đang hiện), `date_from` / `date_to` (chỉ các lần
    mua trong khoảng được xếp hạng), `trend` (all / up / down / flat — lần 1 so lần 2), `min_pct` (|biến động| >= %),
    `only_priced` (mặc định bật), `bom_only` (chỉ mã thành phần của định mức), `scope=bom|all`. `sort_by` là khóa cột
    (`code, name, group, unit, purchase_count, last_price, last_date, v12, v1n, avg` hoặc `p{k}_price` / `p{k}_date`), ô
    trống xuống cuối. Trả thêm `groups` (số mã mỗi nhóm) và `suppliers` (để vẽ chip / ô chọn, chưa áp `q`, `group`,
    `supplier`, `trend`, `min_pct`; `groups` đếm sau mọi bộ lọc trừ chính bộ lọc nhóm). Quyền `packaging_last_price.read`; chỉ tính các dòng sổ giá thuộc pháp nhân người xem được thấy.
    """
    res = build_last_prices(db, **filters, scope_cond=view_scope(db, user, ENTITY, "read"))
    start = (page - 1) * page_size
    return success({"items": res["rows"][start:start + page_size], "total": len(res["rows"]), "groups": res["groups"],
                    "suppliers": res["suppliers"]})


@router.get("/last-prices/export")
def last_prices_export(filters: dict = Depends(last_price_filters), show_qty: bool = False,
                       db: Session = Depends(get_db), user=Depends(require(ENTITY, "export"))):
    """Xuất Excel Giá mua gần nhất theo đúng bộ lọc, số lần `n` và thứ tự đang xem (không phân trang); `show_qty` thêm cột số lượng. Quyền `packaging_last_price.export`."""
    res = build_last_prices(db, **filters, scope_cond=view_scope(db, user, ENTITY, "export"))
    return xl.xlsx_download(xl.build_last_prices_workbook(res["rows"], filters["n"], show_qty), "gia-mua-gan-nhat")
