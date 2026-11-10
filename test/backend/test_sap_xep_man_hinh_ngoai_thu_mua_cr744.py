"""duoc-CR-744 (đợt 2 / W1) - sắp xếp cột ở các màn NGOÀI Thu mua: YCTT, Duyệt dấu, Phân công
văn thư, Nghỉ phép, Đặt phòng họp, và bảng "Kết quả khảo sát đã duyệt".

Mỗi khóa xếp theo ĐÚNG thứ ô đang hiện (tên chứ không id, vòng đời chứ không chữ cái của mã),
ô trống xuống cuối, trùng giá trị thì id giảm dần.
"""
import json
from datetime import date, datetime
from types import SimpleNamespace

import pytest
from starlette.datastructures import QueryParams

from app.core.base_controller import apply_sort_from_request
from app.modules.company.model import Company
from app.modules.leave import request_controller as leave_controller
from app.modules.leave.request_model import LeaveRequest
from app.modules.leave.sort_expressions import list_sort_allow as leave_allow
from app.modules.meeting_room import controller as room_controller
from app.modules.meeting_room.model import MeetingRoom, RoomBooking
from app.modules.meeting_room.sort_expressions import list_sort_allow as room_allow
from app.modules.payment_request.model import PaymentRequest
from app.modules.payment_request.sort_expressions import list_sort_allow as pr_allow
from app.modules.seal_clerk import service as clerk_service
from app.modules.seal_request.model import SealRequest
from app.modules.seal_request.sort_expressions import list_sort_allow as seal_allow


class _Req:
    def __init__(self, **params):
        self.query_params = QueryParams(params)


def _codes(query):
    return [r.code for r in query.all()]


# ── YCTT ─────────────────────────────────────────────────────────────────────────────────
def _yctt(db, code, **kw):
    row = PaymentRequest(code=code, **kw)
    db.add(row)
    db.flush()
    return row


def _sort_yctt(db, key, direction):
    return apply_sort_from_request(db.query(PaymentRequest), PaymentRequest,
                                   _Req(sort_by=key, sort_dir=direction),
                                   default=PaymentRequest.id.desc(), allow=pr_allow())


def test_yctt_loai_no_xep_theo_chu_cua_nhan_khong_theo_ma(db):
    # Nhãn: Chi phí nhập khẩu < Hàng hóa < Thanh toán nghỉ phép < Vận chuyển
    # (xếp theo mã tiếng Anh sẽ ra goods < import_cost < leave_encashment < shipping)
    for code, src in (("G", "goods"), ("S", "shipping"), ("I", "import_cost"), ("L", "leave_encashment")):
        _yctt(db, code, source_type=src)
    assert _codes(_sort_yctt(db, "source_type", "asc")) == ["I", "G", "L", "S"]
    assert _codes(_sort_yctt(db, "source_type", "desc")) == ["S", "L", "G", "I"]


def test_yctt_hinh_thuc_tt_chuyen_khoan_truoc_tien_mat(db):
    _yctt(db, "C", payment_method="cash")
    _yctt(db, "T", payment_method="transfer")
    assert _codes(_sort_yctt(db, "payment_method", "asc")) == ["T", "C"]
    assert _codes(_sort_yctt(db, "payment_method", "desc")) == ["C", "T"]


def test_yctt_trang_thai_theo_vong_doi_khong_theo_chu_cai(db):
    for code, st in (("P", "paid"), ("D", "draft"), ("X", "cancelled"), ("A", "approved"), ("S", "submitted")):
        _yctt(db, code, status=st)
    assert _codes(_sort_yctt(db, "status", "asc")) == ["D", "S", "A", "P", "X"]


def test_yctt_so_tien_so_0_la_gia_tri_that(db):
    _yctt(db, "Z", total=0)
    _yctt(db, "M", total=50)
    _yctt(db, "N", total=7)
    assert _codes(_sort_yctt(db, "total", "asc")) == ["Z", "N", "M"]
    assert _codes(_sort_yctt(db, "total", "desc")) == ["M", "N", "Z"]


def test_yctt_nha_cung_cap_xep_theo_chu_dang_hien_ten_thieu_thi_ma(db):
    _yctt(db, "A", supplier_name="Zeta", supplier_code="A1")
    _yctt(db, "B", supplier_name="", supplier_code="Alpha")     # ô hiện "Alpha"
    _yctt(db, "C", supplier_name="  ", supplier_code="Mid")     # ô hiện "Mid"
    _yctt(db, "D", supplier_name="", supplier_code="")          # ô trống
    assert _codes(_sort_yctt(db, "supplier_name", "asc")) == ["B", "C", "A", "D"]
    assert _codes(_sort_yctt(db, "supplier_name", "desc")) == ["A", "C", "B", "D"]


def test_yctt_cong_ty_va_nguoi_yeu_cau_xep_theo_ten(db, seed):
    from app.modules.employee.model import Employee

    # Đặt tên ASCII để thứ tự giống nhau ở SQLite (so nhị phân) lẫn MySQL (so không phân biệt hoa thường).
    db.get(Employee, seed.emp_req_id).full_name = "Anh Alpha"
    db.get(Employee, seed.emp_nstm_id).full_name = "Binh Beta"
    other = Company(name="AAA Cong ty dau bang", code="CT99", is_active=True)
    db.add(other)
    db.flush()
    _yctt(db, "P1", company_id=seed.company_id, created_by=seed.u_nstm_id)   # Cty Test / Binh Beta
    _yctt(db, "P2", company_id=other.id, created_by=seed.u_req_id)           # AAA / Anh Alpha
    _yctt(db, "P3", company_id=0, created_by=0)                              # không công ty, hệ thống
    assert _codes(_sort_yctt(db, "company", "asc")) == ["P2", "P1", "P3"]
    assert _codes(_sort_yctt(db, "company", "desc")) == ["P1", "P2", "P3"]
    assert _codes(_sort_yctt(db, "created_by_name", "asc")) == ["P2", "P1", "P3"]
    assert _codes(_sort_yctt(db, "created_by_name", "desc")) == ["P1", "P2", "P3"]


def test_yctt_trung_gia_tri_phan_trang_khong_lap_dong(db):
    for i in range(23):
        _yctt(db, f"R{i:02d}", status="submitted", source_type="goods")
    for key in ("status", "source_type", "payment_method"):
        seen = []
        for page in range(4):
            seen += [r.id for r in _sort_yctt(db, key, "desc").offset(page * 6).limit(6).all()]
        assert len(seen) == len(set(seen)) == 23, key


# ── Duyệt dấu ────────────────────────────────────────────────────────────────────────────
def _seal(db, code, title="", purpose="", **kw):
    row = SealRequest(code=code, title=title, purpose=purpose, **kw)
    db.add(row)
    db.flush()
    return row


def _sort_seal(db, key, direction):
    return apply_sort_from_request(db.query(SealRequest), SealRequest,
                                   _Req(sort_by=key, sort_dir=direction),
                                   default=SealRequest.id.desc(), allow=seal_allow())


def test_duyet_dau_muc_dich_xep_theo_chu_dam_dang_hien(db):
    # Ô hiện title (chữ đậm) nếu có, không thì purpose.
    _seal(db, "S1", title="Hợp đồng thuê kho", purpose="aaa")        # hiện "Hợp đồng thuê kho"
    _seal(db, "S2", title="", purpose="Biên bản bàn giao")           # hiện "Biên bản bàn giao"
    _seal(db, "S3", title="   ", purpose="Công văn")                 # tiêu đề toàn khoảng trắng -> purpose
    _seal(db, "S4", title="", purpose="")                            # ô trống
    assert _codes(_sort_seal(db, "purpose", "asc")) == ["S2", "S3", "S1", "S4"]
    assert _codes(_sort_seal(db, "purpose", "desc")) == ["S1", "S3", "S2", "S4"]


def test_duyet_dau_trang_thai_va_nguoi_tao_trung_gia_tri_khong_lap(db):
    for i in range(22):
        _seal(db, f"D{i:02d}", purpose=f"p{i}", status=2, requester="Một người")
    for key in ("status", "requester", "copies"):
        seen = []
        for page in range(4):
            seen += [r.id for r in _sort_seal(db, key, "asc").offset(page * 6).limit(6).all()]
        assert len(seen) == len(set(seen)) == 22, key


# ── Phân công văn thư (sắp trong Python trước khi cắt trang) ─────────────────────────────
def _grouped(db, sort_by, sort_dir):
    _total, items = clerk_service.list_grouped(db, "", 0, 100, sort_by, sort_dir, 0)
    return [it["employee_name"] for it in items]


def test_van_thu_xep_theo_ten_o_trong_xuong_cuoi_hai_chieu(db, seed):
    from app.modules.employee.model import Employee
    from app.modules.seal_clerk.model import SealClerk

    ghost = Employee(code="GHOST", full_name="", company_id=seed.company_id, department_id=seed.dept_id,
                     is_active=True)
    db.add(ghost)
    db.flush()
    for emp_id in (seed.emp_tp_id, seed.emp_req_id, seed.emp_nstm_id, ghost.id):
        db.add(SealClerk(employee_id=emp_id, company_id=seed.company_id, is_head=False, status=1))
    db.flush()
    asc = _grouped(db, "employee_name", "asc")
    desc = _grouped(db, "employee_name", "desc")
    assert asc[:3] == ["Người YC", "NSTM Chính", "Trưởng Phòng"]
    assert desc[:3] == ["Trưởng Phòng", "NSTM Chính", "Người YC"]
    assert asc[3] == desc[3] == ""   # văn thư chưa có tên: cuối cả hai chiều


# ── Nghỉ phép ────────────────────────────────────────────────────────────────────────────
def _leave(db, code, employee_id, *, status=2, days=1.0, reason=""):
    row = LeaveRequest(code=code, employee_id=employee_id, from_date=date(2026, 9, 1),
                       to_date=date(2026, 9, 1), total_days=days, reason=reason, status=status)
    db.add(row)
    db.flush()
    return row


def _sort_leave(db, key, direction):
    return apply_sort_from_request(db.query(LeaveRequest), LeaveRequest,
                                   _Req(sort_by=key, sort_dir=direction),
                                   default=LeaveRequest.id.desc(), allow=leave_allow())


def test_nghi_phep_nguoi_nghi_xep_theo_ten_khong_theo_id(db, seed):
    _leave(db, "NP1", seed.emp_tp_id)     # Trưởng Phòng
    _leave(db, "NP2", seed.emp_req_id)    # Người YC
    _leave(db, "NP3", 0)                  # không rõ người nghỉ
    assert _codes(_sort_leave(db, "employee_name", "asc")) == ["NP2", "NP1", "NP3"]
    assert _codes(_sort_leave(db, "employee_name", "desc")) == ["NP1", "NP2", "NP3"]


def test_nghi_phep_so_ngay_0_va_ly_do_trong(db, seed):
    _leave(db, "A", seed.emp_req_id, days=0, reason="")
    _leave(db, "B", seed.emp_req_id, days=2, reason="Về quê")
    _leave(db, "C", seed.emp_req_id, days=1, reason="Cưới")
    assert _codes(_sort_leave(db, "total_days", "asc")) == ["A", "C", "B"]
    assert _codes(_sort_leave(db, "reason", "asc")) == ["C", "B", "A"]
    assert _codes(_sort_leave(db, "reason", "desc")) == ["B", "C", "A"]


def _call_leave_list(db, user, monkeypatch, mine_ids, **query):
    monkeypatch.setattr(leave_controller.task_service, "my_tasks",
                        lambda _db, _emp, _entity="": [{"entity_id": i} for i in mine_ids])
    pg = {"page": 1, "page_size": 50, "offset": 0, "limit": 50}
    mine_first = query.pop("mine_first", False)
    out = leave_controller.list_requests(_Req(**query), pg, None, None, None, mine_first, db, user)
    return [i["code"] for i in json.loads(out.body)["data"]["items"]]


@pytest.fixture
def leave_user(seed, cap_quyen):
    cap_quyen(seed.u_nstm_id, "leave_request", scope="all", read=True)
    return SimpleNamespace(id=seed.u_nstm_id, employee_id=seed.emp_nstm_id)


def test_nghi_phep_mine_first_dua_don_cua_toi_len_dau_tren_ca_tap(db, seed, leave_user, monkeypatch):
    rows = [_leave(db, f"NP{i}", seed.emp_req_id, status=3 if i % 2 else 2) for i in range(12)]
    mine = rows[1]    # id nhỏ nhất ngoài một đơn đã duyệt: nếu chỉ xếp theo trang thì nằm ở trang cuối
    got = _call_leave_list(db, leave_user, monkeypatch, [mine.id], mine_first=True)
    assert got[0] == mine.code
    #  Phần còn lại giữ luật mặc định: Chờ duyệt (status 2) trước, rồi id giảm dần.
    rest = [c for c in got if c != mine.code]
    pending = [r.code for r in sorted(rows, key=lambda r: -r.id) if r.status == 2 and r.code != mine.code]
    done = [r.code for r in sorted(rows, key=lambda r: -r.id) if r.status != 2 and r.code != mine.code]
    assert rest == pending + done


def test_nghi_phep_da_chon_cot_thi_bo_mine_first(db, seed, leave_user, monkeypatch):
    rows = [_leave(db, f"NP{i}", seed.emp_req_id, days=float(i)) for i in range(5)]
    got = _call_leave_list(db, leave_user, monkeypatch, [rows[0].id], mine_first=True,
                           sort_by="total_days", sort_dir="desc")
    assert got == ["NP4", "NP3", "NP2", "NP1", "NP0"]   # cột bấm quyết định, không phải "của tôi"


def test_nghi_phep_khong_co_viec_treo_thi_mine_first_la_mac_dinh(db, seed, leave_user, monkeypatch):
    for i in range(3):
        _leave(db, f"NP{i}", seed.emp_req_id)
    assert _call_leave_list(db, leave_user, monkeypatch, [], mine_first=True) == ["NP2", "NP1", "NP0"]


# ── Đặt phòng họp ────────────────────────────────────────────────────────────────────────
def _room(db, name):
    room = MeetingRoom(code=f"R-{name}", name=name, company_id=0)
    db.add(room)
    db.flush()
    return room


def _booking(db, code, room_id, emp_id, hour, title="Họp", status=2):
    row = RoomBooking(code=code, room_id=room_id, requester_employee_id=emp_id, title=title,
                      start_at=datetime(2026, 9, 1, hour), end_at=datetime(2026, 9, 1, hour + 1),
                      status=status)
    db.add(row)
    db.flush()
    return row


def _sort_room(db, key, direction):
    return apply_sort_from_request(db.query(RoomBooking), RoomBooking,
                                   _Req(sort_by=key, sort_dir=direction),
                                   default=RoomBooking.start_at.desc(), allow=room_allow())


def test_dat_phong_phong_va_nguoi_dat_xep_theo_ten(db, seed):
    r_a, r_b = _room(db, "Phòng An"), _room(db, "Phòng Bình")
    _booking(db, "B1", r_b.id, seed.emp_tp_id, 8)      # Phòng Bình / Trưởng Phòng
    _booking(db, "B2", r_a.id, seed.emp_req_id, 9)     # Phòng An / Người YC
    _booking(db, "B3", 0, 0, 10)                       # chưa gắn phòng, không người đặt
    assert _codes(_sort_room(db, "room_name", "asc")) == ["B2", "B1", "B3"]
    assert _codes(_sort_room(db, "room_name", "desc")) == ["B1", "B2", "B3"]
    assert _codes(_sort_room(db, "requester_name", "asc")) == ["B2", "B1", "B3"]
    assert _codes(_sort_room(db, "requester_name", "desc")) == ["B1", "B2", "B3"]


def test_dat_phong_cot_bat_dau_xep_hai_chieu_va_trung_gio_on_dinh(db, seed):
    for i in range(14):
        _booking(db, f"T{i:02d}", 0, seed.emp_req_id, 8)    # cùng giờ bắt đầu
    _booking(db, "EARLY", 0, seed.emp_req_id, 7)
    asc = _codes(_sort_room(db, "start_at", "asc"))
    assert asc[0] == "EARLY"
    seen = []
    for page in range(3):
        seen += [r.id for r in _sort_room(db, "start_at", "desc").offset(page * 6).limit(6).all()]
    assert len(seen) == len(set(seen)) == 15


def _call_room_list(db, user, monkeypatch, mine_ids, **query):
    monkeypatch.setattr(room_controller.task_service, "my_tasks",
                        lambda _db, _emp, _entity="": [{"entity_id": i} for i in mine_ids])
    pg = {"page": 1, "page_size": 50, "offset": 0, "limit": 50}
    mine_first = query.pop("mine_first", False)
    scope = query.pop("scope", None)
    #  Gọi bằng TÊN tham số: gọi thẳng hàm thì giá trị mặc định là đối tượng `Query`, không phải None.
    out = room_controller.list_bookings(_Req(**query), pg, search=None, from_time=None, to_time=None,
                                        mine_first=mine_first, scope=scope, db=db, user=user)
    return [i["code"] for i in json.loads(out.body)["data"]["items"]]


def test_dat_phong_mine_first_va_bo_qua_khi_da_chon_cot(db, seed, cap_quyen, monkeypatch):
    cap_quyen(seed.u_nstm_id, "room_booking", scope="all", read=True)
    user = SimpleNamespace(id=seed.u_nstm_id, employee_id=seed.emp_nstm_id)
    rows = [_booking(db, f"M{h:02d}", 0, seed.emp_req_id, h) for h in range(8, 14)]
    oldest = rows[0]
    # mặc định: cuộc họp mới nhất trước; có mine_first thì phiếu chờ tôi duyệt lên đầu
    assert _call_room_list(db, user, monkeypatch, [oldest.id])[0] == "M13"
    assert _call_room_list(db, user, monkeypatch, [oldest.id], mine_first=True)[0] == oldest.code
    # đã chọn cột -> theo cột, không theo "của tôi"
    got = _call_room_list(db, user, monkeypatch, [oldest.id], mine_first=True,
                          sort_by="start_at", sort_dir="asc")
    assert got[0] == oldest.code and got == [r.code for r in rows]
    got = _call_room_list(db, user, monkeypatch, [oldest.id], mine_first=True,
                          sort_by="start_at", sort_dir="desc")
    assert got == [r.code for r in reversed(rows)]


def test_dat_phong_phieu_cua_toi_chi_ra_phieu_toi_dat_hoac_tao_ho(db, seed, cap_quyen, monkeypatch):
    """duoc-CR-744: ô Phạm vi **Phiếu của tôi** gửi `scope=mine` mà máy chủ bỏ qua — chọn xong vẫn
    ra phiếu của mọi người. Nay chỉ còn phiếu tôi là người đặt HOẶC tôi tạo hộ (thư ký đặt cho sếp)."""
    cap_quyen(seed.u_nstm_id, "room_booking", scope="all", read=True)
    user = SimpleNamespace(id=seed.u_nstm_id, employee_id=seed.emp_nstm_id)
    _booking(db, "MY-REQ", 0, seed.emp_nstm_id, 8)                   # tôi là người đặt
    on_behalf = _booking(db, "MY-CREATED", 0, seed.emp_tp_id, 9)     # tôi đặt hộ người khác
    on_behalf.created_by = seed.u_nstm_id
    _booking(db, "OTHER", 0, seed.emp_req_id, 10)                    # của người khác
    db.flush()

    assert sorted(_call_room_list(db, user, monkeypatch, [])) == ["MY-CREATED", "MY-REQ", "OTHER"]
    assert sorted(_call_room_list(db, user, monkeypatch, [], scope="mine")) == ["MY-CREATED", "MY-REQ"]


def test_dat_phong_phieu_cua_toi_khong_rong_hon_quyen_xem(db, seed, cap_quyen, monkeypatch):
    """Tài khoản không gắn nhân sự chỉ còn vế "tôi tạo"; `scope=mine` không bao giờ mở rộng phạm vi."""
    cap_quyen(seed.u_nstm_id, "room_booking", scope="all", read=True)
    user = SimpleNamespace(id=seed.u_nstm_id, employee_id=0)
    _booking(db, "BY-EMP-0", 0, 0, 8)                                # requester 0 nhưng không do tôi tạo
    db.flush()
    assert _call_room_list(db, user, monkeypatch, [], scope="mine") == []


# ── Bảng "Kết quả khảo sát đã duyệt": khóa phụ id ────────────────────────────────────────
def test_ket_qua_khao_sat_da_duyet_trung_ncc_khong_lap_dong_giua_cac_trang(db, seed):
    from app.modules.survey.model import SurveyProductLine
    from app.modules.survey_request import line_service

    sup_code = "NCC-TRUNG"
    lines = db.query(SurveyProductLine).all()
    # nhân bản một dòng khảo sát có sẵn thành nhiều dòng CÙNG mã NCC, để xếp theo NCC phải nhờ khóa phụ
    base = lines[0]
    for i in range(12):
        db.add(SurveyProductLine(survey_id=base.survey_id, supplier_code=sup_code,
                                 product_name=f"Hàng {i}", line_approve="Đã duyệt"))
    db.flush()
    seen = []
    for page in (1, 2, 3):
        items, total = line_service.available_survey_lines(
            db, supplier_code=sup_code, sort_by="supplier_code", sort_dir="asc", page=page, page_size=5)
        seen += [ln.id for ln in items]
    assert total >= 12
    assert len(seen) == len(set(seen)), "có dòng lặp giữa các trang"
    assert seen == sorted(seen, reverse=True)


def test_ket_qua_khao_sat_da_duyet_cot_ncc_xep_theo_ten_dang_hien_khong_theo_ma(db, seed):
    from app.modules.supplier.model import Supplier
    from app.modules.survey.model import SurveyProductLine
    from app.modules.survey_request import line_service

    base = db.query(SurveyProductLine).first()
    db.add_all([
        Supplier(code="Z1", name="An Co", supplier_type="goods", is_active=True),     # tên đứng đầu, mã đứng cuối
        Supplier(code="A1", name="Zeta Co", supplier_type="goods", is_active=True),   # mã đứng đầu, tên đứng cuối
        Supplier(code="M1", name="   ", supplier_type="goods", is_active=True),       # tên trống -> ô hiện mã "M1"
    ])
    # B9 không có trong danh mục -> ô hiện chính mã "B9"; mã rỗng -> ô trống ("—")
    for code in ("Z1", "A1", "M1", "B9", ""):
        db.add(SurveyProductLine(survey_id=base.survey_id, supplier_code=code, product_name="TAGNCC743",
                                 line_approve="Đã duyệt"))
    db.flush()

    def shown(direction):
        items, _ = line_service.available_survey_lines(
            db, search="TAGNCC743", sort_by="supplier_name", sort_dir=direction, page=1, page_size=50)
        return [ln.supplier_code for ln in items]

    assert shown("asc") == ["Z1", "B9", "M1", "A1", ""]      # An Co, B9, M1, Zeta Co, (trống)
    assert shown("desc") == ["A1", "M1", "B9", "Z1", ""]     # trống vẫn xuống cuối
    # khóa cũ theo mã vẫn còn cho nơi gọi cũ, và cho thứ tự KHÁC
    items, _ = line_service.available_survey_lines(
        db, search="TAGNCC743", sort_by="supplier_code", sort_dir="asc", page=1, page_size=50)
    assert [ln.supplier_code for ln in items] == ["A1", "B9", "M1", "Z1", ""]


# ── Bốn cột bật thêm (đợt bổ sung) ──────────────────────────────────────────────────────
def test_yctt_ma_misa_xep_theo_ma_misa_dau_tien_cua_phieu(db):
    from app.modules.payment_request.model import PaymentRequestLine
    from app.modules.purchase_order.model import PurchaseOrder

    db.add_all([PurchaseOrder(code="PO-A", misa_code="MS-30"), PurchaseOrder(code="PO-B", misa_code="MS-10"),
                PurchaseOrder(code="PO-C", misa_code=""), PurchaseOrder(code="PO-D", misa_code="MS-20")])
    db.flush()
    p1 = _yctt(db, "Y1")   # dòng 1 chưa có mã MISA -> mã đầu tiên là MS-30 (dòng 2)
    p2 = _yctt(db, "Y2")   # MS-10 rồi MS-30
    p3 = _yctt(db, "Y3")   # không có mã nào
    p4 = _yctt(db, "Y4")   # MS-20, có khoảng trắng quanh mã PO (dòng phiếu chụp tay)
    for req, pos in ((p1, ["PO-C", "PO-A"]), (p2, ["PO-B", "PO-A"]), (p3, ["PO-C", ""]), (p4, [" PO-D "])):
        for po in pos:
            db.add(PaymentRequestLine(request_id=req.id, po_code=po))
    db.flush()
    assert _codes(_sort_yctt(db, "misa_code", "asc")) == ["Y2", "Y4", "Y1", "Y3"]
    assert _codes(_sort_yctt(db, "misa_code", "desc")) == ["Y1", "Y4", "Y2", "Y3"]   # không mã xuống cuối


def test_duyet_dau_cong_ty_xep_theo_ten_cong_ty_dau_tien(db):
    from app.modules.seal_request.model import SealRequestCompany

    zeta = Company(name="Zeta Holding", code="CZ", is_active=True)
    alpha = Company(name="Alpha Corp", code="CA", is_active=True)
    db.add_all([zeta, alpha])
    db.flush()
    s1, s2, s3, s4 = (_seal(db, c, purpose=c) for c in ("C1", "C2", "C3", "C4"))
    db.add_all([
        SealRequestCompany(seal_request_id=s1.id, company_id=zeta.id),
        SealRequestCompany(seal_request_id=s1.id, company_id=alpha.id),   # công ty đầu = Zeta
        SealRequestCompany(seal_request_id=s2.id, company_id=alpha.id),
        SealRequestCompany(seal_request_id=s3.id, company_id=alpha.id),
        SealRequestCompany(seal_request_id=s3.id, company_id=zeta.id),    # công ty đầu = Alpha
    ])                                                                    # s4: chưa có công ty nào
    db.flush()
    asc = _codes(_sort_seal(db, "company_name", "asc"))
    desc = _codes(_sort_seal(db, "company_name", "desc"))
    assert asc == ["C3", "C2", "C1", "C4"]    # Alpha (id lớn trước), Alpha, Zeta, trống
    assert desc == ["C1", "C3", "C2", "C4"]


def test_dat_phong_so_nguoi_0_la_o_trong_xuong_cuoi_hai_chieu(db, seed):
    for code, n in (("N0", 0), ("N5", 5), ("N2", 2), ("N9", 0)):
        b = _booking(db, code, 0, seed.emp_req_id, 8)
        b.attendee_count = n
    db.flush()
    assert _codes(_sort_room(db, "attendee_count", "asc")) == ["N2", "N5", "N9", "N0"]
    assert _codes(_sort_room(db, "attendee_count", "desc")) == ["N5", "N2", "N9", "N0"]


def test_nghi_phep_loai_nghi_xep_theo_ten_loai_chinh(db, seed):
    from app.modules.leave.catalog_model import LeaveType

    t_phep = LeaveType(code="PN", name="Phép năm")
    t_om = LeaveType(code="OM", name="Nghỉ ốm")
    t_kl = LeaveType(code="KL", name="Không lương")
    db.add_all([t_phep, t_om, t_kl])
    db.flush()
    rows = []
    for code, t in (("L1", t_phep), ("L2", t_om), ("L3", t_kl), ("L4", None)):
        r = _leave(db, code, seed.emp_req_id)
        r.leave_type_id = t.id if t else 0
        rows.append(r)
    db.flush()
    # Chữ cái đầu K < N < P (ASCII) để thứ tự giống nhau ở SQLite (so nhị phân) lẫn MySQL.
    assert _codes(_sort_leave(db, "leave_type_name", "asc")) == ["L3", "L2", "L1", "L4"]
    assert _codes(_sort_leave(db, "leave_type_name", "desc")) == ["L1", "L2", "L3", "L4"]
