"""kh-NT2-8-may-chu (NF-22) — `/api/dashboard/overview` có thêm `kpi_inv_by_warehouse`: giá trị tồn theo từng kho, xếp giảm
dần, tính từ đúng danh sách tồn kho đã qua `apply_scope` (không quét lại toàn bảng). Tên kho lấy từ danh mục kho; kho
chưa có trong danh mục thì tên là chính mã kho."""
from app.modules.catalog.model import Warehouse

from test_pham_vi_tai_chinh_kho_bao_cao import create_inventory, read_overview, two_company_data  # noqa: F401


def test_ton_kho_theo_kho_dung_pham_vi_tong_khop_va_thieu_ten_tra_ma(world, two_company_data):  # noqa: F811
    db = world.db
    co_a = two_company_data.po_a.company_id
    db.add(Warehouse(code="K_A", name="Kho tổng A", is_active=True))
    create_inventory(db, company_id=co_a, warehouse_code="K_A2", product_code="SP_A2", product_name="Hàng A2",
                     qty=3, avg_cost=400, value=1200)
    create_inventory(db, company_id=co_a, warehouse_code="K_A", product_code="SP_A3", product_name="Hàng A3",
                     qty=1, avg_cost=50.5, value=50.5)
    db.commit()
    a1 = world.grant("a1", "inventory", scope="company")
    b1 = world.grant("b1", "inventory", scope="company")

    da = read_overview(db, a1.user)
    rows = da["kpi_inv_by_warehouse"]
    assert rows == [{"warehouse_code": "K_A2", "warehouse_name": "K_A2", "value": 1200.0, "lines": 1},
                    {"warehouse_code": "K_A", "warehouse_name": "Kho tổng A", "value": 550.5, "lines": 2}]
    assert round(sum(r["value"] for r in rows), 2) == da["kpi"]["inv_value"]

    rows_b = read_overview(db, b1.user)["kpi_inv_by_warehouse"]
    assert [r["warehouse_code"] for r in rows_b] == ["K_B"]                     # kho pháp nhân A không lọt sang


def test_thieu_quyen_ton_kho_thi_khong_co_khoi(world, two_company_data):  # noqa: F811
    a1 = world.grant("a1", "payable", scope="company")
    assert read_overview(world.db, a1.user)["kpi_inv_by_warehouse"] == []
