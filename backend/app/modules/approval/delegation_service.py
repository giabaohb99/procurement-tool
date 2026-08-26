"""ỦY QUYỀN CÓ THỜI HẠN — tra lúc chạy (I12).

Ủy quyền **không đổi người được giao việc**. Việc vẫn nằm nguyên tên người gốc;
người được ủy quyền chỉ *bấm thay* được, và nhật ký ghi CẢ HAI danh tính.

Làm ngược lại — chuyển hẳn việc sang người nhận ủy quyền — thì hết hạn ủy quyền
là một đống việc nằm sai chỗ, và bản in dấu vết mất luôn thông tin việc này vốn
của ai.
"""
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .delegation_model import Delegation


def _dang_hieu_luc(query, entity: str, hom_nay: date):
    return query.filter(
        Delegation.is_active.is_(True),
        Delegation.from_date <= hom_nay,
        Delegation.to_date >= hom_nay,
        Delegation.entity.in_(("", entity)),
    )


def nguoi_uy_quyen_cho(db: Session, to_employee_id: int, entity: str,
                       hom_nay: date | None = None) -> list[Delegation]:
    """Những ai đang ủy quyền cho người này — dùng dựng màn Việc của tôi."""
    return _dang_hieu_luc(
        db.query(Delegation).filter(Delegation.to_employee_id == to_employee_id),
        entity, hom_nay or date.today(),
    ).all()


def nguoi_duoc_uy_quyen_boi(db: Session, from_employee_id: int, entity: str,
                            hom_nay: date | None = None) -> list[Delegation]:
    """Chiều NGƯỢC của hàm trên — ai đang được người này ủy quyền bấm thay.

    Dùng lúc BÁO việc: người đi vắng mới là người mang tên trên việc, nên báo
    mỗi họ thì thư rơi vào hộp thư không ai đọc trong đúng khoảng thời gian ủy
    quyền sinh ra để chống lại.
    """
    return _dang_hieu_luc(
        db.query(Delegation).filter(Delegation.from_employee_id == from_employee_id),
        entity, hom_nay or date.today(),
    ).all()


def tim_uy_quyen(db: Session, actor_employee_id: int, owner_employee_id: int,
                 entity: str, hom_nay: date | None = None) -> Delegation | None:
    """`actor` có được bấm thay `owner` không. `None` = không được."""
    if actor_employee_id == owner_employee_id:
        return None
    return _dang_hieu_luc(
        db.query(Delegation).filter(
            Delegation.to_employee_id == actor_employee_id,
            Delegation.from_employee_id == owner_employee_id,
        ),
        entity, hom_nay or date.today(),
    ).first()


def kiem_tra_truoc_khi_luu(db: Session, from_employee_id: int, to_employee_id: int,
                           entity: str, from_date: date, to_date: date,
                           bo_qua_id: int | None = None,
                           actor_employee_id: int | None = None) -> None:
    """Bốn luật của ủy quyền, kiểm trước khi ghi.

    `actor_employee_id` = người đang bấm lưu. Bỏ trống (`None`) nghĩa là **chỗ
    gọi đã tự kiểm quyền lập hộ** — xem `delegation_controller`.
    """
    #  ⚠️ CHỈ CHÍNH CHỦ MỚI CHO ĐI CHỮ KÝ CỦA MÌNH.
    #
    #  Đây là cửa hậu bẩn nhất của cả bộ máy duyệt và nó chỉ cần một quyền hành
    #  chính tầm thường (`approval_flow.create`, thứ hay cấp cho trợ lý và admin
    #  phân hệ): lập một dòng `from = giám đốc, to = chính mình`. Giám đốc không
    #  bấm gì, không nhận thông báo nào, mà từ giây đó kẻ lập ký được MỌI phiếu
    #  đang chờ ông ấy — dấu vết ghi «ký thay theo ủy quyền số 12», đúng thứ
    #  người soát sổ sẽ lướt qua.
    #
    #  Ba luật cũ bên dưới đều đúng nhưng không luật nào hỏi câu này, vì chúng
    #  chỉ nhìn cặp (from, to) chứ không nhìn NGƯỜI ĐANG BẤM.
    if actor_employee_id is not None and actor_employee_id != from_employee_id:
        raise HTTPException(
            403, "Chỉ chính người ủy quyền mới lập được ủy quyền của mình. "
                 "Cần lập hộ thì nhờ người quản trị hệ thống.")

    if from_employee_id == to_employee_id:
        raise HTTPException(400, "Không ủy quyền cho chính mình")
    if from_date > to_date:
        raise HTTPException(400, "Ngày bắt đầu ủy quyền phải trước ngày kết thúc")

    #  ⚠️ CẤM ỦY QUYỀN DÂY CHUYỀN. A ủy cho B rồi B ủy tiếp cho C thì việc của A
    #  cuối cùng do C bấm, mà C không hề biết mình đang ký thay A. Chặn ở đây vì
    #  ràng buộc dữ liệu không nhìn thấy được chuỗi.
    query = db.query(Delegation).filter(
        Delegation.to_employee_id == from_employee_id,
        Delegation.is_active.is_(True),
        Delegation.from_date <= to_date,
        Delegation.to_date >= from_date,
        Delegation.entity.in_(("", entity)),
    )
    if bo_qua_id:
        query = query.filter(Delegation.id != bo_qua_id)
    day_chuyen = query.first()
    if day_chuyen:
        raise HTTPException(
            400,
            "Người này đang nhận ủy quyền từ người khác trong cùng khoảng thời gian, "
            "nên không ủy quyền tiếp được. Ủy quyền dây chuyền làm mất dấu ai chịu "
            "trách nhiệm cuối cùng.",
        )
