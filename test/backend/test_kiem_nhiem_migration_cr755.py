"""duoc-CR-755 — migration `kn755a`: chép dòng phụ của `tab_employee_department` sang `tab_employee_concurrent`.

Engine SQLite RIÊNG (không đụng fixture `db`): dựng schema TRƯỚC migration bằng DDL tối thiểu, rồi chạy
`upgrade()/downgrade()` qua `MigrationContext` (khuôn `test_hdld_gop_bang_mau_migration_cr629b.py`).
Migration không import mã ứng dụng nên test nạp thẳng tệp.
"""
import importlib.util
from datetime import date, timedelta
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

_TEN = "kn755a_bang_kiem_nhiem.py"
_AUDIT = ("created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, created_by BIGINT NOT NULL DEFAULT 0, "
          "updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_by BIGINT NOT NULL DEFAULT 0")
DDL = [
    "CREATE TABLE tab_employee (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id BIGINT, department_id BIGINT)",
    f"""CREATE TABLE tab_employee_department (
        id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id BIGINT NOT NULL, department_id BIGINT NOT NULL,
        is_primary BOOLEAN NOT NULL DEFAULT 0, {_AUDIT}, UNIQUE (employee_id, department_id))""",
]


def _nap():
    path = Path(__file__).resolve().parents[2] / "backend" / "migrations" / "versions" / _TEN
    if not path.exists():   # trong container: /app/test/backend + /app/migrations
        path = Path("/app/migrations/versions") / _TEN
    spec = importlib.util.spec_from_file_location("mig_kn755a", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def env():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    with engine.begin() as c:
        for stmt in DDL:
            c.execute(text(stmt))
    conn = engine.connect()
    ctx = MigrationContext.configure(conn)
    mig = _nap()

    class Env:
        def up(self):
            with Operations.context(ctx):
                mig.upgrade()
            conn.commit()

        def down(self):
            with Operations.context(ctx):
                mig.downgrade()
            conn.commit()

        def sql(self, stmt, **p):
            conn.execute(text(stmt), p)
            conn.commit()

        def rows(self, stmt, **p):
            return [tuple(r) for r in conn.execute(text(stmt), p).fetchall()]

        insp = staticmethod(lambda: inspect(conn))

    yield Env()
    conn.close()


def _emp(env, id_, company, dept):
    env.sql("INSERT INTO tab_employee (id, company_id, department_id) VALUES (:i, :c, :d)", i=id_, c=company, d=dept)


def _dep(env, emp, dept, primary):
    env.sql("INSERT INTO tab_employee_department (employee_id, department_id, is_primary) VALUES (:e, :d, :p)",
            e=emp, d=dept, p=1 if primary else 0)


def _seed(env):
    _emp(env, 1, 10, 100)
    _dep(env, 1, 100, True)
    _dep(env, 1, 101, False)
    _dep(env, 1, 102, False)
    _emp(env, 2, 20, 200)
    _dep(env, 2, 200, True)
    _dep(env, 2, 201, False)
    _dep(env, 3, 300, False)     # mồ côi: không có hồ sơ nhân sự


def test_upgrade_chep_dong_phu_sang_bang_moi_va_giu_dong_chinh(env):
    _seed(env)
    env.up()
    rows = env.rows("SELECT employee_id, company_id, department_id, counts_scope, note, from_date, to_date, "
                    "position_id, work_history_id FROM tab_employee_concurrent ORDER BY employee_id, department_id")
    note = "Chuyển từ kiêm nhiệm cũ"
    assert rows == [(1, 10, 101, 1, note, None, None, 0, 0), (1, 10, 102, 1, note, None, None, 0, 0),
                    (2, 20, 201, 1, note, None, None, 0, 0)]
    #  Bảng cũ chỉ còn dòng CHÍNH; dòng mồ côi cũng bị dọn nhưng không chép.
    assert env.rows("SELECT employee_id, department_id, is_primary FROM tab_employee_department "
                    "ORDER BY employee_id") == [(1, 100, 1), (2, 200, 1)]


def test_upgrade_chay_lai_khong_nhan_doi(env):
    _seed(env)
    env.up()
    env.up()                                     # bảng đã có, không còn dòng phụ → không làm gì
    assert env.rows("SELECT COUNT(*) FROM tab_employee_concurrent") == [(3,)]
    #  Dòng phụ xuất hiện lại (vd chạy lại sau khi đường ghi cũ còn sống): chỉ chép dòng CHƯA có.
    _dep(env, 1, 101, False)
    _dep(env, 2, 202, False)
    env.up()
    assert env.rows("SELECT COUNT(*) FROM tab_employee_concurrent") == [(4,)]


def test_upgrade_khong_chep_dong_phu_trung_phong_chinh(env):
    _emp(env, 1, 10, 100)
    _dep(env, 1, 100, True)
    env.sql("UPDATE tab_employee SET department_id = 101 WHERE id = 1")     # dữ liệu lệch: phụ == chính hiện tại
    _dep(env, 1, 101, False)
    env.up()
    assert env.rows("SELECT COUNT(*) FROM tab_employee_concurrent") == [(0,)]
    assert env.rows("SELECT COUNT(*) FROM tab_employee_department WHERE is_primary = 0") == [(0,)]


def test_upgrade_tao_bang_va_chi_muc(env):
    env.up()
    insp = env.insp()
    assert "tab_employee_concurrent" in insp.get_table_names()
    assert {i["name"] for i in insp.get_indexes("tab_employee_concurrent")} == {
        "ix_employee_concurrent_employee", "ix_employee_concurrent_dept_company",
        "ix_employee_concurrent_work_history"}


def test_downgrade_tra_lai_dong_hieu_luc_cung_cong_ty_chinh_va_bo_bang(env):
    _emp(env, 1, 10, 100)
    _dep(env, 1, 100, True)
    env.up()
    today = date.today()
    ins = ("INSERT INTO tab_employee_concurrent (employee_id, company_id, department_id, from_date, to_date) "
           "VALUES (1, :c, :d, :f, :t)")
    env.sql(ins, c=10, d=101, f=None, t=None)                                   # hiệu lực → trả lại
    env.sql(ins, c=10, d=102, f=str(today - timedelta(days=9)), t=str(today - timedelta(days=1)))  # hết hạn
    env.sql(ins, c=10, d=103, f=str(today + timedelta(days=9)), t=None)         # sắp tới
    env.sql(ins, c=99, d=104, f=None, t=None)                                   # khác công ty
    env.sql(ins, c=10, d=101, f=str(today - timedelta(days=500)), t=str(today - timedelta(days=400)))  # trùng phòng
    env.sql("INSERT INTO tab_employee_concurrent (employee_id, company_id, department_id, counts_scope) "
            "VALUES (1, 10, 105, 0)")                                           # hiệu lực nhưng TẮT công tắc
    env.down()
    assert env.rows("SELECT department_id, is_primary FROM tab_employee_department "
                    "WHERE employee_id = 1 ORDER BY department_id") == [(100, 1), (101, 0)], (
        "dòng tắt công tắc không được chép về: mô hình cũ coi mọi dòng phụ là mở phạm vi (hạ cấp = nới quyền)")
    assert "tab_employee_concurrent" not in env.insp().get_table_names()


def test_chu_trinh_len_xuong_len_giu_nguyen_du_lieu(env):
    _seed(env)
    env.up()
    env.down()
    assert env.rows("SELECT employee_id, department_id, is_primary FROM tab_employee_department "
                    "WHERE is_primary = 0 ORDER BY employee_id, department_id") == [(1, 101, 0), (1, 102, 0), (2, 201, 0)]
    env.up()
    assert env.rows("SELECT employee_id, department_id FROM tab_employee_concurrent "
                    "ORDER BY employee_id, department_id") == [(1, 101), (1, 102), (2, 201)]


def test_revision_noi_dung_sau_stix723():
    mod = _nap()
    assert (mod.revision, mod.down_revision) == ("kn755a", "stix723")
