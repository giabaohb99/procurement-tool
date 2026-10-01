"""Phase 05 mục 5.4 — Báo cáo Phê duyệt (`GET /api/approvals/summary` + `/export`). Canh:
thiếu quyền 1 loại chứng từ -> biến mất; `visible_condition=None` không lọc thành 0 (M5);
"Đang chờ" đúng TẠI MỐC kể cả kỳ quá khứ (M2); SONG SONG đo từ lúc bước mở, bỏ task tự-
qua/đã hủy (M6); số truy vấn CỐ ĐỊNH.
"""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.auth import get_current_user, get_perm_profile
from app.core.database import get_db
from app.core.report_period import parse_period
from app.main import app
from app.modules.approval import report_service as svc
from app.modules.approval.instance_model import (INSTANCE_APPROVED, TASK_SKIPPED_DUPLICATE,
                                                  ApprovalInstance, ApprovalTask)
from app.modules.doc_catalog.model import DocType
from app.modules.document.model import Document
from app.modules.seal_request.model import SEAL_APPROVED, SealRequest
from app.modules.user.model import User

IN_PERIOD = datetime(2026, 3, 10, 3, 0, 0)

def _instance(db, *, entity: str, entity_id: int, started_at=IN_PERIOD, finished_at=None,
             status=INSTANCE_APPROVED, flow_id=1) -> ApprovalInstance:
    i = ApprovalInstance(entity=entity, entity_id=entity_id, flow_id=flow_id, status=status,
                        started_at=started_at, finished_at=finished_at)
    db.add(i)
    db.flush()
    return i

def _task(db, *, instance_id: int, node_seq: int, assignee_employee_id: int, decided_at=None,
         due_at=None, node_name="", status=None) -> ApprovalTask:
    kw = {"status": status} if status is not None else {}
    t = ApprovalTask(instance_id=instance_id, node_seq=node_seq,
                     assignee_employee_id=assignee_employee_id, decided_at=decided_at,
                     due_at=due_at, node_name=node_name, **kw)
    db.add(t)
    db.flush()
    return t

def _seal_request(db, *, company_id: int, department_id: int, requester_id: int) -> SealRequest:
    r = SealRequest(code=f"SR-{requester_id}-{department_id}", status=SEAL_APPROVED,
                    company_id=company_id, department_id=department_id,
                    requester_id=requester_id)
    db.add(r)
    db.flush()
    return r

def _period(d_from="2026-03-01", d_to="2026-03-31", compare="none"):
    return parse_period({"preset": "custom", "date_from": d_from, "date_to": d_to, "compare": compare})

def _build(db, user, group_by=None, **period_kw):
    profile = get_perm_profile(db, user)
    return svc.build_summary(db, user, profile, _period(**period_kw), group_by)

def _viewer(db, seed, cap_quyen, **grants):
    v = db.query(User).filter(User.employee_id == seed.emp_tp_id).one()
    for entity, kw in grants.items():
        cap_quyen(v.id, entity, **kw)
    return v

_AF = dict(scope="all", read=True, export=True)   # grant chuẩn cho `approval_flow`

def test_thieu_quyen_mot_loai_bien_mat(db, seed, cap_quyen):
    """Q5.4: thiếu quyền đọc MỘT loại chứng từ -> phiên loại đó biến mất, có ghi chú."""
    sr = _seal_request(db, company_id=seed.company_id, department_id=seed.dept_id,
                       requester_id=seed.emp_req_id)
    db.flush()
    _instance(db, entity="document", entity_id=999999)          # KHÔNG có document.read
    _instance(db, entity="seal_request", entity_id=sr.id)        # CÓ seal_request.read
    db.commit()
    #  CỐ Ý không cấp `document` — đúng ca "có approval_flow.read nhưng không có document.read".
    viewer = _viewer(db, seed, cap_quyen, approval_flow=_AF, seal_request=dict(scope="all", read=True))
    data = _build(db, viewer, group_by="entity")
    assert data["totals"]["current"]["sessions"] == 1          # chỉ seal_request
    assert "document" not in [g["key"] for g in (data["groups"] or [])]
    assert "Văn bản" in " ".join(data["notes"])                 # có ghi chú giải thích vì sao thiếu

def test_khong_quyen_doc_loai_nao_thi_ve_khong_khong_loi(db, seed, cap_quyen):
    """Không có quyền đọc BẤT KỲ loại chứng từ nào — vẫn phải trả 0, không ném lỗi."""
    _instance(db, entity="seal_request", entity_id=1)
    db.commit()
    viewer = _viewer(db, seed, cap_quyen, approval_flow=_AF)
    assert _build(db, viewer)["totals"]["current"]["sessions"] == 0

def test_quyen_doc_van_ban_scope_all_van_dem_dung_phien(db, seed, cap_quyen):
    """M5: `visible_condition=None` (scope `all`) không lọc thành 0 — thiếu guard thì phiên
    Văn bản luôn đếm ra 0 dù đã cấp đủ quyền đọc."""
    dt = DocType(code="QCX", name="Loại X", id_scheme=2, number_when=2)
    db.add(dt)
    db.flush()
    doc = Document(origin=1, doc_type_id=dt.id, company_id=seed.company_id,
                   owner_employee_id=seed.emp_req_id, title="VB test",
                   created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(doc)
    db.flush()
    _instance(db, entity="document", entity_id=doc.id)
    db.commit()
    viewer = _viewer(db, seed, cap_quyen, approval_flow=_AF, document=dict(scope="all", read=True))
    assert _build(db, viewer)["totals"]["current"]["sessions"] == 1

def test_buoc_tuan_tu_tinh_tu_luc_buoc_lien_truoc_quyet_dinh(db, seed, cap_quyen):
    sr = _seal_request(db, company_id=seed.company_id, department_id=seed.dept_id,
                       requester_id=seed.emp_req_id)
    db.flush()
    step1_decided = datetime(2026, 3, 10, 5, 0, 0)    # +2h từ lúc bắt đầu phiên
    step2_decided = datetime(2026, 3, 10, 8, 0, 0)    # +3h từ lúc bước 1 quyết — KHÔNG phải từ start
    inst = _instance(db, entity="seal_request", entity_id=sr.id, finished_at=step2_decided)
    _task(db, instance_id=inst.id, node_seq=1, assignee_employee_id=seed.emp_tp_id,
         decided_at=step1_decided, node_name="Trưởng phòng duyệt")
    _task(db, instance_id=inst.id, node_seq=2, assignee_employee_id=seed.emp_nstm_id,
         decided_at=step2_decided, node_name="Văn thư đóng dấu")
    db.commit()
    viewer = _viewer(db, seed, cap_quyen, approval_flow=_AF, seal_request=dict(scope="all", read=True))
    totals = _build(db, viewer)["totals"]["current"]
    #  (2h bước 1, từ start 03:00->05:00) + (3h bước 2, TỪ LÚC bước 1 quyết 05:00->08:00) = TB 2.5h.
    assert totals["avg_step_hours"] == 2.5
    assert totals["avg_proc_hours"] == 5.0   # cả phiên: finished (08:00) - started (03:00) = 5h

def test_buoc_song_song_do_tu_luc_mo_va_bo_task_tu_qua(db, seed, cap_quyen):
    """M6: hai task CÙNG bước (song song) đo từ lúc MỞ, không từ nhau; tự-qua-vì-trùng bị loại."""
    sr = _seal_request(db, company_id=seed.company_id, department_id=seed.dept_id,
                       requester_id=seed.emp_req_id)
    db.flush()
    a_decided = datetime(2026, 3, 10, 5, 0, 0)    # +2h từ start
    b_decided = datetime(2026, 3, 10, 7, 0, 0)    # +4h từ start — KHÔNG tính từ a_decided
    inst = _instance(db, entity="seal_request", entity_id=sr.id, finished_at=b_decided)
    _task(db, instance_id=inst.id, node_seq=1, assignee_employee_id=seed.emp_tp_id, decided_at=a_decided)
    _task(db, instance_id=inst.id, node_seq=1, assignee_employee_id=seed.emp_nstm_id, decided_at=b_decided)
    _task(db, instance_id=inst.id, node_seq=1, assignee_employee_id=seed.emp_backup_id,
         decided_at=datetime(2026, 3, 10, 4, 0, 0), status=TASK_SKIPPED_DUPLICATE)
    db.commit()
    viewer = _viewer(db, seed, cap_quyen, approval_flow=_AF, seal_request=dict(scope="all", read=True))
    data = _build(db, viewer, group_by="approver")
    assert data["totals"]["current"]["avg_step_hours"] == 3.0   # (2h + 4h, cả hai từ start) / 2
    approver_keys = {g["key"] for g in data["groups"]}
    assert str(seed.emp_backup_id) not in approver_keys          # tự-qua-vì-trùng bị loại
    assert {str(seed.emp_tp_id), str(seed.emp_nstm_id)} <= approver_keys

def test_dang_cho_o_ky_qua_khu_tinh_dung_tai_moc(db, seed, cap_quyen):
    """M2: "Đang chờ" ở kỳ QUÁ KHỨ dựa vào MỐC thời gian, không phải trạng thái hiện tại."""
    sr = _seal_request(db, company_id=seed.company_id, department_id=seed.dept_id,
                       requester_id=seed.emp_req_id)
    db.commit()
    #  Mở trong kỳ, xong TRƯỚC mốc cuối kỳ -> không còn "đang chờ" tại mốc đó.
    _instance(db, entity="seal_request", entity_id=sr.id, started_at=datetime(2026, 3, 5),
             finished_at=datetime(2026, 3, 10))
    #  Mở trong kỳ, xong SAU mốc cuối kỳ -> vẫn "đang chờ" TẠI mốc đó dù nay đã có kết quả.
    _instance(db, entity="seal_request", entity_id=sr.id, started_at=datetime(2026, 3, 20),
             finished_at=datetime(2026, 4, 5))
    _instance(db, entity="seal_request", entity_id=sr.id, started_at=datetime(2026, 4, 2))  # mở SAU kỳ
    db.commit()
    viewer = _viewer(db, seed, cap_quyen, approval_flow=_AF, seal_request=dict(scope="all", read=True))
    assert _build(db, viewer)["totals"]["current"]["pending"] == 1

@pytest.fixture
def client_as(db):
    def build(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app)

    yield build
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)

def test_summary_tra_200_khong_bi_id_nuot_va_export_ra_xlsx(db, seed, cap_quyen, client_as):
    client = client_as(_viewer(db, seed, cap_quyen, approval_flow=_AF))
    resp = client.get("/api/approvals/summary?preset=this_month&compare=none")
    assert resp.status_code == 200   # `/{instance_id}: int` sẽ ra 422 nếu bị nuốt
    assert "period" in resp.json()["data"] and "totals" in resp.json()["data"]

    resp2 = client.get("/api/approvals/summary/export?preset=this_month&compare=none")
    assert resp2.status_code == 200
    assert "spreadsheet" in resp2.headers["content-type"]

def test_khong_co_quyen_approval_flow_thi_403(db, seed, client_as):
    v = db.query(User).filter(User.employee_id == seed.emp_tp_id).one()
    assert client_as(v).get("/api/approvals/summary").status_code == 403

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

def _seed_n_instances(db, seed, n: int, sr_id: int):
    for _ in range(n):
        inst = _instance(db, entity="seal_request", entity_id=sr_id)
        _task(db, instance_id=inst.id, node_seq=1, assignee_employee_id=seed.emp_tp_id,
             decided_at=datetime(2026, 3, 10, 5, 0, 0))
    db.commit()

def test_so_truy_van_co_dinh_khong_tang_theo_so_phien(db, seed, cap_quyen):
    sr = _seal_request(db, company_id=seed.company_id, department_id=seed.dept_id,
                       requester_id=seed.emp_req_id)
    db.commit()
    viewer = _viewer(db, seed, cap_quyen, approval_flow=_AF, seal_request=dict(scope="all", read=True))
    profile = get_perm_profile(db, viewer)
    period = _period()
    _seed_n_instances(db, seed, 5, sr.id)
    n5 = _dem_truy_van(db, lambda: svc.build_summary(db, viewer, profile, period, None))
    _seed_n_instances(db, seed, 45, sr.id)   # tổng 50
    n50 = _dem_truy_van(db, lambda: svc.build_summary(db, viewer, profile, period, None))
    assert n5 == n50, f"5 phiên = {n5} truy vấn, 50 phiên = {n50} truy vấn — phải BẰNG NHAU"
