"""Luật nghiệp vụ của HỒ SƠ — nơi duy nhất tính hiệu lực và ghi nhãn loại.

Hai nhóm việc:

* `sync_type_label` / `propagate_type_rename` — hai đường ghi DUY NHẤT vào cột
  nhãn `dossier_type_name`. Thêm đường thứ ba là nhãn trôi (xem `model.py`).
* `apply_extra_fields` — kiểm ô JSON theo bộ trường của loại đang chọn.

Tình trạng hiệu lực KHÔNG ở đây mà ở `expiry.py` — `model.py` cũng cần nó, và
`service.py` thì import `model.py`.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .field_schema import parse_field_defs
from .field_values import validate_extra_values
from .model import Dossier
from .type_model import DossierType


def _load_type(db: Session, type_id: int) -> DossierType:
    obj = db.get(DossierType, type_id) if type_id else None
    if not obj:
        raise HTTPException(400, "Loại hồ sơ không tồn tại")
    return obj


def sync_type_label(db: Session, values: dict,
                    current: Dossier | None = None) -> DossierType | None:
    """Chép tên loại vào `dossier_type_name`, và chặn gán loại đã ngừng dùng.

    Sửa TẠI CHỖ trên `values` — nơi gọi là hai chốt `before_create` /
    `before_update` của bộ sinh CRUD, cả hai đều cầm một dict sắp đem gán.

    **Trả về chính loại vừa đọc** (hoặc `None` khi payload không đụng tới loại)
    để `apply_extra_fields` dùng lại, khỏi tra bảng lần hai — xem ghi chú ở đó.

    ⚠️ **Loại đã ngừng dùng thì chặn gán MỚI, nhưng hồ sơ ĐANG giữ nó vẫn lưu
    được** (bài học duoc-CR-320). Màn chi tiết gửi lại mọi ô mỗi lần bấm Lưu,
    nên không có ngoại lệ này thì một hồ sơ mang loại vừa bị ngừng dùng sẽ không
    sửa nổi ô nào khác — kể cả ô ghi chú — cho tới khi có người đi bật lại loại
    đó cho cả công ty.
    """
    if "dossier_type_id" not in values:
        return None
    type_id = int(values.get("dossier_type_id") or 0)
    if not type_id:
        raise HTTPException(400, "Hồ sơ phải thuộc một loại hồ sơ")

    obj = _load_type(db, type_id)
    unchanged = current is not None and current.dossier_type_id == type_id
    if not obj.is_active and not unchanged:
        raise HTTPException(
            400,
            f"Loại hồ sơ «{obj.name}» đã ngừng dùng, không gán cho hồ sơ mới được. "
            "Bật lại «Còn dùng» ở danh mục Loại hồ sơ nếu vẫn cần.",
        )
    values["dossier_type_name"] = obj.name
    return obj


def apply_extra_fields(db: Session, values: dict, current: Dossier | None = None) -> None:
    """Kiểm `extra_fields` theo bộ trường CỦA CHÍNH HỒ SƠ, sửa tại chỗ.

    ⚠️ **`tab_dossier_type.field_schema` KHÔNG còn là luật ở đây** (đổi
    17/09/2026). Nó tụt xuống thành **KHUÔN**: màn lập hồ sơ đổ nó vào bảng
    «Trường riêng» khi người dùng chọn loại, rồi họ sửa/xóa tự do — xóa dòng nào
    thì TỜ NÀY không có ô đó, loại vẫn nguyên và hồ sơ khác cùng loại vẫn có.

    Nên nguồn khai duy nhất là `tab_dossier.custom_fields`. Giữ cả hai như trước
    thì mọi dòng vừa đổ từ khuôn ra đều trùng khóa với chính cái khuôn đẻ ra nó,
    và không hồ sơ nào lưu nổi.

    ⚠️ Vì thế hàm này KHÔNG còn đọc bảng danh mục — cả lần lưu chỉ `sync_type_label`
    tra một lượt (để chép nhãn). Tham số `dossier_type` cũ đã bỏ.

    ⚠️ Hệ quả phải biết: **ô `required` khai ở LOẠI không còn tự áp cho hồ sơ**.
    Nó chỉ có hiệu lực nếu dòng tương ứng còn nằm trong `custom_fields` của tờ
    đó — tức là đúng như người lập đã chốt trên màn hình. Muốn ép cứng cả công ty
    thì phải là một CỘT THẬT, không phải một dòng trong khuôn.
    """
    #  `PATCH` không đụng tới CẢ HAI thì giữ nguyên thứ đang lưu — kiểm luôn ở
    #  đây thì thêm một ô bắt buộc là chặn cả những lần sửa không liên quan.
    if "extra_fields" not in values:
        return

    #  ⚠️ Khai báo lấy từ payload NẾU lần lưu này có gửi, không thì từ bản ghi
    #  cũ. Lấy danh sách rỗng là mọi ô riêng bỗng thành «không còn khai báo» —
    #  mất luôn chốt bắt buộc của chúng.
    raw_custom = values["custom_fields"] if "custom_fields" in values         else (current.custom_field_defs if current else [])

    try:
        values["extra_fields"] = validate_extra_values(
            parse_field_defs(raw_custom), values.get("extra_fields"))
    except ValueError as exc:
        raise HTTPException(422, str(exc))


def propagate_type_rename(db: Session, type_id: int, new_name: str) -> int:
    """Đổi tên một loại thì chép tên mới sang mọi hồ sơ đang mang tên cũ.

    Trả về số dòng đã sửa. Chạy bằng MỘT câu `UPDATE` chứ không lặp từng dòng —
    danh mục này chỉ có dăm loại nhưng mỗi loại có thể gắn hàng nghìn hồ sơ.

    ⚠️ Không đụng `updated_at` / `updated_by` của hồ sơ: đây không phải ai đó
    sửa hồ sơ, mà là hệ chép lại một cái nhãn. Ghi dấu vết vào đây thì cả nghìn
    hồ sơ cùng nhảy lên đầu danh sách «vừa cập nhật» vì một lần sửa chính tả.
    """
    return (db.query(Dossier)
            .filter(Dossier.dossier_type_id == type_id,
                    Dossier.dossier_type_name != new_name)
            .update({Dossier.dossier_type_name: new_name},
                    synchronize_session=False))


def count_by_type(db: Session, type_id: int) -> int:
    """Số hồ sơ đang dùng một loại — đếm TOÀN CÔNG TY, không lọc phạm vi.

    ⚠️ Cố ý khác với con số bày cho người xem (duoc-CR-322): đây là chốt toàn
    vẹn dữ liệu, không phải một ô thống kê. Lọc theo phạm vi người bấm nút Xóa
    thì người chỉ thấy phòng mình sẽ đọc được «0 hồ sơ» và xóa mất loại mà phòng
    khác đang dùng.
    """
    return db.query(Dossier).filter(Dossier.dossier_type_id == type_id).count()
