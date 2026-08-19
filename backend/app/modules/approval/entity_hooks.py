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

#  entity → {"approved": fn, "rejected": fn, "returned": fn, "withdrawn": fn}
_HOOKS: dict[str, dict[str, Callable]] = {}


def register(entity: str, *, on_approved: Callable | None = None,
             on_rejected: Callable | None = None,
             on_returned: Callable | None = None,
             on_withdrawn: Callable | None = None) -> None:
    """Khai hàm chạy khi phiên duyệt của loại chứng từ này kết thúc.

    Mỗi hàm nhận `(db, entity_id, instance)`.

    ⚠️ `on_withdrawn` bổ sung 19/08/2026 và là **bốn kết cục, không phải ba**.
    Thiếu nó thì người nộp rút phiếu xong chứng từ vẫn nằm ở *đang duyệt*:
    không gửi duyệt lại được (đường gửi chỉ nhận bản nháp) mà nút duyệt MỘT
    BƯỚC thì mở lại — vì chốt chặn chỉ khóa khi phiên còn ĐANG CHẠY. Đã dựng
    được ca thật: văn bản lên có hiệu lực, cấp số, trong khi phiên duyệt ghi
    «Đã rút» và không ai ký bước nào.
    """
    _HOOKS[entity] = {
        "approved": on_approved,
        "rejected": on_rejected,
        "returned": on_returned,
        "withdrawn": on_withdrawn,
    }


def fire(db: Session, instance, ket_cuc: str) -> None:
    """Gọi hàm của module chứng từ, nếu có khai.

    ⚠️ Nuốt lỗi CÓ CHỦ Ý. Tới đây phiên duyệt đã kết thúc và đã ghi vào dấu vết;
    để lỗi bay lên thì cả giao dịch bị hủy, chữ ký vừa đặt biến mất, và người
    duyệt bấm lại lần nữa cũng hỏng y như vậy. Chứng từ không đổi được trạng
    thái là việc phải sửa tay — nhưng phải sửa từ một hệ có ghi lại chữ ký, chứ
    không phải từ một hệ đã quên.

    ⚠️ Nuốt lỗi KHÔNG có nghĩa là giấu lỗi. Lý do hỏng được ghi vào
    `instance.finish_reason` để nó nổi lên tận màn hình chứng từ. Trước đây lỗi
    chỉ vào log container: phiếu ghi «Đã duyệt» còn văn bản nằm lại ở *chờ
    duyệt* không số, và không ai — kể cả người vừa ký — biết là có chuyện.
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
        try:
            instance.finish_reason = _cau_bao_hong(loi)
            db.flush()
        except Exception:   # noqa: BLE001
            #  Hỏng vì lỗi cơ sở dữ liệu thì phiên làm việc đã không dùng được
            #  nữa, ghi thêm cũng ném tiếp. Giữ nguyên tinh thần trên: không để
            #  bất cứ gì ở đây làm mất chữ ký vừa đặt.
            logging.getLogger(__name__).warning(
                "Không ghi được lý do hỏng vào phiên duyệt %s", instance.id)


def _cau_bao_hong(loi: Exception) -> str:
    """Câu để người dùng đọc, không phải câu để lập trình viên đọc.

    `HTTPException` mang sẵn thông điệp đã soạn cho người dùng (ví dụ "phải ban
    hành kèm một Quyết định") — lấy đúng câu đó. Lỗi khác thì không bày ruột
    gan ra màn hình, chỉ nói có chuyện và bảo họ gọi ai.
    """
    chi_tiet = getattr(loi, "detail", None)
    if isinstance(chi_tiet, str) and chi_tiet.strip():
        return f"Đã duyệt hết các bước nhưng CHƯA hoàn tất được: {chi_tiet}"
    return ("Đã duyệt hết các bước nhưng chứng từ chưa đổi được trạng thái. "
            "Báo quản trị hệ thống kiểm tra.")


def da_khai(entity: str) -> bool:
    return entity in _HOOKS
