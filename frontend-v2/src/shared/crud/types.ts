import type { ComponentType, ReactNode } from 'react'

import type { PermissionEntity } from '@/core/authorization/permission-types'
import type { FilterFieldDefinition } from '@/shared/conditional-filter'
import type { DataTableColumn } from '@/shared/data-table'
import type { IdentityChip } from '@/shared/ui/record-identity-card'

/**
 * Ràng buộc chung cho bản ghi mà lớp CRUD thao tác: khóa chuỗi, giá trị CHƯA
 * biết kiểu. Cố ý dùng `unknown` chứ không `any` — `typescript.md` cấm để `any`
 * lọt vào chữ ký export; truy cập vào phải tự thu hẹp (String/Number/ép kiểu).
 */
export type CrudRecord = Record<string, unknown>

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
  /**
   * Tên NHÓM ô. Các ô cùng nhóm được gom lại dưới một tiêu đề nhỏ, theo thứ tự
   * nhóm xuất hiện lần đầu trong `formFields`.
   *
   * Form quá 8–10 ô mà bày phẳng thì người khai không biết ô nào ăn với ô nào —
   * và ở màn danh mục, đoán sai quan hệ giữa hai ô là khai sai luật cho cả công
   * ty. Bỏ trống = ô đứng ở nhóm đầu, không tiêu đề (giữ nguyên khuôn cũ cho
   * các màn chưa chia nhóm).
   */
  section?: string
  /**
   * Chỉ hiện ô này khi giá trị đang nhập thỏa điều kiện.
   *
   * Dùng cho những ô CHỈ CÓ NGHĨA ở một nhánh cấu hình (vd tỷ lệ quy đổi khi
   * chưa chọn «quy đổi» thì không nói lên gì). Ẩn hẳn thay vì làm mờ: ô mờ vẫn
   * chiếm chỗ và vẫn khiến người đọc dừng lại đọc chú thích của nó.
   *
   * ⚠️ Ẩn chỉ là chuyện HIỂN THỊ — giá trị vẫn nằm trong form và vẫn gửi lên.
   * Luật thật phải nằm ở backend, xem `catalog_controller._check_year_end_config`.
   */
  showWhen?: (values: CrudRecord) => boolean
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

export interface CrudTab<T> {
  key: string
  label: string
  render: (row: T) => ReactNode
}

export interface QuickFilterConfig {
  key: string
  label: string
  type: 'select' | 'date-range' | 'chip'
  options?: CrudOption[]
  sourceUrl?: string
}

export interface CrudConfig<T> {
  /** Khóa phân quyền — khớp ENTITIES trong backend (vd 'warehouse', 'unit'). */
  entity: PermissionEntity
  /** Tiêu đề danh mục tiếng Việt (vd 'Kho', 'Đơn vị tính'). */
  title: string
  /**
   * Câu dưới tiêu đề — nói màn này để làm gì.
   *
   * Bỏ trống thì `PageHeader` chỉ có mỗi dòng tiêu đề, và màn CRUD đứng cạnh
   * những màn viết tay (vốn luôn có mô tả) sẽ trông cụt lủn — khách chỉ đúng
   * chỗ đó ngày 04/09/2026 ở tab «Danh mục phòng».
   */
  description?: string
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
  /** Cấu hình thanh lọc nhanh ngoài bảng. */
  quickFilters?: QuickFilterConfig[]
  /** Cấu hình các cột hiển thị trên DataTable. */
  columns: DataTableColumn<T>[]
  /**
   * Nội dung MỘT THẺ ở khổ điện thoại (< 768px) — khai nó là bật chế độ thẻ,
   * xem `DataTableProps.mobileCard`.
   *
   * ⚠️ **Tự nguyện, không mặc định.** Khung CRUD này chạy cho hơn hai chục danh
   * mục; bật thẻ cho tất cả bằng một dòng ở đây là hai chục màn đồng loạt đổi
   * hình dạng mà không ai xem lại từng cái. Danh mục hai ba cột thì bảng cuộn
   * ngang vẫn đọc được — chỉ những màn nhiều cột mới cần dời.
   *
   * ⚠️ Thẻ KHÔNG suy ra từ `columns`: cột khai bề rộng, thứ tự, ghim — toàn thứ
   * chỉ có nghĩa trong lưới. Ở thẻ, người dựng tự chọn bày trường nào theo thứ
   * bậc nào.
   */
  mobileCard?: (row: T) => ReactNode
  /** Cấu hình bộ lọc nâng cao (ConditionalFilter). */
  filterConfig?: {
    fields: FilterFieldDefinition[]
    preserveParams?: string[]
    allowConjunctionToggle?: boolean
  }
  /** Cấu hình các trường trong Form thêm / sửa. */
  formFields: CrudFormField[]
  /**
   * Câu mô tả của từng NHÓM ô (khóa = `field.section`). Tùy chọn — nhóm nào
   * không khai thì chỉ hiện tiêu đề. Dùng để nói bằng tiếng người cái mà tên
   * nhóm nói bằng từ chuyên môn.
   */
  formSections?: Record<string, string>
  /** Đường dẫn trang danh sách (vd '/inventory/warehouses'). */
  listRoute?: string
  /** Đường dẫn tới trang chi tiết (vd (id) => `/inventory/warehouses/${id}`). */
  detailRoute?: (id: number | string) => string
  /**
   * Đường dẫn trang THÊM MỚI (vd '/hr/leave-types/new'). Khai nó thì nút «Thêm»
   * **điều hướng sang trang đó** thay vì bật hộp thoại; bỏ trống = giữ hộp thoại
   * như cũ.
   *
   * Dùng cho danh mục mà form thêm mới dài hoặc nhiều ô cần đọc kỹ (Loại nghỉ có
   * 10 ô, kèm bậc thâm niên) — nhồi vào hộp thoại thì người dùng phải cuộn TRONG
   * một khung nổi, bấm ra ngoài là mất sạch, và không dán được link cho người
   * khác. Danh mục hai ba ô thì hộp thoại vẫn nhanh hơn, đừng dời hết sang trang.
   *
   * Trang đó dựng bằng chính `CrudDetailPage`: đăng ký route TĨNH (không có
   * `:id`) trỏ vào cùng component chi tiết, nó tự nhận ra chế độ tạo mới.
   */
  createRoute?: string
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
  /**
   * Bề ngang tối đa của TRANG CHI TIẾT (mặc định `'max-w-5xl'`).
   *
   * Danh mục thường chỉ có một biểu mẫu, mà lưới ô nhập nhiều nhất 2 cột: thả
   * cho giãn hết màn 24" thì mỗi cột rộng ~800px — ô nhập một con số dài bằng
   * nửa màn hình, hàng công tắc thì nhãn dính mép trái nút dính mép phải. Chặn
   * ở TRANG (không chặn riêng biểu mẫu) để thẻ danh tính, tab và dấu vết cùng
   * một cột — chặn mỗi biểu mẫu thì nó ngắn cụt dưới một cái thẻ rộng gấp rưỡi.
   *
   * Đặt `'max-w-none'` cho màn có tab chứa BẢNG rộng (Sản phẩm, Nhà cung cấp,
   * Phòng họp) — bảng bị bóp còn 1024px là cụt cột.
   */
  detailMaxWidth?: string
  /** Render thêm nội dung ở đầu thanh công cụ. */
  renderToolbarExtra?: () => ReactNode
  /**
   * Ghi đè hộp thoại Thêm/Sửa bằng component RIÊNG khi biểu mẫu quá đặc thù cho khung
   * generic (vd form Tài xế có nút Nội bộ/Thuê ngoài + tìm nhân sự theo SĐT). Nhận đúng
   * props như `CrudFormDialog`; bỏ trống thì dùng form dựng từ `formFields`.
   */
  FormDialog?: ComponentType<CrudFormDialogProps<T>>
  /**
   * Bấm một dòng MỞ POPUP Thêm/Sửa (với bản ghi đó) thay vì điều hướng sang trang chi
   * tiết. Dùng khi danh mục xem/sửa gọn trong popup (vd Tài xế). Bỏ trống = giữ hành vi
   * cũ: điều hướng theo `detailRoute`.
   */
  openFormOnRowClick?: boolean
}

/** Props chuẩn của hộp thoại Thêm/Sửa — dùng cho cả `CrudFormDialog` lẫn bản ghi đè. */
export interface CrudFormDialogProps<T> {
  open: boolean
  onOpenChange: (open: boolean) => void
  config: CrudConfig<T>
  /** Có = SỬA bản ghi này; bỏ trống = THÊM mới. */
  item?: T | null
}
