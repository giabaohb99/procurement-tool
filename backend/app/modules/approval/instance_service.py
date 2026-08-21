"""MÁY CHẠY PHIÊN DUYỆT — mở chặng, đi tiếp, kết thúc (I04–I08, I15, I21).

Phần "người dùng bấm gì" nằm ở `action_service`. Ở đây chỉ có *phiếu đang ở đâu
và đi đâu tiếp*.
"""
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import approver_resolver, entity_hooks, flow_service, task_notification
from .flow_model import (MULTI_ALL, MULTI_ANY, MULTI_QUORUM, MULTI_SEQUENTIAL,
                         NO_APPROVER_FALLBACK, NODE_CC, SKIP_ADJACENT,
                         SKIP_ANY_BEFORE, SKIP_NONE)
from .instance_model import (ACTION_APPROVE, ACTION_FINISH,
                             ACTION_SKIP_DUPLICATE, ACTION_START,
                             INSTANCE_APPROVED, INSTANCE_BLOCKED,
                             INSTANCE_OPEN_STATUSES, INSTANCE_RUNNING,
                             TASK_APPROVED, TASK_PENDING,
                             TASK_SKIPPED_DUPLICATE, TASK_WAITING,
                             ApprovalAction, ApprovalInstance, ApprovalTask)


# ── Tra cứu ─────────────────────────────────────────────────────────────────

def phien_dang_chay(db: Session, entity: str, entity_id: int) -> ApprovalInstance | None:
    return (
        db.query(ApprovalInstance)
        .filter(ApprovalInstance.entity == entity,
                ApprovalInstance.entity_id == entity_id,
                ApprovalInstance.status.in_(INSTANCE_OPEN_STATUSES))
        .order_by(ApprovalInstance.id.desc())
        .first()
    )


def viec_cua_phien(db: Session, instance_id: int) -> list[ApprovalTask]:
    return (
        db.query(ApprovalTask)
        .filter(ApprovalTask.instance_id == instance_id)
        .order_by(ApprovalTask.node_seq.asc(), ApprovalTask.order_no.asc(),
                  ApprovalTask.id.asc())
        .all()
    )


def ghi_dau_vet(db: Session, instance: ApprovalInstance, action: int, actor: int,
                node_seq: int = 0, node_name: str = "", comment: str = "",
                task_id: int | None = None, actor_employee_id: int | None = None,
                on_behalf_of_id: int | None = None,
                delegation_id: int | None = None) -> ApprovalAction:
    row = ApprovalAction(
        instance_id=instance.id, task_id=task_id, node_seq=node_seq, node_name=node_name,
        action=action, actor_employee_id=actor_employee_id,
        on_behalf_of_id=on_behalf_of_id, delegation_id=delegation_id,
        comment=comment, created_by=actor, updated_by=actor,
    )
    db.add(row)
    return row


# ── Bắt đầu ─────────────────────────────────────────────────────────────────

def bat_dau(db: Session, entity: str, entity_id: int, subject: dict,
            submitter_employee_id: int | None, actor: int,
            entity_code: str = "", entity_title: str = "", *,
            chi_luong_phap_nhan: bool = False) -> ApprovalInstance | None:
    """Trình một phiếu vào bộ máy. `None` = không có luồng nào áp, gọi đường cũ."""
    if phien_dang_chay(db, entity, entity_id):
        raise HTTPException(400, "Phiếu này đang có một phiên duyệt chưa kết thúc")

    flow = flow_service.chon_luong(
        db, entity, subject, chi_phap_nhan=chi_luong_phap_nhan,
    )
    if flow is None:
        return None

    raw_snapshot = flow_service.snapshot(db, flow)
    chang = flow_service.cac_chang(raw_snapshot)
    if not chang:
        raise HTTPException(400, f"Luồng «{flow.name}» chưa khai bước nào")

    instance = ApprovalInstance(
        entity=entity, entity_id=entity_id,
        entity_code=entity_code, entity_title=entity_title,
        flow_id=flow.id, flow_version=flow.version_no, flow_snapshot=raw_snapshot,
        status=INSTANCE_RUNNING, current_seq=chang[0],
        started_by_employee_id=submitter_employee_id, started_at=datetime.now(),
        created_by=actor, updated_by=actor,
    )
    db.add(instance)
    db.flush()

    ghi_dau_vet(db, instance, ACTION_START, actor,
                actor_employee_id=submitter_employee_id,
                comment=f"Trình duyệt theo luồng «{flow.name}» bản {flow.version_no}")
    mo_chang(db, instance, subject, chang[0])
    db.commit()
    db.refresh(instance)
    return instance


# ── Mở một chặng ────────────────────────────────────────────────────────────

def mo_chang(db: Session, instance: ApprovalInstance, subject: dict, seq: int) -> None:
    """Dựng việc cho chặng `seq`, xử lý trùng người và ca không tìm được ai."""
    node = flow_service.buoc_cua_chang(instance.flow_snapshot, seq, subject)
    if node is None:
        #  ⚠️ Không nhánh nào nhận. Đây đúng là ca phiếu biến mất khỏi mọi danh
        #  sách nếu bỏ qua — nên đánh dấu KẸT để nó còn hiện ở đâu đó.
        _ket(db, instance, f"Chặng {seq}: không nhánh nào khớp và luồng không "
                           f"khai nhánh mặc định")
        return

    instance.current_seq = seq

    if node.node_kind == NODE_CC:
        #  I15 — bước nhận bản sao KHÔNG chặn luồng. Ghi dấu vết rồi đi tiếp
        #  ngay; người nhận biết qua thông báo.
        ghi_dau_vet(db, instance, ACTION_APPROVE, instance.updated_by or 0,
                    node_seq=seq, node_name=node.name or "",
                    comment="Bước nhận bản sao — không chặn luồng")
        di_tiep(db, instance, subject)
        return

    nguoi_duyet = approver_resolver.resolve(db, node, subject, instance.started_by_employee_id)
    nguoi_duyet = _bo_nguoi_nop(instance, node, nguoi_duyet)
    nguoi_duyet, da_bo_qua = _tach_nguoi_trung(db, instance, node, nguoi_duyet)

    if not nguoi_duyet:
        if da_bo_qua:
            #  Cả chặng đều là người đã duyệt phía trước → coi như chặng xong.
            di_tiep(db, instance, subject)
            return
        _khong_co_nguoi_duyet(db, instance, node, subject)
        return

    han = datetime.now() + timedelta(hours=node.sla_hours) if node.sla_hours else None
    lan_luot = node.multi_mode == MULTI_SEQUENTIAL

    viec_moi = []
    for thu_tu, employee_id in enumerate(nguoi_duyet, start=1):
        task = ApprovalTask(
            instance_id=instance.id, node_seq=seq, node_name=node.name or "",
            order_no=thu_tu, assignee_employee_id=employee_id,
            #  Bước "lần lượt" chỉ mở việc cho người đầu; những người sau còn
            #  chờ. Mở hết cùng lúc thì "lần lượt" không còn nghĩa gì.
            status=TASK_WAITING if (lan_luot and thu_tu > 1) else TASK_PENDING,
            due_at=han, created_by=instance.updated_by or 0,
            updated_by=instance.updated_by or 0,
        )
        db.add(task)
        viec_moi.append(task)
    db.flush()
    #  Báo NGAY khi việc mở ra. Không báo thì việc nằm im trong hộp «Việc của
    #  tôi» tới lúc người duyệt tự nhớ ra mà mở hộp — phiếu chết giữa luồng.
    task_notification.bao_viec_moi(db, instance, viec_moi)


def _bo_nguoi_nop(instance: ApprovalInstance, node, ids: list[int]) -> list[int]:
    """I08 — người nộp không duyệt phiếu của chính mình.

    Bỏ họ khỏi danh sách chứ không chặn cả bước: bước còn người khác thì vẫn
    chạy bình thường. Bỏ hết thì rơi vào `_khong_co_nguoi_duyet`, và ở đó luật
    thường là đẩy lên cấp trên — đúng câu tài liệu ghi.
    """
    nguoi_nop = instance.started_by_employee_id
    if not nguoi_nop:
        return ids
    return [employee_id for employee_id in ids if employee_id != nguoi_nop]


def _tach_nguoi_trung(db: Session, instance: ApprovalInstance, node,
                      ids: list[int]) -> tuple[list[int], bool]:
    """I06 — ai đã duyệt phía trước thì bước này tự qua.

    Việc tự qua được ghi thành **trạng thái riêng** (`TASK_SKIPPED_DUPLICATE`),
    KHÔNG ghi thành "đã duyệt": bản in dấu vết phải phân biệt *người này đã ký*
    với *bước này tự qua vì trùng người*. Gộp làm một là bản in nói dối rằng có
    thêm một người đã xem xét.
    """
    if node.skip_duplicate == SKIP_NONE or not ids:
        return ids, False

    da_duyet = _da_duyet_truoc_do(db, instance, node)
    con_lai, bo_qua = [], False

    for employee_id in ids:
        if employee_id in da_duyet:
            db.add(ApprovalTask(
                instance_id=instance.id, node_seq=node.seq, node_name=node.name or "",
                order_no=0, assignee_employee_id=employee_id,
                status=TASK_SKIPPED_DUPLICATE, decided_at=datetime.now(),
                created_by=instance.updated_by or 0, updated_by=instance.updated_by or 0,
            ))
            ghi_dau_vet(db, instance, ACTION_SKIP_DUPLICATE, instance.updated_by or 0,
                        node_seq=node.seq, node_name=node.name or "",
                        actor_employee_id=employee_id,
                        comment="Người này đã duyệt ở bước trước nên bước này tự qua")
            bo_qua = True
        else:
            con_lai.append(employee_id)

    db.flush()
    return con_lai, bo_qua


def _da_duyet_truoc_do(db: Session, instance: ApprovalInstance, node) -> set[int]:
    query = db.query(ApprovalTask.assignee_employee_id).filter(
        ApprovalTask.instance_id == instance.id,
        ApprovalTask.status == TASK_APPROVED,
        ApprovalTask.node_seq < node.seq,
    )
    if node.skip_duplicate == SKIP_ADJACENT:
        #  Chỉ nhìn chặng LIỀN TRƯỚC. `node.seq - 1` là đủ vì chặng đánh số liên
        #  tiếp; chặng đó có thể đã bị bỏ qua hết, khi ấy tập rỗng và không ai
        #  bị bỏ — đúng ý "chỉ bỏ khi vừa ký xong".
        query = query.filter(ApprovalTask.node_seq == node.seq - 1)
    elif node.skip_duplicate != SKIP_ANY_BEFORE:
        return set()
    return {row[0] for row in query.all()}


def _khong_co_nguoi_duyet(db: Session, instance: ApprovalInstance, node, subject: dict) -> None:
    """I07 — bước không tìm được ai.

    ⚠️ **Không có nhánh "tự động duyệt qua"**, và đó là chủ ý. Lark có tùy chọn
    đó; với văn bản nó tạo ra văn bản CÓ HIỆU LỰC mà không ai chịu trách nhiệm.
    Hai lối còn lại đều để lại một người cụ thể phải bấm.

    ⚠️ **Nhánh "đẩy lên cấp trên" ĐÃ BỎ** (21/08/2026, CR-114). Nó là chỗ duy
    nhất bộ máy TỰ CHỌN một người không có tên trong luồng — chủ đầu tư chốt
    phiếu phải đi đúng luồng đã khai, không ai thay ai. Luồng cũ còn khai giá
    trị đó thì nay rơi thẳng xuống *dừng phiếu*: hiện ra để người ta sửa luồng,
    chứ không lặng lẽ giao cho một người lạ.
    """
    if node.on_no_approver == NO_APPROVER_FALLBACK and node.fallback_employee_id:
        task = ApprovalTask(
            instance_id=instance.id, node_seq=node.seq, node_name=node.name or "",
            order_no=1, assignee_employee_id=node.fallback_employee_id,
            status=TASK_PENDING, created_by=instance.updated_by or 0,
            updated_by=instance.updated_by or 0,
        )
        db.add(task)
        ghi_dau_vet(db, instance, ACTION_APPROVE, instance.updated_by or 0,
                    node_seq=node.seq, node_name=node.name or "",
                    comment="Không tìm được người duyệt — chuyển cho người dự phòng")
        db.flush()
        #  Người dự phòng lại càng phải được báo: họ không hề chờ phiếu này.
        task_notification.bao_viec_moi(db, instance, [task])
        return

    _ket(db, instance, f"Bước «{node.name or node.seq}» không tìm được người duyệt")


def _ket(db: Session, instance: ApprovalInstance, ly_do: str) -> None:
    """Phiếu kẹt — vẫn là phiên MỞ để nó còn hiện trên màn quản trị.

    Đóng luôn thì phiếu lặng lẽ biến mất và không ai biết là đang thiếu người.
    """
    instance.status = INSTANCE_BLOCKED
    instance.finish_reason = ly_do
    ghi_dau_vet(db, instance, ACTION_FINISH, instance.updated_by or 0,
                node_seq=instance.current_seq, comment=ly_do)
    db.flush()


# ── Đi tiếp ─────────────────────────────────────────────────────────────────

def chang_da_xong(db: Session, instance: ApprovalInstance, node) -> bool:
    """Chặng hiện tại đã đủ điều kiện đi tiếp chưa — phần `multi_mode` của I05."""
    viec = [row for row in viec_cua_phien(db, instance.id) if row.node_seq == node.seq]
    if not viec:
        return True

    thuan = [row for row in viec
             if row.status in (TASK_APPROVED, TASK_SKIPPED_DUPLICATE)]
    con_cho = [row for row in viec if row.status in (TASK_WAITING, TASK_PENDING)]

    if node.multi_mode == MULTI_ANY:
        return bool(thuan)
    if node.multi_mode in (MULTI_ALL, MULTI_SEQUENTIAL):
        return not con_cho
    if node.multi_mode == MULTI_QUORUM:
        can = len(viec) * max(1, min(node.quorum_percent, 100)) / 100
        return len(thuan) >= can
    return not con_cho


def di_tiep(db: Session, instance: ApprovalInstance, subject: dict) -> None:
    """Sang chặng kế; hết chặng thì phiếu coi như đã duyệt xong."""
    chang = flow_service.cac_chang(instance.flow_snapshot)
    ke_tiep = next((seq for seq in chang if seq > instance.current_seq), None)

    if ke_tiep is None:
        instance.status = INSTANCE_APPROVED
        instance.finished_at = datetime.now()
        ghi_dau_vet(db, instance, ACTION_FINISH, instance.updated_by or 0,
                    node_seq=instance.current_seq, comment="Đã duyệt hết các bước")
        db.flush()
        #  Báo cho module chứng từ để nó tự đổi trạng thái theo luật của mình.
        entity_hooks.fire(db, instance, "approved")
        return

    mo_chang(db, instance, subject, ke_tiep)


def mo_viec_ke_tiep_trong_buoc(db: Session, instance: ApprovalInstance, node) -> None:
    """Bước «lần lượt»: người vừa duyệt xong thì mở việc cho người kế."""
    if node.multi_mode != MULTI_SEQUENTIAL:
        return
    cho = [row for row in viec_cua_phien(db, instance.id)
           if row.node_seq == node.seq and row.status == TASK_WAITING]
    if cho:
        cho[0].status = TASK_PENDING
        db.flush()
        #  Tới lượt ai thì báo người đó — việc của họ vừa từ "chờ" sang "phải làm".
        task_notification.bao_viec_moi(db, instance, [cho[0]])
