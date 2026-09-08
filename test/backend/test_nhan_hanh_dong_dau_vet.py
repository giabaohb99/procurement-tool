"""NHÃN HÀNH ĐỘNG CỦA DẤU VẾT phải phủ CẢ HAI dạng chữ.

⚠️ LỖI ĐÃ XẢY RA (04/09/2026, phiếu đặt phòng PH004): dòng dấu vết hiện
*«Dego Admin — approve: Duyệt phiếu đặt phòng PH004»* — mã tiếng Anh trần nằm
giữa một câu tiếng Việt.

Gốc: bảng nhãn chỉ khai dạng QUÁ KHỨ (`approved`, `cancelled`) vì phân hệ Văn
thư ghi như vậy, còn bảng quyền của hệ lại dùng dạng NGUYÊN THỂ (`approve`,
`cancel` — xem `core/permissions.ACTIONS`), nên controller viết sau quen tay ghi
theo dạng đó. Cả Nghỉ phép lẫn Đặt phòng đều dính.
"""
from app.core.permissions import ACTIONS
from app.modules.audit.controller import ACTION_LABEL

#  Những hành động mà controller THẬT SỰ ghi vào dấu vết, gom từ cả hai lối
#  viết đang tồn tại trong mã nguồn.
USED_ACTIONS = [
    "create", "update", "delete",
    "submit", "submitted",
    "approve", "approved",
    "reject", "rejected",
    "return", "returned",
    "withdraw", "withdrawn",
    "cancel", "cancelled",
]


def test_moi_hanh_dong_dang_ghi_deu_co_nhan_tieng_viet():
    missing = [a for a in USED_ACTIONS if a not in ACTION_LABEL]
    assert missing == [], f"thiếu nhãn, dấu vết sẽ hiện mã trần: {missing}"


def test_hai_dang_cua_cung_mot_viec_noi_giong_nhau():
    """«approve» và «approved» là một việc — hai nhãn khác nhau thì cùng một
    hành động đọc ra hai kiểu trên cùng một dòng thời gian."""
    for nguyen_the, qua_khu in [("approve", "approved"), ("reject", "rejected"),
                                ("return", "returned"), ("withdraw", "withdrawn"),
                                ("cancel", "cancelled"), ("submit", "submitted")]:
        assert ACTION_LABEL[nguyen_the] == ACTION_LABEL[qua_khu], nguyen_the


def test_nhan_khong_bao_gio_la_chuoi_rong():
    """Nhãn rỗng còn tệ hơn mã trần: dòng dấu vết mất luôn phần «làm gì»."""
    assert all((label or "").strip() for label in ACTION_LABEL.values())


def test_moi_hanh_dong_trong_bang_quyen_deu_co_nhan():
    """`ACTIONS` là bộ hành động mà MỌI endpoint gác theo, nên bất kỳ cái nào
    cũng có thể rơi vào dấu vết. Thiếu nhãn là chờ tới lúc ai đó ghi mới lộ.

    Trừ `read`: đọc không ghi dấu vết (đo lại ngày 04/09/2026 — mở chi tiết một
    bản ghi KHÔNG sinh dòng nào).
    """
    missing = [a for a in ACTIONS if a != "read" and a not in ACTION_LABEL]
    assert missing == [], f"hành động gác được nhưng chưa có nhãn: {missing}"
