"""bao-CR-732 — tối ưu sao lưu CSDL ERP: dump luồng, bảng nhật ký máy chỉ lấy cấu trúc, dữ liệu tra cứu thị trường tách
bản riêng (bỏ qua khi không đổi), khôi phục nạp hai bản đúng thứ tự. Giả mysqldump bằng `subprocess.Popen` giả.
"""
import gzip
import io

import pytest

from app.modules.backup import service as bk
from app.modules.backup.model import DbBackup

MYSQL_VERSION = b"mysqldump  Ver 8.4.13 for Linux on x86_64 (MySQL Community Server - GPL)"


class _Done:
    def __init__(self, stdout=b"", returncode=0, stderr=b""):
        self.stdout, self.returncode, self.stderr = stdout, returncode, stderr


@pytest.fixture
def dump(monkeypatch):
    """Giả client: mỗi lượt dump trả một khối có đầu / cuối như mysqldump thật, ghi lại dòng lệnh."""
    state = {"calls": [], "rc": 0, "out": None}

    class _Popen:
        def __init__(self, cmd, **kwargs):
            state["calls"].append(list(cmd))
            body = state["out"] if state["out"] is not None else (
                b"-- MySQL dump 10.13\n-- pass " + str(len(state["calls"])).encode() + b"\n" + b"x" * 3_000_000
                + b"\n-- Dump completed on 2026-11-05\n")
            self.stdout = io.BytesIO(body)
            self._stderr = kwargs.get("stderr")

        def wait(self):
            if state["rc"] and self._stderr is not None:
                self._stderr.write(b"mysqldump: Got error 2013")
            return state["rc"]

    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(bk.subprocess, "run", lambda cmd, **kw: _Done(MYSQL_VERSION))
    monkeypatch.setattr(bk.subprocess, "Popen", _Popen)
    return state


@pytest.fixture
def storage(monkeypatch):
    uploads: dict[str, bytes] = {}
    kinds: list[type] = []

    def _upload(f, key, ct=""):
        kinds.append(type(f))
        uploads[key] = f.read()
        return key

    monkeypatch.setattr(bk, "upload_fileobj", _upload)
    monkeypatch.setattr(bk, "delete_key", lambda key: None)
    monkeypatch.setattr(bk, "is_remote_storage_ready", lambda: True)
    return uploads, kinds


def test_ban_chinh_bo_du_lieu_nhat_ky_may_va_tra_cuu_nhung_giu_cau_truc(dump):
    out = io.BytesIO()
    bk.dump_main_to(out, "procurement")
    first, second = dump["calls"]
    ignored = {a.split(".", 1)[1] for a in first if a.startswith("--ignore-table=")}
    assert {"tab_sync_log", "tab_import_log", "tab_ui_event", "tab_customs_line", "tab_audit_log"} <= ignored
    assert "--no-data" in second and set(ignored) <= set(second)
    assert "tab_import_change" not in ignored          # ảnh chụp để hoàn tác lô nạp vẫn đi theo bản chính
    assert out.getvalue().count(b"-- Dump completed") == 2


def test_ban_tra_cuu_chi_du_lieu_ghi_ro_ten_cot(dump):
    bk.dump_customs_to(io.BytesIO(), "procurement")
    (cmd,) = dump["calls"]
    assert "--no-create-info" in cmd and "--complete-insert" in cmd
    assert cmd[-len(bk.CUSTOMS_DATA_TABLES):] == list(bk.CUSTOMS_DATA_TABLES)


def test_dump_luong_bao_loi_va_bao_rong(dump):
    dump["rc"] = 2
    with pytest.raises(RuntimeError, match="mã 2.*2013"):
        bk.stream_dump_pass(["mysqldump"], "mysqldump", "thử", io.BytesIO())
    dump["rc"], dump["out"] = 0, b""
    with pytest.raises(RuntimeError, match="Dump rỗng"):
        bk.stream_dump_pass(["mysqldump"], "mysqldump", "thử", io.BytesIO())


def test_dump_luong_cat_dong_sandbox_o_khuc_dau(dump):
    dump["out"] = b"/*!999999\\- enable the sandbox mode */ \n-- MySQL dump\nINSERT 1;\n"
    out = io.BytesIO()
    bk.stream_dump_pass(["mysqldump"], "mysqldump", "thử", out)
    assert b"sandbox" not in out.getvalue() and b"INSERT 1;" in out.getvalue()


def test_sao_luu_day_tep_khong_day_bytes_va_tach_hai_ban(db, dump, storage):
    uploads, kinds = storage
    rec = bk.run_backup(db)
    rows = db.query(DbBackup).order_by(DbBackup.id).all()
    assert [(r.part, r.status) for r in rows] == [("main", "success"), ("customs", "success")]
    assert rec.part == "main" and rows[1].fingerprint
    assert all(k is not io.BytesIO for k in kinds)        # đẩy từ tệp tạm, không giữ bản trong RAM
    main_key = next(k for k in uploads if "-customs-" not in k)
    assert gzip.decompress(uploads[main_key]).count(b"-- Dump completed") == 2
    assert any("-customs-" in k for k in uploads)


def test_ban_tra_cuu_bo_qua_khi_khong_doi_chup_lai_khi_doi(db, dump, storage):
    from app.modules.customs.model import CustomsParty

    bk.run_backup(db)
    bk.run_backup(db)                                       # không đổi gì
    assert db.query(DbBackup).filter_by(part="customs").count() == 1
    db.add(CustomsParty(name="Cong ty moi", dedupe_key="moi"))
    db.commit()
    bk.run_backup(db, with_customs=False)                   # lượt chiều: dữ liệu đổi vẫn chờ lượt sáng
    assert db.query(DbBackup).filter_by(part="customs").count() == 1
    bk.run_backup(db, with_customs=True)
    assert db.query(DbBackup).filter_by(part="customs").count() == 2
    assert db.query(DbBackup).filter_by(part="main").count() == 4


def test_doi_cau_truc_thi_luot_nao_cung_chup():
    class _Last:
        fingerprint = "rev1:aaa"
    assert bk.customs_due(None, "rev1:aaa", daily=False) == "chưa có bản nào"
    assert bk.customs_due(_Last(), "rev1:aaa", daily=True) == ""
    assert bk.customs_due(_Last(), "rev1:bbb", daily=False) == ""
    assert bk.customs_due(_Last(), "rev1:bbb", daily=True) == "dữ liệu đổi"
    assert "migration" in bk.customs_due(_Last(), "rev2:aaa", daily=False)


def test_ban_tra_cuu_hong_khong_lam_hong_ban_chinh(db, dump, storage, monkeypatch):
    monkeypatch.setattr(bk, "dump_customs_to", lambda out, name: (_ for _ in ()).throw(RuntimeError("hỏng")))
    rec = bk.run_backup(db)
    assert rec.status == "success"
    assert db.query(DbBackup).filter_by(part="customs").one().status == "failed"


def test_don_rieng_tung_phan(db, dump, storage, monkeypatch):
    monkeypatch.setattr(bk, "keep_count", lambda: 2)
    monkeypatch.setattr(bk, "CUSTOMS_KEEP", 1)
    from app.modules.customs.model import CustomsParty

    for i in range(3):
        bk.run_backup(db)
        db.add(CustomsParty(name="x", dedupe_key=f"k{i}"))
        db.commit()
    assert db.query(DbBackup).filter_by(part="main", status="success").count() == 2
    assert db.query(DbBackup).filter_by(part="customs", status="success").count() == 1


# ---------- khôi phục ----------
def _patch_restore(monkeypatch, *, customs_rec):
    import scripts.restore_backup as rb

    dump_ok = b"-- MySQL dump 10.13\nCREATE TABLE `tab_user` (id int);\n-- Dump completed on x\n"

    class _Rec:
        def __init__(self, rid, part, key):
            self.id, self.part, self.file_key, self.status = rid, part, key, "success"

    main = _Rec(7, "main", "prod/backup/main.sql.gz")

    class _Session:
        def get(self, model, rid):
            return main if rid == 7 else (customs_rec if customs_rec and rid == customs_rec.id else None)

        def close(self):
            pass

    loads: list[bytes] = []
    files = {main.file_key: dump_ok, "prod/backup/c.sql.gz": b"-- MySQL dump 10.13\nINSERT INTO `tab_customs_line` VALUES (1);\n-- Dump completed on x\n"}

    def _run(cmd, **kwargs):
        loads.append(kwargs["stdin"].read())
        return _Done(returncode=0, stderr="")

    monkeypatch.setattr(rb, "SessionLocal", _Session)
    monkeypatch.setattr(rb, "download_bytes", lambda key: gzip.compress(files[key]))
    monkeypatch.setattr(rb, "kill_other_connections", lambda: None)
    monkeypatch.setattr(rb, "ensure_fulltext_stopwords_off", lambda: None)
    monkeypatch.setattr(rb, "pull_updated", lambda *a, **k: None)
    monkeypatch.setattr(rb, "live_table_names", lambda: {"tab_user"})
    monkeypatch.setattr(rb, "latest_customs_backup", lambda db: customs_rec)
    monkeypatch.setattr(rb.subprocess, "run", _run)
    return rb, loads, _Rec


def test_khoi_phuc_nap_ban_chinh_roi_ban_tra_cuu(monkeypatch, capsys):
    rb, loads, rec_cls = _patch_restore(monkeypatch, customs_rec=None)
    customs = rec_cls(9, "customs", "prod/backup/c.sql.gz")
    monkeypatch.setattr(rb, "latest_customs_backup", lambda db: customs)
    monkeypatch.setattr("sys.argv", ["restore_backup", "--id", "7"])
    rb.main()
    assert len(loads) == 2 and b"CREATE TABLE" in loads[0] and b"tab_customs_line" in loads[1]
    assert "bản tra cứu thị trường #9" in capsys.readouterr().out


def test_khoi_phuc_khong_nhan_ban_tra_cuu_lam_ban_chinh(monkeypatch, capsys):
    rb, loads, rec_cls = _patch_restore(monkeypatch, customs_rec=None)
    customs = rec_cls(7, "customs", "prod/backup/c.sql.gz")
    monkeypatch.setattr(rb, "SessionLocal", lambda: type("S", (), {"get": lambda s, m, r: customs,
                                                                    "close": lambda s: None})())
    monkeypatch.setattr("sys.argv", ["restore_backup", "--id", "7"])
    with pytest.raises(SystemExit) as ex:
        rb.main()
    assert ex.value.code == 1 and loads == []
    assert "bản CHÍNH" in capsys.readouterr().out
