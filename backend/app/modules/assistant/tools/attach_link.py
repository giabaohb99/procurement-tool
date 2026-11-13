"""Link sâu mở THẲNG hộp đính tệp của một chứng từ trên web (ai-CR-240) — dùng chung cho mọi tool ghi phiếu qua AI.

Tệp (hóa đơn, phiếu giao, báo giá…) không gửi được qua ứng dụng AI, nên kết quả tool trả link mở đúng chỗ đính tệp:
màn web đọc `?attach=1` và tự mở hộp tải tệp (ĐMH: hộp đính tệp của đúng lần giao; Đề nghị thanh toán / Phiếu khảo sát:
hộp Upload chứng từ; YCBG: hộp chi tiết dòng có ô đính tệp).

Link CHỈ mở giao diện: người dùng vẫn phải đăng nhập web, quyền kiểm như cũ (không có quyền thì màn báo như bình thường).
KHÔNG có đường tải lên ẩn danh hay token tải lên công khai (chưa duyệt — rủi ro bảo mật).

Trả đường TƯƠNG ĐỐI; cổng MCP nối gốc ERP bằng `agent_hub.mcp._absolutize` (khóa `url` / `link` / `*_url`).
"""
from __future__ import annotations

from urllib.parse import urlencode

ATTACH_PARAM = "attach"
DOC_PATHS = {
    "purchase_order": "/procurement/purchase-orders/{id}",
    "payment_request": "/finance/payment-requests/{id}",
    "survey": "/procurement/surveys/{id}",                 # Phiếu khảo sát
    "survey_request": "/procurement/survey-requests/{id}",  # Yêu cầu báo giá (YCBG)
}
#  Tham số chọn đúng chỗ trong màn (theo thứ tự in ra): ĐMH `delivery` = id lần giao, `line` = id dòng hàng,
#  `delivery_no` = số thứ tự lần giao của dòng (lần giao vừa thêm, lúc soạn nháp chưa có id); YCBG `line` = id dòng.
FOCUS_KEYS = ("delivery", "line", "delivery_no")


def _positive(v) -> int:
    try:
        n = int(v or 0)
    except (TypeError, ValueError):
        return 0
    return n if n > 0 else 0


def build_attach_url(doc_kind: str, doc_id, *, open_upload: bool = True, **focus) -> str:
    """Đường tương đối tới màn chi tiết `doc_kind` (khóa của `DOC_PATHS`), kèm tham số chọn chỗ (`FOCUS_KEYS`, số > 0)
    và `attach=1` để mở thẳng hộp đính tệp. Loại lạ / id sai → "" (không bịa link).

    `open_upload=False`: chỉ mở đúng chỗ, không bật hộp tải (chỗ đính chưa tồn tại — ví dụ lần giao chưa ghi)."""
    path, oid = DOC_PATHS.get(doc_kind or ""), _positive(doc_id)
    if not path or not oid:
        return ""
    unknown = set(focus) - set(FOCUS_KEYS)
    if unknown:
        raise ValueError(f"Tham số link lạ: {sorted(unknown)}")
    query = [(k, _positive(focus.get(k))) for k in FOCUS_KEYS if _positive(focus.get(k))]
    if open_upload:
        query.append((ATTACH_PARAM, 1))
    return path.format(id=oid) + (f"?{urlencode(query)}" if query else "")
