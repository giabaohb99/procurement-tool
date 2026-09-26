"""Điền lại «Trưởng phòng phê duyệt» cho chứng từ đã duyệt TRƯỚC bao-CR-490 — bao-CR-498.

Cột `approver_employee_id` chỉ được ghi từ lúc bấm Duyệt sau khi CR-490 lên (dev 25/09/2026).
Phiếu duyệt trước đó ô trống, màn hình hiện «Chưa ghi nhận». Script tra nhật ký thao tác
(`tab_audit_log`, dòng `approved` GẦN NHẤT của từng chứng từ — cùng nguồn bản in đang lùi về)
rồi ghi nhân sự của tài khoản đó vào cột. Chỉ đụng dòng đang = 0 và đang ở trạng thái sau duyệt.

    docker compose exec -T api python scripts/backfill_approver_employee.py             # xem, không ghi
    docker compose exec -T api python scripts/backfill_approver_employee.py --apply     # ghi thật
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app.core.all_models  # noqa: E402,F401
from app.core.database import SessionLocal  # noqa: E402
from app.core.print_signers import employee_id_of_user  # noqa: E402
from app.modules.audit.model import AuditLog  # noqa: E402
from app.modules.purchase_order.model import PurchaseOrder  # noqa: E402
from app.modules.purchase_request.model import STATUS_AFTER_APPROVE, PurchaseRequest  # noqa: E402
from app.modules.survey_request.model import SurveyRequest  # noqa: E402

#  (model, entity trong nhật ký, trạng thái coi là ĐÃ QUA bước duyệt)
TARGETS = (
    (PurchaseRequest, "purchase_request", set(STATUS_AFTER_APPROVE)),
    (SurveyRequest, "survey_request",
     {"approved", "processing", "survey_done", "completed", "done"}),
    (PurchaseOrder, "purchase_order", {"approved", "partial", "received", "completed"}),
)


def backfill(db, apply: bool) -> None:
    for model, entity, statuses in TARGETS:
        docs = (db.query(model).filter(model.status.in_(statuses), model.approver_employee_id == 0)
                .order_by(model.id).all())
        latest: dict[int, int] = {}
        if docs:
            ids = [d.id for d in docs]
            for i in range(0, len(ids), 1000):
                rows = (db.query(AuditLog.entity_id, AuditLog.created_by)
                        .filter(AuditLog.entity == entity, AuditLog.action == "approved",
                                AuditLog.entity_id.in_(ids[i:i + 1000]))
                        .order_by(AuditLog.id.desc()).all())
                for eid, uid in rows:
                    latest.setdefault(int(eid), int(uid or 0))     # dòng đầu = lần duyệt gần nhất
        filled = missing = no_employee = 0
        cache: dict[int, int] = {}
        for d in docs:
            uid = latest.get(d.id, 0)
            if not uid:
                missing += 1
                continue
            if uid not in cache:
                cache[uid] = int(employee_id_of_user(db, uid) or 0)
            emp = cache[uid]
            if not emp:
                no_employee += 1
                continue
            print(f"  {entity} {d.code}: tài khoản {uid} → nhân sự {emp}")
            if apply:
                d.approver_employee_id = emp
            filled += 1
        print(f"{entity}: {len(docs)} chứng từ trống · điền {filled} · không có dòng duyệt trong nhật ký "
              f"{missing} · tài khoản không gắn nhân sự {no_employee}")
    if apply:
        db.commit()
        print("Đã ghi.")
    else:
        print("Chạy thử — chưa ghi gì. Thêm --apply để ghi.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split(chr(10))[0])
    ap.add_argument("--apply", action="store_true", help="ghi thật (mặc định chỉ xem)")
    args = ap.parse_args()
    db = SessionLocal()
    try:
        backfill(db, args.apply)
    finally:
        db.close()


if __name__ == "__main__":
    main()
