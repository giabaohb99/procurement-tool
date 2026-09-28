"""duoc-CR-481 — bản TỔNG HỢP của báo cáo Chi tiết YC mua hàng (màn biểu đồ, phân hệ Báo cáo).

Canh:
  - dòng HỦY chỉ đếm ở `by_line_status`, không cộng vào tổng / tháng / bộ phận / NSTM;
  - `idle_*` gộp đúng hai trạng thái chưa đặt (no_po + not_ordered);
  - `line_status` rỗng của dữ liệu cũ tính là no_po;
  - scope phòng ban + bộ lọc dùng CHUNG với bảng — tổng số dòng khớp `compute_pr_lines`;
  - NSTM xếp theo số dòng chưa đặt, kèm tên.
"""
from types import SimpleNamespace

from app.modules.report import service as report_service
from test_bao_cao_dong_ycmh_ticket23 import _make_item, _make_pr

USER = SimpleNamespace(id=0)


def _see_all(monkeypatch):
    monkeypatch.setattr(report_service, "report_dept_scope", lambda db, user: None)


class TestTongHopDongYCMH:
    def test_dong_huy_chi_nam_o_tien_do_khong_cong_vao_tong(self, db, seed, monkeypatch):
        pr = _make_pr(db, seed, "PYC-S-A", "2026-03-05")
        _make_item(db, pr, "A1", line_status="no_po", qty=1, price=100, vat_pct=0)
        _make_item(db, pr, "A2", line_status="not_ordered", qty=1, price=200, vat_pct=0)
        _make_item(db, pr, "A3", line_status="ordered", qty=1, price=400, vat_pct=0)
        _make_item(db, pr, "A4", line_status="cancelled", qty=1, price=800, vat_pct=0)
        db.commit()
        _see_all(monkeypatch)
        out = report_service.compute_pr_lines_summary(db, USER, year="2026")
        assert out["total"] == {"lines": 3, "idle_lines": 2, "amount": 700.0, "idle_amount": 300.0}
        by_status = {s["code"]: s for s in out["by_line_status"]}
        assert by_status["cancelled"]["lines"] == 1 and by_status["cancelled"]["amount"] == 800.0
        assert sum(s["lines"] for s in out["by_line_status"]) == 4
        assert out["by_month"] == [{"month": "2026-03", "lines": 3, "idle_lines": 2,
                                    "amount": 700.0, "idle_amount": 300.0}]

    def test_line_status_rong_tinh_la_chua_tao_don(self, db, seed, monkeypatch):
        pr = _make_pr(db, seed, "PYC-S-B", "2026-04-01")
        _make_item(db, pr, "B1", line_status="")
        db.commit()
        _see_all(monkeypatch)
        out = report_service.compute_pr_lines_summary(db, USER, year="2026")
        assert [s["code"] for s in out["by_line_status"]] == ["no_po"]
        assert out["total"]["idle_lines"] == 1

    def test_scope_va_bo_loc_khop_bang_chi_tiet(self, db, seed, monkeypatch):
        mine = _make_pr(db, seed, "PYC-S-C", "2026-05-01", department="Phòng Test")
        other = _make_pr(db, seed, "PYC-S-D", "2026-05-01", department="Phòng Khác")
        _make_item(db, mine, "C1", line_status="no_po")
        _make_item(db, mine, "C2", line_status="ordered")
        _make_item(db, other, "D1", line_status="no_po")
        db.commit()
        monkeypatch.setattr(report_service, "report_dept_scope", lambda db, user: {"Phòng Test"})
        out = report_service.compute_pr_lines_summary(db, USER, year="2026")
        assert out["total"]["lines"] == 2
        assert [d["key"] for d in out["by_department"]] == ["Phòng Test"]
        table = report_service.compute_pr_lines(db, USER, year="2026")
        assert table["total"] == out["total"]["lines"]
        # cùng bộ lọc "chưa đặt" với bảng
        idle = report_service.compute_pr_lines_summary(db, USER, year="2026", line_status="chua_dat")
        assert idle["total"]["lines"] == 1
        # scope rỗng -> không thấy gì, không rơi về "thấy hết"
        monkeypatch.setattr(report_service, "report_dept_scope", lambda db, user: set())
        empty = report_service.compute_pr_lines_summary(db, USER, year="2026")
        assert empty["total"]["lines"] == 0 and empty["by_department"] == []

    def test_nstm_xep_theo_so_dong_chua_dat_kem_ten(self, db, seed, monkeypatch):
        pr = _make_pr(db, seed, "PYC-S-E", "2026-06-01")
        _make_item(db, pr, "E1", line_status="ordered", assignee="X-NHIEU-DONG")
        _make_item(db, pr, "E2", line_status="ordered", assignee="X-NHIEU-DONG")
        _make_item(db, pr, "E3", line_status="no_po", assignee=seed.emp_nstm_code)
        _make_item(db, pr, "E4", line_status="no_po")
        db.commit()
        _see_all(monkeypatch)
        out = report_service.compute_pr_lines_summary(db, USER, year="2026")
        first = out["by_assignee"][0]
        assert first["idle_lines"] == 1 and first["name"] in ("NSTM Chính", "")
        codes = [a["code"] for a in out["by_assignee"]]
        assert codes[-1] == "X-NHIEU-DONG"            # 0 dòng chưa đặt -> cuối bảng
        assert "" in codes                              # dòng chưa gán NSTM vẫn được đếm
        nstm = next(a for a in out["by_assignee"] if a["code"] == seed.emp_nstm_code)
        assert nstm["name"] == "NSTM Chính"

    def test_ky_khong_co_dong_nao(self, db, seed, monkeypatch):
        _see_all(monkeypatch)
        out = report_service.compute_pr_lines_summary(db, USER, year="1999")
        assert out["total"] == {"lines": 0, "idle_lines": 0, "amount": 0, "idle_amount": 0}
        assert out["by_month"] == [] and out["by_assignee"] == []
