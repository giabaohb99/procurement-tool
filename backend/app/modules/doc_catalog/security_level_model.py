"""MỨC MẬT và ĐỘ KHẨN — hai thang của phân hệ Văn thư, nay là danh mục sửa được.

Trước 22/08/2026 bảy dòng này khai cứng ở hai nơi (`security-level.ts` bên giao
diện và `SECRECY_LABELS` trong `document/export.py`), không có bảng nào cả. Tách
ra bảng để quản trị tự thêm sửa xóa.

────────────────────────────────────────────────────────────────────────────
QUYẾT ĐỊNH QUAN TRỌNG NHẤT: **`value` VỪA LÀ SỐ LƯU TRÊN VĂN BẢN, VỪA LÀ THỨ BẬC.**

`tab_document.secrecy_level` là một số trần (không phải khóa ngoại), và số đó
đang được so sánh trực tiếp ở nhiều nơi — `excerpt_service.ensure_secrecy_within_source`
chặn bản trích vượt gốc bằng đúng phép `>`. Quan trọng hơn: **điều kiện luồng
duyệt lưu con số ấy dạng chuỗi JSON trong DB** (`ApprovalFlow.condition`, ví dụ
`{"field":"secrecy_level","op":"gte","value":3}`).

Nên KHÔNG tách thêm cột `rank` riêng và KHÔNG đánh số lại. Đánh số lại là mọi
luồng duyệt đã cấu hình lặng lẽ thôi khớp — không lỗi, không cảnh báo, chỉ là
văn bản mật đi thẳng qua mà không ai phải ký. Thêm mức mới thì chính con số của
nó đặt nó vào thứ bậc: muốn nghiêm hơn Mật (3) mà nhẹ hơn Tuyệt mật (4) thì
không chen được — đó là cái giá đã biết, và nó rẻ hơn nhiều so với rủi ro trên.

Vì `value` chỉ duy nhất TRONG MỘT THANG (Công khai và Thường cùng `value = 1`),
khóa chính vẫn là `id` tự tăng, còn khóa nghiệp vụ là cặp `(kind, value)`.

**Không có khóa ngoại từ `tab_document`.** Cột bên đó đã có dữ liệu và mang số
của hai thang khác nhau, không trỏ nổi vào một bảng. Chống mồ côi bằng chốt chặn
lúc xóa (`security_level_guard.py`) — xem quy ước 5 của `van-thu/04` mục 2 và lý
do lệch ghi ở đây.
"""
from sqlalchemy import Boolean, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

#: Hai thang. Số này KHÔNG phải danh mục — thêm thang thứ ba thì không cột nào
#: trên `tab_document` chứa nó, nên nó là hằng số của mã chứ không phải dữ liệu.
KIND_CONFIDENTIAL = 1
KIND_URGENCY = 2
KIND_LABELS = {KIND_CONFIDENTIAL: "Mức mật", KIND_URGENCY: "Độ khẩn"}


class SecurityLevel(Base, AuditMixin):
    """Một bậc của thang mức mật hoặc thang độ khẩn.

    Dùng chung cho mọi pháp nhân nên cố ý KHÔNG có `company_id`: mức "Mật" ở
    DEGO và ở công ty con là cùng một mức, tách theo pháp nhân thì 13 nơi khai
    13 lần rồi lệch nhau.
    """

    __tablename__ = "tab_security_level"
    __table_args__ = (
        #  Khóa nghiệp vụ. Không đặt `unique` lên riêng `value` được vì hai thang
        #  dùng chung dải số nhỏ (Công khai = 1 và Thường = 1).
        UniqueConstraint("kind", "value", name="uq_security_level_kind_value"),
    )

    #: 1 mức mật · 2 độ khẩn — xem `KIND_LABELS`.
    kind: Mapped[int] = mapped_column(SmallInteger, default=KIND_CONFIDENTIAL)
    #: Con số lưu xuống `tab_document.secrecy_level` / `.urgency`. Càng lớn càng
    #: nghiêm / càng gấp — xem phần đầu tệp.
    value: Mapped[int] = mapped_column(SmallInteger)

    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
