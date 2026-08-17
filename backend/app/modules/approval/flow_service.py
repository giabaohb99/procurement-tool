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


def chon_luong(db: Session, entity: str, subject: dict) -> ApprovalFlow | None:
    """Luồng nào áp cho phiếu này.

    Xét theo `priority` giảm dần; luồng có điều kiện mà khớp thì thắng, luồng
    không khai điều kiện là luồng mặc định và đứng cuối hàng. Không có luồng nào
    khớp thì trả `None` — người gọi quay về đường duyệt cũ.
    """
    ung_vien = (
        db.query(ApprovalFlow)
        .filter(ApprovalFlow.entity == entity, ApprovalFlow.is_active.is_(True))
        .order_by(ApprovalFlow.priority.desc(), ApprovalFlow.id.asc())
        .all()
    )

    company_id = subject.get("company_id")
    mac_dinh: ApprovalFlow | None = None

    for flow in ung_vien:
        #  Luồng khai riêng cho một pháp nhân thì chỉ pháp nhân đó dùng.
        if flow.company_id and str(flow.company_id) != str(company_id):
            continue
        if not (flow.condition or "").strip():
            mac_dinh = mac_dinh or flow
            continue
        if condition_service.matches(flow.condition, subject):
            return flow

    return mac_dinh


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
            {ten: getattr(node, ten) for ten in NODE_FIELDS}
            for node in nodes_of(db, flow.id)
        ],
    }, ensure_ascii=False)


def doc_snapshot(raw: str) -> dict:
    try:
        data = json.loads(raw or "{}")
    except (ValueError, TypeError):
        return {"nodes": []}
    return data if isinstance(data, dict) else {"nodes": []}


def cac_buoc(raw_snapshot: str) -> list[SimpleNamespace]:
    """Các bước trong bản chụp, dạng object cho code đọc giống hệt model."""
    nodes = doc_snapshot(raw_snapshot).get("nodes") or []
    return [SimpleNamespace(**node) for node in nodes if isinstance(node, dict)]


def buoc_cua_chang(raw_snapshot: str, seq: int, subject: dict) -> SimpleNamespace | None:
    """Bước nào chạy ở chặng `seq` — phần rẽ nhánh của I04.

    Nhiều bước cùng `seq` là các NHÁNH song song; chọn nhánh đầu tiên khớp điều
    kiện, không khớp cái nào thì rơi vào **nhánh mặc định**.

    ⚠️ Không có nhánh mặc định mà cũng không khớp gì thì trả `None`, và người
    gọi phải coi đó là phiếu KẸT chứ không phải phiếu xong. Đây đúng là chỗ
    phiếu biến mất khỏi mọi danh sách nếu xử ẩu.
    """
    cung_chang = [node for node in cac_buoc(raw_snapshot) if node.seq == seq]
    if not cung_chang:
        return None
    if len(cung_chang) == 1:
        return cung_chang[0]

    for node in cung_chang:
        if node.is_default_branch:
            continue
        if condition_service.matches(node.condition or "", subject):
            return node

    return next((node for node in cung_chang if node.is_default_branch), None)


def cac_chang(raw_snapshot: str) -> list[int]:
    """Danh sách `seq` theo thứ tự, mỗi chặng một lần."""
    return sorted({node.seq for node in cac_buoc(raw_snapshot)})
