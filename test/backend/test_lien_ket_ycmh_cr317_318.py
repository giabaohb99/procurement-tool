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
from app.modules.purchase_request.controller import _has_quote_file, _source_survey_request
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.survey_request.model import (SurveyRequest, SurveyRequestLine,
                                              SurveyRequestPr)


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
    assert _source_survey_request(db, pr) == (0, "")


def test_tra_ve_ycbg_theo_bang_lien_ket(db, seed):
    """Nguồn chuẩn: `tab_survey_request_pr` — ghi mỗi lần chốt phương án tạo YCMH."""
    pr = _make_pr(db, seed, "PYC-318-02")
    sr = _make_ycbg(db, seed, "YCBG03092602")
    db.add(SurveyRequestPr(survey_request_id=sr.id, survey_request_line_id=0, pr_id=pr.id,
                           pr_code=pr.code, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    assert _source_survey_request(db, pr) == (sr.id, "YCBG03092602")


def test_lui_ve_dong_ycbg_khi_chua_co_bang_lien_ket(db, seed):
    """Phiếu tạo trước khi có `tab_survey_request_pr` chỉ còn dấu vết ở dòng YCBG."""
    pr = _make_pr(db, seed, "PYC-318-03")
    sr = _make_ycbg(db, seed, "YCBG01092601")
    db.add(SurveyRequestLine(survey_request_id=sr.id, item_group="Nhãn", request_qty=10,
                             pr_id=pr.id, pr_code=pr.code,
                             created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    assert _source_survey_request(db, pr) == (sr.id, "YCBG01092601")


def test_khong_lay_nham_ycbg_cua_phieu_khac(db, seed):
    """Phiếu không có liên kết vẫn phải rỗng dù trong hệ có YCBG của phiếu khác."""
    pr1 = _make_pr(db, seed, "PYC-318-04")
    pr2 = _make_pr(db, seed, "PYC-318-05")
    sr = _make_ycbg(db, seed, "YCBG02092601")
    db.add(SurveyRequestPr(survey_request_id=sr.id, survey_request_line_id=0, pr_id=pr1.id,
                           pr_code=pr1.code, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    assert _source_survey_request(db, pr1)[1] == "YCBG02092601"
    assert _source_survey_request(db, pr2) == (0, "")


def test_mot_phieu_mua_lai_nhieu_lan_thi_lay_ycbg_dau_tien(db, seed):
    """Một dòng YCBG tạo được NHIỀU YCMH (mua lại). Ngược lại nếu một phiếu lỡ có 2 dòng
    liên kết thì chốt lấy dòng đầu — cố định, không phụ thuộc thứ tự trả về của CSDL."""
    pr = _make_pr(db, seed, "PYC-318-06")
    sr1 = _make_ycbg(db, seed, "YCBG04092601")
    sr2 = _make_ycbg(db, seed, "YCBG04092602")
    for sr in (sr1, sr2):
        db.add(SurveyRequestPr(survey_request_id=sr.id, survey_request_line_id=0, pr_id=pr.id,
                               pr_code=pr.code, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    assert _source_survey_request(db, pr) == (sr1.id, "YCBG04092601")


def test_ycbg_bi_xoa_thi_tra_rong(db, seed):
    """Dòng liên kết trỏ tới YCBG không còn → không hiện mã cụt, cũng không nổ."""
    pr = _make_pr(db, seed, "PYC-318-07")
    db.add(SurveyRequestPr(survey_request_id=999999, survey_request_line_id=0, pr_id=pr.id,
                           pr_code=pr.code, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    assert _source_survey_request(db, pr) == (0, "")
