"""bao-CR-312 P1 — lớp MÁY của nhật ký: `tab_request_log` + ngữ cảnh cho audit.

Bốn thứ được kiểm ở đây, đều là thứ hỏng trong im lặng nếu sai:

1. **Lượt bị chặn phải để lại dấu.** Hôm nay một cú `DELETE` ăn 403 không nằm ở
   đâu cả, vì `record(...)` đứng SAU cửa quyền nên chưa kịp chạy.
2. **QĐ-A** — gia hạn phiên thành công không được đẻ dòng. 126 lượt/ngày, gần
   nửa số lời gọi không phải GET; ghi hết là 46.000 dòng rác mỗi năm làm loãng
   đúng cái màn dựng ra để đọc.
3. **Che mật khẩu.** Ghi nhầm MỘT lần là chuỗi băm nằm trong nhật ký vĩnh viễn,
   và không ai đi rà lại một bảng chỉ-thêm vài trăm nghìn dòng.
4. **QĐ-B** — `request_id` là 16 byte nhị phân ở cả hai bảng, và là **cùng một
   giá trị**, vì đó là sợi dây duy nhất nối lớp máy với lớp kể chuyện.

Tài liệu: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §4.1, §4.2, §4.5.
"""
import uuid

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.audit import record
from app.core.logging_codes import (ACTION_GROUP_AUTH, ACTION_GROUP_DELETE, ACTION_GROUP_EDIT,
                                    ACTOR_KIND_SYSTEM, ACTOR_KIND_USER, SOURCE_API,
                                    group_of_action)
from app.core.logging_policy import mask_payload, should_log_request, should_skip_by_result
from app.core.request_context import open_context, request_id_text
from app.core.request_middleware import RequestContextMiddleware
from app.main import http_exception_handler
from app.modules.audit.model import AuditLog
from app.modules.request_log.model import RequestLog


# ---------------------------------------------------------------------------
# Luật "ghi hay không" — hàm thuần, kiểm trực tiếp
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("method,path,ghi", [
    ("POST", "/api/units", True),
    ("PATCH", "/api/units/3", True),
    ("DELETE", "/api/units/3", True),
    #  Giao diện gọi `/api/notifications` liên tục để đếm chuông — ghi hết thì
    #  bảng phình hàng chục nghìn dòng/ngày toàn rác.
    ("GET", "/api/notifications", False),
    #  Hai loại "xem" CÓ giá trị truy vết (Q6).
    ("GET", "/api/reports/export", True),
    ("GET", "/api/purchase-orders/12/print", True),
    ("GET", "/api/attachments/88/view", True),
    #  NT-5: đường nhật ký không tự ghi chính nó, kẻo mỗi lần mở màn lại đẻ
    #  thêm dòng để đọc.
    ("POST", "/api/system-logs/search", False),
    ("GET", "/api/health", False),
])
def test_luot_nao_duoc_ghi(method, path, ghi):
    assert should_log_request(method, path) is ghi


def test_qd_a_gia_han_phien_thanh_cong_thi_bo():
    assert should_skip_by_result("/api/auth/refresh", 200) is True
    #  Thất bại thì ghi đủ — đó mới là dấu hiệu của BM-003 (token bị cắp).
    assert should_skip_by_result("/api/auth/refresh", 401) is False
    assert should_skip_by_result("/api/auth/login", 200) is False


def test_che_theo_ten_khoa_di_sau_vao_trong():
    goc = {"username": "admin", "password": "bí mật",
           "items": [{"token": "abc", "qty": 3}], "nested": {"new_password": "x"}}

    che = mask_payload(goc)

    assert che == {"username": "admin", "password": "***",
                   "items": [{"token": "***", "qty": 3}], "nested": {"new_password": "***"}}
    #  Chép chứ không sửa tại chỗ: endpoint còn đọc `goc` sau middleware.
    assert goc["password"] == "bí mật"


def test_nhom_hanh_dong_suy_tu_ma():
    assert group_of_action("create") == ACTION_GROUP_EDIT
    assert group_of_action("delete") == ACTION_GROUP_DELETE
    assert group_of_action("login_failed") == ACTION_GROUP_AUTH
    #  Mã lạ thì để 0 ("không rõ") chứ không đoán bừa thành "sửa".
    assert group_of_action("chua_khai_bao_gi_ca") == 0


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


def test_get_thuong_khong_ghi_va_qd_a_khong_ghi(client, db):
    client.get("/api/notifications")
    client.post("/api/auth/refresh", json={"refresh_token": "abc"})

    assert _rows(db) == []
