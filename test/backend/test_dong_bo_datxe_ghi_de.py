"""Luật ghi đè khi app đặt xe cũ đẩy bản cập nhật của một phiếu đã có bên ERP.

Đại ca chốt 17/09/2026: **ghi đè hết, trừ ghi rỗng đè lên đang có.**

Vế "trừ" mới là thứ bài kiểm này canh, vì nó chống một đường mất dữ liệu không
kêu một tiếng nào. Ô `assigned_vehicle_id` không chép thẳng từ app cũ — nó là
`vehicle_index.get(khóa, 0)`. Hôm nào đội xe mua xe mới, app cũ gán liền, ERP
chưa kịp đóng dấu `legacy_id` cho xe đó, thì bộ dựng trả về 0. Ghi đè thẳng là
xóa xe khỏi một chuyến đã chạy xong, trong khi bên app cũ vẫn ghi đủ. Không lỗi,
không cảnh báo, chỉ là ô trống — tới lúc đối soát cuối tháng mới lòi ra.

Đo trên kho Firebase dev ngày 17/09 thì 0/9 thương hiệu, 0/3 tài xế và 3/37
người khớp dấu `legacy_id` dưới ERP, nên đây không phải giả định phòng xa: bật
đồng bộ dev mà không có luật này là mọi phiếu mất sạch xe với tài xế ngay nhịp
đầu tiên.

Bài kiểm chạy thẳng trên đối tượng ORM chưa lưu, không cần DB — luật này là
phép so hai hàng, không dính truy vấn nào.
"""
from datetime import datetime

import collections

from app.modules.legacy_datxe.builder import (
    LEGACY_READONLY_FIELDS,
    copy_legacy_fields,
)
from app.modules.seal_request.model import SealRequest
from app.modules.vehicle_booking.model import (
    BK_COMPLETED,
    DRV_COMPLETED,
    VehicleBooking,
)


def _phieu_erp_da_dieu_phoi() -> VehicleBooking:
    """Một phiếu đã chạy xong dưới ERP: có mã, có xe, có tài xế, có chi phí."""
    return VehicleBooking(
        id=12,
        code="DX000042",
        legacy_id="-NxAbCdEf",
        purpose="Đi ký hợp đồng",
        start_location="Trụ sở",
        end_location="Khách hàng",
        status=BK_COMPLETED,
        assigned_vehicle_id=7,
        assigned_driver_id=3,
        driver_status=DRV_COMPLETED,
        distance_km=48,
        cost=350000,
        company_id=1,
        department_id=4,
        requester_id=21,
        is_round_trip=True,
        created_at=datetime(2026, 9, 1, 3, 0),
        created_by=21,
    )


def _ban_app_cu_tra_khong_ra_danh_muc() -> VehicleBooking:
    """Bản vừa dựng từ app cũ, đúng như `build_booking` trả về khi tra trượt.

    App cũ CÓ gán xe và tài xế, nhưng khóa của chúng chưa có dấu `legacy_id`
    dưới ERP nên `vehicle_index.get(khóa, 0)` trả về 0.
    """
    return VehicleBooking(
        legacy_id="-NxAbCdEf",
        purpose="Đi ký hợp đồng (đã sửa giờ)",
        start_location="Trụ sở",
        end_location="Khách hàng",
        status=BK_COMPLETED,
        assigned_vehicle_id=0,
        assigned_driver_id=0,
        driver_status=DRV_COMPLETED,
        company_id=0,
        department_id=4,
        requester_id=0,
        is_round_trip=True,
        created_at=datetime(2026, 9, 1, 3, 0),
        created_by=21,
    )


def test_app_cu_tra_khong_ra_thi_khong_duoc_xoa_xe_erp_dang_co():
    phieu = _phieu_erp_da_dieu_phoi()
    stats: collections.Counter = collections.Counter()

    doi = copy_legacy_fields(phieu, _ban_app_cu_tra_khong_ra_danh_muc(), stats)

    assert phieu.assigned_vehicle_id == 7
    assert phieu.assigned_driver_id == 3
    assert phieu.company_id == 1
    assert phieu.requester_id == 21
    assert "assigned_vehicle_id" not in doi
    #  Giữ nguyên thì phải kêu, không được im lặng — sổ đồng bộ đọc mấy dòng này.
    assert stats["giu nguyen vi app cu khong tra ra: assigned_vehicle_id"] == 1
    assert stats["giu nguyen vi app cu khong tra ra: assigned_driver_id"] == 1


def test_noi_dung_sua_ben_app_cu_thi_erp_nhan():
    phieu = _phieu_erp_da_dieu_phoi()

    doi = copy_legacy_fields(phieu, _ban_app_cu_tra_khong_ra_danh_muc(),
                             collections.Counter())

    assert phieu.purpose == "Đi ký hợp đồng (đã sửa giờ)"
    assert doi == ["purpose"]


def test_app_cu_doi_sang_xe_khac_thi_erp_ghi_de():
    """Ghi đè là mặc định: giai đoạn này app cũ vẫn là nơi người ta gán xe."""
    phieu = _phieu_erp_da_dieu_phoi()
    ban_moi = _ban_app_cu_tra_khong_ra_danh_muc()
    ban_moi.assigned_vehicle_id = 9
    ban_moi.assigned_driver_id = 5

    doi = copy_legacy_fields(phieu, ban_moi, collections.Counter())

    assert phieu.assigned_vehicle_id == 9
    assert phieu.assigned_driver_id == 5
    assert set(doi) >= {"assigned_vehicle_id", "assigned_driver_id"}


def test_ma_phieu_va_moc_tao_khong_bao_gio_bi_dung():
    """Đổi `code` là mọi bản in với email đã gửi trỏ sai phiếu."""
    phieu = _phieu_erp_da_dieu_phoi()
    ban_moi = _ban_app_cu_tra_khong_ra_danh_muc()
    ban_moi.code = "DX999999"
    ban_moi.created_at = datetime(2020, 1, 1, 0, 0)
    ban_moi.created_by = 999
    ban_moi.id = 777

    doi = copy_legacy_fields(phieu, ban_moi, collections.Counter())

    assert phieu.code == "DX000042"
    assert phieu.created_at == datetime(2026, 9, 1, 3, 0)
    assert phieu.created_by == 21
    assert phieu.id == 12
    assert not (set(doi) & LEGACY_READONLY_FIELDS)


def test_bo_tick_khu_hoi_la_y_dinh_that_chu_khong_phai_o_trong():
    """`False` khác `không biết` — bỏ tick phải đi qua, đừng chặn nhầm."""
    phieu = _phieu_erp_da_dieu_phoi()
    ban_moi = _ban_app_cu_tra_khong_ra_danh_muc()
    ban_moi.is_round_trip = False

    doi = copy_legacy_fields(phieu, ban_moi, collections.Counter())

    assert phieu.is_round_trip is False
    assert "is_round_trip" in doi


def test_khong_co_gi_doi_thi_tra_ve_rong():
    """Rỗng là tín hiệu cho người gọi: khỏi đụng vào DB, khỏi ghi sổ."""
    phieu = _phieu_erp_da_dieu_phoi()
    ban_moi = _ban_app_cu_tra_khong_ra_danh_muc()
    ban_moi.purpose = phieu.purpose

    assert copy_legacy_fields(phieu, ban_moi, collections.Counter()) == []


def test_phieu_dau_cung_mot_luat():
    """Phiếu dấu dùng chung hàm, không có bản chép thứ hai để lệch nhau."""
    phieu = SealRequest(
        id=5, code="DD000153", legacy_id="-NxSeal",
        purpose="Đóng dấu hợp đồng", seal_type_id=2,
        company_id=3, department_id=4, requester_id=21,
        created_at=datetime(2026, 9, 1, 3, 0), created_by=21,
    )
    ban_moi = SealRequest(
        legacy_id="-NxSeal", purpose="Đóng dấu hợp đồng (bản 2)",
        seal_type_id=2, company_id=0, department_id=4, requester_id=0,
        created_at=datetime(2026, 9, 1, 3, 0), created_by=21,
    )

    doi = copy_legacy_fields(phieu, ban_moi, collections.Counter())

    assert phieu.purpose == "Đóng dấu hợp đồng (bản 2)"
    assert phieu.company_id == 3
    assert phieu.code == "DD000153"
    assert doi == ["purpose"]
