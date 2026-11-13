"""duoc-CR-755 giai đoạn 05 (chỉnh theo mô hình hai loại dòng ở duoc-CR-756) — HIỂN THỊ kiêm nhiệm + bật ĐỌC hồ sơ (Q1).

Cảnh (xem `kiem_nhiem_factory`): a2 (công ty A, phòng DÙNG CHUNG SH) kiêm nhiệm CÔNG TY B → ngồi ở (SH, B). hb (B, SH)
là người xem có phạm vi `dept` trên `employee`; y1 (B, B.hc) là người xem phòng KHÁC.

Bốn luật phải giữ, mỗi luật có cặp đối chứng ở chiều ngược (chặn sạch thì bài nào cũng xanh):

1. Q1 — MỌI đường ĐỌC hồ sơ `/api/employees/{eid}/...` mở cho người phủ chỗ ngồi của dòng hiệu lực + bật công tắc;
   hết hạn / tắt công tắc / sắp tới / phòng khác = 404. Đường mới thêm mà quên phân loại thì bài soi `app.routes` đỏ.
2. Q1 chỉ ĐỌC: PATCH / PUT / POST / DELETE đều 404; danh sách `/api/employees`, xuất tệp, báo cáo KHÔNG có người
   kiêm nhiệm (Q5 + không đếm trùng quân số).
3. Bảng "Kiêm nhiệm" theo phòng / công ty + sơ đồ tổ chức: chỉ dòng người xem phủ, danh sách trắng trường, số truy vấn
   cố định.
4. Nhạy cảm vẫn che (`employee_sensitive`), lương không bao giờ ra; xóa dòng quá trình công tác loại Kiêm nhiệm GIỮ dòng
   kiêm nhiệm và chỉ bỏ liên kết.
"""
from datetime import date, timedelta

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute
from sqlalchemy import event

from app.core.auth import perm_cache_clear
from app.core.route_iter import api_routes
from app.core.vn_time import vn_today
from app.main import app
from app.modules.assistant import tools as T
from app.modules.attachment import controller as ac
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.employee import concurrent_members_service as members
from app.modules.employee import work_history_service as whs
from app.modules.employee.concurrent_model import EmployeeConcurrent
from app.modules.employee.model import Employee
from app.modules.employee.work_history_model import EmployeeWorkHistory
from hdld_factory import client_as  # noqa: F401
from kiem_nhiem_factory import add_employee, build_kn_world, kc, kn as kn_dept

TODAY = vn_today()
DAY = timedelta(days=1)
MEMBERS = "/api/employee-concurrents"

#  Dòng kiêm nhiệm ở phòng B.kt công ty B — khóa bị che theo quyền: KHÔNG được có trong bản tóm tắt.
FORBIDDEN_KEYS = {"phone", "phone_label", "extra_phones", "email", "birth_date", "date_of_birth", "id_number",
                  "tax_code", "bank_account_no", "permanent_address", "salary_monthly", "allowance_monthly"}
MEMBER_KEYS = {"id", "employee_id", "code", "full_name", "kind", "kind_label", "position_label", "company_id", "company_name",
               "department_id", "department_name", "from_date", "to_date", "status", "status_label",
               "counts_scope", "primary_company_id", "primary_company_name", "primary_department_id",
               "primary_department_name", "can_open"}


# ── Dựng cảnh ────────────────────────────────────────────────────────────────

@pytest.fixture
def w(world):
    """Thế giới mẫu + công ty C, phòng dùng chung SH, người xem hb / y1 / c1; a2 chuyển sang (A, SH)."""
    return build_kn_world(world)


def kn(w, emp_key="a2", company_key="B", **kw) -> EmployeeConcurrent:
    """Một dòng kiêm nhiệm CÔNG TY (loại 2). Mặc định ĐANG HIỆU LỰC + bật công tắc."""
    return kc(w, emp_key, company_key, position_label=kw.pop("position_label", "Phó phòng"), **kw)


def head_b(w, *, sensitive=True, actions=("read", "write", "delete")):
    """hb = người xem phòng dùng chung SH ở công ty B: đọc + ghi hồ sơ theo phạm vi `dept`."""
    actor = w.grant("hb", "employee", "dept", actions=actions)
    if sensitive:
        actor.grant("employee_sensitive", "all", actions=("read",))
    return actor


def with_cached_off(row: EmployeeConcurrent, how: str, db) -> None:
    """Đưa dòng về một trong các trạng thái KHÔNG mở được hồ sơ."""
    if how == "het_han":
        row.to_date = TODAY - DAY
    elif how == "tat_cong_tac":
        row.counts_scope = False
    elif how == "sap_toi":
        row.from_date = TODAY + DAY
    db.commit()
    perm_cache_clear()


def count_queries(db, fn):
    """Số truy vấn của `fn()` — ĐO LƯỢT THỨ HAI: lượt đầu nạp lại người dùng / ảnh sau `commit` (đối tượng hết hạn)
    nên hơn lượt sau 2 truy vấn không dính gì tới mã đang kiểm. Hồ sơ quyền xóa trước mỗi lượt đo (dựng từ đầu)."""
    perm_cache_clear()
    fn()
    perm_cache_clear()
    n: list[int] = []
    listener = lambda *a, **k: n.append(1)  # noqa: E731
    engine = db.get_bind()
    event.listen(engine, "before_cursor_execute", listener)
    try:
        result = fn()
    finally:
        event.remove(engine, "before_cursor_execute", listener)
    return len(n), result


# ── 1. Q1: soi MỌI đường đọc hồ sơ ───────────────────────────────────────────

#  GET `/api/employees/{eid}/<đuôi>` đã bật `include_concurrent` (đọc hồ sơ theo phạm vi `employee`).
Q1_TAILS = {"/pending-work", "/departments", "/contacts", "/families", "/concurrents", "/work-history"}
#  GET `/api/employees/{eid}` không xét phạm vi từ trước (test_pham_vi_nhan_su_hanh_chinh::c9 ghim, "QUYẾT ĐỊNH CHỜ")
#  — vì vậy với đường này Q1 không có gì để bật; giữ nguyên, không tự bịt trong CR này.
UNSCOPED_TAILS = {""}
#  Thuộc entity khác (`labor_contract`) — theo phạm vi riêng của nó, Q1 không mở (kế hoạch phase 05).
OTHER_ENTITY_TAILS = {"/labor-contracts", "/labor-contract-templates"}


def _eid_get_tails() -> set[str]:
    tails = set()
    for r in api_routes(app):
        if isinstance(r, APIRoute) and "GET" in r.methods and r.path.startswith("/api/employees/{eid}"):
            tails.add(r.path.removeprefix("/api/employees/{eid}"))
    return tails


def test_quet_duoc_moi_duong_doc_ho_so_va_deu_da_phan_loai():
    """Thêm đường `GET /api/employees/{eid}/...` mới mà không xếp vào một trong ba nhóm = đỏ, buộc người thêm nghĩ tới Q1."""
    found = _eid_get_tails()
    assert len(found) >= 8, found   # chốt đáy: bộ lọc tên đường hỏng thì bài quét xanh rỗng
    unknown = found - Q1_TAILS - UNSCOPED_TAILS - OTHER_ENTITY_TAILS
    assert not unknown, f"đường đọc hồ sơ chưa phân loại Q1: {sorted(unknown)}"
    assert Q1_TAILS <= found, "nhóm Q1 khai tên đường không còn tồn tại"


def test_q1_truong_phong_B_doc_duoc_moi_duong_ho_so_cua_nguoi_kiem_nhiem(w, client_as):  # noqa: F811
    kn(w)
    b1 = head_b(w)
    c = client_as(b1)
    got = {t: c.get(f"/api/employees/{w.emp['a2']}{t}").status_code for t in sorted(Q1_TAILS | UNSCOPED_TAILS)}
    assert got == dict.fromkeys(got, 200), got
    #  Đối chứng: người ĐỌC được hồ sơ này nhờ kiêm nhiệm cũng đọc hồ sơ của chính mình như thường.
    assert c.get(f"/api/employees/{w.emp['hb']}/work-history").status_code == 200
    #  …và KHÔNG mở rộng sang người ngoài cặp: a3 (A.mua, công ty A) không kiêm nhiệm gì.
    assert c.get(f"/api/employees/{w.emp['a3']}/work-history").status_code == 404


@pytest.mark.parametrize("how", ["het_han", "tat_cong_tac", "sap_toi"])
def test_q1_dong_khong_con_hieu_luc_hoac_tat_cong_tac_thi_404_het(w, client_as, how):  # noqa: F811
    row = kn(w)
    b1 = head_b(w)
    c = client_as(b1)
    assert c.get(f"/api/employees/{w.emp['a2']}/work-history").status_code == 200   # đối chứng: đang mở
    with_cached_off(row, how, w.db)
    got = {t: c.get(f"/api/employees/{w.emp['a2']}{t}").status_code for t in sorted(Q1_TAILS)}
    assert got == dict.fromkeys(got, 404), got


def test_q1_nguoi_xem_phong_khac_khong_mo_duoc(w, client_as):  # noqa: F811
    kn(w)
    y1 = w.grant("y1", "employee", "dept", actions=("read",))
    y1.grant("employee_sensitive", "all", actions=("read",))
    c = client_as(y1)
    got = {t: c.get(f"/api/employees/{w.emp['a2']}{t}").status_code for t in sorted(Q1_TAILS)}
    assert got == dict.fromkeys(got, 404), got


def test_q1_phong_dung_chung_chi_mo_dung_cong_ty(w, client_as):  # noqa: F811
    """Phòng SH dùng chung: dòng kiêm nhiệm công ty C (chỗ ngồi (SH, C)) KHÔNG mở cho người xem (SH, B)."""
    kn(w, company_key="C")
    c = client_as(head_b(w))
    assert c.get(f"/api/employees/{w.emp['a2']}/work-history").status_code == 404


def test_q1_nhay_cam_van_che_va_luong_khong_bao_gio_ra(w, client_as):  # noqa: F811
    kn(w)
    a2 = w.db.get(Employee, w.emp["a2"])
    a2.id_number, a2.bank_account_no, a2.salary_monthly = "079123456789", "1234567890", 15_000_000
    w.db.commit()
    #  b1 KHÔNG có employee_sensitive: hồ sơ đọc được nhưng nhóm nhạy cảm bị che, contacts / families = 403 (không phải 404).
    c = client_as(head_b(w, sensitive=False))
    body = c.get(f"/api/employees/{w.emp['a2']}").json()["data"]
    assert body["id_number"] == "" and body["bank_account_no"] == ""
    assert c.get(f"/api/employees/{w.emp['a2']}/contacts").status_code == 403
    assert c.get(f"/api/employees/{w.emp['a2']}/families").status_code == 403
    #  Có employee_sensitive: nhạy cảm mở ra nhưng LƯƠNG thì chỉ chính chủ.
    w.actor("hb").grant("employee_sensitive", "all", actions=("read",))
    body = c.get(f"/api/employees/{w.emp['a2']}").json()["data"]
    assert body["id_number"] == "079123456789"
    assert body["salary_monthly"] == 0 and body["allowance_monthly"] == 0
    assert c.get(f"/api/employees/{w.emp['a2']}/contacts").status_code == 200


def test_q1_tep_quyet_dinh_chi_doc_duoc_khi_dong_con_hieu_luc(w):
    """Mở hồ sơ được mà tải tệp QĐ không được là nửa vời: tệp quá trình công tác + tệp kiêm nhiệm cùng luật."""
    row = kn(w)
    wh = EmployeeWorkHistory(employee_id=w.emp["a2"], event_type=4, from_date=TODAY - 30 * DAY,
                             department_id=0, created_by=1, updated_by=1)
    w.db.add(wh)
    w.db.commit()
    entities = (("employee_work_history", wh.id), ("employee_concurrent", row.id))
    b1 = head_b(w)

    for entity, entity_id in entities:
        ac._check(w.db, b1.user, entity, "read", entity_id)   # không ném = được đọc
    #  Không có employee_sensitive.read: 403 dù đã phủ cặp.
    no_sens = w.grant("y1", "employee", "dept", actions=("read",))
    for entity, entity_id in entities:
        with pytest.raises(HTTPException) as e:
            ac._check(w.db, no_sens.user, entity, "read", entity_id)
        assert e.value.status_code == 403
    #  Hết hạn (cả hai tệp cùng treo vào chỗ ngồi của dòng kiêm nhiệm — đã hết thì không còn gì để phủ): 403.
    with_cached_off(row, "het_han", w.db)
    for entity, entity_id in entities:
        with pytest.raises(HTTPException) as e:
            ac._check(w.db, b1.user, entity, "read", entity_id)
        assert e.value.status_code == 403
    #  Ghi tệp (gắn / gỡ) không bao giờ mở theo Q1.
    kn(w)
    for entity, entity_id in entities:
        with pytest.raises(HTTPException) as e:
            ac._check(w.db, b1.user, entity, "write", entity_id)
        assert e.value.status_code in (403, 404)


# ── 2. Q1 chỉ ĐỌC; danh sách / xuất / báo cáo không đổi ──────────────────────

def test_q1_moi_duong_ghi_van_404_va_ho_so_khong_bi_dung(w, client_as):  # noqa: F811
    kn(w)
    b1 = head_b(w, actions=("read", "write", "delete", "create"))
    c = client_as(b1)
    eid = w.emp["a2"]
    before = w.db.get(Employee, eid).full_name
    results = {
        "PATCH": c.patch(f"/api/employees/{eid}", json={"full_name": "Bị sửa"}).status_code,
        "PUT contacts": c.put(f"/api/employees/{eid}/contacts", json={"items": []}).status_code,
        "PUT families": c.put(f"/api/employees/{eid}/families", json={"items": []}).status_code,
        "POST work-history": c.post(f"/api/employees/{eid}/work-history",
                                    json={"event_type": 9, "from_date": "2026-01-01"}).status_code,
        "POST concurrents": c.post(f"/api/employees/{eid}/concurrents",
                                   json={"kind": 2, "company_id": w.co["C"], "from_date": "2026-01-01"}).status_code,
        "DELETE": c.delete(f"/api/employees/{eid}").status_code,
        "set-password": c.post(f"/api/employees/{eid}/set-password",
                               json={"password": "mat-khau-moi-26"}).status_code,
    }
    assert results == dict.fromkeys(results, 404), results
    w.db.expire_all()
    assert w.db.get(Employee, eid).full_name == before


def test_q5_danh_sach_nhan_su_khong_co_nguoi_kiem_nhiem_ke_ca_loc_phong(w, client_as):  # noqa: F811
    kn(w)
    c = client_as(head_b(w))
    for params in ({}, {"department_id": w.dept["SH"]}):
        codes = {i["code"] for i in c.get("/api/employees", params={**params, "page_size": 100}).json()["data"]["items"]}
        assert "A2" not in codes, params
        assert "HB" in codes, params   # đối chứng: danh sách vẫn chạy, người của phòng mình vẫn có


def test_xuat_tep_nhan_su_khong_co_nguoi_kiem_nhiem(w, client_as):  # noqa: F811
    kn(w)
    c = client_as(head_b(w, actions=("read", "export")))
    resp = c.get("/api/employees/export/csv")
    assert resp.status_code == 200
    text = resp.content.decode("utf-8-sig")
    assert "HB" in text and "NHÂN SỰ A2" not in text.upper() and "A2," not in text


def test_bao_cao_quan_so_khong_dem_trung_nguoi_kiem_nhiem(w):
    """Công ty B / phòng kiêm nhiệm KHÔNG đếm a2; phòng chính SH vẫn đếm a2 đúng một lần; thêm dòng không đổi con số nào."""
    from app.core.report_period import parse_period
    from app.modules.employee import report_service

    for emp in w.db.query(Employee).all():   # báo cáo chỉ đếm người đã có ngày vào làm
        emp.hire_date = date(2020, 1, 1)
    w.db.commit()
    period = parse_period({"preset": "custom", "date_from": "2026-09-01", "date_to": "2026-09-30", "compare": "none"})
    all_user = w.grant("a1", "employee", "all", actions=("read",)).user

    def heads(dept_key):
        data = report_service.build_summary(w.db, all_user, w.actor("a1").profile(), period, None,
                                            department_id=w.dept[dept_key])
        return data["totals"]["current"]["headcount_end"]

    #  A.kt: a1 + khongtk (2); SH: a2 + hb + c1 (3); A.mua: a3 (1).
    assert (heads("A.kt"), heads("SH"), heads("A.mua")) == (2, 3, 1)
    kn(w)                                          # a2 kiêm nhiệm cả công ty B
    kn_dept(w, "a2", "A.mua")                      # a2 kiêm nhiệm thêm phòng của chính công ty A
    assert (heads("A.kt"), heads("SH"), heads("A.mua")) == (2, 3, 1)


# ── 3. Bảng "Kiêm nhiệm" theo phòng / công ty ────────────────────────────────

def get_members(c, **params):
    return c.get(MEMBERS, params=params)


def of_b(c, **params):
    """Dòng loại Công ty ở công ty B (bảng ở trang công ty B)."""
    return get_members(c, company_id=params.pop("company_id"), kind=2, **params)


def test_bang_cong_ty_B_thay_nguoi_kiem_nhiem_co_can_open_va_chi_danh_sach_trang(w, client_as):  # noqa: F811
    kn(w)
    a2 = w.db.get(Employee, w.emp["a2"])
    a2.phone, a2.email, a2.id_number = "0912345678", "a2@dego.vn", "079123456789"
    w.db.commit()
    c = client_as(head_b(w, sensitive=False))
    resp = of_b(c, company_id=w.co["B"])
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 1 and data["truncated"] is False
    item = data["items"][0]
    assert set(item) == MEMBER_KEYS
    assert not (set(item) & FORBIDDEN_KEYS)
    assert "0912345678" not in resp.text and "a2@dego.vn" not in resp.text and "079123456789" not in resp.text
    assert (item["code"], item["position_label"], item["status"]) == ("A2", "Phó phòng", 2)
    assert (item["kind"], item["kind_label"]) == (2, "Công ty")
    assert (item["company_name"], item["department_id"], item["department_name"]) == ("Công ty B", 0, "")
    assert item["primary_company_name"] == "Công ty A" and item["primary_department_name"] == "Phòng SH_DC"
    assert item["can_open"] is True and item["counts_scope"] is True


def test_bang_dong_tat_cong_tac_van_hien_ten_nhung_khong_mo_ho_so(w, client_as):  # noqa: F811
    kn(w, counts_scope=False)
    c = client_as(head_b(w))
    item = of_b(c, company_id=w.co["B"]).json()["data"]["items"][0]
    assert item["code"] == "A2" and item["counts_scope"] is False
    assert item["can_open"] is False
    #  Khớp với đường đọc hồ sơ: tắt công tắc thì tab con 404.
    assert c.get(f"/api/employees/{w.emp['a2']}/work-history").status_code == 404


def test_bang_nguoi_xem_cho_ngoi_khac_khong_thay_gi(w, client_as):  # noqa: F811
    kn(w)
    y1 = w.grant("y1", "employee", "dept", actions=("read",))
    assert of_b(client_as(y1), company_id=w.co["B"]).json()["data"]["items"] == []
    #  Người xem phạm vi `own` cũng không.
    own = w.grant("a3", "employee", "own", actions=("read",))
    assert of_b(client_as(own), company_id=w.co["B"]).json()["data"]["items"] == []


def test_bang_het_han_sap_toi_nghi_viec_va_dong_loai_1_trung_phong_chinh(w, client_as):  # noqa: F811
    expired = kn(w, from_date=TODAY - 60 * DAY, to_date=TODAY - 10 * DAY)
    kn(w, emp_key="a3", from_date=TODAY + 5 * DAY, position_label="")
    gone = kn(w, emp_key="a1")
    w.db.get(Employee, w.emp["a1"]).status = "resigned"
    #  Dòng loại Phòng ban TRÙNG cặp (phòng chính, công ty chính) của chính người đó: không hiện lần hai.
    kn_dept(w, "hb", "SH")
    w.db.commit()
    c = client_as(head_b(w))
    #  a3 (A, A.mua) chỉ hiện khi người xem phủ (A.mua, B): cho hb thêm ô "Phòng ban được xem" A.mua.
    w.actor("hb").grant("employee", "dept", inc_dept=["A.mua"])

    items = of_b(c, company_id=w.co["B"]).json()["data"]["items"]
    assert [(i["code"], i["status"]) for i in items] == [("A3", 1)]   # chỉ a3 sắp tới; hết hạn / nghỉ việc bị bỏ
    ended = of_b(c, company_id=w.co["B"], include_ended=1).json()["data"]["items"]
    assert {(i["code"], i["status"]) for i in ended} == {("A3", 1), ("A2", 3)}
    assert expired.id in {i["id"] for i in ended} and gone.id not in {i["id"] for i in ended}
    assert get_members(c, department_id=w.dept["SH"]).json()["data"]["items"] == []   # dòng loại 1 trùng chính: bỏ


def test_bang_loc_theo_cong_ty_kind_va_bat_buoc_mot_trong_hai_id(w, client_as):  # noqa: F811
    kn(w)
    c = client_as(head_b(w))
    assert get_members(c, company_id=w.co["B"]).json()["data"]["total"] == 1
    assert get_members(c, company_id=w.co["A"]).json()["data"]["total"] == 0
    assert get_members(c, company_id=w.co["B"], kind=1).json()["data"]["total"] == 0
    assert c.get(MEMBERS).status_code == 422
    assert c.get(MEMBERS, params={"kind": 2}).status_code == 422
    assert get_members(c, department_id=0).status_code == 422
    assert get_members(c, company_id=w.co["B"], kind=3).status_code == 422
    assert get_members(c, company_id=w.co["B"], include_ended=7).status_code == 422


def test_bang_can_quyen_doc_nhan_su(w, client_as):  # noqa: F811
    kn(w)
    nobody = w.grant("b1", "purchase_request", "all", actions=("read",))
    assert of_b(client_as(nobody), company_id=w.co["B"]).status_code == 403


def test_bang_tran_200_dong_va_co_truncated(w, client_as):  # noqa: F811
    for i in range(members.MAX_ROWS + 3):
        w.db.add(EmployeeConcurrent(employee_id=w.emp["a2"], kind=2, department_id=0, company_id=w.co["B"],
                                    from_date=TODAY - (i + 1) * DAY))
    w.db.commit()
    perm_cache_clear()
    c = client_as(head_b(w))
    data = of_b(c, company_id=w.co["B"]).json()["data"]
    assert len(data["items"]) == members.MAX_ROWS and data["truncated"] is True
    assert data["total"] == members.MAX_ROWS


def test_bang_so_truy_van_co_dinh_khong_theo_so_dong(w, client_as):  # noqa: F811
    kn(w)
    c = client_as(head_b(w))
    one, _ = count_queries(w.db, lambda: of_b(c, company_id=w.co["B"]))
    for i in range(25):
        add_employee(w, f"k{i:02d}", "A", "SH")
        w.db.flush()
        w.db.add(EmployeeConcurrent(employee_id=w.emp[f"k{i:02d}"], kind=2, department_id=0, company_id=w.co["B"],
                                    from_date=TODAY - DAY))
    w.db.commit()
    perm_cache_clear()
    many, resp = count_queries(w.db, lambda: of_b(c, company_id=w.co["B"]))
    assert resp.json()["data"]["total"] == 26
    assert many == one, (one, many)


def test_bang_xep_theo_ho_ten_roi_id(w, client_as):  # noqa: F811
    for key, name in (("a3", "Zeta"), ("a1", "Alpha")):
        emp = w.db.get(Employee, w.emp[key])
        emp.full_name, emp.department_id = name, w.dept["SH"]
        kn(w, emp_key=key)
    kn(w)   # a2 "Nhân sự a2"
    kn(w, emp_key="a1", from_date=TODAY - 90 * DAY, to_date=TODAY - 60 * DAY)   # đã hết, bỏ
    c = client_as(head_b(w))
    names = [i["full_name"] for i in of_b(c, company_id=w.co["B"]).json()["data"]["items"]]
    assert names == ["Alpha", "Nhân sự a2", "Zeta"]


# ── 4. Sơ đồ tổ chức ─────────────────────────────────────────────────────────

def test_so_do_co_khoa_concurrents_va_khong_them_nguoi_kiem_nhiem_vao_nhan_su(w, client_as):  # noqa: F811
    kn(w)
    c = client_as(head_b(w))
    data = c.get("/api/org-chart").json()["data"]
    assert [x["code"] for x in data["concurrents"]] == ["A2"]
    item = data["concurrents"][0]
    assert set(item) == MEMBER_KEYS and not (set(item) & FORBIDDEN_KEYS)
    assert (item["kind"], item["kind_label"], item["department_id"], item["company_id"]) == (2, "Công ty", 0, w.co["B"])
    assert "A2" not in {e["code"] for e in data["employees"]}   # quân số gốc không đổi (Q5 + không đếm trùng)
    assert w.co["B"] in {co["id"] for co in data["companies"]}


def test_so_do_dong_het_han_hoac_nguoi_xem_cho_ngoi_khac_khong_thay(w, client_as):  # noqa: F811
    row = kn(w)
    y1 = w.grant("y1", "employee", "dept", actions=("read",))
    assert client_as(y1).get("/api/org-chart").json()["data"]["concurrents"] == []
    c = client_as(head_b(w))
    assert len(c.get("/api/org-chart").json()["data"]["concurrents"]) == 1
    with_cached_off(row, "het_han", w.db)
    assert c.get("/api/org-chart").json()["data"]["concurrents"] == []
    with_cached_off(row, "sap_toi", w.db)   # sau khi hết hạn: đặt lại thành sắp tới (to_date vẫn hôm qua → đã hết)
    assert c.get("/api/org-chart").json()["data"]["concurrents"] == []


def test_so_do_so_truy_van_co_dinh(w, client_as):  # noqa: F811
    c = client_as(head_b(w))
    kn(w)
    one, resp = count_queries(w.db, lambda: c.get("/api/org-chart"))
    assert len(resp.json()["data"]["concurrents"]) == 1
    added = 0
    for total in (13, 40):   # 1 → 13 → 40 dòng: số truy vấn không đổi
        while added < total - 1:
            add_employee(w, f"s{added:02d}", "A", "SH")
            w.db.flush()
            w.db.add(EmployeeConcurrent(employee_id=w.emp[f"s{added:02d}"], kind=2, department_id=0,
                                        company_id=w.co["B"], from_date=TODAY - DAY))
            added += 1
        w.db.commit()
        many, resp = count_queries(w.db, lambda: c.get("/api/org-chart"))
        assert len(resp.json()["data"]["concurrents"]) == total
        assert many == one, (total, one, many)


# ── 5. Trợ lý AI + /api/auth/me ──────────────────────────────────────────────

def test_tro_ly_ai_tra_concurrent_roles_hai_loai_cua_nguoi_da_duoc_phep_xem(w):
    kn(w)
    kn_dept(w, "a2", "A.mua", position_label="Trưởng nhóm")
    kn(w, company_key="C", position_label="", to_date=TODAY - DAY)   # đã hết: không ra
    a1 = w.grant("a1", "employee", "all", actions=("read",))
    out = T.run_tool(w.db, a1.user, "employee_lookup", {"query": "Nhân sự a2"})
    row = next(r for r in out["items"] if r["code"] == "A2")
    assert row["concurrent_roles"] == ["Phòng Thu mua (Trưởng nhóm)", "Công ty B (Phó phòng)"]
    other = next(r for r in T.run_tool(w.db, a1.user, "employee_lookup", {"query": "Nhân sự a3"})["items"]
                 if r["code"] == "A3")
    assert other["concurrent_roles"] == []
    #  Danh sách trắng vẫn nguyên: không điện thoại / lương lọt theo.
    assert not (set(row) & {"salary_monthly", "allowance_monthly", "id_number", "bank_account_no"})


def test_tro_ly_ai_khong_doi_bo_loc_nguoi_kiem_nhiem_ngoai_pham_vi_van_khong_tra(w):
    """`employee_lookup` KHÔNG bật `include_concurrent`: người xem (SH, B) tra theo tên a2 vẫn không ra (đúng phạm vi hồ sơ)."""
    kn(w)
    hb = head_b(w)
    out = T.run_tool(w.db, hb.user, "employee_lookup", {"query": "Nhân sự a2"})
    assert out["items"] == []


def test_me_tra_kind_va_kind_label_cua_dong_kiem_nhiem(w):
    from app.modules.auth.controller import _me_payload

    kn(w)
    kn_dept(w, "a2", "A.mua")
    payload = _me_payload(w.db, w.actor("a2").user)
    assert [(c["kind"], c["kind_label"]) for c in payload["concurrents"]] == [(1, "Phòng ban"), (2, "Công ty")]
    assert payload["kiem_nhiem"] == ["Phòng Thu mua", "Công ty B (Phó phòng)"]
    assert all("text" not in c for c in payload["concurrents"])


# ── 6. Xóa dòng quá trình công tác loại Kiêm nhiệm giữ dòng kiêm nhiệm ───────

def _attach_file(db, entity: str, entity_id: int) -> FileLink:
    f = StoredFile(filename="qd.pdf", file_key="k", url="u", content_type="application/pdf", size=1, sha256="s")
    db.add(f)
    db.flush()
    link = FileLink(file_id=f.id, entity=entity, entity_id=entity_id, doc_type="", sort_order=0)
    db.add(link)
    db.commit()
    return link


def test_xoa_dong_qtct_kiem_nhiem_giu_dong_kiem_nhiem_va_chi_bo_lien_ket(w):
    a1 = w.grant("a1", "employee", "all", actions=("read", "write"))
    eid = w.emp["a2"]
    wh = EmployeeWorkHistory(employee_id=eid, event_type=4, from_date=TODAY - 30 * DAY,
                             department_id=0, created_by=1, updated_by=1)
    w.db.add(wh)
    w.db.commit()
    linked = kn(w, work_history_id=wh.id)
    other = kn(w, company_key="C", work_history_id=0)
    qd = _attach_file(w.db, "employee_concurrent", linked.id)     # tệp QĐ riêng của dòng kiêm nhiệm
    wh_file = _attach_file(w.db, "employee_work_history", wh.id)  # tệp của dòng QTCT

    whs.delete(w.db, eid, wh.id, a1.user)
    w.db.expire_all()

    assert w.db.get(EmployeeWorkHistory, wh.id) is None
    kept = w.db.get(EmployeeConcurrent, linked.id)
    assert kept is not None and kept.work_history_id == 0
    assert (kept.kind, kept.department_id, kept.company_id, kept.counts_scope) == (2, 0, w.co["B"], True)
    assert w.db.get(FileLink, qd.id) is not None          # tệp của dòng kiêm nhiệm còn
    assert w.db.get(FileLink, wh_file.id) is None          # tệp của dòng QTCT mất theo dòng
    assert w.db.get(EmployeeConcurrent, other.id).work_history_id == 0
    #  Quyền vẫn còn: xóa nhật ký không âm thầm thu hồi phạm vi.
    assert w.db.query(EmployeeConcurrent).filter(EmployeeConcurrent.employee_id == eid).count() == 2


def test_xoa_dong_qtct_khong_dung_lien_ket_cua_nguoi_khac(w):
    a1 = w.grant("a1", "employee", "all", actions=("read", "write"))
    mine = EmployeeWorkHistory(employee_id=w.emp["a2"], event_type=4, from_date=TODAY, created_by=1, updated_by=1,
                               department_id=0)
    theirs = EmployeeWorkHistory(employee_id=w.emp["a3"], event_type=4, from_date=TODAY, created_by=1, updated_by=1,
                                 department_id=0)
    w.db.add_all([mine, theirs])
    w.db.commit()
    row_theirs = kn(w, emp_key="a3", work_history_id=theirs.id)
    whs.delete(w.db, w.emp["a2"], mine.id, a1.user)
    w.db.expire_all()
    assert w.db.get(EmployeeConcurrent, row_theirs.id).work_history_id == theirs.id
