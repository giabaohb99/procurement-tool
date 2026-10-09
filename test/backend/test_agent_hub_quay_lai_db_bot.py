"""ai-CR-141 — quay lại DB bot (agent_hub) qua thẻ «đúng» trên Telegram: liệt kê bản sao lưu, thẻ duyệt không lộ link tải,
chưa «đúng» thì không chạy, điều kiện lấy lại một phần bị chặn khi có «;» / chú thích, script sinh ra đúng cú pháp bash,
quay lại toàn bộ ghi lại sổ thao tác sau khi DB bị thay."""
import subprocess
from datetime import datetime

import pytest

from app.core.config import settings

URL = "https://r2.example/dev/backup/agent_hub-20261009-012000.sql.gz?X-Amz-Signature=BIMAT123"


@pytest.fixture
def owner(db, monkeypatch):
    import app.core.storage as storage
    from app.modules.agent_hub import db_backup, ops, service
    from app.modules.agent_hub.constants import ENV_DEV
    from app.modules.agent_hub.model import AgentDbBackup, AgentEnv

    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    monkeypatch.setattr(settings, "AGENT_OPS_ENABLED", True)
    monkeypatch.setattr(storage, "presigned_url", lambda key, expires=600, download_name="": URL)
    tasks: list = []
    monkeypatch.setattr(ops, "_send_task", lambda db, name, args: tasks.append((name, args)) or True)
    sent: list[str] = []
    monkeypatch.setattr(service.telegram, "send", lambda text, **kw: sent.append(text) or 1)
    db.add(AgentEnv(name="dev", kind=ENV_DEV, dir="~/procurement-tool-dev", compose_args="", branch="erp-v2",
                    health_url="", db_name="procurement_dev", created_by=0, updated_by=0))
    db.add(AgentDbBackup(kind=db_backup.Kind.BACKUP, source=1, status=db_backup.Status.SUCCESS,
                         file_key="dev/backup/agent_hub-20261009-012000.sql.gz", size_bytes=102400, message="",
                         detail={}, started_at=datetime(2026, 10, 9, 1, 20)))
    db.commit()
    return sent, tasks


def _say(db, text):
    from app.modules.agent_hub import ops, service
    from app.modules.agent_hub.constants import DIR_IN

    row = service.log_message(db, DIR_IN, "12345", 1, text)
    db.commit()
    return ops.handle_text(db, "12345", row, text)


def test_liet_ke_va_the_duyet_khong_lo_link_chua_dung_thi_khong_chay(db, owner):
    from app.modules.agent_hub.constants import OP_BOT_DB_RESTORE, OPS_QUEUED, OPS_WAITING
    from app.modules.agent_hub.model import AgentDbBackup, AgentOp

    sent, tasks = owner
    bid = db.query(AgentDbBackup).one().id
    assert _say(db, "sao lưu db bot") and f"#{bid}" in sent[-1]
    assert _say(db, f"quay lại db bot dev bản #{bid}")
    op = db.query(AgentOp).one()
    assert op.kind == OP_BOT_DB_RESTORE and op.status == OPS_WAITING and tasks == []      # chưa «đúng» → không chạy
    assert op.params["url"] == URL and op.params["mode"] == "full"
    assert "BIMAT123" not in op.command and "BIMAT123" not in sent[-1]                     # link ký sẵn không lên thẻ
    assert "MẤT mọi tin nhắn" in sent[-1] and "restore-safety" in sent[-1]
    assert _say(db, "đúng")
    db.refresh(op)
    assert op.status == OPS_QUEUED and tasks == [("agent.run_op", [op.id])]
    assert _say(db, "quay lại db bot dev bản #999") and "Không có bản sao lưu" in sent[-1]


def test_lay_lai_mot_phan_chan_dieu_kien_nguy_hiem(db, owner):
    from app.modules.agent_hub.model import AgentDbBackup, AgentOp

    sent, _ = owner
    bid = db.query(AgentDbBackup).one().id
    assert _say(db, f"lấy lại tab_agent_memory của db bot dev bản #{bid}: user_id = 7")
    op = db.query(AgentOp).one()
    assert op.params["table"] == "tab_agent_memory" and op.params["where"] == "user_id = 7" and op.params["mode"] == "part"
    assert "REPLACE" in sent[-1] and "bot không dừng" in sent[-1]
    for bad in ("user_id = 7; DROP DATABASE agent_hub", "1=1 -- x", "user_id = 7 /* x */"):
        assert _say(db, f"lấy lại tab_agent_memory của db bot dev bản #{bid}: {bad}")
        assert "so sánh đơn giản" in sent[-1]
    assert db.query(AgentOp).count() == 1


def test_nguoi_khac_khong_ra_lenh_duoc(db, owner):
    from app.modules.agent_hub import ops, service
    from app.modules.agent_hub.constants import DIR_IN
    from app.modules.agent_hub.model import AgentOp

    row = service.log_message(db, DIR_IN, "999", 1, "quay lại db bot dev bản #1")
    assert ops.handle_text(db, "999", row, "quay lại db bot dev bản #1") is False
    assert db.query(AgentOp).count() == 0


def test_script_tai_va_chay_dung_cu_phap_khong_nuot_stdin():
    from app.modules.agent_hub import ops_runner as r

    full = r.bot_restore_script({"mode": "full", "url": URL})
    part = r.bot_restore_script({"mode": "part", "url": URL, "table": "tab_agent_note", "where": "user_id = 7"})
    for s in (full, part):
        proc = subprocess.run(["bash", "-n"], input=s, capture_output=True, text=True)
        assert proc.returncode == 0, (s, proc.stderr)
        assert "</dev/null" in s and "--yes" in s and "rm -f" in s
    assert "--full" in full and "'tab_agent_note'" in part and "'user_id = 7'" in part
    with pytest.raises(r.OpsError):
        r.bot_restore_script({"mode": "full", "url": "file:///etc/passwd"})
    with pytest.raises(r.OpsError):
        r.bot_restore_script({"mode": "part", "url": URL, "table": "x; rm -rf /", "where": "1=1"})


def test_quay_lai_toan_bo_ghi_lai_so_sau_khi_db_bi_thay(db, owner, monkeypatch):
    """Sau quay lại toàn bộ, dòng sổ thao tác cũ đã mất theo bản sao lưu → máy sửa mã ghi LẠI một dòng và báo, link tải
    không còn trong sổ."""
    from app.modules.agent_hub import ops, ops_runner as r
    from app.modules.agent_hub.constants import OP_BOT_DB_RESTORE, OPS_OK
    from app.modules.agent_hub.model import AgentDbBackup, AgentEnv, AgentOp

    bid = db.query(AgentDbBackup).one().id
    env = db.query(AgentEnv).one()
    op, err = ops.new_bot_restore_op(db, env, bid, "12345")
    assert err == ""
    monkeypatch.setattr(r, "_ssh", lambda script, env, **kw: "RESTORED")
    rewritten: list = []
    monkeypatch.setattr(r, "_after_full_bot_restore", lambda snap, status, out, error: rewritten.append(
        (snap, status, out, error)))
    res = r.execute(db, op)
    assert res["status"] == "ok" and len(rewritten) == 1
    snap, status, out, error = rewritten[0]
    assert status == OPS_OK and out == "RESTORED" and snap["params"]["mode"] == "full"
    assert db.query(AgentOp).filter_by(kind=OP_BOT_DB_RESTORE).count() == 1
