"""SỐ LIỆU TRANG TỔNG QUAN VĂN THƯ.

Hai chỗ dễ sai và đều sai âm thầm:

1. **Biểu đồ 12 tháng bỏ tháng rỗng.** Để cơ sở dữ liệu tự sinh nhãn tháng thì
   tháng không có văn bản biến mất khỏi trục — biểu đồ đọc ra một câu chuyện
   sai, nhìn như tháng đó không tồn tại.
2. **Đếm không lọc phạm vi.** Trang tổng quan nói một con số mà bấm vào danh
   sách lại ra con số khác; người dùng sẽ tin con số lớn hơn.
"""
from datetime import date, timedelta

import pytest

from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import dashboard_service, service
from app.modules.document.schema import DocumentCreate

ACTOR = 1


class _KhongGioiHan:
    """Hồ sơ quyền xem được tất cả — tách phần phạm vi ra khỏi phép đếm."""


@pytest.fixture()
def ctx(db, seed):
    company = db.get(Company, seed.company_id)
    company.issue_code = "DEGO"
    doc_type = DocType(code="QD", name="Quyết định", id_scheme=2, number_when=2)
    db.add(doc_type)
    db.commit()
    return {"QD": doc_type, "seed": seed}


def _tao(db, ctx, title: str, ban_hanh: bool = False, **kwargs):
    seed = ctx["seed"]
    doc = service.create_document(db, DocumentCreate(
        doc_type_id=ctx["QD"].id, company_id=seed.company_id,
        department_id=seed.dept_id, owner_employee_id=seed.emp_req_id,
        title=title, content_html="<p>x</p>", **kwargs,
    ), ACTOR)
    if ban_hanh:
        service.submit(db, doc, ACTOR)
        service.approve(db, doc, ACTOR)
    return doc


def _overview(db, monkeypatch):
    #  `visible_condition` cần hồ sơ quyền thật; ở đây ta kiểm phép ĐẾM nên cho
    #  nó trả None = không giới hạn.
    from app.modules.document import access_service
    monkeypatch.setattr(access_service, "visible_condition", lambda user, profile: None)
    return dashboard_service.overview(db, None, _KhongGioiHan())


def test_bieu_do_luon_du_12_o_thang_ke_ca_thang_rong(db, ctx, monkeypatch):
    _tao(db, ctx, "Quyết định 1", ban_hanh=True)

    diem = _overview(db, monkeypatch)["issued_12m"]

    assert len(diem) == 12
    #  Ô cuối là tháng này, ô đầu là 11 tháng trước — trục không được nhảy cóc.
    assert diem[-1]["label"] == f"{date.today().month:02d}/{date.today().year}"
    assert sum(item["value"] for item in diem) == 1


def test_kpi_dem_dung_tung_nhom(db, ctx, monkeypatch):
    _tao(db, ctx, "Đã ban hành", ban_hanh=True)
    _tao(db, ctx, "Còn nháp")
    submitted_count = _tao(db, ctx, "Đang duyệt")
    service.submit(db, submitted_count, ACTOR)

    kpi = _overview(db, monkeypatch)["kpi"]

    assert kpi["effective"] == 1
    assert kpi["draft"] == 1
    assert kpi["submitted"] == 1


def test_dem_van_ban_sap_het_hieu_luc_trong_30_ngay(db, ctx, monkeypatch):
    sap_het = _tao(db, ctx, "Sắp hết hiệu lực", ban_hanh=True)
    sap_het.expire_date = date.today() + timedelta(days=10)
    con_lau = _tao(db, ctx, "Còn lâu mới hết", ban_hanh=True)
    con_lau.expire_date = date.today() + timedelta(days=200)
    db.commit()

    assert _overview(db, monkeypatch)["kpi"]["expiring"] == 1


def test_viec_can_xu_ly_bo_han_nhom_rong(db, ctx, monkeypatch):
    """Danh sách toàn số 0 làm loãng đúng dòng đang cần người xử lý."""
    submitted_count = _tao(db, ctx, "Đang duyệt")
    service.submit(db, submitted_count, ACTOR)

    task = _overview(db, monkeypatch)["todo"]

    assert [item["key"] for item in task] == ["submitted"]


def test_van_ban_can_ra_lai_len_dau_danh_sach_viec(db, ctx, monkeypatch):
    doc = _tao(db, ctx, "Cần rà lại", ban_hanh=True)
    doc.needs_review = True
    db.commit()

    task = _overview(db, monkeypatch)["todo"]

    assert task[0]["key"] == "needs_review"
    assert task[0]["tone"] == "warning"


def test_co_cau_theo_loai_xep_nhieu_nhat_len_truoc(db, ctx, monkeypatch):
    thong_bao = DocType(code="TB", name="Thông báo", id_scheme=2, number_when=2)
    db.add(thong_bao)
    db.commit()

    _tao(db, ctx, "Quyết định 1", ban_hanh=True)
    _tao(db, ctx, "Quyết định 2", ban_hanh=True)
    ctx["QD"] = thong_bao
    _tao(db, ctx, "Thông báo 1", ban_hanh=True)

    co_cau = _overview(db, monkeypatch)["by_type"]

    assert co_cau[0]["name"] == "Quyết định"
    assert co_cau[0]["value"] == 2
