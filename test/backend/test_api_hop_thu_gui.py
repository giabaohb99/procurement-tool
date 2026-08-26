"""API HỘP THƯ GỬI — gọi THẲNG hàm controller (26/08/2026).

⚠️ Tệp này sinh ra từ một lỗi thật, ghi lại để không lặp: `test_chon_hop_thu_khi_ban_hanh.py`
kiểm rất kỹ tầng **dịch vụ** (quyền dùng hộp thư, mật khẩu, thư mang địa chỉ nào)
nhưng **không gọi endpoint nào**. Kết quả là màn *Hộp thư gửi* mở ra ăn ngay
**500** ở lần bấm đầu tiên, vì hàm `list_mailboxes` gọi hai tiện ích dùng chung
bằng chữ ký **tự bịa**:

  · `apply_filters(query, Model, {...}, like_fields=..., eq_fields=...)` — chữ ký
    thật là `apply_filters(query, model, request, filterable)`, nhận `Request`
    chứ không nhận dict;
  · `pagination(query, page, page_size)` trả `(rows, meta)` — thật ra nó là một
    **dependency** trả về dict tham số, không chạy truy vấn;
  · `success(data, meta=...)` — `success()` không có tham số `meta`.

Cả ba đều là lỗi *chỉ nổ khi chạy thật*, không một bài kiểm tầng dịch vụ nào bắt
được. Nên bài kiểm ở đây đi qua **đúng hàm mà FastAPI gọi**, và ca đầu tiên chỉ
hỏi đúng một câu: *danh sách có mở được không*.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.response import success
from app.modules.employee.model import Employee
from app.modules.notification import mailbox_controller as mb_ctl
from app.modules.notification import mailbox_service
from app.modules.notification.mailbox_controller import MailboxIn
from app.modules.notification.mailbox_model import Mailbox
from app.modules.user.model import User

ACTOR = 1


def _doc(response) -> object:
    """Bóc phong bì `{success, message, data}` để khẳng định trên `data`."""
    import json

    assert response.status_code == 200, response.body
    return json.loads(response.body)["data"]


@pytest.fixture()
def canh(db, seed, cap_quyen):
    """Một quản trị có đủ quyền `mailbox`, và một nhân sự để cấp hộp thư."""
    nhan_su = Employee(code="HC01", full_name="Nhân sự hành chính",
                       email="nhanvien@gmail.com", company_id=seed.company_id,
                       department_id=seed.dept_id, is_active=True)
    db.add(nhan_su)
    db.flush()
    quan_tri = User(email="admin@dego", employee_id=nhan_su.id,
                    password_hash="x", is_active=True)
    db.add(quan_tri)
    db.commit()

    cap_quyen(quan_tri.id, "mailbox", scope="all",
              read=True, create=True, write=True, delete=True)
    return {"user": quan_tri, "emp": nhan_su, "seed": seed}


def _payload(**doi):
    goc = {
        "code": "HR", "name": "Phòng Hành chính", "email": "hr@gmail.com",
        "display_name": "Phòng Hành chính", "smtp_host": "smtp.gmail.com",
        "smtp_port": 587, "smtp_user": "hr@gmail.com",
        "smtp_password": "mat-khau-ung-dung", "use_tls": True,
        "company_id": None, "note": "", "is_active": True, "employee_ids": [],
    }
    goc.update(doi)
    return MailboxIn(**goc)


# ── 1 · Câu hỏi số một: danh sách MỞ ĐƯỢC không ─────────────────────────────

def test_danh_sach_mo_duoc_khi_chua_co_hop_thu_nao(db, canh):
    """Đúng cú bấm đầu tiên của người dùng — và đúng chỗ đã nổ 500."""
    assert _doc(mb_ctl.list_mailboxes(db=db, user=canh["user"])) == []


def test_danh_sach_tra_thang_MOT_MANG_khong_boc_phan_trang(db, canh):
    """Tầng gọi khai `apiGet<Mailbox[]>` nên phản hồi phải là mảng.

    Bọc thêm phong bì phân trang là tạo hình dạng thứ hai mà màn hình không bóc,
    và bảng sẽ rỗng mà không báo lỗi gì.
    """
    mb_ctl.create_mailbox(_payload(), db=db, user=canh["user"])

    data = _doc(mb_ctl.list_mailboxes(db=db, user=canh["user"]))
    assert isinstance(data, list) and len(data) == 1
    assert data[0]["email"] == "hr@gmail.com"


# ── 2 · Tạo · sửa · đọc lại ────────────────────────────────────────────────

def test_tao_hop_thu_va_doc_lai_duoc(db, canh):
    tao = _doc(mb_ctl.create_mailbox(
        _payload(employee_ids=[canh["emp"].id]), db=db, user=canh["user"]))

    assert tao["code"] == "HR"
    assert tao["employee_ids"] == [canh["emp"].id]
    assert tao["ready"] is True, "Khai đủ máy chủ + mật khẩu thì phải sẵn sàng gửi"

    doc_lai = _doc(mb_ctl.get_mailbox(tao["id"], db=db, user=canh["user"]))
    assert doc_lai["email"] == "hr@gmail.com"


def test_API_KHONG_BAO_GIO_tra_mat_khau_ra_ngoai(db, canh):
    """Chỉ trả cờ `has_password`, không trả giá trị — kể cả bản đã mã hóa."""
    tao = _doc(mb_ctl.create_mailbox(_payload(), db=db, user=canh["user"]))

    assert tao["has_password"] is True
    assert "smtp_password" not in tao
    assert "smtp_password_enc" not in tao
    assert "mat-khau-ung-dung" not in str(tao)


def test_sua_ten_ma_de_trong_o_mat_khau_thi_KHONG_mat_mat_khau(db, canh):
    """Cái bẫy chính của màn này — xem `mailbox_service.dat_mat_khau`.

    Màn sửa không nhận lại được mật khẩu cũ (API không trả) nên nó gửi chuỗi rỗng
    ở MỌI lần sửa. Coi rỗng là xóa thì đổi một cái nhãn cũng đủ làm hộp thư ngừng
    gửi được, mà không dòng nào báo.
    """
    tao = _doc(mb_ctl.create_mailbox(_payload(), db=db, user=canh["user"]))

    sua = _doc(mb_ctl.update_mailbox(
        tao["id"], _payload(name="Phòng Hành chính — Nhân sự", smtp_password=""),
        db=db, user=canh["user"]))

    assert sua["name"] == "Phòng Hành chính — Nhân sự"
    assert sua["has_password"] is True and sua["ready"] is True


def test_xoa_mat_khau_la_mot_duong_RIENG(db, canh):
    tao = _doc(mb_ctl.create_mailbox(_payload(), db=db, user=canh["user"]))

    sau = _doc(mb_ctl.clear_password(tao["id"], db=db, user=canh["user"]))

    assert sau["has_password"] is False
    assert sau["ready"] is False, "Mất mật khẩu là không gửi được nữa"


def test_dia_chi_sai_dinh_dang_thi_chan(db):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        _payload(email="hr-at-gmail")


def test_dia_chi_luon_ve_chu_thuong(db, canh):
    """Hai dòng `HR@Gmail.com` và `hr@gmail.com` là một địa chỉ — ràng buộc duy
    nhất trên cột chỉ chặn được khi đã chuẩn hóa."""
    tao = _doc(mb_ctl.create_mailbox(
        _payload(email="HR@Gmail.COM"), db=db, user=canh["user"]))

    assert tao["email"] == "hr@gmail.com"


# ── 3 · Ngừng dùng, và lọc ─────────────────────────────────────────────────

def test_ngung_dung_chu_KHONG_xoa_han(db, canh):
    """Nhật ký thư cũ còn trỏ vào đây — câu «thư đó gửi danh nghĩa ai» phải trả
    lời được mãi về sau."""
    tao = _doc(mb_ctl.create_mailbox(_payload(), db=db, user=canh["user"]))

    sau = _doc(mb_ctl.delete_mailbox(tao["id"], db=db, user=canh["user"]))

    assert sau["is_active"] is False
    assert db.get(Mailbox, tao["id"]) is not None, "Bản ghi phải còn trong bảng"
    #  Ngừng dùng rồi thì không ai chọn được nó lúc ban hành nữa.
    assert mailbox_service.cua_nhan_su(db, canh["emp"].id) == []


def test_loc_theo_tu_khoa_va_trang_thai(db, canh):
    mb_ctl.create_mailbox(_payload(), db=db, user=canh["user"])
    mb_ctl.create_mailbox(
        _payload(code="KT", name="Phòng Kế toán", email="ketoan@gmail.com"),
        db=db, user=canh["user"])

    chi_hr = _doc(mb_ctl.list_mailboxes(db=db, user=canh["user"], q="hr@"))
    assert [row["email"] for row in chi_hr] == ["hr@gmail.com"]

    tim_ten = _doc(mb_ctl.list_mailboxes(db=db, user=canh["user"], q="Kế toán"))
    assert [row["code"] for row in tim_ten] == ["KT"]

    con_dung = _doc(mb_ctl.list_mailboxes(db=db, user=canh["user"], is_active=True))
    assert len(con_dung) == 2


# ── 4 · Danh sách hộp thư CỦA TÔI ──────────────────────────────────────────

def test_hop_thu_cua_toi_chi_ra_cai_minh_duoc_cap(db, canh, cap_quyen):
    """Đường mà hộp thoại Ban hành gọi. Người chưa được cấp thì thấy rỗng."""
    mb_ctl.create_mailbox(_payload(employee_ids=[canh["emp"].id]),
                          db=db, user=canh["user"])

    nguoi_khac = User(email="khac@dego", employee_id=canh["seed"].emp_tp_id,
                      password_hash="x", is_active=True)
    db.add(nguoi_khac)
    db.commit()
    cap_quyen(nguoi_khac.id, "document", scope="all", read=True)

    cua_toi = _doc(mb_ctl.my_mailboxes(db=db, user=canh["user"]))
    assert [row["email"] for row in cua_toi] == ["hr@gmail.com"]

    assert _doc(mb_ctl.my_mailboxes(db=db, user=nguoi_khac)) == []
