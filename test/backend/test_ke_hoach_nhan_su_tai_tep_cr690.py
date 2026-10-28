"""duoc-CR-690 — «Tải tệp lên» ở mục Văn bản liên kết của kế hoạch nhân sự: `POST /api/headcount-plans/documents/upload`.

Canh: tạo văn bản KÍN loại CCKHNS có tệp ở phiên bản hiện hành, gắn được vào kế hoạch qua `document_ids`, người khác chỉ có
`headcount_plan.read` (kể cả có `document.read` phạm vi công ty) không đọc được, thiếu quyền → 403, tệp cấm / quá lớn / trích
yếu quá dài → 4xx tiếng Việt, thiếu loại văn bản → 409.
"""
import pytest
from hdld_factory import client_as  # noqa: F401
from headcount_plan_factory import URL, grant_hr, plan_body

from app.modules.attachment.model import FileLink, StoredFile
from app.modules.doc_catalog.model import DocType
from app.modules.document.model import Document
from app.modules.headcount_plan import document_upload_service as svc
from app.modules.headcount_plan.model import HeadcountPlanDocument
from app.seed_data.document_phase1 import HEADCOUNT_BASIS_DOC_TYPE

UP = f"{URL}/documents/upload"
PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


@pytest.fixture
def basis_type(db):
    t = DocType(**HEADCOUNT_BASIS_DOC_TYPE)
    db.add(t)
    db.commit()
    return t


def _editor(world, client_as, key="a1"):
    world.grant(key, "document", "own", actions=("read",))
    return grant_hr(world, client_as, key=key)


def _upload(client, name="quyet-dinh.pdf", data=PDF, **form):
    return client.post(UP, files={"file": (name, data, "application/pdf")}, data=form)


def test_tai_tep_tao_van_ban_kin_co_tep_roi_gan_vao_ke_hoach(db, world, client_as, basis_type):
    editor = _editor(world, client_as)
    resp = _upload(editor)
    assert resp.status_code == 201, resp.text
    item = resp.json()["data"]
    assert item["can_read"] is True and item["code"]                       # có số/ký hiệu ngay (mã bất biến cấp lúc tạo)
    assert item["title"] == "Căn cứ kế hoạch nhân sự – quyet-dinh.pdf"
    doc = db.get(Document, item["document_id"])
    assert doc.doc_type_id == basis_type.id and doc.created_by == world.actor("a1").user.id
    link = db.query(FileLink).filter(FileLink.entity == "document_version", FileLink.entity_id == doc.current_version_id).one()
    assert db.get(StoredFile, link.file_id).filename == "quyet-dinh.pdf"
    # gắn vào kế hoạch như văn bản có sẵn
    plan = editor.post(URL, json=plan_body(world, document_ids=[doc.id]))
    assert plan.status_code == 201, plan.text
    assert plan.json()["data"]["documents"] == [item]
    assert db.query(HeadcountPlanDocument).count() == 1


def test_trich_yeu_tuy_chon_va_toi_da_500(db, world, client_as, basis_type):
    editor = _editor(world, client_as)
    assert _upload(editor, title="  Tờ trình ngân sách 2027 ").json()["data"]["title"] == "Tờ trình ngân sách 2027"
    too_long = _upload(editor, title="x" * 501)
    assert too_long.status_code == 422 and "500" in too_long.text
    assert db.query(Document).count() == 1                                   # lần lỗi không để lại văn bản


def test_nguoi_khac_co_headcount_read_khong_doc_duoc_van_ban_kin(db, world, client_as, basis_type):
    editor = _editor(world, client_as)
    doc_id = _upload(editor).json()["data"]["document_id"]
    plan = editor.post(URL, json=plan_body(world, document_ids=[doc_id])).json()["data"]
    # a2: xem kế hoạch + đọc MỌI văn bản của công ty — vẫn không mở được văn bản cá nhân
    world.grant("a2", "document", "company", actions=("read",))
    viewer = grant_hr(world, client_as, key="a2", pay=False)
    docs = viewer.get(f"{URL}/{plan['id']}").json()["data"]["documents"]
    assert docs == [{"document_id": doc_id, "can_read": False}]
    # ... và không tự gắn được văn bản đó vào kế hoạch của mình
    assert viewer.post(URL, json=plan_body(world, period_no=2, document_ids=[doc_id])).status_code == 403


def test_thieu_quyen_ghi_ke_hoach_403_va_thieu_document_read_403(db, world, client_as, basis_type):
    world.grant("a1", "headcount_plan", "all", actions=("read",))
    world.grant("a1", "document", "own", actions=("read",))
    assert _upload(client_as(world.actor("a1"))).status_code == 403          # chỉ đọc kế hoạch
    world.grant("a2", "headcount_plan", "all", actions=("create",))          # có «tạo» là đủ (dùng lúc lập mới)
    no_doc = _upload(client_as(world.actor("a2")))
    assert no_doc.status_code == 403 and "Văn bản" in no_doc.text
    assert db.query(Document).count() == 0


def test_tep_cam_hoac_qua_lon_bi_chan_tieng_viet(db, world, client_as, basis_type, monkeypatch):
    editor = _editor(world, client_as)
    bad = _upload(editor, name="chay.exe", data=b"MZ\x90\x00")
    assert 400 <= bad.status_code < 500 and bad.json()["error"]["message"]
    monkeypatch.setattr(svc, "policy", lambda entity: ("document", {"pdf"}, 1))   # trần 1MB cho bài kiểm
    big = _upload(editor, data=PDF + b"0" * (1024 * 1024 + 10))
    assert 400 <= big.status_code < 500 and "MB" in big.json()["error"]["message"]
    assert db.query(Document).count() == 0


def test_thieu_loai_van_ban_409(db, world, client_as):
    resp = _upload(_editor(world, client_as))
    assert resp.status_code == 409 and "Căn cứ kế hoạch nhân sự" in resp.json()["error"]["message"]
