"""duoc-CR-784 (25/11/2026) — định mức bao bì chuẩn hóa: đầu phiếu `tab_packaging_bom` + thành phần `tab_packaging_bom_part`.

Phủ: (1) migration sao dữ liệu hai chiều + chạy trọn upgrade / downgrade trên SQLite, (2) CRUD giữ bảng thành phần đồng bộ,
(3) tra ngược theo mã vật tư, (4) thêm loại thành phần mới KHÔNG đổi cấu trúc bảng, (5) lọc / xếp danh sách theo mã thành phần
ở máy chủ, (6) mã thành phần chỉ đọc không ghi nhầm.
"""
import importlib.util
from decimal import Decimal
from enum import IntEnum
from pathlib import Path
from types import SimpleNamespace

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.exc import IntegrityError

from app.core.packaging_price_codes import PackagingRole
from app.modules.packaging_cost import bom_parts_service as svc
from app.modules.packaging_cost import cost_service
from app.modules.packaging_cost.impact_service import compute_impact
from app.modules.packaging_cost.model import PackagingBom, PackagingBomPart, role_field
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401  (fixture)
from so_gia_factory_cr784 import add_ledger, add_products, bom_codes_of, build_bom

BOMS = "/api/packaging-boms"
D = Decimal
MIGRATION = next((Path(__file__).resolve().parents[2] / "backend" / "migrations" / "versions").glob("bompart784_*.py"))


def _load_migration():
    spec = importlib.util.spec_from_file_location("bompart784", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def catalog(db):
    add_products(db, ("CPT0105", "Chai 450ml", "Cái"), ("NAP0085", "Nắp", "Cái"), ("NHG0001", "Nhãn", "Cái"),
                 ("NDT0001", "Nhãn thùng", "Cái"), ("THU0001", "Thùng", "Cái"), ("NAP0099", "Nắp khác", "Cái"))


@pytest.fixture
def api(db, seed, cap_quyen, client_as, catalog):  # noqa: F811
    cap_quyen(seed.u_req_id, "packaging_cost", scope="all", read=True, create=True, write=True, delete=True)
    return client_as(db.get(User, seed.u_req_id))


def _bom(db, fg="HH0001", **over) -> PackagingBom:
    base = dict(fg_code=fg, fg_name=f"Sản phẩm {fg}", bottle_code="CPT0105", cap_code="NAP0085", carton_qty=40,
                created_by=1, updated_by=1)
    base.update(over)
    row = build_bom(**base)
    db.add(row)
    db.commit()
    return row


# ── 1. Migration ────────────────────────────────────────────────────────────────
OLD_SCHEMA = """
CREATE TABLE tab_packaging_bom (
  id INTEGER PRIMARY KEY AUTOINCREMENT, fg_code VARCHAR(50) NOT NULL UNIQUE, fg_name VARCHAR(255) NOT NULL DEFAULT '',
  legal_name VARCHAR(255) NOT NULL DEFAULT '', bottle_code VARCHAR(50) NOT NULL DEFAULT '', cap_code VARCHAR(50) NOT NULL DEFAULT '',
  label_code VARCHAR(50) NOT NULL DEFAULT '', carton_label_code VARCHAR(50) NOT NULL DEFAULT '',
  carton_code VARCHAR(50) NOT NULL DEFAULT '', carton_qty INTEGER NOT NULL DEFAULT 0)
"""
OLD_INDEXES = ("ix_pbom_bottle:bottle_code", "ix_pbom_cap:cap_code", "ix_pbom_label:label_code",
               "ix_pbom_carton_label:carton_label_code", "ix_pbom_carton:carton_code")
OLD_ROWS = [  # (fg, chai, nắp, nhãn, nhãn thùng, thùng)
    ("HH1", "C1", "N1", "L1", "NT1", "T1"),      # đủ năm
    ("HH2", "C2", "", "", "", ""),               # chỉ chai
    ("HH3", "C1", "N2", "", "NT1", ""),          # thiếu nhãn + thùng, dùng lại mã chai C1
]


@pytest.fixture
def old_conn():
    """SQLite với bảng định mức đúng hình dạng TRƯỚC khi chuẩn hóa (năm cột mã + năm chỉ mục đơn) và ba dòng mẫu."""
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(sa.text(OLD_SCHEMA))
        for spec in OLD_INDEXES:
            name, col = spec.split(":")
            conn.execute(sa.text(f"CREATE INDEX {name} ON tab_packaging_bom ({col})"))
        for fg, *codes in OLD_ROWS:
            conn.execute(sa.text("INSERT INTO tab_packaging_bom (fg_code, bottle_code, cap_code, label_code, carton_label_code, carton_code)"
                                 " VALUES (:fg, :a, :b, :c, :d, :e)"), dict(fg=fg, **dict(zip("abcde", codes))))
    with engine.connect() as conn:
        yield conn
    engine.dispose()


def _parts(conn):
    rows = conn.execute(sa.text("SELECT b.fg_code, p.part_type, p.part_code FROM tab_packaging_bom_part p "
                                "JOIN tab_packaging_bom b ON b.id = p.bom_id ORDER BY b.fg_code, p.part_type")).all()
    return [tuple(r) for r in rows]


EXPECTED_PARTS = [("HH1", 1, "C1"), ("HH1", 2, "N1"), ("HH1", 3, "L1"), ("HH1", 4, "NT1"), ("HH1", 5, "T1"),
                  ("HH2", 1, "C2"), ("HH3", 1, "C1"), ("HH3", 2, "N2"), ("HH3", 4, "NT1")]


def _run(conn, fn):
    with Operations.context(MigrationContext.configure(conn)):
        fn()
    conn.commit()


def test_migration_sao_nam_cot_thanh_dong_thanh_phan_bo_ma_rong(old_conn):
    """Hàm sao thuần: mã rỗng không thành dòng; loại là số `PackagingRole`; một mã dùng ở hai định mức vẫn hai dòng."""
    mig = _load_migration()
    old_conn.execute(sa.text("CREATE TABLE tab_packaging_bom_part (id INTEGER PRIMARY KEY AUTOINCREMENT, bom_id INTEGER NOT NULL, "
                             "part_type SMALLINT NOT NULL, part_code VARCHAR(50) NOT NULL)"))
    mig.copy_columns_to_parts(old_conn)
    assert _parts(old_conn) == EXPECTED_PARTS
    assert [t for t, _ in mig.ROLE_COLUMNS] == [int(r) for r in PackagingRole]            # bảng sao khớp enum hiện tại
    assert [c for _, c in mig.ROLE_COLUMNS] == [role_field(r) for r in PackagingRole]     # ...và tên cột cũ = tên trường phẳng


def test_migration_upgrade_roi_downgrade_tra_dung_du_lieu(old_conn):
    mig = _load_migration()
    _run(old_conn, mig.upgrade)
    insp = sa.inspect(old_conn)
    bom_cols = {c["name"] for c in insp.get_columns("tab_packaging_bom")}
    assert bom_cols == {"id", "fg_code", "fg_name", "legal_name", "carton_qty"}           # năm cột mã đã bị bỏ
    assert not {i["name"] for i in insp.get_indexes("tab_packaging_bom")} & {s.split(":")[0] for s in OLD_INDEXES}
    covering = next(i for i in insp.get_indexes("tab_packaging_bom_part") if i["name"] == "ix_pbom_part_code")
    assert covering["column_names"] == ["part_code", "part_type", "bom_id"]              # chỉ mục phủ cho tra ngược theo mã
    assert _parts(old_conn) == EXPECTED_PARTS

    _run(old_conn, mig.downgrade)
    insp = sa.inspect(old_conn)
    assert "tab_packaging_bom_part" not in insp.get_table_names()
    assert {s.split(":")[0] for s in OLD_INDEXES} <= {i["name"] for i in insp.get_indexes("tab_packaging_bom")}
    back = [tuple(r) for r in old_conn.execute(sa.text(
        "SELECT fg_code, bottle_code, cap_code, label_code, carton_label_code, carton_code FROM tab_packaging_bom ORDER BY fg_code"))]
    assert back == OLD_ROWS


def test_migration_xoa_dau_phieu_keo_theo_thanh_phan_khi_bat_khoa_ngoai(old_conn):
    mig = _load_migration()
    _run(old_conn, mig.upgrade)
    old_conn.execute(sa.text("PRAGMA foreign_keys = ON"))
    old_conn.execute(sa.text("DELETE FROM tab_packaging_bom WHERE fg_code = 'HH1'"))
    assert [p for p in _parts(old_conn) if p[0] == "HH1"] == [] and len(_parts(old_conn)) == 4


# ── 2. CRUD giữ bảng thành phần đồng bộ ─────────────────────────────────────────
def test_tao_ghi_mot_dong_thanh_phan_cho_moi_ma_co_gia_tri(api, db):
    res = api.post(BOMS, json={"fg_code": "HH9", "bottle_code": "CPT0105", "cap_code": "NAP0085", "label_code": "NHG0001", "carton_qty": 12})
    assert res.status_code == 201, res.text
    data = res.json()["data"]
    assert (data["bottle_code"], data["cap_code"], data["label_code"], data["carton_label_code"], data["carton_code"]) == \
           ("CPT0105", "NAP0085", "NHG0001", "", "")                               # trường phẳng giữ nguyên hình dạng cũ
    assert bom_codes_of(db, "HH9") == {1: "CPT0105", 2: "NAP0085", 3: "NHG0001"}
    assert db.query(PackagingBomPart).count() == 3


def test_sua_doi_them_xoa_thanh_phan_va_day_moc_cap_nhat(api, db):
    row = _bom(db, label_code="NHG0001")
    first_stamp = row.updated_at
    res = api.patch(f"{BOMS}/{row.id}", json={"bottle_code": "NAP0099", "cap_code": "", "carton_code": "THU0001"})
    assert res.status_code == 200, res.text
    assert bom_codes_of(db, "HH0001") == {1: "NAP0099", 3: "NHG0001", 5: "THU0001"}   # đổi chai, bỏ nắp, thêm thùng, giữ nhãn
    body = res.json()["data"]
    assert (body["bottle_code"], body["cap_code"], body["carton_code"]) == ("NAP0099", "", "THU0001")
    db.refresh(row)
    assert row.updated_at >= first_stamp
    #  Gửi lại đúng giá trị cũ: không sinh dòng trùng (ràng buộc duy nhất sẽ nổ nếu thêm hai lần)
    assert api.patch(f"{BOMS}/{row.id}", json={"bottle_code": "NAP0099"}).status_code == 200
    assert db.query(PackagingBomPart).filter(PackagingBomPart.bom_id == row.id).count() == 3


def test_sua_rieng_ten_khong_dong_den_thanh_phan(api, db):
    row = _bom(db)
    assert api.patch(f"{BOMS}/{row.id}", json={"fg_name": "Tên mới"}).status_code == 200
    assert bom_codes_of(db, "HH0001") == {1: "CPT0105", 2: "NAP0085"}


def test_xoa_dinh_muc_xoa_luon_thanh_phan(api, db):
    row = _bom(db, label_code="NHG0001")
    _bom(db, "HH0002")
    assert api.delete(f"{BOMS}/{row.id}").status_code == 200
    assert db.query(PackagingBomPart).count() == 2 and bom_codes_of(db, "HH0001") == {}


def test_khong_the_co_hai_dong_cung_loai_trong_mot_dinh_muc(db):
    row = _bom(db)
    db.add(PackagingBomPart(bom_id=row.id, part_type=int(PackagingRole.BOTTLE), part_code="X"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_loc_va_xep_danh_sach_theo_ma_thanh_phan_o_may_chu(api, db):
    _bom(db, "HH0001", cap_code="NAP0085")
    _bom(db, "HH0002", cap_code="NAP0099")
    _bom(db, "HH0003", cap_code="")
    items = api.get(BOMS, params={"cap_code": "0099"}).json()["data"]["items"]
    assert [i["fg_code"] for i in items] == ["HH0002"]
    asc = [i["fg_code"] for i in api.get(BOMS, params={"sort_by": "cap_code", "sort_dir": "asc"}).json()["data"]["items"]]
    desc = [i["fg_code"] for i in api.get(BOMS, params={"sort_by": "cap_code", "sort_dir": "desc"}).json()["data"]["items"]]
    assert asc[:2] == ["HH0001", "HH0002"] and asc[-1] == "HH0003"                  # ô trống luôn xuống cuối
    assert desc[:2] == ["HH0002", "HH0001"] and desc[-1] == "HH0003"
    op = api.get(BOMS, params={"cap_code__contains": "85"}).json()["data"]["items"]
    assert [i["fg_code"] for i in op] == ["HH0001"]


def test_sort_by_khong_nam_trong_danh_sach_cho_phep_bi_bo_qua(api, db):
    _bom(db)
    res = api.get(BOMS, params={"sort_by": "parts", "sort_dir": "asc"})              # quan hệ, không phải cột / trường tính được phép
    assert res.status_code == 200 and len(res.json()["data"]["items"]) == 1


# ── 3. Tra ngược theo mã vật tư ─────────────────────────────────────────────────
def test_model_khai_dung_chi_muc_phu_va_rang_buoc_duy_nhat():
    indexes = {i.name: [c.name for c in i.columns] for i in PackagingBomPart.__table__.indexes}
    assert indexes == {"ix_pbom_part_code": ["part_code", "part_type", "bom_id"]}
    uniques = {c.name: [col.name for col in c.columns] for c in PackagingBomPart.__table__.constraints if c.name}
    assert uniques["uq_pbom_part_bom_type"] == ["bom_id", "part_type"]


def test_tra_nguoc_san_pham_nao_dung_ma_x(db, catalog):
    _bom(db, "HH0001", cap_code="NAP0085")
    _bom(db, "HH0002", bottle_code="NAP0085", cap_code="NAP0085")                    # cùng một mã ở HAI loại trong cùng sản phẩm
    _bom(db, "HH0003", cap_code="NAP0099")
    assert svc.usage_by_code(db, ["NAP0085"]) == {"NAP0085": 2}                      # đếm theo SẢN PHẨM, không theo dòng thành phần
    assert svc.usage_by_code(db)["CPT0105"] == 2
    assert [b.fg_code for b in svc.load_bom_rows(db, uses_codes=["NAP0099"])] == ["HH0003"]
    assert [b.fg_code for b in svc.load_bom_rows(db, uses_codes=["NAP0085"])] == ["HH0001", "HH0002"]
    assert svc.load_bom_rows(db, uses_codes=[]) == []                                # rỗng nghĩa là KHÔNG ai dùng, không phải "tất cả"
    only = svc.load_bom_rows(db, uses_codes=["NAP0099"])[0]
    assert only.codes == {1: "CPT0105", 2: "NAP0099"} and only.code_of(PackagingRole.LABEL) == ""


def test_tac_dong_gia_dem_dung_so_san_pham_dung_ma(db, catalog):
    add_ledger(db, "NAP0085", 200, "2026-10-01")
    _bom(db, "HH0001")
    _bom(db, "HH0002")
    out = compute_impact(db, ["NAP0085"], {}, page=None)
    assert out["selected"][0]["usage"] == 2 and [p["fg_code"] for p in out["products"]] == ["HH0001", "HH0002"]


# ── 4. Thêm loại thành phần mới không đổi cấu trúc ──────────────────────────────
class ExtendedRole(IntEnum):
    """`PackagingRole` + một loại giả định (màng co) — chỉ để chứng minh mã duyệt theo enum, không theo năm cột."""

    BOTTLE = 1
    CAP = 2
    LABEL = 3
    CARTON_LABEL = 4
    CARTON = 5
    SHRINK_FILM = 6


def test_loai_moi_nam_o_bang_thanh_phan_khong_can_cot_moi(db, catalog):
    row = _bom(db)
    db.add(PackagingBomPart(bom_id=row.id, part_type=6, part_code="MCO001"))        # loại 6 chưa có trong enum thật
    db.commit()
    assert [c.name for c in PackagingBomPart.__table__.columns] == ["id", "bom_id", "part_type", "part_code"]   # không cột nào theo loại
    loaded = svc.load_bom_rows(db)[0]
    assert loaded.codes[6] == "MCO001" and "MCO001" in loaded.code_set()
    assert svc.usage_by_code(db, ["MCO001"]) == {"MCO001": 1}
    cost = cost_service.compute_product_cost(loaded, {}, None, None)                 # enum hiện tại chưa biết loại 6 → bỏ qua, không vỡ
    assert [int(p.role) for p in cost.parts] == [1, 2, 3, 4, 5]


def test_cong_thuc_chi_phi_duyet_moi_loai_trong_enum(monkeypatch):
    """Thêm thành viên enum là loại mới vào chi phí / chai (mặc định tính theo chai) mà không sửa hàm tính."""
    monkeypatch.setattr(cost_service, "PackagingRole", ExtendedRole)
    bom = svc.BomRow("HH", "", "", 10, {1: "C", 6: "M"})
    prices = {code: SimpleNamespace(old=D(price), new=D(price), unit="", floor=None, ceiling=None)
              for code, price in (("C", 1000), ("M", 50))}
    cost = cost_service.compute_product_cost(bom, prices)
    assert [int(p.role) for p in cost.parts] == [1, 2, 3, 4, 5, 6]
    assert cost.cost_old_bottle == D("1050.0000")


def test_set_bom_codes_tu_choi_loai_la_va_khong_ghi_nua_chung(db, catalog):
    row = _bom(db)
    with pytest.raises(ValueError):
        svc.set_bom_codes(row, {99: "X"})
    assert svc.set_bom_codes(row, {1: "CPT0105"}) is False                          # không đổi gì
    assert svc.set_bom_codes(row, {1: "NAP0099", 4: "NDT0001"}) is True
    db.commit()
    assert bom_codes_of(db, "HH0001") == {1: "NAP0099", 2: "NAP0085", 4: "NDT0001"}


def test_flat_codes_la_chi_doc_gan_thuoc_tinh_khong_ghi_xuong_db(db, catalog):
    """Gán `row.cap_code = ...` chỉ đổi bộ nhớ (thuộc tính tính được) — dữ liệu thật đổi qua `set_bom_codes`."""
    row = _bom(db)
    row.cap_code = "NAP0099"
    db.commit()
    assert bom_codes_of(db, "HH0001")[2] == "NAP0085"
