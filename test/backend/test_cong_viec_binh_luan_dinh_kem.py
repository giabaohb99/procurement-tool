"""Phân hệ Dự án — BÌNH LUẬN (E-01) và ĐÍNH KÈM (E-03) của một công việc.

Cả hai đi qua hạ tầng DÙNG CHUNG (`tab_comment`, `tab_file` + `tab_file_link`)
chứ không đẻ bảng riêng, nên chúng thừa hưởng luôn cửa kiểm quyền của hạ tầng ấy
— mà cửa đó được thiết kế cho `apply_scope`, thứ **vô dụng với phân hệ này**.

Đây là chỗ thủng nếu ai đó gỡ nhánh riêng đi:

`work_task` khai `PUBLIC` ở `core/scoping.SCOPE_FIELDS` vì phạm vi thật của nó là
"thành viên của danh sách chứa việc", không diễn đạt được bằng cột phòng ban hay
pháp nhân. Cho nên nếu bình luận/đính kèm đi đường chung:
  - `comment.service.resolve_doc` → `apply_scope` không lọc gì → ai đăng nhập
    cũng bình luận được vào việc của dự án mình không tham gia;
  - `attachment.controller._check` → `ensure_in_scope` im lặng cho qua (không có
    nhánh `parent_records` cho entity này) → đoán đúng id là tải được tệp.

Cả hai đúng là lỗ mà §5.1 và §5.4 của `04-phan-quyen.md` bắt phải khóa.
"""
import pytest
from fastapi import HTTPException

from app.core.comment_registry import COMMENT_POLICY, doc_model, policy
from app.core.file_registry import FILE_POLICY
from app.modules.attachment import controller as ac
from app.modules.comment import service as comment_service
from app.modules.work import list_service, schema, task_service
from app.modules.work.membership_service import Actor
from app.modules.work.model import WorkMemberRole

COMPANY = 1


def _nguoi(uid: int, emp_id: int) -> Actor:
    return Actor(user_id=uid, employee_id=emp_id, company_id=COMPANY)


class _User:
    """Tài khoản giả — `resolve_doc` / `_check` chỉ đọc `id` và `employee_id`."""

    def __init__(self, uid: int, employee_id: int):
        self.id = uid
        self.employee_id = employee_id


@pytest.fixture(autouse=True)
def ho_so_nhan_su(db):
    """Hai hồ sơ nhân sự THẬT cho hai tài khoản giả.

    Bắt buộc, không phải trang trí: cả hai cửa mới đều gọi `resolve_actor`, mà
    hàm ấy TRA BẢNG `Employee` theo `user.employee_id` — không có dòng thật thì
    nó trả `employee_id = 0` và `require_employee` chặn ở 400 «chưa gắn nhân
    sự», che mất đúng cái 403 mà bài test đang muốn đo.
    """
    from app.modules.employee.model import Employee

    for emp_id, ten in ((11, "Chủ dự án"), (22, "Người ngoài")):
        if db.get(Employee, emp_id) is None:
            db.add(Employee(id=emp_id, code=f"NV{emp_id}", full_name=ten,
                            company_id=COMPANY))
    db.commit()


@pytest.fixture()
def chu(db):
    return _nguoi(1, 11)


@pytest.fixture()
def nguoi_ngoai(db):
    return _nguoi(2, 22)


@pytest.fixture()
def mo_khoa_rbac(monkeypatch):
    """Mở sẵn lớp RBAC để bài test nhắm đúng lớp THÀNH VIÊN.

    Lớp vai trò đã có bài riêng ở `test_cong_viec_phan_quyen.py`; ở đây nó chỉ
    che mất thứ đang muốn đo.
    """
    monkeypatch.setattr(comment_service, "user_has_permission", lambda *a, **k: True)
    monkeypatch.setattr(ac, "user_has_permission", lambda *a, **k: True)


def _tao_list(db, actor, name="Dự án A"):
    return list_service.create_list(db, actor, schema.ListCreate(name=name))


def _tao_task(db, actor, list_id, title="Việc A"):
    return task_service.create_task(
        db, actor, schema.TaskCreate(list_id=list_id, title=title))


# ── Khai báo trong hai bộ đăng ký ───────────────────────────────────────────────

def test_khai_du_o_ca_hai_bo_dang_ky():
    """Thiếu một trong hai là tính năng chết câm với thông báo 400 khó hiểu."""
    assert "work_task" in COMMENT_POLICY
    assert doc_model("work_task") is not None
    assert "work_task" in FILE_POLICY


def test_route_thong_bao_ghi_dang_v2_khong_thi_chuong_cam():
    """Link chuông dựng bằng `route + "/" + id`.

    `toAppPath` bên frontend chỉ giữ nguyên link khớp tiền tố v2; ghi `/work/...`
    là nó trả `null` và cái chuông bấm vào không đi đâu cả.
    """
    _, _, route = policy("work_task")
    assert route.startswith("/project/")


def test_dinh_kem_cong_viec_nhan_ca_anh_lan_tai_lieu():
    #  Ảnh chụp màn hình là thứ dán vào việc nhiều nhất; chỉ cho tài liệu là hụt.
    _, exts, _ = FILE_POLICY["work_task"]
    assert {"png", "jpg", "pdf", "xlsx"} <= exts


# ── Bình luận: lớp THÀNH VIÊN ───────────────────────────────────────────────────

def test_thanh_vien_binh_luan_duoc(db, chu, mo_khoa_rbac):
    lst = _tao_list(db, chu)
    task = _tao_task(db, chu, lst["id"])
    doc, nhan, _ = comment_service.resolve_doc(db, _User(1, 11), "work_task", task["id"])
    assert doc.id == task["id"]
    assert nhan


def test_nguoi_ngoai_khong_binh_luan_duoc_du_co_du_quyen_vai_tro(db, chu, mo_khoa_rbac):
    """Bài khóa chính. RBAC mở toang mà vẫn phải 403 — vì họ không ở trong dự án."""
    lst = _tao_list(db, chu)
    task = _tao_task(db, chu, lst["id"])

    with pytest.raises(HTTPException) as e:
        comment_service.resolve_doc(db, _User(2, 22), "work_task", task["id"])
    assert e.value.status_code == 403


def test_khach_xem_doc_duoc_binh_luan_nhung_khong_gui_duoc(db, chu, mo_khoa_rbac):
    """VIEWER là một vai trò THẬT của phân hệ này, nên hai chiều phải tách.

    Dùng chung một mức cho cả đọc lẫn ghi thì hoặc khách xem không đọc nổi phần
    trao đổi của việc họ được mời vào xem, hoặc họ ghi được vào đó.
    """
    lst = _tao_list(db, chu)
    task = _tao_task(db, chu, lst["id"])
    list_service.add_member(
        db, chu, lst["id"],
        schema.MemberIn(employee_id=22, role=int(WorkMemberRole.VIEWER)))
    khach = _User(2, 22)

    #  Đọc: được.
    doc, _, _ = comment_service.resolve_doc(db, khach, "work_task", task["id"])
    assert doc.id == task["id"]

    #  Gửi: chặn.
    with pytest.raises(HTTPException) as e:
        comment_service.resolve_doc(db, khach, "work_task", task["id"], "write")
    assert e.value.status_code == 403


def test_thanh_vien_thuong_gui_duoc_binh_luan(db, chu, mo_khoa_rbac):
    lst = _tao_list(db, chu)
    task = _tao_task(db, chu, lst["id"])
    list_service.add_member(
        db, chu, lst["id"],
        schema.MemberIn(employee_id=22, role=int(WorkMemberRole.MEMBER)))

    doc, _, _ = comment_service.resolve_doc(db, _User(2, 22), "work_task", task["id"], "write")
    assert doc.id == task["id"]


def test_viec_da_xoa_thi_khong_binh_luan_duoc_nua(db, chu, mo_khoa_rbac):
    lst = _tao_list(db, chu)
    task = _tao_task(db, chu, lst["id"])
    task_service.delete_task(db, chu, task["id"])

    with pytest.raises(HTTPException) as e:
        comment_service.resolve_doc(db, _User(1, 11), "work_task", task["id"])
    assert e.value.status_code == 403


def test_id_viec_khong_co_that_cung_403_chu_khong_404(db, chu, mo_khoa_rbac):
    #  Phân biệt 403 với 404 là đã nói cho người ngoài biết id đó có thật.
    _tao_list(db, chu)
    with pytest.raises(HTTPException) as e:
        comment_service.resolve_doc(db, _User(1, 11), "work_task", 999_999)
    assert e.value.status_code == 403


# ── Đính kèm: lớp THÀNH VIÊN ────────────────────────────────────────────────────

def test_thanh_vien_xem_va_gan_duoc_dinh_kem(db, chu, mo_khoa_rbac):
    lst = _tao_list(db, chu)
    task = _tao_task(db, chu, lst["id"])
    nguoi = _User(1, 11)

    exts, max_mb = ac._check(db, nguoi, "work_task", "read", task["id"])
    assert "pdf" in exts and max_mb > 0
    ac._check(db, nguoi, "work_task", "manage", task["id"])


def test_nguoi_ngoai_khong_tai_duoc_dinh_kem_du_doan_dung_id(db, chu, mo_khoa_rbac):
    """Bài khóa §5.4 — RBAC mở toang, chặn phải đến từ tư cách thành viên."""
    lst = _tao_list(db, chu)
    task = _tao_task(db, chu, lst["id"])

    with pytest.raises(HTTPException) as e:
        ac._check(db, _User(2, 22), "work_task", "read", task["id"])
    assert e.value.status_code == 403


def test_khach_xem_doc_duoc_nhung_khong_gan_go_duoc_tep(db, chu, mo_khoa_rbac):
    lst = _tao_list(db, chu)
    task = _tao_task(db, chu, lst["id"])
    list_service.add_member(
        db, chu, lst["id"],
        schema.MemberIn(employee_id=22, role=int(WorkMemberRole.VIEWER)))
    khach = _User(2, 22)

    #  Đọc thì được — khách xem vẫn phải mở được tệp của dự án mình được mời vào.
    ac._check(db, khach, "work_task", "read", task["id"])

    with pytest.raises(HTTPException) as e:
        ac._check(db, khach, "work_task", "manage", task["id"])
    assert e.value.status_code == 403


def test_tai_tep_tam_chua_gan_vao_viec_nao_thi_khong_soi_thanh_vien(db, chu, mo_khoa_rbac):
    """`POST /upload-file` gửi `entity_id=None` — chưa có việc nào để soi.

    Không được vì thế mà nổ: đây là bước một của lối "tải trước, gắn sau".
    """
    exts, max_mb = ac._check(db, _User(1, 11), "work_task", "manage", None)
    assert exts and max_mb > 0


def test_tai_khoan_khong_gan_nhan_su_bi_chan_som_va_noi_ro_ly_do(db, chu, mo_khoa_rbac):
    """`employee_id = 0` (tài khoản kỹ thuật) không tham gia dự án được."""
    lst = _tao_list(db, chu)
    task = _tao_task(db, chu, lst["id"])

    for tai_khoan in (_User(9, 0), _User(9, 404_404)):   # chưa gắn · gắn hồ sơ đã xóa
        with pytest.raises(HTTPException) as e:
            ac._check(db, tai_khoan, "work_task", "read", task["id"])
        assert e.value.status_code == 400
        assert "nhân sự" in e.value.detail


def test_dinh_kem_van_di_qua_lop_rbac_chu_khong_chi_thanh_vien(db, chu, monkeypatch):
    """Không mở `mo_khoa_rbac`: thiếu quyền vai trò thì chặn TRƯỚC cả thành viên.

    Hai lớp phải còn đủ cả hai — gỡ lớp nào cũng là một lỗ.
    """
    lst = _tao_list(db, chu)
    task = _tao_task(db, chu, lst["id"])
    monkeypatch.setattr(ac, "user_has_permission", lambda *a, **k: False)

    with pytest.raises(HTTPException) as e:
        ac._check(db, _User(1, 11), "work_task", "read", task["id"])
    assert e.value.status_code == 403


# ── Số bình luận trên thẻ ───────────────────────────────────────────────────────

def test_so_binh_luan_tren_the_dem_dung_sau_khi_ghi(db, chu, mo_khoa_rbac):
    """`comment_counts` đã đếm sẵn `tab_comment` từ lâu, nay mới có đường ghi.

    Đếm phải nhìn thấy bình luận vừa tạo, và KHÔNG đếm lây của việc khác.
    """
    lst = _tao_list(db, chu)
    a = _tao_task(db, chu, lst["id"], "Việc A")
    b = _tao_task(db, chu, lst["id"], "Việc B")
    nguoi = _User(1, 11)

    comment_service.create_comment(db, "work_task", a["id"], "Xong chưa?", nguoi.id)

    assert task_service.get_task(db, chu, a["id"])["comment_count"] == 1
    assert task_service.get_task(db, chu, b["id"])["comment_count"] == 0
