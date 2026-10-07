"""DANH MỤC BIẾN dùng trong mẫu HĐLĐ (.docx) — nguồn DUY NHẤT.

Người soạn mẫu gõ `{{ ho_ten }}` trong Word. Chỉ biến có trong danh mục này được phép:
biến lạ sẽ render ra RỖNG IM LẶNG nếu cho qua, nên `docx_engine` chặn lúc tải mẫu lên.
FE đọc danh mục qua API (phase 03) để hiện bảng hướng dẫn. Tên biến: ASCII snake_case.
Giá trị luôn là CHUỖI đã định dạng sẵn (ngày dd/mm/yyyy, tiền 15.000.000) — người soạn
mẫu không phải biết filter Jinja.
"""
from dataclasses import dataclass

G_EMP, G_CO, G_CT, G_PAY, G_SYS = "Người lao động", "Pháp nhân (bên A)", "Hợp đồng", "Lương", "Hệ thống"


@dataclass(frozen=True)
class Placeholder:
    key: str
    label: str
    group: str
    example: str


def _p(group: str, rows: list[tuple[str, str, str]]) -> list[Placeholder]:
    return [Placeholder(k, label, group, ex) for k, label, ex in rows]


PLACEHOLDERS: tuple[Placeholder, ...] = tuple(
    _p(G_EMP, [
        ("ho_ten", "Họ và tên", "Nguyễn Văn An"),
        ("ma_nhan_vien", "Mã nhân viên", "NV001"),
        ("gioi_tinh", "Giới tính", "Nam"),
        ("ngay_sinh", "Ngày sinh", "01/02/1990"),
        ("noi_sinh", "Nơi sinh", "Hà Nội"),
        ("dan_toc", "Dân tộc", "Kinh"),
        ("so_cccd", "Số CCCD", "001090000001"),
        ("ngay_cap_cccd", "Ngày cấp CCCD", "15/03/2021"),
        ("noi_cap_cccd", "Nơi cấp CCCD", "Cục CSQLHC về TTXH"),
        ("dia_chi_thuong_tru", "Địa chỉ thường trú", "12 Lê Lợi, Hoàn Kiếm, Hà Nội"),
        ("dia_chi_hien_tai", "Địa chỉ hiện tại", "34 Trần Phú, Hà Đông, Hà Nội"),
        ("so_dien_thoai", "Số điện thoại", "0900000000"),
        ("email", "Email", "an.nguyen@example.com"),
        ("ma_so_thue", "Mã số thuế cá nhân", "8000000001"),
        ("so_bhxh", "Số sổ BHXH", "0100000001"),
        ("so_tai_khoan", "Số tài khoản", "0123456789"),
        ("ten_ngan_hang", "Ngân hàng", "Vietcombank"),
        ("chi_nhanh_ngan_hang", "Chi nhánh ngân hàng", "Hoàn Kiếm"),
        ("trinh_do", "Trình độ", "Đại học"),
        ("chuyen_nganh", "Chuyên ngành", "Quản trị kinh doanh"),
    ])
    + _p(G_CO, [
        ("ten_cong_ty", "Tên pháp nhân", "Công ty TNHH Mẫu"),
        ("ten_viet_tat", "Tên viết tắt", "MAU"),
        ("ma_so_thue_cong_ty", "Mã số thuế pháp nhân", "0100000000"),
        ("dia_chi_cong_ty", "Địa chỉ pháp nhân", "1 Phố Huế, Hai Bà Trưng, Hà Nội"),
        ("nguoi_dai_dien", "Người đại diện", "Trần Thị Bình"),
        ("chuc_vu_nguoi_dai_dien", "Chức vụ người đại diện", "Giám đốc"),
    ])
    + _p(G_CT, [
        ("so_hop_dong", "Số hợp đồng", "HDLD001"),
        ("loai_hop_dong", "Loại hợp đồng", "Xác định thời hạn"),
        ("ngay_ky", "Ngày ký", "01/10/2026"),
        ("ngay_ky_ngay", "Ngày ký (ngày)", "01"),
        ("ngay_ky_thang", "Ngày ký (tháng)", "10"),
        ("ngay_ky_nam", "Ngày ký (năm)", "2026"),
        ("ngay_bat_dau", "Ngày bắt đầu", "01/10/2026"),
        ("ngay_ket_thuc", "Ngày kết thúc", "30/09/2027"),
        ("thoi_han", "Thời hạn", "12 tháng"),
        ("chuc_danh", "Chức danh", "Chuyên viên mua hàng"),
        ("phong_ban", "Phòng ban", "Phòng Mua hàng"),
        ("dia_diem_lam_viec", "Địa điểm làm việc", "Văn phòng Hà Nội"),
        ("ghi_chu", "Ghi chú", ""),
    ])
    + _p(G_PAY, [
        ("luong_co_ban", "Lương cơ bản", "15.000.000"),
        ("luong_co_ban_bang_chu", "Lương cơ bản (bằng chữ)", "Mười lăm triệu đồng chẵn"),
        ("luong_dong_bao_hiem", "Lương đóng bảo hiểm", "12.000.000"),
        ("phu_cap", "Phụ cấp (tổng)", "2.000.000"),
        ("phu_cap_bang_chu", "Phụ cấp (bằng chữ)", "Hai triệu đồng chẵn"),
        ("phu_cap_ghi_chu", "Ghi chú phụ cấp", "Ăn trưa, xăng xe"),
        ("tong_thu_nhap", "Tổng thu nhập", "17.000.000"),
        ("tong_thu_nhap_bang_chu", "Tổng thu nhập (bằng chữ)", "Mười bảy triệu đồng chẵn"),
    ])
    + _p(G_SYS, [("ngay_lap", "Ngày lập", "05/10/2026")])
)

KNOWN_KEYS: frozenset[str] = frozenset(p.key for p in PLACEHOLDERS)

assert len(KNOWN_KEYS) == len(PLACEHOLDERS), "Danh mục biến có khóa trùng"


def sample_context() -> dict[str, str]:
    """Ngữ cảnh mẫu (dùng để render thử lúc tải mẫu lên)."""
    return {p.key: p.example for p in PLACEHOLDERS}
