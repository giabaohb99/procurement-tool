"""
test_ho_so_cua_toi_cr378.py — cửa `GET /api/employees/me` của màn *Trang cá nhân*.

Màn `/me` cần đủ hồ sơ nhân sự của chính người đang đăng nhập. Cửa `/{eid}` có
sẵn **không dùng được** cho việc đó: nó gác bằng `require("employee", "read")`,
mà khóa đó là khóa xem hồ sơ NGƯỜI KHÁC — **9 trong 19 vai trò seed không có**
(Nhân sự, Tài xế, Người đặt xe, Văn thư duyệt dấu, Hỗ trợ, Diễn đàn…). Đo trên
bản chạy: tài khoản `TESTREQ` gọi `/api/employees/92` — **hồ sơ của chính họ** —
nhận đúng `403 Không có quyền: read employee`.

Bộ này canh bốn thứ, xếp theo mức thiệt hại nếu vỡ:

  1. **Cửa `/me` không được gác bằng `employee.read`.** Ai đó "dọn dẹp cho nhất
     quán" mà thêm khóa vào là chín vai trò trên mất luôn trang cá nhân — mà lỗi
     đó không đỏ ở đâu cả, chỉ có người dùng thấy 403.
  2. **`/me` phải khai TRƯỚC `/{eid}`.** FastAPI dò route theo thứ tự khai; để
     sau thì «me» rơi vào `eid: int` và trả 422.
  3. **Chỉ trả hồ sơ của CHÍNH MÌNH** — id lấy từ phiên đăng nhập, không từ URL.
  4. **Tài khoản chưa gắn nhân sự trả `None`, không nổ.** Admin và tài khoản hệ
     thống có `employee_id = 0`.
"""
import json

from app.modules.employee import controller
from app.modules.employee.model import Employee


def _call_me(db, employee_id: int) -> dict:
    """Gọi cửa `/me` rồi bóc phong bì.

    `core.response.success` trả `JSONResponse` chứ không trả dict, nên phải đọc
    `.body` — gọi thẳng rồi index vào là `TypeError`.
    """
    return json.loads(controller.get_my_employee(db=db, user=_FakeUser(employee_id)).body)


def _route(path: str):
    """Route khai ở `controller.router` theo đường dẫn."""
    for r in controller.router.routes:
        if getattr(r, "path", None) == path:
            return r
    raise AssertionError(f"Không tìm thấy route {path}")


def _guards(route) -> str:
    """Gộp mã của mọi dependency thành chuỗi để soi có `require(...)` không."""
    names = []
    for dep in getattr(route, "dependant", None).dependencies:
        call = getattr(dep, "call", None)
        names.append(getattr(call, "__qualname__", "") or repr(call))
    return " ".join(names)


class _FakeUser:
    """Chỉ cần đúng thứ cửa `/me` đọc: id nhân sự gắn với tài khoản."""

    def __init__(self, employee_id: int):
        self.id = 1
        self.employee_id = employee_id


def _emp(db, code="NS900", **kw):
    obj = Employee(code=code, full_name=kw.pop("full_name", "Người Thử"),
                   is_active=True, **kw)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ── 1. Cửa /me KHÔNG được gác bằng employee.read ────────────────────────────

def test_self_route_is_not_gated_by_the_employee_read_key():
    """Thêm `require("employee","read")` vào đây là chín vai trò mất trang cá nhân.

    Khóa đó dành cho việc xem hồ sơ NGƯỜI KHÁC. Hồ sơ của chính mình thì id lấy
    từ phiên đăng nhập nên không có gì để leo thang — gác thêm chỉ chặn nhầm.
    """
    guards = _guards(_route("/api/employees/me"))
    assert "get_current_user" in guards, "Cửa /me phải đòi đăng nhập"
    assert "require" not in guards, (
        "Cửa /me KHÔNG được gác bằng require(...): xem ghi chú đầu tệp — "
        "9/19 vai trò seed không có employee.read và sẽ mất trang cá nhân."
    )


def test_reading_someone_elses_profile_is_still_gated():
    """Ngược lại: cửa `/{eid}` phải GIỮ nguyên khóa, đừng nới theo."""
    assert "require" in _guards(_route("/api/employees/{eid}")), (
        "Cửa /{eid} là cửa xem hồ sơ người khác — bỏ khóa ở đây là lộ hồ sơ toàn công ty."
    )


# ── 2. Thứ tự khai route ────────────────────────────────────────────────────

def test_self_route_is_declared_before_the_id_route():
    """`/me` phải đứng trước `/{eid}`, nếu không «me» rơi vào `eid: int` → 422."""
    paths = [getattr(r, "path", "") for r in controller.router.routes]
    assert paths.index("/api/employees/me") < paths.index("/api/employees/{eid}")


# ── 3. Chỉ trả hồ sơ của chính mình ─────────────────────────────────────────

def test_returns_the_callers_own_record(db):
    mine = _emp(db, code="NS901", full_name="Của Tôi")
    _emp(db, code="NS902", full_name="Của Người Khác")

    body = _call_me(db, mine.id)

    assert body["success"] is True
    assert body["data"]["id"] == mine.id
    assert body["data"]["full_name"] == "Của Tôi"


def test_sensitive_fields_stay_visible_on_ones_own_profile(db):
    """Ngoại lệ `self`: không ai phải xin quyền để đọc CCCD của chính mình.

    Đây là lý do cửa này tồn tại — chặn thì trang cá nhân rỗng một nửa với chính
    chủ, đúng ca mà ghi chú ở `sensitive.can_read_sensitive` đã lường trước.
    """
    mine = _emp(db, code="NS903", id_number="079200001234", bank_name="Vietcombank")

    data = _call_me(db, mine.id)["data"]

    assert data["id_number"] == "079200001234"
    assert data["bank_name"] == "Vietcombank"


# ── 4. Tài khoản chưa gắn nhân sự ───────────────────────────────────────────

def test_account_without_an_employee_link_returns_none_not_an_error(db):
    """Admin và tài khoản hệ thống có `employee_id = 0` — đó là trạng thái hợp
    lệ, không phải lỗi. Ném 404 vào mặt họ là báo sai."""
    body = _call_me(db, 0)

    assert body["success"] is True
    assert body["data"] is None
    assert "chưa gắn" in body["message"].lower()


def test_a_dangling_employee_link_does_not_blow_up(db):
    """Hồ sơ bị xóa mà tài khoản còn trỏ tới — dữ liệu lệch, không phải lỗi của
    người đang đăng nhập."""
    body = _call_me(db, 999_999)

    assert body["success"] is True
    assert body["data"] is None
