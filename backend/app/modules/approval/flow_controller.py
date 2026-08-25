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
from app.core.scoping import apply_scope, get_perm_profile, get_scoped

from . import entity_hooks, flow_service, flow_sync_service, serializer
from .flow_model import (APPROVER_KIND_LABELS, MULTI_MODE_LABELS,
                         NODE_KIND_LABELS, NO_APPROVER_CHOICES,
                         NO_APPROVER_LABELS, ROLE_LABELS,
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
        #  CHỈ những lựa chọn còn khai được — «Đẩy lên cấp trên» đã bỏ (CR-114)
        #  nên không bày ra ô chọn nữa, dù nhãn của nó vẫn còn để đọc dữ liệu cũ.
        "on_no_approver": [{"value": ma, "label": NO_APPROVER_LABELS[ma]}
                           for ma in NO_APPROVER_CHOICES],
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
    query = apply_scope(db.query(ApprovalFlow), ApprovalFlow, "approval_flow",
                        user, get_perm_profile(db, user))
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
    #  Trùng luồng mặc định thì báo NGAY lúc lưu, không đợi người khai tự phát
    #  hiện phiếu đang chạy theo một luồng khác cái họ vừa sửa.
    canh_bao = flow_service.canh_bao_trung_mac_dinh(db, flow)
    return success(serializer.flow_out(db, flow),
                   f"Đã tạo luồng duyệt. ⚠ {canh_bao}" if canh_bao else "Đã tạo luồng duyệt", 201)


@router.get("/{flow_id}")
def get_flow(flow_id: int, db: Session = Depends(get_db),
             user=Depends(require("approval_flow", "read"))):
    return success(serializer.flow_out(db, _load(db, flow_id, user), kem_buoc=True))


@router.patch("/{flow_id}")
def update_flow(flow_id: int, data: FlowIn, db: Session = Depends(get_db),
                user=Depends(require("approval_flow", "write"))):
    flow = _load(db, flow_id, user, "write")
    for ten, gia_tri in data.model_dump().items():
        setattr(flow, ten, gia_tri)
    _len_ban_moi(db, flow, user.id)
    canh_bao = flow_service.canh_bao_trung_mac_dinh(db, flow)
    return success(serializer.flow_out(db, flow, kem_buoc=True),
                   f"Đã lưu luồng duyệt. ⚠ {canh_bao}" if canh_bao else "Đã lưu luồng duyệt")


@router.delete("/{flow_id}")
def delete_flow(flow_id: int, db: Session = Depends(get_db),
                user=Depends(require("approval_flow", "delete"))):
    flow = _load(db, flow_id, user, "delete")
    _chan_khi_dang_chay(db, flow.id)
    db.query(ApprovalNode).filter(ApprovalNode.flow_id == flow.id).delete()
    db.delete(flow)
    db.commit()
    record(db, user.id, "approval_flow", flow_id, "delete")
    return success(None, "Đã xóa luồng duyệt")


@router.post("/{flow_id}/nodes")
def add_node(flow_id: int, data: NodeIn, as_branch: bool = False,
             db: Session = Depends(get_db),
             user=Depends(require("approval_flow", "write"))):
    """Thêm một bước. `as_branch=true` = nhánh song song của chặng đó, mặc định
    là chèn hẳn một chặng mới tại vị trí `seq`."""
    flow = _load(db, flow_id, user, "write")
    node = flow_service.them_buoc(db, flow.id, data.model_dump(), user.id,
                                  la_nhanh=as_branch)
    _len_ban_moi(db, flow, user.id)
    db.refresh(node)
    return success(serializer.node_out(db, node), "Đã thêm bước", 201)


@router.patch("/{flow_id}/nodes/{node_id}")
def update_node(flow_id: int, node_id: int, data: NodeIn, db: Session = Depends(get_db),
                user=Depends(require("approval_flow", "write"))):
    flow = _load(db, flow_id, user, "write")
    node = db.get(ApprovalNode, node_id)
    if node is None or node.flow_id != flow.id:
        raise HTTPException(404, "Không tìm thấy bước này")
    for ten, gia_tri in data.model_dump().items():
        setattr(node, ten, gia_tri)
    db.flush()

    #  CR-114 — phiếu ĐANG CHẠY bám theo người duyệt vừa sửa. Trước đây chúng
    #  giữ nguyên bản chụp cũ, nên đổi người duyệt xong mở phiếu ra vẫn thấy tên
    #  người cũ và không có đường nào sửa — người dùng đọc ra là "sửa không ăn".
    #  Chỉ người duyệt mới bám theo; cấu trúc bước vẫn đóng băng theo bản chụp.
    so_phieu = flow_sync_service.dong_bo_sau_khi_sua_buoc(
        db, node, user.id,
        lambda entity, entity_id: entity_hooks.boi_canh(db, entity, entity_id))

    _len_ban_moi(db, flow, user.id)
    db.refresh(node)
    return success(
        serializer.node_out(db, node),
        f"Đã lưu bước và cập nhật {so_phieu} phiếu đang chạy" if so_phieu
        else "Đã lưu bước",
    )


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
    flow = _load(db, flow_id, user, "write")
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
    flow = _load(db, flow_id, user, "write")
    node = db.get(ApprovalNode, node_id)
    if node is None or node.flow_id != flow.id:
        raise HTTPException(404, "Không tìm thấy bước này")
    db.delete(node)
    _len_ban_moi(db, flow, user.id)
    return success(None, "Đã xóa bước")


def _load(db: Session, flow_id: int, user, action: str = "read") -> ApprovalFlow:
    """Nạp luồng duyệt, CÓ kiểm phạm vi — B-07.

    `ApprovalFlow` có `company_id` nên luồng duyệt là dữ liệu của từng pháp nhân. Trước
    B-07 hàm này gọi thẳng `db.get`, nên ai có `approval_flow.write` là sửa được bộ máy
    duyệt của MỌI pháp nhân — hỏng ở đây thì hỏng cả đường duyệt chứng từ, không chỉ một
    phiếu. Đây là chốt duy nhất của mọi endpoint có `flow_id`, giữ nguyên như vậy.
    """
    flow = get_scoped(db, ApprovalFlow, "approval_flow", flow_id, user,
                      get_perm_profile(db, user), action)
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
    flow.version_no = _ban_ke_tiep(db, flow)
    flow.updated_by = actor
    db.commit()
    record(db, actor, "approval_flow", flow.id, "update", f"Lên bản {flow.version_no}")


def _ban_ke_tiep(db: Session, flow: ApprovalFlow) -> int:
    """Số bản kế tiếp CÒN TRỐNG của cặp (entity, code).

    ⚠️ Không phải `version_no + 1`. Bảng có `UNIQUE(entity, code, version_no)`,
    mà `code` **được phép bỏ trống** — nên hai luồng khác nhau cùng mã rỗng là
    chuyện bình thường trên dữ liệu thật. Lúc đó luồng B lên bản 2 sẽ đâm vào
    luồng A đang giữ bản 2, `IntegrityError` bay thẳng ra ngoài thành **500 trần
    không có nội dung** — người dùng chỉ thấy «Request failed with status code
    500» và bước vừa khai biến mất (lỗi khách báo 25/08/2026, dựng lại được:
    `Duplicate entry 'document--2' for key 'uq_approval_flow_code_version'`).

    Nhảy qua số đã có người giữ: số bản chỉ để người đọc tra lịch sử, không cần
    liên tục — kẹt không sửa nổi luồng mới là cái giá đắt hơn nhiều.
    """
    dang_dung = {
        row[0] for row in
        db.query(ApprovalFlow.version_no)
        .filter(ApprovalFlow.entity == flow.entity,
                ApprovalFlow.code == flow.code,
                ApprovalFlow.id != flow.id)
        .all()
    }
    ke_tiep = (flow.version_no or 0) + 1
    while ke_tiep in dang_dung:
        ke_tiep += 1
    return ke_tiep


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
