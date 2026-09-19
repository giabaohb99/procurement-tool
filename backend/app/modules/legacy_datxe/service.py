"""CỬA DUY NHẤT nhận một phiếu từ app đặt xe cũ về ERP.

Cái móc bên app cũ (§5.1) và vòng quét lưới an toàn (§11) đều gọi đúng hàm
`apply_legacy_record` này. Hai đường vào, một phép xử — nếu mỗi đường tự viết
lấy một bản thì hôm nay giống nhau, mai ai đó vá một bên, và từ đó phiếu về qua
cái móc khác phiếu về qua vòng quét ở vài ô. Không lỗi, không cảnh báo, chỉ là
số liệu lệch.

MỘT LƯỢT ĐI QUA ĐÂY, THEO THỨ TỰ:

1. Băm phần nghiệp vụ. Lần trước đã xử THÀNH CÔNG đúng nội dung này thì thôi,
   không ghi thêm dòng sổ nào — vòng quét chạy mỗi vài phút trên 480 phiếu, ghi
   hết thì sổ ngập và chẳng ai đọc nổi.
2. Ghi dòng sổ *chờ* rồi mới làm (luật §3.2). `event_id` đã nhận rồi thì dừng.
3. Bọc toàn bộ phần ghi trong `suppress_outbound()` — chống hai bên đá qua đá
   lại vô tận.
4. Chưa có `legacy_id` thì tạo mới, sinh mã `DD{id:06d}` / `DX{id:06d}`.
5. Có rồi thì `copy_legacy_fields`: ghi đè hết, trừ ghi rỗng đè lên đang có.
6. Phiếu ĐÃ CHỐT bên ERP (Hoàn thành / Từ chối / Đã hủy) thì không nhận nội
   dung nữa, chỉ nhận đổi trạng thái (§9 mục 5).

Hỏng ở bất cứ đâu thì `rollback` và dòng sổ ghi *lỗi* kèm nguyên văn câu lỗi;
vòng quét sau sẽ gặp lại phiếu đó. Cố ý KHÔNG nuốt lỗi thành *thành công*: sổ mà
nói dối thì không còn dùng để tra sự cố được nữa.
"""
import collections
import logging

from sqlalchemy import select

from app.modules.seal_request.model import (
    SEAL_CANCELLED,
    SEAL_COMPLETED,
    SEAL_REJECTED,
    SealRequest,
    SealRequestCompany,
    SealType,
)
from app.modules.sync_log.constants import SyncAction
from app.modules.sync_log.model import SyncLog
from app.modules.sync_log.registry import SOURCE_DATXE
from app.modules.sync_log.service import (
    compute_hash,
    finish_failed,
    finish_ok,
    finish_skipped,
    is_unchanged,
    mark_running,
    open_entry,
    suppress_outbound,
)
from app.modules.vehicle_booking.model import (
    BK_CANCELLED,
    BK_COMPLETED,
    BK_REJECTED,
    VehicleBooking,
)

from . import firebase
from .builder import (
    LEGACY_SEAL_TYPE_NAME,
    SYSTEM_ACTOR_ID,
    PeopleResolver,
    build_booking,
    build_seal,
    copy_legacy_fields,
    ensure_seal_type,
    fit_to_columns,
)
from .resolver import LegacyCatalog

LOGGER = logging.getLogger(__name__)

ENTITY_SEAL = "seal_request"
ENTITY_BOOKING = "vehicle_booking"

#: Loại phiếu bên app cũ -> đối tượng đồng bộ bên ERP.
ENTITY_FROM_LEGACY_TYPE = {
    "SEAL_REQUEST": ENTITY_SEAL,
    "CAR_BOOKING": ENTITY_BOOKING,
    "DELIVERY": ENTITY_BOOKING,
}

#: Tiền tố mã phiếu, sáu chữ số. Dạng này không bao giờ đụng dạng ba chữ số ERP
#: tự sinh (`DD001`), nên nhìn bảng là phân biệt được phiếu nhập từ app cũ.
CODE_PREFIX = {ENTITY_SEAL: "DD", ENTITY_BOOKING: "DX"}

#: Trạng thái ĐÃ CHỐT — phiếu tới đây thì nội dung đóng băng.
CLOSED_STATUSES = {
    ENTITY_SEAL: {SEAL_COMPLETED, SEAL_REJECTED, SEAL_CANCELLED},
    ENTITY_BOOKING: {BK_COMPLETED, BK_REJECTED, BK_CANCELLED},
}

MODEL = {ENTITY_SEAL: SealRequest, ENTITY_BOOKING: VehicleBooking}

#: Cờ sổ đồng bộ riêng của lượt nhận phiếu. Nhãn khai ở `sync_log/registry.py`.
WARN_CLOSED_LOCKED = "closed_locked"
WARN_BLANK_KEPT = "blank_kept"
WARN_DRIVER_DELETED = "driver_deleted"
WARN_TRUNCATED = "truncated"

#: Tiền tố khóa đếm của bộ dựng -> cờ tương ứng. Bộ dựng đếm bằng câu tiếng Việt
#: không dấu (nó vốn viết cho kịch bản nạp một lần, in thẳng ra màn hình); ở đây
#: phải đổi thành cờ để màn sổ còn lọc lại được.
WARN_FROM_STATS = (
    ("giu nguyen vi app cu khong tra ra", WARN_BLANK_KEPT),
    ("o qua dai", WARN_TRUNCATED),
    ("tai xe da bi xoa ben app cu", WARN_DRIVER_DELETED),
)


def entity_of(node: dict) -> str:
    """Phiếu này bên ERP là loại gì. Rỗng = loại lạ, người gọi tự xử."""
    return ENTITY_FROM_LEGACY_TYPE.get((node or {}).get("type") or "", "")


def get_seal_type_id(db) -> int:
    """Id loại con dấu gom chung, tạo nếu chưa có.

    Hỏi thẳng DB trước rồi mới nhờ `ensure_seal_type`: hàm bên bộ dựng CÓ IN ra
    màn hình (nó viết cho kịch bản nạp một lần), gọi nó cho từng phiếu thì mỗi
    phiếu về là một dòng rác trong log ứng dụng.
    """
    found = db.execute(
        select(SealType.id)
        .where(SealType.name == LEGACY_SEAL_TYPE_NAME)).scalar_one_or_none()
    return found or ensure_seal_type(db, apply=True)


def collect_warnings(catalog_flags, stats) -> list[str]:
    """Gộp cờ của bộ tra danh mục với cờ suy từ bộ đếm của bộ dựng."""
    flags = list(catalog_flags)
    for name in stats:
        for prefix, flag in WARN_FROM_STATS:
            if name.startswith(prefix) and flag not in flags:
                flags.append(flag)
    return flags


def sync_seal_companies(db, seal: SealRequest, company_ids: list[int]) -> bool:
    """Bảng nối công ty của phiếu dấu. Trả về có đụng gì không.

    Chỉ phiếu dấu mới có nhiều pháp nhân, và danh sách này là nguồn của phạm vi
    dữ liệu (`core/scoping.py` nhánh `seal_request`) — sai ở đây là sai người
    được thấy phiếu, nên phải theo sát bên app cũ cả chiều thêm lẫn chiều bớt.
    """
    if not company_ids and getattr(seal, "company_id", 0) > 0:
        company_ids = [seal.company_id]
    current = {row.company_id: row for row in db.execute(
        select(SealRequestCompany)
        .where(SealRequestCompany.seal_request_id == seal.id)).scalars()}
    touched = False
    for cid in company_ids:
        if cid not in current:
            db.add(SealRequestCompany(seal_request_id=seal.id, company_id=cid,
                                      created_by=SYSTEM_ACTOR_ID,
                                      updated_by=SYSTEM_ACTOR_ID))
            touched = True
    for cid, row in current.items():
        if cid not in company_ids:
            db.delete(row)
            touched = True
    return touched


def find_local_id(db, entity: str, legacy_id: str) -> int:
    """Id hàng bên ERP đang mang khóa app cũ này, `0` nếu chưa có.

    Cửa nhận cần nó cho nhánh *không sinh dòng sổ nào* (trùng `event_id`, hoặc
    nội dung y hệt lần trước): bên kia vẫn chờ `erp_id` để ghi ngược, trả `0`
    là bảo nó xóa trắng mối nối đang có.
    """
    model = MODEL.get(entity)
    if model is None or not legacy_id:
        return 0
    row = db.execute(
        select(model.id).where(model.legacy_id == legacy_id)).scalar_one_or_none()
    return int(row or 0)


def apply_legacy_record(
    db,
    *,
    node: dict,
    legacy_id: str,
    entity: str = "",
    event_id: str = "",
    run_id: int = 0,
    people: PeopleResolver | None = None,
    catalog: LegacyCatalog | None = None,
    seal_type_id: int = 0,
    user_id: int = 0,
    force: bool = False,
) -> SyncLog | None:
    """Nhận MỘT phiếu từ app cũ. Trả dòng sổ đã đóng, hoặc `None`.

    `None` nghĩa là lượt này không sinh dòng sổ nào: nội dung y hệt lần trước đã
    xử thành công, hoặc `event_id` đã nhận rồi. Cả hai đều là chuyện thường của
    một vòng quét, không phải lỗi.

    `people` / `catalog` / `seal_type_id` truyền vào được để một vòng quét nhiều
    phiếu chỉ dựng chúng một lần — hàm dựng của hai cái đầu đều nạp sẵn cả bảng.

    `force=True` bỏ qua phép so mã băm, tức là **xử lại phiếu dù nội dung bên app
    cũ không đổi**. Cần có, vì phép so kia chỉ trả lời được "nội dung NGUỒN có đổi
    không", không trả lời được "bên ERP đã dựng đủ thứ suy ra từ nội dung đó
    chưa". Ngày 18/09/2026 có 353 phiếu về ERP trước khi bộ dựng luồng duyệt ra
    đời; từ đó mọi lượt quét đều thoát ở dòng dưới đây, và chúng nằm im không
    luồng duyệt cho tới khi có người chạy tay một đợt vá. Đường `force` là để lần
    sau không phải làm thế nữa — xem `tasks.py::full_sweep`.
    """
    entity = entity or entity_of(node)
    if entity not in MODEL:
        raise ValueError(f"Loại phiếu app cũ không nhận ra: {(node or {}).get('type')!r}")
    if not legacy_id:
        raise ValueError("Thiếu khóa app cũ (legacy_id)")

    content_hash = compute_hash(node)
    if not force and is_unchanged(db, SOURCE_DATXE, entity, legacy_id, content_hash):
        return None

    entry = open_entry(db, source=SOURCE_DATXE, entity=entity, legacy_id=legacy_id,
                       event_id=event_id, payload=node, content_hash=content_hash,
                       run_id=run_id, user_id=user_id,
                       action=int(SyncAction.UPDATE))
    if entry is None:
        return None

    return run_entry(db, entry, node=node, entity=entity, legacy_id=legacy_id,
                     content_hash=content_hash, people=people, catalog=catalog,
                     seal_type_id=seal_type_id, user_id=user_id)


def run_entry(
    db,
    entry: SyncLog,
    *,
    node: dict,
    entity: str = "",
    legacy_id: str = "",
    content_hash: str = "",
    people: PeopleResolver | None = None,
    catalog: LegacyCatalog | None = None,
    seal_type_id: int = 0,
    user_id: int = 0,
) -> SyncLog:
    """Chạy MỘT dòng sổ đang mở. Luôn trả về dòng đó, đã đóng.

    Tách khỏi `apply_legacy_record` vì có hai đường tới đây: dòng vừa mở của một
    phiếu mới về, và dòng *chờ* do nút "Chạy lại" sinh ra (`clone_for_retry`) —
    dòng thứ hai đã nằm sẵn trong sổ, mở thêm dòng nữa là ghi đôi một sự việc.
    """
    entity = entity or entry.entity
    legacy_id = legacy_id or entry.legacy_id
    content_hash = content_hash or entry.content_hash or compute_hash(node)
    mark_running(db, entry)

    try:
        with suppress_outbound():
            return _write(db, entry, entity=entity, legacy_id=legacy_id, node=node,
                          people=people, catalog=catalog, seal_type_id=seal_type_id,
                          content_hash=content_hash, user_id=user_id)
    except Exception as exc:  # noqa: BLE001 — câu lỗi nào cũng phải vào sổ
        db.rollback()
        LOGGER.exception("Nhận phiếu %s %r từ app cũ hỏng", entity, legacy_id)
        return finish_failed(db, entry, f"{type(exc).__name__}: {exc}")


def _write(db, entry: SyncLog, *, entity: str, legacy_id: str, node: dict,
           people: PeopleResolver | None, catalog: LegacyCatalog | None,
           seal_type_id: int, content_hash: str, user_id: int) -> SyncLog:
    stats: collections.Counter = collections.Counter()
    people = people or PeopleResolver(db)
    catalog = catalog or LegacyCatalog(db, actor_id=user_id)
    model = MODEL[entity]
    actor = user_id or SYSTEM_ACTOR_ID

    #  Bộ tra danh mục sống suốt cả vòng quét nên `warnings` của nó là sổ CỘNG
    #  DỒN. Lấy mốc trước khi dựng để dòng sổ của phiếu này chỉ mang cờ của
    #  chính nó — không thì phiếu thứ hai trở đi thừa hưởng cảnh báo của phiếu
    #  đầu, và cả trăm dòng cùng đỏ lên vì một ca duy nhất.
    warn_mark = len(catalog.warnings)

    existing = db.execute(
        select(model).where(model.legacy_id == legacy_id)).scalar_one_or_none()

    if entity == ENTITY_SEAL:
        if not seal_type_id:
            seal_type_id = get_seal_type_id(db)
        fresh, company_ids = build_seal(db, legacy_id, node, people, seal_type_id,
                                        catalog.companies, catalog.departments, stats)
    else:
        fresh = build_booking(db, legacy_id, node, people, catalog.companies,
                              catalog.vehicles, catalog.drivers, stats)
        company_ids = []
    fit_to_columns(fresh, stats)

    def flags() -> list[str]:
        return collect_warnings(catalog.warnings[warn_mark:], stats)

    # --- chưa có: tạo mới -------------------------------------------------
    if existing is None:
        db.add(fresh)
        db.flush()
        #  Mã sinh SAU `flush()` vì tới lúc đó mới có id.
        fresh.code = f"{CODE_PREFIX[entity]}{fresh.id:06d}"
        if entity == ENTITY_SEAL:
            sync_seal_companies(db, fresh, company_ids)
        sync_legacy_audit_logs(db, entity=entity, entity_id=fresh.id, code=fresh.code,
                               node=node, people=people)
        sync_legacy_attachments(db, entity=entity, entity_id=fresh.id, node=node,
                                people=people)
        sync_legacy_approval_history(db, entity=entity, entity_id=fresh.id, code=fresh.code,
                                     purpose=getattr(fresh, "purpose", "") or "", node=node, people=people)
        db.commit()
        entry.action = int(SyncAction.CREATE)
        return finish_ok(db, entry, f"Đã tạo phiếu {fresh.code}", local_id=fresh.id,
                         warnings=flags(), content_hash=content_hash)

    # --- đã chốt: đóng băng nội dung, chỉ nhận đổi trạng thái --------------
    #  KHÔNG `rollback` ở nhánh này: bộ tra danh mục có thể vừa đóng dấu
    #  `legacy_id` lên một hàng có sẵn, và dấu đó đúng bất kể phiếu này có được
    #  ghi hay không. `finish_*` tự `commit` nên phần đó đi theo.
    if existing.status in CLOSED_STATUSES[entity]:
        sync_legacy_audit_logs(db, entity=entity, entity_id=existing.id, code=existing.code,
                               node=node, people=people)
        sync_legacy_attachments(db, entity=entity, entity_id=existing.id, node=node,
                                people=people)
        sync_legacy_approval_history(db, entity=entity, entity_id=existing.id, code=existing.code,
                                     purpose=getattr(existing, "purpose", "") or "", node=node, people=people)
        if fresh.status and fresh.status != existing.status:
            old = existing.status
            existing.status = fresh.status
            existing.updated_by = actor
            entry.action = int(SyncAction.STATUS_CHANGE)
            return finish_ok(db, entry,
                             f"Phiếu đã chốt — chỉ nhận đổi trạng thái {old} -> "
                             f"{fresh.status}", local_id=existing.id,
                             warnings=flags() + [WARN_CLOSED_LOCKED],
                             content_hash=content_hash)
        return finish_skipped(db, entry, "Phiếu đã chốt bên ERP, không nhận cập nhật",
                              local_id=existing.id,
                              warnings=flags() + [WARN_CLOSED_LOCKED])

    # --- đang mở: ghi đè hết, trừ ghi rỗng đè lên đang có ------------------
    changed = copy_legacy_fields(existing, fresh, stats)
    touched = sync_seal_companies(db, existing, company_ids) if entity == ENTITY_SEAL else False
    sync_legacy_audit_logs(db, entity=entity, entity_id=existing.id, code=existing.code,
                           node=node, people=people)
    sync_legacy_attachments(db, entity=entity, entity_id=existing.id, node=node,
                            people=people)
    sync_legacy_approval_history(db, entity=entity, entity_id=existing.id, code=existing.code,
                                 purpose=getattr(existing, "purpose", "") or "", node=node, people=people)
    if not changed and not touched:
        #  Cố ý KHÔNG chốt `content_hash` vào dòng *bỏ qua*: chỉ dòng THÀNH CÔNG
        #  mới chặn được lượt sau (`is_unchanged`). Phiếu đổi ở ô mà ERP không
        #  giữ thì mỗi lượt quét lại ghi một dòng bỏ qua — đó là giá của việc
        #  không nói dối trong sổ.
        return finish_skipped(db, entry, "Không có gì thay đổi", local_id=existing.id,
                              warnings=flags())

    existing.updated_by = actor
    db.commit()
    return finish_ok(db, entry,
                     f"Đã cập nhật {len(changed)} ô: "
                     f"{', '.join(changed) or '(bảng nối công ty)'}",
                     local_id=existing.id, warnings=flags(),
                     content_hash=content_hash)


def sync_legacy_audit_logs(db, *, entity: str, entity_id: int, code: str,
                           node: dict, people: PeopleResolver | None = None) -> int:
    """Đồng bộ mảng approval.history của phiếu app cũ sang tab_audit_log.

    Mỗi lần phiếu được cập nhật từ Firebase, xóa các dòng nhật ký cũ do script
    ghi (actor_kind = ACTOR_KIND_SCRIPT) rồi ghi lại toàn bộ từ history mới nhất.
    Dòng do người dùng thật tạo bên ERP (actor_kind khác) KHÔNG bị xóa.
    """
    hist = (node.get("approval") or {}).get("history") or []
    if not hist:
        return 0

    from app.core.logging_codes import ACTOR_KIND_SCRIPT
    from app.modules.audit.model import AuditLog
    from scripts.legacy_sync.import_audit_log import build_rows

    #  Xóa các dòng nhật ký cũ do script nạp từ app cũ trước đó.
    #  Dòng do người dùng thật tạo bên ERP (actor_kind != ACTOR_KIND_SCRIPT)
    #  được giữ nguyên — chúng là thao tác thật, không phải dữ liệu đồng bộ.
    old_rows = list(db.execute(
        select(AuditLog)
        .where(
            AuditLog.entity == entity,
            AuditLog.entity_id == entity_id,
            AuditLog.actor_kind == ACTOR_KIND_SCRIPT,
        )
    ).scalars())
    for row in old_rows:
        db.delete(row)
    if old_rows:
        db.flush()

    people = people or PeopleResolver(db)
    noun = "yêu cầu đóng dấu" if entity == ENTITY_SEAL else "yêu cầu đặt xe"
    stats: collections.Counter = collections.Counter()

    rows = build_rows(entity, entity_id, noun, code, hist, people, stats)
    for row in rows:
        db.add(row)
    return len(rows)


def sync_legacy_attachments(db, *, entity: str, entity_id: int, node: dict,
                            people: PeopleResolver | None = None) -> int:
    """Tự động đồng bộ mảng details.attachedFileIds của phiếu app cũ sang tab_file + tab_file_link.

    Đảm bảo khối 'Chứng từ & Tài liệu đính kèm' trên màn chi tiết ERP hiển thị đủ các tệp.
    """
    if entity != ENTITY_SEAL:
        return 0
    details = node.get("details") or {}
    ids = details.get("attachedFileIds") or []
    if isinstance(ids, dict):
        ids = [ids[k] for k in sorted(ids, key=lambda k: (len(k), k))]
    file_ids = [i for i in ids if isinstance(i, str) and i.strip()]
    if not file_ids:
        return 0

    from app.core.legacy_files import SOURCE_DATXE
    from app.modules.attachment.model import FileLink, StoredFile
    from scripts.legacy_sync.import_attachments import build_stored_file

    people = people or PeopleResolver(db)
    added = 0

    for external_id in file_ids:
        sf = db.execute(
            select(StoredFile).where(
                StoredFile.source == SOURCE_DATXE,
                StoredFile.external_id == external_id
            )
        ).scalar_one_or_none()

        if sf is None:
            file_meta = firebase.read_node(f"files/{external_id}") or {}
            if not file_meta:
                continue
            stats: collections.Counter = collections.Counter()
            sf = build_stored_file(external_id, file_meta, people, stats)
            db.add(sf)
            db.flush()

        link = db.execute(
            select(FileLink.id).where(
                FileLink.file_id == sf.id,
                FileLink.entity == entity,
                FileLink.entity_id == entity_id
            )
        ).scalar_one_or_none()

        if link is None:
            fl = FileLink(
                file_id=sf.id,
                entity=entity,
                entity_id=entity_id,
                doc_type="signed_doc",
                created_by=sf.created_by,
                updated_by=sf.updated_by,
            )
            db.add(fl)
            added += 1

    return added


def sync_legacy_approval_history(db, *, entity: str, entity_id: int, code: str, purpose: str,
                                node: dict, people: PeopleResolver | None = None) -> int:
    """Đồng bộ mảng approval.history của phiếu app cũ sang tab_approval_instance,
    tab_approval_task, tab_approval_action để widget 'LUỒNG DUYỆT NHIỀU BƯỚC'
    hiển thị đúng quy trình phê duyệt.

    Mỗi lần phiếu được cập nhật từ Firebase, xóa toàn bộ phiên duyệt cũ (instance
    + task + action) rồi tạo lại từ history mới nhất. Chỉ xóa phiên do script nạp
    (flow_id = 0) — phiên duyệt thật bên ERP (flow_id > 0) được bảo toàn.
    """
    from app.modules.approval.instance_model import (
        ApprovalAction,
        ApprovalInstance,
        ApprovalTask,
    )
    from scripts.legacy_sync.import_approval_history import (
        _step_names,
        build_actions,
        build_instance,
        build_tasks,
    )

    #  Xóa các phiên duyệt do script nạp từ app cũ (flow_id = 0).
    #  Phiên duyệt thật bên ERP (flow_id > 0) KHÔNG bị xóa — chúng là
    #  quyết định thật của người dùng, không phải dữ liệu phản chiếu.
    old_instances = list(db.execute(
        select(ApprovalInstance)
        .where(
            ApprovalInstance.entity == entity,
            ApprovalInstance.entity_id == entity_id,
            ApprovalInstance.flow_id == 0,
        )
    ).scalars())
    for inst in old_instances:
        inst_id = inst.id
        #  Xóa action trước (không có FK cascade trong ORM).
        for action_row in db.execute(
            select(ApprovalAction).where(ApprovalAction.instance_id == inst_id)
        ).scalars():
            db.delete(action_row)
        for task_row in db.execute(
            select(ApprovalTask).where(ApprovalTask.instance_id == inst_id)
        ).scalars():
            db.delete(task_row)
        db.delete(inst)
    if old_instances:
        db.flush()

    people = people or PeopleResolver(db)
    stats: collections.Counter = collections.Counter()
    hist = (node.get("approval") or {}).get("history") or []

    instance = build_instance(entity, entity_id, code or "", purpose or "", node, people, stats)
    if instance is None:
        return 0

    names = _step_names((node.get("approval") or {}).get("workflowSnapshot") or {})
    db.add(instance)
    db.flush()

    tasks, decisive = build_tasks(instance.id, hist, names, people, stats)
    for task_row in tasks.values():
        db.add(task_row)
    db.flush()

    for action_row in build_actions(instance.id, hist, names, people, stats, tasks, decisive):
        db.add(action_row)
    db.flush()

    return 1
