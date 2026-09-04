"""DỜI LỊCH BẰNG KÉO THẢ — `service.reschedule` (duoc-CR-279).

Kéo một khối trên màn Lịch là đường sửa **duy nhất** đụng được vào phiếu đang
giữ phòng, nên nó cũng là đường dễ mở toang nhất. Ba thứ tệp này canh:

1. **Vẫn chặn trùng.** Kéo là đổi khoảng giờ; bỏ chốt trùng ở đây thì cả công
   sức chặn ở `reserve_slot` thành vô nghĩa — ai muốn đặt đôi chỉ cần đặt lệch
   giờ rồi kéo về.
2. **Không tự chặn chính mình.** Phiếu đang xét luôn chồng lên khoảng cũ của
   nó, quên `exclude_id` là không ai kéo được gì.
3. **Trạng thái GIỮ NGUYÊN.** Dời một phiếu đã duyệt không được lặng lẽ đẩy nó
   về nháp — phòng sẽ bị nhả ra mà người dùng tưởng vẫn còn giữ.

Gọi thẳng tầng `service`: container không có `httpx` nên không dựng `TestClient`.
"""
from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.meeting_room import service
from app.modules.meeting_room.constants import (RB_APPROVED, RB_CANCELLED,
                                                RB_DRAFT, RB_PENDING,
                                                RB_REJECTED)
from app.modules.meeting_room.model import MeetingRoom, RoomBooking
from app.modules.meeting_room.schema import RoomBookingCreate

MORNING = datetime(2026, 9, 10, 9, 0)


def _at_hour(h: int, m: int = 0) -> datetime:
    return MORNING.replace(hour=h, minute=m)


@pytest.fixture
def env(db):
    company = Company(name="Cty Test", code="CT01", is_active=True)
    db.add(company)
    db.flush()
    dept = Department(code="D1", name="Phòng Test", company_id=company.id, is_active=True)
    db.add(dept)
    db.flush()
    an = Employee(code="AN", full_name="Nguyễn Văn An", company_id=company.id,
                  department_id=dept.id, is_active=True)
    binh = Employee(code="BINH", full_name="Trần Thị Bình", company_id=company.id,
                    department_id=dept.id, is_active=True)
    db.add_all([an, binh])
    db.flush()
    small_room = MeetingRoom(code="P301", name="Phòng 301", company_id=company.id,
                             capacity=8, is_active=True, created_by=1, updated_by=1)
    big_room = MeetingRoom(code="P501", name="Phòng 501", company_id=company.id,
                           capacity=30, is_active=True, created_by=1, updated_by=1)
    db.add_all([small_room, big_room])
    db.commit()
    return SimpleNamespace(small_room=small_room, big_room=big_room,
                           user_an=SimpleNamespace(id=1, employee_id=an.id),
                           user_binh=SimpleNamespace(id=2, employee_id=binh.id))


def _book(db, env, room=None, start=None, end=None, user=None, **kw) -> RoomBooking:
    return service.create(db, RoomBookingCreate(
        room_id=(room or env.small_room).id,
        title=kw.pop("title", "Họp giao ban"),
        start_at=start or _at_hour(9),
        end_at=end or _at_hour(10),
        **kw,
    ), user or env.user_an)


def _held(db, env, **kw) -> RoomBooking:
    """Phiếu ĐANG GIỮ phòng — đúng thứ mà màn Lịch vẽ ra và cho kéo."""
    obj = _book(db, env, **kw)
    service.prepare_submit(db, obj, env.user_an)
    return service.reserve_slot(db, obj, env.user_an)


# ── Dời được ───────────────────────────────────────────────────────────────────

def test_doi_gio_phieu_dang_cho_duyet(db, env):
    """Chờ duyệt là trạng thái phổ biến nhất trên lịch — kéo được nó là luật gốc."""
    obj = _held(db, env)
    out = service.reschedule(db, obj, 0, _at_hour(14), _at_hour(15), env.user_an)
    assert out.start_at == _at_hour(14)
    assert out.end_at == _at_hour(15)


def test_TRANG_THAI_giu_nguyen_sau_khi_doi(db, env):
    """Dời phiếu ĐÃ DUYỆT mà đẩy về nháp là lặng lẽ NHẢ PHÒNG.

    Người dùng vừa kéo xong, nhìn thấy khối vẫn nằm đó, và tin là phòng vẫn của
    mình — trong khi bất kỳ ai cũng đặt chồng lên được.
    """
    obj = _held(db, env)
    obj.status = RB_APPROVED
    db.commit()
    out = service.reschedule(db, obj, 0, _at_hour(14), _at_hour(15), env.user_an)
    assert out.status == RB_APPROVED


def test_khong_TU_CHAN_chinh_minh(db, env):
    """Phiếu luôn chồng lên khoảng CŨ của chính nó — quên `exclude_id` là kẹt cứng."""
    obj = _held(db, env)
    #  Kéo nhích 30 phút: khoảng mới vẫn giao với khoảng cũ.
    out = service.reschedule(db, obj, 0, _at_hour(9, 30), _at_hour(10, 30), env.user_an)
    assert out.start_at == _at_hour(9, 30)


def test_doi_sang_PHONG_KHAC_dang_trong(db, env):
    """Kéo lên/xuống một hàng là đổi phòng — cùng một thao tác, cùng một đường."""
    obj = _held(db, env)
    out = service.reschedule(db, obj, env.big_room.id, _at_hour(9), _at_hour(10),
                             env.user_an)
    assert out.room_id == env.big_room.id


def test_phieu_NHAP_cung_doi_duoc(db, env):
    """Nháp không giữ phòng nên không đi qua khoá, nhưng vẫn phải dời được."""
    obj = _book(db, env)
    out = service.reschedule(db, obj, 0, _at_hour(15), _at_hour(16), env.user_an)
    assert out.status == RB_DRAFT
    assert out.start_at == _at_hour(15)


# ── Bị chặn ────────────────────────────────────────────────────────────────────

def test_doi_vao_khung_da_co_nguoi_thi_CHAN(db, env):
    """Vế quan trọng nhất: kéo KHÔNG được là cửa sau của chốt chặn trùng."""
    _held(db, env, start=_at_hour(14), end=_at_hour(15))
    obj = _held(db, env, start=_at_hour(9), end=_at_hour(10), user=env.user_binh)
    with pytest.raises(HTTPException) as err:
        service.reschedule(db, obj, 0, _at_hour(14), _at_hour(15), env.user_binh)
    assert "giữ từ" in err.value.detail


def test_ca_LIEN_NHAU_van_doi_duoc(db, env):
    """9–10h và 10–11h là hai cuộc nối tiếp, không phải trùng nhau."""
    _held(db, env, start=_at_hour(10), end=_at_hour(11))
    obj = _held(db, env, start=_at_hour(14), end=_at_hour(15), user=env.user_binh)
    out = service.reschedule(db, obj, 0, _at_hour(9), _at_hour(10), env.user_binh)
    assert out.start_at == _at_hour(9)


def test_phieu_DA_HUY_khong_doi_duoc(db, env):
    """Phiếu đã nhả phòng mà dời được thì sinh ra một cuộc họp không ai giữ chỗ."""
    obj = _held(db, env)
    obj.status = RB_CANCELLED
    db.commit()
    with pytest.raises(HTTPException):
        service.reschedule(db, obj, 0, _at_hour(14), _at_hour(15), env.user_an)


def test_phieu_BI_TU_CHOI_khong_doi_duoc(db, env):
    obj = _held(db, env)
    obj.status = RB_REJECTED
    db.commit()
    with pytest.raises(HTTPException):
        service.reschedule(db, obj, 0, _at_hour(14), _at_hour(15), env.user_an)


def test_gio_ket_thuc_khong_duoc_truoc_gio_bat_dau(db, env):
    """Kéo mép trái vượt qua mép phải — chuột làm được, dữ liệu thì không."""
    obj = _held(db, env)
    with pytest.raises(HTTPException):
        service.reschedule(db, obj, 0, _at_hour(15), _at_hour(14), env.user_an)


def test_keo_qua_24_gio_bi_chan(db, env):
    obj = _held(db, env)
    with pytest.raises(HTTPException):
        service.reschedule(db, obj, 0, _at_hour(9),
                           _at_hour(9).replace(day=12), env.user_an)


def test_doi_sang_phong_NHO_HON_suc_chua_thi_chan(db, env):
    """Kéo từ hội trường xuống phòng 8 chỗ với 20 người là sai thật, không phải sở thích."""
    obj = _held(db, env, room=env.big_room, attendee_count=20)
    with pytest.raises(HTTPException) as err:
        service.reschedule(db, obj, env.small_room.id, _at_hour(9), _at_hour(10),
                           env.user_an)
    assert "chứa được" in err.value.detail


def test_doi_sang_phong_NGUNG_DUNG_thi_chan(db, env):
    obj = _held(db, env)
    env.big_room.is_active = False
    db.commit()
    with pytest.raises(HTTPException):
        service.reschedule(db, obj, env.big_room.id, _at_hour(9), _at_hour(10),
                           env.user_an)


def test_phieu_van_o_CHO_DUYET_sau_khi_doi(db, env):
    obj = _held(db, env)
    assert service.reschedule(db, obj, 0, _at_hour(16), _at_hour(17),
                              env.user_an).status == RB_PENDING
