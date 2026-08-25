"""NGƯỜI DÙNG BẤM GÌ — duyệt, từ chối, trả lại, rút, góp ý (I09–I11, I16, I23).

Ba hành động **bắt buộc nhập lý do**: từ chối, trả lại, rút lại. Không có lý do
thì người nộp không biết phải sửa gì và lần gửi sau y hệt lần trước — đó là cách
một quy trình duyệt biến thành vòng lặp.
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import delegation_service, entity_hooks, flow_service, instance_service
from .instance_model import (ACTION_APPROVE, ACTION_COMMENT, ACTION_REASSIGN,
                             ACTION_REJECT, ACTION_RETURN, ACTION_WITHDRAW,
                             INSTANCE_OPEN_STATUSES, INSTANCE_REJECTED,
                             INSTANCE_RETURNED, INSTANCE_RUNNING,
                             INSTANCE_WITHDRAWN, TASK_APPROVED, TASK_CANCELLED,
                             TASK_PENDING, TASK_REJECTED, TASK_WAITING,
                             ApprovalInstance, ApprovalTask)


def _dang_mo(instance: ApprovalInstance) -> None:
    if instance.status not in INSTANCE_OPEN_STATUSES:
        raise HTTPException(400, "Phiên duyệt này đã kết thúc")


def _bat_buoc_ly_do(ly_do: str, hanh_dong: str) -> str:
    ly_do = (ly_do or "").strip()
    if not ly_do:
        raise HTTPException(400, f"Phải nêu lý do khi {hanh_dong} — người nộp cần biết sửa gì")
    return ly_do


def viec_dang_cho_cua(db: Session, instance: ApprovalInstance,
                      actor_employee_id: int) -> tuple[ApprovalTask, int | None]:
    """Việc mà người này được phép bấm, kèm id ủy quyền nếu bấm thay.

    Tìm việc của chính mình TRƯỚC: đang có ủy quyền không có nghĩa là mất quyền
    xử lý việc của bản thân.
    """
    dang_cho = [row for row in instance_service.viec_cua_phien(db, instance.id)
                if row.status == TASK_PENDING]

    cua_minh = next((row for row in dang_cho
                     if row.assignee_employee_id == actor_employee_id), None)
    if cua_minh:
        return cua_minh, None

    #  ⚠️ I08 vẫn phải đứng ở đây. Luật «người nộp không duyệt phiếu của chính
    #  mình» đang cắt ở chỗ DỰNG VIỆC (`_bo_nguoi_nop`), mà ủy quyền thì không
    #  đi qua chỗ đó: nó xét lúc BẤM và chỉ hỏi «tờ ủy quyền còn hạn không».
    #  Ghép hai cái lại là người trình ký được chính phiếu mình vừa trình —
    #  trưởng phòng đi công tác ủy quyền cho cấp dưới là việc thường ngày, mà
    #  cấp dưới đúng là người hay trình phiếu. Dấu vết khi đó ghi «B duyệt thay
    #  A», nhìn qua không thấy gì bất thường (25/08/2026).
    if instance.started_by_employee_id == actor_employee_id:
        raise HTTPException(
            403, "Bạn là người trình phiếu này nên không duyệt thay người khác được, "
                 "kể cả khi đang giữ ủy quyền")

    for row in dang_cho:
        uy_quyen = delegation_service.tim_uy_quyen(
            db, actor_employee_id, row.assignee_employee_id, instance.entity)
        if uy_quyen:
            return row, uy_quyen.id

    raise HTTPException(403, "Bạn không có việc nào đang chờ ở phiếu này")


def chiem_viec(db: Session, task: ApprovalTask, trang_thai_moi: int, actor: int) -> None:
    """CHIẾM một việc bằng MỘT câu UPDATE có điều kiện — để CSDL phân xử.

    ⚠️ Gán thẳng `task.status = …` là **đọc rồi mới ghi**, và hai lượt chạy sát
    nhau đều đọc thấy «Đang chờ» rồi cùng ghi. Lỗi dựng lại được 24/08/2026:
    **nhấp đúp nút «Duyệt» ở bước cuối thì CẢ HAI cú đều thành công** — dấu vết
    ghi hai dòng *Duyệt* và hai dòng *Kết thúc* cho một người bấm một lần.
    Văn bản không hỏng (hàm ban hành thấy phiên bản đã khóa nên lần hai ném lỗi
    và bị nuốt), nhưng **bản in dấu vết nói người ta ký hai lần** — mà cả lý do
    tồn tại của dấu vết là để trả lời "ai duyệt cái này", nên nó nói sai là hỏng
    đúng thứ đáng giá nhất.
    """
    so_dong = (
        db.query(ApprovalTask)
        .filter(ApprovalTask.id == task.id, ApprovalTask.status == TASK_PENDING)
        .update({"status": trang_thai_moi, "decided_at": datetime.now(),
                 "updated_by": actor}, synchronize_session=False)
    )
    if so_dong != 1:
        #  Không phải lỗi hệ: đúng nghĩa "người khác (hoặc chính bạn, lượt bấm
        #  trước) vừa xử lý xong việc này". Cùng câu với `concurrency.py`.
        db.rollback()
        raise HTTPException(
            409, "Việc này vừa được xử lý cùng lúc. "
                 "Tải lại trang để xem phiếu đang ở đâu rồi thao tác tiếp.")
    #  ⚠️ FLUSH/REFRESH BẮT BUỘC, không phải cho gọn. Phiên làm việc của hệ chạy
    #  `autoflush=False`, nên nếu không đồng bộ lại thì mọi truy vấn phía sau
    #  vẫn đọc trạng thái CŨ. Đúng lỗi đã bắt được: bước lẽ ra tự qua vì trùng
    #  người lại hỏi người ta ký lần nữa, vì lúc xét trùng nó chưa thấy chữ ký
    #  vừa đặt.
    db.flush()
    db.refresh(task)


def duyet(db: Session, instance: ApprovalInstance, actor_employee_id: int,
          actor: int, subject: dict, y_kien: str = "") -> ApprovalInstance:
    _dang_mo(instance)
    task, delegation_id = viec_dang_cho_cua(db, instance, actor_employee_id)

    chiem_viec(db, task, TASK_APPROVED, actor)
    #  ⚠️ Đặt TRƯỚC khi đi tiếp, không phải sau. Duyệt nốt bước cuối thì
    #  `di_tiep` gọi thẳng hook của chứng từ, mà hook đọc `instance.updated_by`
    #  để biết AI vừa quyết — đọc lúc chưa gán là ra người ghi trước đó (thường
    #  là người gửi duyệt). Hậu quả: văn bản ban hành mang tên người soạn ở cột
    #  người sửa cuối, và dòng nhật ký ghi sai người duyệt.
    instance.updated_by = actor

    instance_service.ghi_dau_vet(
        db, instance, ACTION_APPROVE, actor, node_seq=task.node_seq,
        node_name=task.node_name, comment=y_kien, task_id=task.id,
        actor_employee_id=actor_employee_id,
        #  Bấm thay thì ghi CẢ HAI danh tính — bản in cần câu "ông B duyệt thay
        #  ông A theo ủy quyền số 12". Ghi một người là mất dấu trách nhiệm.
        on_behalf_of_id=task.assignee_employee_id if delegation_id else None,
        delegation_id=delegation_id,
    )

    node = flow_service.buoc_cua_chang(instance.flow_snapshot, task.node_seq, subject)
    if node is not None and instance_service.chang_da_xong(db, instance, node):
        _huy_viec_con_treo(db, instance, task.node_seq, actor)
        instance_service.di_tiep(db, instance, subject)
    elif node is not None:
        instance_service.mo_viec_ke_tiep_trong_buoc(db, instance, node)

    db.commit()
    db.refresh(instance)
    return instance


def tu_choi(db: Session, instance: ApprovalInstance, actor_employee_id: int,
            actor: int, ly_do: str) -> ApprovalInstance:
    """I10 — từ chối: phiếu dừng hẳn, phải làm phiếu mới."""
    _dang_mo(instance)
    ly_do = _bat_buoc_ly_do(ly_do, "từ chối")
    task, delegation_id = viec_dang_cho_cua(db, instance, actor_employee_id)

    chiem_viec(db, task, TASK_REJECTED, actor)

    instance_service.ghi_dau_vet(
        db, instance, ACTION_REJECT, actor, node_seq=task.node_seq,
        node_name=task.node_name, comment=ly_do, task_id=task.id,
        actor_employee_id=actor_employee_id,
        on_behalf_of_id=task.assignee_employee_id if delegation_id else None,
        delegation_id=delegation_id,
    )

    _huy_viec_con_treo(db, instance, None, actor)
    instance.status = INSTANCE_REJECTED
    instance.finished_at = datetime.now()
    instance.finish_reason = ly_do
    instance.updated_by = actor
    db.flush()
    entity_hooks.fire(db, instance, "rejected")
    db.commit()
    db.refresh(instance)
    return instance


def tra_lai(db: Session, instance: ApprovalInstance, actor_employee_id: int,
            actor: int, ly_do: str, subject: dict,
            ve_buoc: int | None = None) -> ApprovalInstance:
    """I09 — trả lại: về người nộp, hoặc về đúng một bước phía trước.

    Khác từ chối ở chỗ phiếu **còn sống**: sửa xong gửi lại được. Trả về một
    bước cụ thể thì những bước sau nó phải duyệt lại từ đầu — người ký sau đã ký
    trên một nội dung khác với nội dung sắp sửa.
    """
    _dang_mo(instance)
    ly_do = _bat_buoc_ly_do(ly_do, "trả lại")
    task, delegation_id = viec_dang_cho_cua(db, instance, actor_employee_id)

    #  KIỂM TRƯỚC KHI SỬA. Bản cũ chiếm việc, ghi dấu vết, hủy việc còn treo rồi
    #  mới xét `ve_buoc` — hỏng ở đó thì việc của người bấm đã mang trạng thái
    #  «đã hủy», và thứ duy nhất cứu là `get_db` cuộn phiên làm việc lại. Dựa
    #  vào một tầng khác để giữ đúng dữ liệu của tầng này là để ngỏ: chỉ cần
    #  chỗ nào phía trên lỡ `commit` là việc biến mất thật, phiếu kẹt không ai
    #  bấm được nữa.
    if ve_buoc is not None:
        chang = flow_service.cac_chang(instance.flow_snapshot)
        if ve_buoc not in chang or ve_buoc >= task.node_seq:
            raise HTTPException(400, "Chỉ trả về được một bước phía trước bước đang đứng")

    chiem_viec(db, task, TASK_CANCELLED, actor)
    #  Gán TRƯỚC hook, cùng lý do như ở `duyet` — nếu không thì văn bản bị trả
    #  về lại mang tên người GỬI DUYỆT trong nhật ký, đúng người không làm việc đó.
    instance.updated_by = actor

    instance_service.ghi_dau_vet(
        db, instance, ACTION_RETURN, actor, node_seq=task.node_seq,
        node_name=task.node_name, comment=ly_do, task_id=task.id,
        actor_employee_id=actor_employee_id,
        on_behalf_of_id=task.assignee_employee_id if delegation_id else None,
        delegation_id=delegation_id,
    )
    _huy_viec_con_treo(db, instance, None, actor)

    if ve_buoc is None:
        instance.status = INSTANCE_RETURNED
        instance.finished_at = datetime.now()
        instance.finish_reason = ly_do
        db.flush()
        entity_hooks.fire(db, instance, "returned")
    else:
        _xoa_ket_qua_tu_buoc(db, instance, ve_buoc, actor)
        instance.status = INSTANCE_RUNNING
        instance_service.mo_chang(db, instance, subject, ve_buoc)

    db.commit()
    db.refresh(instance)
    return instance


def rut_lai(db: Session, instance: ApprovalInstance, actor_employee_id: int,
            actor: int, ly_do: str) -> ApprovalInstance:
    """I11 — người nộp tự rút. **Chỉ khi chưa ai duyệt.**

    Có người đã ký rồi mà vẫn rút được thì chữ ký đó thành vô nghĩa: người ký
    không biết thứ mình vừa ký đã bị rút khỏi quy trình.
    """
    _dang_mo(instance)
    ly_do = _bat_buoc_ly_do(ly_do, "rút lại")

    #  ⚠️ Phiếu KHÔNG ghi người trình thì cấm luôn, đừng bỏ qua câu kiểm. Câu cũ
    #  là `if instance.started_by_employee_id and … != actor`, nên cột để trống
    #  là cả câu kiểm biến mất và AI cũng rút được phiếu của người khác — rút
    #  xong chứng từ quay về nháp. Ba đường duyệt / trả lại / từ chối tự gác
    #  bằng «có việc đang chờ mình không», riêng đường này chỉ có mỗi câu đó.
    #  Cột để trống khi tài khoản trình phiếu chưa gắn hồ sơ nhân sự.
    if instance.started_by_employee_id != actor_employee_id:
        raise HTTPException(403, "Chỉ người trình duyệt mới rút lại được")

    da_co_nguoi_duyet = any(
        row.status == TASK_APPROVED for row in instance_service.viec_cua_phien(db, instance.id))
    if da_co_nguoi_duyet:
        raise HTTPException(
            400, "Đã có người duyệt nên không rút lại được — dùng Trả lại hoặc Từ chối")

    _huy_viec_con_treo(db, instance, None, actor)
    instance_service.ghi_dau_vet(db, instance, ACTION_WITHDRAW, actor,
                                 node_seq=instance.current_seq, comment=ly_do,
                                 actor_employee_id=actor_employee_id)
    instance.status = INSTANCE_WITHDRAWN
    instance.finished_at = datetime.now()
    instance.finish_reason = ly_do
    instance.updated_by = actor
    #  Trả chứng từ về chỗ SỬA ĐƯỢC. Không có nhịp này thì phiếu rút xong nằm
    #  lại ở *đang duyệt*: gửi duyệt lại không được, mà nút duyệt một bước lại
    #  mở ra — thành đường tắt đi vòng qua cả luồng. Xem `entity_hooks.register`.
    entity_hooks.fire(db, instance, "withdrawn")
    db.commit()
    db.refresh(instance)
    return instance


def gop_y(db: Session, instance: ApprovalInstance, actor_employee_id: int,
          actor: int, noi_dung: str) -> None:
    """I16 — ý kiến trao đổi ngay trên phiếu, không qua chat riêng.

    Không đổi trạng thái gì. Nằm chung bảng dấu vết để bản in đọc được theo đúng
    thứ tự thời gian: ý kiến tách khỏi quyết định thì đọc lại không hiểu vì sao
    người ta duyệt.

    ⚠️ **Phiếu đã kết thúc thì thôi.** Chính vì ý kiến nằm chung bảng với quyết
    định và đi thẳng lên bản in dấu vết, cho ghi tiếp sau khi phiếu đóng nghĩa
    là tờ giấy đã ký vẫn dài thêm được. Hộp thoại trên giao diện chỉ mở khi còn
    việc đang chờ nên không ai gặp; nhưng cửa API thì trước đây vẫn nhận
    (25/08/2026).
    """
    _dang_mo(instance)
    noi_dung = (noi_dung or "").strip()
    if not noi_dung:
        raise HTTPException(400, "Chưa nhập ý kiến")
    instance_service.ghi_dau_vet(db, instance, ACTION_COMMENT, actor,
                                 node_seq=instance.current_seq, comment=noi_dung,
                                 actor_employee_id=actor_employee_id)
    db.commit()


def chuyen_nguoi_xu_ly(db: Session, task: ApprovalTask, to_employee_id: int,
                       actor: int, ly_do: str = "") -> ApprovalTask:
    """I07/I23 — đổi người xử lý một việc đang treo (nghỉ việc, bàn giao)."""
    if task.status not in (TASK_WAITING, TASK_PENDING):
        raise HTTPException(400, "Việc này đã xử lý xong, không chuyển được")
    if task.assignee_employee_id == to_employee_id:
        raise HTTPException(400, "Người nhận trùng người đang giữ việc")

    instance = db.get(ApprovalInstance, task.instance_id)
    #  Cửa sau thứ hai đi vòng qua I08, và tiện hơn ủy quyền vì chỉ cần quyền
    #  `approval_flow.write`: giao thẳng việc duyệt vào tay người vừa trình
    #  phiếu. Bàn giao khi nghỉ việc là thao tác quét hàng loạt, nên chuyện này
    #  xảy ra được mà không ai cố ý.
    if instance is not None and instance.started_by_employee_id == to_employee_id:
        raise HTTPException(
            400, "Người nhận chính là người trình phiếu này — họ không duyệt phiếu "
                 "của chính mình được")

    nguoi_cu = task.assignee_employee_id
    task.assignee_employee_id = to_employee_id
    task.updated_by = actor

    instance_service.ghi_dau_vet(
        db, instance, ACTION_REASSIGN, actor, node_seq=task.node_seq,
        node_name=task.node_name, task_id=task.id,
        actor_employee_id=to_employee_id, on_behalf_of_id=nguoi_cu,
        comment=ly_do or "Chuyển người xử lý",
    )
    db.commit()
    db.refresh(task)
    return task


def ban_giao_hang_loat(db: Session, from_employee_id: int, to_employee_id: int,
                       actor: int, ly_do: str = "") -> int:
    """I23 — nghỉ việc: 30 phiếu đang chờ chuyển hết sang người khác một lần.

    Làm từng phiếu thì người bàn giao bỏ sót, và phiếu bỏ sót nằm im cho tới khi
    có người đi hỏi.
    """
    if from_employee_id == to_employee_id:
        raise HTTPException(400, "Người nhận trùng người bàn giao")

    dang_treo = (
        db.query(ApprovalTask)
        .filter(ApprovalTask.assignee_employee_id == from_employee_id,
                ApprovalTask.status.in_((TASK_WAITING, TASK_PENDING)))
        .all()
    )
    da_chuyen = 0
    for task in dang_treo:
        try:
            chuyen_nguoi_xu_ly(db, task, to_employee_id, actor,
                               ly_do or "Bàn giao hàng loạt khi nghỉ việc")
        except HTTPException:
            #  Trong 30 phiếu có phiếu do CHÍNH người nhận trình — phiếu đó
            #  không chuyển được (I08). Đổ cả mẻ vì nó thì người bàn giao phải
            #  ngồi dò từng phiếu, đúng cái mà thao tác quét này sinh ra để
            #  tránh. Bỏ qua và đếm đúng số đã chuyển; số còn lại vẫn hiện
            #  trong hộp việc của người cũ nên không mất dấu.
            continue
        da_chuyen += 1
    return da_chuyen


# ── Dọn việc ────────────────────────────────────────────────────────────────

def _huy_viec_con_treo(db: Session, instance: ApprovalInstance,
                       node_seq: int | None, actor: int) -> None:
    """Việc còn treo mà phiếu đã đi tiếp thì phải hủy, không để nằm lại.

    Bỏ sót là màn "Việc của tôi" hiện việc của một phiếu đã xong — người dùng
    bấm vào không làm được gì, và lần sau họ thôi tin cái danh sách đó.
    """
    query = db.query(ApprovalTask).filter(
        ApprovalTask.instance_id == instance.id,
        ApprovalTask.status.in_((TASK_WAITING, TASK_PENDING)),
    )
    if node_seq is not None:
        query = query.filter(ApprovalTask.node_seq == node_seq)
    for row in query.all():
        row.status = TASK_CANCELLED
        row.updated_by = actor
    db.flush()


def _xoa_ket_qua_tu_buoc(db: Session, instance: ApprovalInstance, tu_buoc: int,
                         actor: int) -> None:
    """Trả về bước N thì kết quả duyệt từ bước N trở đi không còn giá trị.

    KHÔNG xóa dòng dấu vết — bảng đó chỉ ghi thêm. Chỉ hủy các việc, để lượt
    duyệt mới dựng việc mới.
    """
    for row in instance_service.viec_cua_phien(db, instance.id):
        if row.node_seq >= tu_buoc and row.status != TASK_CANCELLED:
            row.status = TASK_CANCELLED
            row.updated_by = actor
    db.flush()
