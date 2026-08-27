"""Cặp tool xuất file của Trợ lý AI: `export_report_file` (.docx) + `export_excel_file` (.xlsx).

Chốt ba điều: (1) thiếu title/sections (hoặc sheets) trả lỗi mềm chứ không nổ exception,
(2) nội dung model điền được chuẩn hóa (dòng bảng lệch cột bị kẹp/đệm về đúng số cột, mục
rỗng bị loại, chuỗi số thành KIỂU SỐ của Excel), (3) đường thành công tạo StoredFile thuộc
về NGƯỜI HỎI + trả khối `file` có download_url — provider gắn khối này lên tool call để
giao diện dựng nút "Tải báo cáo". Storage được monkeypatch: test không đụng R2/đĩa.
"""
from app.modules.assistant.tools.base import ToolContext
from app.modules.assistant.tools.export_tool import (_clean_sections, _clean_sheets, _run,
                                                     _run_excel, render_docx, render_xlsx)


def _ctx(db, user) -> ToolContext:
    return ToolContext(db=db, user=user)


def _args(**over):
    base = {
        "title": "Báo cáo chi tiêu tháng 7",
        "sections": [{
            "heading": "Chi tiêu theo NCC",
            "paragraphs": ["Tổng chi 1,2 tỷ."],
            "table": {"columns": ["NCC", "Tổng chi"],
                      "rows": [["Công ty A", "450tr", "cột thừa"], ["Công ty B"]]},
        }],
    }
    base.update(over)
    return base


def test_thieu_title_hoac_sections_tra_loi_mem(db, seed):
    from app.modules.user.model import User

    ctx = _ctx(db, db.get(User, seed.u_req_id))
    assert "error" in _run(ctx, {"title": "", "sections": [{"heading": "A"}]})
    assert "error" in _run(ctx, {"title": "Báo cáo", "sections": []})
    # Mục chỉ có heading không có nội dung -> không còn mục hợp lệ nào.
    assert "error" in _run(ctx, {"title": "Báo cáo", "sections": [{"heading": "A"}]})


def test_chuan_hoa_bang_lech_cot():
    sections = _clean_sections(_args()["sections"])
    assert len(sections) == 1
    table = sections[0]["table"]
    assert table["columns"] == ["NCC", "Tổng chi"]
    # Dòng thừa cột bị cắt, dòng thiếu cột được đệm rỗng — mọi dòng đúng 2 ô.
    assert table["rows"] == [["Công ty A", "450tr"], ["Công ty B", ""]]


def test_render_docx_ra_file_zip_hop_le():
    data = render_docx({
        "title": "Thử", "subtitle": "", "meta": [("Kỳ", "07/2026")],
        "summary": ["Một dòng"], "sections": _clean_sections(_args()["sections"]),
    })
    assert data[:2] == b"PK"   # .docx là zip — magic bytes PK
    assert len(data) > 1000


def test_duong_thanh_cong_tao_stored_file_cua_nguoi_hoi(db, seed, monkeypatch):
    from app.modules.attachment.model import StoredFile
    from app.modules.user.model import User

    uploaded: dict = {}

    def fake_upload(fileobj, key, content_type=None):
        uploaded["key"] = key
        uploaded["size"] = len(fileobj.read())
        return key

    # Vá tại NƠI DÙNG (export_tool import trong hàm nên vá module storage gốc là đủ).
    import app.core.storage as storage
    monkeypatch.setattr(storage, "upload_fileobj", fake_upload)

    user = db.get(User, seed.u_req_id)
    out = _run(_ctx(db, user), _args(filename="bao cao thang 7"))

    assert out["status"] == "created"
    f = out["file"]
    assert f["filename"].endswith(".docx")
    assert f["download_url"] == f"/api/assistant/files/{f['id']}/download"
    assert uploaded["size"] == f["size"] > 0
    # Key nằm trong thư mục assistant-report — điều kiện endpoint tải kiểm để không
    # thành lối tải chung cho mọi file đính kèm khác của người đó.
    assert "assistant-report" in uploaded["key"]

    sf = db.get(StoredFile, f["id"])
    assert sf is not None
    assert sf.created_by == user.id
    assert sf.file_key == uploaded["key"]


# ── export_excel_file ─────────────────────────────────────────────────────────────────
def _xlsx_args(**over):
    base = {
        "filename": "tien do mua hang thang 8",
        "sheets": [{
            "name": "Tien do [8/2026]",   # chứa ký tự Excel cấm — phải được rửa
            "columns": ["Mã hàng", "Số lượng", "Thành tiền"],
            "rows": [
                ["NLT0025", "5", "40555800", "cột thừa"],
                ["NLT0030", "2.5"],
            ],
        }],
    }
    base.update(over)
    return base


def test_excel_thieu_sheets_tra_loi_mem(db, seed):
    from app.modules.user.model import User

    ctx = _ctx(db, db.get(User, seed.u_req_id))
    assert "error" in _run_excel(ctx, {})
    assert "error" in _run_excel(ctx, {"sheets": []})
    # Sheet không có dòng nào -> không còn sheet hợp lệ.
    assert "error" in _run_excel(ctx, {"sheets": [{"name": "A", "columns": ["X"], "rows": []}]})


def test_excel_chuan_hoa_sheet_va_doi_chuoi_so_thanh_so():
    sheets = _clean_sheets(_xlsx_args()["sheets"])
    assert len(sheets) == 1
    s = sheets[0]
    # Tên sheet được rửa ký tự cấm của Excel ([ ] : * ? / \).
    assert "[" not in s["name"] and "]" not in s["name"]
    # Dòng thừa cột bị cắt, dòng thiếu cột được đệm rỗng; chuỗi số thành KIỂU SỐ
    # để Excel cộng/lọc/pivot được — đây chính là lý do xuất xlsx thay vì docx.
    assert s["rows"] == [["NLT0025", 5, 40555800], ["NLT0030", 2.5, ""]]


def test_excel_ten_sheet_trung_khong_lam_openpyxl_no():
    sheets = _clean_sheets([
        {"name": "Thang 8", "columns": ["A"], "rows": [["1"]]},
        {"name": "Thang 8", "columns": ["A"], "rows": [["2"]]},
    ])
    assert len({s["name"] for s in sheets}) == 2
    render_xlsx(sheets)   # không nổ ValueError vì trùng tên sheet


def test_render_xlsx_ra_file_zip_hop_le():
    data = render_xlsx(_clean_sheets(_xlsx_args()["sheets"]))
    assert data[:2] == b"PK"   # .xlsx là zip — magic bytes PK
    assert len(data) > 1000


def test_excel_duong_thanh_cong_tao_stored_file_xlsx(db, seed, monkeypatch):
    from app.modules.attachment.model import StoredFile
    from app.modules.user.model import User

    uploaded: dict = {}

    def fake_upload(fileobj, key, content_type=None):
        uploaded["key"] = key
        uploaded["mime"] = content_type
        return key

    import app.core.storage as storage
    monkeypatch.setattr(storage, "upload_fileobj", fake_upload)

    user = db.get(User, seed.u_req_id)
    out = _run_excel(_ctx(db, user), _xlsx_args())

    assert out["status"] == "created"
    f = out["file"]
    assert f["filename"].endswith(".xlsx")
    assert f["download_url"] == f"/api/assistant/files/{f['id']}/download"
    # Cùng thư mục assistant-report với file docx -> endpoint tải hiện có phục vụ luôn.
    assert "assistant-report" in uploaded["key"]
    assert uploaded["mime"] == ("application/vnd.openxmlformats-officedocument"
                                ".spreadsheetml.sheet")

    sf = db.get(StoredFile, f["id"])
    assert sf is not None
    assert sf.created_by == user.id
