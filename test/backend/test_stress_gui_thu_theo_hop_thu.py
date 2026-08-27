"""STRESS TEST ĐƯỜNG GỬI THƯ THEO HỘP THƯ (26/08/2026).

Hai bài trước phủ hai tầng khác: `test_chon_hop_thu_khi_ban_hanh.py` lo **luật**
(ai được dùng hộp thư nào, mật khẩu cất ra sao), `test_api_hop_thu_gui.py` lo
**API** (danh sách mở được không). Còn tầng cuối — thứ quyết định người nhận
THẬT SỰ thấy địa chỉ gì — thì tới giờ **chưa dòng nào chạy qua**:
`notification/service.send_smtp_email` mới được sửa để đăng nhập bằng SMTP của
hộp thư, mà nó nằm trong tác vụ nền nên không bài kiểm nào chạm tới.

Đó đúng là chỗ nguy hiểm nhất của cả tính năng, và nguy hiểm theo kiểu **hỏng
im lặng**: chỉ đổi tiêu đề `From` mà không đăng nhập đúng hộp thư thì Gmail ghi
đè địa chỉ về tài khoản hệ thống, thư vẫn gửi đi, `EmailLog` vẫn ghi `sent` —
không ai biết cho tới lúc người nhận nói *"sao thư này lại từ địa chỉ kia"*.

Nên bài kiểm ở đây **chặn `smtplib.SMTP` lại và soi từng lời gọi**: đăng nhập
bằng tài khoản nào, phong bì mang địa chỉ người gửi nào, tiêu đề `From` ra sao.

Bốn nhóm:
  1. gửi ĐÚNG danh nghĩa hộp thư đã chọn — câu chốt của cả tính năng;
  2. không chọn thì lùi về SMTP dùng chung — đường cũ phải còn nguyên;
  3. hộp thư hỏng giữa chừng (bị xóa · ngừng dùng · mất mật khẩu) thì **lùi an
     toàn**, không để thư nằm chết trong hàng đợi;
  4. chuỗi đầu–cuối thật: khai hộp thư qua API → ban hành → soi thư gửi ra.
"""
import smtplib
from types import SimpleNamespace

import pytest

from app.modules.approval import action_service, instance_service
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, SKIP_NONE,
                                             ApprovalFlow, ApprovalNode,
                                             ApprovalSwitch)
from app.modules.doc_catalog.model import DocType
from app.modules.document import service as doc_service
from app.modules.document.model import STATUS_EFFECTIVE, STATUS_PENDING_ISSUE
from app.modules.document.schema import ApproveIn, DocumentCreate
from app.modules.employee.model import Employee
from app.modules.notification import mailbox_service
from app.modules.notification import service as noti_service
from app.modules.notification.mailbox_controller import MailboxIn
from app.modules.notification.mailbox_model import Mailbox, MailboxMember
from app.modules.notification.model import EmailLog
from app.modules.user.model import User

ACTOR = 1
ENTITY = "document"


# ── Máy chủ SMTP giả — ghi lại MỌI lời gọi ──────────────────────────────────

class SMTPGia:
    """Đứng thay `smtplib.SMTP`, ghi lại đúng ba thứ cần soi.

    Ghi vào một danh sách dùng chung chứ không dùng `Mock`: khẳng định đọc ra
    phải là câu tiếng người (*"đăng nhập bằng hr@gmail.com"*), không phải
    `call_args_list[0][0][1]`.
    """

    ghi: list = []

    def __init__(self, host, port=587, *a, **kw):
        self.instance = {"host": host, "port": port, "tls": False,
                      "login": None, "envelope_from": None, "raw": ""}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        SMTPGia.ghi.append(self.instance)
        return False

    def starttls(self, *a, **kw):
        self.instance["tls"] = True

    def login(self, user, password):
        self.instance["login"] = (user, password)

    def sendmail(self, from_addr, to_addrs, msg):
        self.instance["envelope_from"] = from_addr
        self.instance["to"] = to_addrs
        self.instance["raw"] = msg


@pytest.fixture()
def smtp(monkeypatch):
    SMTPGia.ghi = []
    monkeypatch.setattr(smtplib, "SMTP", SMTPGia)
    return SMTPGia


@pytest.fixture()
def bat_email(monkeypatch):
    """Bật công tắc email + khai SMTP dùng chung, y như hệ đang chạy.

    ⚠️ Phải chặn ở `app_settings.get`, KHÔNG ghi dòng `tab_setting` vào DB test:
    `app_settings._load()` tự mở `SessionLocal()` — tức MySQL thật — nên mọi dòng
    cấu hình ghi vào SQLite trong bộ nhớ đều vô hình với nó. Lần đầu viết bài này
    tôi ghi vào DB test và cả 9 ca cùng xanh giả: `send_smtp_email` dừng ngay ở
    nhánh «email đang tắt», không nối SMTP lần nào, mà khẳng định thì không có
    cái nào bắt được chuyện đó.

    Không bật thì cả tệp này thành bài kiểm rỗng — nên `bat_email` là điều kiện
    tiên quyết của mọi ca dưới đây.
    """
    from app.core import app_settings

    CAU_HINH = {
        "email_enabled": True,
        "smtp_host": "smtp.hethong.vn",
        "smtp_port": 587,
        "smtp_user": "he-thong@dego.vn",
        "smtp_from": "he-thong@dego.vn",
        "smtp_password": "mk-he-thong",
        "email_test_override": "",
    }
    monkeypatch.setattr(app_settings, "get", lambda key: CAU_HINH.get(key, ""))
    return CAU_HINH


class _PhienKhongDongDuoc:
    """Phiên DB mà `close()` KHÔNG làm gì.

    `send_smtp_email` chạy trong tác vụ nền nên nó tự mở phiên rồi `close()` ở
    `finally` — đúng với chạy thật. Nhưng bài kiểm chỉ có MỘT phiên SQLite trong
    bộ nhớ; để nó đóng thật thì mọi khẳng định sau đó nổ `DetachedInstanceError`,
    và tệ hơn là cả CSDL biến mất theo.
    """

    def __init__(self, db):
        self._db = db

    def __getattr__(self, name):
        return getattr(self._db, name)

    def close(self):
        pass


def _phien_db(db):
    """Nhà máy phiên truyền cho `send_smtp_email`. Xem `_PhienKhongDongDuoc`."""
    return lambda: _PhienKhongDongDuoc(db)


def _hop_thu(db, email="hr@gmail.com", *, name="Phòng Hành chính", host="smtp.gmail.com",
             password="mk-hr", tls=True, hoat_dong=True, nguoi_dung=()):
    row = Mailbox(code=email.split("@")[0].upper()[:30], name=name, email=email,
                  display_name=name, smtp_host=host, smtp_port=587,
                  smtp_user=email, use_tls=tls, is_active=hoat_dong,
                  created_by=ACTOR, updated_by=ACTOR)
    if password:
        mailbox_service.set_password(row, password)
    db.add(row)
    db.flush()
    for emp in nguoi_dung:
        db.add(MailboxMember(mailbox_id=row.id, employee_id=emp,
                             created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    return row


def _thu(db, mailbox_id=None, to="nguoinhan@dego.vn"):
    log = EmailLog(event="document_issued", to_email=to, subject="[Văn bản mới] TB-01",
                   status="pending", mailbox_id=mailbox_id, created_by=ACTOR)
    db.add(log)
    db.commit()
    return log


def _gui(db, log, to="nguoinhan@dego.vn"):
    noti_service.send_smtp_email(_phien_db(db), log.id, to,
                                 "[Văn bản mới] TB-01", "<p>Nội dung</p>")
    db.expire_all()
    return db.get(EmailLog, log.id)


# ── 1 · Gửi ĐÚNG danh nghĩa hộp thư ─────────────────────────────────────────

def test_dang_nhap_bang_CHINH_hop_thu_chu_khong_phai_tai_khoan_he_thong(db, smtp, bat_email):
    """Câu chốt của cả tính năng.

    Chỉ đổi tiêu đề `From` mà vẫn đăng nhập bằng tài khoản hệ thống thì Gmail ghi
    đè địa chỉ về tài khoản đó — người nhận thấy `he-thong@dego.vn`, còn hệ thì
    ghi `sent` như không có chuyện gì.
    """
    hr = _hop_thu(db)
    log = _gui(db, _thu(db, mailbox_id=hr.id))

    assert len(smtp.ghi) == 1
    instance = smtp.ghi[0]
    assert instance["host"] == "smtp.gmail.com", "Phải nối tới máy chủ CỦA HỘP THƯ"
    assert instance["login"] == ("hr@gmail.com", "mk-hr"), \
        "Phải đăng nhập bằng chính hộp thư, không phải tài khoản hệ thống"
    assert instance["envelope_from"] == "hr@gmail.com"
    assert log.status == "sent"


def test_tieu_de_From_mang_ten_hien_thi_kem_dia_chi(db, smtp, bat_email):
    """Người nhận phải thấy «Phòng Hành chính», không phải một địa chỉ trơ."""
    hr = _hop_thu(db)
    _gui(db, _thu(db, mailbox_id=hr.id))

    raw = smtp.ghi[0]["raw"]
    dong_from = next(d for d in raw.splitlines() if d.startswith("From:"))
    assert "hr@gmail.com" in dong_from
    #  Tiếng Việt có dấu bị mã hóa MIME trên dòng tiêu đề — đó là ĐÚNG chuẩn,
    #  nên khẳng định vào phần mã hóa chứ không vào chữ thô.
    assert "=?utf-8?" in dong_from.lower() or "Phòng Hành chính" in dong_from


def test_ghi_lai_dia_chi_NGUOI_NHAN_THAY_vao_nhat_ky(db, smtp, bat_email):
    """Hộp thư đổi địa chỉ về sau thì dòng nhật ký cũ vẫn phải đúng."""
    hr = _hop_thu(db)
    log = _gui(db, _thu(db, mailbox_id=hr.id))

    assert log.from_email == "hr@gmail.com"


def test_hop_thu_tat_TLS_thi_khong_goi_starttls(db, smtp, bat_email):
    """Máy chủ nội bộ không có TLS mà vẫn ép `starttls()` là nổ ngay lúc gửi."""
    noi_bo = _hop_thu(db, "vanthu@noibo.local", host="mail.noibo.local", tls=False)
    _gui(db, _thu(db, mailbox_id=noi_bo.id))

    assert smtp.ghi[0]["tls"] is False


# ── 2 · Không chọn hộp thư → đường CŨ phải còn nguyên ───────────────────────

def test_khong_chon_hop_thu_thi_gui_bang_SMTP_dung_chung(db, smtp, bat_email):
    log = _gui(db, _thu(db, mailbox_id=None))

    instance = smtp.ghi[0]
    assert instance["host"] == "smtp.hethong.vn"
    assert instance["login"] == ("he-thong@dego.vn", "mk-he-thong")
    assert instance["envelope_from"] == "he-thong@dego.vn"
    assert log.status == "sent"


def test_cong_tac_email_TAT_thi_khong_gui_gi_du_da_chon_hop_thu(db, smtp, bat_email, monkeypatch):
    """Hộp thư riêng KHÔNG được phép đi vòng qua hàng rào vận hành."""
    from app.core import app_settings

    bat_email["email_enabled"] = False
    monkeypatch.setattr(app_settings, "get", lambda key: bat_email.get(key, ""))

    hr = _hop_thu(db)
    log = _gui(db, _thu(db, mailbox_id=hr.id))

    assert smtp.ghi == [], "Tắt email mà vẫn nối SMTP là thủng hàng rào"
    assert log.status == "disabled"


# ── 3 · Hộp thư hỏng giữa chừng → LÙI AN TOÀN ──────────────────────────────

def test_hop_thu_bi_xoa_sau_khi_ban_hanh_thi_lui_ve_dia_chi_he_thong(db, smtp, bat_email):
    """Ban hành đã xong và đúng — không được để thư nằm chết vì một dòng danh mục."""
    hr = _hop_thu(db)
    log = _thu(db, mailbox_id=hr.id)
    db.delete(hr)
    db.commit()

    log = _gui(db, log)

    assert log.status == "sent"
    assert smtp.ghi[0]["login"] == ("he-thong@dego.vn", "mk-he-thong")
    assert log.from_email == "he-thong@dego.vn"


def test_hop_thu_mat_mat_khau_thi_lui_chu_khong_bao_loi(db, smtp, bat_email):
    hr = _hop_thu(db)
    log = _thu(db, mailbox_id=hr.id)
    mailbox_service.clear_password(hr)
    db.commit()

    log = _gui(db, log)

    assert log.status == "sent"
    assert smtp.ghi[0]["envelope_from"] == "he-thong@dego.vn"


def test_SMTP_cua_hop_thu_no_thi_ghi_that_bai_kem_ly_do(db, smtp, bat_email, monkeypatch):
    """Sai mật khẩu ứng dụng là ca sẽ gặp thật. Phải ghi lại được để tra."""
    def _no(self, user, password):
        raise smtplib.SMTPAuthenticationError(535, b"Username and Password not accepted")

    monkeypatch.setattr(SMTPGia, "login", _no)
    hr = _hop_thu(db)

    log = _gui(db, _thu(db, mailbox_id=hr.id))

    assert log.status == "failed"
    assert "535" in (log.error or "") or "not accepted" in (log.error or "")


# ── 4 · Chuỗi đầu–cuối: khai qua API → ban hành → soi thư ───────────────────

@pytest.fixture()
def align(db, seed, cap_quyen):
    """Nhân sự hành chính (soạn) + giám đốc (ký) + loại Thông báo chờ ban hành."""
    def _people(code, name, email):
        emp = Employee(code=code, full_name=name, email=email,
                       company_id=seed.company_id, department_id=seed.dept_id,
                       is_active=True)
        db.add(emp)
        db.flush()
        u = User(email=email, employee_id=emp.id, password_hash="x", is_active=True)
        db.add(u)
        db.flush()
        return u

    hc = _people("HC01", "Nhân sự hành chính", "nhanvien@gmail.com")
    gd = _people("GD01", "Giám đốc", "giamdoc@dego.vn")
    governance_flow = _people("QT01", "Quản trị", "admin@dego.vn")
    cap_quyen(governance_flow.id, "mailbox", scope="all",
              read=True, create=True, write=True, delete=True)

    tb = DocType(code="TB", name="Thông báo", id_scheme=1, number_when=2,
                 auto_issue_after_approval=False)
    db.add(tb)
    db.commit()

    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True,
                          created_by=ACTOR, updated_by=ACTOR))
    flow = ApprovalFlow(entity=ENTITY, code="VB-01", name="Duyệt văn bản",
                        is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, name="Giám đốc ký",
                        approver_kind=APPROVER_EMPLOYEE,
                        approver_ref=str(gd.employee_id), skip_duplicate=SKIP_NONE,
                        created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    return {"hc": hc, "gd": gd, "qt": governance_flow, "tb": tb, "seed": seed}


def test_chuoi_day_du_tu_khai_hop_thu_den_thu_gui_ra(db, smtp, bat_email, align):
    """Đúng ca khách mô tả, chạy trọn một lượt qua API thật.

    Quản trị khai `hr@gmail.com` và cấp cho nhân sự hành chính → người đó soạn
    Thông báo nghỉ lễ bằng tài khoản `nhanvien@gmail.com` → giám đốc ký → văn bản
    dừng ở *Chờ ban hành* → chính người soạn bấm Ban hành và chọn `hr@gmail.com`
    → thư đi ra mang danh nghĩa phòng Hành chính.
    """
    from app.modules.notification import mailbox_controller as mb_ctl

    # (a) Quản trị khai hộp thư và cấp cho nhân sự hành chính.
    create = mb_ctl.create_mailbox(MailboxIn(
        code="HR", name="Phòng Hành chính", email="hr@gmail.com",
        display_name="Phòng Hành chính", smtp_host="smtp.gmail.com", smtp_port=587,
        smtp_user="hr@gmail.com", smtp_password="mk-hr", use_tls=True,
        company_id=None, note="", is_active=True,
        employee_ids=[align["hc"].employee_id],
    ), db=db, user=align["qt"])
    import json
    mailbox_id = json.loads(create.body)["data"]["id"]

    # (b) Nhân sự hành chính soạn và gửi duyệt.
    doc = doc_service.create_document(db, DocumentCreate(
        doc_type_id=align["tb"].id, company_id=align["seed"].company_id,
        department_id=align["seed"].dept_id,
        owner_employee_id=align["hc"].employee_id,
        drafter_employee_id=align["hc"].employee_id,
        title="Thông báo nghỉ lễ 2/9",
        content_html="<p>Nghỉ từ 01/9 đến 03/9.</p>",
    ), align["hc"].id)
    doc_service.submit(db, doc, align["hc"].id)

    # (c) Giám đốc ký → DỪNG ở «Chờ ban hành», chưa cấp số, chưa gửi thư nào.
    instance = instance_service.running_instance(db, ENTITY, doc.id)
    action_service.approve(db, instance, align["gd"].employee_id, align["gd"].id, {})
    db.refresh(doc)
    assert doc.status == STATUS_PENDING_ISSUE
    assert not (doc.doc_code or doc.issue_number)
    assert db.query(EmailLog).count() == 0, "Chưa ban hành thì chưa báo cho ai"

    # (d) Chính người soạn bấm Ban hành, chọn hộp thư.
    doc_service.ensure_can_issue(db, doc, align["hc"])
    mailbox_service.ensure_can_use(db, mailbox_id, align["hc"].employee_id)
    doc_service.approve(db, doc, align["hc"].id, mailbox_id=mailbox_id)

    db.refresh(doc)
    assert doc.status == STATUS_EFFECTIVE
    assert (doc.doc_code or doc.issue_number), "Ban hành phải cấp số"
    assert doc.issue_mailbox_id == mailbox_id

    # (e) Thư ban hành gắn đúng hộp thư, và gửi ra đúng danh nghĩa.
    thu = db.query(EmailLog).filter(EmailLog.event == "document_issued").all()
    assert thu, "Ban hành phải sinh thư cho người trong phạm vi"
    assert {row.mailbox_id for row in thu} == {mailbox_id}

    for row in thu:
        _gui(db, row, to=row.to_email)
    assert smtp.ghi, "Phải có ít nhất một lượt gửi"
    for phien_smtp in smtp.ghi:
        assert phien_smtp["login"] == ("hr@gmail.com", "mk-hr")
        assert phien_smtp["envelope_from"] == "hr@gmail.com"


def test_nguoi_khac_khong_muon_duoc_hop_thu_khi_ban_hanh(db, align):
    """Chốt cuối cùng: `mailbox_id` là số trong thân request, ai cũng gõ được."""
    from fastapi import HTTPException

    hr = _hop_thu(db, nguoi_dung=[align["hc"].employee_id])

    with pytest.raises(HTTPException) as error:
        mailbox_service.ensure_can_use(db, hr.id, align["gd"].employee_id)
    assert error.value.status_code == 403
