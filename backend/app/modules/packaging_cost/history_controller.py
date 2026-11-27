"""API tab Lịch sử mua hàng của màn Giá bao bì (duoc-CR-784): từng lần mua theo mã VTBB / theo sản phẩm, KPI, biểu đồ, Excel.

Router con, gắn vào `impact_controller.router` (cùng tiền tố `/api/packaging-cost`) nên không phải sửa `main.py`.
Phạm vi dữ liệu theo PHÁP NHÂN đo trên sổ giá — cùng luật với Tác động giá / Bảng giá / Giá mua gần nhất.

bao-CR-792 (27/11/2026): màn này gác khóa `packaging_history`; ô chọn sản phẩm `/fg-options` là danh mục định mức dùng chung
nên mở khi có `read` trên bất kỳ khóa nào của cụm.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import require, require_any
from app.core.database import get_db
from app.core.permissions import PACKAGING_ENTITIES
from app.core.response import success

from . import export_columns as xl
from .history_service import MAX_CODES, build_history
from .last_prices_controller import MAX_PAGE_SIZE, view_scope
from .model import PackagingBom

ENTITY = "packaging_history"
router = APIRouter()


def history_filters(
    mode: str = Query("code", pattern="^(code|product)$"), codes: list[str] = Query([], max_length=MAX_CODES),
    fg_codes: list[str] = Query([], max_length=MAX_CODES), q: str = Query("", max_length=100),
    supplier: list[str] = Query([], max_length=50), date_from: date | None = None, date_to: date | None = None,
    sort_by: str = Query("date", max_length=30), sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
) -> dict:
    """Bộ tham số lọc + xếp dùng chung cho danh sách và Xuất Excel (cùng thứ tự)."""
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "Từ ngày không được sau Đến ngày")
    return {"mode": mode, "codes": codes, "fg_codes": fg_codes, "q": q, "suppliers": supplier, "date_from": date_from,
            "date_to": date_to, "sort_by": sort_by, "sort_dir": sort_dir}


@router.get("/history")
def history(filters: dict = Depends(history_filters), page: int = Query(1, ge=1),
            page_size: int = Query(50, ge=1, le=MAX_PAGE_SIZE), db: Session = Depends(get_db),
            user=Depends(require(ENTITY, "read"))):
    """Lịch sử mua hàng: từng lần mua của mã VTBB (hoặc thành phần của sản phẩm), mới nhất trước, kèm KPI và dữ liệu biểu đồ.

    `mode=code`: `codes` (lặp được, tối đa 200; rỗng = mọi mã VTBB của cụm giá), mỗi dòng một lần mua. `mode=product`: `fg_codes`
    (tối đa 200; rỗng = mọi sản phẩm có định mức): mỗi dòng = một lần mua x MỘT cặp (sản phẩm, mã thành phần của định mức) — mã
    dùng ở 275 sản phẩm thì một lần mua cho 275 dòng (bản mẫu `renderHistBySP`), kèm `fg_code` / `fg_name` / `role` (mã vai trò
    chai / nắp / nhãn / nhãn thùng / thùng); mã xuất hiện hai vai trò trong cùng sản phẩm chỉ tính một lần (vai trò nhỏ nhất).
    Thứ tự mặc định chế độ sản phẩm: ngày giảm dần -> mã sản phẩm -> thành phần. Bộ lọc: `q` (mã, tên vật tư, mã / tên nhà cung
    cấp, tên kho; chế độ sản phẩm thêm mã / tên sản phẩm và tên thành phần), `supplier` (lặp được), `date_from` / `date_to`.
    `sort_by` trong `date, code, name, supplier, warehouse, qty, price, amount, vat, source` (+ `fg_code, fg_name, role` chỉ ở
    chế độ sản phẩm; khóa lạ -> `date` giảm), ô trống xuống cuối. Nguồn: sổ giá ba nguồn (`source_type` 1 = lịch sử cũ nạp Excel, 2 = dòng
    ĐMH của ERP, 3 = sổ Misa) kèm `line_stage` (1 = đang mở, 2 = đã chốt) và cờ `is_open` (= dòng ĐMH đang mở, giao diện hiện nhãn
    "ĐMH đang mở"); khóa xếp `source` theo nhãn hiện: lịch sử < ĐMH đang mở < Misa; dòng đơn giá 0 vẫn hiện nhưng không tính vào KPI / biểu đồ. Mỗi dòng kèm `warehouse` (tên kho nhập
    hàng, rỗng nếu không biết), `amount` = GIÁ TRỊ MUA (thành tiền Misa khi có, không thì giá x số lượng; None ở dòng giá 0),
    `prev_price` / `diff` / `pct` so với lần mua CÓ GIÁ liền trước của cùng mã (không phụ thuộc bộ lọc), `seq` = lần mua của mã
    trên toàn bộ lịch sử trong phạm vi quyền, 1 = lần mua GẦN NHẤT, `doc_id` / `po_code` = ĐMH nguồn (0 / rỗng nếu dữ liệu cũ
    không có). Trả `stats` (trên TOÀN BỘ tập đã lọc: `purchase_count` = số dòng, `priced_count, qty_total, weighted_avg` gia quyền
    theo số lượng của giá trị mua, `min, max, supplier_count, first_date, last_date`, `amount_total` = tổng giá trị mua của lần
    có giá, `code_count` = số mã có lần mua, `product_count` = số sản phẩm có định mức trong phạm vi chọn (chế độ sản phẩm),
    `unit`, `first_price` / `last_price` = giá lần có giá đầu tiên / gần nhất, chế độ sản phẩm để trống), `series` (chế độ mã,
    đúng một mã được chọn: tối đa 1.000 điểm giá cũ -> mới), `series_by_code` (chế độ sản phẩm, đúng MỘT sản phẩm được chọn: mỗi mã
    thành phần có lần mua có giá một đường `{code, name, role, points: [{date, price}]}`, xếp theo vai trò, tối đa 1.000 điểm giá cũ -> mới
    mỗi mã; ngược lại `null`) và `suppliers` (cho ô chọn, chưa áp `q` / `supplier`). Quyền
    `packaging_history.read`; chỉ tính các dòng sổ giá thuộc pháp nhân người xem được thấy.
    """
    res = build_history(db, **filters, page=page, page_size=page_size, scope_cond=view_scope(db, user, ENTITY, "read"))
    return success(res)


@router.get("/history/export")
def history_export(filters: dict = Depends(history_filters), db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "export"))):
    """Xuất Excel Lịch sử mua hàng theo đúng bộ lọc + thứ tự đang xem (không phân trang, tối đa 5.000 dòng). Quyền `packaging_history.export`."""
    res = build_history(db, **filters, page=None, scope_cond=view_scope(db, user, ENTITY, "export"))
    return xl.xlsx_download(xl.build_history_workbook(res["items"], product_mode=filters["mode"] == "product"),
                            "lich-su-mua-hang")


@router.get("/fg-options")
def fg_options(db: Session = Depends(get_db),
               user=Depends(require_any(*((entity, "read") for entity in PACKAGING_ENTITIES)))):
    """Ô chọn sản phẩm của Lịch sử mua hàng: mọi mã hàng hóa có định mức bao bì, kèm `{code, name}` (~1.000, không phân trang).

    Đường dùng chung (bao-CR-792): quyền `read` trên BẤT KỲ khóa nào của cụm Giá NVL sản xuất; không trả giá nên không lọc phạm vi.
    """
    rows = db.query(PackagingBom.fg_code, PackagingBom.fg_name).order_by(PackagingBom.fg_code).all()
    return success({"items": [{"code": code, "name": name or ""} for code, name in rows]})
