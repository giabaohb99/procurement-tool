"""CR-215 — "Đánh dấu làm xong" lưu SERVER theo tài khoản, ba nơi cùng ẩn.

Trước đây tab Việc cần làm ghi localStorage: chuông (/api/alerts) và dashboard
không biết gì, đổi máy hiện lại. Nay khóa việc (`task_key`) lưu ở
`tab_user_task_dismiss`; bài này chốt ba mệnh đề:

1. Service dismiss/restore: ghi - trùng không nhân đôi - khôi phục từng phần/toàn bộ.
2. `alert.build()` bỏ qua key đã ẩn CỦA ĐÚNG user; worker (user=None) và user
   khác vẫn thấy đủ. Key kèm mức nên ẩn "warn" không ẩn lây "danger".
3. `build_my_tasks()` gắn key ổn định + cờ `dismissed`, và gom việc "Chờ tôi
   duyệt" từ bộ máy duyệt (task_service.my_tasks) vào cùng danh sách.
"""
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.modules.alert import controller as alert_ct
from app.modules.contract.model import Contract
from app.modules.dashboard import controller as dash_ct
from app.modules.dashboard.service import dismiss_keys, load_dismissed_keys, restore_keys
from app.modules.payable.model import Payable
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest

USER_ID = 7
NGUOI_KHAC_ID = 8
CTY = 101
QUA_HAN = "2000-01-01"

_ACTIONS = ("read", "create", "write", "delete", "approve", "cancel", "print", "export")
_ENTITIES = ("contract", "payable", "purchase_order", "purchase_request", "survey_request")


def _user(uid=USER_ID, employee_id=0):
    return SimpleNamespace(id=uid, employee_id=employee_id)


def _profile(scope="all"):
    perms = {e: {**{a: True for a in _ACTIONS}, "scope": scope} for e in _ENTITIES}
    return {
        "grants": [{"role_id": 1, "perms": perms, "scope": {"inc": {}, "exc": {}}}],
        "perms_union": perms,
        "company_id": CTY, "dept_id": 0, "dept_name": "",
        "employee_id": 0, "emp_code": "", "emp_name": "",
    }


@pytest.fixture
def du_lieu(db):
    """Một ĐMH có dòng giao trễ + một công nợ quá hạn + một YCMH chờ duyệt."""
    po = PurchaseOrder(code="PO-1", company_id=CTY, status="ordered")
    db.add(po)
    db.flush()
    item = POItem(po_id=po.id, product_code="SP-1", product_name="Hàng 1")
    db.add(item)
    db.flush()
    giao = PODelivery(po_id=po.id, po_item_id=item.id, received_qty=0, promised_date=QUA_HAN)
    db.add(giao)
    no = Payable(company_id=CTY, supplier_code="NCC-1", supplier_name="NCC 1",
                 po_code="PO-1", due_date=QUA_HAN, status="unpaid", remaining=5000)
    db.add(no)
    pr = PurchaseRequest(code="YC-1", company_id=CTY, status="submitted", purpose="Mua đồ")
    db.add(pr)
    db.commit()
    return SimpleNamespace(db=db, giao=giao, no=no, pr=pr)


# ── 1. Service ──────────────────────────────────────────────────────────────────

def test_dismiss_restore_service(db):
    user = _user()
    assert dismiss_keys(db, user, ["pr:1", "pr:1", "  payable:2:danger  ", ""]) == 2
    # Gửi lại key đã có -> không ghi thêm dòng nào
    assert dismiss_keys(db, user, ["pr:1"]) == 0
    assert load_dismissed_keys(db, user) == {"pr:1", "payable:2:danger"}
    # Người khác không dính gì
    assert load_dismissed_keys(db, _user(NGUOI_KHAC_ID)) == set()
    # Khôi phục từng key rồi toàn bộ
    assert restore_keys(db, user, ["pr:1"]) == 1
    assert load_dismissed_keys(db, user) == {"payable:2:danger"}
    assert restore_keys(db, user, [], restore_all=True) == 1
    assert load_dismissed_keys(db, user) == set()


# ── 2. Chuông cảnh báo ──────────────────────────────────────────────────────────

def _build_alerts(db, monkeypatch, user):
    monkeypatch.setattr(alert_ct, "user_has_permission", lambda *a, **k: True)
    monkeypatch.setattr(alert_ct, "get_perm_profile", lambda _db, _u: _profile())
    return alert_ct.build(db, user)


def test_chuong_an_key_da_danh_dau(du_lieu, monkeypatch):
    db, user = du_lieu.db, _user()
    truoc = _build_alerts(db, monkeypatch, user)
    assert {x["key"] for x in truoc["items"]} == {
        f"delivery:{du_lieu.giao.id}:danger", f"payable:{du_lieu.no.id}:danger"}

    dismiss_keys(db, user, [f"delivery:{du_lieu.giao.id}:danger"])
    sau = _build_alerts(db, monkeypatch, user)
    assert {x["key"] for x in sau["items"]} == {f"payable:{du_lieu.no.id}:danger"}
    assert sau["total"] == 1 and sau["danger"] == 1

    # Người khác và worker (user=None) vẫn thấy đủ
    khac = _build_alerts(db, monkeypatch, _user(NGUOI_KHAC_ID))
    assert khac["total"] == 2
    assert alert_ct.build(db)["total"] == 2


def test_an_muc_warn_khong_an_lay_danger(du_lieu, monkeypatch):
    """Key kèm mức: đã ẩn `...:warn` mà cảnh báo leo thang thành danger thì NỔI LẠI."""
    db, user = du_lieu.db, _user()
    dismiss_keys(db, user, [f"delivery:{du_lieu.giao.id}:warn"])
    out = _build_alerts(db, monkeypatch, user)
    assert f"delivery:{du_lieu.giao.id}:danger" in {x["key"] for x in out["items"]}


# ── 3. Việc cần làm ─────────────────────────────────────────────────────────────

def test_build_my_tasks_gan_key_va_co_dismissed(du_lieu):
    db, user = du_lieu.db, _user()
    tasks = dash_ct.build_my_tasks(db, user, _profile())
    keys = {t["key"] for t in tasks}
    assert f"pr:{du_lieu.pr.id}" in keys
    assert f"delivery:{du_lieu.giao.id}:danger" in keys
    assert f"payable:{du_lieu.no.id}:danger" in keys
    assert all(t["dismissed"] is False for t in tasks)

    dismiss_keys(db, user, [f"pr:{du_lieu.pr.id}"])
    tasks = dash_ct.build_my_tasks(db, user, _profile())
    trang_thai = {t["key"]: t["dismissed"] for t in tasks}
    assert trang_thai[f"pr:{du_lieu.pr.id}"] is True
    assert trang_thai[f"delivery:{du_lieu.giao.id}:danger"] is False


def test_build_my_tasks_gom_viec_cho_toi_duyet(db, monkeypatch):
    """Việc từ bộ máy duyệt (trước ở nút riêng trên topbar) nay nằm chung danh sách."""
    monkeypatch.setattr(
        "app.modules.approval.task_service.my_tasks",
        lambda _db, _emp, entity="": [{
            "id": 55, "entity_code": "VB-001", "entity_title": "Quyết định 9",
            "started_by_name": "Nguyễn Văn A", "due_at": datetime(2026, 8, 30),
        }])
    tasks = dash_ct.build_my_tasks(db, _user(employee_id=3), _profile())
    sign = [t for t in tasks if t["type"] == "sign"]
    assert len(sign) == 1
    assert sign[0]["key"] == "sign:55"
    assert sign[0]["code"] == "VB-001"
    assert sign[0]["link"] == "/document/pending-approval"
    assert sign[0]["date"] == "2026-08-30"

    # Không gắn nhân sự (employee_id=0) -> không gọi bộ máy duyệt
    tasks0 = dash_ct.build_my_tasks(db, _user(employee_id=0), _profile())
    assert not [t for t in tasks0 if t["type"] == "sign"]


def test_tab_la_tap_cha_cua_chuong(du_lieu, monkeypatch):
    """MỌI key chuông phát ra phải có mặt trong Việc cần làm — kể cả mức `warn`
    và hợp đồng. Thiếu loại nào thì "Đánh dấu làm hết" quét không sạch chuông,
    người dùng không có chỗ đánh dấu phần còn lại (lỗi "bấm hết vẫn còn 8")."""
    db, user = du_lieu.db, _user()
    # Thêm đủ các dạng chuông biết mà tab từng bỏ sót: nợ sắp đến hạn, lô hàng
    # sắp tới hạn giao, hợp đồng hết hạn + sắp hết hạn.
    sap_toi = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    db.add(Payable(company_id=CTY, supplier_code="NCC-2", supplier_name="NCC 2",
                   po_code="PO-2", due_date=sap_toi, status="unpaid", remaining=100))
    giao_gan = PODelivery(po_id=du_lieu.giao.po_id, po_item_id=du_lieu.giao.po_item_id,
                          received_qty=0, promised_date=sap_toi)
    db.add(giao_gan)
    db.add(Contract(code="HD-1", party_code="NCC-1", party_name="NCC 1",
                    company_id=CTY, end_date=QUA_HAN, status="active"))
    db.add(Contract(code="HD-2", party_code="NCC-2", party_name="NCC 2",
                    company_id=CTY, end_date=sap_toi, status="active"))
    db.commit()

    alert_keys = {x["key"] for x in _build_alerts(db, monkeypatch, user)["items"]}
    task_keys = {t["key"] for t in dash_ct.build_my_tasks(db, user, _profile())}
    assert alert_keys, "fixture phải sinh được cảnh báo"
    assert alert_keys <= task_keys, f"Chuông có key ngoài tab: {alert_keys - task_keys}"
    # Cả hai mức của công nợ + hợp đồng đều phải hiện diện
    assert {f"payable:{du_lieu.no.id}:danger", f"delivery:{giao_gan.id}:warn"} <= task_keys
    assert any(k.startswith("contract:") and k.endswith(":danger") for k in task_keys)
    assert any(k.startswith("contract:") and k.endswith(":warn") for k in task_keys)


def test_dismiss_all_server_tu_gom_key(db, monkeypatch):
    """`all: true` — SERVER tự gom key từ build_my_tasks, bỏ qua việc đã ẩn.

    FE từng gửi key theo danh sách đã nạp: tổng việc vượt trần page_size là
    sót key ngoài trang -> "9 việc mà danh sách trống"."""
    monkeypatch.setattr("app.core.auth.get_perm_profile", lambda _db, _u: _profile())
    monkeypatch.setattr(dash_ct, "build_my_tasks", lambda _db, _u, _prof: [
        {"key": "pr:1", "dismissed": False},
        {"key": "payable:2:danger", "dismissed": False},
        {"key": "po:3", "dismissed": True},
    ])
    user = _user()
    dash_ct.dismiss_tasks({"all": True}, db=db, user=user)
    assert load_dismissed_keys(db, user) == {"pr:1", "payable:2:danger"}
