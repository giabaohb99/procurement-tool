"""Bộ mã KIỂU TRẢ VỀ của Yêu cầu mua hàng — cột `tab_purchase_request.return_mode` (duoc-CR-803).

Trả về thường (`purchase_request/lifecycle_service.return_pr`) không cần cột này: phiếu chưa có ĐMH nên
kéo mọi dòng về `no_po` là xong. Kiểu trả về MỚI cho phiếu Đang mua hàng thì GIỮ NGUYÊN các ĐMH, nên
phiếu nằm ở `rejected` / `submitted` mà phải nhớ là "chỉ được sửa Công ty nhận hóa đơn" và "các ĐMH
đang bị khóa" — đó là việc của cột này.

R2/QĐ-11: SMALLINT + IntEnum, API trả số kèm nhãn. Thuần stdlib để `scripts/gen_status_ts.py` nạp được.
Luật bất biến: số đã cấp giữ nguyên mãi mãi, không tái dùng.
"""
from enum import IntEnum

from app.core.status_catalog import Code, CodeSet, register


class PrReturnMode(IntEnum):
    """`0` = phiếu không ở đợt trả về đặc biệt nào (mặc định của mọi phiếu)."""

    NONE = 0
    INVOICE_COMPANY = 1   # trả về chỉ để sửa Công ty nhận hóa đơn, ĐMH liên quan bị khóa


PR_RETURN_MODE_LABELS: dict[PrReturnMode, str] = {
    PrReturnMode.INVOICE_COMPANY: "Trả về sửa công ty nhận hóa đơn",
}

PR_RETURN_MODE_SET = register(CodeSet("pr_return_mode", "Kiểu trả về yêu cầu mua hàng", [
    Code(str(int(k)), v, sort_order=int(k), key=k.name) for k, v in PR_RETURN_MODE_LABELS.items()
]))
