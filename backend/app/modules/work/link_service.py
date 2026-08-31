"""Phân hệ Công việc — phụ thuộc việc trước–sau (B-15).

Tệp này giữ MỘT luật mà không tầng nào khác giữ nổi: **đồ thị phụ thuộc không
được có vòng lặp**. Khóa ngoại không diễn đạt được nó, giao diện thì chỉ thấy
phần dự án đang lọc — nên phép kiểm phải nằm ở đây, trước mỗi lượt ghi.

Mọi đường vào đều qua `get_task_or_403` / `get_list_or_403` như phần còn lại của
phân hệ: gõ thẳng id vào URL không được đọc hay nối việc của dự án mình không
tham gia (`04-phan-quyen.md` §5.1).
"""
from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.work import serializer as ser
from app.modules.work.link_model import WorkTaskLink
from app.modules.work.membership_service import (CAN_EDIT, Actor,
                                                 block_if_archived,
                                                 get_list_or_403)
from app.modules.work.model import WorkLinkType
from app.modules.work.task_model import WorkTask

LINK_TYPES = {int(t) for t in WorkLinkType}


def list_links(db: Session, list_id: int) -> list[WorkTaskLink]:
    """Mọi mũi tên của một dự án. Quyền do NƠI GỌI kiểm — hàm này chạy bên trong
    `task_service.board()`, chỗ đã qua `get_list_or_403` rồi."""
    return (db.query(WorkTaskLink)
            .filter(WorkTaskLink.list_id == list_id)
            .order_by(WorkTaskLink.id).all())


def _task_for_link(db: Session, task_id: int) -> WorkTask:
    t = db.get(WorkTask, task_id)
    if not t or t.deleted_at is not None:
        raise HTTPException(404, "Không thấy công việc cần nối")
    #  Việc con không bao giờ có mặt trên Gantt (C-05) nên một mũi tên trỏ vào nó
    #  là mũi tên KHÔNG VẼ RA ĐƯỢC: người dùng tạo xong không thấy gì, tưởng hỏng.
    if t.parent_id:
        raise HTTPException(400, "Không đặt phụ thuộc cho việc con")
    return t


def create_link(db: Session, actor: Actor, data) -> dict:
    """Nối việc trước → việc sau. Bốn cửa chặn, xem `link_model.WorkTaskLink`."""
    if data.predecessor_id == data.successor_id:
        raise HTTPException(400, "Một công việc không phụ thuộc chính nó")
    if int(data.link_type) not in LINK_TYPES:
        raise HTTPException(400, "Kiểu phụ thuộc không hợp lệ")

    before = _task_for_link(db, data.predecessor_id)
    after = _task_for_link(db, data.successor_id)
    if before.list_id != after.list_id:
        raise HTTPException(400, "Hai công việc không cùng một dự án")

    lst = get_list_or_403(db, actor, before.list_id, CAN_EDIT)
    block_if_archived(lst)

    existing = (db.query(WorkTaskLink)
                .filter(WorkTaskLink.predecessor_id == before.id,
                        WorkTaskLink.successor_id == after.id).first())
    if existing:
        raise HTTPException(400, "Hai công việc này đã có phụ thuộc")

    if creates_cycle(list_links(db, before.list_id), before.id, after.id):
        raise HTTPException(400, "Phụ thuộc này tạo thành vòng lặp")

    link = WorkTaskLink(company_id=lst.company_id, list_id=before.list_id,
                        predecessor_id=before.id, successor_id=after.id,
                        link_type=int(data.link_type), lag_days=int(data.lag_days or 0),
                        created_by=actor.user_id, updated_by=actor.user_id)
    db.add(link)
    db.commit()
    record(db, actor.user_id, "work_task", after.id, "update",
           f"Thêm phụ thuộc: {before.title} → {after.title}")
    return ser.task_link_out(link)


def delete_link(db: Session, actor: Actor, link_id: int) -> None:
    link = db.get(WorkTaskLink, link_id)
    #  403 chứ không 404 khi thiếu quyền: phân biệt hai cái là đã nói cho người
    #  ngoài biết id đó có thật (cùng luật với `get_task_or_403`).
    if not link:
        raise HTTPException(404, "Không thấy phụ thuộc")
    lst = get_list_or_403(db, actor, link.list_id, CAN_EDIT)
    block_if_archived(lst)

    db.delete(link)
    db.commit()
    record(db, actor.user_id, "work_task", link.successor_id, "update", "Xóa phụ thuộc")


def creates_cycle(links: list[WorkTaskLink], predecessor_id: int,
                  successor_id: int) -> bool:
    """Nối `predecessor → successor` có tạo vòng lặp không?

    Hàm THUẦN, nhận sẵn danh sách cạnh để test được mà không cần CSDL.

    Cách kiểm: đi từ việc SAU theo chiều mũi tên; chạm lại việc TRƯỚC nghĩa là
    cạnh mới khép kín một vòng. Có tập `seen` nên đồ thị lỡ đã có vòng sẵn (dữ
    liệu cũ, hoặc hai lượt ghi song song lọt qua) cũng không treo máy.

    Loại phụ thuộc KHÔNG được xét: FS hay SS gì thì cũng là "việc này đứng trước
    việc kia", vòng lặp vẫn là vòng lặp.
    """
    graph: dict[int, list[int]] = defaultdict(list)
    for link in links:
        graph[link.predecessor_id].append(link.successor_id)

    seen = {successor_id}
    queue = [successor_id]
    while queue:
        node = queue.pop()
        if node == predecessor_id:
            return True
        for nxt in graph[node]:
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return False
