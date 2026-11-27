"""bao-CR-792 (27/11/2026) — TÁCH khóa quyền `packaging_cost` của cụm Giá NVL sản xuất thành mỗi màn một khóa.

Phủ: (a) mỗi khóa chỉ mở đường API của màn mình, khóa khác 403; (b) đường dùng chung (`/code-options`, `/fg-options`) mở với BẤT
KỲ khóa nào, đóng khi không có khóa nào, giá của `/code-options` tính trên HỢP phạm vi các khóa đo trên sổ giá; (c) nhập Excel +
xóa dữ liệu theo lô gác đúng khóa của màn nhận dữ liệu; (d) hàm ánh xạ + migration `permsplit792` chuyển quyền cũ sang khóa mới.
"""
import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi import HTTPException

from app.core.permissions import ENTITIES, ENTITY_LABELS, PACKAGING_ENTITIES, SENSITIVE_PROCUREMENT_ENTITIES
from app.modules.import_tool import controller as imp_ctl
from app.modules.import_tool.model import ImportBatch, ImportMode, ImportModule, ImportStatus
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401  (fixture)
from so_gia_factory_cr784 import add_ledger, add_products, build_bom

PC = "/api/packaging-cost"
QUOTES, BOMS = "/api/product-price-quotes", "/api/packaging-boms"
IMPACT_BODY = {"json": {"codes": ["CPT0105"]}}
#  Khóa -> các đường ĐỌC và XUẤT của màn đó: (phương thức, đường, tham số).
READ = {
    "packaging_impact": [("post", f"{PC}/impact", IMPACT_BODY)],
    "packaging_product_summary": [("get", f"{PC}/product-overview", {})],
    "packaging_price_list": [("get", f"{PC}/price-list", {}), ("get", QUOTES, {})],
    "packaging_last_price": [("get", f"{PC}/last-prices", {})],
    "packaging_history": [("get", f"{PC}/history", {})],
    "packaging_bom": [("get", BOMS, {})],
}
EXPORT = {
    "packaging_impact": [("post", f"{PC}/impact/export", IMPACT_BODY)],
    "packaging_product_summary": [("get", f"{PC}/product-overview/export", {})],
    "packaging_price_list": [("get", f"{PC}/price-list/export", {})],
    "packaging_last_price": [("get", f"{PC}/last-prices/export", {})],
    "packaging_history": [("get", f"{PC}/history/export", {})],
}
SHARED = (f"{PC}/code-options", f"{PC}/fg-options")
KEYS = tuple(READ)
MIGRATION = next((Path(__file__).resolve().parents[2] / "backend" / "migrations" / "versions").glob("permsplit792_*.py"))


@pytest.fixture
def world(db, seed):
    """Một sản phẩm có định mức dùng chai CPT0105; chai có giá 100 ở pháp nhân của người xem và 999 (mới hơn) ở pháp nhân khác."""
    add_products(db, ("CPT0105", "Chai 450ml", "Cái"), ("NAP0085", "Nắp", "Cái"))
    add_ledger(db, "CPT0105", 100, "2026-01-01", company_id=seed.company_id)
    add_ledger(db, "CPT0105", 999, "2026-09-01", company_id=seed.company_id + 99)
    db.add(build_bom(fg_code="HH1", fg_name="Sản phẩm 1", bottle_code="CPT0105", cap_code="NAP0085", carton_qty=12,
                     created_by=1, updated_by=1))
    db.commit()


@pytest.fixture
def api(db, seed, client_as, world):  # noqa: F811
    return client_as(db.get(User, seed.u_req_id))


def _status(api, method, url, kwargs) -> int:
    return getattr(api, method)(url, **kwargs).status_code


# ── Sổ đăng ký ──────────────────────────────────────────────────────────────────
def test_khoa_cu_nghi_han_va_sau_khoa_moi_co_nhan_dung_khuon():
    assert "packaging_cost" not in ENTITIES and "packaging_cost" not in ENTITY_LABELS
    assert tuple(PACKAGING_ENTITIES) == KEYS and set(KEYS) <= set(ENTITIES)
    assert set(KEYS) <= set(SENSITIVE_PROCUREMENT_ENTITIES) and "packaging_cost" not in SENSITIVE_PROCUREMENT_ENTITIES
    for key in KEYS:
        assert ENTITY_LABELS[key].startswith("Giá NVL sản xuất › "), key


def test_nhat_ky_bao_gia_quy_ve_khoa_bang_gia_con_dinh_muc_trung_ten_khoa():
    from app.core.entity_models import model_of
    from app.modules.audit.controller import PERMISSION_KEY_ALIAS
    assert PERMISSION_KEY_ALIAS["packaging_cost_quote"] == "packaging_price_list"
    assert PERMISSION_KEY_ALIAS.get("packaging_bom", "packaging_bom") == "packaging_bom"
    #  Nhật ký định mức không được soi phạm vi trên bảng sổ giá (id định mức không phải id dòng sổ giá).
    assert model_of("packaging_bom") is None and model_of("packaging_cost_quote") is None


# ── (a) Mỗi khóa chỉ mở màn của mình ─────────────────────────────────────────────
@pytest.mark.parametrize("held", KEYS)
def test_moi_khoa_chi_mo_duong_doc_va_xuat_cua_man_minh(api, seed, cap_quyen, held):
    cap_quyen(seed.u_req_id, held, scope="all", read=True, export=True)
    for key in KEYS:
        want = 200 if key == held else 403
        for method, url, kwargs in [*READ[key], *EXPORT.get(key, [])]:
            assert _status(api, method, url, kwargs) == want, (held, method, url)


def test_chi_co_read_thi_khong_xuat_duoc_man_minh(api, seed, cap_quyen):
    for key in EXPORT:
        cap_quyen(seed.u_req_id, key, scope="all", read=True)
    for key, calls in EXPORT.items():
        for method, url, kwargs in calls:
            assert _status(api, method, url, kwargs) == 403, (key, url)


def test_ghi_bao_gia_can_khoa_bang_gia_ghi_dinh_muc_can_khoa_dinh_muc(api, seed, cap_quyen):
    quote = {"product_code": "CPT0105", "price": 120, "valid_from": "2026-11-01"}
    bom = {"fg_code": "HH9", "fg_name": "Tay", "bottle_code": "CPT0105"}
    cap_quyen(seed.u_req_id, "packaging_bom", scope="all", read=True, create=True, write=True, delete=True)
    assert api.post(QUOTES, json=quote).status_code == 403
    assert api.delete(f"{QUOTES}/1").status_code == 403
    assert api.post(BOMS, json=bom).status_code in (200, 201)
    #  Khóa Lịch sử mua hàng có write / delete (nạp Sổ Misa) nhưng không mở CRUD báo giá hay định mức.
    cap_quyen(seed.u_req_id, "packaging_history", scope="all", read=True, write=True, delete=True)
    assert api.post(QUOTES, json=quote).status_code == 403
    cap_quyen(seed.u_req_id, "packaging_price_list", scope="all", create=True)
    assert api.post(QUOTES, json=quote).status_code in (200, 201)


def test_khoa_bang_gia_khong_ghi_duoc_dinh_muc(api, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "packaging_price_list", scope="all", read=True, create=True, write=True, delete=True)
    assert api.post(BOMS, json={"fg_code": "HH9", "fg_name": "Tay", "bottle_code": "CPT0105"}).status_code == 403
    assert api.patch(f"{BOMS}/1", json={"fg_name": "X"}).status_code == 403
    assert api.delete(f"{BOMS}/1").status_code == 403


# ── (b) Đường dùng chung ────────────────────────────────────────────────────────
def test_duong_dung_chung_dong_khi_khong_co_khoa_nao(api):
    for url in SHARED:
        assert api.get(url).status_code == 403, url


@pytest.mark.parametrize("held", KEYS)
def test_duong_dung_chung_mo_voi_bat_ky_khoa_nao(api, seed, cap_quyen, held):
    cap_quyen(seed.u_req_id, held, scope="all", read=True)
    for url in SHARED:
        res = api.get(url)
        assert res.status_code == 200, (held, url)
        assert sorted(r["code"] for r in res.json()["data"]["items"]) == (["CPT0105", "NAP0085"] if "code-options" in url else ["HH1"])


def test_duong_dung_chung_can_quyen_read_khong_phai_hanh_dong_khac(api, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "packaging_bom", scope="all", create=True, write=True, delete=True, export=True)
    for url in SHARED:
        assert api.get(url).status_code == 403, url


def _new_price(api) -> float | None:
    rows = {r["code"]: r for r in api.get(f"{PC}/code-options").json()["data"]["items"]}
    return rows["CPT0105"]["new"]


def test_gia_cua_o_chon_ma_tinh_tren_hop_pham_vi_cac_khoa_do_tren_so_gia(api, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "packaging_bom", scope="all", read=True)
    assert _new_price(api) is None                       # chỉ có khóa định mức (không đo trên sổ giá): có mã, không có giá
    cap_quyen(seed.u_req_id, "packaging_last_price", scope="company", read=True)
    assert _new_price(api) == 100                        # phạm vi công ty: chỉ lần mua của pháp nhân mình
    cap_quyen(seed.u_req_id, "packaging_history", scope="company", read=True)
    assert _new_price(api) == 100                        # hai khóa cùng phạm vi công ty: HỢP vẫn là công ty
    cap_quyen(seed.u_req_id, "packaging_impact", scope="all", read=True)
    assert _new_price(api) == 999                        # thêm một khóa phạm vi tất cả: HỢP = thấy hết


def test_quyen_xuat_tren_khoa_khac_khong_mo_rong_pham_vi_doc_cua_o_chon_ma(api, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "packaging_last_price", scope="company", read=True)
    cap_quyen(seed.u_req_id, "packaging_impact", scope="all", export=True)          # không có read
    assert _new_price(api) == 100


def test_pham_vi_tung_man_theo_dung_khoa_cua_man_do(api, seed, cap_quyen):
    """Khóa Bảng giá phạm vi công ty + khóa Giá mua gần nhất phạm vi tất cả: mỗi màn lọc theo khóa CỦA MÌNH, không lấy hợp."""
    cap_quyen(seed.u_req_id, "packaging_price_list", scope="company", read=True)
    cap_quyen(seed.u_req_id, "packaging_last_price", scope="all", read=True)
    price_row = api.get(f"{PC}/price-list").json()["data"]["items"][0]
    last_row = {r["code"]: r for r in api.get(f"{PC}/last-prices").json()["data"]["items"]}["CPT0105"]
    assert (price_row["code"], price_row["new"]) == ("CPT0105", 100)
    assert last_row["last_price"] == 999


# ── (c) Nhập Excel + xóa dữ liệu theo lô ─────────────────────────────────────────
IMPORT_RULES = [      # (loại lô, bước, khóa, hành động)
    (ImportModule.PACKAGING_BOM, "create", "packaging_bom", "create"),
    (ImportModule.PACKAGING_BOM, "revert", "packaging_bom", "delete"),
    (ImportModule.PACKAGING_QUOTE, "create", "packaging_price_list", "create"),
    (ImportModule.PACKAGING_QUOTE, "revert", "packaging_price_list", "delete"),
    (ImportModule.PACKAGING_MISA, "create", "packaging_history", "write"),
    (ImportModule.PACKAGING_MISA, "revert", "packaging_history", "write"),
]


@pytest.mark.parametrize("module,step,key,action", IMPORT_RULES)
def test_nhap_excel_gac_dung_khoa_cua_man_nhan_du_lieu(db, seed, cap_quyen, module, step, key, action):
    user = db.get(User, seed.u_req_id)
    for other in KEYS:                                   # đủ MỌI hành động trên năm khóa còn lại vẫn không qua
        if other != key:
            cap_quyen(seed.u_req_id, other, scope="all", read=True, create=True, write=True, delete=True, export=True)
    wrong = {a: True for a in ("read", "create", "write", "delete") if a != action}
    cap_quyen(seed.u_req_id, key, scope="all", **wrong)   # đúng khóa nhưng sai hành động cũng không qua
    with pytest.raises(HTTPException) as exc:
        imp_ctl._guard_module(db, user, int(module), step)
    assert exc.value.status_code == 403
    cap_quyen(seed.u_req_id, key, scope="all", **{action: True})
    imp_ctl._guard_module(db, user, int(module), step)


def _batch(db, seed, module) -> ImportBatch:
    batch = ImportBatch(module=int(module), mode=int(ImportMode.APPLY), status=int(ImportStatus.DONE), filename="x.xlsx",
                        created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(batch)
    db.commit()
    return batch


PURGE_KEYS = {ImportModule.PACKAGING_BOM: "packaging_bom", ImportModule.PACKAGING_QUOTE: "packaging_price_list",
              ImportModule.PACKAGING_MISA: "packaging_history"}


@pytest.mark.parametrize("held_module", list(PURGE_KEYS))
def test_xoa_theo_lo_can_quyen_xoa_dung_khoa_theo_loai_lo(api, db, seed, cap_quyen, held_module):
    batches = {module: _batch(db, seed, module) for module in PURGE_KEYS}
    cap_quyen(seed.u_req_id, "import", scope="all", read=True)
    cap_quyen(seed.u_req_id, PURGE_KEYS[held_module], scope="all", delete=True)
    for module, batch in batches.items():
        want = 200 if module == held_module else 403
        assert api.get(f"/api/imports/{batch.id}/purge-preview").status_code == want, (held_module, module)
        assert api.post(f"/api/imports/{batch.id}/purge", json={}).status_code == want, (held_module, module)


def test_xoa_theo_lo_khong_co_quyen_xoa_nao_thi_khong_do_duoc_id_lo(api, db, seed, cap_quyen):
    batch = _batch(db, seed, ImportModule.PACKAGING_BOM)
    cap_quyen(seed.u_req_id, "import", scope="all", read=True)
    for key in KEYS:                                      # đủ quyền khác, KHÔNG có delete ở khóa nào
        cap_quyen(seed.u_req_id, key, scope="all", read=True, create=True, write=True, export=True)
    cap_quyen(seed.u_req_id, "packaging_impact", scope="all", delete=True)     # delete ở khóa không giữ dữ liệu lô: không tính
    assert api.get(f"/api/imports/{batch.id}/purge-preview").status_code == 403
    assert api.get("/api/imports/99999/purge-preview").status_code == 403       # lô có hay không đều 403
    cap_quyen(seed.u_req_id, "packaging_history", scope="all", delete=True)
    assert api.get("/api/imports/99999/purge-preview").status_code == 404       # có quyền xóa ở một khóa: mới biết lô không có
    assert api.get(f"/api/imports/{batch.id}/purge-preview").status_code == 403  # lô định mức cần đúng khóa định mức


def test_xoa_theo_lo_van_can_quyen_xem_import(api, db, seed, cap_quyen):
    batch = _batch(db, seed, ImportModule.PACKAGING_BOM)
    cap_quyen(seed.u_req_id, "packaging_bom", scope="all", read=True, delete=True)
    assert api.get(f"/api/imports/{batch.id}/purge-preview").status_code == 403


# ── Công cụ Trợ lý / MCP ────────────────────────────────────────────────────────
TOOL_KEYS = {"packaging_price_impact": ("packaging_impact", {"codes": ["CPT0105"]}),
             "packaging_price_lookup": ("packaging_price_list", {"codes": ["CPT0105"]}),
             "packaging_product_cost": ("packaging_product_summary", {"fg_codes": ["HH1"]})}


@pytest.mark.parametrize("tool", list(TOOL_KEYS))
def test_moi_cong_cu_tro_ly_gac_bang_khoa_cua_man_tuong_ung(db, seed, cap_quyen, world, tool):
    from app.modules.assistant import tools as T
    key, args = TOOL_KEYS[tool]
    user = db.get(User, seed.u_req_id)
    for other in KEYS:
        if other != key:
            cap_quyen(seed.u_req_id, other, scope="all", read=True, export=True)
    assert T.run_tool(db, user, tool, args).get("denied") is True
    cap_quyen(seed.u_req_id, key, scope="all", read=True)
    assert not T.run_tool(db, user, tool, args).get("denied")


def test_tra_gia_chi_kem_cac_lan_mua_gan_nhat_khi_co_khoa_gia_mua_gan_nhat(db, seed, cap_quyen, world):
    from app.modules.assistant import tools as T
    user = db.get(User, seed.u_req_id)
    cap_quyen(seed.u_req_id, "packaging_price_list", scope="all", read=True)
    out = T.run_tool(db, user, "packaging_price_lookup", {"codes": ["CPT0105"]})
    assert out["items"][0]["new_price"] == 999 and out["items"][0]["recent_purchases"] == []
    assert "Giá mua gần nhất" in out["note"]
    cap_quyen(seed.u_req_id, "packaging_last_price", scope="company", read=True)
    out = T.run_tool(db, user, "packaging_price_lookup", {"codes": ["CPT0105"]})
    assert [p["price"] for p in out["items"][0]["recent_purchases"]] == [100]      # theo phạm vi của khóa Giá mua gần nhất


# ── (d) Migration chuyển quyền ──────────────────────────────────────────────────
def _load_migration():
    spec = importlib.util.spec_from_file_location("permsplit792", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ham_anh_xa_chia_hanh_dong_theo_bang_khoa():
    mig = _load_migration()
    assert set(mig.NEW_KEY_ACTIONS) == set(KEYS)
    full = mig.split_flags({"read": True, "create": True, "write": True, "delete": True, "export": True, "approve": True})
    assert full == {
        "packaging_impact": {"read": True, "export": True},
        "packaging_product_summary": {"read": True, "export": True},
        "packaging_price_list": {"read": True, "export": True, "create": True, "write": True, "delete": True},
        "packaging_last_price": {"read": True, "export": True},
        "packaging_history": {"read": True, "export": True, "write": True, "delete": True},
        "packaging_bom": {"read": True, "export": True, "create": True, "write": True, "delete": True},
    }
    assert mig.split_flags({"read": True}) == {key: {"read": True} for key in KEYS}
    assert mig.split_flags({"create": True}) == {"packaging_price_list": {"create": True}, "packaging_bom": {"create": True}}
    assert set(mig.split_flags({"write": True, "delete": True})) == {"packaging_price_list", "packaging_bom", "packaging_history"}
    assert mig.split_flags({"approve": True, "print": True, "read": False}) == {}


def test_ham_gop_nguoc_lay_hop_co_va_pham_vi_rong_nhat():
    mig = _load_migration()
    flags, scope = mig.merge_flags([{"scope": "company", "read": True}, {"scope": "all", "write": True, "export": False},
                                    {"scope": "own", "delete": True}])
    assert flags == {"read": True, "write": True, "delete": True} and scope == "all"


PERMISSION_DDL = (
    "CREATE TABLE tab_permission (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,"
    " created_by BIGINT NOT NULL, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_by BIGINT NOT NULL,"
    " role_id BIGINT NOT NULL, entity VARCHAR(50) NOT NULL, can_read BOOLEAN NOT NULL, can_create BOOLEAN NOT NULL,"
    " can_write BOOLEAN NOT NULL, can_delete BOOLEAN NOT NULL, can_approve BOOLEAN NOT NULL, can_cancel BOOLEAN NOT NULL,"
    " can_print BOOLEAN NOT NULL, can_export BOOLEAN NOT NULL, can_import BOOLEAN NOT NULL DEFAULT 0, scope VARCHAR(10) NOT NULL)")
FLAG_COLUMNS = ("can_read", "can_create", "can_write", "can_delete", "can_export")


@pytest.fixture
def old_conn():
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(sa.text(PERMISSION_DDL))
    with engine.connect() as conn:
        yield conn
    engine.dispose()


def _permission(conn, role_id, entity, scope, flags: str, by=7):
    """`flags` = chuỗi chữ cái đầu của hành động được bật: r(ead) c(reate) w(rite) d(elete) e(xport) a(pprove)."""
    values = {f"can_{name}": name[0] in flags for name in ("read", "create", "write", "delete", "export", "approve")}
    conn.execute(sa.text(
        "INSERT INTO tab_permission (created_by, updated_by, role_id, entity, scope, can_read, can_create, can_write, can_delete,"
        " can_export, can_approve, can_cancel, can_print) VALUES (:by, :by, :role_id, :entity, :scope, :can_read, :can_create,"
        " :can_write, :can_delete, :can_export, :can_approve, 0, 0)"), {"by": by, "role_id": role_id, "entity": entity,
                                                                         "scope": scope, **values})


def _dump(conn) -> dict[tuple[int, str], tuple[str, str]]:
    """`{(vai trò, khóa): (phạm vi, chuỗi cờ đang bật)}` của mọi dòng quyền."""
    rows = conn.execute(sa.text(f"SELECT role_id, entity, scope, {', '.join(FLAG_COLUMNS)} FROM tab_permission")).mappings().all()
    return {(r["role_id"], r["entity"]): (r["scope"], "".join(c[4] for c in FLAG_COLUMNS if r[c])) for r in rows}


def _run_mig(conn, fn):
    with Operations.context(MigrationContext.configure(conn)):
        fn()
    conn.commit()


def test_migration_chuyen_quyen_cu_sang_khoa_moi_giu_vai_tro_va_pham_vi(old_conn):
    mig = _load_migration()
    assert (mig.revision, mig.down_revision) == ("permsplit792", "phstage790")
    _permission(old_conn, 1, "packaging_cost", "all", "rcwdea")          # đủ quyền (như Quản lý thu mua)
    _permission(old_conn, 2, "packaging_cost", "company", "r")           # chỉ xem, phạm vi công ty
    _permission(old_conn, 3, "packaging_cost", "all", "rw")              # xem + sửa; đã có sẵn dòng định mức chỉnh tay
    _permission(old_conn, 3, "packaging_bom", "company", "r")
    _permission(old_conn, 4, "packaging_cost", "all", "")                # dòng rỗng: không sinh gì
    _permission(old_conn, 1, "purchase_order", "all", "rcwd")            # khóa khác: không đụng
    old_conn.commit()
    _run_mig(old_conn, mig.upgrade)
    got = _dump(old_conn)
    assert not [k for k in got if k[1] == "packaging_cost"]
    assert {k[1]: v for k, v in got.items() if k[0] == 1} == {
        "packaging_impact": ("all", "re"), "packaging_product_summary": ("all", "re"), "packaging_price_list": ("all", "rcwde"),
        "packaging_last_price": ("all", "re"), "packaging_history": ("all", "rwde"), "packaging_bom": ("all", "rcwde"),
        "purchase_order": ("all", "rcwd")}
    assert {k[1]: v for k, v in got.items() if k[0] == 2} == {key: ("company", "r") for key in KEYS}
    role3 = {k[1]: v for k, v in got.items() if k[0] == 3}
    assert role3["packaging_bom"] == ("company", "r")                     # dòng đã có: giữ nguyên, không ghi đè
    assert role3["packaging_price_list"] == ("all", "rw") and role3["packaging_history"] == ("all", "rw")
    assert role3["packaging_impact"] == ("all", "r")
    assert not [k for k in got if k[0] == 4]
    by = old_conn.execute(sa.text("SELECT DISTINCT created_by, can_approve FROM tab_permission WHERE entity = 'packaging_impact'")).all()
    assert [tuple(r) for r in by] == [(7, 0)]                             # chép dấu vết người dựng; approve không chuyển
    _run_mig(old_conn, mig.upgrade)                                       # chạy lại: không sinh trùng
    assert _dump(old_conn) == got and len(got) == old_conn.execute(sa.text("SELECT COUNT(*) FROM tab_permission")).scalar()


def test_migration_downgrade_gop_nguoc_ve_mot_khoa(old_conn):
    mig = _load_migration()
    _permission(old_conn, 1, "packaging_cost", "all", "rcwde")
    _permission(old_conn, 2, "packaging_cost", "company", "re")
    old_conn.commit()
    before = _dump(old_conn)
    _run_mig(old_conn, mig.upgrade)
    old_conn.execute(sa.text("UPDATE tab_permission SET scope = 'all' WHERE role_id = 2 AND entity = 'packaging_history'"))
    _run_mig(old_conn, mig.downgrade)
    got = _dump(old_conn)
    assert got[(1, "packaging_cost")] == before[(1, "packaging_cost")]
    assert got[(2, "packaging_cost")] == ("all", "re")                    # phạm vi rộng nhất trong các dòng gộp
    assert set(got) == {(1, "packaging_cost"), (2, "packaging_cost")}


def test_chuoi_migration_mot_dau_la_permsplit792():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATION.parents[1]))
    script = ScriptDirectory.from_config(cfg)
    assert script.get_heads() == ["matprice800"]            # bao-CR-800 nối tiếp ngay sau `permsplit792`
    assert script.get_revision("matprice800").down_revision == "permsplit792"
    assert script.get_revision("permsplit792").down_revision == "phstage790"
