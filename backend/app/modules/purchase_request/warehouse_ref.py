"""bao-CR-759 — giữ cặp (MÃ kho, TÊN kho) của dòng YCMH khớp nhau lúc lưu.

Dòng YCMH trước đây chỉ lưu TÊN kho (`warehouse`), nên đổi tên kho trong danh mục là dòng mất liên kết, và
mọi chỗ cần mã (tạo ĐMH, in phiếu) phải tự tra ngược tên -> mã. Từ CR-759 dòng lưu thêm `warehouse_code`; cột
tên vẫn giữ cho báo cáo / xuất Excel / trợ lý AI đọc như cũ.

Luật chọn bên nào thắng khi client gửi lên:
- Có MÃ khớp danh mục -> mã thắng, tên lấy theo danh mục (đổi tên kho thì lần lưu sau tên tự cập nhật).
- Không có mã (client cũ, trợ lý AI chỉ nói tên kho) -> suy mã từ tên, khớp ĐÚNG tên.
- Dòng ĐANG CÓ: client giữ nguyên mã cũ mà đổi tên (công cụ chỉ sửa tên) -> suy lại mã theo tên mới; client
  không gửi mã mà tên không đổi -> giữ mã cũ (kho đã đổi tên trong danh mục vẫn không mất liên kết).
"""
from sqlalchemy.orm import Session

from app.modules.catalog.model import Warehouse

#  Độ dài cột `tab_purchase_request_item.warehouse` — tên trong danh mục được tới 255 ký tự.
NAME_MAX_LEN = 100


class WarehouseCatalog:
    """Danh mục kho nạp MỘT lần cho cả lượt lưu phiếu (bảng nhỏ, vài chục dòng)."""

    def __init__(self, db: Session):
        self._db = db
        self._by_code: dict[str, str] | None = None
        self._by_name: dict[str, str] = {}

    def _load(self) -> None:
        rows = (self._db.query(Warehouse.code, Warehouse.name)
                .order_by(Warehouse.is_active.desc(), Warehouse.id.asc()).all())
        self._by_code = {}
        for code, name in rows:
            code, name = (code or "").strip(), (name or "").strip()
            if not code:
                continue
            self._by_code.setdefault(code, name)
            #  Danh mục không chặn trùng tên: kho đang dùng trước, rồi id nhỏ nhất (cùng luật migration).
            if name:
                self._by_name.setdefault(name, code)

    def name_of(self, code: str) -> str | None:
        if self._by_code is None:
            self._load()
        return self._by_code.get(code)

    def code_of(self, name: str) -> str:
        if self._by_code is None:
            self._load()
        return self._by_name.get(name, "")


def sync_line_warehouse(data: dict, catalog: WarehouseCatalog, current=None) -> None:
    """Sửa tại chỗ `data["warehouse_code"]` / `data["warehouse"]` của MỘT dòng YCMH sắp ghi."""
    code = (data.get("warehouse_code") or "").strip()
    name = (data.get("warehouse") or "").strip()
    if current is not None:
        old_code = (getattr(current, "warehouse_code", "") or "").strip()
        old_name = (getattr(current, "warehouse", "") or "").strip()
        if not code and name and name == old_name:
            code = old_code                  # client cũ không gửi mã, tên không đổi -> giữ liên kết cũ
        elif code and code == old_code and name and name != old_name:
            code = ""                        # chỉ tên đổi -> suy lại mã theo tên mới
    if code:
        catalog_name = catalog.name_of(code)
        if catalog_name:
            name = catalog_name[:NAME_MAX_LEN]
    elif name:
        code = catalog.code_of(name)
    data["warehouse_code"] = code
    data["warehouse"] = name
