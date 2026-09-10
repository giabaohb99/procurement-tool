"""bao-CR-312 P1 — lớp MÁY của nhật ký: `tab_request_log` + ngữ cảnh cho audit.

Bốn thứ được kiểm ở đây, đều là thứ hỏng trong im lặng nếu sai:

1. **Lượt bị chặn phải để lại dấu.** Hôm nay một cú `DELETE` ăn 403 không nằm ở
   đâu cả, vì `record(...)` đứng SAU cửa quyền nên chưa kịp chạy.
2. **GHI HẾT, KỂ CẢ ĐỌC** (bao-CR-346, đảo QĐ-A). Trước đây chỉ ghi vài đuôi
   đường dẫn "đáng ngờ" và bỏ lượt gia hạn phiên thành công. Cả hai đều sai:
   luật đuôi đường dẫn quyết định TRƯỚC khi endpoint chạy nên một GET ăn 403
   cũng không để lại gì, còn `/auth/refresh` lại đúng là chỗ token bị cắp lộ ra
   (BM-003). Nay chỉ bỏ hai đầu gọi máy dội (`/notifications`, `/alerts`) và
   đường của chính nhật ký, đổi lại có cơ chế dọn dòng GET quá 90 ngày.
3. **Che mật khẩu.** Ghi nhầm MỘT lần là chuỗi băm nằm trong nhật ký vĩnh viễn,
   và không ai đi rà lại một bảng chỉ-thêm vài trăm nghìn dòng.
4. **QĐ-B** — `request_id` là 16 byte nhị phân ở cả hai bảng, và là **cùng một
   giá trị**, vì đó là sợi dây duy nhất nối lớp máy với lớp kể chuyện.

Tài liệu: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §4.1, §4.2, §4.5.
"""
import json
import uuid
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.orm import sessionmaker

from app.core.audit import record
from app.core.device_fingerprint import device_hash, device_label, normalize_user_agent
from app.core.action_catalog import group_of_action
from app.core.logging_codes import (ACTION_GROUP_AUTH, ACTION_GROUP_DELETE, ACTION_GROUP_EDIT,
                                    ACTION_GROUP_PERMISSION, ACTOR_KIND_SYSTEM, ACTOR_KIND_USER,
                                    SOURCE_API)
from app.core.logging_policy import (mask_error_detail, mask_payload, should_capture_response,
                                     should_log_request, should_skip_by_result, summarize_success)
from app.core.request_context import open_context, request_id_text
from app.core.request_middleware import RequestContextMiddleware
from app.main import http_exception_handler, validation_exception_handler
from app.modules.audit.model import AuditLog
from app.modules.request_log.model import RequestLog
from app.modules.request_log.tasks import cleanup_get_logs_task
from app.modules.role.service import describe_permission_change


# ---------------------------------------------------------------------------
# Luật "ghi hay không" — hàm thuần, kiểm trực tiếp
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("method,path,ghi", [
    ("POST", "/api/units", True),
    ("PATCH", "/api/units/3", True),
    ("DELETE", "/api/units/3", True),
    #  Giao diện gọi `/api/notifications` + `/api/alerts` liên tục để đếm chuông:
    #  4.427 trong 7.440 lượt GET một ngày trên prod, tức 59,5% chỉ để vẽ con số
    #  đỏ trên hình cái chuông. Đó là máy dội máy, không phải người xem gì.
    ("GET", "/api/notifications", False),
    ("GET", "/api/alerts", False),
    #  ...nhưng BỎ THEO PHƯƠNG THỨC, không bỏ theo đường dẫn: bấm "đánh dấu đã
    #  đọc" là một thao tác thật của người dùng trên chính đường dẫn đó.
    ("PATCH", "/api/notifications/55", True),
    #  Mọi lượt ĐỌC khác đều ghi. Luật cũ chỉ nhặt vài đuôi (`/export`, `/print`,
    #  `/view`) nên `/download`, `/preview`, `/chain/zip` — cũng là tải dữ liệu
    #  ra ngoài — lọt sạch, mà thêm đuôi mãi thì luôn thiếu cái vừa ai đó đặt.
    ("GET", "/api/reports/export", True),
    ("GET", "/api/purchase-orders/12/print", True),
    ("GET", "/api/attachments/88/view", True),
    ("GET", "/api/attachments/88/download", True),
    ("GET", "/api/employees", True),
    #  NT-5: đường nhật ký không tự ghi chính nó, kẻo mỗi lần mở màn lại đẻ
    #  thêm dòng để đọc.
    ("POST", "/api/system-logs/search", False),
    ("GET", "/api/audit-logs", False),
    ("GET", "/api/health", False),
])
def test_luot_nao_duoc_ghi(method, path, ghi):
    assert should_log_request(method, path) is ghi


def test_qd_a_da_bi_dao_khong_bo_luot_nao_theo_ket_qua():
    """QĐ-A cũ bỏ lượt gia hạn phiên THÀNH CÔNG. Nay không bỏ nữa.

    Hai lý do: 126 lượt/ngày là con số không đáng kể cạnh ~3.000 GET/ngày, và
    `/auth/refresh` chính là nơi một refresh token bị cắp lộ mặt — nó thành công
    ở máy kẻ trộm, nên đúng cái ca bị bỏ mới là ca cần nhìn (BM-003).
    """
    assert should_skip_by_result("/api/auth/refresh", 200) is False
    assert should_skip_by_result("/api/auth/refresh", 401) is False
    assert should_skip_by_result("/api/auth/login", 200) is False


@pytest.mark.parametrize("method,status,giu", [
    #  GET thành công: thân trả về là dữ liệu người dùng vốn được xem, chép lại
    #  chỉ tổ nhân đôi cả CSDL vào bảng nhật ký.
    ("GET", 200, False),
    #  GET hỏng thì giữ — "vì sao 403" mới là thứ đi tra.
    ("GET", 403, True),
    ("GET", 500, True),
    ("POST", 200, True),
    ("DELETE", 204, True),
])
def test_khi_nao_giu_than_tra_ve(method, status, giu):
    assert should_capture_response(method, status) is giu


def test_che_theo_ten_khoa_di_sau_vao_trong():
    goc = {"username": "admin", "password": "bí mật",
           "items": [{"token": "abc", "qty": 3}], "nested": {"new_password": "x"}}

    che = mask_payload(goc)

    assert che == {"username": "admin", "password": "***",
                   "items": [{"token": "***", "qty": 3}], "nested": {"new_password": "***"}}
    #  Chép chứ không sửa tại chỗ: endpoint còn đọc `goc` sau middleware.
    assert goc["password"] == "bí mật"


def test_che_ca_khoa_co_tien_to_hau_to():
    """Khớp CHÍNH XÁC là hụt: `PUT /api/settings` không gửi khóa tên `password`."""
    che = mask_payload({"values": {"smtp_password": "brevo-app-pass",
                                   "r2_secret_access_key": "R2SECRET",
                                   "r2_access_key_id": "AKIA",
                                   "smtp_host": "smtp-relay.brevo.com"}})

    assert che["values"] == {"smtp_password": "***", "r2_secret_access_key": "***",
                             "r2_access_key_id": "***",
                             #  Che nhầm cũng có giá cả — thứ vô hại phải đi qua.
                             "smtp_host": "smtp-relay.brevo.com"}


def test_che_gia_tri_sql_trong_vet_loi():
    """A1 — lỗ rò TO NHẤT của cả lớp nhật ký, và không khóa nào tên `password`.

    `error_detail` lưu nguyên `traceback.format_exc()`. SQLAlchemy nhét NGUYÊN
    VĂN tham số câu lệnh vào lời báo lỗi, nên một cú `IntegrityError` lúc tạo
    tài khoản là chuỗi băm mật khẩu nằm vĩnh viễn trong nhật ký — ở đúng dòng
    mà `request_body` đã che cẩn thận.
    """
    vet = ("Traceback (most recent call last):\n"
           "  File \"service.py\", line 40, in provision_user\n"
           "sqlalchemy.exc.IntegrityError: (1062, \"Duplicate entry 'admin'\")\n"
           "[SQL: INSERT INTO tab_user (username, password) VALUES (%s, %s)]\n"
           "[parameters: {'username': 'admin', 'password': '$2b$12$BAM_THAT'}]\n"
           "(Background on this error at: https://sqlalche.me/e/20/gkpj)")

    che = mask_error_detail(vet)

    assert "$2b$12$BAM_THAT" not in che
    #  Cắt đúng phần giá trị, giữ nguyên phần kể chuyện — bỏ cả vết lỗi thì
    #  không còn tra được "hỏng ở dòng nào".
    assert "IntegrityError" in che and "Duplicate entry" in che
    assert "https://sqlalche.me" in che
    assert mask_error_detail("") == "" and mask_error_detail(None) is None


def test_che_nhieu_cum_tham_so_trong_mot_vet():
    """Ngoại lệ lồng ngoại lệ ra HAI cụm `[parameters:` — che một cụm là hụt.

    Cụm đầu không nằm cuối chuỗi, nên mốc kết phải nhận cả câu "During handling
    of the above exception"; chỉ nhận mỗi dòng "(Background on this error" thì
    cụm đầu nuốt luôn toàn bộ phần vết lỗi còn lại.
    """
    vet = ("sqlalchemy.exc.DataError: (1406, \"Data too long\")\n"
           "[parameters: {'note': 'GIA_TRI_THU_NHAT'}]\n"
           "(Background on this error at: https://sqlalche.me/e/20/9h9h)\n"
           "\nDuring handling of the above exception, another exception occurred:\n"
           "\nsqlalchemy.exc.IntegrityError: (1062, \"Duplicate entry\")\n"
           "[parameters: {'code': 'GIA_TRI_THU_HAI'}]\n"
           "(Background on this error at: https://sqlalche.me/e/20/gkpj)")

    che = mask_error_detail(vet)

    assert "GIA_TRI_THU_NHAT" not in che and "GIA_TRI_THU_HAI" not in che
    #  Phần kể chuyện của CẢ HAI tầng ngoại lệ phải còn nguyên.
    assert "DataError" in che and "IntegrityError" in che
    assert "During handling of the above exception" in che
    assert che.count("[parameters: ***]") == 2


def test_che_vet_loi_khong_treo_khi_khong_co_moc_ket():
    """Chuỗi thay vào chứa lại chính `[parameters:` — tìm lại từ đầu là lặp mãi.

    Bản đầu treo đúng ở đây, và nó treo BÊN TRONG middleware: một cú 500 là một
    lượt gọi API không bao giờ trả lời, rồi hết chỗ trong pool kết nối.
    """
    che = mask_error_detail("Loi gi do [parameters: {'p': 'BI_MAT'}] khong co moc ket")

    assert "BI_MAT" not in che
    assert che == "Loi gi do [parameters: ***]"


def test_tom_tat_ket_qua_2xx_chi_giu_manh_nhan_dang():
    #  Chỉ nhặt khóa nhận dạng, và chỉ khi nó là giá trị đơn.
    assert summarize_success({"id": 12, "code": "DMH01", "items": [1, 2],
                              "note": "dài"}) == {"id": 12, "code": "DMH01"}
    #  Danh sách: đếm + vài id đầu, không chép cả trang dữ liệu vào nhật ký.
    tom_tat = summarize_success([{"id": 3, "name": "a"}, {"id": 9, "name": "b"}])
    assert tom_tat == {"_count": 2, "ids": [3, 9]}
    #  Không có gì nhận dạng được thì thà không ghi còn hơn ghi một dict rỗng.
    assert summarize_success({"note": "không có mã"}) is None
    assert summarize_success("chuỗi") is None


def test_tom_tat_danh_sach_dai_cat_bot_id():
    tom_tat = summarize_success([{"id": i} for i in range(100)])

    assert tom_tat["_count"] == 100      # tổng vẫn đúng...
    assert len(tom_tat["ids"]) == 20     # ...nhưng không kéo cả trăm id vào


# ---------------------------------------------------------------------------
# Dấu thiết bị — chuẩn hóa TRƯỚC khi băm
# ---------------------------------------------------------------------------
CHROME_126 = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.6478.127 Safari/537.36")
CHROME_127 = CHROME_126.replace("126.0.6478.127", "127.0.6533.72")
IPHONE_SAFARI = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
                 "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1")


def test_dau_thiet_bi_khong_doi_khi_trinh_duyet_tu_cap_nhat():
    """Bẫy chết người: băm thẳng `User-Agent` thì sáng thứ Hai cả công ty đổi dấu.

    Chrome tự cập nhật vài tuần một lần. Nếu 126 -> 127 làm đổi dấu thì cảnh báo
    "đổi thiết bị giữa phiên" kêu hàng trăm lần vào đúng ngày không có chuyện gì
    — và sau ba lần như thế thì không ai đọc cảnh báo nữa.
    """
    assert normalize_user_agent(CHROME_126) == "chrome|windows|desktop"
    assert device_hash(CHROME_126) == device_hash(CHROME_127)
    #  Nhưng mang token sang máy khác thì đổi — đó là điều cả cột này tồn tại vì.
    assert device_hash(CHROME_126) != device_hash(IPHONE_SAFARI)
    assert normalize_user_agent(IPHONE_SAFARI) == "safari|ios|mobile"


@pytest.mark.parametrize("ua,mong_doi", [
    #  Edge và Opera tự khai `Chrome/` trong chuỗi của mình — xét sau Chrome thì
    #  mọi thứ lõi Chromium đổ dồn về một dòng và cột này hết phân biệt.
    ("Mozilla/5.0 (Windows NT 10.0) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.2535.51",
     "edge|windows|desktop"),
    ("Mozilla/5.0 (Windows NT 10.0) Chrome/125.0.0.0 Safari/537.36 OPR/111.0.0.0",
     "opera|windows|desktop"),
    #  iPadOS 13 trở đi tự khai là Macintosh — xét iOS sau macOS thì mọi iPad
    #  trong công ty hiện ra như máy Mac để bàn.
    ("Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) Version/17.5 Safari/605.1.15",
     "safari|ios|tablet"),
    ("Mozilla/5.0 (Linux; Android 14; SM-S918B) Chrome/125.0.0.0 Mobile Safari/537.36",
     "chrome|android|mobile"),
    ("python-requests/2.31.0", "tool|unknown|desktop"),
    #  Không khai `User-Agent` cũng là MỘT loại thiết bị ổn định: hôm nay unknown
    #  mai vẫn unknown, tức KHÔNG phải đổi máy. Trả None thì mất tính chất đó.
    ("", "unknown|unknown|desktop"),
    (None, "unknown|unknown|desktop"),
])
def test_chuan_hoa_user_agent(ua, mong_doi):
    assert normalize_user_agent(ua) == mong_doi


def test_doc_nguoc_dau_thanh_chu():
    """Đây là lý do cột `user_agent` KHÔNG cần tồn tại ở `tab_request_log`.

    Miền giá trị là tập đóng chưa tới hai trăm tổ hợp, nên 8 byte vẫn đọc ra chữ.
    Lưu thêm chuỗi thô ~200 byte × mọi dòng là vài trăm MB để chép đi chép lại
    vài chục giá trị giống nhau.
    """
    assert device_label(device_hash(CHROME_126)) == "chrome|windows|desktop"
    #  Dấu lạ (dòng cũ, hoặc ai đó vừa thêm luật mới) không được làm sập màn đọc.
    assert device_label(b"\x00" * 8) == ""
    assert device_label(None) == ""


# ---------------------------------------------------------------------------
# B3 — sửa ma trận phân quyền phải kể ra ĐÃ ĐỔI GÌ
# ---------------------------------------------------------------------------
def _quyen(entity, scope="own", **actions):
    from app.core.permissions import ACTIONS
    return SimpleNamespace(entity=entity, scope=scope,
                           **{f"can_{a}": actions.get(a, False) for a in ACTIONS})


def test_ke_lai_phan_chenh_cua_ma_tran_quyen():
    """`PUT /roles/{id}/permissions` ghi đè CẢ ma trận — dòng nhật ký "đã sửa
    vai trò" mà không nói sửa gì thì bằng không có."""
    truoc = [_quyen("purchase_order", read=True), _quyen("employee_sensitive", read=True)]
    sau = [_quyen("purchase_order", "all", read=True, approve=True)]

    cau = describe_permission_change(truoc, sau)

    assert "Cấp thêm purchase_order.approve" in cau
    assert "Thu hồi employee_sensitive.read" in cau
    assert "purchase_order: own -> all" in cau


def test_bam_luu_ma_khong_doi_gi_thi_cau_ke_rong():
    giong_nhau = [_quyen("unit", read=True)]

    assert describe_permission_change(giong_nhau, list(giong_nhau)) == ""


def test_nhom_hanh_dong_suy_tu_ma():
    assert group_of_action("create") == ACTION_GROUP_EDIT
    assert group_of_action("delete") == ACTION_GROUP_DELETE
    assert group_of_action("login_failed") == ACTION_GROUP_AUTH
    #  Mã lạ thì để 0 ("không rõ") chứ không đoán bừa thành "sửa".
    assert group_of_action("chua_khai_bao_gi_ca") == 0


@pytest.mark.parametrize("action", ["set_permissions", "assign_roles", "set_scope",
                                    "reset_password", "activate", "deactivate"])
def test_nhom_phan_quyen_khong_con_rong(action):
    """Nhóm "Phân quyền" từng có ĐÚNG KHÔNG thành viên.

    Bộ lọc trên màn đọc nhật ký vẫn hiện, bấm vào ra bảng trắng, và người xem
    kết luận "chưa ai đụng vào phân quyền" — trong khi sáu hành động nguy hiểm
    nhất của cả hệ đều nằm ở đây.
    """
    assert group_of_action(action) == ACTION_GROUP_PERMISSION


def test_ma_dong_phieu_khong_con_roi_vao_khong_ro():
    """36 dòng `closed` trên prod đang mang nhóm 0 vì thiếu một dòng khai báo."""
    assert group_of_action("closed") == ACTION_GROUP_EDIT


# ---------------------------------------------------------------------------
# `record(...)` đọc ngữ cảnh — 213 lời gọi cũ không sửa dòng nào
# ---------------------------------------------------------------------------
def test_record_tu_dien_ngu_canh_tu_contextvar(db):
    with open_context(SOURCE_API, user_id=7, actor_kind=ACTOR_KIND_USER, ip="27.64.133.181") as ctx:
        record(db, 7, "purchase_order_item", 4412, "update", "Cập nhật dòng",
               doc_code="DMH25090012", parent=("purchase_order", 129))

        dong = db.query(AuditLog).one()
        assert dong.request_id == ctx.request_id
        assert len(dong.request_id) == 16          # QĐ-B: nhị phân, không phải 36 ký tự
        assert dong.ip == "27.64.133.181"
        assert dong.actor_kind == ACTOR_KIND_USER
        assert dong.action_group == ACTION_GROUP_EDIT
        assert (dong.doc_code, dong.parent_entity, dong.parent_id) == \
               ("DMH25090012", "purchase_order", 129)
        #  Lớp máy đọc số này để biết có gì đáng mở ra xem.
        assert ctx.audit_count == 1


def test_record_khong_co_ngu_canh_van_chay(db):
    """Celery, seed, script chạy tay — không có request, và không được nổ."""
    record(db, 0, "unit", 5, "create", "Tạo từ seed")

    dong = db.query(AuditLog).one()
    assert dong.request_id is None
    assert dong.actor_kind == ACTOR_KIND_SYSTEM  # "máy chạy", khác hẳn "không rõ"
    assert dong.ip == ""


def test_ma_request_id_doi_qua_lai_duoc():
    """Cột nhị phân, nhưng API và người dùng vẫn thấy chuỗi 36 ký tự (QĐ-B)."""
    raw = uuid.uuid4().bytes

    text = request_id_text(raw)

    assert len(text) == 36 and text.count("-") == 4
    assert uuid.UUID(text).bytes == raw
    assert request_id_text(None) == ""


# ---------------------------------------------------------------------------
# Middleware chạy thật, trên một app tối giản
# ---------------------------------------------------------------------------
@pytest.fixture
def client(db, monkeypatch):
    """App bốn route + middleware, ghi nhật ký vào chính DB của fixture `db`."""
    Session = sessionmaker(bind=db.get_bind(), autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr("app.core.database.SessionLocal", Session)

    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(HTTPException, http_exception_handler)
    #  Đăng ký y như `main.py`: chính bộ xử lỗi này nhét `exc.errors()` vào thân
    #  trả về, và đó là đường mật khẩu suýt lọt vào nhật ký.
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    @app.post("/api/units")
    async def tao(request: Request):
        #  Đọc lại thân SAU khi middleware đã đọc — bẫy 4 ở §6: đọc xong không
        #  trả lại thì endpoint nhận rỗng, và lỗi đó chỉ lộ ra lúc chạy thật.
        than = await request.json()
        return {"success": True, "message": "Đã tạo", "data": {"id": 12, "echo": than}}

    @app.get("/api/notifications")
    def chuong():
        return {"success": True, "data": []}

    @app.post("/api/auth/refresh")
    def gia_han():
        return {"success": True, "message": "ok"}

    @app.delete("/api/units/{oid}")
    def xoa(oid: int):
        raise HTTPException(403, "Không có quyền: delete unit")

    @app.get("/api/employees")
    def danh_sach_nhan_su(q: str = ""):
        #  Thân trả về mang đúng thứ KHÔNG được chép sang bảng nhật ký.
        return {"success": True, "data": [{"id": 9, "bank_account": "0123456789"}]}

    @app.get("/api/employees/{oid}/sensitive")
    def nhay_cam(oid: int):
        raise HTTPException(403, "Không có quyền: read employee_sensitive")

    class DangNhapIn(BaseModel):
        username: str
        password: str

    @app.post("/api/auth/login")
    def dang_nhap(data: DangNhapIn):
        return {"success": True, "message": "ok", "data": {"id": 1}}

    return TestClient(app)


def _rows(db):
    return db.query(RequestLog).order_by(RequestLog.id).all()


def test_luot_ghi_du_endpoint_input_output(client, db):
    res = client.post("/api/units", json={"name": "Thùng", "password": "bí mật"})

    assert res.status_code == 200
    assert res.json()["data"]["echo"] == {"name": "Thùng", "password": "bí mật"}  # endpoint vẫn đủ thân
    dong = _rows(db)[-1]
    assert (dong.method, dong.path, dong.route) == ("POST", "/api/units", "/api/units")
    assert dong.request_body == {"name": "Thùng", "password": "***"}
    #  Q9: 2xx chỉ giữ `message` + `data.id`, không chép lại cả kết quả.
    assert dong.response_body == {"message": "Đã tạo", "data": {"id": 12}}
    assert dong.duration_ms >= 0 and len(dong.request_id) == 16


def test_luot_bi_chan_403_de_lai_dau(client, db):
    """Thứ hôm nay KHÔNG có ở đâu cả — `record(...)` đứng sau cửa quyền."""
    assert client.delete("/api/units/12").status_code == 403

    dong = _rows(db)[-1]
    assert (dong.http_status, dong.method) == (403, "DELETE")
    #  Mẫu route, không phải đường dẫn thật — để gom "endpoint này ai gọi".
    assert dong.route == "/api/units/{oid}"
    assert dong.response_body["error"]["message"] == "Không có quyền: delete unit"


def test_loi_422_khong_luu_thu_nguoi_dung_vua_go(client, db):
    """Thân 4xx giữ nguyên văn, mà 422 của FastAPI vác theo giá trị thô.

    Che theo TÊN KHÓA không đỡ được ca này: khóa tên `input`, không tên
    `password`. Cùng một dòng nhật ký mà `request_body` che đúng còn
    `response_body` để lộ thì coi như không che.
    """
    res = client.post("/api/auth/login",
                      json={"username": "admin", "password": ["MatKhauThatSuBiLo"]})

    assert res.status_code == 422
    dong = _rows(db)[-1]
    assert dong.request_body == {"username": "admin", "password": "***"}
    #  Đọc cả dòng chứ không soi từng khóa: lọt ở đâu cũng là lọt.
    assert "MatKhauThatSuBiLo" not in json.dumps(dong.response_body, ensure_ascii=False)
    #  Vẫn phải trả lời được "hỏng ở ô nào, vì sao" — bỏ giá trị chứ không bỏ lỗi.
    chi_tiet = dong.response_body["error"]["details"][0]
    assert chi_tiet["loc"] == ["body", "password"]
    assert chi_tiet["type"] == "string_type"
    assert chi_tiet["input"] == {"_omitted": True, "type": "list", "size": 1}
    #  Người gọi vẫn nhận đủ thân thật; chỉ bản LƯU LẠI mới bị lược.
    assert res.json()["error"]["details"][0]["input"] == ["MatKhauThatSuBiLo"]


def test_dau_chuong_khong_ghi_nhung_gia_han_phien_thi_ghi(client, db):
    client.get("/api/notifications")          # máy dội máy, bỏ
    client.post("/api/auth/refresh", json={"refresh_token": "abc"})  # ghi (đảo QĐ-A)

    dong = _rows(db)
    assert len(dong) == 1
    assert (dong[0].method, dong[0].path) == ("POST", "/api/auth/refresh")
    #  Thân yêu cầu có `refresh_token` — che theo hậu tố `_token`, không thì
    #  nhật ký thành nơi cấp lại phiên cho bất kỳ ai đọc được nó.
    assert dong[0].request_body == {"refresh_token": "***"}


def test_get_thuong_van_ghi_nhung_khong_chep_than_tra_ve(client, db):
    """Ghi hết GET, nhưng KHÔNG chép dữ liệu trả về của lượt thành công.

    Ghi cả thân là nhân đôi cả CSDL sang bảng nhật ký — và nhân đôi luôn phần
    nhạy cảm (CCCD, tài khoản ngân hàng) sang một bảng KHÔNG có `employee_sensitive`
    gác cửa.
    """
    res = client.get("/api/employees?q=Nguyen")

    assert res.status_code == 200
    dong = _rows(db)[-1]
    assert (dong.method, dong.path) == ("GET", "/api/employees")
    assert dong.query_string == "q=Nguyen"    # tra được "ai tìm gì" là đủ
    assert dong.response_body is None


def test_get_bi_chan_403_van_giu_ly_do(client, db):
    """Luật cũ quyết định TRƯỚC khi endpoint chạy, nên một cú đọc trộm ăn 403
    cũng không để lại gì — đúng lượt đáng nhìn nhất thì mất."""
    assert client.get("/api/employees/9/sensitive").status_code == 403

    dong = _rows(db)[-1]
    assert dong.http_status == 403
    assert dong.response_body["error"]["message"] == "Không có quyền: read employee_sensitive"


def test_dau_thiet_bi_va_referer_duoc_ghi(client, db):
    client.post("/api/units", json={"name": "Thùng"},
                headers={"user-agent": CHROME_126, "referer": "http://erp/units"})

    dong = _rows(db)[-1]
    assert device_label(dong.device_hash) == "chrome|windows|desktop"
    assert dong.referer == "http://erp/units"


# ---------------------------------------------------------------------------
# Dọn dòng GET quá 90 ngày — điều kiện ĐI KÈM của quyết định ghi hết GET
# ---------------------------------------------------------------------------
def _tao_dong(db, method: str, tuoi_ngay: int):
    db.add(RequestLog(request_id=uuid.uuid4().bytes, method=method, path="/api/x",
                      route="/api/x", http_status=200,
                      created_at=datetime.now() - timedelta(days=tuoi_ngay)))
    db.commit()


@pytest.fixture
def cleanup(db, monkeypatch):
    """Việc dọn chạy trên chính DB của fixture, và mặc định COI NHƯ đã có R2."""
    Session = sessionmaker(bind=db.get_bind(), autoflush=False, autocommit=False, future=True)
    #  Vá THẲNG vào module của việc chạy nền: nó `from ... import SessionLocal`
    #  nên tên đã gắn vào module đó lúc nạp, vá ở `app.core.database` không tới.
    monkeypatch.setattr("app.modules.request_log.tasks.SessionLocal", Session)
    monkeypatch.setattr("app.modules.request_log.tasks.is_remote_storage_ready", lambda: True)
    return cleanup_get_logs_task


def test_don_chi_dung_toi_dong_doc_qua_han(cleanup, db):
    _tao_dong(db, "GET", 200)       # quá hạn -> xóa
    _tao_dong(db, "GET", 10)        # còn hạn -> giữ
    #  Dòng GHI thì KHÔNG BAO GIỜ đụng tới, dù có cũ tới đâu: đó là dấu vết của
    #  một thao tác thật, và 16 tháng là hạn của nó, không phải 90 ngày.
    _tao_dong(db, "DELETE", 400)

    ket_qua = cleanup()

    assert ket_qua["deleted"] == 1
    con_lai = {(d.method, (datetime.now() - d.created_at).days > 90) for d in _rows(db)}
    assert con_lai == {("GET", False), ("DELETE", True)}


def test_khong_co_ban_sao_ngoai_may_thi_khong_xoa_gi(db, monkeypatch):
    """Chốt QUAN TRỌNG NHẤT của việc này, và nó không phải chuyện dung lượng.

    Xóa bản DUY NHẤT của một dòng nhật ký là hủy chứng cứ. Chưa cấu hình R2 thì
    trong máy chỉ có một bản — và một việc chạy nền lúc 3 giờ sáng không phải chỗ
    để chuyện đó xảy ra vì lỡ thiếu một biến môi trường.
    """
    Session = sessionmaker(bind=db.get_bind(), autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr("app.modules.request_log.tasks.SessionLocal", Session)
    monkeypatch.setattr("app.modules.request_log.tasks.is_remote_storage_ready", lambda: False)
    _tao_dong(db, "GET", 200)

    ket_qua = cleanup_get_logs_task()

    assert ket_qua["status"] == "skipped"
    assert len(_rows(db)) == 1


def test_chay_thu_chi_dem_khong_xoa(cleanup, db):
    _tao_dong(db, "GET", 200)

    ket_qua = cleanup(dry_run=True)

    assert (ket_qua["status"], ket_qua["matched"]) == ("dry_run", 1)
    assert len(_rows(db)) == 1
