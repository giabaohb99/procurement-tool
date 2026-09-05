"""bao-CR-295 (ticket 23) — Báo cáo Yêu cầu mua hàng theo DÒNG hàng.

Mục tiêu nghiệp vụ: NSTM soi mã hàng nào CHƯA được đặt (1 phiếu 3 mã / 3 NCC -> 3 ĐMH,
tránh đặt sót). Test canh:
  - dòng trả đủ trường ghép header (mã PYC, người YC, bộ phận) + GRAM lấy từ Product.specs
    (hệ không có trường gram riêng) + tên NSTM theo mã NV;
  - lọc line_status='chua_dat' GỘP 2 trạng thái chưa đặt;
  - scope phòng ban: phòng ban YÊU CẦU chỉ thấy phòng mình (mock report_dept_scope);
  - phân trang + lọc search theo mã hàng.
"""
from types import SimpleNamespace

from app.modules.report import service as report_service
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem


def _make_pr(db, seed, code: str, request_date: str, department: str = "Phòng Test",
             status: str = "approved") -> PurchaseRequest:
    pr = PurchaseRequest(code=code, company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department=department,
                         status=status, request_date=request_date,
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    return pr


def _make_item(db, pr, product_code: str, line_status: str = "Chưa tạo đơn mua hàng",
               assignee: str = "", qty=10, price=1000, vat_pct=8) -> PurchaseRequestItem:
    it = PurchaseRequestItem(pr_id=pr.id, product_code=product_code,
                             product_name=f"SP {product_code}", item_group="Nhãn",
                             qty=qty, unit="cái", price=price, vat_pct=vat_pct,
                             amount=float(qty) * float(price) * (1 + vat_pct / 100),
                             warehouse="Kho HN", expected_date="2026-09-20",
                             assignee=assignee, line_status=line_status)
    db.add(it)
    db.flush()
    return it


def _see_all(monkeypatch):
    monkeypatch.setattr(report_service, "report_dept_scope", lambda db, user: None)


USER = SimpleNamespace(id=0)   # không dùng tới khi đã mock report_dept_scope


class TestBaoCaoDongYCMH:
    def test_tra_du_truong_gram_tu_specs_va_ten_nstm(self, db, seed, monkeypatch):
        from app.modules.product.model import Product
        db.add(Product(code="SP-A", name="SP A", specs="120 gram", is_active=True))
        pr = _make_pr(db, seed, "PYC-T23-A", "2026-09-01")
        _make_item(db, pr, "SP-A", assignee=seed.emp_nstm_code)
        db.commit()
        _see_all(monkeypatch)
        out = report_service.compute_pr_lines(db, USER, year="2026")
        assert out["total"] == 1
        r = out["items"][0]
        assert r["pr_code"] == "PYC-T23-A" and r["department"] == "Phòng Test"
        assert r["gram"] == "120 gram"                    # GRAM = Product.specs
        assert r["assignee_name"] == "NSTM Chính"          # mã NV -> tên
        assert r["amount"] == 10800.0 and r["line_status"] == "Chưa tạo đơn mua hàng"
        # dropdown NSTM có kèm tên
        assert out["assignees"] == [{"code": seed.emp_nstm_code, "name": "NSTM Chính"}]

    def test_loc_chua_dat_gop_hai_trang_thai(self, db, seed, monkeypatch):
        pr = _make_pr(db, seed, "PYC-T23-B", "2026-09-02")
        _make_item(db, pr, "SP-1", line_status="Chưa tạo đơn mua hàng")
        _make_item(db, pr, "SP-2", line_status="Chưa đặt hàng")
        _make_item(db, pr, "SP-3", line_status="Đã đặt hàng")
        _make_item(db, pr, "SP-4", line_status="Hoàn thành")
        db.commit()
        _see_all(monkeypatch)
        out = report_service.compute_pr_lines(db, USER, year="2026", line_status="chua_dat")
        assert out["total"] == 2
        assert {r["product_code"] for r in out["items"]} == {"SP-1", "SP-2"}
        # lọc 1 trạng thái đơn lẻ vẫn chạy
        out2 = report_service.compute_pr_lines(db, USER, year="2026", line_status="Đã đặt hàng")
        assert [r["product_code"] for r in out2["items"]] == ["SP-3"]

    def test_scope_phong_ban_chi_thay_phong_minh(self, db, seed, monkeypatch):
        pr1 = _make_pr(db, seed, "PYC-T23-C", "2026-09-03", department="Phòng Test")
        pr2 = _make_pr(db, seed, "PYC-T23-D", "2026-09-03", department="Phòng Khác")
        _make_item(db, pr1, "SP-C")
        _make_item(db, pr2, "SP-D")
        db.commit()
        monkeypatch.setattr(report_service, "report_dept_scope", lambda db, user: {"Phòng Test"})
        out = report_service.compute_pr_lines(db, USER, year="2026")
        assert [r["product_code"] for r in out["items"]] == ["SP-C"]
        # allow = set() rỗng -> không thấy gì (không rơi về "thấy hết")
        monkeypatch.setattr(report_service, "report_dept_scope", lambda db, user: set())
        assert report_service.compute_pr_lines(db, USER, year="2026")["total"] == 0

    def test_phan_trang_va_search_moi_nhat_truoc(self, db, seed, monkeypatch):
        cu = _make_pr(db, seed, "PYC-T23-E", "2026-08-01")
        moi = _make_pr(db, seed, "PYC-T23-F", "2026-09-04")
        _make_item(db, cu, "SP-CU")
        _make_item(db, moi, "SP-MOI")
        db.commit()
        _see_all(monkeypatch)
        out = report_service.compute_pr_lines(db, USER, year="2026", page=1, page_size=1)
        assert out["total"] == 2 and len(out["items"]) == 1
        assert out["items"][0]["pr_code"] == "PYC-T23-F"   # phiếu mới nhất trước
        # search theo mã hàng
        out2 = report_service.compute_pr_lines(db, USER, year="2026", search="SP-CU")
        assert out2["total"] == 1 and out2["items"][0]["product_code"] == "SP-CU"
