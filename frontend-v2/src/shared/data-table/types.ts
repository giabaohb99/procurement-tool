import type { ReactNode } from 'react'

export interface DataTableColumn<T> {
  /** Khóa cột — dùng làm id khi ẩn/hiện và khi nhớ độ rộng. Phải duy nhất trong bảng. */
  key: string
  /**
   * Tiêu đề cột. Kết thúc bằng `" *"` = cột BẮT BUỘC nhập: bảng tự tách phần đó
   * ra và vẽ dấu sao màu đỏ (`required-header.ts`). Đừng tự chèn thẻ vào đây —
   * chuỗi này còn dùng làm nhãn kéo thả và tên cột trong menu ẩn/hiện.
   */
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
  /**
   * `true` = cho phép chữ dài tự xuống dòng thay vì cắt bằng dấu ba chấm "…".
   * Thích hợp cho cột Tên, Nhà cung cấp, Địa chỉ, Ghi chú.
   */
  wrap?: boolean
}

/**
 * Cột của `LinesTable` — bảng DÒNG CHỨNG TỪ (dòng hàng YCMH/ĐMH, dòng khảo sát,
 * các lần giao). Khác `DataTableColumn` ở chỗ KHÔNG khai `cell`: ô của bảng dòng
 * cần cả chỉ số dòng để sửa đúng phần tử, nên nội dung do một hàm `renderCell`
 * duy nhất vẽ theo `key`.
 */
export interface LinesTableColumn {
  /** Khóa cột — vừa là id nhớ bố cục, vừa là nhánh `switch` trong `renderCell`. */
  key: string
  /** Kết thúc bằng `" *"` = cột bắt buộc nhập — xem `DataTableColumn.header`. */
  header: string
  /** Độ rộng ban đầu (px). */
  width?: number
  /** Chặn dưới khi kéo giãn. Mặc định 64px. */
  minWidth?: number
  align?: 'left' | 'center' | 'right'
  /** `false` = cột luôn hiện, không cho tắt trong menu "Cột". */
  hideable?: boolean
  /** Mặc định GHIM sang trái (dính khi cuộn ngang). */
  defaultPinned?: boolean
  /**
   * Cột chỉ hiện ở chế độ "Bảng đầy đủ"; nút chuyển chế độ bật/tắt đúng nhóm này.
   * Vẫn bật/tắt lẻ được trong menu "Cột" như mọi cột khác.
   */
  compactHidden?: boolean
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
  /**
   * Màu người dùng tự đặt cho từng cột (mã màu gốc trong `COLUMN_COLORS`).
   * Không có khóa = cột dùng nền mặc định.
   */
  columnColors: Record<string, string>
}

/** Thả cột vào TRƯỚC hay SAU cột đang trỏ tới. */
export type ColumnDropSide = 'before' | 'after'
