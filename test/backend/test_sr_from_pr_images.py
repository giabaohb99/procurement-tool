"""CR-027 — tạo Yêu cầu báo giá từ YCMH bị trả lại/từ chối thì ẢNH ĐỐI CHIẾU của dòng YCMH
được kéo sang dòng YCBG mới: chỉ THÊM liên kết (FileLink) trỏ vào CÙNG file gốc, không upload lại.
"""
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.purchase_request.model import (PurchaseRequest,
                                                PurchaseRequestItem)
from app.modules.survey_request import service as sr_service
from app.modules.survey_request.schema import (SurveyRequestCreate,
                                               SurveyRequestLineIn)


def _make_pr_line_with_image(db, seed, n_img=2):
    pr = PurchaseRequest(code="PYC000999", company_id=seed.company_id, requester="Người YC",
                         department="Phòng Test", purpose="Test", status="cancelled")
    db.add(pr)
    db.flush()
    it = PurchaseRequestItem(pr_id=pr.id, product_name="Nhãn Sản Phẩm A", item_group="Nhãn",
                             qty=10, unit="Cái", price=1000, amount=10000)
    db.add(it)
    db.flush()
    for i in range(n_img):
        f = StoredFile(filename=f"anh{i}.jpg", file_key=f"k/{i}", url=f"http://x/{i}.jpg")
        db.add(f)
        db.flush()
        db.add(FileLink(file_id=f.id, entity="purchase_request_line_image", entity_id=it.id))
    db.commit()
    return pr, it


def _create_sr(db, seed, src_item_id):
    data = SurveyRequestCreate(
        company_id=seed.company_id, requester="Người YC", department="Phòng Test",
        purpose="Khảo sát lại", request_date="2026-08-05",
        lines=[SurveyRequestLineIn(item_group="Nhãn", requirement_detail="Nhãn Sản Phẩm A",
                                   request_qty=10, uom="Cái", src_pr_item_id=src_item_id)],
    )
    return sr_service.create_sr(db, data, user_id=1)


def _sr_line_links(db, sid):
    ln = sr_service.lines_of(db, sid)[0]
    return db.query(FileLink).filter(FileLink.entity == "survey_request_line",
                                     FileLink.entity_id == ln.id).all()


def test_anh_dong_ycmh_duoc_keo_sang_dong_ycbg(db, seed):
    _, it = _make_pr_line_with_image(db, seed, n_img=2)
    src_file_ids = {l.file_id for l in db.query(FileLink)
                    .filter(FileLink.entity == "purchase_request_line_image").all()}

    s = _create_sr(db, seed, it.id)

    links = _sr_line_links(db, s.id)
    assert len(links) == 2
    assert {l.file_id for l in links} == src_file_ids          # dùng chung file gốc
    assert db.query(StoredFile).count() == 2                   # KHÔNG nhân bản file


def test_khong_co_src_thi_khong_keo_gi(db, seed):
    _make_pr_line_with_image(db, seed, n_img=2)
    s = _create_sr(db, seed, src_item_id=0)
    assert _sr_line_links(db, s.id) == []


def test_src_khong_ton_tai_thi_bo_qua(db, seed):
    _make_pr_line_with_image(db, seed, n_img=2)
    s = _create_sr(db, seed, src_item_id=999999)
    assert _sr_line_links(db, s.id) == []


def test_xoa_dong_ycbg_khong_lam_mat_anh_ben_ycmh(db, seed):
    """Xóa dòng YCBG chỉ gỡ liên kết của nó; ảnh trên YCMH nguồn phải còn nguyên."""
    _, it = _make_pr_line_with_image(db, seed, n_img=2)
    s = _create_sr(db, seed, it.id)

    from app.modules.survey_request.schema import SurveyRequestUpdate
    sr_service.update_sr(db, s.id, SurveyRequestUpdate(lines=[]), user_id=1)

    assert sr_service.lines_of(db, s.id) == []
    assert db.query(FileLink).filter(FileLink.entity == "survey_request_line").count() == 0
    assert db.query(StoredFile).count() == 2                   # file gốc KHÔNG bị xóa lây
    assert db.query(FileLink).filter(FileLink.entity == "purchase_request_line_image",
                                     FileLink.entity_id == it.id).count() == 2
