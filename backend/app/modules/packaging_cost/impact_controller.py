"""API màn Giá bao bì: tác động giá, bảng giá VTBB, ô chọn mã, xuất Excel (duoc-CR-784, phase 04).

Gác khóa `packaging_cost` (read / export). Phạm vi dữ liệu theo PHÁP NHÂN đo trên SỔ GIÁ: `scope_condition(...)` dựng điều
kiện trên `ProductPriceLedger.company_id` và đưa xuống `get_price_states` — giá cũ / mới / min / max chỉ tính trên các dòng sổ
người xem được thấy. Định mức / báo giá / ngưỡng là danh mục dùng chung nên không lọc.
"""
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import export_columns as xl
from .impact_schema import ImpactRequest
from .history_controller import router as history_router
from .impact_service import compute_impact
from .last_prices_controller import router as last_prices_router
from .last_prices_controller import view_scope as _scope
from .price_list_service import SORT_KEYS, build_price_list, build_price_list_page

ENTITY = "packaging_cost"
MAX_PAGE_SIZE = 500
router = APIRouter(prefix="/api/packaging-cost", tags=["packaging-cost"])


def _range(date_from: date | None, date_to: date | None) -> None:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "Từ ngày không được sau Đến ngày")


def _impact(db: Session, body: ImpactRequest, user, action: str, *, paged: bool) -> dict:
    """`paged=True` (màn hình) cắt bảng sản phẩm theo `page` / `page_size`; `False` (xuất Excel) lấy đủ mọi dòng sau lọc + xếp."""
    return compute_impact(db, body.codes, {c: Decimal(str(v)) for c, v in body.assumed_prices.items()},
                          date_from=body.date_from, date_to=body.date_to, scope_cond=_scope(db, user, action),
                          page=body.page if paged else None, page_size=body.page_size, q=body.q,
                          sort_by=body.sort_by, sort_dir=body.sort_dir)


@router.post("/impact")
def impact(body: ImpactRequest, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    """Tác động giá bao bì: chọn các mã chai / nắp / nhãn / nhãn thùng / thùng (kèm giá giả định) → sản phẩm bị ảnh hưởng.

    Trả `{selected, kpis, products, products_total}`; số kèm mã (xu hướng, cảnh báo, vai trò thành phần), không kèm câu tiếng
    Việt. Là đọc thuần (không ghi nhật ký). Quyền `packaging_cost.read`; giá chỉ tính trên các dòng sổ giá thuộc pháp nhân
    người xem được thấy. `kpis` tính trên TOÀN BỘ sản phẩm bị ảnh hưởng; bảng `products` phân trang tại máy chủ
    (`page`, `page_size` <= 500) sau khi lọc `q` (mã HH, tên, tên pháp lý, mã thành phần — không phân biệt dấu) và xếp
    `sort_by` (`hh_code, hh_name, carton_qty, cost_old_bottle, cost_applied_bottle, diff_bottle, diff_carton,
    cost_old_carton, cost_applied_carton, pct, trend`; khóa lạ → `hh_code`) theo `sort_dir`, ô trống xuống cuối;
    `products_total` = số dòng sau lọc `q`. Mã không có trong định mức nào vẫn trả 200 với `products` rỗng; tối đa 500 mã,
    giá giả định >= 0 (422 nếu sai).
    """
    return success(_impact(db, body, user, "read", paged=True))


@router.post("/impact/export")
def impact_export(body: ImpactRequest, db: Session = Depends(get_db), user=Depends(require(ENTITY, "export"))):
    """Xuất Excel kết quả Tác động giá (hai sheet: Mã đã chọn, Sản phẩm bị ảnh hưởng). Quyền `packaging_cost.export`.

    Bỏ qua `page` / `page_size` (xuất ĐỦ mọi dòng, chặn bởi trần số dòng của lần xuất), nhưng theo `q` + `sort_by` / `sort_dir`
    như bảng đang xem.
    """
    return xl.xlsx_download(xl.build_impact_workbook(_impact(db, body, user, "export", paged=False)), "tac-dong-gia-bao-bi")


def _check_list_params(date_from: date | None, date_to: date | None, sort_dir: str) -> None:
    _range(date_from, date_to)
    if sort_dir not in ("asc", "desc"):
        raise HTTPException(422, "sort_dir chỉ nhận asc hoặc desc")


def _price_list(db: Session, user, action: str, *, q, group, scope, breach_only, date_from, date_to, sort_by, sort_dir):
    _check_list_params(date_from, date_to, sort_dir)
    return build_price_list(db, q=q, group=group, scope=scope, breach_only=breach_only, date_from=date_from,
                            date_to=date_to, sort_by=sort_by, sort_dir=sort_dir, scope_cond=_scope(db, user, action))


@router.get("/price-list")
def price_list(q: str = Query("", max_length=100), group: str = Query("", max_length=50),
               scope: str = Query("bom", pattern="^(bom|all)$"), breach_only: bool = False,
               date_from: date | None = None, date_to: date | None = None,
               sort_by: str = Query("code", max_length=30), sort_dir: str = "asc",
               page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=MAX_PAGE_SIZE),
               db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    """Bảng giá VTBB: mỗi mã vật tư một dòng (giá cũ / mới / chênh, số sản phẩm dùng, báo giá, ngưỡng).

    `scope=bom` = mã thành phần của định mức ∪ mã có báo giá; `scope=all` = thêm mọi mã có trong sổ giá. `breach_only` chỉ
    lấy mã đang dưới sàn / vượt trần. Lọc + xếp (`sort_by` trong khóa cho phép, ô trống xuống cuối) tại máy chủ rồi mới
    phân trang; xếp theo cột danh mục (`code, name, group, unit`) thì chỉ tính giá cho các mã của trang (nhanh khi sổ giá lớn).
    Quyền `packaging_cost.read`.
    """
    _check_list_params(date_from, date_to, sort_dir)
    items, total = build_price_list_page(db, page=page, page_size=page_size, q=q, group=group, scope=scope, breach_only=breach_only,
                                         date_from=date_from, date_to=date_to, sort_by=sort_by if sort_by in SORT_KEYS else "code",
                                         sort_dir=sort_dir, scope_cond=_scope(db, user, "read"))
    return success({"items": items, "total": total})


@router.get("/price-list/export")
def price_list_export(q: str = Query("", max_length=100), group: str = Query("", max_length=50),
                      scope: str = Query("bom", pattern="^(bom|all)$"), breach_only: bool = False,
                      date_from: date | None = None, date_to: date | None = None,
                      sort_by: str = Query("code", max_length=30), sort_dir: str = "asc",
                      db: Session = Depends(get_db), user=Depends(require(ENTITY, "export"))):
    """Xuất Excel Bảng giá VTBB theo đúng bộ lọc + thứ tự đang xem (không phân trang). Quyền `packaging_cost.export`."""
    rows = _price_list(db, user, "export", q=q, group=group, scope=scope, breach_only=breach_only, date_from=date_from,
                       date_to=date_to, sort_by=sort_by if sort_by in SORT_KEYS else "code", sort_dir=sort_dir)
    return xl.xlsx_download(xl.build_price_list_workbook(rows), "bang-gia-vtbb")


@router.get("/code-options")
def code_options(q: str = Query("", max_length=100), group: str = Query("", max_length=50),
                 db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    """Ô chọn nhiều mã của màn Tác động: mọi mã đang dùng trong định mức, kèm `{code, name, group, usage, new}`.

    Trả đủ (~1.500 mã), không phân trang — giao diện lọc tại chỗ. Quyền `packaging_cost.read`.
    """
    rows = build_price_list(db, q=q, group=group, scope="bom", scope_cond=_scope(db, user, "read"), new_only=True)
    return success({"items": [{k: r[k] for k in ("code", "name", "group", "usage", "new")} for r in rows if r["usage"] > 0]})


router.include_router(last_prices_router)
router.include_router(history_router)
