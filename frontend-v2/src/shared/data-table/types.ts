import type { ReactNode } from 'react'

export interface DataTableColumn<T> {
  /** Khóa cột — dùng làm id khi ẩn/hiện và khi nhớ độ rộng. Phải duy nhất trong bảng. */
  key: string
  header: string
  /** Nội dung ô. Trả `null`/chuỗi rỗng thì bảng tự hiện dấu gạch ngang. */
  cell: (row: T) => ReactNode
  /** Độ rộng ban đầu (px). Bỏ trống = cột co giãn theo phần còn lại. */
  width?: number
  /** Chặn dưới khi kéo giãn. Mặc định 64px. */
  minWidth?: number
  align?: 'left' | 'center' | 'right'
  /**
   * `false` = cột luôn hiện, không cho tắt trong menu "Cột".
   * Dùng cho cột định danh (tên, mã) — ẩn hết đi thì bảng vô nghĩa.
   */
  hideable?: boolean
  /** Mặc định ẩn khi mở bảng lần đầu; người dùng vẫn bật lại được. */
  defaultHidden?: boolean
  /**
   * Mặc định GHIM sang trái (dính khi cuộn ngang). Chỉ đặt cho cột định danh
   * của bảng nhiều cột — ghim nhiều quá thì không còn chỗ cho dữ liệu.
   */
  defaultPinned?: boolean
}

export interface DataTablePagination {
  /** Trang hiện tại, đếm từ 1. */
  page: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
  onPageSizeChange: (pageSize: number) => void
  /** Danh từ đếm được: "nhân sự", "công ty"… */
  unitLabel: string
}

/** Trạng thái bảng được nhớ lại giữa các phiên (localStorage). */
export interface DataTableLayout {
  hiddenColumns: string[]
  columnWidths: Record<string, number>
  /**
   * Thứ tự cột do người dùng kéo thả, kể cả cột đang ẩn (ẩn rồi hiện lại vẫn
   * về đúng chỗ cũ). Mảng RỖNG = giữ nguyên thứ tự khai báo trong code.
   *
   * Khóa lạ (cột đã bị xóa khỏi code) được bỏ qua khi đọc, cột mới thêm sau
   * này xếp nối vào cuối — nên đổi cấu hình cột không làm hỏng layout đã lưu.
   */
  columnOrder: string[]
  /**
   * Cột được GHIM sang trái: luôn đứng đầu bảng và dính lại khi cuộn ngang.
   * Dành cho bảng nhiều cột (vd Tiến độ mua hàng) — cuộn tới cột thứ 20 mà vẫn
   * biết đang xem đơn nào.
   */
  pinnedColumns: string[]
}

/** Thả cột vào TRƯỚC hay SAU cột đang trỏ tới. */
export type ColumnDropSide = 'before' | 'after'
