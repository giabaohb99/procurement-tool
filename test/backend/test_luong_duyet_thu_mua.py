"""N01 — LƯỚI AN TOÀN cho các luồng duyệt Thu mua đang chạy thật.

Đây là **điều kiện chặn cứng của phase 3** (bộ máy phê duyệt dùng chung). Tài
liệu nói thẳng: bộ kiểm này là lưới an toàn duy nhất, *"không có nó thì mọi cam
kết còn lại chỉ là lời hứa"*. Bộ máy duyệt mới sẽ đứng CẠNH mã cũ và bật theo
cờ từng loại chứng từ; bài kiểm ở đây canh việc mã cũ **không đổi hành vi** khi
bộ máy mới được thêm vào.

Năm luồng: YCMH · ĐMH · Khảo sát · YCBG · YCTT. Hai luồng đã có lưới sẵn, không
chép lại ở đây — chạy đủ ba tệp mới phủ hết năm luồng:
  · ĐMH   → `test_po_submit_guard.py` (11 bài, CR-073)
  · YCTT bước GỬI DUYỆT → `test_payment_request_cr066.py` (CR-066 kiểm từng dòng
    phải khớp một khoản công nợ còn nợ). Ở đây chỉ kiểm phần duyệt/chi.

Kiểm ở tầng CONTROLLER chứ không phải service, vì luật trạng thái phần lớn nằm ở
controller: `set_status` của YCMH, Khảo sát và YCBG chỉ GÁN trạng thái, không
kiểm gì. Riêng YCTT là ngoại lệ — `set_status` của nó có gọi `check_submit`.

⚠️ **Bộ này ghi lại HÀNH VI ĐANG CÓ, không phải hành vi mong muốn.** Ba luồng
(Khảo sát, YCBG, YCTT) hiện KHÔNG chặn trạng thái ở bước duyệt — gọi thẳng API
là duyệt được phiếu còn nháp hoặc duyệt lại phiếu đã hủy. Chỗ nào như vậy đều có
một bài `test_*_chua_chan_*` ghi rõ là **lỗ hổng đã biết**. Chúng ở đó để phase 3
không vá nhầm rồi tưởng mình không đổi gì: vá thì bài kiểm đỏ, và đỏ ở đây nghĩa
là "hành vi đã đổi, xem lại có cố ý không", chứ không phải "mã hỏng".
"""
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.modules.payment_request import controller as pay_ctl
from app.modules.payment_request.model import PaymentRequest
from app.modules.purchase_request import controller as pr_ctl
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import ApproveIn, RejectIn
from app.modules.survey import controller as sv_ctl
from app.modules.survey.model import Survey
from app.modules.survey_request import controller as sr_ctl
from app.modules.survey_request.model import SurveyRequest

USER = SimpleNamespace(id=1)


@pytest.fixture(autouse=True)
def _cat_moi_duong_gui_thong_bao(monkeypatch):
    """Bộ này kiểm LUẬT TRẠNG THÁI, không kiểm thông báo.

    Mỗi module gửi thông báo một kiểu (`trigger_notification` hoặc `_notify`
    riêng), và tất cả đều đụng bảng người dùng/vai trò. Để nguyên thì bài kiểm
    đỏ vì thiếu dữ liệu thông báo chứ không phải vì luật duyệt sai — đúng kiểu
    lưới an toàn báo động giả tới mức không ai còn tin.
    """
    for module in (pr_ctl, sv_ctl, pay_ctl):
        monkeypatch.setattr(module, "trigger_notification", lambda **kw: None)
    monkeypatch.setattr(sr_ctl, "_notify", lambda *a, **kw: None)
    monkeypatch.setattr(pr_ctl, "_notify_assigned", lambda *a, **kw: None)


@pytest.fixture(autouse=True)
def _user_co_quyen_that(cap_quyen):
    """`USER` phải là tài khoản CÓ GRANT, nếu không mọi route ăn 404 trước khi tới luật.

    Từ bản vá phạm vi nhánh ghi (cụm 03), các route theo id của YCMH · Khảo sát · YCBG ·
    YCTT nạp chứng từ qua `_in_scope` thay cho `service.get_*` trần — `SimpleNamespace(id=1)`
    trơ thì không grant nào, mà "không grant" = không thấy gì (đúng như chạy thật). Cấp
    phạm vi `all` để bộ này kiểm đúng thứ nó sinh ra để kiểm: LUẬT TRẠNG THÁI.
    """
    for entity in ("purchase_request", "survey", "survey_request", "payment_request"):
        cap_quyen(USER.id, entity, scope="all", read=True, create=True, write=True,
                  delete=True, approve=True, cancel=True, print=True, export=True)


# ── YCMH · Yêu cầu mua hàng ─────────────────────────────────────────────────
#  Luồng: Nháp → Chờ duyệt → Đã duyệt → (Đã điều phối) → … · Bị trả lại thì sửa
#  và gửi lại được.

@pytest.fixture()
def cho_phep_duyet_ycmh(monkeypatch):
    """Bỏ qua tầng PHẠM VI, chỉ giữ tầng TRẠNG THÁI.

    `_can_edit_own` và `_in_approve_scope` hỏi `apply_scope` — phạm vi dữ liệu
    đã có bộ kiểm riêng. Trộn hai thứ vào một bài thì lúc đỏ không biết hỏng cái
    nào.
    """
    monkeypatch.setattr(pr_ctl, "_can_edit_own", lambda db, pr, user: True)
    monkeypatch.setattr(pr_ctl, "_in_approve_scope", lambda db, user, pid: True)


def _ycmh(db, seed, status="draft", code="PYC-N01-01"):
    pr = PurchaseRequest(code=code, company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="Phòng Test",
                         status=status, created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    db.add(PurchaseRequestItem(pr_id=pr.id, product_code="SP01", product_name="Hàng Nhãn",
                               item_group="Nhãn", qty=10, unit="cái", price=1000,
                               created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    db.refresh(pr)
    return pr


@pytest.mark.parametrize("status", ["draft", "rejected"])
def test_ycmh_gui_duyet_tu_nhap_va_bi_tra_lai(db, seed, cho_phep_duyet_ycmh, status):
    pr = _ycmh(db, seed, status=status)
    pr_ctl.submit_pr(pr.id, BackgroundTasks(), db=db, user=USER)
    db.refresh(pr)
    assert pr.status == "submitted"


@pytest.mark.parametrize("status", ["submitted", "approved", "dispatched", "completed"])
def test_ycmh_gui_duyet_phieu_dang_chay_bi_chan(db, seed, cho_phep_duyet_ycmh, status):
    """Chặn gửi lại phiếu đã đi tiếp — nếu không thì phiếu quay ngược về Chờ duyệt."""
    pr = _ycmh(db, seed, status=status)
    with pytest.raises(HTTPException) as error:
        pr_ctl.submit_pr(pr.id, BackgroundTasks(), db=db, user=USER)
    assert error.value.status_code == 400
    db.refresh(pr)
    assert pr.status == status


def test_ycmh_khong_co_quyen_tren_phieu_thi_khong_gui_duyet_duoc(db, seed, monkeypatch):
    monkeypatch.setattr(pr_ctl, "_can_edit_own", lambda db, pr, user: False)
    pr = _ycmh(db, seed)
    with pytest.raises(HTTPException) as error:
        pr_ctl.submit_pr(pr.id, BackgroundTasks(), db=db, user=USER)
    assert error.value.status_code == 403


def test_ycmh_duyet_ngoai_pham_vi_bi_chan(db, seed, monkeypatch):
    """Có quyền `approve` chưa đủ — phiếu còn phải nằm trong phạm vi của người đó."""
    monkeypatch.setattr(pr_ctl, "_in_approve_scope", lambda db, user, pid: False)
    pr = _ycmh(db, seed, status="submitted")
    with pytest.raises(HTTPException) as error:
        pr_ctl.approve_pr(pr.id, ApproveIn(), BackgroundTasks(), db=db, user=USER)
    assert error.value.status_code == 403
    db.refresh(pr)
    assert pr.status == "submitted"


def test_ycmh_duyet_xong_van_chua_co_nstm_khi_bat_dieu_phoi(db, seed, cho_phep_duyet_ycmh,
                                                            monkeypatch):
    """CR-034 — bật điều phối thì duyệt bước 1 KHÔNG phân bổ nhân sự.

    Đây là chỗ dễ vỡ nhất khi thay bộ máy duyệt: nếu bước duyệt lại kéo theo
    phân bổ như luồng cũ thì phiếu có người phụ trách sớm hơn một bước, và bước
    điều phối mất ý nghĩa.
    """
    monkeypatch.setattr(pr_ctl.service, "dispatch_enabled", lambda: True)
    pr = _ycmh(db, seed, status="submitted")

    pr_ctl.approve_pr(pr.id, ApproveIn(), BackgroundTasks(), db=db, user=USER)

    db.refresh(pr)
    assert pr.status == "approved"
    assert all(not item.assignee for item in pr_ctl.service.items_of(db, pr.id))


def test_ycmh_tat_dieu_phoi_thi_duyet_la_phan_bo_luon(db, seed, cho_phep_duyet_ycmh, monkeypatch):
    """Công tắc TẮT = quay về luồng cũ, duyệt phát là có nhân sự phụ trách."""
    monkeypatch.setattr(pr_ctl.service, "dispatch_enabled", lambda: False)
    pr = _ycmh(db, seed, status="submitted")

    pr_ctl.approve_pr(pr.id, ApproveIn(), BackgroundTasks(), db=db, user=USER)

    assert [item.assignee for item in pr_ctl.service.items_of(db, pr.id)] == [seed.emp_nstm_code]


def test_ycmh_truong_phong_khong_dieu_phoi_duoc(db, seed, monkeypatch):
    """Phạm vi `dept` duyệt bước 1 được nhưng không điều phối — đó là hai vai khác nhau."""
    monkeypatch.setattr(pr_ctl.service, "dispatch_enabled", lambda: True)
    monkeypatch.setattr(pr_ctl, "get_perm_profile", lambda db, user: {
        "grants": [{"perms": {"purchase_request": {"approve": True, "scope": "dept"}}}]
    })
    pr = _ycmh(db, seed, status="approved")

    with pytest.raises(HTTPException) as error:
        pr_ctl.dispatch_pr(pr.id, BackgroundTasks(), db=db, user=USER)
    assert error.value.status_code == 403


def test_ycmh_tra_lai_roi_gui_duyet_lai_duoc(db, seed, cho_phep_duyet_ycmh):
    """Trả lại KHÔNG phải khóa phiếu — người tạo sửa rồi gửi lại."""
    pr = _ycmh(db, seed, status="submitted")

    pr_ctl.reject_pr(pr.id, RejectIn(reason="Thiếu báo giá"), BackgroundTasks(), db=db, user=USER)
    db.refresh(pr)
    assert pr.status == "rejected"

    pr_ctl.submit_pr(pr.id, BackgroundTasks(), db=db, user=USER)
    db.refresh(pr)
    assert pr.status == "submitted"


# ── Khảo sát ────────────────────────────────────────────────────────────────

def _khao_sat(db, status="submitted", code="KS-N01-01"):
    survey = Survey(code=code, survey_type="combined", status=status, item_group="Nhãn")
    db.add(survey)
    db.commit()
    db.refresh(survey)
    return survey


def test_khao_sat_duyet_dat_ca_hai_cot_trang_thai(db):
    """`status` và `approve_status` phải đi cùng nhau — bảng danh sách đọc cột thứ hai.

    ⚠️ `approve_status` lưu **MÃ**, không lưu tiếng Việt (B-04, xem
    `SURVEY_APPROVE_STATUS`). Bài này từng đỏ vì còn khẳng định chuỗi `"Duyệt"`
    sau khi đợt chuyển mã chạy xong. Kiểm cả hai vế — mã đã ghi và nhãn đọc ra —
    để lần sau đổi nhãn không âm thầm đổi dữ liệu, và ngược lại.
    """
    survey = _khao_sat(db)

    sv_ctl.approve_(survey.id, BackgroundTasks(), db=db, user=USER)

    db.refresh(survey)
    assert survey.status == "approved"
    assert survey.approve_status == "approved"
    assert survey.approve_status_label == "Duyệt"


def test_khao_sat_tra_lai_khac_tu_choi(db):
    """Trả lại (`rejected`) còn sửa được; từ chối (`cancelled`) khóa hẳn.

    Hai nút khác nhau trên cùng một màn hình, rất dễ bị gộp làm một khi viết lại
    bằng bộ máy duyệt chung.
    """
    send_back = _khao_sat(db, code="KS-N01-TL")
    sv_ctl.reject_(send_back.id, RejectIn(reason="Thiếu mẫu"), BackgroundTasks(), db=db, user=USER)
    db.refresh(send_back)
    assert send_back.status == "rejected"
    #  MÃ, không phải tiếng Việt — xem ghi chú ở bài kiểm ngay trên.
    assert send_back.approve_status == "rejected"
    assert send_back.approve_status_label == "Không duyệt"

    reject = _khao_sat(db, code="KS-N01-TC")
    sv_ctl.cancel_(reject.id, RejectIn(reason="Không cần nữa"), BackgroundTasks(),
                   db=db, user=USER)
    db.refresh(reject)
    assert reject.status == "cancelled"


@pytest.mark.parametrize("status", ["draft", "approved", "cancelled"])
def test_khao_sat_chi_tu_choi_duoc_phieu_dang_cho_duyet(db, status):
    phieu = _khao_sat(db, status=status, code=f"KS-N01-{status}")
    with pytest.raises(HTTPException) as error:
        sv_ctl.cancel_(phieu.id, RejectIn(reason="x"), BackgroundTasks(), db=db, user=USER)
    assert error.value.status_code == 400


def test_khao_sat_chua_chan_duyet_phieu_con_nhap(db):
    """⚠️ LỖ HỔNG ĐÃ BIẾT — ghi lại chứ không phải tán thành.

    `approve_` gọi thẳng `set_status`, không kiểm trạng thái, nên gọi API trực
    tiếp là duyệt được phiếu chưa ai gửi. Giao diện có ẩn nút, nhưng ẩn nút
    không phải chốt chặn — đúng thứ CR-073 đã vá cho ĐMH mà chưa vá cho đây.
    Bài này ĐỎ khi có người vá: lúc đó xóa nó đi và thêm bài chặn thật.
    """
    phieu = _khao_sat(db, status="draft", code="KS-N01-HO")
    sv_ctl.approve_(phieu.id, BackgroundTasks(), db=db, user=USER)
    db.refresh(phieu)
    assert phieu.status == "approved"


# ── YCBG · Yêu cầu báo giá ──────────────────────────────────────────────────

def _ycbg(db, seed, status="draft", code="YCBG-N01-01"):
    sr = SurveyRequest(code=code, department="Phòng Test", status=status,
                       created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(sr)
    db.commit()
    db.refresh(sr)
    return sr


@pytest.fixture()
def cho_phep_gui_ycbg(monkeypatch):
    monkeypatch.setattr(sr_ctl, "_can_edit_own", lambda db, s, user: True)


@pytest.mark.parametrize("status", ["draft", "rejected"])
def test_ycbg_gui_duyet_tu_nhap_va_bi_tra_lai(db, seed, cho_phep_gui_ycbg, status):
    sr = _ycbg(db, seed, status=status)
    sr_ctl.submit_(sr.id, BackgroundTasks(), db=db, user=USER)
    db.refresh(sr)
    assert sr.status == "submitted"


@pytest.mark.parametrize("status", ["submitted", "approved", "processing", "cancelled"])
def test_ycbg_gui_duyet_phieu_dang_chay_bi_chan(db, seed, cho_phep_gui_ycbg, status):
    sr = _ycbg(db, seed, status=status)
    with pytest.raises(HTTPException) as error:
        sr_ctl.submit_(sr.id, BackgroundTasks(), db=db, user=USER)
    assert error.value.status_code == 400
    db.refresh(sr)
    assert sr.status == status


def test_ycbg_duyet_di_thang_sang_dang_xu_ly(db, seed):
    """Duyệt YCBG đi qua HAI lần đổi trạng thái, dừng ở `processing` chứ không phải `approved`.

    Bộ máy duyệt chung chỉ biết "đã duyệt"; nếu chuyển luồng này sang mà quên
    bước hai thì phiếu nằm lại ở `approved` — không màn hình nào của phần xử lý
    khảo sát nhặt nó lên, và không có gì báo.
    """
    sr = _ycbg(db, seed, status="submitted")

    sr_ctl.approve_(sr.id, BackgroundTasks(), db=db, user=USER)

    db.refresh(sr)
    assert sr.status == "processing"


def test_ycbg_tra_lai_khac_tu_choi(db, seed, cho_phep_gui_ycbg):
    send_back = _ycbg(db, seed, status="submitted", code="YCBG-N01-TL")
    sr_ctl.reject_(send_back.id, RejectIn(reason="Thiếu thông tin"), BackgroundTasks(),
                   db=db, user=USER)
    db.refresh(send_back)
    assert send_back.status == "rejected"
    #  Trả lại thì gửi lại được — đó là điểm khác từ chối.
    sr_ctl.submit_(send_back.id, BackgroundTasks(), db=db, user=USER)
    db.refresh(send_back)
    assert send_back.status == "submitted"

    reject = _ycbg(db, seed, status="submitted", code="YCBG-N01-TC")
    sr_ctl.cancel_(reject.id, RejectIn(reason="Không cần"), BackgroundTasks(), db=db, user=USER)
    db.refresh(reject)
    assert reject.status == "cancelled"
    with pytest.raises(HTTPException):
        sr_ctl.submit_(reject.id, BackgroundTasks(), db=db, user=USER)


def test_ycbg_chua_chan_duyet_phieu_da_huy(db, seed):
    """⚠️ LỖ HỔNG ĐÃ BIẾT — `approve_` không kiểm trạng thái, xem ghi chú ở đầu tệp."""
    sr = _ycbg(db, seed, status="cancelled", code="YCBG-N01-HO")
    sr_ctl.approve_(sr.id, BackgroundTasks(), db=db, user=USER)
    db.refresh(sr)
    assert sr.status == "processing"


# ── YCTT · Yêu cầu thanh toán ───────────────────────────────────────────────

@pytest.fixture
def quyen_yctt(db, cap_quyen):
    """`USER` phải có vai trò THẬT trên `payment_request` mới đi qua cổng phạm vi.

    Từ 05/09/2026 tám route GHI của YCTT nạp phiếu qua `get_scoped(..., action)` (P0 #3
    — trước đó duyệt chi / xóa phiếu của pháp nhân khác đều trót lọt). Một
    `SimpleNamespace(id=1)` trơ không có grant nào, mà "không grant" nghĩa là không thấy
    gì — đúng như chạy thật, xem chú thích của fixture `cap_quyen` trong `conftest.py`.

    Bộ bài này canh LUẬT TRẠNG THÁI chứ không canh phân quyền, nên cấp phạm vi «tất cả».
    Phần phạm vi có bài riêng: `test_pham_vi_tai_chinh_kho_bao_cao.py` (C4–C6c).
    """
    return cap_quyen(USER.id, "payment_request", scope="all",
                     read=True, write=True, approve=True, delete=True, print=True)


def _yctt(db, status="draft", code="YCTT-N01-01"):
    r = PaymentRequest(code=code, status=status)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def test_yctt_duyet_roi_ghi_nhan_chi(db, quyen_yctt):
    """Bắt đầu từ `submitted`: bước gửi duyệt đã có `test_payment_request_cr066.py`
    kiểm kỹ (mỗi dòng phải khớp một khoản công nợ còn nợ), dựng lại ở đây chỉ
    làm bài kiểm này đỏ vì thiếu dữ liệu công nợ chứ không phải vì luật duyệt sai."""
    r = _yctt(db, status="submitted")

    pay_ctl.approve_(r.id, BackgroundTasks(), db=db, user=USER)
    db.refresh(r)
    assert r.status == "approved"

    pay_ctl.pay_(r.id, BackgroundTasks(), db=db, user=USER)
    db.refresh(r)
    assert r.status == "paid"


def test_yctt_tu_choi_la_khoa_phieu(db, quyen_yctt):
    """Từ chối YCTT về `cancelled`, KHÔNG phải `rejected` — phiếu tiền thì khóa hẳn."""
    r = _yctt(db, status="submitted", code="YCTT-N01-TC")

    pay_ctl.reject_(r.id, {"reason": "Sai số tiền"}, BackgroundTasks(), db=db, user=USER)

    db.refresh(r)
    assert r.status == "cancelled"


def test_yctt_chua_chan_ghi_chi_phieu_chua_duyet(db, quyen_yctt):
    """⚠️ LỖ HỔNG ĐÃ BIẾT, và là cái nặng nhất trong ba cái.

    `pay_` không kiểm trạng thái nên gọi API trực tiếp là ghi nhận đã chi cho
    phiếu còn nháp — tức là tiền ra khỏi sổ mà chưa ai duyệt. Ghi lại ở đây để
    phase 3 biết mình đang đứng cạnh cái gì; vá thì bài này đỏ.
    """
    r = _yctt(db, status="draft", code="YCTT-N01-HO")
    pay_ctl.pay_(r.id, BackgroundTasks(), db=db, user=USER)
    db.refresh(r)
    assert r.status == "paid"
