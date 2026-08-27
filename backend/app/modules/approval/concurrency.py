"""HAI NGƯỜI CÙNG BẤM TRÊN MỘT PHIẾU — biến kẹt khóa CSDL thành câu người đọc hiểu.

Lỗi dựng lại được 24/08/2026: hai người cùng đứng ở một bước, một người bấm
*Duyệt*, người kia bấm *Duyệt* (hoặc *Trả lại*) cùng lúc. Một cú ăn, cú còn lại
nhận **`500 Internal Server Error`** — log máy chủ ghi
`Deadlock found when trying to get lock` (MySQL 1213).

Dữ liệu KHÔNG hỏng: giao dịch thua bị cuộn lại trọn vẹn, chỉ một cú ăn. Hỏng là
ở chỗ người thua nhìn thấy một màn hình lỗi đỏ không nói gì, trong khi sự thật
chỉ là *"đồng nghiệp của bạn vừa bấm trước một nhịp"*.

⚠️ **CỐ Ý KHÔNG THỬ LẠI.** Bản đầu của tệp này có chạy lại một lần — cách chữa
kẹt khóa thường thấy — và nó **sai ở đúng chỗ nguy hiểm nhất**. Đã bắt được khi
kiểm lại: hai người ở bước 1, A bấm *Duyệt*, B bấm *Trả lại*; B kẹt khóa, cuộn
lại, **chạy lại trên trạng thái MỚI** — mà lúc đó A đã duyệt xong bước 1 và
phiếu đã sang bước 2, nơi B mới là người duyệt. Thế là cú *Trả lại* mà B bấm cho
**bước 1** lại ăn ở **bước 2**. Cả hai cú cùng "thành công", còn B thì vừa ký
một thứ họ chưa hề mở ra xem.

Cùng cái bẫy đó với *Duyệt*: người giữ hai bước liền nhau bấm một cái mà qua hai
bước. Chữ ký phải bám vào **đúng nội dung người ta đọc lúc bấm** — nguyên tắc đã
ghi ở `version_service.chan_khi_dang_duyet`.

Nên: kẹt khóa → cuộn lại → **409 kèm câu bảo tải lại trang**. Người dùng nhìn
tình trạng mới rồi tự quyết định lần nữa. Một cú bấm ăn đúng một lần, ở đúng
bước mà người bấm đang nhìn.
"""
from typing import Callable, TypeVar

from fastapi import HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

T = TypeVar("T")

#  1213 = deadlock, 1205 = hết giờ chờ khóa. Cùng bản chất "tranh nhau một
#  hàng", cùng cách chữa.
LOCK_ERROR_CODES = (1213, 1205)

CONFLICT_MESSAGE = ("Việc này vừa được người khác xử lý cùng lúc. "
           "Tải lại trang để xem phiếu đang ở đâu rồi thao tác tiếp.")


def _is_lock_error(error: OperationalError) -> bool:
    code = getattr(getattr(error, "orig", None), "args", None)
    return bool(code) and code[0] in LOCK_ERROR_CODES


def run_with_contention_retry(db: Session, task: Callable[[], T]) -> T:
    """Chạy `viec()`; kẹt khóa thì cuộn lại và trả 409 — KHÔNG chạy lại.

    Lỗi không phải kẹt khóa (cột sai kiểu, cú pháp hỏng…) thì để nguyên nó nổi
    lên: nuốt hết thành 409 là giấu lỗi thật sau một câu êm tai.
    """
    try:
        return task()
    except OperationalError as error:
        if not _is_lock_error(error):
            raise
        db.rollback()
        raise HTTPException(409, CONFLICT_MESSAGE) from error
