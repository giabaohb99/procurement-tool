"""CHỌN HỘP THƯ GỬI KHI BAN HÀNH (26/08/2026).

Ca nghiệp vụ: nhân sự hành chính đăng nhập bằng tài khoản của chính mình
(`nhanvien@gmail.com`) nhưng phải ban hành *Thông báo nghỉ lễ* cho toàn công ty
**danh nghĩa `hr@gmail.com`** — người nhận mở hộp thư phải thấy thư đến từ phòng
Hành chính, không phải từ một cá nhân.

Kéo theo một đổi thay lớn hơn: với loại văn bản khai `auto_issue_after_approval
= False`, **ký xong hết các bước KHÔNG còn là ban hành**. Văn bản dừng ở *Chờ
ban hành*, và chính người soạn thảo mở ra, chọn hộp thư, rồi mới bấm *Ban hành*.

Bốn nhóm câu hỏi, đúng thứ tự rủi ro:

1. loại KHÔNG bật cờ thì mọi thứ chạy y như hôm qua — điều kiện số một;
2. loại bật cờ thì dừng đúng chỗ, và dừng ở tư thế ban hành lại được;
3. ai bấm được nút Ban hành, ai không;
4. hộp thư: ai mượn được của ai, và thư gửi ra mang địa chỉ nào.
"""
import pytest
from fastapi import HTTPException

from app.modules.approval import action_service, instance_service
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, SKIP_NONE,
                                             ApprovalFlow, ApprovalNode,
                                             ApprovalSwitch)
from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import service
from app.modules.document.model import (STATUS_EFFECTIVE, STATUS_PENDING_ISSUE,
                                        STATUS_SUBMITTED)
from app.modules.document.schema import DocumentCreate, DocumentUpdate
from app.modules.document.version_model import VERSION_SUBMITTED
from app.modules.employee.model import Employee
from app.modules.notification import mailbox_service
from app.modules.notification.mailbox_model import Mailbox, MailboxMember
from app.modules.notification.model import EmailLog
from app.modules.user.model import User

ENTITY = "document"
ACTOR = 1


# ── Nền ──────────────────────────────────────────────────────────────────────

@pytest.fixture()
def align(db, seed):
    """Nhân sự hành chính (người soạn) + người ký + hai loại văn bản.

    `tb` = Thông báo, tắt tự ban hành — loại của ca nghiệp vụ.
    `qc` = Quy chế, giữ mặc định — chốt "không đổi thứ đang chạy".
    """
    def _people(code, name, email):
        nhan_su = Employee(code=code, full_name=name, email=email,
                           company_id=seed.company_id, department_id=seed.dept_id,
                           is_active=True)
        db.add(nhan_su)
        db.flush()
        tai_khoan = User(email=email, employee_id=nhan_su.id,
                         password_hash="x", is_active=True)
        db.add(tai_khoan)
        db.flush()
        return tai_khoan

    administrative_flow = _people("HC01", "Nhân sự hành chính", "nhanvien@gmail.com")
    nguoi_ky = _people("GD01", "Giám đốc", "giamdoc@gmail.com")
    nguoi_khac = _people("KT01", "Kế toán", "ketoan@gmail.com")

    tb = DocType(code="TB", name="Thông báo", id_scheme=1, number_when=2,
                 auto_issue_after_approval=False)
    qc = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add_all([tb, qc])
    db.commit()

    return {"hc": administrative_flow, "ky": nguoi_ky, "khac": nguoi_khac,
            "tb": tb, "qc": qc, "seed": seed}


def _bat_luong(db, align):
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True,
                          created_by=ACTOR, updated_by=ACTOR))
    flow = ApprovalFlow(entity=ENTITY, code="VB-01", name="Duyệt văn bản",
                        is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, name="Giám đốc ký",
                        approver_kind=APPROVER_EMPLOYEE,
                        approver_ref=str(align["ky"].employee_id),
                        skip_duplicate=SKIP_NONE,
                        created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    return flow


def _soan(db, align, kind=None, title="Thông báo nghỉ lễ 2/9"):
    """Nhân sự hành chính soạn — người soạn thảo ghi đúng là họ."""
    return service.create_document(db, DocumentCreate(
        doc_type_id=(kind or align["tb"]).id,
        company_id=align["seed"].company_id,
        department_id=align["seed"].dept_id,
        owner_employee_id=align["hc"].employee_id,
        drafter_employee_id=align["hc"].employee_id,
        title=title, content_html="<p>Nghỉ từ 01/9 đến 03/9.</p>",
    ), align["hc"].id)


def _ky_het(db, doc, align):
    service.submit(db, doc, align["hc"].id)
    instance = instance_service.running_instance(db, ENTITY, doc.id)
    action_service.approve(db, instance, align["ky"].employee_id, align["ky"].id, {})
    db.refresh(doc)
    return doc


def _hop_thu(db, email="hr@gmail.com", *, nguoi_dung=(), day_du=True,
             company_id=None):
    row = Mailbox(
        code=email.split("@")[0].upper(), name="Phòng Hành chính", email=email,
        display_name="Phòng Hành chính",
        smtp_host="smtp.gmail.com" if day_du else "", smtp_port=587,
        smtp_user=email, use_tls=True, company_id=company_id,
        is_active=True, created_by=ACTOR, updated_by=ACTOR,
    )
    if day_du:
        mailbox_service.set_password(row, "mat-khau-ung-dung")
    db.add(row)
    db.flush()
    for employee_id in nguoi_dung:
        db.add(MailboxMember(mailbox_id=row.id, employee_id=employee_id,
                             created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    return row


# ── 1 · Loại không bật cờ thì KHÔNG ĐỔI GÌ ───────────────────────────────────

def test_loai_giu_mac_dinh_thi_duyet_xong_van_ban_hanh_luon(db, align):
    """Điều kiện số một: mọi loại đang chạy phải hành xử y như hôm qua."""
    _bat_luong(db, align)
    doc = _ky_het(db, _soan(db, align, kind=align["qc"], title="Quy chế A"), align)

    assert doc.status == STATUS_EFFECTIVE
    assert (doc.doc_code or doc.issue_number), "Ban hành phải cấp số"
    assert service.open_version(db, doc) is None, "Ban hành phải khóa phiên bản"


def test_cot_moi_mac_dinh_la_TU_BAN_HANH(db):
    """Mặc định phải là `True`. Đặt `False` là mọi loại đang chạy bỗng dừng lại
    chờ một cú bấm mà chưa ai biết là phải bấm.

    Hỏi sau khi GHI XUỐNG, không hỏi trên đối tượng vừa dựng: mặc định của cột
    áp lúc INSERT, mà cái phải đúng là dòng nằm trong bảng."""
    kind = DocType(code="X", name="Loại chưa khai gì")
    db.add(kind)
    db.commit()

    assert kind.auto_issue_after_approval is True


def test_loai_cu_trong_DB_van_tu_ban_hanh(db, align):
    """Loại đã có sẵn từ trước bản vá — di trú phải điền `True` cho chúng.

    Cột thêm mới mà để `NULL` thì `_tu_ban_hanh` đọc ra rỗng; nó đã có nhánh lùi
    an toàn, nhưng bài kiểm này chốt luôn để không phải dựa vào nhánh đó."""
    from app.modules.document.approval_bridge import _auto_issue

    doc = _soan(db, align, kind=align["qc"], title="Quy chế cũ")
    assert _auto_issue(db, doc) is True


# ── 2 · Loại bật cờ thì DỪNG ở «Chờ ban hành» ────────────────────────────────

def test_ky_het_cac_buoc_thi_dung_o_cho_ban_hanh_chua_cap_so(db, align):
    _bat_luong(db, align)
    doc = _ky_het(db, _soan(db, align), align)

    assert doc.status == STATUS_PENDING_ISSUE
    assert not (doc.doc_code or doc.issue_number), "Chưa bấm ban hành thì chưa cấp số"
    ban = service.open_version(db, doc)
    assert ban is not None and ban.status == VERSION_SUBMITTED, \
        "Bản phải giữ tư thế «chờ duyệt» để `approve()` chạy được lần sau"
    #  Phiên duyệt đã đóng — không còn ai phải ký nữa.
    assert instance_service.running_instance(db, ENTITY, doc.id) is None


def test_dang_cho_ban_hanh_thi_KHONG_SUA_duoc_thong_tin(db, align):
    """Chữ ký đã đặt lên nội dung này. Mở ra sửa rồi mới bấm ban hành thì thứ
    phát hành không còn là thứ người ký đã đọc."""
    _bat_luong(db, align)
    doc = _ky_het(db, _soan(db, align), align)

    with pytest.raises(HTTPException) as error:
        service.update_document(db, doc, DocumentUpdate(title="Đổi tên"), align["hc"].id)
    assert error.value.status_code == 409
    assert "chờ ban hành" in error.value.detail.lower()


def test_dang_cho_ban_hanh_thi_khong_gui_duyet_lai_duoc(db, align):
    """Gửi duyệt chồng lên là đẻ phiên thứ hai trên một văn bản đã ký xong."""
    _bat_luong(db, align)
    doc = _ky_het(db, _soan(db, align), align)

    with pytest.raises(HTTPException):
        service.submit(db, doc, align["hc"].id)


def test_bam_ban_hanh_thi_ban_hanh_that(db, align):
    _bat_luong(db, align)
    doc = _ky_het(db, _soan(db, align), align)

    service.approve(db, doc, align["hc"].id)

    db.refresh(doc)
    assert doc.status == STATUS_EFFECTIVE
    assert (doc.doc_code or doc.issue_number)
    assert service.open_version(db, doc) is None


# ── 3 · Ai bấm được nút Ban hành ─────────────────────────────────────────────

def test_nguoi_soan_thao_bam_duoc(db, align):
    _bat_luong(db, align)
    doc = _ky_het(db, _soan(db, align), align)
    service.ensure_can_issue(db, doc, align["hc"])   # không được ném


def test_nguoi_khac_khong_bam_thay_duoc_du_co_quyen_duyet(db, align):
    """Người ký đã ký xong phần của họ; phát hành là trách nhiệm khác."""
    _bat_luong(db, align)
    doc = _ky_het(db, _soan(db, align), align)

    for ai in (align["ky"], align["khac"]):
        with pytest.raises(HTTPException) as error:
            service.ensure_can_issue(db, doc, ai)
        assert error.value.status_code == 403
        assert "người soạn thảo" in error.value.detail.lower()


def test_tai_khoan_chua_gan_ho_so_nhan_su_thi_khong_bam_duoc(db, align):
    """Tài khoản hệ thống / tác vụ nền không phải "người chịu trách nhiệm"."""
    from types import SimpleNamespace

    _bat_luong(db, align)
    doc = _ky_het(db, _soan(db, align), align)
    with pytest.raises(HTTPException):
        service.ensure_can_issue(db, doc, SimpleNamespace(id=99, employee_id=None))


# ── 4 · Hộp thư gửi ──────────────────────────────────────────────────────────

def test_chi_bay_ra_hop_thu_minh_duoc_cap(db, align):
    hr = _hop_thu(db, "hr@gmail.com", nguoi_dung=[align["hc"].employee_id])
    _hop_thu(db, "ketoan-bo@gmail.com", nguoi_dung=[align["khac"].employee_id])

    cua_hc = mailbox_service.for_employee(db, align["hc"].employee_id)
    assert [row.id for row in cua_hc] == [hr.id]
    assert mailbox_service.for_employee(db, align["ky"].employee_id) == []


def test_muon_hop_thu_khong_duoc_cap_thi_chan(db, align):
    """`mailbox_id` là một con số trong thân request — ai cũng gõ số khác vào
    được, nên chốt phải nằm ở tầng dịch vụ chứ không ở ô chọn."""
    hr = _hop_thu(db, "hr@gmail.com", nguoi_dung=[align["hc"].employee_id])

    with pytest.raises(HTTPException) as error:
        mailbox_service.ensure_can_use(db, hr.id, align["khac"].employee_id)
    assert error.value.status_code == 403
    assert "hr@gmail.com" in error.value.detail


def test_hop_thu_chua_khai_du_smtp_thi_chan_ngay_luc_ban_hanh(db, align):
    """Chọn xong, ban hành xong, rồi mới phát hiện thư không đi là quá muộn —
    số hiệu đã cấp và không lùi được."""
    hr = _hop_thu(db, "hr@gmail.com", nguoi_dung=[align["hc"].employee_id],
                  day_du=False)

    with pytest.raises(HTTPException) as error:
        mailbox_service.ensure_can_use(db, hr.id, align["hc"].employee_id)
    assert error.value.status_code == 400
    assert "SMTP" in error.value.detail


def test_hop_thu_ngung_dung_thi_chan(db, align):
    hr = _hop_thu(db, "hr@gmail.com", nguoi_dung=[align["hc"].employee_id])
    hr.is_active = False
    db.commit()

    with pytest.raises(HTTPException) as error:
        mailbox_service.ensure_can_use(db, hr.id, align["hc"].employee_id)
    assert "ngừng dùng" in error.value.detail


def test_ban_hanh_kem_hop_thu_thi_thu_bao_mang_dia_chi_do(db, align):
    """Câu chốt của cả tính năng: thư ban hành phải đi bằng hộp thư đã chọn."""
    _bat_luong(db, align)
    hr = _hop_thu(db, "hr@gmail.com", nguoi_dung=[align["hc"].employee_id])
    doc = _ky_het(db, _soan(db, align), align)

    service.approve(db, doc, align["hc"].id, mailbox_id=hr.id)

    db.refresh(doc)
    assert doc.issue_mailbox_id == hr.id
    thu = db.query(EmailLog).filter(EmailLog.event == "document_issued").all()
    assert thu, "Ban hành phải sinh thư báo cho người trong phạm vi"
    assert {row.mailbox_id for row in thu} == {hr.id}, \
        "Mọi thư ban hành phải gắn đúng hộp thư đã chọn"


def test_khong_chon_hop_thu_thi_gui_bang_dia_chi_he_thong(db, align):
    """Đường cũ phải còn nguyên — tính năng này là thêm lựa chọn, không phải
    bắt buộc."""
    _bat_luong(db, align)
    doc = _ky_het(db, _soan(db, align), align)

    service.approve(db, doc, align["hc"].id)

    db.refresh(doc)
    assert doc.issue_mailbox_id is None
    thu = db.query(EmailLog).filter(EmailLog.event == "document_issued").all()
    assert all(row.mailbox_id is None for row in thu)


def test_mat_khau_ung_dung_khong_bao_gio_tro_ve_dang_thuong(db, align):
    hr = _hop_thu(db, "hr@gmail.com", nguoi_dung=[align["hc"].employee_id])

    assert "mat-khau-ung-dung" not in hr.smtp_password_enc
    assert mailbox_service.smtp_route(hr)["password"] == "mat-khau-ung-dung"


def test_sua_ten_hop_thu_khong_lam_mat_mat_khau(db, align):
    """Màn sửa không bao giờ nhận lại được mật khẩu cũ (API không trả), nên nó
    gửi lên chuỗi rỗng ở MỌI lần sửa. Coi rỗng là xóa thì sửa một cái nhãn cũng
    đủ làm hộp thư ngừng gửi được mà không dòng nào báo."""
    hr = _hop_thu(db, "hr@gmail.com", nguoi_dung=[align["hc"].employee_id])

    hr.name = "Phòng Hành chính — Nhân sự"
    mailbox_service.set_password(hr, "")
    db.commit()

    assert mailbox_service.ready_to_send(hr) is True
    assert mailbox_service.smtp_route(hr)["password"] == "mat-khau-ung-dung"


def test_xoa_mat_khau_phai_la_thao_tac_rieng(db, align):
    hr = _hop_thu(db, "hr@gmail.com", nguoi_dung=[align["hc"].employee_id])

    mailbox_service.clear_password(hr)
    db.commit()

    assert mailbox_service.ready_to_send(hr) is False


def test_dat_lai_danh_sach_nguoi_dung_theo_lo(db, align):
    hr = _hop_thu(db, "hr@gmail.com", nguoi_dung=[align["hc"].employee_id])

    mailbox_service.set_members(
        db, hr, [align["khac"].employee_id, align["ky"].employee_id], ACTOR)
    db.commit()

    assert set(mailbox_service.member_ids(db, hr.id)) == {
        align["khac"].employee_id, align["ky"].employee_id}
    assert mailbox_service.can_use(db, hr.id, align["hc"].employee_id) is False


def test_hop_thu_cua_phap_nhan_khac_khong_bay_ra(db, align):
    """Cột `company_id` là bộ LỌC HIỂN THỊ: hộp thư của công ty khác không bày
    ra cho rối, hộp thư cấp Tập đoàn (không khai) thì nơi nào cũng thấy."""
    other = Company(code="XXX", name="Công ty khác", level=2, is_active=True)
    db.add(other)
    db.flush()
    specific = _hop_thu(db, "rieng@gmail.com", nguoi_dung=[align["hc"].employee_id],
                     company_id=other.id)
    chung = _hop_thu(db, "chung@gmail.com", nguoi_dung=[align["hc"].employee_id])

    thay = mailbox_service.for_employee(db, align["hc"].employee_id,
                                       align["seed"].company_id)
    assert {row.id for row in thay} == {chung.id}
    thay_o_kia = mailbox_service.for_employee(db, align["hc"].employee_id, other.id)
    assert {row.id for row in thay_o_kia} == {specific.id, chung.id}
