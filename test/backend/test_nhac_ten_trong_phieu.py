"""Gợi ý `@` trong Trao đổi — ưu tiên người TRÊN PHIẾU, không cắt mất họ (yêu cầu 07/09/2026).

Lỗi cũ: menu chỉ lấy 60 dòng chưa sắp xếp rồi cắt còn 8, nên với một họ đông người ("Nguyễn"
có 81 tài khoản) thì đúng người đứng trên phiếu — ví dụ người NHẬN của đơn giao hàng — lại rơi
khỏi danh sách vì tên xếp cuối bảng chữ cái. Sửa: người trên phiếu (người tạo/yêu cầu/duyệt/tài
xế + người gửi/nhận dò từ chữ) được đánh dấu `related`, luôn nổi lên đầu và LUÔN có mặt.
"""
from app.modules.comment import service
from app.modules.employee.model import Employee
from app.modules.user.model import User
from app.modules.vehicle_booking.model import VehicleBooking


def _user(db, full_name: str, code: str) -> User:
    emp = Employee(code=code, full_name=full_name, is_active=True)
    db.add(emp)
    db.flush()
    u = User(email=code, employee_id=emp.id, password_hash="x", is_active=True)
    db.add(u)
    db.flush()
    return u


def _delivery(db, *, creator_id: int, receiver_name: str) -> VehicleBooking:
    b = VehicleBooking(code="DX999", request_type=2, purpose="Giao hàng",
                       receiver_name=receiver_name, sender_name="Anh Thái",
                       requester_id=creator_id, created_by=creator_id, status=3)
    db.add(b)
    db.commit()
    return b


def test_nguoi_nhan_tren_phieu_luon_hien_du_ten_xep_cuoi_bang(db):
    """Người NHẬN của đơn (tên xếp cuối trong 25 người cùng họ) vẫn phải hiện khi search họ."""
    creator = _user(db, "Người Tạo", "TAOPHIEU")
    #  25 người họ "Nguyễn" xếp trước theo bảng chữ cái — thừa sức đẩy người cần ra ngoài hạn.
    for i in range(25):
        _user(db, f"Nguyễn An {i:02d}", f"NG{i:02d}")
    #  Người nhận: tên bắt đầu bằng "Nguyễn Z…" nên xếp SAU cả 25 người trên.
    receiver = _user(db, "Nguyễn Zulu Cuối", "NGZULU")
    b = _delivery(db, creator_id=creator.id, receiver_name="Nguyễn Zulu Cuối")

    out = service.mentionable(db, b, "vehicle_booking", b.id, me_id=0, q="Nguyễn")
    ids = [r["user_id"] for r in out]

    assert receiver.id in ids, "người nhận trên phiếu bị cắt mất — đúng lỗi phải sửa"
    #  Người trên phiếu nổi lên ĐẦU và mang cờ related (FE gắn nhãn 'trong phiếu').
    assert out[0]["user_id"] == receiver.id
    assert out[0]["related"] is True


def test_chua_go_chu_chi_goi_y_nguoi_tren_phieu(db):
    """Mở ô ra (chưa gõ) chỉ gợi người dính tới phiếu — bấm được ngay, không đổ cả công ty."""
    creator = _user(db, "Người Tạo", "TAOPHIEU")
    receiver = _user(db, "Nguyễn Zulu Cuối", "NGZULU")
    _user(db, "Người Ngoài", "NGOAI")   # không dính phiếu -> không được gợi ý khi chưa gõ
    b = _delivery(db, creator_id=creator.id, receiver_name="Nguyễn Zulu Cuối")

    out = service.mentionable(db, b, "vehicle_booking", b.id, me_id=0, q="")
    ids = {r["user_id"] for r in out}
    assert ids == {creator.id, receiver.id}
    assert all(r["related"] for r in out)


def test_khong_tu_goi_y_chinh_minh(db):
    """Người đang gõ không tự xuất hiện trong danh sách @ của chính mình."""
    creator = _user(db, "Người Tạo", "TAOPHIEU")
    receiver = _user(db, "Nguyễn Zulu Cuối", "NGZULU")
    b = _delivery(db, creator_id=creator.id, receiver_name="Nguyễn Zulu Cuối")

    out = service.mentionable(db, b, "vehicle_booking", b.id, me_id=creator.id, q="")
    ids = {r["user_id"] for r in out}
    assert creator.id not in ids and ids == {receiver.id}


def test_cat_dung_so_toi_da_khi_ket_qua_qua_dai(db):
    """Search họ đông người vẫn cắt còn MENTION_LIMIT — menu gọn, không đổ hết 100 dòng."""
    creator = _user(db, "Người Tạo", "TAOPHIEU")
    for i in range(60):
        _user(db, f"Trần Bình {i:02d}", f"TB{i:02d}")
    b = _delivery(db, creator_id=creator.id, receiver_name="Không Ai")

    out = service.mentionable(db, b, "vehicle_booking", b.id, me_id=0, q="Trần")
    assert len(out) <= service.MENTION_LIMIT
