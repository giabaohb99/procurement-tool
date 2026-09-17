"""bao-CR-419 — CHUÔNG cho hai lần bàn giao của luồng phương án YCMH.

Luồng phương án (bao-CR-310) đổi tay hai lần mà trước CR này không có cái chuông nào:
NSTM chốt hoàn thành xử lý thì người yêu cầu không biết tới lượt mình vào chọn; người
yêu cầu chọn xong thì thu mua không biết để vào gom đơn. Hai bên phải hẹn nhau ngoài
hệ thống.

Hai luật đại ca chốt ngày 17/09/2026, test canh đúng hai luật đó:

  - ĐỢI XONG CẢ PHIẾU mới báo, không báo theo từng dòng — phiếu nhiều NSTM thì người
    chốt CUỐI CÙNG mới làm nổ chuông;
  - người nhận chuông "đã chọn xong" là NSTM phụ trách TỪNG DÒNG, không phải người
    đứng tên cả phiếu.

Kèm nút "Chốt xong lựa chọn" — thứ bắt buộc phải có để chuông thứ hai bắn được: H.10.2
tick sẵn phương án 0 nên dòng nào cũng đang có phương án được chọn ngay từ lúc điều
phối, "im lặng vì đồng ý" và "chưa hề mở phiếu ra xem" cho ra cùng một dữ liệu.

TRẠNG THÁI: chuông đang TẮT (`option_service.OPTION_BELLS_ENABLED = False`, đại ca chốt
17/09/2026) vì người yêu cầu phần lớn còn dùng giao diện cũ, bên đó không có khu phương
án để mà chọn. Bài kiểm giữ nguyên nội dung hai luật trên, chỉ bật công tắc lên bằng
`bat_chuong` để canh — có vậy ngày mở lại mới biết ngay là chuông còn chạy đúng. Riêng
`test_mac_dinh_tat_thi_khong_sinh_chuong_nao` canh chiều ngược lại: để mặc định thì
không một dòng thông báo nào được sinh ra.
"""
import json

import pytest
from fastapi import HTTPException

from app.modules.notification.model import Notification
from app.modules.purchase_request import controller as C
from app.modules.purchase_request import option_service
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import PROptionCompleteIn, PROptionManualIn
from app.modules.user.model import User


def _data(resp):
    return json.loads(resp.body)["data"]


@pytest.fixture
def bat_chuong(monkeypatch):
    """Bật công tắc chuông cho riêng một bài kiểm — mặc định của hệ thống là TẮT."""
    monkeypatch.setattr(option_service, "OPTION_BELLS_ENABLED", True)


def _make_pr(db, seed, assignees, code="PYC-CR419"):
    """Phiếu đã điều phối, mỗi mã NSTM trong `assignees` ôm một dòng."""
    pr = PurchaseRequest(code=code, company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="Phòng Test",
                         department_id=seed.dept_id, status="dispatched",
                         request_date="2026-09-17",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    items = []
    for n, emp_code in enumerate(assignees, start=1):
        it = PurchaseRequestItem(pr_id=pr.id, product_code=f"SP-{n}",
                                 product_name=f"Nhãn SP {n}", item_group="Nhãn",
                                 qty=100, unit="cuộn", price=4800, vat_pct=8,
                                 amount=518400, assignee=emp_code,
                                 created_by=seed.u_req_id, updated_by=seed.u_req_id)
        db.add(it)
        items.append(it)
    db.commit()
    return pr, items


def _nstm(db, seed, cap_quyen):
    """NSTM chính — phạm vi 'được giao' nên chỉ chốt được dòng của mình."""
    cap_quyen(seed.u_nstm_id, "purchase_request", scope="assigned", read=True, write=True)
    cap_quyen(seed.u_nstm_id, "supplier", scope="all", read=True)
    return db.get(User, seed.u_nstm_id)


def _backup_nstm(db, seed, cap_quyen):
    u = db.query(User).filter(User.employee_id == seed.emp_backup_id).first()
    cap_quyen(u.id, "purchase_request", scope="assigned", read=True, write=True)
    cap_quyen(u.id, "supplier", scope="all", read=True)
    return u


def _requester(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True)
    return db.get(User, seed.u_req_id)


def _gan_phuong_an(db, pr, item, user):
    """Gắn một phương án nhập tay — dòng phải có phương án thì mới chốt hoàn thành
    được mà không cần tick chốt rỗng."""
    return _data(C.add_option_manual(pr.id, item.id, PROptionManualIn(
        supplier_code="NX", snap_price_by_volume=4700), db=db, user=user))


def _complete(db, pr, user):
    return _data(C.complete_options(pr.id, PROptionCompleteIn(empty_item_ids=[]),
                                    db=db, user=user))


def _notes(db, uid):
    return db.query(Notification).filter(Notification.user_id == uid).all()


# ── Chuông 1: NSTM chốt hoàn thành -> báo người yêu cầu ─────────────────────────

def test_xong_ca_phieu_thi_bao_nguoi_yeu_cau(db, seed, cap_quyen, bat_chuong):
    pr, items = _make_pr(db, seed, [seed.emp_nstm_code])
    nstm = _nstm(db, seed, cap_quyen)
    _gan_phuong_an(db, pr, items[0], nstm)

    out = _complete(db, pr, nstm)

    assert out["all_done"] is True
    notes = _notes(db, seed.u_req_id)
    assert len(notes) == 1
    assert "sẵn sàng để chọn" in notes[0].title
    assert pr.code in notes[0].title
    assert notes[0].link == f"/purchase-requests/{pr.id}"


def test_con_dong_cua_nstm_khac_thi_chua_bao(db, seed, cap_quyen, bat_chuong):
    """Phiếu hai NSTM: người chốt trước KHÔNG được làm nổ chuông — người yêu cầu vào
    chọn lúc đó là chọn trên phiếu mới xong một nửa."""
    pr, items = _make_pr(db, seed, [seed.emp_nstm_code, seed.emp_backup_code])
    nstm = _nstm(db, seed, cap_quyen)
    backup = _backup_nstm(db, seed, cap_quyen)
    _gan_phuong_an(db, pr, items[0], nstm)
    _gan_phuong_an(db, pr, items[1], backup)

    assert _complete(db, pr, nstm)["all_done"] is False
    assert _notes(db, seed.u_req_id) == []

    assert _complete(db, pr, backup)["all_done"] is True
    assert len(_notes(db, seed.u_req_id)) == 1      # đúng MỘT chuông cho cả phiếu


# ── Nút "Chốt xong lựa chọn" ───────────────────────────────────────────────────

def test_nstm_chua_xong_thi_chua_chot_lua_chon_duoc(db, seed, cap_quyen):
    pr, items = _make_pr(db, seed, [seed.emp_nstm_code])
    req = _requester(db, seed, cap_quyen)
    with pytest.raises(HTTPException) as e:
        C.complete_option_choice(pr.id, db=db, user=req)
    assert e.value.status_code == 400
    assert "chưa chốt hoàn thành" in e.value.detail


def test_chot_lua_chon_ghi_moc_va_khong_chot_hai_lan(db, seed, cap_quyen):
    pr, items = _make_pr(db, seed, [seed.emp_nstm_code])
    nstm = _nstm(db, seed, cap_quyen)
    _gan_phuong_an(db, pr, items[0], nstm)
    _complete(db, pr, nstm)
    req = _requester(db, seed, cap_quyen)

    out = _data(C.complete_option_choice(pr.id, db=db, user=req))

    assert out["lines"] == 1
    db.refresh(pr)
    assert pr.options_chosen_at is not None
    assert pr.options_chosen_by == req.id

    with pytest.raises(HTTPException) as e:
        C.complete_option_choice(pr.id, db=db, user=req)
    assert e.value.status_code == 400


def test_nstm_khong_chot_lua_chon_thay_nguoi_yeu_cau(db, seed, cap_quyen):
    """Cùng một ranh giới với nút chốt phương án: NSTM biết giá, người yêu cầu mới
    quyết còn đáng mua không."""
    pr, items = _make_pr(db, seed, [seed.emp_nstm_code])
    nstm = _nstm(db, seed, cap_quyen)
    _gan_phuong_an(db, pr, items[0], nstm)
    _complete(db, pr, nstm)
    with pytest.raises(HTTPException) as e:
        C.complete_option_choice(pr.id, db=db, user=nstm)
    assert e.value.status_code == 403


def test_mo_lai_dong_xoa_moc_da_chot_xong(db, seed, cap_quyen):
    """Mở lại một dòng là mở lại cả vòng: mốc cũ phải biến, kẻo thu mua nhìn dấu cũ
    rồi tưởng phiếu đã yên trong khi NSTM đang sửa dở."""
    pr, items = _make_pr(db, seed, [seed.emp_nstm_code])
    nstm = _nstm(db, seed, cap_quyen)
    _gan_phuong_an(db, pr, items[0], nstm)
    _complete(db, pr, nstm)
    req = _requester(db, seed, cap_quyen)
    C.complete_option_choice(pr.id, db=db, user=req)

    C.reopen_options_line(pr.id, items[0].id, db=db, user=req)

    db.refresh(pr)
    assert pr.options_chosen_at is None
    assert pr.options_chosen_by == 0


# ── Chuông 2: chốt xong lựa chọn -> báo NSTM TỪNG DÒNG ──────────────────────────

def test_chot_xong_bao_nstm_cua_tung_dong(db, seed, cap_quyen, bat_chuong):
    pr, items = _make_pr(db, seed, [seed.emp_nstm_code, seed.emp_backup_code])
    nstm = _nstm(db, seed, cap_quyen)
    backup = _backup_nstm(db, seed, cap_quyen)
    _gan_phuong_an(db, pr, items[0], nstm)
    _gan_phuong_an(db, pr, items[1], backup)
    _complete(db, pr, nstm)
    _complete(db, pr, backup)
    req = _requester(db, seed, cap_quyen)

    C.complete_option_choice(pr.id, db=db, user=req)

    for uid in (nstm.id, backup.id):
        notes = [n for n in _notes(db, uid) if "chốt xong lựa chọn" in n.title.lower()]
        assert len(notes) == 1, f"NSTM {uid} phải nhận đúng một chuông"
        assert notes[0].link == f"/purchase-requests/{pr.id}"


def test_mot_nstm_om_hai_dong_chi_nhan_mot_chuong(db, seed, cap_quyen, bat_chuong):
    pr, items = _make_pr(db, seed, [seed.emp_nstm_code, seed.emp_nstm_code])
    nstm = _nstm(db, seed, cap_quyen)
    for it in items:
        _gan_phuong_an(db, pr, it, nstm)
    _complete(db, pr, nstm)
    req = _requester(db, seed, cap_quyen)

    C.complete_option_choice(pr.id, db=db, user=req)

    notes = [n for n in _notes(db, nstm.id) if "chốt xong lựa chọn" in n.title.lower()]
    assert len(notes) == 1


def test_khong_tu_bao_cho_chinh_minh(db, seed, cap_quyen, bat_chuong):
    """Người yêu cầu cũng đang ôm dòng với tư cách NSTM (phiếu nội bộ phòng thu mua):
    bấm xong không tự dội chuông về chính mình."""
    pr, items = _make_pr(db, seed, [seed.emp_req_code])
    cap_quyen(seed.u_req_id, "purchase_request", scope="all", read=True, write=True)
    cap_quyen(seed.u_req_id, "supplier", scope="all", read=True)
    req = db.get(User, seed.u_req_id)
    _gan_phuong_an(db, pr, items[0], req)
    _complete(db, pr, req)
    assert _notes(db, req.id) == []        # chuông 1 cũng không tự báo về mình

    C.complete_option_choice(pr.id, db=db, user=req)

    assert _notes(db, req.id) == []


# ── Công tắc: mặc định TẮT ─────────────────────────────────────────────────────

def test_mac_dinh_tat_thi_khong_sinh_chuong_nao(db, seed, cap_quyen):
    """Không có `bat_chuong`: cả hai lần bàn giao đều đi trọn vẹn mà không đẻ ra một
    dòng thông báo nào, trong khi mốc chốt xong lựa chọn vẫn được ghi.

    Bài kiểm này canh đúng quyết định ngày 17/09/2026 — tắt chuông chứ không tắt
    luồng. Ai lỡ tay bật `OPTION_BELLS_ENABLED` mà chưa bàn lại thì đỏ ở đây."""
    assert option_service.OPTION_BELLS_ENABLED is False
    pr, items = _make_pr(db, seed, [seed.emp_nstm_code])
    nstm = _nstm(db, seed, cap_quyen)
    _gan_phuong_an(db, pr, items[0], nstm)
    _complete(db, pr, nstm)
    assert _notes(db, seed.u_req_id) == []

    req = _requester(db, seed, cap_quyen)
    C.complete_option_choice(pr.id, db=db, user=req)

    assert _notes(db, nstm.id) == []
    db.refresh(pr)
    assert pr.options_chosen_at is not None
