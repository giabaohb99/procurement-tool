"""Định tuyến thông báo phiếu hỗ trợ + đính kèm theo từng tin nhắn.

- Người nhận việc hỗ trợ CHỈ là vai trò 'support' (QL thu mua đã bị bỏ ra để khỏi spam),
  chưa gán ai vai trò Hỗ trợ thì mới rơi về quản trị.
- Trả lời kiểu nhắn tin: file gắn vào chính tin nhắn (entity 'ticket_message'),
  _msg_files phải gom đúng file về đúng tin nhắn.
"""
from types import SimpleNamespace

from app.modules.ticket import service
from app.modules.ticket.controller import _msg_files, _support_users


def _user(db, email: str, role_code: str):
    from app.modules.role.model import Role
    from app.modules.user.model import User, UserRole
    r = db.query(Role).filter(Role.code == role_code).first()
    if not r:
        r = Role(code=role_code, name=role_code)
        db.add(r); db.flush()
    u = User(email=email, password_hash="x", is_active=True)
    db.add(u); db.flush()
    db.add(UserRole(user_id=u.id, role_id=r.id))
    db.commit()
    return u


def _phieu(db):
    data = SimpleNamespace(subject="Không đăng nhập được", department="Kỹ thuật / Phần mềm",
                           priority="normal", body="Mô tả lỗi", company_id=1,
                           origin_url="/purchase-orders", file_ids=[])
    return service.create_ticket(db, data, user_id=10, requester_emp_id=5)


def test_nguoi_nhan_ho_tro_khong_gom_ql_thu_mua(db):
    """Có người vai trò 'support' → chỉ họ nhận; QL thu mua đứng ngoài."""
    sup = _user(db, "support1@x.vn", "support")
    _user(db, "qltm@x.vn", "pur_manager")
    ids = [u.id for u in _support_users(db)]
    assert ids == [sup.id]


def test_chua_ai_lam_ho_tro_thi_ve_quan_tri(db):
    """Chưa gán vai trò 'support' cho ai → phiếu không rơi vào hư không, quản trị nhận."""
    _user(db, "qltm@x.vn", "pur_manager")
    adm = _user(db, "admin@x.vn", "admin")
    ids = [u.id for u in _support_users(db)]
    assert ids == [adm.id]


def test_file_gan_dung_tin_nhan(db):
    """File đính kèm trong ô trả lời phải nằm đúng bong bóng tin nhắn đó."""
    from app.modules.attachment.model import StoredFile
    t = _phieu(db)
    f1 = StoredFile(filename="anh-loi.png", file_key="k1", url="u1", content_type="image/png", size=10)
    f2 = StoredFile(filename="log.txt", file_key="k2", url="u2", content_type="text/plain", size=20)
    db.add_all([f1, f2]); db.commit()

    m1 = service.add_message(db, t.id, "Gửi anh ảnh lỗi", user_id=10, is_staff=False,
                             file_ids=[f1.id])
    m2 = service.add_message(db, t.id, "Đã nhận, gửi lại log", user_id=7, is_staff=True,
                             file_ids=[f2.id])

    fmap = _msg_files(db, [m1.id, m2.id])
    assert [f["filename"] for f in fmap[m1.id]] == ["anh-loi.png"]
    assert [f["filename"] for f in fmap[m2.id]] == ["log.txt"]


def test_tra_loi_chi_co_file_khong_can_noi_dung(db):
    """Kiểu nhắn tin: gửi mỗi ảnh, không gõ chữ vẫn hợp lệ."""
    from app.modules.attachment.model import StoredFile
    t = _phieu(db)
    f = StoredFile(filename="man-hinh.png", file_key="k", url="u", content_type="image/png", size=10)
    db.add(f); db.commit()
    m = service.add_message(db, t.id, "", user_id=10, is_staff=False, file_ids=[f.id])
    assert m.body == ""
    assert len(_msg_files(db, [m.id])[m.id]) == 1
