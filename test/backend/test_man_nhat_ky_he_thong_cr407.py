"""bao-CR-407 / CR-312 P5 — màn NHẬT KÝ HỆ THỐNG `/system/logs`, đợt backend.

Năm thứ được canh ở đây, đều là thứ hỏng trong im lặng:

1. **Lượt gọi KHÔNG đẻ dấu vết nào vẫn phải lên màn.** Một cú `DELETE` ăn 403 để
   `tab_audit_log` trống trơn — mà đó đúng là dòng người ta đi tra. Lấy
   `tab_audit_log` làm xương sống thì nó biến mất, và không ai biết là đã mất.
2. **Số truy vấn không phụ thuộc số dòng.** Nhét một lượt tra vào vòng lặp thì
   lúc dữ liệu ít không ai thấy; nó nổ trên hệ thật, ở màn 200 dòng.
3. **Thiếu khóa `change_log` thì LƯỢC Ở BACKEND.** Giá trị cũ có thể chứa tên
   nhà cung cấp — thứ cả cơ chế phương án dựng ra để giấu. Giấu bằng giao diện
   thì mở DevTools ra là đọc được.
4. **`build_summary` phải chạy được trên bộ máy CSDL đang dùng.** Bản đầu viết
   `DATE_FORMAT` + `IF()` của MySQL: đúng trên hệ thật, không bao giờ được kiểm.
5. **Ô «Đến» chỉ có ngày phải kéo tới 23:59:59.** Thiếu thì lọc *"hôm nay"* trả
   về đúng những gì xảy ra lúc 00:00:00 — màn vẫn có dữ liệu nên không ai nghi.

Tài liệu: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §7, §8.2–8.4.
"""
import uuid
from datetime import datetime

import pytest
from sqlalchemy import event

from app.core.logging_codes import (ACTION_GROUP_DELETE, ACTION_GROUP_EDIT, CHANGE_OP_ADD,
                                    CHANGE_OP_UPDATE, SOURCE_API, SOURCE_SCRIPT)
from app.core.permissions import ENTITIES, ENTITY_LABELS
from app.core.scoping import PUBLIC, SCOPE_FIELDS
from app.modules.audit.model import AuditLog
from app.modules.change_log.model import ChangeLog
from app.modules.login_session.model import LoginSession
from app.modules.request_log.model import RequestLog
from app.modules.system_log import service
from app.modules.user.model import User


# ── Dụng cụ dựng dữ liệu ────────────────────────────────────────────────────────

def _rid() -> bytes:
    return uuid.uuid4().bytes


def _add_request(db, *, rid=None, at=None, user_id=1, http_status=200, route="/api/units",
                 method="POST", path="/api/units", source=SOURCE_API, ip="10.0.0.1",
                 error_code="", error_detail=None, request_body=None, response_body=None,
                 session_id=None, audit_count=0, change_count=0):
    row = RequestLog(
        request_id=rid or _rid(), source=source, created_at=at or datetime(2026, 9, 15, 9, 30),
        user_id=user_id, session_id=session_id, ip=ip, method=method, path=path, route=route,
        query_string="", http_status=http_status, error_code=error_code,
        error_detail=error_detail, request_body=request_body, response_body=response_body,
        duration_ms=12, audit_count=audit_count, change_count=change_count)
    db.add(row)
    db.flush()
    return row


def _add_audit(db, rid, *, action="update", message="Sửa đơn vị tính", entity="unit",
               entity_id=1, doc_code="", action_group=ACTION_GROUP_EDIT, created_by=1,
               changed_fields="", change_count=0):
    row = AuditLog(entity=entity, entity_id=entity_id, action=action, message=message,
                   request_id=rid, doc_code=doc_code, action_group=action_group,
                   created_by=created_by, changed_fields=changed_fields,
                   change_count=change_count)
    db.add(row)
    db.flush()
    return row


def _add_change(db, rid, *, table_name="tab_unit", row_id=1, field="name",
                before_value="Cái", after_value="Chiếc", op=CHANGE_OP_UPDATE,
                is_masked=False, snapshot_json=None):
    row = ChangeLog(request_id=rid, table_name=table_name, row_id=row_id, op=op,
                    field=field, before_value=before_value, after_value=after_value,
                    is_masked=is_masked, snapshot_json=snapshot_json, created_by=1)
    db.add(row)
    db.flush()
    return row


class _QueryCounter:
    """Đếm câu SQL thật sự gửi xuống, không đếm lời gọi hàm."""

    def __init__(self, db):
        self.bind = db.get_bind()
        self.n = 0

    def _hook(self, *args, **kwargs):
        self.n += 1

    def __enter__(self):
        event.listen(self.bind, "before_cursor_execute", self._hook)
        return self

    def __exit__(self, *exc):
        event.remove(self.bind, "before_cursor_execute", self._hook)
        return False


# ── 1. Hai khóa quyền mới ───────────────────────────────────────────────────────

def test_hai_khoa_quyen_moi_khai_du():
    """`audit` + `change_log` phải có mặt ở CẢ BA chỗ, không thì một chỗ lệch là
    `apply_scope` chặn sạch (B-07) hoặc màn Phân quyền không hiện nổi ô để tick."""
    assert "audit" in ENTITIES
    assert "change_log" in ENTITIES
    assert ENTITY_LABELS.get("audit")
    assert ENTITY_LABELS.get("change_log")
    #  PUBLIC là một quyết định: cắt nhật ký theo phạm vi của người tra thì đúng
    #  lượt cần nhìn nhất (403 ngoài phạm vi, script chạy dưới user_id = 0) biến mất.
    assert SCOPE_FIELDS["audit"] is PUBLIC
    assert SCOPE_FIELDS["change_log"] is PUBLIC


def test_quan_ly_thu_mua_khong_tu_co_khoa_nhat_ky():
    """Vòng `_PUR_MANAGER_PERMS` quét cả `ENTITIES` — quên đưa vào `_SYS_ENTITIES`
    là Quản lý thu mua đọc được giá trị trước/sau của MỌI phân hệ khác."""
    from app.seed import _PUR_MANAGER_PERMS, _SYS_ENTITIES
    assert "audit" in _SYS_ENTITIES
    assert "change_log" in _SYS_ENTITIES
    assert "audit" not in _PUR_MANAGER_PERMS
    assert "change_log" not in _PUR_MANAGER_PERMS


# ── 2. Đọc mã lượt gọi ──────────────────────────────────────────────────────────

def test_parse_request_id_nhan_ca_hai_dang():
    raw = uuid.uuid4()
    assert service.parse_request_id(str(raw)) == raw.bytes
    assert service.parse_request_id(raw.hex) == raw.bytes
    assert service.parse_request_id("  " + str(raw) + " ") == raw.bytes


@pytest.mark.parametrize("bad", ["", "   ", "summary", "123", "khong-phai-uuid"])
def test_parse_request_id_tra_none_thay_vi_no(bad):
    """Trả `None` chứ không ném: controller cần phân biệt «gõ bậy» (404 tử tế)
    với «lỗi hệ thống» (500)."""
    assert service.parse_request_id(bad) is None


# ── 3. Xương sống là request_log ────────────────────────────────────────────────

def test_luot_bi_chan_khong_co_dau_vet_van_len_man(db):
    """Cú DELETE ăn 403: `tab_audit_log` trống, dòng vẫn phải có mặt.

    Đây là LÝ DO cả tệp service lấy `tab_request_log` làm xương sống. Đổi sang
    join từ audit thì bài kiểm này đỏ ngay — đó là điều mong muốn.
    """
    _add_request(db, http_status=403, method="DELETE", path="/api/units/9",
                 route="/api/units/{id}")
    rows = service.build_page(db, service.build_query(db), 0, 20)
    assert len(rows) == 1
    #  Không có dòng audit thì cột «Lần bấm» rơi về `METHOD path` — thô, nhưng có.
    assert rows[0]["summary"] == "DELETE /api/units/9"
    assert rows[0]["http_status"] == 403


def test_cot_lan_bam_lay_dong_audit_DAU_TIEN(db):
    """Cú Duyệt ghi `approve` rồi mới ghi vài dòng phụ (sinh việc, gửi chuông).
    Lấy dòng cuối thì màn hiện «Tạo thông báo» cho thứ người ta nhớ là «Duyệt»."""
    rid = _rid()
    _add_request(db, rid=rid, audit_count=3)
    _add_audit(db, rid, action="approve", message="Duyệt phiếu YCMH-0012",
               doc_code="YCMH-0012")
    _add_audit(db, rid, action="create", message="Tạo việc cho người duyệt chặng 2")
    _add_audit(db, rid, action="create", message="Tạo thông báo")

    rows = service.build_page(db, service.build_query(db), 0, 20)
    assert rows[0]["summary"] == "Duyệt phiếu YCMH-0012"
    assert rows[0]["action"] == "approve"
    assert rows[0]["doc_code"] == "YCMH-0012"


def test_cot_doi_dem_so_BANG_khong_phai_so_truong(db):
    """`change_count` (số TRƯỜNG) đã nằm sẵn trên `tab_request_log`. Thứ cột «Đổi»
    còn thiếu là «đụng mấy bảng» — con số phân biệt sửa một ô đơn giá với một cú
    Duyệt kéo theo bảng việc + bảng thông báo + bảng chứng từ."""
    rid = _rid()
    _add_request(db, rid=rid, change_count=3)
    _add_change(db, rid, table_name="tab_purchase_order", field="status")
    _add_change(db, rid, table_name="tab_purchase_order", field="approved_at")
    _add_change(db, rid, table_name="tab_approval_task", field="state")

    rows = service.build_page(db, service.build_query(db), 0, 20)
    assert rows[0]["change_count"] == 3        # ba TRƯỜNG
    assert rows[0]["change_table_count"] == 2  # hai BẢNG


def test_hai_so_khong_cung_nghia(db):
    """`user_id = 0` ở bảng này nghĩa là CHƯA ĐĂNG NHẬP, khác với `created_by = 0`
    của audit nghĩa là HỆ THỐNG LÀM. Cùng con số, khác chuyện — nên khác nhãn."""
    _add_request(db, user_id=0, source=SOURCE_API, route="/api/auth/login")
    _add_request(db, user_id=0, source=SOURCE_SCRIPT, route="")

    rows = service.build_page(db, service.build_query(db), 0, 20)
    nhan = {r["route"]: r["user_name"] for r in rows}
    assert nhan["/api/auth/login"] == "(chưa đăng nhập)"
    assert nhan[""] == "hệ thống"


# ── 4. Số truy vấn không phụ thuộc số dòng ──────────────────────────────────────

def _seed_page(db, n: int) -> None:
    for i in range(n):
        rid = _rid()
        _add_request(db, rid=rid, user_id=1, audit_count=1, change_count=1,
                     at=datetime(2026, 9, 15, 9, i % 60))
        _add_audit(db, rid, message=f"Sửa dòng {i}")
        _add_change(db, rid, row_id=i)
    db.flush()


def test_so_truy_van_khong_tang_theo_so_dong(db):
    """Trang 3 dòng và trang 30 dòng phải tốn ĐÚNG BẰNG NHAU.

    Canh tính hằng chứ không canh con số: nhét một lượt tra vào vòng lặp thì lúc
    dữ liệu ít không ai thấy, nó nổ trên hệ thật ở màn 200 dòng.
    """
    db.add(User(email="a@x.vn", employee_id=0, password_hash="x", is_active=True))
    _seed_page(db, 30)

    with _QueryCounter(db) as c3:
        assert len(service.build_page(db, service.build_query(db), 0, 3)) == 3
    with _QueryCounter(db) as c30:
        assert len(service.build_page(db, service.build_query(db), 0, 30)) == 30

    assert c3.n == c30.n
    #  Trần: 3 bảng nhật ký + tối đa 2 lượt tra tên.
    assert c30.n <= 5


def test_trang_rong_khong_hoi_gi_them(db):
    """Không dòng nào thì đừng bắn `IN ()` sang hai bảng con."""
    with _QueryCounter(db) as c:
        assert service.build_page(db, service.build_query(db), 0, 20) == []
    assert c.n == 1


# ── 5. Bộ lọc ───────────────────────────────────────────────────────────────────

def test_loc_ket_qua_tach_LOI_khoi_BI_CHAN(db):
    """401/403 là hệ thống làm đúng việc, 5xx là hệ thống hỏng. Trộn vào một bộ
    lọc thì câu hỏi «hôm nay hỏng gì» luôn bị vùi dưới hàng trăm lượt 403."""
    _add_request(db, http_status=200, route="/ok")
    _add_request(db, http_status=403, route="/chan")
    _add_request(db, http_status=401, route="/chan2")
    _add_request(db, http_status=500, route="/hong")

    def _routes(status):
        q = service.build_query(db, status=status)
        return {r["route"] for r in service.build_page(db, q, 0, 20)}

    assert _routes(service.STATUS_ERROR) == {"/hong"}
    assert _routes(service.STATUS_BLOCKED) == {"/chan", "/chan2"}
    assert len(_routes(service.STATUS_ALL)) == 4


def test_loc_theo_ma_chung_tu_di_qua_bang_audit(db):
    rid_a, rid_b = _rid(), _rid()
    _add_request(db, rid=rid_a, route="/a")
    _add_request(db, rid=rid_b, route="/b")
    _add_audit(db, rid_a, doc_code="YCMH-0012")
    _add_audit(db, rid_b, doc_code="YCMH-0099")

    q = service.build_query(db, doc_code="YCMH-0012")
    assert {r["route"] for r in service.build_page(db, q, 0, 20)} == {"/a"}


def test_loc_theo_ten_cot_va_ten_bang_di_qua_change_log(db):
    rid_a, rid_b = _rid(), _rid()
    _add_request(db, rid=rid_a, route="/a")
    _add_request(db, rid=rid_b, route="/b")
    _add_change(db, rid_a, table_name="tab_purchase_order", field="unit_price")
    _add_change(db, rid_b, table_name="tab_unit", field="name")

    q = service.build_query(db, field="unit_price")
    assert {r["route"] for r in service.build_page(db, q, 0, 20)} == {"/a"}

    q = service.build_query(db, table="tab_unit")
    assert {r["route"] for r in service.build_page(db, q, 0, 20)} == {"/b"}

    #  Khai cả hai thì phải là VÀ, không phải HOẶC.
    q = service.build_query(db, table="tab_unit", field="unit_price")
    assert service.build_page(db, q, 0, 20) == []


def test_loc_theo_nhom_hanh_dong(db):
    rid_a, rid_b = _rid(), _rid()
    _add_request(db, rid=rid_a, route="/a")
    _add_request(db, rid=rid_b, route="/b")
    _add_audit(db, rid_a, action_group=ACTION_GROUP_DELETE, action="delete")
    _add_audit(db, rid_b, action_group=ACTION_GROUP_EDIT)

    q = service.build_query(db, action_group=ACTION_GROUP_DELETE)
    assert {r["route"] for r in service.build_page(db, q, 0, 20)} == {"/a"}


def test_o_den_chi_co_ngay_phai_keo_toi_cuoi_ngay(db):
    """Thiếu nhịp này thì lọc «hôm nay» trả về đúng những gì xảy ra lúc 00:00:00
    — màn vẫn có dữ liệu nên không ai nghi ngờ."""
    _add_request(db, at=datetime(2026, 9, 15, 0, 0, 0), route="/nua-dem")
    _add_request(db, at=datetime(2026, 9, 15, 17, 45), route="/chieu")
    _add_request(db, at=datetime(2026, 9, 16, 8, 0), route="/hom-sau")

    q = service.build_query(db, from_time="2026-09-15", to_time="2026-09-15")
    assert {r["route"] for r in service.build_page(db, q, 0, 20)} == {"/nua-dem", "/chieu"}


def test_khoang_mac_dinh_la_HOM_NAY_dung_mot_ngay(db):
    hom_nay = datetime.now().date().isoformat()
    assert service.default_range() == (hom_nay, hom_nay)


# ── 6. Ngăn bốn tab & chốt che dữ liệu ──────────────────────────────────────────

def _seed_detail(db):
    rid = _rid()
    row = _add_request(db, rid=rid, http_status=500, error_code="LOI_HE_THONG",
                       error_detail="Traceback ...", request_body={"price": 120000},
                       response_body={"message": "loi"}, audit_count=1, change_count=1)
    _add_audit(db, rid, message="Sửa đơn giá", changed_fields="unit_price", change_count=1)
    _add_change(db, rid, table_name="tab_purchase_order_item", field="unit_price",
                before_value="100000", after_value="120000")
    return row


def test_thieu_khoa_change_log_thi_LUOC_O_BACKEND(db):
    """Giá trị cũ có thể chứa TÊN NHÀ CUNG CẤP — thứ cả cơ chế phương án dựng ra
    để giấu với người yêu cầu. Giấu bằng giao diện thì mở DevTools ra là thấy."""
    row = _seed_detail(db)
    goi = service.build_detail(db, row, with_change_log=False)

    assert goi["changes"] == []
    assert goi["can_read_changes"] is False
    for o in ("request_body", "response_body", "error_detail"):
        assert o not in goi["request"], f"«{o}» vẫn lọt ra ngoài"
    #  Phần kể chuyện thì vẫn đọc được — đó là khác biệt giữa hai khóa.
    assert goi["audit"][0]["message"] == "Sửa đơn giá"


def test_co_khoa_change_log_thi_tra_du(db):
    row = _seed_detail(db)
    goi = service.build_detail(db, row, with_change_log=True)

    assert goi["can_read_changes"] is True
    assert goi["request"]["request_body"] == {"price": 120000}
    assert goi["request"]["error_detail"] == "Traceback ..."
    assert len(goi["changes"]) == 1
    assert goi["changes"][0]["before_value"] == "100000"
    assert goi["changes"][0]["after_value"] == "120000"


def test_co_can_read_changes_de_phan_biet_KHONG_DOI_voi_KHONG_DUOC_XEM(db):
    """Không có cờ này thì cả hai đều là mảng rỗng, và tab «Thay đổi» nói dối."""
    rid = _rid()
    row = _add_request(db, rid=rid)          # lượt GET, không đổi gì
    goi = service.build_detail(db, row, with_change_log=True)
    assert goi["changes"] == []
    assert goi["can_read_changes"] is True   # rỗng vì KHÔNG ĐỔI


def test_tab_phien_canh_bao_doi_IP(db):
    """Vào từ một IP, dùng tiếp từ IP khác — dấu hiệu token bị mang đi máy khác
    (BM-003). Tính ở backend vì giao diện không nên tự đặt luật cảnh báo."""
    ses = LoginSession(user_id=1, token_id="t1", ip="1.1.1.1", last_seen_ip="2.2.2.2",
                       device_label="Chrome / Windows", os="Windows", browser="Chrome")
    db.add(ses)
    db.flush()
    row = _add_request(db, session_id=ses.id)

    goi = service.build_detail(db, row, with_change_log=True)
    assert goi["session"]["ip_changed"] is True

    #  Lượt không gắn phiên (script, Celery) thì để None chứ đừng dựng gói rỗng.
    assert service.build_detail(db, _add_request(db), with_change_log=True)["session"] is None


def test_find_request_tra_none_thay_vi_no_khi_khong_co(db):
    """Mã hợp lệ nhưng không có dòng nào (đã dọn theo hạn lưu, hoặc gõ từ nhật ký
    của môi trường khác) phải ra `None` để controller trả 404 tử tế."""
    rid = _rid()
    _add_request(db, rid=rid, route="/co-that")
    assert service.find_request(db, rid).route == "/co-that"
    assert service.find_request(db, _rid()) is None


# ── 7. Biểu đồ — phải chạy được trên bộ máy CSDL của bài kiểm ───────────────────

def test_build_summary_chay_duoc_khong_dung_ham_rieng_cua_mysql(db):
    """Bản đầu viết `DATE_FORMAT` + `IF()`: đúng trên hệ thật, không bao giờ được
    kiểm vì `test/backend` chạy SQLite. Sai kiểu đó thì không chỗ nào đỏ lên."""
    _add_request(db, at=datetime(2026, 9, 15, 9, 10), route="/api/units", http_status=200)
    _add_request(db, at=datetime(2026, 9, 15, 9, 50), route="/api/units", http_status=500,
                 error_code="LOI_HE_THONG")
    _add_request(db, at=datetime(2026, 9, 15, 10, 5), route="/api/products", http_status=403)

    so = service.build_summary(db, service.build_query(db))

    assert [h["hour"] for h in so["by_hour"]] == ["2026-09-15 09", "2026-09-15 10"]
    assert so["by_hour"][0] == {"hour": "2026-09-15 09", "total": 2, "errors": 1}
    #  «Hỏng» của biểu đồ giờ là 5xx; của biểu đồ endpoint là từ 400 trở lên —
    #  hai câu hỏi khác nhau, cố ý hai ngưỡng.
    assert so["by_hour"][1] == {"hour": "2026-09-15 10", "total": 1, "errors": 0}
    assert {r["route"]: r for r in so["by_route"]}["/api/products"]["failed"] == 1
    assert so["by_error"] == [{"error_code": "LOI_HE_THONG", "total": 1}]


def test_bieu_do_va_bang_dung_CHUNG_bo_loc(db):
    """Hai đường lọc riêng là kiểu sai kinh điển: người dùng lọc bảng rồi tin
    biểu đồ bên trên, mà biểu đồ vẫn đang vẽ toàn hệ."""
    _add_request(db, route="/api/units", http_status=200)
    _add_request(db, route="/api/units", http_status=500)

    q = service.build_query(db, status=service.STATUS_ERROR)
    so = service.build_summary(db, q)
    assert sum(h["total"] for h in so["by_hour"]) == 1
    assert len(service.build_page(db, q, 0, 20)) == 1


# ── 8. Dòng thời gian của phiếu nối được sang màn này ───────────────────────────

def test_audit_log_tra_them_ba_o_de_noi_sang_man_nhat_ky(db):
    """`/api/audit-logs` phải trả `request_id` dạng chuỗi, và RỖNG với dòng ghi
    trước P1 — giao diện tự ẩn nút «Xem chi tiết», đừng dựng link tới chuỗi trống."""
    from app.modules.audit.controller import list_logs  # noqa: F401  (đảm bảo import được)
    rid = _rid()
    moi = _add_audit(db, rid, changed_fields="unit_price", change_count=1)
    cu = _add_audit(db, None, message="Dòng ghi trước P1")

    from app.core.request_context import request_id_text
    assert request_id_text(moi.request_id) == str(uuid.UUID(bytes=rid))
    assert request_id_text(cu.request_id) == ""


# ── 9. Dòng audit cũ (request_id NULL) không lên màn này ────────────────────────

def test_dong_audit_cu_khong_lot_vao_man(db):
    """Hệ quả đã biết của việc lấy `tab_request_log` làm xương sống: dòng audit
    ghi trước P1 không có `request_id` nên không có lượt gọi nào để gộp vào.
    Chúng vẫn đọc được ở dòng thời gian từng phiếu — ghi rõ để khỏi đi tìm lỗi."""
    _add_audit(db, None, message="Dòng ghi trước P1")
    assert service.build_page(db, service.build_query(db), 0, 20) == []


def test_serialize_change_giu_co_da_che(db):
    """«Đã che» và «đổi từ rỗng sang rỗng» là hai chuyện khác nhau, mà lúc đi tra
    thì khác nhau rất nhiều — nên `is_masked` là cột riêng, phải trả ra."""
    rid = _rid()
    row = _add_request(db, rid=rid)
    _add_change(db, rid, field="password_hash", before_value=None, after_value=None,
                is_masked=True)
    _add_change(db, rid, table_name="tab_unit", op=CHANGE_OP_ADD, field="",
                before_value=None, after_value=None, snapshot_json={"name": "Chiếc"})

    doi = service.build_detail(db, row, with_change_log=True)["changes"]
    assert doi[0]["is_masked"] is True
    assert doi[1]["snapshot_json"] == {"name": "Chiếc"}
    assert doi[1]["op_label"]
