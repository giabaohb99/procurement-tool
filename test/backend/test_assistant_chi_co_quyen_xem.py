"""Tài khoản CHỈ CÓ QUYỀN XEM hỏi trợ lý — hai luật khách chốt 15/09/2026.

1. **Xin TẠO / SỬA / XÓA trong khung chat thì bị CHẶN**, câu hỏi viết khéo tới đâu cũng
   vậy: quyền nằm ở backend, không nằm ở câu chữ. Model không có đường ghi nào ngoài
   allowlist tool, và mọi tool ghi đều tự đòi đúng `entity.create` / `entity.write`.
2. **"Tóm tắt phiếu X" cũng phải đi qua phân quyền.** Trợ lý chỉ tóm tắt được thứ TOOL
   trả về, mà tool lọc bằng `apply_scope`; phiếu ngoài phạm vi trả "không tìm thấy" nên
   không còn gì để tóm tắt. Đây là chỗ dễ tưởng an toàn mà không phải: câu *"tóm tắt"*
   nghe như thao tác đọc vô hại, nhưng nếu tool lấy bản ghi bằng `db.get` trần thì chỉ
   cần đọc đúng mã phiếu là moi được nội dung của phòng khác.

Bộ này đứng NGOÀI các tệp test theo từng tool: nó kiểm phần BẮC CẦU giữa chúng. Mục 3 là
hàng rào cho tool viết SAU — đúng bài học B-07: thiếu khai thì test ĐỎ, chứ không im lặng
lọt. `04-bao-mat-va-van-hanh.md` §8.4 từng ghi nợ đúng hàng rào này.
"""
import pytest

from app.modules.assistant import tools as T
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.user.model import User


def _ycmh(db, seed, code, created_by, purpose="Mua giấy A4"):
    pr = PurchaseRequest(code=code, company_id=seed.company_id, department_id=seed.dept_id,
                         purpose=purpose, need_date="2026-09-01", note="", status="draft",
                         created_by=created_by, updated_by=created_by)
    db.add(pr)
    db.commit()
    return pr


def _hoi(db, seed, name, args):
    """Chạy một tool đúng như lượt chat của người dùng — dưới danh tính của họ."""
    return T.run_tool(db, db.get(User, seed.u_req_id), name, args)


# ── 1. Chỉ có quyền XEM mà xin GHI ──────────────────────────────────────────────────────

def test_chi_co_quyen_xem_thi_khong_de_xuat_sua_phieu_duoc(db, seed, cap_quyen):
    """Đọc được phiếu KHÔNG kéo theo sửa được nó.

    `purchase_request.read` là tất cả những gì tài khoản này có. Xin sửa mục đích mua
    hàng — thứ chính họ vừa đọc xong — vẫn phải `denied`.
    """
    cap_quyen(seed.u_req_id, "purchase_request", scope="all", read=True)
    _ycmh(db, seed, "YCMH-XEM-1", created_by=seed.u_req_id)

    out = _hoi(db, seed, "propose_document_update",
               {"entity": "purchase_request", "code": "YCMH-XEM-1",
                "changes": {"purpose": "Mua giấy A5"}})

    assert out.get("denied") is True, "chỉ có quyền đọc mà đề xuất sửa được là lủng"
    #  Phải NÓI rõ là thiếu quyền, không trả rỗng: rỗng thì model diễn giải thành
    #  "không có gì để sửa" và người dùng tưởng phiếu đã đúng.
    assert "quyền" in out.get("reason", "").lower()
    #  Và phiếu phải NGUYÊN VẸN dưới cơ sở dữ liệu.
    assert db.query(PurchaseRequest).filter_by(code="YCMH-XEM-1").one().purpose == "Mua giấy A4"


def test_chi_co_quyen_xem_thi_khong_soan_nhap_tao_phieu_duoc(db, seed, cap_quyen):
    """Soạn nháp cũng đòi `create`, dù bản thân tool không ghi gì xuống bảng.

    Chặn ở đây là cố ý: bản nháp mở sẵn form kèm dữ liệu là một nửa bước tạo phiếu, mà
    người không có quyền tạo thì nửa bước đó chỉ dẫn tới một nút bấm sẽ 403.
    """
    cap_quyen(seed.u_req_id, "purchase_request", scope="all", read=True)

    out = _hoi(db, seed, "draft_purchase_request",
               {"purpose": "Mua giấy", "lines": [{"description": "Giấy A4", "quantity": 10}]})

    assert out.get("denied") is True


def test_chi_co_quyen_xem_thi_khong_tao_phieu_ho_tro_duoc(db, seed, cap_quyen):
    """`ticket_create` cũng chỉ trả BẢN NHÁP, nhưng vẫn phải đòi `ticket.create`.

    ⚠️ Đừng đọc tên tool thành "tạo phiếu": **không tool nào ghi dữ liệu nghiệp vụ** (rà
    cả lớp `tools/`, chỉ `export_tool` ghi một dòng `StoredFile` cho tệp người dùng vừa
    xuất). Đường ghi DUY NHẤT của cả phân hệ là endpoint `/api/assistant/confirm-update`,
    và nó chỉ chạy khi NGƯỜI bấm nút Xác nhận.
    """
    cap_quyen(seed.u_req_id, "ticket", scope="own", read=True)

    out = _hoi(db, seed, "ticket_create", {"subject": "Xin cấp quyền", "body": "Nội dung"})

    assert out.get("denied") is True


def test_khong_ton_tai_tool_nao_xoa_du_lieu(db):
    """Không có đường XÓA nào cho trợ lý — chặn bằng cách KHÔNG CÓ tool, chắc hơn gác quyền.

    Ai thêm tool xóa thì bài này đỏ và phải giải trình: xóa là thao tác không lùi được,
    mà lời người dùng gõ cho model thì luôn mơ hồ ("bỏ cái phiếu kia đi" là hủy, là xóa
    dòng, hay là xóa cả phiếu?).
    """
    ten = {d.name for d in T.tool_defs()}
    xau = [n for n in ten if any(k in n for k in ("delete", "remove", "destroy", "xoa"))]
    assert xau == [], f"xuất hiện tool xóa dữ liệu: {xau}"


# ── 2. Tóm tắt phải đi qua phân quyền ───────────────────────────────────────────────────

def test_tom_tat_phieu_ngoai_pham_vi_thi_khong_co_gi_de_tom_tat(db, seed, cap_quyen):
    """Kịch bản khách nêu: *"tóm tắt phiếu ABC giùm"* với phiếu KHÔNG thuộc phạm vi mình.

    Phạm vi `own` = phiếu do chính mình lập. Phiếu của người khác phải trả "không tìm
    thấy" — model không nhận được chữ nào của phiếu đó nên không thể tóm tắt, cũng không
    thể lỡ miệng. Vế đối chứng ngay dưới: phiếu CỦA MÌNH thì tóm tắt được, nếu không thì
    bài này xanh vì lý do sai (tool hỏng chứ không phải quyền chặt).
    """
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True)
    _ycmh(db, seed, "YCMH-CUA-TOI", created_by=seed.u_req_id, purpose="Mua giấy của tôi")
    _ycmh(db, seed, "YCMH-NGUOI-KHAC", created_by=seed.u_nstm_id, purpose="Bí mật phòng khác")

    ngoai = _hoi(db, seed, "procurement_doc_read",
                 {"entity": "purchase_request", "code": "YCMH-NGUOI-KHAC"})
    assert "error" in ngoai, "phiếu ngoài phạm vi mà đọc được là lộ dữ liệu"
    #  Không một mẩu nội dung nào của phiếu kia được rò ra, kể cả trong câu báo lỗi.
    assert "Bí mật phòng khác" not in str(ngoai)

    cua_minh = _hoi(db, seed, "procurement_doc_read",
                    {"entity": "purchase_request", "code": "YCMH-CUA-TOI"})
    assert "error" not in cua_minh, "phiếu của chính mình phải đọc được"
    assert "Mua giấy của tôi" in str(cua_minh)


def test_khong_co_khoa_quyen_cua_phan_he_thi_khong_doc_duoc_gi(db, seed, cap_quyen):
    """Thiếu hẳn `purchase_request.read` thì chặn ngay ở trục VAI TRÒ, trước cả phạm vi.

    Hai trục khác nhau và phải chặn độc lập: không có khóa thì `denied`; có khóa nhưng
    ngoài phạm vi thì "không tìm thấy". Gộp một là mất một lớp.
    """
    cap_quyen(seed.u_req_id, "ticket", scope="own", read=True)   # quyền của phân hệ KHÁC
    _ycmh(db, seed, "YCMH-KHONG-KHOA", created_by=seed.u_req_id)

    out = _hoi(db, seed, "procurement_doc_read",
               {"entity": "purchase_request", "code": "YCMH-KHONG-KHOA"})

    assert out.get("denied") is True


# ── 3. Hàng rào cho tool viết SAU ───────────────────────────────────────────────────────

#  Mọi tool có thể DẪN TỚI ghi dữ liệu: khóa quyền nó phải đòi + bộ tham số TỐI THIỂU để
#  lượt gọi đi qua được vòng kiểm đối số. Thêm tool ghi mà quên khai ở đây là test đỏ —
#  đó là mục đích của bảng này, không phải để tra cứu.
#
#  ⚠️ Phải truyền tham số hợp lệ, đừng gọi `{}` cho gọn: tool kiểm đối số TRƯỚC rồi mới
#  kiểm quyền (đúng thứ tự — lỗi gõ sai của người dùng không nên hiện thành "thiếu
#  quyền"), nên `{}` trả về lỗi đối số và bài kiểm thành XANH GIẢ: nó không hề chạm tới
#  cái chốt quyền mà nó tưởng đang canh.
TOOL_GHI = {
    "draft_survey_request": ("survey_request", "create", {"purpose": "Khảo sát giá"}),
    "draft_purchase_request": ("purchase_request", "create", {"purpose": "Mua giấy"}),
    "draft_leave_request": ("leave_request", "create", {"from_date": "2026-09-20"}),
    "draft_payment_request": ("payment_request", "create", {"supplier_name": "NCC A"}),
    "ticket_create": ("ticket", "create", {"subject": "Xin hỗ trợ", "body": "Nội dung"}),
    "propose_document_update": ("purchase_request", "write",
                                {"entity": "purchase_request", "code": "YCMH-BAT-KY",
                                 "changes": {"purpose": "Đổi mục đích"}}),
}

#  Cách nhận diện "tool có mùi ghi" từ TÊN. Cố ý thô: thà bắt nhầm một tool đọc rồi khai
#  vào bảng trên, còn hơn bỏ lọt một tool ghi.
_MUI_GHI = ("draft_", "_create", "create_", "propose_", "update_", "_update", "confirm_")


def test_moi_tool_co_mui_ghi_deu_phai_khai_o_bang_tren(db):
    """Thêm `draft_xyz` mà quên khai là ĐỎ ngay — không đợi tới lúc khách hỏi."""
    ten = {d.name for d in T.tool_defs()}
    nghi_ngo = {n for n in ten if any(k in n for k in _MUI_GHI)}
    thieu = sorted(nghi_ngo - set(TOOL_GHI))
    assert thieu == [], (
        f"tool có mùi ghi nhưng chưa khai ở TOOL_GHI: {thieu}. Khai vào rồi bổ sung một ca "
        "'thiếu quyền thì denied' — đừng sửa `_MUI_GHI` cho hết đỏ.")
    #  Chiều ngược: khai thừa một tool đã gỡ thì bảng thành sai lệch, cũng phải đỏ.
    du = sorted(set(TOOL_GHI) - ten)
    assert du == [], f"TOOL_GHI còn khai tool không tồn tại: {du}"


@pytest.mark.parametrize("ten_tool", sorted(TOOL_GHI))
def test_moi_tool_ghi_deu_tu_choi_khi_thieu_quyen(db, seed, cap_quyen, ten_tool):
    """Chạy TỪNG tool ghi dưới tài khoản chỉ có quyền ĐỌC — không tool nào được lọt.

    Tài khoản được cấp `read` trên ĐÚNG entity mà tool đó đụng tới: nếu chốt là
    `ctx.can(entity, "create"/"write")` thì vẫn `denied`; còn nếu ai đó lỡ viết thành
    `ctx.can(entity)` trơn (mặc định action = read) thì bài này bắt được ngay.
    """
    entity, action, args = TOOL_GHI[ten_tool]
    cap_quyen(seed.u_req_id, entity, scope="all", read=True)

    out = _hoi(db, seed, ten_tool, args)

    assert out.get("denied") is True, (
        f"`{ten_tool}` không chặn tài khoản chỉ có quyền đọc trên `{entity}` — "
        f"phải gọi ctx.can('{entity}', '{action}') trước khi làm gì khác. "
        f"Kết quả thật: {out}")
