"""duoc-CR-755 giai đoạn 01 — KIÊM NHIỆM thành bảng riêng, cho khác công ty: dữ liệu, dịch vụ, API, tệp.

Gọi thẳng hàm controller với vai trò THẬT cấp qua `world.grant(...)` (khuôn
`test_qua_trinh_cong_tac_quyen.py`). Mỗi chốt chặn có cặp đối chứng ở chiều ngược.
"""
import json
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import event

from app.core.auth import get_perm_profile, perm_cache_clear
from app.core.file_registry import FILE_POLICY, PRIVATE_ENTITIES
from app.core.hr_concurrent_codes import ConcurrentStatus, get_concurrent_status
from app.core.vn_time import vn_today
from app.modules.attachment import controller as ac
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.department.model import Department, DepartmentCompany
from app.modules.employee import concurrent_controller as cc
from app.modules.employee import concurrent_service
from app.modules.employee.concurrent_model import EmployeeConcurrent
from app.modules.employee.concurrent_schema import ConcurrentIn, ConcurrentPatch
from app.modules.employee.position_model import JobPosition

D = date(2026, 1, 1)


def _in(world, dept_key="B.kt", company_key="B", **kw) -> ConcurrentIn:
    base = dict(company_id=world.co[company_key], department_id=world.dept[dept_key], from_date=D)
    base.update(kw)
    return ConcurrentIn(**base)


def _body(resp) -> dict:
    return json.loads(resp.body)["data"]


def _writer(world, key="a1", scope="all", sensitive=False):
    actor = world.grant(key, "employee", scope=scope, actions=("read", "write"))
    if sensitive:
        actor.grant("employee_sensitive", scope="all", actions=("read",))
    return actor


def _shared_dept(world, code="SH") -> int:
    """Phòng dùng chung (company_id = 0) — 26/27 phòng prod."""
    row = Department(code=code, name="Phòng dùng chung", company_id=0, is_active=True)
    world.db.add(row)
    world.db.flush()
    return row.id


def _row(world, eid_key="a2", dept_key="B.kt", company_key="B", **kw) -> EmployeeConcurrent:
    row = EmployeeConcurrent(employee_id=world.emp[eid_key], company_id=world.co[company_key],
                             department_id=world.dept[dept_key], from_date=kw.pop("from_date", D), **kw)
    world.db.add(row)
    world.db.commit()
    return row


def _attach_fake_file(db, entity_id: int):
    f = StoredFile(filename="qd.pdf", file_key="k", url="u", content_type="application/pdf", size=1, sha256="s")
    db.add(f)
    db.flush()
    db.add(FileLink(file_id=f.id, entity="employee_concurrent", entity_id=entity_id, doc_type="", sort_order=0))
    db.commit()


# ── Tạo: khác công ty, phòng dùng chung, L3 ──────────────────────────────────

def test_tao_dong_khac_cong_ty_voi_phong_dung_chung_cung_id_phong_chinh(world):
    """Bảng cũ UNIQUE(employee, department) chặn ca này; bảng mới thì không."""
    shared = _shared_dept(world)
    world.db.get(__import__("app.modules.employee.model", fromlist=["Employee"]).Employee,
                 world.emp["a2"]).department_id = shared
    world.db.commit()
    a1 = _writer(world)

    resp = cc.create_concurrent(world.emp["a2"], ConcurrentIn(
        company_id=world.co["B"], department_id=shared, from_date=D), world.db, a1.user)
    assert resp.status_code == 201
    assert _body(resp)["item"]["department_id"] == shared
    assert _body(resp)["item"]["status"] == int(ConcurrentStatus.ACTIVE)


def test_trung_phong_chinh_va_cong_ty_chinh_bi_400(world):
    a1 = _writer(world)
    with pytest.raises(HTTPException) as e:
        cc.create_concurrent(world.emp["a2"], _in(world, "A.kt", "A"), world.db, a1.user)
    assert e.value.status_code == 400
    assert "Trùng phòng ban chính" in e.value.detail


def test_phong_khong_phuc_vu_cong_ty_bi_400_con_co_dong_phuc_vu_thi_qua(world):
    a1 = _writer(world)
    with pytest.raises(HTTPException) as e:
        cc.create_concurrent(world.emp["a2"], _in(world, "A.mua", "B"), world.db, a1.user)
    assert e.value.status_code == 400

    world.db.add(DepartmentCompany(department_id=world.dept["A.mua"], company_id=world.co["B"], is_active=True))
    world.db.commit()
    assert cc.create_concurrent(world.emp["a2"], _in(world, "A.mua", "B"), world.db, a1.user).status_code == 201


def test_dong_phuc_vu_cong_ty_da_tat_khong_tinh(world):
    world.db.add(DepartmentCompany(department_id=world.dept["A.mua"], company_id=world.co["B"], is_active=False))
    world.db.commit()
    a1 = _writer(world)
    with pytest.raises(HTTPException) as e:
        cc.create_concurrent(world.emp["a2"], _in(world, "A.mua", "B"), world.db, a1.user)
    assert e.value.status_code == 400


def test_cong_ty_hoac_phong_khong_ton_tai_bi_400(world):
    a1 = _writer(world)
    for kw in ({"company_id": 99999}, {"department_id": 99999}):
        with pytest.raises(HTTPException) as e:
            cc.create_concurrent(world.emp["a2"], _in(world, "B.kt", "B", **kw), world.db, a1.user)
        assert e.value.status_code == 400


# ── Chồng giai đoạn, trần ────────────────────────────────────────────────────

def test_chong_giai_doan_cung_phong_cong_ty_bi_409_ke_nhau_thi_qua(world):
    a1 = _writer(world)
    cc.create_concurrent(world.emp["a2"], _in(world, from_date=date(2026, 1, 1), to_date=date(2026, 3, 31)),
                         world.db, a1.user)
    with pytest.raises(HTTPException) as e:
        cc.create_concurrent(world.emp["a2"], _in(world, from_date=date(2026, 3, 31), to_date=date(2026, 6, 30)),
                             world.db, a1.user)
    assert e.value.status_code == 409
    #  Đối chứng: liền kề không chồng, và phòng khác thì không liên quan.
    assert cc.create_concurrent(world.emp["a2"], _in(world, from_date=date(2026, 4, 1)),
                                world.db, a1.user).status_code == 201
    assert cc.create_concurrent(world.emp["a2"], _in(world, "B.hc", "B", from_date=date(2026, 1, 1)),
                                world.db, a1.user).status_code == 201


def test_dong_mo_khong_ket_thuc_chong_moi_dong_ve_sau(world):
    a1 = _writer(world)
    cc.create_concurrent(world.emp["a2"], _in(world), world.db, a1.user)       # to_date trống
    with pytest.raises(HTTPException) as e:
        cc.create_concurrent(world.emp["a2"], _in(world, from_date=date(2030, 1, 1)), world.db, a1.user)
    assert e.value.status_code == 409


def test_tran_30_dong_moi_nguoi(world):
    for i in range(30):
        world.db.add(EmployeeConcurrent(employee_id=world.emp["a2"], company_id=world.co["B"],
                                        department_id=world.dept["B.kt"],
                                        from_date=date(2000, 1, 1) + timedelta(days=i * 2),
                                        to_date=date(2000, 1, 1) + timedelta(days=i * 2)))
    world.db.commit()
    a1 = _writer(world)
    with pytest.raises(HTTPException) as e:
        cc.create_concurrent(world.emp["a2"], _in(world, from_date=date(2026, 1, 1)), world.db, a1.user)
    assert e.value.status_code == 400
    assert "30" in e.value.detail


# ── Schema: giới hạn đầu vào ─────────────────────────────────────────────────

def test_schema_note_501_va_so_qd_51_ky_tu_la_422_khong_phai_500():
    for kw in ({"note": "x" * 501}, {"decision_no": "x" * 51}):
        with pytest.raises(ValidationError):
            ConcurrentIn(company_id=1, department_id=1, from_date=D, **kw)
    ConcurrentIn(company_id=1, department_id=1, from_date=D, note="x" * 500, decision_no="x" * 50)


def test_schema_ngay_ngoai_dai_den_truoc_tu_ngay_va_khoa_la():
    for kw in ({"from_date": date(1899, 12, 31)}, {"from_date": date(2101, 1, 1)},
               {"to_date": date(2025, 12, 31)}, {"company_id": 0}, {"department_id": 0}, {"khoa_la": 1}):
        with pytest.raises(ValidationError):
            ConcurrentIn(**{"company_id": 1, "department_id": 1, "from_date": D, **kw})
    with pytest.raises(ValidationError):
        ConcurrentIn(company_id=1, department_id=1)        # thiếu từ ngày


def test_schema_patch_chi_cho_null_to_date_va_decision_date():
    ConcurrentPatch.model_validate({"to_date": None, "decision_date": None})
    for key in ("note", "company_id", "from_date", "counts_scope", "decision_no"):
        with pytest.raises(ValidationError):
            ConcurrentPatch.model_validate({key: None})


# ── L1 / L2 ──────────────────────────────────────────────────────────────────

def test_l1_khong_tu_sua_kiem_nhiem_cua_chinh_minh_ke_ca_quan_tri(world):
    a1 = _writer(world)
    row = _row(world, "a1")
    for call in (
        lambda: cc.create_concurrent(world.emp["a1"], _in(world, "B.hc", "B"), world.db, a1.user),
        lambda: cc.update_concurrent(world.emp["a1"], row.id, ConcurrentPatch(note="x"), world.db, a1.user),
        lambda: cc.delete_concurrent(world.emp["a1"], row.id, world.db, a1.user),
    ):
        with pytest.raises(HTTPException) as e:
            call()
        assert e.value.status_code == 403
    #  Cờ can_edit của chính mình cũng tắt.
    assert _body(cc.list_concurrents(world.emp["a1"], world.db, a1.user))["can_edit"] is False


def test_l2_bac_phong_ban_o_a_khong_gan_duoc_cap_o_b(world):
    """Phòng A.kt có phục vụ B (L3 qua), nhưng người bậc `dept` ở A không với tới cặp (A.kt, B)."""
    world.db.add(DepartmentCompany(department_id=world.dept["A.kt"], company_id=world.co["B"], is_active=True))
    world.db.commit()
    a1 = _writer(world, scope="dept")
    with pytest.raises(HTTPException) as e:
        cc.create_concurrent(world.emp["a2"], _in(world, "A.kt", "B"), world.db, a1.user)
    assert e.value.status_code == 403
    assert "Phòng Kế toán" in e.value.detail


def test_l2_bac_phong_ban_van_gan_duoc_cap_cong_ty_chinh_cua_phong_minh(world):
    """Đối chứng: phòng dùng chung nằm trong dept_ids của a1 (kiêm nhiệm cùng công ty), cặp (shared, A) được."""
    shared = _shared_dept(world)
    world.db.add(EmployeeConcurrent(employee_id=world.emp["a1"], company_id=world.co["A"],
                                    department_id=shared, from_date=D))
    world.db.commit()
    a1 = _writer(world, scope="dept")
    assert shared in a1.profile()["dept_ids"]
    resp = cc.create_concurrent(world.emp["a2"], ConcurrentIn(
        company_id=world.co["A"], department_id=shared, from_date=D), world.db, a1.user)
    assert resp.status_code == 201
    #  ...nhưng cùng phòng đó ở công ty B thì không.
    with pytest.raises(HTTPException) as e:
        cc.create_concurrent(world.emp["a2"], ConcurrentIn(
            company_id=world.co["B"], department_id=shared, from_date=D), world.db, a1.user)
    assert e.value.status_code == 403


def test_l2_bac_cong_ty_a_gan_x_a_duoc_x_b_thi_403(world):
    shared = _shared_dept(world)
    a1 = _writer(world, scope="company")
    ok = cc.create_concurrent(world.emp["a2"], ConcurrentIn(
        company_id=world.co["A"], department_id=shared, from_date=D), world.db, a1.user)
    assert ok.status_code == 201
    with pytest.raises(HTTPException) as e:
        cc.create_concurrent(world.emp["a2"], ConcurrentIn(
            company_id=world.co["B"], department_id=shared, from_date=D), world.db, a1.user)
    assert e.value.status_code == 403


def test_l2_o_phong_ban_duoc_xem_chi_phu_cong_ty_chinh(world):
    """`inc.department` không mang công ty → chỉ phủ công ty chính của người thao tác."""
    shared = _shared_dept(world)
    a1 = world.grant("a1", "employee", scope="dept", actions=("read", "write"), inc_dept=[shared])
    ok = cc.create_concurrent(world.emp["a2"], ConcurrentIn(
        company_id=world.co["A"], department_id=shared, from_date=D), world.db, a1.user)
    assert ok.status_code == 201
    with pytest.raises(HTTPException) as e:
        cc.create_concurrent(world.emp["a2"], ConcurrentIn(
            company_id=world.co["B"], department_id=shared, from_date=D), world.db, a1.user)
    assert e.value.status_code == 403


def test_l2_dung_concurrent_pairs_khi_phase_02_dien(world):
    from app.modules.employee import department_service as dv
    profile = {"grants": [{"perms": {"employee": {"write": True, "scope": "dept"}}, "scope": {}}],
               "company_id": world.co["A"], "dept_ids": [world.dept["A.kt"]], "dept_id": world.dept["A.kt"],
               "concurrent_pairs": [[world.dept["B.kt"], world.co["B"]]]}
    assert dv.pair_in_write_scope(world.db, profile, world.dept["B.kt"], world.co["B"]) is True
    assert dv.pair_in_write_scope(world.db, profile, world.dept["B.hc"], world.co["B"]) is False


def test_khong_co_quyen_ghi_thi_khong_gan_cap_nao(world):
    from app.modules.employee import department_service as dv
    assert dv.pair_in_write_scope(world.db, {"grants": []}, world.dept["A.kt"], world.co["A"]) is False


def test_sua_doi_cap_do_ca_cap_cu_lan_cap_moi(world):
    """Dời dòng từ (B.kt,B) sang (B.hc,B): người chỉ phủ B.hc không dời được dòng của B.kt."""
    row = _row(world, "a2", "B.kt", "B")
    profile = {"grants": [{"perms": {"employee": {"write": True, "scope": "dept"}}, "scope": {}}],
               "company_id": world.co["B"], "dept_ids": [world.dept["B.hc"]], "dept_id": world.dept["B.hc"]}
    emp = world.db.get(__import__("app.modules.employee.model", fromlist=["Employee"]).Employee, world.emp["a2"])
    actor = SimpleNamespace(id=1, employee_id=0)
    with pytest.raises(HTTPException) as e:
        concurrent_service.update_concurrent(world.db, emp, row.id, ConcurrentPatch(department_id=world.dept["B.hc"]),
                                             actor, profile)
    assert e.value.status_code == 403


# ── Sửa tại chỗ, xóa, IDOR ───────────────────────────────────────────────────

def test_sua_tai_cho_giu_id_va_tep_quyet_dinh_dong_thoi_ghi_lai_nhan_chuc_vu(world):
    a1 = _writer(world, sensitive=True)
    created = _body(cc.create_concurrent(world.emp["a2"], _in(world, note="a"), world.db, a1.user))["item"]
    _attach_fake_file(world.db, created["id"])
    pos = JobPosition(code="cv-tp", name="Trưởng phòng", is_active=True)
    world.db.add(pos)
    world.db.commit()

    out = _body(cc.update_concurrent(world.emp["a2"], created["id"],
                                     ConcurrentPatch(position_id=pos.id, note="b", to_date=date(2026, 12, 31)),
                                     world.db, a1.user))["item"]
    assert out["id"] == created["id"] and out["file_count"] == 1
    assert out["position_label"] == "Trưởng phòng" and out["note"] == "b"
    #  Mở lại bằng null tường minh.
    reopened = _body(cc.update_concurrent(world.emp["a2"], created["id"],
                                          ConcurrentPatch.model_validate({"to_date": None}),
                                          world.db, a1.user))["item"]
    assert reopened["to_date"] is None


def test_chuc_vu_ngung_dung_chan_gan_moi_nhung_giu_khi_sua_o_khac(world):
    a1 = _writer(world)
    pos = JobPosition(code="cv-x", name="Chức vụ cũ", is_active=True)
    world.db.add(pos)
    world.db.commit()
    row_id = _body(cc.create_concurrent(world.emp["a2"], _in(world, position_id=pos.id), world.db, a1.user))["item"]["id"]
    pos.is_active = False
    world.db.commit()
    #  Sửa ô khác: vẫn lưu được, nhãn giữ nguyên.
    out = _body(cc.update_concurrent(world.emp["a2"], row_id, ConcurrentPatch(note="ok"), world.db, a1.user))["item"]
    assert out["position_label"] == "Chức vụ cũ"
    #  Gán mới chức vụ đã ngừng: chặn.
    with pytest.raises(HTTPException) as e:
        cc.create_concurrent(world.emp["a2"], _in(world, "B.hc", "B", position_id=pos.id), world.db, a1.user)
    assert e.value.status_code == 400


def test_sua_ghep_ngay_cu_va_moi_den_ngay_truoc_tu_ngay_la_422(world):
    a1 = _writer(world)
    row = _row(world, "a2", from_date=date(2026, 5, 1))
    with pytest.raises(HTTPException) as e:
        cc.update_concurrent(world.emp["a2"], row.id, ConcurrentPatch(to_date=date(2026, 4, 1)), world.db, a1.user)
    assert e.value.status_code == 422


def test_cid_cua_nguoi_khac_qua_eid_trong_pham_vi_la_404(world):
    a1 = _writer(world)
    other = _row(world, "a3")
    for call in (
        lambda: cc.update_concurrent(world.emp["a2"], other.id, ConcurrentPatch(note="x"), world.db, a1.user),
        lambda: cc.delete_concurrent(world.emp["a2"], other.id, world.db, a1.user),
    ):
        with pytest.raises(HTTPException) as e:
            call()
        assert e.value.status_code == 404


def test_ngoai_pham_vi_ho_so_la_404_chu_khong_403(world):
    a1 = _writer(world, scope="dept")
    with pytest.raises(HTTPException) as e:
        cc.list_concurrents(world.emp["a3"], world.db, a1.user)
    assert e.value.status_code == 404


def test_xoa_dong_co_tep_thieu_nhay_cam_la_403_du_nhay_cam_thi_xoa_ca_tep(world):
    row = _row(world, "a2")
    _attach_fake_file(world.db, row.id)
    a1 = _writer(world)
    with pytest.raises(HTTPException) as e:
        cc.delete_concurrent(world.emp["a2"], row.id, world.db, a1.user)
    assert e.value.status_code == 403 and "nhạy cảm" in e.value.detail

    a1.grant("employee_sensitive", scope="all", actions=("read",))
    assert cc.delete_concurrent(world.emp["a2"], row.id, world.db, a1.user).status_code == 200
    assert world.db.query(EmployeeConcurrent).count() == 0
    assert world.db.query(FileLink).filter(FileLink.entity == "employee_concurrent").count() == 0


def test_xoa_ho_so_don_dong_kiem_nhiem_va_tep(world):
    row = _row(world, "a2")
    _attach_fake_file(world.db, row.id)
    _row(world, "a3")
    concurrent_service.delete_all_of(world.db, world.emp["a2"])
    world.db.commit()
    assert [r.employee_id for r in world.db.query(EmployeeConcurrent).all()] == [world.emp["a3"]]
    assert world.db.query(FileLink).filter(FileLink.entity == "employee_concurrent").count() == 0


# ── Tệp quyết định ───────────────────────────────────────────────────────────

def test_entity_tep_quyet_dinh_da_khai_va_la_rieng_tu():
    assert FILE_POLICY["employee_concurrent"][0] == "employee"
    assert "employee_concurrent" in PRIVATE_ENTITIES


def test_tep_cua_nguoi_khac_thieu_nhay_cam_la_403_chinh_chu_doc_duoc(world):
    row = _row(world, "a2")
    a1 = world.grant("a1", "employee", scope="company", actions=("read", "write"))
    with pytest.raises(HTTPException) as e:
        ac._check(world.db, a1.user, "employee_concurrent", "read", row.id)
    assert e.value.status_code == 403
    #  Chính chủ (a2 có tài khoản, không cần employee.read).
    me = world.actor("a2").user
    assert ac._check(world.db, me, "employee_concurrent", "read", row.id)
    #  ...nhưng không tự gắn / gỡ tệp của mình.
    with pytest.raises(HTTPException) as e2:
        ac._check(world.db, me, "employee_concurrent", "manage", row.id)
    assert e2.value.status_code == 403


def test_gan_go_tep_can_ghi_dung_pham_vi_va_cap_phu_dung(world):
    row = _row(world, "a2", "B.kt", "B")
    a1 = _writer(world, scope="dept", sensitive=True)
    a1.grant("employee_sensitive", scope="all", actions=("read",))
    #  a2 ở phòng A.kt cùng phòng a1 (trong phạm vi hồ sơ) nhưng cặp (B.kt, B) ngoài tầm ghi của a1.
    with pytest.raises(HTTPException) as e:
        ac._check(world.db, a1.user, "employee_concurrent", "manage", row.id)
    assert e.value.status_code == 403
    #  Quản trị phạm vi tất cả thì qua.
    boss = world.grant("a3", "employee", scope="all", actions=("read", "write"))
    boss.grant("employee_sensitive", scope="all", actions=("read",))
    assert ac._check(world.db, boss.user, "employee_concurrent", "manage", row.id)


# ── Đọc: danh sách, trạng thái, tương thích ──────────────────────────────────

def test_trang_thai_dan_xuat_theo_ngay_vn_bien_bao_gom():
    today = date(2026, 6, 15)
    assert get_concurrent_status(date(2026, 6, 16), None, today) == ConcurrentStatus.UPCOMING
    assert get_concurrent_status(date(2026, 6, 15), date(2026, 6, 15), today) == ConcurrentStatus.ACTIVE
    assert get_concurrent_status(None, date(2026, 6, 14), today) == ConcurrentStatus.ENDED
    assert get_concurrent_status(None, None, today) == ConcurrentStatus.ACTIVE


def test_danh_sach_tra_so_nhan_ten_dem_tep_va_co_quyen(world):
    t = vn_today()
    a1 = _writer(world)
    _row(world, "a2", "B.kt", "B", from_date=t - timedelta(days=10), to_date=t - timedelta(days=1))
    cur = _row(world, "a2", "B.hc", "B", from_date=t - timedelta(days=1))
    _row(world, "a2", "B.kt", "B", from_date=t + timedelta(days=5))
    _attach_fake_file(world.db, cur.id)

    data = _body(cc.list_concurrents(world.emp["a2"], world.db, a1.user))
    assert [i["status"] for i in data["items"]] == [1, 2, 3]            # mới nhất trước
    assert [i["status_label"] for i in data["items"]] == ["Sắp tới", "Đang hiệu lực", "Đã hết"]
    item = data["items"][1]
    assert item["company_name"] == "Công ty B" and item["department_name"] == "Phòng Hành chính"
    assert item["file_count"] == 1
    assert data["can_edit"] is True and data["can_open_files"] is False


def test_get_departments_cu_van_tra_phong_kiem_nhiem_cung_cong_ty_hieu_luc(world):
    from app.modules.employee import controller as ctl
    a1 = _writer(world)
    t = vn_today()
    _row(world, "a2", "A.mua", "A")                                                     # cùng công ty, hiệu lực
    _row(world, "a2", "B.kt", "B")                                                      # khác công ty
    _row(world, "a2", "A.mua", "A", from_date=t - timedelta(days=9), to_date=t - timedelta(days=5))  # hết hạn
    out = _body(ctl.list_employee_departments(world.emp["a2"], world.db, a1.user))
    assert out["primary_department_id"] == world.dept["A.kt"]
    assert out["extra_department_ids"] == [world.dept["A.mua"]]
    assert not hasattr(ctl, "set_employee_departments"), "PUT /departments đã gỡ"


# ── Hồ sơ quyền ──────────────────────────────────────────────────────────────

def test_ho_so_quyen_dong_cung_cong_ty_vao_dept_ids_khac_cong_ty_chua_vao(world):
    """Phase 01: dòng cùng công ty chính nối vào dept_ids; dòng khác công ty bỏ qua (phase 02)."""
    a1 = world.grant("a1", "employee", scope="dept", actions=("read",))
    _row(world, "a1", "A.mua", "A")
    _row(world, "a1", "B.hc", "B")
    perm_cache_clear(a1.user.id)
    ids = get_perm_profile(world.db, a1.user)["dept_ids"]
    assert ids == [world.dept["A.kt"], world.dept["A.mua"]]


def test_ho_so_quyen_so_truy_van_khong_doi_theo_so_dong(world):
    a1 = world.grant("a1", "employee", scope="dept", actions=("read",))
    engine = world.db.get_bind()
    count = {"n": 0}

    def _tick(*_a, **_k):
        count["n"] += 1

    def _measure() -> int:
        perm_cache_clear(a1.user.id)
        world.db.expire_all()
        count["n"] = 0
        event.listen(engine, "before_cursor_execute", _tick)
        try:
            get_perm_profile(world.db, a1.user)
        finally:
            event.remove(engine, "before_cursor_execute", _tick)
        return count["n"]

    base = _measure()
    t = vn_today()
    for i in range(5):
        world.db.add(EmployeeConcurrent(employee_id=world.emp["a1"], company_id=world.co["A"],
                                        department_id=world.dept["A.mua"], from_date=t - timedelta(days=100 + i * 3),
                                        to_date=t - timedelta(days=99 + i * 3) if i else None))
    world.db.commit()
    assert _measure() == base


def test_tao_sua_xoa_xoa_cache_quyen_cua_tai_khoan_gan_nhan_su(world):
    boss = _writer(world, key="a3")
    a1_user = world.actor("a1").user
    world.grant("a1", "employee", scope="dept", actions=("read",))
    assert get_perm_profile(world.db, a1_user)["dept_ids"] == [world.dept["A.kt"]]       # nạp cache

    resp = cc.create_concurrent(world.emp["a1"], _in(world, "A.mua", "A"), world.db, boss.user)
    cid = _body(resp)["item"]["id"]
    assert get_perm_profile(world.db, a1_user)["dept_ids"] == [world.dept["A.kt"], world.dept["A.mua"]]
    cc.update_concurrent(world.emp["a1"], cid, ConcurrentPatch(counts_scope=False), world.db, boss.user)
    assert get_perm_profile(world.db, a1_user)["dept_ids"] == [world.dept["A.kt"]]
    cc.update_concurrent(world.emp["a1"], cid, ConcurrentPatch(counts_scope=True), world.db, boss.user)
    assert len(get_perm_profile(world.db, a1_user)["dept_ids"]) == 2
    cc.delete_concurrent(world.emp["a1"], cid, world.db, boss.user)
    assert get_perm_profile(world.db, a1_user)["dept_ids"] == [world.dept["A.kt"]]
