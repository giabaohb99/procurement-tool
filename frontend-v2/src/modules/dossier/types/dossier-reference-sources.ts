/**
 * DANH MỤC mà một ô «Chọn từ danh mục» được phép trỏ tới.
 *
 * ⚠️ **Khóa phải khớp từng chữ với `REFERENCE_MODELS` ở
 * `backend/app/modules/dossier/reference_sources.py`.** Lệch một khóa thì người
 * dùng khai được một danh mục mà backend chặn khi bấm Lưu — hoặc ngược lại, một
 * danh mục backend nhận mà giao diện không bày ra.
 *
 * ⚠️ Khai KHÓA, không khai URL ở nơi người dùng chạm tới. `url` dưới đây là của
 * mã nguồn, không phải của biểu mẫu — máy khách chỉ gửi lên khóa.
 */

export interface ReferenceSource {
  /** Nhãn hiện trong ô chọn «Danh mục». */
  label: string
  url: string
  /** Cột dùng làm nhãn hiển thị. */
  labelKey: string
  /**
   * Tham số LỌC phía server, hoặc `null` nếu danh mục nhỏ và nạp hết được.
   *
   * ⚠️ Phải là tên CÓ trong `filterable` của endpoint đó. Tên ngoài danh sách ấy
   * bị `apply_filters` **bỏ qua trong im lặng** — ô tìm gõ gì cũng trả nguyên
   * danh sách, không lỗi nào để lần. Đã thử tay từng cái: `departments` bỏ qua
   * `name` (trả đủ 18 dòng), còn `employees` thì lọc bằng `full_name` chứ không
   * phải `name`.
   */
  searchParam: string | null
}

/**
 * ⚠️ Cố ý HẸP. Thêm một dòng ở đây là mở danh mục đó cho mọi người sửa được bộ
 * trường — phải trả lời được «ai đọc được danh mục này?» trước khi thêm. Quyền
 * vẫn do chính endpoint gác (ô chọn gọi API bằng token của người dùng), nhưng
 * đừng trông vào đó mà thêm bừa.
 */
export const REFERENCE_SOURCES: Record<string, ReferenceSource> = {
  employee: {
    label: 'Nhân sự',
    url: '/api/employees',
    labelKey: 'full_name',
    searchParam: 'full_name',
  },
  department: {
    //  18 dòng — nạp hết, lọc ngay trong trình duyệt. Endpoint này KHÔNG nhận
    //  tham số lọc theo tên (đã thử: `?name=Kho` trả về cả 18).
    label: 'Phòng ban',
    url: '/api/departments',
    labelKey: 'name',
    searchParam: null,
  },
  company: {
    label: 'Pháp nhân',
    url: '/api/companies',
    labelKey: 'name',
    searchParam: null,
  },
  supplier: {
    label: 'Nhà cung cấp',
    url: '/api/suppliers',
    labelKey: 'name',
    searchParam: 'name',
  },
  product: {
    //  ⚠️ **6803 dòng** (đo 17/09/2026) và còn tăng. Trần phân trang của backend
    //  là 5000, nên KHÔNG có cách nào nạp hết — bắt buộc phải tra phía server,
    //  không thì sản phẩm thứ 5001 trở đi không chọn được và **không gì báo**.
    label: 'Sản phẩm / Vật tư',
    url: '/api/products',
    labelKey: 'name',
    searchParam: 'name',
  },
}

export type ReferenceSourceKey = keyof typeof REFERENCE_SOURCES

/** Số dòng nạp mỗi lượt. Danh mục nhỏ thì đây là nạp HẾT; lớn thì là trang đầu. */
export const REFERENCE_PAGE_SIZE = 200

/**
 * Tra một danh mục theo khóa. Khóa lạ → `undefined`.
 *
 * ⚠️ Hỏi `Object.hasOwn` chứ KHÔNG viết thẳng `REFERENCE_SOURCES[key]`: mọi vật
 * thể đều thừa kế `__proto__` · `constructor` · `toString`, nên ba khóa đó trả
 * về một thứ **truthy** mà `label` là `undefined`. Nơi gọi kiểm `if (!config)`
 * sẽ cho lọt, rồi `config.label.toLowerCase()` ném `TypeError` **ngay lúc vẽ** —
 * tức cả biểu mẫu trắng xóa, không phải một ô báo lỗi. Cùng bài học đã ghi ở
 * `vehicle-booking/utils/calendar-views.ts`.
 */
export function referenceSource(key: string): ReferenceSource | undefined {
  return Object.hasOwn(REFERENCE_SOURCES, key) ? REFERENCE_SOURCES[key] : undefined
}
