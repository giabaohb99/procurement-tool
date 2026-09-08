"""ĐẶT PHÒNG HỌP — duoc-CR-279.

Bài kiểm bám đúng thứ quyết định phân hệ này đúng hay sai: **một phòng, một
khung giờ, một phiếu**. Mọi thứ còn lại (tiêu đề, người dự, sức chứa) chỉ là ô
nhập; chặn trùng mới là thứ mà làm sai thì hai cuộc họp đứng chung một cửa.

Gọi thẳng tầng `service` thay vì dựng `TestClient`: bộ kiểm chạy trong container
không có `httpx`, và luật nghiệp vụ nằm trọn ở tầng đó.
"""
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.meeting_room import service
from app.modules.meeting_room.constants import (RB_APPROVED, RB_CANCELLED,
                                                RB_DRAFT, RB_PENDING,
                                                RB_REJECTED, RB_RETURNED)
from app.modules.meeting_room.model import MeetingRoom, RoomBooking
from app.modules.meeting_room.schema import (AttendeeItem, RoomBookingCreate,
                                             RoomBookingUpdate)

#  Một buổi sáng bất kỳ. Ngày CỐ ĐỊNH, không lấy "hôm nay": bài kiểm chạy lúc
#  23:30 mà cộng giờ là trôi sang hôm sau và khẳng định về ngày sẽ lệch.
MORNING = datetime(2026, 9, 10, 9, 0)


def _at_hour(h: int, m: int = 0) -> datetime:
    return MORNING.replace(hour=h, minute=m)


@pytest.fixture
def env(db):
    """Một pháp nhân, một phòng ban, hai nhân sự, hai phòng họp."""
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

    return SimpleNamespace(company=company, dept=dept, an=an, binh=binh,
                           small_room=small_room, big_room=big_room,
                           user_an=SimpleNamespace(id=1, employee_id=an.id),
                           user_binh=SimpleNamespace(id=2, employee_id=binh.id))


def _book(db, env, room=None, start=None, end=None, user=None, **kw) -> RoomBooking:
    payload = RoomBookingCreate(
        room_id=(room or env.small_room).id,
        title=kw.pop("title", "Họp giao ban"),
        start_at=start or _at_hour(9),
        end_at=end or _at_hour(10),
        **kw,
    )
    return service.create(db, payload, user or env.user_an)


def _submit_booking(db, env, obj, user=None) -> RoomBooking:
    #  Đúng hai nhịp mà controller chạy: kiểm rẻ trước, rồi GIỮ CHỖ qua khoá
    #  hàng phòng (`reserve_slot` — xem docstring về đường đua).
    service.prepare_submit(db, obj, user or env.user_an)
    return service.reserve_slot(db, obj, user or env.user_an)


# ── Lập phiếu ──────────────────────────────────────────────────────────────────

class TestCreate:
    def test_phieu_moi_luon_o_nhap(self, db, env):
        """Nháp chưa giữ phòng — giữ chỗ bắt đầu từ lúc gửi duyệt."""
        obj = _book(db, env)
        assert obj.status == RB_DRAFT
        assert obj.code.startswith("PH")

    def test_chep_phap_nhan_va_phong_ban_cua_NGUOI_DAT(self, db, env):
        #  Hai cột này là chiều lọc phạm vi. Không chép thì `apply_scope` không
        #  có gì để lọc và phiếu lọt ra ngoài tầm nhìn đúng của nó.
        obj = _book(db, env)
        assert obj.company_id == env.company.id
        assert obj.department_id == env.dept.id
        assert obj.requester_employee_id == env.an.id

    def test_dat_ho_nguoi_khac_thi_lay_phong_ban_cua_NGUOI_DUOC_DAT(self, db, env):
        """Thư ký đặt hộ sếp: phiếu phải thuộc về sếp, không thuộc thư ký."""
        obj = _book(db, env, user=env.user_an, requester_employee_id=env.binh.id)
        assert obj.requester_employee_id == env.binh.id
        assert obj.created_by == env.user_an.id

    def test_gio_ket_thuc_phai_sau_gio_bat_dau(self, db, env):
        with pytest.raises(HTTPException) as loi:
            _book(db, env, start=_at_hour(10), end=_at_hour(9))
        assert loi.value.status_code == 400

    def test_bang_nhau_cung_khong_duoc(self, db, env):
        """Cuộc họp dài 0 phút không giữ phòng được và cũng chẳng để làm gì."""
        with pytest.raises(HTTPException):
            _book(db, env, start=_at_hour(9), end=_at_hour(9))

    def test_chan_dat_qua_24_gio(self, db, env):
        #  Gần như luôn là gõ nhầm ngày, mà cái giá là phòng bị khóa cả tuần.
        with pytest.raises(HTTPException) as loi:
            _book(db, env, start=_at_hour(9), end=_at_hour(9) + timedelta(hours=30))
        assert "24 giờ" in loi.value.detail

    def test_qua_suc_chua_thi_chan(self, db, env):
        with pytest.raises(HTTPException) as loi:
            _book(db, env, room=env.small_room, attendee_count=20)
        assert "8 người" in loi.value.detail

    def test_suc_chua_0_la_CHUA_KHAI_nen_khong_chan(self, db, env):
        """`0` không có nghĩa là "không chứa được ai" — phòng chưa khai sức chứa."""
        env.small_room.capacity = 0
        db.commit()
        assert _book(db, env, attendee_count=100).id > 0

    def test_phong_ngung_dung_thi_khong_dat_duoc(self, db, env):
        env.small_room.is_active = False
        db.commit()
        with pytest.raises(HTTPException):
            _book(db, env)

    def test_moi_nhan_su_KHONG_TON_TAI_thi_bo_qua(self, db, env):
        #  Id bịa lọt vào thì danh sách hiện dòng «#999999» không tên, không ai
        #  gỡ được vì không biết nó là ai — dựng lại được bằng một lệnh gọi API
        #  thẳng ngày 04/09/2026.
        obj = _book(db, env, attendees=[AttendeeItem(employee_id=999999),
                                       AttendeeItem(employee_id=env.binh.id)])
        db.refresh(obj)
        assert [a.employee_id for a in obj.attendees] == [env.binh.id]

    def test_so_nguoi_du_AM_bi_chan_o_schema(self):
        #  Số âm lọt qua mọi chốt nghiệp vụ vì `check_capacity` chỉ so trần trên
        #  (-5 < sức chứa nên "hợp lệ"), nên phải chặn ngay ở lớp schema.
        with pytest.raises(ValidationError):
            RoomBookingCreate(room_id=1, title="x", start_at=_at_hour(9), end_at=_at_hour(10),
                              attendee_count=-5)

    def test_ghi_chu_qua_dai_bi_chan(self):
        """Cột là `Text` nên không có trần ở tầng dữ liệu — một lệnh gọi thẳng
        có thể nhồi hàng megabyte, và mỗi lần mở danh sách là kéo hết về máy."""
        with pytest.raises(ValidationError):
            RoomBookingCreate(room_id=1, title="x", start_at=_at_hour(9), end_at=_at_hour(10),
                              purpose="a" * 6000)

    def test_moi_trung_mot_nguoi_hai_lan_chi_ghi_mot_dong(self, db, env):
        #  Hai dòng là họ nhận hai thông báo giống hệt nhau.
        obj = _book(db, env, attendees=[AttendeeItem(employee_id=env.binh.id),
                                       AttendeeItem(employee_id=env.binh.id)])
        db.refresh(obj)
        assert len(obj.attendees) == 1


# ── Chặn trùng — luật lõi ──────────────────────────────────────────────────────

class TestConflict:
    def test_nhap_KHONG_giu_phong(self, db, env):
        """Hai bản nháp cùng giờ vẫn lưu được: nháp chưa giữ gì cả."""
        _book(db, env)
        assert _book(db, env).id > 0

    def test_gui_duyet_bi_chan_khi_phong_da_co_nguoi(self, db, env):
        _submit_booking(db, env, _book(db, env))
        later = _book(db, env, user=env.user_binh)
        with pytest.raises(HTTPException) as loi:
            _submit_booking(db, env, later, user=env.user_binh)
        #  Câu báo phải nói RÕ ai đang giữ và tới mấy giờ, không thì người bị
        #  chặn chỉ biết "không đặt được" rồi đi hỏi vòng quanh.
        assert "Phòng 301" in loi.value.detail
        assert "PH" in loi.value.detail

    def test_phieu_CHO_DUYET_da_giu_phong(self, db, env):
        """⚠️ Điểm dễ sai nhất. Bỏ *Chờ duyệt* ra khỏi `BLOCKING_STATUSES` thì hai
        người cùng gửi duyệt một khung giờ đều lọt, và người phát hiện ra lại là
        người duyệt — lúc đó cả hai đã báo lịch cho khách."""
        held = _submit_booking(db, env, _book(db, env))
        assert held.status == RB_PENDING
        assert service.find_conflict(db, env.small_room.id, _at_hour(9), _at_hour(10)) is not None

    def test_ca_lien_nhau_KHONG_tinh_la_trung(self, db, env):
        """Họp 9-10h và 10-11h là hai cuộc nối tiếp — đây là cách xếp lịch thật.
        Dùng `<=` khi so khoảng thì không ai đặt được ca liền sau."""
        _submit_booking(db, env, _book(db, env, start=_at_hour(9), end=_at_hour(10)))
        later = _book(db, env, start=_at_hour(10), end=_at_hour(11), user=env.user_binh)
        assert _submit_booking(db, env, later, user=env.user_binh).status == RB_PENDING

    def test_trung_mot_phan_van_la_trung(self, db, env):
        _submit_booking(db, env, _book(db, env, start=_at_hour(9), end=_at_hour(11)))
        later = _book(db, env, start=_at_hour(10), end=_at_hour(12), user=env.user_binh)
        with pytest.raises(HTTPException):
            _submit_booking(db, env, later, user=env.user_binh)

    def test_bao_TRUM_ca_khoang_cua_nguoi_khac_cung_la_trung(self, db, env):
        _submit_booking(db, env, _book(db, env, start=_at_hour(10), end=_at_hour(11)))
        later = _book(db, env, start=_at_hour(9), end=_at_hour(12), user=env.user_binh)
        with pytest.raises(HTTPException):
            _submit_booking(db, env, later, user=env.user_binh)

    def test_PHONG_KHAC_cung_gio_thi_khong_sao(self, db, env):
        _submit_booking(db, env, _book(db, env, room=env.small_room))
        other = _book(db, env, room=env.big_room, user=env.user_binh)
        assert _submit_booking(db, env, other, user=env.user_binh).status == RB_PENDING

    def test_phieu_da_HUY_nha_phong_ra(self, db, env):
        held = _submit_booking(db, env, _book(db, env))
        service.cancel(db, held, "Họp hoãn", env.user_an.id)
        later = _book(db, env, user=env.user_binh)
        assert _submit_booking(db, env, later, user=env.user_binh).status == RB_PENDING

    def test_khong_tu_chan_chinh_minh_khi_gui_lai(self, db, env):
        """Phiếu bị trả về, sửa rồi gửi lại: chính nó không được tính là kẻ chiếm chỗ."""
        obj = _submit_booking(db, env, _book(db, env))
        obj.status = RB_RETURNED
        db.commit()
        assert _submit_booking(db, env, obj).status == RB_PENDING


# ── Sửa · hủy ──────────────────────────────────────────────────────────────────

class TestEditAndCancel:
    def test_phieu_da_gui_duyet_thi_KHONG_sua_duoc(self, db, env):
        #  Sửa được nghĩa là đổi giờ xong đè lên phòng người khác, trong khi
        #  người duyệt đã ký cho một khung giờ khác.
        obj = _submit_booking(db, env, _book(db, env))
        with pytest.raises(HTTPException):
            service.update(db, obj, RoomBookingUpdate(title="Đổi tên"), env.user_an)

    def test_phieu_TRA_VE_sua_duoc(self, db, env):
        obj = _book(db, env)
        obj.status = RB_RETURNED
        db.commit()
        assert service.update(db, obj, RoomBookingUpdate(title="Sửa lại"),
                              env.user_an).title == "Sửa lại"

    def test_huy_hai_lan_khong_no(self, db, env):
        obj = _submit_booking(db, env, _book(db, env))
        service.cancel(db, obj, "Hoãn", env.user_an.id)
        assert service.cancel(db, obj, "Hoãn nữa", env.user_an.id).status == RB_CANCELLED

    def test_huy_phieu_DA_DUYET_van_duoc(self, db, env):
        """Họp hoãn là chuyện thường; không nhả thì phòng khóa suốt khung giờ đó."""
        obj = _submit_booking(db, env, _book(db, env))
        obj.status = RB_APPROVED
        db.commit()
        assert service.cancel(db, obj, "Hoãn", env.user_an.id).status == RB_CANCELLED

    def test_xoa_mem_chi_voi_phieu_chua_vao_luong(self, db, env):
        obj = _submit_booking(db, env, _book(db, env))
        with pytest.raises(HTTPException):
            service.soft_delete(db, obj, env.user_an)


# ── Gửi duyệt ──────────────────────────────────────────────────────────────────

class TestSubmit:
    def test_thieu_tieu_de_thi_chan_o_buoc_GUI(self, db, env):
        """Chốt "nhập đủ" đặt ở lúc gửi, không phải lúc lưu nháp — người duyệt mở
        phiếu ra mà không có nội dung cuộc họp thì họ duyệt cái gì."""
        obj = _book(db, env)
        obj.title = "   "
        db.commit()
        with pytest.raises(HTTPException) as loi:
            service.prepare_submit(db, obj, env.user_an)
        assert "Nội dung cuộc họp" in loi.value.detail

    def test_gui_hai_lan_thi_chan(self, db, env):
        obj = _submit_booking(db, env, _book(db, env))
        with pytest.raises(HTTPException):
            service.prepare_submit(db, obj, env.user_an)


# ── Phòng trống ────────────────────────────────────────────────────────────────

class TestAvailability:
    def test_liet_ke_ca_phong_ban_kem_phieu_dang_giu(self, db, env):
        """Không lọc bỏ phòng bận: người đặt cần biết "bận vì phiếu nào, tới mấy
        giờ" để đi xin hoặc dời, chứ không phải một danh sách ngắn đi khó hiểu."""
        _submit_booking(db, env, _book(db, env, room=env.small_room))
        rows = service.list_availability(db, _at_hour(9), _at_hour(10), env.company.id)

        by_code = {r["room_code"]: r for r in rows}
        assert by_code["P301"]["available"] is False
        assert len(by_code["P301"]["bookings"]) == 1
        assert by_code["P501"]["available"] is True

    def test_lay_ca_phong_DUNG_CHUNG_moi_phap_nhan(self, db, env):
        """`company_id = 0` nghĩa là phòng của toà nhà chung — lọc thẳng theo
        pháp nhân thì cắt mất đúng những phòng ấy (cùng bẫy với lịch ngày lễ)."""
        db.add(MeetingRoom(code="PC", name="Phòng chung", company_id=0,
                           is_active=True, created_by=1, updated_by=1))
        db.commit()
        codes = {r["room_code"] for r in service.list_availability(
            db, _at_hour(9), _at_hour(10), env.company.id)}
        assert "PC" in codes

    def test_phong_ngung_dung_khong_hien(self, db, env):
        env.big_room.is_active = False
        db.commit()
        codes = {r["room_code"] for r in service.list_availability(
            db, _at_hour(9), _at_hour(10), env.company.id)}
        assert "P501" not in codes

    def test_phieu_bi_tu_choi_khong_lam_phong_ban(self, db, env):
        obj = _submit_booking(db, env, _book(db, env))
        obj.status = RB_REJECTED
        db.commit()
        rows = service.list_availability(db, _at_hour(9), _at_hour(10), env.company.id)
        assert next(r for r in rows if r["room_code"] == "P301")["available"] is True
