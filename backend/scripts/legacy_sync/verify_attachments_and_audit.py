"""Kiểm lại TỆP ĐÍNH KÈM + LỊCH SỬ THAO TÁC vừa nạp — đọc qua ĐÚNG ĐƯỜNG MÀN HÌNH.

Đếm dòng trong bảng không chứng minh được điều gì. Bài học của đợt nạp lịch sử
duyệt: 1313 phiên + 3745 dấu vết nằm đủ dưới DB mà màn hình vẫn vẽ sai, vì thứ
người dùng thấy là do một tầng khác dựng nên. Nên tệp này gọi đúng những hàm mà
hai controller gọi — `_link_out` của đính kèm, `resolve_actor` +
`label_of_action` của nhật ký — rồi soi kết quả.

    MSYS_NO_PATHCONV=1 docker compose exec -T -e PYTHONPATH=/app api \\
        python -m scripts.legacy_sync.verify_attachments_and_audit

Mọi dòng có dấu `<-- SAI` là một thứ người dùng sẽ nhìn thấy sai. Không có dòng
nào là đạt.

BẢY ĐIỀU PHẢI ĐÚNG:

1. **Mọi phiếu nhập về đều có nhật ký.** Phiếu trống nhật ký nghĩa là thẻ *Lịch
   sử thao tác* rỗng — đúng cái đợt nạp này sinh ra để chữa.
2. **Không mã hành động nào lạ.** `label_of_action` trả lại chính mã khi không
   biết, nên mã lạ hiện ra màn hình dưới dạng chữ Anh trần giữa câu tiếng Việt.
3. **Không nhóm hành động nào = 0.** Nhóm 0 là *Không rõ*: dòng đó rơi khỏi mọi
   bộ lọc theo nhóm ở `/system/logs`.
4. **`id` tăng cùng `created_at` trong từng phiếu.** `AuditTimeline` xếp theo
   `id` giảm dần chứ không theo thời gian — hai thứ tự lệch nhau là dòng thời
   gian hiện ra đảo lộn, mà không cột nào trên màn hình lộ ra điều đó.
5. **Không dòng nào lấy GIỜ NẠP làm mốc.** So với `updated_at` chứ đừng so với
   "hôm nay": app cũ vẫn đang chạy, phiếu duyệt sáng nay mang mốc hôm nay một
   cách chính đáng. Mốc sai thì thẻ lịch sử nói mọi phiếu cũ vừa xảy ra xong.
6. **Không câu nhật ký nào rỗng.** Màn phiếu xe đọc `messageOnly`, câu rỗng là
   một dòng trống.
7. **Mọi dây đính kèm đều tra ra tệp và chạy qua `_link_out` không nổ.**
"""

import argparse
import collections

from sqlalchemy import func, select, text

import app.core.all_models  # noqa: F401  nạp đủ model trước khi truy vấn
from app.core.action_catalog import (group_of_action, is_known_action,
                                     label_of_action)
from app.core.audit import resolve_actor
from app.core.database import SessionLocal
from app.core.file_registry import is_private
from app.core.legacy_files import SOURCE_DATXE
from app.core.logging_codes import (ACTION_GROUP_UNKNOWN, ACTOR_KIND_LABELS,
                                    ACTOR_KIND_SCRIPT)
from app.modules.attachment.controller import _link_out
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.audit.model import AuditLog
from app.modules.seal_request.model import SealRequest
from app.modules.vehicle_booking.model import VehicleBooking
from scripts.legacy_sync.import_tickets import legacy_index

SEAL_ENTITY = "seal_request"
BOOKING_ENTITY = "vehicle_booking"
SEAL_DOC_TYPE = "signed_doc"

#  Lô 200 id một lượt — cùng lý do với `verify_approval_history.py`: mệnh đề IN
#  dài quá thì MySQL đổi kế hoạch truy vấn và chậm hẳn.
CHUNK = 200

_FAIL = "  <-- SAI"


def chunked(items: list, size: int = CHUNK):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def check_audit(db, problems: list[str]) -> None:
    print("=== NHAT KY: SO DONG ===")
    rows = db.execute(text(
        "select entity, actor_kind, count(*) from tab_audit_log "
        "where entity in ('seal_request','vehicle_booking') "
        "group by entity, actor_kind order by entity, actor_kind")).all()
    for entity, kind, n in rows:
        mark = "" if kind == ACTOR_KIND_SCRIPT else "   (thao tac that ben ERP)"
        print(f"  {n:>6}  {entity:<16} actor_kind={kind} "
              f"{ACTOR_KIND_LABELS.get(kind, '?')}{mark}")

    #  --- 1. phieu nao trong nhat ky ---------------------------------------
    print("\n=== NHAT KY: PHIEU NHAP VE MA KHONG CO DONG NAO ===")
    for entity, model in ((SEAL_ENTITY, SealRequest), (BOOKING_ENTITY, VehicleBooking)):
        ids = sorted(legacy_index(db, model).values())
        logged: set[int] = set()
        for part in chunked(ids):
            logged |= set(db.execute(
                select(AuditLog.entity_id).where(AuditLog.entity == entity,
                                                 AuditLog.entity_id.in_(part)).distinct()
            ).scalars())
        missing = [i for i in ids if i not in logged]
        flag = _FAIL if missing else ""
        print(f"  {entity:<16} {len(missing)}/{len(ids)} phieu trong{flag}")
        if missing:
            problems.append(f"{len(missing)} phieu {entity} khong co dong nhat ky nao")
            print(f"      vd id: {missing[:10]}")

    #  --- 2+3. ma hanh dong + nhom ------------------------------------------
    print("\n=== NHAT KY: MA HANH DONG ===")
    rows = db.execute(text(
        "select action, action_group, count(*) from tab_audit_log "
        "where entity in ('seal_request','vehicle_booking') and actor_kind = 3 "
        "group by action, action_group order by count(*) desc")).all()
    for action, group, n in rows:
        flags = []
        if not is_known_action(action):
            flags.append("ma la, hien ra chu Anh tran")
        if group == ACTION_GROUP_UNKNOWN:
            flags.append("nhom 0 = Khong ro")
        if group != group_of_action(action):
            flags.append(f"nhom lech, dung ra la {group_of_action(action)}")
        flag = (_FAIL + ": " + " · ".join(flags)) if flags else ""
        print(f"  {n:>6}  {action:<14} nhom={group}  "
              f"«{label_of_action(action)}»{flag}")
        if flags:
            problems.append(f"ma hanh dong `{action}`: {' · '.join(flags)}")

    #  --- 4. id co tang cung thoi gian trong tung phieu khong ---------------
    #  Day la phep kiem QUAN TRONG NHAT cua tep nay, va la thu khong nhin ra
    #  duoc bang mat: `AuditTimeline` xep theo `id`, khong theo `created_at`.
    print("\n=== NHAT KY: THU TU `id` SO VOI THOI GIAN (trong tung phieu) ===")
    bad_order = 0
    checked = 0
    for entity in (SEAL_ENTITY, BOOKING_ENTITY):
        per_ticket: dict[int, list] = collections.defaultdict(list)
        for entity_id, created in db.execute(
            select(AuditLog.entity_id, AuditLog.created_at)
            .where(AuditLog.entity == entity, AuditLog.actor_kind == ACTOR_KIND_SCRIPT)
            .order_by(AuditLog.entity_id, AuditLog.id)
        ).all():
            per_ticket[entity_id].append(created)
        for entity_id, stamps in per_ticket.items():
            checked += 1
            if any(a and b and b < a for a, b in zip(stamps, stamps[1:])):
                bad_order += 1
                if bad_order <= 5:
                    print(f"      {entity} #{entity_id}: moc thoi gian giam theo id")
    flag = _FAIL if bad_order else ""
    print(f"  {bad_order}/{checked} phieu co dong thoi gian dao lon{flag}")
    if bad_order:
        problems.append(f"{bad_order} phieu co `id` khong tang cung thoi gian")

    #  --- 5. moc thoi gian ---------------------------------------------------
    print("\n=== NHAT KY: MOC THOI GIAN ===")
    lo, hi = db.execute(
        select(func.min(AuditLog.created_at), func.max(AuditLog.created_at))
        .where(AuditLog.actor_kind == ACTOR_KIND_SCRIPT)).one()
    print(f"  som nhat {lo}   muon nhat {hi}")
    #  So voi `updated_at` chu KHONG so voi "hom nay": app cu van dang chay, nen
    #  phieu duoc duyet sang nay mang dung moc hom nay mot cach chinh dang. Thu
    #  can bat la dong LAY GIO NAP vi khong co `timestamp` — dong do co
    #  `created_at` trung khit `updated_at` (ca hai deu la `server_default` luc
    #  chen). Chua day mot phut giua hai moc thi gan nhu chac chan la vay.
    n_stamped_now = db.execute(
        select(func.count()).select_from(AuditLog)
        .where(AuditLog.actor_kind == ACTOR_KIND_SCRIPT,
               func.abs(func.timestampdiff(text("SECOND"), AuditLog.created_at,
                                           AuditLog.updated_at)) < 60)).scalar()
    flag = _FAIL + ": nghi la gio NAP chu khong phai gio app cu" if n_stamped_now else ""
    print(f"  {n_stamped_now} dong co `created_at` trung gio chen{flag}")
    if n_stamped_now:
        problems.append(f"{n_stamped_now} dong nhat ky mang moc thoi gian luc nap")

    #  --- 6. cau nhat ky rong ------------------------------------------------
    n_empty = db.execute(
        select(func.count()).select_from(AuditLog)
        .where(AuditLog.actor_kind == ACTOR_KIND_SCRIPT,
               func.trim(AuditLog.message) == "")).scalar()
    flag = _FAIL + ": man phieu xe doc `messageOnly`, cau rong = dong trang" if n_empty else ""
    print(f"  {n_empty} dong co cau nhat ky RONG{flag}")
    if n_empty:
        problems.append(f"{n_empty} dong nhat ky khong co cau nao")

    n_no_code = db.execute(
        select(func.count()).select_from(AuditLog)
        .where(AuditLog.actor_kind == ACTOR_KIND_SCRIPT, AuditLog.doc_code == "")).scalar()
    print(f"  {n_no_code} dong khong co ma chung tu (`doc_code`)")

    #  --- tra ten nguoi thao tac qua DUNG ham controller dung ----------------
    print("\n=== NHAT KY: TEN NGUOI THAO TAC (qua `resolve_actor`) ===")
    actors = collections.Counter()
    for user_id, n in db.execute(text(
            "select created_by, count(*) from tab_audit_log where actor_kind = 3 "
            "group by created_by")).all():
        actors[resolve_actor(db, user_id)] += n
    unresolved = sum(n for name, n in actors.items() if name in ("", "Hệ thống"))
    print(f"  {len(actors)} nguoi khac nhau · {unresolved} dong hien 'He thong' "
          "(UID app cu khong tra ra tai khoan — ten da chep vao cau)")
    for name, n in actors.most_common(5):
        print(f"      {n:>5}  {name}")

    #  --- mot cum dong dung y nhu man hinh se bay ra --------------------------
    print("\n=== NHAT KY: MOT PHIEU MAU, DOC NGUOC THEO `id` nhu man hinh ===")
    sample = db.execute(
        select(AuditLog.entity, AuditLog.entity_id)
        .where(AuditLog.entity == BOOKING_ENTITY,
               AuditLog.actor_kind == ACTOR_KIND_SCRIPT)
        .order_by(AuditLog.id.desc()).limit(1)).first()
    if sample:
        logs = db.execute(
            select(AuditLog).where(AuditLog.entity == sample[0],
                                   AuditLog.entity_id == sample[1])
            .order_by(AuditLog.id.desc())).scalars().all()
        print(f"  {sample[0]} #{sample[1]} — {len(logs)} dong:")
        for log in logs:
            #  Dung khuon cua `vehicle-booking-detail-page.tsx`: `messageOnly`
            #  nen chi co TEN va CAU, khong co nhan hanh dong dem giua.
            print(f"      {log.created_at}  {resolve_actor(db, log.created_by)} — "
                  f"{log.message or label_of_action(log.action)}")


def check_attachments(db, problems: list[str]) -> None:
    print("\n\n=== DINH KEM: SO DONG ===")
    n_files = db.execute(
        select(func.count()).select_from(StoredFile)
        .where(StoredFile.source == SOURCE_DATXE)).scalar()
    n_ext = db.execute(
        select(func.count(func.distinct(StoredFile.external_id))).select_from(StoredFile)
        .where(StoredFile.source == SOURCE_DATXE)).scalar()
    print(f"  {n_files} dong tab_file mang source='{SOURCE_DATXE}' "
          f"· {n_ext} ma tep app cu khac nhau")
    if n_files != n_ext:
        problems.append(f"tab_file co ban trung: {n_files} dong / {n_ext} ma tep")
        print(f"      {_FAIL.strip()}: co ma tep bi nap hai lan")

    rows = db.execute(
        select(FileLink.entity, FileLink.doc_type, func.count())
        .join(StoredFile, StoredFile.id == FileLink.file_id)
        .where(StoredFile.source == SOURCE_DATXE)
        .group_by(FileLink.entity, FileLink.doc_type)).all()
    for entity, doc_type, n in rows:
        flag = "" if doc_type == SEAL_DOC_TYPE else "   (roi vao muc 'Khac')"
        print(f"  {n:>6} day  {entity:<16} doc_type={doc_type or '(rong)'}{flag}")

    #  --- day mo coi: tro toi tep khong con ---------------------------------
    orphan = db.execute(text(
        "select count(*) from tab_file_link lk "
        "left join tab_file f on f.id = lk.file_id where f.id is null")).scalar()
    flag = _FAIL if orphan else ""
    print(f"  {orphan} day tro toi tep khong ton tai{flag}")
    if orphan:
        problems.append(f"{orphan} day dinh kem tro toi tep da bien mat")

    #  --- day tro toi phieu khong con ---------------------------------------
    seal_ids = set(db.execute(select(SealRequest.id)).scalars())
    links = db.execute(
        select(FileLink).join(StoredFile, StoredFile.id == FileLink.file_id)
        .where(StoredFile.source == SOURCE_DATXE)).scalars().all()
    dangling = [lk.id for lk in links if lk.entity == SEAL_ENTITY
                and lk.entity_id not in seal_ids]
    flag = _FAIL if dangling else ""
    print(f"  {len(dangling)} day tro toi phieu khong ton tai{flag}")
    if dangling:
        problems.append(f"{len(dangling)} day dinh kem tro toi phieu da bien mat")

    #  --- 7. chay THAT qua `_link_out` --------------------------------------
    print("\n=== DINH KEM: CHAY QUA `_link_out` (dung ham controller tra ve) ===")
    files = {f.id: f for f in db.execute(
        select(StoredFile).where(StoredFile.source == SOURCE_DATXE)).scalars()}
    broke = no_name = leaked_url = 0
    sample = None
    for lk in links:
        f = files.get(lk.file_id)
        if not f:
            continue
        try:
            out = _link_out(lk, f)
        except Exception as exc:                      # noqa: BLE001
            broke += 1
            if broke == 1:
                problems.append(f"`_link_out` no tren day #{lk.id}: {exc}")
                print(f"      {_FAIL.strip()} day #{lk.id}: {exc}")
            continue
        if not (out["filename"] or "").strip():
            no_name += 1
        #  Entity rieng tu thi `url` PHAI rong — do la duong doc thang bucket,
        #  khong qua kiem quyen.
        if is_private(lk.entity) and out["url"]:
            leaked_url += 1
        sample = sample or out
    print(f"  {len(links)} day chay qua ham, {broke} day lam ham no"
          f"{_FAIL if broke else ''}")
    print(f"  {no_name} day khong co ten tep{_FAIL if no_name else ''}")
    print(f"  {leaked_url} day lo `url` doc thang bucket du entity rieng tu"
          f"{_FAIL if leaked_url else ''}")
    if no_name:
        problems.append(f"{no_name} day dinh kem khong co ten tep")
    if leaked_url:
        problems.append(f"{leaked_url} day rieng tu van tra ve `url` doc thang bucket")
    if sample:
        print("  mot dong mau dung nhu API tra ve:")
        for key in ("id", "file_id", "filename", "url", "content_type", "size",
                    "entity", "entity_id", "doc_type", "sort_order"):
            print(f"      {key:<13} {sample[key]!r}")

    #  --- tep khong co byte: bao so, khong bao loi ---------------------------
    #  `file_key` cua app cu tro vao bucket KHAC, khoa R2 cua ERP khong voi toi.
    #  Day la HAN CHE DA BIET, khong phai loi nap — nen dem va noi ro chu khong
    #  danh dau SAI.
    no_key = sum(1 for f in files.values() if not (f.file_key or "").strip())
    print(f"\n  NHAC: {len(files)} tep deu chi co PHAN MO TA. {no_key} tep khong "
          "co ca khoa kho.")
    print("  Tai duoc byte ve hay khong phu thuoc cau hinh dong bo, xem "
          "`core/legacy_files.read_file_bytes`.")


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    db = SessionLocal()
    problems: list[str] = []
    try:
        check_audit(db, problems)
        check_attachments(db, problems)
    finally:
        db.close()

    print("\n\n=== KET LUAN ===")
    if problems:
        for p in problems:
            print(f"  SAI: {p}")
        return 1
    print("  Khong thay loi nao.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
