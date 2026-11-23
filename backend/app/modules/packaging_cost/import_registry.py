"""Ba loại nhập Excel của cụm Giá NVL sản xuất (duoc-CR-784) gom MỘT chỗ để Quản lý Import rẽ nhánh: mã module → bộ đọc
(có `run(db, batch, wb, apply)` + `precheck(wb)`). Nhập trong hàm để tránh vòng nhập `import_tool` ↔ `packaging_cost`.
"""
from app.modules.import_tool.model import ImportModule

PACKAGING_IMPORT_MODULES = (ImportModule.PACKAGING_BOM, ImportModule.PACKAGING_QUOTE, ImportModule.PACKAGING_MISA)


def is_packaging_module(module: int) -> bool:
    return module in PACKAGING_IMPORT_MODULES


def get_importer(module: int):
    if module == ImportModule.PACKAGING_BOM:
        from . import bom_import
        return bom_import
    if module == ImportModule.PACKAGING_QUOTE:
        from . import quote_import
        return quote_import
    if module == ImportModule.PACKAGING_MISA:
        from . import misa_xlsx_import
        return misa_xlsx_import
    raise ValueError(f"Không phải module nhập của cụm Giá NVL: {module}")
