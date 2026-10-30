"""Ba bộ dữ liệu đầu tiên (đại ca chốt 17/10/2026, doc/erp/21 §5.5): mua hàng, công nợ phải trả, yêu cầu thanh toán.

Thêm bộ mới = thêm một `Dataset(...)` ở đây (hoặc tệp riêng rồi đăng ký ở `__init__.REGISTRY`) — không viết tool mới.
Mỗi bộ phải nói rõ: gác bằng entity nào, phạm vi đi qua `apply_scope` của entity nào (hoặc vì sao không có), tiền trước /
sau VAT ở chỗ đã soi công thức.
"""
from __future__ import annotations

from sqlalchemy import case, func, or_

from app.core.report_keys import ReportKey
from app.core.status_codes import PAYABLE_STATUS
from app.core.vn_time import vn_today

from .base import Dataset, Dimension, Filter, Measure
from .lookups import company_names, department_names


def _like(*cols):
    def apply(q, value):
        pattern = f"%{value}%"
        return q.filter(or_(*(c.like(pattern) for c in cols)))
    return apply


def _eq(col):
    return lambda q, value: q.filter(col == value)


def _gte(col):
    return lambda q, value: q.filter(col >= value)


def _lte(col):
    return lambda q, value: q.filter(col <= value)


def _month(col):
    return lambda: func.substr(col, 1, 7)


# ── Mua hàng — tab_purchase_history ───────────────────────────────────────────────────────────────────────────────
#  Bảng LỊCH SỬ GIÁ, không nằm trong ENTITIES nên không có khóa phạm vi: cổng là `product.read` (+ `supplier.read` khi
#  chia theo NCC) — đúng như màn "Lịch sử mua hàng" và `analytics_query` cũ (test E2 ghi rõ). Trùng số liệu Báo cáo mua
#  hàng nên đòi thêm quyền xem báo cáo đó (ai-CR-207).
def _purchase() -> Dataset:
    from app.modules.purchase_history.model import PurchaseHistory as PH

    def spend():
        #  Thành tiền một dòng: ưu tiên `amount` (đã gồm VAT); dữ liệu cũ để 0 thì lùi về qty × price (y hệt catalog cũ).
        return func.coalesce(func.nullif(PH.amount, 0), PH.qty_order * PH.price)

    return Dataset(
        key="purchase", label="Mua hàng (lịch sử mua)", model=PH, entity="product", scope_entity=None,
        report_key=ReportKey.PURCHASE_REPORT, link="/report/purchase",
        description="Từng dòng hàng đã mua (theo ngày đặt): chi tiêu, số dòng, số lượng, đơn giá theo NCC / mã hàng / "
                    "tháng / pháp nhân.",
        measures=(
            Measure("total_amount", "Tổng chi tiêu", lambda: func.sum(spend()), "money", vat="sau VAT"),
            Measure("count", "Số dòng mua", lambda: func.count(PH.id), "int"),
            Measure("qty", "Tổng số lượng đặt", lambda: func.sum(PH.qty_order), "qty"),
            Measure("avg_price", "Đơn giá trung bình", lambda: func.avg(PH.price), "price", vat="trước VAT"),
            Measure("product_count", "Số mã hàng", lambda: func.count(func.distinct(PH.product_code)), "int"),
        ),
        dimensions=(
            Dimension("supplier", "Nhà cung cấp", lambda: PH.supplier_code, name=lambda: PH.supplier_name,
                      needs=("supplier",)),
            Dimension("product", "Mã hàng", lambda: PH.product_code, name=lambda: PH.product_name),
            Dimension("month", "Tháng", _month(PH.order_date)),
            Dimension("company", "Pháp nhân", lambda: PH.company_id, name=lambda: PH.company_name),
        ),
        filters=(
            Filter("date_from", "Từ ngày đặt", _gte(PH.order_date), "date"),
            Filter("date_to", "Đến ngày đặt", _lte(PH.order_date), "date"),
            Filter("supplier_code", "Mã NCC", _eq(PH.supplier_code)),
            Filter("product_code", "Mã hàng", _eq(PH.product_code)),
            Filter("company_id", "Pháp nhân (id)", _eq(PH.company_id), "int"),
        ),
        notes=("Tổng chi tiêu = thành tiền dòng đã gồm VAT; đơn giá trung bình là giá trước VAT, trung bình theo dòng "
               "(không trọng số theo số lượng).",),
    )


# ── Công nợ phải trả — tab_payable ────────────────────────────────────────────────────────────────────────────────
#  apply_scope(Payable, "payable") — cùng phạm vi màn Công nợ và tool payable_lookup (pháp nhân / phòng xử lý / người lập).
PAYABLE_SOURCE_LABELS = {"goods": "Hàng hóa", "shipping": "Vận chuyển", "import_cost": "Chi phí thu mua"}


def _payable() -> Dataset:
    from app.modules.payable.model import Payable as P

    def overdue():
        today = vn_today().isoformat()
        return func.coalesce(func.sum(case(
            (((P.status != "paid") & (P.due_date != "") & (P.due_date < today)), P.remaining), else_=0)), 0)

    def overdue_filter(q, flag: bool):
        today = vn_today().isoformat()
        cond = (P.status != "paid") & (P.due_date != "") & (P.due_date < today)
        return q.filter(cond) if flag else q.filter(~cond)

    return Dataset(
        key="payable", label="Công nợ phải trả", model=P, entity="payable", scope_entity="payable",
        link="/finance/payables",
        description="Khoản nợ nhà cung cấp / đơn vị vận chuyển theo ngày phát sinh: phải trả, đã trả, còn nợ, quá hạn theo "
                    "NCC / pháp nhân / phòng / trạng thái / tháng / tháng đến hạn.",
        measures=(
            Measure("remaining", "Còn nợ", lambda: func.coalesce(func.sum(P.remaining), 0), "money", vat="sau VAT"),
            Measure("total", "Phải trả", lambda: func.coalesce(func.sum(P.total), 0), "money", vat="sau VAT"),
            Measure("amount", "Tiền hàng trước VAT", lambda: func.coalesce(func.sum(P.amount), 0), "money", vat="trước VAT"),
            Measure("vat", "Tiền VAT", lambda: func.coalesce(func.sum(P.vat), 0), "money"),
            Measure("paid_amount", "Đã trả", lambda: func.coalesce(func.sum(P.paid_amount), 0), "money", vat="sau VAT"),
            Measure("overdue", "Nợ quá hạn", overdue, "money", vat="sau VAT"),
            Measure("count", "Số khoản nợ", lambda: func.count(P.id), "int"),
        ),
        dimensions=(
            Dimension("supplier", "Nhà cung cấp", lambda: P.supplier_code, name=lambda: P.supplier_name),
            Dimension("company", "Pháp nhân", lambda: P.company_id, lookup=company_names),
            Dimension("department", "Phòng xử lý", lambda: P.department_id, lookup=department_names),
            Dimension("status", "Trạng thái", lambda: P.status, labels=PAYABLE_STATUS.labels),
            Dimension("source_type", "Loại nợ", lambda: P.source_type, labels=PAYABLE_SOURCE_LABELS),
            Dimension("month", "Tháng phát sinh", _month(P.incur_date)),
            Dimension("due_month", "Tháng đến hạn", _month(P.due_date)),
        ),
        filters=(
            Filter("date_from", "Phát sinh từ ngày", _gte(P.incur_date), "date"),
            Filter("date_to", "Phát sinh đến ngày", _lte(P.incur_date), "date"),
            Filter("due_from", "Hạn trả từ ngày", lambda q, v: q.filter(P.due_date != "", P.due_date >= v), "date"),
            Filter("due_to", "Hạn trả đến ngày", lambda q, v: q.filter(P.due_date != "", P.due_date <= v), "date"),
            Filter("status", "Trạng thái", _eq(P.status), "enum", enum=tuple(c.value for c in PAYABLE_STATUS.codes)),
            Filter("outstanding", "Chỉ khoản chưa trả xong", lambda q, v: q.filter(P.status != "paid") if v else q, "bool"),
            Filter("overdue", "Chỉ khoản quá hạn (false = chưa quá hạn)", overdue_filter, "bool"),
            Filter("supplier", "NCC (mã hoặc tên, khớp một phần)", _like(P.supplier_code, P.supplier_name)),
            Filter("company_id", "Pháp nhân (id)", _eq(P.company_id), "int"),
            Filter("source_type", "Loại nợ", _eq(P.source_type), "enum", enum=tuple(PAYABLE_SOURCE_LABELS)),
        ),
        notes=("Phải trả = tiền hàng + VAT; còn nợ = phải trả − đã trả; quá hạn = còn nợ của khoản chưa trả xong có hạn trả "
               "trước hôm nay (giờ Việt Nam).",),
    )


# ── Yêu cầu thanh toán — tab_payment_request ──────────────────────────────────────────────────────────────────────
#  apply_scope(PaymentRequest, "payment_request") — mixin xóa mềm nên phiếu đã xóa tự bị loại.
def _payment_request() -> Dataset:
    from app.modules.payment_request.model import PaymentRequest as R
    from app.modules.payment_request.service import STATUS_LABELS

    return Dataset(
        key="payment_request", label="Yêu cầu thanh toán", model=R, entity="payment_request",
        scope_entity="payment_request", link="/finance/payment-requests",
        description="Phiếu đề nghị chi trả NCC theo ngày đề nghị: số phiếu, số tiền đề nghị theo NCC / pháp nhân / phòng / "
                    "trạng thái / tháng / hình thức.",
        measures=(
            Measure("total", "Số tiền đề nghị", lambda: func.coalesce(func.sum(R.total), 0), "money"),
            Measure("count", "Số phiếu", lambda: func.count(R.id), "int"),
        ),
        dimensions=(
            Dimension("supplier", "Nhà cung cấp", lambda: R.supplier_code, name=lambda: R.supplier_name),
            Dimension("company", "Pháp nhân", lambda: R.company_id, lookup=company_names),
            Dimension("department", "Phòng", lambda: R.department_id, lookup=department_names),
            Dimension("status", "Trạng thái", lambda: R.status, labels=STATUS_LABELS),
            Dimension("month", "Tháng đề nghị", _month(R.request_date)),
            Dimension("payment_method", "Hình thức", lambda: R.payment_method,
                      labels={"transfer": "Chuyển khoản", "cash": "Tiền mặt"}),
            Dimension("prepay", "Loại phiếu", lambda: R.prepay, labels={0: "Thanh toán công nợ", 1: "Trả trước"}),
        ),
        filters=(
            Filter("date_from", "Đề nghị từ ngày", _gte(R.request_date), "date"),
            Filter("date_to", "Đề nghị đến ngày", _lte(R.request_date), "date"),
            Filter("status", "Trạng thái", _eq(R.status), "enum", enum=tuple(STATUS_LABELS)),
            Filter("supplier", "NCC (mã hoặc tên, khớp một phần)", _like(R.supplier_code, R.supplier_name)),
            Filter("company_id", "Pháp nhân (id)", _eq(R.company_id), "int"),
            Filter("prepay", "Chỉ phiếu trả trước", lambda q, v: q.filter(R.prepay == (1 if v else 0)), "bool"),
        ),
        notes=("Số tiền đề nghị = tổng số tiền các dòng hóa đơn / công nợ trên phiếu (cùng số in trên phiếu).",),
    )


def build_registry() -> dict[str, Dataset]:
    return {ds.key: ds for ds in (_purchase(), _payable(), _payment_request())}
