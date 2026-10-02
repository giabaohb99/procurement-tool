"""Phase 05 mục 5.3 — Báo cáo Văn bản (`GET /api/documents/summary` + `/export`). Canh: chặn
đích danh/cá nhân/Nháp không vào số nào; `/summary` không bị `/{id}` nuốt; số truy vấn CỐ
ĐỊNH; lọc `company_id` (422 nếu sai định dạng); nhóm theo ID (không theo TÊN, tránh trùng).
"""
import uuid
from datetime import date, datetime

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.auth import get_current_user, get_perm_profile
from app.core.database import get_db
from app.core.report_keys import ReportKey
from app.core.report_period import parse_period
from app.core.subject_match import SUBJECT_ROLE
from app.main import app
from app.modules.department.model import Department
from app.modules.doc_catalog.model import DocType
from app.modules.document import report_service as svc
from app.modules.document.access_model import EFFECT_DENY, SUBJECT_EMPLOYEE, DocumentAccess
from app.modules.document.model import (STATUS_DRAFT, STATUS_EFFECTIVE, STATUS_SUBMITTED,
                                        Document)
from app.modules.user.model import User

IN_PERIOD = datetime(2026, 3, 10, 3, 0, 0)     # 10h sáng giờ VN — chắc chắn trong kỳ
OUT_PERIOD = datetime(2025, 1, 1, 3, 0, 0)

def _doc_type(db, code: str, **kw) -> DocType:
    t = DocType(code=code, name=kw.pop("name", f"Loại {code}"), id_scheme=2, number_when=2, **kw)
    db.add(t)
    db.flush()
    return t

def _doc(db, *, doc_type: DocType, company_id: int, department_id: int, owner_id: int,
        created_by: int, created_at=IN_PERIOD, status=STATUS_EFFECTIVE, **kw) -> Document:
    d = Document(origin=1, doc_type_id=doc_type.id, company_id=company_id,
                department_id=department_id, owner_employee_id=owner_id,
                title=kw.pop("title", "Văn bản test"), status=status, created_at=created_at,
                created_by=created_by, updated_by=created_by, **kw)
    db.add(d)
    db.flush()
    return d

def _period(d_from="2026-03-01", d_to="2026-03-31", compare="none"):
    return parse_period({"preset": "custom", "date_from": d_from, "date_to": d_to, "compare": compare})

def _totals(db, user, group_by=None, company_id=None, **period_kw):
    profile = get_perm_profile(db, user)
    return svc.build_summary(db, user, profile, _period(**period_kw), group_by, company_id)

def _viewer(db, seed, cap_quyen, gan_bao_cao=None, scope="all"):
    """`gan_bao_cao` TÙY CHỌN — chỉ bài gọi qua HTTP thật (`client_as`) mới cần,
    vì `require_report` (phase 02) gác ở `dependencies=[...]` của route, bài
    gọi thẳng `svc.build_summary` không đi qua route nên không bị ảnh hưởng."""
    v = db.query(User).filter(User.employee_id == seed.emp_tp_id).one()
    role = cap_quyen(v.id, "document", scope=scope, read=True, export=True)
    if gan_bao_cao:
        gan_bao_cao(SUBJECT_ROLE, role.id, ReportKey.DOCUMENT)
    return v

def test_van_ban_bi_cam_dich_danh_khong_vao_so_nao(db, seed, cap_quyen):
    """Cấm đích danh thắng cả phạm vi vai trò `all` (luật đầu `access_service.py`);
    Nháp (`STATUS_DRAFT`) cũng không tính vào báo cáo này (review mục 6)."""
    dt = _doc_type(db, "QC1")
    _doc(db, doc_type=dt, company_id=seed.company_id, department_id=seed.dept_id,
        owner_id=seed.emp_req_id, created_by=seed.u_req_id)                       # thấy được
    blocked = _doc(db, doc_type=dt, company_id=seed.company_id, department_id=seed.dept_id,
                   owner_id=seed.emp_req_id, created_by=seed.u_req_id)            # sẽ bị cấm
    _doc(db, doc_type=dt, company_id=seed.company_id, department_id=seed.dept_id,
        owner_id=seed.emp_req_id, created_by=seed.u_req_id, status=STATUS_DRAFT)  # Nháp
    db.commit()
    viewer = _viewer(db, seed, cap_quyen)
    db.add(DocumentAccess(document_id=blocked.id, subject_kind=SUBJECT_EMPLOYEE,
                          subject_id=seed.emp_tp_id, effect=EFFECT_DENY, can_read=True))
    db.commit()

    data = _totals(db, viewer, group_by="doc_type")
    assert data["totals"]["current"]["created"] == 1
    #  Khóa nhóm là ID (chuỗi hóa bởi `bucket_rows`), không phải TÊN (review M4).
    group = next(g for g in data["groups"] if g["key"] == str(dt.id))
    assert group["label"] == dt.name and group["current"]["created"] == 1

def test_van_ban_ca_nhan_khong_phai_cua_minh_khong_vao_so(db, seed, cap_quyen):
    """`is_personal=True`: phạm vi HẸP chỉ thấy văn bản mình có chân trong đó."""
    personal_type = _doc_type(db, "NP1", is_personal=True)
    normal_type = _doc_type(db, "QC2")
    other_user = db.query(User).filter(User.employee_id == seed.emp_nstm_id).one()
    _doc(db, doc_type=personal_type, company_id=seed.company_id, department_id=seed.dept_id,
        owner_id=seed.emp_nstm_id, created_by=other_user.id)
    _doc(db, doc_type=normal_type, company_id=seed.company_id, department_id=seed.dept_id,
        owner_id=seed.emp_nstm_id, created_by=other_user.id)
    db.commit()

    #  CỐ Ý scope="dept" (không phải "all") để nhánh văn bản cá nhân có hiệu lực.
    viewer = _viewer(db, seed, cap_quyen, scope="dept")
    assert _totals(db, viewer)["totals"]["current"]["created"] == 1   # chỉ văn bản THƯỜNG

def test_cho_duyet_va_het_han_trong_ky_la_chi_so_thoi_diem(db, seed, cap_quyen):
    dt = _doc_type(db, "QC3")
    _doc(db, doc_type=dt, company_id=seed.company_id, department_id=seed.dept_id,
        owner_id=seed.emp_req_id, created_by=seed.u_req_id, status=STATUS_SUBMITTED)
    expiring = _doc(db, doc_type=dt, company_id=seed.company_id, department_id=seed.dept_id,
                    owner_id=seed.emp_req_id, created_by=seed.u_req_id, status=STATUS_EFFECTIVE)
    expiring.expire_date = date(2026, 3, 20)
    issued = _doc(db, doc_type=dt, company_id=seed.company_id, department_id=seed.dept_id,
                 owner_id=seed.emp_req_id, created_by=seed.u_req_id, status=STATUS_EFFECTIVE,
                 created_at=OUT_PERIOD)   # lập NGOÀI kỳ nhưng BAN HÀNH trong kỳ
    issued.issued_at = datetime(2026, 3, 15, 3, 0, 0)
    db.commit()

    totals = _totals(db, _viewer(db, seed, cap_quyen))["totals"]["current"]
    assert totals["pending"] == 1
    assert totals["expiring"] == 1
    assert totals["issued"] == 1   # tính theo issued_at, KHÔNG theo created_at

def test_loc_theo_company_id_va_sai_dinh_dang_422(db, seed, cap_quyen):
    dt = _doc_type(db, "QC5")
    other_company = seed.company_id + 999
    _doc(db, doc_type=dt, company_id=seed.company_id, department_id=seed.dept_id,
        owner_id=seed.emp_req_id, created_by=seed.u_req_id)
    _doc(db, doc_type=dt, company_id=other_company, department_id=seed.dept_id,
        owner_id=seed.emp_req_id, created_by=seed.u_req_id)
    db.commit()

    viewer = _viewer(db, seed, cap_quyen)
    assert _totals(db, viewer, company_id=seed.company_id)["totals"]["current"]["created"] == 1
    assert _totals(db, viewer)["totals"]["current"]["created"] == 2   # không lọc -> cả hai
    with pytest.raises(HTTPException) as exc:
        _totals(db, viewer, company_id="abc")
    assert exc.value.status_code == 422

def test_hai_phong_trung_ten_khac_id_khong_gop_nham(db, seed, cap_quyen):
    """M4: hai phòng CÙNG TÊN, KHÁC id — không được gộp làm một nhóm."""
    dup_name = db.get(Department, seed.dept_id).name
    other_dept = Department(code="DEPT-DUP", name=dup_name, company_id=seed.company_id,
                            is_active=True)
    db.add(other_dept)
    db.flush()
    dt = _doc_type(db, "QC6")
    _doc(db, doc_type=dt, company_id=seed.company_id, department_id=seed.dept_id,
        owner_id=seed.emp_req_id, created_by=seed.u_req_id)
    _doc(db, doc_type=dt, company_id=seed.company_id, department_id=other_dept.id,
        owner_id=seed.emp_req_id, created_by=seed.u_req_id)
    db.commit()

    data = _totals(db, _viewer(db, seed, cap_quyen), group_by="department")
    assert len(data["groups"]) == 2   # không gộp dù cùng NHÃN
    assert {g["label"] for g in data["groups"]} == {dup_name}
    assert all(g["current"]["created"] == 1 for g in data["groups"])

@pytest.fixture
def client_as(db):
    """⚠️ Token Bearer GIẢ nhưng DUY NHẤT mỗi lần build — `ReportSummaryCacheMiddleware`
    (gói A2) cache GET `/summary` qua Redis thật theo khóa `(path, query,
    sha256(token))`; không có header thì MỌI bài test (và mọi tệp khác) chia
    cùng khóa (token rỗng), một bài trả 200 làm bài kế ăn lại đúng response cũ
    — kể cả khi KHÔNG còn quyền (`require_report` bị bỏ qua hẳn vì cache HIT
    không đụng tới route)."""
    def build(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield build
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)

def test_summary_tra_200_khong_bi_id_nuot(db, seed, cap_quyen, client_as, gan_bao_cao):
    resp = client_as(_viewer(db, seed, cap_quyen, gan_bao_cao)).get("/api/documents/summary?preset=this_month&compare=none")
    assert resp.status_code == 200   # `/{document_id}: int` sẽ ra 422 nếu bị nuốt
    assert "period" in resp.json()["data"] and "totals" in resp.json()["data"]

def test_summary_export_tra_file_xlsx(db, seed, cap_quyen, client_as, gan_bao_cao):
    resp = client_as(_viewer(db, seed, cap_quyen, gan_bao_cao)).get("/api/documents/summary/export?preset=this_month&compare=none")
    assert resp.status_code == 200
    assert "spreadsheet" in resp.headers["content-type"]

def test_khong_co_quyen_export_thi_403(db, seed, cap_quyen, client_as):
    v = db.query(User).filter(User.employee_id == seed.emp_tp_id).one()
    cap_quyen(v.id, "document", scope="all", read=True, export=False)
    assert client_as(v).get("/api/documents/summary/export").status_code == 403

def _dem_truy_van(db, fn) -> int:
    counted: list[str] = []
    def _on_exec(conn, cursor, statement, *args):
        counted.append(statement)

    event.listen(db.get_bind(), "before_cursor_execute", _on_exec)
    try:
        fn()
    finally:
        event.remove(db.get_bind(), "before_cursor_execute", _on_exec)
    return len(counted)

def _seed_n_docs(db, seed, n: int, dt: DocType):
    for _ in range(n):
        _doc(db, doc_type=dt, company_id=seed.company_id, department_id=seed.dept_id,
            owner_id=seed.emp_req_id, created_by=seed.u_req_id)
    db.commit()

def test_so_truy_van_co_dinh_khong_tang_theo_so_van_ban(db, seed, cap_quyen):
    dt = _doc_type(db, "QC4")
    viewer = _viewer(db, seed, cap_quyen)
    profile = get_perm_profile(db, viewer)
    period = _period()

    _seed_n_docs(db, seed, 5, dt)
    n5 = _dem_truy_van(db, lambda: svc.build_summary(db, viewer, profile, period, None))
    _seed_n_docs(db, seed, 45, dt)   # tổng 50
    n50 = _dem_truy_van(db, lambda: svc.build_summary(db, viewer, profile, period, None))
    assert n5 == n50, f"5 văn bản = {n5} truy vấn, 50 văn bản = {n50} truy vấn — phải BẰNG NHAU"
