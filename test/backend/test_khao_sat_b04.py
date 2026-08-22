"""B-04 — `tab_survey.approve_status` chuyển sang MÃ tiếng Anh.

Đợt thứ tư của kế hoạch đổ bê tông nền v2 (`doc/erp/15-do-be-tong-nen-v2.md` §3). Cột này
KHÔNG giống ba đợt trước: người dùng không nhập nó, không schema đầu vào nào có nó, và
`frontend/` không hề đọc nó — chỉ `survey/service.set_status()` ghi vào. Nghĩa là mọi rủi ro
của đợt này dồn vào bốn chỗ, và đó là bốn nhóm test dưới đây:

  1. Nó KHÔNG phải bản sao của `status`. `set_status` chỉ ghi ở hai nhánh duyệt/không duyệt,
     nên phiếu duyệt xong rồi bị hủy vẫn giữ `approved`. Ai "dọn" bằng cách suy lại từ
     `status` là xóa mất lịch sử quyết định duyệt.
  2. Chuỗi rỗng ở cột này CÓ NGHĨA (chưa xét duyệt), khác B-02/B-03 nơi rỗng là "chưa chọn".
     Vì thế migration phải đổi cả chuỗi rỗng, và bảng nhãn chiều xuống cố ý lệch bộ mã đúng
     một dòng.
  3. Nhãn đi ra API bằng property, mà `_dict()` của controller chỉ quét cột thật — quên gắn
     tay ở `_survey_dict()` thì cột hiện `approved` giữa màn tiếng Việt mà không lỗi gì cả.
  4. Migration chạy theo lô. Lô sai cận là bỏ sót dòng một cách im lặng.
"""
import importlib.util
import inspect
from pathlib import Path

import pytest

from app.core.status_codes import SURVEY_APPROVE_STATUS
from app.modules.survey import controller as sv_ctrl
from app.modules.survey import service as sv_svc
from app.modules.survey.model import Survey


# ── Bộ mã ───────────────────────────────────────────────────────────────────────
def test_ma_la_ascii_thuong_va_khong_trung():
    """Cột lưu MÃ. Lọt tiếng Việt vào đây là quay lại đúng cái mớ vừa dọn."""
    for c in SURVEY_APPROVE_STATUS.codes:
        assert c.value.isascii() and c.value.islower(), c
        assert c.label, c
    assert len(set(SURVEY_APPROVE_STATUS.values)) == len(SURVEY_APPROVE_STATUS.values)


def test_chua_xet_duyet_la_mot_ma_co_ten_chu_khong_phai_chuoi_rong():
    """Rỗng ở cột này KHÔNG phải dữ liệu thiếu — nó là "chưa có quyết định duyệt" (phiếu nháp
    hoặc vừa gửi duyệt). Để nó lẫn với `""`/`NULL` thì không đếm được, không lọc được, và
    người đọc báo cáo không phân biệt nổi với dòng hỏng."""
    assert SURVEY_APPROVE_STATUS.values == {"pending", "approved", "rejected"}
    assert "" not in SURVEY_APPROVE_STATUS.values


def test_nhan_cua_pending_khong_duoc_trung_voi_bo_cap_dong():
    """"Chờ duyệt" là một giá trị của `line_approve` — cột duyệt cấp DÒNG, đứng ngay cạnh cột
    này trên cùng một màn hình. Đặt trùng chữ là người đọc báo cáo hiểu nhầm ngay, mà không
    có gì báo lỗi."""
    assert SURVEY_APPROVE_STATUS.labels["pending"] == "Chưa xét duyệt"
    assert SURVEY_APPROVE_STATUS.labels["pending"] != "Chờ duyệt"


def test_khong_khai_thu_tu_hay_trang_thai_ket():
    """Phiếu bị "Không duyệt" vẫn sửa rồi gửi duyệt lại được — không có chuỗi một chiều nào
    để mà khai. Khai bừa `sort_order`/`is_terminal` là bịa ra một luật rồi sẽ có người dựa
    vào nó mà chặn thao tác."""
    assert all(c.sort_order == 0 for c in SURVEY_APPROVE_STATUS.codes)
    assert not any(c.is_terminal or c.is_exception for c in SURVEY_APPROVE_STATUS.codes)


# ── Tầng ghi: không ai nhập, chỉ máy trạng thái ghi ─────────────────────────────
def test_khong_schema_dau_vao_nao_nhan_approve_status():
    """Cột này do backend suy ra. Mở nó ra cho client gửi lên là mở luôn đường ghi chữ tự do
    trở lại — và lúc đó sẽ chẳng có validator nào chặn vì đợt này không viết validator (cố ý,
    xem `doc/erp/15` §3 B-04)."""
    from app.modules.survey import schema as sv_schema

    for ten in ("SurveyCreate", "SurveyUpdate", "SupplierSurveyCreate", "ProductSurveyCreate",
                "SupplierSurveyUpdate", "ProductSurveyUpdate"):
        assert "approve_status" not in getattr(sv_schema, ten).model_fields, ten


def test_phieu_moi_mac_dinh_la_chua_xet_duyet(db):
    """Mặc định của cột là `pending` chứ không còn là chuỗi rỗng."""
    s = Survey(code="KS90001", survey_type="combined")
    db.add(s)
    db.commit()
    db.refresh(s)
    assert s.approve_status == "pending"


def test_duyet_va_khong_duyet_ghi_ma(db):
    for tt, mong_doi in (("approved", "approved"), ("rejected", "rejected")):
        s = Survey(code=f"KS9{tt[:4]}", survey_type="combined", status="draft")
        db.add(s)
        db.commit()
        sv_svc.set_status(db, s.id, tt, user_id=1)
        db.refresh(s)
        assert s.approve_status == mong_doi


def test_huy_sau_khi_duyet_van_giu_quyet_dinh_duyet(db):
    """`approve_status` nhớ QUYẾT ĐỊNH duyệt gần nhất, `status` nhớ phiếu đang ở đâu. Hai
    khái niệm khác nhau nên cố ý KHÔNG gộp: phiếu hủy rồi vẫn phải trả lời được câu "phiếu
    này đã từng được duyệt chưa"."""
    s = Survey(code="KS90002", survey_type="combined", status="draft")
    db.add(s)
    db.commit()

    sv_svc.set_status(db, s.id, "approved", user_id=1)
    sv_svc.set_status(db, s.id, "cancelled", user_id=1)
    db.refresh(s)

    assert s.status == "cancelled"
    assert s.approve_status == "approved"


def test_cac_trang_thai_khac_khong_dung_toi_cot_nay(db):
    """Gửi duyệt / trả lại nháp không phải là quyết định duyệt."""
    s = Survey(code="KS90003", survey_type="combined", status="draft")
    db.add(s)
    db.commit()
    for tt in ("submitted", "draft"):
        sv_svc.set_status(db, s.id, tt, user_id=1)
        db.refresh(s)
        assert s.approve_status == "pending"


def test_nhan_ban_phieu_tra_ve_chua_xet_duyet(db):
    """Phiếu nhân bản là phiếu MỚI, chưa ai duyệt. Nó ăn theo `HEADER_FIELDS` nên chỉ cần lỡ
    thêm `approve_status` vào danh sách đó là bản sao thừa hưởng luôn dấu đã duyệt."""
    assert "approve_status" not in sv_svc.HEADER_FIELDS

    goc = Survey(code="KS90004", survey_type="combined", status="approved",
                 approve_status="approved")
    db.add(goc)
    db.commit()

    ban_sao = sv_svc.copy_survey(db, goc.id, user_id=1)
    assert ban_sao.approve_status == "pending"


# ── Tầng đọc: nhãn phải có ở CẢ danh sách lẫn chi tiết ──────────────────────────
def test_nhan_di_kem_ma_trong_ban_ghi_tra_ve():
    s = Survey(id=1, code="KS90005", survey_type="combined", approve_status="rejected")
    d = sv_ctrl._survey_dict(s)
    assert d["approve_status"] == "rejected"
    assert d["approve_status_label"] == "Không duyệt"


def test_ma_la_khong_lam_no_tang_doc_chi_la_khong_co_nhan():
    """Dòng chưa chạy migration vẫn phải đọc được. Trả rỗng chứ không trả lại chính mã: nhìn
    dữ liệu là biết ngay dòng nào còn sót."""
    s = Survey(id=2, code="KS90006", survey_type="combined", approve_status="Duyệt")
    assert s.approve_status_label == ""
    assert sv_ctrl._survey_dict(s)["approve_status"] == "Duyệt"   # giữ nguyên, không nuốt mất


def test_danh_sach_cung_gan_nhan_chu_khong_chi_chi_tiet():
    """`_dict()` chỉ quét `mapper.column_attrs` nên KHÔNG thấy property. Dùng `_dict` cho màn
    danh sách thì cột trạng thái duyệt hiện `approved` giữa bảng tiếng Việt — không lỗi, không
    ai để ý, tới lúc khách nhìn thấy mới biết."""
    src = inspect.getsource(sv_ctrl.list_surveys)
    assert "_survey_dict(" in src


# ── Migration đổi dữ liệu ───────────────────────────────────────────────────────
_TEN_MIG = "e7b3f9a15c28_b04_chuan_hoa_survey_approve_status.py"


def _nap_migration():
    duong_dan = Path(__file__).resolve().parents[2] / "migrations" / "versions" / _TEN_MIG
    if not duong_dan.exists():   # chạy trong container: /app/test/backend + /app/migrations
        duong_dan = Path("/app/migrations/versions") / _TEN_MIG
    spec = importlib.util.spec_from_file_location("mig_b04", duong_dan)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_khop_theo_dang_chuan_hoa_chu_khong_khop_tuyet_doi():
    """Khớp tuyệt đối thì một dấu cách thừa hay một chữ hoa lệch là lọt lưới, và dòng đó nằm
    im trong CSDL với giá trị tiếng Việt cho tới lúc có người lọc không ra."""
    mig = _nap_migration()
    doi = lambda s: mig._MAP.get(mig._norm(s))   # noqa: E731

    assert doi("Duyệt") == "approved"
    assert doi("  DUYỆT ") == "approved"
    assert doi("duyet") == "approved"            # bản gõ không dấu
    assert doi("Không duyệt") == "rejected"
    assert doi("khong  duyet") == "rejected"
    assert doi("Chờ duyệt") is None              # không đoán bừa, giữ nguyên + in log


def test_chuoi_rong_cung_phai_doi_khac_hai_dot_truoc(db):
    """B-02/B-03 để chuỗi rỗng nguyên cả hai chiều vì ở đó rỗng = "chưa chọn". Ở đây rỗng có
    nghĩa riêng nên phải thành `pending`. Chép nhầm khuôn cũ (lọc `WHERE cot <> ''` như hai
    migration trước) là 2 dòng prod / 27 dòng dev nằm lại với chuỗi rỗng — đúng cái mà đợt
    này định dọn. Bảng dưới đây CHỈ có dòng rỗng nên nếu bộ lọc đó quay lại thì migration
    chạy xong mà không đổi gì cả."""
    mig = _nap_migration()
    assert mig._MAP[""] == "pending"

    db.add(Survey(code="KR001", survey_type="combined", approve_status=""))
    db.commit()
    _dung_migration(db, mig, "upgrade")
    assert _doc(db) == {"KR001": "pending"}


def test_bang_nhan_chieu_xuong_khop_bo_ma_tru_dung_dong_pending():
    """Bảng nhãn trong migration là bản CHÉP TAY của `status_codes.py` — migration không được
    import mã ứng dụng, vì mã đổi thì migration cũ vẫn phải chạy y như lúc viết.

    Lệch đúng MỘT dòng và là cố ý: `downgrade()` phải trả về ĐÚNG THỨ CSDL đang có trước khi
    chạy, mà thứ đó là chuỗi rỗng, không phải chữ "Chưa xét duyệt" (chữ ấy chưa từng nằm
    trong CSDL bao giờ)."""
    mig = _nap_migration()
    assert mig._LABEL["pending"] == ""
    assert {k: v for k, v in mig._LABEL.items() if k != "pending"} == {
        k: v for k, v in SURVEY_APPROVE_STATUS.labels.items() if k != "pending"}


def _doc(db) -> dict:
    return {s.code: s.approve_status
            for s in db.query(Survey).order_by(Survey.code).all()}


def _dung_migration(db, mig, chieu: str) -> None:
    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    ctx = MigrationContext.configure(db.connection())
    with Operations.context(ctx):
        getattr(mig, chieu)()
    db.expire_all()


def test_chay_xuoi_nguoc_xuoi_tra_ve_dung_tung_ky_tu(db):
    """QĐ-12 cho phép ĐỔI TẠI CHỖ (không thêm cột, không ghi hai nơi) với điều kiện
    `downgrade()` khôi phục byte-exact. Đây là chỗ kiểm điều kiện đó."""
    mig = _nap_migration()
    db.add_all([
        Survey(code="KS01", survey_type="combined", approve_status="Duyệt"),
        Survey(code="KS02", survey_type="combined", approve_status="Không duyệt"),
        Survey(code="KS03", survey_type="combined", approve_status=""),
        Survey(code="KS04", survey_type="combined", approve_status="Chờ duyệt"),  # không nhận ra
    ])
    db.commit()

    ban_dau = _doc(db)
    _dung_migration(db, mig, "upgrade")
    sau_len = _doc(db)
    assert sau_len == {"KS01": "approved", "KS02": "rejected",
                       "KS03": "pending", "KS04": "Chờ duyệt"}

    _dung_migration(db, mig, "downgrade")
    assert _doc(db) == ban_dau

    _dung_migration(db, mig, "upgrade")
    assert _doc(db) == sau_len


def test_chay_theo_lo_khong_bo_sot_dong_nao(db, monkeypatch):
    """Cắt lô sai cận là bỏ sót dòng một cách im lặng — không lỗi, không log, chỉ là vài dòng
    còn tiếng Việt. Ép lô xuống 2 để bắt vòng lặp chạy nhiều vòng với ít dữ liệu; id các dòng
    cố ý KHÔNG liền nhau để mốc MIN/MAX không trùng số dòng."""
    mig = _nap_migration()
    monkeypatch.setattr(mig, "CO_LO", 2)

    db.add_all([Survey(id=i, code=f"KL{i:03d}", survey_type="combined",
                       approve_status="Duyệt") for i in (1, 2, 3, 50, 51, 90, 91)])
    db.add(Survey(id=95, code="KL095", survey_type="combined", approve_status=""))
    db.commit()

    _dung_migration(db, mig, "upgrade")
    con_sot = db.query(Survey).filter(Survey.approve_status.notin_(
        SURVEY_APPROVE_STATUS.values)).all()
    assert con_sot == []
    assert db.query(Survey).filter(Survey.approve_status == "approved").count() == 7
    assert db.query(Survey).filter(Survey.approve_status == "pending").count() == 1


@pytest.mark.parametrize("chieu", ["upgrade", "downgrade"])
def test_bang_rong_khong_no(db, chieu):
    """Môi trường mới dựng thì `tab_survey` rỗng; `MIN(id)` trả `NULL` và vòng lô không được
    lấy `NULL` ra mà cộng."""
    _dung_migration(db, _nap_migration(), chieu)
