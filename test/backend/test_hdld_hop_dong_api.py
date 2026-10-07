"""API Hợp đồng lao động (CRUD, phạm vi, chuyển trạng thái, xóa hồ sơ) qua HTTP thật.

Góc nhìn kẻ phá: nhân sự pháp nhân khác, id gõ tay vào URL, tiền âm / quá lớn / số lẻ, ngày ngược,
loại HĐ lạ, sửa HĐ đã ký, nhảy trạng thái, xóa hồ sơ khi còn chứng từ pháp lý.
"""
from datetime import date

import pytest
from fastapi import HTTPException

from app.core.labor_contract_codes import LaborContractStatus as S
from app.modules.employee import service as employee_service
from app.modules.labor_contract.model import LaborContract
from hdld_factory import (client_as, contract_payload, grant_all, make_contract, make_docx,  # noqa: F401
                          storage, upload_template)

EMP_URL = "/api/employees/{}/labor-contracts"
CT_URL = "/api/labor-contracts"


@pytest.fixture
def setup(db, world, storage, client_as):  # noqa: F811
    grant_all(world, "a1")
    grant_all(world, "b1")
    return world, client_as(world.actor("a1")), client_as, storage


def _colleague_b(db, world) -> int:
    """Một nhân sự pháp nhân B KHÁC `b1` (người lập HĐ không được lập cho chính mình)."""
    from app.modules.employee.model import Employee

    emp = Employee(code="B_X", full_name="Đồng nghiệp B", company_id=world.co["B"],
                   department_id=world.dept["B.kt"], is_active=True)
    db.add(emp)
    db.commit()
    return emp.id


def sign(client, cid, on="2026-01-05"):
    return client.post(f"{CT_URL}/{cid}/transition", json={"to_status": int(S.SIGNED), "date": on})


# ── Đường đẹp + mặc định từ hồ sơ ─────────────────────────────────────────────────────
def test_tao_hd_chup_phap_nhan_phong_va_lay_mac_dinh_tu_ho_so(setup, db):
    world, a1, _, _ = setup
    emp = db.get(__import__("app.modules.employee.model", fromlist=["Employee"]).Employee, world.emp["a2"])
    emp.position, emp.work_location = "Kế toán viên", "Tầng 3"
    db.commit()
    res = a1.post(EMP_URL.format(world.emp["a2"]), json=contract_payload(allowance_note="Ăn trưa"))
    assert res.status_code == 201, res.text
    item = res.json()["data"]["item"]
    assert item["code"].startswith("HDLD") and item["status"] == 1 and item["effective_status"] == 1
    assert (item["company_id"], item["department_id"]) == (world.co["A"], world.dept["A.kt"])
    assert (item["company_name"], item["department_name"]) == ("Công ty A", "Phòng Kế toán")
    assert (item["job_title"], item["work_location"]) == ("Kế toán viên", "Tầng 3")
    assert item["can_edit"] and item["can_generate"] and item["transitions"] == [2, 5]
    assert item["has_generated_file"] is False and item["has_signed_file"] is False
    assert {"url", "file_key", "generated_file_id", "signed_file_id"}.isdisjoint(item)
    assert res.json()["data"]["warnings"] == []


def test_snapshot_khong_doi_khi_nhan_su_chuyen_phap_nhan(setup, db):
    from app.modules.employee.model import Employee

    world, a1, _, _ = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    db.get(Employee, world.emp["a2"]).company_id = world.co["B"]
    db.commit()
    assert db.get(LaborContract, cid).company_id == world.co["A"]


def test_danh_sach_theo_nhan_su_tra_items_va_can_create(setup):
    world, a1, _, _ = setup
    make_contract(a1, world.emp["a2"], start_date="2026-01-01")
    make_contract(a1, world.emp["a2"], start_date="2027-01-01", end_date="2027-12-31", contract_no="HD-2")
    data = a1.get(EMP_URL.format(world.emp["a2"])).json()["data"]
    assert [i["start_date"] for i in data["items"]] == ["2027-01-01", "2026-01-01"] and data["can_create"] is True
    assert a1.get(EMP_URL.format(999_999)).status_code == 404


def test_route_nhan_su_khong_bi_employee_router_nuot(setup):
    """`/api/employees/{eid}/labor-contracts` phải tới handler của HĐLĐ chứ không rơi vào `/{eid}` (404/405/422)."""
    world, a1, _, _ = setup
    assert a1.get(EMP_URL.format(world.emp["a2"])).status_code == 200
    assert a1.get(f"/api/employees/{world.emp['a2']}/labor-contract-templates").status_code == 200


def test_mau_cua_nhan_su_chi_gom_mau_dang_dung_cua_phap_nhan_hien_tai_dung_loai(setup):
    world, a1, make_client, _ = setup
    ok = upload_template(a1, company_id=world.co["A"], name="Xác định", contract_type=2).json()["data"]["id"]
    off = upload_template(a1, company_id=world.co["A"], name="Ngừng", contract_type=2).json()["data"]["id"]
    upload_template(a1, company_id=world.co["A"], name="Thử việc", contract_type=1)
    upload_template(make_client(world.actor("b1")), company_id=world.co["B"], name="Của B", contract_type=2)
    a1.patch(f"/api/labor-contract-templates/{off}", json={"is_active": False})
    url = f"/api/employees/{world.emp['a2']}/labor-contract-templates"
    assert [r["id"] for r in a1.get(url, params={"contract_type": 2}).json()["data"]] == [ok]
    assert {r["name"] for r in a1.get(url).json()["data"]} == {"Xác định", "Thử việc"}
    assert set(a1.get(url).json()["data"][0]) == {"id", "name", "contract_type"}
    world.actor("a3").grant("employee", "company", actions=("read",))     # không có quyền HĐLĐ
    assert make_client(world.actor("a3")).get(url).status_code == 403


def test_o_chon_mau_cua_nhan_su_ngoai_pham_vi_tra_403(setup, db):
    """Lỗ cũ: đường này chỉ xét quyền vai trò, người pháp nhân A gõ id nhân sự B là đọc được tên mẫu của B."""
    world, a1, make_client, _ = setup
    upload_template(make_client(world.actor("b1")), company_id=world.co["B"], name="Của B", contract_type=2)
    url = f"/api/employees/{world.emp['b1']}/labor-contract-templates"
    assert a1.get(url).status_code == 403
    #  Người pháp nhân B vẫn xem được ô chọn mẫu của một nhân sự B KHÁC (không phải chính mình).
    colleague_id = _colleague_b(db, world)
    assert make_client(world.actor("b1")).get(
        f"/api/employees/{colleague_id}/labor-contract-templates").status_code == 200


# ── Phạm vi ───────────────────────────────────────────────────────────────────────────
def test_hd_cua_phap_nhan_khac_404_o_moi_duong_id(setup, db):
    world, a1, make_client, _ = setup
    cid = make_contract(make_client(world.actor("b1")), _colleague_b(db, world))["id"]
    for method, path, kw in [
        ("get", f"/{cid}", {}), ("patch", f"/{cid}", {"json": {"note": "x"}}), ("delete", f"/{cid}", {}),
        ("post", f"/{cid}/generate", {"json": {"template_id": 1}}), ("get", f"/{cid}/document", {}),
        ("get", f"/{cid}/signed-file", {}),
        ("put", f"/{cid}/signed-file", {"files": {"file": ("a.pdf", b"%PDF-1.4", "application/pdf")}}),
        ("post", f"/{cid}/transition", {"json": {"to_status": 5, "reason": "x"}}),
    ]:
        res = getattr(a1, method)(f"{CT_URL}{path}", **kw)
        assert res.status_code == 404, f"{method} {path} → {res.status_code}"
    assert a1.get(EMP_URL.format(world.emp["b1"])).json()["data"]["items"] == []   # danh sách theo NV: rỗng, không lộ


def test_lap_hd_cho_nhan_su_ngoai_pham_vi_403_khong_de_lai_dong(setup, db):
    world, a1, _, _ = setup
    res = a1.post(EMP_URL.format(world.emp["b1"]), json=contract_payload())
    assert res.status_code == 403 and db.query(LaborContract).count() == 0


def test_nhan_su_chua_gan_phap_nhan_400(setup):
    world, a1, _, _ = setup
    assert a1.post(EMP_URL.format(world.emp["khongcty"]), json=contract_payload()).status_code == 400


def test_chi_co_quyen_doc_thi_khong_ghi_duoc(db, world, storage, client_as):  # noqa: F811
    world.actor("a1").grant("labor_contract", "company", actions=("read",))
    world.actor("a2").grant("labor_contract", "company", actions=("read", "create", "write", "delete"))
    boss, ro = client_as(world.actor("a2")), client_as(world.actor("a1"))
    cid = make_contract(boss, world.emp["a3"])["id"]
    item = ro.get(f"{CT_URL}/{cid}").json()["data"]
    assert (item["can_edit"], item["can_delete"], item["can_generate"], item["can_print"], item["transitions"]) \
        == (False, False, False, False, [])
    assert ro.post(EMP_URL.format(world.emp["a3"]), json=contract_payload()).status_code == 403
    assert ro.patch(f"{CT_URL}/{cid}", json={"note": "x"}).status_code == 403
    assert ro.delete(f"{CT_URL}/{cid}").status_code == 403
    assert ro.post(f"{CT_URL}/{cid}/transition", json={"to_status": 5, "reason": "x"}).status_code == 403
    assert client_as(world.actor("b1")).get(f"{CT_URL}/{cid}").status_code == 403    # không có quyền gì


def test_pham_vi_own_chi_thay_hd_cua_chinh_minh(db, world, storage, client_as):  # noqa: F811
    """`self` = employee_id của HĐ: quyền own không được đọc HĐ của đồng nghiệp cùng phòng."""
    grant_all(world, "a1", scope="company")
    boss = client_as(world.actor("a1"))
    mine = make_contract(boss, world.emp["a3"])["id"]
    other = make_contract(boss, world.emp["a2"])["id"]
    world.actor("a3").grant("labor_contract", "own", actions=("read",))
    me = client_as(world.actor("a3"))
    assert me.get(f"{CT_URL}/{mine}").status_code == 200
    assert me.get(f"{CT_URL}/{other}").status_code == 404


# ── Kiểm dữ liệu đầu vào ──────────────────────────────────────────────────────────────
@pytest.mark.parametrize("over", [
    {"contract_type": 0}, {"contract_type": 7}, {"contract_type": -3},
    {"base_salary": -1}, {"base_salary": 10**12 + 1}, {"base_salary": 1.5}, {"base_salary": "abc"},
    {"insurance_salary": -1}, {"allowance": -1},
    {"end_date": "2025-12-31"}, {"end_date": None},                    # ngược ngày / loại có hạn thiếu ngày
    {"contract_type": 3, "end_date": "2027-01-01"},                    # không xác định thời hạn mà có ngày kết thúc
    {"start_date": "0001-01-01"}, {"start_date": "9999-12-31"}, {"start_date": "không phải ngày"},
    {"contract_no": "n" * 51}, {"job_title": "n" * 101}, {"work_location": "n" * 256},
    {"note": "n" * 501}, {"allowance_note": "n" * 501},
    {"status": 2}, {"company_id": 5}, {"signed_file_id": 3},          # trường lạ (mass-assignment) bị cấm
])
def test_payload_sai_bi_422(setup, over):
    world, a1, _, _ = setup
    body = contract_payload(**over)
    res = a1.post(EMP_URL.format(world.emp["a2"]), json=body)
    assert res.status_code == 422, f"{over} → {res.status_code}"


def test_bien_so_hop_le_tien_bang_0_va_dung_tran_1e12(setup):
    world, a1, _, _ = setup
    item = make_contract(a1, world.emp["a2"], base_salary=0, insurance_salary=0, allowance=0)
    assert item["base_salary"] == 0
    big = make_contract(a1, world.emp["a3"], base_salary=10**12, contract_no="BIG")
    assert big["base_salary"] == 10**12


def test_xac_dinh_thoi_han_tren_36_thang_van_tao_duoc_kem_canh_bao(setup):
    world, a1, _, _ = setup
    res = a1.post(EMP_URL.format(world.emp["a2"]), json=contract_payload(end_date="2031-01-01"))
    assert res.status_code == 201 and len(res.json()["data"]["warnings"]) == 1
    cid = res.json()["data"]["item"]["id"]
    ok = a1.patch(f"{CT_URL}/{cid}", json={"end_date": "2027-01-01"})
    assert ok.status_code == 200 and ok.json()["data"]["warnings"] == []


def test_so_hop_dong_trung_trong_phap_nhan_400_tru_hd_da_huy(setup):
    world, a1, _, _ = setup
    first = make_contract(a1, world.emp["a2"], contract_no="HD-01")
    dup = a1.post(EMP_URL.format(world.emp["a3"]), json=contract_payload(contract_no="HD-01"))
    assert dup.status_code == 400 and "đã tồn tại" in dup.json()["error"]["message"]
    a1.post(f"{CT_URL}/{first['id']}/transition", json={"to_status": 5, "reason": "nhầm"})
    assert a1.post(EMP_URL.format(world.emp["a3"]), json=contract_payload(contract_no="HD-01")).status_code == 201


# ── Sửa / xóa ─────────────────────────────────────────────────────────────────────────
def test_sua_gop_kiem_lai_rang_buoc_ngay_va_khong_nhan_cot_khoa(setup):
    world, a1, _, _ = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    assert a1.patch(f"{CT_URL}/{cid}", json={"end_date": "2025-01-01"}).status_code == 400      # trước start (gộp)
    assert a1.patch(f"{CT_URL}/{cid}", json={"contract_type": 3}).status_code == 400            # INDEFINITE mà còn end_date
    assert a1.patch(f"{CT_URL}/{cid}", json={"contract_type": 3, "end_date": None}).status_code == 200
    for bad in ({"status": 2}, {"company_id": 9}, {"employee_id": 1}, {"base_salary": -5}, {"contract_type": 0}):
        assert a1.patch(f"{CT_URL}/{cid}", json=bad).status_code == 422, bad
    assert a1.patch(f"{CT_URL}/{cid}", json={"note": None, "job_title": None}).status_code == 200
    assert a1.get(f"{CT_URL}/{cid}").json()["data"]["job_title"] is not None


def test_sua_hd_da_ky_409(setup):
    world, a1, _, _ = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    assert sign(a1, cid).status_code == 200
    assert a1.patch(f"{CT_URL}/{cid}", json={"note": "x"}).status_code == 409


def test_xoa_chi_nhap_hoac_da_huy(setup):
    world, a1, _, _ = setup
    draft = make_contract(a1, world.emp["a2"], contract_no="A")["id"]
    signed = make_contract(a1, world.emp["a3"], contract_no="B")["id"]
    sign(a1, signed)
    assert a1.delete(f"{CT_URL}/{signed}").status_code == 409
    assert a1.delete(f"{CT_URL}/{draft}").status_code == 200 and a1.get(f"{CT_URL}/{draft}").status_code == 404
    a1.post(f"{CT_URL}/{signed}/transition", json={"to_status": 4, "date": "2026-06-01", "reason": "nghỉ"})
    assert a1.delete(f"{CT_URL}/{signed}").status_code == 409                      # đã chấm dứt cũng là chứng từ


# ── Chuyển trạng thái qua API ─────────────────────────────────────────────────────────
def test_chuyen_trang_thai_day_du_va_ghi_cot_dung(setup, db):
    world, a1, _, _ = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    assert a1.post(f"{CT_URL}/{cid}/transition", json={"to_status": 2}).status_code == 400        # thiếu ngày ký
    ok = sign(a1, cid, "2026-01-05")
    assert ok.status_code == 200 and ok.json()["data"]["sign_date"] == "2026-01-05"
    assert ok.json()["data"]["transitions"] == [4] and ok.json()["data"]["can_edit"] is False
    assert sign(a1, cid).status_code == 409                                                       # đã ký rồi
    assert a1.post(f"{CT_URL}/{cid}/transition", json={"to_status": 5, "reason": "x"}).status_code == 409
    early = a1.post(f"{CT_URL}/{cid}/transition", json={"to_status": 4, "date": "2025-12-01", "reason": "x"})
    assert early.status_code == 400
    end = a1.post(f"{CT_URL}/{cid}/transition", json={"to_status": 4, "date": "2026-06-30", "reason": "Hết nhu cầu"})
    row = db.get(LaborContract, cid)
    db.refresh(row)
    assert end.status_code == 200 and (row.status, row.terminated_date, row.terminate_reason) \
        == (4, date(2026, 6, 30), "Hết nhu cầu")


def test_trang_thai_ngoai_enum_hoac_truong_la_bi_chan(setup):
    world, a1, _, _ = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    for bad in ({"to_status": 0}, {"to_status": 3}, {"to_status": 99}, {"to_status": -1}):
        assert a1.post(f"{CT_URL}/{cid}/transition", json=bad).status_code in (400, 409), bad
    assert a1.post(f"{CT_URL}/{cid}/transition", json={"to_status": 5, "reason": "x", "status": 2}).status_code == 422
    assert a1.post(f"{CT_URL}/{cid}/transition", json={"to_status": 5, "reason": "x" * 501}).status_code == 422


def test_huy_can_ly_do(setup):
    world, a1, _, _ = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    assert a1.post(f"{CT_URL}/{cid}/transition", json={"to_status": 5, "reason": "   "}).status_code == 400
    assert a1.post(f"{CT_URL}/{cid}/transition", json={"to_status": 5, "reason": "Nhầm người"}).status_code == 200


def test_effective_status_het_han_theo_ngay_ket_thuc_da_qua(setup):
    """HĐ đã ký có `end_date` trong quá khứ hiện HẾT HẠN (3) nhưng DB vẫn lưu ĐÃ KÝ (2) và vẫn chấm dứt được."""
    world, a1, _, _ = setup
    cid = make_contract(a1, world.emp["a2"], start_date="2020-01-01", end_date="2020-12-31")["id"]
    assert sign(a1, cid, "2020-01-01").status_code == 200
    item = a1.get(f"{CT_URL}/{cid}").json()["data"]
    assert (item["status"], item["effective_status"]) == (2, 3) and item["transitions"] == [4]
    assert a1.get(EMP_URL.format(world.emp["a2"])).json()["data"]["items"][0]["effective_status"] == 3
    done = a1.post(f"{CT_URL}/{cid}/transition", json={"to_status": 4, "date": "2021-01-01", "reason": "x"})
    assert done.status_code == 200 and done.json()["data"]["effective_status"] == 4


def test_hd_khong_xac_dinh_thoi_han_khong_bao_gio_het_han(setup):
    world, a1, _, _ = setup
    cid = make_contract(a1, world.emp["a2"], contract_type=3, end_date=None, start_date="2000-01-01")["id"]
    sign(a1, cid, "2000-01-01")
    assert a1.get(f"{CT_URL}/{cid}").json()["data"]["effective_status"] == 2


# ── Xóa hồ sơ nhân sự ─────────────────────────────────────────────────────────────────
def test_xoa_ho_so_con_hd_da_ky_409_va_khong_khoa_tai_khoan(setup, db):
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    world, a1, _, _ = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    sign(a1, cid)
    with pytest.raises(HTTPException) as e:
        employee_service.delete_employee(db, world.emp["a2"], world.actor("a1").user.id)
    assert e.value.status_code == 409 and "hợp đồng lao động" in e.value.detail
    assert db.get(Employee, world.emp["a2"]) is not None
    assert db.get(LaborContract, cid) is not None
    assert db.get(User, world.actor("a2").user.id).is_active is True     # chặn TRƯỚC khi khóa tài khoản


def test_xoa_ho_so_con_hd_da_cham_dut_van_409(setup, db):
    world, a1, _, _ = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    sign(a1, cid)
    a1.post(f"{CT_URL}/{cid}/transition", json={"to_status": 4, "date": "2026-06-30", "reason": "x"})
    with pytest.raises(HTTPException) as e:
        employee_service.delete_employee(db, world.emp["a2"], world.actor("a1").user.id)
    assert e.value.status_code == 409


def test_xoa_ho_so_chi_con_hd_nhap_va_da_huy_thi_don_sach_ca_tep(setup, db):
    from app.modules.attachment.model import StoredFile
    from app.modules.employee.model import Employee

    world, a1, _, storage = setup
    tid = upload_template(a1, company_id=world.co["A"]).json()["data"]["id"]
    storage_after_template = len(storage)
    draft = make_contract(a1, world.emp["a2"], contract_no="D")["id"]
    assert a1.post(f"{CT_URL}/{draft}/generate", json={"template_id": tid}).status_code == 200
    cancelled = make_contract(a1, world.emp["a2"], contract_no="C", start_date="2027-01-01", end_date="2027-12-31")["id"]
    a1.post(f"{CT_URL}/{cancelled}/transition", json={"to_status": 5, "reason": "nhầm"})
    assert len(storage) == storage_after_template + 1
    employee_service.delete_employee(db, world.emp["a2"], world.actor("a1").user.id)
    assert db.get(Employee, world.emp["a2"]) is None
    assert db.query(LaborContract).filter(LaborContract.employee_id == world.emp["a2"]).count() == 0
    assert len(storage) == storage_after_template and db.query(StoredFile).count() == 1   # chỉ còn tệp mẫu


def test_xoa_ho_so_nguoi_khong_co_hop_dong_van_chay(setup, db):
    from app.modules.employee.model import Employee

    world, _, _, _ = setup
    employee_service.delete_employee(db, world.emp["khongtk"], world.actor("a1").user.id)
    assert db.get(Employee, world.emp["khongtk"]) is None
