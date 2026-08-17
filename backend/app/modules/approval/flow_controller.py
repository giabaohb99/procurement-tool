"""API KHAI LUỒNG (I01–I05, I21, I26).

Khai luồng bằng **dữ liệu**, không sửa mã và không deploy lại — đó là bài nghiệm
thu số 1 của phase.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import flow_service, serializer
from .flow_model import (APPROVER_KIND_LABELS, MULTI_MODE_LABELS,
                         NODE_KIND_LABELS, NO_APPROVER_LABELS, ROLE_LABELS,
                         SKIP_MODE_LABELS, ApprovalFlow, ApprovalNode,
                         ApprovalSwitch)
from .instance_model import INSTANCE_OPEN_STATUSES, ApprovalInstance

router = APIRouter(prefix="/api/approval-flows", tags=["approval-flow"])


class FlowIn(BaseModel):
    entity: str = Field(min_length=1, max_length=50)
    code: str = ""
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    is_active: bool = True
    company_id: int | None = None
    priority: int = 0
    condition: str = ""


class NodeIn(BaseModel):
    seq: int = Field(ge=1)
    branch_key: str = ""
    name: str = ""
    node_kind: int = 1
    flow_role: int = 4
    approver_kind: int = Field(default=1, ge=1, le=6)
    approver_ref: str = ""
    multi_mode: int = Field(default=1, ge=1, le=4)
    quorum_percent: int = Field(default=50, ge=1, le=100)
    condition: str = ""
    is_default_branch: bool = False
    skip_duplicate: int = Field(default=1, ge=0, le=2)
    sla_hours: int = Field(default=0, ge=0)
    fallback_employee_id: int | None = None
    on_no_approver: int = Field(default=3, ge=1, le=3)


class SwitchIn(BaseModel):
    entity: str
    is_enabled: bool
    note: str = ""


@router.get("/options")
def options(user=Depends(require("approval_flow", "read"))):
    """Nhãn tiếng Việt do backend cấp — giao diện không chép cứng."""
    def bang(labels):
        return [{"value": value, "label": label} for value, label in labels.items()]

    return success({
        "node_kinds": bang(NODE_KIND_LABELS),
        "flow_roles": bang(ROLE_LABELS),
        "approver_kinds": bang(APPROVER_KIND_LABELS),
        "multi_modes": bang(MULTI_MODE_LABELS),
        "skip_modes": bang(SKIP_MODE_LABELS),
        "on_no_approver": bang(NO_APPROVER_LABELS),
    })


@router.get("/switches")
def list_switches(db: Session = Depends(get_db),
                  user=Depends(require("approval_flow", "read"))):
    rows = db.query(ApprovalSwitch).order_by(ApprovalSwitch.entity.asc()).all()
    return success([{"entity": row.entity, "is_enabled": row.is_enabled, "note": row.note}
                    for row in rows])


@router.put("/switches")
def set_switch(data: SwitchIn, db: Session = Depends(get_db),
               user=Depends(require("approval_flow", "write"))):
    """I26 — đường lui của cả phase: tắt là quay về đường duyệt cũ ngay."""
    row = db.query(ApprovalSwitch).filter(ApprovalSwitch.entity == data.entity).first()
    if row is None:
        row = ApprovalSwitch(entity=data.entity, created_by=user.id, updated_by=user.id)
        db.add(row)
    row.is_enabled = data.is_enabled
    row.note = data.note
    row.updated_by = user.id
    db.commit()
    record(db, user.id, "approval_flow", 0, "update",
           f"{'Bật' if data.is_enabled else 'Tắt'} bộ máy duyệt mới cho {data.entity}")
    return success({"entity": row.entity, "is_enabled": row.is_enabled},
                   "Đã cập nhật. Phiếu đang chạy vẫn đi tiếp theo bộ máy cũ của nó.")


@router.get("")
def list_flows(entity: str = "", db: Session = Depends(get_db),
               user=Depends(require("approval_flow", "read"))):
    query = db.query(ApprovalFlow)
    if entity:
        query = query.filter(ApprovalFlow.entity == entity)
    rows = query.order_by(ApprovalFlow.entity.asc(), ApprovalFlow.priority.desc(),
                          ApprovalFlow.id.asc()).all()
    return success({"total": len(rows), "items": [serializer.flow_out(db, row) for row in rows]})


@router.post("")
def create_flow(data: FlowIn, db: Session = Depends(get_db),
                user=Depends(require("approval_flow", "create"))):
    flow = ApprovalFlow(**data.model_dump(), created_by=user.id, updated_by=user.id)
    db.add(flow)
    db.commit()
    db.refresh(flow)
    record(db, user.id, "approval_flow", flow.id, "create", flow.name)
    return success(serializer.flow_out(db, flow), "Đã tạo luồng duyệt", 201)


@router.get("/{flow_id}")
def get_flow(flow_id: int, db: Session = Depends(get_db),
             user=Depends(require("approval_flow", "read"))):
    return success(serializer.flow_out(db, _load(db, flow_id), kem_buoc=True))


@router.patch("/{flow_id}")
def update_flow(flow_id: int, data: FlowIn, db: Session = Depends(get_db),
                user=Depends(require("approval_flow", "write"))):
    flow = _load(db, flow_id)
    for ten, gia_tri in data.model_dump().items():
        setattr(flow, ten, gia_tri)
    _len_ban_moi(db, flow, user.id)
    return success(serializer.flow_out(db, flow, kem_buoc=True), "Đã lưu luồng duyệt")


@router.delete("/{flow_id}")
def delete_flow(flow_id: int, db: Session = Depends(get_db),
                user=Depends(require("approval_flow", "delete"))):
    flow = _load(db, flow_id)
    _chan_khi_dang_chay(db, flow.id)
    db.query(ApprovalNode).filter(ApprovalNode.flow_id == flow.id).delete()
    db.delete(flow)
    db.commit()
    record(db, user.id, "approval_flow", flow_id, "delete")
    return success(None, "Đã xóa luồng duyệt")


@router.post("/{flow_id}/nodes")
def add_node(flow_id: int, data: NodeIn, db: Session = Depends(get_db),
             user=Depends(require("approval_flow", "write"))):
    flow = _load(db, flow_id)
    node = ApprovalNode(flow_id=flow.id, **data.model_dump(),
                        created_by=user.id, updated_by=user.id)
    db.add(node)
    _len_ban_moi(db, flow, user.id)
    db.refresh(node)
    return success(serializer.node_out(db, node), "Đã thêm bước", 201)


@router.patch("/{flow_id}/nodes/{node_id}")
def update_node(flow_id: int, node_id: int, data: NodeIn, db: Session = Depends(get_db),
                user=Depends(require("approval_flow", "write"))):
    flow = _load(db, flow_id)
    node = db.get(ApprovalNode, node_id)
    if node is None or node.flow_id != flow.id:
        raise HTTPException(404, "Không tìm thấy bước này")
    for ten, gia_tri in data.model_dump().items():
        setattr(node, ten, gia_tri)
    _len_ban_moi(db, flow, user.id)
    db.refresh(node)
    return success(serializer.node_out(db, node), "Đã lưu bước")


class ReorderIn(BaseModel):
    """Thứ tự chặng sau khi kéo thả: mỗi phần tử là một CHẶNG, chứa id các bước
    của chặng đó (nhiều id = các nhánh song song cùng chặng)."""
    stages: list[list[int]]


@router.put("/{flow_id}/nodes/reorder")
def reorder_nodes(flow_id: int, data: ReorderIn, db: Session = Depends(get_db),
                  user=Depends(require("approval_flow", "write"))):
    """Ghi lại thứ tự sau khi kéo thả trên màn khai luồng.

    Gán lại `seq` theo vị trí trong mảng thay vì để giao diện tự tính số: giao
    diện tính thì hai người kéo cùng lúc sẽ ra hai bộ số khác nhau, và bộ nào ghi
    sau thắng mà không ai biết.
    """
    flow = _load(db, flow_id)
    theo_id = {node.id: node for node in flow_service.nodes_of(db, flow.id)}

    #  ⚠️ HAI LƯỢT, không phải một. `UNIQUE(flow_id, seq, branch_key)` nổ ngay
    #  giữa chừng nếu gán thẳng: hoán vị chặng 1 với chặng 2 thì có một khoảnh
    #  khắc hai bước cùng mang seq = 1. Đẩy hết sang số ÂM trước rồi mới gán số
    #  thật — số âm không bao giờ trùng số thật.
    for thu_tu, node in enumerate(theo_id.values(), start=1):
        node.seq = -thu_tu
    db.flush()

    for vi_tri, ids_cua_chang in enumerate(data.stages, start=1):
        for nhanh, node_id in enumerate(ids_cua_chang):
            node = theo_id.get(node_id)
            if node is None:
                raise HTTPException(400, f"Bước {node_id} không thuộc luồng này")
            node.seq = vi_tri
            #  Các nhánh song song phải khác `branch_key` nhau, nếu không cũng
            #  đâm vào chính ràng buộc trên. Đánh lại theo vị trí thay vì tin
            #  vào giá trị cũ — kéo một bước từ chặng khác sang là trùng ngay.
            node.branch_key = "" if len(ids_cua_chang) == 1 else f"n{nhanh + 1}"
            node.updated_by = user.id
    db.flush()

    _len_ban_moi(db, flow, user.id)
    return success(serializer.flow_out(db, flow, kem_buoc=True), "Đã lưu thứ tự các bước")


@router.delete("/{flow_id}/nodes/{node_id}")
def delete_node(flow_id: int, node_id: int, db: Session = Depends(get_db),
                user=Depends(require("approval_flow", "write"))):
    flow = _load(db, flow_id)
    node = db.get(ApprovalNode, node_id)
    if node is None or node.flow_id != flow.id:
        raise HTTPException(404, "Không tìm thấy bước này")
    db.delete(node)
    _len_ban_moi(db, flow, user.id)
    return success(None, "Đã xóa bước")


def _load(db: Session, flow_id: int) -> ApprovalFlow:
    flow = db.get(ApprovalFlow, flow_id)
    if flow is None:
        raise HTTPException(404, "Không tìm thấy luồng duyệt")
    return flow


def _len_ban_moi(db: Session, flow: ApprovalFlow, actor: int) -> None:
    """I21 — mỗi lần sửa luồng là một bản mới.

    Phiếu ĐANG CHẠY không bị ảnh hưởng: chúng giữ bản chụp riêng
    (`flow_snapshot`). Số bản ở đây chỉ để người dùng đọc và để tra lịch sử —
    nhưng vẫn phải tăng, không thì hai luồng khác hẳn nhau cùng mang số 1 và
    bản in dấu vết nói sai phiếu chạy theo luồng nào.
    """
    flow.version_no += 1
    flow.updated_by = actor
    db.commit()
    record(db, actor, "approval_flow", flow.id, "update", f"Lên bản {flow.version_no}")


def _chan_khi_dang_chay(db: Session, flow_id: int) -> None:
    dang_chay = (
        db.query(ApprovalInstance.id)
        .filter(ApprovalInstance.flow_id == flow_id,
                ApprovalInstance.status.in_(INSTANCE_OPEN_STATUSES))
        .count()
    )
    if dang_chay:
        raise HTTPException(
            400,
            f"Còn {dang_chay} phiếu đang chạy theo luồng này. Tắt luồng "
            f"(bỏ «Đang dùng») thay vì xóa — phiếu đang chạy vẫn đi hết bản của chúng.",
        )
