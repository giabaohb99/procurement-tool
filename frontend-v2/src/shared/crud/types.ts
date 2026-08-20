import type { ReactNode } from 'react'

import type { PermissionEntity } from '@/core/authorization/permission-types'
import type { FilterFieldDefinition } from '@/shared/conditional-filter'
import type { DataTableColumn } from '@/shared/data-table'

export interface CrudOption {
  value: string | number | boolean
  label: string
}

export interface CrudFormField {
  /** Tên trường trong payload JSON / record object. */
  name: string
  /** Nhãn tiếng Việt hiển thị trên form. */
  label: string
  /**
   * Loại trường form.
   *
   * `percent`: người dùng nhập PHẦN TRĂM (8) còn backend lưu TỈ LỆ (0.08) —
   * quy đổi do `field-values.ts` lo, config chỉ khai kiểu.
   */
  type?: 'text' | 'number' | 'textarea' | 'select' | 'switch' | 'date' | 'percent'
  /** Bắt buộc nhập. */
  required?: boolean
  /** Chỉ đọc khi sửa (vd `code` không cho đổi sau khi tạo). */
  readonlyOnEdit?: boolean
  /** Chiếm trọn 1 dòng (2 cột) trên form. Dành cho textarea / địa chỉ / ghi chú dài. */
  fullWidth?: boolean
  /** Chú thích gợi ý mờ phía dưới ô nhập. */
  hint?: string
  placeholder?: string
  /** Tùy chọn tĩnh cho trường `select`. */
  options?: CrudOption[]
  /** Nạp tùy chọn động từ API (vd `/api/departments`). */
  source?: {
    url: string
    valueKey?: string
    labelKey?: string
  }
  /**
   * Giá trị mặc định khi tạo mới, khai theo DẠNG LƯU của backend (vd VAT 8% thì
   * khai `0.08`, không khai `8`).
   */
  defaultValue?: unknown
}

import type { IdentityChip } from '@/shared/ui/record-identity-card'

export interface CrudTab<T> {
  key: string
  label: string
  render: (row: T) => ReactNode
}

export interface CrudConfig<T> {
  /** Khóa phân quyền — khớp ENTITIES trong backend (vd 'warehouse', 'unit'). */
  entity: PermissionEntity
  /** Tiêu đề danh mục tiếng Việt (vd 'Kho', 'Đơn vị tính'). */
  title: string
  /** Tên đơn vị danh từ (vd 'kho', 'đơn vị tính', dùng cho nút "Thêm kho"). */
  unitLabel: string
  /** Đường dẫn API (vd '/api/warehouses'). */
  apiPath: string
  /** Khóa lưu cấu hình bảng trong localStorage (vd 'inventory.warehouses'). */
  storageKey: string
  /** Trường định danh duy nhất (mặc định 'id'). */
  idKey?: keyof T
  /** Trường tìm kiếm nhanh trên thanh công cụ (mặc định 'name', hoặc 'q'). */
  searchParam?: string
  searchPlaceholder?: string
  /** Cấu hình các cột hiển thị trên DataTable. */
  columns: DataTableColumn<T>[]
  /** Cấu hình bộ lọc nâng cao (ConditionalFilter). */
  filterConfig?: {
    fields: FilterFieldDefinition[]
    preserveParams?: string[]
    allowConjunctionToggle?: boolean
  }
  /** Cấu hình các trường trong Form thêm / sửa. */
  formFields: CrudFormField[]
  /** Cho phép xuất file Excel qua GET {apiPath}/export/xlsx. */
  exportXlsx?: boolean
  /** Đường dẫn trang danh sách (vd '/inventory/warehouses'). */
  listRoute?: string
  /** Đường dẫn tới trang chi tiết (vd (id) => `/inventory/warehouses/${id}`). */
  detailRoute?: (id: number | string) => string
  /** Thẻ danh tính hiển thị trên đầu trang chi tiết. */
  chips?: (row: T) => IdentityChip[]
  /** Cảnh báo khi xóa bản ghi (vd 'Dữ liệu tồn kho liên quan có thể bị ảnh hưởng'). */
  deleteWarning?: string
  /** Tab mở rộng ở trang chi tiết (vd Lịch sử mua hàng, Đơn hàng về kho). */
  tabs?: CrudTab<T>[]
  /** Khối bổ sung hiển thị dưới form ở trang chi tiết. */
  renderExtra?: (row: T) => ReactNode
  /** Hàm lấy tên bản ghi để hiển thị trong câu hỏi xác nhận Xóa. */
  getItemName?: (row: T) => string
  /** Chiều rộng tối đa của hộp thoại thêm mới (mặc định 'sm:max-w-lg'). */
  dialogMaxWidth?: string
  /** Render thêm nội dung ở đầu thanh công cụ. */
  renderToolbarExtra?: () => ReactNode
}
