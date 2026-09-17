"""Nạp LỊCH SỬ THAO TÁC của phiếu app đặt xe cũ vào `tab_audit_log`.

    5095 dòng `approval.history` của 1313 phiếu
      -> 5095 dòng `tab_audit_log` (thẻ "Lịch sử thao tác" trên màn chi tiết)

KHÁC `import_approval_history.py`, đừng lẫn hai cái: bộ kia dựng **bộ máy
duyệt** (`tab_approval_instance` · `_task` · `_action`) — thứ vẽ ra dải chặng
"ai đã ký". Bộ này dựng **dòng thời gian thao tác** — thẻ *Lịch sử thao tác* do
`AuditTimeline` vẽ, hôm nay **trống trơn ở cả 1313 phiếu nhập về** vì
`import_tickets.py` ghi thẳng xuống bảng chứ không đi qua controller, mà mọi
dòng nhật ký đều sinh ra từ `core/audit.record(...)` trong controller.

Cùng một mảng `history` đổ vào HAI chỗ là cố ý, không phải chép thừa: hai bảng
trả lời hai câu hỏi khác nhau và màn hình đọc hai bảng khác nhau. Điểm khác rõ
nhất là **mốc chuyến** — `dispatched` · `driver_accepted` · `trip_started` ·
`trip_completed`: bộ kia CỐ Ý loại chúng khỏi bảng dấu vết duyệt (tài xế bấm
*Bắt đầu chuyến* không phải người ký duyệt), còn ở đây chúng **phải có mặt**,
vì đó đúng là những thao tác người ta làm trên phiếu.

CHẠY SAU `import_tickets.py`: `AuditLog.entity_id` trỏ thẳng vào id phiếu ERP.

CHẠY ĐƯỢC NHIỀU LẦN: phiếu nào đã có dòng nhật ký thì bỏ qua CẢ CỤM. Khử theo
phiếu chứ không theo từng dòng vì `tab_audit_log` không có cột mã bên app cũ —
thêm một cột chỉ để chạy lại được là đắt hơn giá trị nó mang lại, mà nhật ký
thì không sửa, chỉ thêm. Mặc định chỉ xem trước, `--apply` mới ghi.

    python -m scripts.legacy_sync.import_audit_log --export /tmp/fb-export.json
    python -m scripts.legacy_sync.import_audit_log --export /tmp/fb-export.json --apply

BA ĐIỀU RÀNG BUỘC CÁCH VIẾT TỆP NÀY:

1. **KHÔNG gọi được `core/audit.record(...)`.** Hàm đó lấy giờ hiện tại
   (`created_at` để `server_default`) và tự `db.commit()` từng dòng. Dùng nó là
   5095 dòng nhật ký cùng mang mốc "hôm nay" — một dòng thời gian phẳng lì, vô
   dụng. Nên dựng thẳng `AuditLog(...)` và gán `created_at` từ app cũ.
2. **`action` là TẬP MÃ ĐÓNG**, khai duy nhất ở `core/action_catalog.py`. Mã lạ
   vẫn ghi được nhưng người đọc thấy mã Anh trần giữa câu tiếng Việt và dòng đó
   rơi vào nhóm *Không rõ*, biến mất khỏi mọi bộ lọc theo nhóm. Bảng dưới chỉ
   dùng mã ĐÃ khai — có `assert` canh lúc chạy.
3. **`AuditTimeline` xếp theo `id` giảm dần, KHÔNG theo `created_at`.** Nên thứ
   tự `db.add` bên trong một phiếu chính là thứ tự hiện lên màn hình. Mảng
   `history` bên app cũ đã xếp sẵn theo thời gian (đo: 0/5095 dòng lệch thứ tự),
   cứ thêm đúng thứ tự mảng là xong.

CÂU CHỮ LẤY NGUYÊN VĂN CỦA ERP, không tự chế: mỗi dòng dưới đây khớp đúng chuỗi
mà `seal_request/controller.py` và `vehicle_booking/controller.py` đang ghi cho
cùng một thao tác. Hai màn chi tiết đọc `message` theo hai kiểu khác nhau nên
câu chữ phải chịu được cả hai: phiếu dấu bày *«Tên — Duyệt: Duyệt yêu cầu đóng
dấu DD000153»* (`showMessage`), phiếu xe bày *«Tên — Bắt đầu chuyến XE000123»*
(`messageOnly`, `message` phải ĐỨNG MỘT MÌNH đọc được).

`actor_kind = ACTOR_KIND_SCRIPT` (3) cho cả 5095 dòng — nói thẳng rằng chúng do
script nhập liệu ghi, không phải do người bấm nút. Đó là thứ phân biệt được
"nhập từ app cũ" với "thao tác thật bên ERP" khi sau này đọc lại.
"""

import argparse
import collections
import json
import re
import sys

from sqlalchemy import select

import app.core.all_models  # noqa: F401  nạp đủ model để SQLAlchemy dựng xong quan hệ
from app.core.action_catalog import group_of_action, is_known_action
from app.core.database import SessionLocal
from app.core.logging_codes import ACTOR_KIND_SCRIPT
from app.modules.audit.model import AuditLog
from app.modules.seal_request.model import SealRequest
from app.modules.vehicle_booking.model import VehicleBooking
from app.modules.legacy_datxe.builder import (
    PeopleResolver,
    _utc_dt,
    legacy_index,
)

SEAL_ENTITY = "seal_request"
BOOKING_ENTITY = "vehicle_booking"

#  Tên gọi loại phiếu, ghép vào câu nhật ký. Giữ đúng chữ của ERP: "Tạo yêu cầu
#  đóng dấu {code}" / "Tạo yêu cầu đặt xe {code}".
SEAL_NOUN = "yêu cầu đóng dấu"
BOOKING_NOUN = "yêu cầu đặt xe"

MAX_DOC_CODE = 50
MAX_CHANGED_FIELDS = 500

#  Ghi chú app cũ tự sinh, nói y hệt câu nhật ký của ERP. Gắn thêm vào là mỗi
#  dòng đọc hai lần cùng một điều ("Chấp nhận chuyến — Ghi chú: Tài xế đã chấp
#  nhận chuyến đi."). Đây là tập ĐÓNG, đo đủ trên bản kết xuất: bốn câu này
#  chiếm 2118/3376 ghi chú, mọi ghi chú khác đều mang thông tin thật.
BOILERPLATE_COMMENTS = frozenset({
    "Yêu cầu được tạo.",
    "Tài xế đã chấp nhận chuyến đi.",
    "Chuyến đi đã bắt đầu.",
    "Chuyến đi đã hoàn thành.",
})

#  Người tạo sửa phiếu -> app cũ ghi "… đã chỉnh sửa các mục sau: startTime,
#  notes". Bảng này đổi tên trường app cũ sang nhãn tiếng Việt của ERP
#  (`vehicle_booking/controller._EDIT_LABELS`) để câu nhật ký đọc được. Đo trên
#  bản kết xuất: đúng 20 tên trường, 211/211 dòng `edited` khớp khuôn.
EDIT_FIELD_LABELS = {
    "purpose": "Mục đích",
    "startTime": "Thời gian đi / lấy hàng",
    "endTime": "Thời gian về / giao",
    "startLocation": "Điểm đi / lấy hàng",
    "endLocation": "Điểm đến / giao hàng",
    "pickupLocation": "Điểm đón",
    "intermediateStops": "Điểm dừng",
    "isRoundTrip": "Khứ hồi",
    "passengerCount": "Số hành khách",
    "attendees": "Người tham gia",
    "contactPhone": "SĐT liên hệ",
    "itemName": "Tên hàng hóa",
    "dimensions": "Kích thước / KL",
    "specialInstructions": "Chỉ dẫn đặc biệt",
    "notes": "Ghi chú",
    "attachedFileIds": "Tệp đính kèm",
    "brandId": "Thương hiệu",
    #  Ba trường của luồng duyệt bên app cũ, ERP không có ô tương ứng — dịch
    #  theo nghĩa chứ không bỏ, vì đây là thứ giải thích vì sao phiếu quay lại
    #  chặng khác sau khi sửa.
    "firstApproverUid": "Người duyệt đầu tiên",
    "isSkipApproval": "Bỏ qua duyệt",
    "skipApprovalToLevel": "Bỏ qua duyệt tới chặng",
}

_EDITED_PATTERN = re.compile(r"chỉnh sửa các mục sau:\s*(.+)$", re.S)

#  Ba mã app cũ KHÔNG có ở phiếu dấu (đo: 0 dòng) nhưng vẫn khai chung — bảng
#  mã là của app cũ, không phải của từng loại phiếu.
TRIP_ACTIONS = frozenset({"dispatched", "re-dispatched", "driver_accepted",
                          "trip_started", "trip_completed"})


def _with_reason(action: str, reason: str) -> str:
    """Ghép hành động + lý do — BẢN SAO của hàm cùng tên ở hai controller.

    Chép chứ không import: hai controller khai riêng mỗi bên một bản, import
    bên nào cũng là nói rằng câu chữ của phiếu này phụ thuộc phiếu kia.
    """
    reason = (reason or "").strip()
    return f"{action} — Lý do: {reason}" if reason else action


def _with_note(action: str, note: str) -> str:
    """Như trên nhưng cho ghi chú KHÔNG phải lý do — duyệt, tạo phiếu.

    ERP không có sẵn khuôn này (nút Duyệt bên ERP không cho nhập ghi chú), còn
    app cũ thì có: 393 lượt duyệt kèm ghi chú kiểu "Đóng dấu 2 bản". Bỏ đi là
    mất đúng phần người đọc cần.
    """
    note = (note or "").strip()
    return f"{action} — Ghi chú: {note}" if note else action


def edited_labels(comment: str) -> list[str]:
    """Tên trường trong ghi chú `edited` -> nhãn tiếng Việt, giữ nguyên thứ tự.

    Tên lạ giữ NGUYÊN VĂN chứ không bỏ: một cái tên Anh trần trong câu vẫn nói
    được "trường này đã đổi", còn bỏ đi thì dòng nhật ký khai thiếu.
    """
    match = _EDITED_PATTERN.search(comment or "")
    if not match:
        return []
    names = [n.strip() for n in match.group(1).split(",")]
    return [EDIT_FIELD_LABELS.get(n, n) for n in names if n]


def build_message(entity: str, noun: str, code: str, entry: dict,
                  stats: collections.Counter) -> tuple[str, str] | None:
    """Một dòng `history` -> `(mã hành động, câu nhật ký)`. `None` = mã lạ.

    Bảng dịch đầy đủ, mã bên trái là của app cũ:

    - `created`          -> `create`     "Tạo yêu cầu đóng dấu DD000153"
    - `approved`         -> `approve`    "Duyệt yêu cầu đóng dấu DD000153"
    - `needs_correction` -> `update`     "Yêu cầu chỉnh sửa — Lý do: …"
    - `rejected`         -> `cancel`     "Từ chối yêu cầu — Lý do: …"
    - `canceled`         -> `withdraw`   "Rút yêu cầu — Lý do: …"
    - `admin_canceled`   -> `cancel`     "Quản trị hủy yêu cầu — Lý do: …"
    - `edited`           -> `update`     "Chỉnh sửa: Điểm dừng, Tệp đính kèm"
    - `dispatched`       -> `dispatched` ghi chú app cũ (đã đủ câu)
    - `re-dispatched`    -> `dispatched` ghi chú app cũ
    - `driver_accepted`  -> `update`     "Chấp nhận chuyến"
    - `trip_started`     -> `update`     "Bắt đầu chuyến XE000123"
    - `trip_completed`   -> `update`     "Hoàn tất chuyến XE000123"

    HAI chỗ lệch khỏi câu chữ ERP, cả hai đều có lý do:

    * `canceled` và `admin_canceled` — ERP **không có** nút rút phiếu / quản trị
      hủy cho hai loại phiếu này, nên không có câu nào để chép. Dùng đúng hai mã
      đã khai sẵn trong `action_catalog` (`withdraw` = "Rút phiếu", `cancel` =
      "Hủy") và viết câu theo cùng khuôn.
    * `dispatched` — ERP ghi "Đã điều phối Xe 51D-668.25 và Tài xế Lưu Nhựt
      Minh", app cũ ghi "Điều phối cho tài xế Lưu Nhựt Minh và xe 51D-668.25".
      Cùng nội dung, khác thứ tự chữ. Lấy **nguyên văn app cũ** vì tách ngược
      tên xe với tên tài xế ra khỏi câu để ghép lại theo khuôn ERP là một phép
      dò chuỗi có thể sai, đổi lấy đúng một thay đổi về trật tự từ.
    """
    legacy = entry.get("action")
    comment = (entry.get("comment") or "").strip()
    if comment in BOILERPLATE_COMMENTS:
        comment = ""

    if legacy == "created":
        return "create", _with_note(f"Tạo {noun} {code}", comment)
    if legacy == "approved":
        return "approve", _with_note(f"Duyệt {noun} {code}", comment)
    if legacy == "needs_correction":
        return "update", _with_reason("Yêu cầu chỉnh sửa", comment)
    if legacy == "rejected":
        return "cancel", _with_reason("Từ chối yêu cầu", comment)
    if legacy == "canceled":
        return "withdraw", _with_reason(f"Rút {noun} {code}", comment)
    if legacy == "admin_canceled":
        return "cancel", _with_reason(f"Quản trị hủy {noun} {code}", comment)
    if legacy == "edited":
        labels = edited_labels(comment)
        if labels:
            #  Đúng câu `update_booking` của ERP đang ghi. Dùng cho CẢ phiếu dấu
            #  (ERP bên đó ghi "Cập nhật yêu cầu đóng dấu {code}" chung chung):
            #  cùng một bảng nhật ký, nói cụ thể đã đổi gì thì hơn.
            return "update", f"Chỉnh sửa: {', '.join(labels)}"
        stats["dong `edited` khong doc ra ten truong"] += 1
        return "update", _with_note(f"Cập nhật {noun} {code}", comment)

    #  --- mốc chuyến: chỉ phiếu xe mới có ---------------------------------
    if legacy in TRIP_ACTIONS and entity != BOOKING_ENTITY:
        #  Đo được 0 ca. Kêu chứ đừng lặng lẽ ghi: mốc chuyến trên phiếu dấu
        #  nghĩa là bản kết xuất khác thứ mình đã đo.
        stats[f"CHUA XU: phieu dau co moc chuyen `{legacy}`"] += 1
        return None
    if legacy in ("dispatched", "re-dispatched"):
        fallback = "Đã điều phối lại" if legacy == "re-dispatched" else "Đã điều phối"
        return "dispatched", comment or fallback
    if legacy == "driver_accepted":
        return "update", _with_note("Chấp nhận chuyến", comment)
    if legacy == "trip_started":
        return "update", _with_note(f"Bắt đầu chuyến {code}", comment)
    if legacy == "trip_completed":
        return "update", _with_note(f"Hoàn tất chuyến {code}", comment)

    stats[f"ma lich su la: {legacy}"] += 1
    return None


def build_rows(entity: str, entity_id: int, noun: str, code: str,
               hist: list[dict], people: PeopleResolver,
               stats: collections.Counter) -> list[AuditLog]:
    """Cả mảng `history` của MỘT phiếu -> danh sách dòng nhật ký, đúng thứ tự."""
    rows: list[AuditLog] = []
    for entry in hist:
        built = build_message(entity, noun, code, entry, stats)
        if built is None:
            continue
        action, message = built
        #  Chốt mã đóng (xem ràng buộc 2 ở đầu tệp). Đây là lỗi lập trình của
        #  chính tệp này chứ không phải dữ liệu bẩn, nên dừng hẳn.
        assert is_known_action(action), f"mã hành động chưa khai: {action}"

        uid = entry.get("userId") or ""
        actor = people.user_id(uid)
        if not actor and uid:
            #  `resolve_actor(0)` đọc ra "Hệ thống". Chép tên app cũ vào câu để
            #  câu trả lời cho "ai làm" không biến mất — cùng luật với
            #  `import_approval_history.py`.
            who = (entry.get("userName") or "").strip() or uid
            message = f"{message} [App cũ] người thao tác: {who}"
            stats["dong nhat ky khong tra ra tai khoan"] += 1

        row = AuditLog(
            entity=entity,
            entity_id=entity_id,
            action=action,
            message=message,
            actor_kind=ACTOR_KIND_SCRIPT,
            #  Không có lượt gọi API nào sinh ra mấy dòng này: không phiên, không
            #  request, không IP. Để trống đúng như sự thật — giao diện tự ẩn nút
            #  "Xem lượt gọi" khi `request_id` rỗng.
            session_id=None,
            request_id=None,
            ip="",
            on_behalf_of=0,
            doc_code=(code or "")[:MAX_DOC_CODE],
            parent_entity="",
            parent_id=0,
            action_group=group_of_action(action),
            created_by=actor,
            updated_by=actor,
        )
        if action == "update" and message.startswith("Chỉnh sửa: "):
            fields = message[len("Chỉnh sửa: "):]
            row.changed_fields = fields[:MAX_CHANGED_FIELDS]
            row.change_count = len(fields.split(", "))

        #  Gán CÓ ĐIỀU KIỆN: `created_at` không cho NULL, gán thẳng `None` là đợt
        #  nạp chết giữa chừng. Không gán thì `server_default` điền giờ nạp —
        #  sai mốc nhưng còn dòng, hơn hẳn mất cả dòng.
        created = _utc_dt(entry.get("timestamp"))
        if created:
            row.created_at = created
        else:
            stats["dong khong co moc thoi gian (lay gio nap)"] += 1

        rows.append(row)
        stats[f"nhat ky: {entry.get('action')}"] += 1
    return rows


def existing_entities(db, entity: str) -> set[int]:
    """`entity_id` của những phiếu ĐÃ có dòng nhật ký — nền của việc chạy lại."""
    return set(db.execute(
        select(AuditLog.entity_id).where(AuditLog.entity == entity).distinct()
    ).scalars())


def run(db, data: dict, apply: bool) -> collections.Counter:
    stats: collections.Counter = collections.Counter()
    people = PeopleResolver(db)
    requests = data["requests"]

    seal_index = legacy_index(db, SealRequest)
    booking_index = legacy_index(db, VehicleBooking)
    print(f"\n=== PHIEU DA NAP === {len(seal_index)} phieu dau · "
          f"{len(booking_index)} phieu xe")
    if not seal_index and not booking_index:
        raise SystemExit("  DUNG: chua co phieu nao mang dau legacy_id. "
                         "Chay import_tickets.py truoc.")

    done = {SEAL_ENTITY: existing_entities(db, SEAL_ENTITY),
            BOOKING_ENTITY: existing_entities(db, BOOKING_ENTITY)}
    print(f"=== DA CO NHAT KY === {len(done[SEAL_ENTITY])} phieu dau · "
          f"{len(done[BOOKING_ENTITY])} phieu xe")

    #  Xếp theo mốc tạo phiếu để id dòng nhật ký tăng dần đúng dòng thời gian
    #  app cũ — `AuditTimeline` xếp theo `id`, xem ràng buộc 3 ở đầu tệp.
    ordered = sorted(requests.items(), key=lambda kv: (kv[1] or {}).get("createdAt") or 0)

    for key, node in ordered:
        if not isinstance(node, dict):
            continue
        typ = node.get("type")
        if typ == "SEAL_REQUEST":
            entity, model, index, noun = SEAL_ENTITY, SealRequest, seal_index, SEAL_NOUN
        elif typ in ("CAR_BOOKING", "DELIVERY"):
            entity, model, index, noun = (BOOKING_ENTITY, VehicleBooking,
                                          booking_index, BOOKING_NOUN)
        else:
            stats[f"loai la: {typ}"] += 1
            continue

        entity_id = index.get(key)
        if not entity_id:
            stats["phieu app cu chua co ban doi ung ben ERP"] += 1
            continue
        if entity_id in done[entity]:
            stats["phieu bo qua (da co nhat ky)"] += 1
            continue

        hist = (node.get("approval") or {}).get("history") or []
        if not hist:
            stats["phieu khong co dong lich su nao"] += 1
            continue

        obj = db.get(model, entity_id)
        code = getattr(obj, "code", "") or ""
        rows = build_rows(entity, entity_id, noun, code, hist, people, stats)
        if not rows:
            continue
        stats["phieu co nhat ky"] += 1

        if apply:
            #  Thêm đúng thứ tự mảng rồi ghi một lượt: SQLAlchemy giữ nguyên thứ
            #  tự `add` khi chèn cùng một bảng, nên `id` tăng dần đúng dòng thời
            #  gian — mà màn hình lại xếp theo `id`.
            for row in rows:
                db.add(row)
            db.flush()
            done[entity].add(entity_id)

    if people.unknown_uid:
        print("\n  CANH BAO: UID khong tra ra ho so nao — cot `created_by` cua "
              "nhung dong do de 0 (hien 'He thong'), ten app cu chep vao cau:")
        for uid, n in people.unknown_uid.most_common(10):
            print(f"    {uid}  x{n}")

    print("\n  NHAC: 5095 dong nay mang actor_kind = 3 (script nhap lieu) va "
          "khong co request_id — do la cach phan biet chung voi thao tac that "
          "ben ERP khi doc lai sau nay.")
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
    if "requests" not in data:
        print("LOI: ban ket xuat thieu nhanh 'requests'")
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
            print(f"  {name:48} {n}")
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
