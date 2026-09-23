"""Đặt xe — LÝ DO đóng phiếu (hủy / bị từ chối) đọc ra từ nhật ký thao tác.

Lý do không có cột riêng trên `tab_vehicle_booking`: nó nằm trong câu của dòng
nhật ký. `service.close_reasons` rút câu đó ra cho màn Tiến trình xử lý và thẻ
hover trên lịch.

⚠️ Hai đường ghi nhật ký cho hai khuôn câu khác nhau — controller ghép tiền tố
"… — Lý do: …", còn bộ máy duyệt nhiều bước ghi thẳng câu lý do. Bài kiểm ghim
cả hai, vì bỏ sót khuôn thứ hai là mọi phiếu đi qua luồng nhiều bước mất lý do
mà không có gì báo.
"""
from app.core.audit import record
from app.modules.vehicle_booking import model as m
from app.modules.vehicle_booking.service import close_reasons


def _booking(db, code: str, status: int):
    obj = m.VehicleBooking(code=code, status=status)
    db.add(obj)
    db.flush()
    return obj


def test_reason_from_controller_log_shape(db):
    """Khuôn của controller: 'Từ chối yêu cầu — Lý do: …'."""
    obj = _booking(db, 'DX901', m.BK_REJECTED)
    record(db, 1, 'vehicle_booking', obj.id, 'cancel', 'Từ chối yêu cầu — Lý do: Xe hỏng đột xuất')

    assert close_reasons(db, [obj]) == {obj.id: 'Xe hỏng đột xuất'}


def test_reason_from_approval_bridge_log_shape(db):
    """Khuôn của bộ máy duyệt: ghi THẲNG câu lý do, không tiền tố."""
    obj = _booking(db, 'DX902', m.BK_REJECTED)
    record(db, 1, 'vehicle_booking', obj.id, 'cancel', 'Không đúng mục đích công tác')

    assert close_reasons(db, [obj]) == {obj.id: 'Không đúng mục đích công tác'}


def test_reason_from_withdraw_log(db):
    """Phiếu ĐÃ HỦY của app cũ mang mã `withdraw` ('Rút yêu cầu — Lý do: …')."""
    obj = _booking(db, 'DX903', m.BK_CANCELLED)
    record(db, 1, 'vehicle_booking', obj.id, 'withdraw', 'Rút yêu cầu DX903 — Lý do: Khách hoãn lịch')

    assert close_reasons(db, [obj]) == {obj.id: 'Khách hoãn lịch'}


def test_latest_close_log_wins(db):
    """Nhiều dòng đóng thì dòng MỚI NHẤT là câu đang đúng."""
    obj = _booking(db, 'DX904', m.BK_CANCELLED)
    record(db, 1, 'vehicle_booking', obj.id, 'cancel', 'Từ chối yêu cầu — Lý do: Lý do cũ')
    record(db, 1, 'vehicle_booking', obj.id, 'withdraw', 'Rút yêu cầu — Lý do: Lý do mới')

    assert close_reasons(db, [obj]) == {obj.id: 'Lý do mới'}


def test_placeholder_reason_counts_as_empty(db):
    """Câu mặc định của bộ máy duyệt KHÔNG phải lý do — để giao diện nói
    «Không ghi lý do» thay vì lặp lại nhãn trạng thái."""
    obj = _booking(db, 'DX905', m.BK_REJECTED)
    record(db, 1, 'vehicle_booking', obj.id, 'cancel', 'Bị từ chối')

    assert close_reasons(db, [obj]) == {}


def test_no_log_no_reason(db):
    """Phiếu nạp từ tệp Excel hệ cũ không có dòng nhật ký nào."""
    obj = _booking(db, 'DX906', m.BK_CANCELLED)

    assert close_reasons(db, [obj]) == {}


def test_only_closed_statuses_are_queried(db):
    """Phiếu đang chạy KHÔNG lấy lý do, dù nhật ký có dòng `cancel` cũ.

    Phiếu bị từ chối rồi được mở lại thì câu từ chối cũ vẫn nằm trong nhật ký;
    bày nó ra cạnh một phiếu đang chờ duyệt là nói sai trạng thái.
    """
    obj = _booking(db, 'DX907', m.BK_PENDING)
    record(db, 1, 'vehicle_booking', obj.id, 'cancel', 'Từ chối yêu cầu — Lý do: Lần trước bị từ chối')

    assert close_reasons(db, [obj]) == {}


def test_batch_reads_many_bookings_in_one_pass(db):
    """Gọi theo LÔ: màn lịch tháng có thể có vài trăm phiếu một lượt."""
    a = _booking(db, 'DX908', m.BK_CANCELLED)
    b = _booking(db, 'DX909', m.BK_REJECTED)
    c = _booking(db, 'DX910', m.BK_COMPLETED)
    record(db, 1, 'vehicle_booking', a.id, 'withdraw', 'Rút yêu cầu — Lý do: Hoãn chuyến')
    record(db, 1, 'vehicle_booking', b.id, 'cancel', 'Từ chối yêu cầu — Lý do: Sai lộ trình')

    assert close_reasons(db, [a, b, c]) == {a.id: 'Hoãn chuyến', b.id: 'Sai lộ trình'}


def test_empty_input_does_not_touch_db(db):
    assert close_reasons(db, []) == {}
