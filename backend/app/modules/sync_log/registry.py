"""Danh bạ các HỆ NGUỒN dùng chung quyển sổ đồng bộ.

Mỗi hệ ngoài khai một *adapter* `SyncSource`: mã nguồn · nhãn · tên biến môi
trường giữ cờ bật và khóa bí mật · danh sách đối tượng đồng bộ được · cờ cảnh
báo riêng. Thêm hệ mới = thêm một adapter, KHÔNG đụng model/service/controller.

Đang có hai nguồn: `datxe` (app đặt xe + duyệt dấu cũ) và `pos365` (Điểm cà phê).
Đồng bộ đơn hàng sau này chỉ cần gọi `register_source(...)` trong module của nó
là dùng được nguyên bộ sổ, màn hình và cửa "Chạy lại".

Một nguồn KHÔNG phải khai đủ mọi thứ: `pos365` chỉ có `jobs` (năm vòng chạy nền,
ghi dòng `grain = RUN`), còn `datxe` khai CẢ HAI — từng phiếu đi qua cửa nhận ghi
dòng `grain = RECORD`, hai vòng chạy nền của nó ghi dòng `grain = RUN` ôm lấy
đám dòng đó. Nguồn nào cần cả hai thì khai cả hai — sổ không phân biệt.
"""
from dataclasses import dataclass, field

from app.core.config import settings

from .constants import COMMON_WARNINGS


@dataclass(frozen=True)
class SyncSource:
    """Khai báo một hệ nguồn.

    `enabled_setting` / `secret_setting` / `base_url_setting` là TÊN thuộc tính
    trong `core/config.py`, không phải giá trị — đọc lúc chạy để đổi `.env` là
    có hiệu lực ngay, và để khóa bí mật không bị chụp lại lúc nạp module.
    """

    code: str                      # tối đa 20 ký tự, khớp cột `source`
    label: str                     # nhãn tiếng Việt cho màn hình
    enabled_setting: str = ""      # tên cờ bật (bool) trong settings
    # Cờ của nguồn là CẦU DAO NGẮT (vd `POS365_HARD_OFF`) chứ không phải cờ bật:
    # bật cầu dao = tắt đồng bộ. Khai riêng thay vì đổi tên biến môi trường đang
    # chạy thật ở prod.
    enabled_inverted: bool = False
    secret_setting: str = ""       # tên biến giữ khóa ký chung (nguồn nào ký HMAC)
    base_url_setting: str = ""     # tên biến giữ địa chỉ gốc của hệ ngoài
    entities: dict[str, str] = field(default_factory=dict)        # mã -> nhãn
    jobs: dict[str, str] = field(default_factory=dict)            # công việc chạy nền
    extra_warnings: dict[str, str] = field(default_factory=dict)  # cờ riêng

    def is_enabled(self) -> bool:
        if not self.enabled_setting:
            return True
        flag = bool(getattr(settings, self.enabled_setting, False))
        return (not flag) if self.enabled_inverted else flag

    def secret(self) -> str:
        if not self.secret_setting:
            return ""
        return (getattr(settings, self.secret_setting, "") or "").strip()

    def base_url(self) -> str:
        if not self.base_url_setting:
            return ""
        return (getattr(settings, self.base_url_setting, "") or "").strip().rstrip("/")

    def is_ready(self) -> bool:
        """Đủ điều kiện gọi qua lại: đã bật VÀ đã có khóa ký."""
        return self.is_enabled() and bool(self.secret())

    def warning_labels(self) -> dict[str, str]:
        """Cờ dùng chung cộng cờ riêng của nguồn."""
        return {**COMMON_WARNINGS, **self.extra_warnings}

    def entity_label(self, entity: str) -> str:
        return self.entities.get(entity, entity)

    def job_label(self, job: str) -> str:
        return self.jobs.get(job, job)


SYNC_SOURCES: dict[str, SyncSource] = {}


def register_source(source: SyncSource) -> SyncSource:
    """Ghi tên một hệ nguồn. Gọi lại với cùng mã thì đè — tiện cho test."""
    if len(source.code) > 20:
        raise ValueError(f"Mã nguồn '{source.code}' dài quá 20 ký tự (cột source)")
    SYNC_SOURCES[source.code] = source
    return source


def get_source(code: str) -> SyncSource | None:
    return SYNC_SOURCES.get(code)


def require_source(code: str) -> SyncSource:
    """Lấy adapter, không có thì ném lỗi rõ ràng thay vì ghi sổ mã rác."""
    source = SYNC_SOURCES.get(code)
    if source is None:
        known = ", ".join(sorted(SYNC_SOURCES)) or "(chưa khai nguồn nào)"
        raise ValueError(f"Hệ nguồn '{code}' chưa được khai. Đang có: {known}")
    return source


def source_options() -> list[dict[str, str | bool]]:
    """Danh sách nguồn cho ô lọc trên màn hình."""
    return [
        {"code": s.code, "label": s.label, "enabled": s.is_enabled()}
        for s in sorted(SYNC_SOURCES.values(), key=lambda x: x.label)
    ]


def job_options(code: str = "") -> list[dict[str, str]]:
    """Công việc chạy nền của một nguồn; bỏ trống thì gộp mọi nguồn."""
    sources = [require_source(code)] if code else list(SYNC_SOURCES.values())
    seen: dict[str, str] = {}
    for source in sources:
        for job, label in source.jobs.items():
            seen.setdefault(job, label)
    return [{"code": k, "label": v} for k, v in sorted(seen.items(), key=lambda x: x[1])]


def entity_options(code: str = "") -> list[dict[str, str]]:
    """Đối tượng đồng bộ của một nguồn; bỏ trống thì gộp mọi nguồn."""
    sources = [require_source(code)] if code else list(SYNC_SOURCES.values())
    seen: dict[str, str] = {}
    for source in sources:
        for entity, label in source.entities.items():
            seen.setdefault(entity, label)
    return [{"code": k, "label": v} for k, v in sorted(seen.items(), key=lambda x: x[1])]


def warning_labels(code: str = "") -> dict[str, str]:
    """Bảng tra nhãn cờ cảnh báo; bỏ trống thì gộp mọi nguồn."""
    if code:
        return require_source(code).warning_labels()
    merged = dict(COMMON_WARNINGS)
    for source in SYNC_SOURCES.values():
        merged.update(source.extra_warnings)
    return merged


# --- Các nguồn đã khai -----------------------------------------------------

#: App đặt xe / duyệt dấu cũ (Cloudflare Worker + Firebase Realtime Database).
#: Xem doc/dong-bo-dat-xe-duyet-dau/.
SOURCE_DATXE = "datxe"

register_source(
    SyncSource(
        code=SOURCE_DATXE,
        label="App đặt xe & duyệt dấu (cũ)",
        enabled_setting="SYNC_DATXE_ENABLED",
        secret_setting="SYNC_SHARED_SECRET",
        base_url_setting="SYNC_LEGACY_API_BASE",
        entities={
            "vehicle_booking": "Phiếu đặt xe",
            "seal_request": "Phiếu duyệt dấu",
            "vehicle": "Xe",
            "driver": "Tài xế",
            "file": "Tệp đính kèm",
        },
        jobs={
            "pull_updated": "Kéo phiếu đã sửa",
            "retry_pending": "Chạy lại phiếu lỗi",
        },
        extra_warnings={
            "no_plate": "Xe không có biển số, đã đặt mã tạm",
            "title_generated": "Tiêu đề phiếu dấu sinh từ mục đích",
            #  Ba cờ của bộ tra danh mục ba nấc (`legacy_datxe/resolver.py`).
            #  `auto_created` chính là HÀNG ĐỢI SOÁT: `tab_vehicle`/`tab_driver`
            #  không có cột "chờ duyệt" nào, nên lọc "chỉ dòng có cảnh báo" trên
            #  màn sổ này là chỗ duy nhất thấy được hàng do máy đẻ ra.
            "auto_created": "Tự tạo xe / tài xế từ app cũ — cần người soát lại",
            "stamped_by_name": "Ghép theo đặc điểm tự nhiên (biển số / điện thoại / tên)",
            "unresolved_catalog": "Tra danh mục không ra, ô để trống",
            #  Bốn cờ của lượt nhận phiếu (`legacy_datxe/service.py`).
            "closed_locked": "Phiếu đã chốt bên ERP, chỉ nhận đổi trạng thái",
            "blank_kept": "App cũ trả rỗng, giữ nguyên giá trị ERP đang có",
            "driver_deleted": "Tài xế được điều phối đã bị xóa bên app cũ",
            "truncated": "Nội dung quá dài, đã cắt và chép xuống ghi chú",
        },
    )
)

#: Điểm cà phê x POS365 (doc/erp/diem-ca-phe/). Nguồn này CHỈ có dòng lượt chạy
#: — năm vòng chạy nền. Không ký HMAC: ERP gọi ra bằng tài khoản POS365
#: (`POS365_USERNAME`/`POS365_PASSWORD`), không có đường ai gọi ngược vào.
SOURCE_POS365 = "pos365"

register_source(
    SyncSource(
        code=SOURCE_POS365,
        label="POS365 (Điểm cà phê)",
        enabled_setting="POS365_HARD_OFF",
        enabled_inverted=True,
        base_url_setting="POS365_BASE_URL",
        entities={"pos_order": "Đơn hàng POS"},
        jobs={
            "pull_orders": "Kéo đơn hàng",
            "check_voids": "Soát đơn hủy",
            "monthly_reset": "Reset kỳ tháng",
            "reconcile": "Đối chiếu",
            "mirror": "Soi gương số dư",
        },
    )
)
