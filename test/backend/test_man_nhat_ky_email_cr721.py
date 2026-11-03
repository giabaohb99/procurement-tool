"""bao-CR-721 — màn Nhật ký email (`/api/email-logs`, chỉ đọc, quyền `audit.read`).

Chỗ dễ lủng: không có quyền phải 403 (không lộ địa chỉ thư); lọc người nhận không phân biệt hoa thường; lọc nhiều sự kiện
một lượt; khoảng ngày lấy trọn ngày cuối; phân trang mới nhất trước; nhãn sự kiện lấy từ danh mục mẫu email, sự kiện lạ
vẫn trả được; chi tiết trả đủ câu lỗi; thẻ đếm 7 ngày không đếm thư cũ hơn.
"""
from datetime import datetime, timedelta

from app.core.logging_policy import SKIP_PATH_PREFIXES
from app.modules.notification.model import EmailLog
from hdld_factory import client_as  # noqa: F401

NOW = datetime(2026, 11, 3, 9, 0)


def _log(db, **kw):
    base = dict(event="dx_submitted", to_email="a@dego.vn", subject="YCĐX chờ duyệt", status="sent",
                from_email="erp@dego.vn", created_at=NOW)
    base.update(kw)
    row = EmailLog(**base)
    db.add(row)
    return row


def _seed(db):
    rows = [
        _log(db, id=1, to_email="An.Nguyen@dego.vn", status="sent", created_at=NOW - timedelta(days=1)),
        _log(db, id=2, to_email="binh@dego.vn", status="failed", error="SMTP 550: mailbox unavailable, lý do dài " * 20,
             event="dd_completed", created_at=NOW - timedelta(days=2)),
        _log(db, id=3, to_email="an.nguyen@dego.vn", status="pending", event="thu_thu_nghiem",
             created_at=NOW - timedelta(days=3)),
        _log(db, id=4, to_email="cu@dego.vn", status="failed", error="cũ", created_at=NOW - timedelta(days=30)),
    ]
    db.commit()
    return rows


def _reader(world):
    world.grant("a1", "audit", "all", actions=("read",))
    return world.actor("a1")


def test_khong_co_quyen_audit_read_thi_403(world, client_as):  # noqa: F811
    world.grant("a1", "setting", "all", actions=("read",))        # quyền khác không đủ
    c = client_as(world.actor("a1"))
    for path in ("/api/email-logs", "/api/email-logs/meta", "/api/email-logs/stats", "/api/email-logs/1"):
        assert c.get(path).status_code == 403, path


def test_danh_sach_moi_nhat_truoc_va_phan_trang(world, client_as):  # noqa: F811
    _seed(world.db)
    c = client_as(_reader(world))
    data = c.get("/api/email-logs?page=1&page_size=2").json()["data"]
    assert data["total"] == 4 and data["page"] == 1 and data["page_size"] == 2
    #  Mới nhất trước = id giảm dần (id tăng theo thứ tự ghi).
    assert [r["id"] for r in data["items"]] == [4, 3]
    page2 = c.get("/api/email-logs?page=2&page_size=2").json()["data"]["items"]
    assert [r["id"] for r in page2] == [2, 1]
    row = data["items"][1]
    assert row["event_label"] == "thu_thu_nghiem" and row["status_label"] == "Đang chờ"   # sự kiện lạ trả nguyên mã


def test_loc_nguoi_nhan_su_kien_trang_thai_khoang_ngay(world, client_as):  # noqa: F811
    _seed(world.db)
    c = client_as(_reader(world))
    ids = lambda res: [r["id"] for r in res.json()["data"]["items"]]  # noqa: E731
    assert ids(c.get("/api/email-logs?q=AN.NGUYEN")) == [3, 1]                       # không phân biệt hoa thường
    assert ids(c.get("/api/email-logs?event=dd_completed&event=thu_thu_nghiem")) == [3, 2]
    assert ids(c.get("/api/email-logs?status=failed")) == [4, 2]
    day = (NOW - timedelta(days=2)).strftime("%Y-%m-%d")
    assert ids(c.get(f"/api/email-logs?from_date={day}&to_date={day}")) == [2]       # trọn ngày cuối
    assert c.get("/api/email-logs?from_date=03-11-2026").status_code == 400


def test_chi_tiet_tra_du_cau_loi_va_nhan_su_kien(world, client_as):  # noqa: F811
    rows = _seed(world.db)
    c = client_as(_reader(world))
    d = c.get(f"/api/email-logs/{rows[1].id}").json()["data"]
    assert d["error"] == rows[1].error and len(d["error"]) > 255
    assert d["event_label"] == "Hoàn thành → Người tạo" and d["status_label"] == "Lỗi" and d["from_email"] == "erp@dego.vn"
    assert c.get("/api/email-logs/999999").status_code == 404


def test_meta_va_the_dem_7_ngay(world, client_as):  # noqa: F811
    _seed(world.db)
    c = client_as(_reader(world))
    meta = c.get("/api/email-logs/meta").json()["data"]
    codes = [e["code"] for e in meta["events"]]
    assert "dx_submitted" in codes and "thu_thu_nghiem" in codes                     # danh mục + sự kiện lạ đã ghi
    assert {"code": "dx_submitted", "label": "Gửi duyệt → Người duyệt"} in meta["events"]
    assert [s["code"] for s in meta["statuses"]] == ["failed", "sent", "pending", "disabled"]
    stats = c.get("/api/email-logs/stats").json()["data"]
    assert stats["days"] == 7 and stats["failed"] == 1 and stats["total"] == 3            # dòng 30 ngày không tính


def test_duong_doc_nhat_ky_khong_ghi_request_log():
    assert "/api/email-logs" in SKIP_PATH_PREFIXES
