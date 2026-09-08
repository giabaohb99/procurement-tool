"""Nhãn trạng thái CHUNG của phiếu đặt xe có tính BƯỚC TÀI XẾ khi đã điều phối.

Yêu cầu KH 07/09/2026: đổi tên "Điều phối" → "Đã điều phối"; khi đã điều phối mà
tài xế "Đã nhận" thì hiện "Tài xế đã nhận", "Đang đi" thì hiện "Đang đi". Giữ đồng
bộ với `bookingStatusLabel` ở frontend (types/vehicle-booking.ts).
"""
from types import SimpleNamespace

from app.modules.vehicle_booking import model as m
from app.modules.vehicle_booking.service import _display_status_label


def _bk(status, driver_status):
    return SimpleNamespace(status=status, driver_status=driver_status)


def test_dispatched_label_renamed_to_da_dieu_phoi():
    #  Chưa có bước tài xế (chờ tài xế) -> nhãn phiếu "Đã điều phối" (không còn "Điều phối").
    assert _display_status_label(_bk(m.BK_DISPATCHED, m.DRV_WAITING)) == "Đã điều phối"
    assert m.BOOKING_STATUS_LABELS[m.BK_DISPATCHED] == "Đã điều phối"


def test_dispatched_reflects_driver_stage():
    assert _display_status_label(_bk(m.BK_DISPATCHED, m.DRV_ACCEPTED)) == "Tài xế đã nhận"
    assert _display_status_label(_bk(m.BK_DISPATCHED, m.DRV_ONGOING)) == "Đang đi"
    #  Tài xế từ chối khi đã điều phối → chờ điều phối viên phân lại.
    assert _display_status_label(_bk(m.BK_DISPATCHED, m.DRV_REJECTED)) == "Điều phối lại"


def test_other_statuses_use_plain_booking_label():
    #  Ngoài bước điều phối, bước tài xế KHÔNG được lấn nhãn phiếu.
    assert _display_status_label(_bk(m.BK_PENDING, m.DRV_NONE)) == "Chờ duyệt"
    assert _display_status_label(_bk(m.BK_COMPLETED, m.DRV_COMPLETED)) == "Hoàn thành"
    assert _display_status_label(_bk(m.BK_DRAFT, m.DRV_NONE)) == "Nháp"
