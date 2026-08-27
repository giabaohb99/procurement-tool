"""MA TRẬN ƯU TIÊN và BỘ LỌC của trang tổng quan Văn thư.

Trục "khẩn cấp" đọc từ `urgency` của từng văn bản, còn trục "quan trọng" đọc từ
**cờ của LOẠI** (`needs_approval` / `needs_decision`) — `tab_document` không có
cột nào tên là "quan trọng". Bài kiểm canh đúng chỗ ghép hai nguồn đó lại, vì
ghép sai thì bốn con số vẫn cộng đủ tổng và không ai phát hiện ra.
"""
from datetime import date, timedelta

import pytest

from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import dashboard_service, service
from app.modules.document.dashboard_service import DashboardFilters
from app.modules.document.model import STATUS_EFFECTIVE
from app.modules.document.schema import DocumentCreate

ACTOR = 1


def _profile():
    """Hồ sơ quyền xem TẤT CẢ — bài này kiểm bộ lọc, không kiểm phạm vi quyền."""
    perms = {a: True for a in ("read", "create", "write", "delete",
                               "approve", "cancel", "print", "export")}
    perms["scope"] = "all"
    return {
        "grants": [{"role_id": 1, "perms": {"document": perms},
                    "scope": {"inc": {}, "exc": {}}}],
        "company_id": 0, "dept_id": 0, "dept_name": "",
        "employee_id": 0, "emp_code": "", "emp_name": "",
    }


@pytest.fixture()
def catalog(db, seed):
    company = db.get(Company, seed.company_id)
    company.issue_code = "DEGO"

    #  Quy chế phải qua duyệt → QUAN TRỌNG. Giấy mời thì không cờ nào → thường.
    regulation = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2,
                      needs_approval=True)
    giay_moi = DocType(code="GM", name="Giấy mời", id_scheme=2, number_when=2)
    #  Cờ "cần QĐ ban hành" cũng đủ để tính là quan trọng, không cần duyệt.
    decision = DocType(code="QD", name="Quyết định", id_scheme=2, number_when=2,
                         needs_decision=True)
    db.add_all([regulation, giay_moi, decision])
    db.commit()
    return {"QC": regulation, "GM": giay_moi, "QD": decision, "seed": seed}


def _tao_hieu_luc(db, catalog, code: str, title: str, urgency: int = 1,
                  department_id: int | None = None):
    """Tạo rồi đưa thẳng lên trạng thái CÓ HIỆU LỰC — ma trận chỉ đếm mức đó."""
    seed = catalog["seed"]
    doc = service.create_document(db, DocumentCreate(
        doc_type_id=catalog[code].id, company_id=seed.company_id,
        department_id=department_id if department_id is not None else seed.dept_id,
        owner_employee_id=seed.emp_req_id, title=title,
        content_html="<p>Nội dung</p>", urgency=urgency,
    ), ACTOR)
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)
    return doc


def _ma_tran(db, filters: DashboardFilters | None = None):
    return dashboard_service.overview(db, None, _profile(), filters)["priority_matrix"]


def test_bon_o_chia_dung_theo_co_cua_loai_va_do_khan(db, catalog):
    _tao_hieu_luc(db, catalog, "QC", "Quy chế hỏa tốc", urgency=3)
    _tao_hieu_luc(db, catalog, "QC", "Quy chế thường", urgency=1)
    _tao_hieu_luc(db, catalog, "GM", "Giấy mời khẩn", urgency=2)
    _tao_hieu_luc(db, catalog, "GM", "Giấy mời thường", urgency=1)

    assert _ma_tran(db) == {
        "important_urgent": 1,
        "important_normal": 1,
        "normal_urgent": 1,
        "normal_normal": 1,
    }


def test_co_can_qd_ban_hanh_cung_tinh_la_quan_trong(db, catalog):
    """Hai cờ, chỉ cần MỘT là đủ — loại Quyết định không có cờ «cần duyệt»."""
    seed = catalog["seed"]
    doc = service.create_document(db, DocumentCreate(
        doc_type_id=catalog["QD"].id, company_id=seed.company_id,
        department_id=seed.dept_id, owner_employee_id=seed.emp_req_id,
        title="Quyết định bổ nhiệm", content_html="<p>x</p>", urgency=1,
    ), ACTOR)
    #  Đặt trạng thái thẳng tay: loại có cờ `needs_decision` không ban hành được
    #  nếu chưa khai quan hệ «Kèm theo» tới một Quyết định (chốt ở
    #  `issue_service`). Bài này kiểm việc CHIA Ô, không kiểm cổng ban hành —
    #  dựng thêm cả một Quyết định nữa chỉ để đi qua cổng là làm bài kiểm đỏ
    #  mỗi khi cổng đó đổi.
    doc.status = STATUS_EFFECTIVE
    db.commit()

    assert _ma_tran(db)["important_normal"] == 1
    assert _ma_tran(db)["normal_normal"] == 0


def test_muc_khan_1_khong_tinh_la_khan_cap(db, catalog):
    """Ranh giới đúng ở mức 2: «Thường» không phải việc gấp."""
    _tao_hieu_luc(db, catalog, "QC", "Quy chế mức 1", urgency=1)
    _tao_hieu_luc(db, catalog, "QC", "Quy chế mức 2", urgency=2)

    assert _ma_tran(db) == {
        "important_urgent": 1,
        "important_normal": 1,
        "normal_urgent": 0,
        "normal_normal": 0,
    }


def test_ban_nhap_khong_vao_ma_tran(db, catalog):
    """Chỉ đếm văn bản CÒN HIỆU LỰC — nháp chưa áp dụng cho ai."""
    seed = catalog["seed"]
    service.create_document(db, DocumentCreate(
        doc_type_id=catalog["QC"].id, company_id=seed.company_id,
        department_id=seed.dept_id, owner_employee_id=seed.emp_req_id,
        title="Quy chế còn nháp", content_html="<p>x</p>", urgency=3,
    ), ACTOR)

    assert _ma_tran(db) == {
        "important_urgent": 0, "important_normal": 0,
        "normal_urgent": 0, "normal_normal": 0,
    }


def test_loc_theo_phap_nhan_thi_o_khac_khong_dem(db, catalog):
    _tao_hieu_luc(db, catalog, "QC", "Quy chế của pháp nhân A", urgency=2)
    other = catalog["seed"].company_id + 999

    assert _ma_tran(db, DashboardFilters(company_id=other)) == {
        "important_urgent": 0, "important_normal": 0,
        "normal_urgent": 0, "normal_normal": 0,
    }
    assert _ma_tran(db, DashboardFilters(company_id=catalog["seed"].company_id)) == {
        "important_urgent": 1, "important_normal": 0,
        "normal_urgent": 0, "normal_normal": 0,
    }


def test_loc_khoang_ngay_lay_ca_van_ban_lap_trong_chinh_ngay_cuoi(db, catalog):
    """`created_at` là DATETIME — so trần với `to_date` là mất cả ngày hôm đó.

    Lỗi kinh điển: chọn "Hôm nay" mà văn bản vừa lập lúc 09:00 không hiện, vì
    09:00 > 00:00 của chính ngày đó.
    """
    _tao_hieu_luc(db, catalog, "QC", "Quy chế lập hôm nay", urgency=2)
    today = date.today()

    assert _ma_tran(db, DashboardFilters(from_date=today, to_date=today)) == {
        "important_urgent": 1, "important_normal": 0,
        "normal_urgent": 0, "normal_normal": 0,
    }


def test_khoang_ngay_khong_chua_hom_nay_thi_rong(db, catalog):
    _tao_hieu_luc(db, catalog, "QC", "Quy chế lập hôm nay", urgency=2)
    hom_qua = date.today() - timedelta(days=1)

    assert _ma_tran(db, DashboardFilters(from_date=hom_qua - timedelta(days=6),
                                         to_date=hom_qua))["important_urgent"] == 0


def test_bieu_do_12_thang_khong_bi_khoang_ngay_cat(db, catalog):
    """Biểu đồ 12 tháng tự khai cửa sổ của nó; lọc chồng lên là cắt cụt cột cũ."""
    _tao_hieu_luc(db, catalog, "QC", "Quy chế đã ban hành", urgency=1)
    today = date.today()

    data = dashboard_service.overview(
        db, None, _profile(), DashboardFilters(from_date=today, to_date=today)
    )
    assert sum(diem["value"] for diem in data["issued_12m"]) == 1
