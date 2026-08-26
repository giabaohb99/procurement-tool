"""B-07 / N-14 — thiếu khai phạm vi thì CHẶN, không phải thấy tất.

Lỗ hổng gốc: `_role_scope_cond` trả `None` cho entity vắng mặt trong `SCOPE_FIELDS`,
mà `None` nghĩa là *không lọc gì*. Chỉ 12/39 entity được khai, nên 27 entity còn lại
bỏ qua sạch trục phạm vi — vai trò đặt `own` hay `dept` cũng vẫn đọc được toàn hệ.

Bài kiểm ở đây chốt ba thứ, theo thứ tự quan trọng:
  1. **Đủ 39** — thêm entity vào `ENTITIES` mà quên khai là test đỏ ngay, chứ không
     lặng lẽ mở toang. Đây là bài giữ cho lỗ hổng không quay lại.
  2. **Chặn khi không dựng nổi điều kiện** — bốn nhánh rơi tự do cũ.
  3. **`PUBLIC` vẫn thấy tất** — để việc siết lại không vô tình khóa danh mục dùng chung.
"""
import pytest
from types import SimpleNamespace

from app.core.permissions import ENTITIES
from app.core.scoping import (PUBLIC, SCOPE_FIELDS, _role_scope_cond, get_scoped,
                              scope_condition)


def _ai_do(uid=1, company_id=0, dept_id=0, employee_id=0):
    """Cặp (user, profile) tối thiểu — đủ cho `_role_scope_cond`."""
    return (SimpleNamespace(id=uid),
            {"company_id": company_id, "dept_id": dept_id, "dept_name": "",
             "employee_id": employee_id, "emp_code": "", "emp_name": ""})


def _dem(db, Model, cond):
    """Số dòng lọt qua điều kiện. `None` = không lọc gì (thấy tất)."""
    q = db.query(Model)
    return q.count() if cond is None else q.filter(cond).count()


def _hai_hop_dong(db, company_id):
    """Hai hợp đồng thuộc hai pháp nhân khác nhau.

    Có dữ liệu thật mới chứng minh được là đã lọc: đếm ra 0 trên bảng rỗng thì
    điều kiện nào cũng "đúng".
    """
    from app.modules.contract.model import Contract
    db.add_all([Contract(code="HD001", company_id=company_id, title="Của mình"),
                Contract(code="HD002", company_id=company_id + 99, title="Của công ty khác")])
    db.flush()
    assert db.query(Contract).count() == 2
    return Contract


# ── 1. Đủ 39 ────────────────────────────────────────────────────────────────────

def test_moi_entity_deu_phai_duoc_khai_pham_vi():
    """Bài giữ của B-07 — đừng nới lỏng nó.

    Thêm entity mới vào `core/permissions.ENTITIES` thì phải khai luôn ở `SCOPE_FIELDS`:
    có chiều thật thì khai cột, cố ý không lọc thì khai `PUBLIC` kèm lý do. Không có
    lựa chọn thứ ba — bỏ trống là quay lại đúng lỗ N-14.
    """
    thieu = [e for e in ENTITIES if e not in SCOPE_FIELDS]
    assert thieu == [], (
        f"{len(thieu)} entity chưa khai phạm vi: {thieu}. "
        "Khai cột thật hoặc khai PUBLIC (kèm lý do) trong app/core/scoping.py."
    )


def test_khong_khai_thua_entity_khong_ton_tai():
    """Khai dư = khai cho một entity không ai dùng → tưởng đã che mà thật ra chưa."""
    thua = [e for e in SCOPE_FIELDS if e not in ENTITIES]
    assert thua == [], f"khai thừa, không có trong ENTITIES: {thua}"


def test_du_44_entity():
    """Chốt cứng con số để lần sau đọc test là biết ngay quy mô.

    39 → 42 ngày 25/08/2026 (CR-157): tách `doc_template`, `doc_numbering_rule`,
    `doc_link_rule` ra khỏi `doc_type` để phân quyền Văn thư đi theo MÀN HÌNH
    chứ không theo tên bảng.
    42 → 43: thêm entity `assistant` cho Trợ lý AI (gác `assistant.read`).
    43 → 44 ngày 26/08/2026: thêm `mailbox` — ai được KHAI hộp thư gửi và cấp
    cho người khác dùng (quyền *dùng* thì khai đích danh ở `tab_mailbox_member`).
    """
    assert len(ENTITIES) == 44
    assert len(SCOPE_FIELDS) == 44


# ── 2. Không dựng nổi điều kiện thì chặn ────────────────────────────────────────

def test_entity_la_thi_chan_het(db):
    """Entity chưa khai (hoặc gõ sai tên) → chặn sạch, không phải mở toang."""
    from app.modules.company.model import Company
    user, profile = _ai_do(company_id=1)
    cond = _role_scope_cond(Company, "entity_khong_ton_tai", "company", user, profile)
    assert cond is not None
    assert _dem(db, Company, cond) == 0


def test_company_nhung_nguoi_dung_chua_gan_phap_nhan_thi_chan(db, seed):
    """`company_id = 0` — đây là nhánh nguy hiểm nhất, và cũng đông người dính nhất.

    Trước B-07 nhánh này trả `None`: phạm vi ghi là "công ty" mà thực tế rộng bằng
    "tất cả". Nay chặn, cùng luật với nhánh `dept` (chưa gắn phòng → không thấy gì).
    Hệ quả vận hành: nhân sự chưa gắn pháp nhân sẽ thấy màn trắng — phải sửa DỮ LIỆU
    (gắn `company_id` cho nhân sự), đừng nới lại điều kiện.
    """
    Contract = _hai_hop_dong(db, seed.company_id)
    user, profile = _ai_do(company_id=0)
    cond = _role_scope_cond(Contract, "contract", "company", user, profile)
    assert cond is not None
    assert _dem(db, Contract, cond) == 0

    # …và khi có gắn pháp nhân thì vẫn ra đúng phần của mình (không phải chặn mù).
    user, profile = _ai_do(company_id=seed.company_id)
    cond = _role_scope_cond(Contract, "contract", "company", user, profile)
    assert _dem(db, Contract, cond) == 1


def test_company_nhung_entity_khong_co_cot_phap_nhan_thi_chan(db, seed):
    """`survey` chỉ khai `owner`. Không có cột pháp nhân mà vẫn trả `None` thì
    "company" rộng đúng bằng "all" — chính là lỗ N-14."""
    from app.modules.survey.model import Survey
    user, profile = _ai_do(company_id=7)
    assert db.query(Survey).count() > 0        # có dữ liệu thật để chứng minh là đã lọc
    cond = _role_scope_cond(Survey, "survey", "company", user, profile)
    assert cond is not None
    assert _dem(db, Survey, cond) == 0


def test_dept_nhung_entity_khong_co_chieu_nao_thi_chan(db, seed):
    """`user` chỉ khai `self` — không phòng ban, không pháp nhân, không chủ sở hữu."""
    from app.modules.user.model import User
    user, profile = _ai_do(dept_id=3)
    assert db.query(User).count() > 0
    cond = _role_scope_cond(User, "user", "dept", user, profile)
    assert cond is not None
    assert _dem(db, User, cond) == 0


def test_pham_vi_la_thi_chan(db, seed):
    """Chuỗi phạm vi lạ (dữ liệu hỏng, gõ tay vào DB) → chặn, không rơi về thấy tất."""
    Contract = _hai_hop_dong(db, seed.company_id)
    user, profile = _ai_do(company_id=seed.company_id)
    cond = _role_scope_cond(Contract, "contract", "nhap_nham", user, profile)
    assert cond is not None
    assert _dem(db, Contract, cond) == 0


# ── 3. Khai PUBLIC thì vẫn thấy tất ─────────────────────────────────────────────

@pytest.mark.parametrize("entity", ["supplier", "product", "warehouse", "unit",
                                    "item_group", "brand", "role", "report"])
def test_entity_cong_khai_khong_bi_loc(entity):
    """Danh mục dùng chung phải KHÔNG đổi hành vi sau B-07.

    Đây là bài chứng minh việc siết mặc định là **no-op** với dữ liệu gốc: giấu nhà
    cung cấp thì tắt bằng QUYỀN `supplier.read`, không phải bằng phạm vi.
    """
    from app.modules.company.model import Company
    assert SCOPE_FIELDS[entity] is PUBLIC
    user, profile = _ai_do(company_id=0)
    for scope in ("own", "dept", "company", "all"):
        assert _role_scope_cond(Company, entity, scope, user, profile) is None


# ── 4. Chiều thật của các entity mới khai ───────────────────────────────────────

def test_company_loc_theo_chinh_id_cua_no(db, seed):
    """Bảng công ty lấy `id` làm chiều pháp nhân, không phải `company_id`."""
    from app.modules.company.model import Company
    khac = Company(name="Cty Khác", code="CT02", is_active=True)
    db.add(khac)
    db.flush()
    assert db.query(Company).count() == 2

    user, profile = _ai_do(company_id=seed.company_id)
    cond = _role_scope_cond(Company, "company", "company", user, profile)
    con_lai = db.query(Company).filter(cond).all()
    assert [c.id for c in con_lai] == [seed.company_id]


def test_department_loc_theo_phap_nhan_chu_quan(db, seed):
    from app.modules.department.model import Department
    lac = Department(code="DEPT99", name="Phòng Cty Khác", company_id=999, is_active=True)
    db.add(lac)
    db.flush()

    user, profile = _ai_do(company_id=seed.company_id)
    cond = _role_scope_cond(Department, "department", "company", user, profile)
    con_lai = db.query(Department).filter(cond).all()
    assert lac.id not in [d.id for d in con_lai]
    assert seed.dept_id in [d.id for d in con_lai]


def test_user_own_la_dung_tai_khoan_cua_minh(db, seed):
    """`own` trên `user` = tài khoản gắn với hồ sơ nhân sự của chính mình."""
    from app.modules.user.model import User
    user, profile = _ai_do(uid=seed.u_req_id, employee_id=seed.emp_req_id)
    cond = _role_scope_cond(User, "user", "own", user, profile)
    con_lai = db.query(User).filter(cond).all()
    assert [u.id for u in con_lai] == [seed.u_req_id]


# ── 5. Đường vòng theo id — `get_scoped` ────────────────────────────────────────

def test_get_scoped_chan_go_thang_id_vao_url(db, seed):
    """Danh sách giấu đúng nhưng `db.get(Model, id)` thì đi thẳng khóa chính.

    Đây là đường vòng của mọi endpoint lấy/sửa/xóa một dòng — `get_scoped` sinh ra để
    bịt nó, nơi gọi trả 404 y như id không tồn tại.
    """
    from app.modules.company.model import Company
    khac = Company(name="Cty Khác", code="CT02", is_active=True)
    db.add(khac)
    db.flush()

    user = SimpleNamespace(id=seed.u_req_id)
    profile = {"company_id": seed.company_id, "dept_id": 0, "dept_name": "",
               "employee_id": seed.emp_req_id, "emp_code": "", "emp_name": "",
               "grants": [{"perms": {"company": {"read": True, "scope": "company"}},
                           "scope": {}}]}

    assert get_scoped(db, Company, "company", seed.company_id, user, profile) is not None
    assert get_scoped(db, Company, "company", khac.id, user, profile) is None


def test_khong_grant_nao_thi_khong_thay_gi(db, seed):
    """Nhắc lại hợp đồng ba giá trị của `scope_condition`: không grant = `false()`,
    không phải `None`. Bài này giữ cho việc siết mặc định không đảo nhầm hai thứ đó."""
    from app.modules.company.model import Company
    user = SimpleNamespace(id=seed.u_req_id)
    assert _dem(db, Company, scope_condition(Company, "company", user, {"grants": []})) == 0
