"""bao-CR-596 — chiều ERP -> app đặt xe cũ (P3). Bản dựng: doc/dong-bo-dat-xe-duyet-dau/p3-erp-sang-app-cu.md.

Canh bốn thứ: ảnh chụp dịch đúng tên trường và đúng trạng thái app cũ (đi sang rồi về vẫn ra
y như cũ); gửi có sổ, có van, không gửi lại thứ không đổi; phiếu ERP được app cũ tạo thì ghi
ngược khóa mà không đẻ thêm lượt gửi; bộ nghe ORM chỉ giao việc khi công tắc bật, đã commit,
và không phải đang xử tín hiệu nhận về.
"""
import json
from types import SimpleNamespace

import pytest

from app.modules.legacy_datxe import outbound, outbound_listener
from app.modules.legacy_datxe.builder import (
    BOOKING_STATUS_FROM_LEGACY,
    DRIVER_STATUS_FROM_LEGACY,
    SEAL_STATUS_FROM_LEGACY,
)
from app.modules.legacy_datxe.outbound import (
    BOOKING_STATUS_TO_LEGACY,
    DRIVER_STATUS_TO_LEGACY,
    SEAL_STATUS_TO_LEGACY,
    VALVE_MAX_PER_HOUR,
    build_payload,
    push_outbound,
)
from app.modules.legacy_datxe.outbound_tasks import _stuck_targets
from app.modules.seal_request.model import (
    SEAL_APPROVED,
    SEAL_COMPLETED,
    SealRequest,
    SealRequestCompany,
    SealType,
)
from app.modules.sync_log.constants import SyncDirection, SyncStatus
from app.modules.sync_log.model import SyncLog
from app.modules.sync_log.service import suppress_outbound
from app.modules.vehicle_booking.model import (
    BK_DISPATCHED,
    BK_DRAFT,
    BK_PENDING,
    DRV_ACCEPTED,
    TYPE_CAR,
    Driver,
    Vehicle,
    VehicleBooking,
)


class _Resp:
    def __init__(self, status=200, data=None, text="ok"):
        self.status_code = status
        self._data = data or {}
        self.text = text

    def json(self):
        return {"success": 200 <= self.status_code < 300, "data": self._data}


def _sender(resp=None):
    sent = []

    def poster(body):
        sent.append(json.loads(body))
        return resp or _Resp(data={"legacy_id": "", "status": "updated"})

    return sent, poster


def _push(db, entity, row_id, poster):
    return push_outbound(db, entity, row_id, check_switch=False, poster=poster)


@pytest.fixture
def fleet(db, seed):
    vehicle = Vehicle(license_plate="51A-123.45", model="Ford Transit", type="16 chỗ",
                      legacy_id="veh_key_1", created_by=1, updated_by=1)
    driver = Driver(name="Lê Vỹ Khang", phone="0923992996", legacy_id="drv_key_1",
                    created_by=1, updated_by=1)
    db.add_all([vehicle, driver])
    db.commit()
    return SimpleNamespace(vehicle_id=vehicle.id, driver_id=driver.id)


def _booking(db, seed, **kw):
    row = VehicleBooking(
        code=kw.pop("code", "DX000901"), request_type=TYPE_CAR, purpose="Đi gặp NCC",
        start_location="Cần Thơ", end_location="Sóc Trăng",
        start_time="2026-10-06T08:00", end_time="2026-10-06T17:00",
        passenger_count=3, attendees="A, B", contact_phone="0901", is_round_trip=True,
        requester="Người YC", requester_id=seed.u_req_id, company_id=seed.company_id,
        department_id=seed.dept_id, status=kw.pop("status", BK_PENDING),
        note="Ghi chú thật\n[App cũ] contact_phone: 0901 - chị A",
        created_by=seed.u_req_id, updated_by=seed.u_req_id, **kw)
    db.add(row)
    db.commit()
    return row


# ── Ánh xạ ─────────────────────────────────────────────────────────────────────

def test_status_maps_are_exact_inverse_of_inbound():
    """Đi sang rồi đồng bộ về phải ra y như cũ: bảng gửi là bảng ngược của bảng nhận."""
    for erp, text in BOOKING_STATUS_TO_LEGACY.items():
        assert BOOKING_STATUS_FROM_LEGACY[text] == erp
    for erp, text in SEAL_STATUS_TO_LEGACY.items():
        assert SEAL_STATUS_FROM_LEGACY[text] == erp
    for erp, text in DRIVER_STATUS_TO_LEGACY.items():
        if text in DRIVER_STATUS_FROM_LEGACY:
            assert DRIVER_STATUS_FROM_LEGACY[text] == erp


def test_booking_payload_uses_legacy_field_names_and_dispatch_keys(db, seed, fleet):
    row = _booking(db, seed, status=BK_DISPATCHED, assigned_vehicle_id=fleet.vehicle_id,
                   assigned_driver_id=fleet.driver_id, driver_status=DRV_ACCEPTED,
                   dispatched_at="2026-10-06T01:00", distance_km=42.5, cost=350000)

    payload = build_payload(db, "vehicle_booking", row)
    data = payload["data"]

    assert payload["erp_id"] == row.id and payload["erp_code"] == "DX000901"
    assert data["type"] == "CAR_BOOKING" and data["status"] == "dispatched"
    assert data["approval"]["outcome"] == "approved"
    details = data["details"]
    assert details["startLocation"] == "Cần Thơ" and details["isRoundTrip"] is True
    #  start_time là giờ Việt Nam: 08:00 +07 = 01:00 UTC.
    assert details["startTime"] == 1791248400000
    #  Dòng do chiều NHẬN chèn vào không được gửi ngược sang.
    assert details["notes"] == "Ghi chú thật"
    dispatch = data["dispatch"]
    #  Tài xế app cũ lọc chuyến theo KHÓA này — thiếu là tài xế không thấy chuyến.
    assert dispatch["assignedDriverId"] == "drv_key_1"
    assert dispatch["assignedVehicleId"] == "veh_key_1"
    assert dispatch["vehicle"]["license_plate"] == "51A-123.45"
    assert dispatch["driver"]["name"] == "Lê Vỹ Khang"
    assert dispatch["driverStatus"] == "accepted"
    #  dispatched_at là mốc máy chủ, UTC.
    assert dispatch["dispatchedAt"] == 1791248400000
    assert dispatch["distanceKm"] == 42.5 and dispatch["cost"] == 350000


def test_seal_payload_lists_every_company_and_seal_type_label(db, seed):
    seal_type = SealType(name="Phê duyệt dấu", created_by=1, updated_by=1)
    db.add(seal_type)
    db.commit()
    from app.modules.company.model import Company

    company = db.get(Company, seed.company_id)
    company.legacy_id = "brand_key_1"
    row = SealRequest(code="DD000901", title="Hợp đồng", purpose="Đóng dấu HĐ",
                      seal_type_id=seal_type.id, company_id=seed.company_id,
                      department_id=seed.dept_id, requester_id=seed.u_req_id,
                      status=SEAL_COMPLETED, completed_at="2026-10-06T02:00",
                      created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(row)
    db.commit()
    db.add(SealRequestCompany(seal_request_id=row.id, company_id=seed.company_id,
                              created_by=1, updated_by=1))
    db.commit()

    data = build_payload(db, "seal_request", row)["data"]

    assert data["type"] == "SEAL_REQUEST" and data["status"] == "completed"
    assert data["details"]["brandId"] == ["brand_key_1"]
    assert data["details"]["sealTypeId"] == "Phê duyệt dấu"
    assert data["seal"]["completed_at"] == 1791252000000


# ── Gửi ───────────────────────────────────────────────────────────────────────

def test_erp_created_booking_gets_legacy_key_without_triggering_another_push(db, seed, monkeypatch):
    row = _booking(db, seed)
    sent, poster = _sender(_Resp(data={"legacy_id": "-NewKey123", "status": "created"}))
    enqueued = []
    monkeypatch.setattr(outbound_listener, "_after_commit",
                        lambda session: enqueued.append(session.info.get("datxe_outbound_ids")))

    result = _push(db, "vehicle_booking", row.id, poster)
    db.refresh(row)

    assert result["status"] == "sent"
    assert row.legacy_id == "-NewKey123"
    assert sent[0]["legacy_id"] == "" and sent[0]["event_id"]
    log = db.query(SyncLog).filter(SyncLog.direction == int(SyncDirection.OUTBOUND)).one()
    assert log.status == int(SyncStatus.SUCCESS) and log.legacy_id == "-NewKey123"
    assert log.local_id == row.id


def test_unchanged_snapshot_is_not_sent_twice(db, seed):
    row = _booking(db, seed)
    sent, poster = _sender()

    assert _push(db, "vehicle_booking", row.id, poster)["status"] == "sent"
    assert _push(db, "vehicle_booking", row.id, poster)["status"] == "unchanged"
    assert len(sent) == 1

    row.status = BK_DISPATCHED
    db.commit()
    assert _push(db, "vehicle_booking", row.id, poster)["status"] == "sent"
    assert len(sent) == 2


def test_draft_is_never_sent(db, seed):
    row = _booking(db, seed, status=BK_DRAFT)
    sent, poster = _sender()

    assert _push(db, "vehicle_booking", row.id, poster)["status"] == "not_sendable"
    assert sent == []


def test_failed_send_is_logged_and_picked_up_for_retry(db, seed):
    row = _booking(db, seed)
    _, poster = _sender(_Resp(status=503, text="Đường nhận đang tắt"))

    assert _push(db, "vehicle_booking", row.id, poster)["status"] == "failed"
    log = db.query(SyncLog).one()
    assert log.status == int(SyncStatus.FAILED)
    assert "503" in log.message
    assert _stuck_targets(db) == [("vehicle_booking", row.id)]

    _, ok = _sender()
    assert _push(db, "vehicle_booking", row.id, ok)["status"] == "sent"
    assert _stuck_targets(db) == []


def test_valve_stops_a_runaway_ticket(db, seed):
    row = _booking(db, seed)
    sent, poster = _sender()
    for i in range(VALVE_MAX_PER_HOUR):
        row.purpose = f"đổi lần {i}"
        db.commit()
        _push(db, "vehicle_booking", row.id, poster)
    row.purpose = "lần quá van"
    db.commit()

    assert _push(db, "vehicle_booking", row.id, poster)["status"] == "valve"
    assert len(sent) == VALVE_MAX_PER_HOUR
    last = db.query(SyncLog).order_by(SyncLog.id.desc()).first()
    assert last.status == int(SyncStatus.FAILED) and "Van chặn" in last.message


def test_switch_off_sends_nothing(db, seed):
    row = _booking(db, seed)
    sent, poster = _sender()

    assert push_outbound(db, "vehicle_booking", row.id, poster=poster)["status"] == "off"
    assert sent == [] and db.query(SyncLog).count() == 0


# ── Bộ nghe ORM ──────────────────────────────────────────────────────────────

@pytest.fixture
def queue(monkeypatch):
    calls = []
    monkeypatch.setattr(outbound, "is_outbound_enabled", lambda: True)
    from app.core import celery_app as celery_module

    monkeypatch.setattr(celery_module.celery_app, "send_task",
                        lambda name, args=None, **kw: calls.append((name, tuple(args or ()))))
    return calls


def test_listener_enqueues_after_commit_when_switch_on(db, seed, queue):
    row = _booking(db, seed)
    queue.clear()

    row.status = BK_DISPATCHED
    db.commit()

    assert queue == [("datxe.push_outbound", ("vehicle_booking", row.id))]


def test_listener_ignores_inbound_writes_and_bookkeeping_columns(db, seed, queue):
    row = _booking(db, seed)
    queue.clear()

    with suppress_outbound():
        row.status = BK_DISPATCHED
        db.commit()
    row.updated_by = 999
    db.commit()

    assert queue == []


def test_listener_drops_rolled_back_changes(db, seed, queue):
    row = _booking(db, seed)
    queue.clear()

    row.status = BK_DISPATCHED
    db.flush()
    db.rollback()

    assert queue == []


def test_listener_does_nothing_when_switch_off(db, seed, monkeypatch):
    calls = []
    from app.core import celery_app as celery_module

    monkeypatch.setattr(celery_module.celery_app, "send_task",
                        lambda *a, **kw: calls.append(a))
    row = _booking(db, seed)
    row.status = SEAL_APPROVED
    db.commit()

    assert calls == []
