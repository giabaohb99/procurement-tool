"""Nạp TỆP ĐÍNH KÈM của phiếu app đặt xe cũ vào `tab_file` + `tab_file_link`.

    946 phiếu duyệt dấu có `details.attachedFileIds`
      -> 1488 dòng `tab_file`       (mỗi TỆP một dòng)
      -> 1488 dòng `tab_file_link`  (entity `seal_request`)

Đo trên bản kết xuất ngày 16/09/2026 (xem §P6 TIEN-DO.md): **1519 lượt trỏ**
nhưng chỉ **1488 tệp khác nhau**, và 31 lượt dư là **cùng một tệp khai HAI LẦN
trong CÙNG MỘT phiếu** — không có tệp nào dùng chung giữa hai phiếu (đo: 0).
Nên số dây đúng là 1488 chứ không phải 1519: gắn cả 31 lượt dư thì màn chi tiết
bày một tệp hai dòng, người đọc tưởng có hai bản khác nhau. `seen_pairs` khử
đúng chỗ đó. **0 lượt trỏ tới mã không có trong nhánh `files`**; tổng 5621,7 MB;
1287 pdf · 195 jpeg · 3 png · 1 xlsx · 1 tiff · 1 docx. Chỉ phiếu **duyệt dấu**
có tệp — phiếu đặt xe và giao hàng bên app cũ không đính kèm gì, nên không có
nhánh nào cho chúng ở đây.

CHẠY SAU `import_tickets.py`: `FileLink.entity_id` trỏ thẳng vào id phiếu ERP.

CHẠY ĐƯỢC NHIỀU LẦN: tệp tra theo cặp (`source`, `external_id`), dây tra theo
bộ ba (`file_id`, `entity`, `entity_id`). Mặc định chỉ xem trước, `--apply` mới ghi.

    python -m scripts.legacy_sync.import_attachments --export /tmp/fb-export.json
    python -m scripts.legacy_sync.import_attachments --export /tmp/fb-export.json --apply

⚠️ BỘ NẠP NÀY CHÉP **LỜI KHAI VỀ TỆP**, KHÔNG CHÉP BYTE. `file_key` ghi xuống là
khóa `uploads/...` của **kho R2 BÊN APP CŨ**. Khóa R2 của ERP không với sang đó
được — thử thật ngày 16/09/2026: đọc một khóa như vậy trả **404**, hỏi danh sách
bucket trả **AccessDenied**. Vì thế:

* mọi đường đọc byte đi qua `core/legacy_files.read_file_bytes`, nó thấy
  `source = "datxe"` thì hỏi app cũ chứ không hỏi kho ERP;
* đường đó cần app cũ dựng `GET /api/v1/sync/files/{id}/url` (§10.1) **và** hai
  biến `SYNC_DATXE_ENABLED` / `SYNC_SHARED_SECRET` / `SYNC_LEGACY_API_BASE`.
  Chưa có thì người dùng thấy đúng câu "tệp còn nằm ở app cũ", không phải 404;
* ngày tắt app cũ là ngày mọi tệp này chết, trừ khi trước đó có một đợt **chép
  byte thật** sang kho ERP (§10.2) — đợt đó chỉ cần lọc `source = "datxe"`, tải
  về, đẩy lên, ghi lại `file_key` rồi xóa cờ `source`. Chính hai cột đó là đường
  để dành sẵn cho nó.

CỘT `url` ĐỂ **RỖNG**, cố ý. App cũ ký đường dẫn sống một giờ; lưu xuống thì hôm
sau bấm vào là hỏng, mà hỏng theo kiểu khó đoán vì cột `url` trông vẫn có giá
trị. Giao diện không có `url` thì tự rơi xuống đường `/view` có kiểm quyền.

TỆP MỒ CÔI CỐ Ý BỎ: 83 tệp trong nhánh `files` không phiếu nào trỏ tới (645 MB).
Nạp chúng là đẻ ra 83 dòng `tab_file` không dây, mà `purge_orphan_files` lại lọc
theo `file_key like '%/attachment/%'` nên không bao giờ dọn tới — rác vĩnh viễn.
"""

import argparse
import collections
import json
import sys

from sqlalchemy import select

import app.core.all_models  # noqa: F401  nạp đủ model để SQLAlchemy dựng xong quan hệ
from app.core.database import SessionLocal
from app.core.legacy_files import SOURCE_DATXE
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.seal_request.model import SealRequest
from app.modules.legacy_datxe.builder import (
    PeopleResolver,
    _utc_dt,
    legacy_index,
)

SEAL_ENTITY = "seal_request"

#  Nhãn thư mục chứng từ. Bên ERP, tệp người yêu cầu đính vào phiếu duyệt dấu là
#  "Chứng từ đã ký" (`core/document_types.py`) — đúng thứ app cũ đang giữ: bản
#  cần đóng dấu mà Văn thư phải đối chiếu. Để rỗng thì tệp rơi vào mục "Khác".
SEAL_DOC_TYPE = "signed_doc"

#  Trần độ dài đúng bằng cột dưới DB. Cắt ở đây chứ không để MySQL từ chối giữa
#  chừng đợt nạp — tên tệp app cũ do người dùng gõ, không ai canh độ dài.
MAX_FILENAME = 255
MAX_FILE_KEY = 500
MAX_CONTENT_TYPE = 100
MAX_EXTERNAL_ID = 64


def _text(value, limit: int) -> str:
    return (str(value or "").strip())[:limit]


def file_ids_of(node: dict) -> list[str]:
    """Danh sách mã tệp của một phiếu app cũ, giữ NGUYÊN THỨ TỰ.

    Firebase trả mảng khi khóa liên tục và trả từ điển khi có lỗ (xóa một phần
    tử giữa mảng là thành `{"0": ..., "2": ...}`). Đo thật thì bản kết xuất này
    toàn mảng, nhưng nhận cả hai dạng thì rẻ hơn nhiều so với một đợt nạp thiếu
    tệp mà không ai biết.
    """
    ids = ((node.get("details") or {}).get("attachedFileIds")) or []
    if isinstance(ids, dict):
        ids = [ids[k] for k in sorted(ids, key=lambda k: (len(k), k))]
    return [i for i in ids if isinstance(i, str) and i.strip()]


def existing_files(db) -> dict[str, StoredFile]:
    """`{mã tệp app cũ: dòng tab_file}` — nền của việc chạy lại không sinh bản trùng."""
    rows = db.execute(
        select(StoredFile).where(StoredFile.source == SOURCE_DATXE,
                                 StoredFile.external_id != "")
    ).scalars()
    return {row.external_id: row for row in rows}


def existing_links(db, entity: str) -> set[tuple[int, int]]:
    """`{(file_id, entity_id)}` của những dây đã có, để không gắn hai lần."""
    rows = db.execute(
        select(FileLink.file_id, FileLink.entity_id).where(FileLink.entity == entity)
    ).all()
    return {(row[0], row[1]) for row in rows}


def build_stored_file(external_id: str, node: dict, people: PeopleResolver,
                      stats: collections.Counter) -> StoredFile:
    """Một nút của nhánh `files` -> một dòng `tab_file`.

    `created_by` là ID TÀI KHOẢN (cột kiểm toán chung), không phải id nhân sự —
    cùng luật với phiếu bên `import_tickets.py`. `uploadedBy` của app cũ là UID
    Firebase nên phải đi qua `PeopleResolver.user_id`.
    """
    actor = people.user_id(node.get("uploadedBy") or "")
    if not actor:
        stats["tep khong tra ra tai khoan nguoi tai len"] += 1
    row = StoredFile(
        filename=_text(node.get("fileName"), MAX_FILENAME) or "tep-khong-ten",
        file_key=_text(node.get("r2Key"), MAX_FILE_KEY),
        #  RỖNG, cố ý — xem ghi chú "CỘT `url`" ở đầu tệp.
        url="",
        content_type=_text(node.get("mimeType"), MAX_CONTENT_TYPE),
        size=int(node.get("size") or 0),
        #  App cũ không tính mã băm; tính lại thì phải tải cả 5,6 GB về, mà chưa
        #  ai đang cần đối chiếu tệp cũ. Để rỗng đúng như tệp ERP trước CR văn thư.
        sha256="",
        thumb_key="",
        thumb_url="",
        source=SOURCE_DATXE,
        external_id=_text(external_id, MAX_EXTERNAL_ID),
        created_by=actor,
        updated_by=actor,
    )
    #  Gán CÓ ĐIỀU KIỆN: cột `created_at` không cho NULL, gán thẳng `None` là
    #  đợt nạp chết giữa chừng. Không gán thì `server_default` điền giờ hiện tại
    #  — sai ngày nhưng còn dòng dữ liệu, hơn hẳn mất cả tệp.
    created = _utc_dt(node.get("createdAt"))
    if created:
        row.created_at = created
    else:
        stats["tep khong co moc tao (lay gio nap)"] += 1
    return row


def run(db, data: dict, apply: bool) -> collections.Counter:
    stats: collections.Counter = collections.Counter()
    people = PeopleResolver(db)
    requests = data["requests"]
    files = data.get("files") or {}

    seal_index = legacy_index(db, SealRequest)
    print(f"\n=== PHIEU DA NAP === {len(seal_index)} phieu dau")
    if not seal_index:
        raise SystemExit("  DUNG: chua co phieu dau nao mang dau legacy_id. "
                         "Chay import_tickets.py truoc.")

    known = existing_files(db)
    linked = existing_links(db, SEAL_ENTITY)
    print(f"=== DA CO === {len(known)} tep · {len(linked)} day tep-phieu")

    #  Cặp (mã tệp app cũ, id phiếu ERP) đã xử trong LƯỢT CHẠY NÀY.
    seen_pairs: set[tuple[str, int]] = set()

    #  Xếp theo mốc tạo phiếu để id tệp tăng dần đúng dòng thời gian app cũ.
    ordered = sorted(requests.items(), key=lambda kv: (kv[1] or {}).get("createdAt") or 0)

    for key, node in ordered:
        if not isinstance(node, dict):
            continue
        ids = file_ids_of(node)
        if not ids:
            continue

        typ = node.get("type")
        if typ != "SEAL_REQUEST":
            #  Không có phiếu nào như vậy trong bản đo, nhưng nếu app cũ đổi ý
            #  thì phải KÊU chứ đừng lặng lẽ bỏ — mất tệp không ai nhìn ra.
            stats[f"CHUA XU: phieu {typ} co tep dinh kem"] += 1
            continue

        entity_id = seal_index.get(key)
        if not entity_id:
            stats["phieu app cu chua co ban doi ung ben ERP"] += 1
            continue

        stats["phieu co tep"] += 1
        for order, external_id in enumerate(ids):
            stats["luot tro tep"] += 1
            meta = files.get(external_id)
            if not isinstance(meta, dict):
                #  Đo được 0 ca, nhưng đây là ca mất dữ liệu thật nếu có: phiếu
                #  khai có tệp mà nhánh `files` không giữ lời khai nào về nó.
                stats["LOI: ma tep khong co trong nhanh `files`"] += 1
                continue

            stored = known.get(external_id)
            if stored is None:
                stored = build_stored_file(external_id, meta, people, stats)
                stats["tep moi"] += 1
                if apply:
                    db.add(stored)
                    db.flush()          # cần id để gắn dây ngay dưới
                known[external_id] = stored
            else:
                stats["tep da co (bo qua)"] += 1

            #  HAI chốt chống trùng, cho hai thứ khác nhau:
            #  - `seen_pairs` khử lượt LẶP TRONG CHÍNH BẢN KẾT XUẤT (31 ca: một
            #    tệp khai hai lần trong cùng một phiếu). Khóa theo mã app cũ nên
            #    chạy đúng cả lúc xem trước, khi tệp mới chưa có id;
            #  - `linked` khử dây ĐÃ NẰM DƯỚI DB, để chạy lại lần hai không đẻ
            #    thêm. Khóa theo id nên chỉ dùng được khi tệp đã có id thật.
            if (external_id, entity_id) in seen_pairs:
                stats["luot tro LAP trong cung mot phieu (bo qua)"] += 1
                continue
            seen_pairs.add((external_id, entity_id))

            file_id = stored.id or 0
            if file_id and (file_id, entity_id) in linked:
                stats["day da co duoi DB (bo qua)"] += 1
                continue

            link = FileLink(
                file_id=file_id,
                entity=SEAL_ENTITY,
                entity_id=entity_id,
                purchase_order_id=0,
                doc_type=SEAL_DOC_TYPE,
                #  Giữ đúng thứ tự người dùng đã đính bên app cũ.
                sort_order=order,
                created_by=stored.created_by,
                updated_by=stored.created_by,
            )
            link_created = _utc_dt(meta.get("createdAt"))
            if link_created:
                link.created_at = link_created
            stats["day moi"] += 1
            if apply:
                db.add(link)
                linked.add((file_id, entity_id))

        if apply:
            db.flush()

    if people.unknown_uid:
        print("\n  CANH BAO: UID nguoi tai len khong tra ra ho so nao — "
              "cot `created_by` cua nhung tep do de 0:")
        for uid, n in people.unknown_uid.most_common(10):
            print(f"    {uid}  x{n}")

    orphan = set(files) - {i for _, node in requests.items()
                           if isinstance(node, dict) for i in file_ids_of(node)}
    if orphan:
        size = sum((files[i].get("size") or 0) for i in orphan if isinstance(files.get(i), dict))
        print(f"\n  BO QUA {len(orphan)} tep MO COI ({size/1024/1024:.1f} MB) — "
              f"khong phieu nao tro toi, nap ve chi thanh rac khong ai don.")

    print("\n  NHAC: bo nap nay chi chep LOI KHAI ve tep, KHONG chep byte. "
          "Byte van nam o kho R2 cua app cu; muon xem duoc phai bat "
          "SYNC_DATXE_ENABLED va app cu phai co duong /api/v1/sync/files/{id}/url.")
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
    for branch in ("requests", "files"):
        if branch not in data:
            print(f"LOI: ban ket xuat thieu nhanh '{branch}'")
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
