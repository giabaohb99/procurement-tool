/**
 * SỔ VĂN BẢN (`tab_document_book`).
 *
 * Theo lối AMIS Văn thư: sổ là một **bản ghi riêng**, không phải một giá trị
 * enum trên văn bản. Mỗi sổ có người quản lý, đơn vị được xem, và **bộ đếm số
 * của riêng nó** — sổ Công văn đến 2026 đếm 1, 2, 3… độc lập với sổ Quyết định
 * đi 2026.
 */

/** 1 văn bản đến · 2 văn bản đi · 3 văn bản nội bộ. */
export type BookKind = 1 | 2 | 3

export const BOOK_KIND_LABELS: Record<BookKind, string> = {
  1: 'Sổ văn bản đến',
  2: 'Sổ văn bản đi',
  3: 'Sổ văn bản nội bộ',
}

/** Nhãn ngắn dùng trong ô lọc và chip trên bảng. */
export const BOOK_KIND_SHORT: Record<BookKind, string> = {
  1: 'Đến',
  2: 'Đi',
  3: 'Nội bộ',
}

export const BOOK_KIND_OPTIONS = (
  Object.entries(BOOK_KIND_LABELS) as [string, string][]
).map(([value, label]) => ({ value: Number(value) as BookKind, label }))

export interface DocumentBook {
  id: number
  /** Mã sổ — là khóa của bộ đếm, **không sửa được sau khi tạo**. */
  code: string
  name: string
  kind: BookKind
  description: string

  /** Pháp nhân sở hữu sổ. */
  company_id: number

  /** Tiền tố in trước số thứ tự: `VBĐ` → `VBĐ 08/2026`. */
  number_prefix: string
  reset_yearly: boolean
  /** Số đầu tiên của sổ — dùng khi chuyển từ sổ giấy đang dở sang. */
  start_no: number
  is_active: boolean

  /**
   * ID **nhân sự** đích danh — không phải id tài khoản, và **không có chiều
   * phòng ban**: cấp quyền xem theo phòng ban thì người mới vào phòng tự thấy
   * sổ, người chuyển đi tự mất, mà người mở sổ không hề chọn hai hành vi đó.
   */
  manager_ids: number[]
  viewer_ids: number[]

  // ===== Backend tính thêm khi đọc, không gửi lên khi lưu =====
  /** Số kế tiếp sẽ cấp — **chỉ để xem**, không phải số đã chiếm. */
  next_no: number
  next_number_display: string
  /** Đã cấp bao nhiêu số trong năm. */
  issued_count: number
  company_name: string
  manager_names: string[]
  viewer_names: string[]
}

/** Phần gửi lên khi tạo / sửa — bỏ hết trường backend tự tính. */
export type DocumentBookInput = Omit<
  DocumentBook,
  | 'id'
  | 'next_no'
  | 'next_number_display'
  | 'issued_count'
  | 'company_name'
  | 'manager_names'
  | 'viewer_names'
>

export interface BookCounter {
  year: number
  start_no: number
  issued_count: number
  next_no: number
  next_number_display: string
  reset_yearly: boolean
}
