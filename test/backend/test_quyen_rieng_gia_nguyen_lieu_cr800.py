"""bao-CR-800 — giá NGUYÊN LIỆU (sản phẩm nhóm NL) cấp quyền riêng, tách khỏi các màn VTBB. CHỈ kiểm phần vừa làm:

- khóa `packaging_material_price` có trong sổ quyền, đo phạm vi pháp nhân trên sổ giá;
- đường Bảng giá nguyên liệu chỉ trả mã nhóm NL đã có giá, và chỉ mở cho người giữ khóa riêng;
- các màn VTBB (Bảng giá kể cả phạm vi *Mọi mã có giá*, gõ tìm, chọn thẳng mã; Giá mua gần nhất; Lịch sử mua hàng; ô chọn mã)
  không còn trả mã nguyên liệu, kể cả với người giữ đủ mọi khóa VTBB;
- mã nguyên liệu chỉ có báo giá cũng không lọt sang màn VTBB;
- phạm vi pháp nhân vẫn áp trên màn nguyên liệu;
- migration `matprice800` chép Xem / Xuất từ khóa Bảng giá VTBB, không chép quyền ghi, chạy lại không nhân đôi.
"""
import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa

from app.core.permissions import ENTITIES, ENTITY_LABELS, PACKAGING_ENTITIES, SENSITIVE_PROCUREMENT_ENTITIES
from app.core.scoping import SCOPE_FIELDS
from app.modules.packaging_cost.material_scope import MATERIAL_ENTITY, MATERIAL_GROUP
from app.modules.product.model import Product
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401  (fixture)
from so_gia_factory_cr784 import add_ledger, add_products, add_quote, build_bom

MIGRATION = next((Path(__file__).resolve().parents[2] / "backend" / "migrations" / "versions").glob("matprice800_*.py"))


@pytest.fixture
def world(db, seed):
    """Một chai (VTBB, trong định mức), một nguyên liệu có giá, một nguyên liệu chỉ có báo giá, một nguyên liệu chưa có giá."""
    add_products(db, ("CPT0105", "Chai 450ml", "Cái"), ("NAP0085", "Nắp", "Cái"))
    for code, name in (("NL0001", "Hoạt chất A"), ("NL0002", "Dung môi B"), ("NL0003", "Phụ gia C")):
        db.add(Product(code=code, name=name, unit="Kg", item_group=MATERIAL_GROUP))
    db.commit()
    add_ledger(db, "CPT0105", 100, "2026-01-01", company_id=seed.company_id)
    add_ledger(db, "NL0001", 50000, "2026-02-01", company_id=seed.company_id, unit="Kg")
    add_ledger(db, "NL0001", 52000, "2026-03-01", company_id=seed.company_id, unit="Kg")
    add_ledger(db, "NL0001", 99999, "2026-09-01", company_id=seed.company_id + 99, unit="Kg")     # pháp nhân khác
    add_quote(db, "NL0002", 7000, "2026-04-01")
    db.add(build_bom(fg_code="HH1", fg_name="Sản phẩm 1", bottle_code="CPT0105", cap_code="NAP0085", carton_qty=12,
                     created_by=1, updated_by=1))
    db.commit()


@pytest.fixture
def api(db, seed, client_as, world):  # noqa: F811
    return client_as(db.get(User, seed.u_req_id))


def _codes(api, url) -> list[str]:
    res = api.get(url)
    assert res.status_code == 200, (url, res.text)
    return sorted(r["code"] for r in res.json()["data"]["items"])


# ── Sổ đăng ký ────────────────────────────────────────────────────────────────────────────────────────────────────
def test_khoa_moi_co_trong_so_quyen_va_khong_lan_vao_nhom_khoa_vtbb():
    assert MATERIAL_ENTITY == "packaging_material_price" and MATERIAL_ENTITY in ENTITIES
    assert ENTITY_LABELS[MATERIAL_ENTITY] == "Giá NVL sản xuất › Bảng giá nguyên liệu"
    assert SCOPE_FIELDS[MATERIAL_ENTITY] == {"company": "company_id"}
    assert MATERIAL_ENTITY in SENSITIVE_PROCUREMENT_ENTITIES
    assert MATERIAL_ENTITY not in PACKAGING_ENTITIES          # đường dùng chung của các màn VTBB không mở theo khóa này


# ── Màn Bảng giá nguyên liệu ──────────────────────────────────────────────────────────────────────────────────────
def test_bang_gia_nguyen_lieu_chi_co_ma_nhom_nl_da_co_gia(api, seed, cap_quyen):
    cap_quyen(seed.u_req_id, MATERIAL_ENTITY, scope="all", read=True, export=True)

    assert _codes(api, "/api/packaging-cost/material-price-list") == ["NL0001", "NL0002"]     # NL0003 chưa có giá, chai không lên
    row = next(r for r in api.get("/api/packaging-cost/material-price-list").json()["data"]["items"] if r["code"] == "NL0001")
    assert (row["name"], row["group"], row["unit"]) == ("Hoạt chất A", MATERIAL_GROUP, "Kg")
    assert row["purchase_count"] == 3 and row["last_purchase_price"] == 99999                 # phạm vi all: thấy mọi pháp nhân
    assert _codes(api, "/api/packaging-cost/material-price-list?q=dung môi") == ["NL0002"]
    assert _codes(api, "/api/packaging-cost/material-price-list?code=NL0001&code=CPT0105") == ["NL0001"]
    assert _codes(api, "/api/packaging-cost/material-code-options") == ["NL0001", "NL0002"]
    assert api.get("/api/packaging-cost/material-price-list/export").status_code == 200


def test_pham_vi_phap_nhan_van_ap_tren_man_nguyen_lieu(api, db, seed, cap_quyen):
    from app.modules.user.model import UserScope

    role = cap_quyen(seed.u_req_id, MATERIAL_ENTITY, scope="company", read=True)
    db.add(UserScope(user_id=seed.u_req_id, role_id=role.id, dim="company", value=str(seed.company_id)))
    db.commit()
    row = next(r for r in api.get("/api/packaging-cost/material-price-list").json()["data"]["items"] if r["code"] == "NL0001")
    assert row["purchase_count"] == 2 and row["last_purchase_price"] == 52000                  # không thấy dòng của pháp nhân khác


@pytest.mark.parametrize("url", ["/api/packaging-cost/material-price-list", "/api/packaging-cost/material-price-list/export",
                                 "/api/packaging-cost/material-code-options"])
def test_nguoi_giu_du_khoa_vtbb_van_khong_vao_duoc_man_nguyen_lieu(api, seed, cap_quyen, url):
    for key in PACKAGING_ENTITIES:
        cap_quyen(seed.u_req_id, key, scope="all", read=True, export=True)
    assert api.get(url).status_code == 403


def test_chi_co_quyen_xem_thi_khong_xuat_duoc(api, seed, cap_quyen):
    cap_quyen(seed.u_req_id, MATERIAL_ENTITY, scope="all", read=True)
    assert api.get("/api/packaging-cost/material-price-list/export").status_code == 403


def test_khoa_nguyen_lieu_khong_mo_cac_man_vtbb(api, seed, cap_quyen):
    cap_quyen(seed.u_req_id, MATERIAL_ENTITY, scope="all", read=True, export=True)
    for url in ("/api/packaging-cost/price-list", "/api/packaging-cost/last-prices", "/api/packaging-cost/history",
                "/api/packaging-cost/code-options?scope=all"):
        assert api.get(url).status_code == 403, url


# ── Các màn VTBB không còn mã nguyên liệu ─────────────────────────────────────────────────────────────────────────
def test_cac_man_vtbb_khong_tra_ma_nguyen_lieu(api, seed, cap_quyen):
    for key in PACKAGING_ENTITIES:
        cap_quyen(seed.u_req_id, key, scope="all", read=True, export=True)
    cap_quyen(seed.u_req_id, MATERIAL_ENTITY, scope="all", read=True)          # giữ cả khóa nguyên liệu cũng không trộn màn

    assert _codes(api, "/api/packaging-cost/price-list") == ["CPT0105", "NAP0085"]
    assert _codes(api, "/api/packaging-cost/price-list?scope=all") == ["CPT0105", "NAP0085"]      # trước đây lọt NL0001
    assert _codes(api, "/api/packaging-cost/price-list?q=NL0001") == []
    assert _codes(api, "/api/packaging-cost/price-list?code=NL0001&code=NL0002") == []
    assert _codes(api, "/api/packaging-cost/price-list?code=NL0001&code=CPT0105") == ["CPT0105"]
    assert _codes(api, "/api/packaging-cost/code-options?scope=all") == ["CPT0105", "NAP0085"]
    assert _codes(api, "/api/packaging-cost/last-prices?scope=all&only_priced=false") == ["CPT0105", "NAP0085"]   # NL0002 chỉ có báo giá cũng không lọt
    assert _codes(api, "/api/packaging-cost/last-prices?scope=all&code=NL0001") == []
    assert _codes(api, "/api/packaging-cost/history") == ["CPT0105"]
    assert _codes(api, "/api/packaging-cost/history?codes=NL0001") == []


# ── Migration ─────────────────────────────────────────────────────────────────────────────────────────────────────
def _load_migration():
    spec = importlib.util.spec_from_file_location("matprice800", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def conn():
    engine = sa.create_engine("sqlite://")
    with engine.connect() as connection:
        connection.execute(sa.text(
            "CREATE TABLE tab_permission (id INTEGER PRIMARY KEY AUTOINCREMENT, role_id INTEGER, entity TEXT, scope TEXT, "
            "can_read BOOLEAN, can_create BOOLEAN, can_write BOOLEAN, can_delete BOOLEAN, can_export BOOLEAN, can_approve BOOLEAN, "
            "can_cancel BOOLEAN, can_print BOOLEAN, can_import BOOLEAN DEFAULT 0, created_by INTEGER, updated_by INTEGER)"))
        yield connection


def _grant(conn, role_id, entity, scope, **flags):
    conn.execute(sa.text(
        "INSERT INTO tab_permission (role_id, entity, scope, can_read, can_create, can_write, can_delete, can_export, can_approve, "
        "can_cancel, can_print, created_by, updated_by) VALUES (:r, :e, :s, :read, :create, :write, :delete, :export, 0, 0, 0, 7, 7)"),
        {"r": role_id, "e": entity, "s": scope, **{k: bool(flags.get(k)) for k in ("read", "create", "write", "delete", "export")}})


def _run(conn, fn):
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    with Operations.context(MigrationContext.configure(conn)):
        fn()


def _material_rows(conn) -> dict[int, tuple]:
    rows = conn.execute(sa.text("SELECT role_id, scope, can_read, can_export, can_create, can_write, can_delete, created_by "
                                "FROM tab_permission WHERE entity = 'packaging_material_price' ORDER BY role_id")).all()
    return {r[0]: tuple(r[1:]) for r in rows}


def test_migration_chep_xem_xuat_tu_khoa_bang_gia_khong_chep_quyen_ghi(conn):
    mig = _load_migration()
    assert (mig.revision, mig.down_revision) == ("matprice800", "permsplit792")
    _grant(conn, 14, "packaging_price_list", "all", read=True, export=True, create=True, write=True, delete=True)   # quản lý thu mua
    _grant(conn, 95, "packaging_price_list", "company", read=True, export=True)                                     # vai trò xem
    _grant(conn, 96, "packaging_price_list", "all", read=True)                                                      # chỉ xem
    _grant(conn, 97, "packaging_price_list", "all", create=True)                                                    # không xem: bỏ qua
    _grant(conn, 98, "packaging_history", "all", read=True, export=True)                                            # không có khóa bảng giá
    _grant(conn, 96, "packaging_material_price", "own", read=True)                                                  # đã chỉnh tay: giữ

    _run(conn, mig.upgrade)
    assert _material_rows(conn) == {
        14: ("all", 1, 1, 0, 0, 0, 7),
        95: ("company", 1, 1, 0, 0, 0, 7),
        96: ("own", 1, 0, 0, 0, 0, 7),
    }
    _run(conn, mig.upgrade)                                   # chạy lại không nhân đôi
    assert len(_material_rows(conn)) == 3

    _run(conn, mig.downgrade)
    assert _material_rows(conn) == {}
    assert conn.execute(sa.text("SELECT COUNT(*) FROM tab_permission WHERE entity = 'packaging_price_list'")).scalar() == 4
