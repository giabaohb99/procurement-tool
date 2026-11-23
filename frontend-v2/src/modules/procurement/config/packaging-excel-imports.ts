/**
 * duoc-CR-784 — ba loại nhập Excel của cụm Giá NVL sản xuất, cùng một nút `PackagingExcelImportButton`. Mã module khớp
 * `ImportModule` ở `backend/app/modules/import_tool/model.py`; tệp mẫu tải ở `GET /api/imports/template?module=`. Quyền
 * trên `packaging_cost` khớp `_MODULE_GUARDS` của backend: Sổ Misa đổi giá cả cụm nên đòi quyền SỬA.
 */
import {
  IMPORT_MODULE_PACKAGING_BOM,
  IMPORT_MODULE_PACKAGING_MISA,
  IMPORT_MODULE_PACKAGING_QUOTE,
} from '@/modules/system/config/import-meta'

export interface PackagingExcelImportKind {
  module: number
  /** Nhãn nút trên màn. */
  label: string
  title: string
  description: string
  /** Quyền cần có trên `packaging_cost` (ngoài `import.create` + `import.read`). */
  action: 'create' | 'write'
  /** Tên tệp dự phòng khi máy chủ không trả tên. */
  templateName: string
}

export const PACKAGING_BOM_IMPORT: PackagingExcelImportKind = {
  module: IMPORT_MODULE_PACKAGING_BOM,
  label: 'Nhập từ Excel',
  title: 'Nhập định mức bao bì',
  description:
    'Tệp DATA_CHAI.xlsx (sheet MAP_SP, hoặc data + DATA CHUNG). Hệ thống chạy thử trước — xem nhật ký từng dòng ở trang lô rồi mới bấm Ghi thật. Mã HH đã có thì cập nhật, chưa có thì tạo; dòng không có trong tệp giữ nguyên.',
  action: 'create',
  templateName: 'mau-nhap-dinh-muc-bao-bi.xlsx',
}

export const PACKAGING_QUOTE_IMPORT: PackagingExcelImportKind = {
  module: IMPORT_MODULE_PACKAGING_QUOTE,
  label: 'Nhập báo giá',
  title: 'Nhập báo giá VTBB từ Excel',
  description:
    'Mỗi dòng một báo giá: Mã VTBB, Đơn giá (VNĐ chưa VAT), Ngày hiệu lực; tùy chọn Mã NCC, VAT (%), Ghi chú. Trùng mã + NCC + ngày hiệu lực thì cập nhật, chưa có thì thêm. Chạy thử trước, xem nhật ký rồi bấm Ghi thật.',
  action: 'create',
  templateName: 'mau-nhap-bao-gia-vtbb.xlsx',
}

export const PACKAGING_MISA_IMPORT: PackagingExcelImportKind = {
  module: IMPORT_MODULE_PACKAGING_MISA,
  label: 'Nạp sổ Misa',
  title: 'Nạp Sổ chi tiết mua hàng Misa',
  description:
    'Tệp Excel Sổ chi tiết mua hàng xuất từ Misa (cột Ngày, Mã hàng, Số lượng, Đơn giá, Tên NCC, Tên kho…). Chỉ thay dữ liệu Misa trong khoảng ngày của tệp, dòng trùng giữ nguyên, ngoài khoảng không đổi; mốc sổ Misa dời theo ngày lớn nhất. Chạy thử trước, xem nhật ký rồi bấm Ghi thật.',
  action: 'write',
  templateName: 'mau-nap-so-misa.xlsx',
}
