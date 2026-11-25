"""Dụng cụ dùng chung cho bài kiểm sổ giá / tác động giá bao bì (duoc-CR-784): dựng ĐMH, dòng, lịch sử, báo giá."""
from datetime import date
from decimal import Decimal

from app.core.packaging_price_codes import PackagingRole, PriceSourceType
from app.modules.packaging_cost.bom_parts_service import codes_from_fields, set_bom_codes
from app.modules.packaging_cost.model import PackagingBom, PackagingBomPart, role_field
from app.modules.product.model import Product
from app.modules.product_price.model import ProductPriceLedger, ProductPriceLimit, ProductPriceQuote
from app.modules.purchase_order.model import POItem, PurchaseOrder


CODE_FIELDS = tuple(role_field(role) for role in PackagingRole)


def build_bom(**fields) -> PackagingBom:
    """Định mức bao bì dựng từ trường PHẲNG của API (`bottle_code`, `cap_code`...): đầu phiếu + dòng thành phần (mã rỗng thì không
    tạo dòng). CHƯA `add` / `commit` — nơi gọi tự quyết, như khi còn dựng thẳng `PackagingBom(...)`."""
    header = {k: v for k, v in fields.items() if k not in CODE_FIELDS}
    bom = PackagingBom(**header)
    set_bom_codes(bom, codes_from_fields(fields))
    return bom


def bom_codes_of(db, hh_code: str) -> dict[int, str]:
    """`{loại thành phần: mã}` đang lưu trong bảng thành phần của một mã hàng hóa (đọc thẳng DB, không qua thuộc tính chỉ đọc)."""
    rows = (db.query(PackagingBomPart.part_type, PackagingBomPart.part_code).join(PackagingBom, PackagingBom.id == PackagingBomPart.bom_id)
            .filter(PackagingBom.hh_code == hh_code).all())
    return {int(t): c for t, c in rows}


def make_po(db, **over) -> PurchaseOrder:
    base = dict(code="PO0001", pr_code="", misa_code="M1", company_id=1, supplier_code="NCC01", supplier_name="NCC Một",
                order_date="2026-10-01", status="draft", created_by=1, updated_by=1)
    base.update(over)
    po = PurchaseOrder(**base)
    db.add(po)
    db.commit()
    db.refresh(po)
    return po


def make_item(db, po, **over) -> POItem:
    base = dict(po_id=po.id, product_code="CPT0075", product_name="Chai 1L", unit="Cái", qty_order=1000, price=1000,
                vat=8, amount=1080000, progress_status="not_ordered")
    base.update(over)
    it = POItem(**base)
    db.add(it)
    db.commit()
    db.refresh(it)
    return it


def ledger_rows(db, **flt):
    q = db.query(ProductPriceLedger)
    for k, v in flt.items():
        q = q.filter(getattr(ProductPriceLedger, k) == v)
    return q.order_by(ProductPriceLedger.id).all()


def add_ledger(db, code, price, on, *, source_type=PriceSourceType.PURCHASE_HISTORY, source_id=None, supplier="NCC01",
               company_id=1, unit="Cái", qty=100, doc_id=0, warehouse=None, amount=None):
    """Dòng sổ giá dựng thẳng (bài kiểm tầng tính giá không cần đi qua ĐMH). `amount` = thành tiền (None = chưa có)."""
    n = db.query(ProductPriceLedger).count() + 1
    row = ProductPriceLedger(source_type=int(source_type), source_id=source_id or (9000 + n), doc_id=doc_id,
                             product_code=code, supplier_code=supplier, company_id=company_id,
                             price_date=date.fromisoformat(on), price=Decimal(str(price)), vat=Decimal(8),
                             qty=Decimal(qty), unit=unit, warehouse_name=warehouse,
                             amount=None if amount is None else Decimal(str(amount)))
    db.add(row)
    db.commit()
    return row


def add_quote(db, code, price, valid_from, supplier=""):
    q = ProductPriceQuote(product_code=code, supplier_code=supplier, price=Decimal(str(price)), vat=Decimal(8),
                          valid_from=date.fromisoformat(valid_from), created_by=1, updated_by=1)
    db.add(q)
    db.commit()
    return q


def add_limit(db, code, floor=None, ceiling=None):
    row = ProductPriceLimit(product_code=code, floor_price=floor, ceiling_price=ceiling, created_by=1, updated_by=1)
    db.add(row)
    db.commit()
    return row


def add_products(db, *codes_names_units):
    """`(code, name, unit)` -> `tab_product` (chỉ vài cột cần cho màn giá)."""
    for code, name, unit in codes_names_units:
        db.add(Product(code=code, name=name, unit=unit, item_group="Chai"))
    db.commit()


def read_report_sheet(ws):
    """Đọc một sheet xuất theo khuôn bản mẫu HTML (dòng 1–3 là tiêu đề báo cáo): trả `(tên cột, các dòng ô)`.

    Hàng tiêu đề cột = hàng ngay trên ô cố định. Tên cột bỏ xuống dòng thành dấu cách; sheet có hàng nhóm (Giá mua gần
    nhất) thì tên cột = "<nhóm> - <cột>". Dòng trả về là bộ Ô (không phải giá trị) để bài kiểm soi được cả kiểu ô.
    """
    from openpyxl.utils.cell import coordinate_from_string
    head_row = coordinate_from_string(ws.freeze_panes)[1] - 1
    labels = [str(c.value or "").replace("\n", " ") for c in ws[head_row]]
    if head_row > 4:
        group, groups = "", []
        for c in ws[head_row - 1]:
            group = c.value or group          # ô gộp: chỉ ô đầu mang chữ
            groups.append(group)
        labels = [f"{g} - {label}" for g, label in zip(groups, labels)]
    return labels, list(ws.iter_rows(min_row=head_row + 1))


def column_values(ws, label: str) -> list:
    """Giá trị của một cột (theo tên cột của `read_report_sheet`) từ trên xuống."""
    head, rows = read_report_sheet(ws)
    i = head.index(label)
    return [r[i].value for r in rows]
