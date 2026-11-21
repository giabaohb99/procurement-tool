"""API tab Tổng hợp theo sản phẩm của màn Giá bao bì (duoc-CR-784): mọi sản phẩm có định mức, chi phí / chai cũ so với mới.

Router con, gắn vào `impact_controller.router` (cùng tiền tố `/api/packaging-cost`) nên không phải sửa `main.py`. Đường tên
`/product-overview` (KHÔNG đặt `/summary`: cổng của repo coi mọi đường `/summary` là báo cáo của phân hệ Báo cáo, đòi
`require_report`). Phạm vi dữ liệu theo PHÁP NHÂN đo trên sổ giá — cùng luật với Tác động giá / Bảng giá / Lịch sử.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import export_columns as xl
from .last_prices_controller import MAX_PAGE_SIZE, view_scope
from .product_overview_service import build_product_overview

ENTITY = "packaging_cost"
router = APIRouter()


def overview_filters(q: str = Query("", max_length=100), trend: str = Query("all", pattern="^(all|up|down|flat|missing)$"),
                     sort_by: str = Query("hh_code", max_length=30), sort_dir: str = Query("asc", pattern="^(asc|desc)$")) -> dict:
    """Bộ tham số lọc + xếp dùng chung cho danh sách và Xuất Excel (cùng thứ tự)."""
    return {"q": q, "trend": trend, "sort_by": sort_by, "sort_dir": sort_dir}


@router.get("/product-overview")
def product_overview(filters: dict = Depends(overview_filters), page: int = Query(1, ge=1, le=100000),
                     page_size: int = Query(50, ge=1, le=MAX_PAGE_SIZE), db: Session = Depends(get_db),
                     user=Depends(require(ENTITY, "read"))):
    """Tổng hợp theo sản phẩm: mọi mã hàng hóa có định mức bao bì, chi phí bao bì / chai cũ và mới, chênh lệch, xu hướng.

    Cùng công thức và cùng luật giá cũ / mới với Tác động giá (báo giá tính là giá mới, dòng giá 0 bị bỏ qua), nhưng không
    có giá giả định. Mỗi dòng của `items` cùng hình với `products[]` của `POST /impact` (`parts`, `cost_old_bottle`,
    `cost_new_bottle`, `diff_bottle`, `pct`, `cost_old_carton`, `cost_applied_carton` = chi phí / thùng mới, `diff_carton`,
    `trend`, `warnings`). `trend` (mã số) = 1 tăng · 2 giảm · 3 không đổi · 4 chưa có giá (thiếu giá chai thì chi phí rỗng).
    Bộ lọc: `q` (mã HH, tên, tên pháp lý, mã thành phần, không phân biệt dấu), `trend=all|up|down|flat|missing`. `sort_by` trong
    `hh_code, hh_name, carton_qty, cost_old_bottle, cost_new_bottle, diff_bottle, pct, diff_carton` (khóa lạ -> `hh_code`), ô trống
    xuống cuối cả hai chiều. `page_size` <= 500. `counts` = `{all, up, down, flat, missing}` trên tập đã lọc `q` nhưng chưa lọc
    `trend`; `total` = số dòng sau cả hai bộ lọc. Quyền `packaging_cost.read`; giá chỉ tính trên các dòng sổ giá thuộc pháp
    nhân người xem được thấy. Năm truy vấn cố định bất kể số sản phẩm.
    """
    return success(build_product_overview(db, **filters, page=page, page_size=page_size, scope_cond=view_scope(db, user, "read")))


@router.get("/product-overview/export")
def product_overview_export(filters: dict = Depends(overview_filters), db: Session = Depends(get_db),
                            user=Depends(require(ENTITY, "export"))):
    """Xuất Excel Tổng hợp theo sản phẩm theo đúng bộ lọc + thứ tự đang xem (không phân trang, tối đa 5.000 dòng). Quyền `packaging_cost.export`."""
    res = build_product_overview(db, **filters, page=None, scope_cond=view_scope(db, user, "export"))
    return xl.xlsx_download(xl.build_product_overview_workbook(res["items"]), "tong-hop-theo-san-pham")
