"""Nạp 1313 phiếu app đặt xe cũ vào ERP.

    946 SEAL_REQUEST -> tab_seal_request
    321 CAR_BOOKING  -> tab_vehicle_booking (request_type = TYPE_CAR)
     46 DELIVERY     -> tab_vehicle_booking (request_type = TYPE_DELIVERY)

CHẠY ĐƯỢC NHIỀU LẦN: tra `legacy_id` trước, đã có thì bỏ qua, không tạo bản thứ
hai. Mặc định chỉ xem trước, `--apply` mới ghi.

    python -m scripts.legacy_sync.import_tickets --export /tmp/fb-export.json
    python -m scripts.legacy_sync.import_tickets --export /tmp/fb-export.json --apply

MÃ PHIẾU — đại ca chốt 16/09/2026: "prefix + 000 + id, ví dụ DD000789, còn đặt
xe là DX000789". Nên mã sinh sau khi `flush()` vì lúc đó mới có id. Lưu ý mã này
KHÁC nếp ERP đang tự sinh (`DD001` ba chữ số, xem `_next_seal_code`): sáu chữ số
không bao giờ đụng ba chữ số, và bộ sinh của ERP đọc `DD(\\d+)` nên vẫn chạy tiếp
đúng sau khi nạp — nhưng nhìn bảng sẽ thấy hai dạng mã, đó là cố ý để phân biệt
phiếu nhập từ app cũ với phiếu ERP tự tạo.

PHÉP DỰNG PHIẾU KHÔNG CÒN Ở ĐÂY. `PeopleResolver`, `build_seal`, `build_booking`,
`fit_to_columns` đã dời sang `app/modules/legacy_datxe/builder.py` — xem lời mở
đầu tệp đó để hiểu cách đổi trường và luật "hai đồng hồ" (UTC cho mốc máy chủ,
giờ +7 cho giờ người dùng gõ). Dời vì đồng bộ thường trực (cái móc bên app cũ và
vòng quét lưới an toàn) cũng phải dựng phiếu y hệt, mà tầng API không import
được `scripts/`. Tệp này giờ chỉ còn phần điều phối một đợt nạp: đọc bản kết
xuất, đối chiếu bảng tay, bỏ qua phiếu đã nạp, sinh mã, đếm, in tổng kết.

NHỮNG THỨ BỘ NẠP NÀY CỐ Ý KHÔNG LÀM (việc riêng, đừng tưởng là sót):

- KHÔNG nạp lịch sử duyệt. 5095 dòng `approval.history` đi theo §P1.1 của
  TIEN-DO.md, vào `tab_approval_instance` + `tab_approval_action`, và phải chạy
  SAU bước này vì `ApprovalInstance.entity_id` trỏ vào chính phiếu ERP.
- KHÔNG nạp tệp đính kèm. Cả 946 phiếu dấu đều có `attachedFileIds`; tệp nằm ở
  nhánh `files` bên Firebase, dời tệp là một việc riêng.
- KHÔNG mở phiên duyệt thật cho 34 phiếu còn `pending_approval`.
"""

import argparse
import collections
import json
import sys

from sqlalchemy import select

import app.core.all_models  # noqa: F401  nạp đủ model để SQLAlchemy dựng xong quan hệ
from app.core.database import SessionLocal
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.legacy_datxe.builder import (
    SYSTEM_ACTOR_ID,
    PeopleResolver,
    build_booking,
    build_seal,
    ensure_seal_type,
    fit_to_columns,
    legacy_index,
)
from app.modules.legacy_datxe.mapping import (
    BRAND_TO_COMPANY_ID,
    DEPARTMENT_TO_ERP_ID,
    DRIVER_TO_ERP_ID,
    VEHICLE_TO_ERP_ID,
)
from app.modules.seal_request.model import SealRequest, SealRequestCompany
from app.modules.vehicle_booking.model import Driver, Vehicle, VehicleBooking

# ---------------------------------------------------------------------------
# Đối chiếu danh mục trước khi nạp
# ---------------------------------------------------------------------------

def check_against_hand_table(title: str, from_db: dict[str, int],
                             hand: dict[str, int]) -> bool:
    """Đối chiếu bảng tra khai tay với dấu `legacy_id` dưới DB.

    DB là nguồn dùng để nạp, KHÔNG phải bảng tay — vì `sync_master_data` còn
    TẠO THÊM hàng ERP cho những khóa app cũ chưa có bên này rồi đóng dấu cho
    chúng, và những hàng đó không bao giờ có mặt trong bảng tay. Riêng phòng
    ban: bảng tay có 14 dòng, dưới DB có 22 dấu — đọc mỗi bảng tay thì 92 phiếu
    dấu rơi mất phòng ban và lặng lẽ lùi về phòng của người tạo.

    Bảng tay vẫn giữ vai trò cái chốt: nó là hồ sơ của những cặp do NGƯỜI chốt
    (bốn phòng gộp tay), nên hai bên nói khác nhau là có chuyện, phải dừng.
    """
    ok = True
    for key, hand_id in hand.items():
        db_id = from_db.get(key)
        if db_id is None:
            print(f"  LOI    {title}: bang tay co {key!r} -> {hand_id} ma duoi DB "
                  f"khong hang nao mang dau do")
            ok = False
        elif db_id != hand_id:
            print(f"  LOI    {title}: {key!r} bang tay tro {hand_id}, duoi DB "
                  f"la {db_id}")
            ok = False
    thua = set(from_db) - set(hand)
    if thua:
        print(f"  ghi chu {title}: {len(thua)} khoa chi co duoi DB (do "
              f"sync_master_data tao them), van dung binh thuong")
    return ok


def _existing_keys(db, model) -> set[str]:
    return set(db.execute(select(model.legacy_id)
                          .where(model.legacy_id != "")).scalars())


def run(db, data: dict, apply: bool) -> collections.Counter:
    stats: collections.Counter = collections.Counter()
    people = PeopleResolver(db)
    requests = data["requests"]

    print("\n=== DANH MUC ===")
    company_index = legacy_index(db, Company)
    dept_index = legacy_index(db, Department)
    vehicle_index = legacy_index(db, Vehicle)
    driver_index = legacy_index(db, Driver)
    clean = check_against_hand_table("cong ty", company_index, BRAND_TO_COMPANY_ID)
    clean &= check_against_hand_table("phong ban", dept_index, DEPARTMENT_TO_ERP_ID)
    clean &= check_against_hand_table("xe", vehicle_index, VEHICLE_TO_ERP_ID)
    clean &= check_against_hand_table("tai xe", driver_index, DRIVER_TO_ERP_ID)
    if not clean:
        raise SystemExit("  DUNG: dau legacy_id duoi DB lech bang tra tay, "
                         "chay lai sync_master_data truoc.")
    print(f"  cong ty {len(company_index)} dau · phong ban {len(dept_index)} dau · "
          f"xe {len(vehicle_index)} dau · tai xe {len(driver_index)} dau")

    print("\n=== LOAI CON DAU ===")
    seal_type_id = ensure_seal_type(db, apply)

    seal_done = _existing_keys(db, SealRequest)
    booking_done = _existing_keys(db, VehicleBooking)
    print(f"\n=== NAP PHIEU === (da co san: {len(seal_done)} phieu dau, "
          f"{len(booking_done)} phieu xe)")

    #  Xếp theo mốc tạo để id ERP tăng dần đúng thứ tự thời gian bên app cũ —
    #  mã phiếu sinh từ id nên nhờ vậy mã cũng chạy đúng dòng thời gian.
    ordered = sorted(requests.items(), key=lambda kv: kv[1].get("createdAt") or 0)

    for key, node in ordered:
        typ = node.get("type")
        if typ == "SEAL_REQUEST":
            if key in seal_done:
                stats["phieu dau bo qua (da nap)"] += 1
                continue
            req, company_ids = build_seal(db, key, node, people, seal_type_id,
                                          company_index, dept_index, stats)
            fit_to_columns(req, stats)
            stats["phieu dau"] += 1
            if not apply:
                continue
            db.add(req)
            db.flush()
            req.code = f"DD{req.id:06d}"
            for cid in company_ids:
                db.add(SealRequestCompany(seal_request_id=req.id, company_id=cid,
                                          created_by=SYSTEM_ACTOR_ID,
                                          updated_by=SYSTEM_ACTOR_ID))
        elif typ in ("CAR_BOOKING", "DELIVERY"):
            if key in booking_done:
                stats["phieu xe bo qua (da nap)"] += 1
                continue
            booking = build_booking(db, key, node, people, company_index,
                                    vehicle_index, driver_index, stats)
            fit_to_columns(booking, stats)
            stats["phieu xe cong tac" if typ == "CAR_BOOKING" else "phieu giao hang"] += 1
            if not apply:
                continue
            db.add(booking)
            db.flush()
            booking.code = f"DX{booking.id:06d}"
        else:
            stats[f"loai la: {typ}"] += 1

    if people.unknown_uid:
        print("\n  LOI: UID khong tra ra ho so nao (phieu se mat nguoi tao):")
        for uid, n in people.unknown_uid.most_common():
            print(f"    {uid}  x{n}")
    if people.no_account:
        print("\n  CANH BAO: ho so KHONG co tai khoan ERP — app cu da khoa ho tu "
              "truoc nen khong duoc cap tai khoan. Phieu van nap, ten nguoi tao "
              "van con, chi de trong id tai khoan:")
        for who, n in people.no_account.most_common():
            print(f"    {who}  x{n}")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", required=True,
                        help="duong dan ban ket xuat JSON tu Firebase")
    parser.add_argument("--apply", action="store_true",
                        help="ghi that; bo qua thi chi xem truoc")
    args = parser.parse_args()

    with open(args.export, encoding="utf-8") as fh:
        data = json.load(fh)
    for node in ("requests", "users", "brands", "departments"):
        if node not in data:
            print(f"LOI: ban ket xuat thieu nhanh {node!r}")
            return 1

    db = SessionLocal()
    try:
        stats = run(db, data, args.apply)
        if args.apply:
            db.commit()
        else:
            db.rollback()
        print("\n=== TONG KET ===")
        for name, n in sorted(stats.items()):
            print(f"  {name:42} {n}")
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
