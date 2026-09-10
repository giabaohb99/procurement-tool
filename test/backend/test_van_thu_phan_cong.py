"""Phân công VĂN THƯ theo công ty (tab_seal_clerk) + văn thư tổng.

Cơ chế mới: văn thư (có `write`, phạm vi công ty) chỉ thấy phiếu đóng dấu đã duyệt
của công ty MÌNH ĐƯỢC PHÂN CÔNG; phiếu ĐA công ty chỉ về VĂN THƯ TỔNG. Giám đốc
(chỉ `read` công ty) vẫn thấy mọi phiếu đã duyệt có công ty mình trong danh sách.
"""
from types import SimpleNamespace

from app.core.auth import get_perm_profile
from app.core.scoping import apply_scope
from app.modules.employee.model import Employee
from app.modules.seal_clerk.model import SealClerk
from app.modules.seal_request import model as m
from app.modules.seal_request.schema import SealRequestCreate
from app.modules.seal_request.service import create_seal_request

CTY_A, CTY_B, DEPT = 1, 2, 10


def _person(db, cap_quyen, *, uid, company, scope, **actions):
    emp = Employee(code=f"NV{uid}", full_name=f"NV{uid}", email=f"nv{uid}@dego.vn",
                   department_id=DEPT, company_id=company)
    db.add(emp)
    db.flush()
    cap_quyen(uid, "seal_request", scope=scope, **actions)
    return SimpleNamespace(id=uid, employee_id=emp.id, email=f"nv{uid}@dego.vn"), emp


def _visible(db, user):
    prof = get_perm_profile(db, user)
    q = apply_scope(db.query(m.SealRequest), m.SealRequest, "seal_request", user, prof)
    return {r.id for r in q.all()}


def _make(db, creator, purpose, company_ids, *, status):
    req = create_seal_request(
        db, SealRequestCreate(purpose=purpose, company_ids=company_ids, first_approver_id=500),
        creator, submit=False)
    req.status = status
    db.flush()
    return req


def test_van_thu_thay_dung_phieu_theo_phan_cong(db, cap_quyen):
    ns, _ = _person(db, cap_quyen, uid=6001, company=CTY_A, scope="own", read=True, create=True)
    s_a = _make(db, ns, "[A] đã duyệt", [CTY_A], status=m.SEAL_APPROVED)
    s_ab = _make(db, ns, "[A+B] đã duyệt", [CTY_A, CTY_B], status=m.SEAL_APPROVED)
    _make(db, ns, "[A] nháp", [CTY_A], status=m.SEAL_DRAFT)          # nháp — không ai (văn thư) thấy
    _make(db, ns, "[B] đã duyệt", [CTY_B], status=m.SEAL_APPROVED)   # công ty B

    clerk_a, ea = _person(db, cap_quyen, uid=6002, company=CTY_A, scope="company",
                          read=True, write=True)
    db.add(SealClerk(employee_id=ea.id, company_id=CTY_A, is_head=False))
    head, eh = _person(db, cap_quyen, uid=6003, company=0, scope="company",
                       read=True, write=True)
    db.add(SealClerk(employee_id=eh.id, company_id=0, is_head=True))
    unassigned, _ = _person(db, cap_quyen, uid=6004, company=CTY_A, scope="company",
                            read=True, write=True)
    director, _ = _person(db, cap_quyen, uid=6005, company=CTY_A, scope="company", read=True)
    db.flush()

    # Văn thư A: CHỈ phiếu một công ty A đã duyệt → s_a (không nháp, không đa công ty).
    assert _visible(db, clerk_a) == {s_a.id}
    # Văn thư tổng: CHỈ phiếu đa công ty đã duyệt → s_ab.
    assert _visible(db, head) == {s_ab.id}
    # Văn thư chưa được phân công: không thấy phiếu nào.
    assert _visible(db, unassigned) == set()
    # Giám đốc công ty A (chỉ đọc): mọi phiếu đã duyệt có A trong danh sách → s_a, s_ab.
    assert _visible(db, director) == {s_a.id, s_ab.id}


def test_van_thu_khong_hoat_dong_khong_thay_phieu(db, cap_quyen):
    """Nghỉ phép / Ngưng sử dụng thì văn thư NGỪNG nhận phiếu, kể cả tổng."""
    from app.modules.seal_clerk.model import CLERK_ACTIVE, CLERK_INACTIVE, CLERK_ON_LEAVE

    ns, _ = _person(db, cap_quyen, uid=6101, company=CTY_A, scope="own", read=True, create=True)
    s_a = _make(db, ns, "[A] đã duyệt", [CTY_A], status=m.SEAL_APPROVED)
    s_ab = _make(db, ns, "[A+B] đã duyệt", [CTY_A, CTY_B], status=m.SEAL_APPROVED)

    clerk_a, ea = _person(db, cap_quyen, uid=6102, company=CTY_A, scope="company",
                          read=True, write=True)
    db.add(SealClerk(employee_id=ea.id, company_id=CTY_A, is_head=False, status=CLERK_ON_LEAVE))
    head, eh = _person(db, cap_quyen, uid=6103, company=0, scope="company",
                       read=True, write=True)
    db.add(SealClerk(employee_id=eh.id, company_id=0, is_head=True, status=CLERK_INACTIVE))
    db.flush()

    # Cả hai đều không "Đang hoạt động" → không thấy phiếu nào dù đúng công ty phụ trách.
    assert _visible(db, clerk_a) == set()
    assert _visible(db, head) == set()

    # Bật lại văn thư A (ACTIVE) thì thấy lại phiếu một công ty A; tổng vẫn tắt.
    db.query(SealClerk).filter(SealClerk.employee_id == ea.id).update({"status": CLERK_ACTIVE})
    db.flush()
    assert _visible(db, clerk_a) == {s_a.id}
    assert _visible(db, head) == set()
    assert s_ab.id not in _visible(db, clerk_a)  # phiếu đa công ty vẫn chỉ về tổng


def test_sync_status_ap_cho_moi_dong_va_giu_khi_none(db):
    """`sync(status=…)` đặt trạng thái cho MỌI dòng; `status=None` GIỮ NGUYÊN."""
    from app.modules.seal_clerk import service as sc
    from app.modules.seal_clerk.model import CLERK_ACTIVE, CLERK_INACTIVE, SealClerk

    emp_id = 7101
    sc.sync(db, emp_id, [CTY_A, CTY_B], is_head=True, user_id=1)  # mặc định ACTIVE

    def _statuses():
        return {r.status for r in db.query(SealClerk).filter(SealClerk.employee_id == emp_id).all()}

    assert _statuses() == {CLERK_ACTIVE}

    # Ngưng sử dụng cả nhóm.
    sc.sync(db, emp_id, [CTY_A, CTY_B], is_head=True, user_id=1, status=CLERK_INACTIVE)
    assert _statuses() == {CLERK_INACTIVE}

    # Đổi danh sách công ty mà KHÔNG truyền status → giữ nguyên trạng thái cho dòng cũ,
    # không tự bật lại về ACTIVE.
    sc.sync(db, emp_id, [CTY_A], is_head=True, user_id=1)
    assert _statuses() == {CLERK_INACTIVE}


def test_list_grouped_tra_ve_trang_thai(db):
    """Danh sách gộp trả `status` của văn thư (Đang hoạt động thắng khi lệch)."""
    from app.modules.employee.model import Employee
    from app.modules.seal_clerk import service as sc
    from app.modules.seal_clerk.model import CLERK_ACTIVE, CLERK_INACTIVE, SealClerk

    e1 = Employee(code="VTX", full_name="Văn thư X", company_id=CTY_A)
    db.add(e1)
    db.flush()
    db.add_all([
        SealClerk(employee_id=e1.id, company_id=CTY_A, is_head=False, status=CLERK_INACTIVE),
        SealClerk(employee_id=e1.id, company_id=CTY_B, is_head=False, status=CLERK_ACTIVE),
    ])
    db.flush()

    _, items = sc.list_grouped(db)
    it = next(i for i in items if i["employee_code"] == "VTX")
    #  Một dòng còn ACTIVE → nhóm hiển thị ACTIVE (Đang hoạt động thắng).
    assert it["status"] == CLERK_ACTIVE and it["status_label"] == "Đang hoạt động"


def test_sync_dat_lai_dung_danh_sach_cong_ty(db):
    """`sync` đặt LẠI phân công của một văn thư = đúng danh sách (thêm/bớt + cờ tổng)."""
    from app.modules.seal_clerk import service as sc
    from app.modules.seal_clerk.model import SealClerk

    emp_id = 7001
    db.add(SealClerk(employee_id=emp_id, company_id=CTY_A, is_head=False))
    db.flush()

    def _state():
        rows = db.query(SealClerk).filter(SealClerk.employee_id == emp_id).all()
        return (sorted(r.company_id for r in rows if not r.is_head),
                any(r.is_head for r in rows))

    # Thêm công ty B (giữ A).
    sc.sync(db, emp_id, [CTY_A, CTY_B], is_head=False, user_id=1)
    assert _state() == ([CTY_A, CTY_B], False)

    # Bỏ A, giữ B, bật văn thư tổng.
    sc.sync(db, emp_id, [CTY_B], is_head=True, user_id=1)
    assert _state() == ([CTY_B], True)

    # Bỏ hết công ty + tắt tổng → không còn phân công nào.
    sc.sync(db, emp_id, [], is_head=False, user_id=1)
    assert _state() == ([], False)

    # Trùng lặp trong danh sách gửi lên không đẻ dòng thừa.
    sc.sync(db, emp_id, [CTY_A, CTY_A], is_head=False, user_id=1)
    assert _state() == ([CTY_A], False)


def test_list_grouped_moi_van_thu_mot_dong(db):
    """Danh sách gộp: một văn thư = MỘT dòng, dù có nhiều dòng công ty ở bảng nối."""
    from app.modules.employee.model import Employee
    from app.modules.seal_clerk import service as sc
    from app.modules.seal_clerk.model import SealClerk

    e1 = Employee(code="VT1", full_name="Văn thư Một", company_id=CTY_A)
    e2 = Employee(code="VT2", full_name="Văn thư Hai", company_id=CTY_A)
    db.add_all([e1, e2])
    db.flush()
    # e1: 2 công ty + văn thư tổng (3 dòng nối) → vẫn 1 dòng danh sách.
    db.add_all([
        SealClerk(employee_id=e1.id, company_id=CTY_A, is_head=False),
        SealClerk(employee_id=e1.id, company_id=CTY_B, is_head=False),
        SealClerk(employee_id=e1.id, company_id=0, is_head=True),
        SealClerk(employee_id=e2.id, company_id=CTY_A, is_head=False),
    ])
    db.flush()

    total, items = sc.list_grouped(db)
    assert total == 2  # HAI văn thư, không phải 4 dòng nối
    by_code = {it["employee_code"]: it for it in items}
    assert by_code["VT1"]["company_count"] == 2 and by_code["VT1"]["is_head"] is True
    assert by_code["VT2"]["company_count"] == 1 and by_code["VT2"]["is_head"] is False

    # Tìm theo tên văn thư.
    _, hits = sc.list_grouped(db, search="Hai")
    assert [h["employee_code"] for h in hits] == ["VT2"]


def test_giam_doc_kem_own_write_van_thay_phieu_cong_ty(db, cap_quyen):
    """Giám đốc (read company) DÙ có thêm own-write (vai trò nền `employee`) vẫn thấy
    phiếu Đã duyệt của công ty — KHÔNG bị nhánh Văn thư che khuất.

    Trước sửa: `has_write` đọc `perms_union` toàn cục, mà own-write bật cờ đó, nên grant
    company của Giám đốc bị đẩy vào nhánh Văn thư (tra bảng phân công) → thấy rỗng."""
    ns, _ = _person(db, cap_quyen, uid=6201, company=CTY_A, scope="own", read=True, create=True)
    s_a = _make(db, ns, "[A] đã duyệt", [CTY_A], status=m.SEAL_APPROVED)
    _make(db, ns, "[A] nháp", [CTY_A], status=m.SEAL_DRAFT)

    emp = Employee(code="GD1", full_name="Giám đốc", email="gd1@dego.vn",
                   department_id=99, company_id=CTY_A)
    db.add(emp)
    db.flush()
    #  Hai grant như hệ thật: own r/c/w (vai trò nền) + company read (Giám đốc).
    cap_quyen(6202, "seal_request", scope="own", read=True, create=True, write=True)
    cap_quyen(6202, "seal_request", scope="company", read=True)
    director = SimpleNamespace(id=6202, employee_id=emp.id, email="gd1@dego.vn")

    vis = _visible(db, director)
    assert s_a.id in vis            # thấy phiếu Đã duyệt của công ty
    assert len(vis) == 1            # chỉ Đã duyệt/Hoàn thành, KHÔNG nháp; không tạo phiếu nào


def test_chi_van_thu_duoc_phan_cong_moi_thao_tac_cong_2(db, cap_quyen):
    """Cổng-2 (đóng dấu / trả / từ chối) CHỈ cho Văn thư được phân công — `is_assigned_clerk`.

    Nhân sự thường có own-write nên get_scoped('write') chạm phiếu Đã duyệt của mình,
    nhưng KHÔNG được đóng dấu; phiếu đa công ty chỉ về Văn thư tổng."""
    from app.modules.seal_request import service

    ns, _ = _person(db, cap_quyen, uid=6301, company=CTY_A, scope="own", read=True, create=True)
    req_a = _make(db, ns, "[A] đã duyệt", [CTY_A], status=m.SEAL_APPROVED)
    req_ab = _make(db, ns, "[A+B] đã duyệt", [CTY_A, CTY_B], status=m.SEAL_APPROVED)

    assert not service.is_assigned_clerk(db, ns, req_a)   # người tạo KHÔNG phải văn thư

    emp_c = Employee(code="VTA", full_name="VT A", company_id=CTY_A)
    db.add(emp_c)
    db.flush()
    db.add(SealClerk(employee_id=emp_c.id, company_id=CTY_A, is_head=False))
    db.flush()
    clerk = SimpleNamespace(id=6302, employee_id=emp_c.id)
    assert service.is_assigned_clerk(db, clerk, req_a)        # phiếu 1 công ty A → văn thư A
    assert not service.is_assigned_clerk(db, clerk, req_ab)   # phiếu đa công ty → không phải A

    emp_h = Employee(code="VTT", full_name="VT Tổng", company_id=0)
    db.add(emp_h)
    db.flush()
    db.add(SealClerk(employee_id=emp_h.id, company_id=0, is_head=True))
    db.flush()
    head = SimpleNamespace(id=6303, employee_id=emp_h.id)
    assert service.is_assigned_clerk(db, head, req_ab)        # đa công ty → văn thư tổng
    assert not service.is_assigned_clerk(db, head, req_a)     # tổng KHÔNG lo phiếu 1 công ty


def test_van_thu_khong_gan_ho_so_nhan_su_bi_chan(db, cap_quyen):
    #  Tài khoản có quyền write phạm vi công ty nhưng KHÔNG gắn nhân sự (employee_id=0)
    #  → chặn hết, không đọc trộm được phiếu nào.
    cap_quyen(6006, "seal_request", scope="company", read=True, write=True)
    user = SimpleNamespace(id=6006, employee_id=0, email="x@dego.vn")
    assert _visible(db, user) == set()
