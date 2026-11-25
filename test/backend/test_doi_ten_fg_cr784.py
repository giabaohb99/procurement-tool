"""duoc-CR-784 phase 06 (25/11/2026) — đổi định danh `hh_code / hh_name` -> `fg_code / fg_name` ở định mức bao bì.

Phủ: migration `fgname784` lên / xuống trên SQLite giữ dữ liệu + ràng buộc duy nhất, model khớp, và khóa JSON của API định mức
là `fg_*` (khóa cũ không còn).
"""
import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

from app.modules.packaging_cost.model import PackagingBom

MIGRATION = next((Path(__file__).resolve().parents[2] / "backend" / "migrations" / "versions").glob("fgname784_*.py"))


def _load_migration():
    spec = importlib.util.spec_from_file_location("fgname784", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OLD_SCHEMA = """
CREATE TABLE tab_packaging_bom (
  id INTEGER PRIMARY KEY AUTOINCREMENT, hh_code VARCHAR(50) NOT NULL, hh_name VARCHAR(255) NOT NULL DEFAULT '',
  legal_name VARCHAR(255) NOT NULL DEFAULT '', carton_qty INTEGER NOT NULL DEFAULT 0,
  CONSTRAINT uq_tab_packaging_bom_hh_code UNIQUE (hh_code))
"""


@pytest.fixture
def old_conn():
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(sa.text(OLD_SCHEMA))
        conn.execute(sa.text("INSERT INTO tab_packaging_bom (hh_code, hh_name, carton_qty) VALUES ('HH1', 'Sản phẩm 1', 12), ('HH2', '', 6)"))
    with engine.connect() as conn:
        yield conn
    engine.dispose()


def _run(conn, fn):
    with Operations.context(MigrationContext.configure(conn)):
        fn()
    conn.commit()


def _columns(conn) -> set[str]:
    return {c["name"] for c in sa.inspect(conn).get_columns("tab_packaging_bom")}


def test_migration_doi_ten_hai_cot_giu_du_lieu_va_rang_buoc_duy_nhat(old_conn):
    mig = _load_migration()
    assert (mig.revision, mig.down_revision) == ("fgname784", "cleanup784")
    _run(old_conn, mig.upgrade)
    assert _columns(old_conn) == {"id", "fg_code", "fg_name", "legal_name", "carton_qty"}
    assert old_conn.execute(sa.text("SELECT fg_code, fg_name, carton_qty FROM tab_packaging_bom ORDER BY id")).all() == [
        ("HH1", "Sản phẩm 1", 12), ("HH2", "", 6)]
    with pytest.raises(sa.exc.IntegrityError):                      # duy nhất theo cột mới vẫn giữ
        old_conn.execute(sa.text("INSERT INTO tab_packaging_bom (fg_code) VALUES ('HH1')"))
    old_conn.rollback()


def test_migration_downgrade_tra_ten_cu_dung_du_lieu(old_conn):
    mig = _load_migration()
    _run(old_conn, mig.upgrade)
    _run(old_conn, mig.downgrade)
    assert _columns(old_conn) == {"id", "hh_code", "hh_name", "legal_name", "carton_qty"}
    assert old_conn.execute(sa.text("SELECT hh_code, hh_name FROM tab_packaging_bom ORDER BY id")).all() == [
        ("HH1", "Sản phẩm 1"), ("HH2", "")]
    _run(old_conn, mig.upgrade)                                     # lên lại sau xuống vẫn sạch
    assert "fg_code" in _columns(old_conn)


def test_model_dung_ten_fg_va_khong_con_ten_hh():
    cols = {c.name for c in PackagingBom.__table__.columns}
    assert {"fg_code", "fg_name"} <= cols and not {"hh_code", "hh_name"} & cols
    assert PackagingBom.__table__.c.fg_code.unique
