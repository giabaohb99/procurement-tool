"""duoc-CR-744 lượt d — 4 cột Hợp đồng và 2 cột Đặt xe trước không bấm xếp được (A3 soát dev 10/11/2026).

Mỗi cột xếp theo đúng chữ đang hiện trên bảng, ô trống xuống cuối, trùng giá trị giữ `id` giảm dần.
"""
from datetime import date, timedelta

from starlette.datastructures import QueryParams

from app.core.base_controller import apply_sort_from_request
from app.modules.contract.model import Contract
from app.modules.contract.sort_expressions import list_sort_allow as contract_allow
from app.modules.vehicle_booking.model import Driver, Vehicle, VehicleBooking
from app.modules.vehicle_booking.sort_expressions import list_sort_allow as booking_allow


class _Req:
    def __init__(self, **params):
        self.query_params = QueryParams(params)


def _codes(query):
    return [r.code for r in query.all()]


# ── Hợp đồng ─────────────────────────────────────────────────────────────────────────────
def _hd(db, code, **kw):
    db.add(Contract(code=code, **kw))
    db.flush()


def _sort_hd(db, key, direction):
    return apply_sort_from_request(db.query(Contract), Contract, _Req(sort_by=key, sort_dir=direction),
                                   default=Contract.id.desc(), allow=contract_allow())


def test_hop_dong_ben_ky_ket_xep_theo_ten_o_trong_cuoi(db):
    _hd(db, "HD-B", party_name="Bình Minh", party_type="supplier")
    _hd(db, "HD-TRONG", party_name="", party_type="customer")
    _hd(db, "HD-A", party_name="An Phú", party_type="other")
    assert _codes(_sort_hd(db, "party_type", "asc")) == ["HD-A", "HD-B", "HD-TRONG"]
    assert _codes(_sort_hd(db, "party_type", "desc")) == ["HD-B", "HD-A", "HD-TRONG"]


def test_hop_dong_loai_xep_theo_nhan_khong_theo_ma(db):
    # Theo mã: other < principle < purchase < service. Theo nhãn: dịch vụ < mua bán < nguyên tắc < Khác.
    for code, t in (("P", "purchase"), ("O", "other"), ("S", "service"), ("N", "principle")):
        _hd(db, code, contract_type=t)
    assert _codes(_sort_hd(db, "contract_type", "asc")) == ["S", "P", "N", "O"]
    assert _codes(_sort_hd(db, "contract_type", "desc")) == ["O", "N", "P", "S"]


def test_hop_dong_hieu_luc_xep_theo_tinh_trang_han(db):
    today = date.today()
    _hd(db, "HD-CON", end_date=(today + timedelta(days=200)).isoformat())
    _hd(db, "HD-KHONG", end_date="")
    _hd(db, "HD-HET", end_date=(today - timedelta(days=5)).isoformat())
    _hd(db, "HD-SAP", end_date=(today + timedelta(days=10)).isoformat())
    assert _codes(_sort_hd(db, "expiry", "asc")) == ["HD-HET", "HD-SAP", "HD-CON", "HD-KHONG"]
    assert _codes(_sort_hd(db, "expiry", "desc")) == ["HD-KHONG", "HD-CON", "HD-SAP", "HD-HET"]


def test_hop_dong_trang_thai_ky_chua_ky_truoc_khi_tang(db):
    _hd(db, "HD-KY", signed=True)
    _hd(db, "HD-CHUA", signed=False)
    assert _codes(_sort_hd(db, "signed", "asc")) == ["HD-CHUA", "HD-KY"]
    assert _codes(_sort_hd(db, "signed", "desc")) == ["HD-KY", "HD-CHUA"]


# ── Đặt xe ───────────────────────────────────────────────────────────────────────────────
def _xe(db, code, **kw):
    db.add(VehicleBooking(code=code, **kw))
    db.flush()


def _sort_xe(db, key, direction):
    return apply_sort_from_request(db.query(VehicleBooking), VehicleBooking,
                                   _Req(sort_by=key, sort_dir=direction),
                                   default=VehicleBooking.id.desc(), allow=booking_allow())


def test_dat_xe_lo_trinh_xep_theo_diem_di_roi_diem_den(db):
    _xe(db, "X-CT", start_location="Cần Thơ", end_location="Hậu Giang")
    _xe(db, "X-TRONG", start_location="", end_location="")
    _xe(db, "X-AG", start_location="An Giang", end_location="Cần Thơ")
    assert _codes(_sort_xe(db, "route", "asc")) == ["X-AG", "X-CT", "X-TRONG"]
    assert _codes(_sort_xe(db, "route", "desc")) == ["X-CT", "X-AG", "X-TRONG"]


def test_dat_xe_xe_tai_xe_xep_theo_chu_dau_o(db):
    v = Vehicle(license_plate="65A-123.45")
    d = Driver(name="Bảo")
    db.add_all([v, d])
    db.flush()
    _xe(db, "X-XE", assigned_vehicle_id=v.id, assigned_driver_id=d.id)     # hiện "65A-123.45 · Bảo"
    _xe(db, "X-TX", assigned_driver_id=d.id)                               # hiện "Bảo"
    _xe(db, "X-TU", is_self_drive=True, requester="Yến")                   # hiện "Yến (tự lái)"
    _xe(db, "X-CHUA")                                                      # chưa phân -> ô trống
    assert _codes(_sort_xe(db, "assigned", "asc")) == ["X-XE", "X-TX", "X-TU", "X-CHUA"]
    assert _codes(_sort_xe(db, "assigned", "desc")) == ["X-TU", "X-TX", "X-XE", "X-CHUA"]
