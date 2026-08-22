"""B-03 — `tab_employee.status` + `tab_supplier.legal_type` chuyển sang MÃ tiếng Anh.

Đợt thứ ba của kế hoạch đổ bê tông nền v2 (`doc/erp/15-do-be-tong-nen-v2.md` §3). Hai cột này
"rẻ" hơn B-02: không cột nào nằm trong máy trạng thái, không cột nào bị so sánh chuỗi trần ở
tầng nghiệp vụ. Cái đắt nằm ở hai chỗ khác, và đó là chỗ bộ test này nhắm vào:

  1. Bộ giá trị KHÔNG suy ra được từ dữ liệu. Prod chỉ có 3/4 trạng thái nhân sự và 1/4 loại
     hình NCC. Lấy bộ mã theo dữ liệu là lần đầu có người chọn "Cộng tác viên" sẽ ăn 422.
  2. Nhân sự có đường CSV hai chiều mà người dùng mở bằng Excel. Đổ mã ra tệp xuất, hoặc chặn
     nhãn tiếng Việt ở tệp nhập, là hỏng một quy trình đang chạy thật.
"""
import importlib.util
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.status_codes import EMPLOYEE_STATUS, SUPPLIER_LEGAL_TYPE
from app.modules.employee.controller import _ma_trang_thai
from app.modules.employee.model import Employee
from app.modules.employee.schema import EmployeeCreate, EmployeeOut, EmployeeUpdate
from app.modules.supplier.model import Supplier
from app.modules.supplier.schema import SupplierCreate, SupplierOut, SupplierUpdate

_NHAN_CU_NHAN_SU = ["Chính thức", "Cộng tác viên", "Nghỉ thai sản", "Nghỉ việc"]
_NHAN_CU_NCC = ["Công ty", "Cá nhân", "Hợp danh", "Hộ kinh doanh"]


# ── Bộ mã ───────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("bo", [EMPLOYEE_STATUS, SUPPLIER_LEGAL_TYPE])
def test_ma_la_ascii_thuong_va_khong_trung(bo):
    """Cột lưu MÃ. Lọt tiếng Việt vào đây là quay lại đúng cái mớ vừa dọn."""
    for c in bo.codes:
        assert c.value.isascii() and c.value.islower(), c
        assert c.label, c
    assert len(set(bo.values)) == len(bo.values)


def test_bo_ma_khai_du_ca_gia_tri_chua_dong_nao_dung():
    """Đếm ngày 22/08/2026: prod không có dòng "Cộng tác viên" nào, mọi môi trường chỉ có
    "Công ty" trong loại hình NCC. Nhưng ô chọn của cả hai bản giao diện mời đủ 4 — cắt bộ
    mã theo dữ liệu đang có là lần đầu có người chọn giá trị còn lại sẽ ăn 422."""
    assert EMPLOYEE_STATUS.values == {"official", "collaborator", "maternity_leave", "resigned"}
    assert SUPPLIER_LEGAL_TYPE.values == {"company", "individual", "partnership", "household"}


def test_khong_bo_nao_khai_thu_tu_hay_trang_thai_ket():
    """Nhân sự không tự nhảy trạng thái, nghỉ việc rồi vẫn vào lại được, và loại hình pháp
    lý thì không phải tiến trình. Khai `sort_order`/`is_terminal` ở đây là bịa ra một chuỗi
    không có thật, rồi có người dựa vào nó mà chặn thao tác."""
    for bo in (EMPLOYEE_STATUS, SUPPLIER_LEGAL_TYPE):
        assert all(c.sort_order == 0 for c in bo.codes)
        assert not any(c.is_terminal or c.is_exception for c in bo.codes)
        # sort_order = 0 hết -> `ordered_values` giữ nguyên thứ tự khai; thứ tự đó là thứ tự
        # vẽ vòng tròn ở Tổng quan Nhân sự nên không được xáo.
        assert bo.ordered_values == tuple(c.value for c in bo.codes)


# ── Tầng ghi ────────────────────────────────────────────────────────────────────
def test_chi_nhan_ma_trong_bo():
    for ma in EMPLOYEE_STATUS.values:
        assert EmployeeCreate(full_name="A", status=ma).status == ma
    for ma in SUPPLIER_LEGAL_TYPE.values:
        assert SupplierCreate(name="A", legal_type=ma).legal_type == ma


def test_mac_dinh_la_ma_chu_khong_phai_nhan():
    assert EmployeeCreate(full_name="A").status == "official"
    assert SupplierCreate(name="A").legal_type == ""     # NCC: rỗng = chưa chọn


@pytest.mark.parametrize("xau", _NHAN_CU_NHAN_SU)
def test_nhan_nhan_su_cu_bi_chan_ca_luc_tao_lan_luc_sua(xau):
    """Chặn ở CẢ HAI schema. Chỉ chặn `Create` thì màn sửa vẫn ghi chữ tự do vào lại."""
    with pytest.raises(ValidationError):
        EmployeeCreate(full_name="A", status=xau)
    with pytest.raises(ValidationError):
        EmployeeUpdate(status=xau)


@pytest.mark.parametrize("xau", _NHAN_CU_NCC)
def test_nhan_ncc_cu_bi_chan_ca_luc_tao_lan_luc_sua(xau):
    with pytest.raises(ValidationError):
        SupplierCreate(name="A", legal_type=xau)
    with pytest.raises(ValidationError):
        SupplierUpdate(legal_type=xau)


def test_trang_thai_nhan_su_khong_duoc_de_rong():
    """KHÁC `legal_type`: nhân sự luôn phải có tình trạng làm việc, rỗng không mang nghĩa gì.

    Chỗ này giữ một ca thật: hồ sơ mang giá trị cũ ngoài bộ mã thì ô chọn ở giao diện không
    khớp mục nào; nếu để rỗng lọt qua thì bấm lưu là ghi đè trạng thái thật thành rỗng mà
    không ai biết. 422 ở đây buộc người dùng chọn lại."""
    with pytest.raises(ValidationError):
        EmployeeCreate(full_name="A", status="")
    with pytest.raises(ValidationError):
        EmployeeUpdate(status="")


def test_ncc_de_rong_van_hop_le():
    """Rỗng = chưa chọn loại hình, và đó là tình trạng của gần như toàn bộ dữ liệu thật
    (159/161 dòng prod). Chặn rỗng là mọi lần lưu NCC cũ đều 422."""
    assert SupplierCreate(name="A", legal_type="").legal_type == ""
    assert SupplierUpdate(legal_type="").legal_type == ""


def test_khong_tu_dich_nhan_thanh_ma_o_tang_api():
    """Cố ý KHÔNG nhận "Chính thức" rồi âm thầm đổi thành `official`: dịch hộ thì bản giao
    diện chưa vá vẫn chạy được, và sẽ không ai vá nữa cho tới lúc nó hỏng vì lý do khác.
    (Đường CSV là ngoại lệ có chủ đích — xem nhóm test bên dưới.)"""
    with pytest.raises(ValidationError):
        EmployeeCreate(full_name="A", status="Chính thức")


# ── Tầng đọc ────────────────────────────────────────────────────────────────────
def _nhan_su(**kw) -> Employee:
    """Dựng `Employee` KHÔNG qua CSDL. Giá trị mặc định của cột chỉ chạy lúc INSERT, nên
    ở đây phải điền tay mấy cột `EmployeeOut` bắt buộc, nếu không nổ vì lý do chẳng liên
    quan gì tới B-03."""
    return Employee(email="", phone="", company_id=0, department_id=0, position="",
                    role_name="", is_active=True, **kw)


def _ncc(**kw) -> Supplier:
    """Cùng lý do như `_nhan_su`."""
    return Supplier(tax_code="", address="", supplier_type="goods", contact_person="",
                    phone="", payment_terms="", bank_account="", bank_name="",
                    bank_account_name="", vat=0.08, is_active=True, **kw)


def test_gui_kem_nhan_de_giao_dien_khong_phai_khai_lai_bang_nhan():
    e = EmployeeOut.model_validate(
        _nhan_su(id=1, code="NSU0001", full_name="A", status="maternity_leave"))
    assert e.status == "maternity_leave" and e.status_label == "Nghỉ thai sản"

    s = SupplierOut.model_validate(_ncc(id=1, code="NCC001", name="Cty A", legal_type="company"))
    assert s.legal_type == "company" and s.legal_type_label == "Công ty"


def test_ma_la_khong_lam_no_tang_doc_chi_la_khong_co_nhan():
    """Dòng chưa chạy migration (hoặc do nơi khác ghi vào) vẫn phải đọc được — tầng đọc
    KHÔNG có validator, chỉ tầng ghi mới chặn."""
    e = EmployeeOut.model_validate(
        _nhan_su(id=2, code="NSU0002", full_name="B", status="Chính thức"))
    assert e.status == "Chính thức"      # giữ nguyên, không nuốt mất
    assert e.status_label == ""          # không nhận ra -> không có nhãn

    s = SupplierOut.model_validate(_ncc(id=2, code="NCC002", name="B", legal_type=""))
    assert s.legal_type == "" and s.legal_type_label == ""


# ── Đường CSV của Nhân sự ───────────────────────────────────────────────────────
def test_csv_nhap_hieu_ca_nhan_lan_ma():
    """Tệp CSV do người dùng gõ trong Excel, không phải giao diện mình viết ra. Bắt họ gõ
    `maternity_leave` là vô lý, nên ĐÂY là chỗ được phép dịch nhãn thành mã."""
    assert _ma_trang_thai("Chính thức") == "official"
    assert _ma_trang_thai("official") == "official"
    assert _ma_trang_thai("  NGHỈ   thai sản ") == "maternity_leave"
    assert _ma_trang_thai("nghi viec") == "resigned"          # bản gõ không dấu
    assert _ma_trang_thai("Cộng tác viên") == "collaborator"


def test_csv_nhap_khong_doan_bua():
    """Không nhận ra thì trả rỗng để nơi gọi dừng cả lần nhập và nói rõ dòng nào. Đoán bừa
    thành "Chính thức" ở đây là ghi đè trạng thái thật của một con người."""
    assert _ma_trang_thai("Đang thử việc") == ""
    assert _ma_trang_thai("") == ""
    assert _ma_trang_thai(None) == ""


def test_csv_xuat_ra_nhan_chu_khong_ra_ma():
    """Cột "Trạng thái NS" của tệp xuất đọc `status_label`. Đổ `official` ra đó là biến một
    tệp đang đọc được thành tệp phải tra cứu — mà tệp đó còn được sửa rồi nhập ngược lại.

    Bảng cột nằm trong thân hàm endpoint nên không gọi tới được nếu không dựng cả request;
    đọc mã nguồn là cách rẻ nhất để chặn đúng cái hồi quy này (có người đổi lại thành
    `"status"` cho "gọn")."""
    import inspect

    from app.modules.employee.controller import export_employees_csv

    src = inspect.getsource(export_employees_csv)
    assert '"status_label": "Trạng thái NS"' in src
    assert '"status":' not in src

    # `export_csv_response` lấy giá trị bằng `getattr(item, field, "")`, nên cột này sống
    # được là nhờ property trên model chứ không phải nhờ schema.
    assert Employee(id=3, code="NSU0003", full_name="C", status="resigned").status_label == "Nghỉ việc"


# ── Migration đổi dữ liệu ───────────────────────────────────────────────────────
_TEN_MIG = "d2e5b8c04f71_b03_chuan_hoa_employee_status_supplier_legal_type.py"


def _nap_migration():
    duong_dan = Path(__file__).resolve().parents[2] / "migrations" / "versions" / _TEN_MIG
    if not duong_dan.exists():   # chạy trong container: /app/test/backend + /app/migrations
        duong_dan = Path("/app/migrations/versions") / _TEN_MIG
    spec = importlib.util.spec_from_file_location("mig_b03", duong_dan)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_migration_khop_theo_dang_chuan_hoa_chu_khong_khop_tuyet_doi():
    """Khớp tuyệt đối thì một dấu cách thừa hay một chữ hoa lệch là lọt lưới, và dòng đó
    nằm im trong CSDL với giá trị tiếng Việt cho tới lúc có người lọc không ra."""
    mig = _nap_migration()
    doi_ns = lambda s: mig._MAP_EMPLOYEE_STATUS.get(mig._norm(s))   # noqa: E731
    doi_lt = lambda s: mig._MAP_LEGAL_TYPE.get(mig._norm(s))        # noqa: E731

    assert doi_ns("Chính thức") == "official"
    assert doi_ns("  CHÍNH   thức ") == "official"
    assert doi_ns("nghi thai san") == "maternity_leave"
    assert doi_lt("Hộ kinh doanh") == "household"
    assert doi_lt("ho kinh doanh") == "household"
    assert doi_ns("Thử việc") is None       # không đoán bừa, giữ nguyên + in log
    assert doi_lt("Hợp tác xã") is None


def test_chieu_xuong_cua_migration_khop_nhan_chuan_dang_dung():
    """Bảng nhãn trong migration là bản CHÉP TAY của `status_codes.py` — migration không
    được import mã ứng dụng, vì mã đổi thì migration cũ vẫn phải chạy y như lúc viết.
    Lệch nhau là `downgrade()` ghi ra nhãn khác với nhãn giao diện đang hiện."""
    mig = _nap_migration()
    assert mig._LABEL_EMPLOYEE_STATUS == EMPLOYEE_STATUS.labels
    assert mig._LABEL_LEGAL_TYPE == SUPPLIER_LEGAL_TYPE.labels


def test_chay_xuoi_nguoc_xuoi_tra_ve_dung_tung_ky_tu(db):
    """QĐ-12 cho phép ĐỔI TẠI CHỖ (không thêm cột, không ghi hai nơi) với điều kiện
    `downgrade()` khôi phục byte-exact. Đây là chỗ kiểm điều kiện đó."""
    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    mig = _nap_migration()
    db.add_all([
        Employee(code="NS01", full_name="A", status="Chính thức"),
        Employee(code="NS02", full_name="B", status="Nghỉ thai sản"),
        Employee(code="NS03", full_name="C", status=""),            # rỗng: để nguyên hai chiều
        Employee(code="NS04", full_name="D", status="Thử việc"),    # không nhận ra
        Supplier(code="NCC01", name="Cty A", legal_type="Công ty"),
        Supplier(code="NCC02", name="Cty B", legal_type=""),
        Supplier(code="NCC03", name="Cty C", legal_type="Hợp tác xã"),
    ])
    db.commit()

    def doc():
        return (
            {e.code: e.status for e in db.query(Employee).order_by(Employee.code).all()},
            {s.code: s.legal_type for s in db.query(Supplier).order_by(Supplier.code).all()},
        )

    ban_dau = doc()
    conn = db.connection()
    ctx = MigrationContext.configure(conn)

    with Operations.context(ctx):
        mig.upgrade()
    db.expire_all()
    sau_len = doc()
    assert sau_len[0] == {"NS01": "official", "NS02": "maternity_leave",
                          "NS03": "", "NS04": "Thử việc"}
    # Giá trị không nhận ra thì GIỮ NGUYÊN — không đoán bừa trên dữ liệu thật.
    assert sau_len[1] == {"NCC01": "company", "NCC02": "", "NCC03": "Hợp tác xã"}

    with Operations.context(ctx):
        mig.downgrade()
    db.expire_all()
    assert doc() == ban_dau

    with Operations.context(ctx):
        mig.upgrade()
    db.expire_all()
    assert doc() == sau_len
