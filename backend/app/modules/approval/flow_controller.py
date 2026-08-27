"""API KHAI LUỒNG (I01–I05, I21, I26).

Khai luồng bằng **dữ liệu**, không sửa mã và không deploy lại — đó là bài nghiệm
thu số 1 của phase.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import AfterValidator, BaseModel, Field
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import (apply_scope, get_perm_profile, get_scoped,
                              has_global_scope)

from . import entity_hooks, flow_service, flow_sync_service, serializer
from .flow_model import (APPROVER_KIND_LABELS, MULTI_MODE_LABELS,
                         NODE_KIND_LABELS, NO_APPROVER_CHOICES,
                         NO_APPROVER_LABELS, ROLE_LABELS,
                         SKIP_MODE_LABELS, ApprovalFlow, ApprovalNode,
                         ApprovalSwitch)
from .instance_model import INSTANCE_OPEN_STATUSES, ApprovalInstance

router = APIRouter(prefix="/api/approval-flows", tags=["approval-flow"])


def _in_labels(labels: dict, field_name: str):
    """Chỉ nhận những giá trị CÓ TRONG bảng nhãn — không khóa cứng biên số.

    ⚠️ Vá lỗi 26/08/2026. `approver_kind` từng khai `le=6` bằng tay; tới khi thêm
    `APPROVER_DEPT_HEAD_OF = 7` thì `/options` bày ra lựa chọn thứ bảy nhưng
    validator vẫn chặn ở 6 — người khai luồng chọn *«Trưởng bộ phận của phòng
    ban chỉ định»* rồi lưu là ăn đúng một dòng đỏ **«approver_kind: Input should
    be less than or equal to 6»**, không có cách nào khai được cái vừa bày ra.

    Biên số viết tay lúc nào cũng là bản chép thứ hai của bảng nhãn, và bản chép
    thứ hai thì sớm muộn cũng lệch. Buộc thẳng vào bảng nhãn thì thêm giá trị
    mới không phải nhớ sửa thêm chỗ nào, mà giá trị bỏ trống ở giữa bảng cũng bị
    chặn — thứ mà `ge/le` không làm được.
    """
    def _check(value: int) -> int:
        if value not in labels:
            allowed = ", ".join(f"{code} ({label})" for code, label in labels.items())
            raise ValueError(f"{field_name} không hợp lệ. Chọn một trong: {allowed}")
        return value

    return _check


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
    #  Mọi ô "chọn một trong danh sách" đều buộc vào chính bảng nhãn mà
    #  `/options` đổ ra ô chọn — xem `_trong_bang`.
    node_kind: Annotated[int, AfterValidator(
        _in_labels(NODE_KIND_LABELS, "Bước làm gì"))] = 1
    flow_role: Annotated[int, AfterValidator(
        _in_labels(ROLE_LABELS, "Vai trò bước"))] = 4
    approver_kind: Annotated[int, AfterValidator(
        _in_labels(APPROVER_KIND_LABELS, "Cách chọn người duyệt"))] = 1
    approver_ref: str = ""
    multi_mode: Annotated[int, AfterValidator(
        _in_labels(MULTI_MODE_LABELS, "Nhiều người thì"))] = 1
    quorum_percent: int = Field(default=50, ge=1, le=100)
    condition: str = ""
    is_default_branch: bool = False
    skip_duplicate: Annotated[int, AfterValidator(
        _in_labels(SKIP_MODE_LABELS, "Trùng người thì"))] = 1
    sla_hours: int = Field(default=0, ge=0)
    fallback_employee_id: int | None = None
    #  Riêng ô này dùng danh sách CÒN KHAI ĐƯỢC, không dùng bảng nhãn: nhãn còn
    #  giữ giá trị 2 để đọc dữ liệu cũ, nhưng nó đã bỏ (CR-114) và không được
    #  khai mới.
    on_no_approver: Annotated[int, AfterValidator(_in_labels(
        {code: NO_APPROVER_LABELS[code] for code in NO_APPROVER_CHOICES},
        "Không tìm được người duyệt thì"))] = 3


class SwitchIn(BaseModel):
    entity: str
    is_enabled: bool
    note: str = ""


@router.get("/options")
def options(user=Depends(require("approval_flow", "read"))):
    """Nhãn tiếng Việt do backend cấp — giao diện không chép cứng."""
    def options_of(labels):
        return [{"value": value, "label": label} for value, label in labels.items()]

    return success({
        "node_kinds": options_of(NODE_KIND_LABELS),
        "flow_roles": options_of(ROLE_LABELS),
        "approver_kinds": options_of(APPROVER_KIND_LABELS),
        "multi_modes": options_of(MULTI_MODE_LABELS),
        "skip_modes": options_of(SKIP_MODE_LABELS),
        #  CHỈ những lựa chọn còn khai được — «Đẩy lên cấp trên» đã bỏ (CR-114)
        #  nên không bày ra ô chọn nữa, dù nhãn của nó vẫn còn để đọc dữ liệu cũ.
        "on_no_approver": [{"value": code, "label": NO_APPROVER_LABELS[code]}
                           for code in NO_APPROVER_CHOICES],
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
    """I26 — đường lui của cả phase: tắt là quay về đường duyệt cũ ngay.

    ⚠️ **CÔNG TẮC TOÀN HỆ, nên đòi phạm vi TOÀN HỆ.**

    Mọi endpoint khác ở đây đều đi qua `_load` (có `get_scoped`, nên phạm vi hẹp
    chỉ đụng được luồng của pháp nhân mình). Riêng cái này không có `flow_id` để
    mà kiểm — nó lật một cờ áp cho **cả 13 pháp nhân**. Chỉ `require(...)` thôi
    thì một văn thư pháp nhân con có `approval_flow.write` phạm vi *công ty* tắt
    được bộ máy duyệt của toàn hệ: từ giây đó mọi văn bản rơi về đường duyệt cũ,
    mà nhật ký chỉ ghi một dòng «Tắt bộ máy duyệt mới cho document».

    Cùng một họ lỗi với `handover` và ủy quyền: quyền vai trò trả lời *"được làm
    việc này không"*, không trả lời *"được làm trên phạm vi nào"*.
    """
    if not has_global_scope(get_perm_profile(db, user), "approval_flow", "write"):
        raise HTTPException(
            403, "Công tắc này áp cho toàn hệ thống nên chỉ người quản trị có phạm vi "
                 "«tất cả» mới bật/tắt được.")

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
    #  ⚠️ SỬA thì `_load` gác bằng `get_scoped`, còn TẠO MỚI thì trước đây không
    #  ai hỏi gì — mà tạo mới đủ sức cướp luôn đường duyệt của cả tập đoàn:
    #  khai một luồng `company_id = None` (áp cho MỌI pháp nhân) với `priority`
    #  cao nhất và đúng một bước «người duyệt = tôi», thế là mọi văn bản mới đều
    #  chạy về tay người khai. Không giả chữ ký của ai, chỉ đổi chỗ cần chữ ký.
    _block_scope_on_declare(db, user, data.company_id, "create")

    flow = ApprovalFlow(**data.model_dump(), created_by=user.id, updated_by=user.id)
    db.add(flow)
    db.commit()
    db.refresh(flow)
    record(db, user.id, "approval_flow", flow.id, "create", flow.name)
    #  Trùng luồng mặc định thì báo NGAY lúc lưu, không đợi người khai tự phát
    #  hiện phiếu đang chạy theo một luồng khác cái họ vừa sửa.
    warning = flow_service.default_overlap_warning(db, flow)
    return success(serializer.flow_out(db, flow),
                   f"Đã tạo luồng duyệt. ⚠ {warning}" if warning else "Đã tạo luồng duyệt", 201)


@router.get("/{flow_id}")
def get_flow(flow_id: int, db: Session = Depends(get_db),
             user=Depends(require("approval_flow", "read"))):
    return success(serializer.flow_out(db, _load(db, flow_id, user), with_steps=True))


@router.patch("/{flow_id}")
def update_flow(flow_id: int, data: FlowIn, db: Session = Depends(get_db),
                user=Depends(require("approval_flow", "write"))):
    flow = _load(db, flow_id, user, "write")
    #  Sửa `company_id` sang pháp nhân khác (hoặc sang «mọi pháp nhân») là cùng
    #  một cuộc chiếm đường duyệt như lúc tạo mới, chỉ khác là đi vòng qua một
    #  luồng vốn thuộc phạm vi của mình.
    if data.company_id != flow.company_id:
        _block_scope_on_declare(db, user, data.company_id, "write")
    for label, value in data.model_dump().items():
        setattr(flow, label, value)
    _new_version(db, flow, user.id)
    warning = flow_service.default_overlap_warning(db, flow)
    return success(serializer.flow_out(db, flow, with_steps=True),
                   f"Đã lưu luồng duyệt. ⚠ {warning}" if warning else "Đã lưu luồng duyệt")


@router.delete("/{flow_id}")
def delete_flow(flow_id: int, db: Session = Depends(get_db),
                user=Depends(require("approval_flow", "delete"))):
    flow = _load(db, flow_id, user, "delete")
    _block_while_running(db, flow.id)
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
    node = flow_service.add_step(db, flow.id, data.model_dump(), user.id,
                                  is_branch=as_branch)
    _new_version(db, flow, user.id)
    db.refresh(node)
    return success(serializer.node_out(db, node), "Đã thêm bước", 201)


@router.patch("/{flow_id}/nodes/{node_id}")
def update_node(flow_id: int, node_id: int, data: NodeIn, db: Session = Depends(get_db),
                user=Depends(require("approval_flow", "write"))):
    flow = _load(db, flow_id, user, "write")
    node = db.get(ApprovalNode, node_id)
    if node is None or node.flow_id != flow.id:
        raise HTTPException(404, "Không tìm thấy bước này")
    for label, value in data.model_dump().items():
        setattr(node, label, value)
    db.flush()

    #  CR-114 — phiếu ĐANG CHẠY bám theo người duyệt vừa sửa. Trước đây chúng
    #  giữ nguyên bản chụp cũ, nên đổi người duyệt xong mở phiếu ra vẫn thấy tên
    #  người cũ và không có đường nào sửa — người dùng đọc ra là "sửa không ăn".
    #  Chỉ người duyệt mới bám theo; cấu trúc bước vẫn đóng băng theo bản chụp.
    updated_count = flow_sync_service.sync_after_step_edit(
        db, node, user.id,
        lambda entity, entity_id: entity_hooks.entity_context(db, entity, entity_id))

    _new_version(db, flow, user.id)
    db.refresh(node)
    return success(
        serializer.node_out(db, node),
        f"Đã lưu bước và cập nhật {updated_count} phiếu đang chạy" if updated_count
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
    by_id = {node.id: node for node in flow_service.nodes_of(db, flow.id)}

    #  ⚠️ HAI LƯỢT, không phải một. `UNIQUE(flow_id, seq, branch_key)` nổ ngay
    #  giữa chừng nếu gán thẳng: hoán vị chặng 1 với chặng 2 thì có một khoảnh
    #  khắc hai bước cùng mang seq = 1. Đẩy hết sang số ÂM trước rồi mới gán số
    #  thật — số âm không bao giờ trùng số thật.
    for order_index, node in enumerate(by_id.values(), start=1):
        node.seq = -order_index
    db.flush()

    for position, stage_node_ids in enumerate(data.stages, start=1):
        for branch, node_id in enumerate(stage_node_ids):
            node = by_id.get(node_id)
            if node is None:
                raise HTTPException(400, f"Bước {node_id} không thuộc luồng này")
            node.seq = position
            #  Các nhánh song song phải khác `branch_key` nhau, nếu không cũng
            #  đâm vào chính ràng buộc trên. Đánh lại theo vị trí thay vì tin
            #  vào giá trị cũ — kéo một bước từ chặng khác sang là trùng ngay.
            node.branch_key = "" if len(stage_node_ids) == 1 else f"n{branch + 1}"
            node.updated_by = user.id
    db.flush()

    _new_version(db, flow, user.id)
    return success(serializer.flow_out(db, flow, with_steps=True), "Đã lưu thứ tự các bước")


@router.delete("/{flow_id}/nodes/{node_id}")
def delete_node(flow_id: int, node_id: int, db: Session = Depends(get_db),
                user=Depends(require("approval_flow", "write"))):
    flow = _load(db, flow_id, user, "write")
    node = db.get(ApprovalNode, node_id)
    if node is None or node.flow_id != flow.id:
        raise HTTPException(404, "Không tìm thấy bước này")
    db.delete(node)
    _new_version(db, flow, user.id)
    return success(None, "Đã xóa bước")


def _block_scope_on_declare(db: Session, user, company_id: int | None, action: str) -> None:
    """Người này có được khai luồng cho pháp nhân đó không.

    Hai bậc:
      * phạm vi **tất cả** → khai cho pháp nhân nào cũng được, kể cả bỏ trống
        (bỏ trống = áp cho MỌI pháp nhân);
      * phạm vi hẹp → **bắt buộc** ghi rõ pháp nhân, và phải là pháp nhân của
        chính mình.

    Cố ý không đọc danh sách pháp nhân trong `UserScope`: khai luồng duyệt là
    việc quản trị hiếm khi làm, thà chặt tay rồi nới sau khi có ca thật, còn hơn
    để một `include` khai rộng tay mở đường cho việc này.
    """
    if has_global_scope(get_perm_profile(db, user), "approval_flow", action):
        return
    if not company_id:
        raise HTTPException(
            403, "Luồng để trống pháp nhân là áp cho MỌI pháp nhân — chỉ người quản trị "
                 "có phạm vi «tất cả» mới khai được. Hãy chọn đúng pháp nhân của bạn.")
    mine = get_perm_profile(db, user).get("company_id") or 0
    if company_id != mine:
        raise HTTPException(403, "Không khai được luồng duyệt cho pháp nhân khác")


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


def _new_version(db: Session, flow: ApprovalFlow, actor: int) -> None:
    """I21 — mỗi lần sửa luồng là một bản mới.

    Phiếu ĐANG CHẠY không bị ảnh hưởng: chúng giữ bản chụp riêng
    (`flow_snapshot`). Số bản ở đây chỉ để người dùng đọc và để tra lịch sử —
    nhưng vẫn phải tăng, không thì hai luồng khác hẳn nhau cùng mang số 1 và
    bản in dấu vết nói sai phiếu chạy theo luồng nào.
    """
    flow.version_no = _next_version(db, flow)
    flow.updated_by = actor
    db.commit()
    record(db, actor, "approval_flow", flow.id, "update", f"Lên bản {flow.version_no}")


def _next_version(db: Session, flow: ApprovalFlow) -> int:
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
    in_use = {
        row[0] for row in
        db.query(ApprovalFlow.version_no)
        .filter(ApprovalFlow.entity == flow.entity,
                ApprovalFlow.code == flow.code,
                ApprovalFlow.id != flow.id)
        .all()
    }
    next_no = (flow.version_no or 0) + 1
    while next_no in in_use:
        next_no += 1
    return next_no


def _block_while_running(db: Session, flow_id: int) -> None:
    running = (
        db.query(ApprovalInstance.id)
        .filter(ApprovalInstance.flow_id == flow_id,
                ApprovalInstance.status.in_(INSTANCE_OPEN_STATUSES))
        .count()
    )
    if running:
        raise HTTPException(
            400,
            f"Còn {running} phiếu đang chạy theo luồng này. Tắt luồng "
            f"(bỏ «Đang dùng») thay vì xóa — phiếu đang chạy vẫn đi hết bản của chúng.",
        )
