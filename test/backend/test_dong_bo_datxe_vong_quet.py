"""Hai vòng chạy nền của app đặt xe cũ: lưới an toàn + chạy lại phiếu lỗi.

Kiểm ở tầng nghiệp vụ (`tasks.pull_updated` / `tasks.retry_pending`), KHÔNG kiểm
qua Celery: vỏ Celery chỉ mở/đóng dòng lượt chạy, còn thứ dễ sai là con trỏ và
bộ đếm. Firebase thay bằng một hàm `fetch` giả.
"""
import json

import pytest

from app.core.config import settings
from app.modules.legacy_datxe import resolver as resolver_mod
from app.modules.legacy_datxe import tasks
from app.modules.sync_log.constants import SyncGrain, SyncStatus
from app.modules.sync_log.model import SyncLog
from app.modules.sync_log.registry import SOURCE_DATXE
from app.modules.sync_log.service import clone_for_retry, finish_run, open_run
from app.modules.vehicle_booking.model import VehicleBooking

#: Mốc sửa phiếu. Phải là giờ HIỆN TẠI chứ không phải một số viết cứng: lượt đầu
#: chỉ nhìn lại `FIRST_RUN_LOOKBACK_HOURS` giờ, số cũ nằm ngoài cửa sổ đó.
STAMP = tasks.now_ms()


@pytest.fixture(autouse=True)
def bat_dong_bo(monkeypatch):
    """Bật nguồn + giả vờ đã khai khóa đọc Firebase, và chặn mọi đường ra mạng."""
    monkeypatch.setattr(settings, "SYNC_DATXE_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "LEGACY_FIREBASE_DB_URL", "https://vi-du.firebaseio.com",
                        raising=False)
    monkeypatch.setattr(settings, "LEGACY_FIREBASE_SECRET", "khoa-thu", raising=False)
    monkeypatch.setattr(resolver_mod, "read_node", lambda path: None)


def booking_node(updated_at: int = STAMP, **details) -> dict:
    node = {
        "type": "CAR_BOOKING",
        "createdAt": STAMP,
        "updatedAt": updated_at,
        "createdBy": "uid_bat_ky",
        "approval": {"overallStatus": "pending_approval"},
        "details": {"purpose": "Đi họp", "startLocation": "Văn phòng",
                    "endLocation": "Nhà khách"},
    }
    node["details"].update(details)
    return node


def fetcher(nodes: dict, seen: dict | None = None):
    """Hàm `fetch` giả, ghi lại tham số để bài kiểm soi con trỏ."""
    def fetch(path, *, order_by, start_at, limit=0):
        if seen is not None:
            seen.update({"path": path, "order_by": order_by, "start_at": start_at,
                         "limit": limit})
        return {k: v for k, v in nodes.items() if tasks._updated_at(v) >= start_at}
    return fetch


# ---------------------------------------------------------------------------
# Vòng kéo phiếu đã sửa
# ---------------------------------------------------------------------------

def test_keo_phieu_moi_thi_tao_phieu_va_dem_dung(db):
    stats = tasks.pull_updated(db, fetch=fetcher({"req_1": booking_node()}))

    assert db.query(VehicleBooking).count() == 1
    assert (stats["fetched"], stats["written"], stats["skipped"]) == (1, 1, 0)
    assert stats["cursor_to"] == str(STAMP)


def test_keo_lai_ngay_phieu_do_thi_khong_ghi_them_dong_so_nao(db):
    nodes = {"req_1": booking_node()}
    tasks.pull_updated(db, fetch=fetcher(nodes))
    truoc = db.query(SyncLog).count()

    stats = tasks.pull_updated(db, fetch=fetcher(nodes))

    #  Nội dung y hệt -> `is_unchanged` chặn, không dòng sổ nào sinh thêm.
    assert db.query(SyncLog).count() == truoc
    assert (stats["fetched"], stats["written"], stats["skipped"]) == (1, 0, 1)


def test_luot_dau_chua_co_con_tro_thi_nhin_lai_dung_cua_so_mac_dinh(db):
    seen: dict = {}
    tasks.pull_updated(db, fetch=fetcher({}, seen))

    lui = tasks.now_ms() - seen["start_at"]
    mot_gio = 3600 * 1000
    assert tasks.FIRST_RUN_LOOKBACK_HOURS * mot_gio <= lui <= (tasks.FIRST_RUN_LOOKBACK_HOURS + 1) * mot_gio
    assert seen["path"] == tasks.NODE_REQUESTS
    assert seen["order_by"] == tasks.CURSOR_FIELD
    assert seen["limit"] == tasks.MAX_RECORDS_PER_RUN


def test_luot_sau_bat_dau_dung_tai_con_tro_luot_truoc(db):
    run = open_run(db, SOURCE_DATXE, tasks.JOB_PULL)
    finish_run(db, run, SyncStatus.SUCCESS, cursor_to=str(STAMP))

    seen: dict = {}
    tasks.pull_updated(db, fetch=fetcher({}, seen))

    #  BAO GỒM chính mốc đó: hai phiếu sửa cùng một mili-giây thì không được
    #  phép mất phiếu nào.
    assert seen["start_at"] == STAMP


def test_con_tro_cua_luot_hong_khong_duoc_tinh(db):
    xong = open_run(db, SOURCE_DATXE, tasks.JOB_PULL)
    finish_run(db, xong, SyncStatus.SUCCESS, cursor_to=str(STAMP))
    hong = open_run(db, SOURCE_DATXE, tasks.JOB_PULL)
    finish_run(db, hong, SyncStatus.FAILED, cursor_to=str(STAMP + 99_000))

    seen: dict = {}
    tasks.pull_updated(db, fetch=fetcher({}, seen))

    assert seen["start_at"] == STAMP


def test_loai_phieu_la_thi_bo_qua_chu_khong_giet_ca_luot(db):
    nodes = {
        "req_la": {"type": "MEETING_ROOM", "updatedAt": STAMP + 1},
        "req_1": booking_node(STAMP + 2),
    }
    stats = tasks.pull_updated(db, fetch=fetcher(nodes))

    assert stats["unknown_type"] == 1
    assert stats["written"] == 1
    assert db.query(VehicleBooking).count() == 1
    #  Con trỏ vẫn phải đi qua phiếu lạ, không thì lượt sau kéo lại mãi.
    assert stats["cursor_to"] == str(STAMP + 2)


def test_phieu_hong_khong_chan_phieu_sau_no(db, monkeypatch):
    nodes = {"req_hong": booking_node(STAMP + 1), "req_1": booking_node(STAMP + 2)}
    goc = tasks.apply_legacy_record

    def noi_do(db_, *, node, legacy_id, **kw):
        if legacy_id == "req_hong":
            raise ValueError("Thiếu khóa app cũ (legacy_id)")
        return goc(db_, node=node, legacy_id=legacy_id, **kw)

    monkeypatch.setattr(tasks, "apply_legacy_record", noi_do)
    stats = tasks.pull_updated(db, fetch=fetcher(nodes))

    assert stats["written"] == 1
    assert db.query(VehicleBooking).count() == 1


def test_nguon_dang_tat_thi_dung_som_khong_goi_ra_ngoai(db, monkeypatch):
    monkeypatch.setattr(settings, "SYNC_DATXE_ENABLED", False, raising=False)

    def khong_duoc_goi(*a, **kw):
        raise AssertionError("Nguồn đang tắt mà vẫn đi hỏi Firebase")

    with pytest.raises(tasks.LegacySyncOff):
        tasks.pull_updated(db, fetch=khong_duoc_goi)


def test_chua_khai_khoa_firebase_thi_cung_dung_som(db, monkeypatch):
    monkeypatch.setattr(settings, "LEGACY_FIREBASE_SECRET", "", raising=False)

    with pytest.raises(tasks.LegacySyncOff):
        tasks.pull_updated(db, fetch=lambda *a, **kw: {})


# ---------------------------------------------------------------------------
# Vòng chạy lại
# ---------------------------------------------------------------------------

def test_dong_cho_do_nut_chay_lai_sinh_ra_thi_duoc_nhat(db):
    """Nút "Chạy lại" chỉ đẻ một dòng *chờ* rồi thả đó — task này phải nhặt."""
    tasks.pull_updated(db, fetch=fetcher({"req_1": booking_node()}))
    xong = db.query(SyncLog).filter(SyncLog.grain == int(SyncGrain.RECORD)).one()
    moi = clone_for_retry(db, xong)

    stats = tasks.retry_pending(db)

    db.refresh(moi)
    assert stats["fetched"] == 1
    #  Nội dung y hệt lần chạy trước nên kết cục đúng là *bỏ qua* — thứ phải
    #  chốt ở đây là dòng KHÔNG còn nằm im ở trạng thái *chờ*.
    assert moi.status == int(SyncStatus.SKIPPED)
    assert moi.attempt_count == 1
    #  Chạy lại TẠI CHỖ: một sự kiện vẫn một dòng, chỉ tăng số lần thử.
    assert db.query(SyncLog).filter(SyncLog.grain == int(SyncGrain.RECORD)).count() == 2


def test_chay_lai_dung_noi_dung_da_luu_chu_khong_hoi_firebase(db):
    entry = SyncLog(source=SOURCE_DATXE, grain=int(SyncGrain.RECORD),
                    entity="vehicle_booking", legacy_id="req_9",
                    status=int(SyncStatus.PENDING), event_id="evt_9",
                    payload=json.dumps(booking_node(), ensure_ascii=False))
    db.add(entry)
    db.commit()

    stats = tasks.retry_pending(db)

    db.refresh(entry)
    assert stats["written"] == 1
    assert entry.status == int(SyncStatus.SUCCESS)
    assert db.query(VehicleBooking).count() == 1


def test_dong_thu_qua_nhieu_lan_thi_thoi_khong_nhat_nua(db):
    entry = SyncLog(source=SOURCE_DATXE, grain=int(SyncGrain.RECORD),
                    entity="vehicle_booking", legacy_id="req_9",
                    status=int(SyncStatus.FAILED), event_id="evt_9",
                    attempt_count=tasks.MAX_ATTEMPTS,
                    payload=json.dumps(booking_node(), ensure_ascii=False))
    db.add(entry)
    db.commit()

    stats = tasks.retry_pending(db)

    assert stats["fetched"] == 0
    assert db.query(VehicleBooking).count() == 0


def test_noi_dung_da_luu_hong_thi_dong_dong_lai_chu_dung_quay_vong(db):
    entry = SyncLog(source=SOURCE_DATXE, grain=int(SyncGrain.RECORD),
                    entity="vehicle_booking", legacy_id="req_9",
                    status=int(SyncStatus.PENDING), event_id="evt_9",
                    payload="{khong-phai-json")
    db.add(entry)
    db.commit()

    stats = tasks.retry_pending(db)

    db.refresh(entry)
    assert stats["failed"] == 1
    assert entry.status == int(SyncStatus.FAILED)
    #  Lần sau không nhặt lại nữa vì đã lên ba lần thử? Chưa — nó vẫn còn dưới
    #  trần, nhưng dòng đã ở trạng thái *lỗi* với câu nói rõ, người soát sẽ thấy.
    assert "Không đọc lại được" in entry.message


def test_dong_cua_he_nguon_khac_thi_khong_dung_toi(db):
    entry = SyncLog(source="pos365", grain=int(SyncGrain.RECORD),
                    entity="pos_order", legacy_id="don_1",
                    status=int(SyncStatus.PENDING), event_id="evt_pos",
                    payload=json.dumps({"type": "CAR_BOOKING"}, ensure_ascii=False))
    db.add(entry)
    db.commit()

    stats = tasks.retry_pending(db)

    db.refresh(entry)
    assert stats["fetched"] == 0
    assert entry.status == int(SyncStatus.PENDING)


# ---------------------------------------------------------------------------
# Khai báo trong danh bạ nguồn
# ---------------------------------------------------------------------------

def test_hai_viec_chay_nen_da_khai_trong_danh_ba(db):
    """`open_run` ném lỗi nếu công việc chưa khai — chốt luôn ở đây."""
    for job in (tasks.JOB_PULL, tasks.JOB_RETRY):
        assert open_run(db, SOURCE_DATXE, job).id
