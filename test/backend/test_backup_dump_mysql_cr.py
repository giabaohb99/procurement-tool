"""Sao lưu phải KHÔI PHỤC ĐƯỢC vào MySQL 8.4 (phiếu kh-sao-luu-dung, 22/10/2026).

Bối cảnh: image api cài `default-mysql-client` (thực chất là MariaDB), bản dump do
`mariadb-dump` tạo nạp vào MySQL 8.4 chết ở lỗi 3105 — cột sinh
`tab_approval_instance.running_slot` (và `tab_document_version.open_slot`) bị chèn
giá trị. Bộ sao lưu vẫn ghi «thành công», rồi `_prune` xóa dần các bản cũ còn tốt.

Bốn chốt chặn kiểm ở đây:
1. Client MySQL thật → lệnh dump có `--set-gtid-purged=OFF`.
2. Client MariaDB → `run_backup` ghi failed, không tạo bản hỏng.
3. Bản mới nhỏ bất thường (< 50% bản thành công trước) → không dọn bản cũ.
4. Script khôi phục không dùng cờ bỏ qua lỗi, lỗi thì thoát mã khác 0.
"""
from datetime import datetime, timedelta

import pytest

from app.modules.backup import service as backup_service
from app.modules.backup.model import DbBackup


class _FakeProcess:
    def __init__(self, stdout: bytes = b"", returncode: int = 0, stderr: bytes = b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


MYSQL_VERSION = b"mysqldump  Ver 8.4.13 for Linux on x86_64 (MySQL Community Server - GPL)"
MARIADB_VERSION = b"mysqldump from 11.8.6-MariaDB, client 10.19 for debian-linux-gnu (x86_64)"


def _fake_client(monkeypatch, version: bytes, dump_out: bytes = b"-- dump\n") -> list[list[str]]:
    """Giả client dump: `--version` trả chuỗi phiên bản, lượt dump trả `dump_out`."""
    calls: list[list[str]] = []

    def _run(cmd, **kwargs):
        if "--version" in cmd:
            return _FakeProcess(version)
        calls.append(list(cmd))
        return _FakeProcess(dump_out)

    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(backup_service.subprocess, "run", _run)
    return calls


@pytest.fixture
def storage(monkeypatch):
    uploads: dict[str, bytes] = {}
    deleted: list[str] = []
    monkeypatch.setattr(backup_service, "upload_fileobj",
                        lambda f, key, ct="": uploads.__setitem__(key, f.read()) or key)
    monkeypatch.setattr(backup_service, "delete_key", lambda key: deleted.append(key))
    monkeypatch.setattr(backup_service, "is_remote_storage_ready", lambda: True)
    return uploads, deleted


# ---------------------------------------------------------------------------
# 1. Cờ dump của client MySQL
# ---------------------------------------------------------------------------
def test_mysql_client_dump_has_gtid_purged_off(monkeypatch):
    _fake_client(monkeypatch, MYSQL_VERSION)
    cmd = backup_service.build_dump_command("mysqldump")
    assert "--set-gtid-purged=OFF" in cmd
    #  Cờ riêng của MariaDB mà MySQL 8 đã bỏ — đưa vào là mysqldump thật chết ngay.
    assert "--ssl-verify-server-cert=0" not in cmd


def test_both_dump_passes_carry_gtid_flag(monkeypatch):
    calls = _fake_client(monkeypatch, MYSQL_VERSION)
    backup_service.dump_sql("procurement", ("tab_audit_log",))
    assert len(calls) == 2
    assert all("--set-gtid-purged=OFF" in c for c in calls)


# ---------------------------------------------------------------------------
# 2. Client MariaDB bị từ chối
# ---------------------------------------------------------------------------
def test_mariadb_client_makes_run_backup_fail(db, monkeypatch, storage):
    uploads, _ = storage
    calls = _fake_client(monkeypatch, MARIADB_VERSION)
    with pytest.raises(RuntimeError) as err:
        backup_service.run_backup(db)
    assert "MariaDB" in str(err.value)
    assert calls == [], "client MariaDB thì không được chạy lượt dump nào"
    assert uploads == {}, "không được đẩy bản hỏng lên kho"
    rec = db.query(DbBackup).order_by(DbBackup.id.desc()).first()
    assert rec.status == "failed"
    assert "MariaDB" in rec.message


# ---------------------------------------------------------------------------
# 3. Chặn dọn bản cũ khi bản mới đáng ngờ
# ---------------------------------------------------------------------------
def _add(db, status: str, size: int, key: str, *, days_ago: float = 0) -> DbBackup:
    rec = DbBackup(source="auto", status=status, size_bytes=size, file_key=key, message="",
                   started_at=datetime.now() - timedelta(days=days_ago))
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def test_prune_skipped_when_new_backup_abnormally_small(db, monkeypatch, storage):
    _, deleted = storage
    monkeypatch.setattr(backup_service, "keep_count", lambda: 1)
    _add(db, "success", 1000, "old.sql.gz")
    new = _add(db, "success", 400, "new.sql.gz")
    assert backup_service._prune(db, new) == 0
    assert deleted == []
    assert db.query(DbBackup).count() == 2
    db.refresh(new)
    assert "bỏ qua dọn" in new.message.lower()


def test_prune_runs_when_new_backup_normal_size(db, monkeypatch, storage):
    _, deleted = storage
    monkeypatch.setattr(backup_service, "keep_count", lambda: 1)
    _add(db, "success", 1000, "old.sql.gz")
    new = _add(db, "success", 500, "new.sql.gz")       # đúng ngưỡng 50% vẫn dọn
    assert backup_service._prune(db, new) == 1
    assert deleted == ["old.sql.gz"]


def test_prune_compares_with_last_success_not_failed(db, monkeypatch, storage):
    """Bản failed (size 0) đứng giữa không được làm mốc so — mốc là bản THÀNH CÔNG trước."""
    _, deleted = storage
    monkeypatch.setattr(backup_service, "keep_count", lambda: 1)
    _add(db, "success", 1000, "old.sql.gz")
    _add(db, "failed", 0, "")
    new = _add(db, "success", 100, "new.sql.gz")
    assert backup_service._prune(db, new) == 0
    assert deleted == []


def test_prune_runs_when_no_previous_success(db, monkeypatch, storage):
    """Chưa có bản thành công nào trước: không coi là đáng ngờ, bản mới không bị đánh dấu."""
    monkeypatch.setattr(backup_service, "keep_count", lambda: 1)
    _add(db, "failed", 0, "", days_ago=40)
    new = _add(db, "success", 10, "new.sql.gz")
    assert backup_service._prune(db, new) == 1       # chỉ dòng failed quá tuổi
    db.refresh(new)
    assert new.message == ""
    assert db.query(DbBackup).count() == 1


def test_prune_skipped_when_new_backup_not_success(db, monkeypatch, storage):
    _, deleted = storage
    monkeypatch.setattr(backup_service, "keep_count", lambda: 1)
    _add(db, "success", 1000, "old.sql.gz")
    new = _add(db, "failed", 0, "")
    assert backup_service._prune(db, new) == 0
    assert deleted == []


def test_run_backup_keeps_old_copies_when_dump_shrinks(db, monkeypatch, storage):
    """Nối dây đầy đủ: dump «thành công» nhưng bé tí thì bản cũ vẫn còn nguyên."""
    _, deleted = storage
    monkeypatch.setattr(backup_service, "keep_count", lambda: 1)
    _add(db, "success", 10_000_000, "old.sql.gz")
    _fake_client(monkeypatch, MYSQL_VERSION, dump_out="-- gần như rỗng\n".encode())
    rec = backup_service.run_backup(db)
    assert rec.status == "success"
    assert deleted == []
    assert db.query(DbBackup).count() == 2
    assert "bỏ qua dọn" in rec.message.lower()


# ---------------------------------------------------------------------------
# 3b. Rà A2: chốt không tự gỡ sau một lượt; dòng failed không đẩy bản tốt ra
# ---------------------------------------------------------------------------
def test_second_small_backup_still_blocked(db, monkeypatch, storage):
    """Lượt bé thứ hai KHÔNG được lấy lượt bé thứ nhất (đã bị đánh dấu) làm mốc."""
    _, deleted = storage
    monkeypatch.setattr(backup_service, "keep_count", lambda: 1)
    _add(db, "success", 1000, "old.sql.gz")
    first = _add(db, "success", 100, "small1.sql.gz")
    assert backup_service._prune(db, first) == 0
    second = _add(db, "success", 110, "small2.sql.gz")
    assert backup_service._prune(db, second) == 0
    assert deleted == []
    db.refresh(second)
    assert "bỏ qua dọn" in second.message.lower()


def test_baseline_is_median_of_recent_good_backups(db, monkeypatch, storage):
    """Một bản to bất thường lẻ loi không được khóa việc dọn mãi mãi (mốc = trung vị)."""
    _, deleted = storage
    monkeypatch.setattr(backup_service, "keep_count", lambda: 3)
    for size in (1000, 1000, 1000, 9000):
        _add(db, "success", size, f"b{size}.sql.gz")
    new = _add(db, "success", 1000, "new.sql.gz")
    assert backup_service._prune(db, new) == 2


def test_failed_rows_do_not_push_out_good_backups(db, monkeypatch, storage):
    """R2 hỏng nhiều ngày (một chuỗi failed) rồi một lượt thành công: bản tốt cũ phải còn."""
    _, deleted = storage
    monkeypatch.setattr(backup_service, "keep_count", lambda: 3)
    for i in range(3):
        _add(db, "success", 1000, f"good{i}.sql.gz", days_ago=10 - i)
    for i in range(10):
        _add(db, "failed", 0, "", days_ago=5 - i * 0.1)
    new = _add(db, "success", 1000, "new.sql.gz")
    assert backup_service._prune(db, new) == 1
    assert deleted == ["good0.sql.gz"], "chỉ bản tốt cũ nhất vượt quá keep mới bị xóa"
    kept = {r.file_key for r in db.query(DbBackup).filter(DbBackup.status == "success")}
    assert kept == {"good1.sql.gz", "good2.sql.gz", "new.sql.gz"}
    assert db.query(DbBackup).filter(DbBackup.status == "failed").count() == 10


def test_old_failed_rows_pruned_by_age(db, monkeypatch, storage):
    monkeypatch.setattr(backup_service, "keep_count", lambda: 5)
    _add(db, "failed", 0, "", days_ago=40)
    _add(db, "running", 0, "", days_ago=45)
    recent = _add(db, "failed", 0, "", days_ago=2)
    new = _add(db, "success", 1000, "new.sql.gz")
    assert backup_service._prune(db, new) == 2
    assert {r.id for r in db.query(DbBackup)} == {recent.id, new.id}


def test_prune_error_does_not_turn_success_into_failed(db, monkeypatch, storage):
    """Bản đã lên R2 mà dọn lỗi thì vẫn là bản thành công — không được ghi failed rồi bị dọn theo tuổi."""
    monkeypatch.setattr(backup_service, "keep_count", lambda: 1)
    _add(db, "success", 30, "old.sql.gz")
    _fake_client(monkeypatch, MYSQL_VERSION, dump_out=b"-- dump du lieu\n" * 4)

    def _boom(key):
        raise RuntimeError("R2 tạm lỗi khi xóa")

    monkeypatch.setattr(backup_service, "delete_key", _boom)
    rec = backup_service.run_backup(db)
    assert rec.status == "success"


def test_run_backup_refuses_without_r2(db, monkeypatch, storage):
    """Thiếu R2 thì upload_fileobj lùi về uploads/ (phục vụ công khai) — sao lưu phải dừng."""
    uploads, _ = storage
    monkeypatch.setattr(backup_service, "is_remote_storage_ready", lambda: False)
    calls = _fake_client(monkeypatch, MYSQL_VERSION)
    with pytest.raises(RuntimeError) as err:
        backup_service.run_backup(db)
    assert "R2" in str(err.value)
    assert calls == [] and uploads == {}
    rec = db.query(DbBackup).order_by(DbBackup.id.desc()).first()
    assert rec.status == "failed"


# ---------------------------------------------------------------------------
# 3c. Cùng hai chốt ở sao lưu DB bot (agent_hub)
# ---------------------------------------------------------------------------
def _add_bot(db, status, size, key, *, days_ago=0.0):
    from app.modules.agent_hub import db_backup as bk
    from app.modules.agent_hub.model import AgentDbBackup
    from app.modules.agent_hub.timeutil import now_utc

    rec = AgentDbBackup(kind=bk.Kind.BACKUP, source=bk.Source.AUTO, status=status, file_key=key,
                        size_bytes=size, message="", detail={},
                        started_at=now_utc() - timedelta(days=days_ago))
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


@pytest.fixture
def bot_storage(monkeypatch):
    import app.core.storage as core_storage

    deleted: list[str] = []
    monkeypatch.setattr(core_storage, "delete_key", lambda key: deleted.append(key))
    return deleted


def test_bot_failed_rows_do_not_push_out_good_backups(db, monkeypatch, bot_storage):
    from app.modules.agent_hub import db_backup as bk
    from app.modules.agent_hub.model import AgentDbBackup

    monkeypatch.setattr(bk, "keep_count", lambda: 2)
    _add_bot(db, bk.Status.SUCCESS, 1000, "g0", days_ago=9)
    _add_bot(db, bk.Status.SUCCESS, 1000, "g1", days_ago=8)
    for _ in range(6):
        _add_bot(db, bk.Status.FAILED, 0, "", days_ago=3)
    new = _add_bot(db, bk.Status.SUCCESS, 1000, "new")
    assert bk._prune(db, new) == 1
    assert bot_storage == ["g0"]
    assert db.query(AgentDbBackup).filter(AgentDbBackup.status == bk.Status.FAILED).count() == 6


def test_bot_prune_skipped_when_new_backup_abnormally_small(db, monkeypatch, bot_storage):
    from app.modules.agent_hub import db_backup as bk

    monkeypatch.setattr(bk, "keep_count", lambda: 1)
    _add_bot(db, bk.Status.SUCCESS, 1000, "g0")
    small = _add_bot(db, bk.Status.SUCCESS, 100, "small")
    assert bk._prune(db, small) == 0
    small2 = _add_bot(db, bk.Status.SUCCESS, 100, "small2")
    assert bk._prune(db, small2) == 0
    assert bot_storage == []
    db.refresh(small2)
    assert "bỏ qua dọn" in small2.message.lower()


# ---------------------------------------------------------------------------
# 4. Script khôi phục: không bỏ qua lỗi
# ---------------------------------------------------------------------------
COMPLETE_DUMP = (b"-- MySQL dump 10.13  Distrib 8.4.13\nCREATE TABLE `x` (id int);\n"
                 b"CREATE TABLE `tab_y` (id int);\n-- Dump completed on 2026-10-22 10:00:00\n")


def test_restore_command_has_no_force_flag():
    from scripts.restore_backup import build_restore_command

    cmd = build_restore_command("mysql")
    assert "-f" not in cmd and "--force" not in cmd
    #  Chỉ mục FULLTEXT ngram dựng ngay ở CREATE TABLE của bản dump — phải tắt từ dừng
    #  trong CHÍNH phiên nạp, không thì tìm «văn bản» ra rỗng sau khôi phục.
    assert any(a.startswith("--init-command=") and "innodb_ft_enable_stopword" in a
               and "= 0" in a for a in cmd)


def _patch_restore(monkeypatch, rb, *, dump: bytes, live_tables: set[str],
                   load_rc: int = 0, load_err: str = ""):
    """Giả mọi chỗ chạm ngoài của `restore_backup.main`; trả (các bước đã chạy, các lệnh nạp)."""
    import gzip

    class _Rec:
        id, file_key, status = 7, "prod/backup/x.sql.gz", "success"

    class _Session:
        def get(self, model, rid):
            return _Rec() if rid == 7 else None

        def close(self):
            pass

    steps: list[str] = []
    seen: list[list[str]] = []
    monkeypatch.setattr(rb, "SessionLocal", _Session)
    monkeypatch.setattr(rb, "download_bytes", lambda key: gzip.compress(dump))
    monkeypatch.setattr(rb, "kill_other_connections", lambda: steps.append("kill"))
    monkeypatch.setattr(rb, "ensure_fulltext_stopwords_off", lambda: steps.append("ft"))
    monkeypatch.setattr(rb, "pull_updated", lambda *a, **k: steps.append("sync"))
    monkeypatch.setattr(rb, "live_table_names", lambda: set(live_tables))

    def _run(cmd, **kwargs):
        steps.append("load")
        seen.append(list(cmd))
        return _FakeProcess(returncode=load_rc, stderr=load_err)

    monkeypatch.setattr(rb.subprocess, "run", _run)
    monkeypatch.setattr("sys.argv", ["restore_backup", "--id", "7"])
    return steps, seen


def test_restore_failure_exits_nonzero_without_success(monkeypatch, capsys):
    import scripts.restore_backup as rb

    steps, seen = _patch_restore(monkeypatch, rb, dump=COMPLETE_DUMP, live_tables={"x", "tab_y"},
                                 load_rc=1, load_err="ERROR 3105 (HY000) at line 42: generated column")
    with pytest.raises(SystemExit) as ex:
        rb.main()
    assert ex.value.code != 0
    out = capsys.readouterr().out
    assert "SUCCESS" not in out and "XONG" not in out and "thành công" not in out.lower()
    assert "3105" in out
    assert steps == ["kill", "load"], "nạp hỏng thì không được chạy bước sau"
    assert seen and "-f" not in seen[0] and "--force" not in seen[0]


def test_truncated_dump_detected():
    from scripts.restore_backup import check_dump_complete

    assert check_dump_complete(COMPLETE_DUMP) == ""
    assert check_dump_complete(COMPLETE_DUMP[:-30]) != ""
    #  Hai lượt (QĐ-C): lượt đầu cụt mà lượt sau đủ vẫn là bản hỏng.
    first_cut = COMPLETE_DUMP.replace(b"-- Dump completed on 2026-10-22 10:00:00\n", b"")
    assert check_dump_complete(first_cut + b"\n" + COMPLETE_DUMP) != ""
    assert check_dump_complete(COMPLETE_DUMP + b"\n" + COMPLETE_DUMP) == ""


def test_dump_table_names_parsed():
    from scripts.restore_backup import dump_table_names

    assert dump_table_names(COMPLETE_DUMP) == {"x", "tab_y"}


def test_restore_truncated_dump_exits_before_touching_db(monkeypatch, capsys):
    import scripts.restore_backup as rb

    steps, _ = _patch_restore(monkeypatch, rb, dump=COMPLETE_DUMP[:-30], live_tables={"x", "tab_y"})
    with pytest.raises(SystemExit) as ex:
        rb.main()
    assert ex.value.code != 0
    assert steps == [], "bản dump cụt thì không được ngắt kết nối hay nạp gì"
    assert "XONG" not in capsys.readouterr().out


def test_restore_missing_table_after_load_exits_nonzero(monkeypatch, capsys):
    import scripts.restore_backup as rb

    steps, _ = _patch_restore(monkeypatch, rb, dump=COMPLETE_DUMP, live_tables={"x"})
    with pytest.raises(SystemExit) as ex:
        rb.main()
    assert ex.value.code != 0
    out = capsys.readouterr().out
    assert "XONG" not in out and "tab_y" in out
    assert "sync" not in steps


def test_restore_complete_dump_finishes(monkeypatch, capsys):
    import scripts.restore_backup as rb

    steps, _ = _patch_restore(monkeypatch, rb, dump=COMPLETE_DUMP, live_tables={"x", "tab_y", "khac"})
    rb.main()
    assert "XONG" in capsys.readouterr().out
    assert steps == ["kill", "load", "ft", "sync"]


def test_dump_markers_inside_data_are_not_counted():
    """Chuỗi '-- MySQL dump ' nằm TRONG dữ liệu (giữa dòng INSERT) không được tính là một lượt dump."""
    from scripts.restore_backup import check_dump_complete

    data = COMPLETE_DUMP.replace(
        b"CREATE TABLE `tab_y`",
        b"INSERT INTO `x` VALUES ('ghi chu -- MySQL dump  gia');\nCREATE TABLE `tab_y`")
    assert check_dump_complete(data) == ""
    fake_footer = COMPLETE_DUMP[:-45] + b"INSERT INTO `x` VALUES ('-- Dump completed');\n"
    assert check_dump_complete(fake_footer) != ""


def test_mariadb_dump_named_explicitly():
    from scripts.restore_backup import check_dump_complete

    reason = check_dump_complete(b"-- MariaDB dump 10.19  Distrib 10.11.6-MariaDB\nCREATE TABLE `x` (id int);\n"
                                 b"-- Dump completed on 2026-10-01\n")
    assert "MariaDB" in reason and "MySQL 8.4" in reason


# ---------------------------------------------------------------------------
# 5. Rà A2 vòng hai: đang chặn vẫn dọn failed theo tuổi, báo chủ động, chấp nhận cỡ mới
# ---------------------------------------------------------------------------
def test_suspect_still_prunes_old_failed_rows(db, monkeypatch, storage):
    _, deleted = storage
    monkeypatch.setattr(backup_service, "keep_count", lambda: 1)
    monkeypatch.setattr(backup_service, "notify_backup_admins", lambda db, text: 0)
    old_good = _add(db, "success", 1000, "old.sql.gz", days_ago=50)
    _add(db, "failed", 0, "", days_ago=40)
    new = _add(db, "success", 100, "new.sql.gz")
    assert backup_service._prune(db, new) == 1
    assert deleted == []
    assert {r.id for r in db.query(DbBackup)} == {old_good.id, new.id}


def test_suspect_notifies_backup_admins(db, monkeypatch, storage):
    from app.modules.notification.model import Notification
    from app.modules.role.model import Permission, Role
    from app.modules.user.model import User, UserRole

    monkeypatch.setattr(backup_service, "keep_count", lambda: 1)
    role = Role(code="bk_admin_t", name="Quản trị sao lưu")
    other = Role(code="no_bk_t", name="Không có quyền sao lưu")
    db.add_all([role, other])
    db.flush()
    db.add_all([Permission(role_id=role.id, entity="backup", can_read=True),
                Permission(role_id=other.id, entity="purchase_request", can_read=True)])
    u1 = User(email="bk1@test", password_hash="x", is_active=True)
    u2 = User(email="nobk@test", password_hash="x", is_active=True)
    db.add_all([u1, u2])
    db.flush()
    db.add_all([UserRole(user_id=u1.id, role_id=role.id), UserRole(user_id=u2.id, role_id=other.id)])
    db.commit()
    _add(db, "success", 1000, "old.sql.gz")
    new = _add(db, "success", 100, "new.sql.gz")
    backup_service._prune(db, new)
    notes = db.query(Notification).all()
    assert [n.user_id for n in notes] == [u1.id]
    assert notes[0].link == "/system/backups"
    assert "chấp nhận cỡ mới" in notes[0].body.lower()


def test_accept_new_size_unblocks_pruning(db, monkeypatch, storage):
    _, deleted = storage
    monkeypatch.setattr(backup_service, "keep_count", lambda: 3)
    monkeypatch.setattr(backup_service, "notify_backup_admins", lambda db, text: 0)
    for i in range(5):
        _add(db, "success", 1000, f"old{i}.sql.gz", days_ago=10 - i)
    smalls = []
    for i in range(3):
        s = _add(db, "success", 100, f"small{i}.sql.gz", days_ago=3 - i)
        assert backup_service._prune(db, s) == 0
        smalls.append(s)
    assert deleted == []
    assert backup_service.accept_new_size(db, actor_id=9) == 3
    for s in smalls:
        db.refresh(s)
        assert s.message.startswith(backup_service.ACCEPTED_NOTE_PREFIX)
    new = _add(db, "success", 100, "new.sql.gz")
    assert backup_service._prune(db, new) == 6     # small0 + 5 bản to cũ
    db.refresh(new)
    assert new.message == ""
    left = {r.file_key for r in db.query(DbBackup)}
    assert left == {"small1.sql.gz", "small2.sql.gz", "new.sql.gz"}


def test_accept_new_size_with_nothing_blocked(db, storage):
    _add(db, "success", 1000, "a.sql.gz")
    assert backup_service.accept_new_size(db, actor_id=1) == 0


def test_bot_suspect_alerts_and_accept(db, monkeypatch, bot_storage):
    from app.modules.agent_hub import db_backup as bk

    alerts: list[str] = []
    monkeypatch.setattr(bk, "alert", lambda db, t: alerts.append(t))
    monkeypatch.setattr(bk, "keep_count", lambda: 1)
    _add_bot(db, bk.Status.SUCCESS, 1000, "g0", days_ago=2)
    _add_bot(db, bk.Status.FAILED, 0, "", days_ago=40)
    small = _add_bot(db, bk.Status.SUCCESS, 100, "small", days_ago=1)
    assert bk._prune(db, small) == 1                 # chỉ dòng failed quá tuổi
    assert alerts and "chấp nhận cỡ mới" in alerts[0].lower()
    assert bk.accept_new_size(db, actor_id=5) == 1
    new = _add_bot(db, bk.Status.SUCCESS, 100, "new")
    assert bk._prune(db, new) == 2
    assert sorted(bot_storage) == ["g0", "small"]


def test_plan_prune_keep_floor_is_one():
    items = [backup_service.PruneItem(type("R", (), {"id": n})(), True, 100, None, False) for n in (3, 2, 1)]
    out = backup_service.plan_prune(items, keep=0, now=datetime.now())
    assert sorted(i.row.id for i in out) == [1, 2]
