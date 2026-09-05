"""B-07 / N-14 — thiếu khai phạm vi thì CHẶN, không phải thấy tất.

Lỗ hổng gốc: `_role_scope_cond` trả `None` cho entity vắng mặt trong `SCOPE_FIELDS`,
mà `None` nghĩa là *không lọc gì*. Chỉ 12/39 entity được khai, nên 27 entity còn lại
bỏ qua sạch trục phạm vi — vai trò đặt `own` hay `dept` cũng vẫn đọc được toàn hệ.

Bài kiểm ở đây chốt ba thứ, theo thứ tự quan trọng:
  1. **Đủ 39** — thêm entity vào `ENTITIES` mà quên khai là test đỏ ngay, chứ không
     lặng lẽ mở toang. Đây là bài giữ cho lỗ hổng không quay lại.
  2. **Chặn khi không dựng nổi điều kiện** — bốn nhánh rơi tự do cũ.
  3. **`PUBLIC` vẫn thấy tất** — để việc siết lại không vô tình khóa danh mục dùng chung.

Phần DỰNG DỮ LIỆU viết lại trên `scope_factory` (cụm 00, 05/09/2026). Đổi đúng hai
thứ, mọi khẳng định giữ nguyên từng chữ:

  * hồ sơ quyền không còn là `dict` gõ tay mà do `get_perm_profile` dựng từ tài
    khoản thật — hồ sơ gõ tay thiếu `dept_ids`/`dept_names` (CR-167) nên nó kiểm
    một hình dạng dữ liệu KHÔNG còn tồn tại ở chạy thật;
  * `get_scoped` nhận grant thật (Role + Permission + UserRole) thay cho một
    `{"grants": [...]}` bịa ra, tức là đi qua đúng đường mà endpoint đi.
"""
import pytest

from app.core.permissions import ENTITIES
from app.core.scoping import (PUBLIC, SCOPE_FIELDS, _role_scope_cond, get_scoped,
                              scope_condition)


def count_rows(db, Model, cond):
    """Số dòng lọt qua điều kiện. `None` = không lọc gì (thấy tất)."""
    q = db.query(Model)
    return q.count() if cond is None else q.filter(cond).count()


def make_two_contracts(world):
    """Hai hợp đồng thuộc hai pháp nhân khác nhau.

    Có dữ liệu thật mới chứng minh được là đã lọc: đếm ra 0 trên bảng rỗng thì
    điều kiện nào cũng "đúng".
    """
    from app.modules.contract.model import Contract
    world.db.add_all([Contract(code="HD001", company_id=world.co["A"], title="Của mình"),
                      Contract(code="HD002", company_id=world.co["B"],
                               title="Của công ty khác")])
    world.db.flush()
    assert world.db.query(Contract).count() == 2
    return Contract


# ── 1. Đủ 39 ────────────────────────────────────────────────────────────────────

def test_moi_entity_deu_phai_duoc_khai_pham_vi():
    """Bài giữ của B-07 — đừng nới lỏng nó.

    Thêm entity mới vào `core/permissions.ENTITIES` thì phải khai luôn ở `SCOPE_FIELDS`:
    có chiều thật thì khai cột, cố ý không lọc thì khai `PUBLIC` kèm lý do. Không có
    lựa chọn thứ ba — bỏ trống là quay lại đúng lỗ N-14.
    """
    missing = [e for e in ENTITIES if e not in SCOPE_FIELDS]
    assert missing == [], (
        f"{len(missing)} entity chưa khai phạm vi: {missing}. "
        "Khai cột thật hoặc khai PUBLIC (kèm lý do) trong app/core/scoping.py."
    )


def test_khong_khai_thua_entity_khong_ton_tai():
    """Khai dư = khai cho một entity không ai dùng → tưởng đã che mà thật ra chưa."""
    excess = [e for e in SCOPE_FIELDS if e not in ENTITIES]
    assert excess == [], f"khai thừa, không có trong ENTITIES: {excess}"


def test_du_53_entity():
    """Chốt cứng con số để lần sau đọc test là biết ngay quy mô.

    39 → 42 ngày 25/08/2026 (CR-157): tách `doc_template`, `doc_numbering_rule`,
    `doc_link_rule` ra khỏi `doc_type` để phân quyền Văn thư đi theo MÀN HÌNH
    chứ không theo tên bảng.
    42 → 43: thêm entity `assistant` cho Trợ lý AI (gác `assistant.read`).
    43 → 44 ngày 26/08/2026: thêm `mailbox` — ai được KHAI hộp thư gửi và cấp
    cho người khác dùng (quyền *dùng* thì khai đích danh ở `tab_mailbox_member`).
    44 → 45 ngày 27/08/2026: thêm `forum_post` (Diễn đàn, F0) — PUBLIC vì ai
    thấy bài nào đi theo luật audience riêng của API feed, entity chỉ gác cổng
    kiểm duyệt của `forum_admin`.
    45 → 46 ngày 28/08/2026: thêm `work_task` (phân hệ Công việc, CR-216/W0).
    PUBLIC là CỐ Ý và có điều kiện kèm: phạm vi thật của phân hệ là "theo tư cách
    THÀNH VIÊN của list", không diễn đạt được bằng cột của `apply_scope` — đổi
    lại mọi query trong `app/modules/work/` phải tự lọc qua `visible_list_ids`
    (`doc/erp/cong-viec/04-phan-quyen.md` §2).
    46 → 47 ngày 03/09/2026: thêm `forum_board` (chuyên mục kiểu VOZ, F13a) —
    PUBLIC cùng lý do với `forum_post`: entity chỉ gác CRUD cấu trúc nhóm/box
    của `forum_admin`, ai thấy gì do luật audience của API diễn đàn.
    47 → 51 ngày 03/09/2026: phân hệ Nghỉ phép (CR-259) thêm bốn khóa —
    `leave_request` · `leave_balance` · `leave_type` · `holiday`. Bốn chứ không
    một: nộp đơn, cấp quỹ và sửa luật nghỉ là ba việc của ba nhóm người, gộp lại
    thì cho ai xem đơn của mình là cho họ tự tặng thêm ngày phép. Hai khóa đầu
    lọc thật; hai khóa danh mục khai PUBLIC kèm lý do ở `scoping.py`.
    51 → 53 ngày 04/09/2026: Đặt phòng họp (duoc-CR-279) thêm `room_booking` +
    `meeting_room`. Hai chứ không một: đặt phòng là việc của mọi người, khai
    danh mục phòng là việc quản trị — cho quyền sửa danh mục KHÁC cho quyền đặt.
    """
    assert len(ENTITIES) == 53
    assert len(SCOPE_FIELDS) == 53


# ── 2. Không dựng nổi điều kiện thì chặn ────────────────────────────────────────

def test_entity_la_thi_chan_het(db, world):
    """Entity chưa khai (hoặc gõ sai tên) → chặn sạch, không phải mở toang."""
    from app.modules.company.model import Company
    a1 = world.actor("a1")
    cond = _role_scope_cond(Company, "entity_khong_ton_tai", "company",
                            a1.user, a1.profile())
    assert cond is not None
    assert count_rows(db, Company, cond) == 0


def test_company_nhung_nguoi_dung_chua_gan_phap_nhan_thi_chan(db, world):
    """`company_id = 0` — đây là nhánh nguy hiểm nhất, và cũng đông người dính nhất.

    Trước B-07 nhánh này trả `None`: phạm vi ghi là "công ty" mà thực tế rộng bằng
    "tất cả". Nay chặn, cùng luật với nhánh `dept` (chưa gắn phòng → không thấy gì).
    Hệ quả vận hành: nhân sự chưa gắn pháp nhân sẽ thấy màn trắng — phải sửa DỮ LIỆU
    (gắn `company_id` cho nhân sự), đừng nới lại điều kiện.
    """
    Contract = make_two_contracts(world)
    chua_gan = world.actor("khongcty")           # hồ sơ nhân sự chưa gắn pháp nhân
    assert chua_gan.profile()["company_id"] == 0
    cond = _role_scope_cond(Contract, "contract", "company",
                            chua_gan.user, chua_gan.profile())
    assert cond is not None
    assert count_rows(db, Contract, cond) == 0

    # …và khi có gắn pháp nhân thì vẫn ra đúng phần của mình (không phải chặn mù).
    a1 = world.actor("a1")
    cond = _role_scope_cond(Contract, "contract", "company", a1.user, a1.profile())
    assert count_rows(db, Contract, cond) == 1


def test_company_nhung_entity_khong_co_cot_phap_nhan_thi_chan(db, world):
    """`survey` chỉ khai `owner`. Không có cột pháp nhân mà vẫn trả `None` thì
    "company" rộng đúng bằng "all" — chính là lỗ N-14."""
    from app.modules.survey.model import Survey
    db.add_all([Survey(code="KS-001", survey_type="product", status="approved"),
                Survey(code="KS-002", survey_type="product", status="approved")])
    db.flush()
    a1 = world.actor("a1")
    assert db.query(Survey).count() > 0        # có dữ liệu thật để chứng minh là đã lọc
    cond = _role_scope_cond(Survey, "survey", "company", a1.user, a1.profile())
    assert cond is not None
    assert count_rows(db, Survey, cond) == 0


def test_dept_nhung_entity_khong_co_chieu_nao_thi_chan(db, world):
    """`user` chỉ khai `self` — không phòng ban, không pháp nhân, không chủ sở hữu."""
    from app.modules.user.model import User
    a1 = world.actor("a1")
    assert db.query(User).count() > 0
    cond = _role_scope_cond(User, "user", "dept", a1.user, a1.profile())
    assert cond is not None
    assert count_rows(db, User, cond) == 0


def test_pham_vi_la_thi_chan(db, world):
    """Chuỗi phạm vi lạ (dữ liệu hỏng, gõ tay vào DB) → chặn, không rơi về thấy tất."""
    Contract = make_two_contracts(world)
    a1 = world.actor("a1")
    cond = _role_scope_cond(Contract, "contract", "nhap_nham", a1.user, a1.profile())
    assert cond is not None
    assert count_rows(db, Contract, cond) == 0


# ── 3. Khai PUBLIC thì vẫn thấy tất ─────────────────────────────────────────────

@pytest.mark.parametrize("entity", ["supplier", "product", "warehouse", "unit",
                                    "item_group", "brand", "role", "report"])
def test_entity_cong_khai_khong_bi_loc(world, entity):
    """Danh mục dùng chung phải KHÔNG đổi hành vi sau B-07.

    Đây là bài chứng minh việc siết mặc định là **no-op** với dữ liệu gốc: giấu nhà
    cung cấp thì tắt bằng QUYỀN `supplier.read`, không phải bằng phạm vi.
    """
    from app.modules.company.model import Company
    assert SCOPE_FIELDS[entity] is PUBLIC
    chua_gan = world.actor("khongcty")
    for scope in ("own", "dept", "company", "all"):
        assert _role_scope_cond(Company, entity, scope,
                                chua_gan.user, chua_gan.profile()) is None


# ── 4. Chiều thật của các entity mới khai ───────────────────────────────────────

def test_company_loc_theo_chinh_id_cua_no(db, world):
    """Bảng công ty lấy `id` làm chiều pháp nhân, không phải `company_id`."""
    from app.modules.company.model import Company
    assert db.query(Company).count() == 2

    a1 = world.actor("a1")
    cond = _role_scope_cond(Company, "company", "company", a1.user, a1.profile())
    remaining = db.query(Company).filter(cond).all()
    assert [c.id for c in remaining] == [world.co["A"]]


def test_department_loc_theo_phap_nhan_chu_quan(db, world):
    from app.modules.department.model import Department
    lac = Department(code="DEPT99", name="Phòng Cty Khác", company_id=999, is_active=True)
    db.add(lac)
    db.flush()

    a1 = world.actor("a1")
    cond = _role_scope_cond(Department, "department", "company", a1.user, a1.profile())
    remaining = db.query(Department).filter(cond).all()
    assert lac.id not in [d.id for d in remaining]
    assert world.dept["A.kt"] in [d.id for d in remaining]


def test_user_own_la_dung_tai_khoan_cua_minh(db, world):
    """`own` trên `user` = tài khoản gắn với hồ sơ nhân sự của chính mình."""
    from app.modules.user.model import User
    a1 = world.actor("a1")
    cond = _role_scope_cond(User, "user", "own", a1.user, a1.profile())
    remaining = db.query(User).filter(cond).all()
    assert [u.id for u in remaining] == [world.user_id("a1")]


# ── 5. Đường vòng theo id — `get_scoped` ────────────────────────────────────────

def test_get_scoped_chan_go_thang_id_vao_url(db, world):
    """Danh sách giấu đúng nhưng `db.get(Model, id)` thì đi thẳng khóa chính.

    Đây là đường vòng của mọi endpoint lấy/sửa/xóa một dòng — `get_scoped` sinh ra để
    bịt nó, nơi gọi trả 404 y như id không tồn tại.
    """
    from app.modules.company.model import Company
    a1 = world.grant("a1", "company", scope="company")
    profile = a1.profile()

    assert get_scoped(db, Company, "company", world.co["A"], a1.user, profile) is not None
    assert get_scoped(db, Company, "company", world.co["B"], a1.user, profile) is None


def test_khong_grant_nao_thi_khong_thay_gi(db, world):
    """Nhắc lại hợp đồng ba giá trị của `scope_condition`: không grant = `false()`,
    không phải `None`. Bài này giữ cho việc siết mặc định không đảo nhầm hai thứ đó."""
    from app.modules.company.model import Company
    a1 = world.actor("a1")
    assert a1.profile()["grants"] == []
    assert count_rows(db, Company, scope_condition(Company, "company",
                                                   a1.user, a1.profile())) == 0
