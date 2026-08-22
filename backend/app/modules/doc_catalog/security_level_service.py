"""Tra nhãn mức mật / độ khẩn từ danh mục.

Trước đây `document/export.py` giữ một BẢN CHÉP của bảy cái nhãn, với lý do ghi
tại chỗ là "file Excel phải đọc được kể cả khi ai đó đổi nhãn trên màn hình".
Lý do đó chết từ lúc bảy dòng này thành danh mục sửa được: đổi «Nội bộ» thành
«Lưu hành nội bộ» mà file Excel vẫn in chữ cũ thì đó là lỗi, không phải tính
năng — hai tờ giấy cùng nói về một văn bản mà gọi hai tên khác nhau.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .security_level_model import KIND_CONFIDENTIAL, KIND_URGENCY, SecurityLevel


def label_maps(db: Session) -> tuple[dict[int, str], dict[int, str]]:
    """Trả `(nhãn mức mật, nhãn độ khẩn)` theo `value`.

    Đọc cả dòng đã ngừng dùng: văn bản cũ vẫn mang con số đó và vẫn phải tra ra
    tên. Lọc `is_active` ở đây là bản in cũ tự dưng mất chữ.
    """
    mat: dict[int, str] = {}
    khan: dict[int, str] = {}
    for row in db.query(SecurityLevel).all():
        (mat if row.kind == KIND_CONFIDENTIAL else khan)[row.value] = row.name
    return mat, khan


def label(nhan: dict[int, str], value) -> str:
    """Số lạ (dữ liệu cũ, dòng đã bị xóa tay dưới DB) thì in ra chính con số —
    giống `secrecyLabel` bên giao diện. Trả chuỗi rỗng là mất luôn thông tin."""
    if value is None:
        return ""
    return nhan.get(value) or str(value)


def value_of_code(db: Session, code: str, mac_dinh: int = 1) -> int:
    """Bậc mang mã này đang là số mấy.

    Dùng cho những chỗ mã nguồn cần trỏ tới MỘT bậc cụ thể theo nghĩa của nó
    ("loại bảo mật thì tối thiểu phải Mật") — bám vào `code` chứ không viết số
    3 vào mã: quản trị đổi tên hiển thị thì `code` vẫn đứng yên, còn con số thì
    ở bản triển khai khác có thể khác.

    Không tìm thấy (bị ngừng dùng, hoặc nơi triển khai không có bậc đó) thì trả
    `mac_dinh` — im lặng bỏ sàn còn hơn dựng đứng cả luồng tạo văn bản.
    """
    row = db.query(SecurityLevel.value).filter(SecurityLevel.code == code).first()
    return row[0] if row else mac_dinh


def ensure_valid(db: Session, kind: int, value: int | None):
    """Con số gửi lên phải là một bậc ĐANG DÙNG của thang đó.

    Trước đây việc này do Pydantic làm bằng `ge=1, le=4`. Khóa cứng như thế thì
    thêm một bậc mới vào danh mục xong vẫn không lưu nổi văn bản mang bậc đó —
    danh mục sửa được trên giấy. Nay dải hợp lệ là chính danh mục.
    """
    if value is None:
        return
    hop_le = values_of(db, kind)
    #  Thang RỖNG = chưa cấu hình, không phải "không giá trị nào hợp lệ". Chặn
    #  hết ở đây thì một lỗi cấu hình danh mục (hoặc seed chưa kịp chạy trên bản
    #  triển khai mới) làm CẢ phân hệ Văn bản không lưu nổi một dòng nào — hỏng
    #  nặng hơn nhiều so với việc thả lỏng một con số.
    if not hop_le:
        return
    if value not in hop_le:
        from .security_level_model import KIND_LABELS

        raise HTTPException(
            400,
            f"{KIND_LABELS.get(kind, 'Thang')} không có bậc {value} đang dùng. "
            "Kiểm tra lại ở Thiết lập văn bản › Mức mật / khẩn.",
        )


def values_of(db: Session, kind: int) -> set[int]:
    """Các bậc ĐANG DÙNG của một thang — dùng để kiểm giá trị người dùng gửi lên.

    Chỉ lấy `is_active`: đây là danh sách chọn được, khác `label_maps` là danh
    sách đọc được.
    """
    rows = db.query(SecurityLevel.value).filter(
        SecurityLevel.kind == kind, SecurityLevel.is_active.is_(True)
    )
    return {row[0] for row in rows}
