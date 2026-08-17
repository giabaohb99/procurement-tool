"""CẦU NỐI giữa bộ máy duyệt và module chứng từ.

Bộ máy duyệt **cố ý không biết** gì về văn bản, YCMH hay ĐMH. Nhưng khi một
phiên duyệt kết thúc thì chứng từ phải đổi trạng thái theo — và chỉ module của
chứng từ đó mới biết "đã duyệt" nghĩa là gì với nó (văn bản thì cấp số và khóa
phiên bản; YCBG thì đi thẳng sang *đang xử lý*).

Nên module chứng từ **tự đăng ký** hàm của mình, một lần lúc nạp mã. Làm ngược
lại — để bộ máy `if entity == "document": …` — thì mỗi lần thêm một loại chứng
từ lại phải sửa lõi, và lõi dần biến thành nơi chứa luật của mọi phân hệ.
"""
from typing import Callable

from sqlalchemy.orm import Session

#  entity → {"approved": fn, "rejected": fn, "returned": fn}
_HOOKS: dict[str, dict[str, Callable]] = {}


def register(entity: str, *, on_approved: Callable | None = None,
             on_rejected: Callable | None = None,
             on_returned: Callable | None = None) -> None:
    """Khai hàm chạy khi phiên duyệt của loại chứng từ này kết thúc.

    Mỗi hàm nhận `(db, entity_id, instance)`.
    """
    _HOOKS[entity] = {
        "approved": on_approved,
        "rejected": on_rejected,
        "returned": on_returned,
    }


def fire(db: Session, instance, ket_cuc: str) -> None:
    """Gọi hàm của module chứng từ, nếu có khai.

    ⚠️ Nuốt lỗi CÓ CHỦ Ý. Tới đây phiên duyệt đã kết thúc và đã ghi vào dấu vết;
    để lỗi bay lên thì cả giao dịch bị hủy, chữ ký vừa đặt biến mất, và người
    duyệt bấm lại lần nữa cũng hỏng y như vậy. Chứng từ không đổi được trạng
    thái là việc phải sửa tay — nhưng phải sửa từ một hệ có ghi lại chữ ký, chứ
    không phải từ một hệ đã quên.
    """
    ham = (_HOOKS.get(instance.entity) or {}).get(ket_cuc)
    if ham is None:
        return
    try:
        ham(db, instance.entity_id, instance)
    except Exception as loi:   # noqa: BLE001 — xem ghi chú trên
        import logging

        logging.getLogger(__name__).exception(
            "Phiên duyệt %s đã %s nhưng %s #%s không đổi được trạng thái: %s",
            instance.id, ket_cuc, instance.entity, instance.entity_id, loi,
        )


def da_khai(entity: str) -> bool:
    return entity in _HOOKS
