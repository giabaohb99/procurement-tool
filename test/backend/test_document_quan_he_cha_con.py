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
    procedure = DocType(code="QT", name="Quy trình", id_scheme=1, number_when=2)
    guideline = DocType(code="HDCV", name="Hướng dẫn công việc", id_scheme=1, number_when=2)
    form = DocType(code="BM", name="Biểu mẫu", id_scheme=1, number_when=2)
    db.add_all([procedure, guideline, form])
    db.commit()

    #  HDCV hướng dẫn ĐÚNG MỘT Quy trình — dòng bắt buộc của tài liệu.
    db.add(DocTypeLinkRule(source_type_id=guideline.id, relation=RELATION_GUIDE,
                           target_type_id=procedure.id, is_required=True,
                           min_count=1, max_count=1))
    #  HDCV hướng dẫn HDCV: không có trong tài liệu, thêm để dựng được vòng lặp
    #  dài mà vẫn đi qua đúng đường kiểm của `add_link`.
    db.add(DocTypeLinkRule(source_type_id=guideline.id, relation=RELATION_GUIDE,
                           target_type_id=guideline.id, is_required=False))
    db.add(DocTypeLinkRule(source_type_id=form.id, relation=RELATION_BELONGS,
                           target_type_id=procedure.id, is_required=True, min_count=1))
    db.commit()
    return {"QT": procedure, "HDCV": guideline, "BM": form, "seed": seed}


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
    procedure = _tao(db, catalog, "QT", "Quy trình mua hàng")
    guideline = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")

    link = link_service.add_link(db, guideline, RELATION_GUIDE, procedure.id, "", ACTOR)

    assert link.target_document_id == procedure.id
    assert link.rule_id is not None


def test_loai_dich_khong_co_trong_quy_tac_thi_tu_choi(db, catalog):
    form = _tao(db, catalog, "BM", "Biểu mẫu đề nghị")
    guideline = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")

    #  BM chỉ được "thuộc về" Quy trình, không có dòng nào cho "thuộc về" HDCV.
    with pytest.raises(HTTPException) as error:
        link_service.add_link(db, form, RELATION_BELONGS, guideline.id, "", ACTOR)
    assert "Quy tắc quan hệ" in error.value.detail


def test_vuot_so_luong_toi_da_thi_tu_choi(db, catalog):
    mot = _tao(db, catalog, "QT", "Quy trình A")
    hai = _tao(db, catalog, "QT", "Quy trình B")
    guideline = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")

    link_service.add_link(db, guideline, RELATION_GUIDE, mot.id, "", ACTOR)
    with pytest.raises(HTTPException) as error:
        link_service.add_link(db, guideline, RELATION_GUIDE, hai.id, "", ACTOR)
    assert "tối đa" in error.value.detail


def test_tham_chieu_di_qua_duoc_ma_khong_can_quy_tac(db, catalog):
    """«Tham chiếu» là liên kết mềm — tài liệu khai "bất kỳ tham chiếu bất kỳ"."""
    mot = _tao(db, catalog, "QT", "Quy trình A")
    hai = _tao(db, catalog, "BM", "Biểu mẫu B")

    link = link_service.add_link(db, hai, RELATION_REFERENCE, mot.id, "", ACTOR)
    assert link.rule_id is None


# ── E05 · cấm vòng lặp ───────────────────────────────────────────────────────
def test_cam_tu_tro_vao_chinh_minh(db, catalog):
    guideline = _tao(db, catalog, "HDCV", "Hướng dẫn tự trỏ")
    with pytest.raises(HTTPException):
        link_service.add_link(db, guideline, RELATION_GUIDE, guideline.id, "", ACTOR)


def test_cam_vong_lap_hai_buoc(db, catalog):
    a = _tao(db, catalog, "HDCV", "Hướng dẫn A")
    b = _tao(db, catalog, "HDCV", "Hướng dẫn B")

    link_service.add_link(db, a, RELATION_GUIDE, b.id, "", ACTOR)
    with pytest.raises(HTTPException) as error:
        link_service.add_link(db, b, RELATION_GUIDE, a.id, "", ACTOR)
    assert "vòng lặp" in error.value.detail


def test_cam_vong_lap_ca_chuoi_dai(db, catalog):
    """A→B→C→A. Kiểm hai bước cho lọt vòng này, mà lọt là cây đệ quy vô hạn."""
    a = _tao(db, catalog, "HDCV", "Hướng dẫn A")
    b = _tao(db, catalog, "HDCV", "Hướng dẫn B")
    c = _tao(db, catalog, "HDCV", "Hướng dẫn C")

    link_service.add_link(db, a, RELATION_GUIDE, b.id, "", ACTOR)
    link_service.add_link(db, b, RELATION_GUIDE, c.id, "", ACTOR)

    with pytest.raises(HTTPException) as error:
        link_service.add_link(db, c, RELATION_GUIDE, a.id, "", ACTOR)
    assert "vòng lặp" in error.value.detail


def test_vong_lap_chi_xet_trong_cung_mot_loai_quan_he(db, catalog):
    """A hướng dẫn B, rồi B tham chiếu A — KHÔNG phải vòng lặp.

    Hai quan hệ khác nghĩa nhau; chặn cả hai là chặn nhầm việc bình thường.
    """
    procedure = _tao(db, catalog, "QT", "Quy trình A")
    guideline = _tao(db, catalog, "HDCV", "Hướng dẫn B")

    link_service.add_link(db, guideline, RELATION_GUIDE, procedure.id, "", ACTOR)
    link_service.add_link(db, procedure, RELATION_REFERENCE, guideline.id, "", ACTOR)


# ── E04 · chặn gửi duyệt khi thiếu quan hệ bắt buộc ──────────────────────────
def test_thieu_quan_he_bat_buoc_thi_khong_gui_duyet_duoc(db, catalog):
    guideline = _tao(db, catalog, "HDCV", "Hướng dẫn chưa trỏ vào đâu")

    missing = link_service.missing_required(db, guideline)
    assert len(missing) == 1 and "Hướng dẫn" in missing[0]

    with pytest.raises(HTTPException) as error:
        service.submit(db, guideline, ACTOR)
    assert "quan hệ bắt buộc" in error.value.detail


def test_khai_du_quan_he_thi_gui_duyet_duoc(db, catalog):
    procedure = _tao(db, catalog, "QT", "Quy trình mua hàng")
    guideline = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")
    link_service.add_link(db, guideline, RELATION_GUIDE, procedure.id, "", ACTOR)

    assert link_service.missing_required(db, guideline) == []
    service.submit(db, guideline, ACTOR)


def test_loai_khong_co_quy_tac_bat_buoc_thi_gui_thoai_mai(db, catalog):
    procedure = _tao(db, catalog, "QT", "Quy trình đứng một mình")
    assert link_service.missing_required(db, procedure) == []
    service.submit(db, procedure, ACTOR)


# ── E04b · cảnh báo TRƯỚC khi tạo: kho chưa có văn bản cha ───────────────────
def test_chua_co_van_ban_cha_thi_bao_thieu_tien_quyet(db, catalog):
    """Kho trống trơn: chọn loại HDCV là biết trước sẽ mắc kẹt lúc gửi duyệt."""
    missing = link_service.missing_prerequisites(db, catalog["HDCV"].id)

    assert len(missing) == 1
    assert missing[0]["target_type_name"] == "Quy trình"
    assert missing[0]["need"] == 1 and missing[0]["available"] == 0


def test_van_ban_cha_con_nham_thi_van_bao_thieu(db, catalog):
    """Bản nháp KHÔNG tính: lát nữa ô chọn quan hệ cũng không hiện nó ra.

    Đếm cả nháp thì cảnh báo im lặng đúng lúc cần nói — cha còn nằm trong ngăn
    kéo của ai đó, người soạn con vẫn không trỏ vào được.
    """
    _tao(db, catalog, "QT", "Quy trình còn nháp")

    missing = link_service.missing_prerequisites(db, catalog["HDCV"].id)
    assert len(missing) == 1 and missing[0]["available"] == 0


def test_co_van_ban_cha_con_hieu_luc_thi_khong_canh_bao(db, catalog):
    procedure = _tao(db, catalog, "QT", "Quy trình đã ban hành")
    service.submit(db, procedure, ACTOR)
    service.approve(db, procedure, ACTOR)

    assert link_service.missing_prerequisites(db, catalog["HDCV"].id) == []


def test_loai_khong_co_quy_tac_bat_buoc_thi_khong_canh_bao_gi(db, catalog):
    assert link_service.missing_prerequisites(db, catalog["QT"].id) == []


def test_quy_tac_tat_thi_khong_con_canh_bao(db, catalog):
    """Tắt quy tắc = từ nay không chặn gửi duyệt nữa, nên cũng thôi cảnh báo."""
    for rule in link_service.rules_for_type(db, catalog["BM"].id):
        rule.is_active = False
    db.commit()

    assert link_service.missing_prerequisites(db, catalog["BM"].id) == []


# ── E06 · cây tài liệu ───────────────────────────────────────────────────────
def test_cay_tai_lieu_hien_con_tro_vao_minh(db, catalog):
    """Mở một Quy trình thấy ngay Hướng dẫn và Biểu mẫu thuộc nó."""
    procedure = _tao(db, catalog, "QT", "Quy trình mua hàng")
    guideline = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")
    form = _tao(db, catalog, "BM", "Biểu mẫu đề nghị")
    link_service.add_link(db, guideline, RELATION_GUIDE, procedure.id, "", ACTOR)
    link_service.add_link(db, form, RELATION_BELONGS, procedure.id, "", ACTOR)

    cay = link_serializer.build_tree(db, procedure)

    ten_con = sorted(node["title"] for node in cay["children"])
    assert ten_con == ["Biểu mẫu đề nghị", "Hướng dẫn tạo phiếu"]
    assert all(node["relation_label"] for node in cay["children"])


def test_cay_khong_lap_vo_han_khi_hai_loai_quan_he_khep_vong(db, catalog):
    """A hướng dẫn B và B tham chiếu A đều hợp lệ, nhưng duyệt cây thì thành vòng."""
    procedure = _tao(db, catalog, "QT", "Quy trình A")
    guideline = _tao(db, catalog, "HDCV", "Hướng dẫn B")
    link_service.add_link(db, guideline, RELATION_GUIDE, procedure.id, "", ACTOR)
    link_service.add_link(db, procedure, RELATION_REFERENCE, guideline.id, "", ACTOR)

    cay = link_serializer.build_tree(db, procedure)
    assert len(cay["children"]) == 1


def test_doc_nguoc_quan_he_theo_phia_dang_xem(db, catalog):
    """Cùng một dòng dữ liệu, mở từ hai phía phải đọc ra hai câu khác nhau."""
    procedure = _tao(db, catalog, "QT", "Quy trình mua hàng")
    guideline = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")
    link = link_service.add_link(db, guideline, RELATION_GUIDE, procedure.id, "", ACTOR)

    tu_con = link_serializer.serialize_link(db, link, viewed_from=guideline.id)
    tu_cha = link_serializer.serialize_link(db, link, viewed_from=procedure.id)

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
    regulation = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(regulation)
    db.commit()
    db.add(DocTypeLinkRule(source_type_id=catalog["BM"].id, relation=RELATION_BELONGS,
                           target_type_id=regulation.id, is_required=False))
    db.commit()
    catalog["QC"] = regulation
    return catalog


def test_khai_sai_loai_dich_khong_qua_duoc_cong_bat_buoc(db, hai_dong_thuoc_ve):
    form = _tao(db, hai_dong_thuoc_ve, "BM", "Biểu mẫu đề nghị")
    regulation = _tao(db, hai_dong_thuoc_ve, "QC", "Quy chế lương")

    link_service.add_link(db, form, RELATION_BELONGS, regulation.id, "", ACTOR)

    #  Dòng bắt buộc đòi QUY TRÌNH — khai Quy chế không thay thế được.
    missing = link_service.missing_required(db, form)
    assert len(missing) == 1 and "Quy trình" in missing[0]

    with pytest.raises(HTTPException):
        service.submit(db, form, ACTOR)


def test_khai_dung_loai_dich_thi_qua_cong(db, hai_dong_thuoc_ve):
    form = _tao(db, hai_dong_thuoc_ve, "BM", "Biểu mẫu đề nghị")
    procedure = _tao(db, hai_dong_thuoc_ve, "QT", "Quy trình mua hàng")

    link_service.add_link(db, form, RELATION_BELONGS, procedure.id, "", ACTOR)

    assert link_service.missing_required(db, form) == []
    service.submit(db, form, ACTOR)


def test_so_luong_toi_da_dem_rieng_tung_dong_quy_tac(db, hai_dong_thuoc_ve):
    """Dòng QT tối đa 1 không được chặn dòng QC — hai bộ đếm độc lập."""
    for rule in link_service.rules_for_type(db, hai_dong_thuoc_ve["BM"].id):
        rule.max_count = 1
    db.commit()

    form = _tao(db, hai_dong_thuoc_ve, "BM", "Biểu mẫu đề nghị")
    procedure = _tao(db, hai_dong_thuoc_ve, "QT", "Quy trình mua hàng")
    regulation = _tao(db, hai_dong_thuoc_ve, "QC", "Quy chế lương")

    link_service.add_link(db, form, RELATION_BELONGS, procedure.id, "", ACTOR)
    #  Khai tiếp sang loại đích KHÁC phải được — trước đây bị chặn vì đếm gộp.
    link_service.add_link(db, form, RELATION_BELONGS, regulation.id, "", ACTOR)

    #  Nhưng thêm cái thứ hai CÙNG loại đích thì đúng là phải chặn.
    quy_trinh_2 = _tao(db, hai_dong_thuoc_ve, "QT", "Quy trình bán hàng")
    with pytest.raises(HTTPException) as error:
        link_service.add_link(db, form, RELATION_BELONGS, quy_trinh_2.id, "", ACTOR)
    assert "tối đa" in error.value.detail


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


def _new_version(db, doc):
    open_new_version(db, doc, VersionCreate(
        change_kind=CHANGE_MAJOR, change_summary="Sửa điều 5",
    ), ACTOR)
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)


def test_liet_ke_tac_dong_truoc_khi_bam_va_khong_doi_gi(db, catalog):
    """E07 — bảng tác động chỉ ĐỌC. Gọi xong dữ liệu phải y nguyên."""
    procedure = _ban_hanh(db, _tao(db, catalog, "QT", "Quy trình mua hàng"))
    guideline = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")
    link_service.add_link(db, guideline, RELATION_GUIDE, procedure.id, "", ACTOR)

    tac_dong = parent_change_service.impact_of(db, procedure, obsolete=False)

    assert [m["title"] for m in tac_dong] == ["Hướng dẫn tạo phiếu"]
    assert tac_dong[0]["action_label"]
    db.refresh(guideline)
    assert guideline.needs_review is False


def test_cha_len_phien_ban_moi_thi_con_bi_danh_dau(db, catalog):
    procedure = _ban_hanh(db, _tao(db, catalog, "QT", "Quy trình mua hàng"))
    guideline = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")
    link_service.add_link(db, guideline, RELATION_GUIDE, procedure.id, "", ACTOR)

    _new_version(db, procedure)

    db.refresh(guideline)
    assert guideline.needs_review is True
    assert "phiên bản 2.0" in guideline.needs_review_note


def test_quy_tac_khai_khong_lam_gi_thi_con_khong_bi_danh_dau(db, catalog):
    """Cột cấu hình phải thật sự điều khiển — không phải lúc nào cũng đánh dấu."""
    for rule in link_service.rules_for_type(db, catalog["HDCV"].id):
        rule.on_parent_new_version = NEW_VERSION_NOTHING
    db.commit()

    procedure = _ban_hanh(db, _tao(db, catalog, "QT", "Quy trình mua hàng"))
    guideline = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")
    link_service.add_link(db, guideline, RELATION_GUIDE, procedure.id, "", ACTOR)

    _new_version(db, procedure)

    db.refresh(guideline)
    assert guideline.needs_review is False


def test_bai_bo_cha_theo_cau_hinh_het_hieu_luc(db, catalog):
    for rule in link_service.rules_for_type(db, catalog["HDCV"].id):
        rule.on_parent_obsolete = OBSOLETE_EXPIRE
    db.commit()

    procedure = _ban_hanh(db, _tao(db, catalog, "QT", "Quy trình mua hàng"))
    guideline = _tao(db, catalog, "HDCV", "Hướng dẫn tạo phiếu")
    link_service.add_link(db, guideline, RELATION_GUIDE, procedure.id, "", ACTOR)
    _ban_hanh(db, guideline)

    service.revoke(db, procedure, "Thay bằng quy trình mới", ACTOR)

    db.refresh(guideline)
    assert guideline.status == STATUS_EXPIRED


def test_bai_bo_cha_muc_danh_dau_thi_con_van_con_hieu_luc(db, catalog):
    """Mức 2 chỉ đánh dấu: Biểu mẫu vẫn dùng được dù Quy trình cha đã bỏ."""
    procedure = _ban_hanh(db, _tao(db, catalog, "QT", "Quy trình mua hàng"))
    form = _tao(db, catalog, "BM", "Biểu mẫu đề nghị")
    link_service.add_link(db, form, RELATION_BELONGS, procedure.id, "", ACTOR)
    _ban_hanh(db, form)

    service.revoke(db, procedure, "Thay bằng quy trình mới", ACTOR)

    db.refresh(form)
    assert form.needs_review is True
    assert form.status != STATUS_EXPIRED


def test_bai_bo_cha_muc_khong_lam_gi_thi_con_khong_bi_dung(db, catalog):
    for rule in link_service.rules_for_type(db, catalog["BM"].id):
        rule.on_parent_obsolete = OBSOLETE_NOTHING
    db.commit()

    procedure = _ban_hanh(db, _tao(db, catalog, "QT", "Quy trình mua hàng"))
    form = _tao(db, catalog, "BM", "Biểu mẫu đề nghị")
    link_service.add_link(db, form, RELATION_BELONGS, procedure.id, "", ACTOR)
    _ban_hanh(db, form)

    service.revoke(db, procedure, "Thay bằng quy trình mới", ACTOR)

    db.refresh(form)
    assert form.needs_review is False
    assert form.status != STATUS_EXPIRED


# ── E08 · quan hệ NGƯỢC CHIỀU không phải quan hệ cha–con ─────────────────────
def test_thong_bao_bai_bo_KHONG_tu_danh_dau_chinh_minh(db, catalog):
    """Văn bản đi BÃI BỎ không phải là con của văn bản bị bãi bỏ.

    Lỗi dựng lại được trên dữ liệu thật 24/08/2026 (văn bản #368 «Thông báo bãi
    bỏ Văn bản nghỉ lễ 02/09» trên dev): ban hành thông báo bãi bỏ → nó bãi bỏ
    văn bản đích → E08 quét MỌI quan hệ trỏ vào văn bản đích, gặp luôn quan hệ
    *bãi bỏ* của chính thông báo đó → đánh dấu thông báo «Văn bản cha «…» đã bị
    bãi bỏ, rà lại đi». Nó vừa bãi bỏ cái đó xong.

    Và vì MỌI thông báo bãi bỏ đều có đúng quan hệ này nên đây là báo động sai
    CÓ HỆ THỐNG — thứ làm người dùng quen mắt với băng vàng rồi thôi không đọc.
    """
    from app.modules.doc_catalog.link_rule_model import RELATION_REVOKE
    from app.modules.document.model import STATUS_REVOKED

    #  Quan hệ «bãi bỏ» phải có dòng quy tắc thì mới khai được (E03).
    db.add(DocTypeLinkRule(source_type_id=catalog["QT"].id, relation=RELATION_REVOKE,
                           target_type_id=catalog["QT"].id, is_required=False))
    db.commit()

    revoked_docs = _ban_hanh(db, _tao(db, catalog, "QT", "Quy trình cũ"))
    thong_bao = _tao(db, catalog, "QT", "Thông báo bãi bỏ Quy trình cũ")
    link_service.add_link(db, thong_bao, RELATION_REVOKE, revoked_docs.id, "", ACTOR)
    _ban_hanh(db, thong_bao)

    db.refresh(revoked_docs)
    db.refresh(thong_bao)
    assert revoked_docs.status == STATUS_REVOKED, "Thông báo phải bãi bỏ được văn bản đích"
    assert thong_bao.needs_review is False, \
        "Văn bản ĐI bãi bỏ không được tự treo băng «cha đã bị bãi bỏ» lên chính nó"
    assert thong_bao.needs_review_note == ""


def test_van_ban_THAY_THE_cung_khong_bi_danh_dau(db, catalog):
    """«A thay thế B» — A là bản kế nhiệm, không phải kẻ phụ thuộc vào B."""
    from app.modules.doc_catalog.link_rule_model import RELATION_REPLACE
    from app.modules.document.model import STATUS_REPLACED

    db.add(DocTypeLinkRule(source_type_id=catalog["QT"].id, relation=RELATION_REPLACE,
                           target_type_id=catalog["QT"].id, is_required=False))
    db.commit()

    ban_cu = _ban_hanh(db, _tao(db, catalog, "QT", "Quy trình bản cũ"))
    ban_moi = _tao(db, catalog, "QT", "Quy trình bản mới")
    link_service.add_link(db, ban_moi, RELATION_REPLACE, ban_cu.id, "", ACTOR)
    _ban_hanh(db, ban_moi)

    db.refresh(ban_cu)
    db.refresh(ban_moi)
    assert ban_cu.status == STATUS_REPLACED
    assert ban_moi.needs_review is False


def test_con_THAT_SU_thi_van_bi_danh_dau_nhu_cu(db, catalog):
    """Chốt chặn đối chứng: lọc bớt hai quan hệ ngược chiều KHÔNG được làm hỏng
    đường chính — biểu mẫu «thuộc về» quy trình vẫn phải bị đánh dấu khi cha bãi bỏ."""
    procedure = _ban_hanh(db, _tao(db, catalog, "QT", "Quy trình còn con"))
    form = _tao(db, catalog, "BM", "Biểu mẫu của quy trình")
    link_service.add_link(db, form, RELATION_BELONGS, procedure.id, "", ACTOR)
    _ban_hanh(db, form)

    service.revoke(db, procedure, "Bỏ quy trình", ACTOR)

    db.refresh(form)
    assert form.needs_review is True, "Con thật sự vẫn phải được nhắc rà lại"
    assert "đã bị bãi bỏ" in form.needs_review_note
