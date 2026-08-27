"""CHỌN LUỒNG và CHỤP BẢN LUỒNG (I01, I21, I26)."""
import json
from types import SimpleNamespace

from sqlalchemy.orm import Session

from . import condition_service
from .flow_model import ApprovalFlow, ApprovalNode, ApprovalSwitch

#  Các cột của bước được chép vào bản chụp. Khai tường minh chứ không dùng
#  `__dict__`: bản chụp là dữ liệu sống nhiều năm, thêm cột mới vào bảng không
#  được lặng lẽ đổi hình dạng của bản chụp cũ.
NODE_FIELDS = (
    "id", "seq", "branch_key", "name", "node_kind", "flow_role",
    "approver_kind", "approver_ref", "multi_mode", "quorum_percent",
    "condition", "is_default_branch", "skip_duplicate", "sla_hours",
    "fallback_employee_id", "on_no_approver",
)


def is_enabled(db: Session, entity: str) -> bool:
    """I26 — bộ máy mới có đang bật cho loại chứng từ này không.

    Chưa khai dòng nào = TẮT. Thêm bảng mới mà mặc định bật là đổi hành vi của
    thứ đang chạy ngay lúc chạy migration.
    """
    row = db.query(ApprovalSwitch).filter(ApprovalSwitch.entity == entity).first()
    return bool(row and row.is_enabled)


def nodes_of(db: Session, flow_id: int) -> list[ApprovalNode]:
    return (
        db.query(ApprovalNode)
        .filter(ApprovalNode.flow_id == flow_id)
        .order_by(ApprovalNode.seq.asc(), ApprovalNode.id.asc())
        .all()
    )


def add_step(db: Session, flow_id: int, values: dict, actor: int,
              *, is_branch: bool = False) -> ApprovalNode:
    """Chèn một BƯỚC vào luồng, tự dọn chỗ cho nó.

    `UNIQUE(flow_id, seq, branch_key)` nên không thể cứ thế `INSERT` số chặng
    người dùng chọn: chèn vào giữa là đâm thẳng vào bước đang đứng ở đó và cả
    request nổ 500. Chỗ này tự dọn theo đúng ý người dùng vừa bấm:

    * `la_nhanh=False` — **chèn một chặng mới**: đẩy mọi bước từ chặng đó trở đi
      xuống một bậc rồi mới chèn.
    * `la_nhanh=True` — **thêm nhánh song song** vào chặng đang có: đánh lại
      `branch_key` của cả chặng thành `n1..nk` (chặng một nhánh mang khóa rỗng,
      từ hai nhánh trở lên phải có khóa khác nhau — cùng quy ước với `reorder`).

    Dồn số qua **hai lượt**, số âm trước rồi mới số thật, vì nếu gán thẳng thì
    có một khoảnh khắc hai bước cùng mang một `seq` và ràng buộc nổ giữa chừng.
    """
    seq = max(int(values.get("seq") or 1), 1)
    existing = nodes_of(db, flow_id)

    if is_branch:
        same_stage = [node for node in existing if node.seq == seq]
        branch_key = _renumber_branches(db, same_stage, actor)
    else:
        _shift_down_one_seq(db, [node for node in existing if node.seq >= seq], actor)
        branch_key = ""

    node = ApprovalNode(**{**values, "flow_id": flow_id, "seq": seq,
                           "branch_key": branch_key},
                        created_by=actor, updated_by=actor)
    db.add(node)
    db.flush()
    return node


def _shift_down_one_seq(db: Session, later_steps: list[ApprovalNode], actor: int) -> None:
    if not later_steps:
        return
    for node in later_steps:
        node.seq = -node.seq
    db.flush()
    for node in later_steps:
        node.seq = -node.seq + 1
        node.updated_by = actor
    db.flush()


def _renumber_branches(db: Session, same_stage: list[ApprovalNode], actor: int) -> str:
    """Trả về `branch_key` cho nhánh sắp thêm, sau khi đánh lại cả chặng."""
    if not same_stage:
        #  Chặng chưa có bước nào: nhánh đầu tiên mang khóa rỗng như bước thường.
        return ""

    for order_index, node in enumerate(same_stage, start=1):
        node.branch_key = f"x{order_index}"
    db.flush()
    for order_index, node in enumerate(same_stage, start=1):
        node.branch_key = f"n{order_index}"
        node.updated_by = actor
    db.flush()
    return f"n{len(same_stage) + 1}"


def pick_flow(db: Session, entity: str, subject: dict, *,
               company_only: bool = False) -> ApprovalFlow | None:
    """Luồng nào áp cho phiếu này.

    Luồng khai ĐÚNG pháp nhân của phiếu được xét trước toàn bộ luồng dùng chung,
    bất kể độ ưu tiên. Đây là chốt để bản clone ở pháp nhân con chạy luồng riêng
    của nơi nhận, không vô tình đi theo luồng dùng chung đang phục vụ bản gốc.

    Trong từng nhóm vẫn xét theo `priority` giảm dần: luồng có điều kiện mà khớp
    thì thắng, luồng không khai điều kiện là mặc định và đứng cuối hàng. Không
    có luồng riêng nào khớp mới rơi về luồng dùng chung; không có cả hai thì trả
    `None` để người gọi quay về đường duyệt cũ. `chi_phap_nhan=True` tắt đường
    lùi đó — bản clone dùng chốt này để bắt buộc chạy luồng riêng của nơi nhận.
    """
    candidates = (
        db.query(ApprovalFlow)
        .filter(ApprovalFlow.entity == entity, ApprovalFlow.is_active.is_(True))
        .order_by(ApprovalFlow.priority.desc(), ApprovalFlow.id.asc())
        .all()
    )

    company_id = subject.get("company_id")

    def pick_among(rows: list[ApprovalFlow]) -> ApprovalFlow | None:
        default: ApprovalFlow | None = None
        for flow in rows:
            if not (flow.condition or "").strip():
                default = default or flow
                continue
            if condition_service.matches(flow.condition, subject):
                return flow
        return default

    specific = [
        flow for flow in candidates
        if flow.company_id and str(flow.company_id) == str(company_id)
    ]
    chosen = pick_among(specific)
    if chosen is not None:
        return chosen
    if company_only:
        return None

    return pick_among([flow for flow in candidates if not flow.company_id])


def shadowed_default_flows(db: Session, flow: ApprovalFlow) -> list[ApprovalFlow]:
    """Những luồng MẶC ĐỊNH khác cùng phạm vi — chỉ một cái trong số đó chạy.

    "Mặc định" = đang bật và KHÔNG khai điều kiện. `chon_luong` lấy đúng cái đầu
    tiên theo `priority` giảm dần rồi `id` tăng dần, nên khai cái thứ hai là nó
    nằm im vĩnh viễn mà không có gì báo — đã gặp thật ở dữ liệu chạy thử ngày
    19/08/2026: luồng có người dự phòng bị một luồng chặn-cứng che mất, phiếu
    thiếu người duyệt là kẹt luôn thay vì rơi về người dự phòng.

    Trả về danh sách BỊ CHE nếu `flow` là cái thắng, hoặc chính cái thắng nếu
    `flow` là cái bị che — người khai cần biết tên cụ thể, không phải một câu
    chung chung "có trùng".
    """
    if not flow.is_active or (flow.condition or "").strip():
        return []

    same_scope = (
        db.query(ApprovalFlow)
        .filter(ApprovalFlow.entity == flow.entity,
                ApprovalFlow.is_active.is_(True),
                ApprovalFlow.id != flow.id)
        .order_by(ApprovalFlow.priority.desc(), ApprovalFlow.id.asc())
        .all()
    )
    return [
        other for other in same_scope
        if not (other.condition or "").strip()
        #  Luồng riêng được xét trước luồng dùng chung nên hai nhóm KHÔNG che
        #  nhau. Chỉ hai luồng cùng để trống, hoặc cùng đúng một pháp nhân, mới
        #  thật sự tranh cùng một vị trí mặc định.
        and ((not flow.company_id and not other.company_id)
             or (flow.company_id and other.company_id
                 and str(flow.company_id) == str(other.company_id)))
    ]


def default_overlap_warning(db: Session, flow: ApprovalFlow) -> str:
    """Câu cảnh báo cho giao diện, rỗng nếu không trùng ai."""
    overlapping = shadowed_default_flows(db, flow)
    if not overlapping:
        return ""

    ranked = sorted([flow, *overlapping], key=lambda row: (-row.priority, row.id))
    winner = ranked[0]
    remaining_names = ", ".join(f"«{row.name}»" for row in ranked[1:])
    return (
        f"Đang có {len(ranked)} luồng mặc định (không khai điều kiện) cùng bật cho "
        f"«{flow.entity}»: chỉ «{winner.name}» chạy, {remaining_names} sẽ không bao giờ "
        "được chọn. Khai điều kiện hoặc tắt bớt để khỏi tưởng nhầm là đang chạy."
    )


def snapshot(db: Session, flow: ApprovalFlow) -> str:
    """Chụp lại luồng lúc phiếu bắt đầu chạy (I21).

    Phiếu chạy theo bản chụp của chính nó. Đọc bảng `tab_approval_node` lúc chạy
    thì người quản trị sửa luồng là 5 phiếu đang chạy đổi đường giữa chừng —
    hoặc mất đích tới nếu bước đang đứng bị xóa.
    """
    return json.dumps({
        "flow_id": flow.id,
        "code": flow.code,
        "name": flow.name,
        "version_no": flow.version_no,
        "nodes": [
            {field: getattr(node, field) for field in NODE_FIELDS}
            for node in nodes_of(db, flow.id)
        ],
    }, ensure_ascii=False)


def doc_snapshot(raw: str) -> dict:
    try:
        data = json.loads(raw or "{}")
    except (ValueError, TypeError):
        return {"nodes": []}
    return data if isinstance(data, dict) else {"nodes": []}


def steps(raw_snapshot: str) -> list[SimpleNamespace]:
    """Các bước trong bản chụp, dạng object cho code đọc giống hệt model."""
    nodes = doc_snapshot(raw_snapshot).get("nodes") or []
    return [SimpleNamespace(**node) for node in nodes if isinstance(node, dict)]


def step_of_stage(raw_snapshot: str, seq: int, subject: dict) -> SimpleNamespace | None:
    """Bước nào chạy ở chặng `seq` — phần rẽ nhánh của I04.

    Nhiều bước cùng `seq` là các NHÁNH song song; chọn nhánh đầu tiên khớp điều
    kiện, không khớp cái nào thì rơi vào **nhánh mặc định**.

    ⚠️ Không có nhánh mặc định mà cũng không khớp gì thì trả `None`, và người
    gọi phải coi đó là phiếu KẸT chứ không phải phiếu xong. Đây đúng là chỗ
    phiếu biến mất khỏi mọi danh sách nếu xử ẩu.
    """
    same_stage = [node for node in steps(raw_snapshot) if node.seq == seq]
    if not same_stage:
        return None
    if len(same_stage) == 1:
        return same_stage[0]

    for node in same_stage:
        if node.is_default_branch:
            continue
        if condition_service.matches(node.condition or "", subject):
            return node

    return next((node for node in same_stage if node.is_default_branch), None)


def stages(raw_snapshot: str) -> list[int]:
    """Danh sách `seq` theo thứ tự, mỗi chặng một lần."""
    return sorted({node.seq for node in steps(raw_snapshot)})
