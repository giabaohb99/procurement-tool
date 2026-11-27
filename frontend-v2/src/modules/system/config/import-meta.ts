/**
 * Bảng tra nhãn cho các số enum của Import (đối tượng, chế độ, trạng thái, mức log).
 *
 * Khớp `app/modules/import_tool/model.py`: `ImportModule`, `ImportMode`,
 * `ImportStatus`, `LogLevel`. Thêm đối tượng import mới (Đ-13d) thì bổ sung ở đây
 * và ở `IMPORT_MODULE_OPTIONS` bên dưới.
 */
import type { PermissionEntity } from '@/core/authorization/permission-types'

export const IMPORT_MODULE_SURVEY = 1
export const IMPORT_MODULE_PURCHASE_ORDER = 2
// Tờ khai hải quan GTT02 (bao-CR-470) và định mức bao bì DATA_CHAI.xlsx (duoc-CR-784) — khớp `ImportModule` ở backend.
// Cả hai nạp ở màn riêng của phân hệ mình nên KHÔNG có trong `IMPORT_MODULE_OPTIONS`; chỉ cần nhãn để trang lô nhập hiện chữ.
export const IMPORT_MODULE_CUSTOMS_DECLARATION = 3
export const IMPORT_MODULE_PACKAGING_BOM = 4
// duoc-CR-784: báo giá VTBB + Sổ chi tiết mua hàng Misa (.xlsx) của cụm Giá NVL sản xuất.
export const IMPORT_MODULE_PACKAGING_QUOTE = 5
export const IMPORT_MODULE_PACKAGING_MISA = 6
/** Ba loại nhập của cụm Giá NVL sản xuất: không có "Hoàn tác" (không lưu bản chụp), thay bằng "Xóa dữ liệu của lô này". */
export const IMPORT_MODULES_WITHOUT_REVERT: readonly number[] = [
  IMPORT_MODULE_PACKAGING_BOM,
  IMPORT_MODULE_PACKAGING_QUOTE,
  IMPORT_MODULE_PACKAGING_MISA,
]
/** Loại lô có nút "Xóa dữ liệu của lô này" (duoc-CR-784 phase 07) — cùng ba loại không hoàn tác. */
export const IMPORT_MODULES_WITH_PURGE: readonly number[] = IMPORT_MODULES_WITHOUT_REVERT
/**
 * bao-CR-792 — khóa quyền phải có `delete` để "Xóa dữ liệu của lô này", theo loại lô: mỗi loại thuộc một màn của cụm Giá
 * NVL sản xuất nên gác bằng khóa của màn đó (khóa chung `packaging_cost` nghỉ hẳn). Khớp chốt gác ở backend.
 */
export const IMPORT_PURGE_ENTITY: Readonly<Record<number, PermissionEntity>> = {
  [IMPORT_MODULE_PACKAGING_BOM]: 'packaging_bom',
  [IMPORT_MODULE_PACKAGING_QUOTE]: 'packaging_price_list',
  [IMPORT_MODULE_PACKAGING_MISA]: 'packaging_history',
}
// Danh mục nền (Đ-13d) — khớp `ImportModule` ở backend.
export const IMPORT_MODULE_COMPANY = 10
export const IMPORT_MODULE_DEPARTMENT = 11
export const IMPORT_MODULE_EMPLOYEE = 12
// Danh mục Sản xuất + Kho (CR-174).
export const IMPORT_MODULE_SUPPLIER = 13
export const IMPORT_MODULE_PRODUCT = 14
export const IMPORT_MODULE_UNIT = 15
export const IMPORT_MODULE_ITEM_GROUP = 16
export const IMPORT_MODULE_WAREHOUSE = 17
// Chứng từ nhiều dòng (CR-175).
export const IMPORT_MODULE_SURVEY_REQUEST = 18
export const IMPORT_MODULE_PURCHASE_REQUEST = 19
// Danh mục Đặt xe + Duyệt dấu.
export const IMPORT_MODULE_VEHICLE = 20
export const IMPORT_MODULE_DRIVER = 21
export const IMPORT_MODULE_SEAL_TYPE = 22
// Chứng từ header-only — Đặt xe + Duyệt dấu.
export const IMPORT_MODULE_VEHICLE_BOOKING = 23
export const IMPORT_MODULE_SEAL_REQUEST = 24

export const IMPORT_MODULE_LABELS: Record<number, string> = {
  [IMPORT_MODULE_SURVEY]: 'Khảo sát',
  [IMPORT_MODULE_PURCHASE_ORDER]: 'Đơn mua hàng',
  [IMPORT_MODULE_CUSTOMS_DECLARATION]: 'Dữ liệu hải quan',
  [IMPORT_MODULE_PACKAGING_BOM]: 'Định mức bao bì',
  [IMPORT_MODULE_PACKAGING_QUOTE]: 'Báo giá VTBB',
  [IMPORT_MODULE_PACKAGING_MISA]: 'Sổ Misa (giá NVL)',
  [IMPORT_MODULE_COMPANY]: 'Công ty',
  [IMPORT_MODULE_DEPARTMENT]: 'Phòng ban',
  [IMPORT_MODULE_EMPLOYEE]: 'Nhân sự',
  [IMPORT_MODULE_SUPPLIER]: 'Nhà cung cấp',
  [IMPORT_MODULE_PRODUCT]: 'Sản phẩm & Vật tư',
  [IMPORT_MODULE_UNIT]: 'Đơn vị tính',
  [IMPORT_MODULE_ITEM_GROUP]: 'Phân loại VTBB',
  [IMPORT_MODULE_WAREHOUSE]: 'Danh mục kho',
  [IMPORT_MODULE_SURVEY_REQUEST]: 'Yêu cầu báo giá',
  [IMPORT_MODULE_PURCHASE_REQUEST]: 'Yêu cầu mua hàng',
  [IMPORT_MODULE_VEHICLE]: 'Xe',
  [IMPORT_MODULE_DRIVER]: 'Tài xế',
  [IMPORT_MODULE_SEAL_TYPE]: 'Loại con dấu',
  [IMPORT_MODULE_VEHICLE_BOOKING]: 'Yêu cầu đặt xe',
  [IMPORT_MODULE_SEAL_REQUEST]: 'Yêu cầu đóng dấu',
}

/**
 * Đối tượng người dùng được chọn khi upload.
 *
 * `moduleId`: phân hệ chứa bảng (gom nhóm khi chọn — xem `config/data-modules.ts`).
 * `hasTemplate`: có file mẫu tải về (các danh mục nền của Đ-13d). Khảo sát / ĐMH
 * dùng mẫu Misa riêng nên chưa gắn tải mẫu ở đây.
 */
export const IMPORT_MODULE_OPTIONS: {
  value: number
  label: string
  moduleId: string
  hasTemplate?: boolean
}[] = [
  { value: IMPORT_MODULE_COMPANY, label: 'Công ty', moduleId: 'hr', hasTemplate: true },
  { value: IMPORT_MODULE_DEPARTMENT, label: 'Phòng ban', moduleId: 'hr', hasTemplate: true },
  { value: IMPORT_MODULE_EMPLOYEE, label: 'Nhân sự', moduleId: 'hr', hasTemplate: true },
  { value: IMPORT_MODULE_SURVEY_REQUEST, label: 'Yêu cầu báo giá', moduleId: 'procurement', hasTemplate: true },
  { value: IMPORT_MODULE_PURCHASE_REQUEST, label: 'Yêu cầu mua hàng', moduleId: 'procurement', hasTemplate: true },
  { value: IMPORT_MODULE_SURVEY, label: 'Khảo sát', moduleId: 'procurement', hasTemplate: true },
  { value: IMPORT_MODULE_PURCHASE_ORDER, label: 'Đơn mua hàng', moduleId: 'procurement', hasTemplate: true },
  { value: IMPORT_MODULE_SUPPLIER, label: 'Nhà cung cấp', moduleId: 'production', hasTemplate: true },
  { value: IMPORT_MODULE_PRODUCT, label: 'Sản phẩm & Vật tư', moduleId: 'production', hasTemplate: true },
  { value: IMPORT_MODULE_UNIT, label: 'Đơn vị tính', moduleId: 'production', hasTemplate: true },
  { value: IMPORT_MODULE_ITEM_GROUP, label: 'Phân loại VTBB', moduleId: 'production', hasTemplate: true },
  { value: IMPORT_MODULE_WAREHOUSE, label: 'Danh mục kho', moduleId: 'inventory', hasTemplate: true },
  { value: IMPORT_MODULE_VEHICLE, label: 'Xe', moduleId: 'vehicle-booking', hasTemplate: true },
  { value: IMPORT_MODULE_DRIVER, label: 'Tài xế', moduleId: 'vehicle-booking', hasTemplate: true },
  { value: IMPORT_MODULE_VEHICLE_BOOKING, label: 'Yêu cầu đặt xe', moduleId: 'vehicle-booking', hasTemplate: true },
  { value: IMPORT_MODULE_SEAL_TYPE, label: 'Loại con dấu', moduleId: 'seal', hasTemplate: true },
  { value: IMPORT_MODULE_SEAL_REQUEST, label: 'Yêu cầu đóng dấu', moduleId: 'seal', hasTemplate: true },
]

export const IMPORT_MODE_DRY_RUN = 0
export const IMPORT_MODE_APPLY = 1

export const IMPORT_MODE_LABELS: Record<number, string> = {
  [IMPORT_MODE_DRY_RUN]: 'Chạy thử',
  [IMPORT_MODE_APPLY]: 'Ghi thật',
}

export const IMPORT_STATUS_QUEUED = 0
export const IMPORT_STATUS_RUNNING = 1
export const IMPORT_STATUS_DONE = 2
export const IMPORT_STATUS_FAILED = 3
export const IMPORT_STATUS_REVERTED = 4

export const IMPORT_STATUS_LABELS: Record<number, string> = {
  [IMPORT_STATUS_QUEUED]: 'Chờ',
  [IMPORT_STATUS_RUNNING]: 'Đang chạy',
  [IMPORT_STATUS_DONE]: 'Hoàn tất',
  [IMPORT_STATUS_FAILED]: 'Lỗi',
  [IMPORT_STATUS_REVERTED]: 'Đã hoàn tác',
}

export const IMPORT_LEVEL_INFO = 0
export const IMPORT_LEVEL_WARNING = 1
export const IMPORT_LEVEL_REVIEW = 2
export const IMPORT_LEVEL_ERROR = 3

export const IMPORT_LEVEL_LABELS: Record<number, string> = {
  [IMPORT_LEVEL_INFO]: 'Thông tin',
  [IMPORT_LEVEL_WARNING]: 'Cảnh báo',
  [IMPORT_LEVEL_REVIEW]: 'Rà soát',
  [IMPORT_LEVEL_ERROR]: 'Lỗi',
}

/**
 * Nhãn tiếng Việt cho "Phân loại" (category) của từng dòng nhật ký import.
 * Khớp mã category ghi ở backend (`import_tool/{catalog_import,doc_import}.py`).
 */
export const IMPORT_CATEGORY_LABELS: Record<string, string> = {
  created: 'Tạo mới',
  updated: 'Cập nhật',
  deleted: 'Xóa',
  delete_failed: 'Xóa thất bại',
  delete_no_code: 'Xóa: thiếu mã',
  delete_not_found: 'Xóa: không tìm thấy',
  missing_required: 'Thiếu trường bắt buộc',
  missing_code: 'Thiếu mã phiếu',
  ref_not_found: 'Không tìm thấy mã liên quan',
  doc_created: 'Tạo phiếu',
  doc_exists: 'Phiếu đã tồn tại',
  doc_no_line: 'Phiếu không có dòng',
  line_missing: 'Dòng thiếu dữ liệu',
  // duoc-CR-784: nhập báo giá VTBB (`packaging_cost/quote_import.py`) + nạp Sổ Misa (`misa_xlsx_import.py`).
  quote_new: 'Thêm báo giá',
  quote_update: 'Sửa báo giá',
  misa_summary: 'Tóm tắt sổ Misa',
  misa_add: 'Thêm lần mua',
  misa_remove: 'Bỏ lần mua',
  bad_row: 'Dòng thiếu / sai',
  bad_date: 'Sai ngày',
  bad_number: 'Số / mã lỗi',
  bad_vat: 'VAT không hợp lệ',
  code_not_in_catalog: 'Mã chưa có trong danh mục',
  duplicate: 'Trùng dòng',
  log_trimmed: 'Bớt nhật ký',
}

/** Batch còn đang chạy → cần auto-poll để cập nhật khi worker xong. */
export function isImportRunning(status: number): boolean {
  return status <= IMPORT_STATUS_RUNNING
}

/** Phân hệ (moduleId) của một đối tượng import — cho cột "Phân hệ" trên bảng. */
export function importModuleId(module: number): string | undefined {
  return IMPORT_MODULE_OPTIONS.find((o) => o.value === module)?.moduleId
}
