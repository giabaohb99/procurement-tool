# Loại chứng từ (CỐ ĐỊNH trong code). value = lưu DB, label = hiển thị.
# Dùng cho đính kèm theo loại ở Đơn mua hàng và toàn chuỗi chứng từ.
DOCUMENT_TYPES = [
    {"value": "quotation", "label": "Báo giá"},
    {"value": "contract", "label": "Hợp đồng / Phụ lục"},
    {"value": "signed_po", "label": "Đơn đặt hàng (PO ký)"},
    {"value": "vat_invoice", "label": "Hóa đơn GTGT"},
    {"value": "delivery_note", "label": "Biên bản giao nhận / Phiếu giao hàng"},
    {"value": "acceptance_report", "label": "Biên bản nghiệm thu"},
    {"value": "goods_receipt", "label": "Phiếu nhập kho"},
    {"value": "payment_document", "label": "Chứng từ thanh toán"},
    {"value": "co_cq", "label": "CO / CQ"},
    {"value": "other", "label": "Khác"},
]

DOC_TYPE_VALUES = {t["value"] for t in DOCUMENT_TYPES}
DOC_TYPE_LABEL = {t["value"]: t["label"] for t in DOCUMENT_TYPES}
