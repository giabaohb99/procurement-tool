"""API tab Lịch sử mua hàng của màn Giá bao bì (duoc-CR-784): từng lần mua theo mã VTBB / theo sản phẩm, KPI, biểu đồ, Excel.

Router con, gắn vào `impact_controller.router` (cùng tiền tố `/api/packaging-cost`) nên không phải sửa `main.py`.
Phạm vi dữ liệu theo PHÁP NHÂN đo trên sổ giá — cùng luật với Tác động giá / Bảng giá / Giá mua gần nhất.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import export_columns as xl
from .history_service import MAX_CODES, build_history
from .last_prices_controller import MAX_PAGE_SIZE, view_scope
from .model import PackagingBom

ENTITY = "packaging_cost"
router = APIRouter()


def history_filters(
    mode: str = Query("code", pattern="^(code|product)$"), codes: list[str] = Query([], max_length=MAX_CODES),
    hh_codes: list[str] = Query([], max_length=MAX_CODES), q: str = Query("", max_length=100),
    supplier: list[str] = Query([], max_length=50), date_from: date | None = None, date_to: date | None = None,
    sort_by: str = Query("date", max_length=30), sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
) -> dict:
    """Bộ tham số lọc + xếp dùng chung cho danh sách và Xuất Excel (cùng thứ tự)."""
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "Từ ngày không được sau Đến ngày")
    return {"mode": mode, "codes": codes, "hh_codes": hh_codes, "q": q, "suppliers": supplier, "date_from": date_from,
            "date_to": date_to, "sort_by": sort_by, "sort_dir": sort_dir}


@router.get("/history")
def history(filters: dict = Depends(history_filters), page: int = Query(1, ge=1),
            page_size: int = Query(50, ge=1, le=MAX_PAGE_SIZE), db: Session = Depends(get_db),
            user=Depends(require(ENTITY, "read"))):
    """Lịch sử mua hàng: từng lần mua của mã VTBB (hoặc thành phần của sản phẩm), mới nhất trước, kèm KPI và dữ liệu biểu đồ.

    `mode=code`: `codes` (lặp được, tối đa 200; rỗng = mọi mã VTBB của cụm giá). `mode=product`: `hh_codes` (tối đa 200; rỗng
    = mọi sản phẩm có định mức) -> các mã thành phần của định mức, mỗi dòng kèm `roles` (mã vai trò chai / nắp / nhãn /
    nhãn thùng / thùng). Bộ lọc: `q` (mã, tên sản phẩm, mã / tên nhà cung cấp, tên kho), `supplier` (lặp được), `date_from` /
    `date_to`. `sort_by` trong `date, code, name, supplier, warehouse, qty, price, amount, vat, source` (khóa lạ -> `date` giảm), ô
    trống xuống cuối. Nguồn: sổ giá hai nguồn (`source_type` 1 = lịch sử mua, 2 = dòng ĐMH đang mở); dòng đơn giá 0 vẫn
    hiện nhưng không tính vào KPI / biểu đồ. Mỗi dòng kèm `warehouse` (tên kho nhập hàng, rỗng nếu không biết), `prev_price` / `diff` / `pct` so với lần mua CÓ GIÁ liền trước
    của cùng mã (không phụ thuộc bộ lọc), `seq` = số thứ tự lần mua của mã, `doc_id` / `po_code` = ĐMH nguồn (0 / rỗng nếu
    dữ liệu cũ không có). Trả `stats` (trên TOÀN BỘ tập đã lọc: `purchase_count, priced_count, qty_total, weighted_avg`
    gia quyền theo số lượng, `min, max, supplier_count, first_date, last_date`, `amount_total` = tổng giá x SL của lần có giá,
    `code_count` = số mã có lần mua, `unit`, `first_price` / `last_price` = giá lần có giá đầu tiên / gần nhất), `series` (đúng một mã được chọn: tối đa 1.000
    điểm giá cũ -> mới) và `suppliers` (cho ô chọn, chưa áp `q` / `supplier`). Quyền `packaging_cost.read`; chỉ tính các dòng
    sổ giá thuộc pháp nhân người xem được thấy.
    """
    res = build_history(db, **filters, page=page, page_size=page_size, scope_cond=view_scope(db, user, "read"))
    return success(res)


@router.get("/history/export")
def history_export(filters: dict = Depends(history_filters), db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "export"))):
    """Xuất Excel Lịch sử mua hàng theo đúng bộ lọc + thứ tự đang xem (không phân trang, tối đa 5.000 dòng). Quyền `packaging_cost.export`."""
    res = build_history(db, **filters, page=None, scope_cond=view_scope(db, user, "export"))
    return xl.xlsx_download(xl.build_history_workbook(res["items"], product_mode=filters["mode"] == "product"),
                            "lich-su-mua-hang")


@router.get("/hh-options")
def hh_options(db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    """Ô chọn sản phẩm của Lịch sử mua hàng: mọi mã hàng hóa có định mức bao bì, kèm `{code, name}` (~1.000, không phân trang). Quyền `packaging_cost.read`."""
    rows = db.query(PackagingBom.hh_code, PackagingBom.hh_name).order_by(PackagingBom.hh_code).all()
    return success({"items": [{"code": code, "name": name or ""} for code, name in rows]})
