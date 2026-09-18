"""Nạp lịch sử duyệt của 1313 phiếu app đặt xe cũ vào bộ máy duyệt ERP.

    5095 dòng `approval.history`
      -> 1313 `tab_approval_instance`  (mỗi phiếu MỘT phiên)
      -> 3745 `tab_approval_action`    (3534 lượt duyệt thật + 211 dòng sửa phiếu)
      ->      cột điều phối của `tab_vehicle_booking` (1350 mốc chuyến)

CHẠY SAU `import_tickets.py` — không có đường nào khác: `ApprovalInstance.entity_id`
trỏ thẳng vào id phiếu ERP, chưa có phiếu thì không có gì để trỏ.

CHẠY ĐƯỢC NHIỀU LẦN: phiếu nào đã có phiên duyệt thì bỏ qua cả cụm, không ghi
bản thứ hai. Mặc định chỉ xem trước, `--apply` mới ghi.

    python -m scripts.legacy_sync.import_approval_history --export /tmp/fb-export.json
    python -m scripts.legacy_sync.import_approval_history --export /tmp/fb-export.json --apply

BA NHÓM TRONG CÙNG MỘT MẢNG — đo trên bản kết xuất, xem §P1.1 TIEN-DO.md:

- **Lượt duyệt thật** (3534): `created` · `approved` · `needs_correction` ·
  `admin_canceled` · `rejected` · `canceled` -> `tab_approval_action`.
- **Mốc điều phối chuyến** (1350): `dispatched` · `re-dispatched` ·
  `driver_accepted` · `trip_started` · `trip_completed`. Chúng nằm chung mảng
  với lượt duyệt nên đổ cả mảng vào là gọn nhất — và là nói sai một điều vào
  đúng cái bảng cả hệ dùng để tra "ai đã ký". Tài xế bấm *Bắt đầu chuyến*
  không phải người duyệt phiếu. Chỗ đúng của chúng là cột `dispatched_at` ·
  `dispatched_by` · `driver_status` · `actual_start_time` · `actual_end_time`
  trên chính `tab_vehicle_booking`, và `import_tickets.py` đã đổ sẵn từ nhánh
  `details.dispatch`. Ở đây chỉ **vá chỗ nhánh đó bỏ trống** (13 phiếu có dòng
  `dispatched` mà `dispatchedAt` rỗng, 4 phiếu có `driver_accepted` mà
  `driverStatus` rỗng) — vá khi ô đang trống, không đè lên ô đã có.
- **Sửa phiếu** (211 `edited`): giữ lại vì nó giải thích VÌ SAO có lượt duyệt
  thứ hai trên cùng một phiếu, nhưng ghi bằng `ACTION_COMMENT` chứ không phải
  `ACTION_APPROVE`.

HAI THẾ GIỚI ID TRONG CÙNG MỘT DÒNG — bẫy lớn nhất của tệp này:

- `tab_approval_*` dùng **ID NHÂN SỰ**: `started_by_employee_id`,
  `actor_employee_id`, `on_behalf_of_id`. `serializer._name_of` tra thẳng
  `tab_employee`, nên nhét id tài khoản vào là mọi dòng dấu vết hiện tên
  người khác — im lặng, không lỗi.
- `created_by` / `updated_by` (cột kiểm toán chung) vẫn là **ID TÀI KHOẢN**,
  giống hệt phiếu bên `import_tickets.py`.

Nên ở đây dùng CẢ HAI cửa của `PeopleResolver`: `.employee(uid).id` cho cột
nhân sự, `.user_id(uid)` cho cột kiểm toán.

NHỮNG THỨ BỘ NẠP NÀY CỐ Ý KHÔNG LÀM:

- **KHÔNG đi qua `instance_service.start`.** Hàm đó chọn luồng ERP đang sống và
  MỞ VIỆC CHỜ THẬT. Chạy nó cho 1313 phiếu cũ là ném hơn nghìn việc đã xử xong
  vào hàng chờ của người thật.
- **KHÔNG mở việc CHỜ.** `tab_approval_task` có ghi, nhưng chỉ ở trạng thái ĐÃ
  ĐÓNG (`TASK_APPROVED` · `TASK_REJECTED` · `TASK_CANCELLED`) — xem `build_tasks`.
  Không dòng nào mang `TASK_PENDING`/`TASK_WAITING`, nên màn "Việc của tôi"
  (truy vấn đúng hai mã đó) không nhận thêm việc nào.
- **KHÔNG gán `flow_id` của một luồng ERP đang sống** (để 0, `flow_version` 0).
  Phiếu cũ chưa từng chạy luồng nào bên này; gán bừa là khai rằng luồng đó đã
  ký những phiếu nó chưa từng thấy, và sửa luồng đó về sau sẽ đọc như thể lịch
  sử đổi theo.

34 PHIẾU CÒN `pending_approval` nhập về dạng `INSTANCE_RUNNING` **không kèm
việc chờ**. Đó là cố ý và có hai mặt, phải biết cả hai: phiên đang mở chiếm
`running_slot` nên `block_legacy_path` khóa luôn ba nút duyệt thẳng bên ERP —
đúng thứ ta muốn khi app cũ vẫn là nơi xử nốt mấy phiếu đó (không thì hai bên
ký hai đường, lệch nhau ngay), nhưng cũng nghĩa là **bên ERP không ai bấm duyệt
được cho tới khi P2 quyết**. Danh sách 34 phiếu in ra cuối mỗi lần chạy.
"""

import argparse
import collections
import json
import sys

from sqlalchemy import select

import app.core.all_models  # noqa: F401  nạp đủ model để SQLAlchemy dựng xong quan hệ
from app.core.database import SessionLocal
from app.modules.approval.flow_model import (
    APPROVER_DEPT_HEAD,
    APPROVER_EMPLOYEE,
    APPROVER_ROLE,
    MULTI_ANY,
    NODE_APPROVAL,
    NO_APPROVER_BLOCK,
    ROLE_APPROVE,
    SKIP_NONE,
)
from app.modules.approval.flow_service import NODE_FIELDS
from app.modules.approval.instance_model import (
    ACTION_APPROVE,
    ACTION_COMMENT,
    ACTION_REJECT,
    ACTION_RETURN,
    ACTION_START,
    ACTION_WITHDRAW,
    INSTANCE_APPROVED,
    INSTANCE_REJECTED,
    INSTANCE_RETURNED,
    INSTANCE_RUNNING,
    INSTANCE_WITHDRAWN,
    TASK_APPROVED,
    TASK_CANCELLED,
    TASK_REJECTED,
    ApprovalAction,
    ApprovalInstance,
    ApprovalTask,
)
from app.modules.seal_request.model import SealRequest
from app.modules.vehicle_booking.model import (
    DRV_ACCEPTED,
    DRV_COMPLETED,
    DRV_NONE,
    DRV_ONGOING,
    VehicleBooking,
)
from app.modules.legacy_datxe.builder import (
    SYSTEM_ACTOR_ID,
    PeopleResolver,
    _utc_dt,
    _utc_iso,
    legacy_index,
)

SEAL_ENTITY = "seal_request"
BOOKING_ENTITY = "vehicle_booking"

#  Lượt duyệt thật + dòng sửa phiếu. Mọi `action` khác của app cũ hoặc là mốc
#  chuyến (xem `TRIP_ACTIONS`) hoặc là mã lạ — cả hai đều được đếm riêng.
ACTION_FROM_LEGACY = {
    "created": ACTION_START,
    "approved": ACTION_APPROVE,
    "rejected": ACTION_REJECT,
    "needs_correction": ACTION_RETURN,
    "canceled": ACTION_WITHDRAW,
    "admin_canceled": ACTION_WITHDRAW,
}

ADMIN_CANCEL_PREFIX = "[Quản trị hủy] "

#  KẾT CỤC của một chặng -> trạng thái VIỆC, và chỉ ba mã ĐÃ ĐÓNG này. Xem
#  `build_tasks` để biết vì sao bảng việc phải có mặt.
TASK_STATUS_FROM_LEGACY = {
    "approved": TASK_APPROVED,
    "rejected": TASK_REJECTED,
    #  Trả về người nộp: bộ máy ERP hủy việc của chặng đó, và `steps_service`
    #  đọc «việc đã hủy + phiên đang ở trạng thái trả về» thành chấm "trả về".
    "needs_correction": TASK_CANCELLED,
}

TRIP_ACTIONS = ("dispatched", "re-dispatched", "driver_accepted",
                "trip_started", "trip_completed")

INSTANCE_STATUS_FROM_LEGACY = {
    "pending_approval": INSTANCE_RUNNING,
    "completed": INSTANCE_APPROVED,
    "fully_approved": INSTANCE_APPROVED,
    "dispatched": INSTANCE_APPROVED,
    "rejected": INSTANCE_REJECTED,
    "needs_correction": INSTANCE_RETURNED,
    "canceled": INSTANCE_WITHDRAWN,
}

#  Mốc chuyến -> trạng thái tài xế, xếp theo mức ĐI XA NHẤT. Dùng để vá cột
#  `driver_status` khi nhánh `details.dispatch` bỏ trống nó.
DRIVER_STATUS_FROM_ACTION = {
    "driver_accepted": DRV_ACCEPTED,
    "trip_started": DRV_ONGOING,
    "trip_completed": DRV_COMPLETED,
}
DRIVER_STATUS_RANK = {DRV_NONE: 0, DRV_ACCEPTED: 1, DRV_ONGOING: 2, DRV_COMPLETED: 3}

#  Cách chọn người duyệt bên app cũ -> bên ERP. Bản chụp này là để ĐỌC LẠI,
#  không phải để chạy, nên chỗ nào ERP không có khái niệm tương đương thì lấy
#  cái gần nhất và giữ nguyên văn bản gốc dưới khóa `legacy`.
APPROVER_KIND_FROM_LEGACY = {
    "SUBMITTER_CHOICE": APPROVER_EMPLOYEE,   # người tạo tự chọn — ERP không có
    "ROLE": APPROVER_ROLE,
    "DYNAMIC_ROLE": APPROVER_DEPT_HEAD,      # app cũ chỉ dùng cho "HOD"
}


# ---------------------------------------------------------------------------
# Bản chụp luồng
# ---------------------------------------------------------------------------

def build_snapshot(snap: dict, people: PeopleResolver,
                   stats: collections.Counter) -> str:
    """`workflowSnapshot` của app cũ -> khuôn `{"nodes": [...]}` của ERP.

    KHÔNG nhét nguyên dạng Firebase: `flow_service.steps()` đọc `nodes` để đếm
    số chặng, sai khuôn thì mọi phiếu nhập về hiện đúng một chặng.

    Mỗi bước phải có ĐỦ 16 khóa của `NODE_FIELDS`. `serializer.instance_out`
    đọc `node.branch_key` **thẳng**, không qua `getattr` — thiếu một khóa là
    ai mở chi tiết phiên duyệt cũng ăn lỗi 500, và chỉ lòi ra lúc có người bấm.

    Bản gốc Firebase giữ dưới khóa phụ `legacy`: `doc_snapshot` chỉ đọc `nodes`
    nên nó vô hại, mà còn lần ngược được khi cần đối chiếu.
    """
    nodes = []
    for step in snap.get("steps") or []:
        kind_key = step.get("assigneeType") or ""
        approver_kind = APPROVER_KIND_FROM_LEGACY.get(kind_key)
        if approver_kind is None:
            stats[f"cach chon nguoi duyet la: {kind_key}"] += 1
            approver_kind = APPROVER_EMPLOYEE

        #  `approver_ref` của ERP: vai trò thì là mã vai trò, người cụ thể thì
        #  là ID NHÂN SỰ — nên UID mặc định của app cũ phải đổi sang hồ sơ ERP,
        #  không chép nguyên UID Firebase vào.
        approver_ref = ""
        if approver_kind == APPROVER_ROLE:
            approver_ref = " ".join(step.get("assignees") or [])[:300]
        elif approver_kind == APPROVER_EMPLOYEE:
            emp = people.employee(step.get("defaultApproverUid") or "")
            approver_ref = str(emp.id) if emp else ""

        node = dict.fromkeys(NODE_FIELDS)
        node.update({
            "id": 0,                       # không có bước ERP tương ứng
            "seq": step.get("level") or 1,
            "branch_key": "",
            "name": (step.get("name") or "")[:200],
            "node_kind": NODE_APPROVAL,
            "flow_role": ROLE_APPROVE,
            "approver_kind": approver_kind,
            "approver_ref": approver_ref,
            "multi_mode": MULTI_ANY,       # app cũ chỉ có "ANYONE"
            "quorum_percent": 50,
            "condition": "",
            "is_default_branch": False,
            "skip_duplicate": SKIP_NONE,
            "sla_hours": 0,
            "fallback_employee_id": None,
            "on_no_approver": NO_APPROVER_BLOCK,
        })
        nodes.append(node)

    return json.dumps({
        "flow_id": 0,
        "code": snap.get("workflowId") or "",
        "name": snap.get("name") or "",
        "version_no": 0,
        "nodes": nodes,
        "legacy": snap,
    }, ensure_ascii=False)


def _step_names(snap: dict) -> dict[int, str]:
    """`{level: tên bước}` để dán vào `node_name` của từng dòng dấu vết."""
    return {step.get("level"): (step.get("name") or "")[:200]
            for step in (snap.get("steps") or [])}


# ---------------------------------------------------------------------------
# Một phiếu
# ---------------------------------------------------------------------------

def build_tasks(instance_id: int, hist: list[dict], names: dict[int, str],
                people: PeopleResolver, stats: collections.Counter
                ) -> tuple[dict[int, ApprovalTask], set[int]]:
    """Mỗi chặng ĐÃ có người xử lý -> một dòng việc ĐÃ ĐÓNG.

    ⚠️ BỎ BẢNG VIỆC LÀ VẼ SAI LÊN MÀN HÌNH, không phải "thiếu thông tin".
    `steps_service._one_step` xét: chặng không có việc nào + phiên đã kết thúc
    = `STEP_CANCELLED`. Nghĩa là một phiếu duyệt xong xuôi mà không có dòng
    việc nào sẽ hiện **cả ba chặng đều "đã hủy"** trên màn danh sách — đọc
    thành phiếu bị rút. Đo thật trước khi sửa: 1313 phiếu nhập về đều như vậy.

    MỘT CHẶNG MỘT DÒNG, lấy theo lượt xử lý CUỐI CÙNG của chặng đó. Phiếu bị
    trả về ở chặng 3 rồi duyệt lại chính chặng 3 thì kết cục là "đã duyệt" —
    ghi cả hai dòng việc thì `_one_step` thấy lẫn «đã hủy» trong nhóm và vẽ
    chặng đó thành "trả về" trên một phiếu đã duyệt xong. Đường đi đầy đủ vẫn
    còn nguyên trong `tab_approval_action`, đó mới là sổ dấu vết.

    Chặng KHÔNG có lượt nào (bước 2 "tùy chọn" của luồng dấu, hoặc 115 phiếu
    bật `isSkipApproval` nhảy thẳng lên chặng 3) cố ý không có dòng việc: nó
    hiện thành chấm mờ "không còn nghĩa", đúng với việc chặng đó không chạy.
    """
    last: dict[int, tuple[int, dict]] = {}
    for index, entry in enumerate(hist):
        level = entry.get("level")
        if not level or entry.get("action") not in TASK_STATUS_FROM_LEGACY:
            continue
        last[level] = (index, entry)

    tasks: dict[int, ApprovalTask] = {}
    decisive: set[int] = set()
    for level, (index, entry) in sorted(last.items()):
        emp = people.employee(entry.get("userId") or "")
        decided = _utc_dt(entry.get("timestamp"))
        tasks[level] = ApprovalTask(
            instance_id=instance_id,
            node_seq=level,
            node_name=names.get(level, ""),
            order_no=1,
            #  Cột này KHÔNG cho trống. UID không tra ra hồ sơ thì để 0 —
            #  `steps_service._names_of` bỏ qua id 0 nên chấm chỉ mất TÊN người
            #  xử lý, không mất chặng. Tên app cũ đã chép xuống dấu vết.
            assignee_employee_id=emp.id if emp else 0,
            status=TASK_STATUS_FROM_LEGACY[entry["action"]],
            due_at=None,
            decided_at=decided,
            created_at=decided,
            created_by=people.user_id(entry.get("userId") or ""),
            updated_by=people.user_id(entry.get("userId") or ""),
        )
        decisive.add(index)
        stats[f"viec da dong: {entry['action']}"] += 1
    return tasks, decisive


def build_actions(instance_id: int, hist: list[dict], names: dict[int, str],
                  people: PeopleResolver, stats: collections.Counter,
                  tasks: dict[int, ApprovalTask] | None = None,
                  decisive: set[int] | None = None) -> list[ApprovalAction]:
    """Dựng dấu vết duyệt theo đúng thứ tự thời gian của app cũ.

    Mảng `history` bên app cũ đã xếp sẵn theo thời gian (đo: 0/5095 dòng lệch
    thứ tự) và `serializer.actions_of` xếp theo `id`, nên chỉ cần thêm đúng thứ
    tự mảng là bản in ra đúng dòng thời gian.
    """
    tasks = tasks or {}
    decisive = decisive or set()
    rows = []
    for index, entry in enumerate(hist):
        legacy_action = entry.get("action")
        if legacy_action in TRIP_ACTIONS:
            continue
        code = ACTION_FROM_LEGACY.get(legacy_action)
        if code is None:
            stats[f"ma lich su la: {legacy_action}"] += 1
            continue

        uid = entry.get("userId") or ""
        emp = people.employee(uid)
        comment = (entry.get("comment") or "").strip()
        if legacy_action == "admin_canceled":
            comment = ADMIN_CANCEL_PREFIX + comment
        #  UID không tra ra hồ sơ nào thì `actor_employee_id` để trống và dấu
        #  vết sẽ đọc là "Hệ thống". Chép tên app cũ xuống ghi chú để câu trả
        #  lời cho "ai đã ký" không biến mất — đây là bảng kiểm toán.
        if emp is None and uid:
            who = (entry.get("userName") or "").strip() or uid
            comment = (comment + " " if comment else "") + f"[App cũ] người thao tác: {who}"
            stats["dong dau vet khong tra ra ho so"] += 1

        level = entry.get("level")
        #  Chỉ lượt xử lý CUỐI của một chặng mới được gắn vào dòng việc của
        #  chặng đó — đó là lượt đã quyết kết cục. Gắn cả những lượt trước là
        #  nói rằng một dòng việc có hai kết cục.
        task = tasks.get(level) if index in decisive else None
        rows.append(ApprovalAction(
            instance_id=instance_id,
            task_id=task.id if task is not None else None,
            node_seq=level or 0,
            node_name=names.get(level, "") if level else "",
            action=code,
            actor_employee_id=emp.id if emp else None,
            on_behalf_of_id=None,
            delegation_id=None,
            comment=comment,
            created_at=_utc_dt(entry.get("timestamp")),
            created_by=people.user_id(uid),
            updated_by=people.user_id(uid),
        ))
        stats[f"dau vet: {legacy_action}"] += 1
    return rows


def build_instance(entity: str, entity_id: int, code: str, title: str,
                   node: dict, people: PeopleResolver,
                   stats: collections.Counter) -> ApprovalInstance | None:
    approval = node.get("approval") or {}
    hist = approval.get("history") or []
    legacy_status = approval.get("overallStatus")
    status = INSTANCE_STATUS_FROM_LEGACY.get(legacy_status)
    if status is None:
        stats[f"trang thai phien la: {legacy_status}"] += 1
        return None

    created = next((h for h in hist if h.get("action") == "created"), None)
    starter = people.employee((created or {}).get("userId") or node.get("createdBy") or "")

    #  Mốc kết thúc = dòng dấu vết CUỐI CÙNG, bỏ qua mốc chuyến: chuyến xe chạy
    #  xong sau khi phiếu đã duyệt xong, lấy nó làm mốc kết thúc phiên duyệt là
    #  ghi rằng người duyệt ký lúc xe về bãi.
    closing = None
    for entry in hist:
        if entry.get("action") not in TRIP_ACTIONS:
            closing = entry
    finished = None if status == INSTANCE_RUNNING else _utc_dt((closing or {}).get("timestamp"))
    reason = "" if status == INSTANCE_RUNNING else (closing or {}).get("comment") or ""

    actor = people.user_id((created or {}).get("userId") or "")
    return ApprovalInstance(
        entity=entity,
        entity_id=entity_id,
        entity_code=code[:100],
        entity_title=title[:500],
        #  Phiếu cũ KHÔNG chạy luồng nào của ERP — xem ghi chú đầu tệp.
        flow_id=0,
        flow_version=0,
        flow_snapshot=build_snapshot(approval.get("workflowSnapshot") or {},
                                     people, stats),
        status=status,
        current_seq=approval.get("currentLevel") or 1,
        started_by_employee_id=starter.id if starter else None,
        started_at=_utc_dt((created or {}).get("timestamp") or node.get("createdAt")),
        finished_at=finished,
        finish_reason=reason.strip()[:1000],
        created_by=actor,
        updated_by=actor,
    )


# ---------------------------------------------------------------------------
# Mốc điều phối chuyến -> cột của phiếu xe
# ---------------------------------------------------------------------------

def backfill_trip(booking: VehicleBooking, hist: list[dict],
                  people: PeopleResolver, stats: collections.Counter) -> None:
    """Vá cột điều phối từ lịch sử, CHỈ khi nhánh `details.dispatch` bỏ trống ô đó.

    `import_tickets.py` đã đổ năm cột này từ `details.dispatch` — đó là nguồn
    chính xác hơn vì nó là trạng thái cuối. Lịch sử chỉ dùng để vá lỗ: 13 phiếu
    có dòng `dispatched` mà `dispatchedAt` rỗng, 4 phiếu có `driver_accepted`
    mà `driverStatus` rỗng. Ghi đè ô đã có là lấy vòng điều phối ĐẦU đè lên
    vòng CUỐI ở 62 phiếu từng điều phối lại.
    """
    last: dict[str, dict] = {}
    for entry in hist:
        if entry.get("action") in TRIP_ACTIONS:
            last[entry["action"]] = entry

    dispatch = last.get("re-dispatched") or last.get("dispatched")
    if dispatch and not booking.dispatched_at:
        booking.dispatched_at = _utc_iso(dispatch.get("timestamp"))
        if not booking.dispatched_by:
            booking.dispatched_by = people.user_id(dispatch.get("userId") or "")
        stats["va cot dispatched_at tu lich su"] += 1

    if last.get("trip_started") and not booking.actual_start_time:
        booking.actual_start_time = _utc_iso(last["trip_started"].get("timestamp"))
        stats["va cot actual_start_time tu lich su"] += 1

    if last.get("trip_completed") and not booking.actual_end_time:
        booking.actual_end_time = _utc_iso(last["trip_completed"].get("timestamp"))
        stats["va cot actual_end_time tu lich su"] += 1

    if booking.driver_status in (None, DRV_NONE):
        reached = DRV_NONE
        for action, value in DRIVER_STATUS_FROM_ACTION.items():
            if action in last and DRIVER_STATUS_RANK[value] > DRIVER_STATUS_RANK[reached]:
                reached = value
        if reached != DRV_NONE:
            booking.driver_status = reached
            stats["va cot driver_status tu lich su"] += 1


# ---------------------------------------------------------------------------
# Chạy
# ---------------------------------------------------------------------------

def _existing_instances(db, entity: str) -> set[int]:
    """`entity_id` của những phiếu ĐÃ có phiên duyệt — để chạy lại không nhân đôi."""
    return set(db.execute(
        select(ApprovalInstance.entity_id)
        .where(ApprovalInstance.entity == entity)).scalars())


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

    done = {SEAL_ENTITY: _existing_instances(db, SEAL_ENTITY),
            BOOKING_ENTITY: _existing_instances(db, BOOKING_ENTITY)}
    print(f"=== PHIEN DA CO === {len(done[SEAL_ENTITY])} phieu dau · "
          f"{len(done[BOOKING_ENTITY])} phieu xe")

    still_open: list[str] = []
    #  Xếp theo mốc tạo để id phiên tăng dần đúng dòng thời gian bên app cũ.
    ordered = sorted(requests.items(), key=lambda kv: kv[1].get("createdAt") or 0)

    for key, node in ordered:
        typ = node.get("type")
        if typ == "SEAL_REQUEST":
            entity, model, index = SEAL_ENTITY, SealRequest, seal_index
        elif typ in ("CAR_BOOKING", "DELIVERY"):
            entity, model, index = BOOKING_ENTITY, VehicleBooking, booking_index
        else:
            stats[f"loai la: {typ}"] += 1
            continue

        entity_id = index.get(key)
        if not entity_id:
            stats["phieu app cu chua co ban doi ung ben ERP"] += 1
            continue

        hist = (node.get("approval") or {}).get("history") or []

        #  Mốc chuyến vá thẳng vào cột phiếu, KHÔNG phụ thuộc phiên duyệt: phiếu
        #  đã có phiên (chạy lại lần hai) thì cột vẫn phải được vá. Lượt xem
        #  trước cũng chạy qua đây để đếm đúng — cuối cùng `rollback()` bỏ hết.
        if entity == BOOKING_ENTITY:
            booking = db.get(VehicleBooking, entity_id)
            if booking is not None:
                backfill_trip(booking, hist, people, stats)

        if entity_id in done[entity]:
            stats["phieu bo qua (da co phien duyet)"] += 1
            continue

        row = db.get(model, entity_id)
        instance = build_instance(entity, entity_id, getattr(row, "code", "") or "",
                                  getattr(row, "purpose", "") or "",
                                  node, people, stats)
        if instance is None:
            continue
        if instance.status == INSTANCE_RUNNING:
            still_open.append(f"{getattr(row, 'code', '') or key} ({typ})")

        stats["phien duyet"] += 1
        stats[f"phien duyet: {(node.get('approval') or {}).get('overallStatus')}"] += 1
        names = _step_names((node.get("approval") or {}).get("workflowSnapshot") or {})

        if not apply:
            #  Vẫn dựng đủ để ĐẾM ĐÚNG lúc xem trước, chỉ không ghi.
            tasks, decisive = build_tasks(0, hist, names, people, stats)
            build_actions(0, hist, names, people, stats, tasks, decisive)
            continue

        db.add(instance)
        db.flush()
        #  Việc trước, dấu vết sau: dấu vết còn phải trỏ `task_id` sang việc.
        tasks, decisive = build_tasks(instance.id, hist, names, people, stats)
        for task_row in tasks.values():
            db.add(task_row)
        db.flush()
        #  Thêm đúng thứ tự mảng rồi ghi một lượt: SQLAlchemy giữ nguyên thứ tự
        #  `add` khi chèn cùng một bảng, nên `id` tăng dần đúng dòng thời gian —
        #  mà `serializer.actions_of` lại xếp theo `id`.
        for action_row in build_actions(instance.id, hist, names, people, stats,
                                        tasks, decisive):
            db.add(action_row)
        db.flush()

    if people.unknown_uid:
        print("\n  CANH BAO: UID khong tra ra ho so nao — dong dau vet cua ho de "
              "trong nguoi thao tac, ten app cu chep xuong ghi chu:")
        for uid, n in people.unknown_uid.most_common(10):
            print(f"    {uid}  x{n}")

    if still_open:
        print(f"\n  CHU Y: {len(still_open)} phieu nhap ve dang MO "
              f"(INSTANCE_RUNNING, khong co viec cho). Ben ERP khong ai bam duyet "
              f"duoc cho toi khi P2 quyet — xu not ben app cu:")
        for name in still_open:
            print(f"    {name}")

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
