"""Cột + dòng của tệp Excel xuất danh mục Thuốc BVTV (02/10/2026).

Giữ ĐÚNG tên và THỨ TỰ 25 cột gốc của bản cào `danhmuc.thuocbvtv.com` (sheet «Danh sach thuoc»)
và 12 cột gốc (sheet «Pham vi su dung») — để người dùng mở file đối chiếu được với bản cào, và vì
cả hai là NGUYÊN VĂN cấu trúc mà `pesticide_reader` đọc. Cột gốc mà bộ đọc KHÔNG dùng tới (hệ
thống không giữ riêng trường đó) để TRỐNG: `hoat_chat_danh_sach`, `thoi_han_dang_ky`,
`nhom_khang_thuoc`, `pham_vi_su_dung` (ô tổng hợp của bản cào — không nhầm với TÊN SHEET),
`thong_tin_khac`, `cong_ty_url`, `nguon_ecofarm`.

Cột `RAW_RESISTANCE_COLUMN` (`quan_ly_tinh_khang_raw`) là cột THÊM của hệ thống (H2, review
02/10/2026), khai ở `pesticide_reader` (nơi đọc lại nó) — giữ NGUYÊN VĂN `resistance` để nạp lại
không phải tách-rồi-ghép qua `_resistance()` (mất chữ tự do có `;`/`:` bên trong một mục).
"""
from .constants import PESTICIDE_STATUS_LABELS
from .model import CustomsPesticide, CustomsPesticideUse
from .pesticide_reader import RAW_RESISTANCE_COLUMN

LIST_HEADER = [
    "id", "ten_thuoc", "phan_nhom", "linh_vuc", "tinh_trang", "hoat_chat", "ham_luong",
    "hoat_chat_danh_sach", "cong_ty_dang_ky", "so_dang_ky", "thoi_han_dang_ky", "ngay_cap",
    "ngay_het_han", "nhom_doc", "nhom_khang_thuoc", "quan_ly_tinh_khang", RAW_RESISTANCE_COLUMN,
    "so_pham_vi", "cay_trong", "dich_hai", "pham_vi_su_dung", "tom_tat_su_dung", "thong_tin_khac",
    "url", "cong_ty_url", "nguon_ecofarm",
]

USE_HEADER = [
    "id", "ten_thuoc", "so_dang_ky", "phan_nhom", "tinh_trang", "stt_pham_vi", "cay_trong",
    "dich_hai", "lieu_luong", "thoi_gian_cach_ly", "cach_dung", "khac",
]


def export_id(p: CustomsPesticide, dup_source_ids: frozenset = frozenset()) -> int:
    """Giá trị cột `id` lúc xuất — PHẢI khớp đúng cột bộ đọc dùng để NỐI hai sheet, và (cho thuốc
    từ nguồn, không trùng `source_id` với ai khác) khớp lại `source_id` lúc nạp
    (`pesticide_service.replace_catalog`/`pesticide_merge_service.merge_catalog` giữ nguyên id
    thuốc theo `source_id` để tệp đính kèm/nhật ký không mất chủ — duoc-CR-494).

    Trả id ÂM (`-p.id`, C2 review 02/10/2026) cho hai ca id xuất ra PHẢI không bao giờ đụng một
    `source_id` dương thật — bộ đọc coi MỌI id <= 0 là "bỏ qua lúc nạp" (`pesticide_reader`):

    1. Thuốc tự thêm (`is_manual`) — không có `source_id` thật (luôn 0 — `pesticide_edit_
       service`), và `id` hệ thống (dương) của nó có thể TRÙNG `source_id` dương của một thuốc
       khác (cả hai chỉ là số nguyên, không gian riêng) — dùng `source_id = p.id` như bản cũ sẽ
       đụng khóa nối hai sheet của CHÍNH thuốc nguồn đó.
    2. Thuốc NGUỒN mà `source_id` trùng với một thuốc nguồn khác (dữ liệu nhiễm — xem
       `pesticide_export_service._duplicate_source_ids`) — xuất cả hai với `source_id` thật sẽ
       tạo HAI dòng cùng `id` dương ở sheet thuốc, bị bộ đọc TỪ CHỐI (id trùng) hoặc (nếu không có
       kiểm đó) gộp nhầm phạm vi sử dụng của hai thuốc khác nhau. Xuất CẢ HAI (không riêng dòng
       "thứ hai") với id ÂM — KHÔNG chọn ai thắng, cố ý đơn giản: tệp vẫn nạp lại được, cặp trùng
       bị bỏ qua cả hai (admin tự xử lý trùng ở DB), phần CÒN LẠI của danh mục không bị chặn/hỏng.
    """
    if p.is_manual or p.source_id in dup_source_ids:
        return -p.id
    return p.source_id


def _dedupe_join(values: list[str]) -> str:
    """Danh sách cây trồng / dịch hại của một thuốc → chuỗi duy nhất, giữ ĐÚNG thứ tự xuất hiện
    đầu tiên (khớp cách bản cào gộp cột `cay_trong`/`dich_hai` ở sheet «Danh sach thuoc»)."""
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return "; ".join(out)


def list_row(p: CustomsPesticide, uses: list[CustomsPesticideUse],
            dup_source_ids: frozenset = frozenset()) -> list:
    """Một dòng sheet «Danh sach thuoc» — giá trị LẤY THẲNG từ cột đã lưu, không suy diễn lại."""
    pid = export_id(p, dup_source_ids)
    return [
        pid, p.trade_name, p.pest_group, p.sector,
        PESTICIDE_STATUS_LABELS.get(p.status, ""), p.active_ingredient, p.concentration,
        "", p.registrant, p.registration_no, "", p.registered_on, p.expires_on,
        p.toxicity, "", p.resistance, p.resistance, len(uses),
        _dedupe_join([u.crop for u in uses]), _dedupe_join([u.pest for u in uses]),
        "", p.summary, "", p.source_url, "", "",
    ]


def use_rows(p: CustomsPesticide, uses: list[CustomsPesticideUse],
            dup_source_ids: frozenset = frozenset()) -> list[list]:
    """Các dòng sheet «Pham vi su dung» của MỘT thuốc — `ten_thuoc`/`so_dang_ky`/`phan_nhom`/
    `tinh_trang` lặp lại (đúng cách bản cào ghi) để đối chiếu chéo được, không phải tra lại sheet
    thuốc."""
    pid = export_id(p, dup_source_ids)
    label = PESTICIDE_STATUS_LABELS.get(p.status, "")
    return [
        [pid, p.trade_name, p.registration_no, p.pest_group, label, u.sort_order,
         u.crop, u.pest, u.dosage, u.pre_harvest_interval, u.usage, ""]
        for u in uses
    ]
