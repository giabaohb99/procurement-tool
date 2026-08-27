"""CHỐNG TỰ NÂNG QUYỀN — màn Phân quyền tài khoản (CR-158).

Trước 25/08/2026 màn này không có chốt nào, nên **bất kỳ ai có `user.write` đều
tự phong quản trị hệ thống trong một lần bấm**: mở trang của chính mình, tick
«Quản trị hệ thống», bấm *Lưu vai trò*. Dựng lại được qua API — sau cú bấm đó
`/api/auth/me` trả hồ sơ quyền đủ **42/42** entity (sau khi vá còn 2).

Bốn lối vào, đều phải đóng:
  1. tự gán vai trò cao cho CHÍNH MÌNH;
  2. gán cho NGƯỜI KHÁC rồi nhờ họ gán ngược lại;
  3. tick full ma trận của chính vai trò mình đang giữ (`role.write`);
  4. tự nới phạm vi dữ liệu của mình.

Và hai chiều ngược phải giữ nguyên: admin vẫn làm được mọi thứ, người quản lý
vẫn gán được vai trò NẰM TRONG tầm quyền của họ cho người khác. Chốt chặn mà cản
việc hằng ngày thì người ta gỡ nó ra, và lúc đó không còn chốt nào.
"""
import pytest
from fastapi import HTTPException

from app.core import privilege_escalation as pe
from app.core.permissions import ACTIONS
from app.modules.role.model import Permission, Role
from app.modules.user.model import User, UserRole


class _NguoiThaoTac:
    """Đủ dùng cho các hàm chốt chặn — chúng chỉ đọc `.id`."""

    def __init__(self, user_id: int):
        self.id = user_id


@pytest.fixture()
def san(db):
    """Hai vai trò: một 'to' (đủ quyền) và một 'nhỏ' (chỉ đọc)."""
    to = Role(code="ZZ_TO", name="Vai trò to")
    nho = Role(code="ZZ_NHO", name="Vai trò nhỏ")
    db.add_all([to, nho])
    db.flush()

    db.add(Permission(role_id=to.id, entity="user", can_read=True, can_write=True,
                      scope="all", created_by=1, updated_by=1))
    db.add(Permission(role_id=to.id, entity="document", can_read=True, can_create=True,
                      can_write=True, can_delete=True, scope="all",
                      created_by=1, updated_by=1))
    db.add(Permission(role_id=nho.id, entity="document", can_read=True, scope="own",
                      created_by=1, updated_by=1))

    person = User(email="ZZ_HR", password_hash="x", is_active=True)
    db.add(person)
    db.flush()
    db.add(UserRole(user_id=person.id, role_id=nho.id, created_by=1, updated_by=1))
    db.commit()
    return {"to": to.id, "nho": nho.id, "user": person.id}


# ── L1: không tự sửa quyền của chính mình ──────────────────────────────────

def test_khong_tu_gan_vai_tro_cho_chinh_minh(san):
    with pytest.raises(HTTPException) as error:
        pe.block_edit_own_permissions(san["user"], _NguoiThaoTac(san["user"]))
    assert error.value.status_code == 403


def test_van_gan_duoc_cho_nguoi_khac(san):
    """L1 chỉ chặn đúng chiều tự-mình. Cản cả chiều kia là hỏng nghiệp vụ."""
    pe.block_edit_own_permissions(san["user"] + 1, _NguoiThaoTac(san["user"]))


def test_khong_tu_sua_ma_tran_cua_vai_tro_minh_dang_giu(db, san):
    """Cửa sau không đụng tới tài khoản nào — chỉ tick thêm ô vào ma trận."""
    with pytest.raises(HTTPException) as error:
        pe.block_edit_own_role(db, san["nho"], _NguoiThaoTac(san["user"]))
    assert error.value.status_code == 403


def test_van_sua_duoc_ma_tran_cua_vai_tro_minh_khong_giu(db, san):
    pe.block_edit_own_role(db, san["to"], _NguoiThaoTac(san["user"]))


# ── L2: không cấp thứ mình không có ────────────────────────────────────────

def test_khong_gan_duoc_vai_tro_manh_hon_quyen_cua_minh(db, san):
    """Đây là chốt làm L1 có nghĩa.

    Không có nó thì đi vòng xong trong hai phút: gán vai trò to cho đồng nghiệp,
    nhờ họ gán ngược lại cho mình.
    """
    with pytest.raises(HTTPException) as error:
        pe.block_role_escalation(db, _NguoiThaoTac(san["user"]), [san["to"]])
    assert error.value.status_code == 403
    assert "không có" in str(error.value.detail)


def test_gan_duoc_vai_tro_nam_trong_tam_quyen_cua_minh(db, san):
    """Người đang giữ vai trò nhỏ vẫn gán được chính vai trò nhỏ cho người khác."""
    pe.block_role_escalation(db, _NguoiThaoTac(san["user"]), [san["nho"]])


def test_cau_loi_ke_ten_muc_bi_vuong(db, san):
    """Người đọc câu này thường là quản trị đang tưởng hệ hỏng — phải chỉ ra chỗ."""
    with pytest.raises(HTTPException) as error:
        pe.block_privilege_escalation(db, _NguoiThaoTac(san["user"]),
                               {("payment_request", "approve")})
    assert "Yêu cầu thanh toán" in str(error.value.detail)


def test_quyen_cua_vai_tro_gom_dung_tap_entity_action(db, san):
    tap = pe.permissions_of_roles(db, [san["to"]])
    assert ("user", "write") in tap
    assert ("document", "delete") in tap
    assert ("document", "approve") not in tap, "không được bịa ra hành động chưa tick"


def test_vai_tro_khong_ton_tai_bi_chan(db, san):
    with pytest.raises(HTTPException) as error:
        pe.block_missing_roles(db, [san["nho"], 999999])
    assert error.value.status_code == 400
    assert "999999" in str(error.value.detail)


def test_danh_sach_vai_tro_rong_khong_no(db):
    """Gỡ hết vai trò của một người là thao tác hợp lệ."""
    pe.block_missing_roles(db, [])
    pe.block_role_escalation(db, _NguoiThaoTac(1), [])


# ── Đọc ma trận gửi lên ────────────────────────────────────────────────────

def test_doc_dung_o_da_tick_trong_ma_tran_gui_len():
    class _O:
        def __init__(self, entity, **co):
            self.entity = entity
            for action in ACTIONS:
                setattr(self, f"can_{action}", co.get(action, False))

    tap = pe.permissions_in_matrix([_O("document", read=True, delete=True),
                                  _O("user", read=True)])
    assert tap == {("document", "read"), ("document", "delete"), ("user", "read")}


# ── Xóa vai trò còn người giữ ──────────────────────────────────────────────

def test_khong_xoa_duoc_vai_tro_dang_co_nguoi_giu(db, san):
    """`tab_user_role` không có khóa ngoại nên CSDL không đỡ hộ.

    Xóa xong dòng gán ở lại, trỏ vào một vai trò không còn tồn tại: người dùng
    lặng lẽ mất quyền, không thông báo, không dấu vết, và mọi thống kê đếm theo
    vai trò đều đếm cả dòng rác. Dựng lại được 25/08/2026 — ăn 200 gọn ơ.
    """
    from app.modules.role import service

    with pytest.raises(HTTPException) as error:
        service.delete_role(db, san["nho"], 1)
    assert error.value.status_code == 400
    assert "1 tài khoản" in str(error.value.detail)


def test_xoa_duoc_vai_tro_khong_ai_giu(db, san):
    from app.modules.role import service

    service.delete_role(db, san["to"], 1)
    assert db.get(Role, san["to"]) is None
    assert db.query(Permission).filter(Permission.role_id == san["to"]).count() == 0
