"""bao-CR-317 + bao-CR-318 — hai chỗ đứt liên kết trên phiếu YCMH.

CR-317 — ô "Báo giá đính kèm" trên bản in luôn tick "Không".
    Bản in đọc cột `quote_file_url` (ô tải đúng 1 file từ thời đầu), trong khi chứng từ nay
    nằm ở khối đính kèm (`tab_file_link`, loại `quotation`). Trên prod không phiếu nào còn
    ghi vào cột cũ, nên ô tick sai với MỌI phiếu có báo giá thật.

CR-318 — YCMH không có đường quay về YCBG.
    Chiều ĐMH -> YCMH đã có sẵn (`pr_code`), chiều YCMH -> YCBG thì chỉ nằm trong câu chữ ở
    ô Nội dung nên bấm không ra. Liên kết thật vốn có trong CSDL, chỉ là chưa ai đọc lên.
"""
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.purchase_request.controller import _has_quote_file, _linked_survey_requests
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.survey_request.model import (SurveyRequest, SurveyRequestLine,
                                              SurveyRequestPr)


def _first_ycbg(db, pr) -> tuple[int, str]:
    """Hai khóa vô hướng `survey_request_id` / `survey_request_code` mà `_out` vẫn gửi cho
    giao diện cũ và bản in: phiếu nguồn ĐẦU TIÊN, hoặc (0, "") khi không có nguồn nào."""
    rows = _linked_survey_requests(db, pr)
    return (rows[0]["id"], rows[0]["code"]) if rows else (0, "")


def _make_pr(db, seed, code: str, quote_file_url: str = ""):
    pr = PurchaseRequest(code=code, company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="Phòng Test",
                         status="approved", request_date="2026-09-08",
                         quote_file_url=quote_file_url,
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pr


def _attach(db, seed, entity: str, entity_id: int, doc_type: str):
    f = StoredFile(filename="bao-gia.pdf", file_key=f"k/{entity}/{entity_id}/{doc_type}",
                   url="https://r2/bao-gia.pdf", content_type="application/pdf", size=1024,
                   created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(f)
    db.flush()
    db.add(FileLink(file_id=f.id, entity=entity, entity_id=entity_id, doc_type=doc_type,
                    created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()


def _make_ycbg(db, seed, code: str):
    sr = SurveyRequest(code=code, company_id=seed.company_id, requester="Người YC",
                       requester_id=seed.emp_req_id, department="Phòng Test",
                       request_date="2026-09-03", status="survey_done",
                       created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(sr)
    db.commit()
    db.refresh(sr)
    return sr


# --- CR-317: ô "Báo giá đính kèm" -----------------------------------------------------------

def test_khong_co_file_thi_khong_tick_bao_gia(db, seed):
    """Phiếu trắng — không cột cũ, không đính kèm."""
    pr = _make_pr(db, seed, "PYC-317-01")
    assert _has_quote_file(db, pr) is False


def test_file_loai_bao_gia_o_khoi_dinh_kem_thi_tick(db, seed):
    """Đường đi HIỆN TẠI của prod: file loại `quotation` trên entity `purchase_request`.
    Đây chính là ca hỏng — trước CR-317 ô tick vẫn ra "Không"."""
    pr = _make_pr(db, seed, "PYC-317-02")
    _attach(db, seed, "purchase_request", pr.id, "quotation")
    assert _has_quote_file(db, pr) is True


def test_chi_co_file_loai_khac_thi_khong_tick(db, seed):
    """Đính kèm loại "Khác" KHÔNG phải báo giá — ô tick phải giữ "Không"."""
    pr = _make_pr(db, seed, "PYC-317-03")
    _attach(db, seed, "purchase_request", pr.id, "other")
    assert _has_quote_file(db, pr) is False


def test_cot_cu_quote_file_url_van_duoc_tinh(db, seed):
    """Phiếu đời đầu chỉ có cột cũ — không được làm mất bản in đúng của họ."""
    pr = _make_pr(db, seed, "PYC-317-04", quote_file_url="https://r2/bao-gia-cu.pdf")
    assert _has_quote_file(db, pr) is True


def test_entity_cu_purchase_request_quote_van_duoc_tinh(db, seed):
    """Khối tải báo giá riêng thời trước để `doc_type` rỗng — nhận theo entity."""
    pr = _make_pr(db, seed, "PYC-317-05")
    _attach(db, seed, "purchase_request_quote", pr.id, "")
    assert _has_quote_file(db, pr) is True


def test_khong_lay_nham_bao_gia_cua_phieu_khac(db, seed):
    """Cùng `entity_id` nhưng khác phiếu thì không được dính — canh lỗi quên lọc id."""
    pr1 = _make_pr(db, seed, "PYC-317-06")
    pr2 = _make_pr(db, seed, "PYC-317-07")
    _attach(db, seed, "purchase_request", pr1.id, "quotation")
    assert _has_quote_file(db, pr1) is True
    assert _has_quote_file(db, pr2) is False


def test_khong_lay_nham_bao_gia_cua_chung_tu_khac(db, seed):
    """Báo giá gắn ở ĐƠN MUA HÀNG trùng id với phiếu — phải bỏ qua vì khác entity."""
    pr = _make_pr(db, seed, "PYC-317-08")
    _attach(db, seed, "purchase_order", pr.id, "quotation")
    assert _has_quote_file(db, pr) is False


# --- CR-318: đường quay về YCBG -------------------------------------------------------------

def test_phieu_lap_tay_thi_khong_co_ycbg(db, seed):
    """Không sinh từ khảo sát → (0, "") để giao diện không hiện dòng nào."""
    pr = _make_pr(db, seed, "PYC-318-01")
    assert _first_ycbg(db, pr) == (0, "")


def test_tra_ve_ycbg_theo_bang_lien_ket(db, seed):
    """Nguồn chuẩn: `tab_survey_request_pr` — ghi mỗi lần chốt phương án tạo YCMH."""
    pr = _make_pr(db, seed, "PYC-318-02")
    sr = _make_ycbg(db, seed, "YCBG03092602")
    db.add(SurveyRequestPr(survey_request_id=sr.id, survey_request_line_id=0, pr_id=pr.id,
                           pr_code=pr.code, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    assert _first_ycbg(db, pr) == (sr.id, "YCBG03092602")


def test_lui_ve_dong_ycbg_khi_chua_co_bang_lien_ket(db, seed):
    """Phiếu tạo trước khi có `tab_survey_request_pr` chỉ còn dấu vết ở dòng YCBG."""
    pr = _make_pr(db, seed, "PYC-318-03")
    sr = _make_ycbg(db, seed, "YCBG01092601")
    db.add(SurveyRequestLine(survey_request_id=sr.id, item_group="Nhãn", request_qty=10,
                             pr_id=pr.id, pr_code=pr.code,
                             created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    assert _first_ycbg(db, pr) == (sr.id, "YCBG01092601")


def test_khong_lay_nham_ycbg_cua_phieu_khac(db, seed):
    """Phiếu không có liên kết vẫn phải rỗng dù trong hệ có YCBG của phiếu khác."""
    pr1 = _make_pr(db, seed, "PYC-318-04")
    pr2 = _make_pr(db, seed, "PYC-318-05")
    sr = _make_ycbg(db, seed, "YCBG02092601")
    db.add(SurveyRequestPr(survey_request_id=sr.id, survey_request_line_id=0, pr_id=pr1.id,
                           pr_code=pr1.code, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    assert _first_ycbg(db, pr1)[1] == "YCBG02092601"
    assert _first_ycbg(db, pr2) == (0, "")


def test_mot_phieu_mua_lai_nhieu_lan_thi_lay_ycbg_dau_tien(db, seed):
    """Một dòng YCBG tạo được NHIỀU YCMH (mua lại). Ngược lại một phiếu gom từ 2 YCBG thì
    hai khóa vô hướng vẫn chốt lấy phiếu ĐẦU — cố định, không phụ thuộc thứ tự của CSDL.
    Danh sách đầy đủ là việc của `_linked_survey_requests` (bao-CR-422, các bài bên dưới)."""
    pr = _make_pr(db, seed, "PYC-318-06")
    sr1 = _make_ycbg(db, seed, "YCBG04092601")
    sr2 = _make_ycbg(db, seed, "YCBG04092602")
    for sr in (sr1, sr2):
        db.add(SurveyRequestPr(survey_request_id=sr.id, survey_request_line_id=0, pr_id=pr.id,
                               pr_code=pr.code, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    assert _first_ycbg(db, pr) == (sr1.id, "YCBG04092601")


def test_ycbg_bi_xoa_thi_tra_rong(db, seed):
    """Dòng liên kết trỏ tới YCBG không còn → không hiện mã cụt, cũng không nổ."""
    pr = _make_pr(db, seed, "PYC-318-07")
    db.add(SurveyRequestPr(survey_request_id=999999, survey_request_line_id=0, pr_id=pr.id,
                           pr_code=pr.code, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    assert _first_ycbg(db, pr) == (0, "")


# --- CR-422: bày ĐỦ danh sách YCBG nguồn ----------------------------------------------------

def test_liet_ke_du_moi_ycbg_nguon_theo_dung_thu_tu_lien_ket(db, seed):
    """Đây là lý do có bao-CR-422. Một YCMH gom nhiều dòng đã chốt phương án, mà các dòng ấy
    nằm ở những YCBG KHÁC NHAU — bản cũ `limit(1)` chỉ bày phiếu đầu nên người đọc tưởng
    phiếu chỉ có một nguồn. Thứ tự phải theo thứ tự liên kết được ghi, không theo id YCBG."""
    pr = _make_pr(db, seed, "PYC-422-01")
    sr1 = _make_ycbg(db, seed, "YCBG05092601")
    sr2 = _make_ycbg(db, seed, "YCBG05092602")
    # Ghi liên kết NGƯỢC với thứ tự tạo phiếu để bắt lỗi lỡ sắp theo id YCBG.
    for sr in (sr2, sr1):
        db.add(SurveyRequestPr(survey_request_id=sr.id, survey_request_line_id=0, pr_id=pr.id,
                               pr_code=pr.code, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    rows = _linked_survey_requests(db, pr)
    assert [r["code"] for r in rows] == ["YCBG05092602", "YCBG05092601"]
    assert [r["id"] for r in rows] == [sr2.id, sr1.id]


def test_mot_ycbg_nhieu_dong_do_vao_cung_phieu_thi_chi_bay_mot_lan(db, seed):
    """Một YCBG có thể có nhiều dòng cùng đổ vào một YCMH (mỗi dòng một liên kết). Bày hai
    lần là người đọc tưởng có hai phiếu nguồn — phải khử trùng."""
    pr = _make_pr(db, seed, "PYC-422-02")
    sr = _make_ycbg(db, seed, "YCBG05092603")
    for line_id in (11, 12, 13):
        db.add(SurveyRequestPr(survey_request_id=sr.id, survey_request_line_id=line_id,
                               pr_id=pr.id, pr_code=pr.code,
                               created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    rows = _linked_survey_requests(db, pr)
    assert [r["code"] for r in rows] == ["YCBG05092603"]


def test_ycbg_bi_xoa_thi_bo_qua_nhung_van_giu_phieu_con_song(db, seed):
    """Một nguồn bị xóa không được kéo theo nguồn còn sống: bỏ đúng dòng cụt, giữ phần còn lại.
    Cũng canh luôn lỗi lỡ tra CSDL xong rồi sắp theo thứ tự CSDL trả về."""
    pr = _make_pr(db, seed, "PYC-422-03")
    sr = _make_ycbg(db, seed, "YCBG05092604")
    db.add(SurveyRequestPr(survey_request_id=999998, survey_request_line_id=0, pr_id=pr.id,
                           pr_code=pr.code, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.add(SurveyRequestPr(survey_request_id=sr.id, survey_request_line_id=0, pr_id=pr.id,
                           pr_code=pr.code, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    rows = _linked_survey_requests(db, pr)
    assert [r["code"] for r in rows] == ["YCBG05092604"]
    # Hai khóa vô hướng cũ cũng phải nhảy qua dòng cụt chứ không trả (0, "").
    assert _first_ycbg(db, pr) == (sr.id, "YCBG05092604")


def test_moi_dong_du_truong_cho_giao_dien_bam_vao(db, seed):
    """Giao diện cần mã để bấm, thêm trạng thái/ngày/người yêu cầu để khỏi phải mở phiếu mới
    biết nó tới đâu. Thiếu một trường là thẻ liên kết bày ô trống."""
    pr = _make_pr(db, seed, "PYC-422-04")
    sr = _make_ycbg(db, seed, "YCBG05092605")
    db.add(SurveyRequestPr(survey_request_id=sr.id, survey_request_line_id=0, pr_id=pr.id,
                           pr_code=pr.code, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    (row,) = _linked_survey_requests(db, pr)
    assert row == {"id": sr.id, "code": "YCBG05092605", "status": "survey_done",
                   "request_date": "2026-09-03", "requester": "Người YC"}


def test_duong_lui_cung_tra_ve_danh_sach_du(db, seed):
    """Phiếu đời cũ chưa có bảng liên kết: đường lui theo `SurveyRequestLine.pr_id` cũng phải
    gom đủ nhiều nguồn và khử trùng, chứ không chỉ lấy dòng đầu."""
    pr = _make_pr(db, seed, "PYC-422-05")
    sr1 = _make_ycbg(db, seed, "YCBG05092606")
    sr2 = _make_ycbg(db, seed, "YCBG05092607")
    for sr in (sr1, sr1, sr2):
        db.add(SurveyRequestLine(survey_request_id=sr.id, item_group="Nhãn", request_qty=10,
                                 pr_id=pr.id, pr_code=pr.code,
                                 created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    rows = _linked_survey_requests(db, pr)
    assert [r["code"] for r in rows] == ["YCBG05092606", "YCBG05092607"]


def test_co_bang_lien_ket_thi_khong_don_them_duong_lui(db, seed):
    """Đường lui CHỈ chạy khi bảng liên kết rỗng. Phiếu mới luôn có cả hai dấu vết, cộng dồn
    cả hai là đếm trùng và bày cả những YCBG mà bảng liên kết cố ý không nhận."""
    pr = _make_pr(db, seed, "PYC-422-06")
    sr_moi = _make_ycbg(db, seed, "YCBG05092608")
    sr_cu = _make_ycbg(db, seed, "YCBG05092609")
    db.add(SurveyRequestPr(survey_request_id=sr_moi.id, survey_request_line_id=0, pr_id=pr.id,
                           pr_code=pr.code, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.add(SurveyRequestLine(survey_request_id=sr_cu.id, item_group="Nhãn", request_qty=10,
                             pr_id=pr.id, pr_code=pr.code,
                             created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    rows = _linked_survey_requests(db, pr)
    assert [r["code"] for r in rows] == ["YCBG05092608"]
