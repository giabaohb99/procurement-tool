"""Bộ mã và danh sách cột của phân hệ Tra cứu giá hải quan (bao-CR-470).

Thiết kế: `doc/erp/hai-quan/02-thiet-ke-ky-thuat.md`.
"""
from enum import IntEnum


class PartyType(IntEnum):
    """Phân loại đối tượng theo BẢN CHẤT, không theo VAI TRÒ (02 §3.2).

    Vai trò (ai nhập, ai bán) đã nằm ở cột nào của dòng hàng trỏ tới
    (`importer_id` / `partner_id`). Phân loại theo vai trò sẽ vỡ khi có dữ liệu
    xuất khẩu: một công ty Việt Nam lúc là người nhập, lúc là người xuất.
    """
    DOMESTIC = 1   # doanh nghiệp Việt Nam — chống trùng theo MÃ SỐ THUẾ
    FOREIGN = 2    # đối tác nước ngoài — không có mã, chống trùng theo tên đã chuẩn hóa


PARTY_TYPE_LABELS = {
    PartyType.DOMESTIC: "Doanh nghiệp trong nước",
    PartyType.FOREIGN: "Đối tác nước ngoài",
}


class TransportMode(IntEnum):
    """Phương tiện vận chuyển — lấy ĐÚNG mã số VNACCS đứng đầu chuỗi gốc
    (`2-Đường biển (container)`), không tự đánh số mới (luật R2)."""
    AIR = 1
    SEA_CONTAINER = 2
    SEA_BULK = 3
    ROAD = 4
    OTHER = 9


TRANSPORT_LABELS = {
    TransportMode.AIR: "Đường không",
    TransportMode.SEA_CONTAINER: "Đường biển (container)",
    TransportMode.SEA_BULK: "Đường biển (hàng rời, lỏng...)",
    TransportMode.ROAD: "Đường bộ (xe tải)",
    TransportMode.OTHER: "Khác",
}

class RegulationList(IntEnum):
    """Danh sách pháp lý mà một dòng `tab_customs_regulation` thuộc về (HQ6).

    Ý nghĩa pháp lý của từng phụ lục lấy theo phần mềm nguồn (HaiQuan Manager); người
    phụ trách pháp chế nên xác nhận lại trước khi dùng làm căn cứ chính thức.
    """
    ND24_PL1 = 1          # NĐ 24/2026/NĐ-CP — Phụ lục I
    ND24_PL2 = 2          # NĐ 24/2026/NĐ-CP — Phụ lục II
    ND24_PL3 = 3          # NĐ 24/2026/NĐ-CP — Phụ lục III (tiền chất)
    ND24_PL4 = 4          # NĐ 24/2026/NĐ-CP — Phụ lục IV (có NGƯỠNG KHỐI LƯỢNG kg)
    BANNED_TT75 = 10      # TT 75/2025/TT-BNNMT — hoạt chất BVTV CẤM
    PUBLISH_TT01 = 11     # TT 01/2026/TT-BCT Phụ lục XIX — hóa chất phải CÔNG BỐ theo lô


REGULATION_LIST_LABELS = {
    RegulationList.ND24_PL1: "NĐ 24/2026 · Phụ lục I",
    RegulationList.ND24_PL2: "NĐ 24/2026 · Phụ lục II",
    RegulationList.ND24_PL3: "NĐ 24/2026 · Phụ lục III (tiền chất)",
    RegulationList.ND24_PL4: "NĐ 24/2026 · Phụ lục IV (ngưỡng khối lượng)",
    RegulationList.BANNED_TT75: "TT 75/2025 · Hoạt chất cấm",
    RegulationList.PUBLISH_TT01: "TT 01/2026 · Phải công bố theo lô",
}

#  Công thức hóa học → số CAS, để tra nghĩa vụ bằng công thức (`H2SO4`, `Cl2`).
#  Hằng số hóa học chuẩn, lấy theo phần mềm nguồn.
FORMULA_CAS = {
    "H2SO4": "7664-93-9", "HCL": "7647-01-0", "HNO3": "7697-37-2", "H3PO4": "7664-38-2",
    "NH3": "7664-41-7", "CL2": "7782-50-5", "BR2": "7726-95-6", "HF": "7664-39-3",
    "H2S": "7783-06-4", "SO2": "7446-09-5", "NO2": "10102-44-0", "CO": "630-08-0",
    "HCN": "74-90-8", "CH2O": "50-00-0", "CH3OH": "67-56-1", "C2H4O": "75-21-8",
    "COCL2": "75-44-5", "NACN": "143-33-9", "KCN": "151-50-8", "C3H6O": "67-64-1",
    "C7H8": "108-88-3", "C6H6": "71-43-2", "NAOH": "1310-73-2", "KOH": "1310-58-3",
}

#  Kỳ ít dòng hơn ngưỡng này KHÔNG được gắn nhãn "kỳ giá tốt nhất" (04 §4): ATRAZINE
#  tháng 8 "rẻ nhất" chỉ dựa trên 3 dòng, tháng 5 gần ngang giá dựa trên 16 dòng.
MIN_LINES_FOR_BEST = 5

#  MỘT danh sách 32 cột, đúng thứ tự và đúng tiêu đề của tệp GTT02 — vừa là chỗ
#  khớp tiêu đề lúc nạp, vừa là nguồn dựng cột trên màn hình (02 §7). Tiêu đề giữ
#  NGUYÊN VĂN kể cả lỗi chính tả của nguồn («nuớc»); khớp thì so theo chữ đã
#  chuẩn hóa (thường, bỏ dấu), nên nguồn có sửa chính tả cũng không hỏng.
COLUMNS: list[tuple[str, str]] = [
    ("reg_date", "Ngày đăng ký"),
    ("office_code", "Tên nơi mở tờ khai"),
    ("importer_tax_code", "Mã doanh nghiệp XNK"),
    ("importer_name", "Tên doanh nghiệp XNK"),
    ("partner_name", "Đơn vị đối tác"),
    ("hs_code", "Mã hàng khai báo"),
    ("line_no", "Số thứ tự hàng"),
    ("product_name", "Tên hàng"),
    ("price_usd", "Đơn giá khai báo(USD)"),
    ("price_nt", "Đơn giá NT khai báo"),
    ("adj_price_usd", "Đơn giá điều chỉnh(USD)"),
    ("adj_price_nt", "Đơn giá NT điều chỉnh"),
    ("currency", "Nguyên tệ"),
    ("fx_rate", "Tỷ giá nguyên tệ"),
    ("usd_rate", "Tỷ giá USD"),
    ("quantity", "Lượng"),
    ("unit_code", "Đơn vị tính"),
    ("origin_country", "Tên nuớc xuất xứ"),
    ("contract_no", "Số hợp đồng"),
    ("contract_date", "Ngày hợp đồng"),
    ("incoterm", "Điều kiện giao hàng"),
    ("transport_mode", "Phương tiện vận chuyển"),
    ("rate_import", "Thuế suất XNK"),
    ("rate_excise", "Thuế suất TTĐB"),
    ("rate_vat", "Thuế suất VAT"),
    ("rate_safeguard", "Thuế suất tự vệ"),
    ("tax_import", "Thuế XNK"),
    ("tax_excise", "Thuế TTĐB"),
    ("tax_vat", "Thuế VAT"),
    ("tax_environment", "Thuế môi trường"),
    ("tax_safeguard", "Thuế tự vệ"),
    ("import_country", "Nước nhập khẩu"),
]

#  Cột số tiền / đơn giá / tỷ giá / thuế — đọc thành số, ô trống ra NULL (không ra 0).
DECIMAL_KEYS = frozenset({
    "price_usd", "price_nt", "adj_price_usd", "adj_price_nt", "fx_rate", "usd_rate",
    "quantity", "rate_import", "rate_excise", "rate_vat", "rate_safeguard",
    "tax_import", "tax_excise", "tax_vat", "tax_environment", "tax_safeguard",
})

#  Trần độ dài khớp ĐÚNG `String(n)` ở `model.py` — chuỗi dài hơn thì cắt kèm cảnh
#  báo, không để MySQL ném 500 giữa lượt nạp (bài học duoc-CR-316).
TEXT_LIMITS = {
    "office_code": 10, "importer_tax_code": 14, "importer_name": 255, "partner_name": 255,
    "hs_code": 8, "product_name": 255, "currency": 3, "unit_code": 4, "origin_country": 2,
    "contract_no": 40, "incoterm": 3, "import_country": 2,
}

#  Chèn dòng hàng theo khối — một lần kết xuất hàng chục nghìn dòng.
INSERT_CHUNK = 2000
