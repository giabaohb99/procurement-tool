"""Sổ audit của tool Trợ lý AI hỏng thì chỉ mất dòng audit, KHÔNG mất phiên (bao-CR-463).

Bản cũ `db.rollback()` cả phiên khi ghi audit hỏng — và nó hỏng THƯỜNG XUYÊN vì cột
`action` chỉ rộng 20 ký tự trong khi tên tool dài hơn. Với web chỉ mất dòng audit;
với bot Telegram thì con trỏ đọc tin trôi theo, cùng một câu hỏi được trả lời bốn lần.
"""
from types import SimpleNamespace

from app.modules.agent_hub.model import AgentMessage
from app.modules.assistant import tools


def test_audit_hong_thi_dong_dang_cho_van_con(db, monkeypatch):
    def no(*a, **kw):
        raise RuntimeError("Data too long for column 'action'")

    monkeypatch.setattr(tools, "record", no)
    db.add(AgentMessage(task_id=0, direction=2, chat_id="1", body="x"))
    db.flush()

    tools._audit(db, SimpleNamespace(id=1), "recent_purchase_orders", {}, {"total": 3})

    db.commit()
    assert db.query(AgentMessage).count() == 1


def test_ten_tool_dai_van_ghi_duoc(db):
    """Cột `action` nay rộng 50: `tool:` + tên tool dài nhất hiện có phải lọt."""
    from app.modules.audit.model import AuditLog

    longest = max((t.name for t in tools.tool_defs()), key=len)
    tools._audit(db, SimpleNamespace(id=1), longest, {}, {"total": 0})
    row = db.query(AuditLog).one()
    assert row.action == f"tool:{longest}"
    assert len(row.action) <= 50
