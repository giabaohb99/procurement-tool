"""bao-CR-454 — CR-312 P6 đợt 2: phân vùng bốn bảng nhật ký theo năm + dump hai lượt (QĐ-C).

Ba luật cứng được canh ở đây:

1. **Bản sao lưu hằng đêm phải chạy ĐÚNG HAI LƯỢT.** Gộp lại một lượt
   `--ignore-table` là mất luôn `CREATE TABLE` của bốn bảng nhật ký; phục hồi
   xong hệ thống lên xanh rồi chết ở truy vấn đầu tiên chạm nhật ký — tức là ở
   middleware, tức là ở MỌI lượt gọi API. Không có bài kiểm nào bắt được điều
   đó ngoài bài kiểm đếm số lượt dump.
2. **Chỉ bỏ phân vùng của năm đã có bản sao ngoài máy và không còn dòng nào
   chưa quá hạn.** `DROP PARTITION` không hoàn tác được.
3. **Danh sách bốn bảng chỉ khai MỘT CHỖ** (`ARCHIVE_TABLES`). Bảng nhật ký thứ
   năm thêm vào đó phải tự đi theo cả ba đường: đóng gói, sao lưu, phân vùng.

Tài liệu: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §9.
"""
import importlib.util
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.core.config import settings
from app.modules.audit.model import AuditLog
from app.modules.audit.tasks import ARCHIVE_TABLES
from app.modules.backup import service as backup_service
from app.modules.login_session.model import LoginSession
from app.modules.system_log import partition, retention

NOW = datetime(2026, 9, 21, 10, 0, 0)
CUTOFF = datetime(2025, 5, 1)  # mốc 16 tháng tính từ NOW
MIGRATION_FILE = "f2c5b9d71a48_phan_vung_bon_bang_nhat_ky_theo_nam.py"


# ---------------------------------------------------------------------------
# Dựng dữ liệu
# ---------------------------------------------------------------------------
def _audit(db, created_at: datetime) -> AuditLog:
    row = AuditLog(entity="unit", entity_id=1, action="update", message="x",
                   created_by=1, created_at=created_at)
    db.add(row)
    db.flush()
    return row


def _session(db, created_at: datetime, revoked_at=None, expires_at=None) -> LoginSession:
    row = LoginSession(user_id=1, token_id=str(uuid.uuid4()), ip="1.1.1.1",
                       last_seen_ip="1.1.1.1", device_label="chrome / windows",
                       created_at=created_at, revoked_at=revoked_at,
                       expires_at=expires_at or created_at + timedelta(days=7))
    db.add(row)
    db.flush()
    return row


def _load_migration():
    """Nạp tệp migration thẳng từ đĩa — nó không nằm trong gói `app` nên không import được."""
    for root in Path(__file__).resolve().parents:
        for candidate in (root / "migrations" / "versions" / MIGRATION_FILE,
                          root / "backend" / "migrations" / "versions" / MIGRATION_FILE):
            if candidate.exists():
                spec = importlib.util.spec_from_file_location("mig_cr454", candidate)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
    pytest.skip(f"Không tìm thấy {MIGRATION_FILE}")


# ---------------------------------------------------------------------------
# Một danh sách bảng cho cả ba đường
# ---------------------------------------------------------------------------
def test_danh_sach_bang_sao_luu_suy_ra_tu_dong_goi():
    """Chép tay tên bảng sang `backup/service.py` là hai nơi khai, và hai nơi sẽ lệch."""
    assert backup_service.LOG_TABLES == tuple(m.__tablename__ for _, m in ARCHIVE_TABLES)
    assert backup_service.LOG_TABLES == ("tab_audit_log", "tab_request_log",
                                         "tab_change_log", "tab_login_session")


def test_migration_phan_vung_du_bon_bang():
    """Thêm bảng nhật ký thứ năm mà quên migration = bảng đó không bao giờ bỏ được năm cũ."""
    migration = _load_migration()
    assert {row[0] for row in migration.LOG_TABLES} == set(backup_service.LOG_TABLES)
    #  Hai bảng có khóa duy nhất phụ phải được nới ra kèm `created_at`, không thì
    #  MySQL từ chối cả lệnh phân vùng.
    widened = {row[0]: row[1] for row in migration.LOG_TABLES if row[1]}
    assert widened == {"tab_request_log": "request_id", "tab_login_session": "token_id"}


def test_migration_doi_khoa_chinh_trong_mot_cau_alter():
    """`id` là AUTO_INCREMENT — bỏ khóa chính ở câu riêng là lỗi 1075, migration chết giữa chừng."""
    for root in Path(__file__).resolve().parents:
        for candidate in (root / "migrations" / "versions" / MIGRATION_FILE,
                          root / "backend" / "migrations" / "versions" / MIGRATION_FILE):
            if candidate.exists():
                source = candidate.read_text(encoding="utf-8")
                assert "DROP PRIMARY KEY, ADD PRIMARY KEY (id, created_at)" in source
                assert "DROP PRIMARY KEY, ADD PRIMARY KEY (id)" in source  # đường lùi
                return
    pytest.skip(f"Không tìm thấy {MIGRATION_FILE}")


# ---------------------------------------------------------------------------
# Dump hai lượt (QĐ-C)
# ---------------------------------------------------------------------------
class _FakeProcess:
    def __init__(self, stdout: bytes):
        self.returncode = 0
        self.stdout = stdout
        self.stderr = b""


@pytest.fixture
def dump(monkeypatch):
    """Ghi lại mọi dòng lệnh mà `_dump_sql` gọi, không đụng tới mysqldump thật."""
    calls: list[list[str]] = []

    def _fake_run(cmd, **kwargs):
        if "--version" in cmd:
            return _FakeProcess(b"mysqldump Ver 8.4")
        calls.append(list(cmd))
        return _FakeProcess(f"-- luot {len(calls)}\n".encode())

    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr("app.modules.backup.service.subprocess.run", _fake_run)
    return calls


def test_dump_chay_dung_hai_luot(dump):
    out = backup_service._dump_sql()
    assert len(dump) == 2, "Gộp về một lượt là mất CREATE TABLE của bốn bảng nhật ký"
    assert out == b"-- luot 1\n\n-- luot 2\n"


def test_luot_mot_bo_du_lieu_bon_bang_nhat_ky(dump):
    backup_service._dump_sql()
    data_pass = dump[0]
    for table in backup_service.LOG_TABLES:
        assert f"--ignore-table={settings.DB_NAME}.{table}" in data_pass
    #  Không được để tên bảng đứng trần ở lượt này: mysqldump hiểu đối số sau tên
    #  CSDL là «chỉ dump mấy bảng đó», tức lượt 1 sẽ dump ĐÚNG thứ vừa loại ra.
    assert [arg for arg in data_pass if arg in backup_service.LOG_TABLES] == []
    assert "--no-data" not in data_pass
    assert data_pass[-1] == settings.DB_NAME


def test_luot_hai_chi_lay_cau_truc_bon_bang(dump):
    backup_service._dump_sql()
    schema_pass = dump[1]
    assert "--no-data" in schema_pass
    assert schema_pass[-len(backup_service.LOG_TABLES) - 1:] == [settings.DB_NAME,
                                                                 *backup_service.LOG_TABLES]
    assert not any(arg.startswith("--ignore-table=") for arg in schema_pass)


def test_dump_hong_mot_luot_thi_bao_ro_luot_nao(monkeypatch):
    def _fail(cmd, **kwargs):
        if "--version" in cmd:
            return _FakeProcess(b"mysqldump Ver 8.4")
        proc = _FakeProcess(b"")
        proc.returncode = 2
        proc.stderr = b"Access denied"
        return proc

    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr("app.modules.backup.service.subprocess.run", _fail)
    with pytest.raises(RuntimeError) as err:
        backup_service._dump_sql()
    assert "dữ liệu nghiệp vụ" in str(err.value)


def test_dump_rong_thi_ne_m_loi_thay_vi_day_len_r2(monkeypatch):
    """Dump rỗng mà cứ nén và đẩy lên là một bản sao lưu «thành công» không phục hồi được."""
    def _empty(cmd, **kwargs):
        if "--version" in cmd:
            return _FakeProcess(b"mysqldump Ver 8.4")
        return _FakeProcess(b"")

    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr("app.modules.backup.service.subprocess.run", _empty)
    with pytest.raises(RuntimeError) as err:
        backup_service._dump_sql()
    assert "rỗng" in str(err.value)


# ---------------------------------------------------------------------------
# Dựng mệnh đề phân vùng
# ---------------------------------------------------------------------------
def test_ranh_gioi_la_can_tren_ho():
    """`VALUES LESS THAN (2025)` thì phân vùng 2025 rỗng còn dòng 2024 rơi sang nơi khác."""
    clause = partition.build_partition_clause([2025, 2026])
    assert "PARTITION p2025 VALUES LESS THAN (2026)" in clause
    assert "PARTITION p2026 VALUES LESS THAN (2027)" in clause


def test_luon_co_pmax_chot_duoi():
    """Thiếu `pmax` thì dòng của năm chưa khai bị MySQL TỪ CHỐI — nhật ký ngừng ghi."""
    clause = partition.build_partition_clause([2026])
    assert clause.rstrip().endswith("PARTITION pmax VALUES LESS THAN MAXVALUE\n)")


def test_nam_lon_xon_va_trung_duoc_xep_lai():
    clause = partition.build_partition_clause([2027, 2025, 2027, 2026])
    assert clause.count("VALUES LESS THAN (") == 3
    assert clause.index("p2025") < clause.index("p2026") < clause.index("p2027")


def test_khong_co_nam_nao_thi_bao_loi():
    """Trả về mệnh đề chỉ có `pmax` là dựng một bảng không bao giờ bỏ được năm nào."""
    with pytest.raises(ValueError):
        partition.build_partition_clause([])


@pytest.mark.parametrize("name,expect", [
    ("p2025", 2025), ("p1999", 1999), ("pmax", None), ("", None), ("px", None),
    ("p20a5", None), ("q2025", None), (None, None),
])
def test_doc_nguoc_ten_phan_vung(name, expect):
    assert partition.read_partition_year(name) == expect


@pytest.mark.parametrize("bad", [
    "", "  ", "tab_audit_log; DROP TABLE tab_user", "tab-audit-log", "TAB_AUDIT_LOG",
    "1tab", "tab_audit_log`", "tab audit", "t" * 65, None,
])
def test_ten_bang_la_thi_nem_loi(bad):
    """Tên bảng ghép thẳng vào chuỗi DDL, nên chốt này là cửa duy nhất — đừng nới."""
    with pytest.raises(ValueError):
        partition.check_table_name(bad)


def test_ten_bang_that_thi_qua_duoc():
    for table in backup_service.LOG_TABLES:
        assert partition.check_table_name(table) == table


def test_sqlite_khong_co_phan_vung(db):
    """Bộ test chạy SQLite — mọi lệnh phân vùng phải im lặng bỏ qua, không nổ."""
    assert partition.supports_partition(db) is False
    assert partition.list_partition_years(db, "tab_audit_log") == []
    assert partition.ensure_year_partitions(db, "tab_audit_log", 2027) == []
    assert partition.drop_year_partition(db, "tab_audit_log", 2024) is False


# ---------------------------------------------------------------------------
# Điều kiện bỏ phân vùng
# ---------------------------------------------------------------------------
@pytest.fixture
def packaged(monkeypatch):
    """Tập gói `.sha256` coi như đang có trên R2, khai bằng chuỗi `<bảng>:<YYYY-MM>`."""
    have: set[str] = set()

    def _key_exists(key: str) -> bool:
        return any(key.endswith(f"/{label}/{name}.jsonl.gz.sha256")
                   for name, label in (item.split(":") for item in have))

    monkeypatch.setattr("app.modules.system_log.retention.key_exists", _key_exists)
    return have


def test_thang_rong_khong_tinh_la_thieu_goi(db, packaged):
    """`audit.archive` không đẩy gì khi tháng đó rỗng — đòi đủ 12 gói là năm đó kẹt vĩnh viễn."""
    _audit(db, datetime(2024, 6, 10))
    db.commit()
    packaged.add("audit:2024-06")

    assert retention.find_missing_archive_months(db, AuditLog, "audit", 2024) == []


def test_thang_co_dong_ma_chua_co_goi_thi_bao_thieu(db, packaged):
    _audit(db, datetime(2024, 6, 10))
    _audit(db, datetime(2024, 12, 31, 23, 59))
    db.commit()
    packaged.add("audit:2024-06")

    assert retention.find_missing_archive_months(db, AuditLog, "audit", 2024) == ["2024-12"]


def test_dong_cua_nam_khac_khong_lam_nam_nay_thieu_goi(db, packaged):
    """Ranh giới tháng 12: `datetime(year + 1, 1, 1)` chứ không phải `datetime(year, 13, 1)`."""
    _audit(db, datetime(2025, 1, 1))
    db.commit()

    assert retention.find_missing_archive_months(db, AuditLog, "audit", 2024) == []


def test_phien_chua_dong_van_bi_dem_la_chua_qua_han(db):
    """Cột NULL: `NOT (điều kiện)` ra NULL nên dòng rơi khỏi cả hai vế và bị đếm hụt về 0."""
    _session(db, datetime(2024, 12, 28), expires_at=datetime(2026, 12, 31))
    db.commit()

    assert retention.count_unexpired_in_year(db, LoginSession, 2024, CUTOFF) == 1


def test_phien_da_dong_dung_han_thi_khong_con_ai_song(db):
    _session(db, datetime(2024, 12, 28), revoked_at=datetime(2024, 12, 29))
    db.commit()

    assert retention.count_unexpired_in_year(db, LoginSession, 2024, CUTOFF) == 0


def test_dong_nam_khac_khong_lot_vao_phep_dem(db):
    _audit(db, datetime(2025, 6, 1))
    db.commit()

    assert retention.count_unexpired_in_year(db, AuditLog, 2024, CUTOFF) == 0


# ---------------------------------------------------------------------------
# Bỏ phân vùng cả năm
# ---------------------------------------------------------------------------
@pytest.fixture
def partitions(monkeypatch):
    """Giả lập bảng ĐÃ phân vùng trên MySQL, và ghi lại mọi lượt bỏ phân vùng."""
    years: dict[str, list[int]] = {}
    dropped: list[tuple[str, int]] = []

    monkeypatch.setattr(partition, "list_partition_years",
                        lambda db, table: list(years.get(table, [])))

    def _drop(db, table, year):
        dropped.append((table, int(year)))
        return True

    monkeypatch.setattr(partition, "drop_year_partition", _drop)
    return type("Partitions", (), {"years": years, "dropped": dropped})


def test_bo_nguyen_nam_da_nam_tron_ngoai_moc(db, packaged, partitions):
    partitions.years["tab_audit_log"] = [2024, 2025]
    _audit(db, datetime(2024, 6, 10))
    db.commit()
    packaged.add("audit:2024-06")

    result = retention.drop_expired_partitions(db, now=NOW)

    assert result["dropped"] == ["audit:2024"]
    assert result["skipped"] == []
    #  2025 bị mốc 16 tháng cắt ĐÔI (mốc rơi vào 01/05/2025) nên không được đụng —
    #  phần tháng còn lại của nó là việc của vòng xóa theo dòng.
    assert partitions.dropped == [("tab_audit_log", 2024)]


def test_thieu_goi_thi_khong_bo_phan_vung(db, packaged, partitions):
    partitions.years["tab_audit_log"] = [2024]
    _audit(db, datetime(2024, 6, 10))
    db.commit()

    result = retention.drop_expired_partitions(db, now=NOW)

    assert result["dropped"] == [] and result["skipped"] == ["audit:2024:thieu-goi"]
    assert partitions.dropped == []


def test_con_phien_chua_qua_han_thi_khong_bo_phan_vung(db, packaged, partitions):
    partitions.years["tab_login_session"] = [2024]
    _session(db, datetime(2024, 12, 28), expires_at=datetime(2026, 12, 31))
    db.commit()
    packaged.add("session:2024-12")

    result = retention.drop_expired_partitions(db, now=NOW)

    assert result["dropped"] == [] and result["skipped"] == ["session:2024:chua-qua-han"]
    assert partitions.dropped == []


def test_dry_run_khong_dung_toi_phan_vung(db, packaged, partitions):
    partitions.years["tab_audit_log"] = [2024]
    _audit(db, datetime(2024, 6, 10))
    db.commit()
    packaged.add("audit:2024-06")

    result = retention.drop_expired_partitions(db, now=NOW, dry_run=True)

    assert result["dropped"] == ["audit:2024"] and partitions.dropped == []


def test_nam_rong_hoan_toan_van_bo_duoc(db, packaged, partitions):
    """Không dòng nào thì không gói nào — và cũng không có gì để mất."""
    partitions.years["tab_change_log"] = [2023]

    result = retention.drop_expired_partitions(db, now=NOW)

    assert result["dropped"] == ["change:2023"]


# ---------------------------------------------------------------------------
# Nối vào việc dọn hằng đêm
# ---------------------------------------------------------------------------
def test_don_hang_dem_tra_them_hai_khoa_moi(db, packaged, partitions, monkeypatch):
    """Khóa cũ phải giữ nguyên — bài kiểm của đợt 1 đọc `deleted`/`matched`/`skipped`."""
    partitions.years["tab_audit_log"] = [2024]
    _audit(db, datetime(2024, 6, 10))
    db.commit()
    packaged.add("audit:2024-06")

    result = retention.cleanup_expired(db, now=NOW)

    assert result["dropped_partitions"] == ["audit:2024"]
    assert result["added_partitions"] == {}  # SQLite: không dựng phân vùng nào
    assert set(result) >= {"status", "cutoff", "deleted", "matched", "skipped"}
    assert result["status"] == "success"


def test_ly_do_bo_qua_moi_khong_bi_hieu_thanh_het_lo(db, packaged, partitions):
    """Cờ `capped` nhận diện bằng đuôi `:het-lo`; lý do mới phải dùng đuôi khác."""
    partitions.years["tab_audit_log"] = [2024]
    _audit(db, datetime(2024, 6, 10))
    db.commit()

    result = retention.cleanup_expired(db, now=NOW)

    assert "audit:2024:thieu-goi" in result["skipped"]
    assert result["status"] == "success"  # không phải "partial"
