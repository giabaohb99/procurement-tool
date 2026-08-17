"""NHÓM E — quan hệ cha–con giữa các văn bản (E01–E06).

Cả bốn chốt chặn đều nằm ở **tầng dịch vụ** chứ không phải ẩn ô trên giao diện,
nên bài kiểm gọi thẳng hàm service — đúng như một người gọi thẳng API sẽ làm.

Bài quan trọng nhất là `test_cam_vong_lap_ca_chuoi_dai`: kiểm vòng lặp bằng cách
so hai bước (A→B rồi B→A) là cách viết tự nhiên nhất, và nó **cho lọt** vòng ba
cạnh. Lọt rồi thì cây tài liệu đệ quy vô hạn.
"""
import pytest
from fastapi import HTTPException

from app.modules.company.model import Company
from app.modules.doc_catalog.link_rule_model import (RELATION_BELONGS,
                                                     RELATION_GUIDE,
                                                     RELATION_REFERENCE,
                                                     DocTypeLinkRule)
from app.modules.doc_catalog.model import DocType
from app.modules.document import link_serializer, link_service, service
from app.modules.document.schema import DocumentCreate

ACTOR = 1


@pytest.fixture()
def catalog(db, seed):
    company = db.get(Company, seed.company_id)
    company.issue_code = "DEGO"
    quy_trinh = DocType(code="QT", name="Quy trình", id_scheme=1, number_when=2)
    huong_dan = DocType(code="HDCV", name="Hướng dẫn công việc", id_scheme=1, number_when=2)
    bieu_mau = DocType(code="BM", name="Biểu mẫu", id_scheme=1, number_when=2)
    db.add_all([quy_trinh, huong_dan, bieu_mau])
    db.commit()

    #  HDCV hướng dẫn ĐÚNG MỘT Quy trình — dòng bắt buộc của tài liệu.
    db.add(DocTypeLinkRule(source_type_id=huong_dan.id, relation=RELATION_GUIDE,
                           target_type_id=quy_trinh.id, is_required=True,
                           min_count=1, max_count=1))
    #  HDCV hướng dẫn HDCV: không có trong tài liệu, thêm để dựng được vòng lặp
    #  dài mà vẫn đi qua đúng đường kiểm của `add_link`.
    db.add(DocTypeLinkRule(source_type_id=huong_dan.id, relation=RELATION_GUIDE,
                           target_type_id=huong_dan.id, is_required=False))
    db.add(DocTypeLinkRule(source_type_id=bieu_mau.id, relation=RELATION_BELONGS,
                           target_type_id=quy_trinh.id, is_required=True, min_count=1))
    db.commit()
    return {"QT": quy_trinh, "HDCV": huong_dan, "BM": bieu_mau, "seed": seed}


def _tao(db, catalog, code: str, title: str):
    seed = catalog["seed"]
    return service.create_document(db, DocumentCreate(
        doc_type_id=catalog[code].id, company_id=seed.company_id,
        department_id=seed.dept_id, owner_employee_id=seed.emp_req_id,
        title=title, content_html="<p>Nội dung</p>",
    ), ACTOR)


# ── E03 · form tự hiện ô theo quy tắc ────────────────────────────────────────
def test_form_tu_hien_o_quan_he_theo_loai(db, catalog):
    slots = link_service.rules_for_type(db, catalog["HDCV"].id)
    assert [s.relation for s in slots] == [RELATION_GUIDE, RELATION_GUIDE]
    #  Dòng bắt buộc lên đầu — người soạn nhìn thấy thứ chặn mình trước.
    assert slots[0].is_required is True


def test_danh_sach_chon_chi_hien_van_ban_con_hieu_luc(db, catalog):
    con_song = _tao(db, catalog, "QT", "Quy trình đang chạy")
    service.submit(db, con_song, ACTOR)
    service.approve(db, con_song, ACTOR)
    _tao(db, catalog, "QT", "Quy trình còn nháp")

    rule = link_service.rules_for_type(db, catalog["HDCV"].id)[0]
    chon_duoc = link_service.allowed_targets(db, rule)

    #  Bản nháp không được hiện: trỏ vào một quy trình chưa ban hành thì hướng
    #  dẫn ban hành ra trước cả thứ nó hướng dẫn.
    assert [d.title for d in chon_duoc] == ["Quy trình đang chạy"]


# ── Khai quan hệ · phải khớp quy tắc ─────────────────────────────────────────
def test_khai_quan_he_dung_quy_tac_thi_ghi_duoc(db, catalog):
    quy_trinh = _tao(db, catalog, "QT", "Quy trình mua hàng")
    huong_dan = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")

    link = link_service.add_link(db, huong_dan, RELATION_GUIDE, quy_trinh.id, "", ACTOR)

    assert link.target_document_id == quy_trinh.id
    assert link.rule_id is not None


def test_loai_dich_khong_co_trong_quy_tac_thi_tu_choi(db, catalog):
    bieu_mau = _tao(db, catalog, "BM", "Biểu mẫu đề nghị")
    huong_dan = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")

    #  BM chỉ được "thuộc về" Quy trình, không có dòng nào cho "thuộc về" HDCV.
    with pytest.raises(HTTPException) as loi:
        link_service.add_link(db, bieu_mau, RELATION_BELONGS, huong_dan.id, "", ACTOR)
    assert "Quy tắc quan hệ" in loi.value.detail


def test_vuot_so_luong_toi_da_thi_tu_choi(db, catalog):
    mot = _tao(db, catalog, "QT", "Quy trình A")
    hai = _tao(db, catalog, "QT", "Quy trình B")
    huong_dan = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")

    link_service.add_link(db, huong_dan, RELATION_GUIDE, mot.id, "", ACTOR)
    with pytest.raises(HTTPException) as loi:
        link_service.add_link(db, huong_dan, RELATION_GUIDE, hai.id, "", ACTOR)
    assert "tối đa" in loi.value.detail


def test_tham_chieu_di_qua_duoc_ma_khong_can_quy_tac(db, catalog):
    """«Tham chiếu» là liên kết mềm — tài liệu khai "bất kỳ tham chiếu bất kỳ"."""
    mot = _tao(db, catalog, "QT", "Quy trình A")
    hai = _tao(db, catalog, "BM", "Biểu mẫu B")

    link = link_service.add_link(db, hai, RELATION_REFERENCE, mot.id, "", ACTOR)
    assert link.rule_id is None


# ── E05 · cấm vòng lặp ───────────────────────────────────────────────────────
def test_cam_tu_tro_vao_chinh_minh(db, catalog):
    huong_dan = _tao(db, catalog, "HDCV", "Hướng dẫn tự trỏ")
    with pytest.raises(HTTPException):
        link_service.add_link(db, huong_dan, RELATION_GUIDE, huong_dan.id, "", ACTOR)


def test_cam_vong_lap_hai_buoc(db, catalog):
    a = _tao(db, catalog, "HDCV", "Hướng dẫn A")
    b = _tao(db, catalog, "HDCV", "Hướng dẫn B")

    link_service.add_link(db, a, RELATION_GUIDE, b.id, "", ACTOR)
    with pytest.raises(HTTPException) as loi:
        link_service.add_link(db, b, RELATION_GUIDE, a.id, "", ACTOR)
    assert "vòng lặp" in loi.value.detail


def test_cam_vong_lap_ca_chuoi_dai(db, catalog):
    """A→B→C→A. Kiểm hai bước cho lọt vòng này, mà lọt là cây đệ quy vô hạn."""
    a = _tao(db, catalog, "HDCV", "Hướng dẫn A")
    b = _tao(db, catalog, "HDCV", "Hướng dẫn B")
    c = _tao(db, catalog, "HDCV", "Hướng dẫn C")

    link_service.add_link(db, a, RELATION_GUIDE, b.id, "", ACTOR)
    link_service.add_link(db, b, RELATION_GUIDE, c.id, "", ACTOR)

    with pytest.raises(HTTPException) as loi:
        link_service.add_link(db, c, RELATION_GUIDE, a.id, "", ACTOR)
    assert "vòng lặp" in loi.value.detail


def test_vong_lap_chi_xet_trong_cung_mot_loai_quan_he(db, catalog):
    """A hướng dẫn B, rồi B tham chiếu A — KHÔNG phải vòng lặp.

    Hai quan hệ khác nghĩa nhau; chặn cả hai là chặn nhầm việc bình thường.
    """
    quy_trinh = _tao(db, catalog, "QT", "Quy trình A")
    huong_dan = _tao(db, catalog, "HDCV", "Hướng dẫn B")

    link_service.add_link(db, huong_dan, RELATION_GUIDE, quy_trinh.id, "", ACTOR)
    link_service.add_link(db, quy_trinh, RELATION_REFERENCE, huong_dan.id, "", ACTOR)


# ── E04 · chặn gửi duyệt khi thiếu quan hệ bắt buộc ──────────────────────────
def test_thieu_quan_he_bat_buoc_thi_khong_gui_duyet_duoc(db, catalog):
    huong_dan = _tao(db, catalog, "HDCV", "Hướng dẫn chưa trỏ vào đâu")

    thieu = link_service.missing_required(db, huong_dan)
    assert len(thieu) == 1 and "Hướng dẫn" in thieu[0]

    with pytest.raises(HTTPException) as loi:
        service.submit(db, huong_dan, ACTOR)
    assert "quan hệ bắt buộc" in loi.value.detail


def test_khai_du_quan_he_thi_gui_duyet_duoc(db, catalog):
    quy_trinh = _tao(db, catalog, "QT", "Quy trình mua hàng")
    huong_dan = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")
    link_service.add_link(db, huong_dan, RELATION_GUIDE, quy_trinh.id, "", ACTOR)

    assert link_service.missing_required(db, huong_dan) == []
    service.submit(db, huong_dan, ACTOR)


def test_loai_khong_co_quy_tac_bat_buoc_thi_gui_thoai_mai(db, catalog):
    quy_trinh = _tao(db, catalog, "QT", "Quy trình đứng một mình")
    assert link_service.missing_required(db, quy_trinh) == []
    service.submit(db, quy_trinh, ACTOR)


# ── E06 · cây tài liệu ───────────────────────────────────────────────────────
def test_cay_tai_lieu_hien_con_tro_vao_minh(db, catalog):
    """Mở một Quy trình thấy ngay Hướng dẫn và Biểu mẫu thuộc nó."""
    quy_trinh = _tao(db, catalog, "QT", "Quy trình mua hàng")
    huong_dan = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")
    bieu_mau = _tao(db, catalog, "BM", "Biểu mẫu đề nghị")
    link_service.add_link(db, huong_dan, RELATION_GUIDE, quy_trinh.id, "", ACTOR)
    link_service.add_link(db, bieu_mau, RELATION_BELONGS, quy_trinh.id, "", ACTOR)

    cay = link_serializer.build_tree(db, quy_trinh)

    ten_con = sorted(node["title"] for node in cay["children"])
    assert ten_con == ["Biểu mẫu đề nghị", "Hướng dẫn tạo phiếu"]
    assert all(node["relation_label"] for node in cay["children"])


def test_cay_khong_lap_vo_han_khi_hai_loai_quan_he_khep_vong(db, catalog):
    """A hướng dẫn B và B tham chiếu A đều hợp lệ, nhưng duyệt cây thì thành vòng."""
    quy_trinh = _tao(db, catalog, "QT", "Quy trình A")
    huong_dan = _tao(db, catalog, "HDCV", "Hướng dẫn B")
    link_service.add_link(db, huong_dan, RELATION_GUIDE, quy_trinh.id, "", ACTOR)
    link_service.add_link(db, quy_trinh, RELATION_REFERENCE, huong_dan.id, "", ACTOR)

    cay = link_serializer.build_tree(db, quy_trinh)
    assert len(cay["children"]) == 1


def test_doc_nguoc_quan_he_theo_phia_dang_xem(db, catalog):
    """Cùng một dòng dữ liệu, mở từ hai phía phải đọc ra hai câu khác nhau."""
    quy_trinh = _tao(db, catalog, "QT", "Quy trình mua hàng")
    huong_dan = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")
    link = link_service.add_link(db, huong_dan, RELATION_GUIDE, quy_trinh.id, "", ACTOR)

    tu_con = link_serializer.serialize_link(db, link, viewed_from=huong_dan.id)
    tu_cha = link_serializer.serialize_link(db, link, viewed_from=quy_trinh.id)

    assert tu_con["relation_label"] == "Hướng dẫn"
    assert tu_con["direction"] == "outgoing"
    assert tu_cha["relation_label"] == "Được hướng dẫn bởi"
    assert tu_cha["direction"] == "incoming"


# ── Hai dòng quy tắc CÙNG quan hệ, KHÁC loại đích ────────────────────────────
#
# Biểu mẫu *thuộc về* Quy trình (bắt buộc) và Biểu mẫu *thuộc về* Quy chế (tùy
# chọn) là hai dòng khác nhau. Đếm gộp theo loại quan hệ thì khai một Quy chế
# làm thỏa mãn luôn dòng đòi Quy trình — cổng E04 bị đi vòng bằng cách khai sai
# loại đích. Lỗi này lọt qua toàn bộ bài kiểm ở trên vì chúng chỉ dựng MỘT dòng
# quy tắc cho mỗi quan hệ.
@pytest.fixture()
def hai_dong_thuoc_ve(db, catalog):
    quy_che = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(quy_che)
    db.commit()
    db.add(DocTypeLinkRule(source_type_id=catalog["BM"].id, relation=RELATION_BELONGS,
                           target_type_id=quy_che.id, is_required=False))
    db.commit()
    catalog["QC"] = quy_che
    return catalog


def test_khai_sai_loai_dich_khong_qua_duoc_cong_bat_buoc(db, hai_dong_thuoc_ve):
    bieu_mau = _tao(db, hai_dong_thuoc_ve, "BM", "Biểu mẫu đề nghị")
    quy_che = _tao(db, hai_dong_thuoc_ve, "QC", "Quy chế lương")

    link_service.add_link(db, bieu_mau, RELATION_BELONGS, quy_che.id, "", ACTOR)

    #  Dòng bắt buộc đòi QUY TRÌNH — khai Quy chế không thay thế được.
    thieu = link_service.missing_required(db, bieu_mau)
    assert len(thieu) == 1 and "Quy trình" in thieu[0]

    with pytest.raises(HTTPException):
        service.submit(db, bieu_mau, ACTOR)


def test_khai_dung_loai_dich_thi_qua_cong(db, hai_dong_thuoc_ve):
    bieu_mau = _tao(db, hai_dong_thuoc_ve, "BM", "Biểu mẫu đề nghị")
    quy_trinh = _tao(db, hai_dong_thuoc_ve, "QT", "Quy trình mua hàng")

    link_service.add_link(db, bieu_mau, RELATION_BELONGS, quy_trinh.id, "", ACTOR)

    assert link_service.missing_required(db, bieu_mau) == []
    service.submit(db, bieu_mau, ACTOR)


def test_so_luong_toi_da_dem_rieng_tung_dong_quy_tac(db, hai_dong_thuoc_ve):
    """Dòng QT tối đa 1 không được chặn dòng QC — hai bộ đếm độc lập."""
    for rule in link_service.rules_for_type(db, hai_dong_thuoc_ve["BM"].id):
        rule.max_count = 1
    db.commit()

    bieu_mau = _tao(db, hai_dong_thuoc_ve, "BM", "Biểu mẫu đề nghị")
    quy_trinh = _tao(db, hai_dong_thuoc_ve, "QT", "Quy trình mua hàng")
    quy_che = _tao(db, hai_dong_thuoc_ve, "QC", "Quy chế lương")

    link_service.add_link(db, bieu_mau, RELATION_BELONGS, quy_trinh.id, "", ACTOR)
    #  Khai tiếp sang loại đích KHÁC phải được — trước đây bị chặn vì đếm gộp.
    link_service.add_link(db, bieu_mau, RELATION_BELONGS, quy_che.id, "", ACTOR)

    #  Nhưng thêm cái thứ hai CÙNG loại đích thì đúng là phải chặn.
    quy_trinh_2 = _tao(db, hai_dong_thuoc_ve, "QT", "Quy trình bán hàng")
    with pytest.raises(HTTPException) as loi:
        link_service.add_link(db, bieu_mau, RELATION_BELONGS, quy_trinh_2.id, "", ACTOR)
    assert "tối đa" in loi.value.detail


# ── E07 / E08 · tác động khi văn bản CHA thay đổi ────────────────────────────
#
# Hai cột `on_parent_new_version` và `on_parent_obsolete` của bảng quy tắc trước
# đây là CỘT CHẾT: chỉ quan hệ "trích từ" đọc tới, và đọc bằng giá trị khóa cứng
# chứ không qua bảng quy tắc. Nhóm bài kiểm này canh việc chúng thật sự điều
# khiển hành vi.
from app.modules.doc_catalog.link_rule_model import (NEW_VERSION_NOTHING,  # noqa: E402
                                                     OBSOLETE_EXPIRE,
                                                     OBSOLETE_NOTHING)
from app.modules.document import parent_change_service  # noqa: E402
from app.modules.document.model import STATUS_EXPIRED  # noqa: E402
from app.modules.document.schema import VersionCreate  # noqa: E402
from app.modules.document.version_model import CHANGE_MAJOR  # noqa: E402
from app.modules.document.version_service import open_new_version  # noqa: E402


def _ban_hanh(db, doc):
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)
    return doc


def _len_ban_moi(db, doc):
    open_new_version(db, doc, VersionCreate(
        change_kind=CHANGE_MAJOR, change_summary="Sửa điều 5",
    ), ACTOR)
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)


def test_liet_ke_tac_dong_truoc_khi_bam_va_khong_doi_gi(db, catalog):
    """E07 — bảng tác động chỉ ĐỌC. Gọi xong dữ liệu phải y nguyên."""
    quy_trinh = _ban_hanh(db, _tao(db, catalog, "QT", "Quy trình mua hàng"))
    huong_dan = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")
    link_service.add_link(db, huong_dan, RELATION_GUIDE, quy_trinh.id, "", ACTOR)

    tac_dong = parent_change_service.impact_of(db, quy_trinh, obsolete=False)

    assert [m["title"] for m in tac_dong] == ["Hướng dẫn tạo phiếu"]
    assert tac_dong[0]["action_label"]
    db.refresh(huong_dan)
    assert huong_dan.needs_review is False


def test_cha_len_phien_ban_moi_thi_con_bi_danh_dau(db, catalog):
    quy_trinh = _ban_hanh(db, _tao(db, catalog, "QT", "Quy trình mua hàng"))
    huong_dan = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")
    link_service.add_link(db, huong_dan, RELATION_GUIDE, quy_trinh.id, "", ACTOR)

    _len_ban_moi(db, quy_trinh)

    db.refresh(huong_dan)
    assert huong_dan.needs_review is True
    assert "phiên bản 2.0" in huong_dan.needs_review_note


def test_quy_tac_khai_khong_lam_gi_thi_con_khong_bi_danh_dau(db, catalog):
    """Cột cấu hình phải thật sự điều khiển — không phải lúc nào cũng đánh dấu."""
    for rule in link_service.rules_for_type(db, catalog["HDCV"].id):
        rule.on_parent_new_version = NEW_VERSION_NOTHING
    db.commit()

    quy_trinh = _ban_hanh(db, _tao(db, catalog, "QT", "Quy trình mua hàng"))
    huong_dan = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")
    link_service.add_link(db, huong_dan, RELATION_GUIDE, quy_trinh.id, "", ACTOR)

    _len_ban_moi(db, quy_trinh)

    db.refresh(huong_dan)
    assert huong_dan.needs_review is False


def test_bai_bo_cha_theo_cau_hinh_het_hieu_luc(db, catalog):
    for rule in link_service.rules_for_type(db, catalog["HDCV"].id):
        rule.on_parent_obsolete = OBSOLETE_EXPIRE
    db.commit()

    quy_trinh = _ban_hanh(db, _tao(db, catalog, "QT", "Quy trình mua hàng"))
    huong_dan = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")
    link_service.add_link(db, huong_dan, RELATION_GUIDE, quy_trinh.id, "", ACTOR)
    _ban_hanh(db, huong_dan)

    service.revoke(db, quy_trinh, "Thay bằng quy trình mới", ACTOR)

    db.refresh(huong_dan)
    assert huong_dan.status == STATUS_EXPIRED


def test_bai_bo_cha_muc_danh_dau_thi_con_van_con_hieu_luc(db, catalog):
    """Mức 2 chỉ đánh dấu: Biểu mẫu vẫn dùng được dù Quy trình cha đã bỏ."""
    quy_trinh = _ban_hanh(db, _tao(db, catalog, "QT", "Quy trình mua hàng"))
    bieu_mau = _tao(db, catalog, "BM", "Biểu mẫu đề nghị")
    link_service.add_link(db, bieu_mau, RELATION_BELONGS, quy_trinh.id, "", ACTOR)
    _ban_hanh(db, bieu_mau)

    service.revoke(db, quy_trinh, "Thay bằng quy trình mới", ACTOR)

    db.refresh(bieu_mau)
    assert bieu_mau.needs_review is True
    assert bieu_mau.status != STATUS_EXPIRED


def test_bai_bo_cha_muc_khong_lam_gi_thi_con_khong_bi_dung(db, catalog):
    for rule in link_service.rules_for_type(db, catalog["BM"].id):
        rule.on_parent_obsolete = OBSOLETE_NOTHING
    db.commit()

    quy_trinh = _ban_hanh(db, _tao(db, catalog, "QT", "Quy trình mua hàng"))
    bieu_mau = _tao(db, catalog, "BM", "Biểu mẫu đề nghị")
    link_service.add_link(db, bieu_mau, RELATION_BELONGS, quy_trinh.id, "", ACTOR)
    _ban_hanh(db, bieu_mau)

    service.revoke(db, quy_trinh, "Thay bằng quy trình mới", ACTOR)

    db.refresh(bieu_mau)
    assert bieu_mau.needs_review is False
    assert bieu_mau.status != STATUS_EXPIRED
