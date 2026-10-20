"""duoc-CR-656 (D1b) — task Dự án có loại việc, giờ ước lượng, giờ thực tế, kết quả; danh mục loại việc.

Luật cần giữ: giờ ngoài 0…999 → 422 · giờ thực tế chỉ khi xong · «Đạt» chỉ khi xong · «Phải làm lại» mở lại task, xóa
`completed_at` nhưng GIỮ kết quả đó cho tới khi xong lần nữa · chỉ người giao/quản lý đánh giá · danh mục (công ty, mã)
duy nhất · ghi danh mục cần `setting.write`.
"""
import uuid
from decimal import Decimal

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.auth import get_current_user
from app.core.capability_codes import WORK_TASK_OUTCOME_SET, WorkTaskOutcome
from app.core.database import get_db
from app.main import app
from app.modules.work import list_service, schema, task_outcome_service, task_service
from app.modules.work import task_type_service as types
from app.modules.work.membership_service import Actor
from app.modules.work.model import WorkMemberRole, WorkTaskStatus
from app.modules.work.task_model import WorkTask

from ho_so_lam_viec_factory import make_company, make_person

COMPANY = 1


@pytest.fixture()
def owner(db):
    return Actor(user_id=1, employee_id=11, company_id=COMPANY)


@pytest.fixture()
def member(db, owner, work_list):
    """Thành viên thường (vai MEMBER) — không phải người tạo task, không phải quản lý."""
    actor = Actor(user_id=2, employee_id=12, company_id=COMPANY)
    list_service.add_member(db, owner, work_list["id"],
                            schema.MemberIn(employee_id=12, role=int(WorkMemberRole.MEMBER)))
    return actor


@pytest.fixture()
def work_list(db, owner):
    return list_service.create_list(db, owner, schema.ListCreate(name="Thu mua"))


@pytest.fixture()
def type_a(db):
    return types.create_type(db, 1, schema.TaskTypeCreate(company_id=COMPANY, code="BAO_GIA", name="Báo giá NCC",
                                                          default_estimate_hours=Decimal("4")))


def _task(db, owner, list_id, **kw):
    return task_service.create_task(db, owner, schema.TaskCreate(list_id=list_id, title="Việc A", **kw))


def _upd(db, actor, task_id, **kw):
    return task_service.update_task(db, actor, task_id, schema.TaskUpdate(**kw))


def _done(db, owner, task_id):
    return _upd(db, owner, task_id, status=int(WorkTaskStatus.DONE))


# ── Mã ────────────────────────────────────────────────────────────────────────────────

def test_bo_ma_ket_qua_dang_ky_dung():
    assert [(c.value, c.label) for c in WORK_TASK_OUTCOME_SET.codes] == [("1", "Đạt"), ("2", "Phải làm lại")]
    assert int(WorkTaskOutcome.PASSED) == 1 and int(WorkTaskOutcome.REWORK) == 2


# ── Danh mục loại việc ────────────────────────────────────────────────────────────────

def test_danh_muc_trung_ma_trong_cung_cong_ty_bi_409(db, type_a):
    with pytest.raises(HTTPException) as e:
        types.create_type(db, 1, schema.TaskTypeCreate(company_id=COMPANY, code="BAO_GIA", name="Trùng"))
    assert e.value.status_code == 409
    #  Công ty khác dùng lại mã được.
    other = types.create_type(db, 1, schema.TaskTypeCreate(company_id=2, code="BAO_GIA", name="Báo giá"))
    assert other["id"] != type_a["id"]


def test_danh_muc_ma_va_ten_gioi_han_do_dai_o_schema():
    """SQLite không ép VARCHAR nên phải chặn ở schema (luật backend-input-limits)."""
    with pytest.raises(ValidationError):
        schema.TaskTypeCreate(code="x" * 31, name="a")
    with pytest.raises(ValidationError):
        schema.TaskTypeCreate(code="ok", name="y" * 121)


def test_xoa_loai_da_co_task_chi_tat_chua_dung_thi_xoa_han(db, owner, work_list, type_a):
    _task(db, owner, work_list["id"], task_type_id=type_a["id"])
    res = types.delete_type(db, 1, type_a["id"])
    assert res["deleted"] is False and res["task_count"] == 1
    assert types.list_types(db, is_active=True)["items"] == []                  # ẩn khỏi ô chọn
    assert [t["id"] for t in types.list_types(db)["items"]] == [type_a["id"]]    # màn quản trị vẫn thấy

    spare = types.create_type(db, 1, schema.TaskTypeCreate(company_id=COMPANY, code="KHAC", name="Khác"))
    assert types.delete_type(db, 1, spare["id"]) == {"deleted": True}


def test_loc_danh_muc_theo_cong_ty_gom_ca_loai_dung_chung(db):
    types.create_type(db, 1, schema.TaskTypeCreate(company_id=0, code="CHUNG", name="Dùng chung"))
    types.create_type(db, 1, schema.TaskTypeCreate(company_id=1, code="C1", name="Của 1"))
    types.create_type(db, 1, schema.TaskTypeCreate(company_id=2, code="C2", name="Của 2"))
    assert {t["code"] for t in types.list_types(db, company_id=1)["items"]} == {"CHUNG", "C1"}
    assert {t["code"] for t in types.list_types(db)["items"]} == {"CHUNG", "C1", "C2"}


def test_danh_muc_tim_kiem_sap_xep_va_phan_trang(db):
    for code, name in (("B", "Soạn hợp đồng"), ("A", "Báo giá"), ("C", "Đối soát")):
        types.create_type(db, 1, schema.TaskTypeCreate(company_id=1, code=code, name=name))
    page = types.list_types(db, sort_by="code", sort_dir="desc", page=1, page_size=2)
    assert page["total"] == 3 and [t["code"] for t in page["items"]] == ["C", "B"]
    assert [t["code"] for t in types.list_types(db, q="hợp")["items"]] == ["B"]
    assert [t["code"] for t in types.list_types(db, sort_by="khong_co_cot_nay")["items"]] == ["B", "A", "C"]   # theo sort_order, id


# ── Task: loại việc + giờ ─────────────────────────────────────────────────────────────

def test_tao_task_voi_loai_viec_va_gio_uoc_luong(db, owner, work_list, type_a):
    t = _task(db, owner, work_list["id"], task_type_id=type_a["id"], estimate_hours=Decimal("4.5"))
    assert (t["task_type_id"], t["task_type_name"]) == (type_a["id"], "Báo giá NCC")
    assert t["estimate_hours"] == "4.50" and t["actual_hours"] is None and t["outcome"] == 0


def test_task_cu_khong_doi_hanh_vi(db, owner, work_list):
    t = _task(db, owner, work_list["id"])
    assert (t["task_type_id"], t["task_type_name"], t["estimate_hours"], t["actual_hours"], t["outcome"]) == (0, "", None, None, 0)


@pytest.mark.parametrize("bad", ["-1", "1000", "1.234"])
def test_gio_ngoai_dai_la_422(bad):
    with pytest.raises(ValidationError):
        schema.TaskUpdate(estimate_hours=Decimal(bad))


def test_loai_viec_khong_ton_tai_hoac_da_tat_la_422(db, owner, work_list, type_a):
    t = _task(db, owner, work_list["id"])
    with pytest.raises(HTTPException) as e:
        _upd(db, owner, t["id"], task_type_id=99999)
    assert e.value.status_code == 422
    types.update_type(db, 1, type_a["id"], schema.TaskTypeUpdate(is_active=False))
    with pytest.raises(HTTPException):
        _upd(db, owner, t["id"], task_type_id=type_a["id"])


def test_gio_thuc_te_chi_nhap_khi_da_xong(db, owner, work_list):
    t = _task(db, owner, work_list["id"])
    with pytest.raises(HTTPException) as e:
        _upd(db, owner, t["id"], actual_hours=Decimal("6"))
    assert e.value.status_code == 422
    #  Một lượt PATCH vừa xong vừa nhập giờ thực tế vẫn hợp lệ (trạng thái áp trước).
    out = _upd(db, owner, t["id"], status=int(WorkTaskStatus.DONE), actual_hours=Decimal("6"))
    assert out["actual_hours"] == "6.00"


def test_gio_bang_0_la_xoa_gio(db, owner, work_list):
    t = _task(db, owner, work_list["id"], estimate_hours=Decimal("3"))
    assert _upd(db, owner, t["id"], estimate_hours=Decimal("0"))["estimate_hours"] is None


# ── Kết quả ───────────────────────────────────────────────────────────────────────────

def test_danh_gia_dat_khi_chua_xong_la_422(db, owner, work_list):
    t = _task(db, owner, work_list["id"])
    with pytest.raises(HTTPException) as e:
        task_outcome_service.set_outcome(db, owner, t["id"], int(WorkTaskOutcome.PASSED))
    assert e.value.status_code == 422


def test_ket_qua_la_so_la_422(db, owner, work_list):
    t = _task(db, owner, work_list["id"])
    _done(db, owner, t["id"])
    with pytest.raises(HTTPException) as e:
        task_outcome_service.set_outcome(db, owner, t["id"], 3)
    assert e.value.status_code == 422


def test_dat_roi_mo_lai_thi_ket_qua_cu_het_nghia(db, owner, work_list):
    t = _task(db, owner, work_list["id"])
    _done(db, owner, t["id"])
    assert task_outcome_service.set_outcome(db, owner, t["id"], 1)["outcome"] == 1
    assert _upd(db, owner, t["id"], status=int(WorkTaskStatus.OPEN))["outcome"] == 0


def test_phai_lam_lai_mo_lai_task_va_giu_ket_qua_toi_khi_xong_lai(db, owner, work_list):
    t = _task(db, owner, work_list["id"])
    _done(db, owner, t["id"])
    out = task_outcome_service.set_outcome(db, owner, t["id"], int(WorkTaskOutcome.REWORK))
    row = db.get(WorkTask, t["id"])
    assert out["status"] == int(WorkTaskStatus.OPEN) and row.completed_at is None
    assert row.outcome == int(WorkTaskOutcome.REWORK)                         # còn thấy mình đang làm lại
    _done(db, owner, t["id"])
    assert db.get(WorkTask, t["id"]).outcome == 0                             # xong lần nữa → đánh giá lại


def test_chi_nguoi_giao_hoac_quan_ly_moi_danh_gia(db, owner, member, work_list):
    t = _task(db, owner, work_list["id"])                                     # `owner` là người tạo
    _done(db, owner, t["id"])
    with pytest.raises(HTTPException) as e:
        task_outcome_service.set_outcome(db, member, t["id"], 1)
    assert e.value.status_code == 403
    #  Người tạo là thành viên thường vẫn tự đánh giá được việc mình giao.
    mine = _task(db, member, work_list["id"])
    _done(db, member, mine["id"])
    assert task_outcome_service.set_outcome(db, member, mine["id"], 1)["outcome"] == 1


# ── Gác quyền ghi danh mục (HTTP) ─────────────────────────────────────────────────────

@pytest.fixture
def client_as(db):
    def make(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield make
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def test_ghi_danh_muc_can_quyen_setting_write_con_doc_thi_ai_dung_du_an_cung_duoc(db, cap_quyen, client_as):
    co = make_company(db, "CQ")
    staff, _ = make_person(db, "NV1", co)
    admin, _ = make_person(db, "AD1", co)
    cap_quyen(staff.id, "work_task", scope="all", read=True)
    cap_quyen(admin.id, "setting", scope="all", read=True, write=True)
    cap_quyen(admin.id, "work_task", scope="all", read=True)
    db.commit()

    body = {"company_id": co.id, "code": "BC", "name": "Báo cáo"}
    assert client_as(staff).post("/api/work/task-types", json=body).status_code == 403
    ok = client_as(admin).post("/api/work/task-types", json=body)
    assert ok.status_code == 200 and ok.json()["data"]["code"] == "BC"
    assert client_as(admin).post("/api/work/task-types", json=body).status_code == 409
    listed = client_as(staff).get("/api/work/task-types")
    assert listed.status_code == 200 and [r["code"] for r in listed.json()["data"]["items"]] == ["BC"]
    assert client_as(staff).patch(f"/api/work/task-types/{ok.json()['data']['id']}", json={"name": "x"}).status_code == 403


# ── Kế hoạch do AI lập (plan_service) ─────────────────────────────────────────────────

def test_ke_hoach_ai_dat_duoc_loai_viec_va_gio_uoc_luong_con_rac_thi_bo_qua(db, owner, work_list, type_a):
    from app.modules.work.plan_service import _effort_kwargs

    ok = _effort_kwargs(db, {"task_type_id": type_a["id"], "estimate_hours": "3.5"})
    assert ok == {"task_type_id": type_a["id"], "estimate_hours": Decimal("3.50")}
    #  Rác không làm hỏng cả kế hoạch: bỏ riêng trường sai, không ném lỗi.
    assert _effort_kwargs(db, {"task_type_id": "abc", "estimate_hours": "nhiều"}) == {}
    assert _effort_kwargs(db, {"task_type_id": 99999, "estimate_hours": 5000}) == {}
    #  Kết quả đi thẳng vào TaskCreate được (cùng đường với web).
    t = task_service.create_task(db, owner, schema.TaskCreate(list_id=work_list["id"], title="AI", **ok))
    assert t["estimate_hours"] == "3.50" and t["task_type_name"] == "Báo giá NCC"
    types.update_type(db, 1, type_a["id"], schema.TaskTypeUpdate(is_active=False))
    assert _effort_kwargs(db, {"task_type_id": type_a["id"]}) == {}
