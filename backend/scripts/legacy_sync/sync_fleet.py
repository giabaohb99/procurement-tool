"""Đóng dấu `legacy_id` lên `tab_vehicle` và `tab_driver`.

Phiếu đặt xe bên app cũ trỏ tới xe và tài xế bằng khóa Firebase, nên hai danh
mục này phải khớp trước khi nạp phiếu.

Khác hai bước trước, ở đây KHÔNG có khớp tự động: bảng tra
`VEHICLE_TO_ERP_ID` / `DRIVER_TO_ERP_ID` bên `mapping.py` do người soát tay rồi
chốt (lý do ghi ngay trên bảng đó). Script chỉ thi hành và soi lệch: khóa lạ
bên app cũ, hàng ERP không ai trỏ tới, hoặc hai khóa trỏ chung một hàng.

CHẠY ĐƯỢC NHIỀU LẦN. Mặc định chỉ xem trước, `--apply` mới ghi.

    python -m scripts.legacy_sync.sync_fleet --export /tmp/fb-export.json
    python -m scripts.legacy_sync.sync_fleet --export /tmp/fb-export.json --apply
"""

import argparse
import collections
import json
import sys

from sqlalchemy import select

import app.core.all_models  # noqa: F401  nạp đủ model để SQLAlchemy dựng xong quan hệ
from app.core.database import SessionLocal
from app.modules.vehicle_booking.model import Driver, Vehicle
from scripts.legacy_sync.mapping import DRIVER_TO_ERP_ID, VEHICLE_TO_ERP_ID


def _load_export(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _check_table(title: str, mapping: dict[str, int], nodes: dict) -> bool:
    """Soi lệch giữa bảng tra và bản kết xuất. Trả về True nếu sạch."""
    ok = True
    for key in sorted(set(nodes) - set(mapping)):
        print(f"  LOI    {title}: khoa {key!r} co trong ban ket xuat "
              f"ma khong co trong bang tra")
        ok = False
    for key in sorted(set(mapping) - set(nodes)):
        print(f"  CANH BAO {title}: khoa {key!r} trong bang tra khong con "
              f"trong ban ket xuat")
    doubled = [i for i, n in collections.Counter(mapping.values()).items() if n > 1]
    for erp_id in doubled:
        keys = [k for k, v in mapping.items() if v == erp_id]
        print(f"  LOI    {title}: id {erp_id} bi {len(keys)} khoa cung tro vao: {keys}")
        ok = False
    return ok


def stamp(db, model, title: str, mapping: dict[str, int], label) -> int:
    """Gắn `legacy_id` theo bảng tra. Không bao giờ đè khóa khác đang có."""
    print(f"\n=== {title} ===")
    stamped = 0
    for key, erp_id in mapping.items():
        row = db.get(model, erp_id)
        if row is None:
            print(f"  LOI    {key} -> id {erp_id}: khong co hang nay ben ERP")
            continue
        if row.legacy_id == key:
            print(f"  DA CO  id {erp_id:<3} {label(row)}")
            continue
        if row.legacy_id:
            print(f"  LOI    id {erp_id} dang mang legacy_id khac: "
                  f"{row.legacy_id!r}, khong de len")
            continue
        print(f"  DAT    id {erp_id:<3} {label(row):<24} <- {key}")
        row.legacy_id = key
        stamped += 1
    unstamped = [r.id for r in db.execute(select(model)).scalars()
                 if not r.legacy_id]
    if unstamped:
        print(f"  CANH BAO hang ERP chua ai tro toi: {unstamped}")
    return stamped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", required=True,
                        help="duong dan ban ket xuat JSON tu Firebase")
    parser.add_argument("--apply", action="store_true",
                        help="ghi that; bo qua thi chi xem truoc")
    args = parser.parse_args()

    data = _load_export(args.export)
    for node in ("vehicles", "drivers"):
        if node not in data:
            print(f"LOI: ban ket xuat thieu nut {node!r}")
            return 1

    print("=== SOI LECH BANG TRA ===")
    clean = _check_table("xe", VEHICLE_TO_ERP_ID, data["vehicles"])
    clean &= _check_table("tai xe", DRIVER_TO_ERP_ID, data["drivers"])
    if not clean:
        print("\n  DUNG: bang tra lech ban ket xuat, sua mapping.py truoc.")
        return 1
    print("  bang tra khop ban ket xuat")

    db = SessionLocal()
    try:
        n_vehicle = stamp(db, Vehicle, "XE", VEHICLE_TO_ERP_ID,
                          lambda v: v.license_plate)
        n_driver = stamp(db, Driver, "TAI XE", DRIVER_TO_ERP_ID,
                         lambda d: d.name)
        if args.apply:
            db.commit()
        else:
            db.rollback()
        print(f"\n  xe dong dau     : {n_vehicle}")
        print(f"  tai xe dong dau : {n_driver}")
        print("\n  " + ("DA GHI VAO DB." if args.apply
                        else "MOI CHI XEM TRUOC — them --apply de ghi that."))
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
