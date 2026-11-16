"""bao-CR-759 — dòng YCMH lưu MÃ kho (`warehouse_code`) bên cạnh TÊN kho (`warehouse`).

Trước đây dòng YCMH chỉ lưu tên kho: đổi tên kho trong danh mục là mất liên kết, và giao diện v2 tạo ĐMH từ YCMH
không tra được mã nên ĐMH trống kho nhận (PO01160, PO01163, PO01175, PO01178 trên prod).

Bài kiểm chốt bốn điều:
1. Client cũ chỉ gửi TÊN -> máy chủ tự suy MÃ; client mới gửi MÃ -> máy chủ tự điền TÊN theo danh mục.
2. Kho đổi tên trong danh mục: lưu lại phiếu bằng client cũ (gửi tên cũ, không gửi mã) vẫn giữ mã.
3. Công cụ chỉ sửa TÊN (trợ lý AI chép dòng cũ rồi đổi tên kho) -> mã suy lại theo tên mới, không kẹt mã cũ.
4. Câu backfill của migration điền đúng mã theo tên; trùng tên thì lấy kho đang dùng, rồi id nhỏ nhất.
"""
import importlib.util
from pathlib import Path

from app.modules.catalog.model import Warehouse
from app.modules.purchase_request.model import PurchaseRequestItem
from app.modules.purchase_request.schema import PRCreate, PRItemIn, PRUpdate
from app.modules.purchase_request.service import copy_pr, create_pr, items_of, update_pr
from app.modules.purchase_request.serializer import _out
from app.modules.purchase_request.warehouse_ref import WarehouseCatalog, sync_line_warehouse

MIGRATION = Path(__file__).resolve().parents[2] / "backend" / "migrations" / "versions" / "prwh759a_ycmh_dong_luu_ma_kho.py"


def _kho(db):
    db.add_all([
        Warehouse(code="Dego Cần Thơ", name="CÔNG TY TNHH DEGO HOLDING", is_active=True),
        Warehouse(code="KHO-HN", name="Kho Hà Nội", is_active=True),
    ])
    db.commit()


def _tao_phieu(db, seed, *lines):
    return create_pr(db, PRCreate(company_id=seed.company_id, requester="Người YC",
                                  requester_id=seed.emp_req_id, request_date="2026-11-16",
                                  items=list(lines)),
                     user_id=seed.u_req_id)


def _dong(db, pr_id):
    return items_of(db, pr_id)


def test_client_cu_chi_gui_ten_thi_may_chu_suy_ma(db, seed):
    _kho(db)
    pr = _tao_phieu(db, seed, PRItemIn(product_name="Hàng A", qty=1, warehouse="CÔNG TY TNHH DEGO HOLDING"))
    [line] = _dong(db, pr.id)
    assert line.warehouse_code == "Dego Cần Thơ"
    assert line.warehouse == "CÔNG TY TNHH DEGO HOLDING"


def test_client_moi_gui_ma_thi_may_chu_dien_ten_theo_danh_muc(db, seed):
    _kho(db)
    pr = _tao_phieu(db, seed, PRItemIn(product_name="Hàng A", qty=1, warehouse_code="KHO-HN", warehouse=""))
    [line] = _dong(db, pr.id)
    assert (line.warehouse_code, line.warehouse) == ("KHO-HN", "Kho Hà Nội")


def test_ten_khong_khop_kho_nao_thi_de_ma_trong_giu_ten(db, seed):
    _kho(db)
    pr = _tao_phieu(db, seed, PRItemIn(product_name="Hàng A", qty=1, warehouse="Kho lạ"))
    [line] = _dong(db, pr.id)
    assert (line.warehouse_code, line.warehouse) == ("", "Kho lạ")


def test_kho_doi_ten_luu_lai_bang_client_cu_van_giu_ma(db, seed):
    _kho(db)
    pr = _tao_phieu(db, seed, PRItemIn(product_name="Hàng A", qty=1, warehouse="Kho Hà Nội"))
    [line] = _dong(db, pr.id)
    db.query(Warehouse).filter(Warehouse.code == "KHO-HN").update({"name": "Kho Hà Nội mới"})
    db.commit()

    #  Client cũ gửi lại đúng tên đang thấy (tên cũ), không có mã.
    update_pr(db, pr.id, PRUpdate(items=[PRItemIn(id=line.id, product_name="Hàng A", qty=2,
                                                  warehouse="Kho Hà Nội")]), user_id=seed.u_req_id)
    [line] = _dong(db, pr.id)
    assert line.warehouse_code == "KHO-HN"
    #  Mã thắng nên tên tự cập nhật theo danh mục.
    assert line.warehouse == "Kho Hà Nội mới"


def test_cong_cu_chi_doi_ten_kho_thi_ma_suy_lai_theo_ten_moi(db, seed):
    _kho(db)
    pr = _tao_phieu(db, seed, PRItemIn(product_name="Hàng A", qty=1, warehouse_code="KHO-HN"))
    [line] = _dong(db, pr.id)
    #  Trợ lý AI chép nguyên dòng cũ (có mã cũ) rồi chỉ đổi tên kho.
    update_pr(db, pr.id, PRUpdate(items=[PRItemIn(id=line.id, product_name="Hàng A", qty=1,
                                                  warehouse_code="KHO-HN",
                                                  warehouse="CÔNG TY TNHH DEGO HOLDING")]),
              user_id=seed.u_req_id)
    [line] = _dong(db, pr.id)
    assert (line.warehouse_code, line.warehouse) == ("Dego Cần Thơ", "CÔNG TY TNHH DEGO HOLDING")


def test_xoa_trang_kho_thi_ca_hai_cot_trong(db, seed):
    _kho(db)
    pr = _tao_phieu(db, seed, PRItemIn(product_name="Hàng A", qty=1, warehouse_code="KHO-HN"))
    [line] = _dong(db, pr.id)
    update_pr(db, pr.id, PRUpdate(items=[PRItemIn(id=line.id, product_name="Hàng A", qty=1)]),
              user_id=seed.u_req_id)
    [line] = _dong(db, pr.id)
    assert (line.warehouse_code, line.warehouse) == ("", "")


def test_serializer_tra_ma_kho_va_nhan_ban_giu_ma(db, seed):
    _kho(db)
    pr = _tao_phieu(db, seed, PRItemIn(product_name="Hàng A", qty=1, warehouse="Kho Hà Nội"))
    out = _out(db, pr)
    assert out["items"][0]["warehouse"] == "Kho Hà Nội"
    assert out["items"][0]["warehouse_code"] == "KHO-HN"

    clone = copy_pr(db, pr.id, seed.u_req_id)
    [line] = _dong(db, clone.id)
    assert (line.warehouse_code, line.warehouse) == ("KHO-HN", "Kho Hà Nội")


def test_trung_ten_kho_thi_lay_kho_dang_dung_roi_id_nho(db):
    db.add_all([
        Warehouse(code="CU", name="Kho chung", is_active=False),
        Warehouse(code="MOI1", name="Kho chung", is_active=True),
        Warehouse(code="MOI2", name="Kho chung", is_active=True),
    ])
    db.commit()
    data = {"warehouse": "Kho chung", "warehouse_code": ""}
    sync_line_warehouse(data, WarehouseCatalog(db))
    assert data["warehouse_code"] == "MOI1"


def test_migration_backfill_dien_ma_theo_ten(db):
    spec = importlib.util.spec_from_file_location("prwh759a", MIGRATION)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    db.add_all([
        Warehouse(code="CU", name="Kho chung", is_active=False),
        Warehouse(code="MOI1", name="Kho chung", is_active=True),
        Warehouse(code="Dego Cần Thơ", name="CÔNG TY TNHH DEGO HOLDING", is_active=True),
    ])
    db.add_all([
        PurchaseRequestItem(pr_id=1, product_name="a", warehouse="CÔNG TY TNHH DEGO HOLDING", warehouse_code=""),
        PurchaseRequestItem(pr_id=1, product_name="b", warehouse="Kho chung", warehouse_code=""),
        PurchaseRequestItem(pr_id=1, product_name="c", warehouse="Kho lạ", warehouse_code=""),
        PurchaseRequestItem(pr_id=1, product_name="d", warehouse="", warehouse_code=""),
        #  Dòng đã có mã thì không đụng.
        PurchaseRequestItem(pr_id=1, product_name="e", warehouse="Kho chung", warehouse_code="GIU"),
    ])
    db.commit()

    unmatched = migration.backfill_codes(db.connection())
    db.commit()
    assert unmatched == 1                       # chỉ dòng "Kho lạ"

    got = {r.product_name: r.warehouse_code for r in db.query(PurchaseRequestItem).all()}
    assert got == {"a": "Dego Cần Thơ", "b": "MOI1", "c": "", "d": "", "e": "GIU"}
