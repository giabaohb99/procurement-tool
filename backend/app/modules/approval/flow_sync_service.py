"""SỬA LUỒNG THÌ PHIẾU ĐANG CHẠY BÁM THEO (CR-114).

Mặc định của bộ máy là **phiếu chạy theo bản chụp luồng lúc nó bắt đầu**
(`flow_service.snapshot`, I21). Bản chụp bảo vệ một thứ có thật: người quản trị
chèn/xóa/đổi thứ tự bước giữa chừng thì phiếu đang đứng ở bước bị xóa sẽ mất
đích tới, và năm phiếu đang chạy đổi đường cùng lúc.

Nhưng nó bảo vệ luôn cả thứ **không nên** bảo vệ: **ai duyệt bước này**. Người
dùng đổi người duyệt của một bước trong màn Luồng duyệt rồi mở phiếu ra xem —
phiếu vẫn nằm ở tên người cũ, và không có đường nào sửa. Với họ đó là "sửa
không ăn".

Nên module này mở đúng MỘT khe: khi bước được sửa **người duyệt**, các phiếu
đang chạy theo luồng đó được:

  1. **vá lại bản chụp** ở đúng bước đó (bước CHƯA TỚI cũng theo người mới);
  2. **dựng lại việc đang treo** của chính bước đó — hủy việc của người cũ,
     giao cho người mới, báo cho họ;
  3. **hồi sinh phiếu đang KẸT** ở bước đó, nếu nay đã tìm được người duyệt.

Ba thứ KHÔNG đụng tới, và đó là ranh giới của khe này:

  * **việc đã xử lý xong** (đã duyệt / từ chối / tự qua) — chữ ký đã đặt là
    chuyện đã rồi, vá lại là bản in nói dối;
  * **cấu trúc bước** (thêm/xóa/đổi thứ tự) — vẫn đóng băng theo bản chụp;
  * **phiếu đã kết thúc** — không hồi tố gì hết.
"""
import json
import logging

from sqlalchemy.orm import Session

from . import approver_resolver, flow_service, instance_service, task_notification
from .flow_model import MULTI_SEQUENTIAL, NODE_CC, ApprovalNode
from .instance_model import (ACTION_REASSIGN, INSTANCE_BLOCKED,
                             INSTANCE_OPEN_STATUSES, INSTANCE_RUNNING,
                             TASK_CANCELLED, TASK_PENDING, TASK_WAITING,
                             ApprovalInstance, ApprovalTask)

#  Trạng thái của việc CÒN TREO — chỉ những việc này mới dựng lại được.
TREO = (TASK_WAITING, TASK_PENDING)


def _va_ban_chup(instance: ApprovalInstance, node: ApprovalNode) -> bool:
    """Ghi đè bước `node.id` trong bản chụp của phiếu. `False` = phiếu không có bước đó.

    Vá theo **id của bước**, không theo `seq`: một chặng có thể có nhiều nhánh
    song song cùng `seq`, vá theo `seq` là đè nhầm sang nhánh bên cạnh.
    """
    try:
        data = json.loads(instance.flow_snapshot or "{}")
    except json.JSONDecodeError:
        logging.getLogger(__name__).warning(
            "Bản chụp của phiên %s hỏng, không vá được", instance.id)
        return False

    nodes = data.get("nodes") or []
    for i, cu in enumerate(nodes):
        if cu.get("id") == node.id:
            nodes[i] = {ten: getattr(node, ten) for ten in flow_service.NODE_FIELDS}
            instance.flow_snapshot = json.dumps(data, ensure_ascii=False)
            return True
    return False


def _dung_lai_viec(db: Session, instance: ApprovalInstance, node: ApprovalNode,
                   subject: dict, actor: int) -> int:
    """Hủy việc còn treo của bước này rồi giao lại theo người duyệt MỚI.

    Trả về số việc vừa mở. `0` = không tìm được ai — phiếu thành KẸT, chứ tuyệt
    đối không tự đi tiếp: bước không ai duyệt mà vẫn qua là văn bản có hiệu lực
    mà không ai chịu trách nhiệm.
    """
    treo = [row for row in instance_service.viec_cua_phien(db, instance.id)
            if row.node_seq == node.seq and row.status in TREO]
    cu = [row.assignee_employee_id for row in treo]

    nguoi_duyet = approver_resolver.resolve(db, node, subject,
                                            instance.started_by_employee_id)
    nguoi_duyet = instance_service._bo_nguoi_nop(instance, node, nguoi_duyet)
    #  KHÔNG chạy lại `_tach_nguoi_trung` ở đây: nó ghi thêm việc "tự qua" và
    #  thêm dấu vết, mà bước này vốn đã được xét trùng người lúc mở chặng. Chạy
    #  lại là nhân đôi dòng nhật ký cho cùng một sự việc.

    if cu == nguoi_duyet:
        #  Người duyệt tính ra vẫn y nguyên (vd chỉ sửa hạn xử lý, đổi tên bước)
        #  — đừng đụng vào việc đang treo, người ta có thể đang mở dở hộp thoại.
        return len(treo)

    for row in treo:
        row.status = TASK_CANCELLED
        row.updated_by = actor

    if not nguoi_duyet:
        db.flush()
        return 0

    lan_luot = node.multi_mode == MULTI_SEQUENTIAL
    #  Giữ nguyên HẠN của việc cũ: đổi người duyệt không phải là gia hạn cho
    #  phiếu. Không có việc cũ nào (phiếu đang kẹt) thì mới tính hạn mới.
    han = treo[0].due_at if treo else None

    viec_moi = []
    for thu_tu, employee_id in enumerate(nguoi_duyet, start=1):
        task = ApprovalTask(
            instance_id=instance.id, node_seq=node.seq, node_name=node.name or "",
            order_no=thu_tu, assignee_employee_id=employee_id,
            status=TASK_WAITING if (lan_luot and thu_tu > 1) else TASK_PENDING,
            due_at=han, created_by=actor, updated_by=actor,
        )
        db.add(task)
        viec_moi.append(task)

    instance_service.ghi_dau_vet(
        db, instance, ACTION_REASSIGN, actor, node_seq=node.seq,
        node_name=node.name or "",
        comment="Luồng duyệt đổi người duyệt của bước này — việc chuyển sang người mới",
    )
    db.flush()
    #  Người mới phải BIẾT là việc vừa rơi vào tay mình.
    task_notification.bao_viec_moi(db, instance, viec_moi)
    return len(viec_moi)


def dong_bo_sau_khi_sua_buoc(db: Session, node: ApprovalNode, actor: int,
                             boi_canh) -> int:
    """Đẩy thay đổi của một bước xuống mọi phiếu ĐANG CHẠY theo luồng đó.

    `boi_canh(entity, entity_id) -> dict` là hàm dựng lại bối cảnh chứng từ để
    tính người duyệt (vd phòng chủ trì của văn bản). Bộ máy duyệt cố ý không
    biết gì về chứng từ nên phải nhận hàm này từ ngoài.

    Trả về số phiếu đã đụng tới.
    """
    phien = (
        db.query(ApprovalInstance)
        .filter(ApprovalInstance.flow_id == node.flow_id,
                ApprovalInstance.status.in_(INSTANCE_OPEN_STATUSES))
        .all()
    )
    if not phien:
        return 0

    dem = 0
    for instance in phien:
        if not _va_ban_chup(instance, node):
            continue
        dem += 1
        #  Chỉ dựng lại việc khi phiếu đang ĐỨNG ở chặng này. Bước chưa tới thì
        #  bản chụp vừa vá là đủ — tới lượt nó sẽ tự tính theo người mới.
        if instance.current_seq != node.seq:
            continue
        #  Bước nhận bản sao không chặn luồng nên cũng không có việc để dựng lại.
        if node.node_kind == NODE_CC:
            continue

        subject = boi_canh(instance.entity, instance.entity_id)
        so_viec = _dung_lai_viec(db, instance, node, subject, actor)

        if so_viec:
            #  Phiếu đang kẹt mà nay có người duyệt thì cho chạy lại — đó chính
            #  là đường gỡ kẹt bằng cấu hình, khỏi phải sửa tay dưới cơ sở dữ liệu.
            if instance.status == INSTANCE_BLOCKED:
                instance.status = INSTANCE_RUNNING
                instance.finish_reason = ""
                instance.finished_at = None
        elif instance.status == INSTANCE_RUNNING:
            instance_service._ket(
                db, instance,
                f"Bước «{node.name or node.seq}» sau khi đổi người duyệt "
                f"không còn ai duyệt được")
        instance.updated_by = actor

    db.flush()
    return dem
