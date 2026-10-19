"""duoc-CR-629b bước B — migration `lbrct03`: gộp `tab_labor_contract_template` vào `tab_document_template`.

Engine SQLite RIÊNG (không đụng fixture `db`): dựng schema TRƯỚC migration bằng DDL chép từ
`b62f3c8d1a04` + `lbrct01`, rồi chạy `upgrade()/downgrade()` qua `MigrationContext` (khuôn
`test_hop_dong_b02.py`). Migration không import mã ứng dụng ⇒ test cũng nạp thẳng tệp.
"""
import importlib.util
import json
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

_TEN = "lbrct03_gop_mau_hdld_vao_thu_vien_van_ban.py"
_AUDIT_COLS = ("created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, created_by BIGINT NOT NULL DEFAULT 0, "
               "updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_by BIGINT NOT NULL DEFAULT 0")

DDL = [
    f"""CREATE TABLE tab_document_template (
        doc_type_id BIGINT NOT NULL, name VARCHAR(200) NOT NULL, description TEXT NOT NULL,
        content_html TEXT NOT NULL, is_active BOOLEAN NOT NULL DEFAULT 1,
        id INTEGER PRIMARY KEY AUTOINCREMENT, {_AUDIT_COLS},
        CONSTRAINT uq_document_template_type_name UNIQUE (doc_type_id, name))""",
    "CREATE INDEX ix_document_template_type_active ON tab_document_template (doc_type_id, is_active)",
    f"""CREATE TABLE tab_labor_contract_template (
        company_id BIGINT NOT NULL, contract_type SMALLINT NOT NULL, name VARCHAR(200) NOT NULL,
        note VARCHAR(500) NOT NULL DEFAULT '', file_id BIGINT NOT NULL DEFAULT 0,
        original_filename VARCHAR(255) NOT NULL DEFAULT '', placeholders JSON, is_active BOOLEAN NOT NULL DEFAULT 1,
        id INTEGER PRIMARY KEY AUTOINCREMENT, {_AUDIT_COLS},
        CONSTRAINT uq_labor_contract_template_company_name UNIQUE (company_id, name))""",
    "CREATE TABLE tab_labor_contract (id INTEGER PRIMARY KEY AUTOINCREMENT, code VARCHAR(25) NOT NULL, "
    "template_id BIGINT NOT NULL DEFAULT 0)",
    "CREATE TABLE tab_audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, entity VARCHAR(50) NOT NULL, "
    "entity_id BIGINT NOT NULL, action VARCHAR(30) NOT NULL DEFAULT '')",
    "CREATE TABLE tab_change_log (id INTEGER PRIMARY KEY AUTOINCREMENT, table_name VARCHAR(64) NOT NULL, "
    "row_id BIGINT NOT NULL DEFAULT 0)",
]


def _nap():
    path = Path(__file__).resolve().parents[2] / "backend" / "migrations" / "versions" / _TEN
    if not path.exists():   # trong container: /app/test/backend + /app/migrations
        path = Path("/app/migrations/versions") / _TEN
    spec = importlib.util.spec_from_file_location("mig_lbrct03", path)
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
            r = conn.execute(text(stmt), p)
            conn.commit()
            return r

        def rows(self, stmt, **p):
            return [tuple(r) for r in conn.execute(text(stmt), p).fetchall()]

        insp = staticmethod(lambda: inspect(conn))
        module = mig

    yield Env()
    conn.close()


def _vb(env, id_, name, doc_type=7):
    env.sql("INSERT INTO tab_document_template (id, doc_type_id, name, description, content_html) "
            "VALUES (:i, :t, :n, 'mô tả', '<p>nội dung</p>')", i=id_, t=doc_type, n=name)


def _lct(env, id_, name, company=1, note="ghi chú", file_id=None, ph='["ho_ten","so_hop_dong"]'):
    env.sql("INSERT INTO tab_labor_contract_template (id, company_id, contract_type, name, note, file_id, "
            "original_filename, placeholders) VALUES (:i, :c, 2, :n, :note, :f, 'mau.docx', :ph)",
            i=id_, c=company, n=name, note=note, f=file_id or id_ * 100, ph=ph)


def _hd(env, template_id):
    env.sql("INSERT INTO tab_labor_contract (code, template_id) VALUES (:c, :t)", c=f"HD{template_id}", t=template_id)


def test_len_giu_nguyen_id_mau_hdld_va_doi_id_mau_van_ban_khi_trung(env):
    for i, n in ((1, "VB một"), (2, "VB hai")):
        _vb(env, i, n)
    for i, n in ((1, "HĐ một"), (2, "HĐ hai"), (3, "HĐ ba")):
        _lct(env, i, n)
        _hd(env, i)
    env.sql("INSERT INTO tab_audit_log (entity, entity_id) VALUES ('document_template', 2), "
            "('labor_contract_template', 2), ('employee', 2)")
    hd_truoc = env.rows("SELECT id, code, template_id FROM tab_labor_contract ORDER BY id")

    env.up()

    lct = env.rows("SELECT id, name, description, file_id, original_filename, placeholders, company_id, "
                   "contract_type, doc_type_id, content_html FROM tab_document_template "
                   "WHERE template_kind = 2 ORDER BY id")
    assert [r[0] for r in lct] == [1, 2, 3]
    assert lct[0][1:5] == ("HĐ một", "ghi chú", 100, "mau.docx")
    assert json.loads(lct[0][5]) == ["ho_ten", "so_hop_dong"]
    assert lct[0][6:] == (1, 2, 0, "")
    vb = env.rows("SELECT id, name, description, content_html, doc_type_id FROM tab_document_template "
                  "WHERE template_kind = 1 ORDER BY id")
    assert vb == [(4, "VB một", "mô tả", "<p>nội dung</p>", 7), (5, "VB hai", "mô tả", "<p>nội dung</p>", 7)]
    # Lịch sử thao tác mẫu văn bản dời theo; entity khác không đụng.
    assert env.rows("SELECT entity, entity_id FROM tab_audit_log ORDER BY id") == [
        ("document_template", 5), ("labor_contract_template", 2), ("employee", 2)]
    # Chứng từ pháp lý KHÔNG đổi một byte.
    assert env.rows("SELECT id, code, template_id FROM tab_labor_contract ORDER BY id") == hd_truoc
    tables = set(env.insp().get_table_names())
    assert "tab_labor_contract_template" not in tables and "tab_labor_contract_template_bak629" in tables
    assert env.rows("SELECT COUNT(*) FROM tab_labor_contract_template_bak629") == [(3,)]


def test_mau_hdld_nhan_doc_type_id_cua_loai_hdld_neu_loai_da_co(env):
    env.sql("CREATE TABLE tab_doc_type (id INTEGER PRIMARY KEY, code VARCHAR(20) NOT NULL)")
    env.sql("INSERT INTO tab_doc_type (id, code) VALUES (3, 'QD'), (9, 'hdld')")
    _lct(env, 1, "HĐ một")
    env.up()
    assert env.rows("SELECT doc_type_id FROM tab_document_template WHERE template_kind = 2") == [(9,)]


def test_mau_hdld_doc_type_id_bang_0_khi_chua_co_loai_hdld(env):
    _lct(env, 1, "HĐ một")
    env.up()
    assert env.rows("SELECT doc_type_id FROM tab_document_template WHERE template_kind = 2") == [(0,)]


def test_khong_trung_id_thi_khong_doi_id_mau_van_ban(env):
    _vb(env, 10, "VB mười")
    _lct(env, 1, "HĐ một")
    env.sql("INSERT INTO tab_audit_log (entity, entity_id) VALUES ('document_template', 10)")
    env.up()
    assert env.rows("SELECT id FROM tab_document_template WHERE template_kind = 1") == [(10,)]
    assert env.rows("SELECT id FROM tab_document_template WHERE template_kind = 2") == [(1,)]
    assert env.rows("SELECT entity_id FROM tab_audit_log") == [(10,)]


def test_bang_hdld_rong_chi_doi_schema_va_ten_bang(env):
    _vb(env, 1, "VB một")
    env.up()
    cols = {c["name"] for c in env.insp().get_columns("tab_document_template")}
    assert {"template_kind", "company_id", "contract_type", "file_id", "original_filename", "placeholders"} <= cols
    assert env.rows("SELECT id, template_kind FROM tab_document_template") == [(1, 1)]
    assert "tab_labor_contract_template_bak629" in set(env.insp().get_table_names())


def test_chay_len_hai_lan_khong_nhan_doi(env):
    _vb(env, 1, "VB một")
    _lct(env, 1, "HĐ một")
    env.up()
    truoc = env.rows("SELECT id, template_kind, name FROM tab_document_template ORDER BY id")
    env.up()   # mô phỏng chạy lại sau sự cố
    assert env.rows("SELECT id, template_kind, name FROM tab_document_template ORDER BY id") == truoc


def test_chay_lai_khi_bang_cu_chua_doi_ten_sau_su_co_khong_nhan_doi(env):
    """Sự cố giữa DML và rename: bảng cũ còn + đã có dòng kind=2 ⇒ bỏ qua DML, chỉ đổi tên."""
    _lct(env, 1, "HĐ một")
    env.up()
    env.sql("ALTER TABLE tab_labor_contract_template_bak629 RENAME TO tab_labor_contract_template")
    env.up()
    assert env.rows("SELECT COUNT(*) FROM tab_document_template WHERE template_kind = 2") == [(1,)]
    assert "tab_labor_contract_template_bak629" in set(env.insp().get_table_names())


def test_xuong_dong_bo_sua_doi_va_mau_tao_sau_khi_len(env):
    _vb(env, 1, "VB một")
    _lct(env, 1, "HĐ một")
    _lct(env, 2, "HĐ hai", company=2)
    env.up()
    env.sql("UPDATE tab_document_template SET name = 'HĐ một ĐÃ SỬA' WHERE id = 1 AND template_kind = 2")
    env.sql("INSERT INTO tab_document_template (id, template_kind, doc_type_id, name, description, content_html, "
            "company_id, contract_type, file_id, original_filename, placeholders) "
            "VALUES (50, 2, 0, 'HĐ mới', 'mới', '', 1, 3, 777, 'moi.docx', '[]')")
    env.down()

    assert env.rows("SELECT id, company_id, contract_type, name, note, file_id FROM tab_labor_contract_template "
                    "ORDER BY id") == [(1, 1, 2, "HĐ một ĐÃ SỬA", "ghi chú", 100), (2, 2, 2, "HĐ hai", "ghi chú", 200),
                                       (50, 1, 3, "HĐ mới", "mới", 777)]
    # Bảng văn bản: không còn kind=2, mất 6 cột, có lại unique cũ; id mẫu văn bản đã dời GIỮ NGUYÊN.
    insp = env.insp()
    cols = {c["name"] for c in insp.get_columns("tab_document_template")}
    assert not ({"template_kind", "company_id", "contract_type", "file_id", "original_filename",
                 "placeholders"} & cols)
    assert "uq_document_template_type_name" in {u["name"] for u in insp.get_unique_constraints("tab_document_template")}
    assert env.rows("SELECT id, name FROM tab_document_template") == [(3, "VB một")]
    assert "tab_labor_contract_template_bak629" not in set(insp.get_table_names())


def test_xuoi_nguoc_xuoi_on_dinh(env):
    _vb(env, 1, "VB một")
    _lct(env, 1, "HĐ một")
    _lct(env, 2, "HĐ hai")
    env.up()
    lan1 = env.rows("SELECT id, template_kind, doc_type_id, name, description, company_id, file_id "
                    "FROM tab_document_template ORDER BY id")
    env.down()
    env.up()
    lan2 = env.rows("SELECT id, template_kind, doc_type_id, name, description, company_id, file_id "
                    "FROM tab_document_template ORDER BY id")
    # Lần 2 không còn trùng id ⇒ mẫu văn bản giữ id đã dời ở lần 1.
    assert lan1 == lan2


def test_xuong_khi_thieu_bang_bak_ma_con_mau_hdld_thi_dung_khong_mat_du_lieu(env):
    _lct(env, 1, "HĐ một")
    env.up()
    env.sql("DROP TABLE tab_labor_contract_template_bak629")
    with pytest.raises(RuntimeError, match="thieu bang"):
        env.down()
    assert env.rows("SELECT COUNT(*) FROM tab_document_template WHERE template_kind = 2") == [(1,)]


def test_lech_so_hop_dong_mo_coi_thi_huy_migration(env, monkeypatch):
    """Lưới kiểm: nếu sau khi chép số mẫu lệch bảng cũ ⇒ RuntimeError, DML hoàn tác."""
    _vb(env, 1, "VB một")
    _lct(env, 1, "HĐ một")
    _hd(env, 1)
    monkeypatch.setattr(env.module, "_orphans", lambda: 99)
    with pytest.raises(RuntimeError, match="lech du lieu"):
        env.up()


def test_schema_sau_migration_khop_model(env):
    from app.modules.document.template_model import TemplateRecord

    env.up()
    insp = env.insp()
    model = TemplateRecord.__table__
    assert {c["name"] for c in insp.get_columns("tab_document_template")} == {c.name for c in model.columns}
    uniques = {u["name"] for u in insp.get_unique_constraints("tab_document_template")}
    assert uniques == {"uq_document_template_kind_scope_name"}
    indexes = {i["name"] for i in insp.get_indexes("tab_document_template")}
    assert {"ix_document_template_type_active", "ix_document_template_lct_pick"} <= indexes
    assert {i.name for i in model.indexes} <= indexes


def test_chi_mot_head_alembic():
    root = Path(__file__).resolve().parents[2] / "backend"
    if not (root / "migrations").exists():
        root = Path("/app")
    from alembic.config import Config

    cfg = Config()
    cfg.set_main_option("script_location", str(root / "migrations"))
    heads = ScriptDirectory.from_config(cfg).get_heads()
    assert len(heads) == 1, heads


def test_dich_id_vuot_id_lich_su_cua_mau_van_ban_da_xoa_va_dich_ca_change_log(env):
    """Mẫu văn bản id 1 còn; id 50 đã xóa nhưng lịch sử còn. Trùng id với HĐLĐ id 1 ⇒ M >= 50 để id lịch sử
    đã dịch (51+) không đụng id mẫu nào về sau; change_log của mẫu HĐLĐ (tên bảng cũ) KHÔNG bị dịch."""
    _vb(env, 1, "VB một")
    _lct(env, 1, "HĐ một")
    env.sql("INSERT INTO tab_audit_log (entity, entity_id) VALUES ('document_template', 1), "
            "('document_template', 50), ('labor_contract_template', 1)")
    env.sql("INSERT INTO tab_change_log (table_name, row_id) VALUES ('tab_document_template', 1), "
            "('tab_document_template', 60), ('tab_labor_contract_template', 1)")
    env.up()
    assert env.rows("SELECT id FROM tab_document_template WHERE template_kind = 1") == [(61,)]
    assert env.rows("SELECT entity_id FROM tab_audit_log ORDER BY id") == [(61,), (110,), (1,)]
    assert env.rows("SELECT row_id FROM tab_change_log ORDER BY id") == [(61,), (120,), (1,)]


def test_xuong_khi_mau_hdld_da_xoa_het_sau_khi_len_thi_bang_cu_rong(env):
    _vb(env, 1, "VB một")
    _lct(env, 1, "HĐ một")
    _lct(env, 2, "HĐ hai")
    env.up()
    env.sql("DELETE FROM tab_document_template WHERE template_kind = 2")
    env.down()
    assert env.rows("SELECT COUNT(*) FROM tab_labor_contract_template") == [(0,)]
    assert "tab_labor_contract_template_bak629" not in set(env.insp().get_table_names())


def test_xuong_chay_lai_sau_su_co_giua_chung_khong_mat_mau(env):
    """Sự cố sau khi đổi tên bak -> bảng cũ nhưng trước khi xóa kind=2: chạy lại phải hoàn tất, không mất dòng."""
    _lct(env, 1, "HĐ một")
    env.up()
    env.sql("ALTER TABLE tab_labor_contract_template_bak629 RENAME TO tab_labor_contract_template")
    env.down()
    assert env.rows("SELECT id, name FROM tab_labor_contract_template") == [(1, "HĐ một")]
    assert "template_kind" not in {c["name"] for c in env.insp().get_columns("tab_document_template")}


def test_khong_doi_ten_khi_bang_cu_co_id_chua_nam_o_bang_gop(env):
    _lct(env, 1, "HĐ một")
    _lct(env, 2, "HĐ hai")
    env.up()
    env.sql("ALTER TABLE tab_labor_contract_template_bak629 RENAME TO tab_labor_contract_template")
    env.sql("DELETE FROM tab_document_template WHERE id = 2 AND template_kind = 2")
    with pytest.raises(RuntimeError, match="chua co o bang gop"):
        env.up()
    assert "tab_labor_contract_template" in set(env.insp().get_table_names())
