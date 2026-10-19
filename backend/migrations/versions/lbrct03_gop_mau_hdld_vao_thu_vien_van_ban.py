"""Gop bang mau HDLD vao tab_document_template (single-table inheritance) -- duoc-CR-629b buoc B

Revision ID: lbrct03
Revises: mcpmerge01

VIET TAY (autogenerate repo nay troi ~650 dong). KHONG import ma ung dung: hang 1/2 chep tay.
Ke hoach: plans/261019-0935-hdld-sinh-van-ban-luu-tru-cr629/phase-07-*.md

upgrade
  1. DDL: them 6 cot (template_kind, company_id, contract_type, file_id, original_filename,
     placeholders); bo unique cu `uq_document_template_type_name`; tao unique moi
     `uq_document_template_kind_scope_name` + index `ix_document_template_lct_pick`.
  2. DML (1 giao dich, chi khi bang cu con va chua co dong kind=2): GIU NGUYEN id mau HDLD
     (`tab_labor_contract.template_id` khong doi); neu id trung thi DOI id mau van ban thuong
     (id += M) va dong thoi doi `tab_audit_log.entity_id` (entity `document_template`) +
     `tab_change_log.row_id` (table_name `tab_document_template`). M >= moi id, >= AUTO_INCREMENT-1 cua
     bang gop, >= max entity_id / row_id lich su => id lich su cua mau da XOA cung khong dung id tuong lai.
     Lich su thay doi cua mau HDLD ghi duoi ten bang CU `tab_labor_contract_template`
     (`LaborContractTemplate.__change_log_table__`) nen khong phai di chuyen.
     `doc_type_id` cua dong kind=2 = id loai van ban `HDLD` neu da co luc migrate, khong thi 0
     (seed `seed_document_phase1` dien bu cac dong 0 -- chi dien o 0, insert-only).
     Kiem so dong + so HD mo coi, lech => RuntimeError (DML rollback).
  2b. AUTO_INCREMENT bang gop = max(AI bang cu, AI bang gop (+M), MAX(id)+1) -- id mau HDLD da xoa
     khong bi cap lai. Buoc nay chay lai moi lan upgrade khi bang cu con (idempotent, chi tang).
  2c. Truoc khi doi ten: moi id bang cu phai co dong kind=2 o bang gop, khong thi RuntimeError.
  3. Doi ten `tab_labor_contract_template` -> `tab_labor_contract_template_bak629`
     (xoa o `lbrct04` cua lan phat hanh SAU).
downgrade (nguon su that = bang GOP): do kind=2 ve bang bak (KE CA khi khong con dong nao -- mau HDLD
  da xoa het) -> doi ten lai -> xoa dong kind=2 khoi bang gop -> bo cot.
  id mau van ban da doi (va lich su da dich theo) GIU NGUYEN, khong dich nguoc. Moi buoc tu gac (inspect) nen chay lai sau su co (MySQL DDL tu commit) la an toan.
Rollback: `alembic downgrade mcpmerge01`.
"""
from typing import Sequence, Union

import logging

import sqlalchemy as sa
from alembic import op

log = logging.getLogger("alembic.runtime.migration")

revision: str = "lbrct03"
down_revision: Union[str, None] = "mcpmerge01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DOC = "tab_document_template"
OLD = "tab_labor_contract_template"
BAK = "tab_labor_contract_template_bak629"
CONTRACT = "tab_labor_contract"
AUDIT = "tab_audit_log"
CHANGE_LOG = "tab_change_log"
UQ_OLD = "uq_document_template_type_name"
UQ_NEW = "uq_document_template_kind_scope_name"
IX_PICK = "ix_document_template_lct_pick"
DOC_TYPE = "tab_doc_type"
HDLD_TYPE_CODE = "HDLD"      # = document.type_metadata.LABOR_CONTRACT_DOC_TYPE (chep tay)
KIND_HTML, KIND_LCT = 1, 2   # DocumentTemplateKind (chep tay)

_NEW_COLS = (
    ("template_kind", lambda: sa.Column("template_kind", sa.SmallInteger(), nullable=False, server_default="1")),
    ("company_id", lambda: sa.Column("company_id", sa.BigInteger(), nullable=False, server_default="0")),
    ("contract_type", lambda: sa.Column("contract_type", sa.SmallInteger(), nullable=False, server_default="0")),
    ("file_id", lambda: sa.Column("file_id", sa.BigInteger(), nullable=False, server_default="0")),
    ("original_filename", lambda: sa.Column("original_filename", sa.String(255), nullable=False, server_default="")),
    ("placeholders", lambda: sa.Column("placeholders", sa.JSON(), nullable=True)),
)
# Cot chung cua hai bang (khong ke id): dung cho INSERT..SELECT hai chieu.
_AUDIT = "created_at, created_by, updated_at, updated_by"


def _insp():
    return sa.inspect(op.get_bind())


def _cols(table: str) -> set[str]:
    return {c["name"] for c in _insp().get_columns(table)}


def _uniques(table: str) -> set[str]:
    return {u["name"] for u in _insp().get_unique_constraints(table)}


def _indexes(table: str) -> set[str]:
    return {i["name"] for i in _insp().get_indexes(table)}


def _tables() -> set[str]:
    return set(_insp().get_table_names())


def _scalar(sql: str, **params):
    return op.get_bind().execute(sa.text(sql), params).scalar()


def upgrade() -> None:
    # ---- 1. DDL cot ----
    have = _cols(DOC)
    missing = [mk for name, mk in _NEW_COLS if name not in have]
    if missing:
        with op.batch_alter_table(DOC) as batch:
            for mk in missing:
                batch.add_column(mk())
    # ---- 2. DDL rang buoc ----
    if UQ_OLD in _uniques(DOC) or UQ_OLD in _indexes(DOC):
        with op.batch_alter_table(DOC) as batch:
            batch.drop_constraint(UQ_OLD, type_="unique")
    if UQ_NEW not in _uniques(DOC) and UQ_NEW not in _indexes(DOC):
        with op.batch_alter_table(DOC) as batch:
            batch.create_unique_constraint(UQ_NEW, ["template_kind", "doc_type_id", "company_id", "name"])
    if IX_PICK not in _indexes(DOC):
        op.create_index(IX_PICK, DOC, ["template_kind", "company_id", "contract_type", "is_active"])

    # ---- 3. DML: chep mau HDLD vao bang gop ----
    if OLD in _tables():
        floor = 0
        if not _scalar(f"SELECT COUNT(*) FROM {DOC} WHERE template_kind = {KIND_LCT}"):
            n = _scalar(f"SELECT COUNT(*) FROM {OLD}") or 0
            if n:
                floor = _copy_into_merged(n)
        # 3b. Moi id bang cu phai da nam o bang gop (chan mat im lang neu buoc chep bi bo qua khi chay lai).
        lost = _scalar(f"SELECT COUNT(*) FROM {OLD} WHERE id NOT IN "
                       f"(SELECT id FROM {DOC} WHERE template_kind = {KIND_LCT})") or 0
        if lost:
            raise RuntimeError(f"lbrct03: {lost} mau HDLD o bang cu chua co o bang gop -- khong doi ten")
        # 3c. AUTO_INCREMENT (MySQL: ALTER = DDL tu commit nen dat SAU moi buoc kiem DML).
        _bump_auto_increment(floor)

    # ---- 4. Doi ten bang cu ----
    tables = _tables()
    if OLD in tables and BAK not in tables:
        op.rename_table(OLD, BAK)


def _is_mysql() -> bool:
    return op.get_bind().dialect.name == "mysql"


def _auto_increment(table: str) -> int:
    """AUTO_INCREMENT hien tai (MySQL; bo dem thong ke cache nen tat expiry de doc so that). SQLite: 0."""
    if not _is_mysql():
        return 0
    op.get_bind().execute(sa.text("SET SESSION information_schema_stats_expiry = 0"))
    return int(_scalar("SELECT AUTO_INCREMENT FROM information_schema.TABLES "
                       "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t", t=table) or 0)


def _bump_auto_increment(extra_floor: int = 0) -> None:
    """Nang AUTO_INCREMENT bang gop len >= max(bo dem bang cu, bo dem bang gop, MAX(id)+1, extra_floor).
    Chi tang, chay lai an toan. Khong lam gi tren SQLite (tu dong MAX(rowid)+1)."""
    if not _is_mysql():
        return
    target = max(_auto_increment(OLD), _auto_increment(DOC), extra_floor,
                 (_scalar(f"SELECT COALESCE(MAX(id), 0) FROM {DOC}") or 0) + 1)
    if target > _auto_increment(DOC):
        op.execute(f"ALTER TABLE {DOC} AUTO_INCREMENT = {int(target)}")
    log.info("lbrct03: AUTO_INCREMENT %s = %s", DOC, target)


def _orphans() -> int:
    """HD tro mau (template_id>0) ma khong co mau kind=2 tuong ung (HD xoa mem co the tro mau da xoa)."""
    return _scalar(
        f"SELECT COUNT(*) FROM {CONTRACT} WHERE template_id > 0 AND template_id NOT IN "
        f"(SELECT id FROM {DOC} WHERE template_kind = {KIND_LCT})") or 0


def _copy_into_merged(n: int) -> int:
    """Chep mau HDLD vao bang gop; tra ve SAN AUTO_INCREMENT can dat (0 = khong yeu cau them)."""
    conn = op.get_bind()
    max_lct = _scalar(f"SELECT COALESCE(MAX(id), 0) FROM {OLD}")
    max_doc = _scalar(f"SELECT COALESCE(MAX(id), 0) FROM {DOC}")
    orphan_before = _scalar(
        f"SELECT COUNT(*) FROM {CONTRACT} WHERE template_id > 0 AND template_id NOT IN (SELECT id FROM {OLD})") or 0
    clash = _scalar(f"SELECT COUNT(*) FROM {DOC} d WHERE d.id IN (SELECT id FROM {OLD})") or 0
    floor = 0
    if clash:
        # M >= moi id hien co (ca hai bang), >= AUTO_INCREMENT-1 cua bang gop, >= max id lich su cua mau van ban
        # => moi id moi > M khong dung id nao, ke ca id lich su cua mau da XOA.
        has_audit, has_change = AUDIT in _tables(), CHANGE_LOG in _tables()
        audit_max = _scalar(f"SELECT COALESCE(MAX(entity_id), 0) FROM {AUDIT} WHERE entity = 'document_template'") \
            if has_audit else 0
        change_max = _scalar(f"SELECT COALESCE(MAX(row_id), 0) FROM {CHANGE_LOG} WHERE table_name = '{DOC}'") \
            if has_change else 0
        doc_ai = _auto_increment(DOC)
        shift = max(max_lct, max_doc, doc_ai - 1, audit_max or 0, change_max or 0)
        log.info("lbrct03: id trung => dich id mau van ban them M=%s (max_lct=%s max_doc=%s ai=%s audit=%s change=%s)",
                 shift, max_lct, max_doc, doc_ai, audit_max, change_max)
        print(f"lbrct03: id shift M={shift}  (rollback bang dump: xem phase-08 runbook)")
        conn.execute(sa.text(f"UPDATE {DOC} SET id = id + :m WHERE template_kind = {KIND_HTML}"), {"m": shift})
        # Lich su thao tac / thay doi cua mau van ban tro id cu => dich theo (ca dong cua mau da xoa, nhat quan).
        if has_audit:
            conn.execute(sa.text(f"UPDATE {AUDIT} SET entity_id = entity_id + :m WHERE entity = 'document_template'"),
                         {"m": shift})
        if has_change:
            conn.execute(sa.text(f"UPDATE {CHANGE_LOG} SET row_id = row_id + :m WHERE table_name = '{DOC}'"),
                         {"m": shift})
        # Bo dem phai vuot moi id lich su da dich (id mau da xoa cu < AI cu => cu + M < AI cu + M).
        floor = max(doc_ai + shift, (audit_max or 0) + shift + 1, (change_max or 0) + shift + 1)
    hdld_type = 0
    if DOC_TYPE in _tables():
        hdld_type = _scalar(f"SELECT MIN(id) FROM {DOC_TYPE} WHERE UPPER(code) = :c", c=HDLD_TYPE_CODE) or 0
    conn.execute(sa.text(
        f"INSERT INTO {DOC} (id, template_kind, doc_type_id, name, description, content_html, is_active, "
        f"company_id, contract_type, file_id, original_filename, placeholders, {_AUDIT}) "
        f"SELECT id, {KIND_LCT}, :t, name, note, '', is_active, company_id, contract_type, file_id, "
        f"original_filename, placeholders, {_AUDIT} FROM {OLD}"), {"t": hdld_type})
    got = _scalar(f"SELECT COUNT(*) FROM {DOC} WHERE template_kind = {KIND_LCT}")
    orphan_after = _orphans()
    if got != n or orphan_after != orphan_before:
        raise RuntimeError(
            f"lbrct03: lech du lieu (mau {got}/{n}, mo coi {orphan_after}/{orphan_before}) -- huy migration")
    return floor


def downgrade() -> None:
    if DOC in _tables() and "template_kind" in _cols(DOC):
        tables = _tables()
        kind2 = _scalar(f"SELECT COUNT(*) FROM {DOC} WHERE template_kind = {KIND_LCT}") or 0
        if BAK in tables:
            # Nguon su that = bang gop: ghi de bak KE CA khi khong con dong kind=2 (mau HDLD da xoa het sau khi len).
            _dump_back_to_bak()
        elif kind2 and OLD not in tables:
            # Khong co cho do ve => dung, tranh am tham vut mau HDLD khi bo cot.
            raise RuntimeError(f"lbrct03 downgrade: thieu bang {BAK} de nhan mau HDLD -- khoi phuc tu dump")
        tables = _tables()
        if BAK in tables and OLD not in tables:
            op.rename_table(BAK, OLD)
        # Bo dem bang cu >= bo dem bang gop: id mau HDLD da xoa khong bi cap lai (chi MySQL).
        if _is_mysql() and OLD in _tables():
            floor = max(_auto_increment(OLD), _auto_increment(DOC))
            if floor > _auto_increment(OLD):
                op.execute(f"ALTER TABLE {OLD} AUTO_INCREMENT = {int(floor)}")
        # Chi XOA dong kind=2 SAU khi bang cu da co du id (chay lai sau su co van an toan).
        if OLD in _tables() and kind2:
            missing = _scalar(f"SELECT COUNT(*) FROM {DOC} WHERE template_kind = {KIND_LCT} "
                              f"AND id NOT IN (SELECT id FROM {OLD})") or 0
            if missing:
                raise RuntimeError(f"lbrct03 downgrade: {missing} mau HDLD chua co o bang cu -- khong xoa")
            op.get_bind().execute(sa.text(f"DELETE FROM {DOC} WHERE template_kind = {KIND_LCT}"))

    # DDL nguoc
    if "template_kind" in _cols(DOC):
        if IX_PICK in _indexes(DOC):
            op.drop_index(IX_PICK, table_name=DOC)
        if UQ_NEW in _uniques(DOC) or UQ_NEW in _indexes(DOC):
            with op.batch_alter_table(DOC) as batch:
                batch.drop_constraint(UQ_NEW, type_="unique")
        have = _cols(DOC)
        drop = [name for name, _ in _NEW_COLS if name in have]
        if drop:
            with op.batch_alter_table(DOC) as batch:
                for name in drop:
                    batch.drop_column(name)
    if UQ_OLD not in _uniques(DOC) and UQ_OLD not in _indexes(DOC):
        with op.batch_alter_table(DOC) as batch:
            batch.create_unique_constraint(UQ_OLD, ["doc_type_id", "name"])


def _dump_back_to_bak() -> None:
    conn = op.get_bind()
    n = _scalar(f"SELECT COUNT(*) FROM {DOC} WHERE template_kind = {KIND_LCT}")
    conn.execute(sa.text(f"DELETE FROM {BAK}"))
    conn.execute(sa.text(
        f"INSERT INTO {BAK} (id, company_id, contract_type, name, note, file_id, original_filename, "
        f"placeholders, is_active, {_AUDIT}) "
        f"SELECT id, company_id, contract_type, name, SUBSTR(description, 1, 500), file_id, original_filename, "
        f"placeholders, is_active, {_AUDIT} FROM {DOC} WHERE template_kind = {KIND_LCT}"))
    if _scalar(f"SELECT COUNT(*) FROM {BAK}") != n:
        raise RuntimeError("lbrct03 downgrade: so dong do ve bang cu lech -- huy")
