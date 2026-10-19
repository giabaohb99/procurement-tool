"""Phát / thu hồi khóa AI HỘ nhân sự (ai-CR-212, ai-CR-215) — phần nghiệp vụ dùng chung cho màn Khóa nhân sự
(`controller.py`, `/api/agent-hub/mcp-key-admin/*`) và cho quản trị bằng lời qua cổng MCP (bao-CR-634, `mcp_admin.py`).

Tách khỏi controller để hai đường đi CÙNG một luật: phạm vi tính ở ERP trên hồ sơ nhân sự của người phát
(`erp.key_admin_people` / `erp.key_admin_employees`), ≤ `mcp_keys.BATCH_MAX` người một lượt, người ngoài phạm vi → 403
cả lượt, người đủ khóa còn hiệu lực → bỏ qua có lý do, chỉ báo bằng chuông.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from . import mcp_keys
from .model import AgentMcpKey

log = logging.getLogger("app.agent_hub.key_admin")

KEY_ADMIN_ENTITY = "ai_mcp_key_admin"
MY_AI_LINK = "/me?tab=ai-key"


def list_people_in_scope(db: Session, admin, action: str, **kw) -> list[dict]:
    from . import erp

    people = erp.key_admin_people(db, admin, action, **kw)
    if people is None:
        raise HTTPException(403, f"Không có quyền: {action} {KEY_ADMIN_ENTITY}")
    return people


def plan_issue(db: Session, admin, *, user_ids: list[int], employee_ids: list[int], department_id: int,
               days: int) -> tuple[list[dict], list[dict]]:
    """(người sẽ nhận khóa, người bị bỏ qua vì chưa có tài khoản) — chưa ghi gì. Lỗi đầu vào / phạm vi → HTTPException."""
    from . import erp

    if days not in mcp_keys.ISSUE_DAYS:
        raise HTTPException(400, f"Hạn khóa chỉ chọn: {', '.join(map(str, mcp_keys.ISSUE_DAYS))} ngày.")
    wanted = sorted({int(i) for i in user_ids if i})
    wanted_emp = sorted({int(i) for i in employee_ids if i})
    if not wanted and not wanted_emp and not department_id:
        raise HTTPException(400, "Chọn người nhận hoặc một phòng ban.")
    if len(wanted) + len(wanted_emp) > mcp_keys.BATCH_MAX:
        raise HTTPException(400, f"Tối đa {mcp_keys.BATCH_MAX} người một lượt phát.")
    people: list[dict] = []
    skipped: list[dict] = []
    if wanted or (department_id and not wanted_emp):
        people = list_people_in_scope(db, admin, "create", user_ids=wanted or None, department_id=department_id,
                                      limit=mcp_keys.BATCH_MAX + 1)
        if wanted:
            outside = set(wanted) - {p["user_id"] for p in people}
            if outside:
                raise HTTPException(403, f"{len(outside)} người nằm ngoài phạm vi bạn được phát khóa hộ (hoặc tài khoản đã "
                                         "khóa / chưa gắn hồ sơ nhân sự). Chưa phát khóa nào.")
        elif not people:
            raise HTTPException(404, "Phòng này không có nhân sự nào trong phạm vi bạn được phát khóa hộ.")
    if wanted_emp:
        res = erp.key_admin_employees(db, admin, "create", wanted_emp)
        if res is None:
            raise HTTPException(403, f"Không có quyền: create {KEY_ADMIN_ENTITY}")
        if res["outside"]:
            raise HTTPException(403, f"{len(res['outside'])} nhân sự nằm ngoài phạm vi bạn được phát khóa hộ (hoặc không có "
                                     "thật). Chưa phát khóa nào.")
        seen = {p["user_id"] for p in people}
        people += [p for p in res["people"] if p["user_id"] not in seen]
        skipped += [{"user_id": 0, "employee_id": n["employee_id"], "label": n["label"], "reason": n["reason"]}
                    for n in res["no_account"]]
    if len(people) > mcp_keys.BATCH_MAX:
        raise HTTPException(400, f"Phòng có hơn {mcp_keys.BATCH_MAX} người — chọn từng nhóm người, tối đa "
                                 f"{mcp_keys.BATCH_MAX} người một lượt.")
    return people, skipped


def issue_to_people(db: Session, admin, people: list[dict], *, days: int, name: str = "",
                    skipped: list[dict] | None = None) -> dict:
    """Phát khóa CHỈ ĐỌC chờ nhận cho từng người (đã qua `plan_issue`), báo chuông. Trả {batch_id, issued, skipped}."""
    from . import erp

    batch_id = uuid.uuid4().hex[:16]
    issued = []
    skipped = list(skipped or [])
    for p in people:
        try:
            row = mcp_keys.issue(db, p["user_id"], admin.id, days=days, name=name, batch_id=batch_id)
            issued.append({"user_id": p["user_id"], "employee_id": p.get("employee_id", 0), "label": p["label"],
                           "key_id": row.id})
        except ValueError as e:
            skipped.append({"user_id": p["user_id"], "employee_id": p.get("employee_id", 0), "label": p["label"],
                            "reason": str(e)})
    db.commit()
    if issued:
        issuer = erp.describe(db, admin)[0] or "Quản trị"
        try:
            erp.notify_users(db, [i["user_id"] for i in issued], title="Bạn có khóa kết nối AI chờ nhận",
                             body=f"{issuer} đã phát cho bạn một khóa kết nối AI (chỉ đọc, hạn {days} ngày). Vào Trang "
                                  "cá nhân → AI của tôi, bấm Nhận khóa để xem và chép — khóa chỉ hiện một lần.",
                             link=MY_AI_LINK, by_user_id=admin.id)
        except Exception:  # noqa: BLE001 — chuông hỏng không được làm mất khóa đã phát
            log.warning("phát khóa hộ: không gửi được chuông", exc_info=True)
    return {"batch_id": batch_id, "issued": issued, "skipped": skipped}


def find_live_keys(db: Session, *, key_ids: list[int] | None = None, user_ids: list[int] | None = None,
                   batch_id: str = "") -> list[AgentMcpKey]:
    """Khóa CHƯA thu hồi khớp một trong các điều kiện (id khóa · chủ khóa · lượt phát)."""
    conds = []
    if key_ids:
        conds.append(AgentMcpKey.id.in_({int(i) for i in key_ids}))
    if user_ids:
        conds.append(AgentMcpKey.user_id.in_({int(i) for i in user_ids}))
    if batch_id:
        conds.append(AgentMcpKey.batch_id == batch_id)
    if not conds:
        return []
    return [r for r in db.scalars(select(AgentMcpKey).where(or_(*conds)).order_by(AgentMcpKey.id)) if r.revoked_at is None]


def check_revoke_scope(db: Session, admin, rows: list[AgentMcpKey]) -> dict[int, dict]:
    """Chủ khóa nào ngoài phạm vi thu hồi hộ → 403 cả lệnh. Trả {user_id: người} để in nhãn."""
    owners = {int(r.user_id) for r in rows}
    people = {p["user_id"]: p for p in list_people_in_scope(db, admin, "delete", user_ids=sorted(owners))}
    if owners - set(people):
        raise HTTPException(403, f"{len(owners - set(people))} chủ khóa nằm ngoài phạm vi bạn được thu hồi hộ. Chưa thu hồi "
                                 "khóa nào.")
    return people
