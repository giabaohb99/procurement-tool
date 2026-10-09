"""ai-CR-139 — sao lưu DB của dịch vụ AI (agent_hub): lịch có mặt ở chế độ service, dump đúng tên + khu R2, báo khi lỗi /
quá 26 giờ, khôi phục thử nạp được bản và tự dọn DB tạm, script quay lại từ chối khi chưa xác nhận, dọn theo lô."""
import gzip
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.core.config import settings
from app.modules.agent_hub import db_backup as bk

BACKEND = Path(__file__).resolve().parents[2] / "backend"
if not (BACKEND / "app").exists():          # trong container api: /app chính là backend
    BACKEND = Path(__file__).resolve().parents[2]


def _beat(mode: str, once_daily: bool) -> dict:
    env = dict(os.environ, AGENT_MODE=mode, BACKUP_ONCE_DAILY="true" if once_daily else "false")
    code = ("import json; from app.core.celery_app import celery_app as c; import app.modules.agent_hub.tasks; "
            "print(json.dumps({'beat': sorted(c.conf.beat_schedule), 'imports': list(c.conf.imports), "
            "'tasks': sorted(t for t in c.tasks if t.startswith('agent.db'))}))")
    out = subprocess.run([sys.executable, "-c", code], cwd=BACKEND, env=env, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-800:]
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_lich_sao_luu_db_bot_co_mat_o_che_do_service():
    svc = _beat("service", once_daily=True)
    assert {"agent-db-backup-sang", "agent-db-backup-watch", "agent-db-restore-test"} <= set(svc["beat"])
    assert "agent-db-backup-chieu" not in svc["beat"]                  # dev: một lần mỗi ngày
    assert not any(k.startswith("backup-db") for k in svc["beat"])     # lịch ERP vẫn bị lọc như cũ
    assert svc["imports"] == ["app.modules.agent_hub.tasks"]
    assert svc["tasks"] == ["agent.db_backup", "agent.db_backup_watch", "agent.db_restore_test"]
    assert "agent-db-backup-chieu" in _beat("service", once_daily=False)["beat"]   # prod: hai lần như ERP
    #  Nhúng chung DB ERP: bản sao lưu ERP đã gồm bảng bot, không có lịch riêng.
    emb = _beat("embedded", once_daily=False)
    assert not any(k.startswith("agent-db-") for k in emb["beat"]) and "backup-db-sang" in emb["beat"]


@pytest.fixture
def service_mode(monkeypatch):
    import app.core.storage as storage

    monkeypatch.setattr(settings, "AGENT_MODE", "service")
    monkeypatch.setattr(settings, "DB_NAME", "agent_hub")
    monkeypatch.setattr(settings, "STORAGE_PREFIX", "dev")
    monkeypatch.setattr(storage, "is_remote_storage_ready", lambda: True)
    uploads: dict[str, bytes] = {}
    deleted: list[str] = []
    monkeypatch.setattr(storage, "upload_fileobj", lambda f, key, ct="": uploads.__setitem__(key, f.read()) or key)
    monkeypatch.setattr(storage, "delete_key", lambda key: deleted.append(key))
    monkeypatch.setattr(storage, "download_bytes", lambda key: uploads[key])
    alerts: list[str] = []
    monkeypatch.setattr(bk, "alert", lambda db, t: alerts.append(t))
    return uploads, deleted, alerts


def test_dump_db_bot_dung_ten_dung_khu_va_giu_n_ban(db, service_mode, monkeypatch):
    from app.modules.backup import service as erp_backup

    uploads, deleted, alerts = service_mode
    calls = []
    monkeypatch.setattr(erp_backup, "dump_sql", lambda name, log_tables=(): calls.append((name, log_tables)) or b"SQL")
    monkeypatch.setattr(bk, "keep_count", lambda: 2)
    recs = [bk.run(db) for _ in range(3)]
    assert calls == [("agent_hub", ())] * 3                              # chỉ DB bot, không lượt bảng nhật ký ERP
    key = recs[-1].file_key
    assert re.fullmatch(r"dev/backup/agent_hub-\d{8}-\d{6}\.sql\.gz", key)
    assert gzip.decompress(uploads[key]) == b"SQL" and recs[-1].size_bytes == len(uploads[key])
    assert recs[-1].status == bk.Status.SUCCESS and alerts == []
    #  Giữ 2 bản mới nhất: bản đầu bị xóa cả dòng lẫn tệp R2.
    from app.modules.agent_hub.model import AgentDbBackup

    assert db.query(AgentDbBackup).count() == 2 and len(deleted) == 1 and deleted[0].startswith("dev/backup/agent_hub-")
    page = bk.page(db, offset=0, limit=20)
    assert page["enabled"] and page["items"][0]["status"] == "success" and page["items"][0]["kind"] == "backup"


def test_sao_luu_loi_thi_ghi_failed_va_bao(db, service_mode, monkeypatch):
    import app.core.storage as storage
    from app.modules.backup import service as erp_backup

    _, _, alerts = service_mode

    def boom(name, log_tables=()):
        raise RuntimeError("mysqldump lỗi ở lượt dữ liệu: Access denied")

    monkeypatch.setattr(erp_backup, "dump_sql", boom)
    with pytest.raises(RuntimeError):
        bk.run(db)
    from app.modules.agent_hub.model import AgentDbBackup

    row = db.query(AgentDbBackup).one()
    assert row.status == bk.Status.FAILED and "Access denied" in row.message
    assert len(alerts) == 1 and "LỖI" in alerts[0]
    #  Thiếu R2: KHÔNG lùi về thư mục uploads công khai.
    monkeypatch.setattr(storage, "is_remote_storage_ready", lambda: False)
    monkeypatch.setattr(erp_backup, "dump_sql", lambda *a, **k: pytest.fail("không được dump khi không có chỗ cất"))
    with pytest.raises(RuntimeError, match="R2"):
        bk.run(db)


def test_bao_khi_qua_26_gio_khong_co_ban_thanh_cong(db, service_mode):
    from app.modules.agent_hub.model import AgentDbBackup

    _, _, alerts = service_mode
    t0 = datetime(2026, 10, 9, 0, 0)
    assert bk.watch(db, now=t0)["ok"] and alerts == []                   # mới dựng: chờ đủ 26 giờ mới tính
    assert bk.watch(db, now=t0 + timedelta(hours=25))["ok"]
    assert bk.watch(db, now=t0 + timedelta(hours=27))["alerted"] is True
    assert "chưa có bản thành công nào" in alerts[0]
    assert bk.watch(db, now=t0 + timedelta(hours=30))["alerted"] is False  # một lần mỗi 24 giờ
    db.add(AgentDbBackup(kind=1, source=1, status=bk.Status.SUCCESS, file_key="k", message="", detail={},
                         started_at=t0 + timedelta(hours=31), finished_at=t0 + timedelta(hours=31)))
    db.commit()
    assert bk.watch(db, now=t0 + timedelta(hours=40))["ok"]
    assert bk.watch(db, now=t0 + timedelta(hours=31 + 27))["alerted"] is True
    assert "cách đây 27 giờ" in alerts[-1] and len(alerts) == 2


def test_khoi_phuc_thu_nap_kiem_roi_xoa_db_tam(db, service_mode, monkeypatch):
    from app.modules.agent_hub.model import AgentDbBackup

    uploads, _, alerts = service_mode
    uploads["dev/backup/agent_hub-x.sql.gz"] = gzip.compress(b"CREATE TABLE ...")
    db.add(AgentDbBackup(kind=1, source=1, status=bk.Status.SUCCESS, file_key="dev/backup/agent_hub-x.sql.gz",
                         size_bytes=10, message="", detail={}, started_at=datetime.utcnow()))
    db.commit()
    calls: list[tuple] = []
    version = {"v": "grp07"}

    def fake_mysql(sql="", *, database="", stdin=None):
        calls.append((sql, database, stdin))
        if "information_schema" in sql:
            return "40"
        if "alembic_version" in sql:
            return version["v"]
        if sql.startswith("SELECT COUNT(*)"):
            return "12"
        return ""

    monkeypatch.setattr(bk, "_mysql", fake_mysql)
    monkeypatch.setattr(bk, "_live_counts", lambda db: {"tables": 41, "alembic_version": "grp07", "tab_agent_message": 50,
                                                        "tab_agent_task": 3, "tab_agent_chat_link": 2,
                                                        "tab_agent_memory": 1})
    rec = bk.restore_test(db)
    assert rec.status == bk.Status.SUCCESS and rec.detail["restored"]["tables"] == 40 and alerts == []
    assert any(c[1] == "agent_hub_restore_test" and c[2] == b"CREATE TABLE ..." for c in calls)   # nạp vào DB TẠM
    assert calls[-1][0] == "DROP DATABASE IF EXISTS `agent_hub_restore_test`"                     # dọn DB tạm
    assert not any("`agent_hub`" in c[0] for c in calls)                                         # không đụng DB thật
    #  Bản hỏng (không có alembic_version): báo + VẪN dọn DB tạm.
    version["v"] = ""
    calls.clear()
    with pytest.raises(RuntimeError, match="alembic_version"):
        bk.restore_test(db)
    assert calls[-1][0] == "DROP DATABASE IF EXISTS `agent_hub_restore_test`" and "Khôi phục thử" in alerts[-1]


def test_kiem_ban_nap_thu():
    live = {"tables": 40, "tab_agent_message": 100, "tab_agent_task": 5, "tab_agent_chat_link": 2, "tab_agent_memory": 0}
    good = {"tables": 39, "alembic_version": "grp07", "tab_agent_message": 90, "tab_agent_task": 5,
            "tab_agent_chat_link": 2, "tab_agent_memory": 0}
    assert bk.check_restored(good, live) == []
    assert any("thiếu bảng" in e for e in bk.check_restored({**good, "tables": 20}, live))
    assert any("tab_agent_message rỗng" in e for e in bk.check_restored({**good, "tab_agent_message": 0}, live))
    assert any("không có bảng tab_agent_task" in e for e in bk.check_restored({**good, "tab_agent_task": None}, live))


def test_che_do_nhung_khong_sao_luu_rieng(db, monkeypatch):
    monkeypatch.setattr(settings, "AGENT_MODE", "embedded")
    monkeypatch.setattr(bk, "alert", lambda db, t: None)
    with pytest.raises(RuntimeError, match="chung DB ERP"):
        bk.run(db)
    assert bk.watch(db)["ok"] and bk.page(db, offset=0, limit=5)["enabled"] is False


# ---------------------------------------------------------------------------
# Script quay lại
# ---------------------------------------------------------------------------
def _restore(tmp_path, *args, stdin=""):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir(exist_ok=True)
    marker = tmp_path / "docker-called"
    (fake_bin / "docker").write_text(f"#!/bin/sh\ntouch {marker}\nexit 0\n")
    (fake_bin / "docker").chmod(0o755)
    env = dict(os.environ, PATH=f"{fake_bin}:{os.environ.get('PATH', '')}", HOME=str(tmp_path))
    p = subprocess.run(["bash", str(BACKEND / "scripts" / "agent_restore.sh"), *args], input=stdin, env=env,
                       capture_output=True, text=True, timeout=30)
    return p, marker.exists()


def test_script_quay_lai_tu_choi_khi_chua_xac_nhan(tmp_path):
    f = tmp_path / "agent_hub-20261009-012000.sql.gz"
    f.write_bytes(gzip.compress(b"SELECT 1;"))
    p, touched = _restore(tmp_path, str(f), "--full", stdin="")
    assert p.returncode == 3 and "Chưa xác nhận" in p.stderr and not touched
    p, touched = _restore(tmp_path, str(f), "--full", stdin="dong y\n")
    assert p.returncode == 3 and not touched
    p, touched = _restore(tmp_path, str(f), "--table", "tab_agent_memory", stdin="LAY LAI tab_agent_memory\n")
    assert p.returncode == 2 and "--where" in p.stderr and not touched          # lấy một phần mà không có điều kiện
    p, touched = _restore(tmp_path, str(f), "--table", "x; DROP DATABASE agent_hub", "--where", "1=1")
    assert p.returncode == 2 and not touched
    p, touched = _restore(tmp_path, str(tmp_path / "khong-co.sql.gz"), "--full")
    assert p.returncode == 2 and not touched
    #  Gõ đúng cụm thì mới đi tiếp (tới docker — ở đây là docker giả).
    p, touched = _restore(tmp_path, str(f), "--full", stdin="QUAY LAI TOAN BO agent_hub\n")
    assert touched


# ---------------------------------------------------------------------------
# Dọn theo lô
# ---------------------------------------------------------------------------
def test_don_so_y_dinh_va_tin_nhom_theo_lo(db):
    from app.modules.agent_hub import intent_ledger as il
    from app.modules.agent_hub.model import AgentIntent
    from app.modules.agent_hub.purge import delete_in_batches

    rows = [il.record(db, user_id=7, channel=il.Channel.WEB, scope=1, scope_key="1", intent="hoi") for _ in range(7)]
    for r in rows[:5]:
        r.created_at = datetime.utcnow() - timedelta(days=il.RETENTION_DAYS + 3)
    db.commit()
    old = AgentIntent.created_at < datetime.utcnow() - timedelta(days=il.RETENTION_DAYS)
    assert delete_in_batches(db, AgentIntent, old, batch=2) == 5
    assert db.query(AgentIntent).count() == 2
    #  Trần số lô: còn sót thì lượt sau dọn tiếp, không chạy vô hạn.
    more = [il.record(db, user_id=7, channel=il.Channel.WEB, scope=1, scope_key="1", intent="hoi") for _ in range(5)]
    for r in more:
        r.created_at = datetime.utcnow() - timedelta(days=il.RETENTION_DAYS + 3)
    db.commit()
    assert delete_in_batches(db, AgentIntent, old, batch=2, max_batches=1) == 2
    assert il.purge(db) == 3
