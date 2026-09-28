"""duoc-CR-481 — bản TỔNG HỢP cho màn biểu đồ của Tiến độ mua hàng · Tiến độ báo giá ·
Báo cáo khảo sát (phân hệ Báo cáo). Kiểm các hàm gom thuần, không cần DB.

Canh những chỗ dễ đếm sai lặng lẽ:
  - Tiến độ mua hàng: một DÒNG nhiều lần giao chỉ đếm một lần; lần giao chưa nhận không tính
    trễ/đúng hạn; khối NCC rỗng khi không có `supplier.read`.
  - Tiến độ báo giá: đọc lại cột TÍNH của bảng, thứ tự nhãn theo chuỗi tiến độ.
  - Báo cáo khảo sát: dòng thiếu `line_approve` tính là "Chờ duyệt".
"""
from types import SimpleNamespace as NS

from app.modules.purchase_progress.controller import summarize as summarize_purchase
from app.modules.survey.controller import summarize_report_rows
from app.modules.survey_progress import export as sp_ex
from app.modules.survey_progress.controller import summarize as summarize_survey


def _po(dept="Kho", supplier="NCC A"):
    return NS(department=dept, supplier_name=supplier, supplier_code="A")


def _it(item_id, status="ordered", qty=10):
    return NS(id=item_id, progress_status=status, qty_order=qty)


def _dl(received, date="2026-05-10", promise=0, regulated=0):
    return NS(received_qty=received, received_date=date, diff_promise=promise, diff_regulated=regulated)


class TestTienDoMuaHang:
    def test_dong_nhieu_lan_giao_dem_mot_lan_va_tinh_nhan_du(self):
        po, it = _po(), _it(1, qty=10)
        out = summarize_purchase([(po, it, _dl(4)), (po, it, _dl(6, promise=-2))], True)
        assert out["total"]["items"] == 1
        assert out["total"]["full"] == 1 and out["total"]["under"] == 0
        assert out["total"]["deliveries"] == 2 and out["total"]["late"] == 1
        assert out["by_month"] == [{"month": "2026-05", "received": 2, "late": 1}]

    def test_dong_chua_giao_va_lan_giao_chua_nhan(self):
        po = _po()
        out = summarize_purchase([
            (po, _it(1), None),                       # chưa có lần giao
            (po, _it(2), _dl(0, promise=-5)),         # lần giao chưa nhận: không tính trễ
            (po, _it(3, qty=0), None),                # SL đặt 0: không xếp nhóm nhận
        ], True)
        t = out["total"]
        assert t["items"] == 3 and t["unreceived"] == 2 and t["under"] == 0 and t["full"] == 0
        assert t["deliveries"] == 0 and t["late"] == 0

    def test_khong_co_quyen_ncc_thi_khoi_ncc_rong(self):
        out = summarize_purchase([(_po(), _it(1), _dl(10, regulated=-1))], False)
        assert out["by_supplier"] == [] and out["show_supplier"] is False
        assert out["total"]["late"] == 1                 # số tổng vẫn đếm, chỉ giấu tên NCC

    def test_bo_phan_xep_theo_dong_con_mo(self):
        out = summarize_purchase([
            (_po("A"), _it(1, "completed"), None), (_po("A"), _it(2, "completed"), None),
            (_po("B"), _it(3, "ordered"), None),
        ], True)
        assert [d["key"] for d in out["by_department"]] == ["B", "A"]
        assert out["by_department"][1] == {"key": "A", "items": 2, "open": 0}

    def test_tien_do_rong_tinh_la_chua_dat(self):
        out = summarize_purchase([(_po(), _it(1, status=""), None)], True)
        assert out["by_progress_status"] == [{"code": "not_ordered", "items": 1}]

    def test_khong_co_dong_nao(self):
        out = summarize_purchase([], True)
        assert out["total"] == {"items": 0, "deliveries": 0, "late": 0,
                                "unreceived": 0, "under": 0, "full": 0}


def _row(state, late=None, result="", handling=None, month="2026-03-02", who="NV1", group="Nhãn"):
    return {"progress_state": state, "days_late": late, "result_date": result,
            "handling_days": handling, "request_date": month, "assignee_name": who,
            "item_group": group}


class TestTienDoBaoGia:
    def test_giu_thu_tu_chuoi_tien_do_va_bo_nhan_rong(self):
        out = summarize_survey([_row(sp_ex.STATE_DONE), _row(sp_ex.STATE_NOT_RECEIVED)])
        assert [s["state"] for s in out["by_state"]] == [sp_ex.STATE_NOT_RECEIVED, sp_ex.STATE_DONE]

    def test_tre_mo_va_trung_binh_ngay_xu_ly(self):
        out = summarize_survey([
            _row(sp_ex.STATE_SURVEYING, late=3),
            _row(sp_ex.STATE_ANSWERED, result="2026-03-05", handling=2),
            _row(sp_ex.STATE_PR_CREATED, result="2026-03-06", handling=4),
        ])
        t = out["total"]
        assert t["lines"] == 3 and t["late"] == 1 and t["answered"] == 2
        assert t["open"] == 2                            # "Đã tạo YCMH" không còn mở
        assert t["avg_handling_days"] == 3.0

    def test_chua_co_ngay_xu_ly_thi_trung_binh_rong(self):
        assert summarize_survey([_row(sp_ex.STATE_RECEIVED)])["total"]["avg_handling_days"] is None

    def test_nstm_xep_theo_dong_mo(self):
        out = summarize_survey([
            _row(sp_ex.STATE_DONE, who="A"), _row(sp_ex.STATE_DONE, who="A"),
            _row(sp_ex.STATE_SURVEYING, who="B"),
        ])
        assert [a["name"] for a in out["by_assignee"]] == ["B", "A"]


class TestBaoCaoKhaoSat:
    def test_dem_theo_duyet_loai_thang(self):
        out = summarize_report_rows([
            {"kind": "supplier", "line_approve": "Đã duyệt", "date": "2026-04-01", "nspt": "X", "item_group": ""},
            {"kind": "product", "line_approve": "", "date": "2026-04-09", "nspt": "X", "item_group": "Nhãn"},
            {"kind": "product", "line_approve": "Không duyệt", "date": "", "nspt": "", "item_group": "Nhãn"},
        ])
        approve = {a["state"]: a["lines"] for a in out["by_approve"]}
        assert approve == {"Chờ duyệt": 1, "Đã duyệt": 1, "Không duyệt": 1, "Thiếu thông tin": 0}
        assert out["by_kind"] == {"supplier": 1, "product": 2}
        assert out["by_month"] == [{"month": "2026-04", "supplier": 1, "product": 1}]
        assert out["by_nspt"][0] == {"key": "X", "lines": 2, "approved": 1}
        assert out["by_item_group"][0]["key"] == "Nhãn"

    def test_khong_co_dong(self):
        out = summarize_report_rows([])
        assert out["total"] == 0 and out["by_month"] == []
