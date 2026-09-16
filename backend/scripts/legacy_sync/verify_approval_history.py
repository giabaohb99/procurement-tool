"""Kiểm lại lịch sử duyệt vừa nạp — ĐỌC QUA ĐÚNG ĐƯỜNG MÀN HÌNH SẼ ĐỌC.

Đếm dòng trong bảng là chưa đủ: lượt nạp đầu tiên đếm đủ 1313 phiên + 3745 dấu
vết mà màn danh sách vẫn vẽ **cả ba chặng của phiếu đã duyệt thành "đã hủy"**,
vì thiếu bảng việc. Nên bài kiểm ở đây gọi thẳng `steps_service` và
`serializer` — hai thứ dựng nên cái người dùng nhìn thấy.

    docker compose exec -T -e PYTHONPATH=/app api \
        python /app/scripts/legacy_sync/verify_approval_history.py

Ba con số phải đúng:

* **Việc ở trạng thái 1 hoặc 2 = 0.** Lịch sử là chuyện đã rồi, không được đẻ
  ra việc CHỜ — đẻ ra là màn "Việc của tôi" của hàng chục người đầy phiếu cũ.
* **Phiên đã duyệt (2) không còn chặng nào `cancelled`.** Chặng không chạy trên
  phiếu duyệt xong phải là `skipped`.
* **Số dấu vết có `task_id` = số việc.** Mỗi việc đúng một lượt quyết kết cục.
"""
import collections

from sqlalchemy import select, text

from app.core import all_models  # noqa: F401  (nạp đủ mapper trước khi truy vấn)
from app.core.database import SessionLocal
from app.modules.approval import serializer, steps_service
from app.modules.approval.instance_model import (INSTANCE_APPROVED,
                                                 TASK_STATUS_LABELS,
                                                 ApprovalInstance)

#  Lô 200 id một lượt: `steps_of_entities` gom 3 truy vấn cho cả lô, nhưng mệnh
#  đề IN dài quá thì MySQL tự đổi kế hoạch và chậm hẳn.
CHUNK = 200


def count_rows(db) -> None:
    print("=== SO DONG ===")
    for q in ("select count(*) from tab_approval_instance",
              "select count(*) from tab_approval_task",
              "select count(*) from tab_approval_action",
              "select count(*) from tab_approval_action where task_id is not null"):
        print(f"  {db.execute(text(q)).scalar():>6}  {q}")

    print("\n=== VIEC THEO TRANG THAI ===")
    for status, n in db.execute(text(
            "select status, count(*) from tab_approval_task "
            "group by status order by status")):
        flag = "  <-- SAI: lich su khong duoc de ra viec CHO" if status in (1, 2) else ""
        print(f"  {n:>6}  {status} {TASK_STATUS_LABELS.get(status, '')}{flag}")


def count_steps(db) -> None:
    rows = db.execute(select(ApprovalInstance.entity, ApprovalInstance.entity_id,
                             ApprovalInstance.status)).all()
    by_entity: dict[str, list[int]] = collections.defaultdict(list)
    status_of: dict[tuple[str, int], int] = {}
    for entity, entity_id, status in rows:
        by_entity[entity].append(entity_id)
        status_of[(entity, entity_id)] = status

    tally: dict[int, collections.Counter] = collections.defaultdict(collections.Counter)
    summaries: dict[int, collections.Counter] = collections.defaultdict(collections.Counter)
    for entity, ids in by_entity.items():
        for start in range(0, len(ids), CHUNK):
            chunk = ids[start:start + CHUNK]
            for entity_id, info in steps_service.steps_of_entities(db, entity, chunk).items():
                status = status_of[(entity, entity_id)]
                for step in info["steps"]:
                    tally[status][step["state"]] += 1
                summaries[status][info["summary"]] += 1

    print("\n=== VE CHANG (trang thai phien -> trang thai chang) ===")
    for status in sorted(tally):
        print(f"  phien {status}:")
        for state, n in tally[status].most_common():
            flag = ""
            if status == INSTANCE_APPROVED and state == steps_service.STEP_CANCELLED:
                flag = "  <-- SAI: phieu duyet xong khong duoc co chang 'da huy'"
            print(f"      {state:<12} {n}{flag}")

    print("\n=== CAU TOM TAT hay gap nhat ===")
    for status in sorted(summaries):
        for summary, n in summaries[status].most_common(2):
            print(f"  phien {status}: x{n}  {summary!r}")


def show_one(db, entity: str, status: int) -> None:
    inst = db.execute(
        select(ApprovalInstance)
        .where(ApprovalInstance.entity == entity, ApprovalInstance.status == status)
        .order_by(ApprovalInstance.id)).scalars().first()
    if inst is None:
        return
    out = serializer.instance_out(db, inst, with_details=True)
    print(f"\n=== MOT PHIEU: {out['entity_code']} · {out['status_label']} ===")
    print("  chang trong ban chup:", [(s["seq"], s["name"]) for s in out["steps"]])
    for task in out["tasks"]:
        print(f"    viec  chang {task['node_seq']} · {task['status_label']:<10} · "
              f"{task['assignee_name'] or '(khong tra ra ho so)'} · {task['decided_at']}")
    for action in out["actions"]:
        print(f"    dau vet  chang {action['node_seq']} · "
              f"{action.get('action_label') or action['action']} · {action['created_at']} · "
              f"{action.get('actor_name') or '(He thong)'} · {(action['comment'] or '')[:50]!r}")


def main() -> int:
    db = SessionLocal()
    try:
        count_rows(db)
        count_steps(db)
        show_one(db, "seal_request", INSTANCE_APPROVED)
        show_one(db, "vehicle_booking", INSTANCE_APPROVED)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
