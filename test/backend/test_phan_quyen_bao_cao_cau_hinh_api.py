"""Phase 03 — `/api/report-access` (GET danh sách, POST cấp, DELETE thu hồi).

Canh: gác `role.read`/`role.write`; GET đủ 13 mục đúng thứ tự khóa, không có
dòng thu hồi; POST trùng chủ thể+effect -> updated; chủ thể không tồn tại ->
skipped; khóa lạ -> 404; trần 500 ký tự của `reason` (ValidationError, không
tin SQLite); DELETE lần 2 -> 400; có audit; `/auth/me` có `report_keys` khớp
`viewable_keys`.
"""
import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.report_keys import ReportKey
from app.core.subject_match import (SUBJECT_COMPANY, SUBJECT_DEPARTMENT, SUBJECT_EMPLOYEE,
                                    SUBJECT_ROLE)
from app.main import app
from app.modules.audit.model import AuditLog
from app.modules.report_access.model import ReportAccess
from app.modules.report_access.schema import ReportAccessGrantIn, ReportAccessRevokeIn
from app.modules.report_access.service import viewable_keys
from app.modules.role.model import Role
from app.modules.user.model import User, UserRole

ROOT = "/api/report-access"


@pytest.fixture
def client_as(db):
    """Xem chú thích dài ở `test_phan_quyen_bao_cao_gac_duong.client_as` — token
    GIẢ nhưng DUY NHẤT mỗi lần build để tránh dính `ReportSummaryCacheMiddleware`
    (không áp cho `/api/report-access` nhưng giữ đồng bộ thói quen trong bộ test
    này, phòng khi route cache mở rộng allowlist)."""
    def build(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield build
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _viewer(db, seed, cap_quyen, **actions):
    v = db.query(User).filter(User.employee_id == seed.emp_tp_id).one()
    cap_quyen(v.id, "role", scope="all", **actions)
    return v


def test_get_can_role_read_khong_co_403(db, seed, cap_quyen, client_as):
    v = db.query(User).filter(User.employee_id == seed.emp_tp_id).one()
    resp = client_as(v).get(ROOT)
    assert resp.status_code == 403


def test_post_delete_can_role_write(db, seed, cap_quyen, client_as, gan_bao_cao):
    reader = _viewer(db, seed, cap_quyen, read=True)
    resp = client_as(reader).post(f"{ROOT}/{int(ReportKey.DOCUMENT)}/grants",
                                  json={"subjects": [{"subject_kind": SUBJECT_COMPANY,
                                                      "subject_id": seed.company_id}],
                                       "effect": 1, "reason": "x"})
    assert resp.status_code == 403

    rows = gan_bao_cao(SUBJECT_COMPANY, seed.company_id, ReportKey.DOCUMENT)
    resp = client_as(reader).request("DELETE", f"{ROOT}/grants/{rows[0].id}", json={"reason": "x"})
    assert resp.status_code == 403


def test_get_tra_du_13_muc_dung_thu_tu_khong_co_dong_thu_hoi(db, seed, cap_quyen, client_as,
                                                              gan_bao_cao):
    reader = _viewer(db, seed, cap_quyen, read=True)
    rows = gan_bao_cao(SUBJECT_COMPANY, seed.company_id, ReportKey.DOCUMENT)
    revoked = rows[0]
    revoked.revoked_at = datetime.now()
    db.commit()

    resp = client_as(reader).get(ROOT)
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert len(items) == 13
    assert [it["key"] for it in items] == [int(k) for k in ReportKey]
    doc_item = next(it for it in items if it["key"] == int(ReportKey.DOCUMENT))
    assert doc_item["label"] and doc_item["group"]
    assert doc_item["grants"] == []   # dòng vừa thu hồi không được trả


def test_get_hien_ten_chu_the(db, seed, cap_quyen, client_as, gan_bao_cao):
    reader = _viewer(db, seed, cap_quyen, read=True)
    gan_bao_cao(SUBJECT_COMPANY, seed.company_id, ReportKey.HR_HEADCOUNT)
    resp = client_as(reader).get(ROOT)
    item = next(it for it in resp.json()["data"] if it["key"] == int(ReportKey.HR_HEADCOUNT))
    assert item["grants"][0]["subject_name"]


def test_post_trung_chu_the_cung_effect_thi_update_khong_de_them_dong(db, seed, cap_quyen,
                                                                       client_as):
    writer = _viewer(db, seed, cap_quyen, read=True, write=True)
    client = client_as(writer)
    #  Chủ thể là NHÂN SỰ KHÁC (không phải writer) — writer cùng pháp nhân với
    #  `seed.company_id` nên gán pháp nhân đó cho CHÍNH MÌNH giờ bị M3(b) chặn (403).
    body = {"subjects": [{"subject_kind": SUBJECT_EMPLOYEE, "subject_id": seed.emp_nstm_id}],
           "effect": 1, "reason": "lần 1"}
    r1 = client.post(f"{ROOT}/{int(ReportKey.LEAVE_USAGE)}/grants", json=body)
    assert r1.status_code == 200 and r1.json()["data"] == {"created": 1, "updated": 0, "skipped": []}

    body["reason"] = "lần 2"
    r2 = client.post(f"{ROOT}/{int(ReportKey.LEAVE_USAGE)}/grants", json=body)
    assert r2.json()["data"] == {"created": 0, "updated": 1, "skipped": []}

    rows = client.get(ROOT).json()["data"]
    item = next(it for it in rows if it["key"] == int(ReportKey.LEAVE_USAGE))
    assert len(item["grants"]) == 1 and item["grants"][0]["reason"] == "lần 2"


def test_post_chu_the_khong_ton_tai_bi_skip(db, seed, cap_quyen, client_as):
    writer = _viewer(db, seed, cap_quyen, read=True, write=True)
    resp = client_as(writer).post(
        f"{ROOT}/{int(ReportKey.WORK)}/grants",
        json={"subjects": [{"subject_kind": SUBJECT_EMPLOYEE, "subject_id": 999999}],
             "effect": 1, "reason": "x"})
    assert resp.status_code == 200
    assert resp.json()["data"] == {"created": 0, "updated": 0,
                                   "skipped": [{"subject_kind": SUBJECT_EMPLOYEE,
                                               "subject_id": 999999,
                                               "reason": "Không tìm thấy đối tượng"}]}


def test_post_khoa_la_404(db, seed, cap_quyen, client_as):
    writer = _viewer(db, seed, cap_quyen, read=True, write=True)
    resp = client_as(writer).post(f"{ROOT}/999/grants",
                                  json={"subjects": [{"subject_kind": SUBJECT_COMPANY,
                                                      "subject_id": seed.company_id}],
                                       "effect": 1})
    assert resp.status_code == 404


@pytest.mark.parametrize("payload,why", [
    ({"subjects": [], "effect": 1}, "rỗng"),
    ({"subjects": [{"subject_kind": SUBJECT_COMPANY, "subject_id": i} for i in range(1, 202)],
     "effect": 1}, "201 phần tử"),
])
def test_post_so_luong_chu_the_ngoai_dai_422(db, seed, cap_quyen, client_as, payload, why):
    writer = _viewer(db, seed, cap_quyen, read=True, write=True)
    resp = client_as(writer).post(f"{ROOT}/{int(ReportKey.WORK)}/grants", json=payload)
    assert resp.status_code == 422, why


def test_post_subject_kind_va_effect_sai_dai_422(db, seed, cap_quyen, client_as):
    writer = _viewer(db, seed, cap_quyen, read=True, write=True)
    client = client_as(writer)
    r1 = client.post(f"{ROOT}/{int(ReportKey.WORK)}/grants",
                     json={"subjects": [{"subject_kind": 9, "subject_id": 1}], "effect": 1})
    assert r1.status_code == 422
    r2 = client.post(f"{ROOT}/{int(ReportKey.WORK)}/grants",
                     json={"subjects": [{"subject_kind": SUBJECT_COMPANY, "subject_id": 1}],
                          "effect": 3})
    assert r2.status_code == 422


def test_reason_501_ky_tu_nem_validation_error_khong_tin_sqlite():
    with pytest.raises(ValidationError):
        ReportAccessGrantIn(subjects=[{"subject_kind": SUBJECT_COMPANY, "subject_id": 1}],
                           effect=1, reason="x" * 501)
    with pytest.raises(ValidationError):
        ReportAccessRevokeIn(reason="x" * 501)


def test_delete_lan_2_tra_400_dong_con_trong_db_voi_revoked_at(db, seed, cap_quyen, client_as,
                                                                gan_bao_cao):
    writer = _viewer(db, seed, cap_quyen, read=True, write=True)
    rows = gan_bao_cao(SUBJECT_COMPANY, seed.company_id, ReportKey.APPROVAL)
    access_id = rows[0].id
    client = client_as(writer)

    #  `TestClient.delete()` (httpx) không nhận `json=` — gọi qua `.request("DELETE", ...)`.
    r1 = client.request("DELETE", f"{ROOT}/grants/{access_id}", json={"reason": "thu hồi"})
    assert r1.status_code == 200

    r2 = client.request("DELETE", f"{ROOT}/grants/{access_id}", json={"reason": "lần nữa"})
    assert r2.status_code == 400

    from app.modules.report_access.model import ReportAccess
    row = db.get(ReportAccess, access_id)
    assert row.revoked_at is not None and row.revoke_reason == "thu hồi"


def test_audit_co_dong_sau_post_va_delete(db, seed, cap_quyen, client_as):
    writer = _viewer(db, seed, cap_quyen, read=True, write=True)
    client = client_as(writer)
    #  Chủ thể là NHÂN SỰ KHÁC — cùng lý do với test trùng chủ thể ở trên (writer cùng
    #  pháp nhân `seed.company_id` nên không gán được pháp nhân đó cho chính mình, M3(b)).
    resp = client.post(f"{ROOT}/{int(ReportKey.SEAL_REQUEST)}/grants",
                       json={"subjects": [{"subject_kind": SUBJECT_EMPLOYEE,
                                          "subject_id": seed.emp_nstm_id}],
                            "effect": 1, "reason": "test audit"})
    access_id = resp.json()["data"]
    #  POST không trả id trực tiếp -> tra lại danh sách để lấy id vừa tạo.
    item = next(it for it in client.get(ROOT).json()["data"]
                if it["key"] == int(ReportKey.SEAL_REQUEST))
    gid = item["grants"][0]["id"]
    client.request("DELETE", f"{ROOT}/grants/{gid}", json={"reason": "x"})

    logs = db.query(AuditLog).filter(AuditLog.entity == "report_access").all()
    assert len(logs) == 2
    assert {log.action for log in logs} == {"update"}


def test_auth_me_co_report_keys_khop_viewable_keys(db, seed, cap_quyen, client_as, gan_bao_cao):
    v = db.query(User).filter(User.employee_id == seed.emp_tp_id).one()
    gan_bao_cao(SUBJECT_EMPLOYEE, seed.emp_tp_id, ReportKey.DOCUMENT, ReportKey.WORK)

    resp = client_as(v).get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["data"]["report_keys"] == sorted(viewable_keys(db, v))
    assert resp.json()["data"]["report_keys"] == [int(ReportKey.DOCUMENT), int(ReportKey.WORK)]


#  ── M3(a) — CẤM không áp được lên vai trò Quản trị hệ thống ─────────────────────────

@pytest.mark.parametrize("admin_code", ["admin", "ADMINISTRATOR"])
def test_post_cam_vai_tro_quan_tri_tra_400_khong_de_dong(db, seed, cap_quyen, client_as,
                                                           admin_code):
    writer = _viewer(db, seed, cap_quyen, read=True, write=True)
    admin_role = Role(code=admin_code, name="Quản trị hệ thống")
    db.add(admin_role)
    db.commit()

    resp = client_as(writer).post(f"{ROOT}/{int(ReportKey.WORK)}/grants",
                                  json={"subjects": [{"subject_kind": SUBJECT_ROLE,
                                                      "subject_id": admin_role.id}],
                                       "effect": 2, "reason": "x"})
    assert resp.status_code == 400
    assert db.query(ReportAccess).count() == 0   # không đẻ dòng CẤM nào


def test_post_cho_phep_vai_tro_quan_tri_khong_bi_chan_boi_luat_cam(db, seed, cap_quyen, client_as):
    """Chốt M3(a) chỉ xét chiều CẤM — CHO PHÉP lên vai trò admin (vd lúc đại ca tự cấu
    hình lại sau khi seed) không bị chặn bởi chốt này."""
    writer = _viewer(db, seed, cap_quyen, read=True, write=True)
    admin_role = Role(code="admin", name="Quản trị hệ thống")
    db.add(admin_role)
    db.commit()

    resp = client_as(writer).post(f"{ROOT}/{int(ReportKey.WORK)}/grants",
                                  json={"subjects": [{"subject_kind": SUBJECT_ROLE,
                                                      "subject_id": admin_role.id}],
                                       "effect": 1, "reason": "x"})
    assert resp.status_code == 200


#  ── M3(b) — không TỰ gán CHO PHÉP cho chính mình ─────────────────────────────────────

def test_post_khong_tu_gan_cho_phep_cho_chinh_minh_nhan_su(db, seed, cap_quyen, client_as):
    writer = _viewer(db, seed, cap_quyen, read=True, write=True)
    resp = client_as(writer).post(f"{ROOT}/{int(ReportKey.WORK)}/grants",
                                  json={"subjects": [{"subject_kind": SUBJECT_EMPLOYEE,
                                                      "subject_id": seed.emp_tp_id}],
                                       "effect": 1, "reason": "x"})
    assert resp.status_code == 403
    assert db.query(ReportAccess).count() == 0


def test_post_khong_tu_gan_cho_phep_cho_phong_ban_cua_minh(db, seed, cap_quyen, client_as):
    writer = _viewer(db, seed, cap_quyen, read=True, write=True)
    resp = client_as(writer).post(f"{ROOT}/{int(ReportKey.WORK)}/grants",
                                  json={"subjects": [{"subject_kind": SUBJECT_DEPARTMENT,
                                                      "subject_id": seed.dept_id}],
                                       "effect": 1, "reason": "x"})
    assert resp.status_code == 403


def test_post_khong_tu_gan_cho_phep_cho_phap_nhan_cua_minh(db, seed, cap_quyen, client_as):
    writer = _viewer(db, seed, cap_quyen, read=True, write=True)
    resp = client_as(writer).post(f"{ROOT}/{int(ReportKey.WORK)}/grants",
                                  json={"subjects": [{"subject_kind": SUBJECT_COMPANY,
                                                      "subject_id": seed.company_id}],
                                       "effect": 1, "reason": "x"})
    assert resp.status_code == 403


def test_post_khong_tu_gan_cho_phep_cho_vai_tro_minh_dang_giu(db, seed, cap_quyen, client_as):
    writer = db.query(User).filter(User.employee_id == seed.emp_tp_id).one()
    role = cap_quyen(writer.id, "role", scope="all", read=True, write=True)

    resp = client_as(writer).post(f"{ROOT}/{int(ReportKey.WORK)}/grants",
                                  json={"subjects": [{"subject_kind": SUBJECT_ROLE,
                                                      "subject_id": role.id}],
                                       "effect": 1, "reason": "x"})
    assert resp.status_code == 403


def test_post_cam_cho_chinh_minh_khong_bi_chan_boi_luat_tu_gan(db, seed, cap_quyen, client_as):
    """M3(b) chỉ chặn chiều CHO PHÉP — CẤM cho chính mình không mở rộng được gì (vẫn qua
    `require`/`apply_scope`), nên không cần chặn."""
    writer = _viewer(db, seed, cap_quyen, read=True, write=True)
    resp = client_as(writer).post(f"{ROOT}/{int(ReportKey.WORK)}/grants",
                                  json={"subjects": [{"subject_kind": SUBJECT_EMPLOYEE,
                                                      "subject_id": seed.emp_tp_id}],
                                       "effect": 2, "reason": "x"})
    assert resp.status_code == 200


def test_post_admin_tu_gan_cho_phep_cho_chinh_minh_khong_bi_chan(db, seed, cap_quyen, client_as):
    """Ngoại lệ bao-CR-523 — Quản trị hệ thống được miễn L1."""
    writer = db.query(User).filter(User.employee_id == seed.emp_tp_id).one()
    admin_role = Role(code="admin", name="Quản trị hệ thống")
    db.add(admin_role)
    db.flush()
    db.add(UserRole(user_id=writer.id, role_id=admin_role.id))
    db.flush()
    cap_quyen(writer.id, "role", scope="all", read=True, write=True)

    resp = client_as(writer).post(f"{ROOT}/{int(ReportKey.WORK)}/grants",
                                  json={"subjects": [{"subject_kind": SUBJECT_EMPLOYEE,
                                                      "subject_id": seed.emp_tp_id}],
                                       "effect": 1, "reason": "x"})
    assert resp.status_code == 200


#  ── M4 — audit ghi rõ kiểu + tên chủ thể, `entity_id` của thu hồi là `access_id` ───────

def test_audit_grant_ghi_kieu_va_ten_chu_the(db, seed, cap_quyen, client_as):
    writer = _viewer(db, seed, cap_quyen, read=True, write=True)
    #  Pháp nhân RIÊNG, khác `seed.company_id` của writer — gán pháp nhân của CHÍNH MÌNH
    #  giờ bị M3(b) chặn (403), nên test tên chủ thể trong audit cần một pháp nhân khác.
    from app.modules.company.model import Company
    other_co = Company(name="Cty Khác", code="CTKHAC", is_active=True)
    db.add(other_co)
    db.commit()

    resp = client_as(writer).post(f"{ROOT}/{int(ReportKey.WORK)}/grants",
                                  json={"subjects": [{"subject_kind": SUBJECT_COMPANY,
                                                      "subject_id": other_co.id}],
                                       "effect": 1, "reason": "x"})
    assert resp.status_code == 200

    log = db.query(AuditLog).filter(AuditLog.entity == "report_access",
                                    AuditLog.entity_id == int(ReportKey.WORK)).one()
    assert "Pháp nhân" in log.message        # SUBJECT_LABELS[SUBJECT_COMPANY]
    assert "Cty Khác" in log.message          # tên pháp nhân thật, không chỉ số đếm


def test_audit_revoke_ghi_entity_id_la_access_id_va_ten_chu_the(db, seed, cap_quyen, client_as,
                                                                  gan_bao_cao):
    writer = _viewer(db, seed, cap_quyen, read=True, write=True)
    rows = gan_bao_cao(SUBJECT_COMPANY, seed.company_id, ReportKey.WORK)
    access_id = rows[0].id

    client_as(writer).request("DELETE", f"{ROOT}/grants/{access_id}", json={"reason": "x"})

    log = db.query(AuditLog).filter(AuditLog.entity == "report_access",
                                    AuditLog.entity_id == access_id).one()
    assert log.entity_id == access_id          # KHÔNG phải report_key (lỗi cũ)
    assert "Pháp nhân" in log.message
    assert "Cty Test" in log.message
    assert "Công việc" in log.message          # nhãn báo cáo WORK


#  ── M5/Low — dải năm + trần `subject_id` của schema (gọi thẳng, không HTTP) ────────────

def test_valid_to_qua_khu_nem_validation_error():
    with pytest.raises(ValidationError):
        ReportAccessGrantIn(subjects=[{"subject_kind": SUBJECT_COMPANY, "subject_id": 1}],
                           effect=1, valid_to=date.today() - timedelta(days=1))


def test_valid_to_truoc_valid_from_nem_validation_error():
    with pytest.raises(ValidationError):
        ReportAccessGrantIn(subjects=[{"subject_kind": SUBJECT_COMPANY, "subject_id": 1}],
                           effect=1, valid_from=date.today() + timedelta(days=10),
                           valid_to=date.today() + timedelta(days=5))


@pytest.mark.parametrize("field,year", [("valid_from", 1), ("valid_to", 9999)])
def test_valid_nam_ngoai_dai_hop_le_nem_validation_error(field, year):
    with pytest.raises(ValidationError):
        ReportAccessGrantIn(subjects=[{"subject_kind": SUBJECT_COMPANY, "subject_id": 1}],
                           effect=1, **{field: date(year, 1, 1)})


def test_subject_id_vuot_tran_bigint_nem_validation_error():
    with pytest.raises(ValidationError):
        ReportAccessGrantIn(subjects=[{"subject_kind": SUBJECT_COMPANY, "subject_id": 2**63}],
                           effect=1)


@pytest.mark.parametrize("bad_id", [0, -1])
def test_subject_id_khong_duong_nem_validation_error(bad_id):
    with pytest.raises(ValidationError):
        ReportAccessGrantIn(subjects=[{"subject_kind": SUBJECT_COMPANY, "subject_id": bad_id}],
                           effect=1)
