from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import perm_cache_clear
from .model import Permission, Role
from .schema import PermissionUpdate, RoleCreate, RoleUpdate


def list_roles_query(db: Session):
    """Query thô để controller còn gắn thêm bộ lọc (apply_filters) trước khi .all().

    Xếp theo THỨ TỰ NGƯỜI QUẢN TRỊ ĐẶT, `id` chỉ là khóa phụ để hai vai trò cùng
    `sort_order` (mặc định 0 cho tới lần kéo thả đầu tiên) không đảo chỗ nhau
    giữa hai lần nạp — danh sách nhảy lung tung là người dùng mất dấu vai trò
    mình vừa bấm.
    """
    return db.query(Role).order_by(Role.sort_order, Role.id)


def sap_xep_vai_tro(db: Session, role_ids: list[int], user_id: int) -> None:
    """Ghi lại thứ tự vai trò theo đúng dãy `role_ids` nhận được.

    Nhận **toàn bộ** dãy chứ không nhận từng cặp (id, vị trí): kéo một dòng lên
    đầu là mọi dòng phía dưới đổi số, gửi từng cặp thì client phải tự tính lại
    hết rồi bắn N request — nửa chừng đứt mạng là thứ tự vỡ.

    Id lạ (vai trò vừa bị người khác xóa) thì **bỏ qua**, không dựng 404: người
    dùng vẫn đang kéo trên danh sách cũ, chặn cả lượt vì một dòng đã biến mất là
    vứt luôn công sắp xếp của họ.
    """
    for vi_tri, rid in enumerate(role_ids, start=1):
        obj = db.get(Role, rid)
        if obj is None:
            continue
        obj.sort_order = vi_tri
        obj.updated_by = user_id
    db.commit()


def list_roles(db: Session):
    return list_roles_query(db).all()


def get_role(db: Session, rid: int) -> Role:
    obj = db.get(Role, rid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy vai trò")
    return obj


def create_role(db: Session, data: RoleCreate, user_id: int) -> Role:
    if db.query(Role).filter(Role.code == data.code).first():
        raise HTTPException(400, "Mã vai trò đã tồn tại")
    #  Vai trò mới xuống CUỐI danh sách, không để mặc định 0.
    #  Ép ra được 25/08/2026: người quản trị xếp tay 17 vai trò xong thêm một
    #  vai trò mới, nó mang `sort_order = 0` nên nhảy lên **đứng đầu**, trên cả
    #  «Quản trị hệ thống» — phá đúng cái thứ tự họ vừa dựng. Thứ mới thêm thì
    #  người ta trông nó ở cuối. Danh sách chưa ai xếp (toàn 0) thì vai trò mới
    #  nhận 1, vẫn nằm cuối — đúng như xếp theo `id` trước đây.
    ke_tiep = (db.query(func.max(Role.sort_order)).scalar() or 0) + 1
    obj = Role(code=data.code, name=data.name, description=data.description,
               sort_order=ke_tiep, created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_role(db: Session, rid: int, data: RoleUpdate, user_id: int) -> Role:
    obj = get_role(db, rid)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    obj.updated_by = user_id
    db.commit()
    db.refresh(obj)
    return obj


def delete_role(db: Session, rid: int, user_id: int) -> None:
    obj = get_role(db, rid)
    # So sánh KHÔNG phân biệt hoa/thường: vai trò chuẩn trên DB có code là 'admin' (chữ thường),
    # danh sách chặn trước đây viết hoa nên không khớp -> vẫn xóa được vai trò quản trị hệ thống.
    if (obj.code or "").strip().upper() in ("ADMIN", "ADMINISTRATOR"):
        raise HTTPException(400, "Không được xóa vai trò mặc định của hệ thống")

    #  ⚠️ CÒN NGƯỜI GIỮ THÌ KHÔNG XÓA. `tab_user_role` không có khóa ngoại nên
    #  CSDL không đỡ hộ: xóa vai trò xong dòng gán ở lại, trỏ vào một vai trò
    #  không còn tồn tại. Người dùng lặng lẽ mất quyền — không thông báo, không
    #  dấu vết, và màn Phân quyền của họ hiện ít hơn đúng một dòng mà không ai
    #  đọc ra vì sao. Dòng rác thì mọi thống kê đếm theo vai trò đều đếm cả.
    #  Dựng lại được 25/08/2026: xóa một vai trò đang có người giữ ăn 200 gọn ơ.
    #
    #  Chặn chứ không tự gỡ gán: gỡ hộ là quyết định thay người quản trị về việc
    #  «những người này từ nay không còn vai trò nào» — cùng lẽ với chỗ chặn xóa
    #  luồng duyệt còn phiếu đang chạy.
    from app.modules.user.model import UserRole, UserScope

    con_giu = db.query(UserRole).filter(UserRole.role_id == rid).count()
    if con_giu:
        raise HTTPException(
            400,
            f"Vai trò này đang gán cho {con_giu} tài khoản nên chưa xóa được. "
            "Gỡ vai trò khỏi các tài khoản đó trước — hoặc để nguyên nếu chỉ muốn "
            "ngừng dùng.")

    db.query(Permission).filter(Permission.role_id == rid).delete()
    #  Phạm vi lưu theo cặp (tài khoản × vai trò): vai trò đi rồi thì mấy dòng
    #  này cũng hết chỗ bám.
    db.query(UserScope).filter(UserScope.role_id == rid).delete()
    db.delete(obj)
    db.commit()
    perm_cache_clear()


def get_permissions(db: Session, rid: int):
    get_role(db, rid)
    return db.query(Permission).filter(Permission.role_id == rid).all()


def set_permissions(db: Session, rid: int, data: PermissionUpdate, user_id: int):
    get_role(db, rid)
    db.query(Permission).filter(Permission.role_id == rid).delete()
    for item in data.permissions:
        db.add(Permission(role_id=rid, created_by=user_id, updated_by=user_id, **item.model_dump()))
    db.commit()
    perm_cache_clear()  # quyền vừa đổi → nạp lại ở request sau
    return get_permissions(db, rid)
