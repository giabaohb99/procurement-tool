"""Thử Bước 0 (duoc-CR-682) trên phiếu THẬT kéo từ app cũ DEV về local. CHỈ ĐỌC Firebase dev, không ghi gì sang app cũ.

    docker compose cp plans/261026-1028-buoc-0-du-lieu-dev/scripts/try-step0-on-dev-tickets.py api:/tmp/b0.py
    docker compose exec -T api env PYTHONPATH=/app python /tmp/b0.py

Mỗi ca: thao tác trên ERP (đường nghiệp vụ thật nếu có) → đọc lại phiếu đó từ Firebase dev → `apply_legacy_record(force=True)`
(đúng việc lượt quét 02:15 làm) → so trạng thái / ô ERP trước và sau.
"""
from types import SimpleNamespace

import app.core.all_models  # noqa: F401
from app.core.database import SessionLocal
from app.core.config import settings
from app.core import app_settings
from app.modules.legacy_datxe import firebase
from app.modules.legacy_datxe.outbound import is_outbound_enabled
from app.modules.legacy_datxe.service import apply_legacy_record, entity_of
from app.modules.seal_request.model import SEAL_APPROVED, SEAL_COMPLETED, SealRequest
from app.modules.vehicle_booking.model import (BK_APPROVED, BK_COMPLETED, BK_DISPATCHED, Driver, Vehicle,
                                               VehicleBooking)

#  Chốt an toàn: dừng ngay nếu không phải Firebase DEV, hoặc chiều gửi đang bật, hoặc thư không bị chặn.
url = (app_settings.get("legacy_firebase_db_url") or "")
assert "-com-" not in url and "api-degoholding-default-rtdb" in url, "KHÔNG phải Firebase dev — dừng"
assert not is_outbound_enabled() and not (app_settings.get("sync_legacy_api_base") or ""), "chiều gửi phải tắt"
assert settings.EMAIL_HARD_OFF, "phải chặn email"

ACTOR = SimpleNamespace(id=2, employee_id=0, email="admin")


def resync(db, row):
    node = firebase.read_node(f"requests/{row.legacy_id}")
    log = apply_legacy_record(db, node=node, legacy_id=row.legacy_id, entity=entity_of(node), force=True)
    db.expire_all()
    return log


def show(tag, before, row, log, keys):
    after = {k: getattr(row, k) for k in keys}
    ok = before == after
    print(f"{'ĐẠT ' if ok else 'HỎNG'} {tag}: {row.code} trước={before} sau={after} | sổ={log.status}:{(log.message or '')[:70]}")
    return ok


def main():
    db = SessionLocal()
    results = []
    vehicle = db.query(Vehicle).first()
    driver = db.query(Driver).first()

    # A — ERP điều phối phiếu «Đã duyệt» bằng hàm nghiệp vụ thật.
    from app.modules.vehicle_booking.schema import DispatchIn
    from app.modules.vehicle_booking.service import dispatch_booking

    a = db.query(VehicleBooking).filter(VehicleBooking.legacy_id != "", VehicleBooking.status == BK_APPROVED).first()
    dispatch_booking(db, a, DispatchIn(assigned_vehicle_id=vehicle.id, assigned_driver_id=driver.id), ACTOR)
    db.refresh(a)
    keys = ("status", "assigned_vehicle_id", "assigned_driver_id")
    before = {k: getattr(a, k) for k in keys}
    print("A dấu ERP:", a.erp_action_at)
    results.append(show("A điều phối trên ERP rồi quét ép", before, a, resync(db, a), keys))

    # B — ERP hoàn tất phiếu đang điều phối (ghi ORM ngoài lượt đồng bộ, như nút tài xế).
    b = db.query(VehicleBooking).filter(VehicleBooking.legacy_id != "", VehicleBooking.status == BK_DISPATCHED).first()
    b.status = BK_COMPLETED
    db.commit()
    before = {"status": b.status}
    results.append(show("B hoàn tất trên ERP rồi quét ép", before, b, resync(db, b), ("status",)))

    # C — Văn thư đóng dấu trên ERP.
    c = db.query(SealRequest).filter(SealRequest.legacy_id != "", SealRequest.status == SEAL_APPROVED).first()
    if c is not None:
        c.status, c.completed_by = SEAL_COMPLETED, 2
        db.commit()
        before = {"status": c.status, "completed_by": c.completed_by}
        results.append(show("C đóng dấu trên ERP rồi quét ép", before, c, resync(db, c), ("status", "completed_by")))

    # D — phiếu ERP KHÔNG đụng: vẫn soi gương (không đổi, không đóng dấu).
    d = db.query(VehicleBooking).filter(VehicleBooking.legacy_id != "", VehicleBooking.status == BK_APPROVED,
                                        VehicleBooking.erp_action_at == "").first()
    before = {"status": d.status, "erp_action_at": d.erp_action_at}
    results.append(show("D phiếu ERP không đụng, quét ép", before, d, resync(db, d), ("status", "erp_action_at")))

    print(f"\nTổng: {sum(results)}/{len(results)} ca đạt")
    db.close()


if __name__ == "__main__":
    main()
