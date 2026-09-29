"""Mục «Pháp lý» của Tra cứu thị trường (29/09/2026) — duyệt cả danh mục hóa chất theo văn bản.

Canh: dòng ngừng dùng không lọt ra (sửa ở «Cấu hình» là tắt ngay trên màn đọc), tìm được bằng
công thức hóa học như ô tra cũ, và đường API chỉ đòi `customs_price.read` như ô tra.
"""
from app.modules.customs import regulation_browse_service as B
from app.modules.customs.constants import RegulationList
from app.modules.customs.controller import router
from app.modules.customs.model import CustomsRegulation


def _seed(db):
    db.add_all([
        CustomsRegulation(list_code=int(RegulationList.BANNED_TT75), name="Paraquat", cas_no="4685-14-7",
                          banned_year=2017, legal_basis="TT 75/2025/TT-BNNMT"),
        CustomsRegulation(list_code=int(RegulationList.ND24_PL4), name="Sulfuric acid", cas_no="7664-93-9",
                          threshold_kg=500, legal_basis="NĐ 24/2026/NĐ-CP"),
        CustomsRegulation(list_code=int(RegulationList.ND24_PL4), name="Toluene", cas_no="108-88-3",
                          threshold_kg=1000, legal_basis="NĐ 24/2026/NĐ-CP"),
        CustomsRegulation(list_code=int(RegulationList.PUBLISH_TT01), name="Ngừng dùng", cas_no="1-1-1",
                          is_active=False),
    ])
    db.commit()


def test_list_hides_inactive_rows_and_orders_by_document_then_name(db):
    _seed(db)
    total, items = B.list_regulations(db, "", None, 0, 50)
    assert total == 3
    assert [i["name"] for i in items] == ["Sulfuric acid", "Toluene", "Paraquat"]
    assert items[2]["obligation"].startswith("Hoạt chất CẤM từ năm 2017")


def test_filter_by_document_and_search_by_name_cas_or_formula(db):
    _seed(db)
    assert B.list_regulations(db, "", int(RegulationList.ND24_PL4), 0, 50)[0] == 2
    assert B.list_regulations(db, "paraq", None, 0, 50)[0] == 1, "không phân biệt hoa thường"
    assert B.list_regulations(db, "108-88", None, 0, 50)[0] == 1, "gõ dở số CAS vẫn ra"
    assert [i["name"] for i in B.list_regulations(db, "H2SO4", None, 0, 50)[1]] == ["Sulfuric acid"]
    assert B.list_regulations(db, "Ngừng", None, 0, 50)[0] == 0, "dòng ngừng dùng không tìm ra"
    assert B.list_regulations(db, "", None, 100, 50) == (3, [])


def test_options_list_every_document_even_empty_ones(db):
    _seed(db)
    opt = B.regulation_options(db)
    assert opt["total"] == 3
    counts = {o["value"]: o["count"] for o in opt["lists"]}
    assert set(counts) == {int(x) for x in RegulationList}
    assert counts[int(RegulationList.ND24_PL4)] == 2 and counts[int(RegulationList.PUBLISH_TT01)] == 0
    assert all(o["label"] for o in opt["lists"])


def test_empty_catalog(db):
    assert B.list_regulations(db, "", None, 0, 50) == (0, [])
    assert B.regulation_options(db)["total"] == 0


def test_browse_routes_need_only_customs_price_read():
    def guard(route):
        for dep in route.dependant.dependencies:
            code = getattr(dep.call, "__code__", None)
            if code and set(code.co_freevars) >= {"entity", "action"}:
                cells = dict(zip(code.co_freevars, dep.call.__closure__))
                return cells["entity"].cell_contents, cells["action"].cell_contents
    routes = {r.path: guard(r) for r in router.routes
              if r.path in ("/api/customs/regulations", "/api/customs/regulations/options")}
    assert routes == {"/api/customs/regulations": ("customs_price", "read"),
                      "/api/customs/regulations/options": ("customs_price", "read")}
