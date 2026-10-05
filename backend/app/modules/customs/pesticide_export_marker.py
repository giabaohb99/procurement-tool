"""Sheet ẨN `_xuat` — cho bộ đọc biết tệp xuất THEO PHẠM VI nào, để chọn chế độ nạp lại
(C1, review 02/10/2026 của tính năng Xuất Excel Thuốc BVTV):

  · `scope=all`  → nạp lại THAY TOÀN BỘ như trước giờ — tệp đủ cả danh mục, xóa phần
    không có trong tệp là đúng ý (`pesticide_service.replace_catalog`).
  · `scope=page` → nạp lại chỉ CẬP NHẬT đúng những thuốc có trong tệp, KHÔNG xóa gì khác
    (`pesticide_merge_service.merge_catalog`) — một trang không đại diện cho cả danh mục,
    nạp như thay toàn bộ sẽ xóa sạch phần còn lại.
  · KHÔNG có sheet này (bản cào gốc danhmuc.thuocbvtv.com không biết khái niệm này, hoặc
    tệp cũ xuất trước khi có C1) → THAY TOÀN BỘ, giữ đúng hành vi gốc — an toàn hơn vì
    THAY TOÀN BỘ là điều mọi tệp .xlsx đã nạp được từ trước tới giờ.

Dùng CHUNG module cho cả phía ghi (`pesticide_export_service`) và phía đọc
(`pesticide_reader`) — một nơi khai tên sheet + cột, tránh hai nơi chép lại cùng chuỗi.
"""
from app.core.export_xlsx import VN_OFFSET
from datetime import datetime

MARKER_SHEET = "_xuat"
_HEADER = ["scope", "page", "exported_at"]


def write_marker(wb, scope: str, page: int | None) -> None:
    """Ghi sheet ẩn — gọi SAU KHI đã có ít nhất một sheet khác trong `wb`: workbook
    `write_only` không cho ẩn sheet DUY NHẤT của tệp (openpyxl ValueError)."""
    ws = wb.create_sheet(MARKER_SHEET)
    ws.sheet_state = "hidden"
    ws.append(_HEADER)
    ws.append([scope, page if scope == "page" else "",
              (datetime.utcnow() + VN_OFFSET).isoformat(timespec="seconds")])


def detect_mode(wb) -> str:
    """`_xuat` + scope=page → `"merge"`; scope=all HOẶC thiếu sheet (bản cào gốc / tệp cũ
    trước C1) → `"replace"`."""
    if MARKER_SHEET not in wb.sheetnames:
        return "replace"
    rows = list(wb[MARKER_SHEET].iter_rows(values_only=True))
    if len(rows) < 2:
        return "replace"
    header = [str(h or "").strip() for h in rows[0]]
    row = dict(zip(header, rows[1]))
    return "merge" if str(row.get("scope") or "").strip() == "page" else "replace"
