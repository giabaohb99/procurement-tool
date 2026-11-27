"""API tab Tổng hợp theo sản phẩm của màn Giá bao bì (duoc-CR-784): mọi sản phẩm có định mức, chi phí / chai cũ so với mới.

Router con, gắn vào `impact_controller.router` (cùng tiền tố `/api/packaging-cost`) nên không phải sửa `main.py`. Đường tên
`/product-overview` (KHÔNG đặt `/summary`: cổng của repo coi mọi đường `/summary` là báo cáo của phân hệ Báo cáo, đòi
`require_report`). Phạm vi dữ liệu theo PHÁP NHÂN đo trên sổ giá — cùng luật với Tác động giá / Bảng giá / Lịch sử.
bao-CR-792 (27/11/2026): màn này gác khóa `packaging_product_summary`.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.packaging_price_codes import PackagingRole
from app.core.response import success

from . import export_columns as xl
from .impact_filters import ImpactFilters, check_range, make_range
from .impact_schema import MAX_CARTON_QTY, RANGE_LIMIT
from .last_prices_controller import MAX_PAGE_SIZE, view_scope
from .product_overview_service import build_product_overview

ENTITY = "packaging_product_summary"
router = APIRouter()

#  `part_roles=1,3`: danh sách loại thành phần cách nhau dấu phẩy, dựng từ `PackagingRole` (thêm loại mới là tự nhận).
_ROLE_ALT = "|".join(str(int(role)) for role in PackagingRole)
ROLES_PATTERN = f"^(({_ROLE_ALT})(,({_ROLE_ALT})){{0,{len(PackagingRole) - 1}}})?$"
ROLES_MAX_LENGTH = 3 * len(PackagingRole)      # tối đa hai chữ số mỗi loại + dấu phẩy


#  Biên của các ô khoảng số: có thể âm (chênh lệch giảm), chặn NaN / vô cực — cùng trần với thân `POST /impact`.
def _bound():
    return Query(None, ge=-RANGE_LIMIT, le=RANGE_LIMIT, allow_inf_nan=False)


def overview_filters(q: str = Query("", max_length=100), trend: str = Query("all", pattern="^(all|up|down|flat|missing)$"),
                     sort_by: str = Query("fg_code", max_length=30), sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
                     part_roles: str = Query("", pattern=ROLES_PATTERN, max_length=ROLES_MAX_LENGTH),
                     carton_qty_min: int | None = Query(None, ge=0, le=MAX_CARTON_QTY),
                     carton_qty_max: int | None = Query(None, ge=0, le=MAX_CARTON_QTY),
                     cost_old_bottle_min: float | None = _bound(), cost_old_bottle_max: float | None = _bound(),
                     cost_new_bottle_min: float | None = _bound(), cost_new_bottle_max: float | None = _bound(),
                     diff_bottle_min: float | None = _bound(), diff_bottle_max: float | None = _bound(),
                     diff_carton_min: float | None = _bound(), diff_carton_max: float | None = _bound(),
                     pct_min: float | None = _bound(), pct_max: float | None = _bound(),
                     warnings_only: bool = False) -> dict:
    """Bộ tham số lọc + xếp dùng chung cho danh sách và Xuất Excel (cùng thứ tự). Khoảng có biên dưới > biên trên là 422."""
    bounds = {"carton_qty": (carton_qty_min, carton_qty_max), "cost_old_bottle": (cost_old_bottle_min, cost_old_bottle_max),
              "cost_new_bottle": (cost_new_bottle_min, cost_new_bottle_max), "diff_bottle": (diff_bottle_min, diff_bottle_max),
              "diff_carton": (diff_carton_min, diff_carton_max), "pct": (pct_min, pct_max)}
    try:
        for name, (low, high) in bounds.items():
            check_range(name, low, high)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    advanced = ImpactFilters(part_roles=frozenset(int(r) for r in part_roles.split(",") if r), roles_by_presence=True,
                             warnings_only=warnings_only, **{name: make_range(*pair) for name, pair in bounds.items()})
    return {"q": q, "trend": trend, "sort_by": sort_by, "sort_dir": sort_dir, "filters": advanced}


@router.get("/product-overview")
def product_overview(filters: dict = Depends(overview_filters), page: int = Query(1, ge=1, le=100000),
                     page_size: int = Query(50, ge=1, le=MAX_PAGE_SIZE), db: Session = Depends(get_db),
                     user=Depends(require(ENTITY, "read"))):
    """Tổng hợp theo sản phẩm: mọi mã hàng hóa có định mức bao bì, chi phí bao bì / chai cũ và mới, chênh lệch, xu hướng.

    Cùng công thức và cùng luật giá cũ / mới với Tác động giá (báo giá tính là giá mới, dòng giá 0 bị bỏ qua), nhưng không
    có giá giả định. Mỗi dòng của `items` cùng hình với `products[]` của `POST /impact` (`parts`, `cost_old_bottle`,
    `cost_new_bottle`, `diff_bottle`, `pct`, `cost_old_carton`, `cost_applied_carton` = chi phí / thùng mới, `diff_carton`,
    `trend`, `warnings`). `trend` (mã số) = 1 tăng · 2 giảm · 3 không đổi · 4 chưa có giá (thiếu giá chai thì chi phí rỗng).
    Bộ lọc: `q` (mã HH, tên, tên pháp lý, mã thành phần, không phân biệt dấu), `trend=all|up|down|flat|missing`. Lọc nâng cao
    (VÀ với nhau, làm trong bộ nhớ sau khi tính chi phí nên số truy vấn không đổi): `part_roles` (vai trò 1..5 cách nhau dấu
    phẩy, vd `1,5`; giữ sản phẩm có MÃ ở một trong các vai trò đó: 1 chai · 2 nắp · 3 nhãn · 4 nhãn thùng · 5 thùng), khoảng
    `carton_qty_min/max` (số nguyên), `cost_old_bottle_min/max`, `cost_new_bottle_min/max`, `diff_bottle_min/max`,
    `diff_carton_min/max` (đồng) và `pct_min/max` (đơn vị %, so với số một chữ số lẻ đang hiện), biên đóng, dòng có giá trị
    trống bị loại khi khoảng đó bật, biên dưới > biên trên là 422; `warnings_only` (chỉ sản phẩm đang có cảnh báo). `sort_by` trong
    `fg_code, fg_name, carton_qty, cost_old_bottle, cost_new_bottle, diff_bottle, pct, diff_carton` và năm cột thành phần
    `part_bottle, part_cap, part_label, part_carton_label, part_carton` (giá mới của thành phần, hòa theo mã thành phần rồi mã HH;
    khóa lạ -> `fg_code`), ô trống xuống cuối cả hai chiều. `page_size` <= 500. `counts` = `{all, up, down, flat, missing}` trên tập đã lọc `q` + lọc nâng cao nhưng chưa lọc
    `trend`; `total` = số dòng sau mọi bộ lọc. Quyền `packaging_product_summary.read`; giá chỉ tính trên các dòng sổ giá thuộc pháp
    nhân người xem được thấy. Năm truy vấn cố định bất kể số sản phẩm.
    """
    return success(build_product_overview(db, **filters, page=page, page_size=page_size, scope_cond=view_scope(db, user, ENTITY, "read")))


@router.get("/product-overview/export")
def product_overview_export(filters: dict = Depends(overview_filters), db: Session = Depends(get_db),
                            user=Depends(require(ENTITY, "export"))):
    """Xuất Excel Tổng hợp theo sản phẩm theo đúng bộ lọc (kể cả lọc nâng cao) + thứ tự đang xem (không phân trang, tối đa 5.000 dòng). Quyền `packaging_product_summary.export`."""
    res = build_product_overview(db, **filters, page=None, scope_cond=view_scope(db, user, ENTITY, "export"))
    return xl.xlsx_download(xl.build_product_overview_workbook(res["items"]), "tong-hop-theo-san-pham")
