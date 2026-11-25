"""Bộ mã của màn Tác động giá bao bì (duoc-CR-784) — nguồn dòng sổ giá, vai trò thành phần, xu hướng, cảnh báo.

Thuần stdlib: `code_sets.py` phải nạp được khi chạy `scripts/gen_status_ts.py`. Số đã cấp KHÔNG ĐỔI, KHÔNG TÁI DÙNG
(luật R2, QĐ-11). Số 3 của `PriceSourceType` = sổ chi tiết mua hàng MISA (nạp tạm bằng `scripts/import_misa_price_ledger.py`).

Từ migration `srcmerge784` (25/11/2026) nguồn 1 (lịch sử mua) và nguồn 2 (dòng ĐMH) là CÙNG một lần mua của hệ thống: dòng ĐMH là MỘT
dòng sổ theo `po_item_id` suốt đời, cột `line_stage` (`LedgerLineStage`) cho biết còn đang mở hay đã chốt; nguồn 1 chỉ còn dữ liệu cũ
nạp từ Excel. Chữ người dùng thấy ("Nguồn" của Lịch sử mua hàng) vì thế tính từ cặp (nguồn, giai đoạn) — `price_source_text`.
"""
from enum import IntEnum

from app.core.status_catalog import Code, CodeSet, register


class PriceSourceType(IntEnum):
    """Dòng sổ giá lấy từ đâu — cột `tab_product_price_ledger.source_type` (SMALLINT)."""

    PURCHASE_HISTORY = 1   # lịch sử mua hàng CŨ nạp từ Excel (`po_item_id` trống) — chỉ chèn; `source_id` = tab_purchase_history.id
    PO_LINE = 2            # dòng đơn mua hàng ERP, đang mở lẫn đã hoàn thành (theo `line_stage`); `source_id` = tab_po_item.id
    MISA = 3               # sổ chi tiết mua hàng MISA (nạp tạm, tới mốc `misa_price_cutoff`) — chỉ chèn, gỡ được bằng --purge


class LedgerLineStage(IntEnum):
    """Giai đoạn của dòng sổ giá — cột `tab_product_price_ledger.line_stage` (SMALLINT)."""

    OPEN = 1    # dòng ĐMH đã duyệt, chưa hoàn thành: giá còn có thể đổi, `sync_po_price_ledger` cập nhật theo ĐMH
    FINAL = 2   # đã chốt (lịch sử mua đã chụp, dữ liệu cũ, sổ Misa): đồng bộ không đụng nữa


class PackagingRole(IntEnum):
    """Vai trò của một mã trong định mức bao bì của một mã hàng hóa."""

    BOTTLE = 1
    CAP = 2
    LABEL = 3
    CARTON_LABEL = 4
    CARTON = 5


class CostTrend(IntEnum):
    """Xu hướng chi phí bao bì của một mã hàng hóa so với giá cũ."""

    UP = 1
    DOWN = 2
    SAME = 3
    NO_PRICE = 4


class CostWarning(IntEnum):
    """Cảnh báo kèm một dòng chi phí hoặc một mã vật tư."""

    MISSING_BOTTLE_PRICE = 1      # thiếu giá chai — không tính được chi phí
    MISSING_COMPONENT_CODE = 2    # nắp / nhãn chưa khai mã trong định mức
    MISSING_COMPONENT_PRICE = 3   # có mã thành phần nhưng chưa có giá
    MISSING_CARTON_QTY = 4        # có nhãn thùng / thùng mà quy cách thùng bằng 0
    UNIT_MISMATCH = 5             # ĐVT lúc mua khác ĐVT danh mục
    BELOW_FLOOR = 6               # giá đang dùng thấp hơn ngưỡng sàn
    ABOVE_CEILING = 7             # giá đang dùng vượt ngưỡng trần


PRICE_SOURCE_TYPE_LABELS = {
    PriceSourceType.PURCHASE_HISTORY: "Lịch sử mua hàng cũ (nạp Excel)",
    PriceSourceType.PO_LINE: "Đơn mua hàng ERP",
    PriceSourceType.MISA: "Sổ Misa",
}
LEDGER_LINE_STAGE_LABELS = {LedgerLineStage.OPEN: "Đang mở", LedgerLineStage.FINAL: "Đã chốt"}
PACKAGING_ROLE_LABELS = {
    PackagingRole.BOTTLE: "Chai", PackagingRole.CAP: "Nắp", PackagingRole.LABEL: "Nhãn",
    PackagingRole.CARTON_LABEL: "Nhãn thùng", PackagingRole.CARTON: "Thùng",
}
COST_TREND_LABELS = {
    CostTrend.UP: "Tăng", CostTrend.DOWN: "Giảm", CostTrend.SAME: "Không đổi", CostTrend.NO_PRICE: "Chưa có giá",
}
COST_WARNING_LABELS = {
    CostWarning.MISSING_BOTTLE_PRICE: "Thiếu giá chai",
    CostWarning.MISSING_COMPONENT_CODE: "Chưa khai mã thành phần",
    CostWarning.MISSING_COMPONENT_PRICE: "Thiếu giá thành phần",
    CostWarning.MISSING_CARTON_QTY: "Thiếu quy cách thùng",
    CostWarning.UNIT_MISMATCH: "ĐVT mua khác ĐVT danh mục",
    CostWarning.BELOW_FLOOR: "Dưới ngưỡng sàn",
    CostWarning.ABOVE_CEILING: "Vượt ngưỡng trần",
}


def _set(name: str, title: str, labels: dict) -> CodeSet:
    return register(CodeSet(name, title, [Code(str(int(k)), v, sort_order=int(k), key=k.name) for k, v in labels.items()]))


PRICE_SOURCE_TYPE_SET = _set("price_source_type", "Nguồn dòng sổ giá", PRICE_SOURCE_TYPE_LABELS)
LEDGER_LINE_STAGE_SET = _set("ledger_line_stage", "Giai đoạn dòng sổ giá", LEDGER_LINE_STAGE_LABELS)
PACKAGING_ROLE_SET = _set("packaging_role", "Vai trò thành phần bao bì", PACKAGING_ROLE_LABELS)
COST_TREND_SET = _set("packaging_cost_trend", "Xu hướng chi phí bao bì", COST_TREND_LABELS)
COST_WARNING_SET = _set("packaging_cost_warning", "Cảnh báo chi phí bao bì", COST_WARNING_LABELS)


#  Chữ cột "Nguồn" của Lịch sử mua hàng (màn hình, Excel, in): không đổi so với trước khi gộp nguồn — ĐMH đang mở = "Dòng đơn mua hàng",
#  lần mua đã chốt của ERP và dữ liệu cũ = "Lịch sử mua hàng", Misa = "Sổ Misa".
SOURCE_TEXT_OPEN_PO = "Dòng đơn mua hàng"
SOURCE_TEXT_HISTORY = "Lịch sử mua hàng"


def is_open_po_line(source_type: int, line_stage: int) -> bool:
    """Dòng sổ là dòng ĐMH còn mở (giao diện hiện nhãn "ĐMH đang mở")."""
    return int(source_type) == PriceSourceType.PO_LINE and int(line_stage) == LedgerLineStage.OPEN


def price_source_text(source_type: int, line_stage: int) -> str:
    """Nhãn "Nguồn" hiện cho người dùng, tính từ cặp (nguồn, giai đoạn)."""
    if int(source_type) == PriceSourceType.MISA:
        return PRICE_SOURCE_TYPE_LABELS[PriceSourceType.MISA]
    return SOURCE_TEXT_OPEN_PO if is_open_po_line(source_type, line_stage) else SOURCE_TEXT_HISTORY
