"""Tool văn bản của Trợ lý AI: `approval_flow_lookup` + `my_documents` +
`document_search` + `document_read`.

Chốt các điều: (1) tra loại văn bản chịu được cách nói đời thường ("đơn nghỉ phép" trong
khi danh mục ghi "Giấy nghỉ phép"), (2) chưa khai luồng / bộ máy tắt thì nói thẳng cơ chế
duyệt một bước chứ không im lặng, (3) có luồng thì trả từng bước kèm TÊN người duyệt cụ
thể cho chính người hỏi, (4) danh sách "văn bản áp dụng lên tôi" đi đúng phép tính phạm
vi + quyền đọc của văn thư — không rộng hơn thứ người hỏi mở được, (5) tìm kiếm đi đúng
luật lọc của màn danh sách (theo từng từ, đúng phạm vi), (6) đọc nội dung gác quyền trên
CHÍNH văn bản và trả cùng một câu cho "không tồn tại" lẫn "không có quyền".
"""
from app.modules.assistant.tools import document_tool
from app.modules.assistant.tools.base import ToolContext
from app.modules.assistant.tools.document_tool import (_run_document_read,
                                                       _run_document_search,
                                                       _run_flow_lookup,
                                                       _run_my_documents)

ACTOR = 1


def _ctx(db, user, profile=None) -> ToolContext:
    return ToolContext(db=db, user=user, _profile=profile)


def _profile(employee_id=0, dept_id=0, company_id=0, scope="own"):
    """Hồ sơ quyền tối thiểu, đúng hình dạng `get_perm_profile` trả về — dựng thẳng vì
    seed của conftest không gán vai trò nào cho user."""
    perms = {a: a == "read" for a in ("read", "create", "write", "delete",
                                      "approve", "cancel", "print", "export")}
    perms["scope"] = scope
    return {
        "grants": [{"role_id": 1, "perms": {"document": perms},
                    "scope": {"inc": {}, "exc": {}}}],
        "company_id": company_id, "dept_id": dept_id, "dept_name": "",
        "employee_id": employee_id, "emp_code": "", "emp_name": "",
    }


def _them_loai(db, code, name, needs_approval=True, is_personal=False):
    from app.modules.doc_catalog.model import DocType

    row = DocType(code=code, name=name, group_code="A", needs_approval=needs_approval,
                  is_personal=is_personal, is_active=True,
                  created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _bat_bo_may(db):
    from app.modules.approval.flow_model import ApprovalSwitch

    db.add(ApprovalSwitch(entity="document", is_enabled=True,
                          created_by=ACTOR, updated_by=ACTOR))
    db.commit()


def _luong_van_ban(db, **kw):
    from app.modules.approval.flow_model import ApprovalFlow

    flow = ApprovalFlow(entity="document", code=kw.pop("code", "VB-01"),
                        name=kw.pop("name", "Luồng văn bản"), is_active=True,
                        created_by=ACTOR, updated_by=ACTOR, **kw)
    db.add(flow)
    db.commit()
    db.refresh(flow)
    return flow


def _buoc(db, flow, seq, **kw):
    from app.modules.approval.flow_model import ApprovalNode

    node = ApprovalNode(flow_id=flow.id, seq=seq, name=kw.pop("name", f"Bước {seq}"),
                        created_by=ACTOR, updated_by=ACTOR, **kw)
    db.add(node)
    db.commit()
    return node


def test_khong_tim_thay_loai_van_ban_bao_loi_mem(db, seed):
    from app.modules.user.model import User

    _them_loai(db, "QD", "Quyết định")
    out = _run_flow_lookup(_ctx(db, db.get(User, seed.u_req_id)),
                           {"doc_type": "giấy phép lái xe"})
    assert "error" in out
    assert "Quyết định" in out["available_types"]   # gợi ý để model hỏi lại đúng hướng


def test_don_nghi_phep_chua_khai_luong_tra_duyet_mot_buoc(db, seed):
    """Người dùng nói "đơn nghỉ phép", danh mục ghi "Giấy nghỉ phép" — phải khớp được
    (bỏ dần từ đầu câu). Chưa bật bộ máy luồng thì nói thẳng cơ chế duyệt một bước."""
    from app.modules.user.model import User

    _them_loai(db, "GNP", "Giấy nghỉ phép", is_personal=True)
    out = _run_flow_lookup(_ctx(db, db.get(User, seed.u_req_id)),
                           {"doc_type": "đơn nghỉ phép"})
    assert out["status"] == "one_step"
    assert out["doc_type"]["code"] == "GNP"
    assert out["engine_enabled"] is False
    assert "MỘT BƯỚC" in out["message"]


def test_loai_khong_can_duyet_noi_thang(db, seed):
    from app.modules.user.model import User

    _them_loai(db, "TB", "Thông báo", needs_approval=False)
    out = _run_flow_lookup(_ctx(db, db.get(User, seed.u_req_id)), {"doc_type": "thông báo"})
    assert out["status"] == "no_approval"


def test_co_luong_tra_buoc_va_ten_nguoi_duyet_cua_toi(db, seed):
    """Câu "người phê duyệt nghỉ phép CỦA TÔI là ai": bước «Trưởng bộ phận người nộp»
    phải giải ra đúng trưởng phòng của người hỏi, không chỉ trả nhãn quy tắc."""
    from app.modules.approval.flow_model import APPROVER_DEPT_HEAD, APPROVER_EMPLOYEE
    from app.modules.department.model import Department
    from app.modules.user.model import User

    _them_loai(db, "GNP", "Giấy nghỉ phép", is_personal=True)
    _bat_bo_may(db)
    db.get(Department, seed.dept_id).manager_id = seed.emp_tp_id
    flow = _luong_van_ban(db)
    _buoc(db, flow, 1, approver_kind=APPROVER_DEPT_HEAD)
    _buoc(db, flow, 2, approver_kind=APPROVER_EMPLOYEE, approver_ref=str(seed.emp_nstm_id))
    db.commit()

    out = _run_flow_lookup(_ctx(db, db.get(User, seed.u_req_id)), {"doc_type": "nghỉ phép"})
    assert out["status"] == "flow"
    assert out["total"] == 2
    assert out["steps"][0]["approvers_for_me"] == ["Trưởng Phòng"]
    assert "NSTM Chính" in out["steps"][1]["approver_rule"]      # tên dựng ngay trong quy tắc
    assert out["steps"][1]["approvers_for_me"] == ["NSTM Chính"]


def test_luong_chung_tu_gac_quyen_cau_hinh(db, seed, monkeypatch):
    """Tra luồng theo `entity` là xem CẤU HÌNH luồng -> cần quyền approval_flow; còn tra
    theo loại văn bản là thông tin người nộp nào cũng thấy khi gửi duyệt -> không gác."""
    from app.modules.user.model import User

    _them_loai(db, "GNP", "Giấy nghỉ phép", is_personal=True)
    monkeypatch.setattr(ToolContext, "can", lambda self, entity, action="read": False)
    ctx = _ctx(db, db.get(User, seed.u_req_id))

    assert _run_flow_lookup(ctx, {"entity": "purchase_request"}).get("denied") is True
    assert _run_flow_lookup(ctx, {"doc_type": "nghỉ phép"})["status"] == "one_step"


def test_van_ban_ap_dung_cho_toi_dung_pham_vi(db, seed):
    """Văn bản còn sống của pháp nhân người hỏi (không khai phạm vi) thì áp cho họ;
    văn bản của pháp nhân khác và bản nháp thì không. Có lọc keyword."""
    from app.modules.company.model import Company
    from app.modules.document.model import (STATUS_DRAFT, STATUS_EFFECTIVE,
                                            Document)
    from app.modules.user.model import User

    loai = _them_loai(db, "QC", "Quy chế / Quy trình")
    cty_khac = Company(name="Cty Khác", code="CT02", is_active=True)
    db.add(cty_khac)
    db.flush()
    #  Văn bản nội bộ (origin=1) bị CHECK ép có đủ loại + pháp nhân + người chịu
    #  trách nhiệm nội dung — thiếu owner là không chèn nổi bản ghi.
    db.add_all([
        Document(title="Quy chế bảo mật", doc_type_id=loai.id, company_id=seed.company_id,
                 owner_employee_id=seed.emp_tp_id, status=STATUS_EFFECTIVE,
                 issue_number="01/QC", created_by=ACTOR, updated_by=ACTOR),
        Document(title="Quy chế công ty khác", doc_type_id=loai.id, company_id=cty_khac.id,
                 owner_employee_id=seed.emp_tp_id, status=STATUS_EFFECTIVE,
                 created_by=ACTOR, updated_by=ACTOR),
        Document(title="Quy chế nháp", doc_type_id=loai.id, company_id=seed.company_id,
                 owner_employee_id=seed.emp_tp_id, status=STATUS_DRAFT,
                 created_by=ACTOR, updated_by=ACTOR),
    ])
    db.commit()

    ctx = _ctx(db, db.get(User, seed.u_req_id))
    out = _run_my_documents(ctx, {})
    assert out["total"] == 1
    assert out["items"][0]["title"] == "Quy chế bảo mật"
    assert out["items"][0]["status"] == "Có hiệu lực"
    assert out["items"][0]["doc_type"] == "Quy chế / Quy trình"

    assert _run_my_documents(ctx, {"keyword": "không có chữ này"})["total"] == 0


def test_tai_khoan_chua_gan_nhan_su_bao_loi_mem(db, seed):
    from app.modules.user.model import User

    user = User(email="botroi", password_hash="x", is_active=True)
    db.add(user)
    db.commit()
    out = _run_my_documents(_ctx(db, user), {})
    assert "error" in out
    assert "total" not in out


# ── document_search + document_read ─────────────────────────────────────────────────────

def _van_ban(db, loai, title, company_id, owner_id, so_hieu="", content="", **kw):
    from app.modules.document.model import STATUS_EFFECTIVE, Document
    from app.modules.document.version_model import DocumentVersion

    doc = Document(title=title, doc_type_id=loai.id, company_id=company_id,
                   owner_employee_id=owner_id, issue_number=so_hieu,
                   status=kw.pop("status", STATUS_EFFECTIVE),
                   created_by=ACTOR, updated_by=ACTOR, **kw)
    db.add(doc)
    db.flush()
    if content:
        ver = DocumentVersion(document_id=doc.id, content_html=content,
                              created_by=ACTOR, updated_by=ACTOR)
        db.add(ver)
        db.flush()
        doc.current_version_id = ver.id
    db.commit()
    db.refresh(doc)
    return doc


def test_tim_van_ban_thieu_quyen_bi_tu_choi(db, seed, monkeypatch):
    from app.modules.user.model import User

    monkeypatch.setattr(ToolContext, "can", lambda self, entity, action="read": False)
    out = _run_document_search(_ctx(db, db.get(User, seed.u_req_id)), {"keyword": "quy chế"})
    assert out.get("denied") is True
    assert "total" not in out


def test_tim_van_ban_theo_tung_tu_va_dung_pham_vi(db, seed, monkeypatch):
    """Gõ "quy định công tác phí" phải ra "Quy định VỀ CHẾ ĐỘ công tác phí" (khớp theo
    từng từ, không bắt thuộc nguyên văn) — nhưng KHÔNG ra văn bản của pháp nhân khác."""
    from app.modules.company.model import Company
    from app.modules.user.model import User

    loai = _them_loai(db, "QD", "Quy định")
    cty_khac = Company(name="Cty Khác", code="CT02", is_active=True)
    db.add(cty_khac)
    db.flush()
    _van_ban(db, loai, "Quy định về chế độ công tác phí", seed.company_id,
             seed.emp_tp_id, so_hieu="05/QD")
    _van_ban(db, loai, "Quy định công tác phí bên kia", cty_khac.id, seed.emp_tp_id)

    monkeypatch.setattr(ToolContext, "can", lambda self, entity, action="read": True)
    ctx = _ctx(db, db.get(User, seed.u_req_id),
               _profile(employee_id=seed.emp_req_id, company_id=seed.company_id,
                        scope="company"))

    out = _run_document_search(ctx, {"keyword": "quy định công tác phí"})
    assert out["total"] == 1
    assert out["items"][0]["title"] == "Quy định về chế độ công tác phí"
    assert out["items"][0]["document_id"] > 0
    assert "document_read" in out["reminder"]     # chỉ đường sang bước đọc nội dung

    assert "error" in _run_document_search(ctx, {})   # thiếu từ khóa thì hỏi lại


def test_doc_van_ban_theo_so_hieu_va_boc_html(db, seed):
    """Chủ văn bản đọc theo số hiệu: nội dung phải là chữ thuần (bảng thành ` | `),
    không còn thẻ HTML, kèm nhãn trạng thái tiếng Việt."""
    from app.modules.user.model import User

    loai = _them_loai(db, "QC", "Quy chế / Quy trình")
    _van_ban(db, loai, "Quy chế công tác phí", seed.company_id, seed.emp_req_id,
             so_hieu="01/QC-DEGO",
             content="<h2>Điều 1</h2><p>Mức chi tối đa</p>"
                     "<table><tr><td>Hà Nội</td><td>500.000đ/ngày</td></tr></table>")

    ctx = _ctx(db, db.get(User, seed.u_req_id), _profile(employee_id=seed.emp_req_id))
    out = _run_document_read(ctx, {"issue_number": "01/QC-DEGO"})

    assert out["document"]["title"] == "Quy chế công tác phí"
    assert out["document"]["status"] == "Có hiệu lực"
    assert out["total_parts"] == 1
    assert "Điều 1" in out["content"]
    assert "Hà Nội | 500.000đ/ngày" in out["content"]
    assert "<" not in out["content"]


def test_doc_van_ban_khong_quyen_nhu_khong_ton_tai(db, seed):
    """Người ngoài đọc văn bản không phải của mình phải nhận ĐÚNG câu của id không tồn
    tại — như màn chi tiết trả 404 chứ không 403, kẻo lộ 'có văn bản này'. Dùng bản
    NHÁP vì văn bản Có hiệu lực không khai phạm vi thì cả pháp nhân đọc được (nguồn
    'áp dụng lên tôi' của access_service.can)."""
    from app.modules.document.model import STATUS_DRAFT
    from app.modules.user.model import User

    loai = _them_loai(db, "QC", "Quy chế / Quy trình")
    doc = _van_ban(db, loai, "Quy chế lương", seed.company_id, seed.emp_req_id,
                   content="<p>Mật</p>", status=STATUS_DRAFT)

    ctx = _ctx(db, db.get(User, seed.u_nstm_id), _profile(employee_id=seed.emp_nstm_id))
    khong_quyen = _run_document_read(ctx, {"document_id": doc.id})
    khong_co = _run_document_read(ctx, {"document_id": 999999})
    assert khong_quyen["error"] == khong_co["error"]
    assert "content" not in khong_quyen


def test_noi_dung_dai_chia_phan_va_nhieu_ban_khop(db, seed, monkeypatch):
    from app.modules.user.model import User

    loai = _them_loai(db, "QC", "Quy chế / Quy trình")
    doc = _van_ban(db, loai, "Quy chế dài", seed.company_id, seed.emp_req_id,
                   so_hieu="02/QC", content="<p>" + "A" * 70 + "B" * 30 + "</p>")
    ctx = _ctx(db, db.get(User, seed.u_req_id), _profile(employee_id=seed.emp_req_id))

    monkeypatch.setattr(document_tool, "MAX_CONTENT_CHARS", 70)
    phan_1 = _run_document_read(ctx, {"document_id": doc.id})
    assert phan_1["total_parts"] == 2
    assert phan_1["content"] == "A" * 70
    assert "part=2" in phan_1["note"]           # dặn model đọc tiếp, đừng suy đoán
    phan_2 = _run_document_read(ctx, {"document_id": doc.id, "part": 2})
    assert phan_2["content"] == "B" * 30
    assert "note" not in phan_2
    #  part vượt trần thì kẹp về phần cuối chứ không trả rỗng.
    assert _run_document_read(ctx, {"document_id": doc.id, "part": 99})["part"] == 2

    #  Hai bản cùng số hiệu (bản gốc + bản riêng) -> bắt chọn đích danh, kèm danh sách.
    _van_ban(db, loai, "Quy chế dài (bản riêng)", seed.company_id, seed.emp_req_id,
             so_hieu="02/QC")
    nhieu = _run_document_read(ctx, {"issue_number": "02/QC"})
    assert "error" in nhieu
    assert len(nhieu["matches"]) == 2
