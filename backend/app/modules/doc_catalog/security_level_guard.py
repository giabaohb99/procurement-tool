"""Chốt chặn cho danh mục MỨC MẬT / ĐỘ KHẨN.

Danh mục này khác mọi danh mục nền khác ở một điểm: **không có khóa ngoại nào
trỏ vào nó**. `tab_document.secrecy_level` chỉ là một số trần (lý do ở đầu
`security_level_model.py`). Nên toàn bộ việc chống dữ liệu mồ côi nằm ở đây —
xóa nhầm thì không có ràng buộc nào của MySQL đỡ hộ.

Ba nơi phải rà trước khi cho xóa, nơi thứ ba là nơi nguy hiểm nhất:

1. **văn bản** đang mang con số đó;
2. **loại văn bản** đang đặt nó làm mức mật mặc định;
3. **điều kiện luồng duyệt** đang trỏ tới. Đây là chỗ chết người: điều kiện lưu
   dạng CHUỖI JSON trong `tab_approval_flow.condition` / `tab_approval_node.condition`,
   không có khóa ngoại, không truy vấn ngược được bằng SQL thường. Xóa mức 3 mà
   một luồng đang khai "mức ≥ 3 thì thêm bước Giám đốc ký" thì luồng đó **không
   báo lỗi gì cả** — nó chỉ lặng lẽ không khớp nữa, và văn bản mật từ đó đi
   thẳng qua không cần ai ký.
"""
import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .security_level_model import KIND_CONFIDENTIAL, KIND_URGENCY, SecurityLevel

#: Tên trường trong điều kiện luồng duyệt, theo thang. Khớp `approval_bridge.boi_canh()`.
FIELD_BY_KIND = {KIND_CONFIDENTIAL: "secrecy_level", KIND_URGENCY: "urgency"}


def ensure_kind_value_free(db: Session, kind: int, value: int, exclude_id: int | None = None):
    """Một thang không được có hai bậc cùng số — nếu không thì `secrecy_level = 3`
    đọc ra hai mức khác nhau tùy ai tra."""
    q = db.query(SecurityLevel.id).filter(
        SecurityLevel.kind == kind, SecurityLevel.value == value
    )
    if exclude_id:
        q = q.filter(SecurityLevel.id != exclude_id)
    if q.first():
        raise HTTPException(400, f"Thang này đã có bậc số {value}")


def before_create(db: Session, data):
    ensure_kind_value_free(db, data.kind, data.value)


def _dem_van_ban(db: Session, level: SecurityLevel) -> int:
    from app.modules.document.model import Document

    cot = Document.secrecy_level if level.kind == KIND_CONFIDENTIAL else Document.urgency
    return db.query(Document.id).filter(cot == level.value).count()


def _dem_loai_van_ban(db: Session, level: SecurityLevel) -> int:
    #  Chỉ mức mật mới là mặc định của loại văn bản; độ khẩn không có cột tương ứng.
    if level.kind != KIND_CONFIDENTIAL:
        return 0
    from .model import DocType

    return db.query(DocType.id).filter(DocType.default_secrecy == level.value).count()


def _luong_duyet_dang_tro_toi(db: Session, level: SecurityLevel) -> list[str]:
    """Tên các luồng / nút có điều kiện nhắc tới bậc này.

    Đọc JSON trong Python chứ không lọc bằng SQL: điều kiện là cây lồng nhau
    (`all` / `any` chứa các mệnh đề con), so chuỗi thô kiểu `LIKE '%value%'` thì
    vừa bắt nhầm (số 3 khớp cả `value: 30`) vừa bỏ sót. Danh mục luồng chỉ vài
    chục dòng nên đọc hết ra là chấp nhận được.
    """
    from app.modules.approval.flow_model import ApprovalFlow, ApprovalNode

    field = FIELD_BY_KIND[level.kind]
    dang_tro: list[str] = []

    for Model in (ApprovalFlow, ApprovalNode):
        #  `condition` là `Text` mặc định chuỗi rỗng, không phải NULL.
        for row in db.query(Model).filter(Model.condition != "").all():
            if _dieu_kien_co_nhac(row.condition, field, level.value):
                dang_tro.append(row.name or f"#{row.id}")

    return dang_tro


def _dieu_kien_co_nhac(dieu_kien, field: str, value: int) -> bool:
    """Cây điều kiện có mệnh đề nào trỏ vào `field` với đúng con số này không."""
    if not dieu_kien:
        return False
    if isinstance(dieu_kien, str):
        try:
            dieu_kien = json.loads(dieu_kien)
        except (ValueError, TypeError):
            return False
    return _quet(dieu_kien, field, value)


def _quet(nut, field: str, value: int) -> bool:
    if isinstance(nut, list):
        return any(_quet(con, field, value) for con in nut)
    if not isinstance(nut, dict):
        return False
    if nut.get("field") == field:
        moc = nut.get("value")
        #  `in` nhận danh sách; các phép còn lại nhận một giá trị. So bằng chuỗi
        #  vì `condition_service._one()` cũng so bằng chuỗi — khớp đúng cách bộ
        #  máy duyệt đọc, không khớp cách mình đoán.
        moc_list = moc if isinstance(moc, list) else [moc]
        if any(str(m) == str(value) for m in moc_list):
            return True
    #  Mệnh đề lồng: `{"all": [...]}`, `{"any": [...]}`, hoặc khóa bất kỳ.
    return any(_quet(con, field, value) for con in nut.values())


def before_delete(db: Session, level: SecurityLevel):
    """Chặn xóa khi còn nơi dùng. Nêu ĐÍCH DANH chỗ đang vướng.

    Câu "không xóa được vì đang được dùng" bắt người dùng tự đi tìm; mà tìm điều
    kiện luồng duyệt thì không có màn nào tra ngược được.
    """
    vuong: list[str] = []

    so_van_ban = _dem_van_ban(db, level)
    if so_van_ban:
        vuong.append(f"{so_van_ban} văn bản đang ở bậc này")

    so_loai = _dem_loai_van_ban(db, level)
    if so_loai:
        vuong.append(f"{so_loai} loại văn bản đang lấy làm mức mật mặc định")

    luong = _luong_duyet_dang_tro_toi(db, level)
    if luong:
        ten = ", ".join(f"«{t}»" for t in luong[:5])
        them = f" và {len(luong) - 5} chỗ nữa" if len(luong) > 5 else ""
        vuong.append(f"điều kiện phê duyệt đang trỏ tới: {ten}{them}")

    if vuong:
        raise HTTPException(
            400,
            f"Không xóa được bậc «{level.name}» — " + "; ".join(vuong) + ". "
            "Muốn thôi dùng thì bỏ tick «Đang dùng» thay vì xóa.",
        )
