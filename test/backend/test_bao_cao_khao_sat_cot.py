"""CR-248 — Báo cáo khảo sát trả ĐỦ cột.

Bản cũ chỉ dựng 14 trường cho mỗi dòng trong khi phiếu + hai bảng dòng có gần 70,
nên màn báo cáo không có gì để bày ra ngoài mã phiếu và kết quả duyệt.

Ba thứ phải khóa lại:

1. Dòng NCC và dòng SP có tập trường lệch nhau gần hết nhưng đổ chung MỘT bảng,
   nên mọi dòng phải mang ĐỦ bộ khóa — thiếu khóa là cột bên giao diện nhận
   `undefined` và tệp CSV lệch cột từ đó trở đi.
2. Cột số để `None` chứ không để 0, kẻo hàng trăm dòng NCC in một bức tường số 0.
3. Chính vì (2) mà một cột chứa LẪN `float` với `None`/chuỗi rỗng — đem so trực
   tiếp là Python ném TypeError và cả trang báo cáo chết 500 chỉ vì người dùng
   bấm một tiêu đề cột.
"""
import pytest

from app.modules.survey import service
from app.modules.survey.model import Survey, SurveyProductLine, SurveySupplierLine


def make_survey(db, **kw) -> Survey:
    base = dict(code="KS0001", survey_type="combined", status="approved",
                sr_code="YCBG0001", pr_code="PYC0001", item_group="Bao bì",
                item_code="XOT0009", item_name="Thùng carton 3 lớp", uom="Cái",
                nspt="Nguyễn Văn A", main_content="Khảo sát bao bì quý 3",
                received_date="2026-08-10", result_due_date="2026-08-20",
                request_qty=1000, proposed_rate=12000)
    base.update(kw)
    s = Survey(**base)
    db.add(s)
    db.commit()
    return s


def report_of(db, survey_ids=None):
    q = db.query(Survey)
    if survey_ids is not None:
        q = q.filter(Survey.id.in_(survey_ids))
    return service.report_rows(db, q)


def test_dong_ncc_va_dong_sp_cung_bo_khoa(db):
    """Hai loại dòng phải ra cùng một bộ khóa, kể cả trường của loại kia."""
    s = make_survey(db)
    db.add_all([
        SurveySupplierLine(survey_id=s.id, supplier_code="NCC01", supplier_name="Phương Nam"),
        SurveyProductLine(survey_id=s.id, product_name="Thùng carton", price_by_volume=12345.6789),
    ])
    db.commit()

    rows = report_of(db)
    assert len(rows) == 2
    assert set(rows[0]) == set(rows[1])
    # Dòng NCC vẫn có khóa của cột giá (để trống) và ngược lại.
    by_kind = {r["kind"]: r for r in rows}
    supplier, product = by_kind["supplier"], by_kind["product"]
    assert supplier["price_by_volume"] is None
    assert product["tax_code"] == ""


def test_thong_tin_dau_phieu_lap_lai_tren_moi_dong(db):
    """Mã YCBG/PYC, tên VTBB, ĐVT... nằm ở header — mọi dòng đều phải mang theo."""
    s = make_survey(db)
    db.add(SurveySupplierLine(survey_id=s.id, supplier_code="NCC01"))
    db.commit()

    row = report_of(db)[0]
    assert row["sr_code"] == "YCBG0001"
    assert row["pr_code"] == "PYC0001"
    assert row["item_name"] == "Thùng carton 3 lớp"
    assert row["uom"] == "Cái"
    assert row["request_qty"] == 1000
    assert row["proposed_rate"] == 12000
    assert row["survey_type"] == "combined"


def test_o_so_trong_de_none_chu_khong_de_0(db):
    """Trống hoặc 0 -> None, để giao diện bỏ TRẮNG thay vì in một tường số 0."""
    s = make_survey(db, request_qty=0, proposed_rate=0)
    db.add(SurveyProductLine(survey_id=s.id, product_name="Thùng", vat=0, moq=0))
    db.commit()

    row = report_of(db)[0]
    assert row["request_qty"] is None
    assert row["proposed_rate"] is None
    assert row["vat"] is None
    assert row["moq"] is None


def test_sl_cua_dong_thang_sl_du_kien_o_header(db):
    """Dòng SP có SL riêng (số dùng để tính thành tiền); header chỉ là dự phòng."""
    s = make_survey(db, request_qty=1000)
    db.add_all([
        SurveyProductLine(survey_id=s.id, product_name="A", request_qty=250),
        SurveyProductLine(survey_id=s.id, product_name="B"),   # chưa nhập -> lấy của header
    ])
    db.commit()

    rows = sorted(report_of(db), key=lambda r: r["content"])
    assert rows[0]["request_qty"] == 250
    assert rows[1]["request_qty"] == 1000


def test_co_mau_ra_chu_chu_khong_ra_true_false(db):
    """Cờ có/không quy về chữ để cột này xuất CSV và sắp xếp như mọi cột chữ."""
    s = make_survey(db)
    db.add_all([
        SurveyProductLine(survey_id=s.id, product_name="Co mau", sample_ready=True),
        SurveyProductLine(survey_id=s.id, product_name="Khong mau", sample_ready=False),
    ])
    db.commit()

    rows = sorted(report_of(db), key=lambda r: r["content"])
    assert rows[0]["sample_ready"] == "Có"
    assert rows[1]["sample_ready"] == ""


def test_dong_cua_phieu_ngoai_pham_vi_khong_lot_vao(db):
    """`report_rows` chỉ lấy dòng của phiếu trong phạm vi truy vấn được truyền vào."""
    s1 = make_survey(db, code="KS0001")
    s2 = make_survey(db, code="KS0002")
    db.add_all([
        SurveySupplierLine(survey_id=s1.id, supplier_code="TRONG"),
        SurveySupplierLine(survey_id=s2.id, supplier_code="NGOAI"),
    ])
    db.commit()

    rows = report_of(db, survey_ids=[s1.id])
    assert [r["supplier_code"] for r in rows] == ["TRONG"]


def test_khong_co_phieu_nao_thi_khong_hoi_bang_dong(db):
    """Không có phiếu -> trả rỗng ngay, khỏi quét hai bảng dòng."""
    assert report_of(db) == []


# ── sort_report_rows ───────────────────────────────────────────────────────────
def test_sap_xep_cot_lan_so_voi_chu_khong_no(db):
    """Cột giá có dòng SP mang float, dòng NCC mang None — so trực tiếp là TypeError."""
    rows = [
        {"price_by_volume": None, "kind": "supplier"},
        {"price_by_volume": 12000.5, "kind": "product"},
        {"price_by_volume": None, "kind": "supplier"},
        {"price_by_volume": 900.0, "kind": "product"},
    ]

    got = service.sort_report_rows(rows, "price_by_volume", "asc")
    assert [r["price_by_volume"] for r in got] == [900.0, 12000.5, None, None]

    got_desc = service.sort_report_rows(rows, "price_by_volume", "desc")
    assert [r["price_by_volume"] for r in got_desc] == [None, None, 12000.5, 900.0]


def test_sap_xep_cot_chu_khong_phan_biet_hoa_thuong(db):
    rows = [{"content": "beta"}, {"content": "Alpha"}, {"content": "gamma"}]
    got = service.sort_report_rows(rows, "content", "asc")
    assert [r["content"] for r in got] == ["Alpha", "beta", "gamma"]


def test_cot_ngoai_danh_sach_thi_giu_nguyen_thu_tu(db):
    """Cột lạ (hoặc rỗng) -> không sắp xếp, giữ nguyên thứ tự mặc định."""
    rows = [{"content": "b"}, {"content": "a"}]
    assert service.sort_report_rows(rows, "", "asc") is rows
    assert service.sort_report_rows(rows, "khong_ton_tai", "asc") is rows


def test_moi_cot_bay_ra_deu_sap_xep_duoc(db):
    """Danh sách cột cho phép phải BAO cả trường mới, kẻo bấm tiêu đề mà bảng đứng yên."""
    for field in ("price_by_volume", "amount", "tax_code", "item_name", "sr_code",
                  "debt_policy", "delivery_time", "survey_status"):
        assert field in service.REPORT_SORTABLE_FIELDS


@pytest.mark.parametrize("direction", ["asc", "desc"])
def test_sap_xep_on_dinh_giu_thu_tu_mac_dinh_lam_tieu_chi_phu(db, direction):
    """Các dòng bằng nhau ở cột đang sắp xếp thì giữ nguyên thứ tự đưa vào."""
    rows = [{"kind": "supplier", "line_id": i} for i in range(5)]
    got = service.sort_report_rows(rows, "kind", direction)
    assert [r["line_id"] for r in got] == [0, 1, 2, 3, 4]
