"""CR-069 — tìm phiếu theo SẢN PHẨM trên bảng danh sách.

- YCMH: ô "Mã / tên hàng" dò `product_code` + `product_name` của DÒNG HÀNG, khớp một phần.
- YCBG: dòng chưa có mã hàng nên dò "Thông số kỹ thuật" + "Yêu cầu khác" của dòng, cộng thêm
  mã/tên SP của PHƯƠNG ÁN ĐÃ CHỐT; KHÔNG dò các cột lộ NCC.

Test gọi thẳng `_list_query` của hai controller — cùng hàm mà màn danh sách và file xuất Excel
dùng, nên đúng ở đây là đúng cả hai. Tầng phạm vi dữ liệu (`apply_scope`) được vô hiệu hóa để
tách bạch: ở đây chỉ kiểm BỘ LỌC.
"""
from types import SimpleNamespace

import pytest
from starlette.requests import Request as _StarletteRequest


def _req(qs: str = ""):
    """Request giả chỉ mang query string — đủ cho apply_filters / _list_query."""
    return _StarletteRequest({"type": "http", "method": "GET", "path": "/",
                              "query_string": qs.encode(), "headers": []})


USER = SimpleNamespace(id=1, employee_id=1)


def _no_scope(monkeypatch, module):
    monkeypatch.setattr(module, "apply_scope", lambda q, *a, **k: q)
    monkeypatch.setattr(module, "get_perm_profile", lambda db, u: {"grants": []})
    return module


# ── YCMH ────────────────────────────────────────────────────────────────────────
@pytest.fixture
def prc(monkeypatch):
    import app.modules.purchase_request.controller as m
    return _no_scope(monkeypatch, m)


def _pr(db, code, **kw):
    from app.modules.purchase_request.model import PurchaseRequest
    pr = PurchaseRequest(code=code, requester="Người YC", department="Phòng Test",
                         status=kw.pop("status", "approved"), **kw)
    db.add(pr)
    db.flush()
    return pr


def _pr_item(db, pr, **kw):
    from app.modules.purchase_request.model import PurchaseRequestItem
    it = PurchaseRequestItem(pr_id=pr.id, **kw)
    db.add(it)
    db.flush()
    return it


@pytest.fixture
def pr_data(db):
    """3 phiếu: hai phiếu có mã hàng đuôi 5155, một phiếu hoàn toàn khác."""
    a = _pr(db, "PYC-A")
    _pr_item(db, a, product_code="HOP5155", product_name="Hộp giấy 5155")
    b = _pr(db, "PYC-B", status="draft")
    _pr_item(db, b, product_code="NHG5155", product_name="Nhãn giấy")
    _pr_item(db, b, product_code="TEM01", product_name="Tem dán thùng")
    c = _pr(db, "PYC-C")
    _pr_item(db, c, product_code="TUI02", product_name="Túi PE")
    return SimpleNamespace(a=a, b=b, c=c)


def _codes(query):
    return sorted(p.code for p in query.all())


def test_ycmh_go_mot_phan_ma_hang_van_ra(db, prc, pr_data):
    assert _codes(prc._list_query(_req("product=5155"), db, USER)) == ["PYC-A", "PYC-B"]


def test_ycmh_tim_duoc_ca_theo_ten_hang(db, prc, pr_data):
    assert _codes(prc._list_query(_req("product=T%C3%BAi"), db, USER)) == ["PYC-C"]
    # Một phần tên ở giữa chuỗi cũng khớp
    assert _codes(prc._list_query(_req("product=d%C3%A1n"), db, USER)) == ["PYC-B"]


def test_ycmh_khong_phan_biet_hoa_thuong(db, prc, pr_data):
    assert _codes(prc._list_query(_req("product=hop5155"), db, USER)) == ["PYC-A"]


def test_ycmh_nhieu_dong_khop_van_chi_ra_mot_phieu(db, prc, pr_data):
    # Thêm dòng thứ hai cùng khớp -> phiếu vẫn chỉ ra một lần, không nhân bản hàng
    got = [p.code for p in prc._list_query(_req("product=Nh%C3%A3n"), db, USER).all()]
    _pr_item(db, pr_data.b, product_code="NHG5156", product_name="Nhãn giấy loại 2")
    got2 = [p.code for p in prc._list_query(_req("product=Nh%C3%A3n"), db, USER).all()]
    assert got == got2 == ["PYC-B"]


def test_ycmh_khong_khop_thi_rong(db, prc, pr_data):
    assert _codes(prc._list_query(_req("product=KHONGCOMA"), db, USER)) == []


def test_ycmh_bo_trong_thi_khong_loc(db, prc, pr_data):
    assert _codes(prc._list_query(_req(""), db, USER)) == ["PYC-A", "PYC-B", "PYC-C"]
    assert _codes(prc._list_query(_req("product=%20%20"), db, USER)) == ["PYC-A", "PYC-B", "PYC-C"]


def test_ycmh_cong_don_voi_bo_loc_khac(db, prc, pr_data):
    # Cùng lúc lọc trạng thái -> giao nhau, không thay thế nhau
    assert _codes(prc._list_query(_req("product=5155&status=draft"), db, USER)) == ["PYC-B"]


def test_ycmh_khong_dinh_phieu_da_xoa(db, prc, pr_data):
    pr_data.a.is_deleted = True
    db.flush()
    assert _codes(prc._list_query(_req("product=5155"), db, USER)) == ["PYC-B"]


# ── YCBG ────────────────────────────────────────────────────────────────────────
@pytest.fixture
def src(monkeypatch):
    import app.modules.survey_request.controller as m
    return _no_scope(monkeypatch, m)


def _sr(db, code, **kw):
    from app.modules.survey_request.model import SurveyRequest
    sr = SurveyRequest(code=code, requester="Người YC", department="Phòng Test",
                       purpose="Mua mới", status=kw.pop("status", "survey_done"), **kw)
    db.add(sr)
    db.flush()
    return sr


def _sr_line(db, sr, **kw):
    from app.modules.survey_request.model import SurveyRequestLine
    ln = SurveyRequestLine(survey_request_id=sr.id, **kw)
    db.add(ln)
    db.flush()
    return ln


def _sr_opt(db, line, **kw):
    from app.modules.survey_request.model import SurveyRequestOption
    o = SurveyRequestOption(survey_request_line_id=line.id, **kw)
    db.add(o)
    db.flush()
    return o


@pytest.fixture
def sr_data(db):
    a = _sr(db, "YCKS-A")
    _sr_line(db, a, item_group="Bao bì", requirement_detail="Thùng carton 3 lớp, in 2 màu")
    b = _sr(db, "YCKS-B", status="processing")
    ln_b = _sr_line(db, b, item_group="Bao bì", requirement_detail="Màng PE quấn pallet")
    _sr_opt(db, ln_b, is_chosen=True, system_product_code="MPE0088", snap_product_name="Màng PE 500mm",
            snap_internal_code="NCC-XYZ-01", supplier_code="NCC01", supplier_name="Cty Bao Bì XYZ")
    c = _sr(db, "YCKS-C")
    ln_c = _sr_line(db, c, item_group="Văn phòng phẩm", other_requirement="Giao trong ngày, có mẫu thử")
    # Phương án CHƯA chốt: không được kéo phiếu vào kết quả tìm theo mã SP
    _sr_opt(db, ln_c, is_chosen=False, system_product_code="MPE0088", snap_product_name="Màng PE loại khác")
    return SimpleNamespace(a=a, b=b, c=c)


def test_ycbg_tim_theo_thong_so_ky_thuat(db, src, sr_data):
    assert _codes(src._list_query(_req("product=carton"), db, USER)) == ["YCKS-A"]


def test_ycbg_tim_theo_yeu_cau_khac(db, src, sr_data):
    assert _codes(src._list_query(_req("product=m%E1%BA%ABu%20th%E1%BB%AD"), db, USER)) == ["YCKS-C"]


def test_ycbg_tim_theo_ma_sp_cua_phuong_an_da_chot(db, src, sr_data):
    # YCKS-C cũng có option mã MPE0088 nhưng CHƯA chốt -> không ra
    assert _codes(src._list_query(_req("product=MPE0088"), db, USER)) == ["YCKS-B"]


def test_ycbg_tim_theo_ten_sp_bao_gia_da_chot(db, src, sr_data):
    assert _codes(src._list_query(_req("product=500mm"), db, USER)) == ["YCKS-B"]


def test_ycbg_khong_do_cot_lo_ncc(db, src, sr_data):
    """Gõ mã SP theo NCC / mã / tên NCC đều KHÔNG ra — kẻo người không có quyền xem NCC
    dò ngược ra được nhà cung cấp của phiếu."""
    for kw in ("NCC-XYZ-01", "NCC01", "Cty Bao B%C3%AC"):
        assert _codes(src._list_query(_req(f"product={kw}"), db, USER)) == []


def test_ycbg_bo_trong_thi_khong_loc(db, src, sr_data):
    assert _codes(src._list_query(_req(""), db, USER)) == ["YCKS-A", "YCKS-B", "YCKS-C"]


def test_ycbg_cong_don_voi_bo_loc_khac(db, src, sr_data):
    assert _codes(src._list_query(_req("product=PE&status=processing"), db, USER)) == ["YCKS-B"]
    assert _codes(src._list_query(_req("product=PE&status=draft"), db, USER)) == []
