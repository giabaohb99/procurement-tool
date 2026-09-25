"""Trục ĐỌC của Trợ lý AI: tool nào cũng phải lọc phạm vi trước khi đưa dữ liệu cho model.

Đây là nửa còn lại của hàng rào bắt đầu ở `test_assistant_chi_co_quyen_xem.py` (trục GHI),
và là nửa **nguy hiểm hơn**: một tool tóm tắt viết vội bằng `db.get(Model, id)` là moi được
chứng từ của phòng khác **qua miệng trợ lý**, không để lại dấu gì trên màn hình — không
403, không log đỏ, không ai biết.

⚠️ **Vì sao KHÔNG quét mã tĩnh.** Cách rẻ là đọc `inspect.getsource(handler)` rồi tìm chữ
`apply_scope`. Đã thử: sai nhiều tới mức vô dụng. `procurement_doc_read` gọi
`ctx.can(entity)` với entity là BIẾN, và lọc phạm vi nằm dưới helper `_fetch_scoped` ở tệp
khác — quét nguồn của riêng handler thì thấy "không có gì", kết luận ngược hẳn sự thật.
Nên bộ này kiểm **hành vi**: dựng hai chủ sở hữu rồi hỏi xem dữ liệu người kia có lọt ra
không.

Hai tầng:
- **Tầng 1 — phân loại bắt buộc.** Mọi tool phải nằm trong đúng một bảng dưới đây. Thêm
  tool mà quên khai là ĐỎ (bài học B-07), không im lặng lọt.
- **Tầng 2 — ca rò rỉ thật.** Với tool đọc chứng từ mà dựng được dữ liệu rẻ, chạy dưới
  phạm vi `own` và khẳng định chuỗi bí mật của người khác KHÔNG xuất hiện.
"""
import pytest

from app.core.config import settings
from app.modules.assistant import tools as T
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.ticket.model import Ticket
from app.modules.user.model import User

from test_assistant_chi_co_quyen_xem import TOOL_GHI

#  HAI mồi, không phải một — chuỗi hiếm để `in`/`not in` khỏi khớp nhầm chữ nghiệp vụ.
#
#  ⚠️ Tách đôi vì hai thứ này có luật khác nhau. Tool trả về MÃ phiếu mà người dùng vừa
#  gõ vào là chuyện bình thường (câu "không tìm thấy 'YCMH-xxx'" phải nhắc lại mã, không
#  thì người đọc chẳng biết hệ thống đang nói về phiếu nào) — nên `MOI_MA` chỉ dùng cho
#  ca DANH SÁCH, nơi mã người khác lọt ra là rò thật. Còn `MOI_NOI_DUNG` thì tuyệt đối
#  không được xuất hiện ở bất kỳ đâu: người hỏi chưa từng gõ nó, thấy nó nghĩa là dữ liệu
#  phiếu đã đi ra.
MOI_MA = "ZZMAPHONGKHAC"
MOI_NOI_DUNG = "ZZNOIDUNGPHONGKHAC"


# ── Tầng 1: phân loại bắt buộc ──────────────────────────────────────────────────────────

#  Đọc BẢN GHI NGHIỆP VỤ gắn chủ sở hữu → BẮT BUỘC lọc phạm vi (`apply_scope` /
#  `get_scoped` / chốt per-record của phân hệ).
TOOL_CHUNG_TU = {
    "procurement_doc_read": "purchase_request",
    "my_procurement_requests": "purchase_request",
    "my_requests_status": "purchase_request",
    "pending_procurement_approvals": "purchase_request",
    "recent_purchase_orders": "purchase_order",
    "my_approval_tasks": "approval_flow",
    "document_read": "document",
    "document_search": "document",
    "my_documents": "document",
    "payable_lookup": "payable",
    "payment_request_read": "payment_request",
    "employee_lookup": "employee",
    "my_leave_summary": "leave_request",
    "my_tickets": "ticket",
}

#  DANH MỤC / THỐNG KÊ dùng chung toàn công ty: không có cột chủ sở hữu để lọc, phạm vi
#  của chúng là "có khóa entity hay không" (+ cắt cột NCC khi thiếu `supplier.read`).
TOOL_DANH_MUC = {
    "product_search": "danh mục hàng hóa",
    "supplier_search": "danh mục NCC",
    "contract_list_by_expiry": "hợp đồng NCC — dùng chung",
    "contract_count_by_status": "đếm hợp đồng — dùng chung",
    "supplier_contracts": "hợp đồng của một NCC",
    "product_best_price": "giá tốt nhất — tổng hợp lịch sử mua",
    "product_purchase_history": "lịch sử mua một mã hàng",
    "suppliers_for_product": "NCC từng bán một mã hàng",
    "recent_purchases": "lần mua gần nhất toàn hệ",
    "top_suppliers_by_purchase": "xếp hạng NCC theo giá trị mua",
    "purchase_report": "báo cáo tổng quan mua hàng",
    "analytics_query": "thống kê mua hàng tùy biến",
    #  bao-CR-470 — dữ liệu thị trường BÊN NGOÀI (tờ khai hải quan), `customs_price` khai PUBLIC:
    #  không có chủ sở hữu để lọc, phạm vi là "có khóa customs_price.read hay không".
    "customs_price_stats": "giá hải quan theo kỳ — dữ liệu thị trường bên ngoài",
    "customs_buy_timing": "thời điểm mua theo giá hải quan — như trên",
    #  bao-CR-481 — cùng nguồn, cùng khóa customs_price.read.
    "customs_market": "nhà nhập khẩu / đối tác / xuất xứ theo tờ khai — như trên",
    "customs_legal_check": "danh mục pháp lý hóa chất + biểu thuế — danh mục dùng chung",
}

#  CỐ Ý không lọc phạm vi — mỗi dòng phải nói được lý do, nếu không thì nó là lỗ hổng
#  đang được hợp thức hóa bằng một dòng khai báo.
TOOL_KHONG_PHAM_VI = {
    "approval_flow_lookup": "trả CẤU HÌNH luồng duyệt, không phải dữ liệu phiếu của ai",
    "search_docs": ("HDSD + FAQ, chủ đích mở cho mọi người đăng nhập. ⚠️ Index thêm nguồn "
                    "KÍN vào cùng bộ sưu tập là rò ngay — xem `01-…md` §6.5"),
    "export_report_file": "xuất từ dữ liệu ĐÃ lọc ở lượt trước; tệp gác bằng quyền SỞ HỮU",
    "export_excel_file": "như trên",
    #  ai-CR-064: dữ liệu KHÔNG nằm trong ERP — lịch và Drive Google của CHÍNH người hỏi, đọc bằng token
    #  của người đó (tab_agent_google_link); không có bản ghi ERP nào để lọc phạm vi.
    "my_calendar_events": "lịch Google của chính người hỏi, bằng token của họ",
    "create_calendar_event": "tạo sự kiện trên lịch Google của chính người hỏi",
    "drive_search": "tìm trên Drive của chính người hỏi, bằng token của họ",
    "drive_read": "đọc một tệp Drive của chính người hỏi",
}


def test_moi_tool_deu_phai_duoc_phan_loai(db, monkeypatch):
    """Thêm tool mà quên khai là ĐỎ — đó là mục đích của bốn bảng trên.

    Người viết tool mới buộc phải trả lời: nó đọc bản ghi gắn chủ (lọc phạm vi), đọc danh
    mục dùng chung, hay cố ý không lọc (và vì sao)? Không có ô "chưa nghĩ tới".

    ⚠️ Phải BẬT `AI_RAG_ENABLED`: `search_docs` chỉ vào allowlist khi cờ đó bật, mà mặc
    định test tắt. Không bật thì bài này bỏ lọt đúng tool loại B — tool duy nhất đọc kho
    vector, tức chỗ đang KHÔNG có lọc quyền (§6.5).
    """
    monkeypatch.setattr(settings, "AI_RAG_ENABLED", True)
    thuc_te = {d.name for d in T.tool_defs()}
    assert len(thuc_te) == 45, f"số tool đổi ({len(thuc_te)}) — cập nhật tài liệu 02 và 04 kèm theo"
    da_khai = set(TOOL_GHI) | set(TOOL_CHUNG_TU) | set(TOOL_DANH_MUC) | set(TOOL_KHONG_PHAM_VI)

    thieu = sorted(thuc_te - da_khai)
    assert thieu == [], (
        f"tool chưa được phân loại: {thieu}. Khai vào ĐÚNG một bảng ở "
        "`test_assistant_pham_vi_doc.py`, và nếu là tool đọc chứng từ thì bổ sung ca rò rỉ.")

    du = sorted(da_khai - thuc_te)
    assert du == [], f"bảng còn khai tool không tồn tại: {du}"

    #  Một tool không được nằm ở hai bảng — phân loại nhập nhằng là phân loại vô nghĩa.
    tong = len(TOOL_GHI) + len(TOOL_CHUNG_TU) + len(TOOL_DANH_MUC) + len(TOOL_KHONG_PHAM_VI)
    assert tong == len(da_khai), "có tool bị khai ở nhiều hơn một bảng"


#  Tool đọc chứng từ đã có ca rò rỉ Ở TỆP KHÁC — bộ này không viết lại, chỉ trỏ tới.
#
#  ⚠️ Sổ nợ bản đầu khai 8 tool "chưa có ca", rà lại thì 5 trong số đó ĐÃ được canh sẵn ở
#  tệp test riêng của từng tool. Sổ nợ ghi sai theo hướng BI QUAN cũng hại như ghi sai
#  theo hướng lạc quan: nó đẩy người sau đi viết trùng, và làm mờ đúng chỗ thật sự hở.
CA_O_TEP_KHAC = {
    "document_search": "test_assistant_document_tool::test_tim_van_ban_theo_tung_tu_va_dung_pham_vi",
    "my_documents": "test_assistant_document_tool::test_van_ban_ap_dung_cho_toi_dung_pham_vi",
    "payment_request_read": "test_assistant_payable_tool::test_doc_yctt_ngoai_pham_vi_bao_khong_thay",
    "my_leave_summary": "test_assistant_leave_tool::test_only_own_requests_not_ones_filed_for_others",
    "my_approval_tasks": "test_assistant_approval_tool::test_cho_toi_duyet_khong_thay_viec_cua_nguoi_khac",
    "my_requests_status": "test_assistant_approval_tool::test_phieu_cua_toi_khong_lan_phieu_nguoi_khac_va_loc_only_open",
}

#  Tool đọc chứng từ CHƯA có ca rò rỉ ở BẤT KỲ đâu. Để trống là mục tiêu; còn dòng nào thì
#  dòng đó là lỗ đang mở, đếm được.
CHUA_CO_CA_HANH_VI: dict[str, str] = {}


def test_ca_o_tep_khac_phai_ton_tai_that(db):
    """Con trỏ sang tệp khác phải kiểm được, không thì nó mục mà không ai biết.

    Đổi tên một bài test bên kia là bài này đỏ — thay vì để lại một dòng khai báo trỏ vào
    hư không, thứ đọc lên y như đã có bảo đảm.
    """
    import importlib

    for tool, tro_toi in CA_O_TEP_KHAC.items():
        ten_tep, ten_bai = tro_toi.split("::")
        mod = importlib.import_module(ten_tep)
        assert hasattr(mod, ten_bai), (
            f"`{tool}` khai có ca ở `{tro_toi}` nhưng bài đó không tồn tại — "
            "hoặc sửa con trỏ, hoặc viết ca ngay tại đây.")


#  Tool đọc chứng từ có ca rò rỉ NGAY TRONG tệp này.
CA_TAI_DAY = {
    "procurement_doc_read", "my_procurement_requests", "pending_procurement_approvals",
    "employee_lookup", "my_tickets", "document_read", "payable_lookup",
    "recent_purchase_orders",
}


def test_moi_tool_chung_tu_deu_co_ca_ro_ri(db):
    """Ba bảng phải phủ KÍN `TOOL_CHUNG_TU`, không chồng nhau, không sót.

    Đây là chỗ đếm: thêm một tool đọc chứng từ mà chưa viết ca rò rỉ thì nó rơi ra ngoài
    cả ba bảng và bài này đỏ, kèm đúng tên tool còn thiếu.
    """
    phu = CA_TAI_DAY | set(CA_O_TEP_KHAC) | set(CHUA_CO_CA_HANH_VI)

    sot = sorted(set(TOOL_CHUNG_TU) - phu)
    assert sot == [], f"tool đọc chứng từ chưa có ca rò rỉ ở đâu cả: {sot}"

    lac = sorted(phu - set(TOOL_CHUNG_TU))
    assert lac == [], f"khai ca rò rỉ cho tool không phải tool chứng từ: {lac}"

    assert len(phu) == len(CA_TAI_DAY) + len(CA_O_TEP_KHAC) + len(CHUA_CO_CA_HANH_VI), \
        "một tool bị khai ở nhiều hơn một bảng"


# ── Tầng 2: ca rò rỉ thật ───────────────────────────────────────────────────────────────

def _hai_ycmh(db, seed, status="draft"):
    """Một phiếu của mình, một phiếu của người khác mang chuỗi bí mật."""
    db.add_all([
        PurchaseRequest(code="YCMH-CUA-TOI", company_id=seed.company_id,
                        department_id=seed.dept_id, purpose="Mua giấy của tôi",
                        need_date="2026-09-01", status=status,
                        created_by=seed.u_req_id, updated_by=seed.u_req_id),
        #  Mồi đặt ở CẢ mã phiếu lẫn mục đích: mỗi tool trả một hình dạng khác nhau,
        #  và tool nào không in `purpose` (vd hộp chờ duyệt) thì mồi nằm ở `purpose`
        #  không bao giờ lộ ra — ca kiểm xanh dù dữ liệu đã rò qua cột `code`.
        PurchaseRequest(code=f"YCMH-{MOI_MA}", company_id=seed.company_id,
                        department_id=seed.dept_id, purpose=f"Mua {MOI_NOI_DUNG}",
                        need_date="2026-09-01", status=status,
                        created_by=seed.u_nstm_id, updated_by=seed.u_nstm_id),
    ])
    db.commit()


def _hoi(db, seed, name, args=None):
    return T.run_tool(db, db.get(User, seed.u_req_id), name, args or {})


#  Ghi lại kết quả KIỂM NGƯỢC (15/09/2026) để người sau khỏi đoán. Vô hiệu hóa
#  `apply_scope` trong `procurement_doc_tool` + `employee_tool` (biến nó thành hàm trả
#  thẳng query) thì **3 ca đỏ**: `procurement_doc_read`, `pending_procurement_approvals`,
#  `employee_lookup`.
#
#  Hai ca VẪN XANH — và đó KHÔNG phải test yếu: `my_procurement_requests` lọc thêm bằng
#  `_filter_mine` (created_by) và `my_tickets` tự lọc theo `created_by`/`requester_id`.
#  Chúng có lớp thứ hai độc lập với `apply_scope`, nên gỡ một lớp chưa rò. Đừng "sửa" hai
#  ca đó cho đỏ — thứ chúng khẳng định là HÀNH VI (không rò), không phải cách cài đặt.
#
#  ⚠️ LUẬT CỦA MỌI CA DƯỚI ĐÂY: phải có ĐỐI CHỨNG DƯƠNG.
#
#  "Không thấy dữ liệu người khác" một mình là khẳng định RỖNG — nó xanh y hệt khi tool
#  chạy đúng và khi tool không trả gì cả. Bản đầu của bộ này dính đúng bẫy đó: ca
#  `employee_lookup` tìm chữ "Nguyễn" trong khi seed không có ai tên vậy, nên nó xanh vì
#  kết quả RỖNG — gỡ sạch `apply_scope` nó vẫn xanh. Mỗi ca vì thế khẳng định CẢ HAI vế:
#  thấy đúng phần của mình (tool có chạy thật), và không thấy phần của người khác.

@pytest.mark.parametrize("ten_tool,args,phai_thay", [
    ("procurement_doc_read", {"entity": "purchase_request", "code": "YCMH-CUA-TOI"},
     "Mua giấy của tôi"),
    ("my_procurement_requests", {"entity": "purchase_request"}, "YCMH-CUA-TOI"),
])
def test_tool_doc_ycmh_thay_phan_minh_va_khong_thay_phan_nguoi_khac(
        db, seed, cap_quyen, ten_tool, args, phai_thay):
    """Phạm vi `own` = phiếu do chính mình lập."""
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True)
    _hai_ycmh(db, seed)

    out = str(_hoi(db, seed, ten_tool, args))

    assert phai_thay in out, f"`{ten_tool}` không trả cả phần của chính mình — ca này vô nghĩa"
    assert MOI_MA not in out, f"`{ten_tool}` làm lộ MÃ phiếu ngoài phạm vi"
    assert MOI_NOI_DUNG not in out, f"`{ten_tool}` làm lộ NỘI DUNG phiếu ngoài phạm vi"


def test_procurement_doc_read_tu_choi_phieu_ngoai_pham_vi(db, seed, cap_quyen):
    """Đọc thẳng bằng MÃ phiếu của người khác — vector "tóm tắt phiếu X" điển hình."""
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True)
    _hai_ycmh(db, seed)

    out = _hoi(db, seed, "procurement_doc_read",
               {"entity": "purchase_request", "code": f"YCMH-{MOI_MA}"})

    assert "error" in out
    #  Câu báo lỗi ĐƯỢC PHÉP nhắc lại mã người dùng vừa gõ; thứ tuyệt đối không được
    #  rò là NỘI DUNG phiếu — thấy nó nghĩa là tool đã đọc bản ghi rồi mới từ chối.
    assert MOI_NOI_DUNG not in str(out)


def test_pending_procurement_approvals_khong_lam_lo_phieu_ngoai_pham_vi(db, seed, cap_quyen):
    """Hộp "chờ tôi duyệt" đi bằng `approve`, nhưng vẫn phải kẹp trong phạm vi dữ liệu.

    Tách riêng vì tool này đòi action `approve` và chỉ lấy phiếu `submitted`.
    """
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, approve=True)
    _hai_ycmh(db, seed, status="submitted")

    out = str(_hoi(db, seed, "pending_procurement_approvals", {"entity": "purchase_request"}))

    assert "YCMH-CUA-TOI" in out, "tool không chạy tới nơi — ca này không canh được gì"
    assert MOI_MA not in out, "hộp chờ duyệt liệt kê cả phiếu ngoài phạm vi"


def test_my_tickets_khong_lam_lo_phieu_cua_nguoi_khac(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "ticket", scope="own", read=True)
    db.add_all([
        Ticket(code="TK-CUA-TOI", subject="Lỗi của tôi", department="Khác",
               priority="normal", status="open",
               created_by=seed.u_req_id, requester_id=seed.emp_req_id),
        Ticket(code="TK-NGUOI-KHAC", subject=f"Lỗi {MOI_NOI_DUNG}", department="Khác",
               priority="normal", status="open",
               created_by=seed.u_nstm_id, requester_id=seed.emp_nstm_id),
    ])
    db.commit()

    out = str(_hoi(db, seed, "my_tickets"))

    assert "TK-CUA-TOI" in out, "không thấy cả phiếu của mình — ca này vô nghĩa"
    assert MOI_NOI_DUNG not in out
    assert "TK-NGUOI-KHAC" not in out


def test_employee_lookup_khong_lam_lo_ho_so_nguoi_khac(db, seed, cap_quyen):
    """`employee` khai `self: id` nên phạm vi `own` = đúng hồ sơ của chính mình.

    Bài này còn canh một thứ khác: `employee_sensitive` che 15 trường ở tầng serializer.
    Trợ lý đi cửa khác với giao diện, nên nếu tool đọc thẳng model thì CCCD + số tài
    khoản ngân hàng ra thẳng câu trả lời.
    """
    cap_quyen(seed.u_req_id, "employee", scope="own", read=True)

    #  Chữ "N" khớp CẢ BỐN nhân sự trong seed ("Người YC", "Trưởng Phòng", "NSTM Chính",
    #  "NSTM Dự Phòng") — cố ý chọn từ khóa rộng để nếu phạm vi hở thì cả bốn đổ ra.
    out = str(_hoi(db, seed, "employee_lookup", {"query": "N"}))

    assert "Người YC" in out, "không thấy cả hồ sơ của chính mình — ca này vô nghĩa"
    assert "NSTM Chính" not in out, "lộ hồ sơ nhân sự ngoài phạm vi"
    assert "Trưởng Phòng" not in out


def test_payable_lookup_khong_lam_lo_cong_no_ngoai_pham_vi(db, seed, cap_quyen):
    """`payable` neo phạm vi theo `created_by` — khoản nợ người khác nhập không được lọt."""
    from app.modules.payable.model import Payable

    cap_quyen(seed.u_req_id, "payable", scope="own", read=True)
    cap_quyen(seed.u_req_id, "supplier", scope="all", read=True)
    db.add_all([
        Payable(company_id=seed.company_id, supplier_code="NCCA", supplier_name="NCC Anpha",
                source_type="goods", po_code="PO-CUA-TOI", incur_date="2026-08-05",
                period="2026", due_date="2026-12-01", total=1000, paid_amount=0,
                remaining=1000, status="unpaid",
                created_by=seed.u_req_id, updated_by=seed.u_req_id),
        Payable(company_id=seed.company_id, supplier_code="NCCB",
                supplier_name=f"NCC {MOI_NOI_DUNG}", source_type="goods",
                po_code=f"PO-{MOI_MA}", incur_date="2026-08-06", period="2026",
                due_date="2026-12-02", total=9999, paid_amount=0, remaining=9999,
                status="unpaid", created_by=seed.u_nstm_id, updated_by=seed.u_nstm_id),
    ])
    db.commit()

    out = str(_hoi(db, seed, "payable_lookup"))

    assert "PO-CUA-TOI" in out, "không thấy cả khoản nợ của mình — ca này vô nghĩa"
    assert MOI_MA not in out, "lộ mã ĐMH của khoản nợ ngoài phạm vi"
    assert MOI_NOI_DUNG not in out, "lộ tên NCC của khoản nợ ngoài phạm vi"


def test_recent_purchase_orders_khong_lam_lo_dmh_ngoai_pham_vi(db, seed, cap_quyen):
    """ĐMH cũng neo `created_by` — hộp "đơn mua gần nhất" phải kẹp trong phạm vi."""
    from app.modules.purchase_order.model import PurchaseOrder

    cap_quyen(seed.u_req_id, "purchase_order", scope="own", read=True)
    cap_quyen(seed.u_req_id, "supplier", scope="all", read=True)
    db.add_all([
        PurchaseOrder(code="PO-CUA-TOI", company_id=seed.company_id,
                      department_id=seed.dept_id, supplier_code="NCCA",
                      supplier_name="NCC Anpha", order_date="2026-08-05",
                      created_by=seed.u_req_id, updated_by=seed.u_req_id),
        PurchaseOrder(code=f"PO-{MOI_MA}", company_id=seed.company_id,
                      department_id=seed.dept_id, supplier_code="NCCB",
                      supplier_name=f"NCC {MOI_NOI_DUNG}", order_date="2026-08-06",
                      created_by=seed.u_nstm_id, updated_by=seed.u_nstm_id),
    ])
    db.commit()

    out = str(_hoi(db, seed, "recent_purchase_orders"))

    assert "PO-CUA-TOI" in out, "không thấy cả đơn của mình — ca này vô nghĩa"
    assert MOI_MA not in out
    assert MOI_NOI_DUNG not in out


def test_document_read_khong_doc_duoc_van_ban_ngoai_pham_vi(db, seed):
    """Đọc TOÀN VĂN một văn bản của pháp nhân khác — vector "tóm tắt văn bản" điển hình.

    `document_read` cố ý KHÔNG gác bằng `document.read` (văn bản áp dụng cho chính mình
    thì ai cũng đọc được); chốt của nó là `access_service.can` chạy cho TỪNG bản ghi. Bài
    này ép đúng chốt đó: nội dung văn bản công ty khác không được ra, kể cả khi người hỏi
    gõ đúng số hiệu.
    """
    from app.modules.company.model import Company

    from test_assistant_document_tool import _them_loai, _van_ban

    loai = _them_loai(db, "QC", "Quy chế / Quy trình")
    cty_khac = Company(name="Cty Khác", code="CT02", is_active=True)
    db.add(cty_khac)
    db.flush()

    _van_ban(db, loai, "Quy chế của tôi", seed.company_id, seed.emp_tp_id,
             issue_number="01/QC", content="<p>Nội dung ai cũng đọc</p>")
    _van_ban(db, loai, "Quy chế công ty khác", cty_khac.id, seed.emp_tp_id,
             issue_number=f"02/{MOI_MA}", content=f"<p>{MOI_NOI_DUNG}</p>")

    trong = str(_hoi(db, seed, "document_read", {"issue_number": "01/QC"}))
    assert "Nội dung ai cũng đọc" in trong, "không đọc nổi văn bản của chính mình — ca vô nghĩa"

    ngoai = str(_hoi(db, seed, "document_read", {"issue_number": f"02/{MOI_MA}"}))
    assert MOI_NOI_DUNG not in ngoai, "đọc được TOÀN VĂN văn bản ngoài phạm vi"
