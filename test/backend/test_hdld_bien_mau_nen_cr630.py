"""duoc-CR-630 phase 01 — nền: mã số, luật thuần, seed insert-only, registry, đếm giá trị HĐ, migration."""
import inspect
from datetime import date
from pathlib import Path

import pytest
import app as app_pkg
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.dialects import mysql

from app.core.labor_contract_codes import (LABOR_CONTRACT_VARIABLE_SOURCE_SET, LABOR_CONTRACT_VARIABLE_TYPE_SET,
                                           LaborContractVariableSource as Src, LaborContractVariableType as T)
from app.modules.labor_contract import variable_registry as reg, variable_rules as rules
from app.modules.labor_contract.model import LaborContract
from app.modules.labor_contract.placeholder_catalog import KNOWN_KEYS, PLACEHOLDERS
from app.modules.labor_contract.template_model import LaborContractTemplate
from app.modules.labor_contract.variable_model import LaborContractVariable
from app.modules.labor_contract.variable_seed import ensure_system_variables


_APP_DIR = Path(app_pkg.__file__).resolve().parent   # `backend/app` (host) hoặc `/app/app` (container)


def _custom(db, code, vtype=T.TEXT, **kw):
    row = LaborContractVariable(code=code, source=int(Src.CUSTOM), value_type=int(vtype),
                                label=kw.pop("label", code), **kw)
    db.add(row)
    db.flush()
    return row


def _contract(db, values, deleted=False):
    n = db.query(LaborContract).count() + 1
    row = LaborContract(code=f"HDLD{n:03d}", employee_id=1, company_id=1, contract_type=2,
                        start_date=date(2026, 1, 1), custom_values=values, is_deleted=deleted)
    db.add(row)
    db.flush()
    return row


# ── Bộ mã ───────────────────────────────────────────────────────────────────────────
def test_bo_ma_nguon_va_kieu_da_dang_ky():
    assert [c.value for c in LABOR_CONTRACT_VARIABLE_SOURCE_SET.codes] == ["1", "2"]
    assert [c.value for c in LABOR_CONTRACT_VARIABLE_TYPE_SET.codes] == ["1", "2", "3", "4", "5"]


# ── check_code ──────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("code", ["so_ngay_phep", "ab", "muc_thuong2", "a" + "b" * 39])
def test_ma_hop_le(code):
    assert rules.check_code(code) == code


@pytest.mark.parametrize("code", [
    "", "a", "a" * 41, "Ho_Ten", "số_ngày", "1abc", "a__b", "abc_", "luong_bang_chu", "range", "loop",
    "class", "true", "none", "ho_ten", "luong_co_ban", "ab cd", "ab-cd"])
def test_ma_khong_hop_le(code):
    with pytest.raises(ValueError):
        rules.check_code(code)


# ── normalize_value / format_value ──────────────────────────────────────────────────
def test_tien_chuan_hoa_va_bien():
    assert rules.normalize_value(T.MONEY, "15000000") == "15000000"
    assert rules.normalize_value(T.MONEY, 15) == "15"
    assert rules.normalize_value(T.MONEY, 10**12) == str(10**12)
    assert rules.normalize_value(T.MONEY, "") == "" and rules.normalize_value(T.MONEY, None) == ""
    for bad in ("-1", -5, 10**12 + 1, "1.000", "1,000", "abc", True, "1.5"):
        with pytest.raises(ValueError):
            rules.normalize_value(T.MONEY, bad)
    assert rules.format_value(T.MONEY, "15000000") == "15.000.000"


def test_so_chap_nhan_phay_hoac_cham_toi_da_hai_so_le():
    assert rules.normalize_value(T.NUMBER, "1,5") == "1.5"
    assert rules.normalize_value(T.NUMBER, "1.50") == "1.5"
    assert rules.normalize_value(T.NUMBER, "007") == "7"
    assert rules.normalize_value(T.NUMBER, "0") == "0"
    for bad in ("1.234", "-1", "1,2,3", "1.234,5", "abc", "1e3"):
        with pytest.raises(ValueError):
            rules.normalize_value(T.NUMBER, bad)
    assert rules.format_value(T.NUMBER, "1.5") == "1,5"
    assert rules.format_value(T.NUMBER, "1234567.25") == "1.234.567,25"
    assert rules.format_value(T.NUMBER, "1000") == "1.000"


def test_ngay_iso_trong_dai_nam():
    assert rules.normalize_value(T.DATE, "2026-10-01") == "2026-10-01"
    for bad in ("0001-01-01", "2101-01-01", "31/12/2026", "2026-02-30", "2026-1-1", "abc"):
        with pytest.raises(ValueError):
            rules.normalize_value(T.DATE, bad)
    assert rules.format_value(T.DATE, "2026-10-01") == "01/10/2026"


def test_chu_va_chu_nhieu_dong():
    assert rules.normalize_value(T.TEXT, "  a\r\nb  ") == "a b"
    assert rules.normalize_value(T.TEXT, "x" * 255) == "x" * 255
    with pytest.raises(ValueError):
        rules.normalize_value(T.TEXT, "x" * 256)
    assert rules.normalize_value(T.MULTILINE, " a\r\nb\rc ") == "a\nb\nc"
    with pytest.raises(ValueError):
        rules.normalize_value(T.MULTILINE, "x" * 2001)
    with pytest.raises(ValueError):
        rules.normalize_value(99, "x")


def test_chu_bo_ky_tu_dieu_khien_giu_tab_va_xuong_dong():
    assert rules.normalize_value(T.TEXT, "a\x00b\x07c\x1fd\x7fe") == "abcde"
    assert rules.normalize_value(T.TEXT, "a\tb") == "a\tb"
    assert rules.normalize_value(T.MULTILINE, "x\x0by\nz\x1b") == "xy\nz"


def test_khong_la_gia_tri_that_con_rong_la_khong_co():
    assert rules.normalize_value(T.MONEY, 0) == "0" and rules.normalize_value(T.MONEY, "0") == "0"
    assert rules.normalize_value(T.NUMBER, "0") == "0" and rules.normalize_value(T.NUMBER, "0,00") == "0"
    assert rules.normalize_value(T.MONEY, "") == "" and rules.normalize_value(T.NUMBER, None) == ""
    assert rules.format_value(T.MONEY, "0") == "0" and rules.format_value(T.NUMBER, "0") == "0"


def test_loi_khong_chep_lai_gia_tri_nhap():
    for vtype, secret in ((T.MONEY, "gia-tri-bi-mat"), (T.NUMBER, "gia-tri-bi-mat"), (T.DATE, "gia-tri-bi-mat")):
        with pytest.raises(ValueError) as exc:
            rules.normalize_value(vtype, secret)
        assert secret not in str(exc.value)


# ── Seed insert-only ────────────────────────────────────────────────────────────────
def test_seed_chen_du_roi_chay_lai_khong_ghi_de(db):
    assert ensure_system_variables(db) == len(PLACEHOLDERS)
    row = db.query(LaborContractVariable).filter_by(code="ho_ten").one()
    assert row.source == int(Src.SYSTEM)
    row.label, row.is_hidden = "Tên người lao động", True
    db.flush()
    assert ensure_system_variables(db) == 0
    row = db.query(LaborContractVariable).filter_by(code="ho_ten").one()
    assert (row.label, row.is_hidden) == ("Tên người lao động", True)       # D-018


def test_seed_duoc_goi_o_ca_hai_ban_seed():
    root = _APP_DIR
    for name in ("seed.py", "seed_prod.py"):
        assert "ensure_system_variables(db)" in (root / name).read_text(encoding="utf-8"), name


# ── Registry ────────────────────────────────────────────────────────────────────────
def test_allowed_template_keys(db):
    _custom(db, "dang_dung")
    _custom(db, "tien_thuong", T.MONEY)
    _custom(db, "da_ngung", is_active=False)
    _custom(db, "tien_cu", T.MONEY, is_active=False)
    allowed, inactive = reg.allowed_template_keys(db)
    assert KNOWN_KEYS <= allowed
    assert {"dang_dung", "tien_thuong", "tien_thuong_bang_chu"} <= allowed
    assert "dang_dung_bang_chu" not in allowed                       # biến CHỮ không có bạn đồng hành
    assert not ({"da_ngung", "tien_cu", "tien_cu_bang_chu"} & allowed)
    assert {"da_ngung", "tien_cu", "tien_cu_bang_chu"} <= inactive
    allowed2, inactive2 = reg.allowed_template_keys(db, keep=["da_ngung"])
    assert "da_ngung" in allowed2 and "da_ngung" not in inactive2 and "tien_cu" in inactive2


def test_custom_context_dinh_dang_va_bang_chu(db):
    rows = [_custom(db, "so_ngay", T.NUMBER), _custom(db, "ngay_hl", T.DATE), _custom(db, "thuong", T.MONEY),
            _custom(db, "trong", T.TEXT, default_value="mac-dinh")]
    ctx = reg.custom_context(rows, {"so_ngay": "1234.5", "ngay_hl": "2026-10-01", "thuong": "15000000"})
    assert ctx["so_ngay"] == "1.234,5" and ctx["ngay_hl"] == "01/10/2026"
    assert ctx["thuong"] == "15.000.000" and ctx["thuong_bang_chu"] == "Mười lăm triệu đồng chẵn"
    assert ctx["trong"] == ""                                         # mặc định đã SAO lúc lập, không áp ở đây
    empty = reg.custom_context(rows, None)
    assert empty["thuong"] == "" and empty["thuong_bang_chu"] == ""


def test_missing_required(db):
    rows = [_custom(db, "a1", is_required=True, label="Một"), _custom(db, "b1", T.MONEY, is_required=True, label="Hai"),
            _custom(db, "c1", is_required=True, is_active=False, label="Ba"), _custom(db, "d1", label="Bốn")]
    assert reg.missing_required(rows, {}, None) == ["Một", "Hai"]
    assert reg.missing_required(rows, {"a1": "x"}, None) == ["Hai"]
    assert reg.missing_required(rows, {}, ["a1"]) == ["Một"]
    assert reg.missing_required(rows, {}, ["b1_bang_chu"]) == ["Hai"]
    assert reg.missing_required(rows, {}, ["ho_ten"]) == []


def test_template_usage_quet_ma_va_bang_chu(db):
    db.add_all([LaborContractTemplate(company_id=1, contract_type=2, name="M1", placeholders=["thuong", "ho_ten"]),
                LaborContractTemplate(company_id=2, contract_type=2, name="M2", placeholders=["thuong_bang_chu"]),
                LaborContractTemplate(company_id=2, contract_type=2, name="M3", placeholders=None)])
    db.flush()
    assert [n for _, n, _ in reg.template_usage(db, "thuong")] == ["M1", "M2"]
    assert reg.template_usage(db, "khac") == []


def test_contract_value_count_sqlite_va_mysql(db):
    assert reg.contract_value_count(db, "thuong") == 0
    _contract(db, None)
    _contract(db, {})
    _contract(db, {"khac": "1"})
    assert reg.contract_value_count(db, "thuong") == 0
    _contract(db, {"thuong": "5"})
    _contract(db, {"thuong": "7"}, deleted=True)                     # xóa mềm vẫn đếm
    assert reg.contract_value_count(db, "thuong") == 2
    src = inspect.getsource(reg.contract_value_count)
    assert "custom_values[" not in src.split('"""')[2]
    from sqlalchemy import bindparam, func
    sql = str(func.json_extract(LaborContract.custom_values, bindparam("p", '$."x"')).isnot(None)
              .compile(dialect=mysql.dialect()))
    assert "JSON_EXTRACT(" in sql.upper() and "JSON_QUOTE" not in sql.upper()


# ── Schema & migration ──────────────────────────────────────────────────────────────
def test_schema_co_bang_va_cot(db):
    insp = sa_inspect(db.get_bind())
    assert "tab_labor_contract_variable" in insp.get_table_names()
    assert "custom_values" in {c["name"] for c in insp.get_columns("tab_labor_contract")}
    assert LaborContractVariable.code.type.length == 40


def test_chi_mot_head_alembic_va_lbvar01_noi_sau_lbrct02():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config()
    cfg.set_main_option("script_location", str(_APP_DIR.parent / "migrations"))
    script = ScriptDirectory.from_config(cfg)
    assert len(script.get_heads()) == 1, script.get_heads()
    assert script.get_revision("lbvar01").down_revision == "lbrct02"
